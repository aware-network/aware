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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_attention_ontology.session.attention_session_layout import AttentionSessionLayout
    from aware_identity_ontology.session.session import Session


class AttentionSession(ORMModel):
    """
    Identity-backed Attention session over graph/layout focus state.
    Contract:
    - AttentionSession is the lowest shared Attention primitive over Graph OS.
    - It bridges to Identity Session for actor participation.
    - It owns layout/section/focus transition state without importing higher
    application layers, DTO/API, service, or SDK surfaces.
    """

    # Relationships
    identity_session: Session | None = Field(default=None)
    layouts: list[AttentionSessionLayout] = Field(default_factory=list)
    active_layout: AttentionSessionLayout | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    identity_session_id: UUID = Field(description="Foreign key for AttentionSession.identity_session")
    active_layout_id: UUID | None = Field(default=None, description="Foreign key for AttentionSession.active_layout")

    @classmethod
    async def build(
        cls,
        identity_session_id: UUID,
        key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        status: str = "active",
        source_kind: str | None = None,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> AttentionSession:
        """
        Construct one AttentionSession over an Identity Session.

        Contract:
        - Stable identity is the linked Identity Session.
        - Identity owns actor membership/role/provider participation.
        - Attention owns layout/section/focus transition state only.
        """

        payload = {
            "identity_session_id": identity_session_id,
            "key": key,
            "title": title,
            "description": description,
            "purpose": purpose,
            "status": status,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AttentionSession):
            return value
        return AttentionSession.validate_invocation_value(value)

    async def mount_layout(
        self,
        layout_id: UUID,
        layout_config_id: UUID | None = None,
        key: str | None = None,
        order: int = 0,
        is_active: bool = True,
    ) -> AttentionSessionLayout:
        """
        Mount one Attention Layout into this AttentionSession.

        Contract:
        - Parent AttentionSession scope is injected by propagation.
        - Layout topology remains Attention-owned.
        - This is session-local layout state.
        """

        payload = {
            "layout_id": layout_id,
            "layout_config_id": layout_config_id,
            "key": key,
            "order": order,
            "is_active": is_active,
        }
        result = await invoke_instance(orm_model=self, function_name="mount_layout", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.session.attention_session_layout import AttentionSessionLayout

        if isinstance(value, AttentionSessionLayout):
            return value
        return AttentionSessionLayout.validate_invocation_value(value)

    async def set_active_layout(self, attention_session_layout_id: UUID) -> AttentionSessionLayout:
        """Select the active session-local layout."""

        payload = {"attention_session_layout_id": attention_session_layout_id}
        result = await invoke_instance(orm_model=self, function_name="set_active_layout", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.session.attention_session_layout import AttentionSessionLayout

        if isinstance(value, AttentionSessionLayout):
            return value
        return AttentionSessionLayout.validate_invocation_value(value)


class AttentionSessionBuildInput(BaseModel):
    identity_session_id: UUID
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class AttentionSessionBuildOutput(BaseModel):
    value: AttentionSession


class AttentionSessionMountLayoutInput(BaseModel):
    layout_id: UUID
    layout_config_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    order: int = Field(default=0)
    is_active: bool = Field(default=True)


class AttentionSessionMountLayoutOutput(BaseModel):
    value: AttentionSessionLayout


class AttentionSessionSetActiveLayoutInput(BaseModel):
    attention_session_layout_id: UUID


class AttentionSessionSetActiveLayoutOutput(BaseModel):
    value: AttentionSessionLayout


FUNCTIONS = {
    "AttentionSession": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Construct one AttentionSession over an Identity Session.\n\nContract:\n- Stable identity is the linked Identity Session.\n- Identity owns actor membership/role/provider participation.\n- Attention owns layout/section/focus transition state only.",
                "is_constructor": True,
            },
            "input": AttentionSessionBuildInput,
            "output": AttentionSessionBuildOutput,
        },
        "mount_layout": {
            "canonical": {
                "name": "mount_layout",
                "description": "Mount one Attention Layout into this AttentionSession.\n\nContract:\n- Parent AttentionSession scope is injected by propagation.\n- Layout topology remains Attention-owned.\n- This is session-local layout state.",
                "is_constructor": False,
            },
            "input": AttentionSessionMountLayoutInput,
            "output": AttentionSessionMountLayoutOutput,
        },
        "set_active_layout": {
            "canonical": {
                "name": "set_active_layout",
                "description": "Select the active session-local layout.",
                "is_constructor": False,
            },
            "input": AttentionSessionSetActiveLayoutInput,
            "output": AttentionSessionSetActiveLayoutOutput,
        },
    },
}

__all__ = [
    "AttentionSession",
    "AttentionSessionBuildInput",
    "AttentionSessionBuildOutput",
    "AttentionSessionMountLayoutInput",
    "AttentionSessionMountLayoutOutput",
    "AttentionSessionSetActiveLayoutInput",
    "AttentionSessionSetActiveLayoutOutput",
    "FUNCTIONS",
]
