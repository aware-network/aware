from __future__ import annotations

from typing import NotRequired, Protocol, TypedDict


class CompletionItemDict(TypedDict):
    label: str
    kind: NotRequired[int]
    detail: NotRequired[str]


class CompletionResultDict(TypedDict):
    isIncomplete: bool
    items: list[CompletionItemDict]


class CompletionItemAdder(Protocol):
    def __call__(self, label: str, *, kind: int | None = None, detail: str | None = None) -> None: ...
