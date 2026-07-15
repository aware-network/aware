from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.actor.actor_focus_enums import ActorFocusLevelType
from aware_attention_ontology.actor.actor_focus import ActorFocus
from aware_attention_ontology.actor.actor_focus_evidence import ActorFocusEvidence
from aware_attention_ontology.actor.actor_focus_request import ActorFocusRequest

# Code
from aware_code.types import JsonObject

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from datetime import timezone

from aware_attention_ontology.stable_ids import stable_actor_focus_id

# --- AWARE: USER_IMPORTS END


async def create(
    actor_id: UUID,
    focus_id: UUID,
    level: ActorFocusLevelType | None = ActorFocusLevelType.medium,
    weight: float = 0.0,
    expires_at: datetime | None = None,
    is_active: bool = True,
) -> ActorFocus:
    """
    Builds a new ActorFocus owned by Attention for one Identity Actor.
    """

    # --- AWARE: LOGIC START create
    actor_focus_id = stable_actor_focus_id(actor_id=actor_id, focus_id=focus_id)
    now = datetime.now(timezone.utc)
    return ActorFocus(
        id=actor_focus_id,
        actor_id=actor_id,
        focus_id=focus_id,
        level=level,
        weight=weight,
        expires_at=expires_at,
        is_active=is_active,
        last_accessed=now,
        updated_at=now,
    )
    # --- AWARE: LOGIC END create


async def create_request(
    actor_focus: ActorFocus,
    sender_id: UUID,
    confidence: float,
    expires_at: datetime,
    rationale: str,
    suggested_level: ActorFocusLevelType = ActorFocusLevelType.medium,
) -> ActorFocusRequest:
    """
    Creates a new ActorFocusRequest.
    """

    # --- AWARE: LOGIC START create_request
    return ActorFocusRequest(
        sender_id=sender_id,
        receiver_id=actor_focus.actor_id,
        focus_id=actor_focus.focus_id,
        confidence=confidence,
        expires_at=expires_at,
        rationale=rationale,
        suggested_level=suggested_level or ActorFocusLevelType.medium,
    )
    # --- AWARE: LOGIC END create_request


async def record_evidence(
    actor_focus: ActorFocus,
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
) -> ActorFocusEvidence:
    """
    Records one evidence receipt that contributes to this ActorFocus weight.
    """

    # --- AWARE: LOGIC START record_evidence
    evidence_key_norm = (evidence_key or "").strip()
    kind_norm = (kind or "").strip()
    if not evidence_key_norm:
        raise ValueError("ActorFocus.record_evidence requires a non-empty evidence_key")
    if not kind_norm:
        raise ValueError("ActorFocus.record_evidence requires a non-empty kind")

    for existing in actor_focus.evidences:
        if existing.evidence_key == evidence_key_norm:
            return existing

    now = datetime.now(timezone.utc)
    evidence_observed_at = observed_at or now
    evidence = await ActorFocusEvidence.create_via_actor_focus(
        actor_focus_id=actor_focus.id,
        evidence_key=evidence_key_norm,
        kind=kind_norm,
        source_type=source_type,
        source_id=source_id,
        source_key=source_key,
        weight_delta=weight_delta,
        confidence=confidence,
        observed_at=evidence_observed_at,
        expires_at=expires_at,
        rationale=rationale,
        metadata=metadata,
    )

    actor_focus.evidences.append(evidence)
    actor_focus.evidence_count = len(actor_focus.evidences)
    actor_focus.weight = (actor_focus.weight or 0.0) + weight_delta
    actor_focus.weight_algorithm = actor_focus.weight_algorithm or "sum_weight_delta_v0"
    actor_focus.weight_computed_at = now
    actor_focus.last_evidence_at = evidence_observed_at
    actor_focus.updated_at = now
    return evidence
    # --- AWARE: LOGIC END record_evidence
