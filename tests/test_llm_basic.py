"""測試基本 LLM 生成 - LangChain + Ollama"""
import os
os.environ["CGU_USE_LLM"] = "true"
os.environ["CGU_LLM_PROVIDER"] = "ollama"
os.environ["CGU_OLLAMA_MODEL"] = "qwen2.5:3b"

from cgu.llm import get_llm_client

print("=== LangChain + Ollama 測試 ===")

client = get_llm_client()
print(f"Base URL: {client.config.base_url}")
print(f"Model: {client.config.model}")
print(f"Client type: {type(client._llm)}")

print("\n測試基本生成...")
result = client.generate("你好，請用一句話介紹自己")
print(f"結果: {result}")
