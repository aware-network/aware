from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.function.function_config_invocation_enums import (
    FunctionInvocationKind,
    FunctionInvocationRootKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology_orm_models.function.function_config import FunctionConfig


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
