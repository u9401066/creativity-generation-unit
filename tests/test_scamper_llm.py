"""測試 SCAMPER 方法的 LLM 結構化輸出 - LangChain + Ollama"""
import os
os.environ["CGU_USE_LLM"] = "true"
os.environ["CGU_LLM_PROVIDER"] = "ollama"
os.environ["CGU_OLLAMA_MODEL"] = "qwen2.5:3b"

from cgu.llm import get_llm_client, ScamperOutput, SYSTEM_PROMPT_CREATIVITY, PROMPT_SCAMPER

print("=== SCAMPER 結構化輸出測試 ===")
print("使用 LangChain with_structured_output")
print("=" * 50)

client = get_llm_client()
prompt = PROMPT_SCAMPER.format(topic="遠距工作")

print("調用 LLM 中...")
result = client.generate_structured(
    prompt=prompt,
    response_model=ScamperOutput,
    system_prompt=SYSTEM_PROMPT_CREATIVITY,
)

print("\n=== SCAMPER 結果 ===")
print(f"S (替代): {result.substitute[:100] if result.substitute else '(空)'}...")
print(f"C (結合): {result.combine[:100] if result.combine else '(空)'}...")
print(f"A (調適): {result.adapt[:100] if result.adapt else '(空)'}...")
print(f"M (修改): {result.modify[:100] if result.modify else '(空)'}...")
print(f"P (他用): {result.put_to_other_uses[:100] if result.put_to_other_uses else '(空)'}...")
print(f"E (消除): {result.eliminate[:100] if result.eliminate else '(空)'}...")
print(f"R (逆轉): {result.reverse[:100] if result.reverse else '(空)'}...")
print(f"\n最佳點子: {result.best_idea if result.best_idea else '(空)'}")
