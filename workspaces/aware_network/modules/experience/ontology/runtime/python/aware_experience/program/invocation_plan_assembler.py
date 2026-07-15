from __future__ import annotations

from enum import Enum
from typing import cast
from uuid import UUID

from aware_experience.program.language import (
    InvocationPlan,
    PlanActionContinuationActivationFieldBinding,
    PlanActionContinuationBinding,
    PlanActionContinuationOutcomeFieldBinding,
    PlanActionContinuationReceiptFieldBinding,
    PlanActorContract,
    PlanCall,
    PlanCallArg,
    PlanExpectEventConfig,
    PlanExpr,
    PlanInput,
    PlanIntentActionConfig,
    PlanInvoke,
    PlanLet,
    PlanLocalRef,
    PlanPortContract,
    PlanPortProjectionNodeContract,
    PlanPortProjectionNodeKey,
    PlanSymbolRef,
)
from aware_experience.program.snapshot_contract import ProgramOntologySnapshot

from aware_experience_ontology.program.impl.program_impl_instruction_enums import (
    ProgramImplInvokeTargetKind,
)
from aware_experience_ontology.program.program_config_input_config import (
    ProgramConfigInputConfig,
)


def _enum_text(value: object) -> str:
    if isinstance(value, Enum):
        enum_value = cast(object, value.value)
        return str(enum_value or "").strip()
    return str(value or "").strip()


def _instruction_payload_id(
    *,
    instruction: object,
    relationship_name: str,
    id_field_name: str,
) -> UUID | None:
    related = getattr(instruction, relationship_name, None)
    related_id = getattr(related, "id", None)
    if isinstance(related_id, UUID):
        return related_id
    payload_id = getattr(instruction, id_field_name, None)
    if isinstance(payload_id, UUID):
        return payload_id
    return None


def _decode_expr_payload(*, payload: object, known_symbols: set[str]) -> PlanExpr:
    if payload is None or isinstance(payload, (str, int, float, bool)):
        return cast(PlanExpr, payload)
    if isinstance(payload, list):
        payload_items = cast(list[object], payload)
        return cast(
            PlanExpr,
            [
                _decode_expr_payload(payload=item, known_symbols=known_symbols)
                for item in payload_items
            ],
        )
    if not isinstance(payload, dict):
        raise ValueError(
            "Invalid plan expression payload type from ontology: "
            + f"{type(payload).__name__}"
        )

    expr_payload = cast(dict[str, object], payload)
    expr_tag = str(expr_payload.get("$expr") or "").strip()
    if expr_tag == "local_ref":
        name = str(expr_payload.get("name") or "").strip()
        if not name:
            raise ValueError("Invalid local_ref expression payload: missing name")
        return PlanLocalRef(name=name)
    if expr_tag == "symbol_ref":
        name = str(expr_payload.get("name") or "").strip()
        if not name:
            raise ValueError("Invalid symbol_ref expression payload: missing name")
        return PlanSymbolRef(name=name)
    if expr_tag == "literal":
        return cast(PlanExpr, expr_payload.get("value"))
    if expr_tag == "call":
        return _decode_call_payload(payload=expr_payload, known_symbols=known_symbols)

    if "target" in expr_payload and "args" in expr_payload:
        return _decode_call_payload(payload=expr_payload, known_symbols=known_symbols)

    if set(expr_payload.keys()) == {"name"}:
        name = str(expr_payload.get("name") or "").strip()
        if not name:
            raise ValueError("Invalid legacy ref payload: missing name")
        if name in known_symbols or "." in name:
            return PlanSymbolRef(name=name)
        return PlanLocalRef(name=name)

    normalized: dict[str, object] = {}
    for key, value in expr_payload.items():
        normalized[str(key)] = _decode_expr_payload(
            payload=value, known_symbols=known_symbols
        )
    return cast(PlanExpr, normalized)


def _decode_call_payload(
    *,
    payload: dict[str, object],
    known_symbols: set[str],
) -> PlanCall:
    target = str(payload.get("target") or "").strip()
    if not target:
        raise ValueError("Invalid call payload: target is required")
    raw_args_obj = payload.get("args")
    if raw_args_obj is None:
        raw_args: list[object] = []
    else:
        if not isinstance(raw_args_obj, list):
            raise ValueError("Invalid call payload: args must be a list")
        raw_args = cast(list[object], raw_args_obj)
    args: list[PlanCallArg] = []
    for item in raw_args:
        if not isinstance(item, dict):
            raise ValueError("Invalid call payload arg: expected object")
        item_payload = cast(dict[str, object], item)
        raw_name = item_payload.get("name")
        arg_name: str | None
        if raw_name is None:
            arg_name = None
        else:
            candidate_name = str(raw_name).strip()
            arg_name = candidate_name or None
        if "value" not in item_payload:
            raise ValueError("Invalid call payload arg: missing value")
        args.append(
            PlanCallArg(
                name=arg_name,
                value=_decode_expr_payload(
                    payload=item_payload["value"], known_symbols=known_symbols
                ),
            )
        )
    object_expr_raw = payload.get("object_expr")
    object_expr: PlanExpr | None = None
    if object_expr_raw is not None:
        object_expr = _decode_expr_payload(
            payload=object_expr_raw, known_symbols=known_symbols
        )
    return PlanCall(
        target=target,
        args=tuple(args),
        object_expr=object_expr,
    )


def _is_construct_target(value: object) -> bool:
    if isinstance(value, ProgramImplInvokeTargetKind):
        return value == ProgramImplInvokeTargetKind.construct
    return _enum_text(value).casefold() == ProgramImplInvokeTargetKind.construct.value


def _resolve_invoke_target(
    *,
    function_config_id: UUID,
    function_targets: dict[UUID, str],
) -> str:
    target = function_targets.get(function_config_id)
    if target is not None:
        return target
    raise ValueError(
        "Unresolved FunctionConfig target for invoke: "
        + f"{function_config_id}. Ensure OCG class/function links are materialized."
    )


def assemble_invocation_plan_from_snapshot(
    *,
    snapshot: ProgramOntologySnapshot,
    function_targets: dict[UUID, str],
    program_id: UUID | None,
) -> InvocationPlan:
    program_config = snapshot.program_config
    program_impl = snapshot.program_impl
    actor_rows = snapshot.actor_rows
    actor_configs_by_assoc_id = snapshot.actor_configs_by_assoc_id

    actor_alias_by_assoc_id: dict[UUID, str] = {}
    actor_contracts: list[PlanActorContract] = []
    for actor_row in sorted(actor_rows, key=lambda row: (row.alias or "").strip()):
        actor_config = actor_configs_by_assoc_id.get(actor_row.id)
        if actor_config is None:
            raise ValueError(
                f"Program ontology snapshot missing ActorConfig for {actor_row.id}"
            )
        actor_alias = (actor_row.alias or "").strip()
        if not actor_alias:
            raise ValueError("ProgramConfigActorConfig.alias cannot be empty")
        actor_alias_by_assoc_id[actor_row.id] = actor_alias
        actor_contracts.append(
            PlanActorContract(
                key=actor_alias,
                actor=(actor_config.key or "").strip() or str(actor_config.id),
            )
        )

    port_rows = snapshot.port_rows
    class_instance_identity_ids_by_port_node_id = (
        snapshot.class_instance_identity_ids_by_port_node_id
    )
    projections_by_port_id = snapshot.projections_by_port_id
    port_nodes_by_port_id = snapshot.port_nodes_by_port_id
    projection_nodes_by_id = snapshot.projection_nodes_by_id
    projection_node_identity_assocs_by_id = (
        snapshot.projection_node_identity_assocs_by_id
    )
    projection_node_identities_by_id = snapshot.projection_node_identities_by_id
    port_key_by_id: dict[UUID, str] = {}
    port_node_alias_by_id: dict[UUID, str] = {}
    known_symbols: set[str] = set()
    port_contracts: list[PlanPortContract] = []
    for port_row in sorted(port_rows, key=lambda row: (row.key or "").strip()):
        port_key = (port_row.key or "").strip()
        if not port_key:
            raise ValueError("ProgramConfigPort.key cannot be empty")
        projection = projections_by_port_id.get(port_row.id)
        if projection is None:
            raise ValueError(
                f"Program ontology snapshot missing ProjectionExperience for {port_row.id}"
            )
        projection_name = (projection.name or "").strip()
        if not projection_name:
            raise ValueError(
                "ProjectionExperience.name cannot be empty for ProgramConfigPort "
                + f"{port_key!r}"
            )

        port_node_rows = port_nodes_by_port_id.get(port_row.id, ())
        if not port_node_rows:
            raise ValueError(f"ProgramConfigPort {port_key!r} has no projection nodes")

        projection_nodes: list[PlanPortProjectionNodeContract] = []
        for port_node_row in sorted(
            port_node_rows, key=lambda row: (row.key or "").strip()
        ):
            node_alias = (port_node_row.key or "").strip()
            if not node_alias:
                raise ValueError(
                    "ProgramConfigPortProjectionExperienceNode.key cannot be empty"
                )
            projection_node = projection_nodes_by_id.get(
                port_node_row.projection_experience_node_id
            )
            if projection_node is None:
                raise ValueError(
                    "ProgramConfigPortProjectionExperienceNode references missing "
                    + f"ProjectionExperienceNode: {port_node_row.projection_experience_node_id}"
                )
            projection_node_key = (projection_node.key or "").strip()
            if not projection_node_key:
                raise ValueError(
                    "ProjectionExperienceNode.key cannot be empty for port node alias "
                    + f"{node_alias!r}"
                )

            node_ref = projection_node_key
            if port_node_row.projection_node_identity_id is not None:
                identity_assoc = projection_node_identity_assocs_by_id.get(
                    port_node_row.projection_node_identity_id
                )
                if identity_assoc is None:
                    raise ValueError(
                        "ProgramConfigPortProjectionExperienceNode references missing identity association: "
                        + f"{port_node_row.projection_node_identity_id}"
                    )
                projection_identity = projection_node_identities_by_id.get(
                    identity_assoc.projection_experience_node_identity_id
                )
                if projection_identity is None:
                    raise ValueError(
                        "ProgramConfigPortProjectionExperienceNodeIdentity references missing "
                        + "ProjectionExperienceNodeIdentity: "
                        + f"{identity_assoc.projection_experience_node_identity_id}"
                    )
                identity_key = (projection_identity.key or "").strip()
                if not identity_key:
                    raise ValueError(
                        "ProjectionExperienceNodeIdentity.key cannot be empty for node alias "
                        + f"{node_alias!r}"
                    )
                node_ref = f"{projection_node_key}.{identity_key}"

            class_instance_identity_id = (
                class_instance_identity_ids_by_port_node_id.get(port_node_row.id)
            )
            if class_instance_identity_id is None:
                raise ValueError(
                    "Program ontology decode missing class-instance binding for program port node: "
                    + f"port={port_key!r} node_alias={node_alias!r} "
                    + f"program_config_port_projection_experience_node_id={port_node_row.id}"
                )

            port_node_alias_by_id[port_node_row.id] = node_alias
            known_symbols.add(node_alias)
            projection_nodes.append(
                PlanPortProjectionNodeContract(
                    key=node_alias,
                    node=node_ref,
                    keys=(
                        PlanPortProjectionNodeKey(
                            name="class_instance_identity_id",
                            value_expr=str(class_instance_identity_id),
                        ),
                    ),
                )
            )

        known_symbols.add(f"program.port.{port_key}")
        port_key_by_id[port_row.id] = port_key
        port_contracts.append(
            PlanPortContract(
                key=port_key,
                projection=projection_name,
                projection_nodes=tuple(projection_nodes),
                intent=(port_row.intent or "").strip() or None,
            )
        )

    input_config_rows = snapshot.input_config_rows
    instruction_inputs_by_id = snapshot.instruction_inputs_by_id
    instruction_lets_by_id = snapshot.instruction_lets_by_id
    instruction_binds_by_id = snapshot.instruction_binds_by_id
    instruction_invokes_by_id = snapshot.instruction_invokes_by_id
    instruction_expects_by_id = snapshot.instruction_expects_by_id
    instruction_intents_by_id = snapshot.instruction_intents_by_id
    continuation_key_by_intent_id = {
        intent_id: key
        for intent_id, intent in instruction_intents_by_id.items()
        if (key := (getattr(intent, "continuation_key", None) or "").strip())
    }
    activation_field_bindings_by_intent_id = getattr(
        snapshot, "activation_field_bindings_by_intent_id", {}
    )
    outcome_field_bindings_by_intent_id = getattr(
        snapshot, "outcome_field_bindings_by_intent_id", {}
    )
    receipt_field_bindings_by_intent_id = getattr(
        snapshot, "receipt_field_bindings_by_intent_id", {}
    )
    action_continuation_bindings: list[PlanActionContinuationBinding] = []
    invoke_attributes_by_invoke_id = snapshot.invoke_attributes_by_invoke_id
    attribute_name_by_id = snapshot.attribute_name_by_id
    if program_id is None:
        replay_bind_receipts_by_instruction_bind_id = {}
        replay_views_by_bind_receipt_id = {}
        replay_invoke_receipts_by_instruction_invoke_id = {}
        replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id = {}
    else:
        replay_bind_receipts_by_instruction_bind_id = dict(
            snapshot.replay_bind_receipts_by_instruction_bind_id
        )
        replay_views_by_bind_receipt_id = dict(snapshot.replay_views_by_bind_receipt_id)
        replay_invoke_receipts_by_instruction_invoke_id = dict(
            snapshot.replay_invoke_receipts_by_instruction_invoke_id
        )
        replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id = dict(
            snapshot.replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id
        )
    input_configs_by_id: dict[UUID, ProgramConfigInputConfig] = {}
    for row in input_config_rows:
        input_configs_by_id[row.id] = row

    instructions = snapshot.instruction_rows
    steps: list[
        PlanInput
        | PlanLet
        | PlanExpectEventConfig
        | PlanIntentActionConfig
        | PlanInvoke
    ] = []
    for instruction in sorted(instructions, key=lambda row: int(row.sequence)):
        instruction_type = _enum_text(instruction.type).casefold()
        if instruction_type == "input":
            instruction_input_id = _instruction_payload_id(
                instruction=instruction,
                relationship_name="instruction_input",
                id_field_name="instruction_input_id",
            )
            if instruction_input_id is None:
                raise ValueError(
                    "ProgramImplInstruction[input] is missing instruction_input_id: "
                    + f"{instruction.id}"
                )
            instruction_input = instruction_inputs_by_id.get(instruction_input_id)
            if instruction_input is None:
                raise ValueError(
                    "Program ontology snapshot missing ProgramImplInstructionInput: "
                    + f"{instruction_input_id}"
                )
            input_config = input_configs_by_id.get(
                instruction_input.program_config_input_config_id
            )
            if input_config is None:
                raise ValueError(
                    "ProgramImplInstructionInput references missing ProgramConfigInputConfig: "
                    + f"{instruction_input.program_config_input_config_id}"
                )
            source_symbol = (input_config.source or "").strip()
            if not source_symbol:
                raise ValueError(
                    "ProgramConfigInputConfig.source cannot be empty for input "
                    + f"{input_config.name!r}"
                )
            default_expr: PlanExpr | None = None
            if input_config.default_expr is not None:
                default_expr = _decode_expr_payload(
                    payload=input_config.default_expr,
                    known_symbols=known_symbols,
                )
            steps.append(
                PlanInput(
                    name=(input_config.name or "").strip(),
                    source=PlanSymbolRef(name=source_symbol),
                    default=default_expr,
                    required=bool(input_config.required),
                    type_ref=None,
                )
            )
            continue

        if instruction_type == "let":
            instruction_let_id = _instruction_payload_id(
                instruction=instruction,
                relationship_name="instruction_let",
                id_field_name="instruction_let_id",
            )
            if instruction_let_id is None:
                raise ValueError(
                    "ProgramImplInstruction[let] is missing instruction_let_id: "
                    + f"{instruction.id}"
                )
            instruction_let = instruction_lets_by_id.get(instruction_let_id)
            if instruction_let is None:
                raise ValueError(
                    "Program ontology snapshot missing ProgramImplInstructionLet: "
                    + f"{instruction_let_id}"
                )
            steps.append(
                PlanLet(
                    name=(instruction_let.name or "").strip(),
                    value=_decode_expr_payload(
                        payload=instruction_let.value_expr,
                        known_symbols=known_symbols,
                    ),
                )
            )
            continue

        if instruction_type == "bind":
            instruction_bind_id = _instruction_payload_id(
                instruction=instruction,
                relationship_name="instruction_bind",
                id_field_name="instruction_bind_id",
            )
            if instruction_bind_id is None:
                raise ValueError(
                    "ProgramImplInstruction[bind] is missing instruction_bind_id: "
                    + f"{instruction.id}"
                )
            instruction_bind = instruction_binds_by_id.get(instruction_bind_id)
            if instruction_bind is None:
                raise ValueError(
                    "Program ontology snapshot missing ProgramImplInstructionBind: "
                    + f"{instruction_bind_id}"
                )
            bound_port_key = port_key_by_id.get(instruction_bind.program_config_port_id)
            if bound_port_key is None:
                raise ValueError(
                    "ProgramImplInstructionBind references unresolved ProgramConfigPort: "
                    + f"{instruction_bind.program_config_port_id}"
                )
            bind_view_key = instruction_bind.view_key
            bind_is_active = bool(instruction_bind.is_active)
            if program_id is not None:
                replay_bind_receipt = replay_bind_receipts_by_instruction_bind_id.get(
                    instruction_bind.id
                )
                if replay_bind_receipt is None:
                    raise ValueError(
                        "Program ontology replay snapshot missing ProgramTurnInstructionBind for "
                        + f"instruction_bind_id={instruction_bind.id}"
                    )
                if (
                    replay_bind_receipt.program_impl_instruction_bind_id
                    != instruction_bind.id
                ):
                    raise ValueError(
                        "Program ontology replay snapshot bind receipt mismatch for ProgramImplInstructionBind: "
                        + f"instruction_bind_id={instruction_bind.id} "
                        + f"receipt_bind_id={replay_bind_receipt.program_impl_instruction_bind_id}"
                    )
                replay_view = replay_views_by_bind_receipt_id.get(
                    replay_bind_receipt.id
                )
                if replay_view is None:
                    raise ValueError(
                        "Program ontology replay snapshot missing ProjectionExperienceView for bind receipt: "
                        + f"{replay_bind_receipt.id}"
                    )
                bind_view_key = replay_view.name
                if not bind_view_key:
                    raise ValueError(
                        "ProjectionExperienceView.name cannot be empty for replay bind receipt "
                        + f"{replay_bind_receipt.id}"
                    )
            steps.append(
                PlanInvoke(
                    call=PlanCall(
                        target="bind",
                        args=(
                            PlanCallArg(
                                name="port",
                                value=PlanSymbolRef(
                                    name=f"program.port.{bound_port_key}"
                                ),
                            ),
                            PlanCallArg(name="view_key", value=bind_view_key),
                            PlanCallArg(name="is_active", value=bind_is_active),
                        ),
                        object_expr=None,
                    ),
                    kind="effect",
                    actor=None,
                )
            )
            continue

        if instruction_type == "invoke":
            instruction_invoke_id = _instruction_payload_id(
                instruction=instruction,
                relationship_name="instruction_invoke",
                id_field_name="instruction_invoke_id",
            )
            if instruction_invoke_id is None:
                raise ValueError(
                    "ProgramImplInstruction[invoke] is missing instruction_invoke_id: "
                    + f"{instruction.id}"
                )
            instruction_invoke = instruction_invokes_by_id.get(instruction_invoke_id)
            if instruction_invoke is None:
                raise ValueError(
                    "Program ontology snapshot missing ProgramImplInstructionInvoke: "
                    + f"{instruction_invoke_id}"
                )
            if program_id is not None:
                replay_invoke_receipt = (
                    replay_invoke_receipts_by_instruction_invoke_id.get(
                        instruction_invoke.id
                    )
                )
                if replay_invoke_receipt is None:
                    raise ValueError(
                        "Program ontology replay snapshot missing ProgramTurnInstructionInvoke for "
                        + f"instruction_invoke_id={instruction_invoke.id}"
                    )
                if (
                    replay_invoke_receipt.program_impl_instruction_invoke_id
                    != instruction_invoke.id
                ):
                    raise ValueError(
                        "Program ontology replay snapshot invoke receipt mismatch for ProgramImplInstructionInvoke: "
                        + f"instruction_invoke_id={instruction_invoke.id} "
                        + "receipt_invoke_id="
                        + f"{replay_invoke_receipt.program_impl_instruction_invoke_id}"
                    )
            invoke_actor_alias = actor_alias_by_assoc_id.get(
                instruction_invoke.program_config_actor_config_id
            )
            if invoke_actor_alias is None:
                raise ValueError(
                    "ProgramImplInstructionInvoke references unresolved ProgramConfigActorConfig: "
                    + f"{instruction_invoke.program_config_actor_config_id}"
                )
            object_alias = port_node_alias_by_id.get(
                instruction_invoke.program_config_port_projection_experience_node_id
            )
            if object_alias is None:
                raise ValueError(
                    "ProgramImplInstructionInvoke references unresolved ProgramConfigPortProjectionExperienceNode: "
                    + f"{instruction_invoke.program_config_port_projection_experience_node_id}"
                )
            invoke_attributes = invoke_attributes_by_invoke_id.get(
                instruction_invoke.id, ()
            )
            call_args: list[PlanCallArg] = []
            for invoke_attribute in sorted(
                invoke_attributes,
                key=lambda row: (
                    row.position if row.position is not None else 0,
                    str(row.id),
                ),
            ):
                if program_id is not None:
                    replay_invoke_attribute_receipt = replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id.get(
                        invoke_attribute.id
                    )
                    if replay_invoke_attribute_receipt is None:
                        raise ValueError(
                            "Program ontology replay snapshot missing invoke-argument receipt for "
                            + f"instruction_invoke_attribute_id={invoke_attribute.id}"
                        )
                    if (
                        replay_invoke_attribute_receipt.program_impl_instruction_invoke_attribute_config_id
                        != invoke_attribute.id
                    ):
                        raise ValueError(
                            "Program ontology replay snapshot invoke-argument receipt mismatch for "
                            + f"instruction_invoke_attribute_id={invoke_attribute.id} "
                            + "receipt_invoke_attribute_id="
                            + f"{replay_invoke_attribute_receipt.program_impl_instruction_invoke_attribute_config_id}"
                        )
                attribute_name = attribute_name_by_id.get(
                    invoke_attribute.attribute_config_id
                )
                if not attribute_name:
                    raise ValueError(
                        "Program ontology snapshot missing invoke attribute name for "
                        + f"{invoke_attribute.attribute_config_id}"
                    )
                call_args.append(
                    PlanCallArg(
                        name=attribute_name,
                        value=_decode_expr_payload(
                            payload=invoke_attribute.value_expr,
                            known_symbols=known_symbols,
                        ),
                    )
                )

            object_expr: PlanExpr | None
            if _is_construct_target(instruction_invoke.target_kind):
                object_expr = None
            else:
                object_expr = PlanSymbolRef(name=object_alias)

            call_target = _resolve_invoke_target(
                function_config_id=instruction_invoke.function_config_id,
                function_targets=function_targets,
            )
            steps.append(
                PlanInvoke(
                    call=PlanCall(
                        target=call_target,
                        args=tuple(call_args),
                        object_expr=object_expr,
                    ),
                    kind="effect",
                    actor=invoke_actor_alias,
                )
            )
            continue

        if instruction_type == "expect":
            instruction_expect_id = _instruction_payload_id(
                instruction=instruction,
                relationship_name="instruction_expect",
                id_field_name="instruction_expect_id",
            )
            if instruction_expect_id is None:
                raise ValueError(
                    "ProgramImplInstruction[expect] is missing instruction_expect_id: "
                    + f"{instruction.id}"
                )
            instruction_expect = instruction_expects_by_id.get(instruction_expect_id)
            if instruction_expect is None:
                raise ValueError(
                    "Program ontology snapshot missing ProgramImplInstructionExpect: "
                    + f"{instruction_expect_id}"
                )
            steps.append(
                PlanExpectEventConfig(
                    ref=str(instruction_expect.event_config_id),
                    required=bool(instruction_expect.required),
                )
            )
            continue

        if instruction_type == "intent":
            instruction_intent_id = _instruction_payload_id(
                instruction=instruction,
                relationship_name="instruction_intent",
                id_field_name="instruction_intent_id",
            )
            if instruction_intent_id is None:
                raise ValueError(
                    "ProgramImplInstruction[intent] is missing instruction_intent_id: "
                    + f"{instruction.id}"
                )
            instruction_intent = instruction_intents_by_id.get(instruction_intent_id)
            if instruction_intent is None:
                raise ValueError(
                    "Program ontology snapshot missing ProgramImplInstructionIntent: "
                    + f"{instruction_intent_id}"
                )
            continuation_key = (
                getattr(instruction_intent, "continuation_key", None) or ""
            ).strip()
            api_capability_endpoint_id = getattr(
                instruction_intent, "api_capability_endpoint_id", None
            )
            request_class_config_id = getattr(
                instruction_intent, "request_class_config_id", None
            )
            response_class_config_id = getattr(
                instruction_intent, "response_class_config_id", None
            )
            steps.append(
                PlanIntentActionConfig(
                    action_ref=str(instruction_intent.action_config_id),
                    event_ref=str(instruction_intent.event_config_id),
                    continuation_key=continuation_key or None,
                    api_capability_endpoint_ref=(
                        str(api_capability_endpoint_id)
                        if api_capability_endpoint_id is not None
                        else None
                    ),
                    request_class_config_ref=(
                        str(request_class_config_id)
                        if request_class_config_id is not None
                        else None
                    ),
                    response_class_config_ref=(
                        str(response_class_config_id)
                        if response_class_config_id is not None
                        else None
                    ),
                )
            )
            target_key = continuation_key
            for binding in activation_field_bindings_by_intent_id.get(
                instruction_intent.id, ()
            ):
                if not target_key:
                    raise ValueError(
                        "Program continuation activation binding target has no continuation_key"
                    )
                action_continuation_bindings.append(
                    PlanActionContinuationActivationFieldBinding(
                        source_input_key=binding.source_input_key,
                        source_class_config_ref=str(binding.source_class_config_id),
                        source_attribute_config_ref=str(
                            binding.source_attribute_config_id
                        ),
                        target_intent_key=target_key,
                        target_request_attribute_config_ref=str(
                            binding.target_request_attribute_config_id
                        ),
                        required=binding.required,
                        position=binding.position,
                    )
                )
            for binding in outcome_field_bindings_by_intent_id.get(
                instruction_intent.id, ()
            ):
                source_key = continuation_key_by_intent_id.get(
                    binding.source_program_impl_instruction_intent_id
                )
                if not target_key or source_key is None:
                    raise ValueError(
                        "Program continuation outcome binding source/target key missing"
                    )
                action_continuation_bindings.append(
                    PlanActionContinuationOutcomeFieldBinding(
                        source_intent_key=source_key,
                        source_response_attribute_config_ref=str(
                            binding.source_response_attribute_config_id
                        ),
                        target_intent_key=target_key,
                        target_request_attribute_config_ref=str(
                            binding.target_request_attribute_config_id
                        ),
                        required=binding.required,
                        position=binding.position,
                    )
                )
            for binding in receipt_field_bindings_by_intent_id.get(
                instruction_intent.id, ()
            ):
                source_key = continuation_key_by_intent_id.get(
                    binding.source_program_impl_instruction_intent_id
                )
                if not target_key or source_key is None:
                    raise ValueError(
                        "Program continuation receipt binding source/target key missing"
                    )
                action_continuation_bindings.append(
                    PlanActionContinuationReceiptFieldBinding(
                        source_intent_key=source_key,
                        source_receipt_class_config_ref=str(
                            binding.source_receipt_class_config_id
                        ),
                        source_receipt_attribute_config_ref=str(
                            binding.source_receipt_attribute_config_id
                        ),
                        target_intent_key=target_key,
                        target_request_attribute_config_ref=str(
                            binding.target_request_attribute_config_id
                        ),
                        required=binding.required,
                        position=binding.position,
                    )
                )
            continue

        raise ValueError(
            "Unsupported ProgramImplInstruction type for ontology decode: "
            + f"{instruction.type!r}"
        )

    plan_name = (program_impl.key or "").strip() or (program_config.key or "").strip()
    if not plan_name:
        plan_name = str(program_impl.id)
    return InvocationPlan(
        name=plan_name,
        steps=tuple(steps),
        actors=tuple(actor_contracts),
        ports=tuple(port_contracts),
        action_continuation_bindings=tuple(action_continuation_bindings),
    )


__all__ = ["assemble_invocation_plan_from_snapshot"]
