from __future__ import annotations

from uuid import uuid4

from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry
from aware_orm.runtime.graph_artifacts import (
    OrmEntitySpec,
    OrmFieldBinding,
    OrmFieldSpec,
    OrmFieldValueTypeSpec,
    OrmFunctionBinding,
    OrmFunctionSpec,
    OrmGraphBindingSnapshot,
)
from aware_orm.runtime.graph_binding import bind_entities_by_fqn, dump_orm_graph_binding_snapshot_msgpack, index_entities_from_msgpack


def test_bind_entities_by_fqn_skips_inline_value_classes() -> None:
    """
    Inline-value classes are value objects (Pydantic-only) and must not be bound as ORM models.

    Regression: ORM package bootstrap should not fail with "Missing Python classes for canonical binding"
    when an ontology package contains inline_value classes.
    """

    registry_snapshot = ORMModelRegistry.snapshot_state()
    try:
        ORMModelRegistry.clear_registry()
        ORMModelRegistry._initialized = False  # test-local reset

        entity_id = uuid4()
        entity = OrmEntitySpec.model_construct(
            id=entity_id,
            name="Payload",
            entity_fqn="pkg.Payload",
            value_mode="inline_value",
        )

        result = bind_entities_by_fqn(
            bindings=[("pkg.Payload", str(entity_id))],
            entity_index={str(entity_id): entity},
            strict=True,
        )
        assert result.bound_count == 0
        assert result.missing_classes == []
        assert result.missing_entities == []
    finally:
        ORMModelRegistry.restore_state(registry_snapshot)


def test_bind_entities_by_fqn_does_not_merge_stale_installed_fields() -> None:
    """Fresh ORM entity truth must win over stale already-imported model bindings."""

    registry_snapshot = ORMModelRegistry.snapshot_state()
    try:
        ORMModelRegistry.clear_registry()
        ORMModelRegistry._initialized = False  # test-local reset

        class BoundThing(ORMModel):
            pass

        fqn = ORMModelRegistry.register_class_stub(BoundThing)
        entity_id = uuid4()
        current_attr = OrmFieldSpec.model_construct(id=uuid4(), owner_key=fqn, name="current")
        stale_attr = OrmFieldSpec.model_construct(id=uuid4(), owner_key=fqn, name="stale_installed_field")
        current_entity = OrmEntitySpec.model_construct(id=entity_id, name="BoundThing", entity_fqn=fqn)
        current_entity.field_bindings = [
            OrmFieldBinding.model_construct(
                entity_id=entity_id,
                field=current_attr,
                field_id=current_attr.id,
                position=0,
            )
        ]

        stale_installed_entity = current_entity.model_copy(deep=True)
        stale_installed_entity.field_bindings.append(
            OrmFieldBinding.model_construct(
                entity_id=entity_id,
                field=stale_attr,
                field_id=stale_attr.id,
                position=99,
            )
        )
        installed_function = OrmFunctionSpec.model_construct(
            id=uuid4(),
            owner_key=fqn,
            name="runtime_constructor",
        )
        stale_installed_entity.function_bindings.append(
            OrmFunctionBinding.model_construct(
                entity_id=entity_id,
                function=installed_function,
                function_id=installed_function.id,
                position=0,
            )
        )
        BoundThing.bind_class_config(stale_installed_entity)

        result = bind_entities_by_fqn(
            bindings=[(fqn, str(entity_id))],
            entity_index={str(entity_id): current_entity},
            strict=True,
        )

        assert result.bound_count == 1
        bound_cc = BoundThing.get_class_config()
        assert bound_cc is not None
        assert [
            link.attribute_config.name
            for link in bound_cc.class_config_attribute_configs
        ] == ["current"]
        assert [
            link.function_config.name
            for link in bound_cc.class_config_function_configs
        ] == ["runtime_constructor"]
    finally:
        ORMModelRegistry.restore_state(registry_snapshot)


def test_graph_binding_roundtrips_field_binding_role_and_value_type() -> None:
    entity_id = uuid4()
    function_id = uuid4()
    output_field_id = uuid4()
    output_entity_id = uuid4()
    output_field = OrmFieldSpec.model_construct(
        id=output_field_id,
        name="value",
        value_type=OrmFieldValueTypeSpec.model_construct(
            kind="class",
            entity_id=output_entity_id,
            is_collection=False,
        ),
    )
    function = OrmFunctionSpec.model_construct(
        id=function_id,
        name="build",
        field_bindings=[
            OrmFieldBinding.model_construct(
                function_id=function_id,
                field_id=output_field_id,
                field=output_field,
                binding_role="output",
                position=0,
            )
        ],
    )
    snapshot = OrmGraphBindingSnapshot.model_construct(
        entities=[
            OrmEntitySpec.model_construct(
                id=entity_id,
                name="Thing",
                entity_fqn="pkg.Thing",
                function_bindings=[
                    OrmFunctionBinding.model_construct(
                        entity_id=entity_id,
                        function_id=function_id,
                        function=function,
                    )
                ],
            )
        ]
    )

    entity_index = index_entities_from_msgpack(
        dump_orm_graph_binding_snapshot_msgpack(snapshot=snapshot)
    )

    rebound_function = entity_index[str(entity_id)].function_bindings[0].function
    assert rebound_function is not None
    rebound_output = rebound_function.function_config_attribute_configs[0]
    assert rebound_output.binding_role == "output"
    assert rebound_output.attribute_config is not None
    assert rebound_output.attribute_config.value_type is not None
    assert rebound_output.attribute_config.value_type.entity_id == output_entity_id
    assert rebound_output.attribute_config.value_type.is_collection is False
