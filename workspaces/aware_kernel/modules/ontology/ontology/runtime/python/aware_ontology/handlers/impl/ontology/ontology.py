from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Ontology Ontology
from aware_ontology_ontology.ontology.ontology import Ontology

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Ontology Ontology
from aware_ontology_ontology.ontology.ontology_config import OntologyConfig
from aware_ontology_ontology.stable_ids import stable_ontology_id

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_ontology_config(
    ontology_config_id: UUID, key: str, title: str | None = None, description: str | None = None, status: str = "active"
) -> Ontology:
    """
    Create one concrete ontology authority/worldline.

    Contract:
    - Parent `OntologyConfig` scope is injected by propagation.
    - Identity is parent-scoped by `OntologyConfig.ontologies` plus `key`;
      the child does not author a reverse config reference.
    - `object_instance_graph_identities` is a reference/index surface for
      all OIGIs known to belong under this ontology authority.
    - Head/commit selection remains Meta/history truth and is not modeled
      as a shortcut on `Ontology`.
    """

    # --- AWARE: LOGIC START build_via_ontology_config
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("Ontology.build_via_ontology_config requires non-empty key")
    normalized_status = (status or "").strip() or "active"
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None

    ontology_id = stable_ontology_id(
        ontology_config_id=ontology_config_id,
        key=normalized_key,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_ontology_config = session.imap_get(OntologyConfig, ontology_config_id) if session is not None else None

    if session is not None:
        existing = session.imap_get(Ontology, ontology_id)
        if existing is not None:
            if existing.ontology_config_id != ontology_config_id or (existing.key or "").strip() != normalized_key:
                raise RuntimeError(
                    "Ontology.build_via_ontology_config payload mismatch for " f"ontology_id={ontology_id}"
                )
            if existing.ontology_config is None:
                existing.ontology_config = resolved_ontology_config
            existing.title = normalized_title
            existing.description = normalized_description
            existing.status = normalized_status
            return existing

    return Ontology.model_construct(
        id=ontology_id,
        ontology_config=resolved_ontology_config,
        ontology_config_id=ontology_config_id,
        key=normalized_key,
        title=normalized_title,
        description=normalized_description,
        status=normalized_status,
        object_instance_graph_identities=[],
    )
    # --- AWARE: LOGIC END build_via_ontology_config
