from __future__ import annotations

from dataclasses import dataclass


META_OCG_ANNOTATION_COMPILE_CONTRACT_VERSION = (
    "aware.meta.ocg-annotation-compile-readiness.v0"
)
META_OCG_ANNOTATION_SEMANTICS_CAPABILITY_KEY = "ocg.annotation_semantics"

SURFACE_STATUS_READY = "ready"
SURFACE_STATUS_PARTIAL = "partial"
SURFACE_STATUS_BLOCKED = "blocked"

ANNOTATION_WRAPPER_COMPILE_SURFACE = "object_config_graph_annotation_wrapper_compile"
ANNOTATION_RELATIONSHIP_LOAD_POLICY_SURFACE = "relationship_load_policy_effect"
ANNOTATION_OVERLAY_RECOMPUTE_SURFACE = "overlay_recompute_effect"
ANNOTATION_VALIDATION_ONLY_SURFACE = "validation_only_effects"
ANNOTATION_RELATIONSHIP_OVERRIDE_SURFACE = "relationship_override_effect"
ANNOTATION_REFERENCE_STORAGE_SURFACE = "reference_storage_effects"


@dataclass(frozen=True, slots=True)
class MetaOcgAnnotationCompileSurface:
    surface_key: str
    status: str
    annotation_verbs: tuple[str, ...]
    semantic_policy: str
    effect_policy: str
    proof_refs: tuple[str, ...]
    blockers: tuple[str, ...] = ()

    def evidence_payload(self) -> dict[str, object]:
        return {
            "surface_key": self.surface_key,
            "status": self.status,
            "annotation_verbs": self.annotation_verbs,
            "semantic_policy": self.semantic_policy,
            "effect_policy": self.effect_policy,
            "proof_refs": self.proof_refs,
            "blockers": self.blockers,
        }


@dataclass(frozen=True, slots=True)
class MetaOcgAnnotationCompileReadinessContract:
    capability_key: str
    surfaces: tuple[MetaOcgAnnotationCompileSurface, ...]
    code_owns_meta_mutation: bool
    contract_version: str = META_OCG_ANNOTATION_COMPILE_CONTRACT_VERSION

    @property
    def status(self) -> str:
        if all(surface.status == SURFACE_STATUS_READY for surface in self.surfaces):
            return SURFACE_STATUS_READY
        if any(surface.status == SURFACE_STATUS_READY for surface in self.surfaces):
            return SURFACE_STATUS_PARTIAL
        return SURFACE_STATUS_BLOCKED

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(
            blocker
            for surface in self.surfaces
            for blocker in surface.blockers
        )

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "capability_key": self.capability_key,
            "status": self.status,
            "code_owns_meta_mutation": self.code_owns_meta_mutation,
            "surfaces": tuple(surface.evidence_payload() for surface in self.surfaces),
            "blockers": self.blockers,
            "ready_surface_keys": tuple(
                surface.surface_key
                for surface in self.surfaces
                if surface.status == SURFACE_STATUS_READY
            ),
            "blocked_surface_keys": tuple(
                surface.surface_key
                for surface in self.surfaces
                if surface.status == SURFACE_STATUS_BLOCKED
            ),
        }


def meta_ocg_annotation_compile_readiness_contract() -> (
    MetaOcgAnnotationCompileReadinessContract
):
    return MetaOcgAnnotationCompileReadinessContract(
        capability_key=META_OCG_ANNOTATION_SEMANTICS_CAPABILITY_KEY,
        code_owns_meta_mutation=False,
        surfaces=(
            MetaOcgAnnotationCompileSurface(
                surface_key=ANNOTATION_WRAPPER_COMPILE_SURFACE,
                status=SURFACE_STATUS_READY,
                annotation_verbs=(
                    "load",
                    "discriminate",
                    "oneof",
                    "identity",
                    "overlay",
                    "override",
                    "reference",
                    "index",
                    "storage",
                ),
                semantic_policy="deterministic_object_config_graph_annotation_wrapper_compile",
                effect_policy="hash_participating_ocg_annotation_records",
                proof_refs=(
                    "tests/test_ocg_annotations_stable_ids.py",
                    "tests/test_ocg_annotations_compilation.py",
                ),
            ),
            MetaOcgAnnotationCompileSurface(
                surface_key=ANNOTATION_RELATIONSHIP_LOAD_POLICY_SURFACE,
                status=SURFACE_STATUS_READY,
                annotation_verbs=("load",),
                semantic_policy="annotation_effect_typed_operation",
                effect_policy="ClassConfigRelationship.update_config",
                proof_refs=(
                    "tests/provider_delta/test_relationship_scope_closure.py",
                    "tests/provider_delta/test_source_projection.py",
                ),
            ),
            MetaOcgAnnotationCompileSurface(
                surface_key=ANNOTATION_OVERLAY_RECOMPUTE_SURFACE,
                status=SURFACE_STATUS_READY,
                annotation_verbs=("overlay",),
                semantic_policy="deterministic_recompute_from_annotation_wrappers",
                effect_policy="ObjectConfigGraphOverlay recompute",
                proof_refs=(
                    "tests/test_overlay_stable_ids.py",
                    "aware_meta.graph.config.namespace.layout_contract",
                ),
            ),
            MetaOcgAnnotationCompileSurface(
                surface_key=ANNOTATION_VALIDATION_ONLY_SURFACE,
                status=SURFACE_STATUS_READY,
                annotation_verbs=("discriminate", "index"),
                semantic_policy="validation_only_annotation_effect",
                effect_policy="validate annotations against committed OCG class topology",
                proof_refs=(
                    "tests/test_ocg_annotations_discriminate_validation.py",
                    "tests/test_ocg_annotations_compilation.py",
                ),
            ),
            MetaOcgAnnotationCompileSurface(
                surface_key=ANNOTATION_RELATIONSHIP_OVERRIDE_SURFACE,
                status=SURFACE_STATUS_BLOCKED,
                annotation_verbs=("override",),
                semantic_policy="relationship_annotation_effect",
                effect_policy="relationship FK/relationship override mutation",
                proof_refs=("aware_meta.graph.config.annotation.handlers",),
                blockers=("annotation_override_effect_typed_operations_missing",),
            ),
            MetaOcgAnnotationCompileSurface(
                surface_key=ANNOTATION_REFERENCE_STORAGE_SURFACE,
                status=SURFACE_STATUS_BLOCKED,
                annotation_verbs=("reference", "storage", "oneof", "identity"),
                semantic_policy="annotation_effect_typed_operation_required",
                effect_policy="reference/storage/identity semantic effect execution",
                proof_refs=("aware_meta.graph.config.annotation.compiler",),
                blockers=(
                    "annotation_reference_effect_typed_operations_missing",
                    "annotation_storage_effect_typed_operations_missing",
                    "annotation_identity_effect_typed_operations_missing",
                ),
            ),
        ),
    )


def meta_ocg_annotation_compile_contract_payload() -> dict[str, object]:
    return meta_ocg_annotation_compile_readiness_contract().evidence_payload()


__all__ = [
    "ANNOTATION_OVERLAY_RECOMPUTE_SURFACE",
    "ANNOTATION_REFERENCE_STORAGE_SURFACE",
    "ANNOTATION_RELATIONSHIP_LOAD_POLICY_SURFACE",
    "ANNOTATION_RELATIONSHIP_OVERRIDE_SURFACE",
    "ANNOTATION_VALIDATION_ONLY_SURFACE",
    "ANNOTATION_WRAPPER_COMPILE_SURFACE",
    "META_OCG_ANNOTATION_COMPILE_CONTRACT_VERSION",
    "META_OCG_ANNOTATION_SEMANTICS_CAPABILITY_KEY",
    "MetaOcgAnnotationCompileReadinessContract",
    "MetaOcgAnnotationCompileSurface",
    "SURFACE_STATUS_BLOCKED",
    "SURFACE_STATUS_PARTIAL",
    "SURFACE_STATUS_READY",
    "meta_ocg_annotation_compile_contract_payload",
    "meta_ocg_annotation_compile_readiness_contract",
]
