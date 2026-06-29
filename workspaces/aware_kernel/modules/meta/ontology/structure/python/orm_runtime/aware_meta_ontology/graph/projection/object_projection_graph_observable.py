from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class ObjectProjectionGraphObservable(ORMModel):
    """
    Stable observable descriptor for an ObjectProjectionGraphIdentity.
    Purpose:
    - Provide a canonical, network-shared list of observables (shared-attention selectors)
    under a projection identity.
    - Observables are projection-scoped descriptors that can be selected by FocusScope.
    Notes:
    - Observables are expected to be compiler-owned or system-seeded (deterministic IDs/keys).
    - Experience packages bind observables to views.
    - Interface packages bind Experience views to concrete panes.
    """

    # Attributes
    key: str = Field(description='Stable key for this observable (recommended: "{opg_identity.key}:{observable_key}").')
    observable_key: str = Field(description="Short selector for an observable within a projection family.")
    kind: str | None = Field(
        default=None,
        description='Observable kind:\n- "construct": no branch state required (gate-friendly)\n- "instance": requires branch state (materialized OIGB)',
    )
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)

    # Foreign Keys
    object_projection_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphIdentity.object_projection_graph_observables"
    )

    @classmethod
    async def create_via_object_projection_graph_identity(
        cls,
        object_projection_graph_identity_id: UUID,
        observable_key: str,
        key: str,
        kind: str | None = None,
        label: str | None = None,
        description: str | None = None,
        position: int | None = None,
        is_default: bool = False,
    ) -> ObjectProjectionGraphObservable:
        """
        Creates a new ObjectProjectionGraphObservable.

        Contract:
        - Parent `ObjectProjectionGraphIdentity` scope is propagated by traversal lowering.
        - Deterministic identity derives from parent scope + `(observable_key)`.
        - `key` is the caller-materialized canonical projection key.
        """

        payload = {
            "object_projection_graph_identity_id": object_projection_graph_identity_id,
            "observable_key": observable_key,
            "key": key,
            "kind": kind,
            "label": label,
            "description": description,
            "position": position,
            "is_default": is_default,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_projection_graph_identity", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectProjectionGraphObservable):
            return value
        return ObjectProjectionGraphObservable.validate_invocation_value(value)


class ObjectProjectionGraphObservableCreateViaObjectProjectionGraphIdentityInput(BaseModel):
    object_projection_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphIdentity.object_projection_graph_observables"
    )
    observable_key: str
    key: str
    kind: str | None = Field(default=None)
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)


class ObjectProjectionGraphObservableCreateViaObjectProjectionGraphIdentityOutput(BaseModel):
    value: ObjectProjectionGraphObservable


FUNCTIONS = {
    "ObjectProjectionGraphObservable": {
        "create_via_object_projection_graph_identity": {
            "canonical": {
                "name": "create_via_object_projection_graph_identity",
                "description": "Creates a new ObjectProjectionGraphObservable.\n\nContract:\n- Parent `ObjectProjectionGraphIdentity` scope is propagated by traversal lowering.\n- Deterministic identity derives from parent scope + `(observable_key)`.\n- `key` is the caller-materialized canonical projection key.",
                "is_constructor": True,
            },
            "input": ObjectProjectionGraphObservableCreateViaObjectProjectionGraphIdentityInput,
            "output": ObjectProjectionGraphObservableCreateViaObjectProjectionGraphIdentityOutput,
        },
    },
}

__all__ = [
    "ObjectProjectionGraphObservable",
    "ObjectProjectionGraphObservableCreateViaObjectProjectionGraphIdentityInput",
    "ObjectProjectionGraphObservableCreateViaObjectProjectionGraphIdentityOutput",
    "FUNCTIONS",
]
