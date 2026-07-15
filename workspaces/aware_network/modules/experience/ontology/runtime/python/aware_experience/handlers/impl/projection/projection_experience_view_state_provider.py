from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_view_state_provider import (
    ProjectionExperienceViewStateProvider,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import (
    stable_projection_experience_view_state_provider_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_projection_experience_view(
    projection_experience_view_id: UUID,
    provider_ref: str,
    provider_kind: str = "runtime_callable",
    purity: str = "pure_read",
) -> ProjectionExperienceViewStateProvider:
    """
    Create the deterministic provider binding under one ProjectionExperienceView.

    Contract:
    - Parent ProjectionExperienceView scope is propagated by constructor lowering.
    - Identity is the parent view; changing provider_ref is a semantic migration.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_view
    normalized_provider_ref = (provider_ref or "").strip()
    if not normalized_provider_ref:
        raise RuntimeError(
            "ProjectionExperienceViewStateProvider.build_via_projection_experience_view "
            + "requires non-empty provider_ref"
        )
    normalized_provider_kind = (provider_kind or "").strip() or "runtime_callable"
    normalized_purity = (purity or "").strip() or "pure_read"
    if normalized_purity != "pure_read":
        raise RuntimeError(
            "ProjectionExperienceViewStateProvider only supports pure_read providers: "
            + f"purity={normalized_purity!r}"
        )

    session = current_handler_session()
    state_provider_id = stable_projection_experience_view_state_provider_id(
        projection_experience_view_id=projection_experience_view_id,
    )
    existing = session.imap_get(ProjectionExperienceViewStateProvider, state_provider_id)
    if existing is not None:
        if (
            existing.projection_experience_view_id != projection_experience_view_id
            or existing.provider_ref != normalized_provider_ref
            or existing.provider_kind != normalized_provider_kind
            or existing.purity != normalized_purity
        ):
            raise RuntimeError(
                "ProjectionExperienceViewStateProvider payload mismatch for existing provider: "
                + f"projection_experience_view_state_provider_id={state_provider_id}"
            )
        return existing

    return ProjectionExperienceViewStateProvider(
        id=state_provider_id,
        projection_experience_view_id=projection_experience_view_id,
        provider_ref=normalized_provider_ref,
        provider_kind=normalized_provider_kind,
        purity=normalized_purity,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_view
