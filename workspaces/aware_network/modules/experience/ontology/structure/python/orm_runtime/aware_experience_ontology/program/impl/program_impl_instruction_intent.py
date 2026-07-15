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
    from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
    from aware_experience_ontology.program.impl.program_impl_instruction_intent_activation_field_binding import (
        ProgramImplInstructionIntentActivationFieldBinding,
    )
    from aware_experience_ontology.program.impl.program_impl_instruction_intent_outcome_field_binding import (
        ProgramImplInstructionIntentOutcomeFieldBinding,
    )
    from aware_experience_ontology.program.impl.program_impl_instruction_intent_receipt_field_binding import (
        ProgramImplInstructionIntentReceiptFieldBinding,
    )
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_reactivity_ontology.action.action_config import ActionConfig
    from aware_reactivity_ontology.event.event_config import EventConfig


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

    async def add_activation_field_binding(
        self,
        source_class_config_id: UUID,
        source_attribute_config_id: UUID,
        target_request_attribute_config_id: UUID,
        source_input_key: str,
        required: bool = True,
        position: int | None = None,
    ) -> ProgramImplInstructionIntentActivationFieldBinding:
        payload = {
            "source_class_config_id": source_class_config_id,
            "source_attribute_config_id": source_attribute_config_id,
            "target_request_attribute_config_id": target_request_attribute_config_id,
            "source_input_key": source_input_key,
            "required": required,
            "position": position,
        }
        result = await invoke_instance(orm_model=self, function_name="add_activation_field_binding", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.impl.program_impl_instruction_intent_activation_field_binding import (
            ProgramImplInstructionIntentActivationFieldBinding,
        )

        if isinstance(value, ProgramImplInstructionIntentActivationFieldBinding):
            return value
        return ProgramImplInstructionIntentActivationFieldBinding.validate_invocation_value(value)

    async def add_outcome_field_binding(
        self,
        source_program_impl_instruction_intent_id: UUID,
        source_response_attribute_config_id: UUID,
        target_request_attribute_config_id: UUID,
        required: bool = True,
        position: int | None = None,
    ) -> ProgramImplInstructionIntentOutcomeFieldBinding:
        payload = {
            "source_program_impl_instruction_intent_id": source_program_impl_instruction_intent_id,
            "source_response_attribute_config_id": source_response_attribute_config_id,
            "target_request_attribute_config_id": target_request_attribute_config_id,
            "required": required,
            "position": position,
        }
        result = await invoke_instance(orm_model=self, function_name="add_outcome_field_binding", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.impl.program_impl_instruction_intent_outcome_field_binding import (
            ProgramImplInstructionIntentOutcomeFieldBinding,
        )

        if isinstance(value, ProgramImplInstructionIntentOutcomeFieldBinding):
            return value
        return ProgramImplInstructionIntentOutcomeFieldBinding.validate_invocation_value(value)

    async def add_receipt_field_binding(
        self,
        source_program_impl_instruction_intent_id: UUID,
        source_receipt_class_config_id: UUID,
        source_receipt_attribute_config_id: UUID,
        target_request_attribute_config_id: UUID,
        required: bool = True,
        position: int | None = None,
    ) -> ProgramImplInstructionIntentReceiptFieldBinding:
        payload = {
            "source_program_impl_instruction_intent_id": source_program_impl_instruction_intent_id,
            "source_receipt_class_config_id": source_receipt_class_config_id,
            "source_receipt_attribute_config_id": source_receipt_attribute_config_id,
            "target_request_attribute_config_id": target_request_attribute_config_id,
            "required": required,
            "position": position,
        }
        result = await invoke_instance(orm_model=self, function_name="add_receipt_field_binding", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.impl.program_impl_instruction_intent_receipt_field_binding import (
            ProgramImplInstructionIntentReceiptFieldBinding,
        )

        if isinstance(value, ProgramImplInstructionIntentReceiptFieldBinding):
            return value
        return ProgramImplInstructionIntentReceiptFieldBinding.validate_invocation_value(value)

    @classmethod
    async def build_via_program_impl_instruction(
        cls, program_impl_instruction_id: UUID, action_config_id: UUID, event_config_id: UUID
    ) -> ProgramImplInstructionIntent:
        """
        Create deterministic intent payload for one ProgramImplInstruction.

        Contract:
        - Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.
        """

        payload = {
            "program_impl_instruction_id": program_impl_instruction_id,
            "action_config_id": action_config_id,
            "event_config_id": event_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstructionIntent):
            return value
        return ProgramImplInstructionIntent.validate_invocation_value(value)


class ProgramImplInstructionIntentAddActivationFieldBindingInput(BaseModel):
    source_class_config_id: UUID
    source_attribute_config_id: UUID
    target_request_attribute_config_id: UUID
    source_input_key: str
    required: bool = Field(default=True)
    position: int | None = Field(default=None)


class ProgramImplInstructionIntentAddActivationFieldBindingOutput(BaseModel):
    value: ProgramImplInstructionIntentActivationFieldBinding


class ProgramImplInstructionIntentAddOutcomeFieldBindingInput(BaseModel):
    source_program_impl_instruction_intent_id: UUID
    source_response_attribute_config_id: UUID
    target_request_attribute_config_id: UUID
    required: bool = Field(default=True)
    position: int | None = Field(default=None)


class ProgramImplInstructionIntentAddOutcomeFieldBindingOutput(BaseModel):
    value: ProgramImplInstructionIntentOutcomeFieldBinding


class ProgramImplInstructionIntentAddReceiptFieldBindingInput(BaseModel):
    source_program_impl_instruction_intent_id: UUID
    source_receipt_class_config_id: UUID
    source_receipt_attribute_config_id: UUID
    target_request_attribute_config_id: UUID
    required: bool = Field(default=True)
    position: int | None = Field(default=None)


class ProgramImplInstructionIntentAddReceiptFieldBindingOutput(BaseModel):
    value: ProgramImplInstructionIntentReceiptFieldBinding


class ProgramImplInstructionIntentBuildViaProgramImplInstructionInput(BaseModel):
    program_impl_instruction_id: UUID = Field(description="Foreign key for ProgramImplInstruction.instruction_intent")
    action_config_id: UUID
    event_config_id: UUID


class ProgramImplInstructionIntentBuildViaProgramImplInstructionOutput(BaseModel):
    value: ProgramImplInstructionIntent


FUNCTIONS = {
    "ProgramImplInstructionIntent": {
        "add_activation_field_binding": {
            "canonical": {"name": "add_activation_field_binding", "description": None, "is_constructor": False},
            "input": ProgramImplInstructionIntentAddActivationFieldBindingInput,
            "output": ProgramImplInstructionIntentAddActivationFieldBindingOutput,
        },
        "add_outcome_field_binding": {
            "canonical": {"name": "add_outcome_field_binding", "description": None, "is_constructor": False},
            "input": ProgramImplInstructionIntentAddOutcomeFieldBindingInput,
            "output": ProgramImplInstructionIntentAddOutcomeFieldBindingOutput,
        },
        "add_receipt_field_binding": {
            "canonical": {"name": "add_receipt_field_binding", "description": None, "is_constructor": False},
            "input": ProgramImplInstructionIntentAddReceiptFieldBindingInput,
            "output": ProgramImplInstructionIntentAddReceiptFieldBindingOutput,
        },
        "build_via_program_impl_instruction": {
            "canonical": {
                "name": "build_via_program_impl_instruction",
                "description": "Create deterministic intent payload for one ProgramImplInstruction.\n\nContract:\n- Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionIntentBuildViaProgramImplInstructionInput,
            "output": ProgramImplInstructionIntentBuildViaProgramImplInstructionOutput,
        },
    },
}

__all__ = [
    "ProgramImplInstructionIntent",
    "ProgramImplInstructionIntentAddActivationFieldBindingInput",
    "ProgramImplInstructionIntentAddActivationFieldBindingOutput",
    "ProgramImplInstructionIntentAddOutcomeFieldBindingInput",
    "ProgramImplInstructionIntentAddOutcomeFieldBindingOutput",
    "ProgramImplInstructionIntentAddReceiptFieldBindingInput",
    "ProgramImplInstructionIntentAddReceiptFieldBindingOutput",
    "ProgramImplInstructionIntentBuildViaProgramImplInstructionInput",
    "ProgramImplInstructionIntentBuildViaProgramImplInstructionOutput",
    "FUNCTIONS",
]
