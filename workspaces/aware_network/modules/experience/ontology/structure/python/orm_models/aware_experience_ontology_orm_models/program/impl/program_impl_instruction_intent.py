from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_capability_endpoint import ApiCapabilityEndpoint
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_intent_activation_field_binding import (
        ProgramImplInstructionIntentActivationFieldBinding,
    )
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_intent_outcome_field_binding import (
        ProgramImplInstructionIntentOutcomeFieldBinding,
    )
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_intent_receipt_field_binding import (
        ProgramImplInstructionIntentReceiptFieldBinding,
    )
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig
    from aware_reactivity_ontology_orm_models.action.action_config import ActionConfig
    from aware_reactivity_ontology_orm_models.event.event_config import EventConfig


class ProgramImplInstructionIntent(ORMModel):
    """
    Program intent contract step.
    Contract:
    - Declares intended ActionConfig vocabulary.
    - Runtime owns action dispatch/outcomes.
    """

    # Relationships
    action_config: ActionConfig | None = Field(default=None, exclude=True)
    event_config: EventConfig | None = Field(default=None, exclude=True)
    api_capability_endpoint: ApiCapabilityEndpoint | None = Field(default=None, exclude=True)
    request_class_config: ClassConfig | None = Field(default=None, exclude=True)
    response_class_config: ClassConfig | None = Field(default=None, exclude=True)
    activation_field_bindings: list[ProgramImplInstructionIntentActivationFieldBinding] = Field(default_factory=list)
    outcome_field_bindings: list[ProgramImplInstructionIntentOutcomeFieldBinding] = Field(default_factory=list)
    receipt_field_bindings: list[ProgramImplInstructionIntentReceiptFieldBinding] = Field(default_factory=list)

    # Attributes
    continuation_key: str | None = Field(default=None)

    # Foreign Keys
    program_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramImplInstruction.instruction_intent"
    )
    action_config_id: UUID = Field(description="Foreign key for ProgramImplInstructionIntent.action_config")
    event_config_id: UUID = Field(description="Foreign key for ProgramImplInstructionIntent.event_config")
    api_capability_endpoint_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramImplInstructionIntent.api_capability_endpoint"
    )
    request_class_config_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramImplInstructionIntent.request_class_config"
    )
    response_class_config_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramImplInstructionIntent.response_class_config"
    )
