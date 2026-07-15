from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from types import SimpleNamespace
from typing import Any, cast

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_file_system.config import FilterConfig
from python_grammar.renderer_delta_orm_enum import (
    MetaPythonOrmEnumGeneratedMaterializationContext,
    python_orm_generated_materialization_delta_from_enum_config_typed_operation,
)
from python_grammar.renderer_delta_orm_function import (
    MetaPythonOrmFunctionGeneratedMaterializationContext,
    python_orm_generated_materialization_delta_from_function_config_typed_operation,
)
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta.language_plugin import MetaLanguagePlugin
from aware_meta.materialization.deltas.code_dto import (
    CodeGrammarAnchorRenderTargetKind,
    CodeGeneratedMaterializationDeltaEntry,
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedMaterializationDeltaRequest,
    CodeGeneratedMaterializationDeltaResult,
    CodeGeneratedMaterializationEventRef,
    CodeGeneratedMaterializationTargetRef,
    CodeGeneratedRendererDeltaOperation,
    CodeGeneratedRendererDeltaOperationKind,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaGeneratedMaterializationContext,
)
from aware_meta.materialization.deltas.feature_registry import (
    generated_materialization_feature_results_from_typed_operation,
)
from aware_meta.materialization.deltas.language_renderer_contracts import (
    MetaLanguageGeneratedMaterializationDeltaContext,
    MetaLanguageGeneratedMaterializationDeltaRenderer,
    MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    MetaLanguageGeneratedMaterializationDeltaRenderResult,
    MetaLanguageGeneratedMaterializationTargetHint,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from python_grammar.meta_language_plugin import PYTHON_META_PLUGIN
from python_grammar.renderer_delta_orm_runtime import (
    PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME,
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


def test_python_plugin_exposes_orm_runtime_generated_delta_renderer() -> None:
    renderers = PYTHON_META_PLUGIN.get_generated_delta_renderers(
        profile="orm_runtime",
    )

    assert tuple(renderers) == (PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME,)
    renderer = renderers[PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME]
    assert renderer.renderer_profile == "orm_runtime"
    assert renderer.materialization_source == "ontology_orm_models"


def test_python_plugin_orm_runtime_supports_all_migrated_generated_delta_families() -> (
    None
):
    renderers = PYTHON_META_PLUGIN.get_generated_delta_renderers(
        profile="orm_runtime",
    )
    renderer = renderers[PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME]
    expected_routes = {
        ("attribute", "create"),
        ("attribute", "delete"),
        ("attribute", "update"),
        ("class", "create"),
        ("class", "delete"),
        ("class", "update"),
        ("enum", "create"),
        ("enum", "delete"),
        ("enum", "update"),
        ("enum_option", "create"),
        ("enum_option", "delete"),
        ("enum_option", "update"),
        ("function", "create"),
        ("function", "delete"),
        ("function", "update"),
        ("function_invocation", "create"),
        ("function_membership", "update"),
        ("relationship", "create"),
        ("relationship", "delete"),
        ("relationship", "update"),
    }

    supported_routes: set[tuple[str, str]] = set()
    for subject_kind, operation_family in sorted(expected_routes):
        operation = _typed_operation(
            _plugin_support_operation(
                ontology_subject_kind=subject_kind,
                operation_family=operation_family,
            )
        )
        request = _plugin_render_request(operation)

        assert renderer.supports_generated_materialization_delta(request), (
            subject_kind,
            operation_family,
        )
        supported_routes.add(
            (operation.ontology_subject_kind, operation.operation_family)
        )

    assert supported_routes == expected_routes


def test_explicit_sql_generated_delta_routes_through_registered_language_plugin(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        MetaLanguagePluginRegistry,
        "_plugins",
        {CodeLanguage.sql: _FAKE_SQL_META_PLUGIN},
    )
    monkeypatch.setattr(
        MetaLanguagePluginRegistry,
        "_supported_languages",
        {CodeLanguage.sql},
    )
    operation = _typed_operation(_sql_plugin_support_operation())

    results = generated_materialization_feature_results_from_typed_operation(
        operation=operation,
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="content-ontology-sql",
            package_root="/tmp/content-ontology-sql",
            sources_root="sql",
            target_language="sql",
        ),
    )

    assert len(results) == 1
    result = results[0]
    assert result.status == "generated_materialization_projected"
    assert result.reason == "meta_generated_materialization_language_plugin_rendered"
    assert result.delta_request is not None
    assert result.delta_request.targets[0].target_language == "sql"
    assert result.delta_request.targets[0].relative_path == "schema/from_hint.sql"
    assert result.result is not None
    assert (
        result.result.mode is CodeGeneratedMaterializationDeltaMode.fallback_full_render
    )
    assert result.renderer_operation_count == 1
    operation = result.result.entries[0].renderer_operations[0]
    assert operation.renderer_key == "fake.sql.class"
    assert operation.content_text == "-- fake sql delta\n"


def test_class_provider_generated_materialization_builder_is_dispatch_shell(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        MetaLanguagePluginRegistry,
        "_plugins",
        {CodeLanguage.sql: _FAKE_SQL_META_PLUGIN},
    )
    monkeypatch.setattr(
        MetaLanguagePluginRegistry,
        "_supported_languages",
        {CodeLanguage.sql},
    )
    operation = _typed_operation(_sql_plugin_support_operation())

    results = generated_materialization_feature_results_from_typed_operation(
        operation=operation,
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="content-ontology-sql",
            package_root="/tmp/content-ontology-sql",
            sources_root="sql",
            target_language="sql",
        ),
    )

    assert len(results) == 1
    result = results[0]
    assert result.status == "generated_materialization_projected"
    assert result.reason == "meta_generated_materialization_language_plugin_rendered"
    assert result.delta_request is not None
    assert result.delta_request.targets[0].relative_path == "schema/from_hint.sql"


def test_enum_provider_python_target_dispatches_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_content_ontology" / "content"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "content_enums.py"
    generated_source_path.write_text(
        "from enum import Enum\n\n" "class ContentKind(Enum):\n" '    text = "text"\n',
        encoding="utf-8",
    )

    [result] = generated_materialization_feature_results_from_typed_operation(
        operation=_typed_operation(_enum_create_operation()),
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="content-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_content_ontology",
            target_language="python",
        ),
    )

    assert result.status == "generated_materialization_projected"
    assert result.reason == "meta_generated_materialization_language_plugin_rendered"
    assert result.delta_request is not None
    assert result.delta_request.metadata is not None
    assert (
        result.delta_request.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    assert result.result is not None
    assert (
        result.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert result.result.metadata is not None
    assert (
        result.result.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    entry = result.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    assert entry.relative_path == "aware_content_ontology/content/content_enums.py"
    assert entry.grammar_anchor_render_delta.replacements[
        0
    ].span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )


def test_function_provider_python_target_dispatches_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "remote_control.py"
    generated_source_path.write_text(
        "class RemoteControl:\n"
        "    def set_channel(self, channel: int) -> None:\n"
        '        payload = {"channel": channel}\n'
        "        raise NotImplementedError\n"
        "\n"
        "\n"
        "class RemoteControlSetChannelInput:\n"
        "    channel: int\n",
        encoding="utf-8",
    )

    [result] = generated_materialization_feature_results_from_typed_operation(
        operation=_typed_operation(_function_signature_operation()),
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
            target_language="python",
        ),
    )

    assert result.status == "generated_materialization_projected"
    assert result.reason == "meta_generated_materialization_language_plugin_rendered"
    assert result.delta_request is not None
    assert result.delta_request.metadata is not None
    assert (
        result.delta_request.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    assert result.result is not None
    assert (
        result.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert result.result.metadata is not None
    assert (
        result.result.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    entry = result.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    assert entry.grammar_anchor_render_delta.sources[0].before_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )


def test_plugin_target_dispatches_through_target_language_plugin_id(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "remote_control.py"
    generated_source_path.write_text(
        "class RemoteControl:\n"
        "    def set_channel(self, channel: int) -> None:\n"
        '        payload = {"channel": channel}\n'
        "        raise NotImplementedError\n"
        "\n"
        "\n"
        "class RemoteControlSetChannelInput:\n"
        "    channel: int\n",
        encoding="utf-8",
    )

    [result] = generated_materialization_feature_results_from_typed_operation(
        operation=_typed_operation(_function_signature_operation()),
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
            target_language="plugin",
            target_language_plugin_id="python",
        ),
    )

    assert result.status == "generated_materialization_projected"
    assert result.reason == "meta_generated_materialization_language_plugin_rendered"
    assert result.delta_request is not None
    assert result.delta_request.targets[0].target_language == "python"
    assert result.delta_request.metadata is not None
    assert (
        result.delta_request.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    assert result.result is not None
    assert (
        result.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = result.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    assert entry.grammar_anchor_render_delta.sources[0].before_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )


def test_attribute_provider_python_target_dispatches_through_language_plugin(
    monkeypatch,
) -> None:
    _register_python_plugin(monkeypatch)

    [result] = generated_materialization_feature_results_from_typed_operation(
        operation=_typed_operation(_attribute_type_operation()),
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root="modules/home/structure/ontology/python",
            sources_root="aware_home_ontology",
            target_language="python",
        ),
    )

    assert result.status == "generated_materialization_projected"
    assert result.reason == "meta_generated_materialization_language_plugin_rendered"
    assert result.delta_request is not None
    assert result.delta_request.metadata is not None
    assert (
        result.delta_request.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    assert result.result is not None
    assert (
        result.result.mode is CodeGeneratedMaterializationDeltaMode.section_delta_ready
    )
    assert result.result.metadata is not None
    assert (
        result.result.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


def test_class_provider_python_target_dispatches_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class TvChannel(ORMModel):\n"
        "    name: str\n",
        encoding="utf-8",
    )

    [result] = generated_materialization_feature_results_from_typed_operation(
        operation=_typed_operation(_class_create_operation()),
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
            target_language="python",
        ),
    )

    assert result.status == "generated_materialization_projected"
    assert result.reason == "meta_generated_materialization_language_plugin_rendered"
    assert result.delta_request is not None
    assert result.delta_request.metadata is not None
    assert (
        result.delta_request.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    assert result.result is not None
    assert (
        result.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = result.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    assert entry.grammar_anchor_render_delta.replacements[
        0
    ].span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )


def test_relationship_provider_python_target_dispatches_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
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

    [result] = generated_materialization_feature_results_from_typed_operation(
        operation=_typed_operation(_relationship_load_policy_operation()),
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
            target_language="python",
        ),
    )

    assert result.status == "generated_materialization_projected"
    assert result.reason == "meta_generated_materialization_language_plugin_rendered"
    assert result.delta_request is not None
    assert result.delta_request.metadata is not None
    assert (
        result.delta_request.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    assert result.result is not None
    assert (
        result.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = result.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    assert entry.grammar_anchor_render_delta.replacements[
        0
    ].span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )


def test_enum_provider_generated_materialization_requires_target_language() -> None:
    [result] = generated_materialization_feature_results_from_typed_operation(
        operation=_typed_operation(_enum_create_operation()),
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="content-ontology",
            package_root="/tmp/content-ontology",
            sources_root="aware_content_ontology",
        ),
    )

    assert result.status == "generated_materialization_blocked"
    assert result.reason == "meta_generated_materialization_target_language_required"
    assert result.required_evidence_fields == ("target_language",)
    assert result.missing_evidence_fields == ("target_language",)
    assert result.delta_request is None
    assert result.result is None


def test_core_providers_generated_materialization_require_target_language() -> None:
    operations = (
        _attribute_type_operation(),
        _class_create_operation(),
        _relationship_load_policy_operation(),
    )

    for payload in operations:
        [result] = generated_materialization_feature_results_from_typed_operation(
            operation=_typed_operation(payload),
            context=MetaProviderDeltaGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root="/tmp/aware-home-ontology-python",
                sources_root="aware_home_ontology",
            ),
        )

        assert result.status == "generated_materialization_blocked"
        assert (
            result.reason == "meta_generated_materialization_target_language_required"
        )
        assert result.required_evidence_fields == ("target_language",)
        assert result.missing_evidence_fields == ("target_language",)
        assert result.delta_request is None
        assert result.result is None


def test_python_orm_generated_delta_uses_neutral_target_hint_without_legacy_payload() -> (
    None
):
    payload = _attribute_type_operation()
    payload["source_refs"] = ()
    request = MetaLanguageGeneratedMaterializationDeltaRenderRequest(
        operation=_typed_operation(payload),
        context=MetaLanguageGeneratedMaterializationDeltaContext(
            package_name="aware-home-ontology-python",
            package_root="modules/home/structure/ontology/python",
            sources_root="aware_home_ontology",
            target_language="python",
            renderer_profile="orm_runtime",
            materialization_source="ontology_orm_models",
            product_intent="orm_runtime",
            artifact_family="ocg_language_materialization",
            artifact_role="python_orm_model",
            target_hints=(
                MetaLanguageGeneratedMaterializationTargetHint(
                    descriptor_key="orm_runtime",
                    capability_key="orm_runtime",
                    target_language="python",
                    renderer_profile="orm_runtime",
                    materialization_source="ontology_orm_models",
                    product_intent="orm_runtime",
                    owner_key="aware_demo.default.home.TvChannel",
                    relative_path="aware_home_ontology/home/tv_channel_from_hint.py",
                ),
            ),
        ),
        renderer_profile="orm_runtime",
        materialization_source="ontology_orm_models",
    )

    result = PYTHON_META_PLUGIN.render_generated_materialization_delta(request)

    assert result.handled is True
    assert result.delta_request is not None
    assert result.delta_request.targets[0].relative_path == (
        "aware_home_ontology/home/tv_channel_from_hint.py"
    )


def test_attribute_type_generated_delta_routes_through_language_plugin(
    monkeypatch,
) -> None:
    _register_python_plugin(monkeypatch)
    evidence = _render_python_orm_generated_delta(
        _typed_operation(_attribute_type_operation()),
        context=_PythonOrmGeneratedMaterializationContext(
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
    assert evidence.delta_request.metadata is not None
    assert (
        evidence.delta_request.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    assert evidence.result.metadata is not None
    assert (
        evidence.result.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    operation = evidence.result.entries[0].renderer_operations[0]
    assert operation.content_text == "str | None"
    assert operation.metadata is not None
    assert (
        operation.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


def test_attribute_default_value_generated_delta_routes_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n" "    selected_channel: int = 7\n",
        encoding="utf-8",
    )
    evidence = _render_python_orm_generated_delta(
        _typed_operation(_attribute_default_value_operation()),
        context=_PythonOrmGeneratedMaterializationContext(
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

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert evidence.result.metadata is not None
    assert (
        evidence.result.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert (
        replacement.replacement_text
        == "    selected_channel: str | None = Field(default=11)\n"
    )
    assert replacement.span_target is not None
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.renderer_key == "python.orm.attribute.field"
    assert operation.content_text == (
        "    selected_channel: str | None = Field(default=11)\n"
    )
    assert operation.metadata is not None
    assert (
        operation.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


def test_attribute_create_generated_delta_routes_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_content_ontology" / "content"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "content_layout.py"
    generated_source_path.write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class ContentLayout(ORMModel):\n"
        "    name: str\n",
        encoding="utf-8",
    )

    evidence = _render_python_orm_generated_delta(
        _typed_operation(_content_layout_attribute_create_operation()),
        context=_PythonOrmGeneratedMaterializationContext(
            package_name="content-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_content_ontology",
        ),
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == "    title: str\n"
    assert replacement.span_target is not None
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == "python.orm.attribute.field"
    assert operation.content_text == "    title: str\n"
    assert operation.metadata is not None
    assert (
        operation.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


def test_attribute_delete_generated_delta_routes_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
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

    evidence = _render_python_orm_generated_delta(
        _typed_operation(_content_layout_attribute_delete_operation()),
        context=_PythonOrmGeneratedMaterializationContext(
            package_name="content-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_content_ontology",
        ),
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == ""
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest("    title: str\n")
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == "python.orm.attribute.field"
    assert operation.content_text == ""
    assert operation.metadata is not None
    assert (
        operation.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


def test_class_description_generated_delta_routes_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "class TvChannel:\n" "    selected_channel: int | None\n",
        encoding="utf-8",
    )

    evidence = _render_python_orm_generated_delta(
        _typed_operation(_class_update_operation()),
        context=_PythonOrmGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert evidence.delta_request.metadata is not None
    assert (
        evidence.delta_request.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    assert evidence.result.metadata is not None
    assert (
        evidence.result.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == '    """TV channel config."""\n'
    assert replacement.span_target is not None
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == "python.orm.class"
    assert operation.anchor is not None
    assert operation.anchor.anchor_role == "class_description"
    assert operation.metadata is not None
    assert (
        operation.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


def test_class_parent_update_generated_delta_routes_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    (generated_source_root / "device.py").write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class Device(ORMModel):\n"
        "    name: str\n"
        "\n\n"
        "class SmartDevice(ORMModel):\n"
        "    device_id: str\n",
        encoding="utf-8",
    )

    evidence = _render_python_orm_generated_delta(
        _typed_operation(_class_parent_update_operation()),
        context=_PythonOrmGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    result = evidence.result
    assert result is not None
    assert (
        result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == "Device"
    assert replacement.span_target is not None
    assert replacement.span_target.before_text_hash == _digest("ORMModel")
    assert replacement.span_target.before_source_hash == _digest(
        (generated_source_root / "device.py").read_text(encoding="utf-8")
    )
    assert replacement.span_target.graph_selector is not None
    assert replacement.span_target.graph_selector.field_name == "parent_class"
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == "python.orm.class"
    assert operation.content_text == "Device"
    assert operation.anchor is not None
    assert operation.anchor.anchor_role == "class_parent"
    assert operation.metadata is not None
    assert (
        operation.metadata["mode_reason"]
        == "python_orm_class_parent_grammar_anchor_render_delta_ready"
    )


def test_class_create_generated_delta_routes_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "tv_channel.py"
    generated_source_path.write_text(
        "from aware_orm.models.orm_model import ORMModel\n\n\n"
        "class TvChannel(ORMModel):\n"
        "    name: str\n",
        encoding="utf-8",
    )

    evidence = _render_python_orm_generated_delta(
        _typed_operation(_class_create_operation()),
        context=_PythonOrmGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == (
        "class RemoteControl(ORMModel):\n" '    """Remote control config."""\n\n\n'
    )
    assert replacement.span_target is not None
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == "python.orm.class"
    assert operation.anchor is not None
    assert operation.anchor.anchor_role == "class"
    assert operation.metadata is not None
    assert (
        operation.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


def test_class_delete_generated_delta_routes_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
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

    evidence = _render_python_orm_generated_delta(
        _typed_operation(_content_placement_class_delete_operation()),
        context=_PythonOrmGeneratedMaterializationContext(
            package_name="content-ontology",
            package_root=tmp_path.as_posix(),
            sources_root="aware_content_ontology",
        ),
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == ""
    assert replacement.span_target is not None
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == "python.orm.class"
    assert operation.content_text == ""
    assert operation.anchor is not None
    assert operation.anchor.anchor_role == "class"
    assert operation.metadata is not None
    assert (
        operation.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


def test_relationship_load_policy_generated_delta_routes_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
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
        _typed_operation(_relationship_load_policy_operation()),
        context=_PythonOrmGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=tmp_path.as_posix(),
            sources_root="aware_home_ontology",
        ),
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert evidence.delta_request.metadata is not None
    assert (
        evidence.delta_request.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    assert evidence.result.metadata is not None
    assert (
        evidence.result.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == "    selected_channel: TvChannel\n"
    assert replacement.span_target is not None
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == "python.orm.relationship.load_policy"
    assert operation.content_text == "    selected_channel: TvChannel\n"
    assert operation.metadata is not None
    assert (
        operation.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


def test_relationship_create_generated_delta_routes_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
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
        _typed_operation(_relationship_create_operation()),
        context=_PythonOrmGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=tmp_path.as_posix(),
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
    assert len(replacements) == 3
    replacement = replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == (
        "    # Relationships\n" "    primary_device: Device\n" "\n"
    )
    assert replacement.span_target is not None
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    assert replacements[1].replacement_text == (
        "# Standard\n"
        "from uuid import UUID\n"
        "\n"
        "# Third-party\n"
        "from pydantic import Field\n"
        "\n"
    )
    assert replacements[2].replacement_text == (
        "\n"
        "    # Foreign Keys\n"
        "    primary_device_id: UUID | None = "
        'Field(default=None, description="Foreign key for Room.primary_device")\n'
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == "python.orm.relationship.load_policy"
    assert operation.content_text == (
        "    # Relationships\n" "    primary_device: Device\n" "\n"
    )
    assert operation.metadata is not None
    assert (
        operation.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


def test_relationship_delete_generated_delta_routes_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
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
        _typed_operation(_relationship_delete_operation()),
        context=_PythonOrmGeneratedMaterializationContext(
            package_name="aware-home-ontology-python",
            package_root=tmp_path.as_posix(),
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
    assert len(replacements) == 3
    replacement = replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacement.replacement_text == ""
    assert replacement.span_target is not None
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    assert replacements[1].replacement_text == ""
    assert replacements[2].replacement_text == ""
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == "python.orm.relationship.load_policy"
    assert operation.content_text == ""
    assert operation.metadata is not None
    assert (
        operation.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


def test_enum_create_generated_delta_routes_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
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

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert evidence.delta_request.metadata is not None
    assert (
        evidence.delta_request.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    assert evidence.result.metadata is not None
    assert (
        evidence.result.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    replacement = entry.grammar_anchor_render_delta.replacements[0]
    assert replacement.target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert "class ContentSource(Enum):" in replacement.replacement_text
    assert replacement.span_target is not None
    assert replacement.span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == "python.orm.enum"
    assert operation.content_text is not None
    assert "ContentSource" in operation.content_text
    assert operation.anchor is not None
    assert operation.anchor.anchor_role == "enum_class"
    assert operation.metadata is not None
    assert (
        operation.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


def test_function_signature_generated_delta_routes_through_language_plugin(
    monkeypatch,
    tmp_path,
) -> None:
    _register_python_plugin(monkeypatch)
    generated_source_root = tmp_path / "aware_home_ontology" / "home"
    generated_source_root.mkdir(parents=True)
    generated_source_path = generated_source_root / "remote_control.py"
    generated_source_path.write_text(
        "class RemoteControl:\n"
        "    def set_channel(self, channel: int) -> None:\n"
        '        payload = {"channel": channel}\n'
        "        raise NotImplementedError\n"
        "\n"
        "\n"
        "class RemoteControlSetChannelInput:\n"
        "    channel: int\n",
        encoding="utf-8",
    )

    evidence = (
        python_orm_generated_materialization_delta_from_function_config_typed_operation(
            _typed_operation(_function_signature_operation()),
            context=MetaPythonOrmFunctionGeneratedMaterializationContext(
                package_name="aware-home-ontology-python",
                package_root=tmp_path.as_posix(),
                sources_root="aware_home_ontology",
            ),
        )
    )

    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready
    )
    assert evidence.delta_request.metadata is not None
    assert (
        evidence.delta_request.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    assert evidence.result.metadata is not None
    assert (
        evidence.result.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )
    entry = evidence.result.entries[0]
    assert entry.grammar_anchor_render_delta is not None
    sources = entry.grammar_anchor_render_delta.sources
    assert len(sources) == 1
    source_text = sources[0].source_text
    assert source_text == generated_source_path.read_text(
        encoding="utf-8",
    )
    assert source_text is not None
    assert sources[0].before_hash == _digest(source_text)
    replacements = entry.grammar_anchor_render_delta.replacements
    assert len(replacements) == 3
    assert replacements[0].target_kind is CodeGrammarAnchorRenderTargetKind.text_span
    assert replacements[0].before_text_hash == _digest(
        "def set_channel(self, channel: int) -> None:"
    )
    assert replacements[0].replacement_text == (
        "def set_channel(self, channel: str) -> None:"
    )
    assert replacements[2].replacement_text == "    channel: str\n"
    assert replacements[0].span_target is not None
    assert replacements[0].span_target.graph_selector is not None
    assert replacements[0].span_target.graph_selector.field_name == "signature"
    assert replacements[0].span_target.before_source_hash == _digest(
        generated_source_path.read_text(encoding="utf-8")
    )
    operation = entry.renderer_operations[0]
    assert operation.kind is CodeGeneratedRendererDeltaOperationKind.replace_anchor
    assert operation.renderer_key == "python.orm.function"
    assert operation.content_text == "def set_channel(self, channel: str) -> None:"
    assert operation.metadata is not None
    assert (
        operation.metadata["language_plugin_delta_renderer"]
        == PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME
    )


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


def _typed_operation(payload: dict[str, object]) -> MetaProviderDeltaTypedOperation:
    operation = MetaProviderDeltaTypedOperation.from_payload(payload)
    assert operation is not None
    return operation


def _plugin_render_request(
    operation: MetaProviderDeltaTypedOperation,
) -> MetaLanguageGeneratedMaterializationDeltaRenderRequest:
    return MetaLanguageGeneratedMaterializationDeltaRenderRequest(
        operation=operation,
        context=MetaLanguageGeneratedMaterializationDeltaContext(
            package_name="content-ontology",
            package_root="/tmp/aware-plugin-contract",
            sources_root="aware_content_ontology",
            target_language="python",
            renderer_profile="orm_runtime",
            materialization_source="ontology_orm_models",
            product_intent="orm_runtime",
            artifact_family="ocg_language_materialization",
            artifact_role="python_orm_model",
        ),
        renderer_profile="orm_runtime",
        materialization_source="ontology_orm_models",
    )


def _plugin_support_operation(
    *,
    ontology_subject_kind: str,
    operation_family: str,
) -> dict[str, object]:
    semantic_key = (
        "ocg:content/node:content.default.PluginCoverage"
        f"/{ontology_subject_kind}:{operation_family}"
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": (
            "meta_ocg.generated_delta_plugin_coverage:"
            f"{ontology_subject_kind}:{operation_family}"
        ),
        "operation_family": operation_family,
        "provider_operation_type": (
            f"meta_ocg.{ontology_subject_kind}.{operation_family}"
        ),
        "semantic_key": semantic_key,
        "semantic_subject_type": f"aware_meta.{ontology_subject_kind}",
        "ontology_subject_kind": ontology_subject_kind,
        "source_refs": ("content/plugin_coverage.aware",),
        "baseline": {"object": {}},
        "current": {},
    }


def _sql_plugin_support_operation() -> dict[str, object]:
    payload = _plugin_support_operation(
        ontology_subject_kind="class",
        operation_family="update",
    )
    payload["current"] = {
        "generated_materialization": {
            "targets": {
                "sql_schema": {
                    "descriptor_key": "sql_schema",
                    "capability_key": "fake_sql_delta",
                    "owner_key": "content.default.PluginCoverage",
                    "relative_path": "schema/from_hint.sql",
                },
            },
        },
    }
    return payload


class _FakeSqlGeneratedDeltaRenderer(MetaLanguageGeneratedMaterializationDeltaRenderer):
    renderer_key = "fake_sql_delta"
    renderer_profile = "sql_runtime"
    materialization_source = "sql_schema"

    def supports_generated_materialization_delta(
        self,
        request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    ) -> bool:
        return request.operation.ontology_subject_kind == "class"

    def render_generated_materialization_delta(
        self,
        request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    ) -> MetaLanguageGeneratedMaterializationDeltaRenderResult:
        event_key = (
            "aware_meta.provider_delta.world_change."
            f"{request.operation.ontology_subject_kind}."
            f"{request.operation.operation_family}"
        )
        relative_path = "schema.sql"
        if request.context.target_hints:
            relative_path = (
                request.context.target_hints[0].relative_path or relative_path
            )
        target = CodeGeneratedMaterializationTargetRef(
            target_key=f"fake_sql:{request.operation.semantic_key}",
            provider_key="aware_meta",
            semantic_owner="aware_meta.ocg",
            target_language="sql",
            package_name=request.context.package_name,
            package_root=request.context.package_root,
            sources_root=request.context.sources_root,
            renderer_key="fake.sql.class",
            renderer_profile=self.renderer_profile,
            materialization_source=self.materialization_source,
            relative_path=relative_path,
        )
        delta_request = CodeGeneratedMaterializationDeltaRequest(
            provider_key="aware_meta",
            semantic_owner="aware_meta.ocg",
            package_name=request.context.package_name,
            package_root=request.context.package_root,
            sources_root=request.context.sources_root,
            product_intent="fake_sql_schema",
            events=[
                CodeGeneratedMaterializationEventRef(
                    event_key=event_key,
                    semantic_key=request.operation.semantic_key,
                    verb=request.operation.operation_family,
                    subject_type=request.operation.ontology_subject_kind,
                    source="test.fake_sql_generated_delta_renderer",
                )
            ],
            targets=[target],
        )
        renderer_operation = CodeGeneratedRendererDeltaOperation(
            operation_key=f"fake_sql:{request.operation.operation_key}",
            kind=CodeGeneratedRendererDeltaOperationKind.replace_anchor,
            target=target,
            renderer_key="fake.sql.class",
            renderer_profile=self.renderer_profile,
            content_text="-- fake sql delta\n",
            replacement_text="-- fake sql delta\n",
            event_refs=[event_key],
            semantic_keys=[request.operation.semantic_key],
        )
        result = CodeGeneratedMaterializationDeltaResult(
            provider_key="aware_meta",
            semantic_owner="aware_meta.ocg",
            available=True,
            mode=CodeGeneratedMaterializationDeltaMode.fallback_full_render,
            entries=[
                CodeGeneratedMaterializationDeltaEntry(
                    entry_key=f"fake_sql:{request.operation.operation_key}",
                    mode=CodeGeneratedMaterializationDeltaMode.fallback_full_render,
                    target=target,
                    relative_path=relative_path,
                    renderer_operations=[renderer_operation],
                    event_refs=[event_key],
                    semantic_keys=[request.operation.semantic_key],
                )
            ],
        )
        return MetaLanguageGeneratedMaterializationDeltaRenderResult.from_evidence(
            delta_request=delta_request,
            result=result,
            reason="fake_sql_generated_delta_rendered",
        )


_FAKE_SQL_META_PLUGIN = MetaLanguagePlugin(
    language=CodeLanguage.sql,
    file_filter_config_factory=lambda: FilterConfig.model_validate({}),
    code_plugin=cast(
        Any,
        SimpleNamespace(
            comment_prefix="--",
            materialization_artifact_outputs=(),
        ),
    ),
    surgical_renderers={},
    generated_delta_renderers={
        "fake_sql_delta": _FakeSqlGeneratedDeltaRenderer,
    },
)


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
    semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel"
        "/attribute:selected_channel:default_value"
    )
    baseline = dict(cast(dict[str, object], payload["baseline"]))
    current = dict(cast(dict[str, object], payload["current"]))
    baseline_object = dict(cast(dict[str, object], baseline["object"]))
    baseline_signature = dict(
        cast(dict[str, object], baseline_object["attribute_signature"])
    )
    current_signature = dict(cast(dict[str, object], current["attribute_signature"]))
    baseline_signature["default_value"] = "7"
    current_signature["default_value"] = "11"
    baseline_object["attribute_signature"] = baseline_signature
    baseline["object"] = baseline_object
    current["attribute_signature"] = current_signature
    payload.update(
        {
            "operation_key": f"meta_ocg_provider_delta:update:{semantic_key}",
            "semantic_key": semantic_key,
            "baseline": baseline,
            "current": current,
        }
    )
    return payload


def _content_layout_attribute_create_operation() -> dict[str, object]:
    semantic_key = "ocg:content/node:content.default.ContentLayout/attribute:title"
    signature = {
        "owner_key": "content.default.ContentLayout",
        "name": "title",
        "description": "Title.",
        "default_value": None,
        "is_required": True,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": "string",
        },
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.attribute.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.attribute.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": ("content/content_layout.aware",),
        "baseline": {},
        "current": {
            "attribute_name": "title",
            "owner_key": "content.default.ContentLayout",
            "attribute_signature": signature,
        },
    }


def _content_layout_attribute_delete_operation() -> dict[str, object]:
    payload = _content_layout_attribute_create_operation()
    semantic_key = str(payload["semantic_key"])
    payload.update(
        {
            "operation_key": f"meta_ocg.attribute.delete:{semantic_key}",
            "operation_family": "delete",
            "provider_operation_type": "meta_ocg.attribute.delete",
            "baseline": {
                "object": dict(cast(dict[str, object], payload["current"])),
            },
        }
    )
    return payload


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


def _class_parent_update_operation() -> dict[str, object]:
    semantic_key = "ocg:aware_demo/node:aware_demo.default.home.SmartDevice"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.class.parent.update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.class.parent.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ClassConfig",
        "ontology_subject_kind": "class",
        "source_refs": ("home/device.aware",),
        "baseline": {
            "object": {
                "class_fqn": "aware_demo.default.home.SmartDevice",
                "class_name": "SmartDevice",
                "parent_class_id": None,
                "parent_class_fqn": None,
                "parent_class_semantic_key": None,
            },
        },
        "current": {
            "class_fqn": "aware_demo.default.home.SmartDevice",
            "class_name": "SmartDevice",
            "parent_class_id": "1c2e20a0-8752-5545-82c8-7a46008ec53d",
            "parent_class_fqn": "aware_demo.default.home.Device",
            "parent_class_semantic_key": (
                "ocg:aware_demo/node:aware_demo.default.home.Device"
            ),
            "generated_materialization": _python_orm_runtime_targets(
                "aware_home_ontology/home/device.py"
            ),
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
            "generated_materialization": _python_orm_runtime_targets(
                "aware_home_ontology/home/tv_channel.py"
            ),
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
            "generated_materialization": _python_orm_runtime_targets(
                "aware_content_ontology/content/content_layout.py"
            ),
        },
    }


def _relationship_load_policy_operation() -> dict[str, object]:
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
    return {
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


def _relationship_create_operation() -> dict[str, object]:
    current_signature = {
        "source_class_fqn": "home.Room",
        "target_class_fqn": "home.Device",
        "relationship_key": "primary_device",
        "relationship_type": "many_to_one",
        "forward_loading_strategy": "eager",
    }
    return {
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


def _relationship_delete_operation() -> dict[str, object]:
    baseline_signature = {
        "source_class_fqn": "home.Room",
        "target_class_fqn": "home.Device",
        "relationship_key": "primary_device",
        "relationship_type": "many_to_one",
        "forward_loading_strategy": "eager",
    }
    return {
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
            "generated_materialization": _python_orm_runtime_targets(
                "aware_content_ontology/content/content_enums.py"
            ),
        },
    }


def _function_signature_operation() -> dict[str, object]:
    semantic_key = "ocg:home/node:home.RemoteControl/function:set_channel"
    baseline_signature = {
        "owner_key": "home.RemoteControl",
        "name": "set_channel",
        "description": "Set the active channel.",
        "is_async": False,
        "inputs": [
            {
                "name": "channel",
                "position": 0,
                "is_required": True,
                "type_descriptor": {
                    "kind": "primitive",
                    "primitive_base_type": "integer",
                },
            }
        ],
        "outputs": [],
    }
    current_signature = {
        **baseline_signature,
        "inputs": [
            {
                "name": "channel",
                "position": 0,
                "is_required": True,
                "type_descriptor": {
                    "kind": "primitive",
                    "primitive_base_type": "string",
                },
            }
        ],
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.function.update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.function.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.FunctionConfig",
        "ontology_subject_kind": "function",
        "source_refs": ("home/remote_control.aware",),
        "baseline": {
            "object": {
                "function_name": "set_channel",
                "function_signature": baseline_signature,
            },
        },
        "current": {
            "function_name": "set_channel",
            "owner_key": "home.RemoteControl",
            "function_signature": current_signature,
        },
    }


def _digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _python_orm_runtime_targets(relative_path: str) -> dict[str, object]:
    return {
        "targets": {
            "orm_runtime": {
                "descriptor_key": "orm_runtime",
                "capability_key": "orm_runtime",
                "target_language": "python",
                "renderer_profile": "orm_runtime",
                "materialization_source": "ontology_orm_models",
                "relative_path": relative_path,
            },
        },
    }


__all__ = []
