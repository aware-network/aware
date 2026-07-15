from __future__ import annotations

from uuid import UUID


def as_uuid(value: UUID | str, *, field_name: str) -> UUID:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{field_name} must be a UUID: {value!r}") from exc


def required_token(value: str | None, *, field_name: str) -> str:
    token = (value or "").strip()
    if not token:
        raise RuntimeError(f"{field_name} is required")
    return token


def optional_token(value: str | None) -> str | None:
    token = (value or "").strip()
    return token or None


def status_token(value: str | None, *, default: str) -> str:
    return optional_token(value) or default


def ensure_existing_payload(
    existing: object,
    *,
    fields: dict[str, object],
    label: str,
    object_id: UUID,
) -> None:
    for name, expected in fields.items():
        if getattr(existing, name) != expected:
            raise RuntimeError(
                f"{label} payload mismatch for existing object: {label}_id={object_id}"
            )
