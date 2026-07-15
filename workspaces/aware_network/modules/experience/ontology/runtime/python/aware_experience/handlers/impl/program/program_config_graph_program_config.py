from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_config_graph_program_config import ProgramConfigGraphProgramConfig
from aware_experience_ontology.program.\
    program_config_graph_program_config_port_projection_experience_node_class import (
        ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass,
    )

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Ontology
from aware_experience_ontology.program.program_config import ProgramConfig
from aware_experience.stable_ids import (
    stable_program_config_graph_program_config_id,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)

from aware_meta.runtime.handler_context import (
    current_handler_context,
    current_handler_index,
    current_handler_session,
)
from aware_meta.runtime.oig_model_reifier import reify_oig_session

# --- AWARE: USER_IMPORTS END


async def add_port_projection_experience_node_class(
    program_config_graph_program_config: ProgramConfigGraphProgramConfig,
    program_config_port_projection_experience_node_id: UUID,
    projection_experience_node_class_identity_id: UUID,
    key: str | None = None,
) -> ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass:
    """
    Attach one graph-level wiring edge from program port-node contract to shared projection node-class
    identity.
    """

    # --- AWARE: LOGIC START add_port_projection_experience_node_class
    program_config_graph_program_config_id = program_config_graph_program_config.id
    normalized_key = (key or "").strip() or None
    created = await ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.build_via_program_config_graph_program_config(
        program_config_graph_program_config_id=program_config_graph_program_config_id,
        program_config_port_projection_experience_node_id=program_config_port_projection_experience_node_id,
        projection_experience_node_class_identity_id=projection_experience_node_class_identity_id,
        key=normalized_key,
    )
    for existing in program_config_graph_program_config.port_projection_experience_node_classes:
        if existing.id == created.id:
            return existing
    program_config_graph_program_config.port_projection_experience_node_classes.append(created)
    return created
    # --- AWARE: LOGIC END add_port_projection_experience_node_class


async def build_via_program_config_graph(
    program_config_graph_id: UUID, program_config_id: UUID, key: str | None = None
) -> ProgramConfigGraphProgramConfig:
    """
    Create a deterministic ProgramConfigGraphProgramConfig under a ProgramConfigGraph.

    Contract:
    - Parent graph context (`program_config_graph_id`) is injected by parent-edge lowering.
    - Identity is derived from `(program_config_graph_id, program_config_id)`.
    """

    # --- AWARE: LOGIC START build_via_program_config_graph
    normalized_key = (key or "").strip() or None
    session = current_handler_session()
    assoc_id = stable_program_config_graph_program_config_id(
        program_config_graph_id=program_config_graph_id,
        program_config_id=program_config_id,
    )
    program_config = session.imap_get(ProgramConfig, program_config_id)
    if program_config is None:
        ctx = current_handler_context()
        index = current_handler_index()
        if ctx.branch_id is None:
            raise RuntimeError(
                "ProgramConfigGraphProgramConfig.build_via_program_config_graph requires branch_id in handler context"
            )

        target_opgs = [opg for opg in index.opg_by_hash.values() if (opg.name or "") == "ProgramConfig"]
        if len(target_opgs) != 1:
            raise RuntimeError(
                "ProgramConfigGraphProgramConfig.build_via_program_config_graph requires exactly one "
                f"program_config projection (found={len(target_opgs)})"
            )
        target_opg = target_opgs[0]
        target_projection_hash = target_opg.projection_hash

        store = FSCommitStore()
        target_head = await store.head(
            branch_id=ctx.branch_id,
            projection_hash=target_projection_hash,
        )
        if target_head is None or not target_head.get("commit_id"):
            raise RuntimeError(
                "ProgramConfigGraphProgramConfig.build_via_program_config_graph requires existing ProgramConfig: "
                f"program_config_id={program_config_id}"
            )
        target_commit_id = UUID(str(target_head["commit_id"]))
        target_oig_id = (
            UUID(str(target_head["object_instance_graph_id"])) if target_head.get("object_instance_graph_id") else None
        )
        target_oig, _ = await CachedLaneMaterializer().get(
            branch_id=ctx.branch_id,
            ocg=index.ocg,
            opg=target_opg,
            commit_id=target_commit_id,
            oig_id=target_oig_id,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        scratch = reify_oig_session(
            index=index,
            opg=target_opg,
            oig=target_oig,
            branch_id=ctx.branch_id,
        )
        hydrated_program = scratch.imap_get(ProgramConfig, program_config_id)
        if hydrated_program is None:
            raise RuntimeError(
                "ProgramConfigGraphProgramConfig.build_via_program_config_graph requires existing ProgramConfig: "
                f"program_config_id={program_config_id}"
            )
        session.merge(hydrated_program)
        program_config = session.imap_get(ProgramConfig, program_config_id)
        if program_config is None:
            raise RuntimeError(
                "ProgramConfigGraphProgramConfig.build_via_program_config_graph failed to merge ProgramConfig "
                f"into session: program_config_id={program_config_id}"
            )
    existing = session.imap_get(ProgramConfigGraphProgramConfig, assoc_id)
    if existing is not None:
        existing_key = (existing.key or "").strip() or None
        if (
            existing.program_config_graph_id != program_config_graph_id
            or existing.program_config_id != program_config_id
            or existing_key != normalized_key
        ):
            raise RuntimeError(
                "ProgramConfigGraphProgramConfig.build_via_program_config_graph payload mismatch for existing association: "
                f"association_id={assoc_id}"
            )
        existing.program_config = program_config
        return existing

    return ProgramConfigGraphProgramConfig(
        id=assoc_id,
        program_config_graph_id=program_config_graph_id,
        program_config_id=program_config_id,
        program_config=program_config,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build_via_program_config_graph
