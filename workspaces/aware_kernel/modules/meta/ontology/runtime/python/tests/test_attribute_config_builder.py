from __future__ import annotations

from uuid import uuid4

from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_grammar.primitive_codec import AwarePrimitiveCodec
from aware_grammar.type_descriptor_adapter import AwareTypeDescriptorAdapter

from aware_meta.attribute.config.builder import build_attribute_config_from_code
from aware_meta.fqn_resolver import (
    FqnRegistry,
    NamespacePath,
)
from aware_meta.test_support import make_enum_config


def _scope_with_enum(enum_name: str):
    code_id = uuid4()
    namespace = NamespacePath(
        package="aware_service", namespace="service"
    )
    registry = FqnRegistry(namespace_by_code_id={code_id: namespace})
    _ = registry.add_enum_with_namespace(
        make_enum_config(
            name=enum_name,
            enum_fqn=namespace.fqn(enum_name),
            enum_options=[],
        ),
        namespace,
        origin_code_id=code_id,
    )
    resolver = registry.build()
    return resolver.scope_for_code_id(code_id)


def _code_section_attribute(
    *,
    type_text: str,
    default_value_text: str,
    is_required: bool,
) -> CodeSectionAttribute:
    return CodeSectionAttribute.model_construct(
        id=uuid4(),
        name="settlement_policy",
        description=None,
        type_text=type_text,
        default_value_text=default_value_text,
        is_required=is_required,
        is_public=True,
        is_unique=False,
        is_primary=False,
        is_many_to_many=False,
        edge_spec_name=None,
    )


def test_build_attribute_config_from_code_preserves_aware_enum_token_default() -> None:
    scope = _scope_with_enum("ServiceOperationSettlementPolicy")

    attribute_config = build_attribute_config_from_code(
        fqn_scope=scope,
        primitive_codec=AwarePrimitiveCodec(),
        type_descriptor_adapter=AwareTypeDescriptorAdapter(),
        code_section_attribute=_code_section_attribute(
            type_text="ServiceOperationSettlementPolicy",
            default_value_text="none",
            is_required=True,
        ),
        owner_key="aware_service.service.service_config.create_service_operation_config::input",
    )

    assert attribute_config.default_value == '"none"'


def test_build_attribute_config_from_code_keeps_optional_enum_null_default() -> None:
    scope = _scope_with_enum("ServiceOperationSettlementPolicy")

    attribute_config = build_attribute_config_from_code(
        fqn_scope=scope,
        primitive_codec=AwarePrimitiveCodec(),
        type_descriptor_adapter=AwareTypeDescriptorAdapter(),
        code_section_attribute=_code_section_attribute(
            type_text="ServiceOperationSettlementPolicy?",
            default_value_text="null",
            is_required=False,
        ),
        owner_key="aware_service.service.service_config.create_service_operation_config::input",
    )

    assert attribute_config.default_value == "null"


def test_build_attribute_config_from_code_preserves_enum_collection_defaults() -> None:
    scope = _scope_with_enum("ServiceOperationSettlementPolicy")

    attribute_config = build_attribute_config_from_code(
        fqn_scope=scope,
        primitive_codec=AwarePrimitiveCodec(),
        type_descriptor_adapter=AwareTypeDescriptorAdapter(),
        code_section_attribute=_code_section_attribute(
            type_text="ServiceOperationSettlementPolicy[]",
            default_value_text="[none, reserve_before_execute]",
            is_required=True,
        ),
        owner_key="aware_service.service.service_config.create_service_operation_config::input",
    )

    assert attribute_config.default_value == '["none", "reserve_before_execute"]'
