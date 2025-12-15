"""快速測試 LangGraph Agent"""
import asyncio
from cgu.graph import run_cgu
from cgu.core import CreativityLevel

async def test():
    result = await run_cgu(
        topic="未來的辦公空間",
        creativity_level=CreativityLevel.L1_COMBINATIONAL,
        target_count=3,
    )
    print("✅ LangGraph Agent 測試成功")
    print(f"  - Pattern: {result.get('pattern')}")
    print(f"  - Iterations: {result.get('iterations')}")
    print(f"  - Fast steps: {result.get('total_fast_steps')}")
    print(f"  - Slow steps: {result.get('total_slow_steps')}")
    print(f"  - Thinking steps: {result.get('thinking_steps')}")
    
    ideas = result.get("ideas", [])
    print(f"  - 最終點子: {len(ideas)}")
    print()
    for i, idea in enumerate(ideas[:5]):
        print(f"  💡 {i+1}. {idea.get('content', '?')} (score: {idea.get('score', 0):.2f})")

if __name__ == "__main__":
    asyncio.run(test())
