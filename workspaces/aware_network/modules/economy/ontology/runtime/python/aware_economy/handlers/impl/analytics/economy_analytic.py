from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.analytics.economy_analytic import EconomyAnalytic

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(key: str = "default", analytic_id: UUID | None = None) -> EconomyAnalytic:
    """
    Creates an Economy-owned analytic container.

    If `analytic_id` is provided, it is used as the object id to support idempotent callers
    that derive stable ids from Economy service roots.
    """

    # --- AWARE: LOGIC START build
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build
