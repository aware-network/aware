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
    from aware_meta_ontology.graph.projection.object_projection_graph_identity import ObjectProjectionGraphIdentity


class ObjectConfigGraphIdentity(ORMModel):
    """
    Stable identity for a family of ObjectConfigGraphs.
    This object is intended to be created by the compiler (environment-artifacts)
    and remain stable even as config graph snapshots evolve.
    """

    # Relationships
    object_projection_graph_identities: list[ObjectProjectionGraphIdentity] = Field(default_factory=list)

    # Attributes
    key: str = Field(description="Stable key for this config graph family (e.g. fqn_prefix).")
    label: str | None = Field(default=None)

    @classmethod
    async def create(cls, key: str, label: str | None = None) -> ObjectConfigGraphIdentity:
        """Create deterministic ObjectConfigGraphIdentity from semantic key only."""

        payload = {"key": key, "label": label}
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectConfigGraphIdentity):
            return value
        return ObjectConfigGraphIdentity.validate_invocation_value(value)

    async def create_object_projection_graph_identity(
        self, object_projection_graph_id: UUID, projection_name: str, label: str | None = None
    ) -> ObjectProjectionGraphIdentity:
        """Create deterministic ObjectProjectionGraphIdentity under this ObjectConfigGraphIdentity."""

        payload = {
            "object_projection_graph_id": object_projection_graph_id,
            "projection_name": projection_name,
            "label": label,
        }
        result = await invoke_instance(
            orm_model=self, function_name="create_object_projection_graph_identity", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.projection.object_projection_graph_identity import ObjectProjectionGraphIdentity

        if isinstance(value, ObjectProjectionGraphIdentity):
            return value
        return ObjectProjectionGraphIdentity.validate_invocation_value(value)


class ObjectConfigGraphIdentityCreateInput(BaseModel):
    key: str
    label: str | None = Field(default=None)


class ObjectConfigGraphIdentityCreateOutput(BaseModel):
    value: ObjectConfigGraphIdentity


class ObjectConfigGraphIdentityCreateObjectProjectionGraphIdentityInput(BaseModel):
    object_projection_graph_id: UUID
    projection_name: str
    label: str | None = Field(default=None)


class ObjectConfigGraphIdentityCreateObjectProjectionGraphIdentityOutput(BaseModel):
    value: ObjectProjectionGraphIdentity


FUNCTIONS = {
    "ObjectConfigGraphIdentity": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create deterministic ObjectConfigGraphIdentity from semantic key only.",
                "is_constructor": True,
            },
            "input": ObjectConfigGraphIdentityCreateInput,
            "output": ObjectConfigGraphIdentityCreateOutput,
        },
        "create_object_projection_graph_identity": {
            "canonical": {
                "name": "create_object_projection_graph_identity",
                "description": "Create deterministic ObjectProjectionGraphIdentity under this ObjectConfigGraphIdentity.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphIdentityCreateObjectProjectionGraphIdentityInput,
            "output": ObjectConfigGraphIdentityCreateObjectProjectionGraphIdentityOutput,
        },
    },
}

__all__ = [
    "ObjectConfigGraphIdentity",
    "ObjectConfigGraphIdentityCreateInput",
    "ObjectConfigGraphIdentityCreateOutput",
    "ObjectConfigGraphIdentityCreateObjectProjectionGraphIdentityInput",
    "ObjectConfigGraphIdentityCreateObjectProjectionGraphIdentityOutput",
    "FUNCTIONS",
]
