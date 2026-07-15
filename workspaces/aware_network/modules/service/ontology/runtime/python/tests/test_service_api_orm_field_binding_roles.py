from __future__ import annotations

from uuid import uuid4

from aware_orm.runtime.graph_artifacts import (
    OrmEntitySpec,
    OrmFieldBinding,
    OrmFieldSpec,
    OrmFieldValueTypeSpec,
    OrmFunctionSpec,
)

from aware_service_runtime.api_ingress.gateway_execution import (
    _resolve_exact_instance_output_field_name as resolve_gateway_output_field_name,
)
from aware_service_runtime.api_ingress.target_resolution import (
    ResolvedServiceApiGraphFunctionTarget,
)


def _resolved_target(
    *, output_entity_matches: bool = True
) -> ResolvedServiceApiGraphFunctionTarget:
    target_entity_id = uuid4()
    output_entity_id = target_entity_id if output_entity_matches else uuid4()
    function_id = uuid4()
    input_field = OrmFieldSpec.model_construct(id=uuid4(), name="name")
    output_field = OrmFieldSpec.model_construct(
        id=uuid4(),
        name="value",
        value_type=OrmFieldValueTypeSpec.model_construct(
            kind="class",
            entity_id=output_entity_id,
            is_collection=False,
        ),
    )
    function = OrmFunctionSpec.model_construct(
        id=function_id,
        name="create",
        field_bindings=[
            OrmFieldBinding.model_construct(
                function_id=function_id,
                field_id=input_field.id,
                field=input_field,
                binding_role="input",
                position=0,
            ),
            OrmFieldBinding.model_construct(
                function_id=function_id,
                field_id=output_field.id,
                field=output_field,
                binding_role="output",
                position=0,
            ),
        ],
    )
    return ResolvedServiceApiGraphFunctionTarget(
        class_config=OrmEntitySpec.model_construct(id=target_entity_id),
        function_link=object(),
        function_config=function,
    )


def test_exact_output_resolution_uses_orm_field_binding_role() -> None:
    assert (
        resolve_gateway_output_field_name(resolved_target=_resolved_target()) == "value"
    )


def test_exact_output_resolution_requires_matching_orm_value_entity() -> None:
    assert (
        resolve_gateway_output_field_name(
            resolved_target=_resolved_target(output_entity_matches=False)
        )
        is None
    )


def test_orm_field_binding_exposes_identity_key_contract() -> None:
    binding = OrmFieldBinding.model_construct(
        binding_role="input",
        is_identity_key=True,
        field=OrmFieldSpec.model_construct(name="service_id"),
        position=0,
    )

    assert binding.binding_role == "input"
    assert binding.position == 0
    assert binding.is_identity_key is True
    assert binding.field is not None
    assert binding.field.name == "service_id"


def test_service_contract_generated_orm_binding_preserves_constructor_identity_contract() -> (
    None
):
    from aware_service_ontology.service.service_contract import ServiceContract

    class_config = ServiceContract.get_class_config()
    assert class_config is not None

    matches = [
        link
        for link in class_config.class_config_function_configs
        if link.function_config is not None
        and link.function_config.name == "build_via_service"
    ]
    assert len(matches) == 1
    function_link = matches[0]
    assert function_link.is_constructor is True

    input_edges = [
        edge
        for edge in function_link.function_config.function_config_attribute_configs
        if edge.binding_role == "input"
    ]
    identity_names = tuple(
        edge.attribute_config.name
        for edge in sorted(input_edges, key=lambda edge: int(edge.position))
        if edge.is_identity_key
    )
    assert identity_names == (
        "service_id",
        "service_contract_config_id",
        "smart_contract_id",
    )
