from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.function.function_config_invocation_enums import (
    FunctionInvocationKind,
    FunctionInvocationRootKind,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology_dto.function.function_config import FunctionConfig


class FunctionConfigInvocation(BaseModel):
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
    target_function_config: FunctionConfig | None = Field(default=None)
    root_invocation: FunctionConfigInvocation | None = Field(default=None)
    class_config_relationship: ClassConfigRelationship | None = Field(default=None)

    # Attributes
    position: int
    kind: FunctionInvocationKind
    relationship_fingerprint: str = Field(default="owner")
    root_kind: FunctionInvocationRootKind = Field(default=FunctionInvocationRootKind.owner)
    capture_name: str | None = Field(default=None)
