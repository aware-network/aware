from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.target_impact import (
    provider_delta_language_target_impact_plan,
)


def test_function_impl_update_targets_runtime_handlers_only() -> None:
    plan = provider_delta_language_target_impact_plan(
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _typed_operation(
                subject_kind="function_impl",
                operation_family="update",
                provider_operation_type="meta_ocg.function_impl.update",
            )
        ),
        target_payloads=_language_targets(),
    )

    assert plan["impact_policy"] == "function_impl_runtime_handlers_only"
    assert plan["render_all"] is False
    assert plan["required_target_groups"] == ("runtime_handlers",)
    assert plan["selected_target_indexes"] == (0, 1)
    assert plan["skipped_target_indexes"] == (2, 3, 4, 5)
    assert plan["operation_type_counts"] == {"meta_ocg.function_impl.update": 1}


def test_structural_relationship_update_skips_runtime_handlers() -> None:
    plan = provider_delta_language_target_impact_plan(
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _typed_operation(
                subject_kind="relationship",
                operation_family="update",
                provider_operation_type="meta_ocg.relationship.update",
            )
        ),
        target_payloads=_language_targets(),
    )

    assert plan["impact_policy"] == "structural_language_targets_only"
    assert plan["render_all"] is False
    assert plan["required_target_groups"] == ("structural",)
    assert plan["selected_target_indexes"] == (2, 3, 4, 5)
    assert plan["skipped_target_indexes"] == (0, 1)
    assert plan["ontology_subject_kind_counts"] == {"relationship": 1}


def test_structural_attribute_create_ignores_anchor_operations() -> None:
    plan = provider_delta_language_target_impact_plan(
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _typed_operation(
                subject_kind="class",
                operation_family="anchor",
                provider_operation_type="meta_ocg.class.anchor",
            ),
            _typed_operation(
                subject_kind="attribute",
                operation_family="create",
                provider_operation_type="meta_ocg.attribute.create",
            ),
        ),
        target_payloads=_language_targets(),
    )

    assert plan["impact_policy"] == "structural_language_targets_only"
    assert plan["selected_target_indexes"] == (2, 3, 4, 5)
    assert plan["operation_count"] == 1
    assert plan["operation_type_counts"] == {"meta_ocg.attribute.create": 1}


def test_mixed_function_impl_and_structural_operations_selects_union() -> None:
    plan = provider_delta_language_target_impact_plan(
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _typed_operation(
                subject_kind="function_impl",
                operation_family="update",
                provider_operation_type="meta_ocg.function_impl.update",
            ),
            _typed_operation(
                subject_kind="attribute",
                operation_family="update",
                provider_operation_type="meta_ocg.attribute.update",
            ),
        ),
        target_payloads=_language_targets(),
    )

    assert plan["impact_policy"] == "supported_operation_target_union"
    assert plan["reason"] == "supported_operation_target_union"
    assert plan["render_all"] is False
    assert plan["required_target_groups"] == ("runtime_handlers", "structural")
    assert plan["selected_target_indexes"] == (0, 1, 2, 3, 4, 5)
    assert plan["skipped_target_indexes"] == ()


def test_function_description_update_targets_structural_outputs_only() -> None:
    plan = provider_delta_language_target_impact_plan(
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _function_description_update_operation()
        ),
        target_payloads=_language_targets(),
    )

    assert plan["impact_policy"] == "structural_language_targets_only"
    assert plan["render_all"] is False
    assert plan["required_target_groups"] == ("structural",)
    assert plan["selected_target_indexes"] == (2, 3, 4, 5)
    assert plan["skipped_target_indexes"] == (0, 1)


def test_function_signature_update_targets_runtime_and_structural_outputs() -> None:
    plan = provider_delta_language_target_impact_plan(
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _function_signature_update_operation()
        ),
        target_payloads=_language_targets(),
    )

    assert plan["impact_policy"] == "supported_operation_target_union"
    assert plan["render_all"] is False
    assert plan["required_target_groups"] == ("runtime_handlers", "structural")
    assert plan["selected_target_indexes"] == (0, 1, 2, 3, 4, 5)
    assert plan["skipped_target_indexes"] == ()


def test_function_membership_update_targets_structural_outputs_only() -> None:
    plan = provider_delta_language_target_impact_plan(
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _typed_operation(
                subject_kind="function_membership",
                operation_family="update",
                provider_operation_type="meta_ocg.function_membership.update",
            )
        ),
        target_payloads=_language_targets(),
    )

    assert plan["impact_policy"] == "structural_language_targets_only"
    assert plan["render_all"] is False
    assert plan["required_target_groups"] == ("structural",)
    assert plan["selected_target_indexes"] == (2, 3, 4, 5)
    assert plan["skipped_target_indexes"] == (0, 1)


def test_missing_typed_operation_plan_renders_all() -> None:
    plan = provider_delta_language_target_impact_plan(
        provider_delta_typed_operation_plan=None,
        target_payloads=_language_targets(),
    )

    assert plan["impact_policy"] == "render_all"
    assert plan["reason"] == "typed_operation_plan_missing"
    assert plan["required_target_groups"] == ()
    assert plan["selected_target_count"] == 6
    assert plan["skipped_target_count"] == 0


def test_blocked_typed_operation_plan_renders_all() -> None:
    plan = provider_delta_language_target_impact_plan(
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_blocked",
            "reason": "meta_ocg_provider_delta_typed_operation_plan_blocked",
            "typed_operations": (),
        },
        target_payloads=_language_targets(),
    )

    assert plan["impact_policy"] == "render_all"
    assert plan["reason"] == "typed_operation_plan_not_ready"
    assert plan["typed_operation_plan_status"] == "typed_operation_plan_blocked"
    assert plan["selected_target_indexes"] == (0, 1, 2, 3, 4, 5)


def _typed_operation_plan(
    *typed_operations: Mapping[str, object],
) -> dict[str, object]:
    return {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operations": typed_operations,
    }


def _typed_operation(
    *,
    subject_kind: str,
    operation_family: str,
    provider_operation_type: str,
) -> dict[str, object]:
    semantic_key = f"ocg:aware_demo/{subject_kind}:demo"
    return {
        "operation_key": f"meta_ocg_provider_delta:{operation_family}:{semantic_key}",
        "operation_family": operation_family,
        "provider_operation_type": provider_operation_type,
        "semantic_key": semantic_key,
        "ontology_subject_kind": subject_kind,
    }


def _function_description_update_operation() -> dict[str, object]:
    operation = _typed_operation(
        subject_kind="function",
        operation_family="update",
        provider_operation_type="meta_ocg.function.update",
    )
    baseline_signature = {
        "owner_key": "aware_demo.default.home.TvChannel",
        "name": "rename",
        "kind": "instance",
        "description": "Rename the channel display label.",
        "inputs": (),
        "outputs": (),
    }
    current_signature = {
        **baseline_signature,
        "description": "Rename the channel display label for assistants.",
    }
    operation["baseline"] = {
        "object": {"function_signature": baseline_signature},
    }
    operation["current"] = {"function_signature": current_signature}
    return operation


def _function_signature_update_operation() -> dict[str, object]:
    operation = _function_description_update_operation()
    operation["current"] = {
        "function_signature": {
            "owner_key": "aware_demo.default.home.TvChannel",
            "name": "rename",
            "kind": "instance",
            "description": "Rename the channel display label for assistants.",
            "inputs": (
                {
                    "name": "display_name",
                    "type": "input",
                    "position": 0,
                    "is_required": True,
                },
            ),
            "outputs": (),
        },
    }
    return operation


def _language_targets() -> tuple[dict[str, object], ...]:
    return (
        _target(
            target_index=0,
            materialization_source="runtime_handlers",
            code_package_surface="runtime",
            renderer_kind="runtime_handlers_impl",
        ),
        _target(
            target_index=1,
            materialization_source="runtime_handlers",
            code_package_surface="runtime",
            renderer_kind="runtime_handlers_meta",
        ),
        _target(
            target_index=2,
            materialization_source="ontology_dto",
            code_package_surface="structure",
            renderer_profile="ontology_dto",
        ),
        _target(
            target_index=3,
            materialization_source="ontology",
            code_package_surface="structure",
            renderer_profile="orm_runtime",
        ),
        _target(
            target_index=4,
            materialization_source="ontology_orm_models",
            code_package_surface="structure",
            renderer_profile="orm_models",
        ),
        _target(
            target_index=5,
            materialization_source="ontology",
            code_package_surface="structure",
            target_language_plugin_id="sql",
            renderer_profile="orm_runtime",
        ),
    )


def _target(
    *,
    target_index: int,
    materialization_source: str,
    code_package_surface: str,
    target_language_plugin_id: str = "python",
    renderer_profile: str | None = None,
    renderer_kind: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "target_index": target_index,
        "target_language_plugin_id": target_language_plugin_id,
        "output_root": f"target-{target_index}",
        "import_root": "aware_demo_ontology",
        "package_name": "demo-ontology",
        "materialization_source": materialization_source,
        "code_package_surface": code_package_surface,
        "source_is_runtime": materialization_source == "runtime_handlers",
    }
    if renderer_profile is not None:
        payload["renderer_profile"] = renderer_profile
    if renderer_kind is not None:
        payload["renderer_kind"] = renderer_kind
    return payload
