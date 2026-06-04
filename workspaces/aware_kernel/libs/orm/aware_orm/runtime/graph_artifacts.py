"""ORM-native graph artifact DTOs.

These DTOs are the public package artifact contract consumed by `aware-orm`.
Ontology producers such as Meta translate their own graph models into this
runtime shape before ORM sees the payload.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrmGraphDTO(BaseModel):
    """Base for public ORM graph artifact DTOs."""

    model_config = ConfigDict(extra="allow")


class OrmProducerRef(OrmGraphDTO):
    """Opaque producer provenance retained for diagnostics and drift receipts."""

    producer: str | None = None
    kind: str | None = None
    id: str | None = None
    node_id: str | None = None


class OrmFieldValueTypeSpec(OrmGraphDTO):
    """ORM-owned field value type summary for runtime consumers."""

    kind: Any = None
    entity_id: UUID | None = None
    primitive_id: UUID | None = None
    enum_id: UUID | None = None
    collection_kind: Any = None
    is_collection: bool | None = None


class OrmFieldSpec(OrmGraphDTO):
    id: UUID | None = None
    name: str | None = None
    owner_key: str | None = None
    description: str | None = None
    default_value: str | None = None
    is_primary: bool | None = None
    is_public: bool | None = None
    is_required: bool | None = None
    is_unique: bool | None = None
    is_virtual: bool | None = None
    value_type: OrmFieldValueTypeSpec | None = None
    producer_ref: OrmProducerRef | None = None


class OrmFieldBinding(OrmGraphDTO):
    id: UUID | None = None
    entity_id: UUID | None = None
    function_id: UUID | None = None
    field_id: UUID | None = None
    position: int | None = None
    binding_role: str | None = None
    field: OrmFieldSpec | None = None

    @property
    def class_config_id(self) -> UUID | None:
        return self.entity_id

    @property
    def function_config_id(self) -> UUID | None:
        return self.function_id

    @property
    def attribute_config_id(self) -> UUID | None:
        return self.field_id

    @property
    def attribute_config(self) -> OrmFieldSpec | None:
        return self.field


class OrmFunctionSpec(OrmGraphDTO):
    id: UUID | None = None
    owner_key: str | None = None
    name: str | None = None
    kind: Any = None
    is_public: bool | None = None
    is_constructor: bool | None = None
    field_bindings: list[OrmFieldBinding] = Field(default_factory=list)
    producer_ref: OrmProducerRef | None = None

    @property
    def function_config_attribute_configs(self) -> list[OrmFieldBinding]:
        return self.field_bindings


class OrmFunctionBinding(OrmGraphDTO):
    id: UUID | None = None
    entity_id: UUID | None = None
    function_id: UUID | None = None
    position: int | None = None
    function: OrmFunctionSpec | None = None

    @property
    def class_config_id(self) -> UUID | None:
        return self.entity_id

    @property
    def function_config_id(self) -> UUID | None:
        return self.function_id

    @property
    def function_config(self) -> OrmFunctionSpec | None:
        return self.function


class OrmRelationshipField(OrmGraphDTO):
    id: UUID | None = None
    relationship_id: UUID | None = None
    field_id: UUID | None = None
    direction: Any = None
    role: Any = None
    field: OrmFieldSpec | None = None
    producer_ref: OrmProducerRef | None = None

    @property
    def class_config_relationship_id(self) -> UUID | None:
        return self.relationship_id

    @property
    def attribute_config_id(self) -> UUID | None:
        return self.field_id

    @property
    def attribute_config(self) -> OrmFieldSpec | None:
        return self.field


class OrmRelationshipSpec(OrmGraphDTO):
    id: UUID | None = None
    source_entity_id: UUID | None = None
    target_entity_id: UUID | None = None
    relationship_key: str | None = None
    relationship_type: Any = None
    identity_rail: Any = None
    forward_required: bool | None = None
    forward_loading_strategy: Any = None
    reverse_loading_strategy: Any = None
    fields: list[OrmRelationshipField] = Field(default_factory=list)
    producer_ref: OrmProducerRef | None = None

    @property
    def class_config_id(self) -> UUID | None:
        return self.source_entity_id

    @property
    def target_class_config_id(self) -> UUID | None:
        return self.target_entity_id

    @property
    def class_config_relationship_attributes(self) -> list[OrmRelationshipField]:
        return self.fields


class OrmEntitySpec(OrmGraphDTO):
    id: UUID | None = None
    entity_fqn: str | None = None
    name: str | None = None
    value_mode: Any = "graph_ref"
    identity_mode: Any = "contained"
    parent_entity_id: UUID | None = None
    code_section_entity_id: UUID | None = None
    field_bindings: list[OrmFieldBinding] = Field(default_factory=list)
    function_bindings: list[OrmFunctionBinding] = Field(default_factory=list)
    relationships: list[OrmRelationshipSpec] = Field(default_factory=list)
    producer_ref: OrmProducerRef | None = None

    @property
    def class_fqn(self) -> str | None:
        return self.entity_fqn

    @property
    def parent_class_id(self) -> UUID | None:
        return self.parent_entity_id

    @property
    def code_section_class_id(self) -> UUID | None:
        return self.code_section_entity_id

    @property
    def class_config_attribute_configs(self) -> list[OrmFieldBinding]:
        return self.field_bindings

    @property
    def class_config_function_configs(self) -> list[OrmFunctionBinding]:
        return self.function_bindings

    @property
    def class_config_relationships(self) -> list[OrmRelationshipSpec]:
        return self.relationships


class OrmGraphBindingSnapshot(OrmGraphDTO):
    """Canonical package binding snapshot consumed by ORM."""

    version: str = "v1"
    source_package: str | None = None
    graph_id: UUID | None = None
    entities: list[OrmEntitySpec] = Field(default_factory=list)


__all__ = [
    "OrmEntitySpec",
    "OrmFieldBinding",
    "OrmFieldSpec",
    "OrmFieldValueTypeSpec",
    "OrmFunctionBinding",
    "OrmFunctionSpec",
    "OrmGraphBindingSnapshot",
    "OrmGraphDTO",
    "OrmProducerRef",
    "OrmRelationshipField",
    "OrmRelationshipSpec",
]
