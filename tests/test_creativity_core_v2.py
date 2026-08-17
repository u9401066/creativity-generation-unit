"""
測試 CGU v2 核心引擎

測試三大引擎：
1. AnalogyEngine - 跨領域類比
2. GraphTraversalEngine - 圖譜遍歷
3. AdversarialEngine - 對抗進化
4. CreativityCore - 整合引擎
"""

import asyncio

import pytest


class TestAnalogyEngine:
    """類比引擎測試"""

    def test_extract_structure(self):
        """測試結構抽取"""
        from cgu.core.analogy import AnalogyEngine

        engine = AnalogyEngine()
        structure = engine.extract_structure("軟體專案的技術債累積問題", domain="軟體開發")

        assert structure.domain == "軟體開發"
        assert "累積" in structure.patterns
        print(f"\n結構: {structure}")
        print(f"簽名: {structure.to_abstract_signature()}")

    def test_find_analogies(self):
        """測試類比搜尋"""
        from cgu.core.analogy import AnalogyEngine

        engine = AnalogyEngine()
        analogies = engine.find_analogies(
            problem="技術債累積導致系統維護成本增加",
            source_domain="軟體開發",
            max_analogies=3,
        )

        assert len(analogies) > 0
        print(f"\n找到 {len(analogies)} 個類比：")
        for a in analogies:
            print(f"  - {a.source_domain}: {a.insight[:50]}... (品質: {a.quality_score:.2f})")

    def test_explain_analogy(self):
        """測試類比解釋"""
        from cgu.core.analogy import AnalogyEngine

        engine = AnalogyEngine()
        analogies = engine.find_analogies(
            problem="遠端工作的孤獨感問題",
            max_analogies=1,
        )

        if analogies:
            explanation = engine.explain_analogy(analogies[0])
            print(f"\n{explanation}")


class TestGraphTraversalEngine:
    """圖譜遍歷引擎測試"""

    def test_shortest_path(self):
        """測試最短路徑"""
        from cgu.core.graph import get_graph_engine

        engine = get_graph_engine()
        path = engine.find_shortest_path("咖啡", "程式設計")

        if path:
            print(f"\n最短路徑: {path.to_string()}")
            print(f"跳數: {path.hop_count}")
        else:
            print("\n找不到直接路徑（這是正常的，概念可能不直接相連）")

    def test_creative_paths(self):
        """測試創意路徑"""
        from cgu.core.graph import get_graph_engine

        engine = get_graph_engine()
        paths = engine.find_creative_paths(
            source="咖啡",
            target="程式設計",
            max_paths=3,
        )

        print(f"\n找到 {len(paths)} 條創意路徑：")
        for i, path in enumerate(paths, 1):
            print(f"  {i}. {path.to_string()}")
            print(f"     新穎度: {path.novelty_score:.2f}, 品質: {path.quality_score:.2f}")

    def test_unexpected_connection(self):
        """測試意外連結"""
        from cgu.core.graph import find_connection

        result = find_connection("咖啡", "遠端工作")
        print("\n意外連結分析：")
        print(f"  驚喜度: {result.get('surprise_score', 0):.2f}")
        print(f"  洞察: {result.get('insight', '無')}")

    def test_explore_concept(self):
        """測試概念探索"""
        from cgu.core.graph import explore_concept

        result = explore_concept("咖啡", depth=2)
        print("\n從「咖啡」出發探索：")
        for depth, concepts in result.items():
            print(f"  {depth}: {concepts}")


class TestAdversarialEngine:
    """對抗式引擎測試"""

    @pytest.mark.asyncio
    async def test_adversarial_evolve(self):
        """測試對抗進化"""
        from cgu.core.adversarial import AdversarialEngine

        engine = AdversarialEngine()
        result = await engine.adversarial_evolve(
            initial_idea="用 AI 自動寫程式碼",
            topic="AI 程式設計輔助",
            max_rounds=3,
        )

        print("\n對抗進化結果：")
        print(f"  原始: {result.original_idea}")
        print(f"  最終: {result.final_idea}")
        print(f"  輪數: {result.total_rounds}")
        print(f"  新穎度提升: {result.novelty_improvement:.2f}")

        assert result.total_rounds > 0
        assert result.final_idea != result.original_idea

    def test_evolution_report(self):
        """測試進化報告"""
        from cgu.core.adversarial import AdversarialEngine, evolve_idea_sync

        result = evolve_idea_sync(
            idea="每天早上開會同步進度",
            topic="遠端團隊溝通",
            rounds=2,
        )

        engine = AdversarialEngine()
        report = engine.format_evolution_report(result)
        print(f"\n{report}")


class TestCreativityCore:
    """統一創意引擎測試"""

    @pytest.mark.asyncio
    async def test_analogy_mode(self):
        """測試類比模式"""
        from cgu.core.creativity_core import CreativityCore, CreativityMode

        core = CreativityCore()
        result = await core.generate(
            topic="軟體開發中的技術債問題",
            mode=CreativityMode.ANALOGY,
            source_domain="軟體開發",
        )

        print("\n類比模式結果：")
        print(f"  找到 {len(result.analogies)} 個類比")
        if result.best_analogy:
            print(f"  最佳類比: {result.best_analogy['source_domain']}")
            print(f"  洞察: {result.best_analogy['insight']}")

    @pytest.mark.asyncio
    async def test_exploration_mode(self):
        """測試探索模式"""
        from cgu.core.creativity_core import CreativityCore, CreativityMode

        core = CreativityCore()
        result = await core.generate(
            topic="咖啡與專注力的關係",
            mode=CreativityMode.EXPLORATION,
        )

        print("\n探索模式結果：")
        print(f"  找到 {len(result.unexpected_connections)} 個意外連結")
        for insight in result.insights:
            print(f"  洞察: {insight}")

    @pytest.mark.asyncio
    async def test_adversarial_mode(self):
        """測試對抗模式"""
        from cgu.core.creativity_core import CreativityCore, CreativityMode

        core = CreativityCore()
        result = await core.generate(
            topic="提高遠端工作效率",
            mode=CreativityMode.ADVERSARIAL,
            initial_idea="每天開視訊會議同步",
        )

        print("\n對抗模式結果：")
        print(f"  進化輪數: {result.adversarial_rounds}")
        print(f"  最終想法: {result.evolved_idea[:100]}...")

    @pytest.mark.asyncio
    async def test_full_mode(self):
        """測試完整模式"""
        from cgu.core.creativity_core import CreativityCore, CreativityMode

        core = CreativityCore()
        result = await core.generate(
            topic="如何讓遠端工作更有歸屬感",
            mode=CreativityMode.FULL,
        )

        print("\n完整模式結果：")
        report = core.format_report(result)
        print(report)

        assert result.quality_score >= 0

    def test_sync_api(self):
        """測試同步 API"""
        from cgu.core.creativity_core import create_sync

        result = create_sync(
            topic="改善線上學習體驗",
            mode="analogy",
        )

        print("\n同步 API 結果：")
        print(f"  品質分數: {result.quality_score:.2f}")
        print(f"  洞察: {result.insights}")


# === 執行測試 ===

if __name__ == "__main__":
    print("=" * 60)
    print("CGU v2 核心引擎測試")
    print("=" * 60)

    # 類比引擎
    print("\n\n📚 1. AnalogyEngine 測試")
    print("-" * 40)
    test_analogy = TestAnalogyEngine()
    test_analogy.test_extract_structure()
    test_analogy.test_find_analogies()
    test_analogy.test_explain_analogy()

    # 圖譜引擎
    print("\n\n🕸️ 2. GraphTraversalEngine 測試")
    print("-" * 40)
    test_graph = TestGraphTraversalEngine()
    test_graph.test_shortest_path()
    test_graph.test_creative_paths()
    test_graph.test_unexpected_connection()
    test_graph.test_explore_concept()

    # 對抗引擎
    print("\n\n⚔️ 3. AdversarialEngine 測試")
    print("-" * 40)
    test_adversarial = TestAdversarialEngine()
    asyncio.run(test_adversarial.test_adversarial_evolve())
    test_adversarial.test_evolution_report()

    # 統一引擎
    print("\n\n🎨 4. CreativityCore 測試")
    print("-" * 40)
    test_core = TestCreativityCore()
    asyncio.run(test_core.test_analogy_mode())
    asyncio.run(test_core.test_exploration_mode())
    asyncio.run(test_core.test_adversarial_mode())
    asyncio.run(test_core.test_full_mode())
    test_core.test_sync_api()

    print("\n\n" + "=" * 60)
    print("✅ 所有測試完成！")
    print("=" * 60)
