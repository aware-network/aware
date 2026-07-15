from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Code
from aware_code.types import JsonObject

# Economy Ontology
from aware_economy_ontology.price.pricing_policy import PricingPolicy

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Runtime
from aware_economy.stable_ids import stable_pricing_policy_id

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    version: int = 1,
    description: str | None = None,
    policy_json: JsonObject = JsonObject(),
    fail_closed: bool = True,
) -> PricingPolicy:
    """
    Creates one Economy-owned pricing policy receipt.
    """

    # --- AWARE: LOGIC START build
    name_norm = name.strip()
    if not name_norm:
        raise ValueError("pricing_policy.build requires a non-empty name")
    if version < 1:
        raise ValueError("pricing_policy.build requires version >= 1")

    pricing_policy_id = stable_pricing_policy_id(name=name_norm, version=version)
    return PricingPolicy(
        id=pricing_policy_id,
        name=name_norm,
        version=version,
        description=description.strip() if description is not None else None,
        policy_json=policy_json if policy_json is not None else JsonObject({}),
        fail_closed=fail_closed,
    )
    # --- AWARE: LOGIC END build
