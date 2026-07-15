from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_sdk_ontology_orm_models.sdk.sdk_operation import SdkOperation


class SdkSurfaceMethod(ORMModel):
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

    # Foreign Keys
    sdk_surface_id: UUID = Field(description="Foreign key for SdkSurface.methods")
    target_sdk_operation_id: UUID | None = Field(
        default=None, description="Foreign key for SdkSurfaceMethod.target_sdk_operation"
    )
