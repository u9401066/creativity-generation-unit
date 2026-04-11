"""
Creative Session Manager - 跨呼叫的互動式創意會話

核心理念：Agent Harness 的「互動」面
- 外部 Agent 不是一次性呼叫，而是透過多次 MCP 呼叫推進創意過程
- 每次呼叫都帶入 Agent 自己的思考結果
- CGU 根據 Agent 的輸入決定下一步：挑戰、深化、碰撞、還是收工

典型互動流程：
  Agent → start_session(topic)
  Agent → submit_ideas(session_id, ideas)        ← Agent 自己想的
  Agent ← receive_challenges(session_id)          ← CGU 回擊
  Agent → submit_evolved_ideas(session_id, ideas) ← Agent 進化後的
  Agent ← receive_cross_pollination(session_id)   ← CGU 做碰撞
  Agent → finalize_session(session_id)            ← 收工，得到最終報告
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ── 會話狀態 ──────────────────────────────────────────────


class SessionState(BaseModel):
    """會話狀態"""

    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    topic: str
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    status: str = Field(default="awaiting_ideas")

    # 會話數據
    submitted_ideas: list[str] = Field(default_factory=list)
    challenges: list[str] = Field(default_factory=list)
    evolved_ideas: list[str] = Field(default_factory=list)
    cross_pollinations: list[str] = Field(default_factory=list)
    final_output: str | None = None

    # 品質追蹤
    quality_scores: list[float] = Field(default_factory=list)
    round_count: int = 0


# ── 有效的狀態轉移 ────────────────────────────────────────


_VALID_TRANSITIONS: dict[str, list[str]] = {
    "awaiting_ideas": ["ideas_submitted"],
    "ideas_submitted": ["challenges_generated"],
    "challenges_generated": ["evolved_ideas_submitted"],
    "evolved_ideas_submitted": ["cross_pollinated"],
    "cross_pollinated": ["finalized", "ideas_submitted"],  # 可以再迭代
    "finalized": [],
}


# ── 會話管理器 ────────────────────────────────────────────


class SessionManager:
    """
    創意會話管理器

    管理跨 MCP 呼叫的會話狀態，讓外部 Agent 能以互動方式
    推進創意過程。

    用法（MCP 工具呼叫序列）：
        1. start_session(topic) → session_id
        2. submit_ideas(session_id, ideas) → challenges
        3. submit_evolved_ideas(session_id, ideas) → cross_pollinations
        4. finalize_session(session_id) → final_report
    """

    def __init__(self, llm_client: Any = None) -> None:
        self.llm = llm_client
        self._sessions: dict[str, SessionState] = {}

    def start_session(self, topic: str) -> SessionState:
        """啟動新的創意會話"""
        session = SessionState(topic=topic)
        self._sessions[session.session_id] = session
        logger.info("新會話啟動：%s (%s)", topic, session.session_id)
        return session

    def get_session(self, session_id: str) -> SessionState | None:
        """取得會話狀態"""
        return self._sessions.get(session_id)

    def _transition(self, session: SessionState, new_status: str) -> None:
        """狀態轉移（含驗證）"""
        valid = _VALID_TRANSITIONS.get(session.status, [])
        if new_status not in valid:
            raise ValueError(
                f"無效的狀態轉移：{session.status} → {new_status}。"
                f"有效目標：{valid}"
            )
        session.status = new_status
        session.round_count += 1

    def submit_ideas(
        self, session_id: str, ideas: list[str]
    ) -> dict[str, Any]:
        """
        提交想法並接收挑戰

        Agent 提交自己思考的想法，CGU 回擊針對性的挑戰。
        """
        session = self._get_or_raise(session_id)
        self._transition(session, "ideas_submitted")

        session.submitted_ideas = ideas

        # 生成挑戰
        challenges = self._generate_challenges(session.topic, ideas)
        session.challenges = challenges
        self._transition(session, "challenges_generated")

        return {
            "session_id": session_id,
            "status": session.status,
            "challenges": challenges,
            "instruction": "請回應每個挑戰，提交進化後的想法。",
        }

    def submit_evolved_ideas(
        self, session_id: str, evolved_ideas: list[str]
    ) -> dict[str, Any]:
        """
        提交進化後的想法並接收交叉授粉

        Agent 回應挑戰後的進化版想法，CGU 做碰撞尋找連結。
        """
        session = self._get_or_raise(session_id)
        self._transition(session, "evolved_ideas_submitted")

        session.evolved_ideas = evolved_ideas

        # 評估品質提升
        quality = self._estimate_quality(evolved_ideas, session.submitted_ideas)
        session.quality_scores.append(quality)

        # 交叉授粉
        crosses = self._cross_pollinate(session.topic, evolved_ideas)
        session.cross_pollinations = crosses
        self._transition(session, "cross_pollinated")

        return {
            "session_id": session_id,
            "status": session.status,
            "cross_pollinations": crosses,
            "quality_score": round(quality, 3),
            "can_iterate": True,
            "instruction": (
                "你可以選擇：\n"
                "1. 基於交叉授粉結果提交新想法（繼續迭代）\n"
                "2. 結束會話取得最終報告"
            ),
        }

    def finalize_session(self, session_id: str) -> dict[str, Any]:
        """結束會話，產生最終報告"""
        session = self._get_or_raise(session_id)
        self._transition(session, "finalized")

        final = self._synthesize(session)
        session.final_output = final

        return {
            "session_id": session_id,
            "status": "finalized",
            "topic": session.topic,
            "total_rounds": session.round_count,
            "quality_trajectory": [round(q, 3) for q in session.quality_scores],
            "initial_ideas": session.submitted_ideas,
            "evolved_ideas": session.evolved_ideas,
            "cross_pollinations": session.cross_pollinations,
            "final_output": final,
        }

    def list_sessions(self) -> list[dict[str, Any]]:
        """列出所有會話"""
        return [
            {
                "session_id": s.session_id,
                "topic": s.topic,
                "status": s.status,
                "round_count": s.round_count,
                "created_at": s.created_at,
            }
            for s in self._sessions.values()
        ]

    # ── 內部方法 ──

    def _get_or_raise(self, session_id: str) -> SessionState:
        """取得會話，不存在則拋錯"""
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"會話不存在：{session_id}")
        return session

    def _generate_challenges(
        self, topic: str, ideas: list[str]
    ) -> list[str]:
        """生成針對性的挑戰"""
        if self.llm:
            try:
                ideas_text = "\n".join(f"- {idea}" for idea in ideas)
                prompt = (
                    f"你是一位嚴苛的創意評論家。針對以下想法各提出一個最致命的批判。\n\n"
                    f"主題：{topic}\n想法：\n{ideas_text}\n\n"
                    f"每個批判必須具體、有理有據，不能泛泛而談。"
                    f"每個批判以「⚔️」開頭。"
                )
                response = self.llm.generate(prompt=prompt, temperature=0.7)
                lines = [
                    line.strip()
                    for line in response.strip().splitlines()
                    if line.strip()
                ]
                if lines:
                    return lines
            except Exception as e:
                logger.warning("LLM 挑戰生成失敗：%s", e)

        # 框架模式
        return [
            f"⚔️ 針對「{idea[:50]}…」：這個想法最大的盲點是什麼？"
            f"它真的是新的嗎？有什麼根本性障礙？"
            for idea in ideas
        ]

    def _cross_pollinate(
        self, topic: str, ideas: list[str]
    ) -> list[str]:
        """交叉授粉"""
        if self.llm:
            try:
                ideas_text = "\n".join(f"- {idea}" for idea in ideas)
                prompt = (
                    f"以下是經過進化的想法，請找出它們之間意想不到的連結。\n\n"
                    f"主題：{topic}\n想法：\n{ideas_text}\n\n"
                    f"嘗試將不同想法的精華結合，創造嫁接想法。"
                    f"每個以「🌱」開頭。"
                )
                response = self.llm.generate(prompt=prompt, temperature=0.8)
                lines = [
                    line.strip()
                    for line in response.strip().splitlines()
                    if line.strip()
                ]
                if lines:
                    return lines
            except Exception as e:
                logger.warning("LLM 交叉授粉失敗：%s", e)

        # 框架模式
        crosses: list[str] = []
        for i, idea_a in enumerate(ideas):
            for idea_b in ideas[i + 1 :]:
                crosses.append(
                    f"🌱 將「{idea_a[:30]}…」的骨架"
                    f"與「{idea_b[:30]}…」的靈魂嫁接"
                )
        return crosses or [f"🌱 深化「{ideas[0][:50]}…」的跨域可能性"]

    def _estimate_quality(
        self, evolved: list[str], original: list[str]
    ) -> float:
        """估算品質提升"""
        if not evolved or not original:
            return 0.5

        # 新詞彙比例
        orig_words = set()
        for idea in original:
            orig_words.update(idea.split())
        evolved_words = set()
        for idea in evolved:
            evolved_words.update(idea.split())

        new_words = evolved_words - orig_words
        word_novelty = len(new_words) / max(len(evolved_words), 1)

        # 內容增長
        orig_len = sum(len(i) for i in original)
        evolved_len = sum(len(i) for i in evolved)
        growth = (evolved_len - orig_len) / max(orig_len, 1)
        growth_score = min(1.0, max(0.0, growth))

        return min(1.0, word_novelty * 0.6 + growth_score * 0.4)

    def _synthesize(self, session: SessionState) -> str:
        """綜合最終產出"""
        all_ideas = (
            session.evolved_ideas
            or session.cross_pollinations
            or session.submitted_ideas
        )

        if self.llm:
            try:
                ideas_text = "\n".join(f"- {idea}" for idea in all_ideas)
                prompt = (
                    f"經過多輪審議，請從以下想法中選出最有潛力的方向"
                    f"並深化為完整方案。\n\n"
                    f"主題：{session.topic}\n"
                    f"存活想法：\n{ideas_text}\n\n"
                    f"輸出一個精煉的最終創意方案。"
                )
                return self.llm.generate(prompt=prompt, temperature=0.7)
            except Exception as e:
                logger.warning("LLM 綜合失敗：%s", e)

        return (
            f"【最終綜合】主題：{session.topic}\n"
            f"經過 {session.round_count} 輪互動審議，"
            f"從 {len(all_ideas)} 個存活想法中整合。\n"
            f"請選出最有潛力的方向並深化為完整方案。"
        )


# ── 全域管理器 ────────────────────────────────────────────


_manager: SessionManager | None = None


def get_session_manager(llm_client: Any = None) -> SessionManager:
    """取得全域會話管理器"""
    global _manager
    if _manager is None:
        _manager = SessionManager(llm_client)
    return _manager
