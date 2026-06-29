from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ObjectProjectionGraphObservable(BaseModel):
    """
    Stable observable descriptor for an ObjectProjectionGraphIdentity.
    Purpose:
    - Provide a canonical, network-shared list of observables (shared-attention selectors)
    under a projection identity.
    - Observables are projection-scoped descriptors that can be selected by FocusScope.
    Notes:
    - Observables are expected to be compiler-owned or system-seeded (deterministic IDs/keys).
    - Experience packages bind observables to views.
    - Interface packages bind Experience views to concrete panes.
    """

    # Attributes
    key: str = Field(description='Stable key for this observable (recommended: "{opg_identity.key}:{observable_key}").')
    observable_key: str = Field(description="Short selector for an observable within a projection family.")
    kind: str | None = Field(
        default=None,
        description='Observable kind:\n- "construct": no branch state required (gate-friendly)\n- "instance": requires branch state (materialized OIGB)',
    )
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)
