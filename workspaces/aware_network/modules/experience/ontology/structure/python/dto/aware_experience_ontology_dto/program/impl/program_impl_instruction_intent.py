from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_capability_endpoint import ApiCapabilityEndpoint
    from aware_experience_ontology_dto.program.impl.program_impl_instruction_intent_activation_field_binding import (
        ProgramImplInstructionIntentActivationFieldBinding,
    )
    from aware_experience_ontology_dto.program.impl.program_impl_instruction_intent_outcome_field_binding import (
        ProgramImplInstructionIntentOutcomeFieldBinding,
    )
    from aware_experience_ontology_dto.program.impl.program_impl_instruction_intent_receipt_field_binding import (
        ProgramImplInstructionIntentReceiptFieldBinding,
    )
    from aware_meta_ontology_dto.class_.class_config import ClassConfig
    from aware_reactivity_ontology_dto.action.action_config import ActionConfig
    from aware_reactivity_ontology_dto.event.event_config import EventConfig


class ProgramImplInstructionIntent(BaseModel):
    """
    Program intent contract step.
    Contract:
    - Declares intended ActionConfig vocabulary.
    - Runtime owns action dispatch/outcomes.
    """

    # Relationships
    action_config: ActionConfig | None = Field(default=None)
    event_config: EventConfig | None = Field(default=None)
    api_capability_endpoint: ApiCapabilityEndpoint | None = Field(default=None)
    request_class_config: ClassConfig | None = Field(default=None)
    response_class_config: ClassConfig | None = Field(default=None)
    activation_field_bindings: list[ProgramImplInstructionIntentActivationFieldBinding] = Field(default_factory=list)
    outcome_field_bindings: list[ProgramImplInstructionIntentOutcomeFieldBinding] = Field(default_factory=list)
    receipt_field_bindings: list[ProgramImplInstructionIntentReceiptFieldBinding] = Field(default_factory=list)

    # Attributes
    continuation_key: str | None = Field(default=None)
