"""
CGU v3: Agent-Driven Creativity Tools 測試

測試五大工具類別及統一工具箱：
1. ConceptExplorer - 概念搜尋器
2. ConnectionFinder - 連結發現器
3. NoveltyChecker - 新穎度驗證器
4. IdeaEvolver - 想法演化器
5. CreativityLogger - 創意記錄器
6. CreativityToolbox - 統一工具箱

以及 MCP Tool 註冊後的整合測試。
"""

import pytest

from cgu.tools import (
    ConceptExplorer,
    ConceptSearchResult,
    Connection,
    ConnectionFinder,
    CreativityLogger,
    CreativityToolbox,
    Evolution,
    IdeaEvolver,
    NoveltyChecker,
    NoveltyReport,
)

# ============================================================
# ConceptExplorer 測試
# ============================================================


class TestConceptExplorer:
    """概念搜尋器測試"""

    def test_search_known_concept(self):
        """搜尋已知概念應返回相關結果"""
        explorer = ConceptExplorer()
        result = explorer.search("AI")

        assert isinstance(result, ConceptSearchResult)
        assert result.query == "AI"
        assert len(result.found_concepts) > 0
        assert len(result.related_domains) > 0

    def test_search_with_cross_domain(self):
        """啟用跨域搜尋應包含意外發現"""
        explorer = ConceptExplorer()
        result = explorer.search("AI", include_cross_domain=True)

        assert len(result.unexpected_finds) > 0

    def test_search_without_cross_domain(self):
        """停用跨域搜尋不應包含意外發現"""
        explorer = ConceptExplorer()
        result = explorer.search("AI", include_cross_domain=False)

        assert len(result.unexpected_finds) == 0

    def test_search_unknown_concept(self):
        """搜尋未知概念仍應返回結構化結果"""
        explorer = ConceptExplorer()
        result = explorer.search("量子糾纏")

        assert isinstance(result, ConceptSearchResult)
        assert result.query == "量子糾纏"

    def test_fuzzy_search(self):
        """模糊搜尋能匹配部分關鍵字"""
        explorer = ConceptExplorer()
        # "程式" is a substring of "程式設計" in the knowledge base
        result = explorer.search("程式")

        assert len(result.found_concepts) > 0

    def test_random_concept(self):
        """隨機概念應返回知識庫中的概念"""
        explorer = ConceptExplorer()
        concept = explorer.random_concept()

        assert isinstance(concept, str)
        assert concept in explorer.knowledge_base

    def test_random_concept_with_exclude(self):
        """排除某些概念後仍能返回"""
        explorer = ConceptExplorer()
        exclude = ["AI", "程式設計"]
        concept = explorer.random_concept(exclude=exclude)

        assert concept not in exclude

    def test_results_are_deduplicated(self):
        """搜尋結果應去重"""
        explorer = ConceptExplorer()
        result = explorer.search("AI")

        assert len(result.found_concepts) == len(set(result.found_concepts))
        assert len(result.unexpected_finds) == len(set(result.unexpected_finds))


# ============================================================
# ConnectionFinder 測試
# ============================================================


class TestConnectionFinder:
    """連結發現器測試"""

    def test_find_direct_connection(self):
        """應找到直接連結"""
        finder = ConnectionFinder()
        result = finder.find_connection("AI", "機器學習")

        assert isinstance(result, Connection)
        assert result.connection_type == "direct"
        assert result.novelty_score == pytest.approx(0.2)

    def test_find_unexpected_connection(self):
        """應找到跨域連結"""
        finder = ConnectionFinder()
        result = finder.find_connection("AI", "創意")

        assert isinstance(result, Connection)
        assert result.connection_type == "unexpected"
        assert result.novelty_score == pytest.approx(0.8)

    def test_find_unexplored_connection(self):
        """完全無關概念應返回未探索連結"""
        finder = ConnectionFinder()
        result = finder.find_connection("量子力學", "烹飪藝術")

        assert isinstance(result, Connection)
        assert result.connection_type == "unexplored"
        assert result.novelty_score == pytest.approx(0.95)

    def test_connection_caching(self):
        """相同查詢應使用快取"""
        finder = ConnectionFinder()
        result1 = finder.find_connection("AI", "創意")
        result2 = finder.find_connection("AI", "創意")

        assert result1 is result2

    def test_suggest_bridge_with_common(self):
        """應建議橋接概念"""
        finder = ConnectionFinder()
        bridges = finder.suggest_bridge("AI", "教育")

        assert isinstance(bridges, list)

    def test_suggest_bridge_no_common(self):
        """無共同概念時仍應建議跨域概念"""
        finder = ConnectionFinder()
        bridges = finder.suggest_bridge("未知A", "未知B")

        assert isinstance(bridges, list)

    def test_connection_has_explanation(self):
        """連結應包含解釋"""
        finder = ConnectionFinder()
        result = finder.find_connection("AI", "教育")

        assert result is not None
        assert len(result.explanation) > 0


# ============================================================
# NoveltyChecker 測試
# ============================================================


class TestNoveltyChecker:
    """新穎度驗證器測試"""

    def test_check_common_idea(self):
        """常見想法應低新穎度"""
        checker = NoveltyChecker()
        result = checker.check("用 AI 寫程式碼 自動化")

        assert isinstance(result, NoveltyReport)
        assert result.novelty_score < 0.7
        assert len(result.similar_existing) > 0

    def test_check_novel_idea(self):
        """獨特想法應高新穎度"""
        checker = NoveltyChecker()
        result = checker.check("用蘑菇菌絲體建造月球基地")

        assert result.is_novel is True
        assert result.novelty_score > 0.6

    def test_differentiation_suggestions(self):
        """低新穎度想法應包含差異化建議"""
        checker = NoveltyChecker()
        result = checker.check("AI 程式 自動化")

        if not result.is_novel:
            assert len(result.differentiation_suggestions) > 0

    def test_add_existing_idea(self):
        """新增已知想法後應影響後續檢查"""
        checker = NoveltyChecker()
        checker.add_existing_idea(
            "用蘑菇建太空站",
            ["蘑菇", "太空站", "建造"],
        )

        result = checker.check("蘑菇 建造 太空站")
        assert len(result.similar_existing) > 0

    def test_novelty_score_range(self):
        """新穎度分數應在 0-1 之間"""
        checker = NoveltyChecker()
        result = checker.check("任何想法測試")

        assert 0.0 <= result.novelty_score <= 1.0


# ============================================================
# IdeaEvolver 測試
# ============================================================


class TestIdeaEvolver:
    """想法演化器測試"""

    def test_mutate_combine(self):
        """combine 突變應結合隨機概念"""
        evolver = IdeaEvolver()
        result = evolver.mutate("用 AI 教學", "combine")

        assert isinstance(result, Evolution)
        assert result.mutation_type == "combine"
        assert result.original == "用 AI 教學"
        assert result.evolved != result.original

    def test_mutate_split(self):
        """split 突變應聚焦特定維度"""
        evolver = IdeaEvolver()
        result = evolver.mutate("改善線上學習", "split")

        assert result.mutation_type == "split"
        assert "特別針對" in result.evolved

    def test_mutate_reverse(self):
        """reverse 突變應反向思考"""
        evolver = IdeaEvolver()
        result = evolver.mutate("增加互動", "reverse")

        assert result.mutation_type == "reverse"
        assert "反面" in result.evolved

    def test_mutate_analogize(self):
        """analogize 突變應借用其他領域"""
        evolver = IdeaEvolver()
        result = evolver.mutate("團隊協作", "analogize")

        assert result.mutation_type == "analogize"
        assert "角度" in result.evolved

    def test_mutate_extreme(self):
        """extreme 突變應極端化"""
        evolver = IdeaEvolver()
        result = evolver.mutate("每天學習", "extreme")

        assert result.mutation_type == "extreme"

    def test_mutate_random(self):
        """不指定突變類型應隨機選擇"""
        evolver = IdeaEvolver()
        result = evolver.mutate("創意想法")

        assert result.mutation_type in ["combine", "split", "reverse", "analogize", "extreme"]

    def test_evolution_has_reasoning(self):
        """每次突變都應有推理說明"""
        evolver = IdeaEvolver()
        for mutation_type in ["combine", "split", "reverse", "analogize", "extreme"]:
            result = evolver.mutate("測試想法", mutation_type)
            assert len(result.reasoning) > 0


# ============================================================
# CreativityLogger 測試
# ============================================================


class TestCreativityLogger:
    """創意記錄器測試"""

    def test_start_session(self):
        """應能開始新會話"""
        logger = CreativityLogger()
        session_id = logger.start_session("測試主題")

        assert isinstance(session_id, str)
        assert len(session_id) == 8
        assert logger.current_session is not None
        assert logger.current_session.topic == "測試主題"

    def test_log_exploration(self):
        """應能記錄探索動作"""
        logger = CreativityLogger()
        logger.start_session("測試")
        logger.log_exploration("search", {"result": "test"})

        assert len(logger.current_session.explorations) == 1

    def test_log_idea(self):
        """應能記錄想法"""
        logger = CreativityLogger()
        logger.start_session("測試")
        logger.log_idea("好想法", novelty_score=0.8)

        assert len(logger.current_session.ideas_generated) == 1
        assert logger.current_session.best_idea == "好想法"
        assert logger.current_session.best_novelty_score == 0.8

    def test_best_idea_tracking(self):
        """應追蹤最佳想法"""
        logger = CreativityLogger()
        logger.start_session("測試")
        logger.log_idea("普通想法", novelty_score=0.3)
        logger.log_idea("好想法", novelty_score=0.9)
        logger.log_idea("還行的想法", novelty_score=0.5)

        assert logger.current_session.best_idea == "好想法"
        assert logger.current_session.best_novelty_score == 0.9

    def test_session_summary(self):
        """應能取得會話摘要"""
        logger = CreativityLogger()
        logger.start_session("測試主題")
        logger.log_exploration("test", {})
        logger.log_idea("想法1", 0.5)

        summary = logger.get_session_summary()
        assert summary["topic"] == "測試主題"
        assert summary["total_explorations"] == 1
        assert summary["total_ideas"] == 1

    def test_empty_session_summary(self):
        """無會話時摘要應為空 dict"""
        logger = CreativityLogger()
        summary = logger.get_session_summary()

        assert summary == {}

    def test_exploration_history(self):
        """應能取得探索歷史"""
        logger = CreativityLogger()
        logger.start_session("測試")
        logger.log_exploration("step1", "result1")
        logger.log_exploration("step2", "result2")

        history = logger.get_exploration_history()
        assert len(history) == 2

    def test_multiple_sessions(self):
        """應能管理多個會話"""
        logger = CreativityLogger()
        id1 = logger.start_session("主題1")
        id2 = logger.start_session("主題2")

        assert id1 != id2
        assert len(logger.sessions) == 2


# ============================================================
# CreativityToolbox 整合測試
# ============================================================


class TestCreativityToolbox:
    """統一工具箱整合測試"""

    def test_toolbox_initialization(self):
        """工具箱應正確初始化所有元件"""
        toolbox = CreativityToolbox()

        assert isinstance(toolbox.concept_explorer, ConceptExplorer)
        assert isinstance(toolbox.connection_finder, ConnectionFinder)
        assert isinstance(toolbox.novelty_checker, NoveltyChecker)
        assert isinstance(toolbox.idea_evolver, IdeaEvolver)
        assert isinstance(toolbox.logger, CreativityLogger)

    def test_explore_concept_returns_dict(self):
        """explore_concept 應返回 dict"""
        toolbox = CreativityToolbox()
        result = toolbox.explore_concept("AI")

        assert isinstance(result, dict)
        assert "query" in result
        assert "related" in result
        assert "unexpected" in result

    def test_find_connection_returns_dict(self):
        """find_connection 應返回 dict"""
        toolbox = CreativityToolbox()
        result = toolbox.find_connection("AI", "教育")

        assert isinstance(result, dict)
        assert "connection_type" in result
        assert "novelty_score" in result

    def test_check_novelty_returns_dict(self):
        """check_novelty 應返回 dict"""
        toolbox = CreativityToolbox()
        result = toolbox.check_novelty("創新教育方式")

        assert isinstance(result, dict)
        assert "is_novel" in result
        assert "novelty_score" in result

    def test_evolve_idea_returns_dict(self):
        """evolve_idea 應返回 dict"""
        toolbox = CreativityToolbox()
        result = toolbox.evolve_idea("用 AI 教學")

        assert isinstance(result, dict)
        assert "original" in result
        assert "evolved" in result
        assert "mutation_type" in result

    def test_get_random_concept_returns_string(self):
        """get_random_concept 應返回字串"""
        toolbox = CreativityToolbox()
        result = toolbox.get_random_concept()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_suggest_bridges_returns_list(self):
        """suggest_bridges 應返回列表"""
        toolbox = CreativityToolbox()
        result = toolbox.suggest_bridges("AI", "藝術")

        assert isinstance(result, list)

    def test_session_workflow(self):
        """完整的會話工作流程測試"""
        toolbox = CreativityToolbox()

        # 1. 開始會話
        session_id = toolbox.start_session("用 AI 改善教育")
        assert isinstance(session_id, str)

        # 2. 探索概念
        exploration = toolbox.explore_concept("教育")
        assert len(exploration["related"]) > 0

        # 3. 尋找連結
        connection = toolbox.find_connection("AI", "教育")
        assert "connection_type" in connection

        # 4. 產生想法
        evolved = toolbox.evolve_idea("AI 個人化學習", "combine")
        assert evolved["mutation_type"] == "combine"

        # 5. 記錄想法
        record = toolbox.record_idea(evolved["evolved"])
        assert "novelty_score" in record

        # 6. 查看進度
        progress = toolbox.get_progress()
        assert progress["total_ideas"] >= 1
        assert progress["total_explorations"] >= 2  # explore + find_connection

    def test_toolbox_logs_explorations(self):
        """工具箱操作應自動記錄到 logger"""
        toolbox = CreativityToolbox()
        toolbox.start_session("測試")

        toolbox.explore_concept("AI")
        toolbox.find_connection("AI", "教育")
        toolbox.check_novelty("新想法")
        toolbox.evolve_idea("想法", "reverse")

        history = toolbox.get_history()
        assert len(history) == 4


# ============================================================
# MCP Tool 整合測試（直接呼叫 async 函數）
# ============================================================


class TestMCPToolIntegration:
    """MCP Tool 註冊後的整合測試"""

    @pytest.mark.asyncio
    async def test_mcp_explore_concept(self):
        """MCP explore_concept 工具"""
        from cgu.server import explore_concept

        result = await explore_concept("AI")
        assert isinstance(result, dict)
        assert result["query"] == "AI"
        assert "related" in result

    @pytest.mark.asyncio
    async def test_mcp_find_connections(self):
        """MCP find_connections 工具"""
        from cgu.server import find_connections

        result = await find_connections("AI", "創意")
        assert isinstance(result, dict)
        assert "connection_type" in result
        assert "novelty_score" in result

    @pytest.mark.asyncio
    async def test_mcp_check_novelty(self):
        """MCP check_novelty 工具"""
        from cgu.server import check_novelty

        result = await check_novelty("用蘑菇建太空站")
        assert isinstance(result, dict)
        assert "is_novel" in result
        assert "novelty_score" in result

    @pytest.mark.asyncio
    async def test_mcp_evolve_idea_tool(self):
        """MCP evolve_idea_tool 工具"""
        from cgu.server import evolve_idea_tool

        result = await evolve_idea_tool("AI 教學", "reverse")
        assert isinstance(result, dict)
        assert result["mutation_type"] == "reverse"

    @pytest.mark.asyncio
    async def test_mcp_evolve_idea_tool_random(self):
        """MCP evolve_idea_tool 不指定突變類型"""
        from cgu.server import evolve_idea_tool

        result = await evolve_idea_tool("創新想法", "")
        assert isinstance(result, dict)
        assert result["mutation_type"] in ["combine", "split", "reverse", "analogize", "extreme"]

    @pytest.mark.asyncio
    async def test_mcp_random_concept(self):
        """MCP random_concept 工具"""
        from cgu.server import random_concept

        result = await random_concept()
        assert isinstance(result, dict)
        assert "concept" in result
        assert isinstance(result["concept"], str)

    @pytest.mark.asyncio
    async def test_mcp_suggest_bridges(self):
        """MCP suggest_bridges 工具"""
        from cgu.server import suggest_bridges

        result = await suggest_bridges("AI", "藝術")
        assert isinstance(result, dict)
        assert "bridges" in result
        assert isinstance(result["bridges"], list)

    @pytest.mark.asyncio
    async def test_mcp_session_workflow(self):
        """MCP 會話工作流程：start → record → progress"""
        from cgu.server import (
            creativity_session_progress,
            creativity_session_record,
            creativity_session_start,
        )

        # 開始會話
        start_result = await creativity_session_start("MCP 測試主題")
        assert "session_id" in start_result
        assert start_result["topic"] == "MCP 測試主題"

        # 記錄想法
        record_result = await creativity_session_record("MCP 生成的想法")
        assert "novelty_score" in record_result

        # 查看進度
        progress_result = await creativity_session_progress()
        assert progress_result["total_ideas"] >= 1
