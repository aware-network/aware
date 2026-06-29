from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization.deltas.code_dto import (
    CodeSectionDeltaEntry,
    CodeSectionDeltaOperationKind,
)
from aware_meta.materialization.deltas.change_evidence import (
    _provider_delta_semantic_change_report,
)
from aware_meta.materialization.deltas.source_projection import (
    META_SEMANTIC_APPLY_SOURCE_PROJECTION_EVIDENCE_CONTRACT_VERSION,
    META_SOURCE_PROJECTION_PROVIDER_KEY,
    code_section_delta_entries_from_meta_function_impl_typed_operations,
    code_source_projection_result_from_meta_feature_results,
    code_source_projection_request_from_meta_change_report,
    provider_delta_result_from_semantic_apply_source_projection_evidence,
    provider_delta_source_projection_stage,
    source_projection_feature_results_from_meta_typed_operations,
    typed_operation_plan_from_semantic_source_meaning,
)
from aware_meta.semantic_operation_resolution import (
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION,
    resolve_meta_semantic_operation_function_call_plan_previews,
)

from .fixtures import provider_delta_uuid


def test_meta_function_impl_typed_operation_emits_code_section_delta_entry() -> None:
    typed_operation_plan = _typed_operation_plan(_function_impl_operation())
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        typed_operation_plan
    )
    entries = code_section_delta_entries_from_meta_function_impl_typed_operations(
        typed_operation_plan
    )

    assert len(feature_results) == 1
    assert feature_results[0].feature_key == "function_impl"
    assert feature_results[0].status == "source_projection_projected"
    assert feature_results[0].reason == (
        "meta_source_projection_function_impl_section_delta_ready"
    )
    assert feature_results[0].projected is True
    assert feature_results[0].missing_evidence_fields == ()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.operation is CodeSectionDeltaOperationKind.replace_segment
    assert entry.provider_key == META_SOURCE_PROJECTION_PROVIDER_KEY
    assert entry.event_ref == (
        "aware_meta.provider_delta.world_change.function_impl.update"
    )
    assert entry.semantic_key == (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel.rename"
        "/function_impl:default"
    )
    assert entry.content_text == "set name = display_name"
    assert entry.after_hash == _digest("set name = display_name")
    assert entry.section_ref.relative_path == "home/tv_channel.aware"
    assert entry.section_ref.language == "aware"
    assert entry.section_ref.section_type == "function"
    assert entry.section_ref.qualname == "TvChannel.rename"
    assert entry.section_ref.source_refs == ["home/tv_channel.aware"]
    assert entry.segment_ref is not None
    assert entry.segment_ref.segment_name == "body"
    assert entry.segment_ref.before_segment_hash == _digest("")


def test_meta_semantic_apply_attribute_structural_create_builds_operation() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
                "manifest_relative_path": (
                    "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml"
                ),
                "delta_fingerprint": "sha256:attribute-structural-create",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.attribute:"
                                "ContentLayout.title:create"
                            ),
                            "operation_family": "create",
                            "semantic_operation_type": (
                                META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION
                            ),
                            "semantic_key": "meta.attribute:ContentLayout.title",
                            "semantic_subject_type": "aware_meta.AttributeConfig",
                            "field_path": "definition",
                            "event_key": (
                                "meta.attribute:ContentLayout.title:"
                                "definition:upsert"
                            ),
                            "source_refs": ("content/content_layout.aware",),
                            "before_payload": None,
                            "after_payload": {
                                "definition": "title String",
                                "class_name": "ContentLayout",
                                "attribute_name": "title",
                                "type": "String",
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_layout.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    operations = cast(tuple[dict[str, object], ...], typed_plan["typed_operations"])
    assert len(operations) == 1
    operation = operations[0]
    assert operation["operation_family"] == "create"
    assert operation["provider_operation_type"] == "meta_ocg.attribute.create"
    assert operation["ontology_subject_kind"] == "attribute"
    current = _mapping(operation["current"])
    signature = _mapping(current["attribute_signature"])
    generated = _mapping(current["generated_materialization"])
    python_orm = _mapping(generated["python_orm"])
    assert current["owner_semantic_key"] == "meta.class:ContentLayout"
    assert current["owner_key"] == "aware_content.default.content.ContentLayout"
    assert current["attribute_name"] == "title"
    assert signature["type_descriptor"] == {
        "kind": "primitive",
        "primitive_base_type": "string",
    }
    assert python_orm["relative_path"] == (
        "aware_content_ontology/content/content_layout.py"
    )


def test_meta_semantic_apply_attribute_structural_delete_builds_operation() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
                "manifest_relative_path": (
                    "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml"
                ),
                "delta_fingerprint": "sha256:attribute-structural-delete",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.attribute:"
                                "ContentLayout.title:delete"
                            ),
                            "operation_family": "delete",
                            "semantic_operation_type": (
                                META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION
                            ),
                            "semantic_key": "meta.attribute:ContentLayout.title",
                            "semantic_subject_type": "aware_meta.AttributeConfig",
                            "field_path": "definition",
                            "event_key": (
                                "meta.attribute:ContentLayout.title:"
                                "definition:delete"
                            ),
                            "source_refs": ("content/content_layout.aware",),
                            "before_payload": {
                                "definition": "title String",
                                "class_name": "ContentLayout",
                                "attribute_name": "title",
                                "type": "String",
                            },
                            "after_payload": None,
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_layout.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    operations = cast(tuple[dict[str, object], ...], typed_plan["typed_operations"])
    assert len(operations) == 1
    operation = operations[0]
    assert operation["operation_family"] == "delete"
    assert operation["provider_operation_type"] == "meta_ocg.attribute.delete"
    current = _mapping(operation["current"])
    baseline = _mapping(operation["baseline"])
    baseline_object = _mapping(baseline["object"])
    assert current["owner_semantic_key"] == "meta.class:ContentLayout"
    assert current["owner_key"] == "aware_content.default.content.ContentLayout"
    assert current["attribute_name"] == "title"
    assert baseline["object_id"] == current["attribute_config_id"]
    assert baseline_object["attribute_name"] == "title"


def test_meta_attribute_structural_resolution_exposes_generated_intent() -> None:
    class_config_id = str(provider_delta_uuid("semantic-op-attr-owner-class"))
    create_resolution, delete_resolution = (
        resolve_meta_semantic_operation_function_call_plan_previews(
            typed_operations=(
                _attribute_structural_create_semantic_operation(),
                _attribute_structural_delete_semantic_operation(),
            ),
            current_semantic_object_ids={
                "meta.class:ContentLayout": class_config_id,
            },
        )
    )

    assert create_resolution.status == "function_call_plan_blocked"
    assert delete_resolution.status == "function_call_plan_blocked"
    for resolution, operation_kind in (
        (create_resolution, "create"),
        (delete_resolution, "delete"),
    ):
        metadata = dict(resolution.metadata)
        assert metadata["execution_ready"] is True
        assert metadata["receiver_object_id"] == class_config_id
        assert metadata["provider_delta_typed_operation_status"] == (
            "provider_delta_typed_operation_ready"
        )
        assert metadata["generated_materialization_intent_status"] == (
            "generated_materialization_intent_ready"
        )
        intent = _mapping(metadata["generated_materialization_intent"])
        assert intent["renderer_key"] == "python.orm.attribute.field"
        assert intent["policy_key"] == (
            f"aware_meta.python_orm.attribute.{operation_kind}"
        )
        typed_plan = _mapping(
            metadata["provider_delta_generated_materialization_typed_operation_plan"]
        )
        typed_operations = cast(
            tuple[dict[str, object], ...],
            typed_plan["typed_operations"],
        )
        assert typed_operations[0]["provider_operation_type"] == (
            f"meta_ocg.attribute.{operation_kind}"
        )


def test_meta_source_projection_normalizes_code_language_enum_values() -> None:
    typed_operation_plan = _typed_operation_plan(_function_impl_operation())
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        typed_operation_plan,
        package_name="home-ontology",
        target_language=CodeLanguage.aware,
    )

    assert len(feature_results) == 1
    entry = feature_results[0].entries[0]
    payload = entry.model_dump(mode="json")
    section_ref = cast(dict[str, object], payload["section_ref"])

    assert entry.section_ref.language == "aware"
    assert section_ref["language"] == "aware"
    assert CodeSectionDeltaEntry.model_validate(payload).section_ref.language == (
        "aware"
    )


def test_meta_function_impl_section_delta_adapter_does_not_guess_missing_evidence() -> (
    None
):
    operation = _function_impl_operation()
    current = dict(cast(dict[str, object], operation["current"]))
    current.pop("source_projection")
    operation["current"] = current

    entries = code_section_delta_entries_from_meta_function_impl_typed_operations(
        _typed_operation_plan(operation)
    )
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        _typed_operation_plan(operation)
    )

    assert entries == ()
    assert len(feature_results) == 1
    assert feature_results[0].feature_key == "function_impl"
    assert feature_results[0].status == "source_projection_skipped"
    assert feature_results[0].reason == (
        "meta_source_projection_function_impl_requires_explicit_section_evidence"
    )
    assert feature_results[0].missing_evidence_fields == (
        "content_text",
        "segment_name",
        "section_identity",
    )


def test_meta_source_projection_section_delta_adapter_skips_structural_operations() -> (
    None
):
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        _typed_operation_plan(_attribute_operation())
    )
    entries = code_section_delta_entries_from_meta_function_impl_typed_operations(
        _typed_operation_plan(_attribute_operation())
    )

    assert len(feature_results) == 1
    assert feature_results[0].feature_key == "attribute_config"
    assert feature_results[0].status == "source_projection_skipped"
    assert feature_results[0].reason == (
        "meta_source_projection_attribute_config_requires_renderer_segment_policy"
    )
    assert entries == ()


def test_meta_attribute_config_primitive_type_update_emits_code_section_delta_entry() -> (
    None
):
    typed_operation_plan = _typed_operation_plan(_attribute_type_operation())
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        typed_operation_plan,
        package_name="home-ontology",
        target_language="aware",
    )

    assert len(feature_results) == 1
    result = feature_results[0]
    assert result.feature_key == "attribute_config"
    assert result.status == "source_projection_projected"
    assert result.reason == (
        "meta_source_projection_attribute_config_type_segment_delta_ready"
    )
    assert result.projected is True
    assert result.grammar_anchor_binding_count == 1
    assert result.grammar_anchor_source_count == 1
    assert result.grammar_anchor_replacement_count == 1
    assert result.required_evidence_fields == (
        "single_source_ref",
        "attribute_name",
        "owner_key",
        "renderable_primitive_type_descriptor",
    )
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.operation is CodeSectionDeltaOperationKind.replace_segment
    assert entry.provider_key == META_SOURCE_PROJECTION_PROVIDER_KEY
    assert entry.event_ref == "aware_meta.provider_delta.world_change.attribute.update"
    assert entry.semantic_key == (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel/attribute:selected_channel"
    )
    assert entry.content_text == "String?"
    assert entry.before_hash is None
    assert entry.after_hash == _digest("String?")
    assert entry.section_ref.package_name == "home-ontology"
    assert entry.section_ref.relative_path == "home/tv_channel.aware"
    assert entry.section_ref.language == "aware"
    assert entry.section_ref.section_type == "attribute"
    assert entry.section_ref.qualname == "TvChannel.selected_channel"
    assert entry.segment_ref is not None
    assert entry.segment_ref.segment_name == "type"
    assert entry.segment_ref.before_segment_hash == _digest("Int?")
    binding = result.grammar_anchor_bindings[0]
    source = result.grammar_anchor_sources[0]
    replacement = result.grammar_anchor_replacements[0]
    assert binding.grammar_rule_name == "attr_def"
    assert binding.anchor_field_path == "type"
    assert binding.graph_selector.class_name == "TvChannel"
    assert binding.graph_selector.attribute_name == "selected_channel"
    assert binding.graph_selector.attribute_path == ("TvChannel.selected_channel.type")
    assert binding.compatibility_segment_name == "type"
    assert source.source_key == "home/tv_channel.aware"
    assert source.relative_path == "home/tv_channel.aware"
    assert replacement.binding_key == binding.binding_key
    assert replacement.replacement_text == "String?"
    assert replacement.before_text_hash is None
    replacement_metadata = cast(dict[str, object], replacement.metadata)
    assert replacement_metadata["semantic_baseline_text"] == "Int?"
    assert replacement_metadata["semantic_baseline_text_hash"] == _digest("Int?")
    assert replacement_metadata["source_context_before_text_hash"] is None


def test_meta_attribute_config_default_value_update_emits_code_section_delta_entry() -> (
    None
):
    typed_operation_plan = _typed_operation_plan(_attribute_default_value_operation())
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        typed_operation_plan,
        package_name="home-ontology",
        target_language="aware",
    )

    assert len(feature_results) == 1
    result = feature_results[0]
    assert result.feature_key == "attribute_config"
    assert result.status == "source_projection_projected"
    assert result.reason == (
        "meta_source_projection_attribute_config_default_value_segment_delta_ready"
    )
    assert result.grammar_anchor_binding_count == 1
    assert result.grammar_anchor_source_count == 1
    assert result.grammar_anchor_replacement_count == 1
    assert result.required_evidence_fields == (
        "single_source_ref",
        "attribute_name",
        "owner_key",
        "renderable_default_value",
    )
    assert result.missing_evidence_fields == ()
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.operation is CodeSectionDeltaOperationKind.replace_segment
    assert entry.provider_key == META_SOURCE_PROJECTION_PROVIDER_KEY
    assert entry.event_ref == "aware_meta.provider_delta.world_change.attribute.update"
    assert entry.content_text == "11"
    assert entry.before_hash is None
    assert entry.after_hash == _digest("11")
    assert entry.section_ref.section_type == "attribute"
    assert entry.section_ref.qualname == "TvChannel.selected_channel"
    assert entry.segment_ref is not None
    assert entry.segment_ref.segment_name == "default_value"
    assert entry.segment_ref.before_segment_hash == _digest("7")
    binding = result.grammar_anchor_bindings[0]
    replacement = result.grammar_anchor_replacements[0]
    assert binding.grammar_rule_name == "attr_def"
    assert binding.anchor_field_path == "default"
    assert binding.graph_selector.attribute_path == (
        "TvChannel.selected_channel.default_value"
    )
    assert binding.compatibility_segment_name == "default_value"
    assert replacement.binding_key == binding.binding_key
    assert replacement.replacement_text == "11"
    assert replacement.before_text_hash is None
    replacement_metadata = cast(dict[str, object], replacement.metadata)
    assert replacement_metadata["semantic_baseline_text"] == "7"
    assert replacement_metadata["semantic_baseline_text_hash"] == _digest("7")
    assert replacement_metadata["source_context_before_text_hash"] is None


def test_meta_attribute_config_default_value_removal_blocks_segment_delete_guess() -> (
    None
):
    operation = _attribute_default_value_operation()
    current = cast(dict[str, object], operation["current"])
    signature = dict(cast(dict[str, object], current["attribute_signature"]))
    signature["default_value"] = None
    current["attribute_signature"] = signature

    feature_results = source_projection_feature_results_from_meta_typed_operations(
        _typed_operation_plan(operation),
        package_name="home-ontology",
        target_language="aware",
    )

    assert len(feature_results) == 1
    result = feature_results[0]
    assert result.feature_key == "attribute_config"
    assert result.status == "source_projection_blocked"
    assert result.reason == (
        "meta_source_projection_attribute_config_default_value_requires_renderable_default_value"
    )
    assert result.required_evidence_fields == (
        "single_source_ref",
        "attribute_name",
        "owner_key",
        "renderable_default_value",
    )
    assert result.missing_evidence_fields == ("renderable_default_value",)
    assert result.entries == ()


def test_meta_source_projection_structural_policy_matrix_is_explicit() -> None:
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        _typed_operation_plan(
            _class_operation(),
            _relationship_operation(),
            _attribute_operation(),
            _attribute_membership_operation(),
            _function_operation(),
            _function_membership_operation(),
        )
    )

    reason_by_subject = {
        result.ontology_subject_kind: result.reason for result in feature_results
    }
    feature_by_subject = {
        result.ontology_subject_kind: result.feature_key for result in feature_results
    }

    assert len(feature_results) == 6
    assert tuple(result.status for result in feature_results) == (
        "source_projection_skipped",
        "source_projection_skipped",
        "source_projection_skipped",
        "source_projection_skipped",
        "source_projection_skipped",
        "source_projection_skipped",
    )
    assert all(not result.projected for result in feature_results)
    assert all(result.entries == () for result in feature_results)
    assert feature_by_subject == {
        "class": "class_config",
        "relationship": "relationship_config",
        "attribute": "attribute_config",
        "attribute_membership": "attribute_config",
        "function": "function_config",
        "function_membership": "function_config",
    }
    assert reason_by_subject == {
        "class": (
            "meta_source_projection_class_config_requires_renderer_segment_policy"
        ),
        "relationship": (
            "meta_source_projection_relationship_config_requires_renderer_segment_policy"
        ),
        "attribute": (
            "meta_source_projection_attribute_config_requires_renderer_segment_policy"
        ),
        "attribute_membership": (
            "meta_source_projection_attribute_membership_requires_renderer_segment_policy"
        ),
        "function": (
            "meta_source_projection_function_config_requires_renderer_segment_policy"
        ),
        "function_membership": (
            "meta_source_projection_function_membership_requires_renderer_segment_policy"
        ),
    }
    assert feature_results[0].event_refs == (
        "aware_meta.provider_delta.world_change.class.update",
    )


def test_meta_function_config_description_projection_emits_code_section_delta_entry() -> (
    None
):
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        _typed_operation_plan(_function_description_operation()),
        package_name="home-ontology",
        target_language="aware",
    )

    assert len(feature_results) == 1
    result = feature_results[0]
    assert result.feature_key == "function_config"
    assert result.status == "source_projection_projected"
    assert result.blocked is False
    assert result.projected is True
    assert result.reason == (
        "meta_source_projection_function_config_description_segment_delta_ready"
    )
    assert result.required_evidence_fields == (
        "single_source_ref",
        "function_name",
        "owner_key",
        "renderable_description_text",
    )
    assert result.missing_evidence_fields == ()
    assert result.event_refs == (
        "aware_meta.provider_delta.world_change.function.update",
    )
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.operation is CodeSectionDeltaOperationKind.replace_segment
    assert entry.provider_key == META_SOURCE_PROJECTION_PROVIDER_KEY
    assert entry.event_ref == "aware_meta.provider_delta.world_change.function.update"
    assert entry.semantic_key == (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel.rename"
    )
    assert entry.content_text == (
        "Rename the channel display label and keep assistant-facing media "
        "context synchronized."
    )
    assert entry.before_hash is None
    assert entry.after_hash == _digest(
        "Rename the channel display label and keep assistant-facing media "
        "context synchronized."
    )
    assert entry.section_ref.package_name == "home-ontology"
    assert entry.section_ref.relative_path == "home/tv_channel.aware"
    assert entry.section_ref.language == "aware"
    assert entry.section_ref.section_type == "function"
    assert entry.section_ref.qualname == "TvChannel.rename"
    assert entry.section_ref.source_refs == ["home/tv_channel.aware"]
    assert entry.segment_ref is not None
    assert entry.segment_ref.segment_name == "description_comment"
    assert entry.segment_ref.before_segment_hash == _digest(
        "Rename the channel display label for humans and assistants."
    )


def test_meta_function_config_signature_projection_emits_code_section_delta_entry() -> (
    None
):
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        _typed_operation_plan(_function_signature_operation()),
        package_name="home-ontology",
        target_language="aware",
    )

    assert len(feature_results) == 1
    result = feature_results[0]
    assert result.feature_key == "function_config"
    assert result.status == "source_projection_projected"
    assert result.reason == (
        "meta_source_projection_function_config_signature_segment_delta_ready"
    )
    assert result.required_evidence_fields == (
        "single_source_ref",
        "function_name",
        "owner_key",
        "renderable_signature_text",
    )
    assert result.missing_evidence_fields == ()
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.operation is CodeSectionDeltaOperationKind.replace_segment
    assert entry.provider_key == META_SOURCE_PROJECTION_PROVIDER_KEY
    assert entry.event_ref == "aware_meta.provider_delta.world_change.function.update"
    assert entry.semantic_key == (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel.rename"
    )
    assert entry.content_text == "(label String) -> TvChannel"
    assert entry.before_hash is None
    assert entry.after_hash == _digest("(label String) -> TvChannel")
    assert entry.section_ref.package_name == "home-ontology"
    assert entry.section_ref.relative_path == "home/tv_channel.aware"
    assert entry.section_ref.language == "aware"
    assert entry.section_ref.section_type == "function"
    assert entry.section_ref.qualname == "TvChannel.rename"
    assert entry.section_ref.source_refs == ["home/tv_channel.aware"]
    assert entry.segment_ref is not None
    assert entry.segment_ref.segment_name == "signature"
    assert entry.segment_ref.before_segment_hash == (
        _digest("(display_name String) -> TvChannel")
    )


def test_meta_function_config_signature_projection_blocks_unrenderable_shape() -> None:
    operation = _function_signature_operation()
    current = cast(dict[str, object], operation["current"])
    signature = dict(cast(dict[str, object], current["function_signature"]))
    signature["outputs"] = ()
    current["function_signature"] = signature

    feature_results = source_projection_feature_results_from_meta_typed_operations(
        _typed_operation_plan(operation),
        package_name="home-ontology",
        target_language="aware",
    )

    assert len(feature_results) == 1
    result = feature_results[0]
    assert result.feature_key == "function_config"
    assert result.status == "source_projection_blocked"
    assert result.reason == (
        "meta_source_projection_function_config_signature_requires_renderable_signature"
    )
    assert result.required_evidence_fields == (
        "single_source_ref",
        "function_name",
        "owner_key",
        "renderable_signature_text",
    )
    assert result.missing_evidence_fields == ("renderable_signature_text",)
    assert result.entries == ()


def test_meta_function_impl_section_delta_entries_feed_source_projection_result() -> (
    None
):
    typed_operation_plan = _typed_operation_plan(
        _function_impl_operation(),
        _attribute_operation(),
    )
    report = _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "ready",
            "dirty_entry_count": 2,
        },
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    projection = code_source_projection_request_from_meta_change_report(
        report,
        package_name="home-ontology",
        package_root=".",
        sources_root="home",
        target_language="aware",
    )
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        typed_operation_plan,
        package_name=projection.package_name,
        target_language=projection.target_language,
    )

    result = code_source_projection_result_from_meta_feature_results(
        report,
        projection=projection,
        feature_results=feature_results,
    )

    assert result.projected is True
    assert result.delta_set is not None
    assert len(result.delta_set.entries) == 1
    assert result.delta_set.entries[0].event_ref == (
        "aware_meta.provider_delta.world_change.function_impl.update"
    )
    assert len(result.skipped_events) == 1
    assert result.skipped_events[0].event_key == (
        "aware_meta.provider_delta.world_change.attribute.update"
    )
    assert result.skipped_events[0].reason == (
        "meta_source_projection_attribute_config_requires_renderer_segment_policy"
    )
    assert result.skipped_events[0].metadata is not None
    assert result.skipped_events[0].metadata["feature_key"] == "attribute_config"


def test_meta_provider_delta_source_projection_stage_exposes_code_evidence(
    tmp_path,
) -> None:
    typed_operation_plan = _typed_operation_plan(
        _attribute_default_value_operation(),
    )
    report = _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "ready",
            "dirty_entry_count": 1,
        },
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    stage = provider_delta_source_projection_stage(
        package_payload={"package_name": "home-ontology"},
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=report,
        provider_delta_typed_operation_plan=typed_operation_plan,
        code_package_delta=SimpleNamespace(
            package_name="home-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware",
            paths=(
                SimpleNamespace(
                    relative_path="home/tv_channel.aware",
                    language=CodeLanguage.aware,
                ),
            ),
        ),
    )

    assert stage["status"] == "source_projection_ready"
    assert stage["ready"] is True
    assert stage["projected"] is True
    assert stage["change_count"] == 1
    assert stage["action_count"] == 1
    assert stage["projected_entry_count"] == 1
    assert stage["grammar_anchor_binding_count"] == 1
    assert stage["grammar_anchor_source_count"] == 1
    assert stage["grammar_anchor_replacement_count"] == 1
    assert stage["blocked_feature_result_count"] == 0
    assert stage["skipped_feature_result_count"] == 0
    projection = cast(dict[str, object], stage["projection"])
    result = cast(dict[str, object], stage["result"])
    delta_set = cast(dict[str, object], result["delta_set"])
    entries = cast(list[dict[str, object]], delta_set["entries"])
    section_ref = cast(dict[str, object], entries[0]["section_ref"])
    segment_ref = cast(dict[str, object], entries[0]["segment_ref"])

    assert projection["provider_key"] == "aware_meta"
    assert projection["package_name"] == "home-ontology"
    assert projection["package_root"] == tmp_path.as_posix()
    assert projection["sources_root"] == "aware"
    assert projection["target_language"] == "aware"
    assert section_ref["section_type"] == "attribute"
    assert segment_ref["segment_name"] == "default_value"
    assert entries[0]["content_text"] == "11"
    render_request = cast(
        dict[str, object],
        stage["grammar_anchor_render_delta_request"],
    )
    bindings = cast(list[dict[str, object]], render_request["bindings"])
    sources = cast(list[dict[str, object]], render_request["sources"])
    replacements = cast(list[dict[str, object]], render_request["replacements"])
    graph_selector = cast(dict[str, object], bindings[0]["graph_selector"])

    assert render_request["package_name"] == "home-ontology"
    assert render_request["package_root"] == tmp_path.as_posix()
    assert render_request["sources_root"] == "aware"
    assert bindings[0]["grammar_rule_name"] == "attr_def"
    assert bindings[0]["anchor_field_path"] == "default"
    assert graph_selector["attribute_path"] == (
        "TvChannel.selected_channel.default_value"
    )
    assert sources[0]["source_key"] == "home/tv_channel.aware"
    assert replacements[0]["replacement_text"] == "11"
    assert replacements[0]["before_text_hash"] is None
    replacement_metadata = cast(dict[str, object], replacements[0]["metadata"])
    assert replacement_metadata["semantic_baseline_text"] == "7"
    assert replacement_metadata["semantic_baseline_text_hash"] == _digest("7")
    assert replacement_metadata["source_context_before_text_hash"] is None


def test_meta_semantic_apply_source_projection_evidence_builds_provider_result(
    tmp_path,
) -> None:
    source_text = "class TvChannel {\n" "    channel_number Int key\n" "}\n"
    result = provider_delta_result_from_semantic_apply_source_projection_evidence(
        semantic_status={
            "status": "ready",
            "packages": (
                {
                    "package_name": "home-ontology",
                    "delta_fingerprint": "sha256:test-current-delta",
                    "semantic_source_meaning": {
                        "typed_operations": (
                            {
                                "operation_key": (
                                    "aware_meta.object_config_graph.attribute.type:"
                                    "TvChannel.channel_number:update"
                                ),
                                "operation_family": "update",
                                "semantic_operation_type": (
                                    "aware_meta.object_config_graph."
                                    "attribute.type.update"
                                ),
                                "semantic_key": (
                                    "meta.attribute:TvChannel.channel_number"
                                ),
                                "semantic_subject_type": ("ClassConfigAttributeConfig"),
                                "field_path": "type",
                                "event_key": (
                                    "aware_meta.object_config_graph.attribute."
                                    "type:TvChannel.channel_number"
                                ),
                                "source_refs": ("home/tv_channel.aware",),
                                "before_payload": {"type": "Int"},
                                "after_payload": {"type": "String"},
                            },
                        ),
                    },
                },
            ),
        },
        semantic_apply={"status": "executed"},
        package_name="home-ontology",
        package_root=tmp_path.as_posix(),
        sources_root="aware",
        target_language="aware",
        source_text_by_ref={"home/tv_channel.aware": source_text},
        source_session_context={
            "source_session_id": "source-session-1",
            "source_delta_fingerprint": "workspace-source-delta:test",
        },
        commit_ids=("commit-1",),
        head_commit_ids=("head-1",),
        metadata={"proof": "test"},
    )

    assert result["semantic_contract"] == {
        "provider_key": "aware_meta",
        "semantic_owner": "aware_meta.provider",
    }
    assert result["current_delta_fingerprint"] == "workspace-source-delta:test"
    result_metadata = cast(dict[str, object], result["metadata"])
    assert result_metadata["contract_version"] == (
        META_SEMANTIC_APPLY_SOURCE_PROJECTION_EVIDENCE_CONTRACT_VERSION
    )

    details = cast(dict[str, object], result["details"])
    stage = cast(dict[str, object], details["provider_delta_source_projection"])
    assert stage["status"] == "source_projection_ready"
    assert stage["reason"] == "meta_source_projection_section_delta_entries_ready"
    assert stage["projected_entry_count"] == 1
    assert stage["grammar_anchor_binding_count"] == 1
    assert stage["grammar_anchor_source_count"] == 1
    assert stage["grammar_anchor_replacement_count"] == 1
    stage_metadata = cast(dict[str, object], stage["metadata"])
    assert stage_metadata["semantic_apply_head_commit_ids"] == ("head-1",)

    render_request = cast(
        dict[str, object],
        stage["grammar_anchor_render_delta_request"],
    )
    bindings = cast(list[dict[str, object]], render_request["bindings"])
    sources = cast(tuple[dict[str, object], ...], render_request["sources"])
    replacements = cast(
        list[dict[str, object]],
        render_request["replacements"],
    )
    metadata = cast(dict[str, object], render_request["metadata"])

    assert metadata["source"] == "aware_meta.semantic_apply.source_projection_evidence"
    assert metadata["semantic_apply_status"] == "executed"
    assert metadata["semantic_apply_commit_ids"] == ("commit-1",)
    assert metadata["semantic_apply_head_commit_ids"] == ("head-1",)
    assert render_request["baseline_fingerprint"] == _digest(source_text)
    assert bindings[0]["grammar_rule_name"] == "attr_def"
    assert bindings[0]["anchor_field_path"] == "type"
    graph_selector = cast(dict[str, object], bindings[0]["graph_selector"])
    assert graph_selector["class_name"] == "TvChannel"
    assert graph_selector["attribute_name"] == "channel_number"
    assert graph_selector["attribute_path"] == "TvChannel.channel_number.type"
    assert sources[0]["source_key"] == "home/tv_channel.aware"
    assert sources[0]["source_text"] == source_text
    assert sources[0]["before_hash"] == _digest(source_text)
    assert replacements[0]["replacement_text"] == "String"
    replacement_metadata = cast(dict[str, object], replacements[0]["metadata"])
    assert replacement_metadata["semantic_baseline_text"] == "Int"
    assert replacement_metadata["semantic_baseline_text_hash"] == _digest("Int")


def test_meta_semantic_apply_function_source_meaning_builds_function_typed_operation(
    tmp_path,
) -> None:
    source_text = (
        "class TvChannel {\n"
        "    name String\n"
        "    channel_number Int key\n"
        "\n"
        "    fn rename(display_name String) -> TvChannel {\n"
        '        """\n'
        "        Rename the channel display label for humans and assistants.\n"
        '        """\n'
        "    }\n"
        "}\n"
    )
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "home-ontology",
                "delta_fingerprint": "sha256:function-current-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.function:"
                                "TvChannel.rename:create"
                            ),
                            "operation_family": "create",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.function.create"
                            ),
                            "semantic_key": "meta.function:TvChannel.rename",
                            "semantic_subject_type": "aware_meta.FunctionConfig",
                            "field_path": "name",
                            "event_key": ("meta.function:TvChannel.rename:name:upsert"),
                            "source_refs": ("home/tv_channel.aware",),
                            "before_payload": None,
                            "after_payload": {
                                "name": "rename",
                                "class_name": "TvChannel",
                                "function_name": "rename",
                                "function_description": (
                                    "Rename the channel display label for "
                                    "humans and assistants."
                                ),
                            },
                        },
                    ),
                },
            },
        ),
    }
    result = provider_delta_result_from_semantic_apply_source_projection_evidence(
        semantic_status=semantic_status,
        semantic_apply={"status": "executed"},
        package_name="home-ontology",
        package_root=tmp_path.as_posix(),
        sources_root="aware",
        target_language="aware",
        source_text_by_ref={"home/tv_channel.aware": source_text},
        source_session_context={
            "source_session_id": "source-session-1",
            "source_delta_fingerprint": "workspace-source-delta:function",
        },
        commit_ids=("commit-1",),
        head_commit_ids=("head-1",),
        metadata={"proof": "test"},
    )

    assert result["current_delta_fingerprint"] == "workspace-source-delta:function"
    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("home/tv_channel.aware",),
    )
    typed_operations = cast(
        tuple[dict[str, object], ...],
        typed_plan["typed_operations"],
    )
    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert len(typed_operations) == 1
    operation = typed_operations[0]
    assert operation["operation_family"] == "create"
    assert operation["provider_operation_type"] == "meta_ocg.function.create"
    assert operation["ontology_subject_kind"] == "function"
    assert operation["semantic_subject_type"] == "aware_meta.FunctionConfig"
    assert operation["semantic_key"] == "meta.function:TvChannel.rename"
    current = cast(dict[str, object], operation["current"])
    assert current["function_name"] == "rename"
    assert current["owner_key"] == "TvChannel"
    signature = cast(dict[str, object], current["function_signature"])
    assert signature["description"] == (
        "Rename the channel display label for humans and assistants."
    )


def test_meta_semantic_apply_enum_option_source_meaning_builds_create_operation() -> (
    None
):
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "delta_fingerprint": "sha256:enum-option-current-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.enum_option.value:"
                                "ContentSource.assistant:create"
                            ),
                            "operation_family": "create",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum_option.create"
                            ),
                            "semantic_key": (
                                "meta.enum:ContentSource/option:assistant"
                            ),
                            "semantic_subject_type": "aware_meta.EnumOption",
                            "field_path": "value",
                            "event_key": (
                                "meta.enum:ContentSource/option:assistant:"
                                "value:upsert"
                            ),
                            "source_refs": ("content/content_enums.aware",),
                            "before_payload": None,
                            "after_payload": {
                                "value": "assistant",
                                "enum_name": "ContentSource",
                                "enum_option_value": "assistant",
                                "position": "6",
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_enums.aware",),
    )
    typed_operations = cast(
        tuple[dict[str, object], ...],
        typed_plan["typed_operations"],
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert len(typed_operations) == 1
    operation = typed_operations[0]
    assert operation["operation_family"] == "create"
    assert operation["provider_operation_type"] == "meta_ocg.enum_option.create"
    assert operation["ontology_subject_kind"] == "enum_option"
    assert operation["semantic_subject_type"] == "aware_meta.EnumOption"
    assert operation["semantic_key"] == "meta.enum:ContentSource/option:assistant"
    assert operation["source_refs"] == ["content/content_enums.aware"]
    current = cast(dict[str, object], operation["current"])
    payload = cast(dict[str, object], current["payload"])
    assert current["enum_semantic_key"] == "meta.enum:ContentSource"
    assert current["parent_semantic_key"] == "meta.enum:ContentSource"
    assert current["enum_name"] == "ContentSource"
    assert current["value"] == "assistant"
    assert current["position"] == 6
    assert payload["value"] == "assistant"
    assert payload["position"] == 6


def test_meta_semantic_apply_enum_option_reorder_delete_build_operations() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "delta_fingerprint": "sha256:enum-option-fallback-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.enum_option.position:"
                                "ContentSource.assistant:update"
                            ),
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum_option."
                                "position.update"
                            ),
                            "semantic_key": (
                                "meta.enum:ContentSource/option:assistant"
                            ),
                            "semantic_subject_type": "aware_meta.EnumOption",
                            "field_path": "position",
                            "event_key": (
                                "meta.enum:ContentSource/option:assistant:"
                                "position:update"
                            ),
                            "source_refs": ("content/content_enums.aware",),
                            "before_payload": {
                                "value": "assistant",
                                "enum_name": "ContentSource",
                                "enum_config_id": "enum-config-content-source",
                                "enum_option_id": "enum-option-assistant",
                                "position": "6",
                            },
                            "after_payload": {
                                "value": "assistant",
                                "enum_name": "ContentSource",
                                "enum_config_id": "enum-config-content-source",
                                "enum_option_id": "enum-option-assistant",
                                "position": "1",
                            },
                        },
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.enum_option.value:"
                                "ContentSource.event:delete"
                            ),
                            "operation_family": "delete",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum_option.delete"
                            ),
                            "semantic_key": "meta.enum:ContentSource/option:event",
                            "semantic_subject_type": "aware_meta.EnumOption",
                            "field_path": "value",
                            "event_key": (
                                "meta.enum:ContentSource/option:event:value:delete"
                            ),
                            "source_refs": ("content/content_enums.aware",),
                            "before_payload": {
                                "value": "event",
                                "enum_name": "ContentSource",
                                "enum_config_id": "enum-config-content-source",
                                "enum_option_id": "enum-option-event",
                                "position": "1",
                            },
                            "after_payload": None,
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_enums.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    typed_operations = cast(
        tuple[dict[str, object], ...],
        typed_plan["typed_operations"],
    )
    assert [operation["provider_operation_type"] for operation in typed_operations] == [
        "meta_ocg.enum_option.update",
        "meta_ocg.enum_option.delete",
    ]
    update_current = cast(dict[str, object], typed_operations[0]["current"])
    update_baseline = cast(dict[str, object], typed_operations[0]["baseline"])
    update_baseline_object = cast(dict[str, object], update_baseline["object"])
    delete_current = cast(dict[str, object], typed_operations[1]["current"])
    delete_baseline = cast(dict[str, object], typed_operations[1]["baseline"])
    delete_baseline_object = cast(dict[str, object], delete_baseline["object"])
    assert update_current["enum_config_id"] == "enum-config-content-source"
    assert update_current["enum_option_id"] == "enum-option-assistant"
    assert update_current["position"] == 1
    assert update_baseline_object["position"] == 6
    assert delete_current["enum_config_id"] == "enum-config-content-source"
    assert delete_current["enum_option_id"] == "enum-option-event"
    assert delete_current["value"] == "event"
    assert delete_baseline_object["enum_option_id"] == "enum-option-event"


def test_meta_semantic_apply_enum_structural_create_builds_typed_operation() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "delta_fingerprint": "sha256:enum-structural-create-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.enum.identity:"
                                "ContentSource:create"
                            ),
                            "operation_family": "create",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum.create"
                            ),
                            "semantic_key": "meta.enum:ContentSource",
                            "semantic_subject_type": "aware_meta.EnumConfig",
                            "field_path": "name",
                            "event_key": "meta.enum:ContentSource:name:upsert",
                            "source_refs": ("content/content_enums.aware",),
                            "before_payload": None,
                            "after_payload": {
                                "name": "ContentSource",
                                "enum_name": "ContentSource",
                                "enum_fqn": (
                                    "aware_content.default.content.ContentSource"
                                ),
                                "graph_semantic_key": "ocg:aware_content",
                                "object_config_graph_node_id": (
                                    "enum-node-content-source"
                                ),
                                "enum_config_id": "enum-config-content-source",
                                "values": ("text", "image"),
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_enums.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["reason"] == (
        "semantic_apply_source_projection_from_semantic_source_meaning"
    )
    operations = cast(tuple[dict[str, object], ...], typed_plan["typed_operations"])
    assert len(operations) == 1
    operation = operations[0]
    current = cast(dict[str, object], operation["current"])
    assert operation["operation_family"] == "create"
    assert operation["provider_operation_type"] == "meta_ocg.enum.create"
    assert operation["ontology_subject_kind"] == "enum"
    assert current["graph_semantic_key"] == "ocg:aware_content"
    assert current["object_config_graph_node_id"] == "enum-node-content-source"
    assert current["enum_config_id"] == "enum-config-content-source"
    assert current["values"] == ("text", "image")
    assert typed_plan["blocked_operations"] == []


def test_meta_semantic_apply_class_structural_create_builds_typed_operation() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
                "manifest_relative_path": (
                    "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml"
                ),
                "delta_fingerprint": "sha256:class-structural-create-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.class.identity:"
                                "ContentPlacement:create"
                            ),
                            "operation_family": "create",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.class.create"
                            ),
                            "semantic_key": "meta.class:ContentPlacement",
                            "semantic_subject_type": "aware_meta.ClassConfig",
                            "field_path": "name",
                            "event_key": ("meta.class:ContentPlacement:name:upsert"),
                            "source_refs": ("content/content_layout.aware",),
                            "before_payload": None,
                            "after_payload": {
                                "name": "ContentPlacement",
                                "class_name": "ContentPlacement",
                                "description": (
                                    "Content placement hints for generated "
                                    "layout tests."
                                ),
                                "object_config_graph_node_id": (
                                    "class-node-content-placement"
                                ),
                                "class_config_id": ("class-config-content-placement"),
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_layout.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    operations = cast(tuple[dict[str, object], ...], typed_plan["typed_operations"])
    assert len(operations) == 1
    operation = operations[0]
    current = cast(dict[str, object], operation["current"])
    source_event = cast(dict[str, object], operation["source_semantic_change"])
    semantic_source_operation = cast(
        dict[str, object],
        source_event["semantic_source_operation"],
    )
    enriched_after_payload = cast(
        dict[str, object],
        semantic_source_operation["after_payload"],
    )

    assert operation["operation_family"] == "create"
    assert operation["provider_operation_type"] == "meta_ocg.class.create"
    assert operation["ontology_subject_kind"] == "class"
    assert current["graph_semantic_key"] == "ocg:aware_content"
    assert current["node_key"] == "aware_content.default.content.ContentPlacement"
    assert current["class_fqn"] == "aware_content.default.content.ContentPlacement"
    assert current["class_config_id"] == "class-config-content-placement"
    assert enriched_after_payload["graph_semantic_key"] == "ocg:aware_content"
    assert typed_plan["blocked_operations"] == []


def test_meta_semantic_apply_class_structural_delete_stays_in_ready_plan() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
                "manifest_relative_path": (
                    "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml"
                ),
                "delta_fingerprint": "sha256:class-structural-delete-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.class.identity:"
                                "LegacyWidget:delete"
                            ),
                            "operation_family": "delete",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.class.delete"
                            ),
                            "semantic_key": "meta.class:LegacyWidget",
                            "semantic_subject_type": "aware_meta.ClassConfig",
                            "field_path": "name",
                            "event_key": "meta.class:LegacyWidget:name:delete",
                            "source_refs": ("content/content_layout.aware",),
                            "before_payload": {
                                "name": "LegacyWidget",
                                "class_name": "LegacyWidget",
                                "class_fqn": (
                                    "aware_content.default.content.LegacyWidget"
                                ),
                                "description": "Legacy widget.",
                                "graph_semantic_key": "ocg:aware_content",
                                "object_config_graph_node_id": (
                                    "00000000-0000-0000-0000-000000000421"
                                ),
                                "class_config_id": (
                                    "00000000-0000-0000-0000-000000000422"
                                ),
                            },
                            "after_payload": None,
                        },
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.class.description:"
                                "LegacyWidget:update"
                            ),
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.class.description."
                                "update"
                            ),
                            "semantic_key": "meta.class:LegacyWidget",
                            "semantic_subject_type": "aware_meta.ClassConfig",
                            "field_path": "description",
                            "event_key": ("meta.class:LegacyWidget:description:update"),
                            "source_refs": ("content/content_layout.aware",),
                            "before_payload": {
                                "name": "LegacyWidget",
                                "class_name": "LegacyWidget",
                                "description": "Legacy widget.",
                            },
                            "after_payload": {
                                "name": "LegacyWidget",
                                "class_name": "LegacyWidget",
                                "description": "Ignored because class is deleted.",
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_layout.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    operations = cast(tuple[dict[str, object], ...], typed_plan["typed_operations"])
    assert len(operations) == 1
    [delete_operation] = operations
    current = _mapping(delete_operation["current"])
    baseline = _mapping(delete_operation["baseline"])
    baseline_object = _mapping(baseline["object"])
    assert delete_operation["operation_family"] == "delete"
    assert delete_operation["provider_operation_type"] == "meta_ocg.class.delete"
    assert delete_operation["semantic_subject_type"] == "aware_meta.ObjectConfigGraph"
    assert current["graph_semantic_key"] == "ocg:aware_content"
    assert current["object_config_graph_node_id"] == (
        "00000000-0000-0000-0000-000000000421"
    )
    assert current["class_config_id"] == "00000000-0000-0000-0000-000000000422"
    assert current["node_key"] == "aware_content.default.content.LegacyWidget"
    assert baseline_object["object_config_graph_node_id"] == (
        "00000000-0000-0000-0000-000000000421"
    )
    assert typed_plan["blocked_operations"] == []


def test_meta_semantic_apply_class_identity_rename_composes_delete_create() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
                "manifest_relative_path": (
                    "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml"
                ),
                "delta_fingerprint": "sha256:class-identity-rename-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.class.identity:"
                                "ContentPlacementRenamed:rename"
                            ),
                            "operation_family": "rename",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.class.identity.rename"
                            ),
                            "semantic_key": "meta.class:ContentPlacementRenamed",
                            "semantic_subject_type": "aware_meta.ClassConfig",
                            "field_path": "name",
                            "event_key": (
                                "meta.class:ContentPlacementRenamed:name:rename"
                            ),
                            "source_refs": ("content/content_layout.aware",),
                            "before_payload": {
                                "semantic_key": "meta.class:ContentPlacement",
                                "name": "ContentPlacement",
                                "class_name": "ContentPlacement",
                                "class_fqn": (
                                    "aware_content.default.content.ContentPlacement"
                                ),
                                "graph_semantic_key": "ocg:aware_content",
                                "object_config_graph_node_id": (
                                    "00000000-0000-0000-0000-000000000621"
                                ),
                                "class_config_id": (
                                    "00000000-0000-0000-0000-000000000622"
                                ),
                                "description": (
                                    "Content placement hints for generated "
                                    "layout tests."
                                ),
                            },
                            "after_payload": {
                                "semantic_key": ("meta.class:ContentPlacementRenamed"),
                                "name": "ContentPlacementRenamed",
                                "class_name": "ContentPlacementRenamed",
                                "class_fqn": (
                                    "aware_content.default.content."
                                    "ContentPlacementRenamed"
                                ),
                                "graph_semantic_key": "ocg:aware_content",
                                "description": (
                                    "Content placement hints for generated "
                                    "layout tests."
                                ),
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_layout.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["blocked_operations"] == []
    operations = cast(tuple[dict[str, object], ...], typed_plan["typed_operations"])
    assert [operation["provider_operation_type"] for operation in operations] == [
        "meta_ocg.class.delete",
        "meta_ocg.class.create",
    ]

    delete_operation, create_operation = operations
    delete_current = _mapping(delete_operation["current"])
    create_current = _mapping(create_operation["current"])
    delete_event = cast(dict[str, object], delete_operation["source_semantic_change"])
    create_event = cast(dict[str, object], create_operation["source_semantic_change"])
    delete_source_operation = cast(
        dict[str, object],
        delete_event["semantic_source_operation"],
    )
    create_source_operation = cast(
        dict[str, object],
        create_event["semantic_source_operation"],
    )

    assert delete_operation["operation_family"] == "delete"
    assert delete_operation["semantic_key"] == "meta.class:ContentPlacement"
    assert delete_current["name"] == "ContentPlacement"
    assert delete_current["class_fqn"] == (
        "aware_content.default.content.ContentPlacement"
    )
    assert delete_current["object_config_graph_node_id"] == (
        "00000000-0000-0000-0000-000000000621"
    )
    assert delete_source_operation["composition"] == {
        "composition_kind": "class_identity_rename_delete_create",
        "composition_part": "delete_old",
        "source_operation_key": (
            "aware_meta.object_config_graph.class.identity:"
            "ContentPlacementRenamed:rename"
        ),
        "rename_semantic_key": "meta.class:ContentPlacementRenamed",
        "old_semantic_key": "meta.class:ContentPlacement",
        "new_semantic_key": "meta.class:ContentPlacementRenamed",
    }

    assert create_operation["operation_family"] == "create"
    assert create_operation["semantic_key"] == "meta.class:ContentPlacementRenamed"
    assert create_current["entity_name"] == "ContentPlacementRenamed"
    assert create_current["class_fqn"] == (
        "aware_content.default.content.ContentPlacementRenamed"
    )
    assert create_current["node_id"] == ""
    assert create_current["entity_id"] == ""
    assert create_source_operation["composition"] == {
        "composition_kind": "class_identity_rename_delete_create",
        "composition_part": "create_new",
        "source_operation_key": (
            "aware_meta.object_config_graph.class.identity:"
            "ContentPlacementRenamed:rename"
        ),
        "rename_semantic_key": "meta.class:ContentPlacementRenamed",
        "old_semantic_key": "meta.class:ContentPlacement",
        "new_semantic_key": "meta.class:ContentPlacementRenamed",
    }


def test_meta_semantic_apply_class_identity_rename_blocks_without_identity() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "delta_fingerprint": "sha256:class-identity-rename-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.class.identity:"
                                "ContentPlacementRenamed:rename"
                            ),
                            "operation_family": "rename",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.class.identity.rename"
                            ),
                            "semantic_key": "meta.class:ContentPlacementRenamed",
                            "semantic_subject_type": "aware_meta.ClassConfig",
                            "field_path": "name",
                            "event_key": (
                                "meta.class:ContentPlacementRenamed:name:rename"
                            ),
                            "source_refs": ("content/content_layout.aware",),
                            "before_payload": {
                                "name": "ContentPlacement",
                                "class_name": "ContentPlacement",
                            },
                            "after_payload": {
                                "name": "ContentPlacementRenamed",
                                "class_name": "ContentPlacementRenamed",
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_layout.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_blocked"
    assert typed_plan["typed_operations"] == []
    [blocked_operation] = cast(
        tuple[dict[str, object], ...],
        typed_plan["blocked_operations"],
    )
    assert blocked_operation["reason"] == (
        "meta_class_identity_rename_requires_explicit_policy"
    )
    blockers = cast(tuple[str, ...], blocked_operation["blockers"])
    assert blockers == (
        "class_identity_rename_missing_before_object_config_graph_node_id",
        "explicit_fallback_required",
    )


def test_meta_semantic_apply_class_name_scalar_update_blocks() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "delta_fingerprint": "sha256:class-name-update-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.class.identity:"
                                "ContentPlacement:update"
                            ),
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.class.name.update"
                            ),
                            "semantic_key": "meta.class:ContentPlacement",
                            "semantic_subject_type": "aware_meta.ClassConfig",
                            "field_path": "name",
                            "event_key": "meta.class:ContentPlacement:name:update",
                            "source_refs": ("content/content_layout.aware",),
                            "before_payload": {
                                "name": "ContentPlacement",
                                "class_name": "ContentPlacement",
                            },
                            "after_payload": {
                                "name": "ContentPlacementRenamed",
                                "class_name": "ContentPlacementRenamed",
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_layout.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_blocked"
    assert typed_plan["typed_operations"] == []
    [blocked_operation] = cast(
        tuple[dict[str, object], ...],
        typed_plan["blocked_operations"],
    )
    assert blocked_operation["reason"] == (
        "meta_class_identity_rename_requires_explicit_policy"
    )
    blockers = cast(tuple[str, ...], blocked_operation["blockers"])
    assert "class_identity_must_not_use_scalar_update" in blockers


def test_meta_semantic_apply_enum_structural_create_derives_graph_from_package() -> (
    None
):
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
                "manifest_relative_path": (
                    "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml"
                ),
                "delta_fingerprint": "sha256:enum-structural-create-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.enum.identity:"
                                "ContentAudience:create"
                            ),
                            "operation_family": "create",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum.create"
                            ),
                            "semantic_key": "meta.enum:ContentAudience",
                            "semantic_subject_type": "aware_meta.EnumConfig",
                            "field_path": "name",
                            "event_key": "meta.enum:ContentAudience:name:upsert",
                            "source_refs": ("content/content_enums.aware",),
                            "before_payload": None,
                            "after_payload": {
                                "name": "ContentAudience",
                                "enum_name": "ContentAudience",
                                "enum_description": (
                                    "Audience role for generated content dispatch."
                                ),
                                "values": ("internal", "public"),
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_enums.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    operations = cast(tuple[dict[str, object], ...], typed_plan["typed_operations"])
    assert len(operations) == 1
    operation = operations[0]
    current = cast(dict[str, object], operation["current"])
    source_event = cast(dict[str, object], operation["source_semantic_change"])
    semantic_source_operation = cast(
        dict[str, object],
        source_event["semantic_source_operation"],
    )
    enriched_after_payload = cast(
        dict[str, object],
        semantic_source_operation["after_payload"],
    )

    assert current["graph_semantic_key"] == "ocg:aware_content"
    assert current["node_key"] == "aware_content.default.content.ContentAudience"
    assert current["description"] == ("Audience role for generated content dispatch.")
    assert current["values"] == ("internal", "public")
    assert semantic_source_operation["package_name"] == "content-ontology"
    assert semantic_source_operation["fqn_prefix"] == "aware_content"
    assert enriched_after_payload["graph_semantic_key"] == "ocg:aware_content"


def test_meta_semantic_apply_attribute_identity_rename_composes_delete_create() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
                "manifest_relative_path": (
                    "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml"
                ),
                "delta_fingerprint": "sha256:attribute-identity-rename-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.attribute.identity:"
                                "ContentLayout.label:rename"
                            ),
                            "operation_family": "rename",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.attribute.identity.rename"
                            ),
                            "semantic_key": "meta.attribute:ContentLayout.label",
                            "semantic_subject_type": "aware_meta.AttributeConfig",
                            "field_path": "name",
                            "event_key": (
                                "meta.attribute:ContentLayout.label:name:rename"
                            ),
                            "source_refs": ("content/content_layout.aware",),
                            "before_payload": {
                                "semantic_key": "meta.attribute:ContentLayout.title",
                                "class_name": "ContentLayout",
                                "attribute_name": "title",
                                "name": "title",
                                "class_fqn": (
                                    "aware_content.default.content.ContentLayout"
                                ),
                                "owner_key": (
                                    "aware_content.default.content.ContentLayout"
                                ),
                                "owner_semantic_key": "meta.class:ContentLayout",
                                "attribute_config_id": (
                                    "00000000-0000-0000-0000-000000000721"
                                ),
                                "type": "String",
                                "default_value": "\"Untitled\"",
                                "description": "Visible title text.",
                            },
                            "after_payload": {
                                "semantic_key": "meta.attribute:ContentLayout.label",
                                "class_name": "ContentLayout",
                                "attribute_name": "label",
                                "name": "label",
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_layout.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["blocked_operations"] == []
    operations = cast(tuple[dict[str, object], ...], typed_plan["typed_operations"])
    assert [operation["provider_operation_type"] for operation in operations] == [
        "meta_ocg.attribute.delete",
        "meta_ocg.attribute.create",
    ]

    delete_operation, create_operation = operations
    delete_current = _mapping(delete_operation["current"])
    create_current = _mapping(create_operation["current"])
    create_signature = _mapping(create_current["attribute_signature"])
    delete_event = cast(dict[str, object], delete_operation["source_semantic_change"])
    create_event = cast(dict[str, object], create_operation["source_semantic_change"])
    delete_source_operation = cast(
        dict[str, object],
        delete_event["semantic_source_operation"],
    )
    create_source_operation = cast(
        dict[str, object],
        create_event["semantic_source_operation"],
    )

    assert delete_operation["operation_family"] == "delete"
    assert delete_operation["semantic_key"] == "meta.attribute:ContentLayout.title"
    assert delete_current["attribute_name"] == "title"
    assert delete_current["attribute_config_id"] == (
        "00000000-0000-0000-0000-000000000721"
    )
    assert delete_source_operation["composition"] == {
        "composition_kind": "attribute_identity_rename_delete_create",
        "composition_part": "delete_old",
        "source_operation_key": (
            "aware_meta.object_config_graph.attribute.identity:"
            "ContentLayout.label:rename"
        ),
        "rename_semantic_key": "meta.attribute:ContentLayout.label",
        "old_semantic_key": "meta.attribute:ContentLayout.title",
        "new_semantic_key": "meta.attribute:ContentLayout.label",
    }

    assert create_operation["operation_family"] == "create"
    assert create_operation["semantic_key"] == "meta.attribute:ContentLayout.label"
    assert create_current["attribute_name"] == "label"
    assert create_current["attribute_config_id"] != (
        "00000000-0000-0000-0000-000000000721"
    )
    assert create_signature["name"] == "label"
    assert create_signature["default_value"] == "\"Untitled\""
    assert create_signature["type_descriptor"] == {
        "kind": "primitive",
        "primitive_base_type": "string",
    }
    assert create_source_operation["composition"] == {
        "composition_kind": "attribute_identity_rename_delete_create",
        "composition_part": "create_new",
        "source_operation_key": (
            "aware_meta.object_config_graph.attribute.identity:"
            "ContentLayout.label:rename"
        ),
        "rename_semantic_key": "meta.attribute:ContentLayout.label",
        "old_semantic_key": "meta.attribute:ContentLayout.title",
        "new_semantic_key": "meta.attribute:ContentLayout.label",
    }


def test_meta_semantic_apply_attribute_identity_rename_blocks_without_identity() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "delta_fingerprint": "sha256:attribute-identity-rename-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.attribute.identity:"
                                "ContentLayout.label:rename"
                            ),
                            "operation_family": "rename",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.attribute.identity.rename"
                            ),
                            "semantic_key": "meta.attribute:ContentLayout.label",
                            "semantic_subject_type": "aware_meta.AttributeConfig",
                            "field_path": "name",
                            "event_key": (
                                "meta.attribute:ContentLayout.label:name:rename"
                            ),
                            "source_refs": ("content/content_layout.aware",),
                            "before_payload": {
                                "class_name": "ContentLayout",
                                "attribute_name": "title",
                                "name": "title",
                            },
                            "after_payload": {
                                "class_name": "ContentLayout",
                                "attribute_name": "label",
                                "name": "label",
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_layout.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_blocked"
    assert typed_plan["typed_operations"] == []
    [blocked_operation] = cast(
        tuple[dict[str, object], ...],
        typed_plan["blocked_operations"],
    )
    assert blocked_operation["reason"] == (
        "meta_attribute_identity_rename_requires_explicit_policy"
    )
    blockers = cast(tuple[str, ...], blocked_operation["blockers"])
    assert blockers == (
        "attribute_identity_rename_missing_before_attribute_config_id",
        "explicit_fallback_required",
    )


def test_meta_semantic_apply_enum_identity_rename_composes_delete_create() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "delta_fingerprint": "sha256:enum-identity-rename-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.enum.identity:"
                                "ContentAudience:rename"
                            ),
                            "operation_family": "rename",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum.identity.rename"
                            ),
                            "semantic_key": "meta.enum:ContentAudience",
                            "semantic_subject_type": "aware_meta.EnumConfig",
                            "field_path": "name",
                            "event_key": "meta.enum:ContentAudience:name:rename",
                            "source_refs": ("content/content_enums.aware",),
                            "before_payload": {
                                "semantic_key": "meta.enum:LegacyAudience",
                                "name": "LegacyAudience",
                                "enum_name": "LegacyAudience",
                                "enum_fqn": (
                                    "aware_content.default.content.LegacyAudience"
                                ),
                                "graph_semantic_key": "ocg:aware_content",
                                "object_config_graph_node_id": (
                                    "00000000-0000-0000-0000-000000000521"
                                ),
                                "enum_config_id": (
                                    "00000000-0000-0000-0000-000000000522"
                                ),
                            },
                            "after_payload": {
                                "semantic_key": "meta.enum:ContentAudience",
                                "name": "ContentAudience",
                                "enum_name": "ContentAudience",
                                "enum_fqn": (
                                    "aware_content.default.content.ContentAudience"
                                ),
                                "graph_semantic_key": "ocg:aware_content",
                                "values": ("internal", "public"),
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_enums.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["blocked_operations"] == []
    operations = cast(tuple[dict[str, object], ...], typed_plan["typed_operations"])
    assert [operation["provider_operation_type"] for operation in operations] == [
        "meta_ocg.enum.delete",
        "meta_ocg.enum.create",
    ]

    delete_operation, create_operation = operations
    delete_current = cast(dict[str, object], delete_operation["current"])
    create_current = cast(dict[str, object], create_operation["current"])
    delete_event = cast(dict[str, object], delete_operation["source_semantic_change"])
    create_event = cast(dict[str, object], create_operation["source_semantic_change"])
    delete_source_operation = cast(
        dict[str, object],
        delete_event["semantic_source_operation"],
    )
    create_source_operation = cast(
        dict[str, object],
        create_event["semantic_source_operation"],
    )

    assert delete_operation["operation_family"] == "delete"
    assert delete_operation["semantic_key"] == "meta.enum:LegacyAudience"
    assert delete_current["name"] == "LegacyAudience"
    assert delete_current["object_config_graph_node_id"] == (
        "00000000-0000-0000-0000-000000000521"
    )
    assert delete_source_operation["composition"] == {
        "composition_kind": "enum_identity_rename_delete_create",
        "composition_part": "delete_old",
        "source_operation_key": (
            "aware_meta.object_config_graph.enum.identity:" "ContentAudience:rename"
        ),
        "rename_semantic_key": "meta.enum:ContentAudience",
        "old_semantic_key": "meta.enum:LegacyAudience",
        "new_semantic_key": "meta.enum:ContentAudience",
    }

    assert create_operation["operation_family"] == "create"
    assert create_operation["semantic_key"] == "meta.enum:ContentAudience"
    assert create_current["name"] == "ContentAudience"
    assert create_current["object_config_graph_node_id"] is None
    assert create_current["enum_config_id"] is None
    assert create_current["values"] == ("internal", "public")
    assert create_source_operation["composition"] == {
        "composition_kind": "enum_identity_rename_delete_create",
        "composition_part": "create_new",
        "source_operation_key": (
            "aware_meta.object_config_graph.enum.identity:" "ContentAudience:rename"
        ),
        "rename_semantic_key": "meta.enum:ContentAudience",
        "old_semantic_key": "meta.enum:LegacyAudience",
        "new_semantic_key": "meta.enum:ContentAudience",
    }


def test_meta_semantic_apply_enum_identity_rename_blocks_without_identity() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "delta_fingerprint": "sha256:enum-identity-rename-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.enum.identity:"
                                "ContentAudience:rename"
                            ),
                            "operation_family": "rename",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum.identity.rename"
                            ),
                            "semantic_key": "meta.enum:ContentAudience",
                            "semantic_subject_type": "aware_meta.EnumConfig",
                            "field_path": "name",
                            "event_key": "meta.enum:ContentAudience:name:rename",
                            "source_refs": ("content/content_enums.aware",),
                            "before_payload": {
                                "name": "LegacyAudience",
                                "enum_name": "LegacyAudience",
                            },
                            "after_payload": {
                                "name": "ContentAudience",
                                "enum_name": "ContentAudience",
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_enums.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_blocked"
    assert typed_plan["typed_operations"] == []
    [blocked_operation] = cast(
        tuple[dict[str, object], ...],
        typed_plan["blocked_operations"],
    )
    assert blocked_operation["reason"] == (
        "meta_enum_identity_rename_requires_explicit_policy"
    )
    blockers = cast(tuple[str, ...], blocked_operation["blockers"])
    assert blockers == (
        "enum_identity_rename_missing_before_object_config_graph_node_id",
        "explicit_fallback_required",
    )


def test_meta_semantic_apply_enum_name_scalar_update_blocks() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "delta_fingerprint": "sha256:enum-name-update-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.enum.identity:"
                                "ContentAudience:update"
                            ),
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum.name.update"
                            ),
                            "semantic_key": "meta.enum:ContentAudience",
                            "semantic_subject_type": "aware_meta.EnumConfig",
                            "field_path": "name",
                            "event_key": "meta.enum:ContentAudience:name:update",
                            "source_refs": ("content/content_enums.aware",),
                            "before_payload": {
                                "name": "LegacyAudience",
                                "enum_name": "LegacyAudience",
                            },
                            "after_payload": {
                                "name": "ContentAudience",
                                "enum_name": "ContentAudience",
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_enums.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_blocked"
    assert typed_plan["typed_operations"] == []
    [blocked_operation] = cast(
        tuple[dict[str, object], ...],
        typed_plan["blocked_operations"],
    )
    assert blocked_operation["reason"] == (
        "meta_enum_identity_rename_requires_explicit_policy"
    )
    blockers = cast(tuple[str, ...], blocked_operation["blockers"])
    assert "enum_identity_must_not_use_scalar_update" in blockers


def test_meta_semantic_apply_enum_structural_delete_stays_in_ready_plan() -> None:
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "delta_fingerprint": "sha256:enum-structural-fallback-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.enum.identity:"
                                "ContentSource:create"
                            ),
                            "operation_family": "create",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum.create"
                            ),
                            "semantic_key": "meta.enum:ContentSource",
                            "semantic_subject_type": "aware_meta.EnumConfig",
                            "field_path": "name",
                            "event_key": "meta.enum:ContentSource:name:upsert",
                            "source_refs": ("content/content_enums.aware",),
                            "before_payload": None,
                            "after_payload": {
                                "name": "ContentSource",
                                "enum_name": "ContentSource",
                            },
                        },
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.enum.description:"
                                "ContentSource:update"
                            ),
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum.description.update"
                            ),
                            "semantic_key": "meta.enum:ContentSource",
                            "semantic_subject_type": "aware_meta.EnumConfig",
                            "field_path": "description",
                            "event_key": ("meta.enum:ContentSource:description:update"),
                            "source_refs": ("content/content_enums.aware",),
                            "before_payload": {
                                "enum_name": "ContentSource",
                                "description": "Original.",
                            },
                            "after_payload": {
                                "enum_name": "ContentSource",
                                "description": "Updated.",
                            },
                        },
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.enum.identity:"
                                "LegacySource:delete"
                            ),
                            "operation_family": "delete",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum.delete"
                            ),
                            "semantic_key": "meta.enum:LegacySource",
                            "semantic_subject_type": "aware_meta.EnumConfig",
                            "field_path": "name",
                            "event_key": "meta.enum:LegacySource:name:delete",
                            "source_refs": ("content/content_enums.aware",),
                            "before_payload": {
                                "name": "LegacySource",
                                "enum_name": "LegacySource",
                                "enum_fqn": (
                                    "aware_content.default.content.LegacySource"
                                ),
                                "graph_semantic_key": "ocg:aware_content",
                                "object_config_graph_node_id": (
                                    "00000000-0000-0000-0000-000000000411"
                                ),
                                "enum_config_id": (
                                    "00000000-0000-0000-0000-000000000412"
                                ),
                            },
                            "after_payload": None,
                        },
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.enum_option:"
                                "LegacySource.old:delete"
                            ),
                            "operation_family": "delete",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum_option.delete"
                            ),
                            "semantic_key": "meta.enum:LegacySource/option:old",
                            "semantic_subject_type": "aware_meta.EnumOption",
                            "field_path": "value",
                            "event_key": (
                                "meta.enum:LegacySource/option:old:value:delete"
                            ),
                            "source_refs": ("content/content_enums.aware",),
                            "before_payload": {
                                "enum_semantic_key": "meta.enum:LegacySource",
                                "enum_name": "LegacySource",
                                "enum_fqn": (
                                    "aware_content.default.content.LegacySource"
                                ),
                                "value": "old",
                                "position": 0,
                            },
                            "after_payload": None,
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_enums.aware",),
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["reason"] == (
        "semantic_apply_source_projection_from_semantic_source_meaning"
    )
    operations = cast(
        tuple[dict[str, object], ...],
        typed_plan["typed_operations"],
    )
    assert len(operations) == 3
    assert {item["provider_operation_type"] for item in operations} == {
        "meta_ocg.enum.create",
        "meta_ocg.enum.update",
        "meta_ocg.enum.delete",
    }
    delete_operation = next(
        item for item in operations if item["operation_family"] == "delete"
    )
    current = _mapping(delete_operation["current"])
    assert delete_operation["provider_operation_type"] == "meta_ocg.enum.delete"
    assert delete_operation["semantic_subject_type"] == "aware_meta.ObjectConfigGraph"
    assert current["graph_semantic_key"] == "ocg:aware_content"
    assert current["object_config_graph_node_id"] == (
        "00000000-0000-0000-0000-000000000411"
    )
    assert current["enum_config_id"] == "00000000-0000-0000-0000-000000000412"
    assert typed_plan["blocked_operations"] == []


def test_meta_enum_structural_delete_source_projection_emits_node_anchor() -> None:
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        _typed_operation_plan(_enum_structural_delete_operation()),
        package_name="content-ontology",
        target_language="aware",
    )

    assert len(feature_results) == 1
    result = feature_results[0]
    assert result.feature_key == "enum_config"
    assert result.status == "source_projection_projected"
    assert result.reason == (
        "meta_source_projection_enum_config_structural_delete_grammar_anchor_ready"
    )
    assert result.projected is True
    assert result.projected_entry_count == 0
    assert result.grammar_anchor_binding_count == 1
    assert result.grammar_anchor_source_count == 1
    assert result.grammar_anchor_replacement_count == 1
    binding = result.grammar_anchor_bindings[0]
    source = result.grammar_anchor_sources[0]
    replacement = result.grammar_anchor_replacements[0]

    assert binding.grammar_rule_name == "enum_def"
    assert binding.anchor_field_path == "__node__"
    assert binding.graph_selector.object_key == (
        "aware_content.default.content.LegacySource"
    )
    assert binding.graph_selector.field_path == "LegacySource.__node__"
    assert source.source_key == "content/content_enums.aware"
    assert replacement.replacement_text == ""
    assert replacement.binding_key == binding.binding_key


def test_meta_enum_structural_delete_source_projection_normalizes_aware_root_source_refs() -> (
    None
):
    operation = _enum_structural_delete_operation()
    operation["source_refs"] = (
        "aware/content/content_enums.aware",
        "content/content_enums.aware",
    )

    feature_results = source_projection_feature_results_from_meta_typed_operations(
        _typed_operation_plan(operation),
        package_name="content-ontology",
        package_root="workspaces/aware_kernel/modules/content/ontology/structure",
        sources_root="workspaces/aware_kernel/modules/content/ontology/structure/aware",
        target_language="aware",
    )

    [result] = feature_results
    assert result.status == "source_projection_projected"
    [source] = result.grammar_anchor_sources
    [replacement] = result.grammar_anchor_replacements
    assert source.source_key == "content/content_enums.aware"
    assert source.relative_path == "content/content_enums.aware"
    assert replacement.source_key == "content/content_enums.aware"


def test_meta_enum_structural_delete_source_projection_stage_is_ready(
    tmp_path,
) -> None:
    typed_operation_plan = _typed_operation_plan(_enum_structural_delete_operation())
    report = _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "ready",
            "dirty_entry_count": 1,
        },
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    stage = provider_delta_source_projection_stage(
        package_payload={"package_name": "content-ontology"},
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=report,
        provider_delta_typed_operation_plan=typed_operation_plan,
        code_package_delta=SimpleNamespace(
            package_name="content-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware",
            paths=(
                SimpleNamespace(
                    relative_path="content/content_enums.aware",
                    language=CodeLanguage.aware,
                ),
            ),
        ),
    )

    assert stage["status"] == "source_projection_ready"
    assert stage["reason"] == "meta_source_projection_grammar_anchor_render_delta_ready"
    assert stage["ready"] is True
    assert stage["projected_entry_count"] == 0
    assert stage["grammar_anchor_binding_count"] == 1
    assert stage["grammar_anchor_source_count"] == 1
    assert stage["grammar_anchor_replacement_count"] == 1
    render_request = cast(
        dict[str, object],
        stage["grammar_anchor_render_delta_request"],
    )
    bindings = cast(list[dict[str, object]], render_request["bindings"])
    replacements = cast(list[dict[str, object]], render_request["replacements"])

    assert render_request["package_name"] == "content-ontology"
    assert bindings[0]["grammar_rule_name"] == "enum_def"
    assert bindings[0]["anchor_field_path"] == "__node__"
    assert replacements[0]["replacement_text"] == ""


def test_meta_class_structural_delete_source_projection_emits_node_anchor() -> None:
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        _typed_operation_plan(_class_structural_delete_operation()),
        package_name="content-ontology",
        target_language="aware",
    )

    assert len(feature_results) == 1
    result = feature_results[0]
    assert result.feature_key == "class_config"
    assert result.status == "source_projection_projected"
    assert result.reason == (
        "meta_source_projection_class_config_structural_delete_grammar_anchor_ready"
    )
    assert result.projected is True
    assert result.projected_entry_count == 0
    assert result.grammar_anchor_binding_count == 1
    assert result.grammar_anchor_source_count == 1
    assert result.grammar_anchor_replacement_count == 1
    binding = result.grammar_anchor_bindings[0]
    source = result.grammar_anchor_sources[0]
    replacement = result.grammar_anchor_replacements[0]

    assert binding.grammar_rule_name == "class_def"
    assert binding.anchor_field_path == "__node__"
    assert binding.graph_selector.object_key == (
        "aware_content.default.content.ContentPlacement"
    )
    assert binding.graph_selector.class_fqn == (
        "aware_content.default.content.ContentPlacement"
    )
    assert binding.graph_selector.class_name == "ContentPlacement"
    assert binding.graph_selector.field_path == "ContentPlacement.__node__"
    assert source.source_key == "content/content_layout.aware"
    assert replacement.replacement_text == ""
    assert replacement.binding_key == binding.binding_key


def test_meta_class_structural_delete_source_projection_normalizes_aware_root_source_refs() -> (
    None
):
    operation = _class_structural_delete_operation()
    operation["source_refs"] = (
        "aware/content/content_layout.aware",
        "content/content_layout.aware",
    )

    feature_results = source_projection_feature_results_from_meta_typed_operations(
        _typed_operation_plan(operation),
        package_name="content-ontology",
        package_root="workspaces/aware_kernel/modules/content/ontology/structure",
        sources_root="workspaces/aware_kernel/modules/content/ontology/structure/aware",
        target_language="aware",
    )

    [result] = feature_results
    assert result.status == "source_projection_projected"
    [source] = result.grammar_anchor_sources
    [replacement] = result.grammar_anchor_replacements
    assert source.source_key == "content/content_layout.aware"
    assert source.relative_path == "content/content_layout.aware"
    assert replacement.source_key == "content/content_layout.aware"


def test_meta_class_structural_delete_source_projection_stage_is_ready(
    tmp_path,
) -> None:
    typed_operation_plan = _typed_operation_plan(_class_structural_delete_operation())
    report = _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "ready",
            "dirty_entry_count": 1,
        },
        provider_delta_typed_operation_plan=typed_operation_plan,
    )

    stage = provider_delta_source_projection_stage(
        package_payload={"package_name": "content-ontology"},
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=report,
        provider_delta_typed_operation_plan=typed_operation_plan,
        code_package_delta=SimpleNamespace(
            package_name="content-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware",
            paths=(
                SimpleNamespace(
                    relative_path="content/content_layout.aware",
                    language=CodeLanguage.aware,
                ),
            ),
        ),
    )

    assert stage["status"] == "source_projection_ready"
    assert stage["reason"] == "meta_source_projection_grammar_anchor_render_delta_ready"
    assert stage["ready"] is True
    assert stage["projected_entry_count"] == 0
    assert stage["grammar_anchor_binding_count"] == 1
    assert stage["grammar_anchor_source_count"] == 1
    assert stage["grammar_anchor_replacement_count"] == 1
    render_request = cast(
        dict[str, object],
        stage["grammar_anchor_render_delta_request"],
    )
    bindings = cast(list[dict[str, object]], render_request["bindings"])
    replacements = cast(list[dict[str, object]], render_request["replacements"])

    assert render_request["package_name"] == "content-ontology"
    assert bindings[0]["grammar_rule_name"] == "class_def"
    assert bindings[0]["anchor_field_path"] == "__node__"
    assert replacements[0]["replacement_text"] == ""


def test_meta_semantic_apply_function_signature_source_meaning_builds_update_operation() -> (
    None
):
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "home-ontology",
                "delta_fingerprint": "sha256:function-signature-current-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.function.signature:"
                                "TvChannel.rename:update"
                            ),
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.function."
                                "signature.update"
                            ),
                            "semantic_key": "meta.function:TvChannel.rename",
                            "semantic_subject_type": "aware_meta.FunctionConfig",
                            "field_path": "signature",
                            "event_key": (
                                "meta.function:TvChannel.rename:signature:update"
                            ),
                            "source_refs": ("home/tv_channel.aware",),
                            "before_payload": {
                                "signature": ("(display_name String) -> TvChannel"),
                                "class_name": "TvChannel",
                                "function_name": "rename",
                                "function_description": "Rename the channel.",
                            },
                            "after_payload": {
                                "signature": "(label String) -> TvChannel",
                                "class_name": "TvChannel",
                                "function_name": "rename",
                                "function_description": "Rename the channel.",
                            },
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("home/tv_channel.aware",),
    )

    typed_operations = cast(
        list[dict[str, object]],
        typed_plan["typed_operations"],
    )
    assert typed_plan["status"] == "typed_operation_plan_ready"
    [operation] = typed_operations
    assert operation["operation_family"] == "update"
    assert operation["provider_operation_type"] == "meta_ocg.function.update"
    assert operation["ontology_subject_kind"] == "function"
    assert operation["semantic_subject_type"] == "aware_meta.FunctionConfig"
    baseline = cast(dict[str, object], operation["baseline"])
    baseline_object = cast(dict[str, object], baseline["object"])
    baseline_signature = cast(
        dict[str, object],
        baseline_object["function_signature"],
    )
    current = cast(dict[str, object], operation["current"])
    current_signature = cast(dict[str, object], current["function_signature"])
    assert baseline_signature["signature_text"] == (
        "(display_name String) -> TvChannel"
    )
    assert current_signature["signature_text"] == "(label String) -> TvChannel"
    baseline_inputs = cast(tuple[dict[str, object], ...], baseline_signature["inputs"])
    current_inputs = cast(tuple[dict[str, object], ...], current_signature["inputs"])
    outputs = cast(tuple[dict[str, object], ...], current_signature["outputs"])
    assert baseline_inputs[0]["name"] == "display_name"
    assert current_inputs[0]["name"] == "label"
    output_descriptor = cast(dict[str, object], outputs[0]["type_descriptor"])
    assert output_descriptor == {"kind": "class", "class_fqn": "TvChannel"}

    feature_results = source_projection_feature_results_from_meta_typed_operations(
        typed_plan,
        package_name="home-ontology",
        target_language="aware",
    )
    [result] = feature_results
    assert result.status == "source_projection_projected"
    assert result.reason == (
        "meta_source_projection_function_config_signature_segment_delta_ready"
    )
    [entry] = result.entries
    assert entry.segment_ref is not None
    assert entry.segment_ref.segment_name == "signature"
    assert entry.content_text == "(label String) -> TvChannel"


def test_meta_semantic_apply_function_delete_source_meaning_preserves_source_identity() -> (
    None
):
    semantic_status = {
        "status": "ready",
        "packages": (
            {
                "package_name": "content-ontology",
                "delta_fingerprint": "sha256:function-delete-current-delta",
                "semantic_source_meaning": {
                    "typed_operations": (
                        {
                            "operation_key": (
                                "aware_meta.object_config_graph.function:"
                                "ContentLayout.render:delete"
                            ),
                            "operation_family": "delete",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.function.delete"
                            ),
                            "semantic_key": "meta.function:ContentLayout.render",
                            "semantic_subject_type": "aware_meta.FunctionConfig",
                            "field_path": "definition",
                            "event_key": (
                                "meta.function:ContentLayout.render:"
                                "definition:delete"
                            ),
                            "source_refs": ("content/content_layout.aware",),
                            "semantic_source_object_id": "function-source-id",
                            "semantic_apply_receiver_object_id": (
                                "function-executable-id"
                            ),
                            "generated_materialization": {
                                "python_orm": {
                                    "relative_path": (
                                        "aware_content_ontology/content/"
                                        "content_layout.py"
                                    ),
                                },
                            },
                            "before_payload": {
                                "class_name": "ContentLayout",
                                "class_fqn": (
                                    "aware_content.default.content.ContentLayout"
                                ),
                                "class_config_id": "class-executable-id",
                                "function_name": "render",
                                "name": "render",
                                "kind": "instance",
                                "function_config_id": "function-executable-id",
                                "entity_id": "function-executable-id",
                                "object_id": "function-executable-id",
                                "definition": "fn render() -> String {\n    }",
                            },
                            "after_payload": None,
                        },
                    ),
                },
            },
        ),
    }

    typed_plan = typed_operation_plan_from_semantic_source_meaning(
        semantic_status=semantic_status,
        default_source_refs=("content/content_layout.aware",),
    )

    typed_operations = cast(
        list[dict[str, object]],
        typed_plan["typed_operations"],
    )
    assert typed_plan["status"] == "typed_operation_plan_ready"
    [operation] = typed_operations
    assert operation["operation_family"] == "delete"
    assert operation["provider_operation_type"] == "meta_ocg.function.delete"
    current = cast(dict[str, object], operation["current"])
    payload = cast(dict[str, object], current["payload"])
    baseline = cast(dict[str, object], operation["baseline"])
    baseline_object = cast(dict[str, object], baseline["object"])
    membership = cast(dict[str, object], current["function_membership_signature"])
    assert current["class_config_id"] == "class-executable-id"
    assert current["function_config_id"] == "function-source-id"
    assert current["semantic_source_object_id"] == "function-source-id"
    assert current["semantic_apply_receiver_object_id"] == "function-executable-id"
    assert current["generated_materialization"] == {
        "python_orm": {
            "relative_path": "aware_content_ontology/content/content_layout.py",
        },
    }
    assert payload["function_config_id"] == "function-source-id"
    assert payload["semantic_source_object_id"] == "function-source-id"
    assert baseline["object_id"] == "function-source-id"
    assert baseline["semantic_source_object_id"] == "function-source-id"
    assert baseline_object["function_config_id"] == "function-source-id"
    assert baseline_object["semantic_source_object_id"] == "function-source-id"
    assert membership["class_config_id"] == "class-executable-id"
    assert membership["function_config_id"] == "function-source-id"


def test_meta_source_projection_boundary_does_not_import_code_service_or_workspace() -> (
    None
):
    source_root = Path(__file__).resolve().parents[2] / "aware_meta"
    forbidden_tokens = (
        "aware_code" + "_api",
        "aware_code_service_api" + ".models",
        "from aware_code_service import",
        "import aware_code_service",
        "from aware_code_sdk",
        "import aware_code_sdk",
        "from aware_workspace",
        "import aware_workspace",
    )
    checked_paths = sorted(source_root.rglob("source_projection.py")) + [
        source_root / "materialization" / "deltas" / "code_dto.py",
    ]
    offenders: list[str] = []
    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in text:
                offenders.append(f"{path.relative_to(source_root)}:{token}")

    assert offenders == []
    assert "aware_code_service_dto" in (
        source_root / "materialization" / "deltas" / "code_dto.py"
    ).read_text(encoding="utf-8")


def test_meta_function_config_description_source_projection_result_is_projected() -> (
    None
):
    typed_operation_plan = _typed_operation_plan(
        _function_impl_operation(),
        _function_description_operation(),
    )
    report = _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "reason": "ready",
            "dirty_entry_count": 2,
        },
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    projection = code_source_projection_request_from_meta_change_report(
        report,
        package_name="home-ontology",
        package_root=".",
        sources_root="home",
        target_language="aware",
    )
    feature_results = source_projection_feature_results_from_meta_typed_operations(
        typed_operation_plan,
        package_name=projection.package_name,
        target_language=projection.target_language,
    )

    result = code_source_projection_result_from_meta_feature_results(
        report,
        projection=projection,
        feature_results=feature_results,
    )

    assert result.projected is True
    assert result.delta_set is not None
    assert len(result.delta_set.entries) == 2
    assert {
        entry.segment_ref.segment_name
        for entry in result.delta_set.entries
        if entry.segment_ref is not None
    } == {"body", "description_comment"}
    assert {entry.event_ref for entry in result.delta_set.entries} == {
        "aware_meta.provider_delta.world_change.function_impl.update",
        "aware_meta.provider_delta.world_change.function.update",
    }
    assert result.skipped_events == []


def test_meta_function_config_description_projection_blocks_missing_source_ref() -> (
    None
):
    operation = _function_description_operation()
    operation["source_refs"] = ()

    feature_results = source_projection_feature_results_from_meta_typed_operations(
        _typed_operation_plan(operation),
        package_name="home-ontology",
        target_language="aware",
    )

    assert len(feature_results) == 1
    result = feature_results[0]
    assert result.feature_key == "function_config"
    assert result.status == "source_projection_blocked"
    assert result.blocked is True
    assert result.projected is False
    assert result.reason == (
        "meta_source_projection_function_config_description_requires_renderable_segment"
    )
    assert result.required_evidence_fields == (
        "single_source_ref",
        "function_name",
        "owner_key",
        "renderable_description_text",
    )
    assert result.missing_evidence_fields == ("single_source_ref",)
    assert result.entries == ()


def _typed_operation_plan(
    *typed_operations: dict[str, object],
) -> dict[str, object]:
    return {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operations": typed_operations,
        "semantic_object_anchors": (),
        "blocked_operations": (),
    }


def _function_impl_operation() -> dict[str, object]:
    class_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
    function_key = f"{class_key}.rename"
    function_impl_key = f"{function_key}/function_impl:default"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg_provider_delta:update:{function_impl_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.function_impl.update",
        "semantic_key": function_impl_key,
        "semantic_subject_type": "aware_meta.FunctionImpl",
        "ontology_subject_kind": "function_impl",
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {
            "object": {
                "function_impl_signature": {
                    "instruction_count": 0,
                    "instruction_summaries": (),
                    "instructions": (),
                },
            },
        },
        "current": {
            "function_semantic_key": function_key,
            "function_name": "rename",
            "function_impl_key": "default",
            "function_impl_kind": "instruction_body",
            "function_impl_signature": {
                "instruction_count": 1,
                "instruction_summaries": ("set name = display_name",),
            },
            "source_projection": {
                "relative_path": "home/tv_channel.aware",
                "language": "aware",
                "section_type": "function",
                "qualname": "TvChannel.rename",
                "segment_name": "body",
                "content_text": "set name = display_name",
                "before_segment_hash": _digest(""),
            },
        },
    }


def _attribute_operation() -> dict[str, object]:
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": "meta_ocg_provider_delta:update:attribute:name",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.attribute.update",
        "semantic_key": "ocg:aware_demo/node:aware_demo.default.home.TvChannel/attribute:name",
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {
            "object": {
                "attribute_name": "name",
                "attribute_signature": {"kind": "primitive"},
            },
        },
        "current": {
            "attribute_name": "name",
            "attribute_signature": {"kind": "primitive"},
        },
    }


def _attribute_type_operation() -> dict[str, object]:
    operation = _attribute_operation()
    semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
        "/attribute:selected_channel"
    )
    baseline_signature = {
        "owner_key": "aware_demo.default.home.TvChannel",
        "name": "selected_channel",
        "description": "Selected channel index.",
        "default_value": None,
        "is_required": False,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": "integer",
        },
    }
    current_signature = {
        **baseline_signature,
        "description": "Selected channel identifier.",
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": "string",
        },
    }
    operation.update(
        {
            "operation_key": f"meta_ocg_provider_delta:update:{semantic_key}",
            "semantic_key": semantic_key,
            "source_refs": ("home/tv_channel.aware",),
            "baseline": {
                "object": {
                    "attribute_name": "selected_channel",
                    "attribute_signature": baseline_signature,
                },
            },
            "current": {
                "attribute_name": "selected_channel",
                "owner_key": "aware_demo.default.home.TvChannel",
                "attribute_signature": current_signature,
            },
        }
    )
    return operation


def _attribute_default_value_operation() -> dict[str, object]:
    operation = _attribute_operation()
    semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
        "/attribute:selected_channel"
    )
    baseline_signature = {
        "owner_key": "aware_demo.default.home.TvChannel",
        "name": "selected_channel",
        "description": "Selected channel index.",
        "default_value": "7",
        "is_required": True,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": "integer",
        },
    }
    current_signature = {
        **baseline_signature,
        "default_value": "11",
    }
    operation.update(
        {
            "operation_key": f"meta_ocg_provider_delta:update:{semantic_key}",
            "semantic_key": semantic_key,
            "source_refs": ("home/tv_channel.aware",),
            "baseline": {
                "object": {
                    "attribute_name": "selected_channel",
                    "attribute_signature": baseline_signature,
                },
            },
            "current": {
                "attribute_name": "selected_channel",
                "owner_key": "aware_demo.default.home.TvChannel",
                "attribute_signature": current_signature,
            },
        }
    )
    return operation


def _enum_structural_delete_operation() -> dict[str, object]:
    semantic_key = "meta.enum:LegacySource"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum.delete:{semantic_key}",
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.enum.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraph",
        "ontology_subject_kind": "enum",
        "source_refs": ("content/content_enums.aware",),
        "baseline": {
            "object": {
                "name": "LegacySource",
                "enum_name": "LegacySource",
                "enum_fqn": "aware_content.default.content.LegacySource",
            },
        },
        "current": {
            "name": "LegacySource",
            "enum_name": "LegacySource",
            "enum_fqn": "aware_content.default.content.LegacySource",
            "node_key": "aware_content.default.content.LegacySource",
            "graph_semantic_key": "ocg:aware_content",
            "object_config_graph_node_id": "00000000-0000-0000-0000-000000000411",
            "enum_config_id": "00000000-0000-0000-0000-000000000412",
        },
    }


def _class_structural_delete_operation() -> dict[str, object]:
    semantic_key = "meta.class:ContentPlacement"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.class.delete:{semantic_key}",
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.class.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraph",
        "ontology_subject_kind": "class",
        "source_refs": ("content/content_layout.aware",),
        "baseline": {
            "object": {
                "name": "ContentPlacement",
                "class_name": "ContentPlacement",
                "class_fqn": "aware_content.default.content.ContentPlacement",
            },
        },
        "current": {
            "name": "ContentPlacement",
            "entity_name": "ContentPlacement",
            "class_name": "ContentPlacement",
            "class_fqn": "aware_content.default.content.ContentPlacement",
            "node_key": "aware_content.default.content.ContentPlacement",
            "graph_semantic_key": "ocg:aware_content",
            "object_config_graph_node_id": "00000000-0000-0000-0000-000000000511",
            "class_config_id": "00000000-0000-0000-0000-000000000512",
        },
    }


def _attribute_structural_create_semantic_operation() -> dict[str, object]:
    return {
        "operation_key": (
            "aware_meta.object_config_graph.attribute.ContentLayout.title:create"
        ),
        "operation_family": "create",
        "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
        "semantic_key": "meta.attribute:ContentLayout.title",
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "field_path": "definition",
        "event_key": "meta.attribute:ContentLayout.title:definition:upsert",
        "source_refs": ("content/content_layout.aware",),
        "package_name": "content-ontology",
        "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
        "after_payload": {
            "definition": "title String",
            "class_name": "ContentLayout",
            "attribute_name": "title",
            "type": "String",
        },
    }


def _attribute_structural_delete_semantic_operation() -> dict[str, object]:
    return {
        "operation_key": (
            "aware_meta.object_config_graph.attribute.ContentLayout.title:delete"
        ),
        "operation_family": "delete",
        "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION,
        "semantic_key": "meta.attribute:ContentLayout.title",
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "field_path": "definition",
        "event_key": "meta.attribute:ContentLayout.title:definition:delete",
        "source_refs": ("content/content_layout.aware",),
        "package_name": "content-ontology",
        "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
        "before_payload": {
            "definition": "title String",
            "class_name": "ContentLayout",
            "attribute_name": "title",
            "type": "String",
        },
    }


def _class_operation() -> dict[str, object]:
    return _structural_operation(
        subject_kind="class",
        operation_family="update",
        semantic_key="ocg:aware_demo/node:aware_demo.default.home.TvChannel",
        provider_operation_type="meta_ocg.class.update",
    )


def _relationship_operation() -> dict[str, object]:
    return _structural_operation(
        subject_kind="relationship",
        operation_family="update",
        semantic_key=(
            "ocg:aware_demo/node:aware_demo.default.home.Room:room_devices:"
            "one_to_many:aware_demo.default.home.Device"
        ),
        provider_operation_type="meta_ocg.relationship.update",
    )


def _attribute_membership_operation() -> dict[str, object]:
    return _structural_operation(
        subject_kind="attribute_membership",
        operation_family="update",
        semantic_key=(
            "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
            "/attribute:name/membership:class_config"
        ),
        provider_operation_type="meta_ocg.attribute_membership.update",
    )


def _function_operation() -> dict[str, object]:
    return _structural_operation(
        subject_kind="function",
        operation_family="update",
        semantic_key="ocg:aware_demo/node:aware_demo.default.home.TvChannel.rename",
        provider_operation_type="meta_ocg.function.update",
    )


def _function_description_operation() -> dict[str, object]:
    operation = _function_operation()
    baseline_signature = {
        "owner_key": "aware_demo.default.home.TvChannel",
        "name": "rename",
        "kind": "instance",
        "description": "Rename the channel display label for humans and assistants.",
    }
    current_signature = {
        **baseline_signature,
        "description": (
            "Rename the channel display label and keep assistant-facing media "
            "context synchronized."
        ),
    }
    operation["baseline"] = {
        "object": {
            "function_name": "rename",
            "owner_semantic_key": (
                "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
            ),
            "function_signature": baseline_signature,
        },
    }
    operation["current"] = {
        "function_name": "rename",
        "owner_semantic_key": ("ocg:aware_demo/node:aware_demo.default.home.TvChannel"),
        "function_signature": current_signature,
    }
    return operation


def _function_signature_operation() -> dict[str, object]:
    operation = _function_operation()
    baseline_signature = {
        "owner_key": "aware_demo.default.home.TvChannel",
        "name": "rename",
        "kind": "instance",
        "description": "Rename the channel display label.",
        "inputs": (
            {
                "name": "display_name",
                "type": "input",
                "position": 0,
                "is_required": True,
                "type_descriptor": {
                    "kind": "primitive",
                    "primitive_base_type": "string",
                },
            },
        ),
        "outputs": (
            {
                "name": "result",
                "type": "output",
                "position": 0,
                "is_required": True,
                "type_descriptor": {
                    "kind": "class",
                    "class_fqn": "aware_demo.default.home.TvChannel",
                },
            },
        ),
    }
    current_signature = {
        **baseline_signature,
        "inputs": (
            {
                "name": "label",
                "type": "input",
                "position": 0,
                "is_required": True,
                "type_descriptor": {
                    "kind": "primitive",
                    "primitive_base_type": "string",
                },
            },
        ),
    }
    operation["baseline"] = {
        "object": {
            "function_name": "rename",
            "owner_semantic_key": (
                "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
            ),
            "function_signature": baseline_signature,
        },
    }
    operation["current"] = {
        "function_name": "rename",
        "owner_semantic_key": ("ocg:aware_demo/node:aware_demo.default.home.TvChannel"),
        "function_signature": current_signature,
    }
    return operation


def _function_membership_operation() -> dict[str, object]:
    return _structural_operation(
        subject_kind="function_membership",
        operation_family="update",
        semantic_key=(
            "ocg:aware_demo/node:aware_demo.default.home.TvChannel.rename"
            "/membership:class_config"
        ),
        provider_operation_type="meta_ocg.function_membership.update",
    )


def _structural_operation(
    *,
    subject_kind: str,
    operation_family: str,
    semantic_key: str,
    provider_operation_type: str,
) -> dict[str, object]:
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            f"meta_ocg_provider_delta:{operation_family}:"
            f"{subject_kind}:{semantic_key}"
        ),
        "operation_family": operation_family,
        "provider_operation_type": provider_operation_type,
        "semantic_key": semantic_key,
        "semantic_subject_type": f"aware_meta.{subject_kind}",
        "ontology_subject_kind": subject_kind,
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {"object": {}},
        "current": {"payload": {}},
    }


def _digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _mapping(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}
