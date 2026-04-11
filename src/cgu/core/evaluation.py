"""
EvaluationEngine - LLM 驅動的創意品質評估引擎

核心理念：
- 品質指標必須有意義，不是隨機數字
- 使用 LLM 進行語意層級的評估（而非字元集合差異）
- 實作 NUS 模型：Novelty × Usefulness × Surprise

無 LLM 時使用改良版啟發式（基於文本特徵而非隨機數）
"""

from __future__ import annotations

import logging
import re
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

try:
    from cgu.llm import SYSTEM_PROMPT_EVALUATION
except ImportError:
    SYSTEM_PROMPT_EVALUATION = None


# ── 評估模型 ──────────────────────────────────────────────


class CreativityScore(BaseModel):
    """單一想法的創意評分"""

    novelty: float = Field(default=0.0, ge=0.0, le=1.0, description="新穎度：是否提出了不常見的觀點？")
    usefulness: float = Field(default=0.0, ge=0.0, le=1.0, description="實用度：是否可行且有價值？")
    surprise: float = Field(default=0.0, ge=0.0, le=1.0, description="驚喜度：是否出乎意料？")
    specificity: float = Field(default=0.0, ge=0.0, le=1.0, description="具體性：是否足夠具體可執行？")
    reasoning: str = Field(default="", description="評估推理過程")

    @property
    def nus_score(self) -> float:
        """NUS 模型：Novelty × Usefulness × Surprise"""
        return self.novelty * self.usefulness * self.surprise

    @property
    def overall(self) -> float:
        """綜合分數（加權平均）"""
        return (
            self.novelty * 0.3
            + self.usefulness * 0.25
            + self.surprise * 0.25
            + self.specificity * 0.2
        )


class ComparisonResult(BaseModel):
    """兩個想法的比較結果"""

    idea_a: str
    idea_b: str
    winner: str = Field(description="哪個更有創意：'a'、'b' 或 'tie'")
    reason: str = Field(default="", description="判斷理由")
    novelty_delta: float = Field(default=0.0, description="新穎度差異")


class EvaluationReport(BaseModel):
    """完整的評估報告"""

    topic: str
    scores: list[CreativityScore] = Field(default_factory=list)
    ranking: list[int] = Field(default_factory=list, description="按品質排序的索引")
    best_idea_index: int = Field(default=0)
    summary: str = Field(default="")


# ── 評估引擎 ──────────────────────────────────────────────


_EVALUATE_PROMPT = """你是一位創意品質評估專家。請為以下想法評分。

主題：{topic}
想法：{idea}

請在 0-10 分範圍內評估以下四個維度：
1. 新穎度（Novelty）：這個想法是否提出了不常見的觀點或方法？
2. 實用度（Usefulness）：這個想法是否可行且有實際價值？
3. 驚喜度（Surprise）：這個想法是否出乎意料、令人眼前一亮？
4. 具體性（Specificity）：這個想法是否足夠具體，可以付諸執行？

請用 JSON 格式回答：
{{"novelty": 0-10, "usefulness": 0-10, "surprise": 0-10, "specificity": 0-10, "reasoning": "評估理由"}}"""

_COMPARE_PROMPT = """你是一位創意品質評估專家。請比較以下兩個想法的創意品質。

主題：{topic}
想法 A：{idea_a}
想法 B：{idea_b}

哪個更有創意？請說明理由。
回答格式：先說勝者（A 或 B 或平手），再說理由。"""


class EvaluationEngine:
    """
    創意品質評估引擎

    使用 LLM 進行語意層級的品質評估，
    無 LLM 時使用基於文本特徵的啟發式評估。
    """

    def __init__(self, llm_client: Any = None) -> None:
        self.llm = llm_client

    async def evaluate(self, idea: str, topic: str) -> CreativityScore:
        """評估單一想法的創意品質"""
        if self.llm:
            return await self._evaluate_with_llm(idea, topic)
        return self._evaluate_heuristic(idea, topic)

    async def evaluate_batch(
        self, ideas: list[str], topic: str
    ) -> EvaluationReport:
        """批量評估並排序"""
        scores = [await self.evaluate(idea, topic) for idea in ideas]

        ranked = sorted(
            range(len(scores)),
            key=lambda i: scores[i].overall,
            reverse=True,
        )

        best_idx = ranked[0] if ranked else 0
        summary = self._generate_summary(ideas, scores, ranked, topic)

        return EvaluationReport(
            topic=topic,
            scores=scores,
            ranking=ranked,
            best_idea_index=best_idx,
            summary=summary,
        )

    async def compare(
        self, idea_a: str, idea_b: str, topic: str
    ) -> ComparisonResult:
        """比較兩個想法"""
        if self.llm:
            return await self._compare_with_llm(idea_a, idea_b, topic)
        return self._compare_heuristic(idea_a, idea_b, topic)

    # ── LLM 評估 ──

    async def _evaluate_with_llm(
        self, idea: str, topic: str
    ) -> CreativityScore:
        """使用 LLM 評估"""
        prompt = _EVALUATE_PROMPT.format(topic=topic, idea=idea)
        system = SYSTEM_PROMPT_EVALUATION or "你是一位嚴謹的創意品質評估專家。"
        try:
            # CGULLMClient.generate() 是同步的
            response = self.llm.generate(
                prompt=prompt, system_prompt=system, temperature=0.3
            )
            return self._parse_llm_score(response)
        except Exception as e:
            logger.warning("LLM 評估失敗，降級為啟發式：%s", e)
            return self._evaluate_heuristic(idea, topic)

    async def _compare_with_llm(
        self, idea_a: str, idea_b: str, topic: str
    ) -> ComparisonResult:
        """使用 LLM 比較"""
        prompt = _COMPARE_PROMPT.format(
            topic=topic, idea_a=idea_a, idea_b=idea_b
        )
        system = SYSTEM_PROMPT_EVALUATION or "你是一位嚴謹的創意品質評估專家。"
        try:
            # CGULLMClient.generate() 是同步的
            response = self.llm.generate(
                prompt=prompt, system_prompt=system, temperature=0.3
            )
            winner = "tie"
            if "A" in response[:20].upper():
                winner = "a"
            elif "B" in response[:20].upper():
                winner = "b"
            return ComparisonResult(
                idea_a=idea_a,
                idea_b=idea_b,
                winner=winner,
                reason=response.strip(),
            )
        except Exception as e:
            logger.warning("LLM 比較失敗，降級為啟發式：%s", e)
            return self._compare_heuristic(idea_a, idea_b, topic)

    def _parse_llm_score(self, response: str) -> CreativityScore:
        """解析 LLM 回傳的評分"""
        import json

        try:
            # 嘗試從回應中提取 JSON
            json_match = re.search(r"\{[^}]+\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return CreativityScore(
                    novelty=min(1.0, data.get("novelty", 5) / 10),
                    usefulness=min(1.0, data.get("usefulness", 5) / 10),
                    surprise=min(1.0, data.get("surprise", 5) / 10),
                    specificity=min(1.0, data.get("specificity", 5) / 10),
                    reasoning=data.get("reasoning", ""),
                )
        except (json.JSONDecodeError, ValueError):
            pass
        # 解析失敗時返回中等分數
        return CreativityScore(
            novelty=0.5,
            usefulness=0.5,
            surprise=0.5,
            specificity=0.5,
            reasoning=f"LLM 回應解析失敗，使用預設分數。原始回應：{response[:100]}",
        )

    # ── 啟發式評估 ──

    def _evaluate_heuristic(self, idea: str, topic: str) -> CreativityScore:
        """
        基於文本特徵的啟發式評估

        比隨機數有意義：
        - 新穎度：詞彙多樣性 + 是否包含跨域概念
        - 實用度：是否包含動作詞和具體名詞
        - 驚喜度：是否包含轉折詞、類比或反直覺表達
        - 具體性：長度、數字/步驟的存在
        """
        words = re.split(r"[\s,，、。！？：；\n]+", idea)
        words = [w for w in words if w]
        word_count = len(words)
        unique_words = len(set(words))

        # 新穎度：詞彙多樣性（unique/total ratio）
        diversity = unique_words / max(word_count, 1)
        cross_domain_markers = [
            "如同", "像", "類比", "借鏡", "跨", "結合", "融合",
            "just like", "analogy", "cross", "combine",
        ]
        has_cross_domain = any(m in idea for m in cross_domain_markers)
        novelty = min(1.0, diversity * 0.7 + (0.3 if has_cross_domain else 0.0))

        # 實用度：包含動作詞和具體名詞
        action_markers = [
            "可以", "應該", "建立", "開發", "設計", "實作",
            "create", "build", "design", "implement", "use",
        ]
        action_count = sum(1 for m in action_markers if m in idea)
        usefulness = min(1.0, 0.3 + action_count * 0.15)

        # 驚喜度：轉折詞、反直覺表達
        surprise_markers = [
            "但是", "然而", "意外", "反而", "竟然", "不是…而是",
            "however", "surprisingly", "instead", "counter",
        ]
        surprise_count = sum(1 for m in surprise_markers if m in idea)
        surprise = min(1.0, 0.2 + surprise_count * 0.2 + (0.2 if has_cross_domain else 0.0))

        # 具體性：長度 + 數字/步驟
        length_score = min(1.0, word_count / 30)
        has_numbers = bool(re.search(r"\d+", idea))
        has_steps = any(m in idea for m in ["步驟", "第一", "第二", "1.", "2.", "首先"])
        specificity = min(
            1.0, length_score * 0.5 + (0.25 if has_numbers else 0.0) + (0.25 if has_steps else 0.0)
        )

        return CreativityScore(
            novelty=round(novelty, 3),
            usefulness=round(usefulness, 3),
            surprise=round(surprise, 3),
            specificity=round(specificity, 3),
            reasoning="啟發式評估：基於詞彙多樣性、動作詞、轉折詞、具體度",
        )

    def _compare_heuristic(
        self, idea_a: str, idea_b: str, topic: str
    ) -> ComparisonResult:
        """啟發式比較"""
        score_a = self._evaluate_heuristic(idea_a, topic)
        score_b = self._evaluate_heuristic(idea_b, topic)

        if score_a.overall > score_b.overall + 0.05:
            winner = "a"
        elif score_b.overall > score_a.overall + 0.05:
            winner = "b"
        else:
            winner = "tie"

        return ComparisonResult(
            idea_a=idea_a,
            idea_b=idea_b,
            winner=winner,
            reason=f"A={score_a.overall:.2f} vs B={score_b.overall:.2f}",
            novelty_delta=score_a.novelty - score_b.novelty,
        )

    # ── 報告生成 ──

    def _generate_summary(
        self,
        ideas: list[str],
        scores: list[CreativityScore],
        ranking: list[int],
        topic: str,
    ) -> str:
        """生成評估摘要"""
        if not ideas:
            return "無想法可評估"

        best_idx = ranking[0]
        best_score = scores[best_idx]
        lines = [
            f"主題：{topic}",
            f"評估了 {len(ideas)} 個想法",
            f"最佳：#{best_idx + 1}（綜合={best_score.overall:.0%}）",
            f"  新穎度={best_score.novelty:.0%}"
            f"  實用度={best_score.usefulness:.0%}"
            f"  驚喜度={best_score.surprise:.0%}"
            f"  具體性={best_score.specificity:.0%}",
        ]
        return "\n".join(lines)

    def format_report(self, report: EvaluationReport) -> str:
        """格式化評估報告"""
        lines = [
            "═" * 60,
            "📊 創意品質評估報告",
            "═" * 60,
            "",
            report.summary,
            "",
        ]
        for rank, idx in enumerate(report.ranking, 1):
            score = report.scores[idx]
            lines.extend([
                "─" * 60,
                f"#{rank} 綜合={score.overall:.0%}"
                f"  N={score.novelty:.0%}"
                f"  U={score.usefulness:.0%}"
                f"  S={score.surprise:.0%}"
                f"  Sp={score.specificity:.0%}",
                f"   {score.reasoning[:80]}",
            ])
        lines.append("═" * 60)
        return "\n".join(lines)


# ── 便捷函數 ──────────────────────────────────────────────


async def evaluate_idea(
    idea: str, topic: str, llm_client: Any = None
) -> CreativityScore:
    """快速評估單一想法"""
    engine = EvaluationEngine(llm_client)
    return await engine.evaluate(idea, topic)


async def rank_ideas(
    ideas: list[str], topic: str, llm_client: Any = None
) -> EvaluationReport:
    """快速排序多個想法"""
    engine = EvaluationEngine(llm_client)
    return await engine.evaluate_batch(ideas, topic)
