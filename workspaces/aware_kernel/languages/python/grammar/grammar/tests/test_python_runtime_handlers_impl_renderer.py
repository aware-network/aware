from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionKind
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

from python_grammar.renderer_runtime_handlers import (
    PythonRendererRuntimeHandlerImplStubs,
)
from python_grammar_test_support import (
    function_attr_link,
    function_io_owner_key,
    function_owner_key,
    make_attribute,
    make_class,
    make_class_node,
    make_function,
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
        return Path("conversation") / "conversation.py"

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        _ = enum_config
        return Path("handlers") / "_generated" / "handlers.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        _ = function_config
        return Path("handlers") / "_generated" / "handlers.py"

    def get_file_extension(self) -> str:
        return ".py"


def _render(
    renderer: PythonRendererRuntimeHandlerImplStubs,
    meta_objects: list[object],
) -> str:
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file(meta_objects, writer)
    return writer.code.content_part_text.inline_text or ""


def _class_desc(target: ClassConfig) -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config=target,
        class_config_id=target.id,
    )


def test_runtime_handlers_impl_renderer_has_no_generated_registry_path(
    tmp_path: Path,
) -> None:
    renderer = PythonRendererRuntimeHandlerImplStubs(
        layout_strategy=_Layout(base_dir=tmp_path)
    )

    assert renderer.extra_output_paths() == []
    assert _render(renderer, []) == ""


def test_runtime_handlers_impl_renderer_emits_only_impl_stub(
    tmp_path: Path,
) -> None:
    thing = make_class(name="Thing", is_base=True)
    build = make_function(
        name="build",
        owner_key=function_owner_key(thing),
        is_async=True,
        kind=FunctionKind.instance,
    )
    thing.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=thing.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=False,
            position=0,
        )
    ]

    renderer = PythonRendererRuntimeHandlerImplStubs(
        layout_strategy=_Layout(base_dir=tmp_path)
    )

    assert renderer.layout_strategy.get_class_file_path(thing) == (
        Path("handlers") / "impl" / "conversation" / "conversation.py"
    )
    source = _render(renderer, [thing, build])

    assert "async def build(" in source
    assert "# --- AWARE: LOGIC START build" in source
    assert "FUNCTION_IMPLS" not in source
    assert "handlers._generated.handlers" not in source


def test_runtime_handlers_impl_renderer_uses_runtime_policy_for_lowered_constructor_logic(
    tmp_path: Path,
) -> None:
    source_class = make_class(name="Code", is_base=True)
    source_create = make_function(
        name="create",
        owner_key=function_owner_key(source_class),
        is_async=True,
        kind=FunctionKind.class_,
    )
    source_class.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=source_class.id,
            function_config_id=source_create.id,
            function_config=source_create,
            is_public=True,
            is_constructor=True,
            position=0,
        )
    ]

    runtime_class = make_class(name="Code", is_base=True)
    runtime_class.class_fqn = source_class.class_fqn
    runtime_create = make_function(
        name="create_via_code_package_code",
        owner_key=function_owner_key(runtime_class),
        is_async=True,
        kind=FunctionKind.class_,
    )
    runtime_class.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=runtime_class.id,
            function_config_id=runtime_create.id,
            function_config=runtime_create,
            is_public=True,
            is_constructor=True,
            position=0,
        )
    ]
    runtime_graph = ObjectConfigGraph(
        name="aware_code_runtime",
        hash="runtime-hash",
        fqn_prefix="aware_code",
        language=CodeLanguage.aware,
    )
    runtime_graph.object_config_graph_nodes = [
        make_class_node(runtime_graph.id, runtime_class)
    ]

    layout = _Layout(base_dir=tmp_path)
    unconfigured_renderer = PythonRendererRuntimeHandlerImplStubs(
        layout_strategy=layout
    )
    impl_path = tmp_path / unconfigured_renderer.layout_strategy.get_class_file_path(
        runtime_class
    )
    impl_path.parent.mkdir(parents=True, exist_ok=True)
    impl_path.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "",
                "# --- AWARE: USER_IMPORTS START",
                "# --- AWARE: USER_IMPORTS END",
                "",
                "async def create_via_code_package_code():",
                "    # --- AWARE: LOGIC START create_via_code_package_code",
                "    return None",
                "    # --- AWARE: LOGIC END create_via_code_package_code",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown/legacy logic blocks"):
        _render(unconfigured_renderer, [source_class, source_create])

    renderer = PythonRendererRuntimeHandlerImplStubs(layout_strategy=layout)
    renderer.set_policy({"stable_ids_source_graph": runtime_graph})

    source = _render(renderer, [source_class, source_create])

    assert "async def create_via_code_package_code(" in source
    assert "# --- AWARE: LOGIC START create_via_code_package_code" in source
    assert "async def create(" not in source


def test_runtime_handlers_impl_renderer_preserves_required_managed_import_modules_without_overrides(
    tmp_path: Path,
) -> None:
    thing = make_class(name="Thing", is_base=True)
    door = make_class(name="Door", is_base=True)
    build = make_function(
        name="build",
        owner_key=function_owner_key(thing),
        is_async=True,
        kind=FunctionKind.instance,
    )
    output_attr = make_attribute(
        name="door",
        owner_key=function_io_owner_key(build, FunctionAttributeType.output),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_desc(door),
    )
    build.function_config_attribute_configs = [
        function_attr_link(
            build,
            output_attr,
            type=FunctionAttributeType.output,
            position=0,
        ),
    ]
    thing.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=thing.id,
            function_config_id=build.id,
            function_config=build,
            is_public=True,
            is_constructor=False,
            position=0,
        )
    ]
    output_path = tmp_path / "handlers" / "impl" / "conversation" / "conversation.py"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        """from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Test Ontology
from aware_test_ontology.conversation.conversation import Thing
from aware_test_ontology.conversation.door import (
    Door,
)
from aware_test_ontology.conversation.legacy import LegacyType

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(thing: Thing) -> Door:
    # --- AWARE: LOGIC START build
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build
""",
        encoding="utf-8",
    )

    renderer = PythonRendererRuntimeHandlerImplStubs(
        layout_strategy=_Layout(base_dir=tmp_path)
    )

    source = _render(renderer, [thing, build])

    assert "from aware_test_ontology.conversation.conversation import Thing" in source
    assert "from aware_test_ontology.conversation.door import Door" in source
    assert "LegacyType" not in source
    assert "async def build(thing: Thing) -> Door:" in source
