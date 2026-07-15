from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import cast
from uuid import UUID

from aware_experience.program.lane_materialized_reader import (
    ProgramLaneMaterializedReader,
)

from aware_identity_ontology.actor.actor_config import ActorConfig
from aware_identity_ontology.actor.actor_config_role_config import ActorConfigRoleConfig
from aware_experience_ontology.program.impl.program_impl_instruction import (
    ProgramImplInstruction,
)
from aware_experience_ontology.program.impl.program_impl_instruction_bind import (
    ProgramImplInstructionBind,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke import (
    ProgramImplInstructionInvoke,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke_attribute_config import (
    ProgramImplInstructionInvokeAttributeConfig,
)
from aware_experience_ontology.program.program_config_port_projection_experience_node import (
    ProgramConfigPortProjectionExperienceNode,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_experience_ontology.program.program_actor import ProgramActor
from aware_experience_ontology.program.program_actor_role import ProgramActorRole
from aware_experience_ontology.program.program_turn import ProgramTurn
from aware_experience_ontology.program.program_turn_instruction import (
    ProgramTurnInstruction,
)
from aware_experience_ontology.program.program_turn_instruction_bind import (
    ProgramTurnInstructionBind as ProgramTurnInstructionBindReceipt,
)
from aware_experience_ontology.program.program_turn_instruction_action import (
    ProgramTurnInstructionAction as ProgramTurnInstructionActionReceipt,
)
from aware_experience_ontology.program.program_turn_instruction_bind_identity import (
    ProgramTurnInstructionBindIdentity,
)
from aware_experience_ontology.program.program_turn_instruction_invoke import (
    ProgramTurnInstructionInvoke as ProgramTurnInstructionInvokeReceipt,
)
from aware_experience_ontology.program.program_turn_instruction_invoke_attribute_config import (
    ProgramTurnInstructionInvokeAttributeConfig as ProgramTurnInstructionInvokeAttributeConfigReceipt,
)


def _enum_text(value: object) -> str:
    if isinstance(value, Enum):
        enum_value = cast(object, value.value)
        return str(enum_value or "").strip()
    return str(value or "").strip()


@dataclass(frozen=True, slots=True)
class ProgramRunBindResolution:
    class_instance_identity_ids_by_port_node_id: dict[UUID, UUID]
    replay_bind_receipts_by_instruction_bind_id: dict[
        UUID, ProgramTurnInstructionBindReceipt
    ]
    replay_views_by_bind_receipt_id: dict[UUID, ProjectionExperienceView]
    replay_action_receipts_by_instruction_intent_id: dict[
        UUID, ProgramTurnInstructionActionReceipt
    ]
    replay_invoke_receipts_by_instruction_invoke_id: dict[
        UUID, ProgramTurnInstructionInvokeReceipt
    ]
    replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id: dict[
        UUID, ProgramTurnInstructionInvokeAttributeConfigReceipt
    ]


def _select_latest_program_turn(*, turn_rows: list[ProgramTurn]) -> ProgramTurn:
    if not turn_rows:
        raise ValueError("Program ontology replay decode missing ProgramTurn receipts")
    return max(turn_rows, key=lambda row: (int(row.order), str(row.id)))


async def _load_replay_receipts_for_program(
    *,
    program_id: UUID,
    lane_reader: ProgramLaneMaterializedReader | None = None,
) -> tuple[
    dict[UUID, ProgramTurnInstructionBindReceipt],
    dict[UUID, tuple[ProgramTurnInstructionBindIdentity, ...]],
    dict[UUID, ProgramTurnInstructionActionReceipt],
    dict[UUID, ProgramTurnInstructionInvokeReceipt],
    dict[UUID, tuple[ProgramTurnInstructionInvokeAttributeConfigReceipt, ...]],
    dict[UUID, ProjectionExperienceNodeClassIdentity],
    dict[UUID, ProjectionExperienceNodeIdentity],
    dict[UUID, ProjectionExperienceView],
    dict[UUID, ProgramActorRole],
    dict[UUID, ProgramActor],
    dict[UUID, ActorConfigRoleConfig],
]:
    program_turn_rows = (
        await ProgramTurn.where(
            cache_valid=False,
            program_id=program_id,
        )
        .limit(4096)
        .all()
    )
    if not program_turn_rows:
        raise ValueError(
            "Program ontology replay decode missing ProgramTurn receipts for "
            + f"program_id={program_id}"
        )
    latest_turn = _select_latest_program_turn(turn_rows=program_turn_rows)
    turn_instruction_rows = (
        await ProgramTurnInstruction.where(
            cache_valid=False,
            program_turn_id=latest_turn.id,
        )
        .limit(4096)
        .all()
    )
    if not turn_instruction_rows:
        raise ValueError(
            "Program ontology replay decode missing ProgramTurnInstruction receipts for "
            + f"program_id={program_id} program_turn_id={latest_turn.id}"
        )

    bind_receipts_by_program_instruction_id: dict[
        UUID, ProgramTurnInstructionBindReceipt
    ] = {}
    bind_identity_rows_by_receipt_id: dict[
        UUID, tuple[ProgramTurnInstructionBindIdentity, ...]
    ] = {}
    action_receipts_by_program_instruction_id: dict[
        UUID, ProgramTurnInstructionActionReceipt
    ] = {}
    invoke_receipts_by_program_instruction_id: dict[
        UUID, ProgramTurnInstructionInvokeReceipt
    ] = {}
    invoke_attribute_rows_by_receipt_id: dict[
        UUID, tuple[ProgramTurnInstructionInvokeAttributeConfigReceipt, ...]
    ] = {}
    node_class_identity_ids: set[UUID] = set()
    view_ids: set[UUID] = set()
    program_actor_role_ids: set[UUID] = set()

    for turn_instruction in turn_instruction_rows:
        bind_receipt_id = turn_instruction.bind_receipt_id
        if bind_receipt_id is not None:
            bind_receipt = await ProgramTurnInstructionBindReceipt.by_id(
                bind_receipt_id,
                cache_valid=False,
            )
            if bind_receipt is None:
                raise ValueError(
                    "Program ontology replay decode references missing ProgramTurnInstructionBind: "
                    + f"{bind_receipt_id}"
                )
            existing = bind_receipts_by_program_instruction_id.get(
                turn_instruction.program_instruction_id
            )
            if existing is not None and existing.id != bind_receipt.id:
                raise ValueError(
                    "Ambiguous ProgramTurnInstruction bind receipts for program instruction: "
                    + f"program_instruction_id={turn_instruction.program_instruction_id}"
                )
            bind_receipts_by_program_instruction_id[
                turn_instruction.program_instruction_id
            ] = bind_receipt
            view_ids.add(bind_receipt.projection_experience_view_id)
            bind_identity_rows = (
                await ProgramTurnInstructionBindIdentity.where(
                    cache_valid=False,
                    program_turn_instruction_bind_id=bind_receipt.id,
                )
                .limit(4096)
                .all()
            )
            bind_identity_rows_by_receipt_id[bind_receipt.id] = tuple(
                bind_identity_rows
            )
            for bind_identity_row in bind_identity_rows:
                node_class_identity_ids.add(
                    bind_identity_row.projection_experience_node_class_identity_id
                )

        action_receipt_id = turn_instruction.action_receipt_id
        if action_receipt_id is not None:
            action_receipt = await ProgramTurnInstructionActionReceipt.by_id(
                action_receipt_id,
                cache_valid=False,
            )
            if action_receipt is None:
                raise ValueError(
                    "Program ontology replay decode references missing ProgramTurnInstructionAction: "
                    + f"{action_receipt_id}"
                )
            existing_action = action_receipts_by_program_instruction_id.get(
                turn_instruction.program_instruction_id
            )
            if existing_action is not None and existing_action.id != action_receipt.id:
                raise ValueError(
                    "Ambiguous ProgramTurnInstruction action receipts for program instruction: "
                    + f"program_instruction_id={turn_instruction.program_instruction_id}"
                )
            action_receipts_by_program_instruction_id[
                turn_instruction.program_instruction_id
            ] = action_receipt

        invoke_receipt_id = turn_instruction.invoke_receipt_id
        if invoke_receipt_id is None:
            continue
        invoke_receipt = await ProgramTurnInstructionInvokeReceipt.by_id(
            invoke_receipt_id,
            cache_valid=False,
        )
        if invoke_receipt is None:
            raise ValueError(
                "Program ontology replay decode references missing ProgramTurnInstructionInvoke: "
                + f"{invoke_receipt_id}"
            )
        existing_invoke = invoke_receipts_by_program_instruction_id.get(
            turn_instruction.program_instruction_id
        )
        if existing_invoke is not None and existing_invoke.id != invoke_receipt.id:
            raise ValueError(
                "Ambiguous ProgramTurnInstruction invoke receipts for program instruction: "
                + f"program_instruction_id={turn_instruction.program_instruction_id}"
            )
        invoke_receipts_by_program_instruction_id[
            turn_instruction.program_instruction_id
        ] = invoke_receipt
        program_actor_role_ids.add(invoke_receipt.program_actor_role_id)
        node_class_identity_ids.add(
            invoke_receipt.projection_experience_node_class_identity_id
        )
        invoke_attribute_rows = (
            await ProgramTurnInstructionInvokeAttributeConfigReceipt.where(
                cache_valid=False,
                program_turn_instruction_invoke_id=invoke_receipt.id,
            )
            .limit(4096)
            .all()
        )
        invoke_attribute_rows_by_receipt_id[invoke_receipt.id] = tuple(
            invoke_attribute_rows
        )

    node_class_identities_by_id: dict[UUID, ProjectionExperienceNodeClassIdentity] = {}
    for node_class_identity_id in sorted(node_class_identity_ids, key=str):
        node_class_identity = await ProjectionExperienceNodeClassIdentity.by_id(
            node_class_identity_id,
            cache_valid=False,
        )
        if node_class_identity is None:
            raise ValueError(
                "Program ontology replay decode references missing ProjectionExperienceNodeClassIdentity: "
                + f"{node_class_identity_id}"
            )
        node_class_identities_by_id[node_class_identity_id] = node_class_identity
    projection_node_identity_ids = {
        row.projection_experience_node_identity_id
        for row in node_class_identities_by_id.values()
    }
    projection_node_identities_by_id: dict[UUID, ProjectionExperienceNodeIdentity] = {}
    for projection_node_identity_id in sorted(projection_node_identity_ids, key=str):
        projection_node_identity = await ProjectionExperienceNodeIdentity.by_id(
            projection_node_identity_id,
            cache_valid=False,
        )
        if projection_node_identity is None:
            raise ValueError(
                "Program ontology replay decode references missing ProjectionExperienceNodeIdentity: "
                + f"{projection_node_identity_id}"
            )
        projection_node_identities_by_id[projection_node_identity_id] = (
            projection_node_identity
        )

    views_by_receipt_id: dict[UUID, ProjectionExperienceView] = {}
    views_by_id: dict[UUID, ProjectionExperienceView] = {}
    for view_id in sorted(view_ids, key=str):
        view = await ProjectionExperienceView.by_id(view_id, cache_valid=False)
        if view is None:
            raise ValueError(
                "Program ontology replay decode references missing ProjectionExperienceView: "
                + f"{view_id}"
            )
        views_by_id[view_id] = view
    for bind_receipt in bind_receipts_by_program_instruction_id.values():
        view = views_by_id.get(bind_receipt.projection_experience_view_id)
        if view is None:
            raise ValueError(
                "Program ontology replay decode missing ProjectionExperienceView for bind receipt: "
                + f"{bind_receipt.id}"
            )
        views_by_receipt_id[bind_receipt.id] = view

    if lane_reader is not None and views_by_id:
        projection_ids = {
            view.projection_experience_id for view in views_by_id.values()
        }
        await lane_reader.ensure_projection_lanes_materialized_by_ids(
            projection_ids=projection_ids,
        )

    program_actor_roles_by_id: dict[UUID, ProgramActorRole] = {}
    for program_actor_role_id in sorted(program_actor_role_ids, key=str):
        program_actor_role = await ProgramActorRole.by_id(
            program_actor_role_id,
            cache_valid=False,
        )
        if program_actor_role is None:
            raise ValueError(
                "Program ontology replay decode references missing ProgramActorRole: "
                + f"{program_actor_role_id}"
            )
        program_actor_roles_by_id[program_actor_role_id] = program_actor_role
    program_actor_ids = {
        row.program_actor_id for row in program_actor_roles_by_id.values()
    }
    actor_config_role_config_ids = {
        row.actor_config_role_config_id for row in program_actor_roles_by_id.values()
    }
    program_actors_by_id: dict[UUID, ProgramActor] = {}
    for program_actor_id in sorted(program_actor_ids, key=str):
        program_actor = await ProgramActor.by_id(program_actor_id, cache_valid=False)
        if program_actor is None:
            raise ValueError(
                "Program ontology replay decode references missing ProgramActor: "
                + f"{program_actor_id}"
            )
        program_actors_by_id[program_actor_id] = program_actor
    actor_config_role_configs_by_id: dict[UUID, ActorConfigRoleConfig] = {}
    for actor_config_role_config_id in sorted(actor_config_role_config_ids, key=str):
        actor_config_role_config = await ActorConfigRoleConfig.by_id(
            actor_config_role_config_id,
            cache_valid=False,
        )
        if actor_config_role_config is None:
            raise ValueError(
                "Program ontology replay decode references missing ActorConfigRoleConfig: "
                + f"{actor_config_role_config_id}"
            )
        actor_config_role_configs_by_id[actor_config_role_config_id] = (
            actor_config_role_config
        )

    return (
        bind_receipts_by_program_instruction_id,
        bind_identity_rows_by_receipt_id,
        action_receipts_by_program_instruction_id,
        invoke_receipts_by_program_instruction_id,
        invoke_attribute_rows_by_receipt_id,
        node_class_identities_by_id,
        projection_node_identities_by_id,
        views_by_receipt_id,
        program_actor_roles_by_id,
        program_actors_by_id,
        actor_config_role_configs_by_id,
    )


def _resolve_replay_bind_contracts(
    *,
    instruction_rows: tuple[ProgramImplInstruction, ...],
    instruction_binds_by_id: dict[UUID, ProgramImplInstructionBind],
    port_nodes_by_port_id: dict[
        UUID, tuple[ProgramConfigPortProjectionExperienceNode, ...]
    ],
    replay_bind_receipts_by_program_instruction_id: dict[
        UUID, ProgramTurnInstructionBindReceipt
    ],
    replay_bind_identity_rows_by_receipt_id: dict[
        UUID, tuple[ProgramTurnInstructionBindIdentity, ...]
    ],
    replay_node_class_identities_by_id: dict[
        UUID, ProjectionExperienceNodeClassIdentity
    ],
) -> tuple[dict[UUID, UUID], dict[UUID, ProgramTurnInstructionBindReceipt]]:
    class_instance_identity_ids_by_port_node_id: dict[UUID, UUID] = {}
    replay_bind_receipts_by_instruction_bind_id: dict[
        UUID, ProgramTurnInstructionBindReceipt
    ] = {}

    for instruction in sorted(instruction_rows, key=lambda row: int(row.sequence)):
        instruction_type = _enum_text(instruction.type).casefold()
        if instruction_type != "bind":
            continue
        if instruction.instruction_bind_id is None:
            raise ValueError(
                "ProgramImplInstruction[bind] is missing instruction_bind_id for replay decode: "
                + f"{instruction.id}"
            )
        instruction_bind = instruction_binds_by_id.get(instruction.instruction_bind_id)
        if instruction_bind is None:
            raise ValueError(
                "Program ontology replay snapshot missing ProgramImplInstructionBind: "
                + f"{instruction.instruction_bind_id}"
            )
        replay_bind_receipt = replay_bind_receipts_by_program_instruction_id.get(
            instruction.id
        )
        if replay_bind_receipt is None:
            raise ValueError(
                "Program ontology replay snapshot missing ProgramTurnInstructionBind for program instruction: "
                + f"{instruction.id}"
            )
        if replay_bind_receipt.program_impl_instruction_bind_id != instruction_bind.id:
            raise ValueError(
                "Program ontology replay snapshot bind receipt mismatch for ProgramImplInstructionBind: "
                + f"instruction_id={instruction.id} "
                + f"expected_bind_id={instruction_bind.id} "
                + f"receipt_bind_id={replay_bind_receipt.program_impl_instruction_bind_id}"
            )
        existing_bind_receipt = replay_bind_receipts_by_instruction_bind_id.get(
            instruction_bind.id
        )
        if (
            existing_bind_receipt is not None
            and existing_bind_receipt.id != replay_bind_receipt.id
        ):
            raise ValueError(
                "Program ontology replay snapshot has ambiguous bind receipts for instruction_bind_id="
                + f"{instruction_bind.id}"
            )
        replay_bind_receipts_by_instruction_bind_id[instruction_bind.id] = (
            replay_bind_receipt
        )

        port_node_rows = port_nodes_by_port_id.get(
            instruction_bind.program_config_port_id, ()
        )
        if not port_node_rows:
            raise ValueError(
                "Program ontology replay snapshot bind references ProgramConfigPort without nodes: "
                + f"{instruction_bind.program_config_port_id}"
            )
        bind_identity_rows = replay_bind_identity_rows_by_receipt_id.get(
            replay_bind_receipt.id
        )
        if bind_identity_rows is None:
            raise ValueError(
                "Program ontology replay snapshot missing bind identity rows for bind receipt: "
                + f"{replay_bind_receipt.id}"
            )
        bind_identity_by_port_node_id: dict[
            UUID, ProgramTurnInstructionBindIdentity
        ] = {}
        for bind_identity_row in bind_identity_rows:
            existing_bind_identity = bind_identity_by_port_node_id.get(
                bind_identity_row.program_config_port_projection_experience_node_id
            )
            if existing_bind_identity is not None:
                raise ValueError(
                    "Program ontology replay snapshot has duplicate bind identity rows for "
                    + "program_config_port_projection_experience_node_id="
                    + f"{bind_identity_row.program_config_port_projection_experience_node_id}"
                )
            bind_identity_by_port_node_id[
                bind_identity_row.program_config_port_projection_experience_node_id
            ] = bind_identity_row

        expected_port_node_ids = {port_node_row.id for port_node_row in port_node_rows}
        unexpected_port_node_ids = set(bind_identity_by_port_node_id).difference(
            expected_port_node_ids
        )
        if unexpected_port_node_ids:
            unexpected_ids = ", ".join(
                sorted(str(node_id) for node_id in unexpected_port_node_ids)
            )
            raise ValueError(
                "Program ontology replay snapshot has bind identity rows outside bound "
                + "ProgramConfigPort node contract: "
                + f"instruction_id={instruction.id} "
                + f"program_config_port_id={instruction_bind.program_config_port_id} "
                + f"unexpected_port_node_ids=[{unexpected_ids}]"
            )

        for port_node_row in port_node_rows:
            matched_bind_identity_row: ProgramTurnInstructionBindIdentity | None = (
                bind_identity_by_port_node_id.get(port_node_row.id)
            )
            if matched_bind_identity_row is None:
                raise ValueError(
                    "Program ontology replay snapshot missing bind identity for program port node: "
                    + f"program_config_port_projection_experience_node_id={port_node_row.id}"
                )
            node_class_identity = replay_node_class_identities_by_id.get(
                matched_bind_identity_row.projection_experience_node_class_identity_id
            )
            if node_class_identity is None:
                raise ValueError(
                    "Program ontology replay snapshot missing ProjectionExperienceNodeClassIdentity: "
                    + f"{matched_bind_identity_row.projection_experience_node_class_identity_id}"
                )
            class_instance_identity_id = node_class_identity.class_instance_identity_id
            existing_class_instance_identity_id = (
                class_instance_identity_ids_by_port_node_id.get(port_node_row.id)
            )
            if (
                existing_class_instance_identity_id is not None
                and existing_class_instance_identity_id != class_instance_identity_id
            ):
                raise ValueError(
                    "Program ontology replay snapshot has conflicting class-instance bindings for "
                    + f"program_config_port_projection_experience_node_id={port_node_row.id}: "
                    + f"existing={existing_class_instance_identity_id} "
                    + f"requested={class_instance_identity_id}"
                )
            class_instance_identity_ids_by_port_node_id[port_node_row.id] = (
                class_instance_identity_id
            )

    return (
        class_instance_identity_ids_by_port_node_id,
        replay_bind_receipts_by_instruction_bind_id,
    )


def _resolve_replay_invoke_contracts(
    *,
    instruction_rows: tuple[ProgramImplInstruction, ...],
    instruction_invokes_by_id: dict[UUID, ProgramImplInstructionInvoke],
    invoke_attributes_by_invoke_id: dict[
        UUID, tuple[ProgramImplInstructionInvokeAttributeConfig, ...]
    ],
    actor_configs_by_assoc_id: dict[UUID, ActorConfig],
    port_nodes_by_port_id: dict[
        UUID, tuple[ProgramConfigPortProjectionExperienceNode, ...]
    ],
    replay_invoke_receipts_by_program_instruction_id: dict[
        UUID, ProgramTurnInstructionInvokeReceipt
    ],
    replay_invoke_attribute_rows_by_receipt_id: dict[
        UUID, tuple[ProgramTurnInstructionInvokeAttributeConfigReceipt, ...]
    ],
    replay_program_actor_roles_by_id: dict[UUID, ProgramActorRole],
    replay_program_actors_by_id: dict[UUID, ProgramActor],
    replay_actor_config_role_configs_by_id: dict[UUID, ActorConfigRoleConfig],
    replay_node_class_identities_by_id: dict[
        UUID, ProjectionExperienceNodeClassIdentity
    ],
    replay_projection_node_identities_by_id: dict[
        UUID, ProjectionExperienceNodeIdentity
    ],
) -> tuple[
    dict[UUID, ProgramTurnInstructionInvokeReceipt],
    dict[UUID, ProgramTurnInstructionInvokeAttributeConfigReceipt],
]:
    port_nodes_by_id: dict[UUID, ProgramConfigPortProjectionExperienceNode] = {}
    for port_node_rows in port_nodes_by_port_id.values():
        for port_node_row in port_node_rows:
            port_nodes_by_id[port_node_row.id] = port_node_row

    replay_invoke_receipts_by_instruction_invoke_id: dict[
        UUID, ProgramTurnInstructionInvokeReceipt
    ] = {}
    replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id: dict[
        UUID, ProgramTurnInstructionInvokeAttributeConfigReceipt
    ] = {}
    expected_program_instruction_ids: set[UUID] = set()
    for instruction in sorted(instruction_rows, key=lambda row: int(row.sequence)):
        instruction_type = _enum_text(instruction.type).casefold()
        if instruction_type != "invoke":
            continue
        expected_program_instruction_ids.add(instruction.id)
        instruction_invoke = instruction.instruction_invoke
        if instruction_invoke is None:
            raise ValueError(
                "ProgramImplInstruction[invoke] is missing instruction_invoke for replay decode: "
                + f"{instruction.id}"
            )
        persisted_instruction_invoke = instruction_invokes_by_id.get(
            instruction_invoke.id
        )
        if persisted_instruction_invoke is None:
            raise ValueError(
                "Program ontology replay snapshot missing ProgramImplInstructionInvoke: "
                + f"{instruction_invoke.id}"
            )
        instruction_invoke = persisted_instruction_invoke
        replay_invoke_receipt = replay_invoke_receipts_by_program_instruction_id.get(
            instruction.id
        )
        if replay_invoke_receipt is None:
            raise ValueError(
                "Program ontology replay snapshot missing ProgramTurnInstructionInvoke for program instruction: "
                + f"{instruction.id}"
            )
        if (
            replay_invoke_receipt.program_impl_instruction_invoke_id
            != instruction_invoke.id
        ):
            raise ValueError(
                "Program ontology replay snapshot invoke receipt mismatch for ProgramImplInstructionInvoke: "
                + f"instruction_id={instruction.id} "
                + f"expected_invoke_id={instruction_invoke.id} "
                + f"receipt_invoke_id={replay_invoke_receipt.program_impl_instruction_invoke_id}"
            )
        existing_invoke_receipt = replay_invoke_receipts_by_instruction_invoke_id.get(
            instruction_invoke.id
        )
        if (
            existing_invoke_receipt is not None
            and existing_invoke_receipt.id != replay_invoke_receipt.id
        ):
            raise ValueError(
                "Program ontology replay snapshot has ambiguous invoke receipts for instruction_invoke_id="
                + f"{instruction_invoke.id}"
            )

        invoke_actor_config = actor_configs_by_assoc_id.get(
            instruction_invoke.program_config_actor_config_id
        )
        if invoke_actor_config is None:
            raise ValueError(
                "Program ontology replay snapshot missing ActorConfig for ProgramConfigActorConfig association: "
                + f"{instruction_invoke.program_config_actor_config_id}"
            )
        replay_program_actor_role = replay_program_actor_roles_by_id.get(
            replay_invoke_receipt.program_actor_role_id
        )
        if replay_program_actor_role is None:
            raise ValueError(
                "Program ontology replay snapshot missing ProgramActorRole for invoke receipt: "
                + f"{replay_invoke_receipt.program_actor_role_id}"
            )
        replay_program_actor = replay_program_actors_by_id.get(
            replay_program_actor_role.program_actor_id
        )
        if replay_program_actor is None:
            raise ValueError(
                "Program ontology replay snapshot missing ProgramActor for ProgramActorRole: "
                + f"{replay_program_actor_role.program_actor_id}"
            )
        if (
            replay_program_actor.program_config_actor_config_id
            != instruction_invoke.program_config_actor_config_id
        ):
            raise ValueError(
                "Program ontology replay snapshot actor alias mismatch for invoke receipt: "
                + f"instruction_invoke_id={instruction_invoke.id} "
                + "expected_program_config_actor_config_id="
                + f"{instruction_invoke.program_config_actor_config_id} "
                + "receipt_program_config_actor_config_id="
                + f"{replay_program_actor.program_config_actor_config_id}"
            )
        replay_actor_config_role_config = replay_actor_config_role_configs_by_id.get(
            replay_program_actor_role.actor_config_role_config_id
        )
        if replay_actor_config_role_config is None:
            raise ValueError(
                "Program ontology replay snapshot missing ActorConfigRoleConfig for ProgramActorRole: "
                + f"{replay_program_actor_role.actor_config_role_config_id}"
            )
        if replay_actor_config_role_config.actor_config_id != invoke_actor_config.id:
            raise ValueError(
                "Program ontology replay snapshot actor-role mismatch for invoke receipt: "
                + f"instruction_invoke_id={instruction_invoke.id} "
                + f"expected_actor_config_id={invoke_actor_config.id} "
                + f"receipt_actor_config_id={replay_actor_config_role_config.actor_config_id}"
            )

        invoke_port_node = port_nodes_by_id.get(
            instruction_invoke.program_config_port_projection_experience_node_id
        )
        if invoke_port_node is None:
            raise ValueError(
                "Program ontology replay snapshot missing ProgramConfigPortProjectionExperienceNode for invoke receipt: "
                + f"{instruction_invoke.program_config_port_projection_experience_node_id}"
            )
        resolved_node_class_identity = replay_node_class_identities_by_id.get(
            replay_invoke_receipt.projection_experience_node_class_identity_id
        )
        if resolved_node_class_identity is None:
            raise ValueError(
                "Program ontology replay snapshot missing ProjectionExperienceNodeClassIdentity for invoke receipt: "
                + f"{replay_invoke_receipt.projection_experience_node_class_identity_id}"
            )
        invoke_port_node_identity = invoke_port_node.projection_node_identity
        if invoke_port_node_identity is not None:
            if (
                resolved_node_class_identity.projection_experience_node_identity_id
                != invoke_port_node_identity.projection_experience_node_identity_id
            ):
                raise ValueError(
                    "Program ontology replay snapshot identity mismatch for fixed invoke node identity: "
                    + "invoke_node_identity_id="
                    + f"{invoke_port_node_identity.projection_experience_node_identity_id} "
                    + "resolved_identity_id="
                    + f"{resolved_node_class_identity.projection_experience_node_identity_id}"
                )
        else:
            resolved_identity = replay_projection_node_identities_by_id.get(
                resolved_node_class_identity.projection_experience_node_identity_id
            )
            if resolved_identity is None:
                raise ValueError(
                    "Program ontology replay snapshot missing ProjectionExperienceNodeIdentity for invoke receipt: "
                    + f"{resolved_node_class_identity.projection_experience_node_identity_id}"
                )
            if (
                resolved_identity.projection_experience_node_id
                != invoke_port_node.projection_experience_node_id
            ):
                raise ValueError(
                    "Program ontology replay snapshot node mismatch for dynamic invoke node resolution: "
                    + f"invoke_node_id={invoke_port_node.projection_experience_node_id} "
                    + f"resolved_identity_node_id={resolved_identity.projection_experience_node_id}"
                )

        invoke_attribute_rows = invoke_attributes_by_invoke_id.get(
            instruction_invoke.id, ()
        )
        replay_invoke_attribute_rows = replay_invoke_attribute_rows_by_receipt_id.get(
            replay_invoke_receipt.id,
            (),
        )
        replay_invoke_attribute_by_id: dict[
            UUID, ProgramTurnInstructionInvokeAttributeConfigReceipt
        ] = {}
        for replay_invoke_attribute_row in replay_invoke_attribute_rows:
            replay_invoke_attribute_id = (
                replay_invoke_attribute_row.program_impl_instruction_invoke_attribute_config_id
            )
            existing_replay_invoke_attribute = replay_invoke_attribute_by_id.get(
                replay_invoke_attribute_id
            )
            if existing_replay_invoke_attribute is not None:
                raise ValueError(
                    "Program ontology replay snapshot has duplicate invoke-argument receipts for "
                    + "program_impl_instruction_invoke_attribute_config_id="
                    + f"{replay_invoke_attribute_id}"
                )
            replay_invoke_attribute_by_id[replay_invoke_attribute_id] = (
                replay_invoke_attribute_row
            )

        expected_invoke_attribute_ids = {row.id for row in invoke_attribute_rows}
        unexpected_invoke_attribute_ids = set(replay_invoke_attribute_by_id).difference(
            expected_invoke_attribute_ids
        )
        if unexpected_invoke_attribute_ids:
            unexpected_ids = ", ".join(
                sorted(
                    str(attribute_id)
                    for attribute_id in unexpected_invoke_attribute_ids
                )
            )
            raise ValueError(
                "Program ontology replay snapshot has invoke-argument receipts outside invoke contract: "
                + f"instruction_invoke_id={instruction_invoke.id} "
                + f"unexpected_invoke_attribute_ids=[{unexpected_ids}]"
            )
        for invoke_attribute_row in invoke_attribute_rows:
            replay_invoke_attribute_row = replay_invoke_attribute_by_id.get(
                invoke_attribute_row.id
            )
            if replay_invoke_attribute_row is None:
                raise ValueError(
                    "Program ontology replay snapshot missing invoke-argument receipt for invoke contract: "
                    + f"program_impl_instruction_invoke_attribute_config_id={invoke_attribute_row.id}"
                )
            if (
                replay_invoke_attribute_row.program_impl_instruction_invoke_attribute_config_id
                != invoke_attribute_row.id
            ):
                raise ValueError(
                    "Program ontology replay snapshot invoke-argument receipt mismatch for invoke contract: "
                    + f"expected_invoke_attribute_id={invoke_attribute_row.id} "
                    + "receipt_invoke_attribute_id="
                    + f"{replay_invoke_attribute_row.program_impl_instruction_invoke_attribute_config_id}"
                )
            replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id[
                invoke_attribute_row.id
            ] = replay_invoke_attribute_row

        replay_invoke_receipts_by_instruction_invoke_id[instruction_invoke.id] = (
            replay_invoke_receipt
        )

    unexpected_program_instruction_ids = set(
        replay_invoke_receipts_by_program_instruction_id
    ).difference(expected_program_instruction_ids)
    if unexpected_program_instruction_ids:
        unexpected_ids = ", ".join(
            sorted(
                str(instruction_id)
                for instruction_id in unexpected_program_instruction_ids
            )
        )
        raise ValueError(
            "Program ontology replay snapshot has invoke receipts outside invoke instruction contract: "
            + f"unexpected_program_instruction_ids=[{unexpected_ids}]"
        )
    return (
        replay_invoke_receipts_by_instruction_invoke_id,
        replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id,
    )


def _resolve_replay_action_contracts(
    *,
    instruction_rows: tuple[ProgramImplInstruction, ...],
    replay_action_receipts_by_program_instruction_id: dict[
        UUID, ProgramTurnInstructionActionReceipt
    ],
) -> dict[UUID, ProgramTurnInstructionActionReceipt]:
    replay_action_receipts_by_instruction_intent_id: dict[
        UUID, ProgramTurnInstructionActionReceipt
    ] = {}
    expected_program_instruction_ids: set[UUID] = set()
    for instruction in sorted(instruction_rows, key=lambda row: int(row.sequence)):
        instruction_type = _enum_text(instruction.type).casefold()
        if instruction_type != "intent":
            continue
        expected_program_instruction_ids.add(instruction.id)
        instruction_intent_id = getattr(instruction, "instruction_intent_id", None)
        if instruction_intent_id is None:
            raise ValueError(
                "ProgramImplInstruction[intent] is missing instruction_intent_id for replay decode: "
                + f"{instruction.id}"
            )
        replay_action_receipt = replay_action_receipts_by_program_instruction_id.get(
            instruction.id
        )
        if replay_action_receipt is None:
            continue
        if (
            replay_action_receipt.program_impl_instruction_intent_id
            != instruction_intent_id
        ):
            raise ValueError(
                "Program ontology replay snapshot action receipt mismatch for ProgramImplInstructionIntent: "
                + f"instruction_id={instruction.id} "
                + f"expected_intent_id={instruction_intent_id} "
                + f"receipt_intent_id={replay_action_receipt.program_impl_instruction_intent_id}"
            )
        existing_action_receipt = replay_action_receipts_by_instruction_intent_id.get(
            instruction_intent_id
        )
        if (
            existing_action_receipt is not None
            and existing_action_receipt.id != replay_action_receipt.id
        ):
            raise ValueError(
                "Program ontology replay snapshot has ambiguous action receipts for instruction_intent_id="
                + f"{instruction_intent_id}"
            )
        replay_action_receipts_by_instruction_intent_id[instruction_intent_id] = (
            replay_action_receipt
        )

    unexpected_program_instruction_ids = set(
        replay_action_receipts_by_program_instruction_id
    ).difference(expected_program_instruction_ids)
    if unexpected_program_instruction_ids:
        unexpected_ids = ", ".join(
            sorted(
                str(instruction_id)
                for instruction_id in unexpected_program_instruction_ids
            )
        )
        raise ValueError(
            "Program ontology replay snapshot has action receipts outside intent instruction contract: "
            + f"unexpected_program_instruction_ids=[{unexpected_ids}]"
        )
    return replay_action_receipts_by_instruction_intent_id


async def load_program_run_bind_resolution(
    *,
    program_id: UUID,
    instruction_rows: tuple[ProgramImplInstruction, ...],
    instruction_binds_by_id: dict[UUID, ProgramImplInstructionBind],
    instruction_invokes_by_id: dict[UUID, ProgramImplInstructionInvoke],
    invoke_attributes_by_invoke_id: dict[
        UUID, tuple[ProgramImplInstructionInvokeAttributeConfig, ...]
    ],
    actor_configs_by_assoc_id: dict[UUID, ActorConfig],
    port_nodes_by_port_id: dict[
        UUID, tuple[ProgramConfigPortProjectionExperienceNode, ...]
    ],
    lane_reader: ProgramLaneMaterializedReader | None = None,
) -> ProgramRunBindResolution:
    (
        replay_bind_receipts_by_program_instruction_id,
        replay_bind_identity_rows_by_receipt_id,
        replay_action_receipts_by_program_instruction_id,
        replay_invoke_receipts_by_program_instruction_id,
        replay_invoke_attribute_rows_by_receipt_id,
        replay_node_class_identities_by_id,
        replay_projection_node_identities_by_id,
        replay_views_by_bind_receipt_id,
        replay_program_actor_roles_by_id,
        replay_program_actors_by_id,
        replay_actor_config_role_configs_by_id,
    ) = await _load_replay_receipts_for_program(
        program_id=program_id,
        lane_reader=lane_reader,
    )
    (
        class_instance_identity_ids_by_port_node_id,
        replay_bind_receipts_by_instruction_bind_id,
    ) = _resolve_replay_bind_contracts(
        instruction_rows=instruction_rows,
        instruction_binds_by_id=instruction_binds_by_id,
        port_nodes_by_port_id=port_nodes_by_port_id,
        replay_bind_receipts_by_program_instruction_id=replay_bind_receipts_by_program_instruction_id,
        replay_bind_identity_rows_by_receipt_id=replay_bind_identity_rows_by_receipt_id,
        replay_node_class_identities_by_id=replay_node_class_identities_by_id,
    )
    replay_action_receipts_by_instruction_intent_id = _resolve_replay_action_contracts(
        instruction_rows=instruction_rows,
        replay_action_receipts_by_program_instruction_id=replay_action_receipts_by_program_instruction_id,
    )
    (
        replay_invoke_receipts_by_instruction_invoke_id,
        replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id,
    ) = _resolve_replay_invoke_contracts(
        instruction_rows=instruction_rows,
        instruction_invokes_by_id=instruction_invokes_by_id,
        invoke_attributes_by_invoke_id=invoke_attributes_by_invoke_id,
        actor_configs_by_assoc_id=actor_configs_by_assoc_id,
        port_nodes_by_port_id=port_nodes_by_port_id,
        replay_invoke_receipts_by_program_instruction_id=replay_invoke_receipts_by_program_instruction_id,
        replay_invoke_attribute_rows_by_receipt_id=replay_invoke_attribute_rows_by_receipt_id,
        replay_program_actor_roles_by_id=replay_program_actor_roles_by_id,
        replay_program_actors_by_id=replay_program_actors_by_id,
        replay_actor_config_role_configs_by_id=replay_actor_config_role_configs_by_id,
        replay_node_class_identities_by_id=replay_node_class_identities_by_id,
        replay_projection_node_identities_by_id=replay_projection_node_identities_by_id,
    )
    return ProgramRunBindResolution(
        class_instance_identity_ids_by_port_node_id=class_instance_identity_ids_by_port_node_id,
        replay_bind_receipts_by_instruction_bind_id=replay_bind_receipts_by_instruction_bind_id,
        replay_views_by_bind_receipt_id=replay_views_by_bind_receipt_id,
        replay_action_receipts_by_instruction_intent_id=replay_action_receipts_by_instruction_intent_id,
        replay_invoke_receipts_by_instruction_invoke_id=replay_invoke_receipts_by_instruction_invoke_id,
        replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id=(
            replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id
        ),
    )


__all__ = ["ProgramRunBindResolution", "load_program_run_bind_resolution"]
