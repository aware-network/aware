from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_view_stream_enums import ApiViewStreamMode
from aware_api_ontology.api.api_view_stream_policy import ApiViewStreamPolicy

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_api_view(
    api_view_id: UUID, stream_mode: ApiViewStreamMode, description: str | None = None
) -> ApiViewStreamPolicy:
    """
    Create one API view stream policy beneath ApiView.
    """

    # --- AWARE: LOGIC START build_via_api_view
    return ApiViewStreamPolicy(
        api_view_id=api_view_id,
        stream_mode=stream_mode,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_api_view
