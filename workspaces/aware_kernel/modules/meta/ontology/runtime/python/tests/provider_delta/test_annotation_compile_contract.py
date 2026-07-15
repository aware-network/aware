from __future__ import annotations

from typing import cast

from aware_meta.graph.config.annotation.compile_contract import (
    ANNOTATION_OVERLAY_RECOMPUTE_SURFACE,
    ANNOTATION_REFERENCE_STORAGE_SURFACE,
    ANNOTATION_RELATIONSHIP_LOAD_POLICY_SURFACE,
    ANNOTATION_RELATIONSHIP_OVERRIDE_SURFACE,
    ANNOTATION_VALIDATION_ONLY_SURFACE,
    ANNOTATION_WRAPPER_COMPILE_SURFACE,
    META_OCG_ANNOTATION_COMPILE_CONTRACT_VERSION,
    META_OCG_ANNOTATION_SEMANTICS_CAPABILITY_KEY,
    SURFACE_STATUS_BLOCKED,
    SURFACE_STATUS_READY,
    meta_ocg_annotation_compile_contract_payload,
)


def test_annotation_compile_contract_splits_wrapper_compile_from_effects() -> None:
    payload = meta_ocg_annotation_compile_contract_payload()
    surface_payloads = cast(tuple[dict[str, object], ...], payload["surfaces"])
    surfaces = {
        str(surface["surface_key"]): surface
        for surface in surface_payloads
    }

    assert payload["contract_version"] == META_OCG_ANNOTATION_COMPILE_CONTRACT_VERSION
    assert payload["capability_key"] == META_OCG_ANNOTATION_SEMANTICS_CAPABILITY_KEY
    assert payload["status"] == "partial"
    assert payload["code_owns_meta_mutation"] is False
    assert payload["ready_surface_keys"] == (
        ANNOTATION_WRAPPER_COMPILE_SURFACE,
        ANNOTATION_RELATIONSHIP_LOAD_POLICY_SURFACE,
        ANNOTATION_OVERLAY_RECOMPUTE_SURFACE,
        ANNOTATION_VALIDATION_ONLY_SURFACE,
    )
    assert payload["blocked_surface_keys"] == (
        ANNOTATION_RELATIONSHIP_OVERRIDE_SURFACE,
        ANNOTATION_REFERENCE_STORAGE_SURFACE,
    )

    wrapper_surface = surfaces[ANNOTATION_WRAPPER_COMPILE_SURFACE]
    assert wrapper_surface["status"] == SURFACE_STATUS_READY
    assert wrapper_surface["annotation_verbs"] == (
        "load",
        "discriminate",
        "oneof",
        "identity",
        "overlay",
        "override",
        "reference",
        "index",
        "storage",
    )

    load_surface = surfaces[ANNOTATION_RELATIONSHIP_LOAD_POLICY_SURFACE]
    assert load_surface["status"] == SURFACE_STATUS_READY
    assert load_surface["effect_policy"] == "ClassConfigRelationship.update_config"

    overlay_surface = surfaces[ANNOTATION_OVERLAY_RECOMPUTE_SURFACE]
    assert overlay_surface["status"] == SURFACE_STATUS_READY
    assert overlay_surface["annotation_verbs"] == ("overlay",)

    override_surface = surfaces[ANNOTATION_RELATIONSHIP_OVERRIDE_SURFACE]
    assert override_surface["status"] == SURFACE_STATUS_BLOCKED
    assert override_surface["blockers"] == (
        "annotation_override_effect_typed_operations_missing",
    )

    reference_storage_surface = surfaces[ANNOTATION_REFERENCE_STORAGE_SURFACE]
    assert reference_storage_surface["status"] == SURFACE_STATUS_BLOCKED
    assert reference_storage_surface["blockers"] == (
        "annotation_reference_effect_typed_operations_missing",
        "annotation_storage_effect_typed_operations_missing",
        "annotation_identity_effect_typed_operations_missing",
    )
    assert payload["blockers"] == (
        "annotation_override_effect_typed_operations_missing",
        "annotation_reference_effect_typed_operations_missing",
        "annotation_storage_effect_typed_operations_missing",
        "annotation_identity_effect_typed_operations_missing",
    )
