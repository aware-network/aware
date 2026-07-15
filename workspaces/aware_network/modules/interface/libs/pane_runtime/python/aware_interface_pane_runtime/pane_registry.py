from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


class MissingPaneProviderError(KeyError):
    pass


class DuplicatePaneProviderError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PaneMountContext:
    window_key: str
    layout_key: str
    section_key: str
    pane_key: str


PaneProvider = Callable[[PaneMountContext], str]


@dataclass(frozen=True, slots=True)
class PaneProviderBinding:
    module_id: str
    pane_key: str
    provider: PaneProvider


class ModulePaneRegistry:
    def __init__(self) -> None:
        self._bindings: dict[str, PaneProviderBinding] = {}

    def register(
        self,
        *,
        module_id: str,
        pane_key: str,
        provider: PaneProvider,
    ) -> PaneProviderBinding:
        normalized_module = _normalize_required_token(module_id, field_name="module_id")
        normalized_pane = _normalize_required_token(pane_key, field_name="pane_key")

        existing = self._bindings.get(normalized_pane)
        if existing is not None and existing.provider is not provider:
            raise DuplicatePaneProviderError(
                f"Pane provider already registered for pane_key {normalized_pane!r} "
                + f"(existing module={existing.module_id!r})"
            )
        if existing is not None:
            return existing

        binding = PaneProviderBinding(
            module_id=normalized_module,
            pane_key=normalized_pane,
            provider=provider,
        )
        self._bindings[normalized_pane] = binding
        return binding

    def resolve(self, pane_key: str) -> PaneProviderBinding:
        normalized_pane = _normalize_required_token(pane_key, field_name="pane_key")
        binding = self._bindings.get(normalized_pane)
        if binding is None:
            raise MissingPaneProviderError(f"Pane provider not registered: {normalized_pane!r}")
        return binding

    def has(self, pane_key: str) -> bool:
        normalized_pane = _normalize_required_token(pane_key, field_name="pane_key")
        return normalized_pane in self._bindings


def _normalize_required_token(raw: str, *, field_name: str) -> str:
    token = (raw or "").strip().lower()
    if not token:
        raise ValueError(f"{field_name} must be non-empty")
    return token

