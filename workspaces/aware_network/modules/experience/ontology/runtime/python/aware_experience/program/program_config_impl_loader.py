from __future__ import annotations

from typing import TypeVar
from uuid import UUID

from aware_orm.filters import EqFilter
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.current_session_ctx import current_session

from aware_experience.program.lane_materialized_reader import (
    ProgramLaneMaterializedReader,
)
from aware_experience.program.snapshot_contract import ProgramOntologySnapshot

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
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig


TModel = TypeVar("TModel", bound=BaseORMModel)


def _filter_column_candidates(column: str) -> tuple[str, ...]:
    normalized = (column or "").strip()
    if normalized == "config_id":
        return ("config_id", "program_config_id")
    return (normalized,)


def _matches_filter(*, obj: BaseORMModel, filter_item: object) -> bool:
    if not isinstance(filter_item, EqFilter):
        return False
    for column in _filter_column_candidates(filter_item.column):
        if not column:
            continue
        if not hasattr(obj, column):
            continue
        value = getattr(obj, column)
        return str(value) == str(filter_item.value)
    return False


def _cached_list(
    cls: type[TModel], *, filters: list[object] | None = None
) -> list[TModel]:
    session = current_session()
    if session is None:
        return []
    candidates = [obj for obj in session.imap_all_objects() if isinstance(obj, cls)]
    if not filters:
        return candidates
    return [
        obj
        for obj in candidates
        if all(
            _matches_filter(obj=obj, filter_item=filter_item) for filter_item in filters
        )
    ]


async def _get_by_id(cls: type[TModel], obj_id: UUID) -> TModel | None:
    session = current_session()
    if session is not None:
        cached = session.imap_get(cls, obj_id)
        if cached is not None:
            return cached
    return await cls.by_id(obj_id, cache_valid=True)


async def _get_list(
    cls: type[TModel],
    *,
    filters: list[object] | None = None,
    limit: int = 1024,
) -> list[TModel]:
    cached = _cached_list(cls, filters=filters)
    if cached:
        return cached[:limit]
    query = cls.query(cache_valid=True)
    if filters:
        query = query.where(*filters)
    return await query.limit(limit).all()


async def _get_instruction_payload(
    *,
    instruction: ProgramImplInstruction,
    relationship_name: str,
    id_field_name: str,
    cls: type[TModel],
) -> TModel | None:
    related = getattr(instruction, relationship_name, None)
    if isinstance(related, cls):
        return related
    payload_id = getattr(instruction, id_field_name, None)
    if not isinstance(payload_id, UUID):
        return None
    return await _get_by_id(cls, payload_id)


def _select_program_impl(
    *,
    program_impls: list[ProgramImpl],
    preferred_key: str | None,
) -> ProgramImpl:
    if preferred_key:
        preferred_matches = [
            item for item in program_impls if (item.key or "").strip() == preferred_key
        ]
        if len(preferred_matches) == 1:
            return preferred_matches[0]
        if len(preferred_matches) > 1:
            raise ValueError(
                "Ambiguous ProgramImpl for preferred key "
                + f"{preferred_key!r} (matches={len(preferred_matches)})"
            )
    if len(program_impls) == 1:
        return program_impls[0]
    available = sorted((item.key or "").strip() for item in program_impls)
    raise ValueError(
        "Ambiguous ProgramImpl for ProgramConfig; provide explicit program_ref key "
        + f"(available_impl_keys={available})"
    )


async def load_program_config_impl_snapshot(
    *,
    program_config_id: UUID,
    preferred_program_impl_key: str | None,
    lane_reader: ProgramLaneMaterializedReader | None = None,
) -> ProgramOntologySnapshot:
    """
    Load ProgramConfig + ProgramImpl snapshot only.

    Contract:
    - Uses current lane/session context.
    - Does not resolve runtime Program turn receipts.
    - Does not resolve environment graph class-instance bindings.
    """

    program_config = await _get_by_id(ProgramConfig, program_config_id)
    if program_config is None:
        raise ValueError(
            f"ProgramConfig not found in active branch: {program_config_id}"
        )

    program_impls = await _get_list(
        ProgramImpl,
        filters=[EqFilter(column="config_id", value=str(program_config_id))],
        limit=1024,
    )
    if not program_impls:
        raise ValueError(
            "No ProgramImpl found for ProgramConfig "
            + f"{program_config_id} in active branch"
        )
    program_impl = _select_program_impl(
        program_impls=program_impls,
        preferred_key=preferred_program_impl_key,
    )
    actor_rows = await _get_list(
        ProgramConfigActorConfig,
        filters=[EqFilter(column="program_config_id", value=str(program_config_id))],
        limit=1024,
    )
    port_rows = await _get_list(
        ProgramConfigPort,
        filters=[EqFilter(column="program_config_id", value=str(program_config_id))],
        limit=1024,
    )
    if lane_reader is not None:
        projection_ids = {row.projection_id for row in port_rows}
        await lane_reader.ensure_projection_lanes_materialized_by_ids(
            projection_ids=projection_ids,
        )
    input_config_rows = await _get_list(
        ProgramConfigInputConfig,
        filters=[EqFilter(column="program_config_id", value=str(program_config_id))],
        limit=1024,
    )
    instruction_rows = await _get_list(
        ProgramImplInstruction,
        filters=[EqFilter(column="program_impl_id", value=str(program_impl.id))],
        limit=8192,
    )

    actor_configs_by_assoc_id: dict[UUID, ActorConfig] = {}
    for actor_row in actor_rows:
        actor_config = await _get_by_id(ActorConfig, actor_row.actor_config_id)
        if actor_config is None:
            raise ValueError(
                "ProgramConfigActorConfig references missing ActorConfig: "
                + f"{actor_row.actor_config_id}"
            )
        actor_configs_by_assoc_id[actor_row.id] = actor_config

    projections_by_port_id: dict[UUID, ProjectionExperience] = {}
    port_nodes_by_port_id: dict[
        UUID, tuple[ProgramConfigPortProjectionExperienceNode, ...]
    ] = {}
    projection_node_ids: set[UUID] = set()
    projection_node_identity_assoc_ids: set[UUID] = set()
    for port_row in port_rows:
        projection = await _get_by_id(ProjectionExperience, port_row.projection_id)
        if projection is None:
            raise ValueError(
                "ProgramConfigPort references missing ProjectionExperience: "
                + f"{port_row.projection_id}"
            )
        projections_by_port_id[port_row.id] = projection
        port_node_rows = await _get_list(
            ProgramConfigPortProjectionExperienceNode,
            filters=[EqFilter(column="program_config_port_id", value=str(port_row.id))],
            limit=1024,
        )
        port_nodes_by_port_id[port_row.id] = tuple(port_node_rows)
        for port_node_row in port_node_rows:
            projection_node_ids.add(port_node_row.projection_experience_node_id)
            if port_node_row.projection_node_identity_id is not None:
                projection_node_identity_assoc_ids.add(
                    port_node_row.projection_node_identity_id
                )

    projection_nodes_by_id: dict[UUID, ProjectionExperienceNode] = {}
    for projection_node_id in sorted(projection_node_ids, key=str):
        projection_node = await _get_by_id(ProjectionExperienceNode, projection_node_id)
        if projection_node is None:
            raise ValueError(
                "ProgramConfigPortProjectionExperienceNode references missing ProjectionExperienceNode: "
                + f"{projection_node_id}"
            )
        projection_nodes_by_id[projection_node_id] = projection_node

    projection_node_identity_assocs_by_id: dict[
        UUID,
        ProgramConfigPortProjectionExperienceNodeIdentity,
    ] = {}
    projection_node_identity_ids: set[UUID] = set()
    for assoc_id in sorted(projection_node_identity_assoc_ids, key=str):
        identity_assoc = await _get_by_id(
            ProgramConfigPortProjectionExperienceNodeIdentity,
            assoc_id,
        )
        if identity_assoc is None:
            raise ValueError(
                "ProgramConfigPortProjectionExperienceNode references missing identity association: "
                + f"{assoc_id}"
            )
        projection_node_identity_assocs_by_id[assoc_id] = identity_assoc
        projection_node_identity_ids.add(
            identity_assoc.projection_experience_node_identity_id
        )

    projection_node_identities_by_id: dict[UUID, ProjectionExperienceNodeIdentity] = {}
    for projection_node_identity_id in sorted(projection_node_identity_ids, key=str):
        projection_node_identity = await _get_by_id(
            ProjectionExperienceNodeIdentity,
            projection_node_identity_id,
        )
        if projection_node_identity is None:
            raise ValueError(
                "ProgramConfigPortProjectionExperienceNodeIdentity references missing "
                + "ProjectionExperienceNodeIdentity: "
                + f"{projection_node_identity_id}"
            )
        projection_node_identities_by_id[projection_node_identity_id] = (
            projection_node_identity
        )

    instruction_inputs_by_id: dict[UUID, ProgramImplInstructionInput] = {}
    instruction_lets_by_id: dict[UUID, ProgramImplInstructionLet] = {}
    instruction_binds_by_id: dict[UUID, ProgramImplInstructionBind] = {}
    instruction_invokes_by_id: dict[UUID, ProgramImplInstructionInvoke] = {}
    instruction_expects_by_id: dict[UUID, ProgramImplInstructionExpect] = {}
    instruction_intents_by_id: dict[UUID, ProgramImplInstructionIntent] = {}
    activation_field_bindings_by_intent_id: dict[
        UUID, tuple[ProgramImplInstructionIntentActivationFieldBinding, ...]
    ] = {}
    outcome_field_bindings_by_intent_id: dict[
        UUID, tuple[ProgramImplInstructionIntentOutcomeFieldBinding, ...]
    ] = {}
    receipt_field_bindings_by_intent_id: dict[
        UUID, tuple[ProgramImplInstructionIntentReceiptFieldBinding, ...]
    ] = {}
    invoke_attributes_by_invoke_id: dict[
        UUID, tuple[ProgramImplInstructionInvokeAttributeConfig, ...]
    ] = {}
    attribute_config_ids: set[UUID] = set()

    for instruction in instruction_rows:
        instruction_input = await _get_instruction_payload(
            instruction=instruction,
            relationship_name="instruction_input",
            id_field_name="instruction_input_id",
            cls=ProgramImplInstructionInput,
        )
        if instruction_input is not None:
            instruction_inputs_by_id[instruction_input.id] = instruction_input
        instruction_let = await _get_instruction_payload(
            instruction=instruction,
            relationship_name="instruction_let",
            id_field_name="instruction_let_id",
            cls=ProgramImplInstructionLet,
        )
        if instruction_let is not None:
            instruction_lets_by_id[instruction_let.id] = instruction_let
        instruction_bind = await _get_instruction_payload(
            instruction=instruction,
            relationship_name="instruction_bind",
            id_field_name="instruction_bind_id",
            cls=ProgramImplInstructionBind,
        )
        if instruction_bind is not None:
            instruction_binds_by_id[instruction_bind.id] = instruction_bind
        instruction_invoke = await _get_instruction_payload(
            instruction=instruction,
            relationship_name="instruction_invoke",
            id_field_name="instruction_invoke_id",
            cls=ProgramImplInstructionInvoke,
        )
        if instruction_invoke is not None:
            instruction_invokes_by_id[instruction_invoke.id] = instruction_invoke
            invoke_attribute_rows = await _get_list(
                ProgramImplInstructionInvokeAttributeConfig,
                filters=[
                    EqFilter(
                        column="program_impl_instruction_invoke_id",
                        value=str(instruction_invoke.id),
                    )
                ],
                limit=1024,
            )
            invoke_attributes_by_invoke_id[instruction_invoke.id] = tuple(
                invoke_attribute_rows
            )
            for invoke_attribute_row in invoke_attribute_rows:
                attribute_config_ids.add(invoke_attribute_row.attribute_config_id)
        instruction_expect = await _get_instruction_payload(
            instruction=instruction,
            relationship_name="instruction_expect",
            id_field_name="instruction_expect_id",
            cls=ProgramImplInstructionExpect,
        )
        if instruction_expect is not None:
            instruction_expects_by_id[instruction_expect.id] = instruction_expect
        instruction_intent = await _get_instruction_payload(
            instruction=instruction,
            relationship_name="instruction_intent",
            id_field_name="instruction_intent_id",
            cls=ProgramImplInstructionIntent,
        )
        if instruction_intent is not None:
            instruction_intents_by_id[instruction_intent.id] = instruction_intent
            activation_field_bindings_by_intent_id[instruction_intent.id] = tuple(
                await _get_list(
                    ProgramImplInstructionIntentActivationFieldBinding,
                    filters=[
                        EqFilter(
                            column="program_impl_instruction_intent_id",
                            value=str(instruction_intent.id),
                        )
                    ],
                    limit=1024,
                )
            )
            outcome_field_bindings_by_intent_id[instruction_intent.id] = tuple(
                await _get_list(
                    ProgramImplInstructionIntentOutcomeFieldBinding,
                    filters=[
                        EqFilter(
                            column="program_impl_instruction_intent_id",
                            value=str(instruction_intent.id),
                        )
                    ],
                    limit=1024,
                )
            )
            receipt_field_bindings_by_intent_id[instruction_intent.id] = tuple(
                await _get_list(
                    ProgramImplInstructionIntentReceiptFieldBinding,
                    filters=[
                        EqFilter(
                            column="program_impl_instruction_intent_id",
                            value=str(instruction_intent.id),
                        )
                    ],
                    limit=1024,
                )
            )

    attribute_name_by_id: dict[UUID, str] = {}
    for attribute_config_id in sorted(attribute_config_ids, key=str):
        attribute_config = await _get_by_id(AttributeConfig, attribute_config_id)
        if attribute_config is None:
            raise ValueError(
                "ProgramImplInstructionInvokeAttributeConfig references missing AttributeConfig: "
                + f"{attribute_config_id}"
            )
        attribute_name = (attribute_config.name or "").strip()
        if not attribute_name:
            raise ValueError(
                "AttributeConfig.name cannot be empty for invoke attribute config "
                + f"{attribute_config_id}"
            )
        attribute_name_by_id[attribute_config_id] = attribute_name

    return ProgramOntologySnapshot(
        program_config=program_config,
        program_impl=program_impl,
        actor_rows=tuple(actor_rows),
        port_rows=tuple(port_rows),
        input_config_rows=tuple(input_config_rows),
        instruction_rows=tuple(instruction_rows),
        actor_configs_by_assoc_id=actor_configs_by_assoc_id,
        projections_by_port_id=projections_by_port_id,
        port_nodes_by_port_id=port_nodes_by_port_id,
        projection_nodes_by_id=projection_nodes_by_id,
        projection_node_identity_assocs_by_id=projection_node_identity_assocs_by_id,
        projection_node_identities_by_id=projection_node_identities_by_id,
        class_instance_identity_ids_by_port_node_id={},
        instruction_inputs_by_id=instruction_inputs_by_id,
        instruction_lets_by_id=instruction_lets_by_id,
        instruction_binds_by_id=instruction_binds_by_id,
        instruction_invokes_by_id=instruction_invokes_by_id,
        instruction_expects_by_id=instruction_expects_by_id,
        instruction_intents_by_id=instruction_intents_by_id,
        activation_field_bindings_by_intent_id=(activation_field_bindings_by_intent_id),
        outcome_field_bindings_by_intent_id=outcome_field_bindings_by_intent_id,
        receipt_field_bindings_by_intent_id=receipt_field_bindings_by_intent_id,
        invoke_attributes_by_invoke_id=invoke_attributes_by_invoke_id,
        attribute_name_by_id=attribute_name_by_id,
    )


__all__ = ["load_program_config_impl_snapshot"]
