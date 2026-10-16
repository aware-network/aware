"""Portable grammar payloads. Matching bytes never confer source authority."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import cast

from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from .semantic_candidates import _path as _source_path

MAX_GRAMMAR_BODY_BYTES = 8_388_608
MAX_GRAMMAR_PROVIDERS = 256
MAX_GRAMMAR_CONTRIBUTIONS = 128
MAX_GRAMMAR_ANCHORS = 8_192
_TOKEN = re.compile(r"[^\s]+\Z")

GRAMMAR_PROFILE_RESULT_REF = SemanticContractRef(
    "aware.code.semantic-contract-profile.v1",
    "1",
    ContentDigest(
        "sha256:29f376ace08de95cf419a58e856f8a8507ffa99033ce45987c27753f84f77dee"
    ),
)
GRAMMAR_SYNTAX_BINDING_V2_REF = SemanticContractRef(
    "aware.code.grammar-syntax-binding.v2",
    "2",
    ContentDigest(
        "sha256:8d07dadea4dfba14a8e5da185698f9e3884184d67f922a6d4f1f82651166139a"
    ),
)
GRAMMAR_DECLARATION_SOURCE_REF = SemanticContractRef(
    "aware.code.grammar-declaration-source.v1",
    "1",
    ContentDigest(
        "sha256:7b49cdb29784713baeb34f24663c4049858d3b49b88c8902891882b07731b4bd"
    ),
)


def _exact[T](value: object, expected: type[T]) -> T:
    if type(value) is not expected:
        raise TypeError(f"exact {expected.__name__} required")
    return cast(T, value)


def _token(value: object, limit: int = 512) -> str:
    text = _exact(value, str)
    try:
        size = len(text.encode("utf-8"))
    except UnicodeError as exc:
        raise ContractViolation("grammar token must be UTF-8") from exc
    if not 1 <= size <= limit or not _TOKEN.fullmatch(text):
        raise ContractViolation("grammar token must be bounded and nonblank")
    return text


def _digest(value: object) -> ContentDigest:
    item = _exact(value, ContentDigest)
    ContentDigest.__post_init__(item)
    return item


def _ref(value: object) -> SemanticContractRef:
    item = _exact(value, SemanticContractRef)
    _ = _token(item.key)
    _ = _token(item.version)
    _ = _digest(item.schema_digest)
    return item


def _coordinate(value: object) -> SemanticValueCoordinate:
    item = _exact(value, SemanticValueCoordinate)
    _ = _token(item.role)
    _ = _ref(item.contract)
    _ = _token(item.value_ref)
    _ = _digest(item.digest)
    _ = _integer(item.size_bytes, MAX_GRAMMAR_BODY_BYTES)
    return item


def _integer(value: object, limit: int) -> int:
    size = _exact(value, int)
    if not 0 <= size <= limit:
        raise ContractViolation("grammar size/count exceeds bound")
    return size


def _items(value: object, limit: int) -> tuple[object, ...]:
    items = cast(tuple[object, ...], _exact(value, tuple))
    if len(items) > limit:
        raise ContractViolation("grammar collection exceeds bound")
    return items


def _ordered(keys: tuple[bytes, ...] | tuple[tuple[bytes, bytes], ...]) -> None:
    if keys != tuple(sorted(set(keys))):
        raise ContractViolation("grammar inventory must be unique and ordered")


def _bounded(wire: object, limit: int = MAX_GRAMMAR_BODY_BYTES) -> bytes:
    try:
        body = canonical_json_bytes(wire)
    except (UnicodeError, RecursionError) as exc:
        raise ContractViolation("invalid grammar wire") from exc
    if len(body) > limit:
        raise ContractViolation("grammar body exceeds bound")
    return body


@dataclass(frozen=True, slots=True)
class CodeGrammarDeclarationSourceV1:
    repository_binding_ref: str
    scope_key: str
    source_kind: str
    relative_path: str
    body_ref: str
    content_digest: ContentDigest
    size_bytes: int

    def __post_init__(self) -> None:
        _ = _exact(self, CodeGrammarDeclarationSourceV1)
        _ = _token(self.repository_binding_ref, 4096)
        _ = _source_path(self.scope_key)
        _ = _source_path(self.relative_path)
        if _exact(self.source_kind, str) not in {"profile", "module"}:
            raise ContractViolation("declaration source kind differs")
        _ = _token(self.body_ref, 4096)
        _ = _digest(self.content_digest)
        _ = _integer(self.size_bytes, MAX_GRAMMAR_BODY_BYTES)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": "aware.code.grammar-declaration-source.v1",
            "repository_binding_ref": self.repository_binding_ref,
            "scope_key": self.scope_key,
            "source_kind": self.source_kind,
            "relative_path": self.relative_path,
            "body_ref": self.body_ref,
            "content_digest": self.content_digest.value,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class CodeGrammarProviderBindingV2:
    occurrence_ref: str
    module_id: str
    provider_key: str
    semantic_contract: SemanticContractRef
    declaration: CodeGrammarDeclarationSourceV1
    syntax_binding_digest: ContentDigest

    def __post_init__(self) -> None:
        _ = _exact(self, CodeGrammarProviderBindingV2)
        for value in (self.occurrence_ref, self.module_id, self.provider_key):
            _ = _token(value)
        _ = _ref(self.semantic_contract)
        _ = _exact(self.declaration, CodeGrammarDeclarationSourceV1).__post_init__()
        if self.declaration.source_kind != "module":
            raise ContractViolation("provider requires a module declaration")
        _ = _digest(self.syntax_binding_digest)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": "aware.code.grammar-provider-binding.v2",
            "occurrence_ref": self.occurrence_ref,
            "module_id": self.module_id,
            "provider_key": self.provider_key,
            "semantic_contract": self.semantic_contract.to_wire(),
            "declaration": self.declaration.to_wire(),
            "syntax_binding_digest": self.syntax_binding_digest.value,
        }


@dataclass(frozen=True, slots=True)
class CodeGrammarContributionBindingV1:
    occurrence_ref: str
    relative_path: str
    contribution_coordinate: SemanticValueCoordinate

    def __post_init__(self) -> None:
        _ = _exact(self, CodeGrammarContributionBindingV1)
        _ = _token(self.occurrence_ref)
        _ = _source_path(self.relative_path)
        if not self.relative_path.endswith(".syntax.json"):
            raise ContractViolation("contribution path must end .syntax.json")
        _ = _coordinate(self.contribution_coordinate)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": "aware.code.grammar-contribution-binding.v1",
            "occurrence_ref": self.occurrence_ref,
            "relative_path": self.relative_path,
            "contribution_coordinate": self.contribution_coordinate.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class CodeGrammarAnchorRequirementV1:
    provider_key: str
    consumer_contract: SemanticContractRef
    role: str
    rule_name: str
    field_path: tuple[str, ...]
    required: bool
    top_level: bool

    def __post_init__(self) -> None:
        _ = _exact(self, CodeGrammarAnchorRequirementV1)
        for value in (self.provider_key, self.role, self.rule_name):
            _ = _token(value)
        _ = _ref(self.consumer_contract)
        for value in _items(self.field_path, 64):
            _ = _token(value)
        _ = _exact(self.required, bool)
        _ = _exact(self.top_level, bool)

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": "aware.code.grammar-anchor-requirement.v1",
            "provider_key": self.provider_key,
            "consumer_contract": self.consumer_contract.to_wire(),
            "role": self.role,
            "rule_name": self.rule_name,
            "field_path": list(self.field_path),
            "required": self.required,
            "top_level": self.top_level,
        }


@dataclass(frozen=True, slots=True)
class CodeGrammarSyntaxBindingV2:
    profile_key: str
    profile_ref: str
    profile_version: str
    code_profile_digest: ContentDigest
    profile_source: CodeGrammarDeclarationSourceV1
    provider_bindings: tuple[CodeGrammarProviderBindingV2, ...]
    contribution_coordinates: tuple[SemanticValueCoordinate, ...]
    contribution_bindings: tuple[CodeGrammarContributionBindingV1, ...]
    anchor_requirements: tuple[CodeGrammarAnchorRequirementV1, ...]
    interpretation_profile: SemanticValueCoordinate

    def __post_init__(self) -> None:
        _ = _exact(self, CodeGrammarSyntaxBindingV2)
        for value in (self.profile_key, self.profile_ref, self.profile_version):
            _ = _token(value)
        _ = _digest(self.code_profile_digest)
        _ = _exact(self.profile_source, CodeGrammarDeclarationSourceV1).__post_init__()
        if self.profile_source.source_kind != "profile":
            raise ContractViolation("syntax requires a profile declaration")
        providers = _items(self.provider_bindings, MAX_GRAMMAR_PROVIDERS)
        for value in providers:
            _ = _exact(value, CodeGrammarProviderBindingV2).__post_init__()
        keys = tuple((p.occurrence_ref, p.provider_key) for p in self.provider_bindings)
        if len(keys) != len(set(keys)):
            raise ContractViolation("duplicate occurrence/provider binding")
        if (
            len(
                {
                    canonical_json_bytes(p.semantic_contract.to_wire())
                    for p in self.provider_bindings
                }
            )
            > 32
        ):
            raise ContractViolation("too many distinct semantic contracts")
        coords = _items(self.contribution_coordinates, MAX_GRAMMAR_CONTRIBUTIONS)
        for value in coords:
            _ = _coordinate(value)
        coord_keys = tuple(
            canonical_json_bytes(c.to_wire()) for c in self.contribution_coordinates
        )
        _ordered(coord_keys)
        bindings = _items(self.contribution_bindings, MAX_GRAMMAR_CONTRIBUTIONS)
        for value in bindings:
            _ = _exact(value, CodeGrammarContributionBindingV1).__post_init__()
        _ordered(
            tuple(
                (c.occurrence_ref.encode(), c.relative_path.encode())
                for c in self.contribution_bindings
            )
        )
        bound_keys = tuple(
            canonical_json_bytes(c.contribution_coordinate.to_wire())
            for c in self.contribution_bindings
        )
        if len(set(bound_keys)) != len(bound_keys) or set(bound_keys) != set(
            coord_keys
        ):
            raise ContractViolation("contribution correspondence must be bijective")
        anchors = _items(self.anchor_requirements, MAX_GRAMMAR_ANCHORS)
        for value in anchors:
            _ = _exact(value, CodeGrammarAnchorRequirementV1).__post_init__()
        _ordered(
            tuple(canonical_json_bytes(a.to_wire()) for a in self.anchor_requirements)
        )
        predecessor = _coordinate(self.interpretation_profile)
        if (
            predecessor.role != "code.profile_selection"
            or predecessor.contract != GRAMMAR_PROFILE_RESULT_REF
        ):
            raise ContractViolation(
                "syntax interpretation requires the full profile reference"
            )
        _ = _bounded(self._wire())

    def _wire(self) -> dict[str, object]:
        return {
            "contract": "aware.code.grammar-syntax-binding.v2",
            "profile_key": self.profile_key,
            "profile_ref": self.profile_ref,
            "profile_version": self.profile_version,
            "code_profile_digest": self.code_profile_digest.value,
            "profile_source": self.profile_source.to_wire(),
            "provider_bindings": [p.to_wire() for p in self.provider_bindings],
            "contribution_coordinates": [
                c.to_wire() for c in self.contribution_coordinates
            ],
            "contribution_bindings": [c.to_wire() for c in self.contribution_bindings],
            "anchor_requirements": [a.to_wire() for a in self.anchor_requirements],
            "interpretation_profile": self.interpretation_profile.to_wire(),
            "trivia_policy": "shared_syntax_only",
        }

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return self._wire()
