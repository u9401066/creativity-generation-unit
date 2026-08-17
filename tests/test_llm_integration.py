"""Opt-in integration tests for a live Ollama model."""

from __future__ import annotations

import os

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("CGU_RUN_LLM_TESTS") != "1",
        reason="set CGU_RUN_LLM_TESTS=1 with a reachable Ollama model",
    ),
]


def _client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CGU_USE_LLM", "true")
    monkeypatch.setenv("CGU_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("CGU_OLLAMA_MODEL", os.getenv("CGU_OLLAMA_MODEL", "qwen2.5:3b"))

    from cgu.llm import get_llm_client

    return get_llm_client()


def test_live_ollama_generates_text(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _client(monkeypatch).generate("你好，請用一句話介紹自己")
    assert isinstance(result, str)
    assert result.strip()


def test_live_ollama_generates_structured_scamper(monkeypatch: pytest.MonkeyPatch) -> None:
    from cgu.llm import PROMPT_SCAMPER, SYSTEM_PROMPT_CREATIVITY, ScamperOutput

    result = _client(monkeypatch).generate_structured(
        prompt=PROMPT_SCAMPER.format(topic="遠距工作"),
        response_model=ScamperOutput,
        system_prompt=SYSTEM_PROMPT_CREATIVITY,
    )

    assert isinstance(result, ScamperOutput)
    assert any(
        value.strip()
        for value in (
            result.substitute,
            result.combine,
            result.adapt,
            result.modify,
            result.put_to_other_uses,
            result.eliminate,
            result.reverse,
        )
        if value
    )
