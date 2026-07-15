from __future__ import annotations

from dataclasses import replace
from typing import Any
from uuid import UUID

from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_orm.session.current_session_ctx import set_session
from aware_orm.session.session import Session
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_experience.program.lane_materialized_reader import (
    ProgramLaneMaterializedReader,
)
from aware_experience.program.program_config_impl_loader import (
    load_program_config_impl_snapshot,
)
from aware_experience.program.program_graph_binding_reader import (
    ProgramGraphBindingReader,
)
from aware_experience.program.program_run_receipt_loader import (
    load_program_run_bind_resolution,
)
from aware_experience.program.snapshot_contract import ProgramOntologySnapshot
from aware_experience_ontology.program.impl.program_impl import ProgramImpl
from aware_experience_ontology.program.program_config import ProgramConfig


def _hydrate_oig_into_session(
    *,
    index: Any,
    opg: ObjectProjectionGraph,
    session: Session,
    oig: Any,
    branch_id: UUID,
) -> int:
    hydrated = reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )
    count = 0
    for obj in hydrated.imap_all_objects():
        session.imap_add(obj)
        count += 1
    return count


class ProgramOntologySnapshotReader:
    """
    Canonical typed reader for ProgramConfig|ProgramImpl|Program replay snapshot rails.
    """

    def __init__(
        self,
        *,
        branch_id: UUID,
        environment_id: UUID,
        index: Any | None = None,
    ) -> None:
        self._branch_id: UUID = branch_id
        self._environment_id: UUID = environment_id
        self._index: Any | None = index
        self._lane_reader: ProgramLaneMaterializedReader | None
        if index is None:
            self._lane_reader = None
        else:
            self._lane_reader = ProgramLaneMaterializedReader(
                index=index,
                branch_id=branch_id,
            )

    def _resolve_projection_by_name(
        self, *, projection_name: str
    ) -> ObjectProjectionGraph:
        if self._index is None:
            raise ValueError("Program ontology snapshot decode requires runtime index")
        normalized_name = (projection_name or "").strip().casefold()
        for projection in self._index.opg_by_hash.values():
            candidate_name = (getattr(projection, "name", "") or "").strip().casefold()
            if candidate_name == normalized_name:
                return projection
        raise ValueError(
            "Program ontology snapshot decode could not resolve projection "
            + f"{projection_name!r} in runtime index"
        )

    async def _hydrate_projection_lane_into_session(
        self,
        *,
        session: Session,
        projection_name: str,
    ) -> None:
        if self._index is None or self._lane_reader is None:
            return
        projection = self._resolve_projection_by_name(projection_name=projection_name)
        snapshot = await self._lane_reader.ensure_projection_lane_materialized(
            projection=projection,
        )
        if snapshot is None:
            return
        oig, _indexes = snapshot
        _hydrate_oig_into_session(
            index=self._index,
            opg=projection,
            session=session,
            oig=oig,
            branch_id=self._branch_id,
        )

    async def _resolve_class_instance_identity_ids_by_port_node_id(
        self,
        *,
        program_config_id: UUID,
        required_port_node_ids: tuple[UUID, ...],
    ) -> dict[UUID, UUID]:
        reader = ProgramGraphBindingReader(
            environment_id=self._environment_id,
            program_config_id=program_config_id,
        )
        return await reader.resolve_class_instance_identity_ids_by_port_node_id(
            required_port_node_ids=required_port_node_ids,
        )

    async def load(
        self,
        *,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
        program_id: UUID | None = None,
    ) -> ProgramOntologySnapshot:
        session = Session(branch_id=self._branch_id)
        with set_session(session=session, branch_id=self._branch_id):
            await self._hydrate_projection_lane_into_session(
                session=session,
                projection_name="ProgramConfig",
            )
            await self._hydrate_projection_lane_into_session(
                session=session,
                projection_name="ProgramImpl",
            )
            snapshot = await load_program_config_impl_snapshot(
                program_config_id=program_config_id,
                preferred_program_impl_key=preferred_program_impl_key,
                lane_reader=self._lane_reader,
            )
            if not snapshot.port_rows:
                return snapshot
            required_port_node_ids = tuple(
                sorted(
                    {
                        port_node.id
                        for port_nodes in snapshot.port_nodes_by_port_id.values()
                        for port_node in port_nodes
                    },
                    key=str,
                )
            )
            if not required_port_node_ids:
                raise ValueError(
                    "Program ontology snapshot has ProgramConfigPort rows but no "
                    + "ProgramConfigPortProjectionExperienceNode rows"
                )
            if program_id is None:
                class_instance_identity_ids_by_port_node_id = (
                    await self._resolve_class_instance_identity_ids_by_port_node_id(
                        program_config_id=program_config_id,
                        required_port_node_ids=required_port_node_ids,
                    )
                )
                return replace(
                    snapshot,
                    class_instance_identity_ids_by_port_node_id=class_instance_identity_ids_by_port_node_id,
                )

            bind_resolution = await load_program_run_bind_resolution(
                program_id=program_id,
                instruction_rows=snapshot.instruction_rows,
                instruction_binds_by_id=dict(snapshot.instruction_binds_by_id),
                instruction_invokes_by_id=dict(snapshot.instruction_invokes_by_id),
                invoke_attributes_by_invoke_id=dict(
                    snapshot.invoke_attributes_by_invoke_id
                ),
                actor_configs_by_assoc_id=dict(snapshot.actor_configs_by_assoc_id),
                port_nodes_by_port_id=dict(snapshot.port_nodes_by_port_id),
                lane_reader=self._lane_reader,
            )
            return replace(
                snapshot,
                class_instance_identity_ids_by_port_node_id=bind_resolution.class_instance_identity_ids_by_port_node_id,
                replay_bind_receipts_by_instruction_bind_id=bind_resolution.replay_bind_receipts_by_instruction_bind_id,
                replay_views_by_bind_receipt_id=bind_resolution.replay_views_by_bind_receipt_id,
                replay_action_receipts_by_instruction_intent_id=(
                    bind_resolution.replay_action_receipts_by_instruction_intent_id
                ),
                replay_invoke_receipts_by_instruction_invoke_id=(
                    bind_resolution.replay_invoke_receipts_by_instruction_invoke_id
                ),
                replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id=(
                    bind_resolution.replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id
                ),
            )

    async def resolve_action_continuation_candidates(
        self,
        *,
        action_config_id: UUID,
        event_config_id: UUID,
    ) -> tuple[ProgramOntologySnapshot, ...]:
        """Resolve committed continuation graphs activated by one event action."""

        session = Session(branch_id=self._branch_id)
        with set_session(session=session, branch_id=self._branch_id):
            await self._hydrate_projection_lane_into_session(
                session=session,
                projection_name="ProgramConfig",
            )
            await self._hydrate_projection_lane_into_session(
                session=session,
                projection_name="ProgramImpl",
            )
            program_configs = {
                item.id: item
                for item in session.imap_all_objects()
                if isinstance(item, ProgramConfig)
            }
            program_impls = sorted(
                (
                    item
                    for item in session.imap_all_objects()
                    if isinstance(item, ProgramImpl)
                ),
                key=lambda item: (str(item.program_config_id), item.key, str(item.id)),
            )
            candidates: list[ProgramOntologySnapshot] = []
            for program_impl in program_impls:
                program_config_id = program_impl.program_config_id
                if program_config_id not in program_configs:
                    continue
                snapshot = await load_program_config_impl_snapshot(
                    program_config_id=program_config_id,
                    preferred_program_impl_key=program_impl.key,
                    lane_reader=self._lane_reader,
                )
                incoming_intent_ids = (
                    {
                        intent_id
                        for intent_id, rows in (
                            snapshot.activation_field_bindings_by_intent_id.items()
                        )
                        if rows
                    }
                    | {
                        intent_id
                        for intent_id, rows in snapshot.outcome_field_bindings_by_intent_id.items()
                        if rows
                    }
                    | {
                        intent_id
                        for intent_id, rows in snapshot.receipt_field_bindings_by_intent_id.items()
                        if rows
                    }
                )
                initial_matches = [
                    intent
                    for intent in snapshot.instruction_intents_by_id.values()
                    if intent.id not in incoming_intent_ids
                    and (intent.continuation_key or "").strip()
                    and intent.action_config_id == action_config_id
                    and intent.event_config_id == event_config_id
                ]
                if len(initial_matches) > 1:
                    raise ValueError(
                        "Program continuation graph has ambiguous initial intent: "
                        + f"program_impl_id={program_impl.id}"
                    )
                if initial_matches:
                    candidates.append(snapshot)
            return tuple(candidates)


__all__ = ["ProgramOntologySnapshotReader"]
