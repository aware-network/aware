from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.actor.actor_focus_scope_evidence import ActorFocusScopeEvidence

# Code
from aware_code.types import JsonObject

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_actor_focus_scope_evidence_id

# --- AWARE: USER_IMPORTS END


async def create_via_actor_focus_scope(
    actor_focus_scope_id: UUID,
    evidence_key: str,
    kind: str,
    source_type: str | None = None,
    source_id: UUID | None = None,
    source_key: str | None = None,
    weight_delta: float = 0.0,
    confidence: float | None = None,
    observed_at: datetime | None = None,
    expires_at: datetime | None = None,
    rationale: str | None = None,
    metadata: JsonObject | None = None,
) -> ActorFocusScopeEvidence:
    """
    Builds an ActorFocusScopeEvidence receipt under an ActorFocusScope.
    """

    # --- AWARE: LOGIC START create_via_actor_focus_scope
    evidence_key_norm = (evidence_key or "").strip()
    kind_norm = (kind or "").strip()
    if not evidence_key_norm:
        raise ValueError("ActorFocusScopeEvidence.create_via_actor_focus_scope requires a non-empty evidence_key")
    if not kind_norm:
        raise ValueError("ActorFocusScopeEvidence.create_via_actor_focus_scope requires a non-empty kind")

    return ActorFocusScopeEvidence(
        id=stable_actor_focus_scope_evidence_id(
            actor_focus_scope_id=actor_focus_scope_id,
            evidence_key=evidence_key_norm,
        ),
        actor_focus_scope_id=actor_focus_scope_id,
        evidence_key=evidence_key_norm,
        kind=kind_norm,
        source_type=source_type,
        source_id=source_id,
        source_key=source_key,
        weight_delta=weight_delta,
        confidence=confidence,
        observed_at=observed_at,
        expires_at=expires_at,
        rationale=rationale,
        metadata=metadata,
    )
    # --- AWARE: LOGIC END create_via_actor_focus_scope
