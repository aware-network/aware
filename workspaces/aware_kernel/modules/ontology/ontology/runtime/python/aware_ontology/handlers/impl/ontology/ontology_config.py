from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Ontology Ontology
from aware_ontology_ontology.ontology.ontology import Ontology
from aware_ontology_ontology.ontology.ontology_config import OntologyConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

# Ontology Ontology
from aware_ontology_ontology.stable_ids import stable_ontology_config_id

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    fqn_prefix: str,
    object_config_graph_id: UUID | None = None,
    object_config_graph_object_instance_graph_commit_id: UUID | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    schema_hash: str | None = None,
) -> OntologyConfig:
    """
    Create the ontology-owned config/schema root.

    Contract:
    - Identity is keyed by `(name, fqn_prefix)` and intentionally matches
      the package-level semantic identity.
    - `object_config_graph_id` points at Meta-owned schema truth.
    - `object_config_graph_object_instance_graph_commit_id` pins the exact
      OCG root commit used to replay this config.
    - Package-level OCG package replay stays on `OntologyPackage`; the
      config root owns the direct OCG relationship.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    normalized_fqn_prefix = (fqn_prefix or "").strip()
    if not normalized_name:
        raise RuntimeError("OntologyConfig.build requires non-empty name")
    if not normalized_fqn_prefix:
        raise RuntimeError("OntologyConfig.build requires non-empty fqn_prefix")

    ontology_config_id = stable_ontology_config_id(
        name=normalized_name,
        fqn_prefix=normalized_fqn_prefix,
    )
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_schema_hash = (schema_hash or "").strip() or None

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_object_config_graph = (
        session.imap_get(ObjectConfigGraph, object_config_graph_id)
        if session is not None and object_config_graph_id is not None
        else None
    )
    resolved_ocg_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            object_config_graph_object_instance_graph_commit_id,
        )
        if session is not None and object_config_graph_object_instance_graph_commit_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(OntologyConfig, ontology_config_id)
        if existing is not None:
            if (existing.name or "").strip() != normalized_name or (
                existing.fqn_prefix or ""
            ).strip() != normalized_fqn_prefix:
                raise RuntimeError(
                    "OntologyConfig.build payload mismatch for existing config: "
                    f"ontology_config_id={ontology_config_id}"
                )
            if object_config_graph_id is not None and existing.object_config_graph_id not in {
                None,
                object_config_graph_id,
            }:
                raise RuntimeError(
                    "OntologyConfig.build object_config_graph_id mismatch for "
                    f"ontology_config_id={ontology_config_id}"
                )
            if (
                object_config_graph_object_instance_graph_commit_id is not None
                and existing.object_config_graph_object_instance_graph_commit_id
                not in {None, object_config_graph_object_instance_graph_commit_id}
            ):
                raise RuntimeError(
                    "OntologyConfig.build object_config_graph commit mismatch for "
                    f"ontology_config_id={ontology_config_id}"
                )
            if object_config_graph_id is not None:
                existing.object_config_graph_id = object_config_graph_id
                existing.object_config_graph = resolved_object_config_graph
            if object_config_graph_object_instance_graph_commit_id is not None:
                existing.object_config_graph_object_instance_graph_commit_id = (
                    object_config_graph_object_instance_graph_commit_id
                )
                existing.object_config_graph_object_instance_graph_commit = resolved_ocg_commit
            existing.version_number = version_number
            existing.title = normalized_title
            existing.description = normalized_description
            existing.schema_hash = normalized_schema_hash
            return existing

    return OntologyConfig.model_construct(
        id=ontology_config_id,
        name=normalized_name,
        fqn_prefix=normalized_fqn_prefix,
        object_config_graph=resolved_object_config_graph,
        object_config_graph_id=object_config_graph_id,
        object_config_graph_object_instance_graph_commit=resolved_ocg_commit,
        object_config_graph_object_instance_graph_commit_id=(object_config_graph_object_instance_graph_commit_id),
        version_number=version_number,
        title=normalized_title,
        description=normalized_description,
        schema_hash=normalized_schema_hash,
    )
    # --- AWARE: LOGIC END build


async def create_ontology(
    ontology_config: OntologyConfig,
    key: str,
    title: str | None = None,
    description: str | None = None,
    status: str = "active",
) -> Ontology:
    """
    Create one concrete ontology authority/worldline for this config.

    Contract:
    - Parent `OntologyConfig` scope is injected by propagation.
    - OIGI membership is registered through the Ontology authority surface;
      this constructor only creates the ontology authority root.
    """

    # --- AWARE: LOGIC START create_ontology
    ontology = await Ontology.build_via_ontology_config(
        ontology_config_id=ontology_config.id,
        key=key,
        title=title,
        description=description,
        status=status,
    )
    if all(existing.id != ontology.id for existing in ontology_config.ontologies):
        ontology_config.ontologies.append(ontology)
    return ontology
    # --- AWARE: LOGIC END create_ontology
