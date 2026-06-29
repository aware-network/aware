from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace
from typing import Any, cast

import pytest

from aware_code_service import build_aware_code_service_protocol_handler
from aware_meta.attribute.config.deltas.generated_materialization import (
    META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_ANCHOR_KEY,
    META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_RENDERER_KEY,
    META_PYTHON_ORM_ATTRIBUTE_FIELD_ANCHOR_KEY,
    META_PYTHON_ORM_ATTRIBUTE_FIELD_EVIDENCE_ONLY_DIAGNOSTIC,
    META_PYTHON_ORM_ATTRIBUTE_FIELD_RENDERER_KEY,
    META_PYTHON_ORM_ATTRIBUTE_FIELD_SPAN_MISSING_DIAGNOSTIC,
    META_PYTHON_ORM_ATTRIBUTE_TYPE_ANCHOR_KEY,
    META_PYTHON_ORM_ATTRIBUTE_TYPE_BASELINE_HASH_MISSING_DIAGNOSTIC,
    META_PYTHON_ORM_ATTRIBUTE_TYPE_EVIDENCE_ONLY_DIAGNOSTIC,
    META_PYTHON_ORM_ATTRIBUTE_TYPE_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC,
    META_PYTHON_ORM_ATTRIBUTE_TYPE_UNSUPPORTED_REASON,
    MetaPythonOrmGeneratedMaterializationContext,
    python_orm_generated_materialization_delta_from_attribute_config_typed_operation,
)
from aware_meta.class_.config.deltas.generated_materialization import (
    META_PYTHON_ORM_CLASS_CLASS_ANCHOR_KEY,
    META_PYTHON_ORM_CLASS_DESCRIPTION_ANCHOR_KEY,
    META_PYTHON_ORM_CLASS_RENDERER_KEY,
    MetaPythonOrmClassGeneratedMaterializationContext,
    python_orm_generated_materialization_delta_from_class_config_typed_operation,
)
from aware_meta.function.config.deltas.generated_materialization import (
    META_PYTHON_ORM_FUNCTION_ANCHOR_KEY,
    META_PYTHON_ORM_FUNCTION_EVIDENCE_ONLY_DIAGNOSTIC,
    META_PYTHON_ORM_FUNCTION_INVOCATION_ANCHOR_KEY,
    META_PYTHON_ORM_FUNCTION_INVOCATION_BASELINE_BODY_MISSING_DIAGNOSTIC,
    META_PYTHON_ORM_FUNCTION_INVOCATION_BODY_MISSING_DIAGNOSTIC,
    META_PYTHON_ORM_FUNCTION_INVOCATION_RENDERER_KEY,
    META_PYTHON_ORM_FUNCTION_RENDERER_KEY,
    META_PYTHON_ORM_FUNCTION_SIGNATURE_INPUT_MODEL_SPAN_MISSING_DIAGNOSTIC,
    META_PYTHON_ORM_FUNCTION_SIGNATURE_PAYLOAD_SPAN_MISSING_DIAGNOSTIC,
    META_PYTHON_ORM_FUNCTION_SIGNATURE_SPAN_MISSING_DIAGNOSTIC,
    MetaPythonOrmFunctionGeneratedMaterializationContext,
    generated_materialization_feature_results_from_function_config_typed_operation,
    python_orm_generated_materialization_delta_from_function_config_typed_operation,
)
from aware_meta.function.config.deltas.typed_operations import (
    function_config_create_typed_operation,
    function_config_delete_typed_operation,
    function_invocation_create_typed_operation,
)
from aware_meta.enum.config.deltas.generated_materialization import (
    META_PYTHON_ORM_ENUM_CLASS_ANCHOR_KEY,
    MetaPythonOrmEnumGeneratedMaterializationContext,
    python_orm_generated_materialization_delta_from_enum_config_typed_operation,
)
from aware_meta.materialization.deltas.code_dto import (
    CodeGrammarAnchorRenderTargetKind,
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedMaterializationDeltaRequest,
    CodeGeneratedMaterializationDeltaResult,
    CodeGeneratedRendererDeltaOperationKind,
    FingerprintCodeGeneratedMaterializationDeltaRequest,
    ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    ValidateCodeGeneratedMaterializationDeltaRequest,
)
from aware_meta.materialization.deltas.generated_materialization import (
    provider_delta_generated_materialization_stage,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaGeneratedMaterializationContext,
)
from aware_meta.materialization.deltas.result import _provider_delta_result
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


def test_meta_python_orm_attribute_type_delta_emits_renderer_operation_evidence() -> (
    None
):
    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        _typed_operation(_attribute_type_operation()),
        context=MetaPythonOrmGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root="modules/home/structure/ontology/python",
            sources_root="aware_home_ontology",
            relative_path_by_owner_key={
                "aware_demo.default.home.TvChannel": (
                    "aware_home_ontology/home/tv_channel.py"
                )
            },
        ),
    )

    assert evidence.delta_request.provider_key == "aware_meta"
    assert len(evidence.delta_request.events) == 1
    assert len(evidence.delta_request.action_bindings) == 1
    assert len(evidence.delta_request.targets) == 1
    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.section_delta_ready
    )
    assert len(evidence.result.entries) == 1
    entry = evidence.result.entries[0]
    assert entry.mode is CodeGeneratedMaterializationDeltaMode.section_delta_ready
    assert entry.package_delta is None
    assert entry.section_delta is not None
    assert len(entry.section_delta.entries) == 1
    section_entry = entry.section_delta.entries[0]
    assert section_entry.operation.value == "replace_segment"
    assert section_entry.section_ref.relative_path == "home/tv_channel.py"
    assert section_entry.section_ref.language == "python"
    assert section_entry.section_ref.section_type == "attribute"
    assert section_entry.section_ref.qualname == "TvChannel.selected_channel"
    assert section_entry.segment_ref is not None
    assert section_entry.segment_ref.segment_name == "type"
    assert section_entry.segment_ref.before_segment_hash == _digest("int | None")
    assert section_entry.content_text == "str | None"
    assert section_entry.after_hash == _digest("str | None")
    assert len(entry.renderer_operations) == 1
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == "python.orm.attribute.type"
    assert operation.renderer_profile == "orm_runtime"
    assert operation.content_text == "str | None"
    assert operation.replacement_text == "str | None"
    assert operation.before_hash == _digest("int | None")
    assert operation.after_hash == _digest("str | None")
    assert operation.semantic_keys == [
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
        "/attribute:selected_channel"
    ]
    assert operation.event_refs == [
        "aware_meta.provider_delta.world_change.attribute.update"
    ]
    assert operation.diagnostics == []
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_ATTRIBUTE_TYPE_ANCHOR_KEY
    assert operation.anchor.anchor_path == "TvChannel.selected_channel.type"
    assert operation.anchor.anchor_role == "type_annotation"
    assert operation.anchor.section_type == "attribute"
    assert operation.anchor.segment_name == "type"
    graph_selector = cast(dict[str, object], operation.anchor.graph_selector)
    assert graph_selector["class_name"] == "TvChannel"
    assert graph_selector["attribute_name"] == "selected_channel"
    assert operation.target is not None
    assert operation.target.relative_path == "aware_home_ontology/home/tv_channel.py"
    assert operation.target.materialization_source == "ontology_orm_models"


def test_meta_python_orm_attribute_default_value_delta_emits_renderer_operation_evidence() -> (
    None
):
    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        _typed_operation(_attribute_default_value_operation()),
        context=MetaPythonOrmGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root="modules/home/structure/ontology/python",
            sources_root="aware_home_ontology",
            relative_path_by_owner_key={
                "aware_demo.default.home.TvChannel": (
                    "aware_home_ontology/home/tv_channel.py"
                )
            },
        ),
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.section_delta_ready
    )
    assert len(evidence.result.entries) == 1
    entry = evidence.result.entries[0]
    assert entry.section_delta is not None
    assert len(entry.section_delta.entries) == 1
    section_entry = entry.section_delta.entries[0]
    assert section_entry.operation.value == "replace_segment"
    assert section_entry.section_ref.relative_path == "home/tv_channel.py"
    assert section_entry.section_ref.qualname == "TvChannel.selected_channel"
    assert section_entry.segment_ref is not None
    assert section_entry.segment_ref.segment_name == "default_value"
    assert section_entry.segment_ref.before_segment_hash == _digest("7")
    assert section_entry.content_text == "11"
    assert section_entry.after_hash == _digest("11")
    assert len(entry.renderer_operations) == 1
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert (
        operation.renderer_key == META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_RENDERER_KEY
    )
    assert operation.content_text == "11"
    assert operation.replacement_text == "11"
    assert operation.before_hash == _digest("7")
    assert operation.after_hash == _digest("11")
    assert operation.diagnostics == []
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == (
        META_PYTHON_ORM_ATTRIBUTE_DEFAULT_VALUE_ANCHOR_KEY
    )
    assert operation.anchor.anchor_path == "TvChannel.selected_channel.default_value"
    assert operation.anchor.anchor_role == "default_value"
    assert operation.anchor.segment_name == "default_value"


@pytest.mark.asyncio
async def test_meta_python_orm_attribute_create_resolves_guarded_field_insert(
    tmp_path,
) -> None:
    generated_source_root = tmp_path / "aware_content_ontology" / "content"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "content_layout.py"
    generated_source_path.write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class ContentLayout(ORMModel):\n"
        "    name: str\n",
        encoding="utf-8",
    )
    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        _typed_operation(_content_layout_attribute_create_operation()),
        context=MetaPythonOrmGeneratedMaterializationContext(
            package_name="content-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_content_ontology",
        ),
    )

    assert evidence.result.mode is (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert evidence.result.diagnostics == []
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == "    title: str\n"
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest("")
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == META_PYTHON_ORM_ATTRIBUTE_FIELD_RENDERER_KEY
    assert operation.content_text == "    title: str\n"
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_ATTRIBUTE_FIELD_ANCHOR_KEY
    assert operation.anchor.anchor_role == "attribute_field"
    assert operation.anchor.segment_name == "field"

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.package_delta is not None
    assert resolved.path_count == 1
    assert resolved.package_delta.paths[0].relative_path == (
        "content/content_layout.py"
    )
    content_text = resolved.package_delta.paths[0].content_text or ""
    assert "class ContentLayout(ORMModel):" in content_text
    assert "    name: str\n" in content_text
    assert "    title: str\n" in content_text
    assert resolved.package_delta_entry_count == 0
    assert resolved.grammar_anchor_render_entry_count == 1
    assert resolved.section_delta_entry_count == 0


@pytest.mark.asyncio
async def test_meta_python_orm_attribute_create_normalizes_workspace_relative_generated_path(
    tmp_path,
) -> None:
    package_root = (
        tmp_path / "modules" / "content" / "structure" / "ontology" / "python"
    )
    generated_source_root = package_root / "aware_content_ontology" / "content"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "content_layout.py"
    generated_source_path.write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class ContentLayout(ORMModel):\n"
        "    name: str\n",
        encoding="utf-8",
    )
    payload = _content_layout_attribute_create_operation()
    current = dict(cast(dict[str, object], payload["current"]))
    generated_materialization = dict(
        cast(dict[str, object], current["generated_materialization"])
    )
    python_orm = dict(cast(dict[str, object], generated_materialization["python_orm"]))
    python_orm["relative_path"] = "content/content_layout.py"
    generated_materialization["python_orm"] = python_orm
    current["generated_materialization"] = generated_materialization
    payload["current"] = current

    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        _typed_operation(payload),
        context=MetaPythonOrmGeneratedMaterializationContext(
            package_name="content-ontology",
            package_root=package_root.as_posix(),
            sources_root="aware_content_ontology",
        ),
    )

    assert evidence.result.mode is (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = evidence.result.entries[0]
    assert entry.relative_path == "aware_content_ontology/content/content_layout.py"
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.span_target is not None
    assert replacement.span_target.relative_path == "content/content_layout.py"


@pytest.mark.asyncio
async def test_meta_python_orm_attribute_delete_resolves_guarded_field_removal(
    tmp_path,
) -> None:
    generated_source_root = tmp_path / "aware_content_ontology" / "content"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "content_layout.py"
    generated_source_path.write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class ContentLayout(ORMModel):\n"
        "    name: str\n"
        "    title: str\n",
        encoding="utf-8",
    )
    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        _typed_operation(_content_layout_attribute_delete_operation()),
        context=MetaPythonOrmGeneratedMaterializationContext(
            package_name="content-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_content_ontology",
        ),
    )

    assert evidence.result.mode is (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.replacement_text == ""
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest("    title: str\n")
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.content_text == ""
    assert operation.replacement_text == ""
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_ATTRIBUTE_FIELD_ANCHOR_KEY

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.package_delta is not None
    assert resolved.path_count == 1
    assert resolved.package_delta.paths[0].relative_path == (
        "content/content_layout.py"
    )
    content_text = resolved.package_delta.paths[0].content_text or ""
    assert "class ContentLayout(ORMModel):" in content_text
    assert "    name: str\n" in content_text
    assert "    title: str\n" not in content_text
    assert resolved.package_delta_entry_count == 0
    assert resolved.grammar_anchor_render_entry_count == 1
    assert resolved.section_delta_entry_count == 0


def test_meta_python_orm_attribute_create_missing_span_fails_closed(
    tmp_path,
) -> None:
    generated_source_root = tmp_path / "aware_content_ontology" / "content"
    generated_source_root.mkdir(parents=True)
    (generated_source_root / "content_layout.py").write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class OtherLayout(ORMModel):\n"
        "    name: str\n",
        encoding="utf-8",
    )
    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        _typed_operation(_content_layout_attribute_create_operation()),
        context=MetaPythonOrmGeneratedMaterializationContext(
            package_name="content-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_content_ontology",
        ),
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.fallback_full_render
    )
    assert evidence.result.diagnostics == [
        META_PYTHON_ORM_ATTRIBUTE_FIELD_EVIDENCE_ONLY_DIAGNOSTIC,
        META_PYTHON_ORM_ATTRIBUTE_FIELD_SPAN_MISSING_DIAGNOSTIC,
    ]
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is None
    operation = entry.renderer_operations[0]
    assert (
        operation.kind is CodeGeneratedRendererDeltaOperationKind.fallback_full_render
    )
    assert operation.renderer_key == META_PYTHON_ORM_ATTRIBUTE_FIELD_RENDERER_KEY


def test_meta_python_orm_attribute_type_delta_renders_single_collection_kind_as_scalar() -> (
    None
):
    payload = _attribute_type_operation()
    baseline = dict(cast(dict[str, object], payload["baseline"]))
    baseline_object = dict(cast(dict[str, object], baseline["object"]))
    baseline_signature = dict(
        cast(dict[str, object], baseline_object["attribute_signature"])
    )
    baseline_signature["collection_kind"] = "single"
    baseline_signature["is_required"] = True
    baseline_object["attribute_signature"] = baseline_signature
    baseline["object"] = baseline_object
    current = dict(cast(dict[str, object], payload["current"]))
    current_signature = dict(cast(dict[str, object], current["attribute_signature"]))
    current_signature["collection_kind"] = "single"
    current_signature["is_required"] = True
    current["attribute_signature"] = current_signature
    payload["baseline"] = baseline
    payload["current"] = current

    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        _typed_operation(payload),
        context=MetaPythonOrmGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root="modules/home/structure/ontology/python",
            sources_root="aware_home_ontology",
            relative_path_by_owner_key={
                "aware_demo.default.home.TvChannel": (
                    "aware_home_ontology/home/tv_channel.py"
                )
            },
        ),
    )
    entry = evidence.result.entries[0]
    operation = entry.renderer_operations[0]

    assert operation.content_text == "str"
    assert operation.before_hash == _digest("int")
    assert entry.section_delta is not None
    assert entry.section_delta.entries[0].content_text == "str"


def test_meta_python_orm_function_create_delta_emits_renderer_operation_evidence() -> (
    None
):
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _function_create_typed_operation(),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root="modules/home/structure/ontology/python",
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert evidence.delta_request.provider_key == "aware_meta"
    assert len(evidence.delta_request.events) == 1
    assert len(evidence.delta_request.action_bindings) == 1
    assert len(evidence.delta_request.targets) == 1
    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.section_delta_ready
    )
    assert evidence.result.diagnostics == []
    assert len(evidence.result.entries) == 1
    entry = evidence.result.entries[0]
    assert entry.mode is CodeGeneratedMaterializationDeltaMode.section_delta_ready
    assert entry.package_delta is None
    assert entry.section_delta is not None
    assert len(entry.section_delta.entries) == 1
    section_entry = entry.section_delta.entries[0]
    assert section_entry.operation.value == "insert_after_section"
    assert section_entry.section_ref.relative_path == "home/tv_channel.py"
    assert section_entry.section_ref.language == "python"
    assert section_entry.section_ref.section_type == "class"
    assert section_entry.section_ref.qualname == "TvChannel"
    assert section_entry.nested_member_insert_anchor is not None
    assert section_entry.nested_member_insert_anchor.member_section_type == ("function")
    assert section_entry.nested_member_insert_anchor.member_qualname == (
        "TvChannel.rename"
    )
    assert section_entry.content_text == (
        "\n    def rename(self) -> None:\n"
        '        """Rename the channel."""\n'
        "        raise NotImplementedError\n"
    )
    assert entry.target.relative_path == ("aware_home_ontology/home/tv_channel.py")
    assert len(entry.renderer_operations) == 1
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.insert_section
    assert operation.renderer_key == META_PYTHON_ORM_FUNCTION_RENDERER_KEY
    assert operation.renderer_profile == "orm_runtime"
    assert operation.content_text == section_entry.content_text
    assert operation.replacement_text == section_entry.content_text
    assert operation.after_hash == section_entry.after_hash
    assert operation.diagnostics == []
    assert operation.event_refs == [
        "aware_meta.provider_delta.world_change.function.create"
    ]
    assert operation.semantic_keys == [
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel/function:rename"
    ]
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_FUNCTION_ANCHOR_KEY
    assert operation.anchor.anchor_role == "function_section"
    assert operation.anchor.anchor_path == "TvChannel.rename"
    graph_selector = cast(dict[str, object], operation.anchor.graph_selector)
    assert graph_selector["class_name"] == "TvChannel"
    assert graph_selector["function_name"] == "rename"


def test_meta_python_orm_function_invocation_delta_emits_renderer_operation_evidence() -> (
    None
):
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _function_invocation_typed_operation(),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root="modules/home/structure/ontology/python",
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.section_delta_ready
    )
    assert evidence.result.diagnostics == []
    entry = evidence.result.entries[0]
    assert entry.mode is CodeGeneratedMaterializationDeltaMode.section_delta_ready
    assert entry.section_delta is not None
    assert len(entry.section_delta.entries) == 1
    section_entry = entry.section_delta.entries[0]
    assert section_entry.operation.value == "replace_segment"
    assert section_entry.section_ref.relative_path == "home/tv_channel.py"
    assert section_entry.section_ref.language == "python"
    assert section_entry.section_ref.section_type == "function"
    assert section_entry.section_ref.qualname == "TvChannel.rename"
    assert section_entry.segment_ref is not None
    assert section_entry.segment_ref.segment_name == "body"
    assert section_entry.segment_ref.before_segment_hash == _digest(
        _PYTHON_ORM_RENAME_BASELINE_BODY_TEXT
    )
    assert section_entry.content_text == _PYTHON_ORM_RENAME_INVOCATION_BODY_TEXT
    assert section_entry.after_hash == _digest(_PYTHON_ORM_RENAME_INVOCATION_BODY_TEXT)
    operation = entry.renderer_operations[0]

    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == META_PYTHON_ORM_FUNCTION_INVOCATION_RENDERER_KEY
    assert operation.before_hash == _digest(_PYTHON_ORM_RENAME_BASELINE_BODY_TEXT)
    assert operation.after_hash == _digest(_PYTHON_ORM_RENAME_INVOCATION_BODY_TEXT)
    assert operation.content_text == _PYTHON_ORM_RENAME_INVOCATION_BODY_TEXT
    assert operation.replacement_text == _PYTHON_ORM_RENAME_INVOCATION_BODY_TEXT
    assert operation.diagnostics == []
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_FUNCTION_INVOCATION_ANCHOR_KEY
    assert operation.anchor.anchor_role == "function_invocation_plan"
    assert operation.anchor.anchor_path == "TvChannel.rename.invocation[0]"
    assert operation.anchor.segment_name == "body"
    graph_selector = cast(dict[str, object], operation.anchor.graph_selector)
    assert graph_selector["function_semantic_key"] == (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel/function:rename"
    )
    assert graph_selector["invocation_position"] == 0


def test_meta_python_orm_function_invocation_delta_falls_back_without_body_evidence() -> (
    None
):
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _function_invocation_typed_operation(include_body_evidence=False),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root="modules/home/structure/ontology/python",
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.fallback_full_render
    )
    assert evidence.result.diagnostics == [
        META_PYTHON_ORM_FUNCTION_EVIDENCE_ONLY_DIAGNOSTIC,
        META_PYTHON_ORM_FUNCTION_INVOCATION_BASELINE_BODY_MISSING_DIAGNOSTIC,
        META_PYTHON_ORM_FUNCTION_INVOCATION_BODY_MISSING_DIAGNOSTIC,
    ]
    entry = evidence.result.entries[0]
    operation = entry.renderer_operations[0]

    assert (
        operation.kind is CodeGeneratedRendererDeltaOperationKind.fallback_full_render
    )
    assert operation.renderer_key == META_PYTHON_ORM_FUNCTION_INVOCATION_RENDERER_KEY
    assert operation.anchor is not None
    assert operation.anchor.segment_name == "body"
    assert operation.diagnostics == [
        META_PYTHON_ORM_FUNCTION_EVIDENCE_ONLY_DIAGNOSTIC,
        META_PYTHON_ORM_FUNCTION_INVOCATION_BASELINE_BODY_MISSING_DIAGNOSTIC,
        META_PYTHON_ORM_FUNCTION_INVOCATION_BODY_MISSING_DIAGNOSTIC,
    ]


def test_meta_python_orm_function_update_description_delta_emits_body_segment_evidence() -> (
    None
):
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _function_update_description_typed_operation(),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root="modules/home/structure/ontology/python",
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.section_delta_ready
    )
    assert evidence.result.diagnostics == []
    entry = evidence.result.entries[0]
    assert entry.mode is CodeGeneratedMaterializationDeltaMode.section_delta_ready
    assert entry.section_delta is not None
    assert len(entry.section_delta.entries) == 1
    section_entry = entry.section_delta.entries[0]
    assert section_entry.operation.value == "replace_segment"
    assert section_entry.section_ref.relative_path == "home/tv_channel.py"
    assert section_entry.section_ref.language == "python"
    assert section_entry.section_ref.section_type == "function"
    assert section_entry.section_ref.qualname == "TvChannel.rename"
    assert section_entry.segment_ref is not None
    assert section_entry.segment_ref.segment_name == "body"
    assert section_entry.segment_ref.before_segment_hash == _digest(
        _PYTHON_ORM_RENAME_BASELINE_BODY_TEXT
    )
    assert section_entry.content_text == _PYTHON_ORM_RENAME_UPDATED_BODY_TEXT
    assert section_entry.after_hash == _digest(_PYTHON_ORM_RENAME_UPDATED_BODY_TEXT)
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == META_PYTHON_ORM_FUNCTION_RENDERER_KEY
    assert operation.before_hash == _digest(_PYTHON_ORM_RENAME_BASELINE_BODY_TEXT)
    assert operation.after_hash == _digest(_PYTHON_ORM_RENAME_UPDATED_BODY_TEXT)
    assert operation.content_text == _PYTHON_ORM_RENAME_UPDATED_BODY_TEXT
    assert operation.replacement_text == _PYTHON_ORM_RENAME_UPDATED_BODY_TEXT
    assert operation.diagnostics == []
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_FUNCTION_ANCHOR_KEY
    assert operation.anchor.anchor_role == "function_section"
    assert operation.anchor.anchor_path == "TvChannel.rename"
    assert operation.anchor.segment_name == "function"


def test_meta_python_orm_function_update_signature_delta_falls_back_without_span() -> (
    None
):
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _function_update_signature_typed_operation(),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root="modules/home/structure/ontology/python",
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.fallback_full_render
    )
    assert evidence.result.diagnostics == [
        META_PYTHON_ORM_FUNCTION_EVIDENCE_ONLY_DIAGNOSTIC,
        META_PYTHON_ORM_FUNCTION_SIGNATURE_SPAN_MISSING_DIAGNOSTIC,
    ]
    entry = evidence.result.entries[0]
    operation = entry.renderer_operations[0]
    assert (
        operation.kind is CodeGeneratedRendererDeltaOperationKind.fallback_full_render
    )
    assert operation.diagnostics == [
        META_PYTHON_ORM_FUNCTION_EVIDENCE_ONLY_DIAGNOSTIC,
        META_PYTHON_ORM_FUNCTION_SIGNATURE_SPAN_MISSING_DIAGNOSTIC,
    ]


@pytest.mark.asyncio
async def test_meta_python_orm_function_update_signature_delta_resolves_generated_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    def rename(self) -> None:\n"
        "        raise NotImplementedError\n",
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _function_update_signature_typed_operation(),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root=generated_package_root.as_posix(),
                sources_root="aware_home_ontology",
            ),
        )
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
    assert replacement.replacement_text == "async def rename(self) -> None:"
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest(
        "def rename(self) -> None:"
    )
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.content_text == "async def rename(self) -> None:"
    assert operation.before_hash == _digest("def rename(self) -> None:")
    assert operation.after_hash == _digest("async def rename(self) -> None:")

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
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    async def rename(self) -> None:\n"
        "        raise NotImplementedError\n"
    )


@pytest.mark.asyncio
async def test_meta_python_orm_function_update_signature_delta_resolves_parameter_annotation_span(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    async def rename(self, display_name: str) -> TvChannel:\n"
        '        payload = {"display_name": display_name}\n'
        "        result = await invoke_instance(\n"
        '            orm_model=self, function_name="rename", payload=payload\n'
        "        )\n"
        "        return result\n"
        "\n"
        "\n"
        "class TvChannelRenameInput(BaseModel):\n"
        "    display_name: str\n",
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _function_update_input_signature_typed_operation(),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root=generated_package_root.as_posix(),
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert evidence.result.diagnostics == []
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.replacement_text == (
        "async def rename(self, label: str) -> TvChannel:"
    )
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest(
        "async def rename(self, display_name: str) -> TvChannel:"
    )

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
    assert resolved.package_delta.paths[0].relative_path == "home/tv_channel.py"
    assert resolved.package_delta.paths[0].content_text == (
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    async def rename(self, label: str) -> TvChannel:\n"
        '        payload = {"label": label}\n'
        "        result = await invoke_instance(\n"
        '            orm_model=self, function_name="rename", payload=payload\n'
        "        )\n"
        "        return result\n"
        "\n"
        "\n"
        "class TvChannelRenameInput(BaseModel):\n"
        "    label: str\n"
    )


def test_meta_python_orm_function_update_signature_delta_blocks_partial_generated_invocation_surface(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    async def rename(self, display_name: str) -> TvChannel:\n"
        "        raise NotImplementedError\n",
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _function_update_input_signature_typed_operation(),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root=generated_package_root.as_posix(),
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.fallback_full_render
    )
    assert evidence.result.diagnostics == [
        META_PYTHON_ORM_FUNCTION_EVIDENCE_ONLY_DIAGNOSTIC,
        META_PYTHON_ORM_FUNCTION_SIGNATURE_PAYLOAD_SPAN_MISSING_DIAGNOSTIC,
        META_PYTHON_ORM_FUNCTION_SIGNATURE_INPUT_MODEL_SPAN_MISSING_DIAGNOSTIC,
    ]
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is None
    operation = entry.renderer_operations[0]
    assert (
        operation.kind is CodeGeneratedRendererDeltaOperationKind.fallback_full_render
    )
    assert operation.diagnostics == [
        META_PYTHON_ORM_FUNCTION_EVIDENCE_ONLY_DIAGNOSTIC,
        META_PYTHON_ORM_FUNCTION_SIGNATURE_PAYLOAD_SPAN_MISSING_DIAGNOSTIC,
        META_PYTHON_ORM_FUNCTION_SIGNATURE_INPUT_MODEL_SPAN_MISSING_DIAGNOSTIC,
    ]


@pytest.mark.asyncio
async def test_meta_provider_delta_generated_materialization_stage_resolves_workspace_relative_python_root(
    tmp_path,
) -> None:
    workspace_root = tmp_path / "workspace"
    manifest_path = (
        workspace_root / "modules" / "home" / "ontology" / "structure" / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    generated_package_root = (
        workspace_root
        / "modules"
        / "home"
        / "ontology"
        / "structure"
        / "python"
        / "orm_runtime"
    )
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    async def rename(self, display_name: str) -> TvChannel:\n"
        '        payload = {"display_name": display_name}\n'
        "        result = await invoke_instance(\n"
        '            orm_model=self, function_name="rename", payload=payload\n'
        "        )\n"
        "        return result\n"
        "\n"
        "\n"
        "class TvChannelRenameInput(BaseModel):\n"
        "    display_name: str\n",
        encoding="utf-8",
    )
    stage = provider_delta_generated_materialization_stage(
        package_payload={
            "package_name": "home-ontology",
            "manifest_path": "modules/home/ontology/aware.ontology.toml",
        },
        manifest_path=manifest_path,
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=(
            _provider_delta_semantic_change_report()
        ),
        provider_delta_typed_operation_plan={
            **_typed_operation_plan(
                _function_update_input_signature_typed_operation().evidence_payload()
            ),
            "typed_operations": (
                _function_update_input_signature_typed_operation().evidence_payload(),
                _function_impl_update_operation(),
            ),
        },
        code_package_delta={
            "package_name": "home-ontology",
            "package_root": "modules/home/ontology",
            "sources_root": "modules/home/ontology/structure/aware",
        },
    )
    delta_requests = cast(tuple[dict[str, object], ...], stage["delta_requests"])
    results = cast(tuple[dict[str, object], ...], stage["results"])
    delta_request = CodeGeneratedMaterializationDeltaRequest.model_validate(
        delta_requests[0]
    )
    result = CodeGeneratedMaterializationDeltaResult.model_validate(results[0])

    assert stage["status"] == "generated_materialization_ready"
    assert stage["unsupported_generated_output_count"] == 1
    assert stage["blocking_unsupported_generated_output_count"] == 0
    assert result.diagnostics == []
    assert result.mode is (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert (
        delta_request.package_root
        == (
            workspace_root / "modules" / "home" / "ontology" / "structure" / "python"
        ).as_posix()
    )

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=delta_request,
            result=result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.package_delta is not None
    assert resolved.package_delta.package_root == generated_package_root.as_posix()
    assert resolved.package_delta.sources_root == "aware_home_ontology"
    assert resolved.package_delta.paths[0].relative_path == "home/tv_channel.py"
    assert "async def rename(self, label: str) -> TvChannel:" in (
        resolved.package_delta.paths[0].content_text or ""
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_generated_materialization_stage_coalesces_function_input_rename(
    tmp_path,
) -> None:
    workspace_root = tmp_path / "workspace"
    manifest_path = (
        workspace_root / "modules" / "home" / "ontology" / "structure" / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    generated_package_root = (
        workspace_root
        / "modules"
        / "home"
        / "ontology"
        / "structure"
        / "python"
        / "orm_runtime"
    )
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    async def rename(self, display_name: str) -> TvChannel:\n"
        '        payload = {"display_name": display_name}\n'
        "        result = await invoke_instance(\n"
        '            orm_model=self, function_name="rename", payload=payload\n'
        "        )\n"
        "        return result\n"
        "\n"
        "\n"
        "class TvChannelRenameInput(BaseModel):\n"
        "    display_name: str\n",
        encoding="utf-8",
    )
    function_operation = _function_update_input_signature_typed_operation()
    function_current = dict(function_operation.current)
    current_signature = dict(
        cast(dict[str, object], function_current["function_signature"])
    )
    current_signature.pop("inputs")
    current_signature.pop("outputs")
    function_current["function_signature"] = current_signature
    function_operation = replace(function_operation, current=function_current)

    stage = provider_delta_generated_materialization_stage(
        package_payload={
            "package_name": "home-ontology",
            "manifest_path": "modules/home/ontology/aware.ontology.toml",
        },
        manifest_path=manifest_path,
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=(
            _provider_delta_semantic_change_report()
        ),
        provider_delta_typed_operation_plan={
            **_typed_operation_plan(function_operation.evidence_payload()),
            "typed_operations": (
                _function_input_delete_operation().evidence_payload(),
                function_operation.evidence_payload(),
                _function_input_create_operation().evidence_payload(),
                _function_impl_update_operation(),
            ),
        },
        code_package_delta={
            "package_name": "home-ontology",
            "package_root": "modules/home/ontology",
            "sources_root": "modules/home/ontology/structure/aware",
        },
    )
    results = cast(tuple[dict[str, object], ...], stage["results"])
    function_results = tuple(
        result
        for result in results
        if result.get("mode") == "grammar_anchor_render_ready"
    )

    assert stage["status"] == "generated_materialization_ready"
    assert stage["unsupported_generated_output_count"] == 1
    assert stage["blocking_unsupported_generated_output_count"] == 0
    assert function_results
    result = CodeGeneratedMaterializationDeltaResult.model_validate(function_results[0])
    assert result.diagnostics == []
    assert result.mode is (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )

    delta_requests = cast(tuple[dict[str, object], ...], stage["delta_requests"])
    target_key = result.entries[0].target.target_key
    function_request = next(
        request
        for request in delta_requests
        if any(
            target.get("target_key") == target_key
            for target in cast(list[dict[str, object]], request.get("targets"))
        )
    )
    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=CodeGeneratedMaterializationDeltaRequest.model_validate(
                function_request
            ),
            result=result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.package_delta is not None
    assert resolved.package_delta.package_root == generated_package_root.as_posix()
    assert resolved.package_delta.paths[0].relative_path == "home/tv_channel.py"
    generated_text = resolved.package_delta.paths[0].content_text or ""
    assert "async def rename(self, label: str) -> TvChannel:" in generated_text
    assert 'payload = {"label": label}' in generated_text
    assert "class TvChannelRenameInput(BaseModel):\n    label: str\n" in (
        generated_text
    )
    assert "display_name" not in generated_text


@pytest.mark.asyncio
async def test_meta_python_orm_class_description_delta_resolves_generated_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n" "    selected_channel: int | None\n",
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_class_config_typed_operation(
            _typed_operation(_class_update_operation()),
            context=MetaPythonOrmClassGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root=generated_package_root.as_posix(),
                sources_root="aware_home_ontology",
            ),
        )
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
    assert replacement.replacement_text == '    """TV channel config."""\n'
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest("")
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == META_PYTHON_ORM_CLASS_RENDERER_KEY
    assert operation.content_text == '    """TV channel config."""\n'
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_CLASS_DESCRIPTION_ANCHOR_KEY
    assert operation.anchor.anchor_role == "class_description"
    assert operation.anchor.segment_name == "description_comment"

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
        "class TvChannel:\n"
        '    """TV channel config."""\n'
        "    selected_channel: int | None\n"
    )


@pytest.mark.asyncio
async def test_meta_python_orm_class_create_delta_resolves_generated_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class TvChannel(ORMModel):\n"
        "    name: str\n",
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_class_config_typed_operation(
            _typed_operation(_class_create_operation()),
            context=MetaPythonOrmClassGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root=generated_package_root.as_posix(),
                sources_root="aware_home_ontology",
            ),
        )
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
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == (
        "\n\nclass RemoteControl(ORMModel):\n" '    """Remote control config."""\n'
    )
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest("")
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == META_PYTHON_ORM_CLASS_RENDERER_KEY
    assert operation.content_text == (
        "\n\nclass RemoteControl(ORMModel):\n" '    """Remote control config."""\n'
    )
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_CLASS_CLASS_ANCHOR_KEY
    assert operation.anchor.anchor_role == "class"
    assert operation.anchor.segment_name == "class"

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
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class TvChannel(ORMModel):\n"
        "    name: str\n"
        "\n\n"
        "class RemoteControl(ORMModel):\n"
        '    """Remote control config."""\n'
    )


@pytest.mark.asyncio
async def test_meta_python_orm_class_create_delta_resolves_from_authored_source_context(
    tmp_path,
) -> None:
    package_root = tmp_path / "modules" / "content" / "structure" / "ontology"
    authored_sources_root = package_root / "aware"
    generated_source_root = (
        package_root / "python" / "orm_runtime" / "aware_content_ontology" / "content"
    )
    authored_sources_root.mkdir(parents=True)
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "content_layout.py"
    generated_source_path.write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class ContentLayout(ORMModel):\n"
        "    name: str\n",
        encoding="utf-8",
    )

    stage = provider_delta_generated_materialization_stage(
        package_payload={"package_name": "content-ontology"},
        manifest_path=package_root / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=(
            _provider_delta_semantic_change_report()
        ),
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _content_placement_class_create_operation()
        ),
        code_package_delta=SimpleNamespace(
            package_name="content-ontology",
            package_root=package_root.as_posix(),
            sources_root=authored_sources_root.as_posix(),
        ),
    )

    assert stage["status"] == "generated_materialization_ready"
    results = cast(tuple[dict[str, object], ...], stage["results"])
    assert results[0]["mode"] == "grammar_anchor_render_ready"
    entries = cast(list[dict[str, object]], results[0]["entries"])
    assert entries[0]["relative_path"] == (
        "aware_content_ontology/content/content_layout.py"
    )
    request_payload = cast(tuple[dict[str, object], ...], stage["delta_requests"])[0]

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=CodeGeneratedMaterializationDeltaRequest.model_validate(
                request_payload
            ),
            result=CodeGeneratedMaterializationDeltaResult.model_validate(results[0]),
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.grammar_anchor_render_entry_count == 1
    assert resolved.package_delta is not None
    assert resolved.package_delta.package_root == (
        package_root / "python" / "orm_runtime"
    ).as_posix()
    assert resolved.package_delta.sources_root == "aware_content_ontology"
    assert resolved.package_delta.paths[0].relative_path == "content/content_layout.py"
    assert "class ContentPlacement(ORMModel):" in (
        resolved.package_delta.paths[0].content_text or ""
    )


@pytest.mark.asyncio
async def test_meta_python_orm_class_delete_delta_resolves_guarded_class_removal(
    tmp_path,
) -> None:
    generated_source_root = tmp_path / "aware_content_ontology" / "content"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "content_layout.py"
    generated_source_path.write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class ContentLayout(ORMModel):\n"
        "    name: str\n"
        "\n\n"
        "class ContentPlacement(ORMModel):\n"
        '    """Content placement config."""\n',
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_class_config_typed_operation(
            _typed_operation(_content_placement_class_delete_operation()),
            context=MetaPythonOrmClassGeneratedMaterializationContext(
                package_name="content-ontology",
                package_root=tmp_path.as_posix(),
                sources_root="aware_content_ontology",
            ),
        )
    )

    assert evidence.result.mode is (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert len(evidence.result.entries) == 1
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.content_text == ""
    assert operation.replacement_text == ""
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_CLASS_CLASS_ANCHOR_KEY
    assert operation.anchor.anchor_role == "class"

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.package_delta is not None
    assert resolved.path_count == 1
    assert resolved.package_delta.paths[0].relative_path == "content/content_layout.py"
    content_text = resolved.package_delta.paths[0].content_text or ""
    assert "class ContentLayout(ORMModel):" in content_text
    assert "class ContentPlacement(ORMModel):" not in content_text
    assert resolved.package_delta_entry_count == 0
    assert resolved.grammar_anchor_render_entry_count == 1
    assert resolved.section_delta_entry_count == 0


def test_meta_python_orm_function_membership_generated_materialization_not_required() -> (
    None
):
    operation = _function_membership_operation()
    feature_results = (
        generated_materialization_feature_results_from_function_config_typed_operation(
            operation,
            context=MetaProviderDeltaGeneratedMaterializationContext(
                package_name="home-ontology",
                package_root="modules/home/structure/ontology",
                sources_root="aware",
            ),
        )
    )

    assert len(feature_results) == 1
    result = feature_results[0]
    assert result.status == "generated_materialization_skipped"
    assert result.result is not None
    assert result.result.mode is CodeGeneratedMaterializationDeltaMode.not_required


def test_meta_provider_delta_generated_materialization_stage_exposes_evidence(
    tmp_path,
) -> None:
    stage = _ready_generated_materialization_stage(tmp_path)

    assert stage["status"] == "generated_materialization_ready"
    assert stage["ready"] is True
    assert stage["projected"] is True
    assert stage["typed_operation_count"] == 1
    assert stage["feature_result_count"] == 1
    assert stage["target_count"] == 1
    assert stage["entry_count"] == 1
    assert stage["renderer_operation_count"] == 1
    assert stage["skipped_target_count"] == 0
    assert stage["generated_materialization_expectation_count"] == 1
    assert stage["expected_generated_output_count"] == 1
    assert stage["fulfilled_generated_output_count"] == 1
    assert stage["missing_generated_output_count"] == 0
    assert stage["unsupported_generated_output_count"] == 0
    assert stage["deferred_generated_output_count"] == 0
    assert stage["not_required_generated_output_count"] == 0
    assert stage["blocked_feature_result_count"] == 0
    assert stage["skipped_feature_result_count"] == 0
    assert stage["diagnostics"] == ()

    expectations = cast(tuple[dict[str, object], ...], stage["expectations"])
    delta_requests = cast(tuple[dict[str, object], ...], stage["delta_requests"])
    results = cast(tuple[dict[str, object], ...], stage["results"])
    assert len(expectations) == 1
    assert expectations[0]["expectation"] == "required"
    assert expectations[0]["fulfillment"] == "fulfilled"
    assert expectations[0]["required"] is True
    assert expectations[0]["fulfilled"] is True
    assert expectations[0]["semantic_key"] == (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
        "/attribute:selected_channel"
    )
    assert len(delta_requests) == 1
    assert len(results) == 1
    assert delta_requests[0]["provider_key"] == "aware_meta"
    assert results[0]["mode"] == "section_delta_ready"
    entries = cast(list[dict[str, object]], results[0]["entries"])
    assert entries[0]["mode"] == "section_delta_ready"
    assert "section_delta" in entries[0]
    renderer_operations = cast(
        list[dict[str, object]],
        entries[0]["renderer_operations"],
    )
    assert renderer_operations[0]["kind"] == "replace_anchor"
    assert renderer_operations[0]["renderer_key"] == "python.orm.attribute.type"


def test_meta_provider_delta_generated_materialization_stage_exposes_function_evidence(
    tmp_path,
) -> None:
    operation = _function_create_typed_operation()
    stage = provider_delta_generated_materialization_stage(
        package_payload={"package_name": "home-ontology"},
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=(
            _provider_delta_semantic_change_report()
        ),
        provider_delta_typed_operation_plan=_typed_operation_plan(
            operation.evidence_payload()
        ),
        code_package_delta=SimpleNamespace(
            package_name="home-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware",
        ),
    )

    assert stage["status"] == "generated_materialization_ready"
    assert stage["ready"] is True
    assert stage["projected"] is True
    assert stage["typed_operation_count"] == 1
    assert stage["feature_result_count"] == 1
    assert stage["renderer_operation_count"] == 1
    assert stage["entry_count"] == 1
    assert stage["generated_materialization_expectation_count"] == 1
    assert stage["expected_generated_output_count"] == 1
    assert stage["fulfilled_generated_output_count"] == 1
    assert stage["missing_generated_output_count"] == 0
    assert stage["unsupported_generated_output_count"] == 0
    assert stage["deferred_generated_output_count"] == 0
    assert stage["not_required_generated_output_count"] == 0
    assert stage["diagnostics"] == ()
    expectations = cast(tuple[dict[str, object], ...], stage["expectations"])
    assert expectations[0]["expectation"] == "required"
    assert expectations[0]["fulfillment"] == "fulfilled"
    results = cast(tuple[dict[str, object], ...], stage["results"])
    assert results[0]["mode"] == "section_delta_ready"
    entries = cast(list[dict[str, object]], results[0]["entries"])
    assert "section_delta" in entries[0]
    renderer_operations = cast(
        list[dict[str, object]],
        entries[0]["renderer_operations"],
    )
    assert renderer_operations[0]["kind"] == "insert_section"
    assert renderer_operations[0]["renderer_key"] == (
        META_PYTHON_ORM_FUNCTION_RENDERER_KEY
    )


def test_meta_provider_delta_generated_materialization_stage_tracks_not_required(
    tmp_path,
) -> None:
    stage = provider_delta_generated_materialization_stage(
        package_payload={"package_name": "home-ontology"},
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=(
            _provider_delta_semantic_change_report()
        ),
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _function_membership_operation().evidence_payload()
        ),
        code_package_delta=SimpleNamespace(
            package_name="home-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    assert stage["status"] == "generated_materialization_not_required"
    assert stage["ready"] is False
    assert stage["projected"] is False
    assert stage["generated_materialization_expectation_count"] == 1
    assert stage["expected_generated_output_count"] == 0
    assert stage["fulfilled_generated_output_count"] == 0
    assert stage["missing_generated_output_count"] == 0
    assert stage["unsupported_generated_output_count"] == 0
    assert stage["deferred_generated_output_count"] == 0
    assert stage["not_required_generated_output_count"] == 1
    assert stage["diagnostics"] == ()

    expectations = cast(tuple[dict[str, object], ...], stage["expectations"])
    assert len(expectations) == 1
    assert expectations[0]["expectation"] == "not_required"
    assert expectations[0]["fulfillment"] == "not_applicable"
    assert expectations[0]["not_required"] is True


def test_meta_provider_delta_generated_materialization_stage_exposes_class_fallback_evidence(
    tmp_path,
) -> None:
    stage = provider_delta_generated_materialization_stage(
        package_payload={"package_name": "home-ontology"},
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=(
            _provider_delta_semantic_change_report()
        ),
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _class_update_operation()
        ),
        code_package_delta=SimpleNamespace(
            package_name="home-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    assert stage["status"] == "generated_materialization_ready"
    assert stage["reason"] == (
        "meta_generated_materialization_renderer_operation_evidence_ready"
    )
    assert stage["ready"] is True
    assert stage["projected"] is True
    assert stage["generated_materialization_expectation_count"] == 1
    assert stage["expected_generated_output_count"] == 1
    assert stage["fulfilled_generated_output_count"] == 1
    assert stage["missing_generated_output_count"] == 0
    assert stage["unsupported_generated_output_count"] == 0
    assert stage["deferred_generated_output_count"] == 0
    assert stage["not_required_generated_output_count"] == 0
    assert stage["diagnostics"] == (
        "meta_python_orm_class_generated_materialization_renderer_operation_evidence_only",
        "meta_python_orm_class_description_generated_materialization_span_missing",
    )

    expectations = cast(tuple[dict[str, object], ...], stage["expectations"])
    assert len(expectations) == 1
    assert expectations[0]["expectation"] == "required"
    assert expectations[0]["fulfillment"] == "fulfilled"
    assert expectations[0]["fulfilled"] is True
    results = cast(tuple[dict[str, object], ...], stage["results"])
    assert results[0]["mode"] == "fallback_full_render"
    entries = cast(list[dict[str, object]], results[0]["entries"])
    renderer_operations = cast(
        list[dict[str, object]],
        entries[0]["renderer_operations"],
    )
    assert renderer_operations[0]["kind"] == "fallback_full_render"
    assert renderer_operations[0]["renderer_key"] == META_PYTHON_ORM_CLASS_RENDERER_KEY


def test_meta_provider_delta_generated_materialization_stage_exposes_class_create_evidence(
    tmp_path,
) -> None:
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    (generated_source_root / "tv_channel.py").write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class TvChannel(ORMModel):\n"
        "    name: str\n",
        encoding="utf-8",
    )
    stage = provider_delta_generated_materialization_stage(
        package_payload={"package_name": "home-ontology"},
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=(
            _provider_delta_semantic_change_report()
        ),
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _class_create_operation()
        ),
        code_package_delta=SimpleNamespace(
            package_name="home-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    assert stage["status"] == "generated_materialization_ready"
    assert stage["reason"] == (
        "meta_generated_materialization_renderer_operation_evidence_ready"
    )
    assert stage["ready"] is True
    assert stage["projected"] is True
    assert stage["renderer_operation_count"] == 1
    assert stage["generated_materialization_expectation_count"] == 1
    assert stage["expected_generated_output_count"] == 1
    assert stage["fulfilled_generated_output_count"] == 1
    assert stage["missing_generated_output_count"] == 0
    assert stage["unsupported_generated_output_count"] == 0
    assert stage["not_required_generated_output_count"] == 0
    assert stage["diagnostics"] == ()
    results = cast(tuple[dict[str, object], ...], stage["results"])
    assert results[0]["mode"] == "grammar_anchor_render_ready"
    entries = cast(list[dict[str, object]], results[0]["entries"])
    renderer_operations = cast(
        list[dict[str, object]],
        entries[0]["renderer_operations"],
    )
    assert renderer_operations[0]["kind"] == "replace_anchor"
    assert renderer_operations[0]["renderer_key"] == META_PYTHON_ORM_CLASS_RENDERER_KEY


def test_meta_provider_delta_generated_materialization_stage_coalesces_class_create_description(
    tmp_path,
) -> None:
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    (generated_source_root / "tv_channel.py").write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class TvChannel(ORMModel):\n"
        "    name: str\n",
        encoding="utf-8",
    )
    create_operation = _class_create_operation()
    description_operation = _class_create_description_update_operation()

    stage = provider_delta_generated_materialization_stage(
        package_payload={"package_name": "home-ontology"},
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=(
            _provider_delta_semantic_change_report()
        ),
        provider_delta_typed_operation_plan={
            **_typed_operation_plan(create_operation),
            "typed_operations": (
                create_operation,
                description_operation,
            ),
        },
        code_package_delta=SimpleNamespace(
            package_name="home-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    assert stage["status"] == "generated_materialization_ready"
    assert stage["typed_operation_count"] == 1
    assert stage["feature_result_count"] == 1
    assert stage["renderer_operation_count"] == 1
    results = cast(tuple[dict[str, object], ...], stage["results"])
    entries = cast(list[dict[str, object]], results[0]["entries"])
    renderer_operations = cast(
        list[dict[str, object]],
        entries[0]["renderer_operations"],
    )
    assert renderer_operations[0]["kind"] == "replace_anchor"
    assert renderer_operations[0]["renderer_key"] == META_PYTHON_ORM_CLASS_RENDERER_KEY


def test_meta_provider_delta_generated_materialization_stage_tracks_mixed_ready_and_class_fallback(
    tmp_path,
) -> None:
    stage = provider_delta_generated_materialization_stage(
        package_payload={"package_name": "home-ontology"},
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=(
            _provider_delta_semantic_change_report()
        ),
        provider_delta_typed_operation_plan={
            **_typed_operation_plan(_attribute_type_operation()),
            "typed_operations": (
                _attribute_type_operation(),
                _class_update_operation(),
            ),
        },
        code_package_delta=SimpleNamespace(
            package_name="home-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    assert stage["status"] == "generated_materialization_ready"
    assert stage["reason"] == (
        "meta_generated_materialization_renderer_operation_evidence_ready"
    )
    assert stage["renderer_operation_count"] == 2
    assert stage["expected_generated_output_count"] == 2
    assert stage["fulfilled_generated_output_count"] == 2
    assert stage["unsupported_generated_output_count"] == 0
    assert stage["not_required_generated_output_count"] == 0
    assert stage["diagnostics"] == (
        "meta_python_orm_class_generated_materialization_renderer_operation_evidence_only",
        "meta_python_orm_class_description_generated_materialization_span_missing",
    )


@pytest.mark.asyncio
async def test_meta_python_orm_function_create_delta_resolves_generated_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n" "    selected_channel: int | None\n",
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _function_create_typed_operation(),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root=generated_package_root.as_posix(),
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert evidence.result.mode is (
        CodeGeneratedMaterializationDeltaMode.section_delta_ready
    )
    entry = evidence.result.entries[0]
    assert entry.section_delta is not None
    assert entry.grammar_anchor_render_delta is None
    section_entry = entry.section_delta.entries[0]
    assert section_entry.section_ref.relative_path == "home/tv_channel.py"
    assert section_entry.content_text == (
        "\n"
        "    def rename(self) -> None:\n"
        '        """Rename the channel."""\n'
        "        raise NotImplementedError\n"
    )
    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.diagnostics == []
    assert resolved.package_delta is not None
    assert resolved.package_delta.package_root == generated_package_root.as_posix()
    assert resolved.package_delta.sources_root == "aware_home_ontology"
    assert resolved.package_delta.paths[0].relative_path == "home/tv_channel.py"
    assert resolved.package_delta.paths[0].content_text == (
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    def rename(self) -> None:\n"
        '        """Rename the channel."""\n'
        "        raise NotImplementedError\n"
    )


@pytest.mark.asyncio
async def test_meta_python_orm_function_delete_delta_resolves_generated_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    def rename(self) -> None:\n"
        '        """Rename the channel."""\n'
        "        raise NotImplementedError\n"
        "\n"
        "    def keep(self) -> None:\n"
        "        raise NotImplementedError\n",
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _function_delete_typed_operation(),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root=generated_package_root.as_posix(),
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert evidence.result.mode is (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == ""
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest(
        "    def rename(self) -> None:\n"
        '        """Rename the channel."""\n'
        "        raise NotImplementedError\n"
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.delete_section
    assert operation.renderer_key == META_PYTHON_ORM_FUNCTION_RENDERER_KEY
    assert operation.content_text == ""
    assert operation.replacement_text == ""
    assert operation.diagnostics == []

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.diagnostics == []
    assert resolved.package_delta is not None
    assert resolved.package_delta.paths[0].relative_path == "home/tv_channel.py"
    assert resolved.package_delta.paths[0].content_text == (
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "\n"
        "    def keep(self) -> None:\n"
        "        raise NotImplementedError\n"
    )


@pytest.mark.asyncio
async def test_meta_python_orm_function_delete_delta_resolves_orm_runtime_package_root(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = (
        generated_package_root / "orm_runtime" / "aware_content_ontology" / "content"
    )
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "content_layout.py"
    generated_source_path.write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class ContentLayout(ORMModel):\n"
        "    name: str\n"
        "\n"
        "    def render(self) -> str:\n"
        '        return ""\n',
        encoding="utf-8",
    )
    operation = function_config_delete_typed_operation(
        semantic_key="meta.function:ContentLayout.render",
        owner_semantic_key="meta.class:ContentLayout",
        class_config_id="class-config-id",
        function_config_id="function-config-id",
        function_name="render",
        owner_key="aware_content.default.content.ContentLayout",
        source_refs=("aware/content/content_layout.aware",),
        kind="instance",
    )
    operation = replace(
        operation,
        current={
            **dict(operation.current),
            "generated_materialization": {
                "python_orm": {"relative_path": "content/content_layout.py"},
            },
        },
    )

    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            operation,
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="content-ontology",
                package_root=generated_package_root.as_posix(),
                sources_root="aware_content_ontology",
            ),
        )
    )

    assert evidence.result.mode is (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.span_target is not None
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.package_delta is not None
    assert resolved.package_delta.paths[0].relative_path == "content/content_layout.py"
    assert "def render" not in (resolved.package_delta.paths[0].content_text or "")


@pytest.mark.asyncio
async def test_meta_python_orm_function_invocation_delta_resolves_generated_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    def rename(self) -> None:\n"
        f"        {_PYTHON_ORM_RENAME_BASELINE_BODY_TEXT}\n",
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _function_invocation_typed_operation(),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root=generated_package_root.as_posix(),
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert evidence.result.mode is (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = evidence.result.entries[0]
    assert entry.section_delta is None
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.span_target is not None
    assert replacement.span_target.relative_path == "home/tv_channel.py"
    assert replacement.replacement_text == (
        "        self.rename_source()\n" "        return None\n"
    )
    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.diagnostics == []
    assert resolved.package_delta is not None
    assert resolved.package_delta.package_root == generated_package_root.as_posix()
    assert resolved.package_delta.sources_root == "aware_home_ontology"
    assert resolved.package_delta.paths[0].relative_path == "home/tv_channel.py"
    assert resolved.package_delta.paths[0].content_text == (
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    def rename(self) -> None:\n"
        "        self.rename_source()\n"
        "        return None\n"
    )


@pytest.mark.asyncio
async def test_meta_python_orm_function_update_description_delta_resolves_generated_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    def rename(self) -> None:\n"
        '        """Rename the channel."""\n'
        "        raise NotImplementedError\n",
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _function_update_description_typed_operation(),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root=generated_package_root.as_posix(),
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = evidence.result.entries[0]
    assert entry.section_delta is None
    assert entry.grammar_anchor_render_delta is not None
    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.diagnostics == []
    assert resolved.package_delta is not None
    assert resolved.package_delta.package_root == generated_package_root.as_posix()
    assert resolved.package_delta.sources_root == "aware_home_ontology"
    assert resolved.package_delta.paths[0].relative_path == "home/tv_channel.py"
    assert resolved.package_delta.paths[0].content_text == (
        "class TvChannel:\n"
        "    selected_channel: int | None\n"
        "\n"
        "    def rename(self) -> None:\n"
        '        """Rename the channel for assistants."""\n'
        "        raise NotImplementedError\n"
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_generated_materialization_stage_resolves_source_package_shape(
    tmp_path,
) -> None:
    generated_package_root = (
        tmp_path / "structure" / "ontology" / "python" / "orm_runtime"
    )
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n    selected_channel: int | None\n",
        encoding="utf-8",
    )
    stage = provider_delta_generated_materialization_stage(
        package_payload={"package_name": "home-ontology"},
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=(
            _provider_delta_semantic_change_report()
        ),
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _attribute_type_operation()
        ),
        code_package_delta=SimpleNamespace(
            package_name="home-ontology",
            package_root="structure/ontology",
            sources_root="aware",
        ),
    )
    delta_requests = cast(tuple[dict[str, object], ...], stage["delta_requests"])
    results = cast(tuple[dict[str, object], ...], stage["results"])
    delta_request = CodeGeneratedMaterializationDeltaRequest.model_validate(
        delta_requests[0]
    )
    result = CodeGeneratedMaterializationDeltaResult.model_validate(results[0])
    entry = result.entries[0]

    assert stage["status"] == "generated_materialization_ready"
    assert result.mode is CodeGeneratedMaterializationDeltaMode.section_delta_ready
    assert delta_request.package_root == generated_package_root.as_posix()
    assert delta_request.sources_root == "aware_home_ontology"
    assert entry.target.relative_path == "aware_home_ontology/home/tv_channel.py"
    assert entry.section_delta is not None
    assert entry.section_delta.package_root == generated_package_root.as_posix()
    assert entry.section_delta.sources_root == "aware_home_ontology"
    assert entry.section_delta.entries[0].section_ref.relative_path == (
        "home/tv_channel.py"
    )

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=delta_request,
            result=result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.package_delta is not None
    assert resolved.package_delta.package_root == generated_package_root.as_posix()
    assert resolved.package_delta.sources_root == "aware_home_ontology"
    assert resolved.package_delta.paths[0].relative_path == "home/tv_channel.py"
    assert "selected_channel: str | None" in (
        resolved.package_delta.paths[0].content_text or ""
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_generated_materialization_stage_uses_stage_sources_root(
    tmp_path,
) -> None:
    package_root = tmp_path / "modules" / "content" / "structure" / "ontology"
    generated_package_root = package_root / "python" / "orm_runtime"
    generated_source_root = (
        generated_package_root / "aware_content_ontology" / "content"
    )
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "content_layout.py"
    generated_source_path.write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class ContentLayout(ORMModel):\n"
        "    name: str\n",
        encoding="utf-8",
    )
    payload = _content_layout_attribute_create_operation()
    current = dict(cast(dict[str, object], payload["current"]))
    generated_materialization = dict(
        cast(dict[str, object], current["generated_materialization"])
    )
    python_orm = dict(cast(dict[str, object], generated_materialization["python_orm"]))
    python_orm["relative_path"] = "content/content_layout.py"
    generated_materialization["python_orm"] = python_orm
    current["generated_materialization"] = generated_materialization
    payload["current"] = current

    stage = provider_delta_generated_materialization_stage(
        package_payload={"package_name": "content-ontology"},
        manifest_path=package_root / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=(
            _provider_delta_semantic_change_report()
        ),
        provider_delta_typed_operation_plan=_typed_operation_plan(payload),
        code_package_delta={
            "package_name": "content-ontology",
            "package_root": package_root.as_posix(),
            "sources_root": (package_root / "aware").as_posix(),
            "workspace_package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
            "workspace_sources_root": "workspaces/aware_kernel/modules/content/ontology/structure/aware",
            "stage_sources_root": "aware",
        },
    )
    delta_requests = cast(tuple[dict[str, object], ...], stage["delta_requests"])
    results = cast(tuple[dict[str, object], ...], stage["results"])
    delta_request = CodeGeneratedMaterializationDeltaRequest.model_validate(
        delta_requests[0]
    )
    result = CodeGeneratedMaterializationDeltaResult.model_validate(results[0])

    assert stage["status"] == "generated_materialization_ready"
    assert result.mode is (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert delta_request.package_root == generated_package_root.as_posix()
    assert delta_request.sources_root == "aware_content_ontology"
    assert result.entries[0].relative_path == "content/content_layout.py"

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=delta_request,
            result=result,
        )
    )

    assert resolved.resolved is True
    assert resolved.package_delta is not None
    assert resolved.package_delta.paths[0].relative_path == "content/content_layout.py"


def test_meta_provider_delta_result_details_include_generated_materialization_stage(
    tmp_path,
) -> None:
    stage = _ready_generated_materialization_stage(tmp_path)

    result = _provider_delta_result(
        request=SimpleNamespace(),
        package_payload={"package_name": "home-ontology"},
        semantic_contract_payload={"provider_key": "aware_meta"},
        manifest_path=tmp_path / "aware.toml",
        analysis=SimpleNamespace(
            source_files=("home/tv_channel.aware",),
            change_preview=SimpleNamespace(
                changed_source_files=("home/tv_channel.aware",),
                semantic_deltas=(object(),),
                semantic_events=(object(),),
            ),
        ),
        current_delta_fingerprint="sha256:test-current-delta",
        operation_plan={"status": "ready"},
        operation_execution={"status": "dry_run"},
        provider_delta_execution_context_preflight={"status": "available"},
        provider_delta_execute_flag_preflight={
            "status": "execute_flag_preflight_not_requested",
        },
        provider_delta_oig_commit_receipt={"status": "execute_flag_commit_noop"},
        provider_delta_head_move_applied_receipt={"status": "not_required"},
        provider_delta_runtime_package_index_patch={
            "status": "runtime_package_index_patch_empty",
        },
        provider_delta_semantic_commit_evidence={
            "status": "semantic_commit_evidence_ready",
            "available": True,
        },
        provider_delta_source_projection={},
        provider_delta_generated_materialization=stage,
        provider_delta_output_materialization={
            "status": "provider_delta_output_materialization_not_required",
            "artifact_ownership_receipt_count": 0,
        },
        provider_delta_head_move_plan={"status": "head_move_not_requested"},
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _attribute_type_operation()
        ),
        provider_delta_mutation_plan={"status": "mutation_plan_ready"},
        provider_delta_ontology_execution_plan={
            "status": "ontology_execution_not_requested",
        },
        provider_delta_functioncall_capability_matrix={
            "coverage_status": "not_required",
        },
        baseline_dirty_preflight={"status": "ready"},
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "available": True,
            "semantic_dirty_entries": (),
        },
        applied_semantic_keys=(),
        stale_semantic_keys=(),
    )
    details = cast(dict[str, object], result["details"])

    assert details["provider_delta_generated_materialization"] == stage
    assert details["provider_delta_generated_materialization_status"] == (
        "generated_materialization_ready"
    )
    assert details["provider_delta_generated_materialization_ready"] is True
    assert (
        details["provider_delta_generated_materialization_renderer_operation_count"]
        == 1
    )


def _ready_generated_materialization_stage(tmp_path) -> dict[str, object]:
    payload = _attribute_type_operation()
    current = dict(cast(dict[str, object], payload["current"]))
    current["generated_materialization"] = {
        "python_orm": {
            "relative_path": "aware_home_ontology/home/tv_channel.py",
        },
    }
    payload["current"] = current
    typed_operation_plan = _typed_operation_plan(payload)

    stage = provider_delta_generated_materialization_stage(
        package_payload={"package_name": "home-ontology"},
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-current-delta",
        provider_delta_semantic_change_report=(
            _provider_delta_semantic_change_report()
        ),
        provider_delta_typed_operation_plan=typed_operation_plan,
        code_package_delta=SimpleNamespace(
            package_name="home-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )
    return stage


@pytest.mark.asyncio
async def test_meta_python_orm_section_delta_evidence_resolves_through_code(
    tmp_path,
) -> None:
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n    selected_channel: int | None\n",
        encoding="utf-8",
    )
    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        _typed_operation(_attribute_type_operation()),
        context=MetaPythonOrmGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
            relative_path_by_owner_key={
                "aware_demo.default.home.TvChannel": (
                    "aware_home_ontology/home/tv_channel.py"
                )
            },
        ),
    )
    handler = cast(Any, build_aware_code_service_protocol_handler())

    validation = await handler.code.generated_materialization_delta.validate(
        ValidateCodeGeneratedMaterializationDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )
    fingerprint = await handler.code.generated_materialization_delta.fingerprint(
        FingerprintCodeGeneratedMaterializationDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert validation.valid is True
    assert validation.diagnostics == []
    assert validation.renderer_operation_count == 1
    assert validation.package_delta_entry_count == 0
    assert validation.section_delta_entry_count == 1
    assert fingerprint.success is True
    assert fingerprint.fingerprint is not None
    assert fingerprint.renderer_operation_count == 1
    assert fingerprint.section_delta_entry_count == 1

    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.package_delta is not None
    assert resolved.path_count == 1
    assert resolved.package_delta.paths[0].relative_path == "home/tv_channel.py"
    assert "selected_channel: str | None" in (
        resolved.package_delta.paths[0].content_text or ""
    )
    assert resolved.package_delta_entry_count == 0
    assert resolved.section_delta_entry_count == 1


@pytest.mark.asyncio
async def test_meta_python_orm_default_value_section_delta_resolves_through_code(
    tmp_path,
) -> None:
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n    selected_channel: int = 7\n",
        encoding="utf-8",
    )
    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        _typed_operation(_attribute_default_value_operation()),
        context=MetaPythonOrmGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
            relative_path_by_owner_key={
                "aware_demo.default.home.TvChannel": (
                    "aware_home_ontology/home/tv_channel.py"
                )
            },
        ),
    )
    handler = cast(Any, build_aware_code_service_protocol_handler())

    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.package_delta is not None
    assert resolved.path_count == 1
    assert resolved.package_delta.paths[0].relative_path == "home/tv_channel.py"
    assert "selected_channel: int = 11" in (
        resolved.package_delta.paths[0].content_text or ""
    )
    assert "selected_channel: int = 7" not in (
        resolved.package_delta.paths[0].content_text or ""
    )
    assert resolved.package_delta_entry_count == 0
    assert resolved.section_delta_entry_count == 1


@pytest.mark.asyncio
async def test_meta_python_orm_enum_create_delta_resolves_through_code(
    tmp_path,
) -> None:
    generated_source_root = tmp_path / "aware_content_ontology" / "content"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "content_enums.py"
    generated_source_path.write_text(
        "from enum import Enum\n\n" "class ContentKind(Enum):\n" '    text = "text"\n',
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(_enum_create_operation()),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
                package_name="content-ontology",
                package_root=tmp_path.as_posix(),
                sources_root="aware_content_ontology",
            ),
        )
    )

    assert evidence.result.mode is (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert len(evidence.result.entries) == 1
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    anchor = entry.renderer_operations[0].anchor
    assert anchor is not None
    assert anchor.anchor_key == META_PYTHON_ORM_ENUM_CLASS_ANCHOR_KEY
    assert entry.renderer_operations[0].content_text is not None
    assert "class ContentSource(Enum):" in entry.renderer_operations[0].content_text
    assert '    text = "text"' in entry.renderer_operations[0].content_text
    assert '    image = "image"' in entry.renderer_operations[0].content_text

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.package_delta is not None
    assert resolved.path_count == 1
    assert resolved.package_delta.paths[0].relative_path == "content/content_enums.py"
    content_text = resolved.package_delta.paths[0].content_text or ""
    assert "class ContentKind(Enum):" in content_text
    assert "class ContentSource(Enum):" in content_text
    assert '    image = "image"' in content_text
    assert resolved.package_delta_entry_count == 0
    assert resolved.grammar_anchor_render_entry_count == 1
    assert resolved.section_delta_entry_count == 0


@pytest.mark.asyncio
async def test_meta_python_orm_enum_delete_resolves_guarded_class_removal(
    tmp_path,
) -> None:
    generated_source_root = tmp_path / "aware_content_ontology" / "content"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "content_enums.py"
    generated_source_path.write_text(
        "from enum import Enum\n\n"
        "class ContentKind(Enum):\n"
        '    text = "text"\n'
        "\n\n"
        "class ContentSource(Enum):\n"
        '    text = "text"\n'
        '    image = "image"\n',
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(_enum_delete_operation()),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
                package_name="content-ontology",
                package_root=tmp_path.as_posix(),
                sources_root="aware_content_ontology",
            ),
        )
    )

    assert evidence.result.mode is (
        CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert len(evidence.result.entries) == 1
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.content_text == ""
    assert operation.replacement_text == ""
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_ENUM_CLASS_ANCHOR_KEY

    handler = cast(Any, build_aware_code_service_protocol_handler())
    resolved = await handler.code.generated_materialization_delta.resolve_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.package_delta is not None
    assert resolved.path_count == 1
    assert resolved.package_delta.paths[0].relative_path == "content/content_enums.py"
    content_text = resolved.package_delta.paths[0].content_text or ""
    assert "class ContentKind(Enum):" in content_text
    assert "class ContentSource(Enum):" not in content_text
    assert resolved.package_delta_entry_count == 0
    assert resolved.grammar_anchor_render_entry_count == 1
    assert resolved.section_delta_entry_count == 0


def test_meta_python_orm_renderer_operation_evidence_is_honest_without_target_path() -> (
    None
):
    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        _typed_operation(_attribute_type_operation()),
    )

    entry = evidence.result.entries[0]
    operation = entry.renderer_operations[0]

    assert operation.target is not None
    assert operation.target.relative_path is None
    assert operation.diagnostics == [
        META_PYTHON_ORM_ATTRIBUTE_TYPE_EVIDENCE_ONLY_DIAGNOSTIC,
        META_PYTHON_ORM_ATTRIBUTE_TYPE_TARGET_RELATIVE_PATH_MISSING_DIAGNOSTIC,
    ]


def test_meta_python_orm_renderer_operation_evidence_is_honest_without_baseline() -> (
    None
):
    payload = _attribute_type_operation()
    payload["baseline"] = {"object": {}}

    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        _typed_operation(payload),
        context=MetaPythonOrmGeneratedMaterializationContext(
            relative_path_by_owner_key={
                "aware_demo.default.home.TvChannel": (
                    "aware_home_ontology/home/tv_channel.py"
                )
            },
        ),
    )
    operation = evidence.result.entries[0].renderer_operations[0]

    assert operation.before_hash is None
    assert operation.diagnostics == [
        META_PYTHON_ORM_ATTRIBUTE_TYPE_EVIDENCE_ONLY_DIAGNOSTIC,
        META_PYTHON_ORM_ATTRIBUTE_TYPE_BASELINE_HASH_MISSING_DIAGNOSTIC,
    ]


def test_meta_python_orm_renderer_operation_blocks_unsupported_type_descriptor() -> (
    None
):
    payload = _attribute_type_operation()
    current = dict(cast(dict[str, object], payload["current"]))
    signature = dict(cast(dict[str, object], current["attribute_signature"]))
    signature["type_descriptor"] = {"kind": "class", "class_name": "Device"}
    current["attribute_signature"] = signature
    payload["current"] = current

    evidence = python_orm_generated_materialization_delta_from_attribute_config_typed_operation(
        _typed_operation(payload),
    )

    assert evidence.result.mode is CodeGeneratedMaterializationDeltaMode.blocked
    assert evidence.result.entries == []
    assert len(evidence.result.skipped_targets) == 1
    assert evidence.result.skipped_targets[0].reason == (
        META_PYTHON_ORM_ATTRIBUTE_TYPE_UNSUPPORTED_REASON
    )
    assert evidence.result.diagnostics == [
        META_PYTHON_ORM_ATTRIBUTE_TYPE_UNSUPPORTED_REASON
    ]


def _enum_create_operation() -> dict[str, object]:
    semantic_key = "ocg:aware_content/node:aware_content.default.content.ContentSource"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.enum.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "enum",
        "source_refs": ("content/content_enums.aware",),
        "baseline": {"object": {}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "enum",
            "enum_fqn": "aware_content.default.content.ContentSource",
            "name": "ContentSource",
            "entity_name": "ContentSource",
            "description": "Content source.",
            "values": ("text", "image"),
            "generated_materialization": {
                "python_orm": {
                    "relative_path": "aware_content_ontology/content/content_enums.py",
                },
            },
        },
    }


def _enum_delete_operation() -> dict[str, object]:
    semantic_key = "ocg:aware_content/node:aware_content.default.content.ContentSource"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum.delete:{semantic_key}",
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.enum.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumConfig",
        "ontology_subject_kind": "enum",
        "source_refs": ("content/content_enums.aware",),
        "baseline": {
            "object": {
                "enum_fqn": "aware_content.default.content.ContentSource",
                "name": "ContentSource",
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "enum",
            "enum_fqn": "aware_content.default.content.ContentSource",
            "name": "ContentSource",
            "entity_name": "ContentSource",
            "generated_materialization": {
                "python_orm": {
                    "relative_path": "aware_content_ontology/content/content_enums.py",
                },
            },
        },
    }


def _typed_operation(payload: dict[str, object]) -> MetaProviderDeltaTypedOperation:
    operation = MetaProviderDeltaTypedOperation.from_payload(payload)
    assert operation is not None
    return operation


def _function_create_typed_operation() -> MetaProviderDeltaTypedOperation:
    current = {
        "generated_materialization": {
            "python_orm": {
                "relative_path": "aware_home_ontology/home/tv_channel.py",
            },
        },
    }
    operation = function_config_create_typed_operation(
        semantic_key=(
            "ocg:aware_demo/node:aware_demo.default.home.TvChannel" "/function:rename"
        ),
        owner_semantic_key=("ocg:aware_demo/node:aware_demo.default.home.TvChannel"),
        class_config_id="class-config-id",
        function_config_id="function-config-id",
        function_name="rename",
        owner_key="aware_demo.default.home.TvChannel",
        source_refs=("home/tv_channel.aware",),
        description="Rename the channel.",
        verb="rename",
        is_async=False,
        kind="instance",
        is_public=True,
        is_constructor=False,
        position=1,
    )
    return replace(operation, current={**dict(operation.current), **current})


def _function_delete_typed_operation() -> MetaProviderDeltaTypedOperation:
    current = {
        "generated_materialization": {
            "python_orm": {
                "relative_path": "aware_home_ontology/home/tv_channel.py",
            },
        },
    }
    operation = function_config_delete_typed_operation(
        semantic_key=(
            "ocg:aware_demo/node:aware_demo.default.home.TvChannel" "/function:rename"
        ),
        owner_semantic_key=("ocg:aware_demo/node:aware_demo.default.home.TvChannel"),
        class_config_id="class-config-id",
        function_config_id="function-config-id",
        function_name="rename",
        owner_key="aware_demo.default.home.TvChannel",
        source_refs=("home/tv_channel.aware",),
        kind="instance",
    )
    return replace(operation, current={**dict(operation.current), **current})


def _function_invocation_typed_operation(
    *,
    include_body_evidence: bool = True,
) -> MetaProviderDeltaTypedOperation:
    operation = function_invocation_create_typed_operation(
        semantic_key=(
            "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
            "/function:rename/invocation:0"
        ),
        function_semantic_key=(
            "ocg:aware_demo/node:aware_demo.default.home.TvChannel" "/function:rename"
        ),
        function_config_id="function-config-id",
        function_config_invocation_id="function-invocation-id",
        position=0,
        kind="call",
        target_function_config_id="target-function-config-id",
        relationship_fingerprint="owner",
        source_refs=("home/tv_channel.aware",),
    )
    python_orm_payload: dict[str, object] = {
        "relative_path": "aware_home_ontology/home/tv_channel.py",
    }
    if include_body_evidence:
        python_orm_payload.update(
            {
                "baseline_body_text": _PYTHON_ORM_RENAME_BASELINE_BODY_TEXT,
                "body_text": _PYTHON_ORM_RENAME_INVOCATION_BODY_TEXT,
            }
        )
    return replace(
        operation,
        current={
            **dict(operation.current),
            "generated_materialization": {
                "python_orm": python_orm_payload,
            },
        },
    )


def _function_update_description_typed_operation() -> MetaProviderDeltaTypedOperation:
    return _function_update_typed_operation(
        baseline_description="Rename the channel.",
        current_description="Rename the channel for assistants.",
        baseline_is_async=False,
        current_is_async=False,
    )


def _function_update_signature_typed_operation() -> MetaProviderDeltaTypedOperation:
    return _function_update_typed_operation(
        baseline_description="Rename the channel.",
        current_description="Rename the channel.",
        baseline_is_async=False,
        current_is_async=True,
    )


def _function_update_input_signature_typed_operation() -> (
    MetaProviderDeltaTypedOperation
):
    semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel" "/function:rename"
    )
    baseline_signature = {
        "owner_key": "aware_demo.default.home.TvChannel",
        "name": "rename",
        "kind": "instance",
        "description": "Rename the channel.",
        "verb": "rename",
        "is_async": False,
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
                    "class_fqn": "TvChannel",
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
    return _typed_operation(
        {
            "operation_kind": "meta_ocg_provider_delta_typed_operation",
            "operation_key": f"meta_ocg.function.update:{semantic_key}",
            "operation_family": "update",
            "provider_operation_type": "meta_ocg.function.update",
            "semantic_key": semantic_key,
            "semantic_subject_type": "aware_meta.FunctionConfig",
            "ontology_subject_kind": "function",
            "source_refs": ("home/tv_channel.aware",),
            "baseline": {
                "object": {
                    "function_signature": baseline_signature,
                },
            },
            "current": {
                "semantic_key": semantic_key,
                "owner_key": "aware_demo.default.home.TvChannel",
                "function_name": "rename",
                "function_signature": current_signature,
                "generated_materialization": {
                    "python_orm": {
                        "relative_path": "aware_home_ontology/home/tv_channel.py",
                    },
                },
            },
        }
    )


def _function_input_delete_operation() -> MetaProviderDeltaTypedOperation:
    semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
        "/function:rename/attribute:input:display_name"
    )
    baseline_signature = {
        "name": "display_name",
        "attribute_config_name": "display_name",
        "type": "input",
        "function_attribute_type": "input",
        "position": 0,
        "is_required": True,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": "string",
        },
    }
    return _typed_operation(
        {
            "operation_kind": "meta_ocg_provider_delta_typed_operation",
            "operation_key": f"meta_ocg.attribute.delete:{semantic_key}",
            "operation_family": "delete",
            "provider_operation_type": "meta_ocg.attribute.delete",
            "semantic_key": semantic_key,
            "semantic_subject_type": "aware_meta.AttributeConfig",
            "ontology_subject_kind": "attribute",
            "source_refs": ("home/tv_channel.aware",),
            "baseline": {
                "object": {
                    "owner_semantic_key": (
                        "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
                        "/function:rename"
                    ),
                    "attribute_name": "display_name",
                    "function_attribute_type": "input",
                    "attribute_signature": baseline_signature,
                    "attribute_membership_signature": {
                        "owner_kind": "function",
                        "name": "display_name",
                        "type": "input",
                        "position": 0,
                    },
                },
            },
            "current": {
                "owner_semantic_key": (
                    "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
                    "/function:rename"
                ),
                "attribute_name": "display_name",
                "function_attribute_type": "input",
                "payload": {
                    "attribute_name": "display_name",
                    "function_attribute_type": "input",
                    "semantic_key": semantic_key,
                },
            },
        }
    )


def _function_input_create_operation() -> MetaProviderDeltaTypedOperation:
    semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
        "/function:rename/attribute:input:label"
    )
    current_signature = {
        "name": "label",
        "attribute_config_name": "label",
        "type": "input",
        "function_attribute_type": "input",
        "position": 0,
        "is_required": True,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": "string",
        },
    }
    return _typed_operation(
        {
            "operation_kind": "meta_ocg_provider_delta_typed_operation",
            "operation_key": f"meta_ocg.attribute.create:{semantic_key}",
            "operation_family": "create",
            "provider_operation_type": "meta_ocg.attribute.create",
            "semantic_key": semantic_key,
            "semantic_subject_type": "aware_meta.AttributeConfig",
            "ontology_subject_kind": "attribute",
            "source_refs": ("home/tv_channel.aware",),
            "baseline": {},
            "current": {
                "owner_semantic_key": (
                    "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
                    "/function:rename"
                ),
                "attribute_name": "label",
                "function_attribute_type": "input",
                "attribute_signature": current_signature,
                "attribute_membership_signature": {
                    "owner_kind": "function",
                    "name": "label",
                    "type": "input",
                    "position": 0,
                },
                "payload": {
                    "attribute_name": "label",
                    "function_attribute_type": "input",
                    "attribute_signature": current_signature,
                    "semantic_key": semantic_key,
                },
            },
        }
    )


def _function_impl_update_operation() -> dict[str, object]:
    semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
        "/function:rename/function_impl:default"
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.function_impl.update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.function_impl.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.FunctionImplValueSource",
        "ontology_subject_kind": "function_impl",
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {
            "object": {
                "function_impl_key": "default",
                "function_impl_kind": "instruction_body",
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "function_impl_key": "default",
            "function_impl_kind": "instruction_body",
        },
    }


def _function_update_typed_operation(
    *,
    baseline_description: str | None,
    current_description: str | None,
    baseline_is_async: bool,
    current_is_async: bool,
) -> MetaProviderDeltaTypedOperation:
    semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel" "/function:rename"
    )
    baseline_signature = {
        "owner_key": "aware_demo.default.home.TvChannel",
        "name": "rename",
        "kind": "instance",
        "description": baseline_description,
        "verb": "rename",
        "is_async": baseline_is_async,
    }
    current_signature = {
        "owner_key": "aware_demo.default.home.TvChannel",
        "name": "rename",
        "kind": "instance",
        "description": current_description,
        "verb": "rename",
        "is_async": current_is_async,
    }
    return _typed_operation(
        {
            "operation_kind": "meta_ocg_provider_delta_typed_operation",
            "operation_key": f"meta_ocg.function.update:{semantic_key}",
            "operation_family": "update",
            "provider_operation_type": "meta_ocg.function.update",
            "semantic_key": semantic_key,
            "semantic_subject_type": "aware_meta.FunctionConfig",
            "ontology_subject_kind": "function",
            "source_refs": ("home/tv_channel.aware",),
            "baseline": {
                "object": {
                    "function_signature": baseline_signature,
                },
            },
            "current": {
                "semantic_key": semantic_key,
                "owner_key": "aware_demo.default.home.TvChannel",
                "function_name": "rename",
                "function_signature": current_signature,
                "generated_materialization": {
                    "python_orm": {
                        "relative_path": "aware_home_ontology/home/tv_channel.py",
                    },
                },
            },
        }
    )


def _function_membership_operation() -> MetaProviderDeltaTypedOperation:
    return _typed_operation(
        {
            "operation_kind": "meta_ocg_provider_delta_typed_operation",
            "operation_key": (
                "meta_ocg.function_membership.update:"
                "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
                "/function:rename/membership"
            ),
            "operation_family": "update",
            "provider_operation_type": "meta_ocg.function_membership.update",
            "semantic_key": (
                "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
                "/function:rename/membership"
            ),
            "semantic_subject_type": "aware_meta.ClassConfigFunctionConfig",
            "ontology_subject_kind": "function_membership",
            "source_refs": ("home/tv_channel.aware",),
            "baseline": {},
            "current": {},
        }
    )


def _class_update_operation() -> dict[str, object]:
    semantic_key = "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.class.update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.class.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ClassConfig",
        "ontology_subject_kind": "class",
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {
            "object": {
                "class_name": "TvChannel",
                "description": None,
            },
        },
        "current": {
            "class_name": "TvChannel",
            "description": "TV channel config.",
        },
    }


def _class_create_operation() -> dict[str, object]:
    semantic_key = "ocg:aware_demo/node:aware_demo.default.home.RemoteControl"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.class.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.class.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {"object": {}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "class",
            "class_fqn": "aware_demo.default.home.RemoteControl",
            "class_name": "RemoteControl",
            "name": "RemoteControl",
            "entity_name": "RemoteControl",
            "description": "Remote control config.",
            "generated_materialization": {
                "python_orm": {
                    "relative_path": "aware_home_ontology/home/tv_channel.py",
                },
            },
        },
    }


def _content_placement_class_create_operation() -> dict[str, object]:
    semantic_key = (
        "ocg:aware_content/node:aware_content.default.content.ContentPlacement"
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.class.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.class.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "source_refs": ("aware/content/content_layout.aware",),
        "baseline": {"object": {}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "class",
            "class_fqn": "aware_content.default.content.ContentPlacement",
            "class_name": "ContentPlacement",
            "name": "ContentPlacement",
            "entity_name": "ContentPlacement",
            "description": "Content placement config.",
        },
    }


def _content_placement_class_delete_operation() -> dict[str, object]:
    semantic_key = (
        "ocg:aware_content/node:aware_content.default.content.ContentPlacement"
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.class.delete:{semantic_key}",
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.class.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraph",
        "ontology_subject_kind": "class",
        "source_refs": ("aware/content/content_layout.aware",),
        "baseline": {
            "object": {
                "class_fqn": "aware_content.default.content.ContentPlacement",
                "class_name": "ContentPlacement",
                "name": "ContentPlacement",
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "class",
            "class_fqn": "aware_content.default.content.ContentPlacement",
            "class_name": "ContentPlacement",
            "name": "ContentPlacement",
            "entity_name": "ContentPlacement",
            "generated_materialization": {
                "python_orm": {
                    "relative_path": (
                        "aware_content_ontology/content/content_layout.py"
                    ),
                },
            },
        },
    }


def _class_create_description_update_operation() -> dict[str, object]:
    semantic_key = "ocg:aware_demo/node:aware_demo.default.home.RemoteControl"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.class.update:{semantic_key}:description",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.class.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ClassConfig",
        "ontology_subject_kind": "class",
        "source_refs": ("home/tv_channel.aware",),
        "baseline": {"object": {"description": None}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "class",
            "class_fqn": "aware_demo.default.home.RemoteControl",
            "class_name": "RemoteControl",
            "name": "RemoteControl",
            "entity_name": "RemoteControl",
            "description": "Remote control config.",
            "payload": {
                "semantic_key": semantic_key,
                "class_fqn": "aware_demo.default.home.RemoteControl",
                "class_name": "RemoteControl",
                "name": "RemoteControl",
                "description": "Remote control config.",
            },
        },
    }


def _typed_operation_plan(payload: dict[str, object]) -> dict[str, object]:
    return {
        "status": "typed_operation_plan_ready",
        "reason": "ready",
        "typed_operations": (payload,),
        "semantic_object_anchors": (),
        "blocked_operations": (),
    }


def _provider_delta_semantic_change_report() -> dict[str, object]:
    return {
        "status": "semantic_change_report_ready",
        "reason": "ready",
        "available": True,
        "blocked": False,
        "semantic_world_change_count": 1,
    }


def _attribute_type_operation() -> dict[str, object]:
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
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg_provider_delta:update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.attribute.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
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


def _attribute_default_value_operation() -> dict[str, object]:
    payload = _attribute_type_operation()
    baseline = dict(cast(dict[str, object], payload["baseline"]))
    baseline_object = dict(cast(dict[str, object], baseline["object"]))
    baseline_signature = dict(
        cast(dict[str, object], baseline_object["attribute_signature"])
    )
    baseline_signature["default_value"] = "7"
    baseline_object["attribute_signature"] = baseline_signature
    baseline["object"] = baseline_object
    current = dict(cast(dict[str, object], payload["current"]))
    current_signature = dict(cast(dict[str, object], current["attribute_signature"]))
    current_signature["description"] = baseline_signature["description"]
    current_signature["type_descriptor"] = baseline_signature["type_descriptor"]
    current_signature["default_value"] = "11"
    current["attribute_signature"] = current_signature
    payload["operation_key"] = (
        "meta_ocg_provider_delta:update:"
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
        "/attribute:selected_channel:default_value"
    )
    payload["baseline"] = baseline
    payload["current"] = current
    return payload


def _content_layout_attribute_create_operation() -> dict[str, object]:
    semantic_key = (
        "ocg:aware_content/node:aware_content.default.content.ContentLayout"
        "/attribute:title"
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.attribute.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.attribute.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": ("aware/content/content_layout.aware",),
        "baseline": {"object": {}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "attribute",
            "owner_key": "aware_content.default.content.ContentLayout",
            "owner_semantic_key": (
                "ocg:aware_content/node:" "aware_content.default.content.ContentLayout"
            ),
            "attribute_name": "title",
            "attribute_signature": {
                "name": "title",
                "description": "Display title.",
                "is_required": True,
                "is_public": True,
                "type_descriptor": {
                    "kind": "primitive",
                    "primitive_base_type": "string",
                },
            },
            "generated_materialization": {
                "python_orm": {
                    "relative_path": (
                        "aware_content_ontology/content/content_layout.py"
                    ),
                },
            },
        },
    }


def _content_layout_attribute_delete_operation() -> dict[str, object]:
    payload = _content_layout_attribute_create_operation()
    payload["operation_key"] = (
        "meta_ocg.attribute.delete:"
        "ocg:aware_content/node:aware_content.default.content.ContentLayout"
        "/attribute:title"
    )
    payload["operation_family"] = "delete"
    payload["provider_operation_type"] = "meta_ocg.attribute.delete"
    payload["baseline"] = {
        "object_id": "75abf967-b070-58f3-9c40-5352dde77c64",
        "object_kind": "attribute",
        "object": {
            "owner_key": "aware_content.default.content.ContentLayout",
            "owner_semantic_key": (
                "ocg:aware_content/node:" "aware_content.default.content.ContentLayout"
            ),
            "attribute_name": "title",
            "attribute_signature": {
                "name": "title",
                "is_required": True,
                "type_descriptor": {
                    "kind": "primitive",
                    "primitive_base_type": "string",
                },
            },
        },
    }
    return payload


def _digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


_PYTHON_ORM_RENAME_BASELINE_BODY_TEXT = (
    '"""Rename the channel."""\n' "        raise NotImplementedError"
)
_PYTHON_ORM_RENAME_UPDATED_BODY_TEXT = (
    '"""Rename the channel for assistants."""\n' "        raise NotImplementedError"
)
_PYTHON_ORM_RENAME_INVOCATION_BODY_TEXT = "self.rename_source()\n" "        return None"
