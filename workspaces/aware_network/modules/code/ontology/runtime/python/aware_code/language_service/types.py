from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from aware_code.language_service.position import ByteRange


@dataclass(frozen=True, slots=True)
class SpannedToken:
    text: str
    range: ByteRange


@dataclass(frozen=True, slots=True)
class AnnotationStatementTokens:
    path: SpannedToken | None
    verb: SpannedToken | None
    args: tuple[SpannedToken, ...]


@dataclass(frozen=True, slots=True)
class DefinitionTarget:
    uri: str
    range: ByteRange


@dataclass(frozen=True, slots=True)
class CompletionSegment:
    range: ByteRange
    kind: Literal[
        "type",
        "default_value",
        "import_module",
        "import_alias",
        "annotation_path",
        "annotation_args",
    ]


@dataclass(frozen=True, slots=True)
class ResolvedSymbol:
    kind: Literal["class", "enum"]
    fqn: str
    name: str
