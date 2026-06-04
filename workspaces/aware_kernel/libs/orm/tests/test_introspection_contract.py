from __future__ import annotations

from uuid import uuid4

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)

from aware_orm.models.base_model import BaseORMModel
from aware_orm.models.introspection import ModelIntrospection


def test_base_orm_model_satisfies_model_introspection_protocol() -> None:
    class Person(BaseORMModel):
        name: str
        age: int | None = None

    p = Person(id=uuid4(), name="Luis")
    assert isinstance(p, ModelIntrospection)

    assert p.field_is_declared("name") is True
    assert p.field_is_declared("age") is True
    assert p.field_is_declared("does_not_exist") is False

    found, value = p.try_field_value("name")
    assert found is True and value == "Luis"

    # Unset defaulted field: not found unless include_unset=True.
    found, value = p.try_field_value("age")
    assert found is False and value is None
    found, value = p.try_field_value("age", include_unset=True)
    assert found is True and value is None


def test_virtual_value_resolution_is_ssot_on_orm_model() -> None:
    class Person(BaseORMModel):
        name: str

    p = Person(id=uuid4(), name="Luis")

    desc = AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])
    id_attr = AttributeConfig(name="id", owner_key="id", is_virtual=True, is_required=True, type_descriptor=desc)
    name_attr = AttributeConfig(
        name="name",
        owner_key="name",
        is_virtual=False,
        is_required=True,
        type_descriptor=desc,
    )

    found, value = p.try_virtual_value(id_attr)
    assert found is True and value == p.id

    found, value = p.try_attribute_value(id_attr)
    assert found is True and value == p.id

    found, value = p.try_attribute_value(name_attr)
    assert found is True and value == "Luis"


def test_try_field_value_does_not_access_undeclared_attributes() -> None:
    class Person(BaseORMModel):
        name: str

        @property
        def danger(self) -> str:
            raise AssertionError("property should not be accessed by try_field_value")

    p = Person(id=uuid4(), name="Luis")

    found, value = p.try_field_value("danger", include_unset=True)
    assert found is False and value is None
