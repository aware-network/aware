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

# Reactivity Ontology
from aware_reactivity_ontology.action.action_enums import (
    ActionExecutionStatus,
    ActionIntentStatus,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
    from aware_reactivity_ontology.action.action_config import ActionConfig
    from aware_reactivity_ontology.action.action_execution import ActionExecution


class ActionIntent(ORMModel):
    # Relationships
    action_executions: list[ActionExecution] = Field(default_factory=list, exclude=True)
    config: ActionConfig | None = Field(default=None, exclude=True)
    payload_model: InlineValueInstance | None = Field(default=None)

    # Attributes
    action_payload: JsonObject = Field(
        default_factory=JsonObject,
        description="Deprecated compatibility payload mirror.\nCanonical typed payload truth is `payload_model`, whose ClassConfig is\nresolved by Experience policy from the bound endpoint request config.",
    )
    action_type: str | None = Field(default=None)
    actor_id: UUID | None = Field(
        default=None,
        description="Deprecated actor-provenance mirror.\nReactivity owns lifecycle only. Caller provenance is owned by the\nsubscription bridge or Experience program receipt rails.",
    )
    actor_subscription_id: UUID | None = Field(
        default=None,
        description="Deprecated subscription-provenance mirror.\nStable identity migrated to caller-supplied `intent_key`; subscription\ncallers derive that key in their bridge layer.",
    )
    intent_key: str = Field(
        description="Caller-supplied opaque idempotency key for this event/action intent.\nReactivity treats this as an uninterpreted primitive. Program,\nsubscription, and future caller rails own derivation/provenance."
    )
    priority: int = Field(default=0)
    status: ActionIntentStatus = Field(default=ActionIntentStatus.requested)
    subscription_filter_config: JsonObject = Field(
        default_factory=JsonObject,
        description="Deprecated subscription-provenance mirror.\nResolver-owned subscription policy context lives above Reactivity.",
    )
    target_actor_id: UUID | None = Field(
        default=None,
        description="Deprecated actor-provenance mirror.\nDispatch-time registration, not ActionIntent identity, decides\nfulfillment routing.",
    )

    # Foreign Keys
    event_id: UUID = Field(description="Foreign key for Event.action_intents")
    config_id: UUID = Field(description="Foreign key for ActionIntent.config")
    payload_model_id: UUID | None = Field(default=None, description="Foreign key for ActionIntent.payload_model")

    async def start_execution(
        self,
        execution_key: str = "primary",
        status: ActionExecutionStatus = ActionExecutionStatus.created,
        execution_context: JsonObject = {},
    ) -> ActionExecution:
        """Create one service-fulfillment execution promise for this intent."""

        payload = {"execution_key": execution_key, "status": status, "execution_context": execution_context}
        result = await invoke_instance(orm_model=self, function_name="start_execution", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.action.action_execution import ActionExecution

        if isinstance(value, ActionExecution):
            return value
        return ActionExecution.validate_invocation_value(value)

    async def set_status(self, status: ActionIntentStatus) -> None:
        """Update intent status without mutating execution lifecycle truth."""

        payload = {"status": status}
        await invoke_instance(orm_model=self, function_name="set_status", payload=payload)
        return None

    @classmethod
    async def create_via_event(
        cls,
        event_id: UUID,
        config_id: UUID,
        intent_key: str,
        action_type: str | None = None,
        actor_id: UUID | None = None,
        target_actor_id: UUID | None = None,
        actor_subscription_id: UUID | None = None,
        action_payload: JsonObject = {},
        payload_class_config_id: UUID | None = None,
        subscription_filter_config: JsonObject = {},
        priority: int = 0,
        status: ActionIntentStatus = ActionIntentStatus.requested,
    ) -> ActionIntent:
        """
        Create commit-backed Reactivity action intent evidence for a raised event.

        Contract:
        - This is the canonical "should react" record.
        - Stable-id migration B1: deterministic id is derived from event,
          action config, and caller-supplied `intent_key`; actor subscription no
          longer participates in identity.
        - `payload_model` is typed request payload evidence. Its ClassConfig is
          supplied by the Experience/API resolver; Reactivity remains API-agnostic.
        - `action_payload` is deprecated compatibility metadata only.
        - Actor/subscription fields are deprecated provenance mirrors; caller
          provenance lives in the bridge/Experience receipt rails.
        """

        payload = {
            "event_id": event_id,
            "config_id": config_id,
            "intent_key": intent_key,
            "action_type": action_type,
            "actor_id": actor_id,
            "target_actor_id": target_actor_id,
            "actor_subscription_id": actor_subscription_id,
            "action_payload": action_payload,
            "payload_class_config_id": payload_class_config_id,
            "subscription_filter_config": subscription_filter_config,
            "priority": priority,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_event", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActionIntent):
            return value
        return ActionIntent.validate_invocation_value(value)


class ActionIntentStartExecutionInput(BaseModel):
    execution_key: str = Field(default="primary")
    status: ActionExecutionStatus = Field(default=ActionExecutionStatus.created)
    execution_context: JsonObject = Field(default_factory=JsonObject)


class ActionIntentStartExecutionOutput(BaseModel):
    value: ActionExecution


class ActionIntentSetStatusInput(BaseModel):
    status: ActionIntentStatus


class ActionIntentSetStatusOutput(BaseModel):
    pass


class ActionIntentCreateViaEventInput(BaseModel):
    event_id: UUID = Field(description="Foreign key for Event.action_intents")
    config_id: UUID
    intent_key: str
    action_type: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    target_actor_id: UUID | None = Field(default=None)
    actor_subscription_id: UUID | None = Field(default=None)
    action_payload: JsonObject = Field(default_factory=JsonObject)
    payload_class_config_id: UUID | None = Field(default=None)
    subscription_filter_config: JsonObject = Field(default_factory=JsonObject)
    priority: int = Field(default=0)
    status: ActionIntentStatus = Field(default=ActionIntentStatus.requested)


class ActionIntentCreateViaEventOutput(BaseModel):
    value: ActionIntent


FUNCTIONS = {
    "ActionIntent": {
        "start_execution": {
            "canonical": {
                "name": "start_execution",
                "description": "Create one service-fulfillment execution promise for this intent.",
                "is_constructor": False,
            },
            "input": ActionIntentStartExecutionInput,
            "output": ActionIntentStartExecutionOutput,
        },
        "set_status": {
            "canonical": {
                "name": "set_status",
                "description": "Update intent status without mutating execution lifecycle truth.",
                "is_constructor": False,
            },
            "input": ActionIntentSetStatusInput,
            "output": ActionIntentSetStatusOutput,
        },
        "create_via_event": {
            "canonical": {
                "name": "create_via_event",
                "description": 'Create commit-backed Reactivity action intent evidence for a raised event.\n\nContract:\n- This is the canonical "should react" record.\n- Stable-id migration B1: deterministic id is derived from event,\n  action config, and caller-supplied `intent_key`; actor subscription no\n  longer participates in identity.\n- `payload_model` is typed request payload evidence. Its ClassConfig is\n  supplied by the Experience/API resolver; Reactivity remains API-agnostic.\n- `action_payload` is deprecated compatibility metadata only.\n- Actor/subscription fields are deprecated provenance mirrors; caller\n  provenance lives in the bridge/Experience receipt rails.',
                "is_constructor": True,
            },
            "input": ActionIntentCreateViaEventInput,
            "output": ActionIntentCreateViaEventOutput,
        },
    },
}

__all__ = [
    "ActionIntent",
    "ActionIntentStartExecutionInput",
    "ActionIntentStartExecutionOutput",
    "ActionIntentSetStatusInput",
    "ActionIntentSetStatusOutput",
    "ActionIntentCreateViaEventInput",
    "ActionIntentCreateViaEventOutput",
    "FUNCTIONS",
]
