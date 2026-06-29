from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import replace
from uuid import UUID

from aware_meta.function.config.deltas.typed_operations import (
    function_invocation_create_typed_operation,
)
from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION,
    MetaProviderDeltaTypedOperation,
)
from aware_meta_ontology.stable_ids import (
    stable_function_impl_instruction_id,
    stable_function_impl_instruction_set_id,
    stable_function_impl_value_source_id,
)

try:
    from aware_grammar.function.parser import (
        FunctionParseError,
        parse_function_statements_from_block,
    )
except Exception:  # pragma: no cover - import fallback for partial runtimes
    FunctionParseError = ValueError
    parse_function_statements_from_block = None


FUNCTION_IMPL_BODY_PROVIDER_DELTA_OPERATION_NORMALIZATION_CONTRACT_VERSION = (
    "aware.meta.function_impl.body.provider_delta_operation_normalization.v0"
)
FUNCTION_IMPL_BODY_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION = (
    "aware.meta.function_impl.body.generated_materialization_intent.v0"
)
FUNCTION_IMPL_BODY_PROVIDER_OPERATION_TYPE = "meta_ocg.function_impl.update"
FUNCTION_IMPL_BODY_ONTOLOGY_SUBJECT_KIND = "function_impl"

_TARGET_EDGE_ID_MAP_FIELDS = (
    "target_class_config_attribute_config_ids_by_name",
    "target_attribute_config_edge_ids_by_name",
    "class_config_attribute_config_ids_by_name",
)
_SOURCE_INPUT_EDGE_ID_MAP_FIELDS = (
    "source_function_config_attribute_config_ids_by_name",
    "source_function_input_edge_ids_by_name",
    "function_config_attribute_config_ids_by_name",
)


@dataclass(frozen=True, slots=True)
class FunctionImplBodyProviderDeltaOperationNormalization:
    status: str
    reason: str
    blockers: tuple[str, ...]
    provider_delta_typed_operation: Mapping[str, object] | None = None
    provider_delta_typed_operation_plan: Mapping[str, object] | None = None

    @property
    def ready(self) -> bool:
        return self.status == "provider_delta_typed_operation_ready"

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "normalization_kind": (
                "meta_function_impl_body_provider_delta_operation_normalization"
            ),
            "contract_version": (
                FUNCTION_IMPL_BODY_PROVIDER_DELTA_OPERATION_NORMALIZATION_CONTRACT_VERSION
            ),
            "status": self.status,
            "reason": self.reason,
            "blocker_count": len(self.blockers),
            "blockers": self.blockers,
        }
        if self.provider_delta_typed_operation is not None:
            payload["provider_delta_typed_operation"] = dict(
                self.provider_delta_typed_operation
            )
        if self.provider_delta_typed_operation_plan is not None:
            payload["provider_delta_typed_operation_plan"] = dict(
                self.provider_delta_typed_operation_plan
            )
        return payload


@dataclass(frozen=True, slots=True)
class FunctionImplBodyGeneratedMaterializationIntent:
    status: str
    reason: str
    blockers: tuple[str, ...]
    provider_delta_typed_operation: Mapping[str, object] | None = None
    provider_delta_typed_operation_plan: Mapping[str, object] | None = None

    @property
    def ready(self) -> bool:
        return self.status == "generated_materialization_intent_ready"

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "intent_kind": (
                "meta_function_impl_body_generated_materialization_intent"
            ),
            "contract_version": (
                FUNCTION_IMPL_BODY_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
            ),
            "status": self.status,
            "reason": self.reason,
            "blocker_count": len(self.blockers),
            "blockers": self.blockers,
        }
        if self.provider_delta_typed_operation is not None:
            payload["provider_delta_typed_operation"] = dict(
                self.provider_delta_typed_operation
            )
        if self.provider_delta_typed_operation_plan is not None:
            payload["provider_delta_typed_operation_plan"] = dict(
                self.provider_delta_typed_operation_plan
            )
        return payload


def normalize_function_impl_body_source_meaning_provider_delta_operation(
    *,
    operation: Mapping[str, object],
    function_impl_object_id: str | None,
    function_impl_source_object_id: str | None = None,
    current_semantic_object_ids: Mapping[str, str] | None = None,
    current_semantic_source_object_ids: Mapping[str, str] | None = None,
) -> FunctionImplBodyProviderDeltaOperationNormalization:
    after_payload = _mapping_value(operation.get("after_payload"))
    before_payload = _mapping_value(operation.get("before_payload"))
    semantic_key = _string_value(operation.get("semantic_key"))
    operation_key = _string_value(operation.get("operation_key"))
    if semantic_key is None or operation_key is None:
        return _blocked_normalization(
            reason="function_impl_body_operation_identity_unavailable",
            blockers=(
                "missing_semantic_key" if semantic_key is None else "",
                "missing_operation_key" if operation_key is None else "",
            ),
        )
    normalized_receiver_object_id = _first_text(
        function_impl_object_id,
        after_payload.get("semantic_apply_receiver_object_id"),
        after_payload.get("receiver_object_id"),
        after_payload.get("executable_object_id"),
        before_payload.get("semantic_apply_receiver_object_id"),
        before_payload.get("receiver_object_id"),
        before_payload.get("executable_object_id"),
        after_payload.get("entity_id"),
        before_payload.get("entity_id"),
    )
    normalized_source_object_id = _first_text(
        function_impl_source_object_id,
        after_payload.get("semantic_source_object_id"),
        after_payload.get("source_object_id"),
        after_payload.get("function_impl_id"),
        before_payload.get("semantic_source_object_id"),
        before_payload.get("source_object_id"),
        before_payload.get("function_impl_id"),
        after_payload.get("entity_id"),
        before_payload.get("entity_id"),
        normalized_receiver_object_id,
    )
    if normalized_receiver_object_id is None:
        return _blocked_normalization(
            reason="function_impl_body_requires_function_impl_object_id",
            blockers=("function_impl_object_id_unavailable",),
        )
    if normalized_source_object_id is None:
        return _blocked_normalization(
            reason="function_impl_body_requires_function_impl_source_object_id",
            blockers=("function_impl_source_object_id_unavailable",),
        )

    class_name = _first_text(
        after_payload.get("class_name"),
        before_payload.get("class_name"),
        _class_name_from_function_impl_semantic_key(semantic_key),
    )
    function_name = _first_text(
        after_payload.get("function_name"),
        before_payload.get("function_name"),
        _function_name_from_function_impl_semantic_key(semantic_key),
    )
    semantic_reference_object_ids = (
        current_semantic_source_object_ids
        or current_semantic_object_ids
        or {}
    )
    receiver_object_ids = current_semantic_object_ids or {}
    current_signature, current_blockers = _function_impl_signature_from_payload(
        payload=after_payload,
        payload_role="current",
        class_name=class_name,
        function_name=function_name,
        semantic_object_ids=semantic_reference_object_ids,
    )
    baseline_signature, baseline_blockers = _function_impl_signature_from_payload(
        payload=before_payload,
        payload_role="baseline",
        class_name=class_name,
        function_name=function_name,
        semantic_object_ids=semantic_reference_object_ids,
    )
    blockers = (*baseline_blockers, *current_blockers)
    if blockers:
        return _blocked_normalization(
            reason="function_impl_body_signature_normalization_blocked",
            blockers=tuple(dict.fromkeys(blockers)),
        )

    requested_function_semantic_key = _first_text(
        after_payload.get("function_semantic_key"),
        before_payload.get("function_semantic_key"),
        (
            f"meta.function:{class_name}.{function_name}"
            if class_name is not None and function_name is not None
            else None
        ),
    )
    function_semantic_key = requested_function_semantic_key
    function_impl_key = _first_text(
        after_payload.get("function_impl_key"),
        before_payload.get("function_impl_key"),
        _function_impl_key_from_semantic_key(semantic_key),
        "default",
    )
    current_signature = _function_impl_signature_with_nested_receiver_ids(
        signature=current_signature,
        function_impl_object_id=normalized_source_object_id,
        class_name=class_name,
        function_name=function_name,
        function_impl_key=function_impl_key,
        semantic_object_ids=receiver_object_ids,
    )
    baseline_signature = _function_impl_signature_with_nested_receiver_ids(
        signature=baseline_signature,
        function_impl_object_id=normalized_source_object_id,
        class_name=class_name,
        function_name=function_name,
        function_impl_key=function_impl_key,
        semantic_object_ids=receiver_object_ids,
    )
    provider_operation_key = (
        f"meta_ocg_provider_delta:update:function_impl:{semantic_key}"
    )
    source_refs = _tuple_text(operation.get("source_refs"))
    current_payload: dict[str, object] = {
        "semantic_key": semantic_key,
        "object_kind": "function_impl",
        "entity_id": normalized_receiver_object_id,
        "function_impl_id": normalized_source_object_id,
        "semantic_source_object_id": normalized_source_object_id,
        "source_object_id": normalized_source_object_id,
        "function_semantic_key": function_semantic_key,
        "function_name": function_name,
        "function_impl_key": function_impl_key,
        "function_impl_kind": "instruction_body",
        "function_impl_signature": current_signature,
    }
    if normalized_receiver_object_id != normalized_source_object_id:
        current_payload["semantic_apply_receiver_object_id"] = (
            normalized_receiver_object_id
        )
        current_payload["receiver_object_id"] = normalized_receiver_object_id
        current_payload["executable_object_id"] = normalized_receiver_object_id
    typed_operation = MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=provider_operation_key,
        operation_family="update",
        provider_operation_type=FUNCTION_IMPL_BODY_PROVIDER_OPERATION_TYPE,
        semantic_key=semantic_key,
        semantic_subject_type="aware_meta.FunctionImpl",
        ontology_subject_kind=FUNCTION_IMPL_BODY_ONTOLOGY_SUBJECT_KIND,
        source_entry_key=operation_key,
        source_delta_key=_optional_text(operation.get("event_key")),
        source_refs=source_refs,
        baseline={
            "object_id": normalized_receiver_object_id,
            "object": {
                "function_impl_signature": baseline_signature,
            },
        },
        current=current_payload,
        include_operation_evidence=True,
    ).evidence_payload()
    typed_operation_plan = {
        "plan_kind": "meta_ocg_provider_delta_typed_operation_plan",
        "contract_version": (
            META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION
        ),
        "operation_contract_version": typed_operation.get("contract_version"),
        "status": "typed_operation_plan_ready",
        "reason": "meta_function_impl_body_provider_delta_operation_ready",
        "source": "aware_meta.semantic_operation_resolution",
        "provider_key": "aware_meta",
        "typed_operation_count": 1,
        "typed_operations": (typed_operation,),
        "semantic_object_anchor_count": 0,
        "semantic_object_anchors": (),
        "blocked_operation_count": 0,
        "blocked_operations": (),
        "available": True,
        "blocked": False,
    }
    return FunctionImplBodyProviderDeltaOperationNormalization(
        status="provider_delta_typed_operation_ready",
        reason="function_impl_body_provider_delta_operation_ready",
        blockers=(),
        provider_delta_typed_operation=typed_operation,
        provider_delta_typed_operation_plan=typed_operation_plan,
    )


def build_function_impl_body_generated_materialization_intent(
    *,
    operation: Mapping[str, object],
    current_semantic_object_ids: Mapping[str, str] | None = None,
) -> FunctionImplBodyGeneratedMaterializationIntent:
    after_payload = _mapping_value(operation.get("after_payload"))
    before_payload = _mapping_value(operation.get("before_payload"))
    semantic_key = _string_value(operation.get("semantic_key"))
    operation_key = _string_value(operation.get("operation_key"))
    class_name = _first_text(
        after_payload.get("class_name"),
        before_payload.get("class_name"),
        _class_name_from_function_impl_semantic_key(semantic_key or ""),
    )
    function_name = _first_text(
        after_payload.get("function_name"),
        before_payload.get("function_name"),
        _function_name_from_function_impl_semantic_key(semantic_key or ""),
    )
    requested_function_semantic_key = _first_text(
        after_payload.get("function_semantic_key"),
        before_payload.get("function_semantic_key"),
        (
            f"meta.function:{class_name}.{function_name}"
            if class_name is not None and function_name is not None
            else None
        ),
    )
    semantic_object_ids = current_semantic_object_ids or {}
    resolved_function_semantic_key, resolved_function_config_id = (
        _function_config_identity_from_semantic_object_ids(
            semantic_object_ids=semantic_object_ids,
            requested_function_semantic_key=requested_function_semantic_key,
            class_name=class_name,
            function_name=function_name,
        )
    )
    function_semantic_key = _first_text(
        resolved_function_semantic_key,
        requested_function_semantic_key,
    )
    function_config_id = _first_text(
        after_payload.get("function_config_id"),
        before_payload.get("function_config_id"),
        resolved_function_config_id,
    )
    source_refs = _tuple_text(operation.get("source_refs"))
    baseline_body_text = _python_orm_baseline_body_text(
        aware_body_text=_optional_text(before_payload.get("body_text")),
        description=_first_text(
            after_payload.get("function_description"),
            before_payload.get("function_description"),
        ),
    )
    body_text = _python_orm_current_body_text(
        aware_body_text=_optional_text(after_payload.get("body_text")),
    )
    blockers = tuple(
        blocker
        for blocker, value in (
            ("missing_operation_key", operation_key),
            ("missing_semantic_key", semantic_key),
            ("missing_class_name", class_name),
            ("missing_function_name", function_name),
            ("missing_function_semantic_key", function_semantic_key),
            ("missing_function_config_id", function_config_id),
            ("missing_source_refs", source_refs),
            ("missing_python_orm_baseline_body_text", baseline_body_text),
            ("missing_python_orm_body_text", body_text),
        )
        if value in {None, (), ""}
    )
    if blockers:
        return FunctionImplBodyGeneratedMaterializationIntent(
            status="generated_materialization_intent_blocked",
            reason="function_impl_body_generated_materialization_intent_blocked",
            blockers=blockers,
        )

    invocation_semantic_key = (
        f"{function_semantic_key}/invocation:function_impl_body"
    )
    invocation_operation = function_invocation_create_typed_operation(
        semantic_key=invocation_semantic_key,
        function_semantic_key=function_semantic_key or "",
        function_config_id=function_config_id or "",
        function_config_invocation_id=(
            f"{semantic_key}:generated_materialization_invocation"
        ),
        position=0,
        kind="assignment_body",
        target_function_config_id=(
            f"{semantic_key}:generated_materialization_body"
        ),
        relationship_fingerprint="function_impl_body",
        source_refs=source_refs,
    )
    current = {
        **dict(invocation_operation.current),
        "owner_key": class_name,
        "owner_semantic_key": f"meta.class:{class_name}",
        "function_name": function_name,
        "function_impl_semantic_key": semantic_key,
        "generated_materialization": {
            "python_orm": {
                "baseline_body_text": baseline_body_text,
                "body_text": body_text,
            },
        },
    }
    typed_operation = replace(
        invocation_operation,
        current=current,
        would_execute=False,
        would_persist=False,
        extra={
            "intent_only": True,
            "intent_source": "aware_meta.function_impl.body.source_meaning",
            "source_operation_key": operation_key,
        },
    ).evidence_payload()
    typed_operation_plan = {
        "plan_kind": "meta_ocg_provider_delta_typed_operation_plan",
        "contract_version": (
            META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION
        ),
        "operation_contract_version": typed_operation.get("contract_version"),
        "status": "typed_operation_plan_ready",
        "reason": (
            "meta_function_impl_body_generated_materialization_intent_ready"
        ),
        "source": "aware_meta.semantic_operation_resolution",
        "provider_key": "aware_meta",
        "typed_operation_count": 1,
        "typed_operations": (typed_operation,),
        "semantic_object_anchor_count": 0,
        "semantic_object_anchors": (),
        "blocked_operation_count": 0,
        "blocked_operations": (),
        "available": True,
        "blocked": False,
    }
    return FunctionImplBodyGeneratedMaterializationIntent(
        status="generated_materialization_intent_ready",
        reason="function_impl_body_generated_materialization_intent_ready",
        blockers=(),
        provider_delta_typed_operation=typed_operation,
        provider_delta_typed_operation_plan=typed_operation_plan,
    )


def _function_impl_signature_from_payload(
    *,
    payload: Mapping[str, object],
    payload_role: str,
    class_name: str | None,
    function_name: str | None,
    semantic_object_ids: Mapping[str, str],
) -> tuple[dict[str, object], tuple[str, ...]]:
    explicit_signature = _mapping_value(payload.get("function_impl_signature"))
    if explicit_signature:
        return explicit_signature, ()
    body_text = _optional_text(payload.get("body_text"))
    if body_text is None:
        if payload_role == "baseline":
            return _function_impl_signature(instructions=()), ()
        return {}, (f"{payload_role}_function_impl_body_text_unavailable",)
    return _function_impl_signature_from_body_text(
        body_text=body_text,
        payload=payload,
        payload_role=payload_role,
        class_name=class_name,
        function_name=function_name,
        semantic_object_ids=semantic_object_ids,
    )


def _function_impl_signature_from_body_text(
    *,
    body_text: str,
    payload: Mapping[str, object],
    payload_role: str,
    class_name: str | None,
    function_name: str | None,
    semantic_object_ids: Mapping[str, str],
) -> tuple[dict[str, object], tuple[str, ...]]:
    if parse_function_statements_from_block is None:
        return {}, ("aware_function_body_parser_unavailable",)
    try:
        statements = parse_function_statements_from_block(body_text)
    except FunctionParseError as exc:
        return {}, (f"{payload_role}_function_impl_body_parse_error:{exc}",)
    blockers: list[str] = []
    instructions: list[dict[str, object]] = []
    for sequence, statement in enumerate(statements):
        if getattr(statement, "kind", None) != "set":
            blockers.append(
                f"unsupported_{payload_role}_function_impl_statement:"
                f"{getattr(statement, 'kind', 'unknown')}"
            )
            continue
        target_name = _optional_text(getattr(statement, "name", None))
        value = getattr(statement, "value", None)
        value_kind = _optional_text(getattr(value, "kind", None))
        source_name = _optional_text(getattr(value, "text", None))
        if target_name is None:
            blockers.append(f"{payload_role}_function_impl_set_target_unavailable")
            continue
        if value_kind != "reference" or source_name is None:
            blockers.append(
                f"unsupported_{payload_role}_function_impl_set_value_source:"
                f"{value_kind or 'unknown'}"
            )
            continue
        target_edge_id = _edge_id_for_name(
            payload=payload,
            name=target_name,
            map_fields=_TARGET_EDGE_ID_MAP_FIELDS,
            direct_field="target_class_config_attribute_config_id",
            semantic_object_ids=semantic_object_ids,
            semantic_object_aliases=_target_class_attribute_edge_aliases(
                class_name=class_name,
                attribute_name=target_name,
            ),
        )
        source_input_id = _edge_id_for_name(
            payload=payload,
            name=source_name,
            map_fields=_SOURCE_INPUT_EDGE_ID_MAP_FIELDS,
            direct_field="source_function_config_attribute_config_id",
            semantic_object_ids=semantic_object_ids,
            semantic_object_aliases=_source_function_input_edge_aliases(
                class_name=class_name,
                function_name=function_name,
                input_name=source_name,
            ),
        )
        if target_edge_id is None:
            blockers.append(
                f"{payload_role}_function_impl_target_edge_id_unavailable:"
                f"{target_name}"
            )
            continue
        if source_input_id is None:
            blockers.append(
                f"{payload_role}_function_impl_source_input_edge_id_unavailable:"
                f"{source_name}"
            )
            continue
        instructions.append(
            {
                "type": "set",
                "sequence": sequence,
                "set": {
                    "target_attribute_name": target_name,
                    "target_class_config_attribute_config_id": target_edge_id,
                    "value_source": {
                        "key": source_name,
                        "kind": "function_input_ref",
                        "source_function_config_attribute_config_id": (
                            source_input_id
                        ),
                        "source_function_input_name": source_name,
                    },
                },
            }
        )
    if blockers:
        return {}, tuple(dict.fromkeys(blockers))
    return _function_impl_signature(instructions=tuple(instructions)), ()


def _python_orm_baseline_body_text(
    *,
    aware_body_text: str | None,
    description: str | None,
) -> str | None:
    docstring = _docstring_text(aware_body_text) or _optional_text(description)
    if docstring is None:
        return "raise NotImplementedError"
    return f'"""{docstring}"""\n        raise NotImplementedError'


def _python_orm_current_body_text(*, aware_body_text: str | None) -> str | None:
    if aware_body_text is None or parse_function_statements_from_block is None:
        return None
    try:
        statements = parse_function_statements_from_block(aware_body_text)
    except FunctionParseError:
        return None
    lines: list[str] = []
    for statement in statements:
        if getattr(statement, "kind", None) != "set":
            continue
        target_name = _optional_text(getattr(statement, "name", None))
        value = getattr(statement, "value", None)
        value_kind = _optional_text(getattr(value, "kind", None))
        source_name = _optional_text(getattr(value, "text", None))
        if target_name is None or value_kind != "reference" or source_name is None:
            continue
        lines.append(f"self.{target_name} = {source_name}")
    if not lines:
        return None
    lines.append("return self")
    return "\n        ".join(lines)


def _docstring_text(value: str | None) -> str | None:
    if value is None or '"""' not in value:
        return None
    _, remainder = value.split('"""', maxsplit=1)
    if '"""' not in remainder:
        return None
    raw_docstring, _ = remainder.split('"""', maxsplit=1)
    return " ".join(line.strip() for line in raw_docstring.splitlines()).strip() or None


def _function_impl_signature(
    *,
    instructions: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return {
        "instruction_count": len(instructions),
        "instruction_summaries": tuple(
            _instruction_summary(instruction=instruction)
            for instruction in instructions
        ),
        "instructions": instructions,
    }


def _instruction_summary(*, instruction: Mapping[str, object]) -> str:
    instruction_type = _optional_text(instruction.get("type")) or "unknown"
    if instruction_type != "set":
        return instruction_type
    set_payload = _mapping_value(instruction.get("set"))
    value_source = _mapping_value(set_payload.get("value_source"))
    target = _optional_text(set_payload.get("target_attribute_name")) or "unknown"
    source = _optional_text(value_source.get("key")) or "unknown"
    return f"set {target} = {source}"


def _function_impl_signature_with_nested_receiver_ids(
    *,
    signature: Mapping[str, object],
    function_impl_object_id: str,
    class_name: str | None,
    function_name: str | None,
    function_impl_key: str | None,
    semantic_object_ids: Mapping[str, str],
) -> dict[str, object]:
    function_impl_uuid = _uuid_value(function_impl_object_id)
    if (
        function_impl_uuid is None
        or class_name is None
        or function_name is None
        or function_impl_key is None
    ):
        return dict(signature)
    enriched_signature = dict(signature)
    enriched_instructions: list[dict[str, object]] = []
    changed = False
    for raw_instruction in _tuple_values(signature.get("instructions")):
        if not isinstance(raw_instruction, Mapping):
            continue
        instruction = dict(raw_instruction)
        instruction_type = _optional_text(instruction.get("type"))
        sequence = _int_value(instruction.get("sequence"))
        if instruction_type is None or sequence is None:
            enriched_instructions.append(instruction)
            continue
        instruction_id = stable_function_impl_instruction_id(
            function_impl_id=function_impl_uuid,
            type=instruction_type,
            sequence=sequence,
        )
        key_prefix = (
            f"{class_name}.{function_name}:{function_impl_key}:"
            f"{instruction_type}:{sequence}"
        )
        changed |= _attach_nested_identity(
            payload=instruction,
            source_field_name="function_impl_instruction_id",
            source_object_id=str(instruction_id),
            receiver_object_id=_optional_text(
                semantic_object_ids.get(
                    f"meta.function_impl_instruction_receiver:{key_prefix}"
                )
            ),
        )
        set_payload = _mapping_value(instruction.get("set"))
        if set_payload:
            set_payload = dict(set_payload)
            instruction_set_id = stable_function_impl_instruction_set_id(
                function_impl_instruction_id=instruction_id,
            )
            changed |= _attach_nested_identity(
                payload=set_payload,
                source_field_name="function_impl_instruction_set_id",
                source_object_id=str(instruction_set_id),
                receiver_object_id=_optional_text(
                    semantic_object_ids.get(
                        "meta.function_impl_instruction_set_receiver:"
                        f"{key_prefix}"
                    )
                ),
            )
            value_source = _mapping_value(set_payload.get("value_source"))
            if value_source:
                value_source = _function_impl_value_source_with_receiver_id(
                    value_source=value_source,
                    instruction_id=instruction_id,
                    semantic_object_ids=semantic_object_ids,
                    key_prefix=key_prefix,
                )
                set_payload["value_source"] = value_source
                changed = True
            instruction["set"] = set_payload
        value_sources: list[dict[str, object]] = []
        for raw_value_source in _tuple_values(instruction.get("value_sources")):
            if not isinstance(raw_value_source, Mapping):
                continue
            value_sources.append(
                _function_impl_value_source_with_receiver_id(
                    value_source=raw_value_source,
                    instruction_id=instruction_id,
                    semantic_object_ids=semantic_object_ids,
                    key_prefix=key_prefix,
                )
            )
        if value_sources:
            instruction["value_sources"] = tuple(value_sources)
            changed = True
        enriched_instructions.append(instruction)
    if changed:
        enriched_signature["instructions"] = tuple(enriched_instructions)
    return enriched_signature


def _function_impl_value_source_with_receiver_id(
    *,
    value_source: Mapping[str, object],
    instruction_id: UUID,
    semantic_object_ids: Mapping[str, str],
    key_prefix: str,
) -> dict[str, object]:
    enriched = dict(value_source)
    value_source_key = _optional_text(enriched.get("key"))
    if value_source_key is None:
        return enriched
    value_source_id = stable_function_impl_value_source_id(
        function_impl_instruction_id=instruction_id,
        key=value_source_key,
    )
    _attach_nested_identity(
        payload=enriched,
        source_field_name="function_impl_value_source_id",
        source_object_id=str(value_source_id),
        receiver_object_id=_optional_text(
            semantic_object_ids.get(
                "meta.function_impl_value_source_receiver:"
                f"{key_prefix}:{value_source_key}"
            )
        ),
    )
    return enriched


def _attach_nested_identity(
    *,
    payload: dict[str, object],
    source_field_name: str,
    source_object_id: str,
    receiver_object_id: str | None,
) -> bool:
    changed = False
    if payload.get(source_field_name) != source_object_id:
        payload[source_field_name] = source_object_id
        changed = True
    payload.setdefault("semantic_source_object_id", source_object_id)
    payload.setdefault("source_object_id", source_object_id)
    if receiver_object_id is None:
        return changed
    if payload.get("semantic_apply_receiver_object_id") != receiver_object_id:
        payload["semantic_apply_receiver_object_id"] = receiver_object_id
        changed = True
    payload["receiver_object_id"] = receiver_object_id
    payload["executable_object_id"] = receiver_object_id
    return True


def _edge_id_for_name(
    *,
    payload: Mapping[str, object],
    name: str,
    map_fields: tuple[str, ...],
    direct_field: str,
    semantic_object_ids: Mapping[str, str],
    semantic_object_aliases: tuple[str, ...],
) -> str | None:
    for field_name in map_fields:
        entries = _mapping_value(payload.get(field_name))
        edge_id = _optional_text(entries.get(name))
        if edge_id is not None:
            return edge_id
    direct = _optional_text(payload.get(direct_field))
    if direct is not None:
        return direct
    for alias in semantic_object_aliases:
        edge_id = _optional_text(semantic_object_ids.get(alias))
        if edge_id is not None:
            return edge_id
    return None


def _target_class_attribute_edge_aliases(
    *,
    class_name: str | None,
    attribute_name: str,
) -> tuple[str, ...]:
    if class_name is None:
        return ()
    return (
        f"meta.class_attribute_edge:{class_name}.{attribute_name}",
        f"meta.attribute_edge:{class_name}.{attribute_name}",
    )


def _source_function_input_edge_aliases(
    *,
    class_name: str | None,
    function_name: str | None,
    input_name: str,
) -> tuple[str, ...]:
    if class_name is None or function_name is None:
        return ()
    return (
        f"meta.function_input_edge:{class_name}.{function_name}.{input_name}",
        f"meta.function_attribute_edge:{class_name}.{function_name}.{input_name}",
    )


def _function_config_identity_from_semantic_object_ids(
    *,
    semantic_object_ids: Mapping[str, str],
    requested_function_semantic_key: str | None,
    class_name: str | None,
    function_name: str | None,
) -> tuple[str | None, str | None]:
    if requested_function_semantic_key is not None:
        object_id = _optional_text(
            semantic_object_ids.get(requested_function_semantic_key)
        )
        if object_id is not None:
            return requested_function_semantic_key, object_id
    if class_name is None or function_name is None:
        return None, None
    meta_alias = f"meta.function:{class_name}.{function_name}"
    object_id = _optional_text(semantic_object_ids.get(meta_alias))
    if object_id is not None:
        return meta_alias, object_id
    function_suffix = f"/function:{function_name}"
    class_marker = f".{class_name}"
    for semantic_key, raw_object_id in sorted(semantic_object_ids.items()):
        if (
            semantic_key.endswith(function_suffix)
            and class_marker in semantic_key
        ):
            object_id = _optional_text(raw_object_id)
            if object_id is not None:
                return semantic_key, object_id
    ocg_node_suffix = f".{class_name}.{function_name}"
    for semantic_key, raw_object_id in sorted(semantic_object_ids.items()):
        if "/node:" not in semantic_key or not semantic_key.endswith(
            ocg_node_suffix
        ):
            continue
        object_id = _optional_text(raw_object_id)
        if object_id is not None:
            return semantic_key, object_id
    return None, None


def _blocked_normalization(
    *,
    reason: str,
    blockers: tuple[str, ...],
) -> FunctionImplBodyProviderDeltaOperationNormalization:
    return FunctionImplBodyProviderDeltaOperationNormalization(
        status="provider_delta_typed_operation_blocked",
        reason=reason,
        blockers=tuple(item for item in blockers if item),
    )


def _class_name_from_function_impl_semantic_key(semantic_key: str) -> str | None:
    target = semantic_key.split(":", maxsplit=1)[-1]
    if "." not in target:
        return None
    return target.split(".", maxsplit=1)[0].strip() or None


def _function_name_from_function_impl_semantic_key(semantic_key: str) -> str | None:
    target = semantic_key.split(":", maxsplit=1)[-1]
    if "." not in target:
        return None
    class_remainder = target.split(".", maxsplit=1)[1]
    if ":" in class_remainder:
        class_remainder = class_remainder.rsplit(":", maxsplit=1)[0]
    return class_remainder.strip() or None


def _function_impl_key_from_semantic_key(semantic_key: str) -> str | None:
    if ":" not in semantic_key:
        return None
    return semantic_key.rsplit(":", maxsplit=1)[-1].strip() or None


def _mapping_value(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _tuple_values(value: object) -> tuple[object, ...]:
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


def _uuid_value(value: object) -> UUID | None:
    text = _optional_text(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _int_value(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = _optional_text(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_value(value: object) -> str | None:
    return _optional_text(value)


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _tuple_text(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        text = _optional_text(value)
        return () if text is None else (text,)
    if not isinstance(value, (list, tuple, set, frozenset)):
        return ()
    return tuple(
        text for item in value if (text := _optional_text(item)) is not None
    )


__all__ = [
    "FUNCTION_IMPL_BODY_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION",
    "FUNCTION_IMPL_BODY_PROVIDER_DELTA_OPERATION_NORMALIZATION_CONTRACT_VERSION",
    "FUNCTION_IMPL_BODY_PROVIDER_OPERATION_TYPE",
    "FunctionImplBodyGeneratedMaterializationIntent",
    "FunctionImplBodyProviderDeltaOperationNormalization",
    "build_function_impl_body_generated_materialization_intent",
    "normalize_function_impl_body_source_meaning_provider_delta_operation",
]
