from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.language_service.capability_scope import CapabilityProviderExecutionContext
from aware_code.language_service.position import ByteRange, Utf16PositionMapper
from aware_meta.fqn_resolver import FqnScope


TOKEN_TYPES: list[str] = [
    "namespace",
    "class",
    "enum",
    "enumMember",
    "function",
    "method",
    "property",
    "parameter",
    "type",
    # IMPORTANT: only append new token types to keep indices stable across releases.
    "keyword",
    "modifier",
    "comment",
    "string",
    "number",
    "operator",
]

# IMPORTANT: only append new token modifiers to keep indices stable across releases.
TOKEN_MODIFIERS: list[str] = [
    "projection",
    "experience",
    "api",
    "program",
    "environment",
    "role",
    "actor",
    "portNode",
    "intrinsic",
    "identity",
    "event",
    "action",
]

TOKEN_TYPE_INDEX: dict[str, int] = {name: idx for idx, name in enumerate(TOKEN_TYPES)}
TOKEN_MODIFIER_INDEX: dict[str, int] = {name: idx for idx, name in enumerate(TOKEN_MODIFIERS)}

PrimitiveTypeResolver = Callable[[str], bool]


@dataclass(frozen=True, slots=True)
class SemanticToken:
    line: int
    start_char: int
    length: int
    token_type: int
    token_modifiers: int = 0


@dataclass(frozen=True, slots=True)
class LexicalToken:
    token_type: str
    byte_range: ByteRange
    modifiers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SemanticTokensContext:
    code: Code
    execution: CapabilityProviderExecutionContext
    scope: FqnScope
    mapper: Utf16PositionMapper
    document_bytes: bytes
    workspace_language: CodeLanguage
    is_primitive_type: PrimitiveTypeResolver
