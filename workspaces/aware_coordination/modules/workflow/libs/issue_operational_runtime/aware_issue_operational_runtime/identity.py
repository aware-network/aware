from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence


def fingerprint(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def stable_local_ref(*, authority_ref: str, kind: str, semantic_key: str) -> str:
    payload = {
        "authority_ref": required_token(authority_ref, "authority_ref"),
        "kind": required_token(kind, "kind"),
        "semantic_key": required_token(semantic_key, "semantic_key"),
    }
    return f"issue-{kind}:{fingerprint(payload)}"


def stable_issue_ref(*, authority_ref: str, tag: str) -> str:
    return stable_local_ref(
        authority_ref=authority_ref,
        kind="instance",
        semantic_key=normalize_tag(tag),
    )


def normalize_tag(value: str) -> str:
    return required_token(value, "tag").casefold()


def required_token(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{name} must be a non-empty trimmed string")
    return value


def optional_token(value: str | None, name: str) -> str | None:
    return None if value is None else required_token(value, name)


def required_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def optional_text(value: str | None, name: str) -> str | None:
    return None if value is None else required_text(value, name)


def nonnegative(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def positive(value: int, name: str) -> int:
    if nonnegative(value, name) < 1:
        raise ValueError(f"{name} must be positive")
    return value


def unique_by(values: Sequence[object], attribute: str, label: str) -> None:
    keys = tuple(getattr(value, attribute) for value in values)
    if len(keys) != len(set(keys)):
        raise ValueError(f"{label} must be unique by {attribute}")


def normalize_scope_path(value: str) -> str:
    normalized = required_token(value.replace("\\", "/"), "relative_path")
    if normalized.startswith("/") or normalized in {".", ".."}:
        raise ValueError("relative_path must be repository-relative")
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("relative_path must be normalized")
    return normalized
