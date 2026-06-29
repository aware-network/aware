from __future__ import annotations

from hashlib import sha256
from typing import Any, cast

import pytest

from aware_code_service import build_aware_code_service_protocol_handler
from aware_meta.enum.config.deltas.generated_materialization import (
    META_PYTHON_ORM_ENUM_CLASS_ANCHOR_KEY,
    META_PYTHON_ORM_ENUM_DESCRIPTION_ANCHOR_KEY,
    META_PYTHON_ORM_ENUM_DESCRIPTION_SPAN_MISSING_DIAGNOSTIC,
    META_PYTHON_ORM_ENUM_EVIDENCE_ONLY_DIAGNOSTIC,
    META_PYTHON_ORM_ENUM_OPTION_DELETE_POLICY_MISSING_DIAGNOSTIC,
    META_PYTHON_ORM_ENUM_OPTION_LINE_ANCHOR_KEY,
    META_PYTHON_ORM_ENUM_OPTION_REORDER_POLICY_MISSING_DIAGNOSTIC,
    META_PYTHON_ORM_ENUM_RENDERER_KEY,
    MetaPythonOrmEnumGeneratedMaterializationContext,
    generated_materialization_feature_results_from_enum_config_typed_operation,
    python_orm_generated_materialization_delta_from_enum_config_typed_operation,
)
from aware_meta.materialization.deltas.code_dto import (
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedRendererDeltaOperationKind,
    CodeGrammarAnchorRenderTargetKind,
    ResolveCodeGeneratedMaterializationPackageDeltaRequest,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaGeneratedMaterializationContext,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


@pytest.mark.asyncio
async def test_meta_python_orm_enum_description_delta_resolves_generated_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "playback_state_enums.py"
    generated_source_path.write_text(
        "from enum import Enum\n"
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    paused = "paused"\n'
        '    playing = "playing"\n',
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(_enum_update_operation()),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
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
        '    """Playback state visible to assistants."""\n'
    )
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest("")
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == META_PYTHON_ORM_ENUM_RENDERER_KEY
    assert operation.content_text == (
        '    """Playback state visible to assistants."""\n'
    )
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_ENUM_DESCRIPTION_ANCHOR_KEY
    assert operation.anchor.anchor_role == "enum_description"
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
    assert resolved.package_delta.paths[0].relative_path == (
        "home/playback_state_enums.py"
    )
    assert resolved.package_delta.paths[0].content_text == (
        "from enum import Enum\n"
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    """Playback state visible to assistants."""\n'
        '    paused = "paused"\n'
        '    playing = "playing"\n'
    )


@pytest.mark.asyncio
async def test_meta_python_orm_enum_option_create_delta_resolves_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "playback_state_enums.py"
    generated_source_path.write_text(
        "from enum import Enum\n"
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    paused = "paused"\n'
        '    playing = "playing"\n',
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(_enum_option_create_operation()),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
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
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == '    stopped = "stopped"\n'
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest("")
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_ENUM_OPTION_LINE_ANCHOR_KEY
    assert operation.anchor.anchor_role == "enum_option_line"
    assert operation.anchor.segment_name == "option_line"

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
    assert resolved.package_delta.paths[0].relative_path == (
        "home/playback_state_enums.py"
    )
    assert resolved.package_delta.paths[0].content_text == (
        "from enum import Enum\n"
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    paused = "paused"\n'
        '    playing = "playing"\n'
        '    stopped = "stopped"\n'
    )


@pytest.mark.asyncio
async def test_meta_python_orm_enum_option_delete_delta_resolves_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "playback_state_enums.py"
    generated_source_path.write_text(
        "from enum import Enum\n"
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    paused = "paused"\n'
        '    playing = "playing"\n'
        '    buffering = "buffering"\n',
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(_enum_option_delete_operation(value="playing")),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
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
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == ""
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest(
        '    playing = "playing"\n'
    )
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_ENUM_OPTION_LINE_ANCHOR_KEY

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
    assert resolved.package_delta.paths[0].relative_path == (
        "home/playback_state_enums.py"
    )
    assert resolved.package_delta.paths[0].content_text == (
        "from enum import Enum\n"
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    paused = "paused"\n'
        '    buffering = "buffering"\n'
    )


@pytest.mark.asyncio
async def test_meta_python_orm_enum_option_reorder_delta_resolves_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "playback_state_enums.py"
    generated_source_path.write_text(
        "from enum import Enum\n"
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    paused = "paused"\n'
        '    playing = "playing"\n'
        '    buffering = "buffering"\n',
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(
                _enum_option_update_operation(
                    value="playing",
                    before_position=1,
                    after_position=2,
                )
            ),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
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
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == (
        '    paused = "paused"\n'
        '    buffering = "buffering"\n'
        '    playing = "playing"\n'
    )
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest(
        '    paused = "paused"\n'
        '    playing = "playing"\n'
        '    buffering = "buffering"\n'
    )
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == META_PYTHON_ORM_ENUM_OPTION_LINE_ANCHOR_KEY

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
    assert resolved.package_delta.paths[0].relative_path == (
        "home/playback_state_enums.py"
    )
    assert resolved.package_delta.paths[0].content_text == (
        "from enum import Enum\n"
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    paused = "paused"\n'
        '    buffering = "buffering"\n'
        '    playing = "playing"\n'
    )


def test_meta_python_orm_enum_description_delta_not_required_when_unchanged() -> None:
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(
                _enum_update_operation(
                    before_description="Playback state.",
                    after_description="Playback state.",
                )
            ),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root="modules/home/structure/ontology/python",
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert evidence.result.mode is CodeGeneratedMaterializationDeltaMode.not_required
    assert evidence.result.entries == []
    assert len(evidence.result.skipped_targets) == 1
    assert evidence.result.skipped_targets[0].reason == (
        "meta_python_orm_enum_generated_materialization_not_required"
    )


def test_meta_python_orm_enum_option_label_update_is_not_required() -> None:
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(_enum_option_update_operation()),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root="modules/home/structure/ontology/python",
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert evidence.result.mode is CodeGeneratedMaterializationDeltaMode.not_required
    assert evidence.result.entries == []
    assert len(evidence.result.skipped_targets) == 1
    assert evidence.result.skipped_targets[0].reason == (
        "meta_python_orm_enum_generated_materialization_not_required"
    )


def test_meta_python_orm_enum_option_reorder_falls_back_without_policy() -> None:
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(
                _enum_option_update_operation(
                    before_position=1,
                    after_position=3,
                )
            ),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
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
    assert META_PYTHON_ORM_ENUM_OPTION_REORDER_POLICY_MISSING_DIAGNOSTIC in (
        evidence.result.diagnostics
    )
    assert len(evidence.result.entries) == 1
    assert evidence.result.entries[0].grammar_anchor_render_delta is None


def test_meta_python_orm_enum_option_delete_falls_back_without_policy() -> None:
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(_enum_option_delete_operation()),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
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
    assert META_PYTHON_ORM_ENUM_OPTION_DELETE_POLICY_MISSING_DIAGNOSTIC in (
        evidence.result.diagnostics
    )
    assert META_PYTHON_ORM_ENUM_OPTION_REORDER_POLICY_MISSING_DIAGNOSTIC not in (
        evidence.result.diagnostics
    )
    assert len(evidence.result.entries) == 1
    assert evidence.result.entries[0].grammar_anchor_render_delta is None


def test_meta_python_orm_enum_description_delta_falls_back_without_source() -> None:
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(_enum_update_operation()),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root="/missing/generated/package/root",
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.fallback_full_render
    )
    assert len(evidence.result.entries) == 1
    assert evidence.result.entries[0].grammar_anchor_render_delta is None
    assert META_PYTHON_ORM_ENUM_EVIDENCE_ONLY_DIAGNOSTIC in (
        evidence.result.diagnostics
    )
    assert META_PYTHON_ORM_ENUM_DESCRIPTION_SPAN_MISSING_DIAGNOSTIC in (
        evidence.result.diagnostics
    )


@pytest.mark.asyncio
async def test_meta_python_orm_enum_create_resolves_generated_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "playback_state_enums.py"
    generated_source_path.write_text(
        "from enum import Enum\n",
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(_enum_structural_create_operation()),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
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
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == (
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    """Playback state visible to assistants."""\n'
        '    paused = "paused"\n'
        '    playing = "playing"\n'
    )
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest("")
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.anchor is not None
    assert operation.anchor.anchor_key == "python.orm.enum.class"
    assert operation.anchor.anchor_role == "enum_class"

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
    assert resolved.package_delta.paths[0].relative_path == (
        "home/playback_state_enums.py"
    )
    assert resolved.package_delta.paths[0].content_text == (
        "from enum import Enum\n"
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    """Playback state visible to assistants."""\n'
        '    paused = "paused"\n'
        '    playing = "playing"\n'
    )


@pytest.mark.asyncio
async def test_meta_python_orm_enum_delete_resolves_generated_package_delta(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "playback_state_enums.py"
    generated_source_path.write_text(
        "from enum import Enum\n"
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    """Playback state visible to assistants."""\n'
        '    paused = "paused"\n'
        '    playing = "playing"\n',
        encoding="utf-8",
    )
    evidence = (
        python_orm_generated_materialization_delta_from_enum_config_typed_operation(
            _typed_operation(_enum_structural_delete_operation()),
            context=MetaPythonOrmEnumGeneratedMaterializationContext(
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
    assert len(evidence.result.entries) == 1
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.content_text == ""
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
    assert resolved.grammar_anchor_render_entry_count == 1
    assert resolved.package_delta is not None
    assert resolved.package_delta.paths[0].relative_path == (
        "home/playback_state_enums.py"
    )
    assert resolved.package_delta.paths[0].content_text == "from enum import Enum\n"


def test_meta_enum_feature_provider_builds_generated_materialization_result(
    tmp_path,
) -> None:
    generated_package_root = tmp_path / "structure" / "ontology" / "python"
    generated_source_root = generated_package_root / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    (generated_source_root / "playback_state_enums.py").write_text(
        "from enum import Enum\n"
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    paused = "paused"\n',
        encoding="utf-8",
    )

    [feature_result] = (
        generated_materialization_feature_results_from_enum_config_typed_operation(
            _typed_operation(_enum_update_operation()),
            context=MetaProviderDeltaGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root=generated_package_root.as_posix(),
                sources_root="aware_home_ontology",
                target_language="python",
            ),
        )
    )

    assert feature_result.feature_key == "enum_config"
    assert feature_result.status == "generated_materialization_projected"
    assert feature_result.projected is True
    assert feature_result.renderer_operation_count == 1
    assert feature_result.result is not None
    assert (
        feature_result.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )


def test_meta_enum_feature_provider_maps_full_authored_source_root_to_generated_python(
    tmp_path,
) -> None:
    package_root = tmp_path / "modules" / "content" / "structure" / "ontology"
    authored_source_root = package_root / "aware"
    generated_source_root = (
        package_root / "python" / "aware_content_ontology" / "content"
    )
    generated_source_root.mkdir(parents=True)
    authored_source_root.mkdir(parents=True)
    (generated_source_root / "content_enums.py").write_text(
        "from enum import Enum\n"
        "\n"
        "\n"
        "class PlaybackState(Enum):\n"
        '    paused = "paused"\n',
        encoding="utf-8",
    )
    operation_payload = _enum_update_operation()
    operation_payload["source_refs"] = ("aware/content/content_enums.aware",)
    cast(dict[str, object], operation_payload["current"]).pop(
        "generated_materialization",
        None,
    )

    [feature_result] = (
        generated_materialization_feature_results_from_enum_config_typed_operation(
            _typed_operation(operation_payload),
            context=MetaProviderDeltaGeneratedMaterializationContext(
                package_name="content-ontology",
                package_root=package_root.as_posix(),
                sources_root=authored_source_root.as_posix(),
                target_language="python",
            ),
        )
    )

    assert feature_result.result is not None
    assert (
        feature_result.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = feature_result.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    assert entry.relative_path == "aware_content_ontology/content/content_enums.py"


def _typed_operation(payload: dict[str, object]) -> MetaProviderDeltaTypedOperation:
    operation = MetaProviderDeltaTypedOperation.from_payload(payload)
    assert operation is not None
    return operation


def _enum_update_operation(
    *,
    before_description: str | None = None,
    after_description: str | None = "Playback state visible to assistants.",
) -> dict[str, object]:
    semantic_key = "meta.enum:PlaybackState"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum.update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.enum.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumConfig",
        "ontology_subject_kind": "enum",
        "source_refs": ("home/playback_state_enums.aware",),
        "baseline": {
            "object": {
                "enum_name": "PlaybackState",
                "description": before_description,
            },
        },
        "current": {
            "enum_name": "PlaybackState",
            "enum_fqn": "aware_home.default.home.PlaybackState",
            "description": after_description,
            "generated_materialization": {
                "python_orm": {
                    "relative_path": (
                        "aware_home_ontology/home/playback_state_enums.py"
                    ),
                },
            },
        },
    }


def _enum_structural_create_operation() -> dict[str, object]:
    semantic_key = "meta.enum:PlaybackState"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.enum.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumConfig",
        "ontology_subject_kind": "enum",
        "source_refs": ("home/playback_state_enums.aware",),
        "baseline": {"object": {}},
        "current": {
            "enum_name": "PlaybackState",
            "enum_fqn": "aware_home.default.home.PlaybackState",
            "description": "Playback state visible to assistants.",
            "values": ("paused", "playing"),
            "generated_materialization": {
                "python_orm": {
                    "relative_path": (
                        "aware_home_ontology/home/playback_state_enums.py"
                    ),
                },
            },
        },
    }


def _enum_structural_delete_operation() -> dict[str, object]:
    semantic_key = "meta.enum:PlaybackState"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum.delete:{semantic_key}",
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.enum.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumConfig",
        "ontology_subject_kind": "enum",
        "source_refs": ("home/playback_state_enums.aware",),
        "baseline": {
            "object": {
                "enum_name": "PlaybackState",
                "enum_fqn": "aware_home.default.home.PlaybackState",
            }
        },
        "current": {
            "enum_name": "PlaybackState",
            "enum_fqn": "aware_home.default.home.PlaybackState",
            "generated_materialization": {
                "python_orm": {
                    "relative_path": (
                        "aware_home_ontology/home/playback_state_enums.py"
                    ),
                },
            },
        },
    }


def _enum_option_create_operation(
    *,
    value: str = "stopped",
    position: int = 2,
) -> dict[str, object]:
    semantic_key = (
        "ocg:aware_home/node:aware_home.default.home.PlaybackState" f"/option:{value}"
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum_option.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.enum_option.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumOption",
        "ontology_subject_kind": "enum_option",
        "source_refs": ("home/playback_state_enums.aware",),
        "baseline": {"object": {}},
        "current": {
            "enum_fqn": "aware_home.default.home.PlaybackState",
            "enum_config_id": "enum-config-playback-state",
            "enum_option_id": f"enum-option-{value}",
            "value": value,
            "label": value.title(),
            "position": position,
            "generated_materialization": {
                "python_orm": {
                    "relative_path": (
                        "aware_home_ontology/home/playback_state_enums.py"
                    ),
                },
            },
        },
    }


def _enum_option_update_operation(
    *,
    value: str = "playing",
    before_position: int = 1,
    after_position: int = 1,
) -> dict[str, object]:
    semantic_key = (
        "ocg:aware_home/node:aware_home.default.home.PlaybackState" f"/option:{value}"
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum_option.update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.enum_option.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumOption",
        "ontology_subject_kind": "enum_option",
        "source_refs": ("home/playback_state_enums.aware",),
        "baseline": {
            "object": {
                "enum_fqn": "aware_home.default.home.PlaybackState",
                "enum_config_id": "enum-config-playback-state",
                "enum_option_id": f"enum-option-{value}",
                "value": value,
                "label": "Playing",
                "position": before_position,
            }
        },
        "current": {
            "enum_fqn": "aware_home.default.home.PlaybackState",
            "enum_config_id": "enum-config-playback-state",
            "enum_option_id": f"enum-option-{value}",
            "value": value,
            "label": "Currently playing",
            "position": after_position,
            "generated_materialization": {
                "python_orm": {
                    "relative_path": (
                        "aware_home_ontology/home/playback_state_enums.py"
                    ),
                },
            },
        },
    }


def _enum_option_delete_operation(
    *,
    value: str = "playing",
    position: int = 1,
) -> dict[str, object]:
    semantic_key = (
        "ocg:aware_home/node:aware_home.default.home.PlaybackState" f"/option:{value}"
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum_option.delete:{semantic_key}",
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.enum_option.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumOption",
        "ontology_subject_kind": "enum_option",
        "source_refs": ("home/playback_state_enums.aware",),
        "baseline": {
            "object": {
                "enum_fqn": "aware_home.default.home.PlaybackState",
                "enum_config_id": "enum-config-playback-state",
                "enum_option_id": f"enum-option-{value}",
                "value": value,
                "label": value.title(),
                "position": position,
            }
        },
        "current": {
            "enum_fqn": "aware_home.default.home.PlaybackState",
            "enum_config_id": "enum-config-playback-state",
            "enum_option_id": f"enum-option-{value}",
            "value": value,
            "position": position,
            "generated_materialization": {
                "python_orm": {
                    "relative_path": (
                        "aware_home_ontology/home/playback_state_enums.py"
                    ),
                },
            },
        },
    }


def _digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()
