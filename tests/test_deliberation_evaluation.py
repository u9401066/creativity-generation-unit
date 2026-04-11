"""
測試 Deliberation Engine 和 Evaluation Engine

涵蓋：
- 多輪審議流程（framework 模式）
- 品質指標計算
- 品質停滯偵測
- 評估引擎（啟發式）
- 批量評估和排序
- 想法比較
"""

import asyncio
import pytest
from cgu.core.deliberation import (
    DeliberationEngine,
    DeliberationPhase,
    DeliberationResult,
    DeliberationRound,
    DeliberationSession,
    QualityMetrics,
    PHASE_ORDER,
    deliberate,
)
from cgu.core.evaluation import (
    EvaluationEngine,
    CreativityScore,
    ComparisonResult,
    EvaluationReport,
    evaluate_idea,
    rank_ideas,
)


# ═══ Deliberation Engine Tests ═══


class TestQualityMetrics:
    """品質指標測試"""

    def test_default_quality_is_zero(self):
        m = QualityMetrics()
        assert m.overall == 0.0

    def test_overall_is_weighted_average(self):
        m = QualityMetrics(novelty=1.0, depth=1.0, coherence=1.0, surprise=1.0)
        assert m.overall == pytest.approx(1.0)

    def test_partial_scores(self):
        m = QualityMetrics(novelty=0.8, depth=0.6, coherence=0.4, surprise=0.2)
        expected = 0.8 * 0.3 + 0.6 * 0.25 + 0.4 * 0.25 + 0.2 * 0.2
        assert m.overall == pytest.approx(expected)


class TestDeliberationSession:
    """審議會議測試"""

    def test_empty_session(self):
        s = DeliberationSession(topic="test")
        assert s.current_phase is None
        assert not s.is_quality_plateaued

    def test_quality_plateaued_needs_three_rounds(self):
        s = DeliberationSession(
            topic="test", quality_trajectory=[0.5, 0.51, 0.52]
        )
        assert s.is_quality_plateaued

    def test_quality_not_plateaued_when_improving(self):
        s = DeliberationSession(
            topic="test", quality_trajectory=[0.5, 0.6, 0.7]
        )
        assert not s.is_quality_plateaued


class TestDeliberationEngine:
    """多輪審議引擎測試"""

    @pytest.mark.asyncio
    async def test_full_deliberation_runs_all_phases(self):
        engine = DeliberationEngine(max_rounds=5)
        result = await engine.deliberate("如何讓遠端工作更有效率")

        assert result.total_rounds == 5
        assert result.session.status == "completed"
        assert len(result.session.rounds) == 5
        assert len(result.session.quality_trajectory) == 5

    @pytest.mark.asyncio
    async def test_phases_in_correct_order(self):
        engine = DeliberationEngine(max_rounds=5)
        result = await engine.deliberate("永續城市設計")

        for i, rnd in enumerate(result.session.rounds):
            assert rnd.phase == PHASE_ORDER[i]

    @pytest.mark.asyncio
    async def test_each_round_has_outputs(self):
        engine = DeliberationEngine(max_rounds=5)
        result = await engine.deliberate("AI 教育應用")

        for rnd in result.session.rounds:
            assert len(rnd.outputs) > 0

    @pytest.mark.asyncio
    async def test_framework_mode_returns_prompts(self):
        """無 LLM 時應返回框架提示"""
        engine = DeliberationEngine(llm_client=None)
        result = await engine.deliberate("創意城市")

        for rnd in result.session.rounds:
            assert rnd.framework_prompt is not None

    @pytest.mark.asyncio
    async def test_deliberation_respects_max_rounds(self):
        engine = DeliberationEngine(max_rounds=3)
        result = await engine.deliberate("短流程測試")

        assert result.total_rounds == 3

    @pytest.mark.asyncio
    async def test_idea_evolution_tracked(self):
        engine = DeliberationEngine(max_rounds=5)
        result = await engine.deliberate("食物浪費解決方案")

        assert len(result.idea_evolution) == result.total_rounds

    @pytest.mark.asyncio
    async def test_peak_quality_is_max(self):
        engine = DeliberationEngine(max_rounds=5)
        result = await engine.deliberate("智慧醫療")

        assert result.peak_quality == max(result.session.quality_trajectory)

    def test_format_report(self):
        engine = DeliberationEngine()
        result = DeliberationResult(
            session=DeliberationSession(
                topic="test",
                rounds=[
                    DeliberationRound(
                        round_number=1,
                        phase=DeliberationPhase.DIVERGE,
                        outputs=["idea 1", "idea 2"],
                        quality=QualityMetrics(novelty=0.7),
                    )
                ],
                quality_trajectory=[0.7],
            ),
            final_output="best idea",
            total_rounds=1,
            peak_quality=0.7,
        )
        report = engine.format_report(result)
        assert "審議報告" in report
        assert "test" in report


class TestDeliberationConvenience:
    """便捷函數測試"""

    @pytest.mark.asyncio
    async def test_deliberate_function(self):
        result = await deliberate("快速測試")
        assert isinstance(result, DeliberationResult)
        assert result.total_rounds > 0


# ═══ Evaluation Engine Tests ═══


class TestCreativityScore:
    """創意評分測試"""

    def test_nus_score(self):
        s = CreativityScore(novelty=0.8, usefulness=0.6, surprise=0.5)
        assert s.nus_score == pytest.approx(0.8 * 0.6 * 0.5)

    def test_overall_score(self):
        s = CreativityScore(
            novelty=0.8, usefulness=0.6, surprise=0.4, specificity=0.2
        )
        expected = 0.8 * 0.3 + 0.6 * 0.25 + 0.4 * 0.25 + 0.2 * 0.2
        assert s.overall == pytest.approx(expected)


class TestEvaluationEngine:
    """評估引擎測試"""

    @pytest.mark.asyncio
    async def test_evaluate_single_idea(self):
        engine = EvaluationEngine()
        score = await engine.evaluate(
            "建立一個跨領域的 AI 知識圖譜，結合醫療和教育數據",
            "AI 應用",
        )
        assert 0 <= score.novelty <= 1
        assert 0 <= score.usefulness <= 1
        assert 0 <= score.surprise <= 1
        assert 0 <= score.specificity <= 1

    @pytest.mark.asyncio
    async def test_heuristic_novelty_rewards_cross_domain(self):
        """包含跨域概念的想法應得到更高的新穎度分數"""
        engine = EvaluationEngine()
        cross_domain = await engine.evaluate(
            "將軍事戰略的迂迴戰術類比到市場行銷中",
            "行銷",
        )
        generic = await engine.evaluate(
            "做更多廣告投放來增加銷量",
            "行銷",
        )
        assert cross_domain.novelty > generic.novelty

    @pytest.mark.asyncio
    async def test_heuristic_usefulness_rewards_action_words(self):
        """包含動作詞的想法應得到更高的實用度分數"""
        engine = EvaluationEngine()
        actionable = await engine.evaluate(
            "可以建立一個自動化系統來設計和實作解決方案",
            "自動化",
        )
        vague = await engine.evaluate(
            "這東西不錯",
            "自動化",
        )
        assert actionable.usefulness > vague.usefulness

    @pytest.mark.asyncio
    async def test_heuristic_specificity_rewards_detail(self):
        """具體詳細的想法應得到更高的具體性分數"""
        engine = EvaluationEngine()
        detailed = await engine.evaluate(
            "第一步建立數據庫，第二步分析3000筆交易記錄，第三步產出報告",
            "數據分析",
        )
        brief = await engine.evaluate(
            "分析資料",
            "數據分析",
        )
        assert detailed.specificity > brief.specificity

    @pytest.mark.asyncio
    async def test_evaluate_batch(self):
        ideas = [
            "建立跨域知識圖譜結合醫療與教育",
            "做更多的廣告",
            "設計一個第一步收集數據第二步分析第三步決策的系統",
        ]
        engine = EvaluationEngine()
        report = await engine.evaluate_batch(ideas, "AI 應用")

        assert len(report.scores) == 3
        assert len(report.ranking) == 3
        assert report.summary

    @pytest.mark.asyncio
    async def test_compare_ideas(self):
        engine = EvaluationEngine()
        result = await engine.compare(
            "建立一個結合軍事戰略類比的創新行銷平台",
            "做更多廣告",
            "行銷",
        )
        assert result.winner in ("a", "b", "tie")

    @pytest.mark.asyncio
    async def test_rank_ideas_convenience(self):
        report = await rank_ideas(
            ["想法 A：結合設計思維", "想法 B：隨便做做"],
            "創新",
        )
        assert isinstance(report, EvaluationReport)

    @pytest.mark.asyncio
    async def test_evaluate_idea_convenience(self):
        score = await evaluate_idea("一個具體的可以建立的系統", "測試")
        assert isinstance(score, CreativityScore)


class TestEvaluationReport:
    """評估報告測試"""

    def test_format_report(self):
        engine = EvaluationEngine()
        report = EvaluationReport(
            topic="test",
            scores=[
                CreativityScore(novelty=0.8, usefulness=0.7, surprise=0.6, specificity=0.5),
                CreativityScore(novelty=0.3, usefulness=0.4, surprise=0.2, specificity=0.1),
            ],
            ranking=[0, 1],
            best_idea_index=0,
            summary="test summary",
        )
        text = engine.format_report(report)
        assert "品質評估報告" in text
        assert "test summary" in text
