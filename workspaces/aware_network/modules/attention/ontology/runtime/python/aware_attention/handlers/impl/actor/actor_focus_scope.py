from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.actor.actor_focus_scope import ActorFocusScope
from aware_attention_ontology.actor.actor_focus_scope_evidence import ActorFocusScopeEvidence
from aware_attention_ontology.actor.actor_focus_scope_request import ActorFocusScopeRequest

# Code
from aware_code.types import JsonObject

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from datetime import timezone

from aware_attention_ontology.stable_ids import stable_actor_focus_scope_id

# --- AWARE: USER_IMPORTS END


async def create(actor_id: UUID, focus_scope_id: UUID) -> ActorFocusScope:
    """
    Builds a new ActorFocusScope by linking an Identity Actor to FocusScope.
    """

    # --- AWARE: LOGIC START create
    actor_focus_scope_id = stable_actor_focus_scope_id(
        actor_id=actor_id,
        focus_scope_id=focus_scope_id,
    )
    existing = ActorFocusScope.by_id_cached(actor_focus_scope_id)
    if existing is not None:
        if existing.actor_id != actor_id:
            raise ValueError(
                "ActorFocusScope.create stable-id collision for different actor ownership: "
                f"actor_focus_scope_id={actor_focus_scope_id} "
                f"existing_actor_id={existing.actor_id} requested_actor_id={actor_id}"
            )
        return existing
    return ActorFocusScope(
        id=actor_focus_scope_id,
        actor_id=actor_id,
        focus_scope_id=focus_scope_id,
    )
    # --- AWARE: LOGIC END create


async def add_request(actor_focus_scope: ActorFocusScope, focus_scope_request_id: UUID) -> ActorFocusScopeRequest:
    """
    Links a FocusScopeRequest under this ActorFocusScope.
    """

    # --- AWARE: LOGIC START add_request
    request = await ActorFocusScopeRequest.create_via_actor_focus_scope(
        actor_focus_scope_id=actor_focus_scope.id,
        focus_scope_request_id=focus_scope_request_id,
    )
    if all(x.id != request.id for x in actor_focus_scope.requests):
        actor_focus_scope.requests.append(request)
    return request
    # --- AWARE: LOGIC END add_request


async def record_evidence(
    actor_focus_scope: ActorFocusScope,
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
    Records one evidence receipt that contributes to this ActorFocusScope weight.
    """

    # --- AWARE: LOGIC START record_evidence
    evidence_key_norm = (evidence_key or "").strip()
    kind_norm = (kind or "").strip()
    if not evidence_key_norm:
        raise ValueError("ActorFocusScope.record_evidence requires a non-empty evidence_key")
    if not kind_norm:
        raise ValueError("ActorFocusScope.record_evidence requires a non-empty kind")

    for existing in actor_focus_scope.evidences:
        if existing.evidence_key == evidence_key_norm:
            return existing

    now = datetime.now(timezone.utc)
    evidence_observed_at = observed_at or now
    evidence = await ActorFocusScopeEvidence.create_via_actor_focus_scope(
        actor_focus_scope_id=actor_focus_scope.id,
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

    actor_focus_scope.evidences.append(evidence)
    actor_focus_scope.evidence_count = len(actor_focus_scope.evidences)
    actor_focus_scope.weight = (actor_focus_scope.weight or 0.0) + weight_delta
    actor_focus_scope.weight_algorithm = actor_focus_scope.weight_algorithm or "sum_weight_delta_v0"
    actor_focus_scope.weight_computed_at = now
    actor_focus_scope.last_evidence_at = evidence_observed_at
    actor_focus_scope.updated_at = now
    return evidence
    # --- AWARE: LOGIC END record_evidence
