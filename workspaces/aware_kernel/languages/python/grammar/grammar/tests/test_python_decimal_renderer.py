from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
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
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionKind,
)
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig
from python_grammar.renderer import PythonRenderer
from python_grammar_test_support import (
    class_attr_link,
    function_attr_link,
    function_io_owner_key,
    function_owner_key,
    make_attribute,
    make_class,
    make_function,
)


@dataclass(frozen=True)
class _Layout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = None

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path("default") / "models.py"

    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        return Path("default") / "models.py"

    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        return Path("default") / "models.py"

    def get_file_extension(self) -> str:
        return ".py"

    def get_module_import_path(self, file_path: Path) -> str:
        return ".".join(file_path.with_suffix("").parts)


def _render_decimal_model() -> str:
    primitive = build_code_primitive_type(base_type=CodePrimitiveBaseType.decimal)
    primitive_config = PrimitiveConfig(
        primitive_type=primitive,
        primitive_type_id=primitive.id,
    )
    descriptor = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
    )
    account = make_class(name="Account")
    balance = make_attribute(
        name="opening_balance",
        owner_key=account.class_fqn,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        default_value='"1.23"',
        type_descriptor=descriptor,
    )
    account.class_config_attribute_configs = [
        class_attr_link(account, balance, position=0)
    ]
    replace = make_function(
        name="replace_amount",
        owner_key=function_owner_key(account),
        is_async=True,
        kind=FunctionKind.instance,
    )
    optional_amount = make_attribute(
        name="optional_amount",
        owner_key=function_io_owner_key(replace, FunctionAttributeType.input),
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        default_value="null",
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )
    replace.function_config_attribute_configs = [
        function_attr_link(
            replace,
            optional_amount,
            type=FunctionAttributeType.input,
            position=0,
        )
    ]
    account.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=account.id,
            function_config=replace,
            function_config_id=replace.id,
            is_public=True,
            is_constructor=False,
            position=0,
        )
    ]

    renderer = PythonRenderer(layout_strategy=_Layout(base_dir=Path("/tmp")))
    code = renderer.create_empty_code()
    writer = CodeSectionWriter(
        code=code,
        index=CodeSectionBuilderIndex(),
        indent_size=renderer.indent,
    )
    renderer.emit_file(
        [account, replace],
        writer,
        class_to_class_config_map={account.id: account},
    )
    return code.content_part_text.inline_text or ""


def test_python_renderer_emits_executable_exact_decimal_model() -> None:
    source = _render_decimal_model()
    assert "from decimal import Decimal" in source
    assert "from typing import Annotated" in source
    assert "from aware_types import DecimalWire" in source
    assert "opening_balance: Annotated[Decimal, DecimalWire()]" in source
    assert "Field(default=Decimal('1.23'))" in source
    assert (
        "async def replace_amount(self, optional_amount: "
        "Annotated[Decimal, DecimalWire()] | None = None)" in source
    )
    assert "opening_balance: float" not in source

    namespace: dict[str, object] = {
        "__name__": "test_generated_decimal_model",
        "__package__": None,
    }
    exec(compile(source, "<generated_decimal_model>", "exec"), namespace)
    account_type = namespace["Account"]
    assert isinstance(account_type, type)
    account_type.model_rebuild(_types_namespace=namespace)

    account = account_type(opening_balance=Decimal("1.2300"))
    assert account.opening_balance == Decimal("1.23")
    assert '"opening_balance":"1.23"' in account.model_dump_json()

    with pytest.raises(ValidationError):
        account_type(opening_balance=1.23)
    with pytest.raises(ValidationError):
        account_type.model_validate_json('{"opening_balance":1.23}')

    from_json = account_type.model_validate_json('{"opening_balance":"1.2300"}')
    assert from_json.opening_balance == Decimal("1.23")
    assert '"opening_balance":"1.23"' in from_json.model_dump_json()
