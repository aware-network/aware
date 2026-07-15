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


class ObjectProjectionGraphBinding(ORMModel):
    """
    Resolved binding between a projection declaration and a canonical class (and optionally member).
    Contract:
    - Root membership is expressed by `attribute_name == null`.
    - Member membership is expressed by `attribute_name != null`.
    - Portal relationships are expressed by `target_projection_name != null`.
    """

    # Attributes
    fqn_prefix: str
    namespace: str
    class_name: str
    attribute_name: str | None = Field(default=None)
    target_projection_name: str | None = Field(
        default=None,
        description='Target projection reference (canonical authored identity, e.g. "Focus" or "aware_identity.Identity").',
    )
    side: str | None = Field(default=None)

    # Foreign Keys
    object_projection_graph_declaration_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphDeclaration.object_projection_graph_bindings"
    )

    @classmethod
    async def create_via_object_projection_graph_declaration(
        cls,
        object_projection_graph_declaration_id: UUID,
        fqn_prefix: str,
        namespace: str,
        class_name: str,
        attribute_name: str | None = None,
        target_projection_name: str | None = None,
        side: str | None = None,
    ) -> ObjectProjectionGraphBinding:
        """
        Create deterministic ObjectProjectionGraphBinding under one projection declaration.

        Contract:
        - Parent `object_projection_graph_declaration_id` is propagated by constructor lowering.
        - Runtime provider-delta handlers may validate external identity evidence.
        """

        payload = {
            "object_projection_graph_declaration_id": object_projection_graph_declaration_id,
            "fqn_prefix": fqn_prefix,
            "namespace": namespace,
            "class_name": class_name,
            "attribute_name": attribute_name,
            "target_projection_name": target_projection_name,
            "side": side,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_projection_graph_declaration", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectProjectionGraphBinding):
            return value
        return ObjectProjectionGraphBinding.validate_invocation_value(value)


class ObjectProjectionGraphBindingCreateViaObjectProjectionGraphDeclarationInput(BaseModel):
    object_projection_graph_declaration_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphDeclaration.object_projection_graph_bindings"
    )
    fqn_prefix: str
    namespace: str
    class_name: str
    attribute_name: str | None = Field(default=None)
    target_projection_name: str | None = Field(default=None)
    side: str | None = Field(default=None)


class ObjectProjectionGraphBindingCreateViaObjectProjectionGraphDeclarationOutput(BaseModel):
    value: ObjectProjectionGraphBinding


FUNCTIONS = {
    "ObjectProjectionGraphBinding": {
        "create_via_object_projection_graph_declaration": {
            "canonical": {
                "name": "create_via_object_projection_graph_declaration",
                "description": "Create deterministic ObjectProjectionGraphBinding under one projection declaration.\n\nContract:\n- Parent `object_projection_graph_declaration_id` is propagated by constructor lowering.\n- Runtime provider-delta handlers may validate external identity evidence.",
                "is_constructor": True,
            },
            "input": ObjectProjectionGraphBindingCreateViaObjectProjectionGraphDeclarationInput,
            "output": ObjectProjectionGraphBindingCreateViaObjectProjectionGraphDeclarationOutput,
        },
    },
}

__all__ = [
    "ObjectProjectionGraphBinding",
    "ObjectProjectionGraphBindingCreateViaObjectProjectionGraphDeclarationInput",
    "ObjectProjectionGraphBindingCreateViaObjectProjectionGraphDeclarationOutput",
    "FUNCTIONS",
]
