"""測試 LLM 生成結構化輸出的詳細版"""
import os
os.environ["CGU_USE_LLM"] = "true"
os.environ["CGU_LLM_PROVIDER"] = "ollama"
os.environ["CGU_OLLAMA_MODEL"] = "qwen2.5:3b"

from cgu.llm import get_llm_client, ScamperOutput, SYSTEM_PROMPT_CREATIVITY, PROMPT_SCAMPER

print("=== LLM 詳細測試 ===")

client = get_llm_client()
print(f"Client type: {type(client)}")

topic = "遠距工作"
prompt = PROMPT_SCAMPER.format(topic=topic)
print(f"\nPrompt:\n{prompt[:300]}...")

print("\n調用 LLM 中...")
try:
    result = client.generate_structured(
        prompt=prompt,
        response_model=ScamperOutput,
        system_prompt=SYSTEM_PROMPT_CREATIVITY,
    )
    print(f"\n結果類型: {type(result)}")
    print(f"\nsubstitute: {repr(result.substitute)}")
    print(f"combine: {repr(result.combine)}")
    print(f"adapt: {repr(result.adapt)}")
    print(f"modify: {repr(result.modify)}")
    print(f"put_to_other_uses: {repr(result.put_to_other_uses)}")
    print(f"eliminate: {repr(result.eliminate)}")
    print(f"reverse: {repr(result.reverse)}")
    print(f"best_idea: {repr(result.best_idea)}")
except Exception as e:
    print(f"錯誤: {e}")
    import traceback
    traceback.print_exc()
