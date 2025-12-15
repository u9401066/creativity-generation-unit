"""
CGU LLM Client

Ollama + Instructor 整合，提供 Structured Output
Ollama 提供 OpenAI-compatible API，支援 Windows/macOS/Linux
"""

import os
from typing import TypeVar, Type
from functools import lru_cache

from pydantic import BaseModel
from openai import OpenAI
import instructor

# 預設配置（Ollama）
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen2.5:3b"  # 或 qwen2.5:7b, llama3.2, mistral 等


T = TypeVar("T", bound=BaseModel)


class LLMConfig(BaseModel):
    """LLM 配置"""
    base_url: str = DEFAULT_OLLAMA_BASE_URL
    model: str = DEFAULT_MODEL
    api_key: str = "ollama"  # Ollama 不需要 API key，但 OpenAI client 需要非空值
    temperature: float = 0.7
    max_tokens: int = 1024
    timeout: float = 120.0  # Ollama 本地推理可能較慢


@lru_cache()
def get_llm_config() -> LLMConfig:
    """取得 LLM 配置（從環境變數）"""
    return LLMConfig(
        base_url=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
        model=os.getenv("OLLAMA_MODEL", DEFAULT_MODEL),
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
        temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS", "1024")),
        timeout=float(os.getenv("OLLAMA_TIMEOUT", "120.0")),
    )


class CGULLMClient:
    """
    CGU LLM 客戶端
    
    整合 Ollama (OpenAI-compatible API) + Instructor (Structured Output)
    支援 Windows/macOS/Linux，可使用 Qwen, Llama, Mistral 等模型
    """
    
    def __init__(self, config: LLMConfig | None = None):
        self.config = config or get_llm_config()
        
        # 建立 OpenAI 客戶端（指向 vLLM）
        self._client = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=self.config.timeout,
        )
        
        # 包裝 Instructor 以支援 Structured Output
        self._instructor = instructor.from_openai(self._client)
    
    @property
    def client(self) -> OpenAI:
        """原始 OpenAI 客戶端"""
        return self._client
    
    @property
    def instructor_client(self):
        """Instructor 包裝的客戶端"""
        return self._instructor
    
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        基本生成（非結構化）
        
        Args:
            prompt: 使用者提示
            system_prompt: 系統提示
            temperature: 溫度（覆蓋預設）
            max_tokens: 最大 token 數（覆蓋預設）
        
        Returns:
            生成的文字
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
        )
        
        return response.choices[0].message.content or ""
    
    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int = 3,
    ) -> T:
        """
        結構化生成（使用 Instructor）
        
        Args:
            prompt: 使用者提示
            response_model: Pydantic 模型類別
            system_prompt: 系統提示
            temperature: 溫度
            max_tokens: 最大 token 數
            max_retries: 最大重試次數
        
        Returns:
            Pydantic 模型實例
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self._instructor.chat.completions.create(
            model=self.config.model,
            messages=messages,
            response_model=response_model,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            max_retries=max_retries,
        )
        
        return response
    
    def generate_sync(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """同步版本的基本生成"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
        )
        
        return response.choices[0].message.content or ""
    
    def generate_structured_sync(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int = 3,
    ) -> T:
        """同步版本的結構化生成"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self._instructor.chat.completions.create(
            model=self.config.model,
            messages=messages,
            response_model=response_model,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            max_retries=max_retries,
        )
        
        return response


# 全域客戶端實例
_llm_client: CGULLMClient | None = None


def get_llm_client() -> CGULLMClient:
    """取得全域 LLM 客戶端"""
    global _llm_client
    if _llm_client is None:
        _llm_client = CGULLMClient()
    return _llm_client


def reset_llm_client() -> None:
    """重置全域 LLM 客戶端"""
    global _llm_client
    _llm_client = None
