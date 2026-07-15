from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology
from aware_meta_ontology.function.function_config_invocation_enums import (
    FunctionInvocationKind,
    FunctionInvocationRootKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology.function.function_config import FunctionConfig


class FunctionConfigInvocation(ORMModel):
    """
    Canonical invocation-plan step owned by FunctionConfig.
    Contract:
    - `FunctionConfig::invocations` defines ordered propagation truth for a function.
    - Steps represent invocation intent (`call` / `construct`) and resolved target function.
    - Receiver traversal is one-hop only and represented by canonical
    `class_config_relationship` when cross-object (no multi-hop path segments).
    - Owner-local calls keep `class_config_relationship` empty.
    - For identity-standalone targets, public constructor names stay path-agnostic; containment/path truth still
    lives on `class_config_relationship` and runtime propagation state.
    """

    # Relationships
    target_function_config: FunctionConfig | None = Field(default=None, exclude=True)
    root_invocation: FunctionConfigInvocation | None = Field(default=None, exclude=True)
    class_config_relationship: ClassConfigRelationship | None = Field(default=None)

    # Attributes
    position: int
    kind: FunctionInvocationKind
    relationship_fingerprint: str = Field(default="owner")
    root_kind: FunctionInvocationRootKind = Field(default=FunctionInvocationRootKind.owner)
    capture_name: str | None = Field(default=None)

    # Foreign Keys
    function_config_id: UUID = Field(description="Foreign key for FunctionConfig.invocations")
    target_function_config_id: UUID = Field(
        description="Foreign key for FunctionConfigInvocation.target_function_config"
    )
    root_invocation_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionConfigInvocation.root_invocation"
    )
    class_config_relationship_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionConfigInvocation.class_config_relationship"
    )

    @classmethod
    async def create_via_function_config(
        cls,
        function_config_id: UUID,
        position: int,
        kind: FunctionInvocationKind,
        target_function_config_id: UUID,
        relationship_fingerprint: str = "owner",
        class_config_relationship_id: UUID | None = None,
        root_invocation_id: UUID | None = None,
        root_kind: FunctionInvocationRootKind = FunctionInvocationRootKind.owner,
        capture_name: str | None = None,
    ) -> FunctionConfigInvocation:
        """
        Create deterministic FunctionConfigInvocation under a parent FunctionConfig path.

        Contract:
        - Parent FunctionConfig ownership is propagated by traversal lowering.
        - Constructor identity keys are
          `(position, kind, target_function_config_id, relationship_fingerprint)` plus propagated parent
        context.
        - `class_config_relationship_id` remains relationship metadata (nullable for owner-local
        invocations).
        - Standalone target constructors still rely on `class_config_relationship_id` for caller-owned
          containment/path routing even when the target function name itself stays semantic (no `_via_*`
        requirement).
        """

        payload = {
            "function_config_id": function_config_id,
            "position": position,
            "kind": kind,
            "target_function_config_id": target_function_config_id,
            "relationship_fingerprint": relationship_fingerprint,
            "class_config_relationship_id": class_config_relationship_id,
            "root_invocation_id": root_invocation_id,
            "root_kind": root_kind,
            "capture_name": capture_name,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_function_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionConfigInvocation):
            return value
        return FunctionConfigInvocation.validate_invocation_value(value)


class FunctionConfigInvocationCreateViaFunctionConfigInput(BaseModel):
    function_config_id: UUID = Field(description="Foreign key for FunctionConfig.invocations")
    position: int
    kind: FunctionInvocationKind
    target_function_config_id: UUID
    relationship_fingerprint: str = Field(default="owner")
    class_config_relationship_id: UUID | None = Field(default=None)
    root_invocation_id: UUID | None = Field(default=None)
    root_kind: FunctionInvocationRootKind = Field(default=FunctionInvocationRootKind.owner)
    capture_name: str | None = Field(default=None)


class FunctionConfigInvocationCreateViaFunctionConfigOutput(BaseModel):
    value: FunctionConfigInvocation


FUNCTIONS = {
    "FunctionConfigInvocation": {
        "create_via_function_config": {
            "canonical": {
                "name": "create_via_function_config",
                "description": "Create deterministic FunctionConfigInvocation under a parent FunctionConfig path.\n\nContract:\n- Parent FunctionConfig ownership is propagated by traversal lowering.\n- Constructor identity keys are\n  `(position, kind, target_function_config_id, relationship_fingerprint)` plus propagated parent context.\n- `class_config_relationship_id` remains relationship metadata (nullable for owner-local invocations).\n- Standalone target constructors still rely on `class_config_relationship_id` for caller-owned\n  containment/path routing even when the target function name itself stays semantic (no `_via_*` requirement).",
                "is_constructor": True,
            },
            "input": FunctionConfigInvocationCreateViaFunctionConfigInput,
            "output": FunctionConfigInvocationCreateViaFunctionConfigOutput,
        },
    },
}

__all__ = [
    "FunctionConfigInvocation",
    "FunctionConfigInvocationCreateViaFunctionConfigInput",
    "FunctionConfigInvocationCreateViaFunctionConfigOutput",
    "FUNCTIONS",
]
