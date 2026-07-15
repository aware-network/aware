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
    from aware_meta_ontology.graph.projection.object_projection_graph_binding import ObjectProjectionGraphBinding


class ObjectProjectionGraphDeclaration(ORMModel):
    """
    Compiler-owned, hashable projection declaration attached to an ObjectConfigGraph.
    This is the SSOT for *membership/portal* semantics of a projection:
    - Which canonical classes participate in a projection (root + members)
    - Which members form explicit cross-projection portals (target_projection_name)
    Notes:
    - Projections are declared in `.aware` via `projection { ... }` (grammar-level construct).
    - The compiler resolves type/member references to canonical namespaces and persists the
    resolved bindings here so the runtime can build OPGs deterministically.
    """

    # Relationships
    object_projection_graph_bindings: list[ObjectProjectionGraphBinding] = Field(default_factory=list)

    # Attributes
    key: str = Field(
        description='Stable key for this projection declaration (recommended: "{ocg.fqn_prefix}:{projection_name}").'
    )
    projection_name: str = Field(
        description="Canonical projection identity name (authored projection symbol unless explicitly overridden)."
    )
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    is_branchable: bool = Field(default=False)

    # Foreign Keys
    object_config_graph_id: UUID = Field(
        description="Foreign key for ObjectConfigGraph.object_projection_graph_declarations"
    )

    async def create_binding(
        self,
        fqn_prefix: str,
        namespace: str,
        class_name: str,
        attribute_name: str | None = None,
        target_projection_name: str | None = None,
        side: str | None = None,
        object_projection_graph_binding_id: UUID | None = None,
    ) -> ObjectProjectionGraphBinding:
        """
        Create deterministic ObjectProjectionGraphBinding under this declaration.

        Contract:
        - Parent `object_projection_graph_declaration_id` is propagated by constructor lowering.
        - `object_projection_graph_binding_id` is provider-delta identity evidence.
        - Binding identity is declaration-scoped; callers must not derive it from class fields alone.
        """

        payload = {
            "fqn_prefix": fqn_prefix,
            "namespace": namespace,
            "class_name": class_name,
            "attribute_name": attribute_name,
            "target_projection_name": target_projection_name,
            "side": side,
            "object_projection_graph_binding_id": object_projection_graph_binding_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_binding", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.projection.object_projection_graph_binding import ObjectProjectionGraphBinding

        if isinstance(value, ObjectProjectionGraphBinding):
            return value
        return ObjectProjectionGraphBinding.validate_invocation_value(value)

    @classmethod
    async def create_via_object_config_graph(
        cls,
        object_config_graph_id: UUID,
        key: str,
        projection_name: str,
        label: str | None = None,
        description: str | None = None,
        is_branchable: bool = False,
    ) -> ObjectProjectionGraphDeclaration:
        """
        Create deterministic ObjectProjectionGraphDeclaration under one ObjectConfigGraph.

        Contract:
        - Parent `object_config_graph_id` is propagated by constructor lowering.
        - Runtime provider-delta handlers may validate external identity evidence.
        """

        payload = {
            "object_config_graph_id": object_config_graph_id,
            "key": key,
            "projection_name": projection_name,
            "label": label,
            "description": description,
            "is_branchable": is_branchable,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_config_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectProjectionGraphDeclaration):
            return value
        return ObjectProjectionGraphDeclaration.validate_invocation_value(value)


class ObjectProjectionGraphDeclarationCreateBindingInput(BaseModel):
    fqn_prefix: str
    namespace: str
    class_name: str
    attribute_name: str | None = Field(default=None)
    target_projection_name: str | None = Field(default=None)
    side: str | None = Field(default=None)
    object_projection_graph_binding_id: UUID | None = Field(default=None)


class ObjectProjectionGraphDeclarationCreateBindingOutput(BaseModel):
    value: ObjectProjectionGraphBinding


class ObjectProjectionGraphDeclarationCreateViaObjectConfigGraphInput(BaseModel):
    object_config_graph_id: UUID = Field(
        description="Foreign key for ObjectConfigGraph.object_projection_graph_declarations"
    )
    key: str
    projection_name: str
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    is_branchable: bool = Field(default=False)


class ObjectProjectionGraphDeclarationCreateViaObjectConfigGraphOutput(BaseModel):
    value: ObjectProjectionGraphDeclaration


FUNCTIONS = {
    "ObjectProjectionGraphDeclaration": {
        "create_binding": {
            "canonical": {
                "name": "create_binding",
                "description": "Create deterministic ObjectProjectionGraphBinding under this declaration.\n\nContract:\n- Parent `object_projection_graph_declaration_id` is propagated by constructor lowering.\n- `object_projection_graph_binding_id` is provider-delta identity evidence.\n- Binding identity is declaration-scoped; callers must not derive it from class fields alone.",
                "is_constructor": False,
            },
            "input": ObjectProjectionGraphDeclarationCreateBindingInput,
            "output": ObjectProjectionGraphDeclarationCreateBindingOutput,
        },
        "create_via_object_config_graph": {
            "canonical": {
                "name": "create_via_object_config_graph",
                "description": "Create deterministic ObjectProjectionGraphDeclaration under one ObjectConfigGraph.\n\nContract:\n- Parent `object_config_graph_id` is propagated by constructor lowering.\n- Runtime provider-delta handlers may validate external identity evidence.",
                "is_constructor": True,
            },
            "input": ObjectProjectionGraphDeclarationCreateViaObjectConfigGraphInput,
            "output": ObjectProjectionGraphDeclarationCreateViaObjectConfigGraphOutput,
        },
    },
}

__all__ = [
    "ObjectProjectionGraphDeclaration",
    "ObjectProjectionGraphDeclarationCreateBindingInput",
    "ObjectProjectionGraphDeclarationCreateBindingOutput",
    "ObjectProjectionGraphDeclarationCreateViaObjectConfigGraphInput",
    "ObjectProjectionGraphDeclarationCreateViaObjectConfigGraphOutput",
    "FUNCTIONS",
]
