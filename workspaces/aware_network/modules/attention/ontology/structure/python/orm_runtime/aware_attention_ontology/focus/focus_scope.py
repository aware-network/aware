from __future__ import annotations

# Standard
from datetime import datetime
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
    from aware_attention_ontology.focus.focus import Focus
    from aware_attention_ontology.focus.focus_scope_commit import FocusScopeCommit
    from aware_attention_ontology.focus.focus_scope_request import FocusScopeRequest
    from aware_meta_ontology.graph.projection.object_projection_graph_observable import ObjectProjectionGraphObservable


class FocusScope(ORMModel):
    """Attention abstraction that allows to set an scope over DYNAMIC FOCUS."""

    # Relationships
    focus: Focus | None = Field(default=None, exclude=True)
    observable: ObjectProjectionGraphObservable | None = Field(
        default=None,
        exclude=True,
        description="Selected observable for the current focus scope.\nContract:\n- This is a canonical, network-shared selector (commit-backed).\n- FocusScope never owns Experience views. It only owns ontology-backed\nobservable selection.\n- The observable must be an ObjectProjectionGraphObservable (meta) so it can be shared and replayed.",
    )
    requests: list[FocusScopeRequest] = Field(default_factory=list, exclude=True)
    commits: list[FocusScopeCommit] = Field(
        default_factory=list,
        exclude=True,
        description="Commit pins observed while this FocusScope is active.\nContract:\n- FocusScopeCommit is provenance, not a semantic change rail.\n- Each row links the active Focus and an existing Meta ObjectInstanceGraphCommit.\n- Observation time is the create commit time for the FocusScopeCommit itself.",
    )

    # Attributes
    title: str
    description: str | None = Field(default=None)
    rationale: str | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)
    last_accessed: datetime | None = Field(default=None)

    # Foreign Keys
    focus_id: UUID | None = Field(default=None, description="Foreign key for FocusScope.focus")
    observable_id: UUID | None = Field(default=None, description="Foreign key for FocusScope.observable")

    @classmethod
    async def build(
        cls,
        title: str,
        description: str | None = None,
        expires_at: datetime | None = None,
        is_active: bool = True,
        last_accessed: datetime | None = None,
    ) -> FocusScope:
        """Builds a new FocusScope."""

        payload = {
            "title": title,
            "description": description,
            "expires_at": expires_at,
            "is_active": is_active,
            "last_accessed": last_accessed,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FocusScope):
            return value
        return FocusScope.validate_invocation_value(value)

    async def create_request(self, focus_id: UUID, rationale: str | None = None) -> FocusScopeRequest:
        """Creates a new FocusScopeRequest."""

        payload = {"focus_id": focus_id, "rationale": rationale}
        result = await invoke_instance(orm_model=self, function_name="create_request", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.focus.focus_scope_request import FocusScopeRequest

        if isinstance(value, FocusScopeRequest):
            return value
        return FocusScopeRequest.validate_invocation_value(value)

    async def set_focus(self, focus_id: UUID, rationale: str | None = None) -> FocusScope:
        """Sets the current focus for this scope (commit-backed)."""

        payload = {"focus_id": focus_id, "rationale": rationale}
        result = await invoke_instance(orm_model=self, function_name="set_focus", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FocusScope):
            return value
        return FocusScope.validate_invocation_value(value)

    async def set_observable(self, observable_id: UUID, rationale: str | None = None) -> FocusScope:
        """Sets the current observable for this scope (commit-backed)."""

        payload = {"observable_id": observable_id, "rationale": rationale}
        result = await invoke_instance(orm_model=self, function_name="set_observable", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FocusScope):
            return value
        return FocusScope.validate_invocation_value(value)

    async def ensure_commit(self, focus_id: UUID, object_instance_graph_commit_id: UUID) -> FocusScopeCommit:
        """
        Pin one existing Meta OIG commit under this FocusScope context.

        Canonical v0:
        - `focus_id` is mandatory so consumers can replay the attention context.
        - `object_instance_graph_commit_id` points to Meta-owned commit truth.
        - The FocusScopeCommit create commit time is the observed time; no
          separate `observed_at` scalar is modeled in v0.
        """

        payload = {"focus_id": focus_id, "object_instance_graph_commit_id": object_instance_graph_commit_id}
        result = await invoke_instance(orm_model=self, function_name="ensure_commit", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.focus.focus_scope_commit import FocusScopeCommit

        if isinstance(value, FocusScopeCommit):
            return value
        return FocusScopeCommit.validate_invocation_value(value)


class FocusScopeBuildInput(BaseModel):
    title: str
    description: str | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)
    last_accessed: datetime | None = Field(default=None)


class FocusScopeBuildOutput(BaseModel):
    value: FocusScope


class FocusScopeCreateRequestInput(BaseModel):
    focus_id: UUID
    rationale: str | None = Field(default=None)


class FocusScopeCreateRequestOutput(BaseModel):
    value: FocusScopeRequest


class FocusScopeSetFocusInput(BaseModel):
    focus_id: UUID
    rationale: str | None = Field(default=None)


class FocusScopeSetFocusOutput(BaseModel):
    value: FocusScope


class FocusScopeSetObservableInput(BaseModel):
    observable_id: UUID
    rationale: str | None = Field(default=None)


class FocusScopeSetObservableOutput(BaseModel):
    value: FocusScope


class FocusScopeEnsureCommitInput(BaseModel):
    focus_id: UUID
    object_instance_graph_commit_id: UUID


class FocusScopeEnsureCommitOutput(BaseModel):
    value: FocusScopeCommit


FUNCTIONS = {
    "FocusScope": {
        "build": {
            "canonical": {"name": "build", "description": "Builds a new FocusScope.", "is_constructor": True},
            "input": FocusScopeBuildInput,
            "output": FocusScopeBuildOutput,
        },
        "create_request": {
            "canonical": {
                "name": "create_request",
                "description": "Creates a new FocusScopeRequest.",
                "is_constructor": False,
            },
            "input": FocusScopeCreateRequestInput,
            "output": FocusScopeCreateRequestOutput,
        },
        "set_focus": {
            "canonical": {
                "name": "set_focus",
                "description": "Sets the current focus for this scope (commit-backed).",
                "is_constructor": False,
            },
            "input": FocusScopeSetFocusInput,
            "output": FocusScopeSetFocusOutput,
        },
        "set_observable": {
            "canonical": {
                "name": "set_observable",
                "description": "Sets the current observable for this scope (commit-backed).",
                "is_constructor": False,
            },
            "input": FocusScopeSetObservableInput,
            "output": FocusScopeSetObservableOutput,
        },
        "ensure_commit": {
            "canonical": {
                "name": "ensure_commit",
                "description": "Pin one existing Meta OIG commit under this FocusScope context.\n\nCanonical v0:\n- `focus_id` is mandatory so consumers can replay the attention context.\n- `object_instance_graph_commit_id` points to Meta-owned commit truth.\n- The FocusScopeCommit create commit time is the observed time; no\n  separate `observed_at` scalar is modeled in v0.",
                "is_constructor": False,
            },
            "input": FocusScopeEnsureCommitInput,
            "output": FocusScopeEnsureCommitOutput,
        },
    },
}

__all__ = [
    "FocusScope",
    "FocusScopeBuildInput",
    "FocusScopeBuildOutput",
    "FocusScopeCreateRequestInput",
    "FocusScopeCreateRequestOutput",
    "FocusScopeSetFocusInput",
    "FocusScopeSetFocusOutput",
    "FocusScopeSetObservableInput",
    "FocusScopeSetObservableOutput",
    "FocusScopeEnsureCommitInput",
    "FocusScopeEnsureCommitOutput",
    "FUNCTIONS",
]
