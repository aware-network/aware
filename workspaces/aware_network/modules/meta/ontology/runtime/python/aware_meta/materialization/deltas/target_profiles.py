from __future__ import annotations

from collections.abc import Mapping

from aware_meta.generated_materialization_contract import (
    GeneratedMaterializationTargetProfile,
    ORM_RUNTIME_TARGET_PROFILE,
    TARGET_DESCRIPTOR_SOURCE_PROFILE_SELECTION,
)


def default_generated_materialization_target_profile() -> (
    GeneratedMaterializationTargetProfile
):
    return ORM_RUNTIME_TARGET_PROFILE


def generated_materialization_target_profile_from_payload(
    value: object | None,
    *,
    default: GeneratedMaterializationTargetProfile | None = None,
) -> GeneratedMaterializationTargetProfile | None:
    if isinstance(value, GeneratedMaterializationTargetProfile):
        return value
    if value is False:
        return None
    if value is None:
        return default
    if isinstance(value, str) and value.strip().lower() in {"none", "disabled"}:
        return None
    if not isinstance(value, Mapping):
        return default

    descriptor_key = _optional_text(
        value.get("descriptor_key")
        or value.get("target_key")
        or value.get("capability_key")
    )
    if descriptor_key is None:
        descriptor_key = default.descriptor_key if default is not None else None
    renderer_profile = _optional_text(value.get("renderer_profile")) or (
        default.renderer_profile if default is not None else None
    )
    materialization_source = _optional_text(value.get("materialization_source")) or (
        default.materialization_source if default is not None else None
    )
    if (
        descriptor_key is None
        or renderer_profile is None
        or materialization_source is None
    ):
        return default
    return GeneratedMaterializationTargetProfile(
        descriptor_key=descriptor_key,
        target_language=_optional_text(value.get("target_language"))
        or (default.target_language if default is not None else None),
        renderer_profile=renderer_profile,
        materialization_source=materialization_source,
        descriptor_source=(
            _optional_text(value.get("target_descriptor_source"))
            or _optional_text(value.get("descriptor_source"))
            or TARGET_DESCRIPTOR_SOURCE_PROFILE_SELECTION
        ),
    )


def _optional_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "ORM_RUNTIME_TARGET_PROFILE",
    "GeneratedMaterializationTargetProfile",
    "TARGET_DESCRIPTOR_SOURCE_PROFILE_SELECTION",
    "default_generated_materialization_target_profile",
    "generated_materialization_target_profile_from_payload",
]
