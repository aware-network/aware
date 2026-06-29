from __future__ import annotations

from hashlib import sha256
from typing import Any, cast

import pytest

from aware_code_service import build_aware_code_service_protocol_handler
from aware_meta.class_.config.relationship.deltas.generated_materialization import (
    META_PYTHON_ORM_RELATIONSHIP_ANCHOR_KEY,
    META_PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
    MetaPythonOrmRelationshipGeneratedMaterializationContext,
    generated_materialization_feature_results_from_relationship_config_typed_operation,
    python_orm_generated_materialization_delta_from_relationship_config_typed_operation,
)
from aware_meta.class_.config.relationship.deltas.source_projection import (
    RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_READY_REASON,
    source_projection_feature_results_from_relationship_config_typed_operation,
)
from aware_meta.materialization.deltas.code_dto import (
    CodeSectionDeltaOperationKind,
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedRendererDeltaOperationKind,
    CodeGrammarAnchorRenderTargetKind,
    ResolveCodeGeneratedMaterializationPackageDeltaRequest,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaGeneratedMaterializationContext,
    MetaProviderDeltaSourceProjectionContext,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


@pytest.mark.asyncio
async def test_meta_python_orm_relationship_load_policy_delta_resolves_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from pydantic import Field\n"
        "\n"
        "class TvChannel:\n"
        "    channel_number: str\n"
        "\n"
        "\n"
        "class RemoteControl:\n"
        "    selected_channel: TvChannel | None = Field(default=None)\n",
        encoding="utf-8",
    )
    evidence = python_orm_generated_materialization_delta_from_relationship_config_typed_operation(
        _relationship_load_policy_typed_operation(),
        context=MetaPythonOrmRelationshipGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=generated_package_root.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert evidence.result.diagnostics == []
    entry = evidence.result.entries[0]
    assert (
        entry.mode is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert entry.section_delta is None
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == "    selected_channel: TvChannel\n"
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest(
        "    selected_channel: TvChannel | None = Field(default=None)\n"
    )
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == META_PYTHON_ORM_RELATIONSHIP_RENDERER_KEY
    assert operation.content_text == "    selected_channel: TvChannel\n"
    assert operation.before_hash == _digest(
        "    selected_channel: TvChannel | None = Field(default=None)\n"
    )
    assert operation.after_hash == _digest("    selected_channel: TvChannel\n")
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_RELATIONSHIP_ANCHOR_KEY
    assert operation.anchor.anchor_role == "relationship_load_policy_field"

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.grammar_anchor_render_entry_count == 1
    assert resolved.package_delta is not None
    assert resolved.package_delta.package_root == generated_package_root.as_posix()
    assert resolved.package_delta.sources_root == "aware_home_ontology"
    assert resolved.package_delta.paths[0].relative_path == "home/tv_channel.py"
    assert resolved.package_delta.paths[0].content_text == (
        "from __future__ import annotations\n"
        "\n"
        "from pydantic import Field\n"
        "\n"
        "class TvChannel:\n"
        "    channel_number: str\n"
        "\n"
        "\n"
        "class RemoteControl:\n"
        "    selected_channel: TvChannel\n"
    )


@pytest.mark.asyncio
async def test_meta_python_orm_relationship_create_delta_resolves_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "model.py"
    generated_source_path.write_text(
        "from __future__ import annotations\n"
        "\n"
        "class Device:\n"
        "    name: str\n"
        "\n"
        "\n"
        "class Room:\n"
        "    room_name: str\n",
        encoding="utf-8",
    )
    evidence = python_orm_generated_materialization_delta_from_relationship_config_typed_operation(
        _relationship_create_typed_operation(),
        context=MetaPythonOrmRelationshipGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=generated_package_root.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert evidence.result.diagnostics == []
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == "    primary_device: Device\n"
    assert replacement.span_target is not None
    assert replacement.span_target.byte_start == replacement.span_target.byte_end
    assert replacement.span_target.before_text_hash == _digest("")
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.content_text == "    primary_device: Device\n"

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.grammar_anchor_render_entry_count == 1
    assert resolved.package_delta is not None
    assert resolved.package_delta.paths[0].relative_path == "home/model.py"
    assert resolved.package_delta.paths[0].content_text == (
        "from __future__ import annotations\n"
        "\n"
        "class Device:\n"
        "    name: str\n"
        "\n"
        "\n"
        "class Room:\n"
        "    room_name: str\n"
        "    primary_device: Device\n"
    )


@pytest.mark.asyncio
async def test_meta_python_orm_relationship_delete_delta_resolves_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "model.py"
    generated_source_path.write_text(
        "from __future__ import annotations\n"
        "\n"
        "class Device:\n"
        "    name: str\n"
        "\n"
        "\n"
        "class Room:\n"
        "    room_name: str\n"
        "    primary_device: Device\n",
        encoding="utf-8",
    )
    evidence = python_orm_generated_materialization_delta_from_relationship_config_typed_operation(
        _relationship_delete_typed_operation(),
        context=MetaPythonOrmRelationshipGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=generated_package_root.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert evidence.result.diagnostics == []
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == ""
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest(
        "    primary_device: Device\n"
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.content_text == ""

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.grammar_anchor_render_entry_count == 1
    assert resolved.package_delta is not None
    assert resolved.package_delta.paths[0].relative_path == "home/model.py"
    assert resolved.package_delta.paths[0].content_text == (
        "from __future__ import annotations\n"
        "\n"
        "class Device:\n"
        "    name: str\n"
        "\n"
        "\n"
        "class Room:\n"
        "    room_name: str\n"
    )


def test_relationship_generated_materialization_feature_provider_emits_result() -> None:
    [result] = (
        generated_materialization_feature_results_from_relationship_config_typed_operation(
            _relationship_load_policy_typed_operation(),
            context=MetaProviderDeltaGeneratedMaterializationContext(
                package_name="home-ontology",
                package_root="modules/home/structure/ontology",
                sources_root="aware",
                target_language="python",
            ),
        )
    )

    assert result.status == "generated_materialization_projected"
    assert result.feature_key == "relationship_config"
    assert result.result is not None
    assert (
        result.result.mode is CodeGeneratedMaterializationDeltaMode.fallback_full_render
    )
    assert result.result.entries[0].diagnostics == [
        "meta_python_orm_relationship_generated_materialization_renderer_operation_evidence_only",
        "meta_python_orm_relationship_generated_materialization_field_span_missing",
    ]


def test_relationship_source_projection_inserts_first_load_policy_annotation() -> None:
    [result] = (
        source_projection_feature_results_from_relationship_config_typed_operation(
            _relationship_first_load_policy_annotation_typed_operation(),
            context=MetaProviderDeltaSourceProjectionContext(
                package_name="home-ontology",
                target_language="aware",
            ),
        )
    )

    assert result.status == "source_projection_projected"
    assert result.reason == RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_READY_REASON
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.operation is CodeSectionDeltaOperationKind.insert_after_section
    assert entry.section_ref.relative_path == "home/tv_channel.aware"
    assert entry.section_ref.language == "aware"
    assert entry.section_ref.section_type == "class"
    assert entry.section_ref.qualname == "RemoteControl"
    assert entry.segment_ref is None
    assert entry.content_text == (
        "\nann home.RemoteControl::selected_channel load forward eager"
    )
    assert entry.metadata is not None
    assert (
        entry.metadata["source"]
        == "aware_meta.provider_delta.relationship_load_policy_annotation_insert_delta"
    )


def test_relationship_source_projection_ignores_aware_source_root_for_annotation_path() -> (
    None
):
    [result] = (
        source_projection_feature_results_from_relationship_config_typed_operation(
            _relationship_first_load_policy_annotation_typed_operation(
                source_ref="aware/home/tv_channel.aware",
            ),
            context=MetaProviderDeltaSourceProjectionContext(
                package_name="home-ontology",
                target_language="aware",
            ),
        )
    )

    entry = result.entries[0]
    assert entry.section_ref.relative_path == "aware/home/tv_channel.aware"
    assert entry.content_text == (
        "\nann home.RemoteControl::selected_channel load forward eager"
    )


def _relationship_load_policy_typed_operation() -> MetaProviderDeltaTypedOperation:
    baseline_signature = {
        "relationship_key": "selected_channel",
        "relationship_type": "many_to_one",
        "source_class_fqn": "home.RemoteControl",
        "target_class_fqn": "home.TvChannel",
        "forward_loading_strategy": "lazy",
    }
    current_signature = {
        **baseline_signature,
        "forward_loading_strategy": "eager",
    }
    operation = MetaProviderDeltaTypedOperation.from_payload(
        {
            "operation_kind": "meta_ocg_provider_delta_typed_operation",
            "operation_key": (
                "meta_ocg.relationship.update:"
                "meta.relationship:RemoteControl.selected_channel"
            ),
            "operation_family": "update",
            "provider_operation_type": "meta_ocg.relationship.update",
            "semantic_key": "meta.relationship:RemoteControl.selected_channel",
            "semantic_subject_type": "aware_meta.ClassConfigRelationship",
            "ontology_subject_kind": "relationship",
            "source_refs": ("home/tv_channel.aware",),
            "baseline": {
                "object": {
                    "relationship_key": "selected_channel",
                    "relationship_signature": baseline_signature,
                },
            },
            "current": {
                "relationship_key": "selected_channel",
                "source_class_fqn": "home.RemoteControl",
                "target_class_fqn": "home.TvChannel",
                "relationship_type": "many_to_one",
                "forward_loading_strategy": "eager",
                "relationship_signature": current_signature,
            },
        }
    )
    assert operation is not None
    return operation


def _relationship_first_load_policy_annotation_typed_operation(
    *,
    source_ref: str = "home/tv_channel.aware",
) -> MetaProviderDeltaTypedOperation:
    baseline_signature = {
        "relationship_key": "selected_channel",
        "relationship_type": "many_to_one",
        "source_class_fqn": "home.RemoteControl",
        "target_class_fqn": "home.TvChannel",
    }
    current_signature = {
        **baseline_signature,
        "forward_loading_strategy": "eager",
    }
    operation = MetaProviderDeltaTypedOperation.from_payload(
        {
            "operation_kind": "meta_ocg_provider_delta_typed_operation",
            "operation_key": (
                "meta_ocg.relationship.update:"
                "meta.relationship:RemoteControl.selected_channel"
            ),
            "operation_family": "update",
            "provider_operation_type": "meta_ocg.relationship.update",
            "semantic_key": "meta.relationship:RemoteControl.selected_channel",
            "semantic_subject_type": "aware_meta.ClassConfigRelationship",
            "ontology_subject_kind": "relationship",
            "source_refs": (source_ref,),
            "baseline": {
                "object": {
                    "relationship_key": "selected_channel",
                    "relationship_signature": baseline_signature,
                },
            },
            "current": {
                "relationship_key": "selected_channel",
                "source_class_fqn": "home.RemoteControl",
                "target_class_fqn": "home.TvChannel",
                "relationship_type": "many_to_one",
                "forward_loading_strategy": "eager",
                "relationship_signature": current_signature,
            },
        }
    )
    assert operation is not None
    return operation


def _relationship_create_typed_operation() -> MetaProviderDeltaTypedOperation:
    current_signature = {
        "source_class_fqn": "home.Room",
        "target_class_fqn": "home.Device",
        "relationship_key": "primary_device",
        "relationship_type": "many_to_one",
        "forward_loading_strategy": "eager",
    }
    operation = MetaProviderDeltaTypedOperation.from_payload(
        {
            "operation_kind": "meta_ocg_provider_delta_typed_operation",
            "operation_key": (
                "meta_ocg.relationship.create:"
                "meta.relationship:Room.primary_device"
            ),
            "operation_family": "create",
            "provider_operation_type": "meta_ocg.relationship.create",
            "semantic_key": "meta.relationship:Room.primary_device",
            "semantic_subject_type": "aware_meta.ClassConfigRelationship",
            "ontology_subject_kind": "relationship",
            "source_refs": ("home/model.aware",),
            "baseline": {},
            "current": {
                "relationship_key": "primary_device",
                "source_class_fqn": "home.Room",
                "target_class_fqn": "home.Device",
                "relationship_type": "many_to_one",
                "forward_loading_strategy": "eager",
                "relationship_signature": current_signature,
            },
        }
    )
    assert operation is not None
    return operation


def _relationship_delete_typed_operation() -> MetaProviderDeltaTypedOperation:
    baseline_signature = {
        "source_class_fqn": "home.Room",
        "target_class_fqn": "home.Device",
        "relationship_key": "primary_device",
        "relationship_type": "many_to_one",
        "forward_loading_strategy": "eager",
    }
    operation = MetaProviderDeltaTypedOperation.from_payload(
        {
            "operation_kind": "meta_ocg_provider_delta_typed_operation",
            "operation_key": (
                "meta_ocg.relationship.delete:"
                "meta.relationship:Room.primary_device"
            ),
            "operation_family": "delete",
            "provider_operation_type": "meta_ocg.relationship.delete",
            "semantic_key": "meta.relationship:Room.primary_device",
            "semantic_subject_type": "aware_meta.ClassConfigRelationship",
            "ontology_subject_kind": "relationship",
            "source_refs": ("home/model.aware",),
            "baseline": {
                "object": {
                    "relationship_key": "primary_device",
                    "relationship_signature": baseline_signature,
                },
            },
            "current": {
                "relationship_key": "primary_device",
                "source_class_fqn": "home.Room",
                "target_class_fqn": "home.Device",
                "relationship_type": "many_to_one",
                "relationship_signature": baseline_signature,
            },
        }
    )
    assert operation is not None
    return operation


def _digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()
