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
    from aware_environment_ontology.environment.environment_session_thread import EnvironmentSessionThread


class EnvironmentNavigationContext(ORMModel):
    """
    Shared Environment navigation surface under an EnvironmentSession.
    Contract:
    - Parent constructor is EnvironmentSession.
    - This is the durable shared OS pointer that Interface windows/tabs follow.
    - One EnvironmentSession may own many navigation contexts.
    - SessionThread target changes are committed state; history is derived by
    commit replay and no EnvironmentNavigationEvent object exists in v0.
    - Attention layout/section focus and Experience lens/action resolution are
    later rails.
    """

    # Relationships
    session_thread: EnvironmentSessionThread | None = Field(default=None)

    # Attributes
    key: str
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    is_default: bool = Field(
        default=False, description="Marks the EnvironmentSession-owned default navigation entrypoint."
    )

    # Foreign Keys
    environment_session_id: UUID = Field(description="Foreign key for EnvironmentSession.navigation_contexts")
    session_thread_id: UUID = Field(description="Foreign key for EnvironmentNavigationContext.session_thread")

    async def select_target(self, session_thread_id: UUID) -> EnvironmentNavigationContext:
        """
        Select the current session-thread target for this navigation context.

        Contract:
        - Mutates only the invoked EnvironmentNavigationContext.
        - Updates only the EnvironmentSessionThread relationship FK.
        - Does not mutate EnvironmentSession or create a session singleton
          cursor.
        - History is the commit trail over this context.
        """

        payload = {"session_thread_id": session_thread_id}
        result = await invoke_instance(orm_model=self, function_name="select_target", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentNavigationContext):
            return value
        return EnvironmentNavigationContext.validate_invocation_value(value)

    @classmethod
    async def build_via_environment_session(
        cls,
        environment_session_id: UUID,
        key: str,
        session_thread_id: UUID,
        title: str | None = None,
        status: str = "active",
        is_default: bool = False,
    ) -> EnvironmentNavigationContext:
        """
        Construct one EnvironmentNavigationContext under an EnvironmentSession.

        Contract:
        - Stable identity is EnvironmentSession path + `key`.
        - `session_thread_id` binds the EnvironmentSessionThread target pin.
        - No parent id is authored here; parent context is propagated by
          containment path.
        """

        payload = {
            "environment_session_id": environment_session_id,
            "key": key,
            "session_thread_id": session_thread_id,
            "title": title,
            "status": status,
            "is_default": is_default,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_environment_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentNavigationContext):
            return value
        return EnvironmentNavigationContext.validate_invocation_value(value)


class EnvironmentNavigationContextSelectTargetInput(BaseModel):
    session_thread_id: UUID


class EnvironmentNavigationContextSelectTargetOutput(BaseModel):
    value: EnvironmentNavigationContext


class EnvironmentNavigationContextBuildViaEnvironmentSessionInput(BaseModel):
    environment_session_id: UUID = Field(description="Foreign key for EnvironmentSession.navigation_contexts")
    key: str
    session_thread_id: UUID
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    is_default: bool = Field(default=False)


class EnvironmentNavigationContextBuildViaEnvironmentSessionOutput(BaseModel):
    value: EnvironmentNavigationContext


FUNCTIONS = {
    "EnvironmentNavigationContext": {
        "select_target": {
            "canonical": {
                "name": "select_target",
                "description": "Select the current session-thread target for this navigation context.\n\nContract:\n- Mutates only the invoked EnvironmentNavigationContext.\n- Updates only the EnvironmentSessionThread relationship FK.\n- Does not mutate EnvironmentSession or create a session singleton\n  cursor.\n- History is the commit trail over this context.",
                "is_constructor": False,
            },
            "input": EnvironmentNavigationContextSelectTargetInput,
            "output": EnvironmentNavigationContextSelectTargetOutput,
        },
        "build_via_environment_session": {
            "canonical": {
                "name": "build_via_environment_session",
                "description": "Construct one EnvironmentNavigationContext under an EnvironmentSession.\n\nContract:\n- Stable identity is EnvironmentSession path + `key`.\n- `session_thread_id` binds the EnvironmentSessionThread target pin.\n- No parent id is authored here; parent context is propagated by\n  containment path.",
                "is_constructor": True,
            },
            "input": EnvironmentNavigationContextBuildViaEnvironmentSessionInput,
            "output": EnvironmentNavigationContextBuildViaEnvironmentSessionOutput,
        },
    },
}

__all__ = [
    "EnvironmentNavigationContext",
    "EnvironmentNavigationContextSelectTargetInput",
    "EnvironmentNavigationContextSelectTargetOutput",
    "EnvironmentNavigationContextBuildViaEnvironmentSessionInput",
    "EnvironmentNavigationContextBuildViaEnvironmentSessionOutput",
    "FUNCTIONS",
]
