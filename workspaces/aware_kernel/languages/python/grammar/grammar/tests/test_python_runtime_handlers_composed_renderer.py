from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import ClassConfigFunctionConfig
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipType,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionKind,
)
from aware_meta_ontology.function.function_config_invocation import FunctionConfigInvocation
from aware_meta_ontology.function.function_config_invocation_enums import (
    FunctionInvocationKind,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig

from python_grammar.renderer_runtime_handlers import PythonRendererRuntimeHandlers
from python_grammar.renderer_runtime_handlers_aware import (
    PythonRendererRuntimeHandlersAware,
)
from python_grammar.renderer_runtime_handlers_composed import (
    PythonRendererRuntimeHandlersComposed,
)
from python_grammar_test_support import (
    function_attr_link,
    function_io_owner_key,
    function_owner_key,
    make_attribute,
    make_class,
    make_class_node,
    make_function,
    make_relationship,
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
        return Path("handlers") / "impl" / "default" / "thing.py"

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        _ = enum_config
        return Path("handlers") / "_generated" / "handlers.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        _ = function_config
        return Path("handlers") / "_generated" / "handlers.py"

    def get_file_extension(self) -> str:
        return ".py"


def test_runtime_handlers_composed_defaults_to_manual_backend(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("AWARE_PY_RUNTIME_HANDLERS_BACKEND", raising=False)
    renderer = PythonRendererRuntimeHandlersComposed(layout_strategy=_Layout(base_dir=tmp_path))
    assert isinstance(renderer._delegate, PythonRendererRuntimeHandlers)


def test_runtime_handlers_composed_can_select_aware_backend(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AWARE_PY_RUNTIME_HANDLERS_BACKEND", "aware")
    renderer = PythonRendererRuntimeHandlersComposed(layout_strategy=_Layout(base_dir=tmp_path))
    assert isinstance(renderer._delegate, PythonRendererRuntimeHandlersAware)


def test_runtime_handlers_composed_policy_compiler_selects_aware(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AWARE_PY_RUNTIME_HANDLERS_BACKEND", "manual")
    renderer = PythonRendererRuntimeHandlersComposed(layout_strategy=_Layout(base_dir=tmp_path))
    assert isinstance(renderer._delegate, PythonRendererRuntimeHandlers)
    renderer.set_policy({"function_impl_ownership": "compiler"})
    assert isinstance(renderer._delegate, PythonRendererRuntimeHandlersAware)


def test_runtime_handlers_composed_policy_authored_selects_manual(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AWARE_PY_RUNTIME_HANDLERS_BACKEND", "aware")
    renderer = PythonRendererRuntimeHandlersComposed(layout_strategy=_Layout(base_dir=tmp_path))
    assert isinstance(renderer._delegate, PythonRendererRuntimeHandlersAware)
    renderer.set_policy({"function_impl_ownership": "authored"})
    assert isinstance(renderer._delegate, PythonRendererRuntimeHandlers)


def test_runtime_handlers_composed_preserves_profile_inputs_across_delegate_switches(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("AWARE_PY_RUNTIME_HANDLERS_BACKEND", "manual")
    renderer = PythonRendererRuntimeHandlersComposed(layout_strategy=_Layout(base_dir=tmp_path))
    profile_inputs = {
        "api.interface_spec": {"apis": []},
        "api.invocation_manifest": {"endpoints": []},
        "api.public_package_plan": {"package_name": "aware_test_api"},
    }

    renderer.bind_profile_inputs(profile_inputs)
    assert renderer.profile_inputs == profile_inputs

    renderer.set_policy({"function_impl_ownership": "compiler"})
    assert isinstance(renderer._delegate, PythonRendererRuntimeHandlersAware)
    assert renderer.profile_inputs == profile_inputs

    renderer.set_policy({"function_impl_ownership": "authored"})
    assert isinstance(renderer._delegate, PythonRendererRuntimeHandlers)
    assert renderer.profile_inputs == profile_inputs


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


def test_runtime_handlers_aware_warns_on_unresolved_logic_when_compiler_owned(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("AWARE_PY_RUNTIME_HANDLERS_BACKEND", "manual")
    home = make_class(name="Home", is_base=True)
    unresolved_fn = make_function(
        name="unresolved",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.instance,
    )
    output_attr = make_attribute(
        name="value",
        owner_key=function_io_owner_key(unresolved_fn, FunctionAttributeType.output),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.string),
    )
    unresolved_fn.function_config_attribute_configs = [
        function_attr_link(unresolved_fn, output_attr, type=FunctionAttributeType.output, position=0),
    ]
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=unresolved_fn.id,
            function_config=unresolved_fn,
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

    renderer = PythonRendererRuntimeHandlersComposed(layout_strategy=_Layout(base_dir=tmp_path))
    renderer.set_policy({"function_impl_ownership": "compiler", "function_impl_parity_policy": "error"})
    renderer.bind_object_config_graph(ocg)

    code = renderer.create_empty_code()
    writer = CodeSectionWriter(code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent)
    renderer.emit_file([home, unresolved_fn], writer)
    out = writer.code.content_part_text.inline_text or ""

    assert 'raise NotImplementedError("AWARE: implement handler logic")' in out
    assert any("FunctionImpl compiler ownership unresolved for Home.unresolved" in w for w in renderer.get_warnings())


def test_runtime_handlers_aware_wraps_long_function_docstring_lines(tmp_path: Path) -> None:
    home = make_class(name="Home", is_base=True)
    described_fn = make_function(
        name="described",
        owner_key=function_owner_key(home),
        description=(
            "Validates a settlement and materializes a deterministic smart-contract settlement receipt, "
            "without finalizing reservation."
        ),
        is_async=True,
        kind=FunctionKind.instance,
    )
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=described_fn.id,
            function_config=described_fn,
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

    renderer = PythonRendererRuntimeHandlersAware(layout_strategy=_Layout(base_dir=tmp_path))
    renderer.bind_object_config_graph(ocg)

    code = renderer.create_empty_code()
    writer = CodeSectionWriter(code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent)
    renderer.emit_file([home, described_fn], writer)
    out = writer.code.content_part_text.inline_text or ""

    assert (
        "Validates a settlement and materializes a deterministic smart-contract settlement receipt, "
        "without finalizing reservation."
    ) not in out
    assert max(len(line) for line in out.splitlines()) <= 120


def test_runtime_handlers_manual_wraps_long_function_docstring_lines(tmp_path: Path) -> None:
    home = make_class(name="Home", is_base=True)
    described_fn = make_function(
        name="described",
        owner_key=function_owner_key(home),
        description=(
            "Validates a settlement and materializes a deterministic smart-contract settlement receipt, "
            "without finalizing reservation."
        ),
        is_async=True,
        kind=FunctionKind.instance,
    )
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=described_fn.id,
            function_config=described_fn,
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

    renderer = PythonRendererRuntimeHandlers(layout_strategy=_Layout(base_dir=tmp_path))
    renderer.bind_object_config_graph(ocg)

    code = renderer.create_empty_code()
    writer = CodeSectionWriter(code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent)
    renderer.emit_file([home, described_fn], writer)
    out = writer.code.content_part_text.inline_text or ""

    assert (
        "Validates a settlement and materializes a deterministic smart-contract settlement receipt, "
        "without finalizing reservation."
    ) not in out
    assert max(len(line) for line in out.splitlines()) <= 120


def test_runtime_handlers_aware_falls_back_to_invocations_when_impl_unavailable(tmp_path: Path) -> None:
    home = make_class(name="Home", is_base=True)
    door = make_class(name="Door", is_base=True)

    door_create = make_function(
        name="create_via_home",
        owner_key=function_owner_key(door),
        is_async=True,
        kind=FunctionKind.instance,
    )
    add_door = make_function(
        name="add_door",
        owner_key=function_owner_key(home),
        is_async=True,
        kind=FunctionKind.instance,
    )

    home_id_input = make_attribute(
        name="home_id",
        owner_key=function_io_owner_key(door_create, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.uuid),
    )
    label_input = make_attribute(
        name="label",
        owner_key=function_io_owner_key(door_create, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.string),
    )
    door_output = make_attribute(
        name="door",
        owner_key=function_io_owner_key(door_create, FunctionAttributeType.output),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_desc(door),
    )

    door_create.function_config_attribute_configs = [
        function_attr_link(door_create, home_id_input, type=FunctionAttributeType.input, position=0),
        function_attr_link(door_create, label_input, type=FunctionAttributeType.input, position=1),
        function_attr_link(door_create, door_output, type=FunctionAttributeType.output, position=0),
    ]

    add_door.function_config_attribute_configs = [
        function_attr_link(add_door, label_input, type=FunctionAttributeType.input, position=0),
        function_attr_link(add_door, door_output, type=FunctionAttributeType.output, position=0),
    ]
    home_doors_relationship = make_relationship(
        home,
        door,
        relationship_key="doors",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
    )
    home.class_config_relationships = [home_doors_relationship]
    add_door.invocations = [
        FunctionConfigInvocation(
            function_config_id=add_door.id,
            position=0,
            kind=FunctionInvocationKind.construct,
            target_function_config_id=door_create.id,
            target_function_config=door_create,
            class_config_relationship_id=home_doors_relationship.id,
            class_config_relationship=home_doors_relationship,
            capture_name="created",
        )
    ]

    door.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=door.id,
            function_config_id=door_create.id,
            function_config=door_create,
            is_public=True,
            is_constructor=True,
            position=0,
        )
    ]
    home.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=home.id,
            function_config_id=add_door.id,
            function_config=add_door,
            is_public=True,
            is_constructor=False,
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
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), home),
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), door),
        ],
        object_projection_graphs=[],
    )

    layout = _Layout(base_dir=tmp_path)
    renderer = PythonRendererRuntimeHandlersAware(layout_strategy=layout)
    renderer.import_overrides = {
        str(home.id): "aware_test_ontology.home.home",
        str(door.id): "aware_test_ontology.home.door",
    }
    renderer.bind_object_config_graph(ocg)

    code = renderer.create_empty_code()
    writer = CodeSectionWriter(code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent)
    renderer.emit_file([home, add_door], writer)
    out = writer.code.content_part_text.inline_text or ""

    assert "created = await Door.create_via_home(home_id=home.id, label=label)" in out
    assert "return created" in out
    assert renderer.get_warnings() == []
