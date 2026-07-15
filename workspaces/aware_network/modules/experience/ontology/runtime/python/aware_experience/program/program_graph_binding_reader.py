from __future__ import annotations

from uuid import UUID

from aware_experience_ontology.program.program_config_graph_program_config import (
    ProgramConfigGraphProgramConfig,
)
from aware_experience_ontology.program import (
    program_config_graph_program_config_port_projection_experience_node_class as _pcg_port_node_class,
)
from aware_experience_ontology.program.program_config_graph_projection_experience_oigi import (
    ProgramConfigGraphProjectionExperienceOIGI,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)

ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass = (
    _pcg_port_node_class.ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass
)


class ProgramGraphBindingReader:
    """
    Typed reader for Experience-owned program graph association rails.

    Centralizes:
    - program_config -> program_config_graph bindings
    - graph port-node -> projection node class identity bindings
    """

    def __init__(
        self,
        *,
        environment_id: UUID,
        program_config_id: UUID,
    ) -> None:
        self._environment_id: UUID = environment_id
        self._program_config_id: UUID = program_config_id

    async def resolve_program_graph_program_config_for_environment(
        self,
    ) -> ProgramConfigGraphProgramConfig:
        program_graph_program_configs = (
            await ProgramConfigGraphProgramConfig.where(
                cache_valid=False,
                program_config_id=self._program_config_id,
            )
            .limit(4096)
            .all()
        )
        if not program_graph_program_configs:
            raise ValueError(
                "Program ontology decode missing ProgramConfigGraphProgramConfig association for "
                + f"program_config_id={self._program_config_id}"
            )

        matching_rows: list[ProgramConfigGraphProgramConfig] = []
        for graph_program_config in program_graph_program_configs:
            projection_experience_oigi_rows = (
                await ProgramConfigGraphProjectionExperienceOIGI.where(
                    cache_valid=False,
                    program_config_graph_id=graph_program_config.program_config_graph_id,
                )
                .limit(4096)
                .all()
            )
            if not projection_experience_oigi_rows:
                continue
            matching_rows.append(graph_program_config)

        if not matching_rows:
            raise ValueError(
                "Program ontology decode missing ProgramConfigGraphProjectionExperienceOIGI association for "
                + f"program_config_id={self._program_config_id} environment_id={self._environment_id}"
            )
        if len(matching_rows) > 1:
            graph_ids = sorted(
                str(row.program_config_graph_id) for row in matching_rows
            )
            raise ValueError(
                "Ambiguous ProgramConfigGraphProgramConfig association for environment-bound decode: "
                + f"program_config_id={self._program_config_id} environment_id={self._environment_id} "
                + f"program_config_graph_ids={graph_ids}"
            )
        return matching_rows[0]

    async def resolve_class_instance_identity_ids_by_port_node_id(
        self,
        *,
        required_port_node_ids: tuple[UUID, ...],
    ) -> dict[UUID, UUID]:
        required_port_node_ids_set = set(required_port_node_ids)
        if not required_port_node_ids_set:
            raise ValueError(
                "Program ontology decode requires non-empty required_port_node_ids for graph binding resolution"
            )
        graph_program_config = (
            await self.resolve_program_graph_program_config_for_environment()
        )
        graph_node_class_rows = (
            await ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.where(
                cache_valid=False,
                program_config_graph_program_config_id=graph_program_config.id,
            )
            .limit(4096)
            .all()
        )
        if not graph_node_class_rows:
            raise ValueError(
                "Program ontology decode missing graph-level port-node class bindings for "
                + f"program_config_id={self._program_config_id} environment_id={self._environment_id}"
            )

        class_instance_identity_ids_by_port_node_id: dict[UUID, UUID] = {}
        for graph_node_class_row in graph_node_class_rows:
            port_node_id = (
                graph_node_class_row.program_config_port_projection_experience_node_id
            )
            if port_node_id not in required_port_node_ids_set:
                raise ValueError(
                    "Program ontology decode found unexpected graph-level port-node class binding "
                    + "outside required port-node contract set: "
                    + f"program_config_port_projection_experience_node_id={port_node_id}"
                )
            if port_node_id in class_instance_identity_ids_by_port_node_id:
                raise ValueError(
                    "Ambiguous ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass mapping for "
                    + f"program_config_port_projection_experience_node_id={port_node_id}"
                )
            node_class_identity = await ProjectionExperienceNodeClassIdentity.by_id(
                graph_node_class_row.projection_experience_node_class_identity_id,
                cache_valid=False,
            )
            if node_class_identity is None:
                raise ValueError(
                    "Program ontology decode references missing ProjectionExperienceNodeClassIdentity: "
                    + f"{graph_node_class_row.projection_experience_node_class_identity_id}"
                )
            class_instance_identity_ids_by_port_node_id[port_node_id] = (
                node_class_identity.class_instance_identity_id
            )

        missing_port_node_ids = required_port_node_ids_set.difference(
            class_instance_identity_ids_by_port_node_id.keys()
        )
        if missing_port_node_ids:
            missing_ids = ", ".join(
                sorted(str(node_id) for node_id in missing_port_node_ids)
            )
            raise ValueError(
                "Program ontology decode missing graph-level class-instance bindings for required "
                + f"ProgramConfigPortProjectionExperienceNode ids: [{missing_ids}]"
            )

        return class_instance_identity_ids_by_port_node_id


__all__ = ["ProgramGraphBindingReader"]
