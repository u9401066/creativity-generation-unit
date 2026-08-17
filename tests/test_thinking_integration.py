"""
測試 ThinkingEngine 整合

驗證三種思考模式：
1. Simple - 快速單次
2. Deep - Multi-Agent 並發
3. Spark - 概念碰撞
"""

import asyncio
import sys

sys.path.insert(0, "src")


async def test_langgraph_functional_entrypoint_accepts_serializable_input():
    """Regression: LangGraph 1.x entrypoints receive one input object."""
    from cgu.graph.builder_functional import run_cgu_functional

    result = await run_cgu_functional(
        "auditable academic writing",
        creativity_level=2,
        target_count=3,
        pattern="explore",
    )

    assert result["topic"] == "auditable academic writing"
    assert result["creativity_level"] == "L2_EXPLORATORY"
    assert result["pattern"] == "explore"
    assert len(result["ideas"]) == 3


async def test_simple_mode():
    """測試簡單模式（Copilot 框架）"""
    print("\n" + "=" * 60)
    print("🚀 測試 Simple 模式（Copilot 框架）")
    print("=" * 60)

    from cgu.thinking import ThinkingConfig, ThinkingEngine, ThinkingMode

    config = ThinkingConfig()
    engine = ThinkingEngine(config=config)
    engine.set_copilot_mode(True)  # 模擬 Copilot 模式

    result = await engine.think(
        topic="AI 在教育領域的應用",
        mode=ThinkingMode.SIMPLE,
    )

    print(f"\n模式: {result.mode_used}")
    print(f"主題: {result.topic}")
    print(f"點子數量: {len(result.ideas)}")
    print("\n生成的框架：")
    for idea in result.ideas[:3]:
        print(f"  - {idea['content']}")
        if "hint" in idea:
            print(f"    提示: {idea['hint']}")

    return result


async def test_deep_mode():
    """測試深度模式（Multi-Agent）"""
    print("\n" + "=" * 60)
    print("🧠 測試 Deep 模式（Multi-Agent 並發）")
    print("=" * 60)

    from cgu.thinking import ThinkingEngine, ThinkingMode

    engine = ThinkingEngine()

    result = await engine.think(
        topic="未來教育模式",
        mode=ThinkingMode.DEEP,
        agent_count=3,
        thinking_steps=2,
        collision_count=3,
    )

    print(f"\n模式: {result.mode_used}")
    print(f"主題: {result.topic}")
    print(f"點子數量: {len(result.ideas)}")
    print(f"火花數量: {len(result.sparks)}")

    print("\nAgent 貢獻：")
    for contrib in result.agent_contributions:
        print(f"  - {contrib['personality']}: {contrib['idea_count']} 個點子")

    print("\n最佳點子：")
    for idea in result.best_ideas[:3]:
        source = idea.get("source", "unknown")
        print(f"  - [{source}] {idea['content'][:50]}...")

    if result.best_spark:
        print(f"\n最佳火花 (值={result.best_spark['spark_value']:.2f}):")
        print(f"  {result.best_spark['content']}")

    return result


async def test_spark_mode():
    """測試火花模式（概念碰撞）"""
    print("\n" + "=" * 60)
    print("⚡ 測試 Spark 模式（概念碰撞）")
    print("=" * 60)

    from cgu.thinking import ThinkingEngine, ThinkingMode

    engine = ThinkingEngine()

    result = await engine.think(
        topic="咖啡 × 程式設計",
        mode=ThinkingMode.SPARK,
        collision_count=5,
    )

    print(f"\n模式: {result.mode_used}")
    print(f"主題: {result.topic}")
    print(f"火花數量: {len(result.sparks)}")

    print("\n火花列表：")
    for spark in result.sparks[:3]:
        print(f"  ⚡ ({spark.get('spark_value', 0):.2f}) {spark['content']}")

    return result


async def test_hybrid_mode():
    """測試混合模式（快思 + 慢想）"""
    print("\n" + "=" * 60)
    print("🔄 測試 Hybrid 模式（快思慢想）")
    print("=" * 60)

    from cgu.thinking import ThinkingEngine, ThinkingMode

    engine = ThinkingEngine()

    result = await engine.think(
        topic="智慧城市",
        mode=ThinkingMode.HYBRID,
    )

    print(f"\n模式: {result.mode_used}")
    print(f"主題: {result.topic}")
    print(f"總點子數: {len(result.ideas)}")
    print(f"火花數量: {len(result.sparks)}")
    print(f"執行時間: {result.total_time_ms}ms")

    print("\n推理過程：")
    for chain in result.reasoning_chains:
        print(f"  [{chain.get('phase', 'unknown')}] {chain.get('output', '')}")

    print("\n最佳點子 Top 3：")
    for i, idea in enumerate(result.best_ideas[:3], 1):
        content = idea["content"][:60] if len(idea["content"]) > 60 else idea["content"]
        print(f"  {i}. {content}")

    return result


async def test_facade():
    """測試 Facade 便捷函數"""
    print("\n" + "=" * 60)
    print("🎯 測試 Facade 便捷函數")
    print("=" * 60)

    from cgu.thinking import quick_think, think

    # quick_think
    print("\n📌 quick_think:")
    ideas = await quick_think("環保創新", count=3)
    for idea in ideas:
        print(f"  - {idea['content']}")

    # think with depth
    print("\n📌 think (medium depth):")
    result = await think("遠距工作", depth="medium")
    print(f"  模式: {result['mode_used']}")
    print(f"  點子: {len(result['ideas'])} 個")

    return True


async def main():
    """主測試函數"""
    print("=" * 60)
    print("CGU ThinkingEngine 整合測試")
    print("=" * 60)

    try:
        await test_simple_mode()
        await test_deep_mode()
        await test_spark_mode()
        await test_hybrid_mode()
        await test_facade()

        print("\n" + "=" * 60)
        print("✅ 所有測試完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
