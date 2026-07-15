from __future__ import annotations

from dataclasses import dataclass


META_OCG_BINDING_MIRROR_CONTRACT_VERSION = (
    "aware.meta.ocg-binding-mirror-readiness.v0"
)
META_OCG_BINDING_MIRROR_CAPABILITY_KEY = "ocg.binding_mirror"
META_OCG_BINDING_SURFACE_KEY = "object_config_graph_binding"
META_OCG_MIRROR_SURFACE_KEY = "object_config_graph_mirror"

SURFACE_STATUS_READY = "ready"
SURFACE_STATUS_BLOCKED = "blocked"

BINDING_SEMANTIC_POLICY = "persisted_meta_graph_state"
MIRROR_SEMANTIC_POLICY = "authored_code_meta_rewrite_directive"


@dataclass(frozen=True, slots=True)
class MetaOcgBindingMirrorSurface:
    surface_key: str
    semantic_policy: str
    status: str
    required_ontology_functions: tuple[str, ...]
    required_handlers: tuple[str, ...]
    proof_refs: tuple[str, ...]
    blockers: tuple[str, ...] = ()

    def evidence_payload(self) -> dict[str, object]:
        return {
            "surface_key": self.surface_key,
            "semantic_policy": self.semantic_policy,
            "status": self.status,
            "required_ontology_functions": self.required_ontology_functions,
            "required_handlers": self.required_handlers,
            "proof_refs": self.proof_refs,
            "blockers": self.blockers,
        }


@dataclass(frozen=True, slots=True)
class MetaOcgBindingMirrorReadinessContract:
    capability_key: str
    binding_surface: MetaOcgBindingMirrorSurface
    mirror_surface: MetaOcgBindingMirrorSurface
    code_owns_meta_mutation: bool
    contract_version: str = META_OCG_BINDING_MIRROR_CONTRACT_VERSION

    @property
    def status(self) -> str:
        if self.binding_surface.status == SURFACE_STATUS_READY and (
            self.mirror_surface.status == SURFACE_STATUS_READY
        ):
            return SURFACE_STATUS_READY
        return "partial"

    @property
    def blockers(self) -> tuple[str, ...]:
        return (*self.binding_surface.blockers, *self.mirror_surface.blockers)

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "capability_key": self.capability_key,
            "status": self.status,
            "code_owns_meta_mutation": self.code_owns_meta_mutation,
            "binding_surface": self.binding_surface.evidence_payload(),
            "mirror_surface": self.mirror_surface.evidence_payload(),
            "blockers": self.blockers,
        }


def meta_ocg_binding_mirror_readiness_contract() -> (
    MetaOcgBindingMirrorReadinessContract
):
    return MetaOcgBindingMirrorReadinessContract(
        capability_key=META_OCG_BINDING_MIRROR_CAPABILITY_KEY,
        code_owns_meta_mutation=False,
        binding_surface=MetaOcgBindingMirrorSurface(
            surface_key=META_OCG_BINDING_SURFACE_KEY,
            semantic_policy=BINDING_SEMANTIC_POLICY,
            status=SURFACE_STATUS_READY,
            required_ontology_functions=(
                "ObjectConfigGraph.create_object_config_graph_binding",
                "ObjectConfigGraphBinding.create_class",
                "ObjectProjectionGraphNode.create_key",
                "ObjectProjectionGraphNodeKey.build_via_object_projection_graph_node",
            ),
            required_handlers=(
                "aware_meta.handlers.impl.config.object_config_graph",
                "aware_meta.handlers.impl.config.object_config_graph_binding",
                "aware_meta.handlers.impl.config.object_config_graph_binding_class",
                "aware_meta.handlers.impl.projection.object_projection_graph_node",
                "aware_meta.handlers.impl.projection.object_projection_graph_node_key",
            ),
            proof_refs=(
                "tests/test_object_config_graph_binding_handlers.py",
                "tests/test_object_config_graph_binding_module_proof.py",
                "tests/test_object_projection_graph_handlers.py",
            ),
        ),
        mirror_surface=MetaOcgBindingMirrorSurface(
            surface_key=META_OCG_MIRROR_SURFACE_KEY,
            semantic_policy=MIRROR_SEMANTIC_POLICY,
            status=SURFACE_STATUS_BLOCKED,
            required_ontology_functions=(),
            required_handlers=(
                "aware_meta.graph.config.mirror.apply.apply_object_config_graph_mirrors_to_build_inputs",
                "aware_meta.graph.config.mirror.apply.apply_object_config_graph_mirrors",
            ),
            proof_refs=(
                "tests/test_mirror_legality_and_shape.py",
                "tests/test_mirror_local_api_symbol_resolution.py",
                "tests/test_mirror_transitive_api_rewrite.py",
            ),
            blockers=("mirror_rewrite_typed_operations_missing",),
        ),
    )


def meta_ocg_binding_mirror_contract_payload() -> dict[str, object]:
    return meta_ocg_binding_mirror_readiness_contract().evidence_payload()


__all__ = [
    "BINDING_SEMANTIC_POLICY",
    "META_OCG_BINDING_MIRROR_CAPABILITY_KEY",
    "META_OCG_BINDING_MIRROR_CONTRACT_VERSION",
    "META_OCG_BINDING_SURFACE_KEY",
    "META_OCG_MIRROR_SURFACE_KEY",
    "MIRROR_SEMANTIC_POLICY",
    "SURFACE_STATUS_BLOCKED",
    "SURFACE_STATUS_READY",
    "MetaOcgBindingMirrorReadinessContract",
    "MetaOcgBindingMirrorSurface",
    "meta_ocg_binding_mirror_contract_payload",
    "meta_ocg_binding_mirror_readiness_contract",
]
