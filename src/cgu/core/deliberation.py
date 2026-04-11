"""
DeliberationEngine - 多輪審議式創意引擎

核心理念：Agent Harness Engineering
- 不是「產生創意」，是「結構化創意思考過程」
- 呼叫端的 Agent（Copilot、Claude、GPT）提供真正的智慧
- CGU 提供多輪審議鷹架（scaffolding）

流程：
  DIVERGE → CHALLENGE → EVOLVE → CROSS_POLLINATE → SYNTHESIZE

每一輪都有明確的目標和評估標準，創意透過多輪對話逐步深化。
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 嘗試匯入 LLM 系統提示（可選依賴）
try:
    from cgu.llm import SYSTEM_PROMPT_CREATIVITY
except ImportError:
    SYSTEM_PROMPT_CREATIVITY = None


# ── 階段枚舉 ──────────────────────────────────────────────


class DeliberationPhase(StrEnum):
    """審議階段"""

    DIVERGE = "diverge"                    # 發散：多角度生成種子想法
    CHALLENGE = "challenge"                # 挑戰：對抗式批判
    EVOLVE = "evolve"                      # 進化：回應挑戰後升級
    CROSS_POLLINATE = "cross_pollinate"    # 交叉授粉：跨想法連結
    SYNTHESIZE = "synthesize"              # 綜合：整合為精煉產出


PHASE_ORDER: list[DeliberationPhase] = list(DeliberationPhase)


# ── 資料模型 ──────────────────────────────────────────────


class QualityMetrics(BaseModel):
    """單輪品質指標"""

    novelty: float = Field(default=0.0, ge=0.0, le=1.0, description="新穎度")
    depth: float = Field(default=0.0, ge=0.0, le=1.0, description="深度")
    coherence: float = Field(default=0.0, ge=0.0, le=1.0, description="連貫性")
    surprise: float = Field(default=0.0, ge=0.0, le=1.0, description="驚喜感")

    @property
    def overall(self) -> float:
        """綜合品質 = 加權平均"""
        return (
            self.novelty * 0.3
            + self.depth * 0.25
            + self.coherence * 0.25
            + self.surprise * 0.2
        )


class DeliberationRound(BaseModel):
    """單一審議輪次"""

    round_number: int = Field(description="輪次編號")
    phase: DeliberationPhase = Field(description="審議階段")
    inputs: list[str] = Field(default_factory=list, description="本輪輸入")
    outputs: list[str] = Field(default_factory=list, description="本輪產出")
    reasoning: str = Field(default="", description="本輪推理過程")
    quality: QualityMetrics = Field(
        default_factory=QualityMetrics, description="品質指標"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
    )

    # 框架模式回傳的結構化提示（供外部 Agent 填寫）
    framework_prompt: str | None = Field(
        default=None, description="無 LLM 時的結構化提示"
    )


class DeliberationSession(BaseModel):
    """審議會議：管理跨輪次的完整狀態"""

    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    topic: str = Field(description="審議主題")
    rounds: list[DeliberationRound] = Field(default_factory=list)
    quality_trajectory: list[float] = Field(
        default_factory=list, description="品質變化軌跡"
    )
    surviving_ideas: list[str] = Field(
        default_factory=list, description="存活至今的想法"
    )
    final_output: str | None = Field(default=None, description="最終綜合產出")
    status: str = Field(default="pending", description="會議狀態")

    @property
    def current_phase(self) -> DeliberationPhase | None:
        """目前所在階段"""
        if not self.rounds:
            return None
        return self.rounds[-1].phase

    @property
    def is_quality_plateaued(self) -> bool:
        """品質是否已趨於平穩（連續兩輪改善 < 5%）"""
        if len(self.quality_trajectory) < 3:
            return False
        recent = self.quality_trajectory[-3:]
        delta1 = abs(recent[-1] - recent[-2])
        delta2 = abs(recent[-2] - recent[-3])
        return delta1 < 0.05 and delta2 < 0.05


class DeliberationResult(BaseModel):
    """審議最終結果"""

    session: DeliberationSession
    final_output: str = Field(default="", description="最終創意產出")
    total_rounds: int = 0
    peak_quality: float = 0.0
    idea_evolution: list[str] = Field(
        default_factory=list, description="想法演化軌跡"
    )


# ── 階段提示模板 ─────────────────────────────────────────


_DIVERGE_PROMPT = """你是一位發散思考大師。請針對以下主題，從至少 3 個截然不同的角度各生成一個種子想法。

主題：{topic}

要求：
1. 每個角度必須來自不同的領域或思維框架
2. 追求多樣性而非品質——越不同越好
3. 包含至少一個反直覺的方向

輸出格式：每個想法一行，以「-」開頭。"""

_CHALLENGE_PROMPT = """你是一位嚴苛的創意評論家。針對以下每個想法，提出最具針對性的批判。

主題：{topic}
想法：
{ideas}

對每個想法：
1. 找出最致命的弱點（不是泛泛的「不夠好」）
2. 指出具體的邏輯漏洞或盲點
3. 提出「如果……會怎樣？」的壓力測試

輸出格式：每條批判以「⚔️」開頭，標明對應的想法。"""

_EVOLVE_PROMPT = """你是一位創意進化專家。每個想法都被嚴厲批判了，現在它們必須進化。

主題：{topic}
原始想法與挑戰：
{challenged_ideas}

規則：
1. 不能迴避批判——必須正面回應
2. 進化後的想法必須比原始版本更強
3. 可以改變方向，但核心洞察必須保留

輸出格式：每個進化想法以「🔄」開頭。"""

_CROSS_POLLINATE_PROMPT = """你是一位跨域連結大師。以下是經過進化的想法，請找出它們之間意想不到的連結。

主題：{topic}
進化後的想法：
{evolved_ideas}

任務：
1. 找出任意兩個想法之間的隱藏共通點
2. 嘗試將不同想法的精華部分結合
3. 創造至少一個「嫁接」想法——取 A 的骨架 + B 的靈魂

輸出格式：每個交叉想法以「🌱」開頭，並說明來源。"""

_SYNTHESIZE_PROMPT = """你是一位創意整合大師。經過發散、挑戰、進化、交叉授粉，現在要產出最終成果。

主題：{topic}
所有存活的想法：
{all_ideas}
品質軌跡：{quality_trajectory}

任務：
1. 選出最有潛力的 1-2 個方向
2. 深化為完整、可執行的創意方案
3. 說明為什麼這個方案比初始想法好

輸出：一個精煉的最終創意方案。"""


# ── 引擎 ─────────────────────────────────────────────────


class DeliberationEngine:
    """
    多輪審議式創意引擎

    用法：
        engine = DeliberationEngine(llm_client=my_llm)
        result = await engine.deliberate("如何讓城市更宜居？")

    無 LLM 時回傳結構化框架提示，由外部 Agent 填寫。
    """

    def __init__(
        self,
        llm_client: Any = None,
        *,
        max_rounds: int = 5,
        quality_threshold: float = 0.7,
    ) -> None:
        self.llm = llm_client
        self.max_rounds = max_rounds
        self.quality_threshold = quality_threshold

        self._phase_runners = {
            DeliberationPhase.DIVERGE: self._run_diverge,
            DeliberationPhase.CHALLENGE: self._run_challenge,
            DeliberationPhase.EVOLVE: self._run_evolve,
            DeliberationPhase.CROSS_POLLINATE: self._run_cross_pollinate,
            DeliberationPhase.SYNTHESIZE: self._run_synthesize,
        }

    # ── 主要入口 ──

    async def deliberate(self, topic: str) -> DeliberationResult:
        """
        執行完整的多輪審議流程

        流程自動依序進行五個階段，並在品質趨於平穩時提前停止。
        """
        session = DeliberationSession(topic=topic, status="in_progress")
        logger.info("開始審議：%s (session=%s)", topic, session.session_id)

        for round_num, phase in enumerate(PHASE_ORDER, start=1):
            if round_num > self.max_rounds:
                logger.info("達到最大輪數 %d，停止", self.max_rounds)
                break

            rnd = await self._execute_round(session, round_num, phase)
            session.rounds.append(rnd)
            session.quality_trajectory.append(rnd.quality.overall)

            if rnd.outputs:
                session.surviving_ideas = rnd.outputs

            # 品質停滯時提前結束（但至少完成前 3 輪）
            if round_num >= 3 and session.is_quality_plateaued:
                logger.info("品質趨於平穩，於第 %d 輪提前停止", round_num)
                break

        session.final_output = (
            session.surviving_ideas[-1] if session.surviving_ideas else ""
        )
        session.status = "completed"

        return DeliberationResult(
            session=session,
            final_output=session.final_output or "",
            total_rounds=len(session.rounds),
            peak_quality=max(session.quality_trajectory, default=0.0),
            idea_evolution=self._extract_evolution(session),
        )

    # ── 輪次執行 ──

    async def _execute_round(
        self,
        session: DeliberationSession,
        round_number: int,
        phase: DeliberationPhase,
    ) -> DeliberationRound:
        """執行單一輪次"""
        runner = self._phase_runners[phase]
        inputs = session.surviving_ideas or [session.topic]

        logger.info("第 %d 輪 [%s] 開始", round_number, phase.value)
        rnd = await runner(session.topic, inputs)
        rnd.round_number = round_number
        rnd.phase = phase

        if not rnd.quality.overall:
            rnd.quality = self._estimate_quality(rnd, session)

        return rnd

    # ── 五階段實作 ──

    async def _run_diverge(
        self, topic: str, inputs: list[str]
    ) -> DeliberationRound:
        """發散階段：從多角度生成種子想法"""
        prompt = _DIVERGE_PROMPT.format(topic=topic)

        if self.llm:
            return await self._llm_round(prompt, inputs)

        angles = ["技術/工程視角", "人文/社會視角", "自然/生態視角", "反直覺視角"]
        framework_ideas = [
            f"從{a}思考「{topic}」，會得到什麼種子想法？" for a in angles
        ]
        return DeliberationRound(
            round_number=0,
            phase=DeliberationPhase.DIVERGE,
            inputs=inputs,
            outputs=framework_ideas,
            reasoning="框架模式：提供四個發散角度供外部 Agent 填寫",
            framework_prompt=prompt,
        )

    async def _run_challenge(
        self, topic: str, inputs: list[str]
    ) -> DeliberationRound:
        """挑戰階段：對每個想法進行對抗式批判"""
        ideas_text = "\n".join(f"- {idea}" for idea in inputs)
        prompt = _CHALLENGE_PROMPT.format(topic=topic, ideas=ideas_text)

        if self.llm:
            return await self._llm_round(prompt, inputs)

        critiques = [
            f"⚔️ 針對「{idea}」：這個想法最大的盲點是什麼？"
            + "它是否只是常識的重新包裝？有沒有根本性的邏輯漏洞？"
            for idea in inputs
        ]
        return DeliberationRound(
            round_number=0,
            phase=DeliberationPhase.CHALLENGE,
            inputs=inputs,
            outputs=critiques,
            reasoning="框架模式：為每個想法生成針對性批判提示",
            framework_prompt=prompt,
        )

    async def _run_evolve(
        self, topic: str, inputs: list[str]
    ) -> DeliberationRound:
        """進化階段：想法回應挑戰後升級"""
        challenged_text = "\n".join(f"- {item}" for item in inputs)
        prompt = _EVOLVE_PROMPT.format(
            topic=topic, challenged_ideas=challenged_text
        )

        if self.llm:
            return await self._llm_round(prompt, inputs)

        evolved = [
            f"🔄 基於批判，將「{idea}」進化：保留核心洞察，"
            + "但解決被指出的弱點，使其更具體、更可行。"
            for idea in inputs
        ]
        return DeliberationRound(
            round_number=0,
            phase=DeliberationPhase.EVOLVE,
            inputs=inputs,
            outputs=evolved,
            reasoning="框架模式：為每個想法提供進化方向提示",
            framework_prompt=prompt,
        )

    async def _run_cross_pollinate(
        self, topic: str, inputs: list[str]
    ) -> DeliberationRound:
        """交叉授粉階段：找到想法之間的意外連結"""
        evolved_text = "\n".join(f"- {idea}" for idea in inputs)
        prompt = _CROSS_POLLINATE_PROMPT.format(
            topic=topic, evolved_ideas=evolved_text
        )

        if self.llm:
            return await self._llm_round(prompt, inputs)

        # 生成交叉組合提示
        crosses: list[str] = []
        for i, idea_a in enumerate(inputs):
            for idea_b in inputs[i + 1 :]:
                crosses.append(
                    f"🌱 如果將「{idea_a[:30]}…」的骨架"
                    + f"與「{idea_b[:30]}…」的靈魂嫁接，會產生什麼？"
                )
        if not crosses:
            crosses = [f"🌱 深化「{inputs[0]}」的跨域連結可能性"]

        return DeliberationRound(
            round_number=0,
            phase=DeliberationPhase.CROSS_POLLINATE,
            inputs=inputs,
            outputs=crosses,
            reasoning="框架模式：生成想法交叉配對提示",
            framework_prompt=prompt,
        )

    async def _run_synthesize(
        self, topic: str, inputs: list[str]
    ) -> DeliberationRound:
        """綜合階段：整合為精煉的最終產出"""
        all_ideas_text = "\n".join(f"- {idea}" for idea in inputs)
        prompt = _SYNTHESIZE_PROMPT.format(
            topic=topic,
            all_ideas=all_ideas_text,
            quality_trajectory="逐輪提升",
        )

        if self.llm:
            return await self._llm_round(prompt, inputs)

        synthesis = (
            f"【最終綜合】主題：{topic}\n"
            f"經過發散、挑戰、進化、交叉授粉四輪審議，"
            f"從 {len(inputs)} 個存活想法中整合出最終方案。\n"
            f"請選出最有潛力的方向並深化為完整方案。"
        )
        return DeliberationRound(
            round_number=0,
            phase=DeliberationPhase.SYNTHESIZE,
            inputs=inputs,
            outputs=[synthesis],
            reasoning="框架模式：提供最終綜合提示",
            framework_prompt=prompt,
        )

    # ── LLM 呼叫 ──

    async def _llm_round(
        self, prompt: str, inputs: list[str]
    ) -> DeliberationRound:
        """透過 LLM 執行一輪審議"""
        system = SYSTEM_PROMPT_CREATIVITY or ""
        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=system,
                temperature=0.8,
            )
            outputs = [
                line.lstrip("-⚔️🔄🌱 ").strip()
                for line in response.strip().splitlines()
                if line.strip() and not line.startswith("#")
            ]
            return DeliberationRound(
                round_number=0,
                phase=DeliberationPhase.DIVERGE,  # 由呼叫端覆寫
                inputs=inputs,
                outputs=outputs or [response],
                reasoning=f"LLM 生成（{len(outputs)} 項產出）",
            )
        except Exception as e:
            logger.warning("LLM 呼叫失敗，降級為框架模式：%s", e)
            return DeliberationRound(
                round_number=0,
                phase=DeliberationPhase.DIVERGE,
                inputs=inputs,
                outputs=[],
                reasoning=f"LLM 呼叫失敗：{e}",
                framework_prompt=prompt,
            )

    # ── 品質估算 ──

    def _estimate_quality(
        self,
        rnd: DeliberationRound,
        session: DeliberationSession,
    ) -> QualityMetrics:
        """啟發式品質估算（無 LLM 時使用）"""
        output_count = len(rnd.outputs)
        total_length = sum(len(o) for o in rnd.outputs)
        prev_quality = (
            session.quality_trajectory[-1] if session.quality_trajectory else 0.0
        )

        # 多樣性 → 新穎度
        unique_starts = len({o[:20] for o in rnd.outputs}) if rnd.outputs else 0
        novelty = min(1.0, unique_starts / max(output_count, 1))

        # 內容豐富度 → 深度
        depth = min(1.0, total_length / max(output_count * 80, 1))

        # 階段遞進 → 連貫性
        phase_idx = PHASE_ORDER.index(rnd.phase) if rnd.phase in PHASE_ORDER else 0
        coherence = min(1.0, 0.4 + phase_idx * 0.15)

        # 與前一輪的差異 → 驚喜感
        surprise = min(1.0, abs(novelty - prev_quality) + 0.2)

        return QualityMetrics(
            novelty=round(novelty, 3),
            depth=round(depth, 3),
            coherence=round(coherence, 3),
            surprise=round(surprise, 3),
        )

    # ── 輔助方法 ──

    def _extract_evolution(self, session: DeliberationSession) -> list[str]:
        """萃取想法演化軌跡（每輪取第一個產出作為代表）"""
        return [
            rnd.outputs[0] if rnd.outputs else "(無產出)"
            for rnd in session.rounds
        ]

    def format_report(self, result: DeliberationResult) -> str:
        """產生審議報告"""
        lines = [
            "═" * 60,
            "🧠 多輪審議報告",
            "═" * 60,
            "",
            f"📋 主題：{result.session.topic}",
            f"🔄 總輪數：{result.total_rounds}",
            f"📈 最高品質：{result.peak_quality:.0%}",
            f"🆔 會議：{result.session.session_id}",
            "",
        ]
        for rnd in result.session.rounds:
            phase_emoji = {
                DeliberationPhase.DIVERGE: "💡",
                DeliberationPhase.CHALLENGE: "⚔️",
                DeliberationPhase.EVOLVE: "🔄",
                DeliberationPhase.CROSS_POLLINATE: "🌱",
                DeliberationPhase.SYNTHESIZE: "🏆",
            }
            emoji = phase_emoji.get(rnd.phase, "▪️")
            lines.extend([
                "─" * 60,
                f"{emoji} 第 {rnd.round_number} 輪 [{rnd.phase.value}]"
                f"  品質={rnd.quality.overall:.0%}",
                f"   推理：{rnd.reasoning}",
            ])
            for i, out in enumerate(rnd.outputs[:3], 1):
                lines.append(f"   {i}. {out[:80]}")
            if len(rnd.outputs) > 3:
                lines.append(f"   ...（共 {len(rnd.outputs)} 項）")
            lines.append("")

        lines.extend([
            "═" * 60,
            "🏆 最終產出",
            result.final_output or "(無)",
            "═" * 60,
        ])
        return "\n".join(lines)


# ── 便捷函數 ─────────────────────────────────────────────


async def deliberate(
    topic: str,
    llm_client: Any = None,
    max_rounds: int = 5,
) -> DeliberationResult:
    """快速執行多輪審議"""
    engine = DeliberationEngine(llm_client, max_rounds=max_rounds)
    return await engine.deliberate(topic)


def deliberate_sync(
    topic: str,
    llm_client: Any = None,
    max_rounds: int = 5,
) -> DeliberationResult:
    """同步版本的 deliberate"""
    import asyncio

    return asyncio.run(deliberate(topic, llm_client, max_rounds))
