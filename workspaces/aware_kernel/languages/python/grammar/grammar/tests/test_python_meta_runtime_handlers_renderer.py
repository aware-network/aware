from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.function.code_section_function import CodeSectionFunction
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.part.content_part_text_segment import (
    ContentPartTextSegment,
)
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionIdentityKeyOrigin,
    FunctionKind,
)
from aware_meta_ontology.function.function_config_invocation import (
    FunctionConfigInvocation,
)
from aware_meta_ontology.function.function_config_invocation_enums import (
    FunctionInvocationKind,
)
from aware_meta_ontology.function.function_impl import FunctionImpl
from aware_meta_ontology.function.function_impl_instruction import (
    FunctionImplInstruction,
)
from aware_meta_ontology.function.function_impl_instruction_construct import (
    FunctionImplInstructionConstruct,
)
from aware_meta_ontology.function.function_impl_instruction_construct_assignment import (
    FunctionImplInstructionConstructAssignment,
)
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplInstructionType,
    FunctionImplInvokeKind,
    FunctionImplValueSourceKind,
)
from aware_meta_ontology.function.function_impl_instruction_invoke import (
    FunctionImplInstructionInvoke,
)
from aware_meta_ontology.function.function_impl_value_source import (
    FunctionImplValueSource,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig

from python_grammar.meta_language_plugin import PYTHON_META_PLUGIN
import python_grammar.renderer_runtime_handlers_meta as runtime_handlers_meta_module
from python_grammar.renderer_runtime_handlers_meta import (
    PythonMetaRuntimeHandlersRenderer,
)
from python_grammar.renderer_runtime_handlers_aware import (
    PythonRendererRuntimeHandlersAware,
)
from python_grammar.renderer_stable_ids import (
    PYTHON_STABLE_IDS_IMPORT_ROOT_POLICY_KEY,
)
from python_grammar_test_support import (
    class_attr_link,
    function_attr_link,
    function_io_owner_key,
    function_owner_key,
    make_attribute,
    make_class,
    make_class_node,
    make_function,
    make_relationship,
    make_relationship_attribute,
)


@dataclass(frozen=True)
class _Layout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = "aware_test_runtime"

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        _ = class_config
        return Path("environment") / "home.py"

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        _ = enum_config
        return Path("handlers") / "_generated" / "meta_handlers.py"

    def get_function_file_path(self, function_config) -> Path:
        _ = function_config
        return Path("handlers") / "_generated" / "meta_handlers.py"

    def get_file_extension(self) -> str:
        return ".py"


@dataclass(frozen=True)
class _ProgramImplSchemaLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = "aware_test_runtime"

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        _ = class_config
        return Path("program") / "impl" / "program_impl.py"

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        _ = enum_config
        return Path("handlers") / "_generated" / "meta_handlers.py"

    def get_function_file_path(self, function_config) -> Path:
        _ = function_config
        return Path("handlers") / "_generated" / "meta_handlers.py"

    def get_file_extension(self) -> str:
        return ".py"


def _primitive_desc(base: CodePrimitiveBaseType) -> AttributeTypeDescriptor:
    prim = build_code_primitive_type(base_type=base)
    prim_cfg = PrimitiveConfig(primitive_type=prim, primitive_type_id=prim.id)
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=prim_cfg,
        primitive_config_id=prim_cfg.id,
    )


def _class_desc(target: ClassConfig) -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config=target,
        class_config_id=target.id,
    )


def _list_desc(target: ClassConfig) -> AttributeTypeDescriptor:
    _ = target
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.collection,
        collection_kind=AttributeCollectionType.list,
    )


def test_python_meta_runtime_handlers_renderer_groups_orm_support_imports(
    tmp_path: Path,
) -> None:
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
    )
    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    compile(out, "meta_handlers.py", "exec")
    assert "# Third-party\nfrom aware_orm" not in out
    assert (
        "# Orm\n"
        "from aware_orm.models.orm_model import ORMModel\n"
        "from aware_orm.registry import ORMModelRegistry\n"
        "from aware_orm.session.change_collector import current_change_collector\n"
        in out
    )


def _body_code_section_function(body: str) -> CodeSectionFunction:
    content = ContentPartText(inline_text=body)
    body_segment = ContentPartTextSegment.model_construct(
        key="body",
        byte_start=0,
        byte_end=len(body.encode("utf-8")),
        content_part_text=content,
        content_part_text_id=content.id,
    )
    return CodeSectionFunction.model_construct(
        name="generated",
        description=None,
        is_async=True,
        is_public=True,
        signature_segment=body_segment,
        body_segment=body_segment,
    )


def test_python_meta_runtime_handlers_renderer_is_registered() -> None:
    renderers = PYTHON_META_PLUGIN.language_renderers
    assert renderers is not None
    assert renderers["runtime_handlers_meta"] is PythonMetaRuntimeHandlersRenderer
    assert "runtime_handlers" in renderers
    assert "runtime_handlers_manual" in renderers
    assert "runtime_handlers_aware" in renderers


def test_python_meta_runtime_handlers_renderer_hydration_policy(
    tmp_path: Path,
) -> None:
    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )

    assert renderer.requires_graph_metadata_hydration() is False

    renderer.set_policy(
        {
            "function_impl_ownership": "compiler",
            "function_impl_parity_policy": "error",
        }
    )

    assert renderer.requires_graph_metadata_hydration() is True


def test_python_meta_runtime_handlers_renderer_emits_meta_provider(
    tmp_path: Path,
) -> None:
    home = make_class(name="Home", is_base=True)
    build = make_function(
        name="build",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.class_,
    )
    key_input = make_attribute(
        name="key",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=True,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.string),
    )
    build.function_config_attribute_configs = [
        function_attr_link(
            build,
            key_input,
            type=FunctionAttributeType.input,
            position=0,
            is_identity_key=True,
        ),
    ]
    rename = make_function(
        name="rename",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.instance,
    )
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=rename.id,
            function_config=rename,
            is_public=True,
            is_constructor=False,
            position=1,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), home),
        ],
        object_projection_graphs=[],
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {PYTHON_STABLE_IDS_IMPORT_ROOT_POLICY_KEY: "aware_test_ontology"}
    )
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    compile(out, "meta_handlers.py", "exec")
    assert "from uuid import UUID" in out
    assert "AWARE_META_GRAPH_HANDLERS" in out
    assert "AWARE_META_GRAPH_INVOCATION_HANDLERS" in out
    assert "AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS" in out
    assert "MetaGraphGeneratedInvocationHandlerCallable" in out
    assert "MetaGraphGeneratedLanguageHandlerKey" in out
    assert "home__rename__handler" in out
    assert "home__rename__invocation_handler" in out
    assert "is_constructor=False" in out
    assert "): home__rename__handler" in out
    assert "reify_oig_root_model" in out
    assert "target_class_instance_id=target_object_id" in out
    assert "ORMModelRegistry" in out
    assert "# Third-party\nfrom aware_orm" not in out
    assert (
        "# Orm\n"
        "from aware_orm.models.orm_model import ORMModel\n"
        "from aware_orm.registry import ORMModelRegistry\n"
        "from aware_orm.session.change_collector import current_change_collector\n"
        in out
    )
    assert (
        "from aware_test_runtime.handlers.impl.environment.home import build as _impl"
        in out
    )
    assert (
        "from aware_test_runtime.handlers.impl.environment.home import rename as _impl"
        in out
    )
    assert "aware_test_runtime.handlers.impl.default.home" not in out
    assert "from aware_test_ontology.stable_ids import stable_home_id" not in out
    assert "aware_test_runtime.stable_ids" not in out
    assert "aware_runtime.stable_ids" not in out
    assert "aware_runtime" not in out
    assert "coerce_meta_handler_call_kwargs" in out
    assert (
        "call_kwargs = coerce_meta_handler_call_kwargs(_impl, dict(bound_input))" in out
    )
    assert "disable_change_tracking_hooks" not in out
    assert "disable_autobind" not in out
    assert "result = await _impl(**call_kwargs)" in out
    assert "result = await _impl(home=target, **call_kwargs)" in out
    assert "aware_meta.runtime.value_resolvers" in out
    assert "default_meta_enum_option_resolver" in out
    assert "enum_option_resolver=default_meta_enum_option_resolver" in out
    assert renderer.extra_output_paths() == [
        Path("handlers") / "_generated" / "meta_handlers.py",
    ]
    assert renderer.renders_only_extra_output_paths() is True


def test_python_meta_runtime_handlers_renderer_uses_compiler_owned_function_impl(
    tmp_path: Path,
) -> None:
    home = make_class(name="Home", is_base=True)
    build = make_function(
        name="build",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.class_,
    )
    key_input = make_attribute(
        name="key",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=True,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.string),
    )
    build.function_config_attribute_configs = [
        function_attr_link(
            build,
            key_input,
            type=FunctionAttributeType.input,
            position=0,
            is_identity_key=True,
        ),
    ]
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), home),
        ],
        object_projection_graphs=[],
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {
            PYTHON_STABLE_IDS_IMPORT_ROOT_POLICY_KEY: "aware_test_ontology",
            "function_impl_ownership": "compiler",
            "function_impl_parity_policy": "error",
        }
    )
    renderer.import_overrides = {
        str(home.id): "aware_test_ontology.environment.home",
    }
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    compile(out, "meta_handlers.py", "exec")
    assert "handlers.impl" not in out
    assert "from aware_test_ontology.environment.home import Home" in out
    assert "async def _impl(key: str) -> None:" in out
    assert "_aware_self_values = {'key': key}" in out
    assert (
        "_aware_self_stable_values = {key: getattr("
        "_aware_self_values[key], 'value', _aware_self_values[key]) "
        "for key in _aware_self_key_names}"
    ) in out
    assert "return Home(id=_aware_self_id, key=key)" in out
    assert (
        "call_kwargs = coerce_meta_handler_call_kwargs(_impl, dict(bound_input))" in out
    )
    assert "result = await _impl(**call_kwargs)" in out


def test_python_meta_runtime_handlers_renderer_delegates_compiler_owned_impl_when_present(
    tmp_path: Path,
) -> None:
    home = make_class(name="Home", is_base=True)
    rename = make_function(
        name="rename",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.instance,
    )
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=rename.id,
            function_config=rename,
            is_public=True,
            is_constructor=False,
            position=0,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), home),
        ],
        object_projection_graphs=[],
    )
    impl_path = tmp_path / "handlers" / "impl" / "environment" / "home.py"
    impl_path.parent.mkdir(parents=True)
    impl_path.write_text(
        "async def rename(home):\n" "    return None\n",
        encoding="utf-8",
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {
            "function_impl_ownership": "compiler",
            "function_impl_parity_policy": "error",
        }
    )
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    compile(out, "meta_handlers.py", "exec")
    assert (
        "from aware_test_runtime.handlers.impl.environment.home import rename as _impl"
        in out
    )
    assert "Compiler-owned FunctionImpl lowering unavailable for Home.rename" not in out
    assert "result = await _impl(home=target, **call_kwargs)" in out


def test_python_meta_runtime_handlers_renderer_delegates_runtime_function_to_source_impl(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_home = make_class(name="Home", is_base=True)
    runtime_home = make_class(name="Home", is_base=True)
    runtime_home.id = source_home.id
    runtime_home.class_fqn = source_home.class_fqn

    source_body = _body_code_section_function("return None")
    source_build = make_function(
        name="build",
        owner_key=function_owner_key(source_home),
        is_async=True,
        kind=FunctionKind.class_,
        code_section_function=source_body,
        code_section_function_id=source_body.id,
    )
    runtime_build = make_function(
        name="build_via_parent",
        owner_key=function_owner_key(runtime_home),
        is_async=True,
        kind=FunctionKind.class_,
        code_section_function=source_body,
        code_section_function_id=source_body.id,
    )
    source_home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=source_home.id,
            function_config_id=source_build.id,
            function_config=source_build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]
    runtime_home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=runtime_home.id,
            function_config_id=runtime_build.id,
            function_config=runtime_build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]
    source_ocg = ObjectConfigGraph(
        name="source",
        description="source",
        hash="sha256:source",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000001"), source_home),
        ],
        object_projection_graphs=[],
    )
    runtime_ocg = ObjectConfigGraph(
        name="runtime",
        description="runtime",
        hash="sha256:runtime",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000002"), runtime_home),
        ],
        object_projection_graphs=[],
    )
    impl_path = tmp_path / "handlers" / "impl" / "environment" / "home.py"
    impl_path.parent.mkdir(parents=True)
    impl_path.write_text(
        "async def build():\n" "    return None\n",
        encoding="utf-8",
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {
            "function_impl_ownership": "compiler",
            "function_impl_parity_policy": "error",
            "function_impl_source_graph": source_ocg,
        }
    )
    monkeypatch.setattr(
        runtime_handlers_meta_module,
        "_iter_graph_function_configs",
        lambda graph: (_ for _ in ()).throw(
            AssertionError("source graph traversal must finish during set_policy")
        ),
    )
    renderer.bind_object_config_graph(runtime_ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    compile(out, "meta_handlers.py", "exec")
    assert (
        "from aware_test_runtime.handlers.impl.environment.home import build as _impl"
        in out
    )
    assert (
        "from aware_test_runtime.handlers.impl.environment.home import "
        "build_via_parent as _impl"
    ) not in out
    assert (
        "Compiler-owned FunctionImpl lowering unavailable for Home.build_via_parent"
        not in out
    )


def test_python_meta_runtime_handlers_renderer_bootstrap_uses_stable_id_binding(
    tmp_path: Path,
) -> None:
    child = make_class(name="ChildEntity", is_base=True)
    build = make_function(
        name="build_via_parent",
        owner_key=function_owner_key(child),
        is_async=True,
        kind=FunctionKind.class_,
    )
    parent_entity_id = make_attribute(
        name="parent_entity_id",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=True,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    type_attr = make_attribute(
        name="type",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        default_value='"text"',
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.string),
    )
    build.function_config_attribute_configs = [
        function_attr_link(
            build,
            parent_entity_id,
            type=FunctionAttributeType.input,
            position=0,
            is_identity_key=True,
        ),
        function_attr_link(
            build,
            type_attr,
            type=FunctionAttributeType.input,
            position=1,
            is_identity_key=False,
        ),
    ]
    child.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=child.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), child),
        ],
        object_projection_graphs=[],
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {
            PYTHON_STABLE_IDS_IMPORT_ROOT_POLICY_KEY: "aware_test_ontology",
            "function_impl_ownership": "compiler",
            "function_impl_parity_policy": "error",
        }
    )
    renderer.import_overrides = {
        str(child.id): "aware_test_ontology.environment.child_entity",
    }
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""
    helper_start = out.index("def _root_id_child_entity__build_via_parent")
    helper_end = out.index("\ndef ", helper_start + 1)
    helper = out[helper_start:helper_end]

    compile(out, "meta_handlers.py", "exec")
    assert (
        "from aware_test_ontology.stable_ids import "
        "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID"
    ) in helper
    assert "parent_entity_id = bound_input.get('parent_entity_id')" in helper
    assert "type = bound_input.get('type')" in helper
    assert "if type is None:" in helper
    assert "type = 'text'" in helper
    assert (
        "_aware_self_values = {'parent_entity_id': parent_entity_id, 'type': type}"
        in helper
    )
    assert "_aware_self_fn, _aware_self_key_names = _aware_self_binding" in helper
    assert (
        "return getattr(import_module('aware_test_ontology.stable_ids'), _aware_self_fn)"
        in helper
    )
    assert "stable_child_entity_id(parent_entity_id=parent_entity_id" not in helper


def test_python_meta_runtime_handlers_renderer_reuses_compiler_render_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    home = make_class(name="Home", is_base=True)
    build = make_function(
        name="build",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.class_,
    )
    key_input = make_attribute(
        name="key",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=True,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.string),
    )
    build.function_config_attribute_configs = [
        function_attr_link(
            build,
            key_input,
            type=FunctionAttributeType.input,
            position=0,
            is_identity_key=True,
        ),
    ]
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), home),
        ],
        object_projection_graphs=[],
    )

    render_signature_calls = 0
    generated_logic_calls = 0
    original_render_signature = PythonRendererRuntimeHandlersAware._render_signature
    original_build_generated_impl_logic = (
        PythonRendererRuntimeHandlersAware._build_generated_impl_logic
    )

    def _count_render_signature(self, *, fn):
        nonlocal render_signature_calls
        render_signature_calls += 1
        return original_render_signature(self, fn=fn)

    def _count_build_generated_impl_logic(self, *, class_config, fn_link, fn):
        nonlocal generated_logic_calls
        generated_logic_calls += 1
        return original_build_generated_impl_logic(
            self,
            class_config=class_config,
            fn_link=fn_link,
            fn=fn,
        )

    monkeypatch.setattr(
        PythonRendererRuntimeHandlersAware,
        "_render_signature",
        _count_render_signature,
    )
    monkeypatch.setattr(
        PythonRendererRuntimeHandlersAware,
        "_build_generated_impl_logic",
        _count_build_generated_impl_logic,
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {
            PYTHON_STABLE_IDS_IMPORT_ROOT_POLICY_KEY: "aware_test_ontology",
            "function_impl_ownership": "compiler",
            "function_impl_parity_policy": "error",
        }
    )
    renderer.import_overrides = {
        str(home.id): "aware_test_ontology.environment.home",
    }
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )

    renderer.emit_file([], writer)

    out = writer.code.content_part_text.inline_text or ""
    compile(out, "meta_handlers.py", "exec")
    assert render_signature_calls == 2
    assert generated_logic_calls == 1


def test_python_meta_runtime_handlers_renderer_caches_bound_graph_render_facts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    home = make_class(name="Home", is_base=True)
    build = make_function(
        name="build",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.class_,
    )
    rename = make_function(
        name="rename",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.instance,
    )
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=rename.id,
            function_config=rename,
            is_public=True,
            is_constructor=False,
            position=1,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), home),
        ],
        object_projection_graphs=[],
    )

    snake_calls: list[str] = []
    original_to_snake_case = runtime_handlers_meta_module.to_snake_case

    def _count_to_snake_case(value: str) -> str:
        snake_calls.append(value)
        return original_to_snake_case(value)

    monkeypatch.setattr(
        runtime_handlers_meta_module,
        "to_snake_case",
        _count_to_snake_case,
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {PYTHON_STABLE_IDS_IMPORT_ROOT_POLICY_KEY: "aware_test_ontology"}
    )
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    compile(out, "meta_handlers.py", "exec")
    assert "home__build__handler" in out
    assert "home__rename__invocation_handler" in out
    assert snake_calls.count("Home") == 1
    assert (
        renderer._class_function_edge(owner=home, fn=build)
        is home.class_config_function_configs[0]
    )
    assert renderer._input_edges(build) is renderer._input_edges(build)


def test_python_meta_runtime_handlers_renderer_reports_render_phase_timings(
    tmp_path: Path,
    monkeypatch,
) -> None:
    home = make_class(name="Home", is_base=True)
    build = make_function(
        name="build",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.class_,
    )
    rename = make_function(
        name="rename",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.instance,
    )
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=rename.id,
            function_config=rename,
            is_public=True,
            is_constructor=False,
            position=1,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), home),
        ],
        object_projection_graphs=[],
    )
    ticks = iter(index / 1000 for index in range(1000))
    monkeypatch.setattr(
        runtime_handlers_meta_module,
        "perf_counter",
        lambda: next(ticks),
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {PYTHON_STABLE_IDS_IMPORT_ROOT_POLICY_KEY: "aware_test_ontology"}
    )
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    first_out = writer.code.content_part_text.inline_text or ""
    first_timings = renderer.get_render_phase_timings()

    second_code = renderer.create_empty_code()
    second_writer = CodeSectionWriter(
        code=second_code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], second_writer)
    second_out = second_writer.code.content_part_text.inline_text or ""

    compile(first_out, "meta_handlers.py", "exec")
    assert second_out == first_out
    assert set(first_timings) >= {
        "entries",
        "base_imports",
        "compiler_imports",
        "grouped_imports",
        "generated_helpers",
        "constructor_entries",
        "wrappers",
        "invocation_wrappers",
        "registries",
        "exports",
    }
    assert all(duration_s == 0.001 for duration_s in first_timings.values())
    assert renderer.get_render_phase_timings() == first_timings


def test_python_meta_runtime_handlers_renderer_hydrates_constructor_relationships(
    tmp_path: Path,
) -> None:
    instruction_set = make_class(name="FunctionImplInstructionSet", is_base=True)
    target_edge = make_class(name="ClassConfigAttributeConfig", is_base=True)
    value_source = make_class(name="FunctionImplValueSource", is_base=True)

    target_relationship = make_relationship(
        instruction_set,
        target_edge,
        relationship_key="target_class_config_attribute_config",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
    )
    target_relationship.target_class_config = target_edge
    value_source_relationship = make_relationship(
        instruction_set,
        value_source,
        relationship_key="value_source",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
    )
    value_source_relationship.target_class_config = value_source
    instruction_set.class_config_relationships = [
        target_relationship,
        value_source_relationship,
    ]

    build = make_function(
        name="build_via_function_impl_instruction",
        owner_key=function_owner_key(instruction_set),
        is_async=True,
        kind=FunctionKind.class_,
    )
    function_impl_instruction_id = make_attribute(
        name="function_impl_instruction_id",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    target_edge_id = make_attribute(
        name="target_class_config_attribute_config_id",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    value_source_id = make_attribute(
        name="value_source_id",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    build.function_config_attribute_configs = [
        function_attr_link(
            build,
            function_impl_instruction_id,
            type=FunctionAttributeType.input,
            position=0,
            is_identity_key=True,
        ),
        function_attr_link(
            build,
            target_edge_id,
            type=FunctionAttributeType.input,
            position=1,
            is_identity_key=True,
        ),
        function_attr_link(
            build,
            value_source_id,
            type=FunctionAttributeType.input,
            position=2,
            is_identity_key=True,
        ),
    ]
    instruction_set.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=instruction_set.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(
                UUID("00000000-0000-0000-0000-000000000000"),
                instruction_set,
            ),
            make_class_node(
                UUID("00000000-0000-0000-0000-000000000000"),
                target_edge,
            ),
            make_class_node(
                UUID("00000000-0000-0000-0000-000000000000"),
                value_source,
            ),
        ],
        object_projection_graphs=[],
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {
            "function_impl_ownership": "compiler",
            "function_impl_parity_policy": "error",
        }
    )
    renderer.import_overrides = {
        str(instruction_set.id): (
            "aware_test_ontology.function.function_impl_instruction_set"
        ),
        str(target_edge.id): "aware_test_ontology.class_.class_config_attribute_config",
        str(value_source.id): "aware_test_ontology.function.function_impl_value_source",
    }
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""
    helper_start = out.index(
        "async def _call_function_impl_instruction_set__build_via_function_impl_instruction"
    )
    helper_end = out.index("\ndef ", helper_start + 1)
    helper = out[helper_start:helper_end]

    compile(out, "meta_handlers.py", "exec")
    assert "current_handler_session" in out
    assert "_aware_handler_session = current_handler_session()" in helper
    assert (
        "target_class_config_attribute_config = _aware_handler_session.imap_get("
        "ClassConfigAttributeConfig, target_class_config_attribute_config_id)"
    ) in helper
    assert (
        "value_source = _aware_handler_session.imap_get("
        "FunctionImplValueSource, value_source_id)"
    ) in helper
    assert (
        "target_class_config_attribute_config=target_class_config_attribute_config"
        in helper
    )
    assert "value_source=value_source" in helper


def test_python_meta_runtime_handlers_renderer_skips_constructor_self_identity_relationship(
    tmp_path: Path,
) -> None:
    primitive_config = make_class(name="PrimitiveConfig", is_base=True)
    self_relationship = make_relationship(
        primitive_config,
        primitive_config,
        relationship_key="primitive_config",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
    )
    self_relationship.target_class_config = primitive_config
    primitive_type = make_class(name="CodePrimitiveType", is_base=True)
    primitive_type_relationship = make_relationship(
        primitive_config,
        primitive_type,
        relationship_key="primitive_type",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
    )
    primitive_type_relationship.target_class_config = primitive_type
    optional_external_relationship = make_relationship(
        primitive_config,
        primitive_type,
        relationship_key="content_part_text",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=False,
    )
    optional_external_relationship.target_class_config = None
    required_external_relationship = make_relationship(
        primitive_config,
        primitive_type,
        relationship_key="content_part_text_segment",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
    )
    required_external_relationship.target_class_config = None
    primitive_config.class_config_relationships = [
        self_relationship,
        primitive_type_relationship,
        optional_external_relationship,
        required_external_relationship,
    ]

    renderer = PythonRendererRuntimeHandlersAware(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    bindings = renderer._constructor_relationship_bindings(
        class_config=primitive_config,
        input_names={
            "content_part_text_id",
            "content_part_text_segment_id",
            "primitive_config_id",
            "primitive_type_id",
        },
    )

    assert [binding.member_identifier for binding in bindings] == ["primitive_type"]


def test_python_meta_runtime_handlers_renderer_attaches_relationship_construct(
    tmp_path: Path,
) -> None:
    parent = make_class(name="Parent", is_base=True)
    child = make_class(name="Child", is_base=True)

    children_attr = make_attribute(
        name="children",
        owner_key=parent.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_list_desc(child),
    )
    relationship = make_relationship(
        parent,
        child,
        relationship_key="children",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=False,
    )
    relationship.target_class_config = child
    relationship.class_config_relationship_attributes = [
        make_relationship_attribute(
            relationship,
            children_attr,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]
    parent.class_config_relationships = [relationship]

    child_build = make_function(
        name="build",
        owner_key=function_owner_key(child),
        is_async=True,
        kind=FunctionKind.class_,
    )
    parent_id_input = make_attribute(
        name="parent_id",
        owner_key=function_io_owner_key(child_build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    child_build.function_config_attribute_configs = [
        function_attr_link(
            child_build,
            parent_id_input,
            type=FunctionAttributeType.input,
            position=0,
            is_identity_key=True,
            identity_key_origin=FunctionIdentityKeyOrigin.propagated_parent,
        )
    ]
    child.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=child.id,
            function_config_id=child_build.id,
            function_config=child_build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]

    create_child = make_function(
        name="create_child",
        owner_key=function_owner_key(parent),
        is_async=True,
        kind=FunctionKind.instance,
    )
    child_output = make_attribute(
        name="child",
        owner_key=function_io_owner_key(create_child, FunctionAttributeType.output),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_desc(child),
    )
    create_child.function_config_attribute_configs = [
        function_attr_link(
            create_child,
            child_output,
            type=FunctionAttributeType.output,
            position=0,
        ),
    ]
    create_child.invocations = [
        FunctionConfigInvocation(
            function_config_id=create_child.id,
            position=0,
            kind=FunctionInvocationKind.construct,
            target_function_config_id=child_build.id,
            target_function_config=child_build,
            class_config_relationship_id=relationship.id,
            class_config_relationship=relationship,
            capture_name="created",
        ),
    ]
    parent.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=parent.id,
            function_config_id=create_child.id,
            function_config=create_child,
            is_public=True,
            is_constructor=False,
            position=0,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), parent),
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), child),
        ],
        object_projection_graphs=[],
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {
            "function_impl_ownership": "compiler",
            "function_impl_parity_policy": "error",
        }
    )
    renderer.import_overrides = {
        str(parent.id): "aware_test_ontology.environment.parent",
        str(child.id): "aware_test_ontology.environment.child",
    }
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    compile(out, "meta_handlers.py", "exec")
    assert "created = await Child.build(parent_id=parent.id)" in out
    assert "_aware_relationship_member_invocation_0 = parent.children" in out
    assert "if _aware_relationship_member_invocation_0 is None:" in out
    assert "parent.children = []" in out
    assert (
        "getattr(item, 'id', None) != getattr(created, 'id', None) "
        "for item in _aware_relationship_member_invocation_0"
    ) in out
    assert "_aware_relationship_member_invocation_0.append(created)" in out
    assert "return created" in out


def test_python_meta_runtime_handlers_renderer_lowers_body_relationship_construct(
    tmp_path: Path,
) -> None:
    parent = make_class(name="Parent", is_base=True)
    child = make_class(name="Child", is_base=True)

    children_attr = make_attribute(
        name="children",
        owner_key=parent.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_list_desc(child),
    )
    relationship = make_relationship(
        parent,
        child,
        relationship_key="children",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=False,
    )
    relationship.target_class_config = child
    relationship.class_config_relationship_attributes = [
        make_relationship_attribute(
            relationship,
            children_attr,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]
    parent.class_config_relationships = [relationship]

    child_build = make_function(
        name="build",
        owner_key=function_owner_key(child),
        is_async=True,
        kind=FunctionKind.class_,
    )
    parent_id_input = make_attribute(
        name="parent_id",
        owner_key=function_io_owner_key(child_build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    type_child_input = make_attribute(
        name="type",
        owner_key=function_io_owner_key(child_build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.string),
    )
    sequence_child_input = make_attribute(
        name="sequence",
        owner_key=function_io_owner_key(child_build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.integer),
    )
    child_build.function_config_attribute_configs = [
        function_attr_link(
            child_build,
            parent_id_input,
            type=FunctionAttributeType.input,
            position=0,
            is_identity_key=True,
            identity_key_origin=FunctionIdentityKeyOrigin.propagated_parent,
        ),
        function_attr_link(
            child_build,
            type_child_input,
            type=FunctionAttributeType.input,
            position=1,
            is_identity_key=True,
        ),
        function_attr_link(
            child_build,
            sequence_child_input,
            type=FunctionAttributeType.input,
            position=2,
            is_identity_key=True,
        ),
    ]
    child.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=child.id,
            function_config_id=child_build.id,
            function_config=child_build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]

    create_child = make_function(
        name="create_child",
        owner_key=function_owner_key(parent),
        is_async=True,
        kind=FunctionKind.instance,
    )
    create_child.code_section_function = _body_code_section_function(
        "let created = construct children.build(type = type, sequence = sequence)\n"
    )
    type_input = make_attribute(
        name="type",
        owner_key=function_io_owner_key(create_child, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.string),
    )
    sequence_input = make_attribute(
        name="sequence",
        owner_key=function_io_owner_key(create_child, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.integer),
    )
    child_output = make_attribute(
        name="child",
        owner_key=function_io_owner_key(create_child, FunctionAttributeType.output),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_desc(child),
    )
    create_child.function_config_attribute_configs = [
        function_attr_link(
            create_child,
            type_input,
            type=FunctionAttributeType.input,
            position=0,
        ),
        function_attr_link(
            create_child,
            sequence_input,
            type=FunctionAttributeType.input,
            position=1,
        ),
        function_attr_link(
            create_child,
            child_output,
            type=FunctionAttributeType.output,
            position=0,
        ),
    ]
    parent.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=parent.id,
            function_config_id=create_child.id,
            function_config=create_child,
            is_public=True,
            is_constructor=False,
            position=0,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), parent),
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), child),
        ],
        object_projection_graphs=[],
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {
            "function_impl_ownership": "compiler",
            "function_impl_parity_policy": "error",
        }
    )
    renderer.import_overrides = {
        str(parent.id): "aware_test_ontology.environment.parent",
        str(child.id): "aware_test_ontology.environment.child",
    }
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    compile(out, "meta_handlers.py", "exec")
    assert (
        "_aware_constructed_0 = await Child.build(parent_id=parent.id, type=type, sequence=sequence)"
        in out
    )
    assert "_aware_relationship_member_instruction_0 = parent.children" in out
    assert "parent.children = []" in out
    assert (
        "_aware_relationship_member_instruction_0.append(_aware_constructed_0)" in out
    )
    assert "return _aware_constructed_0" in out


def test_python_meta_runtime_handlers_renderer_lowers_receiver_attr_construct_arg(
    tmp_path: Path,
) -> None:
    class_instance = make_class(name="ClassInstance", is_base=True)
    class_instance_attribute = make_class(name="ClassInstanceAttribute", is_base=True)

    source_object_id_attr = make_attribute(
        name="source_object_id",
        owner_key=class_instance.class_fqn,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    class_instance.class_config_attribute_configs = [
        class_attr_link(class_instance, source_object_id_attr, position=0),
    ]

    class_instance_attributes_attr = make_attribute(
        name="class_instance_attributes",
        owner_key=class_instance.class_fqn,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_list_desc(class_instance_attribute),
    )
    relationship = make_relationship(
        class_instance,
        class_instance_attribute,
        relationship_key="class_instance_attributes",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=False,
    )
    relationship.target_class_config = class_instance_attribute
    relationship.class_config_relationship_attributes = [
        make_relationship_attribute(
            relationship,
            class_instance_attributes_attr,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]
    class_instance.class_config_relationships = [relationship]

    create_edge = make_function(
        name="create",
        owner_key=function_owner_key(class_instance_attribute),
        is_async=True,
        kind=FunctionKind.class_,
    )
    class_instance_id_input = make_attribute(
        name="class_instance_id",
        owner_key=function_io_owner_key(create_edge, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    owner_key_input = make_attribute(
        name="owner_key",
        owner_key=function_io_owner_key(create_edge, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    attribute_config_id_input = make_attribute(
        name="attribute_config_id",
        owner_key=function_io_owner_key(create_edge, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    value_root_id_input = make_attribute(
        name="value_root_id",
        owner_key=function_io_owner_key(create_edge, FunctionAttributeType.input),
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    create_edge.function_config_attribute_configs = [
        function_attr_link(
            create_edge,
            class_instance_id_input,
            type=FunctionAttributeType.input,
            position=0,
            is_identity_key=True,
            identity_key_origin=FunctionIdentityKeyOrigin.propagated_parent,
        ),
        function_attr_link(
            create_edge,
            owner_key_input,
            type=FunctionAttributeType.input,
            position=1,
            is_identity_key=True,
        ),
        function_attr_link(
            create_edge,
            attribute_config_id_input,
            type=FunctionAttributeType.input,
            position=2,
            is_identity_key=True,
        ),
        function_attr_link(
            create_edge,
            value_root_id_input,
            type=FunctionAttributeType.input,
            position=3,
        ),
    ]
    class_instance_attribute.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=class_instance_attribute.id,
            function_config_id=create_edge.id,
            function_config=create_edge,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]

    create_attribute = make_function(
        name="create_attribute",
        owner_key=function_owner_key(class_instance),
        is_async=True,
        kind=FunctionKind.instance,
    )
    create_attribute.code_section_function = _body_code_section_function(
        "let created = construct class_instance_attributes.create("
        "owner_key = source_object_id, "
        "attribute_config_id = attribute_config_id, "
        "value_root_id = value_root_id"
        ")\n"
    )
    attribute_config_id = make_attribute(
        name="attribute_config_id",
        owner_key=function_io_owner_key(create_attribute, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    value_root_id = make_attribute(
        name="value_root_id",
        owner_key=function_io_owner_key(create_attribute, FunctionAttributeType.input),
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    edge_output = make_attribute(
        name="class_instance_attribute",
        owner_key=function_io_owner_key(create_attribute, FunctionAttributeType.output),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_desc(class_instance_attribute),
    )
    create_attribute.function_config_attribute_configs = [
        function_attr_link(
            create_attribute,
            attribute_config_id,
            type=FunctionAttributeType.input,
            position=0,
        ),
        function_attr_link(
            create_attribute,
            value_root_id,
            type=FunctionAttributeType.input,
            position=1,
        ),
        function_attr_link(
            create_attribute,
            edge_output,
            type=FunctionAttributeType.output,
            position=0,
        ),
    ]
    class_instance.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=class_instance.id,
            function_config_id=create_attribute.id,
            function_config=create_attribute,
            is_public=True,
            is_constructor=False,
            position=0,
        ),
    ]

    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(
                UUID("00000000-0000-0000-0000-000000000000"),
                class_instance,
            ),
            make_class_node(
                UUID("00000000-0000-0000-0000-000000000000"),
                class_instance_attribute,
            ),
        ],
        object_projection_graphs=[],
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {
            "function_impl_ownership": "compiler",
            "function_impl_parity_policy": "error",
        }
    )
    renderer.import_overrides = {
        str(class_instance.id): "aware_test_ontology.class_.class_instance",
        str(class_instance_attribute.id): (
            "aware_test_ontology.class_.class_instance_attribute"
        ),
    }
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    compile(out, "meta_handlers.py", "exec")
    assert "owner_key=source_object_id" not in out
    assert (
        "owner_key=getattr("
        "class_instance.source_object_id, 'value', class_instance.source_object_id"
        ")"
    ) in out


def test_python_meta_runtime_handlers_renderer_returns_final_construct_after_captured_helper(
    tmp_path: Path,
) -> None:
    home = make_class(name="Home", is_base=True)
    helper = make_class(name="Helper", is_base=True)
    parent_id_attr = make_attribute(
        name="parent_id",
        owner_key=home.class_fqn,
        is_public=True,
        is_required=True,
        is_unique=True,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    key_attr = make_attribute(
        name="key",
        owner_key=home.class_fqn,
        is_public=True,
        is_required=True,
        is_unique=True,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.string),
    )
    home_key_edge = class_attr_link(
        home,
        key_attr,
        position=1,
        is_identity_key=True,
    )
    home_parent_id_edge = class_attr_link(
        home,
        parent_id_attr,
        position=0,
        is_identity_key=True,
    )
    home.class_config_attribute_configs = [home_parent_id_edge, home_key_edge]
    build = make_function(
        name="build",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.class_,
    )
    scope_id_input = make_attribute(
        name="scope_id",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=True,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    scope_id_input_edge = function_attr_link(
        build,
        scope_id_input,
        type=FunctionAttributeType.input,
        position=0,
        is_identity_key=True,
        identity_key_origin=FunctionIdentityKeyOrigin.propagated_parent,
    )
    parent_id_input = make_attribute(
        name="parent_id",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=True,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    parent_id_input_edge = function_attr_link(
        build,
        parent_id_input,
        type=FunctionAttributeType.input,
        position=1,
        is_identity_key=True,
        identity_key_origin=FunctionIdentityKeyOrigin.propagated_parent,
    )
    key_input = make_attribute(
        name="key",
        owner_key=function_io_owner_key(build, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=True,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.string),
    )
    key_input_edge = function_attr_link(
        build,
        key_input,
        type=FunctionAttributeType.input,
        position=2,
        is_identity_key=True,
    )
    home_output = make_attribute(
        name="home",
        owner_key=function_io_owner_key(build, FunctionAttributeType.output),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_desc(home),
    )
    build.function_config_attribute_configs = [
        scope_id_input_edge,
        parent_id_input_edge,
        key_input_edge,
        function_attr_link(
            build,
            home_output,
            type=FunctionAttributeType.output,
            position=0,
        ),
    ]
    helper_build = make_function(
        name="build",
        owner_key=function_owner_key(helper),
        is_async=True,
        kind=FunctionKind.class_,
    )
    helper.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=helper.id,
            function_config_id=helper_build.id,
            function_config=helper_build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]
    build.invocations = [
        FunctionConfigInvocation(
            function_config_id=build.id,
            position=0,
            kind=FunctionInvocationKind.construct,
            target_function_config_id=helper_build.id,
            target_function_config=helper_build,
            capture_name="helper",
        )
    ]
    function_impl = FunctionImpl(
        function_config_id=build.id,
        key="body",
    )
    invoke_payload = FunctionImplInstructionInvoke(
        function_impl_instruction_id=UUID("00000000-0000-0000-0000-000000000101"),
        target_function_config_id=helper_build.id,
        target_function_config=helper_build,
        kind=FunctionImplInvokeKind.construct,
    )
    invoke_instruction = FunctionImplInstruction(
        id=UUID("00000000-0000-0000-0000-000000000101"),
        function_impl_id=function_impl.id,
        type=FunctionImplInstructionType.invoke,
        sequence=0,
        instruction_invoke=invoke_payload,
    )
    construct_value_source = FunctionImplValueSource(
        function_impl_instruction_id=UUID("00000000-0000-0000-0000-000000000102"),
        key="key",
        kind=FunctionImplValueSourceKind.function_input_ref,
        source_function_config_attribute_config=key_input_edge,
        source_function_config_attribute_config_id=key_input_edge.id,
    )
    construct_payload = FunctionImplInstructionConstruct(
        id=UUID("00000000-0000-0000-0000-000000000202"),
        function_impl_instruction_id=UUID("00000000-0000-0000-0000-000000000102"),
        target_class_config_id=home.id,
        target_class_config=home,
        assignments=[
            FunctionImplInstructionConstructAssignment(
                function_impl_instruction_construct_id=UUID(
                    "00000000-0000-0000-0000-000000000202"
                ),
                target_class_config_attribute_config_id=home_key_edge.id,
                target_class_config_attribute_config=home_key_edge,
                value_source_id=construct_value_source.id,
                value_source=construct_value_source,
                position=0,
            )
        ],
    )
    construct_instruction = FunctionImplInstruction(
        id=UUID("00000000-0000-0000-0000-000000000102"),
        function_impl_id=function_impl.id,
        type=FunctionImplInstructionType.construct,
        sequence=1,
        instruction_construct=construct_payload,
        value_sources=[construct_value_source],
    )
    function_impl.instructions = [invoke_instruction, construct_instruction]
    build.function_impl = function_impl
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), home),
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), helper),
        ],
        object_projection_graphs=[],
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {
            "function_impl_ownership": "compiler",
            "function_impl_parity_policy": "error",
        }
    )
    renderer.import_overrides = {
        str(home.id): "aware_test_ontology.environment.home",
        str(helper.id): "aware_test_ontology.environment.helper",
    }
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    compile(out, "meta_handlers.py", "exec")
    assert "helper = await Helper.build()" in out
    assert "_aware_construct_values_1 = {'key': key, 'parent_id': parent_id}" in out
    assert (
        "_aware_construct_identity_values_1 = {**_aware_construct_values_1, "
        "'scope_id': scope_id}"
    ) in out
    assert "return helper" not in out
    assert "return _aware_constructed_" in out or "return Home(key=key)" in out


def test_python_meta_runtime_handlers_renderer_preserves_schema_named_impl(
    tmp_path: Path,
) -> None:
    program_impl = make_class(name="ProgramImpl", is_base=True)
    build = make_function(
        name="build",
        owner_key=function_owner_key(program_impl),
        is_async=True,
        kind=FunctionKind.class_,
    )
    program_impl.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=program_impl.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=True,
            position=0,
        )
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(
                UUID("00000000-0000-0000-0000-000000000000"),
                program_impl,
            ),
        ],
        object_projection_graphs=[],
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_ProgramImplSchemaLayout(base_dir=tmp_path),
    )
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    compile(out, "meta_handlers.py", "exec")
    assert (
        "from aware_test_runtime.handlers.impl.impl.program_impl import build as _impl"
        in out
    )
    assert "aware_test_runtime.handlers.impl.program_impl" not in out


def test_python_meta_runtime_handlers_renderer_keeps_semantic_owner_class_fqn(
    tmp_path: Path,
) -> None:
    home = make_class(name="Home", is_base=True)
    build = make_function(
        name="build",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.class_,
    )
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), home),
        ],
        object_projection_graphs=[],
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.import_overrides = {
        str(home.id): "aware_test_runtime.handlers.impl.environment.home",
    }
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    assert f"owner_key={home.class_fqn!r}" in out
    assert f"owner_class_fqn={home.class_fqn!r}" in out
    assert "aware_test_runtime.handlers.impl.environment.home.Home" not in out


def test_python_meta_runtime_handlers_renderer_uses_branch_id_for_constructor_without_identity(
    tmp_path: Path,
) -> None:
    home = make_class(name="Home", is_base=True)
    build = make_function(
        name="build",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.class_,
    )
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
    ]
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), home),
        ],
        object_projection_graphs=[],
    )

    renderer = PythonMetaRuntimeHandlersRenderer(
        layout_strategy=_Layout(base_dir=tmp_path),
    )
    renderer.set_policy(
        {PYTHON_STABLE_IDS_IMPORT_ROOT_POLICY_KEY: "aware_test_ontology"}
    )
    renderer.bind_object_config_graph(ocg)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""
    helper_start = out.index("def _root_id_home__build")
    helper_end = out.index("\ndef ", helper_start + 1)
    helper = out[helper_start:helper_end]

    compile(out, "meta_handlers.py", "exec")
    assert (
        "def _root_id_home__build(*, request: MetaGraphHandlerExecutionRequest, bound_input: JsonObject):"
        in helper
    )
    assert (
        "return request.execution_plan.staged_call.lane_scope.domain_branch_id"
        in helper
    )
    assert "from aware_test_ontology.stable_ids import stable_home_id" not in helper
