"""Authored syntax requirements; no provider, source or parser authority."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from typing import Callable, cast

_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}\Z")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_TOKEN = re.compile(r"[^\s]+\Z")
MAX_SYNTAX_DECLARATION_BYTES = 8_388_608


class SyntaxDeclarationError(ValueError):
    """Malformed authored requirements, with no attempted effects."""


def _exact[T](value: object, kind: type[T]) -> T:
    if type(value) is not kind:
        raise SyntaxDeclarationError("syntax declaration requires exact owned types")
    return cast(T, value)


def _field(value: object, name: str) -> object:
    try:
        return cast(object, object.__getattribute__(value, name))
    except AttributeError as exc:
        raise SyntaxDeclarationError("uninitialized syntax declaration") from exc


def _text(value: object, *, limit: int = 512) -> str:
    item = _exact(value, str)
    try:
        size = len(item.encode("utf-8"))
    except UnicodeError as exc:
        raise SyntaxDeclarationError("syntax text must be UTF-8") from exc
    if not 1 <= size <= limit or not _TOKEN.fullmatch(item):
        raise SyntaxDeclarationError("syntax text must be a bounded nonempty token")
    return item


def _name(value: object) -> str:
    item = _text(value, limit=128)
    if not _NAME.fullmatch(item):
        raise SyntaxDeclarationError("syntax reference name is invalid")
    return item


def _path(value: object) -> str:
    item = _exact(value, str)
    try:
        size = len(item.encode("utf-8"))
    except UnicodeError as exc:
        raise SyntaxDeclarationError("contribution path must be UTF-8") from exc
    parts = item.split("/")
    if (
        not 1 <= size <= 4096
        or not item.endswith(".syntax.json")
        or "\\" in item
        or "\x00" in item
        or unicodedata.normalize("NFC", item) != item
        or len(parts) > 128
        or any(
            not part.strip() or part in (".", "..") or len(part.encode()) > 255
            for part in parts
        )
    ):
        raise SyntaxDeclarationError(
            "contribution requires a normalized package-relative .syntax.json path"
        )
    return item


@dataclass(frozen=True, slots=True)
class AwareModuleSyntaxContractRefSpec:
    key: str
    version: str
    schema_digest: str

    def __post_init__(self) -> None:
        _ = _contract_wire(self)


@dataclass(frozen=True, slots=True)
class AwareModuleSyntaxAnchorSpec:
    consumer_contract: AwareModuleSyntaxContractRefSpec
    role: str
    rule_name: str
    field_path: tuple[str, ...]
    required: bool
    top_level: bool

    def __post_init__(self) -> None:
        _ = _anchor_wire(self)


@dataclass(frozen=True, slots=True)
class AwareModuleSyntaxDeclarationSpec:
    version: int
    contributions: tuple[str, ...]
    anchors: tuple[AwareModuleSyntaxAnchorSpec, ...]

    def __post_init__(self) -> None:
        _ = syntax_declaration_wire(self)


def _contract_wire(value: object) -> dict[str, object]:
    item = _exact(value, AwareModuleSyntaxContractRefSpec)
    digest = _text(_field(item, "schema_digest"), limit=71)
    if not _DIGEST.fullmatch(digest):
        raise SyntaxDeclarationError(
            "consumer contract needs a complete lowercase SHA-256"
        )
    return {
        "key": _text(_field(item, "key")),
        "version": _text(_field(item, "version")),
        "schema_digest": digest,
    }


def _anchor_wire(value: object) -> dict[str, object]:
    item = _exact(value, AwareModuleSyntaxAnchorSpec)
    path = cast(tuple[object, ...], _exact(_field(item, "field_path"), tuple))
    if not 1 <= len(path) <= 64:
        raise SyntaxDeclarationError("field path must contain 1..64 names")
    return {
        "consumer_contract": _contract_wire(_field(item, "consumer_contract")),
        "role": _text(_field(item, "role")),
        "rule_name": _name(_field(item, "rule_name")),
        "field_path": [_name(part) for part in path],
        "required": _exact(_field(item, "required"), bool),
        "top_level": _exact(_field(item, "top_level"), bool),
    }


def _canonical(value: dict[str, object]) -> bytes:
    # The existing module-manifest owner supplies canonical JSON. This local
    # import avoids its parser/models cycle; it does not discover a provider.
    from .v2_parser import canonical

    encode = cast(Callable[[object], bytes], canonical)
    return encode(value)


def syntax_declaration_wire(
    value: AwareModuleSyntaxDeclarationSpec,
) -> dict[str, object]:
    item = _exact(value, AwareModuleSyntaxDeclarationSpec)
    version = _exact(_field(item, "version"), int)
    if version != 1:
        raise SyntaxDeclarationError("syntax declaration version must be integer 1")
    paths = cast(tuple[object, ...], _exact(_field(item, "contributions"), tuple))
    anchors = cast(tuple[object, ...], _exact(_field(item, "anchors"), tuple))
    if not 1 <= len(paths) <= 128 or not 1 <= len(anchors) <= 8192:
        raise SyntaxDeclarationError("syntax declaration collection bounds exceeded")
    declared = [_path(path) for path in paths]
    if len(set(declared)) != len(declared):
        raise SyntaxDeclarationError("duplicate authored contribution path")
    rows = [_anchor_wire(anchor) for anchor in anchors]
    if len({_canonical(row) for row in rows}) != len(rows):
        raise SyntaxDeclarationError("duplicate authored syntax anchor")
    wire: dict[str, object] = {
        "version": version,
        "contributions": declared,
        "anchors": rows,
    }
    if len(_canonical(wire)) > MAX_SYNTAX_DECLARATION_BYTES:
        raise SyntaxDeclarationError("syntax declaration byte bound exceeded")
    return wire


def syntax_declaration_digest(value: AwareModuleSyntaxDeclarationSpec) -> str:
    body = _canonical(
        {
            "contract": "aware.code.grammar-syntax-declaration.v1",
            "value": syntax_declaration_wire(value),
        }
    )
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _table(value: object, keys: set[str]) -> dict[str, object]:
    item = cast(dict[object, object], _exact(value, dict))
    if set(item) != keys:
        raise SyntaxDeclarationError("syntax declaration has missing or unknown fields")
    return cast(dict[str, object], item)


def _array(value: object, maximum: int) -> list[object]:
    item = cast(list[object], _exact(value, list))
    if not 1 <= len(item) <= maximum:
        raise SyntaxDeclarationError("authored syntax array bounds exceeded")
    return item


def parse_syntax_declaration_table(value: object) -> AwareModuleSyntaxDeclarationSpec:
    row = _table(value, {"version", "contributions", "anchors"})
    anchors: list[AwareModuleSyntaxAnchorSpec] = []
    for raw in _array(row["anchors"], 8192):
        anchor = _table(
            raw,
            {
                "consumer_contract",
                "role",
                "rule_name",
                "field_path",
                "required",
                "top_level",
            },
        )
        ref = _table(anchor["consumer_contract"], {"key", "version", "schema_digest"})
        anchors.append(
            AwareModuleSyntaxAnchorSpec(
                AwareModuleSyntaxContractRefSpec(
                    _text(ref["key"]),
                    _text(ref["version"]),
                    _text(ref["schema_digest"], limit=71),
                ),
                _text(anchor["role"]),
                _name(anchor["rule_name"]),
                tuple(_name(part) for part in _array(anchor["field_path"], 64)),
                _exact(anchor["required"], bool),
                _exact(anchor["top_level"], bool),
            )
        )
    return AwareModuleSyntaxDeclarationSpec(
        _exact(row["version"], int),
        tuple(_path(path) for path in _array(row["contributions"], 128)),
        tuple(anchors),
    )
