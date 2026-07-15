from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.environment.environment_ontology import EnvironmentOntology

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_environment_ontology_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment(
    environment_id: UUID,
    ontology_id: UUID,
    role: str = "runtime",
    status: str = "active",
    title: str | None = None,
    description: str | None = None,
) -> EnvironmentOntology:
    """
    Construct one Environment-owned Ontology membership.

    Contract:
    - Parent Environment scope is injected by propagation.
    - Identity is Environment path plus target Ontology.
    - `ontology_id` points to the Ontology authority root.
    - OIGI inventory remains reachable only from the linked Ontology.
    """

    # --- AWARE: LOGIC START build_via_environment
    environment_ontology_id = stable_environment_ontology_id(
        environment_id=environment_id,
        ontology_id=ontology_id,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(
        EnvironmentOntology,
        environment_ontology_id,
    )
    if existing is not None:
        if existing.environment_id != environment_id or existing.ontology_id != ontology_id:
            raise RuntimeError(
                "EnvironmentOntology.build_via_environment mismatch "
                f"for existing membership: environment_ontology_id={environment_ontology_id}"
            )
        existing.ontology = None
        return existing

    return EnvironmentOntology(
        id=environment_ontology_id,
        environment_id=environment_id,
        ontology=None,
        ontology_id=ontology_id,
        role=role,
        status=status,
        title=title,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_environment
