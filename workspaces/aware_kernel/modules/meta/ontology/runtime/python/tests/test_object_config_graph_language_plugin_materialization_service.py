from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Any, ClassVar, cast
from uuid import UUID

import pytest

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code.language.plugin import CodeLanguageMaterializationOutputDescriptor
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import (
    CodePrimitiveBaseType,
)
from aware_file_system.config import FilterConfig
from aware_code.section.writer import CodeSectionWriter
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    build_renderer_empty_code,
)
import aware_meta.graph.config.render.renderer_language as renderer_language_module
from aware_meta.graph.config.runtime_derivation.schemas import (
    RuntimeObjectConfigGraphDerivationResult,
)
from aware_meta.language_plugin import MetaLanguagePlugin
from aware_meta.language_plugin import (
    MetaLanguageDeclaredOutputProducedFile,
    MetaLanguageDeclaredOutputProducerRequest,
    MetaLanguageDeclaredOutputProducerResult,
)
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
import aware_meta.materialization.language_service as language_service_module
from aware_meta.materialization import (
    GraphMaterializationTransformRequest,
    GraphMaterializationTransformService,
    LanguageMaterializationRenderRequest,
    LanguagePluginMaterializationRequest,
    RuntimeToLanguageClosureLoweringRequest,
    RuntimeToLanguageClosureLoweringService,
    RuntimeToLanguageLoweringCache,
    materialize_object_config_graph_via_language_plugin,
    render_language_materialization,
)
from aware_meta.materialization.language_service import (  # noqa: E402
    RuntimeObjectConfigGraphDerivationCache,
)
from aware_meta.semantic_contract import (
    META_LANGUAGE_MATERIALIZATION_CODE_PACKAGE_DELTAS_OUTPUT_KEY,
    META_LANGUAGE_MATERIALIZATION_GENERATED_FILES_OUTPUT_KEY,
    META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY,
    META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY,
    META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
    META_OBJECT_CONFIG_GRAPH_OWNER,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionKind,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_node_layout import (
    ObjectConfigGraphNodeLayout,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig


PYTHON_META_RUNTIME_HANDLERS_OUTPUT_KEY = "python.meta_runtime_handlers_provider"


class _FakeRuntimeToSqlTransformer:
    last_kwargs: ClassVar[dict[str, object] | None] = None
    calls: ClassVar[list[dict[str, object]]] = []

    def __init__(self, **kwargs: object) -> None:
        type(self).last_kwargs = dict(kwargs)
        type(self).calls.append(dict(kwargs))

    def transform(
        self,
        object_config_graph: ObjectConfigGraph,
        code_primitive_type: object | None = None,
    ) -> ObjectConfigGraph:
        _ = code_primitive_type
        out = object_config_graph.model_copy(deep=True)
        out.language = CodeLanguage.sql
        out.hash = f"{object_config_graph.hash}:sql"
        return out

    def get_generated_ocg_node_manifest(self) -> None:
        return None

    def set_policy(self, policy: object | None) -> None:
        _ = policy


class _MutatingRuntimeToSqlTransformer:
    def __init__(self, **kwargs: object) -> None:
        _ = kwargs

    def transform(
        self,
        object_config_graph: ObjectConfigGraph,
        code_primitive_type: object | None = None,
    ) -> ObjectConfigGraph:
        _ = code_primitive_type
        object_config_graph.hash = "mutated-language-hash"
        class_config = next(
            node.class_config
            for node in object_config_graph.object_config_graph_nodes
            if node.class_config is not None
        )
        class_config.name = "MutatedDevice"
        return object_config_graph

    def get_generated_ocg_node_manifest(self) -> None:
        return None

    def set_policy(self, policy: object | None) -> None:
        _ = policy


class _FakeSqlLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy):
    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.sql

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path(f"classes/{class_config.name}.sql")

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        return Path(f"enums/{enum_config.name}.sql")

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        return Path(f"functions/{function_config.name}.sql")

    def get_file_extension(self) -> str:
        return ".sql"


class _FakePythonLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy):
    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path(f"classes/{class_config.name}.py")

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        return Path(f"enums/{enum_config.name}.py")

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        return Path(f"functions/{function_config.name}.py")

    def get_file_extension(self) -> str:
        return ".py"


class _FakeSqlRendererLanguage(ObjectConfigGraphRendererLanguage):
    last_external_graphs: ClassVar[tuple[ObjectConfigGraph, ...]] = ()
    last_import_overrides: ClassVar[dict[str, str]] = {}
    emit_declared_manifest: ClassVar[bool] = False
    emit_render_phase_timings: ClassVar[bool] = False

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy)
        self._graph: ObjectConfigGraph | None = None
        self._warnings: list[str] = []

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.sql

    @property
    def indent(self) -> int:
        return 2

    @property
    def comment_prefix(self) -> str:
        return "--"

    def define_assemblers(self) -> None:
        return None

    def bind_profile_inputs(self, profile_inputs: Mapping[str, object]) -> None:
        self.profile_inputs = dict(profile_inputs)

    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        self._graph = graph

    def extra_output_paths(self) -> list[Path]:
        return [Path("rendered/demo.sql")]

    def create_empty_code(self):
        return build_renderer_empty_code(
            language=CodeLanguage.sql,
            renderer_key="fake_sql",
        )

    def emit_file(
        self,
        meta_objects: list[Any],
        writer: CodeSectionWriter,
        schema: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        _ = (
            meta_objects,
            schema,
            class_to_class_config_map,
            base_class_module,
            base_class_name,
        )
        graph = self._graph
        if graph is None:
            raise AssertionError("Expected graph to be bound before emit_file")
        type(self).last_external_graphs = tuple(self.external_graphs)
        type(self).last_import_overrides = dict(self.import_overrides or {})
        writer.token(
            f"-- rendered by fake sql plugin\nselect '{graph.name}' as graph_name;\n"
        )

    def clear_warnings(self) -> None:
        self._warnings.clear()

    def get_warnings(self) -> list[str]:
        return list(self._warnings)

    def get_render_phase_timings(self) -> dict[str, float]:
        if not type(self).emit_render_phase_timings:
            return {}
        return {
            "writer_assembly": 0.125,
            "write_compare": 0.25,
        }


class _FakePythonRendererLanguage(ObjectConfigGraphRendererLanguage):
    emit_black_stable_source: ClassVar[bool] = False

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy)
        self._warnings: list[str] = []

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    @property
    def indent(self) -> int:
        return 4

    @property
    def comment_prefix(self) -> str:
        return "#"

    def define_assemblers(self) -> None:
        return None

    def create_empty_code(self):
        return build_renderer_empty_code(
            language=CodeLanguage.python,
            renderer_key="fake_python",
        )

    def emit_file(
        self,
        meta_objects: list[Any],
        writer: CodeSectionWriter,
        schema: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        _ = (
            meta_objects,
            schema,
            class_to_class_config_map,
            base_class_module,
            base_class_name,
        )
        if type(self).emit_black_stable_source:
            writer.token('value = {"name": "demo"}\n')
            return
        writer.token("value={'name':'demo'}\n")

    def clear_warnings(self) -> None:
        self._warnings.clear()

    def get_warnings(self) -> list[str]:
        return list(self._warnings)


class _FakeStableIdsRendererLanguage(ObjectConfigGraphRendererLanguage):
    last_policy: ClassVar[dict[str, object] | None] = None
    last_bound_graph_hash: ClassVar[str | None] = None
    last_source_graph_hash: ClassVar[str | None] = None

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy)
        self._graph: ObjectConfigGraph | None = None
        self._warnings: list[str] = []

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.sql

    @property
    def indent(self) -> int:
        return 2

    @property
    def comment_prefix(self) -> str:
        return "--"

    def define_assemblers(self) -> None:
        return None

    def set_policy(self, policy: object | None) -> None:
        if policy is None:
            type(self).last_policy = None
            type(self).last_source_graph_hash = None
            return
        if not isinstance(policy, Mapping):
            raise AssertionError("Expected stable ids policy mapping")
        policy_dict = dict(policy)
        type(self).last_policy = policy_dict
        source_graph = policy_dict.get("stable_ids_source_graph")
        if not isinstance(source_graph, ObjectConfigGraph):
            raise AssertionError("Expected stable ids source graph policy")
        type(self).last_source_graph_hash = source_graph.hash

    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        self._graph = graph
        type(self).last_bound_graph_hash = graph.hash

    def extra_output_paths(self) -> list[Path]:
        return [Path("rendered/stable_ids.sql")]

    def create_empty_code(self):
        return build_renderer_empty_code(
            language=CodeLanguage.sql,
            renderer_key="fake_stable_ids",
        )

    def emit_file(
        self,
        meta_objects: list[Any],
        writer: CodeSectionWriter,
        schema: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        _ = (
            meta_objects,
            schema,
            class_to_class_config_map,
            base_class_module,
            base_class_name,
        )
        graph = self._graph
        if graph is None:
            raise AssertionError("Expected graph to be bound before emit_file")
        writer.token(f"-- stable ids for {graph.name}\n")

    def clear_warnings(self) -> None:
        self._warnings.clear()

    def get_warnings(self) -> list[str]:
        return list(self._warnings)


@pytest.fixture
def isolated_meta_language_plugin_registry() -> Iterator[None]:
    saved_plugins = dict(MetaLanguagePluginRegistry._plugins)
    saved_supported = set(MetaLanguagePluginRegistry._supported_languages)
    saved_file_filters = dict(MetaLanguagePluginRegistry._file_filter_overrides)
    saved_structural_filters = dict(
        MetaLanguagePluginRegistry._structural_filter_overrides
    )
    saved_code_plugins = dict(CodeLanguagePluginRegistry._plugins)
    saved_code_supported = set(CodeLanguagePluginRegistry._supported_languages)
    MetaLanguagePluginRegistry.clear()
    CodeLanguagePluginRegistry.clear()
    try:
        yield
    finally:
        MetaLanguagePluginRegistry.clear()
        CodeLanguagePluginRegistry.clear()
        MetaLanguagePluginRegistry._plugins.update(saved_plugins)
        MetaLanguagePluginRegistry._supported_languages.update(saved_supported)
        MetaLanguagePluginRegistry._file_filter_overrides.update(saved_file_filters)
        MetaLanguagePluginRegistry._structural_filter_overrides.update(
            saved_structural_filters
        )
        CodeLanguagePluginRegistry._plugins.update(saved_code_plugins)
        CodeLanguagePluginRegistry._supported_languages.update(saved_code_supported)


def _register_builtin_aware_plugin() -> None:
    for plugin in AwareModulePluginRegistry.get_builtin_meta_language_plugins():
        if getattr(plugin, "language", None) == CodeLanguage.aware:
            MetaLanguagePluginRegistry.register(cast(MetaLanguagePlugin, plugin))
            return
    raise AssertionError("Expected built-in Aware Meta language plugin")


def _register_fake_sql_plugin(
    *,
    include_stable_ids: bool = False,
    runtime_to_language_transformer: type[object] = _FakeRuntimeToSqlTransformer,
) -> None:
    _FakeRuntimeToSqlTransformer.calls = []
    _FakeRuntimeToSqlTransformer.last_kwargs = None
    _FakeSqlRendererLanguage.last_external_graphs = ()
    _FakeSqlRendererLanguage.last_import_overrides = {}
    _FakeSqlRendererLanguage.emit_declared_manifest = False
    _FakeSqlRendererLanguage.emit_render_phase_timings = False
    _FakeStableIdsRendererLanguage.last_policy = None
    _FakeStableIdsRendererLanguage.last_bound_graph_hash = None
    _FakeStableIdsRendererLanguage.last_source_graph_hash = None
    language_renderers: dict[str, type[ObjectConfigGraphRendererLanguage]] = {
        "default": _FakeSqlRendererLanguage,
    }
    default_renderer_names = ("default",)
    if include_stable_ids:
        language_renderers["stable_ids"] = _FakeStableIdsRendererLanguage
        default_renderer_names = ("default", "stable_ids")
    MetaLanguagePluginRegistry.register(
        MetaLanguagePlugin(
            language=CodeLanguage.sql,
            file_filter_config_factory=lambda: FilterConfig.model_validate({}),
            code_plugin=cast(
                Any,
                SimpleNamespace(
                    comment_prefix="--",
                    materialization_artifact_outputs=(
                        CodeLanguageMaterializationOutputDescriptor(
                            output_key="sql.test_manifest",
                            description="Fake SQL plugin manifest output.",
                            output_kind="manifest",
                            artifact_role="test_manifest",
                            path_templates=("_aware/sql.manifest.json",),
                            producer_step="manifest_write",
                            required_for=("workspace_revision",),
                        ),
                    ),
                ),
            ),
            surgical_renderers={},
            language_renderers=language_renderers,
            default_renderer_names=default_renderer_names,
            layout_strategy=_FakeSqlLayoutStrategy,
            runtime_to_language_transformer=cast(Any, runtime_to_language_transformer),
            declared_output_producer=_fake_sql_declared_output_producer,
        )
    )


def _register_fake_python_plugin() -> None:
    _FakePythonRendererLanguage.emit_black_stable_source = False
    MetaLanguagePluginRegistry.register(
        MetaLanguagePlugin(
            language=CodeLanguage.python,
            file_filter_config_factory=lambda: FilterConfig.model_validate({}),
            code_plugin=cast(Any, SimpleNamespace(comment_prefix="#")),
            surgical_renderers={},
            language_renderers={"default": _FakePythonRendererLanguage},
            default_renderer_names=("default",),
            layout_strategy=_FakePythonLayoutStrategy,
        )
    )


def _fake_sql_declared_output_producer(
    request: MetaLanguageDeclaredOutputProducerRequest,
) -> MetaLanguageDeclaredOutputProducerResult:
    if not _FakeSqlRendererLanguage.emit_declared_manifest:
        return MetaLanguageDeclaredOutputProducerResult()
    descriptor = next(
        item for item in request.descriptors if item.output_key == "sql.test_manifest"
    )
    return MetaLanguageDeclaredOutputProducerResult(
        produced_files=(
            MetaLanguageDeclaredOutputProducedFile(
                output_key=descriptor.output_key,
                path=Path("_aware/sql.manifest.json"),
                content_text='{"language":"sql","status":"ok"}\n',
                output_kind=descriptor.output_kind,
                artifact_role=descriptor.artifact_role,
            ),
        ),
        metrics={"fake_sql_declared_output_count": 1},
    )


def _build_demo_runtime_graph() -> ObjectConfigGraph:
    graph_id = UUID("aaaaaaaa-aaaa-5aaa-aaaa-aaaaaaaaaaaa")
    class_fqn = "aware_demo.default.default.Device"
    class_config = ClassConfig(
        class_fqn=class_fqn,
        name="Device",
        is_base=True,
    )
    return ObjectConfigGraph(
        id=graph_id,
        name="demo_runtime",
        hash="runtime-hash",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=class_fqn,
                class_config=class_config,
                object_config_graph_id=graph_id,
            )
        ],
    )


def test_language_renderer_policies_feed_runtime_graph_to_runtime_handler_impls() -> (
    None
):
    runtime_graph = _build_demo_runtime_graph()

    policies = language_service_module._language_renderer_policies(
        runtime_graph=runtime_graph
    )

    assert policies["runtime_handlers_impl"]["stable_ids_source_graph"] is runtime_graph
    assert policies["runtime_handlers"]["stable_ids_source_graph"] is runtime_graph


def _build_public_dto_relationship_graph() -> ObjectConfigGraph:
    graph_id = UUID("dddddddd-dddd-5ddd-dddd-dddddddddddd")
    parent = ClassConfig(
        class_fqn="aware_demo.default.default.Parent",
        name="Parent",
        is_base=True,
    )
    lazy_child = ClassConfig(
        class_fqn="aware_demo.default.default.LazyChild",
        name="LazyChild",
        is_base=True,
    )
    eager_child = ClassConfig(
        class_fqn="aware_demo.default.default.EagerChild",
        name="EagerChild",
        is_base=True,
    )
    lazy_attr = _class_ref_attr(parent, "lazy_child", lazy_child)
    eager_attr = _class_ref_attr(parent, "eager_child", eager_child)
    parent.class_config_attribute_configs = [
        ClassConfigAttributeConfig(
            class_config_id=parent.id,
            attribute_config=lazy_attr,
            attribute_config_id=lazy_attr.id,
            position=0,
        ),
        ClassConfigAttributeConfig(
            class_config_id=parent.id,
            attribute_config=eager_attr,
            attribute_config_id=eager_attr.id,
            position=1,
        ),
    ]
    lazy_relationship = _relationship_for_attr(
        source=parent,
        target=lazy_child,
        attr=lazy_attr,
        key="Parent.lazy_child",
        strategy=None,
    )
    eager_relationship = _relationship_for_attr(
        source=parent,
        target=eager_child,
        attr=eager_attr,
        key="Parent.eager_child",
        strategy=ClassConfigRelationshipSideLoadingStrategy.eager,
    )
    parent.class_config_relationships = [lazy_relationship, eager_relationship]
    return ObjectConfigGraph(
        id=graph_id,
        name="demo_source",
        hash="source-hash",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=parent.class_fqn,
                class_config=parent,
                object_config_graph_id=graph_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=lazy_child.class_fqn,
                class_config=lazy_child,
                object_config_graph_id=graph_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=eager_child.class_fqn,
                class_config=eager_child,
                object_config_graph_id=graph_id,
            ),
        ],
    )


def _class_ref_attr(
    owner: ClassConfig,
    name: str,
    target: ClassConfig,
) -> AttributeConfig:
    descriptor = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config=target,
        class_config_id=target.id,
    )
    return AttributeConfig(
        owner_key=owner.class_fqn,
        name=name,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )


def _relationship_for_attr(
    *,
    source: ClassConfig,
    target: ClassConfig,
    attr: AttributeConfig,
    key: str,
    strategy: ClassConfigRelationshipSideLoadingStrategy | None,
) -> ClassConfigRelationship:
    relationship = ClassConfigRelationship(
        class_config_id=source.id,
        target_class_config_id=target.id,
        relationship_key=key,
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
        forward_loading_strategy=strategy,
    )
    relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=relationship.id,
            attribute_config_id=attr.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]
    return relationship


def _class_by_name(graph: ObjectConfigGraph, name: str) -> ClassConfig:
    for node in graph.object_config_graph_nodes:
        class_config = node.class_config
        if class_config is not None and class_config.name == name:
            return class_config
    raise AssertionError(f"Missing class {name}")


def _attr_by_name(class_config: ClassConfig, name: str) -> AttributeConfig:
    for link in class_config.class_config_attribute_configs:
        if link.attribute_config.name == name:
            return link.attribute_config
    raise AssertionError(f"Missing attribute {class_config.name}.{name}")


def _primitive_desc(base: CodePrimitiveBaseType) -> AttributeTypeDescriptor:
    primitive_type = build_code_primitive_type(base_type=base)
    primitive_config = PrimitiveConfig(
        primitive_type=primitive_type,
        primitive_type_id=primitive_type.id,
    )
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
    )


def _build_constructor_runtime_graph() -> ObjectConfigGraph:
    graph = _build_demo_runtime_graph()
    class_config = graph.object_config_graph_nodes[0].class_config
    assert class_config is not None
    build_function = FunctionConfig(
        owner_key=class_config.class_fqn,
        name="build",
        is_async=True,
        kind=FunctionKind.class_,
    )
    key_attribute = AttributeConfig(
        owner_key=(
            f"{build_function.owner_key}.{build_function.name}::"
            f"{FunctionAttributeType.input.value}"
        ),
        name="key",
        is_public=True,
        is_required=True,
        is_unique=True,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.string),
    )
    build_function.function_config_attribute_configs = [
        FunctionConfigAttributeConfig(
            function_config_id=build_function.id,
            attribute_config=key_attribute,
            attribute_config_id=key_attribute.id,
            name=key_attribute.name,
            type=FunctionAttributeType.input,
            position=0,
            is_identity_key=True,
        )
    ]
    class_config.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=class_config.id,
            function_config_id=build_function.id,
            function_config=build_function,
            is_public=True,
            is_constructor=True,
            position=0,
        )
    ]
    return graph


def _build_instance_runtime_graph() -> ObjectConfigGraph:
    graph = _build_demo_runtime_graph()
    class_config = graph.object_config_graph_nodes[0].class_config
    assert class_config is not None
    refresh_function = FunctionConfig(
        owner_key=class_config.class_fqn,
        name="refresh",
        is_async=True,
        kind=FunctionKind.instance,
    )
    class_config.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=class_config.id,
            function_config_id=refresh_function.id,
            function_config=refresh_function,
            is_public=True,
            is_constructor=False,
            position=0,
        )
    ]
    return graph


def _build_external_runtime_graph() -> ObjectConfigGraph:
    graph_id = UUID("bbbbbbbb-bbbb-5bbb-bbbb-bbbbbbbbbbbb")
    class_fqn = "dep_demo.default.default.ExternalDevice"
    class_config = ClassConfig(
        class_fqn=class_fqn,
        name="ExternalDevice",
        is_base=True,
    )
    return ObjectConfigGraph(
        id=graph_id,
        name="dependency_runtime",
        hash="dependency-runtime-hash",
        fqn_prefix="dep_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=class_fqn,
                class_config=class_config,
                object_config_graph_id=graph_id,
            )
        ],
    )


def _build_external_enum_runtime_graph() -> tuple[ObjectConfigGraph, EnumConfig]:
    graph_id = UUID("cccccccc-cccc-5ccc-cccc-cccccccccccc")
    node_id = UUID("dddddddd-dddd-5ddd-dddd-dddddddddddd")
    enum_fqn = "dep_demo.enums.ExternalKind"
    enum_config = EnumConfig(
        enum_fqn=enum_fqn,
        name="ExternalKind",
        object_config_graph_node_id=node_id,
    )
    return (
        ObjectConfigGraph(
            id=graph_id,
            name="dependency_runtime",
            hash="dependency-runtime-hash",
            fqn_prefix="dep_demo",
            language=CodeLanguage.aware,
            object_config_graph_nodes=[
                ObjectConfigGraphNode(
                    id=node_id,
                    type=ObjectConfigGraphNodeType.enum,
                    node_key=enum_fqn,
                    enum_config=enum_config,
                    object_config_graph_id=graph_id,
                    layouts=[
                        ObjectConfigGraphNodeLayout(
                            object_config_graph_node_id=node_id,
                            relative_path="enums/external_kind.aware",
                            source_position=0,
                        )
                    ],
                )
            ],
        ),
        enum_config,
    )


def _build_demo_runtime_graph_with_external_enum(
    external_enum: EnumConfig,
) -> ObjectConfigGraph:
    graph = _build_demo_runtime_graph()
    class_config = graph.object_config_graph_nodes[0].class_config
    assert class_config is not None
    type_descriptor = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.enum,
        enum_config=external_enum,
        enum_config_id=external_enum.id,
    )
    attribute_config = AttributeConfig(
        owner_key=class_config.class_fqn,
        name="kind",
        is_public=True,
        is_required=False,
        type_descriptor=type_descriptor,
        type_descriptor_id=type_descriptor.id,
    )
    class_config.class_config_attribute_configs = [
        ClassConfigAttributeConfig(
            class_config_id=class_config.id,
            attribute_config=attribute_config,
            attribute_config_id=attribute_config.id,
            position=0,
        )
    ]
    return graph


def test_meta_semantic_contract_declares_language_materialization_outputs_by_provider_key() -> (
    None
):
    semantic_contract_source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/semantic_contract.py"
    ).read_text(encoding="utf-8")
    assert "python.meta_runtime_handlers_provider" not in semantic_contract_source

    outputs = AwareModulePluginRegistry.semantic_materialization_artifact_outputs_for_provider_key(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        required_for="workspace_revision",
    )

    assert {item.output_key for item in outputs} == {
        META_LANGUAGE_MATERIALIZATION_GENERATED_FILES_OUTPUT_KEY,
        META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY,
        META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY,
    }
    lifecycle_output = {item.output_key: item for item in outputs}[
        META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY
    ]
    assert lifecycle_output.artifact_path_pattern == (
        "{materialization_root}/lifecycle_receipts/**/"
        "ocg.language_materialization.lifecycle.json"
    )
    assert lifecycle_output.manifest_relpath is None
    runtime_index_outputs = AwareModulePluginRegistry.semantic_materialization_artifact_outputs_for_provider_key(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        required_for="runtime_index",
    )
    assert [item.output_key for item in runtime_index_outputs] == [
        META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY,
        META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY,
    ]
    for plugin in AwareModulePluginRegistry.get_builtin_code_language_plugins():
        if plugin.language == CodeLanguage.python:
            python_outputs = {
                item.output_key: item
                for item in plugin.materialization_artifact_outputs
            }
            break
    else:
        raise AssertionError("Expected Python Code language plugin")
    meta_handler_output = python_outputs[PYTHON_META_RUNTIME_HANDLERS_OUTPUT_KEY]
    assert meta_handler_output.artifact_role == "meta_runtime_handler_provider"
    assert meta_handler_output.path_templates == (
        "handlers/_generated/meta_handlers.py",
    )
    assert meta_handler_output.provider_payload["renderer_kind"] == (
        "runtime_handlers_meta"
    )

    delta_outputs = AwareModulePluginRegistry.semantic_materialization_code_package_delta_outputs_for_provider_key(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        required_for="local_checkout",
    )
    assert [item.output_key for item in delta_outputs] == [
        META_LANGUAGE_MATERIALIZATION_CODE_PACKAGE_DELTAS_OUTPUT_KEY,
    ]
    assert delta_outputs[0].provider_payload == {
        "receipt_field": "generated_code_package_deltas",
        "target_language": "plugin",
    }


def test_language_plugin_materialization_uses_generic_runtime_to_language_boundary(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_builtin_aware_plugin()
    _register_fake_sql_plugin()
    source_graph = ObjectConfigGraph(
        name="demo_runtime",
        hash="runtime-hash",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
    )

    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=source_graph,
            target_language_plugin_id=CodeLanguage.sql,
            source_is_runtime=True,
        )
    )

    assert result.target_language_plugin_id == CodeLanguage.sql
    assert result.source_graph_hash == "runtime-hash"
    assert result.runtime_graph_hash == "runtime-hash"
    assert result.language_graph_hash == "runtime-hash:sql"
    assert result.runtime_graph.language == CodeLanguage.aware
    assert result.language_graph.language == CodeLanguage.sql
    assert result.generated_files == ()
    assert result.package_outputs == ()
    assert result.status == "succeeded"
    assert result.metrics["target_language_plugin_id"] == "sql"
    assert _FakeRuntimeToSqlTransformer.last_kwargs is not None
    assert "namespace_by_code_id" in _FakeRuntimeToSqlTransformer.last_kwargs
    step_by_name = {step.name: step for step in result.tool_steps}
    assert set(step_by_name) >= {
        "derive_runtime_graph",
        "runtime_to_language",
        "runtime_to_language.primary.cache_miss",
        "runtime_to_language.primary.namespace_index",
        "runtime_to_language.primary.transformer_resolve",
        "runtime_to_language.primary.clone_graph",
        "runtime_to_language.primary.transform",
        "runtime_to_language.primary.copy_runtime_surfaces",
        "runtime_to_language.primary.generated_manifest",
        "runtime_to_language.primary.cache_store",
    }
    assert (
        step_by_name["runtime_to_language.primary.transform"].details[
            "timing_parent_step"
        ]
        == "runtime_to_language"
    )


def test_language_plugin_materialization_reports_subphase_progress(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_builtin_aware_plugin()
    _register_fake_sql_plugin()
    source_graph = ObjectConfigGraph(
        name="demo_runtime",
        hash="runtime-hash",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
    )
    progress_events: list[dict[str, object]] = []

    def progress_callback(payload: Mapping[str, object]) -> None:
        progress_events.append(dict(payload))

    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=source_graph,
            target_language_plugin_id=CodeLanguage.sql,
            source_is_runtime=True,
            progress_callback=progress_callback,
        )
    )

    assert result.status == "succeeded"
    subphase_statuses = [
        (
            cast(Mapping[str, object], event["detail_payload"])["subphase_name"],
            event["status"],
        )
        for event in progress_events
    ]
    assert subphase_statuses[0] == ("derive_runtime_graph", "running")
    assert ("derive_runtime_graph.service", "running") in subphase_statuses
    assert ("derive_runtime_graph.ensure_plugins", "running") in subphase_statuses
    assert ("derive_runtime_graph.external_runtime_graphs", "running") in (
        subphase_statuses
    )
    assert ("derive_runtime_graph.derive_graph", "running") in subphase_statuses
    assert ("derive_runtime_graph.rebind_relationship_targets", "running") in (
        subphase_statuses
    )
    assert ("derive_runtime_graph.attach_relationships", "running") in (
        subphase_statuses
    )
    assert ("derive_runtime_graph.derive_opgs", "running") in subphase_statuses
    assert ("derive_runtime_graph", "succeeded") in subphase_statuses
    assert ("runtime_to_language", "running") in subphase_statuses
    assert ("runtime_to_language", "succeeded") in subphase_statuses
    assert ("receipt_assembly", "running") in subphase_statuses
    assert subphase_statuses[-1] == ("receipt_assembly", "succeeded")
    derive_graph_running = next(
        event
        for event in progress_events
        if cast(Mapping[str, object], event["detail_payload"])["subphase_name"]
        == "derive_runtime_graph.derive_graph"
        and event["status"] == "running"
    )
    derive_graph_detail = cast(
        Mapping[str, object],
        derive_graph_running["detail_payload"],
    )
    assert derive_graph_detail["source_graph_hash"] == "runtime-hash"
    assert derive_graph_detail["source_is_runtime"] is True
    succeeded_events = [
        event for event in progress_events if event["status"] == "succeeded"
    ]
    assert all(isinstance(event.get("duration_s"), float) for event in succeeded_events)
    assert result.metrics["runtime_to_language_cache"] == {
        "entry_count": 1,
        "hit_count": 0,
        "miss_count": 1,
        "store_count": 1,
        "deep_copy_hits": True,
    }


def test_language_plugin_materialization_reports_source_to_runtime_transform_failure_progress(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_builtin_aware_plugin()
    _register_fake_sql_plugin()
    progress_events: list[dict[str, object]] = []

    def progress_callback(payload: Mapping[str, object]) -> None:
        progress_events.append(dict(payload))

    with pytest.raises(ValueError, match="missing namespace"):
        materialize_object_config_graph_via_language_plugin(
            LanguagePluginMaterializationRequest(
                source_graph=_build_demo_runtime_graph(),
                target_language_plugin_id=CodeLanguage.sql,
                source_is_runtime=False,
                progress_callback=progress_callback,
            )
        )

    subphase_statuses = [
        (
            cast(Mapping[str, object], event["detail_payload"])["subphase_name"],
            event["status"],
        )
        for event in progress_events
    ]
    assert (
        "derive_runtime_graph.language_to_runtime.clone_source_graph",
        "running",
    ) in subphase_statuses
    assert (
        "derive_runtime_graph.language_to_runtime.namespace_index",
        "running",
    ) in subphase_statuses
    assert (
        "derive_runtime_graph.language_to_runtime.transformer_resolve",
        "running",
    ) in subphase_statuses
    assert (
        "derive_runtime_graph.language_to_runtime.transform",
        "running",
    ) in subphase_statuses
    assert (
        "derive_runtime_graph.language_to_runtime.transform",
        "failed",
    ) in subphase_statuses
    assert ("derive_runtime_graph.service", "failed") in subphase_statuses
    assert ("derive_runtime_graph", "failed") in subphase_statuses
    transform_running = next(
        event
        for event in progress_events
        if cast(Mapping[str, object], event["detail_payload"])["subphase_name"]
        == "derive_runtime_graph.language_to_runtime.transform"
        and event["status"] == "running"
    )
    transform_detail = cast(
        Mapping[str, object],
        transform_running["detail_payload"],
    )
    assert transform_detail["source_language"] == "aware"
    assert transform_detail["external_graph_count"] == 0
    transform_failed = next(
        event
        for event in progress_events
        if cast(Mapping[str, object], event["detail_payload"])["subphase_name"]
        == "derive_runtime_graph.language_to_runtime.transform"
        and event["status"] == "failed"
    )
    failed_detail = cast(Mapping[str, object], transform_failed["detail_payload"])
    assert failed_detail["error_type"] == "ValueError"


def test_language_plugin_materialization_records_renderer_phase_timings(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_builtin_aware_plugin()
    _register_fake_sql_plugin()
    _FakeSqlRendererLanguage.emit_render_phase_timings = True
    progress_events: list[dict[str, object]] = []

    def progress_callback(payload: Mapping[str, object]) -> None:
        progress_events.append(dict(payload))

    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=_build_demo_runtime_graph(),
            target_language_plugin_id=CodeLanguage.sql,
            source_is_runtime=True,
            output_root=tmp_path / "materialized_sql",
            emit_files=True,
            progress_callback=progress_callback,
        )
    )

    step_by_name = {step.name: step for step in result.tool_steps}
    assert step_by_name["render.default.render_graph"].duration_s >= 0.0
    assert step_by_name["render.default.writer_assembly"].duration_s == 0.125
    assert step_by_name["render.default.write_compare"].duration_s == 0.25
    assert step_by_name["render.default.writer_assembly"].details == {
        "timing_scope": "substep",
        "timing_parent_step": "render",
        "graph_role": "all",
        "renderer_name": "default",
        "renderer_phase_name": "writer_assembly",
    }
    render_events = {
        cast(Mapping[str, object], event["detail_payload"])["subphase_name"]: event[
            "duration_s"
        ]
        for event in progress_events
        if cast(Mapping[str, object], event["detail_payload"])[
            "subphase_name"
        ].startswith("render.default.")
    }
    assert render_events["render.default.render_graph"] >= 0.0
    assert render_events["render.default.write_compare"] == 0.25
    assert render_events["render.default.writer_assembly"] == 0.125


def test_graph_materialization_transform_service_exposes_stage_refs(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_builtin_aware_plugin()
    _register_fake_sql_plugin()
    source_graph = _build_demo_runtime_graph()

    result = GraphMaterializationTransformService().transform(
        GraphMaterializationTransformRequest(
            source_graph=source_graph,
            target_language_plugin_id=CodeLanguage.sql,
            source_stage="canonical_runtime_graph",
            target_stage="language_graph",
        )
    )

    assert result.source_stage == "canonical_runtime_graph"
    assert result.target_stage == "language_graph"
    assert result.source_graph_ref == "runtime-hash"
    assert result.runtime_graph.language == CodeLanguage.aware
    assert result.runtime_graph_ref is not None
    assert result.require_language_graph().language == CodeLanguage.sql
    assert result.language_graph_ref is not None
    step_by_name = {step.name: step for step in result.tool_steps}
    assert set(step_by_name) >= {
        "derive_runtime_graph",
        "runtime_to_language",
        "runtime_to_language.primary.cache_miss",
        "runtime_to_language.primary.transform",
        "runtime_to_language.primary.cache_store",
    }
    assert (
        step_by_name["runtime_to_language.primary.transform"].details["timing_scope"]
        == "substep"
    )
    assert _FakeRuntimeToSqlTransformer.last_kwargs is not None
    assert "namespace_by_code_id" in _FakeRuntimeToSqlTransformer.last_kwargs


def test_graph_materialization_transform_service_derives_public_dto_language_graph(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_sql_plugin()
    source_graph = _build_demo_runtime_graph().model_copy(
        update={"hash": "dto-source-hash"}
    )
    _FakeRuntimeToSqlTransformer.calls = []
    _FakeRuntimeToSqlTransformer.last_kwargs = None

    result = GraphMaterializationTransformService().transform(
        GraphMaterializationTransformRequest(
            source_graph=source_graph,
            target_language_plugin_id=CodeLanguage.sql,
            source_stage="source_graph",
            target_stage="language_graph",
            graph_profile="public_dto",
        )
    )

    assert result.require_language_graph() is not source_graph
    assert result.runtime_graph is source_graph
    assert result.source_graph_ref == "dto-source-hash"
    assert result.runtime_graph_ref is None
    assert result.language_graph_ref == "dto-source-hash"
    assert result.metrics["canonical_runtime_graph_derived"] is False
    assert {step.name for step in result.tool_steps} == {"derive_public_dto_graph"}
    assert _FakeRuntimeToSqlTransformer.last_kwargs is None
    assert _FakeRuntimeToSqlTransformer.calls == []


def test_graph_materialization_transform_service_applies_public_dto_loading_policy(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_sql_plugin()
    source_graph = _build_public_dto_relationship_graph()

    result = GraphMaterializationTransformService().transform(
        GraphMaterializationTransformRequest(
            source_graph=source_graph,
            target_language_plugin_id=CodeLanguage.sql,
            source_stage="source_graph",
            target_stage="language_graph",
            graph_profile="public_dto",
        )
    )

    source_parent = _class_by_name(source_graph, "Parent")
    source_lazy_attr = _attr_by_name(source_parent, "lazy_child")
    assert source_lazy_attr.is_required is True
    assert source_lazy_attr.default_value is None

    language_graph = result.require_language_graph()
    language_parent = _class_by_name(language_graph, "Parent")
    lazy_attr = _attr_by_name(language_parent, "lazy_child")
    eager_attr = _attr_by_name(language_parent, "eager_child")
    assert lazy_attr.is_required is False
    assert lazy_attr.default_value == "null"
    assert lazy_attr.exclude_serialization is False
    assert eager_attr.is_required is True
    assert eager_attr.default_value is None

    assert result.metrics["public_dto_relationship_attrs_seen"] == 2
    assert result.metrics["public_dto_lazy_relationship_attrs_lowered"] == 1
    assert result.metrics["public_dto_eager_relationship_attrs_preserved"] == 1
    assert _FakeRuntimeToSqlTransformer.last_kwargs is None
    assert _FakeRuntimeToSqlTransformer.calls == []


def test_graph_materialization_transform_service_rejects_language_graph_as_runtime(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_sql_plugin()
    language_graph = _build_demo_runtime_graph().model_copy(
        update={"language": CodeLanguage.sql}
    )

    with pytest.raises(ValueError, match="canonical_runtime_graph"):
        GraphMaterializationTransformService().transform(
            GraphMaterializationTransformRequest(
                source_graph=language_graph,
                target_language_plugin_id=CodeLanguage.sql,
                source_stage="canonical_runtime_graph",
                target_stage="language_graph",
            )
        )


def test_prepared_language_materialization_render_runs_inside_meta(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_sql_plugin()
    output_root = tmp_path / "prepared_sql"
    language_graph = _build_demo_runtime_graph().model_copy(
        update={"language": CodeLanguage.sql, "hash": "runtime-hash:sql"}
    )
    external_graph = _build_external_runtime_graph()

    result = render_language_materialization(
        LanguageMaterializationRenderRequest(
            target_language_plugin_id=CodeLanguage.sql,
            language_graph=language_graph,
            output_root=output_root,
            layout_strategy=_FakeSqlLayoutStrategy(output_root),
            language_external_graphs=(external_graph,),
            import_overrides={"dep_demo": "package:dep_demo"},
        )
    )

    assert result.renderer_names == ("default",)
    assert result.renderer_file_counts == {"default": 2}
    assert result.renderer_warning_counts == {"default": 0}
    assert result.warnings == ()
    assert sorted(path.relative_to(output_root) for path in result.written_files) == [
        Path("classes/Device.sql"),
        Path("rendered/demo.sql"),
    ]
    assert sorted(path.relative_to(output_root) for path in result.changed_files) == [
        Path("classes/Device.sql"),
        Path("rendered/demo.sql"),
    ]
    assert (output_root / "rendered" / "demo.sql").read_text(encoding="utf-8") == (
        "-- rendered by fake sql plugin\nselect 'demo_runtime' as graph_name;\n"
    )
    assert _FakeSqlRendererLanguage.last_external_graphs == (external_graph,)
    assert _FakeSqlRendererLanguage.last_import_overrides == {
        "dep_demo": "package:dep_demo"
    }

    second = render_language_materialization(
        LanguageMaterializationRenderRequest(
            target_language_plugin_id=CodeLanguage.sql,
            language_graph=language_graph,
            output_root=output_root,
            layout_strategy=_FakeSqlLayoutStrategy(output_root),
            language_external_graphs=(external_graph,),
            import_overrides={"dep_demo": "package:dep_demo"},
        )
    )

    assert sorted(path.relative_to(output_root) for path in second.written_files) == [
        Path("classes/Device.sql"),
        Path("rendered/demo.sql"),
    ]
    assert second.changed_files == ()


def test_prepared_language_materialization_render_reports_renderer_phase_timings(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_sql_plugin()
    _FakeSqlRendererLanguage.emit_render_phase_timings = True
    output_root = tmp_path / "prepared_sql"
    language_graph = _build_demo_runtime_graph().model_copy(
        update={"language": CodeLanguage.sql, "hash": "runtime-hash:sql"}
    )

    result = render_language_materialization(
        LanguageMaterializationRenderRequest(
            target_language_plugin_id=CodeLanguage.sql,
            language_graph=language_graph,
            output_root=output_root,
            layout_strategy=_FakeSqlLayoutStrategy(output_root),
        )
    )

    assert set(result.renderer_phase_timings) == {"default"}
    default_timings = result.renderer_phase_timings["default"]
    assert default_timings["write_compare"] == 0.25
    assert default_timings["writer_assembly"] == 0.125
    assert isinstance(default_timings["render_graph"], float)
    assert default_timings["render_graph"] >= 0.0


def test_prepared_python_render_canonicalizes_before_changed_detection(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_python_plugin()
    output_root = tmp_path / "prepared_python"
    language_graph = _build_demo_runtime_graph().model_copy(
        update={"language": CodeLanguage.python, "hash": "runtime-hash:python"}
    )

    first = render_language_materialization(
        LanguageMaterializationRenderRequest(
            target_language_plugin_id=CodeLanguage.python,
            language_graph=language_graph,
            output_root=output_root,
            layout_strategy=_FakePythonLayoutStrategy(output_root),
        )
    )

    rendered_path = output_root / "classes" / "Device.py"
    assert rendered_path.read_text(encoding="utf-8") == ('value = {"name": "demo"}\n')
    assert first.changed_files == (rendered_path.resolve(),)

    second = render_language_materialization(
        LanguageMaterializationRenderRequest(
            target_language_plugin_id=CodeLanguage.python,
            language_graph=language_graph,
            output_root=output_root,
            layout_strategy=_FakePythonLayoutStrategy(output_root),
        )
    )

    assert second.written_files == (rendered_path.resolve(),)
    assert second.changed_files == ()


def test_prepared_python_render_skips_canonicalizer_when_raw_source_matches(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_python_plugin()
    _FakePythonRendererLanguage.emit_black_stable_source = True
    output_root = tmp_path / "prepared_python"
    language_graph = _build_demo_runtime_graph().model_copy(
        update={"language": CodeLanguage.python, "hash": "runtime-hash:python"}
    )

    first = render_language_materialization(
        LanguageMaterializationRenderRequest(
            target_language_plugin_id=CodeLanguage.python,
            language_graph=language_graph,
            output_root=output_root,
            layout_strategy=_FakePythonLayoutStrategy(output_root),
        )
    )

    rendered_path = output_root / "classes" / "Device.py"
    assert first.changed_files == (rendered_path.resolve(),)
    assert rendered_path.read_text(encoding="utf-8") == ('value = {"name": "demo"}\n')

    canonicalizer_calls: list[Path] = []

    def _unexpected_canonicalizer(*, relative_path: Path, source: str) -> str:
        _ = source
        canonicalizer_calls.append(relative_path)
        raise AssertionError("raw-matching generated Python source must skip Black")

    monkeypatch.setattr(
        renderer_language_module,
        "_canonicalize_python_generated_source",
        _unexpected_canonicalizer,
    )

    second = render_language_materialization(
        LanguageMaterializationRenderRequest(
            target_language_plugin_id=CodeLanguage.python,
            language_graph=language_graph,
            output_root=output_root,
            layout_strategy=_FakePythonLayoutStrategy(output_root),
        )
    )

    assert second.written_files == (rendered_path.resolve(),)
    assert second.changed_files == ()
    assert canonicalizer_calls == []


def test_language_plugin_materialization_skips_post_steps_for_unchanged_rendered_files(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_sql_plugin()
    output_root = tmp_path / "materialized_sql"
    calls: list[tuple[Path, ...]] = []

    def _fake_post_steps(
        request: Any,
    ) -> SimpleNamespace:
        calls.append(
            tuple(Path(path).resolve() for path in request.generated_file_paths)
        )
        return SimpleNamespace(
            execution_results=(),
            receipts=(),
            metrics={"fake_post_step_target_count": len(request.generated_file_paths)},
            warnings=(),
        )

    monkeypatch.setattr(
        language_service_module,
        "execute_language_materialization_post_steps",
        _fake_post_steps,
    )
    request = LanguagePluginMaterializationRequest(
        source_graph=_build_demo_runtime_graph(),
        target_language_plugin_id=CodeLanguage.sql,
        source_is_runtime=True,
        output_root=output_root,
        emit_files=True,
    )

    first = materialize_object_config_graph_via_language_plugin(request)

    assert calls
    assert len(calls[0]) == first.metrics["generated_file_count"]

    calls.clear()
    second = materialize_object_config_graph_via_language_plugin(request)

    assert calls == []
    assert second.metrics["post_step_receipt_count"] == 0
    post_step_metrics = cast(dict[str, object], second.metrics["post_step_metrics"])
    assert post_step_metrics["post_step_candidate_changed_file_count"] == 0
    assert post_step_metrics["post_step_selected_generated_file_count"] == 0
    assert (
        post_step_metrics["post_step_skipped_unchanged_file_count"]
        == second.metrics["generated_file_count"]
    )


def test_python_post_step_selection_catches_unstable_existing_generated_files(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "runtime"
    rendered_path = output_root / "handlers" / "impl" / "code.py"
    rendered_path.parent.mkdir(parents=True)
    rendered_path.write_text('value = {"name": "demo"}\n', encoding="utf-8")
    generated_file = language_service_module.LanguageMaterializationGeneratedFile(
        path=Path("handlers/impl/code.py"),
        output_kind="source_code",
        producer_step="render",
        sha256="stable-sha",
        size_bytes=rendered_path.stat().st_size,
        source_graph_ref="runtime-hash:python",
        renderer_name="runtime_handlers_impl",
    )
    request = LanguagePluginMaterializationRequest(
        source_graph=_build_demo_runtime_graph(),
        target_language_plugin_id=CodeLanguage.python,
        source_is_runtime=True,
        output_root=output_root,
        import_root="aware_demo",
        materialization_source="runtime_handlers",
        renderer_kind="runtime_handlers_impl",
        emit_files=True,
    )

    stable_selection = language_service_module._post_step_generated_files(
        request=request,
        generated_files=(generated_file,),
        candidate_paths=set(),
    )

    assert stable_selection == ()

    rendered_path.write_text("value={'name':'demo'}\n", encoding="utf-8")
    unstable_selection = language_service_module._post_step_generated_files(
        request=request,
        generated_files=(generated_file,),
        candidate_paths=set(),
    )

    assert unstable_selection == (generated_file,)


def test_language_plugin_materialization_emits_stable_plugin_file_receipts(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_builtin_aware_plugin()
    _register_fake_sql_plugin()
    source_graph = ObjectConfigGraph(
        name="demo_runtime",
        hash="runtime-hash",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
    )
    output_root = tmp_path / "materialized_sql"
    request = LanguagePluginMaterializationRequest(
        source_graph=source_graph,
        target_language_plugin_id=CodeLanguage.sql,
        source_is_runtime=True,
        output_root=output_root,
        emit_files=True,
    )

    first = materialize_object_config_graph_via_language_plugin(request)
    second = materialize_object_config_graph_via_language_plugin(request)

    assert (output_root / "rendered" / "demo.sql").read_text(encoding="utf-8") == (
        "-- rendered by fake sql plugin\nselect 'demo_runtime' as graph_name;\n"
    )
    assert [item.path for item in first.generated_files] == [Path("rendered/demo.sql")]
    assert first.generated_files == second.generated_files
    generated_file = first.generated_files[0]
    assert generated_file.output_kind == "source_code"
    assert generated_file.producer_step == "render"
    assert generated_file.renderer_name == "default"
    assert generated_file.source_graph_ref == "runtime-hash:sql"
    assert len(first.manifest_snapshots) == 1
    assert first.manifest_snapshots[0].sha256 == second.manifest_snapshots[0].sha256
    snapshot = first.manifest_snapshots[0]
    assert snapshot.snapshot_key == "language_materialization_manifest_snapshot"
    assert snapshot.source_graph_ref == "runtime-hash"
    assert snapshot.runtime_graph_ref == "runtime-hash"
    assert snapshot.language_graph_ref == "runtime-hash:sql"
    assert "workspace_revision" in snapshot.required_for
    payload = snapshot.payload
    assert payload["provider_key"] == "aware_meta"
    assert payload["target_language_plugin_id"] == "sql"
    generated_payloads = cast(list[dict[str, object]], payload["generated_files"])
    assert generated_payloads == [
        {
            "path": "rendered/demo.sql",
            "output_kind": "source_code",
            "producer_step": "render",
            "sha256": generated_file.sha256,
            "size_bytes": generated_file.size_bytes,
            "source_graph_ref": "runtime-hash:sql",
            "renderer_name": "default",
        }
    ]
    package_payloads = cast(list[dict[str, object]], payload["package_outputs"])
    assert package_payloads[0]["output_root_mode"] == "package_root"
    declared_payloads = cast(
        list[dict[str, object]],
        payload["plugin_declared_outputs"],
    )
    assert declared_payloads[0]["output_key"] == "sql.test_manifest"
    assert declared_payloads[0]["status"] == "declared"
    assert first.metrics["generated_file_count"] == 1
    assert second.metrics["generated_file_count"] == 1
    assert first.metrics["plugin_declared_output_count"] == 1
    assert first.metrics["manifest_snapshot_count"] == 1
    assert {step.name for step in first.tool_steps} >= {
        "derive_runtime_graph",
        "runtime_to_language",
        "render",
    }


def test_language_plugin_materialization_passes_runtime_graph_to_stable_ids_renderer(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_builtin_aware_plugin()
    _register_fake_sql_plugin(include_stable_ids=True)

    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=_build_demo_runtime_graph(),
            target_language_plugin_id=CodeLanguage.sql,
            source_is_runtime=True,
            output_root=tmp_path / "materialized_sql",
            stable_ids_ownership="compiler",
            stable_ids_resolution_policy="class_strict",
            emit_files=True,
        )
    )

    assert result.status == "succeeded"
    assert result.runtime_graph_hash == "runtime-hash"
    assert result.language_graph_hash == "runtime-hash:sql"
    assert {item.path for item in result.generated_files} >= {
        Path("rendered/demo.sql"),
        Path("rendered/stable_ids.sql"),
    }
    assert _FakeStableIdsRendererLanguage.last_policy is not None
    assert (
        _FakeStableIdsRendererLanguage.last_policy["stable_ids_ownership"] == "compiler"
    )
    assert (
        _FakeStableIdsRendererLanguage.last_policy["stable_ids_resolution_policy"]
        == "class_strict"
    )
    assert _FakeStableIdsRendererLanguage.last_source_graph_hash == "runtime-hash"
    assert _FakeStableIdsRendererLanguage.last_bound_graph_hash == "runtime-hash:sql"


def test_language_plugin_materialization_runs_python_plugin_validation_gate(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    output_root = tmp_path / "materialized_python"
    request = LanguagePluginMaterializationRequest(
        source_graph=_build_demo_runtime_graph(),
        target_language_plugin_id=CodeLanguage.python,
        source_is_runtime=True,
        output_root=output_root,
        import_root="aware_demo",
        materialization_source="ontology",
        source_code_package_id=UUID("11111111-1111-4111-8111-111111111111"),
        object_config_graph_package_id=UUID("22222222-2222-4222-8222-222222222222"),
        object_config_graph_commit_id=UUID("33333333-3333-4333-8333-333333333333"),
        emit_files=True,
        quality_gate_ids=("python.compile.syntax",),
    )

    first = materialize_object_config_graph_via_language_plugin(request)
    second = materialize_object_config_graph_via_language_plugin(request)

    assert first.status == "succeeded"
    assert [item.path for item in first.generated_files] == [
        Path(".aware/materializations/ocg.node_paths.python.json"),
        Path(".aware/materializations/python.models.json"),
        Path("aware_demo/_aware/ocg.node_paths.python.json"),
        Path("aware_demo/_aware/orm.graph.binding.msgpack"),
        Path("aware_demo/_aware/python.bootstrap.json"),
        Path("aware_demo/_aware/python.models.json"),
        Path("aware_demo/default/device.py"),
    ]
    assert first.generated_files == second.generated_files
    assert not list((output_root / "aware_demo").rglob("__pycache__"))
    assert not (output_root / "default" / "device.py").exists()
    assert (output_root / "aware_demo" / "default" / "device.py").is_file()
    assert (output_root / "aware_demo" / "_aware" / "python.bootstrap.json").read_text(
        encoding="utf-8"
    ) == (
        "{\n"
        '  "dependency_import_roots": [],\n'
        '  "modules": [\n'
        '    "aware_demo.default.device"\n'
        "  ],\n"
        '  "package_prefix": "aware_demo",\n'
        '  "version": "v1"\n'
        "}\n"
    )
    models_payload = json.loads(
        (output_root / "aware_demo" / "_aware" / "python.models.json").read_text(
            encoding="utf-8"
        )
    )
    language_node = first.language_graph.object_config_graph_nodes[0]
    class_config = language_node.class_config
    assert class_config is not None
    assert models_payload["language"] == "python"
    assert models_payload["classes"] == [
        {
            "class_config_id": str(class_config.id),
            "module": "aware_demo.default.device",
            "name": "Device",
            "aware_class_ref": "aware_demo.Device",
            "functions": [],
        }
    ]
    assert models_payload["enums"] == []
    node_paths_payload = json.loads(
        (
            output_root / "aware_demo" / "_aware" / "ocg.node_paths.python.json"
        ).read_text(encoding="utf-8")
    )
    assert node_paths_payload == {
        "language": "python",
        "nodes": [
            {
                "node_id": str(language_node.id),
                "node_type": "class",
                "entity_id": str(class_config.id),
                "relative_path": "default/device.py",
            }
        ],
    }
    assert (
        output_root / "aware_demo" / "_aware" / "orm.graph.binding.msgpack"
    ).stat().st_size > 0
    step_by_name = {step.name: step for step in first.tool_steps}
    validation_step = step_by_name["quality_gate:python.compile.syntax"]
    assert validation_step.status == "succeeded"
    assert validation_step.details["target_count"] == 1
    assert validation_step.details["returncode"] == 0
    assert first.metrics["quality_gate_count"] == 1
    assert [item.package_name for item in first.package_outputs] == ["aware-demo"]
    artifact_output_by_key = {item.output_key: item for item in first.artifact_outputs}
    generated_output = artifact_output_by_key[
        META_LANGUAGE_MATERIALIZATION_GENERATED_FILES_OUTPUT_KEY
    ]
    assert generated_output.generated_file_refs == (
        Path("aware_demo/default/device.py"),
    )
    assert generated_output.provider_key == "aware_meta"
    package_output = artifact_output_by_key[
        META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY
    ]
    assert package_output.package_output_refs == ("aware-demo",)
    assert "runtime_index" in package_output.required_for
    assert first.metrics["package_output_count"] == 1
    assert first.metrics["artifact_output_count"] == 2
    assert first.metrics["ownership_receipt_count"] == len(first.ownership_receipts)
    assert first.metrics["generated_file_count"] == 7
    assert first.metrics["plugin_declared_output_produced_file_count"] == 6
    assert first.metrics["plugin_declared_output_count"] == 4
    assert first.metrics["manifest_snapshot_count"] == 1
    ownership_by_output = {
        (item.output_key, item.path.as_posix() if item.path is not None else ""): item
        for item in first.ownership_receipts
    }
    models_receipt = ownership_by_output[
        (
            "python.models_manifest",
            (output_root / "aware_demo" / "_aware" / "python.models.json").as_posix(),
        )
    ]
    assert models_receipt.producer_provider_key == "aware_meta"
    assert models_receipt.semantic_owner == META_OBJECT_CONFIG_GRAPH_OWNER
    assert models_receipt.producer_key == META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY
    assert models_receipt.artifact_family == "ocg_language_materialization"
    assert models_receipt.artifact_role == "runtime_model_index"
    assert models_receipt.status == "available"
    assert models_receipt.digest
    assert (
        models_receipt.size_bytes
        == (output_root / "aware_demo" / "_aware" / "python.models.json").stat().st_size
    )
    assert models_receipt.source_code_package_id == UUID(
        "11111111-1111-4111-8111-111111111111"
    )
    assert models_receipt.object_config_graph_package_id == UUID(
        "22222222-2222-4222-8222-222222222222"
    )
    assert models_receipt.object_config_graph_commit_id == UUID(
        "33333333-3333-4333-8333-333333333333"
    )
    snapshot_receipts = cast(
        list[dict[str, object]],
        first.manifest_snapshots[0].payload["ownership_receipts"],
    )
    snapshot_models_receipt = next(
        item
        for item in snapshot_receipts
        if item["output_key"] == "python.models_manifest"
        and item["path"]
        == (output_root / "aware_demo" / "_aware" / "python.models.json").as_posix()
    )
    assert snapshot_models_receipt["producer_provider_key"] == "aware_meta"
    assert snapshot_models_receipt["source_code_package_id"] == (
        "11111111-1111-4111-8111-111111111111"
    )
    declared_by_key = {item.output_key: item for item in first.plugin_declared_outputs}
    assert {
        "python.models_manifest",
        "python.orm_graph_binding",
        "python.bootstrap_manifest",
        "python.ocg_node_paths",
    }.issubset(declared_by_key)
    assert "python.event_render_catalog" not in declared_by_key
    assert declared_by_key["python.models_manifest"].resolved_paths == (
        Path(".aware/materializations/python.models.json"),
        Path("aware_demo/_aware/python.models.json"),
    )
    assert declared_by_key["python.models_manifest"].status == "materialized"
    assert declared_by_key["python.models_manifest"].generated_file_refs == (
        Path(".aware/materializations/python.models.json"),
        Path("aware_demo/_aware/python.models.json"),
    )
    assert declared_by_key["python.orm_graph_binding"].status == "materialized"
    assert declared_by_key["python.orm_graph_binding"].generated_file_refs == (
        Path("aware_demo/_aware/orm.graph.binding.msgpack"),
    )
    assert declared_by_key["python.ocg_node_paths"].artifact_role == (
        "dependency_import_resolution"
    )
    assert declared_by_key["python.ocg_node_paths"].status == "materialized"
    assert declared_by_key["python.ocg_node_paths"].generated_file_refs == (
        Path(".aware/materializations/ocg.node_paths.python.json"),
        Path("aware_demo/_aware/ocg.node_paths.python.json"),
    )
    assert declared_by_key["python.bootstrap_manifest"].status == "materialized"
    assert declared_by_key["python.bootstrap_manifest"].generated_file_refs == (
        Path("aware_demo/_aware/python.bootstrap.json"),
    )


def test_python_materialization_derives_external_graph_import_overrides(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    external_graph, external_enum = _build_external_enum_runtime_graph()
    unused_external_graph = _build_external_runtime_graph().model_copy(
        deep=True,
        update={
            "id": UUID("eeeeeeee-eeee-5eee-eeee-eeeeeeeeeeee"),
            "name": "unused_dependency_runtime",
            "hash": "unused-dependency-runtime-hash",
            "fqn_prefix": "unused_demo",
        },
    )
    output_root = tmp_path / "materialized_python"

    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=_build_demo_runtime_graph_with_external_enum(external_enum),
            target_language_plugin_id=CodeLanguage.python,
            external_runtime_graphs=(external_graph, unused_external_graph),
            source_is_runtime=True,
            output_root=output_root,
            import_root="aware_demo",
            materialization_source="ontology",
            emit_files=True,
        )
    )

    device_source = (output_root / "aware_demo" / "default" / "device.py").read_text(
        encoding="utf-8"
    )
    assert (
        "from dep_demo_ontology.enums.external_kind import ExternalKind"
        in device_source
    )
    assert "aware_demo.default.external_kind" not in device_source
    assert "aware_meta_ontology.default.external_kind" not in device_source
    bootstrap_payload = json.loads(
        (output_root / "aware_demo" / "_aware" / "python.bootstrap.json").read_text(
            encoding="utf-8"
        )
    )
    assert bootstrap_payload["dependency_import_roots"] == ["dep_demo_ontology"]
    snapshot_payload = result.manifest_snapshots[0].payload
    import_overrides = cast(
        list[dict[str, str]],
        snapshot_payload["import_overrides"],
    )
    assert {
        "source": str(external_enum.id),
        "target": "dep_demo_ontology.enums.external_kind",
    } in import_overrides
    assert not (output_root / "default" / "device.py").exists()


def test_python_materialization_does_not_treat_ontology_fqn_as_import_suffix(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    external_graph, external_enum = _build_external_enum_runtime_graph()
    ontology_named_external_graph = external_graph.model_copy(
        deep=True,
        update={
            "name": "ontology-ontology",
            "fqn_prefix": "aware_ontology",
        },
    )
    output_root = tmp_path / "materialized_python"

    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=_build_demo_runtime_graph_with_external_enum(external_enum),
            target_language_plugin_id=CodeLanguage.python,
            external_runtime_graphs=(ontology_named_external_graph,),
            source_is_runtime=True,
            output_root=output_root,
            import_root="aware_demo",
            materialization_source="ontology",
            emit_files=True,
        )
    )

    device_source = (output_root / "aware_demo" / "default" / "device.py").read_text(
        encoding="utf-8"
    )
    assert (
        "from aware_ontology_ontology.enums.external_kind import ExternalKind"
        in device_source
    )
    assert (
        "from aware_ontology.enums.external_kind import ExternalKind"
        not in device_source
    )
    bootstrap_payload = json.loads(
        (output_root / "aware_demo" / "_aware" / "python.bootstrap.json").read_text(
            encoding="utf-8"
        )
    )
    assert bootstrap_payload["dependency_import_roots"] == ["aware_ontology_ontology"]
    snapshot_payload = result.manifest_snapshots[0].payload
    import_overrides = cast(
        list[dict[str, str]],
        snapshot_payload["import_overrides"],
    )
    assert {
        "source": str(external_enum.id),
        "target": "aware_ontology_ontology.enums.external_kind",
    } in import_overrides


def test_python_runtime_handler_materialization_derives_local_ontology_import_overrides(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    external_graph, external_enum = _build_external_enum_runtime_graph()
    source_graph = _build_instance_runtime_graph()
    class_config = source_graph.object_config_graph_nodes[0].class_config
    assert class_config is not None
    refresh_function = class_config.class_config_function_configs[0].function_config
    enum_descriptor = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.enum,
        enum_config=external_enum,
        enum_config_id=external_enum.id,
    )
    kind_attribute = AttributeConfig(
        owner_key=(
            f"{refresh_function.owner_key}.{refresh_function.name}::"
            f"{FunctionAttributeType.input.value}"
        ),
        name="kind",
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=enum_descriptor,
        type_descriptor_id=enum_descriptor.id,
    )
    refresh_function.function_config_attribute_configs = [
        FunctionConfigAttributeConfig(
            function_config_id=refresh_function.id,
            attribute_config=kind_attribute,
            attribute_config_id=kind_attribute.id,
            name=kind_attribute.name,
            type=FunctionAttributeType.input,
            position=0,
        )
    ]
    output_root = tmp_path / "runtime_handlers"

    materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=source_graph,
            target_language_plugin_id=CodeLanguage.python,
            external_runtime_graphs=(external_graph,),
            source_is_runtime=True,
            output_root=output_root,
            import_root="aware_demo_runtime",
            stable_ids_import_root="aware_demo_ontology",
            materialization_source="runtime_handlers",
            renderer_kind="runtime_handlers_impl",
            emit_files=True,
        )
    )

    device_sources = sorted(output_root.rglob("device.py"))
    assert len(device_sources) == 1
    device_source = device_sources[0].read_text(encoding="utf-8")
    assert (
        "async def refresh(device: Device, kind: ExternalKind) -> None:"
        in device_source
    )
    assert "from aware_demo_ontology.default.device import Device" in device_source
    assert (
        "from dep_demo_ontology.enums.external_kind import ExternalKind"
        in device_source
    )


def test_python_ontology_package_distribution_uses_import_root(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    output_root = tmp_path / "materialized_python"

    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=_build_demo_runtime_graph(),
            target_language_plugin_id=CodeLanguage.python,
            source_is_runtime=True,
            output_root=output_root,
            import_root="aware_demo_ontology",
            package_name="demo-ontology",
            materialization_source="ontology",
            emit_files=True,
        )
    )

    pyproject_text = (output_root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "aware-demo-ontology"' in pyproject_text
    assert 'name = "demo-ontology"' not in pyproject_text
    assert (output_root / "aware_demo_ontology" / "default" / "device.py").is_file()
    assert not (output_root / "default" / "device.py").exists()
    assert [item.package_name for item in result.package_outputs] == [
        "aware-demo-ontology"
    ]


def test_python_ontology_dto_package_includes_runtime_graph_stable_ids(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    output_root = tmp_path / "materialized_python_dto"

    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=_build_constructor_runtime_graph(),
            target_language_plugin_id=CodeLanguage.python,
            source_is_runtime=True,
            output_root=output_root,
            import_root="aware_demo_ontology_dto",
            package_name="aware-demo-ontology-dto",
            renderer_profile="ontology_dto",
            materialization_source="ontology_dto",
            emit_files=True,
        )
    )

    stable_ids_source = (
        output_root / "aware_demo_ontology_dto" / "stable_ids.py"
    ).read_text(encoding="utf-8")
    assert "def stable_device_id(*, key: str) -> UUID:" in stable_ids_source
    assert "aware:device:{key_norm}" in stable_ids_source
    assert not (output_root / "stable_ids.py").exists()
    assert {item.path for item in result.generated_files} >= {
        Path("aware_demo_ontology_dto/default/device.py"),
        Path("aware_demo_ontology_dto/stable_ids.py"),
    }


def test_language_plugin_materialization_declares_python_meta_handler_provider(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    output_root = tmp_path / "runtime" / "aware_demo"
    request = LanguagePluginMaterializationRequest(
        source_graph=_build_constructor_runtime_graph(),
        target_language_plugin_id=CodeLanguage.python,
        source_is_runtime=True,
        output_root=output_root,
        import_root="aware_demo",
        stable_ids_import_root="aware_demo_ontology",
        package_name="aware_demo",
        renderer_kind="runtime_handlers_meta",
        materialization_source="runtime_handlers",
        source_code_package_id=UUID("11111111-1111-4111-8111-111111111111"),
        object_config_graph_package_id=UUID("22222222-2222-4222-8222-222222222222"),
        object_config_graph_commit_id=UUID("33333333-3333-4333-8333-333333333333"),
        emit_files=True,
    )

    result = materialize_object_config_graph_via_language_plugin(request)

    assert result.materialization_source == "runtime_handlers"
    assert [item.path for item in result.generated_files] == [
        Path("handlers/_generated/meta_handlers.py"),
    ]
    provider_source = (
        output_root / "handlers" / "_generated" / "meta_handlers.py"
    ).read_text(encoding="utf-8")
    assert "AWARE_META_GRAPH_HANDLERS" in provider_source
    assert "AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS" in provider_source
    assert (
        "from aware_demo_ontology.stable_ids import stable_device_id" in provider_source
    )
    assert "aware_demo.stable_ids" not in provider_source
    assert "aware_runtime" not in provider_source

    declared_by_key = {item.output_key: item for item in result.plugin_declared_outputs}
    assert set(declared_by_key) == {PYTHON_META_RUNTIME_HANDLERS_OUTPUT_KEY}
    declared_output = declared_by_key[PYTHON_META_RUNTIME_HANDLERS_OUTPUT_KEY]
    assert declared_output.status == "materialized"
    assert declared_output.generated_file_refs == (
        Path("handlers/_generated/meta_handlers.py"),
    )
    assert declared_output.renderer_kinds == ("runtime_handlers_meta",)
    assert declared_output.materialization_sources == ("runtime_handlers",)

    receipt_by_output = {
        (item.output_key, item.path.as_posix() if item.path is not None else ""): item
        for item in result.ownership_receipts
    }
    provider_receipt = receipt_by_output[
        (
            PYTHON_META_RUNTIME_HANDLERS_OUTPUT_KEY,
            (output_root / "handlers" / "_generated" / "meta_handlers.py").as_posix(),
        )
    ]
    assert provider_receipt.status == "available"
    assert provider_receipt.artifact_role == "meta_runtime_handler_provider"
    assert provider_receipt.output_kind == "generated_file"
    assert provider_receipt.digest
    assert provider_receipt.source_code_package_id == UUID(
        "11111111-1111-4111-8111-111111111111"
    )


def test_python_plugin_does_not_declare_event_render_catalog_output(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _ = tmp_path
    from python_grammar.code_language_plugin import PYTHON_CODE_PLUGIN

    assert all(
        descriptor.output_key != "python.event_render_catalog"
        for descriptor in PYTHON_CODE_PLUGIN.materialization_artifact_outputs
    )


def test_language_plugin_materialization_links_plugin_declared_manifest_output(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_builtin_aware_plugin()
    _register_fake_sql_plugin()
    _FakeSqlRendererLanguage.emit_declared_manifest = True
    output_root = tmp_path / "materialized_sql_declared_manifest"
    request = LanguagePluginMaterializationRequest(
        source_graph=ObjectConfigGraph(
            name="demo_runtime",
            hash="runtime-hash",
            fqn_prefix="aware_demo",
            language=CodeLanguage.aware,
        ),
        target_language_plugin_id=CodeLanguage.sql,
        source_is_runtime=True,
        output_root=output_root,
        emit_files=True,
    )

    result = materialize_object_config_graph_via_language_plugin(request)

    assert [item.path for item in result.generated_files] == [
        Path("_aware/sql.manifest.json"),
        Path("rendered/demo.sql"),
    ]
    declared_output = result.plugin_declared_outputs[0]
    assert declared_output.output_key == "sql.test_manifest"
    assert declared_output.status == "materialized"
    assert declared_output.generated_file_refs == (Path("_aware/sql.manifest.json"),)
    assert result.metrics["plugin_declared_output_count"] == 1
    snapshot_payload = result.manifest_snapshots[0].payload
    declared_payloads = cast(
        list[dict[str, object]],
        snapshot_payload["plugin_declared_outputs"],
    )
    assert declared_payloads == [
        {
            "language": "sql",
            "output_key": "sql.test_manifest",
            "output_kind": "manifest",
            "artifact_role": "test_manifest",
            "producer_step": "manifest_write",
            "path_templates": ["_aware/sql.manifest.json"],
            "resolved_paths": ["_aware/sql.manifest.json"],
            "generated_file_refs": ["_aware/sql.manifest.json"],
            "required_for": ["workspace_revision"],
            "renderer_profiles": [],
            "renderer_kinds": [],
            "materialization_sources": [],
            "required": False,
            "status": "materialized",
            "provider_payload": {},
        }
    ]


def test_language_plugin_materialization_records_import_root_dependency_snapshot(
    isolated_meta_language_plugin_registry: None,
    tmp_path: Path,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_builtin_aware_plugin()
    _register_fake_sql_plugin()
    output_root = tmp_path / "materialized_sql_with_dependency"
    request = LanguagePluginMaterializationRequest(
        source_graph=_build_demo_runtime_graph(),
        target_language_plugin_id=CodeLanguage.sql,
        external_runtime_graphs=(_build_external_runtime_graph(),),
        source_is_runtime=True,
        output_root=output_root,
        import_root="aware_demo",
        import_overrides={"dep_demo": "dep_pkg.dep_demo"},
        profile_inputs={"package_policy": {"mode": "runtime-index-ready"}},
        emit_files=True,
    )

    first = materialize_object_config_graph_via_language_plugin(request)
    second = materialize_object_config_graph_via_language_plugin(request)

    assert first.dependency_signature is not None
    assert first.dependency_signature == second.dependency_signature
    assert len(first.manifest_snapshots) == 1
    assert first.manifest_snapshots[0].sha256 == second.manifest_snapshots[0].sha256
    snapshot = first.manifest_snapshots[0]
    assert snapshot.dependency_signature == first.dependency_signature
    assert "dependency_import_resolution" in snapshot.required_for

    payload = snapshot.payload
    assert payload["import_root"] == "aware_demo"
    assert payload["import_overrides"] == [
        {"source": "dep_demo", "target": "dep_pkg.dep_demo"}
    ]
    assert payload["dependency_signature"] == first.dependency_signature
    external_runtime_graphs = cast(
        list[dict[str, object]],
        payload["external_runtime_graphs"],
    )
    assert external_runtime_graphs == [
        {
            "id": "bbbbbbbb-bbbb-5bbb-bbbb-bbbbbbbbbbbb",
            "name": "dependency_runtime",
            "hash": "dependency-runtime-hash",
            "fqn_prefix": "dep_demo",
            "language": "aware",
        }
    ]
    language_external_graphs = cast(
        list[dict[str, object]],
        payload["language_external_graphs"],
    )
    assert language_external_graphs[0]["hash"] == "dependency-runtime-hash:sql"
    assert language_external_graphs[0]["language"] == "sql"
    assert _FakeSqlRendererLanguage.last_import_overrides == {
        "dep_demo": "dep_pkg.dep_demo"
    }
    assert [graph.hash for graph in _FakeSqlRendererLanguage.last_external_graphs] == [
        "dependency-runtime-hash:sql"
    ]
    assert any(
        "external_graphs_by_id" in kwargs
        for kwargs in _FakeRuntimeToSqlTransformer.calls
    )


def test_language_plugin_materialization_reuses_runtime_to_language_cache(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_sql_plugin()
    source_graph = _build_demo_runtime_graph()
    external_graph = _build_external_runtime_graph()
    cache = RuntimeToLanguageLoweringCache()
    request = LanguagePluginMaterializationRequest(
        source_graph=source_graph,
        target_language_plugin_id=CodeLanguage.sql,
        external_runtime_graphs=(external_graph,),
        source_is_runtime=True,
        runtime_to_language_cache=cache,
    )

    first = materialize_object_config_graph_via_language_plugin(request)
    second = materialize_object_config_graph_via_language_plugin(request)

    assert len(_FakeRuntimeToSqlTransformer.calls) == 2
    assert first.language_graph is not second.language_graph
    assert first.language_external_graphs[0] is not second.language_external_graphs[0]
    assert second.metrics["runtime_to_language_cache"] == {
        "entry_count": 2,
        "hit_count": 2,
        "miss_count": 2,
        "store_count": 2,
        "deep_copy_hits": True,
    }
    second_step_by_name = {step.name: step for step in second.tool_steps}
    assert set(second_step_by_name) >= {
        "runtime_to_language.primary.cache_hit",
        "runtime_to_language.external_0.cache_hit",
    }


def test_language_plugin_materialization_reuses_runtime_derivation_cache(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_sql_plugin()
    source_graph = _build_demo_runtime_graph()
    external_graph = _build_external_runtime_graph()
    cache = RuntimeObjectConfigGraphDerivationCache()
    request = LanguagePluginMaterializationRequest(
        source_graph=source_graph,
        target_language_plugin_id=CodeLanguage.sql,
        external_runtime_graphs=(external_graph,),
        source_is_runtime=True,
        runtime_derivation_cache=cache,
    )

    first = materialize_object_config_graph_via_language_plugin(request)
    second = materialize_object_config_graph_via_language_plugin(request)

    assert first.runtime_graph is not second.runtime_graph
    assert first.language_external_graphs[0] is not second.language_external_graphs[0]
    assert second.metrics["runtime_derivation_cache"] == {
        "entry_count": 1,
        "hit_count": 1,
        "miss_count": 1,
        "store_count": 1,
        "deep_copy_hits": True,
    }
    second_step_by_name = {step.name: step for step in second.tool_steps}
    assert "derive_runtime_graph.cache_hit" in second_step_by_name
    assert "derive_runtime_graph.cache_store" not in second_step_by_name
    assert any(step.name.startswith("runtime_derivation:") for step in first.tool_steps)
    assert not any(
        step.name.startswith("runtime_derivation:") for step in second.tool_steps
    )


def test_language_plugin_materialization_can_reuse_external_runtime_graph_refs(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_sql_plugin()
    source_graph = _build_demo_runtime_graph()
    external_graph = _build_external_runtime_graph()

    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=source_graph,
            target_language_plugin_id=CodeLanguage.sql,
            external_runtime_graphs=(external_graph,),
            source_is_runtime=True,
            reuse_external_runtime_graphs=True,
            lower_language_external_graphs=False,
        )
    )

    assert result.runtime_graph is not source_graph
    assert result.language_external_graphs == (external_graph,)
    assert result.language_external_graphs[0] is external_graph
    assert result.metrics["runtime_external_graphs_reused"] is True
    assert result.metrics["runtime_external_graph_reuse_count"] == 1
    assert (
        sum(
            1
            for step in result.tool_steps
            if step.name == "runtime_derivation:clone_runtime_graph.shallow"
        )
        == 1
    )


def test_language_plugin_materialization_runtime_derivation_cache_can_return_shallow_hit_copies(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_sql_plugin()
    source_graph = _build_demo_runtime_graph()
    external_graph = _build_external_runtime_graph()
    cache = RuntimeObjectConfigGraphDerivationCache(deep_copy_hits=False)
    request = LanguagePluginMaterializationRequest(
        source_graph=source_graph,
        target_language_plugin_id=CodeLanguage.sql,
        external_runtime_graphs=(external_graph,),
        source_is_runtime=True,
        runtime_derivation_cache=cache,
    )

    materialize_object_config_graph_via_language_plugin(request)
    second = materialize_object_config_graph_via_language_plugin(request)
    third = materialize_object_config_graph_via_language_plugin(request)

    assert second.runtime_graph is not third.runtime_graph
    assert (
        second.runtime_graph.object_config_graph_nodes
        is third.runtime_graph.object_config_graph_nodes
    )
    assert third.metrics["runtime_derivation_cache"] == {
        "entry_count": 1,
        "hit_count": 2,
        "miss_count": 1,
        "store_count": 1,
        "deep_copy_hits": False,
    }


def test_runtime_derivation_cache_can_store_shallow_copies(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_sql_plugin()
    source_graph = _build_demo_runtime_graph()
    external_graph = _build_external_runtime_graph()
    cache = RuntimeObjectConfigGraphDerivationCache(
        deep_copy_hits=False,
        deep_copy_stores=False,
    )
    request = LanguagePluginMaterializationRequest(
        source_graph=source_graph,
        target_language_plugin_id=CodeLanguage.sql,
        external_runtime_graphs=(external_graph,),
        source_is_runtime=True,
        runtime_derivation_cache=cache,
    )

    first = materialize_object_config_graph_via_language_plugin(request)
    second = materialize_object_config_graph_via_language_plugin(request)

    assert first.runtime_graph is not second.runtime_graph
    assert (
        first.runtime_graph.object_config_graph_nodes
        is second.runtime_graph.object_config_graph_nodes
    )
    assert second.metrics["runtime_derivation_cache"] == {
        "entry_count": 1,
        "hit_count": 1,
        "miss_count": 1,
        "store_count": 1,
        "deep_copy_hits": False,
    }


def test_runtime_to_language_cache_can_skip_language_graph_store() -> None:
    runtime_graph = _build_demo_runtime_graph()
    cache = RuntimeToLanguageLoweringCache(store_language_results=False)
    cache_key = language_service_module._runtime_to_language_cache_key(  # noqa: SLF001
        runtime_graph=runtime_graph,
        target_language_plugin_id=CodeLanguage.python,
        renderer_profile="orm_runtime",
        external_runtime_graphs=(),
    )

    cache.store(
        cache_key,
        language_graph=runtime_graph,
        generated_manifest=None,
    )

    assert cache.get(cache_key) is None
    assert cache.stats_payload() == {
        "entry_count": 0,
        "hit_count": 0,
        "miss_count": 1,
        "store_count": 0,
        "deep_copy_hits": True,
        "language_graph_store_enabled": False,
        "store_skipped_count": 1,
    }


def test_runtime_to_language_cache_can_return_shallow_hit_copies() -> None:
    runtime_graph = _build_demo_runtime_graph()
    cache = RuntimeToLanguageLoweringCache(deep_copy_hits=False)
    cache_key = language_service_module._runtime_to_language_cache_key(  # noqa: SLF001
        runtime_graph=runtime_graph,
        target_language_plugin_id=CodeLanguage.python,
        renderer_profile="orm_runtime",
        external_runtime_graphs=(),
    )

    cache.store(
        cache_key,
        language_graph=runtime_graph,
        generated_manifest=None,
    )

    first, _ = cache.get(cache_key) or (None, None)
    second, _ = cache.get(cache_key) or (None, None)

    assert first is not None
    assert second is not None
    assert first is not second
    assert first.object_config_graph_nodes is second.object_config_graph_nodes
    assert cache.stats_payload() == {
        "entry_count": 1,
        "hit_count": 2,
        "miss_count": 0,
        "store_count": 1,
        "deep_copy_hits": False,
    }


def test_runtime_to_language_cache_can_store_shallow_copies() -> None:
    runtime_graph = _build_demo_runtime_graph()
    cache = RuntimeToLanguageLoweringCache(
        deep_copy_hits=False,
        deep_copy_stores=False,
    )
    cache_key = language_service_module._runtime_to_language_cache_key(  # noqa: SLF001
        runtime_graph=runtime_graph,
        target_language_plugin_id=CodeLanguage.python,
        renderer_profile="orm_runtime",
        external_runtime_graphs=(),
    )

    cache.store(
        cache_key,
        language_graph=runtime_graph,
        generated_manifest=None,
    )

    cached_graph, _ = cache.get(cache_key) or (None, None)

    assert cached_graph is not None
    assert cached_graph is not runtime_graph
    assert (
        cached_graph.object_config_graph_nodes
        is runtime_graph.object_config_graph_nodes
    )
    assert cache.stats_payload() == {
        "entry_count": 1,
        "hit_count": 1,
        "miss_count": 0,
        "store_count": 1,
        "deep_copy_hits": False,
    }


def test_runtime_to_language_closure_service_reuses_prepared_python_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_graph = _build_demo_runtime_graph()
    external_graph = _build_external_runtime_graph()
    runtime_graph.object_projection_graphs = [
        ObjectProjectionGraph(
            name="DemoRuntime",
            language=CodeLanguage.aware,
            projection_hash="demo-runtime",
            object_config_graph_id=runtime_graph.id,
        )
    ]
    calls: list[tuple[str, object | None]] = []

    def _fake_lower_runtime_graph_to_language(
        graph: ObjectConfigGraph,
        _: CodeLanguage,
        *,
        graph_role: str,
        portal_closure_context_factory: Callable[[], object | None] | None = None,
        **__: object,
    ) -> tuple[ObjectConfigGraph, None]:
        portal_closure_context = (
            portal_closure_context_factory()
            if portal_closure_context_factory is not None
            else None
        )
        calls.append((graph_role, portal_closure_context))
        return graph, None

    monkeypatch.setattr(
        language_service_module,
        "_lower_runtime_graph_to_language",
        _fake_lower_runtime_graph_to_language,
    )
    steps: list[language_service_module.LanguageMaterializationStep] = []

    result = RuntimeToLanguageClosureLoweringService().lower(
        RuntimeToLanguageClosureLoweringRequest(
            runtime_graph=runtime_graph,
            target_language_plugin_id=CodeLanguage.python,
            runtime_external_graphs=(external_graph,),
            steps=steps,
        )
    )

    closure_contexts = [context for _, context in calls]
    assert [role for role, _ in calls] == ["primary", "external_0"]
    assert closure_contexts[0] is not None
    assert closure_contexts[1] is closure_contexts[0]
    assert result.language_graph is runtime_graph
    assert result.language_external_graphs == (external_graph,)
    assert result.metrics == {
        "runtime_to_language_closure_context_prepared": True,
        "runtime_to_language_closure_context_graph_count": 2,
        "runtime_to_language_external_graph_lowering_skipped_count": 0,
    }
    step_by_name = {step.name: step for step in steps}
    assert "runtime_to_language.closure_context_prepare" in step_by_name
    assert (
        step_by_name["runtime_to_language.closure_context_prepare"].details[
            "graph_role"
        ]
        == "all"
    )


def test_runtime_to_language_closure_service_caches_prepared_python_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_graph = _build_demo_runtime_graph()
    external_graph = _build_external_runtime_graph()
    runtime_graph.object_projection_graphs = [
        ObjectProjectionGraph(
            name="DemoRuntime",
            language=CodeLanguage.aware,
            projection_hash="demo-runtime",
            object_config_graph_id=runtime_graph.id,
        )
    ]
    cache = RuntimeToLanguageLoweringCache()
    calls: list[tuple[str, object | None]] = []

    def _fake_lower_runtime_graph_to_language(
        graph: ObjectConfigGraph,
        _: CodeLanguage,
        *,
        graph_role: str,
        portal_closure_context_factory: Callable[[], object | None] | None = None,
        **__: object,
    ) -> tuple[ObjectConfigGraph, None]:
        portal_closure_context = (
            portal_closure_context_factory()
            if portal_closure_context_factory is not None
            else None
        )
        calls.append((graph_role, portal_closure_context))
        return graph, None

    monkeypatch.setattr(
        language_service_module,
        "_lower_runtime_graph_to_language",
        _fake_lower_runtime_graph_to_language,
    )

    first_steps: list[language_service_module.LanguageMaterializationStep] = []
    RuntimeToLanguageClosureLoweringService().lower(
        RuntimeToLanguageClosureLoweringRequest(
            runtime_graph=runtime_graph,
            target_language_plugin_id=CodeLanguage.python,
            runtime_external_graphs=(external_graph,),
            runtime_to_language_cache=cache,
            steps=first_steps,
        )
    )
    first_context = calls[0][1]
    assert first_context is not None

    second_steps: list[language_service_module.LanguageMaterializationStep] = []
    RuntimeToLanguageClosureLoweringService().lower(
        RuntimeToLanguageClosureLoweringRequest(
            runtime_graph=runtime_graph,
            target_language_plugin_id=CodeLanguage.python,
            runtime_external_graphs=(external_graph,),
            runtime_to_language_cache=cache,
            steps=second_steps,
        )
    )

    assert [role for role, _ in calls] == [
        "primary",
        "external_0",
        "primary",
        "external_0",
    ]
    assert calls[1][1] is first_context
    assert calls[2][1] is first_context
    assert calls[3][1] is first_context
    assert cache.stats_payload()["portal_closure_context"] == {
        "entry_count": 1,
        "hit_count": 1,
        "miss_count": 1,
        "store_count": 1,
    }
    first_step_names = {step.name for step in first_steps}
    second_step_names = {step.name for step in second_steps}
    assert "runtime_to_language.closure_context_prepare" in first_step_names
    assert "runtime_to_language.closure_context_cache_miss" in first_step_names
    assert "runtime_to_language.closure_context_cache_store" in first_step_names
    assert "runtime_to_language.closure_context_cache_hit" in second_step_names
    assert "runtime_to_language.closure_context_prepare" not in second_step_names


def test_runtime_to_language_closure_service_can_skip_external_graph_lowering(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_graph = _build_demo_runtime_graph()
    external_graph = _build_external_runtime_graph()
    calls: list[str] = []

    def _fake_lower_runtime_graph_to_language(
        graph: ObjectConfigGraph,
        _: CodeLanguage,
        *,
        graph_role: str,
        **__: object,
    ) -> tuple[ObjectConfigGraph, None]:
        calls.append(graph_role)
        return graph, None

    monkeypatch.setattr(
        language_service_module,
        "_lower_runtime_graph_to_language",
        _fake_lower_runtime_graph_to_language,
    )
    steps: list[language_service_module.LanguageMaterializationStep] = []

    result = RuntimeToLanguageClosureLoweringService().lower(
        RuntimeToLanguageClosureLoweringRequest(
            runtime_graph=runtime_graph,
            target_language_plugin_id=CodeLanguage.python,
            runtime_external_graphs=(external_graph,),
            lower_external_graphs=False,
            steps=steps,
        )
    )

    assert calls == ["primary"]
    assert result.language_graph is runtime_graph
    assert result.language_external_graphs == (external_graph,)
    assert (
        result.metrics["runtime_to_language_external_graph_lowering_skipped_count"] == 1
    )
    assert "runtime_to_language.external_graph_lowering_skipped" in {
        step.name for step in steps
    }


def test_runtime_to_language_closure_service_can_skip_sql_external_graph_lowering(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_graph = _build_demo_runtime_graph()
    external_graph = _build_external_runtime_graph()
    calls: list[str] = []

    def _fake_lower_runtime_graph_to_language(
        graph: ObjectConfigGraph,
        _: CodeLanguage,
        *,
        graph_role: str,
        **__: object,
    ) -> tuple[ObjectConfigGraph, None]:
        calls.append(graph_role)
        return graph, None

    monkeypatch.setattr(
        language_service_module,
        "_lower_runtime_graph_to_language",
        _fake_lower_runtime_graph_to_language,
    )
    steps: list[language_service_module.LanguageMaterializationStep] = []

    result = RuntimeToLanguageClosureLoweringService().lower(
        RuntimeToLanguageClosureLoweringRequest(
            runtime_graph=runtime_graph,
            target_language_plugin_id=CodeLanguage.sql,
            runtime_external_graphs=(external_graph,),
            lower_external_graphs=False,
            steps=steps,
        )
    )

    assert calls == ["primary"]
    assert result.language_external_graphs == (external_graph,)
    assert (
        result.metrics["runtime_to_language_external_graph_lowering_skipped_count"] == 1
    )
    assert "runtime_to_language.external_graph_lowering_skipped" in {
        step.name for step in steps
    }


def test_runtime_to_language_clone_graph_uses_shallow_transformer_handoff(
    isolated_meta_language_plugin_registry: None,
) -> None:
    _ = isolated_meta_language_plugin_registry
    _register_fake_sql_plugin(
        runtime_to_language_transformer=_MutatingRuntimeToSqlTransformer,
    )
    runtime_graph = _build_demo_runtime_graph()
    source_class = next(
        node.class_config
        for node in runtime_graph.object_config_graph_nodes
        if node.class_config is not None
    )
    steps: list[language_service_module.LanguageMaterializationStep] = []

    result = RuntimeToLanguageClosureLoweringService().lower(
        RuntimeToLanguageClosureLoweringRequest(
            runtime_graph=runtime_graph,
            target_language_plugin_id=CodeLanguage.sql,
            steps=steps,
        )
    )

    language_class = next(
        node.class_config
        for node in result.language_graph.object_config_graph_nodes
        if node.class_config is not None
    )
    assert source_class.name == "Device"
    assert runtime_graph.hash == "runtime-hash"
    assert language_class.name == "MutatedDevice"
    assert result.language_graph.hash == "mutated-language-hash"
    step_by_name = {step.name: step for step in steps}
    assert (
        step_by_name["runtime_to_language.primary.clone_graph"].details[
            "clone_strategy"
        ]
        == "shallow_runtime_language_transformer_handoff"
    )


def test_language_plugin_lowers_external_graphs_with_source_and_siblings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_graph = _build_demo_runtime_graph()
    external_a = _build_external_runtime_graph()
    external_b = external_a.model_copy(
        deep=True,
        update={
            "id": UUID("cccccccc-cccc-5ccc-cccc-cccccccccccc"),
            "name": "dependency_runtime_b",
            "hash": "dependency-runtime-b-hash",
            "fqn_prefix": "dep_demo_b",
        },
    )
    calls: list[tuple[str, tuple[str, ...]]] = []

    class _FakeRuntimeDerivationService:
        def derive(self, _: object) -> RuntimeObjectConfigGraphDerivationResult:
            return RuntimeObjectConfigGraphDerivationResult(
                source_graph=runtime_graph,
                runtime_graph=runtime_graph,
                runtime_external_graphs=(external_a, external_b),
            )

    def _fake_lower_runtime_graph_to_language(
        graph: ObjectConfigGraph,
        _: CodeLanguage,
        *,
        external_runtime_graphs: tuple[ObjectConfigGraph, ...],
        **__: object,
    ) -> tuple[ObjectConfigGraph, None]:
        calls.append((graph.name, tuple(item.name for item in external_runtime_graphs)))
        return graph, None

    monkeypatch.setattr(
        language_service_module,
        "RuntimeObjectConfigGraphDerivationService",
        _FakeRuntimeDerivationService,
    )
    monkeypatch.setattr(
        language_service_module,
        "_ensure_target_language_plugin",
        lambda _: None,
    )
    monkeypatch.setattr(
        language_service_module,
        "_lower_runtime_graph_to_language",
        _fake_lower_runtime_graph_to_language,
    )

    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=runtime_graph,
            target_language_plugin_id=CodeLanguage.python,
            external_runtime_graphs=(external_a, external_b),
            emit_files=False,
        )
    )

    assert result.status == "succeeded"
    assert calls == [
        ("demo_runtime", ("dependency_runtime", "dependency_runtime_b")),
        ("dependency_runtime", ("demo_runtime", "dependency_runtime_b")),
        ("dependency_runtime_b", ("demo_runtime", "dependency_runtime")),
    ]
