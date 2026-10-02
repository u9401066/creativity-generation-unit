"""Ports: what the use cases need from the outside world."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Protocol

from pydantic import BaseModel, Field

from cgu.domain.common import Session
from cgu.domain.frame import Frame
from cgu.domain.idea import Fragment, Idea
from cgu.domain.judge import Matchup, Verdict

ProgressFn = Callable[[float, float | None, str | None], Awaitable[None]]


class EmbeddingUnavailableError(Exception):
    pass


class LLMUnavailableError(Exception):
    pass


class RetrievalUnavailableError(Exception):
    pass


class EmbeddingInfo(BaseModel):
    backend: str
    semantic: bool


class Embedded(BaseModel):
    """Unit-length vectors from a single backend, so one call never mixes spaces."""

    vectors: list[list[float]]
    backend: str
    semantic: bool
    warnings: list[str] = Field(default_factory=list)


class RetrievedDoc(BaseModel):
    title: str
    text: str
    url: str | None = None
    source_id: str | None = None


class EmbeddingPort(Protocol):
    async def describe(self) -> EmbeddingInfo: ...

    async def embed(self, texts: Sequence[str]) -> Embedded: ...


class LLMPort(Protocol):
    model: str

    async def complete(self, prompt: str, *, seed: int | None = None) -> str: ...


class RetrievalPort(Protocol):
    async def search(self, query: str, *, lang: str, limit: int) -> list[RetrievedDoc]: ...


class ArchivePort(Protocol):
    async def create_session(self, session: Session) -> None: ...

    async def get_session(self, session_id: str) -> Session | None: ...

    async def list_sessions(self) -> list[Session]: ...

    async def delete_session(self, session_id: str) -> bool: ...

    async def export_session(self, session_id: str) -> dict[str, Any]: ...

    async def counts(self, session_id: str) -> dict[str, int]: ...

    async def bump_counter(self, session_id: str, name: str) -> int: ...

    async def save_frame(self, frame: Frame) -> None: ...

    async def get_frame(self, frame_id: str) -> Frame | None: ...

    async def list_frames(self, session_id: str) -> list[Frame]: ...

    async def save_ideas(self, ideas: Sequence[Idea]) -> None: ...

    async def update_idea(self, idea: Idea) -> None: ...

    async def list_ideas(self, session_id: str, kind: str | None = None) -> list[Idea]: ...

    async def save_fragments(self, fragments: Sequence[Fragment]) -> None: ...

    async def list_fragments(self, session_id: str) -> list[Fragment]: ...

    async def save_matchups(self, matchups: Sequence[Matchup]) -> None: ...

    async def list_matchups(self, session_id: str) -> list[Matchup]: ...

    async def save_verdicts(self, session_id: str, verdicts: Sequence[Verdict]) -> None: ...

    async def list_verdicts(self, session_id: str) -> list[Verdict]: ...

    async def get_niches(self, session_id: str) -> dict[str, dict[str, Any]]: ...

    async def put_niche(self, session_id: str, niche: str, state: dict[str, Any]) -> None: ...

    async def save_question(self, session_id: str, record: dict[str, Any]) -> None: ...

    async def list_questions(self, session_id: str) -> list[dict[str, Any]]: ...

    async def save_feedback(self, session_id: str, record: dict[str, Any]) -> None: ...

    async def list_feedback(self, session_id: str) -> list[dict[str, Any]]: ...

    async def delete_feedback(self, session_id: str) -> int: ...
