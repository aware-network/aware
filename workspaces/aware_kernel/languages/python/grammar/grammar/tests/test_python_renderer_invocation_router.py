from dataclasses import dataclass
from pathlib import Path

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
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)

from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionKind,
)

from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)

from python_grammar.meta_language_plugin import PYTHON_META_PLUGIN
from python_grammar.renderer import PythonRenderer
from python_grammar.renderer_policy import PythonRenderPolicy
from python_grammar_test_support import (
    function_attr_link,
    function_io_owner_key,
    function_owner_key,
    make_attribute,
    make_class,
    make_function,
)


@dataclass(frozen=True)
class _TestLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    @property
    def import_root(self) -> str:
        return "aware_test_ontology"

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path("default") / "models.py"

    def get_enum_file_path(self, enum_config) -> Path:  # pragma: no cover
        return Path("default") / "models.py"

    def get_function_file_path(
        self, function_config: FunctionConfig
    ) -> Path:  # pragma: no cover
        return Path("default") / "models.py"

    def get_file_extension(self) -> str:
        return ".py"

    def get_module_import_path(self, file_path: Path) -> str:
        parts = list(file_path.parts)
        if parts:
            parts[-1] = Path(parts[-1]).stem
        return ".".join(p for p in parts if p).strip(".")


def _class_descriptor(target: ClassConfig) -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config=target,
        class_config_id=target.id,
    )


def test_python_renderer_uses_runtime_invocation_router_for_function_facades() -> None:
    cls = make_class(name="Thing", is_base=True)

    prim = build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    prim_cfg = PrimitiveConfig(primitive_type=prim, primitive_type_id=prim.id)
    desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=prim_cfg,
        primitive_config_id=prim_cfg.id,
    )
    fn = make_function(
        name="do",
        owner_key=function_owner_key(cls),
        is_async=True,
        kind=FunctionKind.instance,
    )
    input_attr = make_attribute(
        name="text",
        owner_key=function_io_owner_key(fn, FunctionAttributeType.input),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=desc,
        type_descriptor_id=desc.id,
    )

    fn.function_config_attribute_configs = [
        function_attr_link(fn, input_attr, type=FunctionAttributeType.input, position=0)
    ]
    cls.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=cls.id,
            function_config=fn,
            function_config_id=fn.id,
            is_public=True,
            is_constructor=False,
            position=0,
        )
    ]

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    renderer.emit_file(
        [cls, fn], writer, schema="default", class_to_class_config_map={cls.id: cls}
    )

    out = writer.code.content_part_text.inline_text or ""
    assert "from aware_orm.runtime.invocation import" in out
    assert "async def do(self, text: str) -> None" in out
    assert 'payload = {"text": text}' in out
    assert "await invoke_instance(orm_model=self" in out
    assert "call_chain" not in out


def test_python_meta_plugin_exposes_orm_models_profile() -> None:
    assert PYTHON_META_PLUGIN.default_renderer_names_by_profile["orm_models"] == (
        "default",
        "stable_ids",
    )
    policy = PYTHON_META_PLUGIN.renderer_policies_by_profile["orm_models"]
    assert isinstance(policy, PythonRenderPolicy)
    assert policy.emit_relationship_fields is True
    assert policy.emit_foreign_key_fields is True
    assert policy.emit_function_facades is False
    assert policy.emit_function_io_models is False
    assert policy.emit_function_registry is False


def test_python_renderer_orm_models_policy_omits_function_facades() -> None:
    cls = make_class(name="Thing", is_base=True)

    fn = make_function(
        name="do",
        owner_key=function_owner_key(cls),
        is_async=True,
        kind=FunctionKind.instance,
    )
    cls.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=cls.id,
            function_config=fn,
            function_config_id=fn.id,
            is_public=True,
            is_constructor=False,
            position=0,
        )
    ]

    renderer = PythonRenderer(
        layout_strategy=_TestLayout(base_dir=Path("/tmp")),
        policy=PythonRenderPolicy.orm_models_default(),
    )
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    renderer.emit_file(
        [cls, fn], writer, schema="default", class_to_class_config_map={cls.id: cls}
    )

    out = writer.code.content_part_text.inline_text or ""
    assert "class Thing(ORMModel):" in out
    assert "from aware_orm.runtime.invocation import" not in out
    assert "async def do(" not in out
    assert "ThingDoInput" not in out


def test_python_renderer_returns_single_output_value_type_for_constructor() -> None:
    cls = make_class(name="Thing", is_base=True)

    fn = make_function(
        name="build",
        owner_key=function_owner_key(cls),
        is_async=True,
        kind=FunctionKind.class_,
    )
    out_attr = make_attribute(
        name="value",
        owner_key=function_io_owner_key(fn, FunctionAttributeType.output),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(cls),
    )
    fn.function_config_attribute_configs = [
        function_attr_link(fn, out_attr, type=FunctionAttributeType.output, position=0)
    ]
    cls.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=cls.id,
            function_config=fn,
            function_config_id=fn.id,
            is_public=True,
            is_constructor=True,
            position=0,
        )
    ]

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    renderer.emit_file(
        [cls, fn], writer, schema="default", class_to_class_config_map={cls.id: cls}
    )

    out = writer.code.content_part_text.inline_text or ""
    assert "async def build(cls) -> Thing" in out
    assert "result = await invoke_constructor(orm_class=cls" in out
    assert (
        'value = result.get("value") if isinstance(result, dict) and "value" in result else result'
        in out
    )
    assert "if isinstance(value, Thing):" in out
    assert "return Thing.validate_invocation_value(value)" in out


def test_python_renderer_model_validates_inline_value_single_output() -> None:
    owner = make_class(name="Thing", is_base=True)
    result = make_class(name="ThingResult", value_mode=ClassValueMode.inline_value)

    fn = make_function(
        name="apply",
        owner_key=function_owner_key(owner),
        is_async=True,
        kind=FunctionKind.instance,
    )
    out_attr = make_attribute(
        name="value",
        owner_key=function_io_owner_key(fn, FunctionAttributeType.output),
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=_class_descriptor(result),
    )
    fn.function_config_attribute_configs = [
        function_attr_link(fn, out_attr, type=FunctionAttributeType.output, position=0)
    ]
    owner.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=owner.id,
            function_config=fn,
            function_config_id=fn.id,
            is_public=True,
            is_constructor=False,
            position=0,
        )
    ]

    renderer = PythonRenderer(layout_strategy=_TestLayout(base_dir=Path("/tmp")))
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code, index=CodeSectionBuilderIndex(), indent_size=renderer.indent
    )
    renderer.emit_file(
        [owner, result, fn],
        writer,
        schema="default",
        class_to_class_config_map={owner.id: owner, result.id: result},
    )

    out = writer.code.content_part_text.inline_text or ""
    assert "async def apply(self) -> ThingResult" in out
    assert "result = await invoke_instance(orm_model=self" in out
    assert (
        'value = result.get("value") if isinstance(result, dict) and "value" in result else result'
        in out
    )
    assert "if isinstance(value, ThingResult):" in out
    assert "return ThingResult.model_validate(value)" in out
    assert "return ThingResult.validate_invocation_value(value)" not in out
