from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.class_.config.relationship.deltas.source_projection import (
    RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_READY_REASON,
    source_projection_feature_results_from_relationship_config_typed_operation,
)
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
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
from aware_meta.materialization.deltas.feature_registry import (
    generated_materialization_feature_results_from_typed_operation,
)
from aware_meta.materialization.deltas.language_renderer_contracts import (
    MetaLanguageGeneratedMaterializationDeltaContext,
    MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    MetaLanguageGeneratedMaterializationDeltaRenderResult,
    MetaLanguageGeneratedMaterializationTargetHint,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from .generated_materialization_resolution import (
    resolve_code_ready_grammar_anchor_package_delta,
)
from python_grammar.meta_language_plugin import PYTHON_META_PLUGIN
from python_grammar.renderer_delta_orm_relationship import (
    PYTHON_ORM_RELATIONSHIP_ANCHOR_KEY as META_PYTHON_ORM_RELATIONSHIP_ANCHOR_KEY,
    PYTHON_ORM_RELATIONSHIP_RENDERER_KEY as META_PYTHON_ORM_RELATIONSHIP_RENDERER_KEY,
)
from python_grammar.renderer_delta_orm_runtime import (
    PythonOrmRuntimeGeneratedDeltaRenderer,
)


@dataclass(frozen=True, slots=True)
class _PythonOrmGeneratedMaterializationContext:
    package_name: str | None = None
    package_root: str | None = None
    sources_root: str | None = None
    target_language: str | None = "python"
    renderer_profile: str | None = None
    materialization_source: str | None = None
    product_intent: str | None = None
    artifact_family: str | None = None
    artifact_role: str | None = None
    relative_path_by_owner_key: dict[str, str] | None = None


def _render_python_orm_generated_delta(
    operation: MetaProviderDeltaTypedOperation,
    *,
    context: _PythonOrmGeneratedMaterializationContext | None = None,
) -> MetaLanguageGeneratedMaterializationDeltaRenderResult:
    resolved_context = context or _PythonOrmGeneratedMaterializationContext()
    return (
        PythonOrmRuntimeGeneratedDeltaRenderer().render_generated_materialization_delta(
            MetaLanguageGeneratedMaterializationDeltaRenderRequest(
                operation=operation,
                context=MetaLanguageGeneratedMaterializationDeltaContext(
                    package_name=resolved_context.package_name,
                    package_root=resolved_context.package_root,
                    sources_root=resolved_context.sources_root,
                    target_language=resolved_context.target_language,
                    renderer_profile=resolved_context.renderer_profile,
                    materialization_source=resolved_context.materialization_source,
                    product_intent=resolved_context.product_intent,
                    artifact_family=resolved_context.artifact_family,
                    artifact_role=resolved_context.artifact_role,
                    target_hints=tuple(
                        MetaLanguageGeneratedMaterializationTargetHint(
                            owner_key=owner_key,
                            relative_path=relative_path,
                        )
                        for owner_key, relative_path in (
                            resolved_context.relative_path_by_owner_key or {}
                        ).items()
                    ),
                ),
            )
        )
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
        "from uuid import UUID\n"
        "\n"
        "from pydantic import Field\n"
        "\n"
        "class TvChannel:\n"
        "    channel_number: str\n"
        "\n"
        "\n"
        "class RemoteControl:\n"
        "    selected_channel: TvChannel | None = Field(default=None, exclude=True)\n"
        '    selected_channel_id: UUID = Field(description="Foreign key for RemoteControl.selected_channel")\n',
        encoding="utf-8",
    )
    evidence = _render_python_orm_generated_delta(
        _relationship_load_policy_typed_operation(),
        context=_PythonOrmGeneratedMaterializationContext(
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
    replacements = entry.grammar_anchor_render_delta.replacements
    assert len(replacements) == 2
    relationship_replacement = replacements[0]
    assert (
        relationship_replacement.target_kind
        is CodeGrammarAnchorRenderTargetKind.text_span
    )
    assert (
        relationship_replacement.replacement_text == "    selected_channel: TvChannel\n"
    )
    assert relationship_replacement.span_target is not None
    assert relationship_replacement.span_target.before_text_hash == _digest(
        "    selected_channel: TvChannel | None = Field(default=None, exclude=True)\n"
    )
    assert relationship_replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    foreign_key_replacement = replacements[1]
    assert (
        foreign_key_replacement.target_kind
        is CodeGrammarAnchorRenderTargetKind.text_span
    )
    assert foreign_key_replacement.replacement_text == (
        "    selected_channel_id: UUID | None = "
        'Field(default=None, description="Foreign key for RemoteControl.selected_channel")\n'
    )
    assert foreign_key_replacement.span_target is not None
    assert foreign_key_replacement.span_target.before_text_hash == _digest(
        '    selected_channel_id: UUID = Field(description="Foreign key for RemoteControl.selected_channel")\n'
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == META_PYTHON_ORM_RELATIONSHIP_RENDERER_KEY
    assert operation.content_text == "    selected_channel: TvChannel\n"
    assert operation.before_hash == _digest(
        "    selected_channel: TvChannel | None = Field(default=None, exclude=True)\n"
    )
    assert operation.after_hash == _digest("    selected_channel: TvChannel\n")
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_RELATIONSHIP_ANCHOR_KEY
    assert operation.anchor.anchor_role == "relationship_load_policy_field"

    resolved = resolve_code_ready_grammar_anchor_package_delta(
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
        "from uuid import UUID\n"
        "\n"
        "from pydantic import Field\n"
        "\n"
        "class TvChannel:\n"
        "    channel_number: str\n"
        "\n"
        "\n"
        "class RemoteControl:\n"
        "    selected_channel: TvChannel\n"
        "    selected_channel_id: UUID | None = "
        'Field(default=None, description="Foreign key for RemoteControl.selected_channel")\n'
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
        "# Orm\n"
        "from aware_orm.models.orm_model import ORMModel\n"
        "\n"
        "\n"
        "class Device(ORMModel):\n"
        "    # Attributes\n"
        "    name: str\n"
        "\n"
        "\n"
        "class Room(ORMModel):\n"
        "    # Attributes\n"
        "    room_name: str\n",
        encoding="utf-8",
    )
    evidence = _render_python_orm_generated_delta(
        _relationship_create_typed_operation(),
        context=_PythonOrmGeneratedMaterializationContext(
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
    replacements = entry.grammar_anchor_render_delta.replacements
    assert len(replacements) == 3
    replacement = replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == (
        "    # Relationships\n" "    primary_device: Device\n" "\n"
    )
    assert replacement.span_target is not None
    assert replacement.span_target.byte_start == replacement.span_target.byte_end
    assert replacement.span_target.before_text_hash == _digest("")
    import_replacement = replacements[1]
    assert import_replacement.replacement_text == (
        "# Standard\n"
        "from uuid import UUID\n"
        "\n"
        "# Third-party\n"
        "from pydantic import Field\n"
        "\n"
    )
    fk_replacement = replacements[2]
    assert fk_replacement.replacement_text == (
        "\n"
        "    # Foreign Keys\n"
        "    primary_device_id: UUID | None = "
        'Field(default=None, description="Foreign key for Room.primary_device")\n'
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.content_text == (
        "    # Relationships\n" "    primary_device: Device\n" "\n"
    )

    resolved = resolve_code_ready_grammar_anchor_package_delta(
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
        "# Standard\n"
        "from uuid import UUID\n"
        "\n"
        "# Third-party\n"
        "from pydantic import Field\n"
        "\n"
        "# Orm\n"
        "from aware_orm.models.orm_model import ORMModel\n"
        "\n"
        "\n"
        "class Device(ORMModel):\n"
        "    # Attributes\n"
        "    name: str\n"
        "\n"
        "\n"
        "class Room(ORMModel):\n"
        "    # Relationships\n"
        "    primary_device: Device\n"
        "\n"
        "    # Attributes\n"
        "    room_name: str\n"
        "\n"
        "    # Foreign Keys\n"
        "    primary_device_id: UUID | None = "
        'Field(default=None, description="Foreign key for Room.primary_device")\n'
    )


@pytest.mark.asyncio
async def test_meta_python_orm_relationship_create_delta_resolves_markerless_class(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_root.joinpath("model.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "# Orm\n"
        "from aware_orm.models.orm_model import ORMModel\n"
        "\n"
        "\n"
        "class Device(ORMModel):\n"
        "    name: str\n"
        "\n"
        "\n"
        "class Room(ORMModel):\n"
        "    room_name: str\n",
        encoding="utf-8",
    )
    evidence = _render_python_orm_generated_delta(
        _relationship_create_typed_operation(),
        context=_PythonOrmGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=generated_package_root.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacements = entry.grammar_anchor_render_delta.replacements
    assert replacements[0].replacement_text == (
        "    # Relationships\n" "    primary_device: Device\n" "\n"
    )

    resolved = resolve_code_ready_grammar_anchor_package_delta(
        ResolveCodeGeneratedMaterializationPackageDeltaRequest(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )
    )

    assert resolved.success is True
    assert resolved.resolved is True
    assert resolved.package_delta is not None
    content_text = resolved.package_delta.paths[0].content_text or ""
    assert (
        "class Room(ORMModel):\n"
        "    # Relationships\n"
        "    primary_device: Device\n"
        "\n"
        "    room_name: str\n"
        "\n"
        "    # Foreign Keys\n"
        "    primary_device_id: UUID | None = "
        'Field(default=None, description="Foreign key for Room.primary_device")\n'
        in content_text
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
        "# Standard\n"
        "from uuid import UUID\n"
        "\n"
        "# Third-party\n"
        "from pydantic import Field\n"
        "\n"
        "# Orm\n"
        "from aware_orm.models.orm_model import ORMModel\n"
        "\n"
        "\n"
        "class Device(ORMModel):\n"
        "    # Attributes\n"
        "    name: str\n"
        "\n"
        "\n"
        "class Room(ORMModel):\n"
        "    # Relationships\n"
        "    primary_device: Device\n"
        "\n"
        "    # Attributes\n"
        "    room_name: str\n"
        "\n"
        "    # Foreign Keys\n"
        "    primary_device_id: UUID | None = "
        'Field(default=None, description="Foreign key for Room.primary_device")\n',
        encoding="utf-8",
    )
    evidence = _render_python_orm_generated_delta(
        _relationship_delete_typed_operation(),
        context=_PythonOrmGeneratedMaterializationContext(
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
    replacements = entry.grammar_anchor_render_delta.replacements
    assert len(replacements) == 3
    replacement = replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == ""
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest(
        "    # Relationships\n" "    primary_device: Device\n" "\n"
    )
    fk_replacement = replacements[1]
    assert fk_replacement.replacement_text == ""
    assert fk_replacement.span_target is not None
    assert fk_replacement.span_target.before_text_hash == _digest(
        "\n"
        "    # Foreign Keys\n"
        "    primary_device_id: UUID | None = "
        'Field(default=None, description="Foreign key for Room.primary_device")\n'
    )
    import_replacement = replacements[2]
    assert import_replacement.replacement_text == ""
    assert import_replacement.span_target is not None
    assert import_replacement.span_target.before_text_hash == _digest(
        "# Standard\n"
        "from uuid import UUID\n"
        "\n"
        "# Third-party\n"
        "from pydantic import Field\n"
        "\n"
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.content_text == ""

    resolved = resolve_code_ready_grammar_anchor_package_delta(
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
        "# Orm\n"
        "from aware_orm.models.orm_model import ORMModel\n"
        "\n"
        "\n"
        "class Device(ORMModel):\n"
        "    # Attributes\n"
        "    name: str\n"
        "\n"
        "\n"
        "class Room(ORMModel):\n"
        "    # Attributes\n"
        "    room_name: str\n"
    )


def test_relationship_generated_materialization_feature_provider_emits_result(
    monkeypatch,
) -> None:
    _register_python_plugin(monkeypatch)

    [result] = generated_materialization_feature_results_from_typed_operation(
        _relationship_load_policy_typed_operation(),
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="home-ontology",
            package_root="modules/home/structure/ontology",
            sources_root="aware",
            target_language="python",
        ),
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


def _register_python_plugin(monkeypatch) -> None:
    monkeypatch.setattr(
        MetaLanguagePluginRegistry,
        "_plugins",
        {CodeLanguage.python: PYTHON_META_PLUGIN},
    )
    monkeypatch.setattr(
        MetaLanguagePluginRegistry,
        "_supported_languages",
        {CodeLanguage.python},
    )


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
                "meta_ocg.relationship.create:" "meta.relationship:Room.primary_device"
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
                "meta_ocg.relationship.delete:" "meta.relationship:Room.primary_device"
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
