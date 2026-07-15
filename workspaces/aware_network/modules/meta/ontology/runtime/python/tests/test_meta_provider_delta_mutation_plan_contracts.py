from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_MUTATION_PLAN_CONTRACT_VERSION,
    META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION,
    MetaProviderDeltaMutationPlan,
    MetaProviderDeltaMutationStep,
)
from aware_meta.materialization.deltas.pipeline import (
    MetaProviderDeltaPipelineContext,
)


def test_mutation_plan_contract_normalizes_ready_steps() -> None:
    mutation_plan = MetaProviderDeltaMutationPlan.from_payload(_ready_mutation_plan())

    assert mutation_plan.ready is True
    assert mutation_plan.status == "mutation_plan_ready"
    assert mutation_plan.mutation_step_count == 2
    assert mutation_plan.blocked_mutation_step_count == 0
    assert mutation_plan.mutation_step_operation_counts == {
        "meta_ocg.attribute.update": 1,
        "meta_ocg.class.create": 1,
    }
    assert _descriptor_tree_payload_keys(mutation_plan.evidence_payload()) == ()
    assert not hasattr(mutation_plan, "descriptor_tree_execution_status")
    assert not hasattr(mutation_plan, "descriptor_tree_execution_draft_status")

    class_step = mutation_plan.steps_for_subject("class")[0]
    assert class_step.ready is True
    assert class_step.semantic_key == "home.NewDevice"
    assert class_step.function_ref == "aware_meta.object_config_graph.create_node"
    assert class_step.receiver_source == "semantic_key"
    assert class_step.dependencies == ("home.Graph",)
    assert class_step.arguments == {
        "type": "class",
        "node_key": "home.NewDevice",
    }

    attribute_step = mutation_plan.steps_for_subject("attribute")[0]
    assert attribute_step.receiver_entity_kind == "class_config"
    assert attribute_step.receiver_entity_id == "class-config-1"
    assert attribute_step.attribute_descriptor_kind == "primitive"
    assert attribute_step.method_binding["binding_key"] == (
        "aware_meta.class_config.create_primitive_attribute_config"
    )

    assert mutation_plan.evidence_payload()["contract_version"] == (
        META_PROVIDER_DELTA_MUTATION_PLAN_CONTRACT_VERSION
    )


def test_mutation_step_contract_preserves_blocked_receivers() -> None:
    step = MetaProviderDeltaMutationStep.from_payload(
        {
            "step_kind": "meta_ocg_provider_delta_mutation_step",
            "contract_version": META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION,
            "status": "mutation_step_blocked",
            "reason": "meta_ocg_attribute_mutation_requires_owner_typed_operation",
            "step_key": "meta_ocg_mutation:update:attribute:home.Device/name",
            "semantic_key": "home.Device/attribute:name",
            "operation_family": "update",
            "provider_operation_type": "meta_ocg.attribute.update",
            "ontology_subject_kind": "attribute",
            "receiver_semantic_key": "home.Device",
            "receiver_source": "blocked",
            "candidate_arguments": {"name": "name"},
            "blockers": ("missing_owner_typed_operation:home.Device",),
        }
    )

    assert step is not None
    assert step.blocked is True
    assert step.ready is False
    assert step.receiver_semantic_key == "home.Device"
    assert step.candidate_arguments == {"name": "name"}
    assert step.blockers == ("missing_owner_typed_operation:home.Device",)


def test_mutation_plan_contract_normalizes_partially_blocked_plan() -> None:
    mutation_plan = MetaProviderDeltaMutationPlan.from_payload(
        {
            "plan_kind": "meta_ocg_provider_delta_mutation_plan",
            "contract_version": META_PROVIDER_DELTA_MUTATION_PLAN_CONTRACT_VERSION,
            "status": "mutation_plan_partially_blocked",
            "reason": "meta_ocg_provider_delta_mutation_plan_has_blocked_steps",
            "available": True,
            "blocked": True,
            "mutation_step_count": 1,
            "blocked_mutation_step_count": 1,
            "mutation_steps": (_class_step(),),
            "blocked_mutation_steps": (
                {
                    **_attribute_step(),
                    "status": "mutation_step_blocked",
                    "reason": (
                        "meta_ocg_attribute_mutation_requires_owner_typed_operation"
                    ),
                    "function_ref": None,
                    "blockers": ("missing_owner_typed_operation:home.Device",),
                },
            ),
        }
    )

    assert mutation_plan.ready is False
    assert mutation_plan.partially_blocked is True
    assert mutation_plan.blocked is True
    assert len(mutation_plan.mutation_steps) == 1
    assert len(mutation_plan.blocked_mutation_steps) == 1
    assert mutation_plan.blocked_mutation_steps[0].blocked is True


def test_pipeline_context_keeps_mutation_plan_out_of_public_summary() -> None:
    context = _context().with_mutation_plan(_ready_mutation_plan())
    summary = context.evidence_summary()

    assert context.mutation_plan.ready is True
    assert context.mutation_plan_status == "mutation_plan_ready"
    assert context.mutation_plan_ready is True
    assert "legacy_mutation_plan_status" not in summary
    assert "legacy_descriptor_tree_execution_status" not in summary
    stage_statuses = cast(dict[str, object], summary["stage_statuses"])
    assert "legacy_descriptor_tree_mutation_plan" not in stage_statuses


def _context() -> MetaProviderDeltaPipelineContext:
    return MetaProviderDeltaPipelineContext.create(
        request=SimpleNamespace(),
        package_payload={"package_name": "home-ontology"},
        semantic_contract_payload={"provider_key": "aware_meta"},
        manifest_path="modules/home/structure/ontology/aware.toml",
        current_delta_fingerprint="sha256:current",
        provider_delta_execution_context_preflight={
            "status": "execution_context_available",
        },
        baseline_dirty_preflight={"status": "baseline_dirty_preflight_ready"},
    )


def _ready_mutation_plan() -> dict[str, object]:
    return {
        "plan_kind": "meta_ocg_provider_delta_mutation_plan",
        "contract_version": META_PROVIDER_DELTA_MUTATION_PLAN_CONTRACT_VERSION,
        "step_contract_version": META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION,
        "status": "mutation_plan_ready",
        "reason": "meta_ocg_provider_delta_mutation_plan_ready",
        "typed_operation_plan_status": "typed_operation_plan_ready",
        "typed_operation_count": 2,
        "semantic_object_anchor_count": 1,
        "blocked_typed_operation_count": 0,
        "source_operation_count": 2,
        "mutation_step_count": 2,
        "blocked_mutation_step_count": 0,
        "mutation_step_operation_counts": {
            "meta_ocg.attribute.update": 1,
            "meta_ocg.class.create": 1,
        },
        "blocked_mutation_step_reason_counts": {},
        "mutation_steps": (_class_step(), _attribute_step()),
        "blocked_mutation_steps": (),
        "available": True,
        "blocked": False,
    }


def _descriptor_tree_payload_keys(payload: dict[str, object]) -> tuple[str, ...]:
    return tuple(sorted(key for key in payload if "descriptor_tree" in key))


def _class_step() -> dict[str, object]:
    return {
        "step_kind": "meta_ocg_provider_delta_mutation_step",
        "contract_version": META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION,
        "status": "mutation_step_ready",
        "reason": "meta_ocg_provider_delta_mutation_step_ready",
        "step_key": "meta_ocg_mutation:create:class:home.NewDevice",
        "source_typed_operation_key": "op:class:create",
        "source_refs": ("aware/home/device.aware",),
        "semantic_key": "home.NewDevice",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.class.create",
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "function_ref": "aware_meta.object_config_graph.create_node",
        "receiver_semantic_key": "home.Graph",
        "receiver_object_id": "graph-1",
        "receiver_source": "semantic_key",
        "arguments": {"type": "class", "node_key": "home.NewDevice"},
        "argument_refs": {},
        "dependencies": ("home.Graph",),
        "baseline": {},
        "current": {"node_key": "home.NewDevice"},
        "blockers": (),
    }


def _attribute_step() -> dict[str, object]:
    return {
        "step_kind": "meta_ocg_provider_delta_mutation_step",
        "contract_version": META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION,
        "status": "mutation_step_ready",
        "reason": "meta_ocg_attribute_mutation_step_ready",
        "step_key": "meta_ocg_mutation:update:attribute:home.Device/name",
        "source_typed_operation_key": "op:attribute:update",
        "source_refs": ("aware/home/device.aware",),
        "semantic_key": "home.Device/attribute:name",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.attribute.update",
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "function_ref": (
            "aware_meta_ontology.class_.class_config."
            "ClassConfig.create_primitive_attribute_config"
        ),
        "receiver_semantic_key": "home.Device",
        "receiver_object_id": "class-config-1",
        "receiver_source": "semantic_node_contained_entity",
        "receiver_entity_kind": "class_config",
        "receiver_entity_id": "class-config-1",
        "receiver_entity_path": "object_config_graph_node.class_config",
        "arguments": {
            "name": "name",
            "primitive_base_type": "str",
            "is_required": True,
        },
        "argument_refs": {},
        "dependencies": ("home.Device",),
        "baseline": {"object_id": "attr-1"},
        "current": {"attribute_name": "name"},
        "blockers": (),
        "receiver_resolution": {
            "status": "attribute_receiver_resolved",
            "receiver_entity_id": "class-config-1",
        },
        "method_binding": {
            "status": "attribute_method_bound",
            "binding_key": "aware_meta.class_config.create_primitive_attribute_config",
            "function_ref": (
                "aware_meta_ontology.class_.class_config."
                "ClassConfig.create_primitive_attribute_config"
            ),
        },
        "attribute_descriptor_kind": "primitive",
        "attribute_descriptor_resolution": {
            "status": "attribute_descriptor_resolved",
            "descriptor_kind": "primitive",
        },
    }
