from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json


@dataclass(frozen=True, slots=True)
class EnvironmentProfileMountApplyPlan:
    environment_handle: str
    package_name: str
    profile_key: str
    mount_key: str
    mode: str = "mounted"
    position: int | None = None


def profile_mount_apply_plans_from_runtime_artifact_refs_json(
    *,
    artifact_refs_json: str | None,
    environment_handle: str,
) -> tuple[EnvironmentProfileMountApplyPlan, ...]:
    text = (artifact_refs_json or "").strip()
    if not text:
        return ()
    payload = json.loads(text)
    if not isinstance(payload, list):
        raise ValueError("Environment runtime artifact refs must be a JSON list.")

    plans: list[EnvironmentProfileMountApplyPlan] = []
    seen_mount_keys: set[str] = set()
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError(
                "Environment runtime artifact refs must contain object entries."
            )
        source = _node_runtime_source_payload(item)
        if source is None:
            continue
        for target in _sequence_of_mappings(source.get("environment_targets")):
            target_handle = _required_text(
                target.get("environment_handle"),
                "environment_targets[].environment_handle",
            )
            if target_handle.casefold() != environment_handle.casefold():
                continue
            for mount in _sequence_of_mappings(target.get("profile_mounts")):
                plan = EnvironmentProfileMountApplyPlan(
                    environment_handle=target_handle,
                    package_name=_required_text(
                        mount.get("package_name"),
                        "profile_mounts[].package_name",
                    ),
                    profile_key=_required_text(
                        mount.get("profile_key"),
                        "profile_mounts[].profile_key",
                    ),
                    mount_key=_required_text(
                        mount.get("mount_key"),
                        "profile_mounts[].mount_key",
                    ),
                    mode=_optional_text(mount.get("mode")) or "mounted",
                    position=_optional_int(mount.get("position")),
                )
                mount_key = plan.mount_key.casefold()
                if mount_key in seen_mount_keys:
                    raise ValueError(
                        "Duplicate Environment profile mount key in Node "
                        f"runtime source: {plan.mount_key!r}"
                    )
                seen_mount_keys.add(mount_key)
                plans.append(plan)

    return tuple(
        sorted(
            plans,
            key=lambda item: (
                item.position is None,
                item.position or 0,
                item.mount_key.casefold(),
            ),
        )
    )


def _node_runtime_source_payload(
    artifact_ref: Mapping[object, object],
) -> Mapping[str, object] | None:
    for key in ("provider_payload", "receipt"):
        payload = artifact_ref.get(key)
        if isinstance(payload, Mapping):
            source = payload.get("node_runtime_source")
            if isinstance(source, Mapping):
                return {str(k): v for k, v in source.items()}
            source = payload.get("provider_node_runtime_source")
            if isinstance(source, Mapping):
                return {str(k): v for k, v in source.items()}
    source = artifact_ref.get("node_runtime_source")
    if isinstance(source, Mapping):
        return {str(k): v for k, v in source.items()}
    return None


def _sequence_of_mappings(value: object) -> tuple[Mapping[str, object], ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("Expected a list of objects.")
    result: list[Mapping[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("Expected a list of objects.")
        result.append({str(k): v for k, v in item.items()})
    return tuple(result)


def _required_text(value: object, field_name: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise ValueError(f"{field_name} is required.")
    return text


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return int(str(value).strip())


__all__ = [
    "EnvironmentProfileMountApplyPlan",
    "profile_mount_apply_plans_from_runtime_artifact_refs_json",
]
