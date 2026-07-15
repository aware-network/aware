from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from uuid import UUID

from aware_identity_ontology.actor.actor_config import ActorConfig
from aware_experience_ontology.program.impl.program_impl import ProgramImpl
from aware_experience_ontology.program.impl.program_impl_instruction import (
    ProgramImplInstruction,
)
from aware_experience_ontology.program.impl.program_impl_instruction_bind import (
    ProgramImplInstructionBind,
)
from aware_experience_ontology.program.impl.program_impl_instruction_expect import (
    ProgramImplInstructionExpect,
)
from aware_experience_ontology.program.impl.program_impl_instruction_input import (
    ProgramImplInstructionInput,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent import (
    ProgramImplInstructionIntent,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent_activation_field_binding import (
    ProgramImplInstructionIntentActivationFieldBinding,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent_outcome_field_binding import (
    ProgramImplInstructionIntentOutcomeFieldBinding,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent_receipt_field_binding import (
    ProgramImplInstructionIntentReceiptFieldBinding,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke import (
    ProgramImplInstructionInvoke,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke_attribute_config import (
    ProgramImplInstructionInvokeAttributeConfig,
)
from aware_experience_ontology.program.impl.program_impl_instruction_let import (
    ProgramImplInstructionLet,
)
from aware_experience_ontology.program.program_config import ProgramConfig
from aware_experience_ontology.program.program_config_actor_config import (
    ProgramConfigActorConfig,
)
from aware_experience_ontology.program.program_config_input_config import (
    ProgramConfigInputConfig,
)
from aware_experience_ontology.program.program_config_port import ProgramConfigPort
from aware_experience_ontology.program.program_config_port_projection_experience_node import (
    ProgramConfigPortProjectionExperienceNode,
)
from aware_experience_ontology.program.program_config_port_projection_experience_node_identity import (
    ProgramConfigPortProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_node import (
    ProjectionExperienceNode,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.program.program_turn_instruction_bind import (
    ProgramTurnInstructionBind,
)
from aware_experience_ontology.program.program_turn_instruction_action import (
    ProgramTurnInstructionAction,
)
from aware_experience_ontology.program.program_turn_instruction_invoke import (
    ProgramTurnInstructionInvoke,
)
from aware_experience_ontology.program.program_turn_instruction_invoke_attribute_config import (
    ProgramTurnInstructionInvokeAttributeConfig,
)


def _empty_replay_bind_receipts() -> dict[UUID, ProgramTurnInstructionBind]:
    return {}


def _empty_replay_bind_views() -> dict[UUID, ProjectionExperienceView]:
    return {}


def _empty_replay_invoke_receipts() -> dict[UUID, ProgramTurnInstructionInvoke]:
    return {}


def _empty_replay_action_receipts() -> dict[UUID, ProgramTurnInstructionAction]:
    return {}


def _empty_replay_invoke_attribute_receipts() -> (
    dict[UUID, ProgramTurnInstructionInvokeAttributeConfig]
):
    return {}


@dataclass(frozen=True, slots=True)
class ProgramOntologySnapshot:
    """
    Typed runtime snapshot for ontology-backed program decode.

    Contract:
    - Snapshot is materialized from one branch and one ProgramConfig id.
    - Runtime decode consumes this typed shape instead of issuing ad-hoc queries
      directly in decode steps.
    """

    program_config: ProgramConfig
    program_impl: ProgramImpl
    actor_rows: tuple[ProgramConfigActorConfig, ...]
    port_rows: tuple[ProgramConfigPort, ...]
    input_config_rows: tuple[ProgramConfigInputConfig, ...]
    instruction_rows: tuple[ProgramImplInstruction, ...]
    actor_configs_by_assoc_id: Mapping[UUID, ActorConfig]
    projections_by_port_id: Mapping[UUID, ProjectionExperience]
    port_nodes_by_port_id: Mapping[
        UUID, tuple[ProgramConfigPortProjectionExperienceNode, ...]
    ]
    projection_nodes_by_id: Mapping[UUID, ProjectionExperienceNode]
    projection_node_identity_assocs_by_id: Mapping[
        UUID, ProgramConfigPortProjectionExperienceNodeIdentity
    ]
    projection_node_identities_by_id: Mapping[UUID, ProjectionExperienceNodeIdentity]
    class_instance_identity_ids_by_port_node_id: Mapping[UUID, UUID]
    instruction_inputs_by_id: Mapping[UUID, ProgramImplInstructionInput]
    instruction_lets_by_id: Mapping[UUID, ProgramImplInstructionLet]
    instruction_binds_by_id: Mapping[UUID, ProgramImplInstructionBind]
    instruction_invokes_by_id: Mapping[UUID, ProgramImplInstructionInvoke]
    instruction_expects_by_id: Mapping[UUID, ProgramImplInstructionExpect]
    instruction_intents_by_id: Mapping[UUID, ProgramImplInstructionIntent]
    activation_field_bindings_by_intent_id: Mapping[
        UUID, tuple[ProgramImplInstructionIntentActivationFieldBinding, ...]
    ]
    outcome_field_bindings_by_intent_id: Mapping[
        UUID, tuple[ProgramImplInstructionIntentOutcomeFieldBinding, ...]
    ]
    receipt_field_bindings_by_intent_id: Mapping[
        UUID, tuple[ProgramImplInstructionIntentReceiptFieldBinding, ...]
    ]
    invoke_attributes_by_invoke_id: Mapping[
        UUID,
        tuple[ProgramImplInstructionInvokeAttributeConfig, ...],
    ]
    attribute_name_by_id: Mapping[UUID, str]
    replay_bind_receipts_by_instruction_bind_id: Mapping[
        UUID, ProgramTurnInstructionBind
    ] = field(default_factory=_empty_replay_bind_receipts)
    replay_views_by_bind_receipt_id: Mapping[UUID, ProjectionExperienceView] = field(
        default_factory=_empty_replay_bind_views
    )
    replay_action_receipts_by_instruction_intent_id: Mapping[
        UUID, ProgramTurnInstructionAction
    ] = field(default_factory=_empty_replay_action_receipts)
    replay_invoke_receipts_by_instruction_invoke_id: Mapping[
        UUID, ProgramTurnInstructionInvoke
    ] = field(default_factory=_empty_replay_invoke_receipts)
    replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id: Mapping[
        UUID, ProgramTurnInstructionInvokeAttributeConfig
    ] = field(default_factory=_empty_replay_invoke_attribute_receipts)


__all__ = ["ProgramOntologySnapshot"]
