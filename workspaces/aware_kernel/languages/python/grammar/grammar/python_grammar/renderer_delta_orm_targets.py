from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.coercion import mapping_value, optional_text


ORM_RUNTIME_TARGET_DESCRIPTOR_KEY = "orm_runtime"
ORM_RUNTIME_TARGET_LANGUAGE = "python"
ORM_RUNTIME_RENDERER_PROFILE = "orm_runtime"
ORM_RUNTIME_MATERIALIZATION_SOURCE = "ontology_orm_models"
ORM_RUNTIME_PRODUCT_INTENT = "orm_runtime"


def orm_runtime_target_payload(payload: Mapping[str, object]) -> dict[str, object]:
    generated = mapping_value(payload.get("generated_materialization"))
    targets = mapping_value(generated.get("targets"))
    direct_target = mapping_value(targets.get(ORM_RUNTIME_TARGET_DESCRIPTOR_KEY))
    if direct_target:
        return direct_target
    for target_payload in targets.values():
        target = mapping_value(target_payload)
        if _is_orm_runtime_target(target):
            return target
    return {}


def _is_orm_runtime_target(target: Mapping[str, object]) -> bool:
    return (
        optional_text(target.get("target_language")) == ORM_RUNTIME_TARGET_LANGUAGE
        and optional_text(target.get("renderer_profile"))
        == ORM_RUNTIME_RENDERER_PROFILE
        and optional_text(target.get("materialization_source"))
        == ORM_RUNTIME_MATERIALIZATION_SOURCE
    )


__all__ = [
    "ORM_RUNTIME_MATERIALIZATION_SOURCE",
    "ORM_RUNTIME_PRODUCT_INTENT",
    "ORM_RUNTIME_RENDERER_PROFILE",
    "ORM_RUNTIME_TARGET_DESCRIPTOR_KEY",
    "ORM_RUNTIME_TARGET_LANGUAGE",
    "orm_runtime_target_payload",
]
