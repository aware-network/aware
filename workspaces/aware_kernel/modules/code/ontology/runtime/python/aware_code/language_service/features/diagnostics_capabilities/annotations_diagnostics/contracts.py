from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol, TypeAlias

from aware_code.language_service.position import ByteRange
from aware_code.language_service.types import SpannedToken

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig

from ..contracts import DiagnosticDataValue


class AnnotationAddDiagnostic(Protocol):
    def __call__(
        self,
        *,
        rng: ByteRange,
        message: str,
        code: str | None = None,
        data: Mapping[str, DiagnosticDataValue] | None = None,
        severity: int = 1,
    ) -> None: ...


class AnnotationSuggestFn(Protocol):
    def __call__(self, value: str, options: list[str]) -> list[str]: ...


ClassResolution: TypeAlias = tuple[str, ClassConfig]
EnumResolution: TypeAlias = tuple[str, EnumConfig]
ResolveClassFn: TypeAlias = Callable[[str], ClassResolution | None]
ResolveEnumFn: TypeAlias = Callable[[str], EnumResolution | None]


@dataclass(frozen=True, slots=True)
class AnnotationVerbInput:
    path: SpannedToken
    verb_token: SpannedToken
    args_tokens: tuple[SpannedToken, ...]
    type_ref: SpannedToken
    members: tuple[SpannedToken, ...]
    args: tuple[str, ...]
    class_candidates: tuple[str, ...]
    enum_candidates: tuple[str, ...]
