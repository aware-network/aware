from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict

from aware_hub_sdk.models import HubCodePackagePublicationEntry


def build_code_package_authority_index_payload(
    entries: Iterable[HubCodePackagePublicationEntry],
    *,
    generated_at: str | None = None,
) -> dict[str, object]:
    """Build the Hub CodePackage authority index payload for publish receipts."""

    package_entries: list[dict[str, object]] = []
    channel_heads: list[dict[str, object]] = []
    for entry in entries:
        descriptor = _json_dict(asdict(entry.descriptor))
        artifact_lock = _json_dict(asdict(entry.artifact_lock))
        package_entries.append(
            {
                "descriptor": descriptor,
                "artifact_lock": artifact_lock,
            }
        )
        revision_id = descriptor.get("revision_id") or artifact_lock.get("revision_id")
        if revision_id:
            head: dict[str, object] = {
                "package_name": descriptor["package_name"],
                "language": descriptor.get("language"),
                "surface": descriptor.get("surface"),
                "channel": entry.channel,
                "revision_id": revision_id,
            }
            if entry.updated_at:
                head["updated_at"] = entry.updated_at
            channel_heads.append(_json_dict(head))

    payload: dict[str, object] = {
        "version": 1,
        "authority_kind": "code_package_distribution",
        "packages": package_entries,
        "channel_heads": channel_heads,
    }
    if generated_at:
        payload["generated_at"] = generated_at
    return payload


def _json_dict(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        key: _json_value(value)
        for key, value in payload.items()
        if value is not None
    }


def _json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return _json_dict(value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    return value


__all__ = [
    "build_code_package_authority_index_payload",
]
