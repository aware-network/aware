from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_sdk_ontology_dto.sdk.sdk_operation import SdkOperation


class SdkSurfaceMethod(BaseModel):
    """
    SDK surface method truth.
    Surface methods are the stable SDK-facing method contract that renderers can
    project into CLI commands, Skill targets, or other invocation affordances.
    """

    # Relationships
    target_sdk_operation: SdkOperation | None = Field(default=None)

    # Attributes
    name: str
    operation_ref: str
    operation_name: str
    method_family: str
    effect: str = Field(default="read")
    mutation_scope: str = Field(default="none")
    confirmation_policy: str = Field(default="none")
    execution_mode: str = Field(default="request_response")
    runtime_binding_kind: str = Field(default="unbound")
    description: str | None = Field(default=None)
