from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import pytest

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionKind,
)
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)

from python_grammar.renderer_runtime_handlers import (
    PythonRendererRuntimeHandlers,
    _normalize_preserved_user_imports_for_runtime_handlers,
    _normalize_runtime_handler_imports,
    runtime_handler_impl_module_import,
    runtime_handler_impl_relative_path,
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
class _HandlersLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = "aware_test_runtime"

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_file_extension(self) -> str:
        return ".py"

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        _ = class_config
        return Path("handlers") / "impl" / "identity" / "thing.py"

    def get_enum_file_path(self, enum_config):  # pragma: no cover
        _ = enum_config
        return Path("handlers") / "_generated" / "handlers.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        _ = function_config
        return Path("handlers") / "_generated" / "handlers.py"


@dataclass(frozen=True)
class _KeywordHandlersLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = "aware_test_runtime"

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_file_extension(self) -> str:
        return ".py"

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        _ = class_config
        return Path("handlers") / "impl" / "class" / "class.py"

    def get_enum_file_path(self, enum_config):  # pragma: no cover
        _ = enum_config
        return Path("handlers") / "_generated" / "handlers.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        _ = function_config
        return Path("handlers") / "_generated" / "handlers.py"


@dataclass(frozen=True)
class _AuthoredNodePathLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = "aware_test_runtime"

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_file_extension(self) -> str:
        return ".py"

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        _ = class_config
        return Path("environment") / "home.py"

    def get_enum_file_path(self, enum_config):  # pragma: no cover
        _ = enum_config
        return Path("handlers") / "_generated" / "handlers.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        _ = function_config
        return Path("handlers") / "_generated" / "handlers.py"


@dataclass(frozen=True)
class _GraphConfigPathLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = "aware_meta"

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_file_extension(self) -> str:
        return ".py"

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        _ = class_config
        return Path("graph") / "config" / "object_config_graph.py"

    def get_enum_file_path(self, enum_config):  # pragma: no cover
        _ = enum_config
        return Path("handlers") / "_generated" / "handlers.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        _ = function_config
        return Path("handlers") / "_generated" / "handlers.py"


@dataclass(frozen=True)
class _ProgramImplSchemaLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = "aware_test_runtime"

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_file_extension(self) -> str:
        return ".py"

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        _ = class_config
        return Path("program") / "impl" / "program_impl.py"

    def get_enum_file_path(self, enum_config):  # pragma: no cover
        _ = enum_config
        return Path("handlers") / "_generated" / "handlers.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        _ = function_config
        return Path("handlers") / "_generated" / "handlers.py"


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


def _make_test_graph() -> tuple[ObjectConfigGraph, ClassConfig, FunctionConfig]:
    cls = make_class(name="Thing", is_base=True)

    build_fn = make_function(
        name="build",
        owner_key=function_owner_key(cls),
        is_async=True,
        kind=FunctionKind.class_,
    )
    build_in = make_attribute(
        name="initial",
        owner_key=function_io_owner_key(build_fn, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.integer),
    )
    build_out = make_attribute(
        name="value",
        owner_key=function_io_owner_key(build_fn, FunctionAttributeType.output),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_desc(cls),
    )
    build_fn.function_config_attribute_configs = [
        function_attr_link(
            build_fn, build_in, type=FunctionAttributeType.input, position=0
        ),
        function_attr_link(
            build_fn, build_out, type=FunctionAttributeType.output, position=0
        ),
    ]

    add_fn = make_function(
        name="add",
        owner_key=function_owner_key(cls),
        is_async=True,
        kind=FunctionKind.instance,
    )
    add_in = make_attribute(
        name="delta",
        owner_key=function_io_owner_key(add_fn, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_primitive_desc(CodePrimitiveBaseType.integer),
    )
    add_fn.function_config_attribute_configs = [
        function_attr_link(add_fn, add_in, type=FunctionAttributeType.input, position=0)
    ]

    cls.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=cls.id,
            function_config=build_fn,
            function_config_id=build_fn.id,
            is_public=True,
            is_constructor=True,
            position=0,
        ),
        ClassConfigFunctionConfig(
            class_config_id=cls.id,
            function_config=add_fn,
            function_config_id=add_fn.id,
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
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), cls)
        ],
        object_projection_graphs=[],
    )
    return ocg, cls, build_fn


def test_runtime_handler_impl_import_uses_authored_node_path_under_impl_root(
    tmp_path: Path,
) -> None:
    cls = make_class(name="Home", is_base=True)
    layout = _AuthoredNodePathLayout(base_dir=tmp_path)

    assert (
        runtime_handler_impl_relative_path(
            layout_strategy=layout,
            class_config=cls,
        )
        == Path("handlers") / "impl" / "environment" / "home.py"
    )
    assert (
        runtime_handler_impl_module_import(
            layout_strategy=layout,
            class_config=cls,
            import_root="aware_test_runtime",
        )
        == "aware_test_runtime.handlers.impl.environment.home"
    )


def test_runtime_handler_impl_import_flattens_meta_graph_category(
    tmp_path: Path,
) -> None:
    cls = make_class(name="ObjectConfigGraph", is_base=True)
    layout = _GraphConfigPathLayout(base_dir=tmp_path)

    assert (
        runtime_handler_impl_relative_path(
            layout_strategy=layout,
            class_config=cls,
        )
        == Path("handlers") / "impl" / "config" / "object_config_graph.py"
    )
    assert (
        runtime_handler_impl_module_import(
            layout_strategy=layout,
            class_config=cls,
            import_root="aware_meta",
        )
        == "aware_meta.handlers.impl.config.object_config_graph"
    )


def test_runtime_handler_impl_import_preserves_schema_named_impl(
    tmp_path: Path,
) -> None:
    cls = make_class(name="ProgramImpl", is_base=True)
    layout = _ProgramImplSchemaLayout(base_dir=tmp_path)

    assert (
        runtime_handler_impl_relative_path(
            layout_strategy=layout,
            class_config=cls,
        )
        == Path("handlers") / "impl" / "impl" / "program_impl.py"
    )
    assert (
        runtime_handler_impl_module_import(
            layout_strategy=layout,
            class_config=cls,
            import_root="aware_test_runtime",
        )
        == "aware_test_runtime.handlers.impl.impl.program_impl"
    )


def test_python_runtime_handlers_renderer_preserves_user_blocks(tmp_path: Path) -> None:
    ocg, cls, fn = _make_test_graph()

    layout = _HandlersLayout(base_dir=tmp_path)
    renderer = PythonRendererRuntimeHandlers(layout_strategy=layout)
    renderer.import_overrides = {str(cls.id): "aware_test_ontology.identity.thing"}
    renderer.bind_object_config_graph(ocg)

    # First render (stub)
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    renderer.emit_file([cls, fn], writer)
    out = writer.code.content_part_text.inline_text or ""
    assert "# --- AWARE: USER_IMPORTS START" in out
    assert "# --- AWARE: USER_IMPORTS END" in out
    assert "# --- AWARE: LOGIC START build" in out
    assert "# --- AWARE: LOGIC END build" in out
    assert "# --- AWARE: LOGIC START add" in out
    assert "# --- AWARE: LOGIC END add" in out

    assert "from uuid import UUID" not in out
    assert out.count("from aware_test_ontology.identity.thing import Thing") == 1

    # Managed imports must contain TYPE_CHECKING and all type-only imports.
    managed_block = out.split("# --- AWARE: MANAGED_IMPORTS START\n", 1)[1].split(
        "# --- AWARE: MANAGED_IMPORTS END\n", 1
    )[0]
    assert "from uuid import UUID" not in managed_block
    assert "from aware_test_ontology.identity.thing import Thing" in managed_block

    # Write a file with edits in the managed blocks.
    path = (tmp_path / layout.get_class_file_path(cls)).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    edited = out.replace(
        "# --- AWARE: USER_IMPORTS START\n# --- AWARE: USER_IMPORTS END",
        "# --- AWARE: USER_IMPORTS START\nfrom x import y\n# --- AWARE: USER_IMPORTS END",
    )
    edited = edited.replace(
        'raise NotImplementedError("AWARE: implement handler logic")',
        "return initial",
    )
    path.write_text(edited, encoding="utf-8")

    # Second render must preserve user edits (imports + logic), without indentation drift.
    code2 = renderer.create_empty_code()
    writer2 = CodeSectionWriter(
        code=code2, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    renderer.emit_file([cls, fn], writer2)
    out2 = writer2.code.content_part_text.inline_text or ""

    assert "from x import y" in out2
    assert "return initial" in out2
    # Ensure logic line is indented exactly once (4 spaces).
    assert "\n    return initial\n" in out2


def test_python_runtime_handlers_renderer_normalizes_meta_user_imports() -> None:
    preserved_imports = (
        "# Runtime\n"
        "from aware_runtime.function_call.author import resolve_author_id\n"
        "from aware_runtime.function_call.handler_execution_context import (\n"
        "    current_function_call,\n"
        "    current_handler_session,\n"
        ")\n"
    )

    normalized = _normalize_preserved_user_imports_for_runtime_handlers(
        import_root="aware_meta",
        preserved_imports=preserved_imports,
    )

    assert "aware_runtime" not in normalized
    assert "# Meta Runtime\n" in normalized
    assert "from aware_meta.runtime.author import resolve_author_id" in normalized
    assert "from aware_meta.runtime.handler_context import (" in normalized


def test_python_runtime_handlers_renderer_leaves_non_meta_user_imports_unchanged() -> (
    None
):
    preserved_imports = (
        "from aware_runtime.function_call.handler_execution_context import "
        "current_handler_session\n"
    )

    normalized = _normalize_preserved_user_imports_for_runtime_handlers(
        import_root="aware_identity",
        preserved_imports=preserved_imports,
    )

    assert normalized == preserved_imports


def test_python_runtime_handlers_renderer_normalizes_embedded_import_symbols() -> None:
    imports = _normalize_runtime_handler_imports(
        {
            "aware_code_ontology.code.code_enums": {
                "CodeLanguage\n        from uuid import UUID",
            },
        }
    )

    assert imports == {
        "aware_code_ontology.code.code_enums": {"CodeLanguage"},
        "uuid": {"UUID"},
    }


def test_python_runtime_handlers_renderer_warns_on_meta_user_import_migration(
    tmp_path: Path,
) -> None:
    ocg, cls, fn = _make_test_graph()
    layout = _HandlersLayout(base_dir=tmp_path, import_root="aware_meta")
    renderer = PythonRendererRuntimeHandlers(layout_strategy=layout)
    renderer.import_overrides = {str(cls.id): "aware_test_ontology.identity.thing"}
    renderer.bind_object_config_graph(ocg)

    path = (tmp_path / layout.get_class_file_path(cls)).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            (
                "# --- AWARE: MANAGED_IMPORTS START",
                "# --- AWARE: MANAGED_IMPORTS END",
                "",
                "# --- AWARE: USER_IMPORTS START",
                "# Runtime",
                "from aware_runtime.function_call.handler_execution_context import (",
                "    current_handler_session,",
                ")",
                "# --- AWARE: USER_IMPORTS END",
                "",
                "async def build(initial: int) -> object:",
                "    # --- AWARE: LOGIC START build",
                "    return initial",
                "    # --- AWARE: LOGIC END build",
                "",
                "async def add(delta: int) -> None:",
                "    # --- AWARE: LOGIC START add",
                "    return None",
                "    # --- AWARE: LOGIC END add",
                "",
            )
        ),
        encoding="utf-8",
    )

    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    renderer.emit_file([cls, fn], writer)

    out = writer.code.content_part_text.inline_text or ""
    warnings = renderer.get_warnings()

    assert "aware_runtime.function_call" not in out
    assert "from aware_meta.runtime.handler_context import (" in out
    assert len(warnings) == 1
    assert "Deprecated Meta handler USER_IMPORTS migrated" in warnings[0]
    assert path.as_posix() in warnings[0]


def test_python_runtime_handlers_renderer_skips_classes_without_functions(
    tmp_path: Path,
) -> None:
    cls = make_class(name="Empty", is_base=True)
    ocg = ObjectConfigGraph(
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), cls)
        ],
        object_projection_graphs=[],
    )

    layout = _HandlersLayout(base_dir=tmp_path)
    renderer = PythonRendererRuntimeHandlers(layout_strategy=layout)
    renderer.import_overrides = {str(cls.id): "aware_test_ontology.identity.empty"}
    renderer.bind_object_config_graph(ocg)

    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    renderer.emit_file([cls], writer)
    out = writer.code.content_part_text.inline_text or ""
    assert out.strip() == ""


def test_python_runtime_handlers_renderer_emits_registry_with_new_impl_names(
    tmp_path: Path,
) -> None:
    ocg, cls, fn = _make_test_graph()
    layout = _HandlersLayout(base_dir=tmp_path)
    renderer = PythonRendererRuntimeHandlers(layout_strategy=layout)
    renderer.import_overrides = {str(cls.id): "aware_test_ontology.identity.thing"}
    renderer.bind_object_config_graph(ocg)

    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    # The generated registry is emitted when no meta objects are present (extra output path).
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    assert "AWARE_HANDLERS" in out
    assert (
        "from aware_test_runtime.handlers.impl.identity.thing import build as _impl"
        in out
    )
    assert (
        "from aware_test_runtime.handlers.impl.identity.thing import add as _impl"
        in out
    )
    assert "thing_build" not in out
    assert "from typing import TYPE_CHECKING" in out
    assert "TYPE_CHECKING" in out
    assert "cast" not in out
    assert "from typing import Any" not in out
    assert (
        "async def thing__build__handler(session: Session, ctx: HandlerContext, "
        "orm_class: type[ORMModel], args: list[object], kwargs: dict[str, object], "
        "function_call: FunctionCall) -> tuple[ORMModel, object]:"
    ) in out
    assert (
        "async def thing__add__handler(session: Session, ctx: HandlerContext, orm_model: ORMModel, "
        "args: list[object], kwargs: dict[str, object], function_call: FunctionCall) -> object:"
    ) in out
    assert "_raw_initial: object | None = None" in out
    assert "initial: int = TypeAdapter(int).validate_python(_raw_initial)" in out


def test_python_runtime_handlers_renderer_preserves_full_via_constructor_name(
    tmp_path: Path,
) -> None:
    cls = make_class(name="SectionConfig", is_base=True)
    build_via_fn = make_function(
        name="build_via_layout_config_section_config",
        owner_key=function_owner_key(cls),
        is_async=True,
        kind=FunctionKind.class_,
    )
    cls.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=cls.id,
            function_config=build_via_fn,
            function_config_id=build_via_fn.id,
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
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), cls)
        ],
        object_projection_graphs=[],
    )

    layout = _HandlersLayout(base_dir=tmp_path)
    renderer = PythonRendererRuntimeHandlers(layout_strategy=layout)
    renderer.import_overrides = {
        str(cls.id): "aware_test_ontology.section.section_config"
    }
    renderer.bind_object_config_graph(ocg)

    # Emit impl file first so generated registry binds to rendered classes.
    code_impl = renderer.create_empty_code()
    writer_impl = CodeSectionWriter(
        code=code_impl, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    renderer.emit_file([cls, build_via_fn], writer_impl)
    impl_out = writer_impl.code.content_part_text.inline_text or ""
    assert "async def build_via_layout_config_section_config(" in impl_out

    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    assert "build_via_layout_config_section_config as _impl" in out
    assert "import build_via_layout as _impl" not in out


def test_python_runtime_handlers_renderer_rejects_legacy_logic_blocks(
    tmp_path: Path,
) -> None:
    ocg, cls, fn = _make_test_graph()

    layout = _HandlersLayout(base_dir=tmp_path)
    renderer = PythonRendererRuntimeHandlers(layout_strategy=layout)
    renderer.import_overrides = {str(cls.id): "aware_test_ontology.identity.thing"}
    renderer.bind_object_config_graph(ocg)

    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    renderer.emit_file([cls, fn], writer)
    out = writer.code.content_part_text.inline_text or ""

    legacy = out.replace(
        "# --- AWARE: LOGIC START build", "# --- AWARE: LOGIC START thing_build"
    ).replace("# --- AWARE: LOGIC END build", "# --- AWARE: LOGIC END thing_build")
    legacy = legacy.replace(
        "# --- AWARE: LOGIC START add", "# --- AWARE: LOGIC START thing_add"
    ).replace("# --- AWARE: LOGIC END add", "# --- AWARE: LOGIC END thing_add")

    path = (tmp_path / layout.get_class_file_path(cls)).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(legacy, encoding="utf-8")

    code2 = renderer.create_empty_code()
    writer2 = CodeSectionWriter(
        code=code2, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    with pytest.raises(ValueError, match=r"unknown/legacy logic blocks") as excinfo:
        renderer.emit_file([cls, fn], writer2)

    message = str(excinfo.value)
    assert "class='Thing'" in message
    assert f"impl_output={path}" in message
    assert "unknown_logic_blocks=['thing_add', 'thing_build']" in message
    assert "current_function_names=['add', 'build']" in message


def test_python_runtime_handlers_renderer_escapes_keyword_impl_module_segments(
    tmp_path: Path,
) -> None:
    cls = make_class(name="Class", is_base=True)
    build_fn = make_function(
        name="build",
        owner_key=function_owner_key(cls),
        is_async=True,
        kind=FunctionKind.class_,
    )
    cls.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=cls.id,
            function_config=build_fn,
            function_config_id=build_fn.id,
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
            make_class_node(UUID("00000000-0000-0000-0000-000000000000"), cls)
        ],
        object_projection_graphs=[],
    )

    layout = _KeywordHandlersLayout(base_dir=tmp_path)
    renderer = PythonRendererRuntimeHandlers(layout_strategy=layout)
    renderer.import_overrides = {str(cls.id): "aware_test_ontology.class_.class_"}
    renderer.bind_object_config_graph(ocg)

    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    renderer.emit_file([], writer)
    out = writer.code.content_part_text.inline_text or ""

    assert (
        "from aware_test_runtime.handlers.impl.class_.class_ import build as _impl"
        in out
    )
    assert "from aware_meta.runtime.generated_handlers import constructor\n" in out
    assert (
        "from aware_meta.runtime.generated_handlers import constructor, instance"
        not in out
    )
    assert "from typing import TYPE_CHECKING" in out
    assert "from typing import TYPE_CHECKING, cast" not in out
    assert "from pydantic import TypeAdapter" not in out
