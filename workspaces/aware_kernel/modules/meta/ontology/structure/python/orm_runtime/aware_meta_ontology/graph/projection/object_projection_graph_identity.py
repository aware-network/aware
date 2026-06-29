from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity
    from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology.graph.projection.object_projection_graph_observable import ObjectProjectionGraphObservable


class ObjectProjectionGraphIdentity(ORMModel):
    """
    Stable identity for a family of ObjectProjectionGraphs under an ObjectConfigGraphIdentity.
    This object is intended to be created by the compiler (environment-artifacts)
    and remain stable even as projection snapshots evolve.
    """

    # Relationships
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None, exclude=True)
    object_instance_graph_identities: list[ObjectInstanceGraphIdentity] = Field(default_factory=list)
    object_projection_graph_observables: list[ObjectProjectionGraphObservable] = Field(default_factory=list)

    # Attributes
    projection_name: str
    label: str | None = Field(default=None)
    is_branchable: bool = Field(default=False)

    # Foreign Keys
    object_config_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphIdentity.object_projection_graph_identities"
    )
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphIdentity.object_projection_graph"
    )

    async def create_object_instance_graph_identity(
        self, object_instance_graph_id: UUID, label: str | None = None
    ) -> ObjectInstanceGraphIdentity:
        """Create deterministic ObjectInstanceGraphIdentity under this ObjectProjectionGraphIdentity."""

        payload = {"object_instance_graph_id": object_instance_graph_id, "label": label}
        result = await invoke_instance(
            orm_model=self, function_name="create_object_instance_graph_identity", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity

        if isinstance(value, ObjectInstanceGraphIdentity):
            return value
        return ObjectInstanceGraphIdentity.validate_invocation_value(value)

    async def create_observable(
        self,
        observable_key: str,
        key: str,
        kind: str | None = None,
        label: str | None = None,
        description: str | None = None,
        position: int | None = None,
        is_default: bool = False,
    ) -> ObjectProjectionGraphObservable:
        """
        Creates (or ensures) a new ObjectProjectionGraphObservable under this identity.

        Contract:
        - `ObjectProjectionGraphObservable.id` is deterministic for `(self.id, observable_key)`.
        - `ObjectProjectionGraphObservable.key` is the caller-materialized canonical key:
          "{projection_name}:{observable_key}".
        """

        payload = {
            "observable_key": observable_key,
            "key": key,
            "kind": kind,
            "label": label,
            "description": description,
            "position": position,
            "is_default": is_default,
        }
        result = await invoke_instance(orm_model=self, function_name="create_observable", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.projection.object_projection_graph_observable import (
            ObjectProjectionGraphObservable,
        )

        if isinstance(value, ObjectProjectionGraphObservable):
            return value
        return ObjectProjectionGraphObservable.validate_invocation_value(value)

    @classmethod
    async def create_via_object_config_graph_identity(
        cls,
        object_config_graph_identity_id: UUID,
        object_projection_graph_id: UUID,
        projection_name: str,
        label: str | None = None,
    ) -> ObjectProjectionGraphIdentity:
        """
        Create deterministic ObjectProjectionGraphIdentity for one stable OPG payload.

        Contract:
        - Identity resolves from `(object_config_graph_identity_id via path, object_projection_graph_id)`.
        - `object_projection_graph` is the boundary pointer to the stable payload and must not be
          traversed inside the identity projection payload.
        """

        payload = {
            "object_config_graph_identity_id": object_config_graph_identity_id,
            "object_projection_graph_id": object_projection_graph_id,
            "projection_name": projection_name,
            "label": label,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_config_graph_identity", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectProjectionGraphIdentity):
            return value
        return ObjectProjectionGraphIdentity.validate_invocation_value(value)


class ObjectProjectionGraphIdentityCreateObjectInstanceGraphIdentityInput(BaseModel):
    object_instance_graph_id: UUID
    label: str | None = Field(default=None)


class ObjectProjectionGraphIdentityCreateObjectInstanceGraphIdentityOutput(BaseModel):
    value: ObjectInstanceGraphIdentity


class ObjectProjectionGraphIdentityCreateObservableInput(BaseModel):
    observable_key: str
    key: str
    kind: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)


class ObjectProjectionGraphIdentityCreateObservableOutput(BaseModel):
    value: ObjectProjectionGraphObservable


class ObjectProjectionGraphIdentityCreateViaObjectConfigGraphIdentityInput(BaseModel):
    object_config_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphIdentity.object_projection_graph_identities"
    )
    object_projection_graph_id: UUID
    projection_name: str
    label: str | None = Field(default=None)


class ObjectProjectionGraphIdentityCreateViaObjectConfigGraphIdentityOutput(BaseModel):
    value: ObjectProjectionGraphIdentity


FUNCTIONS = {
    "ObjectProjectionGraphIdentity": {
        "create_object_instance_graph_identity": {
            "canonical": {
                "name": "create_object_instance_graph_identity",
                "description": "Create deterministic ObjectInstanceGraphIdentity under this ObjectProjectionGraphIdentity.",
                "is_constructor": False,
            },
            "input": ObjectProjectionGraphIdentityCreateObjectInstanceGraphIdentityInput,
            "output": ObjectProjectionGraphIdentityCreateObjectInstanceGraphIdentityOutput,
        },
        "create_observable": {
            "canonical": {
                "name": "create_observable",
                "description": 'Creates (or ensures) a new ObjectProjectionGraphObservable under this identity.\n\nContract:\n- `ObjectProjectionGraphObservable.id` is deterministic for `(self.id, observable_key)`.\n- `ObjectProjectionGraphObservable.key` is the caller-materialized canonical key:\n  "{projection_name}:{observable_key}".',
                "is_constructor": False,
            },
            "input": ObjectProjectionGraphIdentityCreateObservableInput,
            "output": ObjectProjectionGraphIdentityCreateObservableOutput,
        },
        "create_via_object_config_graph_identity": {
            "canonical": {
                "name": "create_via_object_config_graph_identity",
                "description": "Create deterministic ObjectProjectionGraphIdentity for one stable OPG payload.\n\nContract:\n- Identity resolves from `(object_config_graph_identity_id via path, object_projection_graph_id)`.\n- `object_projection_graph` is the boundary pointer to the stable payload and must not be\n  traversed inside the identity projection payload.",
                "is_constructor": True,
            },
            "input": ObjectProjectionGraphIdentityCreateViaObjectConfigGraphIdentityInput,
            "output": ObjectProjectionGraphIdentityCreateViaObjectConfigGraphIdentityOutput,
        },
    },
}

__all__ = [
    "ObjectProjectionGraphIdentity",
    "ObjectProjectionGraphIdentityCreateObjectInstanceGraphIdentityInput",
    "ObjectProjectionGraphIdentityCreateObjectInstanceGraphIdentityOutput",
    "ObjectProjectionGraphIdentityCreateObservableInput",
    "ObjectProjectionGraphIdentityCreateObservableOutput",
    "ObjectProjectionGraphIdentityCreateViaObjectConfigGraphIdentityInput",
    "ObjectProjectionGraphIdentityCreateViaObjectConfigGraphIdentityOutput",
    "FUNCTIONS",
]
