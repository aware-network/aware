from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping

_TOKEN_PATTERN = re.compile(r"^[^\s|]+$")


def required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def optional_text(value: object | None, field: str) -> str | None:
    if value is None:
        return None
    return required_text(value, field)


def required_token(value: object, field: str) -> str:
    token = required_text(value, field)
    if not _TOKEN_PATTERN.fullmatch(token):
        raise ValueError(f"{field} must be one non-whitespace token without pipes")
    return token


def optional_token(value: object | None, field: str) -> str | None:
    if value is None:
        return None
    return required_token(value, field)


def nonnegative(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a nonnegative integer")
    return value


def positive(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def normalize_goal_tag(value: object) -> str:
    tag = required_token(value, "tag")
    if not tag.startswith("goal/"):
        raise ValueError("Goal tag must start with 'goal/'")
    return tag


def unique_tokens(values: Iterable[str], field: str) -> tuple[str, ...]:
    normalized = tuple(required_token(value, field) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field} must contain unique values")
    return normalized


def fingerprint(value: Mapping[str, object]) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


def stable_ref(*, kind: str, authority_ref: str, coordinates: Iterable[str]) -> str:
    payload = {
        "kind": required_token(kind, "kind"),
        "authority_ref": required_token(authority_ref, "authority_ref"),
        "coordinates": [required_text(item, "coordinate") for item in coordinates],
    }
    return f"{kind}:" + fingerprint(payload)
