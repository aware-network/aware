from __future__ import annotations

from collections.abc import Mapping, Sequence

from aware_meta.materialization.deltas.baseline import (
    _mapping_value,
    _optional_text,
    _tuple_text,
)
from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_COMMITTED_SEMANTIC_CHANGE_CONTRACT_VERSION,
    META_PROVIDER_DELTA_READABLE_SEMANTIC_CHANGE_CHAIN_CONTRACT_VERSION,
    META_PROVIDER_DELTA_SEMANTIC_CHANGE_REPORT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_SEMANTIC_COMMIT_EVIDENCE_CONTRACT_VERSION,
    META_PROVIDER_DELTA_SEMANTIC_WORLD_CHANGE_CONTRACT_VERSION,
)
from aware_meta.materialization.deltas.typed_operations import (
    _typed_operation_count_by_field,
)


_SUPPORTED_DELTA_PROVIDER_KEY = "aware_meta"


def _provider_delta_semantic_change_report(
    *,
    semantic_dirty_diff: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
) -> dict[str, object]:
    dirty_status = _optional_text(semantic_dirty_diff.get("status"))
    typed_status = _optional_text(provider_delta_typed_operation_plan.get("status"))
    blockers = _semantic_change_report_blockers(
        dirty_status=dirty_status,
        typed_status=typed_status,
    )
    typed_operations = tuple(
        _mapping_value(operation)
        for operation in _tuple_evidence(
            provider_delta_typed_operation_plan.get("typed_operations")
        )
        if isinstance(operation, Mapping)
    )
    world_changes = (
        ()
        if blockers
        else tuple(
            _semantic_world_change_from_typed_operation(
                typed_operation=operation,
            )
            for operation in typed_operations
            if _optional_text(operation.get("operation_family"))
            in {"create", "update", "delete"}
        )
    )
    available = not blockers
    readable_change_chain = _readable_semantic_change_chain(
        available=available,
        blockers=blockers,
        world_changes=world_changes,
    )
    return {
        "report_kind": "meta_ocg_provider_delta_semantic_change_report",
        "contract_version": (
            META_PROVIDER_DELTA_SEMANTIC_CHANGE_REPORT_CONTRACT_VERSION
        ),
        "change_contract_version": (
            META_PROVIDER_DELTA_SEMANTIC_WORLD_CHANGE_CONTRACT_VERSION
        ),
        "readable_change_chain_contract_version": (
            META_PROVIDER_DELTA_READABLE_SEMANTIC_CHANGE_CHAIN_CONTRACT_VERSION
        ),
        "status": (
            "semantic_change_report_ready"
            if available
            else "semantic_change_report_blocked"
        ),
        "reason": (
            "meta_ocg_provider_delta_semantic_changes_reported"
            if available
            else "meta_ocg_provider_delta_semantic_change_report_blocked"
        ),
        "source": "aware_meta.provider_delta.semantic_dirty_diff",
        "provider_key": _SUPPORTED_DELTA_PROVIDER_KEY,
        "semantic_dirty_diff_status": dirty_status,
        "semantic_dirty_diff_reason": _optional_text(semantic_dirty_diff.get("reason")),
        "provider_delta_typed_operation_status": typed_status,
        "provider_delta_typed_operation_reason": _optional_text(
            provider_delta_typed_operation_plan.get("reason")
        ),
        "semantic_dirty_entry_count": _int_payload_value(
            semantic_dirty_diff.get("dirty_entry_count")
        ),
        "typed_operation_count": len(typed_operations),
        "semantic_world_change_count": len(world_changes),
        "semantic_world_changes": world_changes,
        "minimal_readable_semantic_change_chain": readable_change_chain,
        "readable_semantic_change_chain": readable_change_chain,
        "readable_semantic_change_chain_markdown": readable_change_chain["markdown"],
        "readable_semantic_change_chain_lines": readable_change_chain["lines"],
        "natural_language_summaries": tuple(
            _optional_text(change.get("summary")) or "" for change in world_changes
        ),
        "change_type_counts": _typed_operation_count_by_field(
            operations=world_changes,
            field_name="change_type",
        ),
        "change_key_counts": _typed_operation_count_by_field(
            operations=world_changes,
            field_name="change_key",
        ),
        "operation_family_counts": _typed_operation_count_by_field(
            operations=world_changes,
            field_name="verb",
        ),
        "available": available,
        "blocked": not available,
        "blockers": blockers,
        "blocker_count": len(blockers),
    }


def _semantic_change_report_blockers(
    *,
    dirty_status: str | None,
    typed_status: str | None,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if dirty_status != "semantic_dirty_diff_ready":
        blockers.append(f"semantic_dirty_diff_not_ready:{dirty_status or 'unknown'}")
    if typed_status != "typed_operation_plan_ready":
        blockers.append(f"typed_operation_plan_not_ready:{typed_status or 'unknown'}")
    return tuple(blockers)


def _readable_semantic_change_chain(
    *,
    available: bool,
    blockers: tuple[str, ...],
    world_changes: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    chain_changes = tuple(
        change
        for change in world_changes
        if _optional_text(change.get("ontology_subject_kind"))
        not in {"object_config_graph", "object_config_graph_package"}
    )
    lines = (
        tuple(
            _readable_semantic_change_chain_line(
                change=change,
                index=index,
            )
            for index, change in enumerate(chain_changes, start=1)
        )
        if available
        else ()
    )
    return {
        "chain_kind": "meta_ocg_provider_delta_readable_semantic_change_chain",
        "contract_version": (
            META_PROVIDER_DELTA_READABLE_SEMANTIC_CHANGE_CHAIN_CONTRACT_VERSION
        ),
        "status": (
            "readable_semantic_change_chain_ready"
            if available
            else "readable_semantic_change_chain_blocked"
        ),
        "reason": (
            "meta_ocg_provider_delta_readable_semantic_change_chain_ready"
            if available
            else "meta_ocg_provider_delta_readable_semantic_change_chain_blocked"
        ),
        "source": "aware_meta.provider_delta.semantic_change_report",
        "provider_key": _SUPPORTED_DELTA_PROVIDER_KEY,
        "source_change_count": len(world_changes),
        "change_count": len(chain_changes),
        "line_count": len(lines),
        "lines": lines,
        "markdown": _readable_semantic_change_chain_markdown(lines=lines),
        "plain_text": "\n".join(lines),
        "available": available,
        "blocked": not available,
        "blockers": blockers,
        "blocker_count": len(blockers),
    }


def _readable_semantic_change_chain_line(
    *,
    change: Mapping[str, object],
    index: int,
) -> str:
    operation = _optional_text(change.get("verb")) or "change"
    subject_label = _optional_text(change.get("subject_label")) or (
        _optional_text(change.get("semantic_key")) or "semantic object"
    )
    subject_kind = _optional_text(change.get("ontology_subject_kind"))
    description = _optional_text(change.get("subject_description"))
    suffix = (
        f" {description}"
        if subject_kind in {"attribute", "function", "function_impl"}
        and description is not None
        else ""
    )
    return f"{index}. {_readable_operation_label(operation)} {subject_label}.{suffix}"


def _readable_operation_label(operation: str) -> str:
    if operation == "create":
        return "Add"
    if operation == "update":
        return "Update"
    if operation == "delete":
        return "Remove"
    return operation.replace("_", " ").capitalize()


def _readable_semantic_change_chain_markdown(
    *,
    lines: tuple[str, ...],
) -> str:
    if not lines:
        return "No semantic changes are ready."
    return "\n".join(lines)


def _semantic_world_change_from_typed_operation(
    *,
    typed_operation: Mapping[str, object],
) -> dict[str, object]:
    current = _mapping_value(typed_operation.get("current"))
    baseline = _mapping_value(typed_operation.get("baseline"))
    operation_family = _optional_text(typed_operation.get("operation_family")) or (
        "unknown"
    )
    subject_kind = _optional_text(typed_operation.get("ontology_subject_kind")) or (
        "unknown"
    )
    semantic_key = _optional_text(typed_operation.get("semantic_key"))
    subject_label = _dirty_change_subject_label(
        subject_kind=subject_kind,
        current=current,
        baseline=baseline,
        semantic_key=semantic_key,
    )
    description = _dirty_change_subject_description(
        subject_kind=subject_kind,
        current=current,
        baseline=baseline,
    )
    summary = _dirty_change_summary(
        context_label=_dirty_change_context_label(current=current),
        operation_family=operation_family,
        subject_kind=subject_kind,
        subject_label=subject_label,
        description=description,
    )
    return {
        "change_kind": "meta_ocg_provider_delta_semantic_world_change",
        "contract_version": (
            META_PROVIDER_DELTA_SEMANTIC_WORLD_CHANGE_CONTRACT_VERSION
        ),
        "change_key": (
            "aware_meta.provider_delta.world_change."
            f"{subject_kind}.{operation_family}"
        ),
        "change_type": "semantic_world_change_preview",
        "summary": summary,
        "narrative": summary,
        "world_change": summary,
        "semantic_key": semantic_key,
        "verb": operation_family,
        "subject_type": _optional_text(typed_operation.get("semantic_subject_type")),
        "ontology_subject_kind": subject_kind,
        "subject_label": subject_label,
        "subject_description": description,
        "provider_operation_type": _optional_text(
            typed_operation.get("provider_operation_type")
        ),
        "source": "aware_meta.provider_delta.semantic_dirty_diff",
        "source_refs": _tuple_text(typed_operation.get("source_refs")),
        "delta_keys": _dirty_change_delta_keys(typed_operation=typed_operation),
        "condition_keys": (
            "meta.provider_delta.semantic_dirty_diff_ready",
            "meta.provider_delta.typed_operation_plan_ready",
            f"meta.provider_delta.operation_family.{operation_family}",
            f"meta.provider_delta.subject_kind.{subject_kind}",
        ),
        "baseline": baseline,
        "current": current,
        "ocg_operation": _mapping_value(typed_operation.get("ocg_operation")),
    }


def _provider_delta_semantic_commit_evidence(
    *,
    provider_delta_typed_operation_plan: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
    provider_delta_head_move_applied_receipt: Mapping[str, object],
    provider_delta_oig_commit_receipt: Mapping[str, object],
) -> dict[str, object]:
    typed_status = _optional_text(provider_delta_typed_operation_plan.get("status"))
    head_move_status = _optional_text(provider_delta_head_move_plan.get("status"))
    applied_receipt_status = _optional_text(
        provider_delta_head_move_applied_receipt.get("status")
    )
    commit_status = _optional_text(provider_delta_oig_commit_receipt.get("status"))
    blockers = _semantic_commit_evidence_blockers(
        typed_status=typed_status,
        head_move_status=head_move_status,
        applied_receipt_status=applied_receipt_status,
        commit_status=commit_status,
    )
    typed_operations = tuple(
        _mapping_value(operation)
        for operation in _tuple_evidence(
            provider_delta_typed_operation_plan.get("typed_operations")
        )
        if isinstance(operation, Mapping)
    )
    committable_operations = tuple(
        operation
        for operation in typed_operations
        if _optional_text(operation.get("operation_family"))
        in {"create", "update", "delete"}
    )
    if (
        not blockers
        and not committable_operations
        and commit_status == ("execute_flag_commit_noop")
    ):
        return _provider_delta_semantic_commit_evidence_payload(
            status="semantic_commit_evidence_ready",
            reason="meta_ocg_provider_delta_semantic_commit_evidence_noop",
            blockers=(),
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            provider_delta_head_move_plan=provider_delta_head_move_plan,
            provider_delta_head_move_applied_receipt=(
                provider_delta_head_move_applied_receipt
            ),
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
            committed_semantic_changes=(),
        )
    if not blockers and not committable_operations:
        blockers = ("committed_semantic_changes_empty",)
    if blockers:
        return _provider_delta_semantic_commit_evidence_payload(
            status="semantic_commit_evidence_blocked",
            reason="meta_ocg_provider_delta_semantic_commit_evidence_blocked",
            blockers=blockers,
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            provider_delta_head_move_plan=provider_delta_head_move_plan,
            provider_delta_head_move_applied_receipt=(
                provider_delta_head_move_applied_receipt
            ),
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
            committed_semantic_changes=(),
        )

    committed_changes = tuple(
        _committed_semantic_change_from_typed_operation(
            typed_operation=operation,
            provider_delta_head_move_applied_receipt=(
                provider_delta_head_move_applied_receipt
            ),
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
        )
        for operation in committable_operations
    )
    return _provider_delta_semantic_commit_evidence_payload(
        status="semantic_commit_evidence_ready",
        reason="meta_ocg_provider_delta_semantic_commit_evidence_ready",
        blockers=(),
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        provider_delta_head_move_plan=provider_delta_head_move_plan,
        provider_delta_head_move_applied_receipt=(
            provider_delta_head_move_applied_receipt
        ),
        provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
        committed_semantic_changes=committed_changes,
    )


def _semantic_commit_evidence_blockers(
    *,
    typed_status: str | None,
    head_move_status: str | None,
    applied_receipt_status: str | None,
    commit_status: str | None,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if typed_status != "typed_operation_plan_ready":
        blockers.append(f"typed_operation_plan_not_ready:{typed_status or 'unknown'}")
    if commit_status not in {
        "execute_flag_commit_applied",
        "execute_flag_commit_noop",
    }:
        blockers.append(f"oig_commit_not_applied:{commit_status or 'unknown'}")
    if head_move_status != "head_move_applied":
        blockers.append(f"head_move_not_applied:{head_move_status or 'unknown'}")
    if applied_receipt_status != "head_move_applied_receipt_ready":
        blockers.append(
            "head_move_applied_receipt_not_ready:"
            f"{applied_receipt_status or 'unknown'}"
        )
    return tuple(blockers)


def _provider_delta_semantic_commit_evidence_payload(
    *,
    status: str,
    reason: str,
    blockers: tuple[str, ...],
    provider_delta_typed_operation_plan: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
    provider_delta_head_move_applied_receipt: Mapping[str, object],
    provider_delta_oig_commit_receipt: Mapping[str, object],
    committed_semantic_changes: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    available = status == "semantic_commit_evidence_ready"
    return {
        "plan_kind": "meta_ocg_provider_delta_semantic_commit_evidence",
        "contract_version": (
            META_PROVIDER_DELTA_SEMANTIC_COMMIT_EVIDENCE_CONTRACT_VERSION
        ),
        "change_contract_version": (
            META_PROVIDER_DELTA_COMMITTED_SEMANTIC_CHANGE_CONTRACT_VERSION
        ),
        "status": status,
        "reason": reason,
        "source": "aware_meta.provider_delta.oig_commit",
        "provider_key": _SUPPORTED_DELTA_PROVIDER_KEY,
        "provider_delta_typed_operation_status": _optional_text(
            provider_delta_typed_operation_plan.get("status")
        ),
        "provider_delta_head_move_status": _optional_text(
            provider_delta_head_move_plan.get("status")
        ),
        "provider_delta_head_move_applied_receipt_status": _optional_text(
            provider_delta_head_move_applied_receipt.get("status")
        ),
        "provider_delta_oig_commit_receipt_status": _optional_text(
            provider_delta_oig_commit_receipt.get("status")
        ),
        "provider_delta_oig_commit_receipt_commit_id": _optional_text(
            provider_delta_oig_commit_receipt.get("commit_id")
        ),
        "committed_semantic_change_count": len(committed_semantic_changes),
        "committed_semantic_changes": committed_semantic_changes,
        "change_type_counts": _typed_operation_count_by_field(
            operations=committed_semantic_changes,
            field_name="change_type",
        ),
        "change_key_counts": _typed_operation_count_by_field(
            operations=committed_semantic_changes,
            field_name="change_key",
        ),
        "operation_family_counts": _typed_operation_count_by_field(
            operations=committed_semantic_changes,
            field_name="verb",
        ),
        "available": available,
        "blocked": not available,
        "blockers": blockers,
        "blocker_count": len(blockers),
    }


def _committed_semantic_change_from_typed_operation(
    *,
    typed_operation: Mapping[str, object],
    provider_delta_head_move_applied_receipt: Mapping[str, object],
    provider_delta_oig_commit_receipt: Mapping[str, object],
) -> dict[str, object]:
    projection = _mapping_value(typed_operation.get("semantic_change_projection"))
    source_change = _mapping_value(typed_operation.get("source_semantic_change"))
    head_refs = _mapping_value(
        provider_delta_head_move_applied_receipt.get("head_refs")
    )
    operation_family = _optional_text(typed_operation.get("operation_family")) or (
        "unknown"
    )
    subject_kind = _optional_text(typed_operation.get("ontology_subject_kind")) or (
        "unknown"
    )
    source_change_key = (
        _optional_text(projection.get("change_key"))
        or f"aware_meta.provider_delta.{subject_kind}.{operation_family}"
    )
    source_delta_key = _optional_text(typed_operation.get("source_delta_key"))
    delta_keys = _tuple_text(projection.get("delta_keys")) or (
        (source_delta_key,) if source_delta_key is not None else ()
    )
    condition_keys = tuple(
        dict.fromkeys(
            (
                *_tuple_text(projection.get("condition_keys")),
                "meta.provider_delta.oig_commit_applied",
                "meta.provider_delta.head_move_applied",
                f"meta.provider_delta.operation_family.{operation_family}",
                f"meta.provider_delta.subject_kind.{subject_kind}",
            )
        )
    )
    return {
        "change_kind": "meta_ocg_provider_delta_committed_semantic_change",
        "contract_version": (
            META_PROVIDER_DELTA_COMMITTED_SEMANTIC_CHANGE_CONTRACT_VERSION
        ),
        "change_key": f"{source_change_key}.committed",
        "change_type": "semantic_operation_committed",
        "semantic_key": _optional_text(typed_operation.get("semantic_key")),
        "verb": operation_family,
        "subject_type": _optional_text(typed_operation.get("semantic_subject_type")),
        "ontology_subject_kind": subject_kind,
        "provider_operation_type": _optional_text(
            typed_operation.get("provider_operation_type")
        ),
        "source": "aware_meta.provider_delta.oig_commit",
        "source_change_key": _optional_text(source_change.get("change_key")),
        "source_refs": _tuple_text(typed_operation.get("source_refs")),
        "delta_keys": delta_keys,
        "condition_keys": condition_keys,
        "payload": _mapping_value(projection.get("payload"))
        or _mapping_value(typed_operation.get("current")),
        "baseline": _mapping_value(typed_operation.get("baseline")),
        "current": _mapping_value(typed_operation.get("current")),
        "ocg_operation": _mapping_value(typed_operation.get("ocg_operation")),
        "head_refs": head_refs,
        "commit_ref": {
            "commit_id": _optional_text(
                provider_delta_oig_commit_receipt.get("commit_id")
            ),
            "branch_id": _optional_text(
                provider_delta_oig_commit_receipt.get("branch_id")
            ),
            "projection_hash": _optional_text(
                provider_delta_oig_commit_receipt.get("projection_hash")
            ),
            "object_instance_graph_id": _optional_text(
                provider_delta_oig_commit_receipt.get("object_instance_graph_id")
            ),
            "object_instance_graph_identity_id": _optional_text(
                provider_delta_oig_commit_receipt.get(
                    "object_instance_graph_identity_id"
                )
            ),
            "graph_hash_pre": _optional_text(
                provider_delta_oig_commit_receipt.get("graph_hash_pre")
            ),
            "graph_hash_post": _optional_text(
                provider_delta_oig_commit_receipt.get("graph_hash_post")
            ),
        },
        "metadata": {
            "typed_operation_key": _optional_text(typed_operation.get("operation_key")),
            "source_semantic_change": source_change if source_change else None,
            "head_move_applied_receipt_status": _optional_text(
                provider_delta_head_move_applied_receipt.get("status")
            ),
        },
    }


def _dirty_change_context_label(*, current: Mapping[str, object]) -> str:
    payload = _mapping_value(current.get("payload"))
    package_name = _optional_text(payload.get("package_name"))
    if package_name is None:
        graph_fqn = _graph_fqn_from_semantic_key(
            _optional_text(current.get("semantic_key"))
        )
        if graph_fqn is not None:
            return f"{_human_graph_label(graph_fqn)} ontology"
    if package_name is None:
        return "Semantic workspace"
    words = package_name.replace("_", "-").split("-")
    if words and words[-1] == "ontology":
        return f"{' '.join(words[:-1]).title()} ontology".strip()
    return package_name.replace("-", " ").title()


def _dirty_change_subject_label(
    *,
    subject_kind: str,
    current: Mapping[str, object],
    baseline: Mapping[str, object],
    semantic_key: str | None,
) -> str:
    if subject_kind == "attribute":
        attribute_name = (
            _optional_text(current.get("attribute_name"))
            or _optional_text(
                _mapping_value(baseline.get("object")).get("attribute_name")
            )
            or _attribute_name_from_semantic_key(semantic_key)
            or "unknown"
        )
        owner_label = _class_label_from_semantic_key(
            _optional_text(current.get("owner_semantic_key"))
            or _optional_text(current.get("parent_semantic_key"))
            or _optional_text(
                _mapping_value(baseline.get("object")).get("owner_semantic_key")
            )
            or _parent_semantic_key_from_attribute_key(semantic_key)
        )
        if owner_label is not None:
            return f"attribute `{attribute_name}` on `{owner_label}`"
        return f"attribute `{attribute_name}`"
    if subject_kind == "class":
        return f"class `{_class_label(current=current, semantic_key=semantic_key)}`"
    if subject_kind == "function":
        function_name = (
            _optional_text(current.get("function_name"))
            or _optional_text(current.get("entity_name"))
            or _function_name_from_semantic_key(semantic_key)
            or "unknown"
        )
        owner_label = _class_label_from_semantic_key(
            _optional_text(current.get("owner_semantic_key"))
            or _optional_text(current.get("parent_semantic_key"))
            or _optional_text(
                _mapping_value(baseline.get("object")).get("owner_semantic_key")
            )
            or _parent_semantic_key_from_function_key(semantic_key)
        )
        if owner_label is not None:
            return f"function `{function_name}` on `{owner_label}`"
        return f"function `{function_name}`"
    if subject_kind == "function_impl":
        function_name = (
            _optional_text(current.get("function_name"))
            or _optional_text(
                _mapping_value(baseline.get("object")).get("function_name")
            )
            or _function_name_from_semantic_key(semantic_key)
            or "unknown"
        )
        owner_label = _class_label_from_semantic_key(
            _optional_text(current.get("owner_semantic_key"))
            or _optional_text(
                _mapping_value(baseline.get("object")).get("owner_semantic_key")
            )
            or _parent_semantic_key_from_function_key(semantic_key)
        )
        if owner_label is not None:
            return f"implementation for function `{function_name}` on `{owner_label}`"
        return f"implementation for function `{function_name}`"
    if subject_kind == "relationship":
        relationship_label = (
            _optional_text(current.get("relationship_key"))
            or _optional_text(current.get("entity_name"))
            or _relationship_name_from_semantic_key(semantic_key)
            or "unknown"
        )
        endpoints = _relationship_endpoint_labels(semantic_key=semantic_key)
        if endpoints is not None:
            source_label, target_label = endpoints
            return (
                f"relationship `{relationship_label}` from "
                f"`{source_label}` to `{target_label}`"
            )
        return f"relationship `{relationship_label}`"
    if subject_kind == "object_config_graph":
        payload = _mapping_value(current.get("payload"))
        return (
            f"ontology graph `{_optional_text(payload.get('fqn_prefix')) or 'unknown'}`"
        )
    if subject_kind == "object_config_graph_package":
        payload = _mapping_value(current.get("payload"))
        return f"ontology package `{_optional_text(payload.get('package_name')) or 'unknown'}`"
    return f"{subject_kind} `{semantic_key or 'unknown'}`"


def _dirty_change_summary(
    *,
    context_label: str,
    operation_family: str,
    subject_kind: str,
    subject_label: str,
    description: str | None,
) -> str:
    if operation_family == "create":
        verb = "add"
    elif operation_family == "update":
        verb = "update"
    elif operation_family == "delete":
        verb = "remove"
    else:
        verb = f"{operation_family} change"
    preposition = "from" if operation_family == "delete" else "in"
    if subject_kind in {
        "attribute",
        "class",
        "function",
        "function_impl",
        "relationship",
    }:
        suffix = (
            f" {description}"
            if subject_kind in {"attribute", "function", "function_impl"}
            and description
            else ""
        )
        if operation_family == "create":
            return f"{context_label} will {verb} {subject_label}.{suffix}"
        if operation_family == "delete":
            return f"{context_label} will {verb} {subject_label}.{suffix}"
        return f"{context_label} will {verb} {subject_label}.{suffix}"
    return (
        f"{context_label} will {verb} {subject_label} {preposition} the semantic graph."
    )


def _dirty_change_subject_description(
    *,
    subject_kind: str,
    current: Mapping[str, object],
    baseline: Mapping[str, object],
) -> str | None:
    if subject_kind == "attribute":
        return _dirty_change_attribute_description(current=current, baseline=baseline)
    if subject_kind == "function_impl":
        return _dirty_change_function_impl_description(
            current=current,
            baseline=baseline,
        )
    if subject_kind != "function":
        return None
    current_signature = _mapping_value(current.get("function_signature"))
    baseline_object = _mapping_value(baseline.get("object"))
    baseline_signature = _mapping_value(baseline_object.get("function_signature"))
    return _optional_text(current_signature.get("description")) or _optional_text(
        baseline_signature.get("description")
    )


def _dirty_change_function_impl_description(
    *,
    current: Mapping[str, object],
    baseline: Mapping[str, object],
) -> str | None:
    current_signature = _mapping_value(current.get("function_impl_signature"))
    baseline_object = _mapping_value(baseline.get("object"))
    baseline_signature = _mapping_value(baseline_object.get("function_impl_signature"))
    if not current_signature and not baseline_signature:
        return None
    current_label = _function_impl_body_label(signature=current_signature)
    baseline_label = _function_impl_body_label(signature=baseline_signature)
    if current_label == baseline_label:
        return None
    return f"Body changes from {baseline_label} to {current_label}."


def _function_impl_body_label(*, signature: Mapping[str, object]) -> str:
    summaries = _tuple_text(signature.get("instruction_summaries"))
    if not summaries:
        return "no executable instructions"
    return "`" + "; ".join(summaries) + "`"


def _dirty_change_attribute_description(
    *,
    current: Mapping[str, object],
    baseline: Mapping[str, object],
) -> str | None:
    current_signature = _mapping_value(current.get("attribute_signature"))
    baseline_object = _mapping_value(baseline.get("object"))
    baseline_signature = _mapping_value(baseline_object.get("attribute_signature"))
    if not current_signature or not baseline_signature:
        return None
    current_type = _attribute_type_label(signature=current_signature)
    baseline_type = _attribute_type_label(signature=baseline_signature)
    if current_type is None or baseline_type is None:
        return None
    if current_type == baseline_type:
        return None
    return f"Type changes from `{baseline_type}` to `{current_type}`."


def _attribute_type_label(*, signature: Mapping[str, object]) -> str | None:
    descriptor_kind = _optional_text(signature.get("kind"))
    if descriptor_kind == "primitive":
        label = _primitive_type_label(
            _optional_text(signature.get("primitive_base_type"))
            or _optional_text(signature.get("primitive_signature"))
        )
    elif descriptor_kind == "class":
        label = _short_name(_optional_text(signature.get("class_fqn")) or "class")
    elif descriptor_kind == "enum":
        label = _short_name(_optional_text(signature.get("enum_fqn")) or "enum")
    elif descriptor_kind == "collection":
        label = _collection_type_label(signature=signature)
    else:
        label = descriptor_kind
    if label is None:
        return None
    if signature.get("is_required") is False and not label.endswith("?"):
        return f"{label}?"
    return label


def _collection_type_label(*, signature: Mapping[str, object]) -> str | None:
    collection_kind = _optional_text(signature.get("collection_kind"))
    child_label = None
    child_links = _tuple_evidence(signature.get("child_links"))
    if child_links:
        first_child = _mapping_value(child_links[0])
        child_signature = _mapping_value(first_child.get("child"))
        child_label = _attribute_type_label(signature=child_signature)
    if collection_kind == "list" and child_label is not None:
        return f"{child_label}[]"
    if collection_kind is not None and child_label is not None:
        return f"{collection_kind}<{child_label}>"
    return collection_kind or child_label


def _primitive_type_label(value: str | None) -> str | None:
    if value is None:
        return None
    return {
        "bool": "Bool",
        "boolean": "Bool",
        "datetime": "DateTime",
        "float": "Float",
        "int": "Int",
        "integer": "Int",
        "string": "String",
        "uuid": "UUID",
    }.get(value.lower(), value)


def _dirty_change_delta_keys(
    *,
    typed_operation: Mapping[str, object],
) -> tuple[str, ...]:
    projection = _mapping_value(typed_operation.get("semantic_change_projection"))
    delta_keys = _tuple_text(projection.get("delta_keys"))
    if delta_keys:
        return delta_keys
    source_delta_key = _optional_text(typed_operation.get("source_delta_key"))
    return (source_delta_key,) if source_delta_key is not None else ()


def _class_label(
    *,
    current: Mapping[str, object],
    semantic_key: str | None,
) -> str:
    entity_name = _optional_text(current.get("entity_name"))
    if entity_name is not None:
        return _short_name(entity_name)
    node_key = _optional_text(current.get("node_key"))
    if node_key is not None:
        return _short_name(node_key)
    parsed = _class_label_from_semantic_key(semantic_key)
    return parsed or "unknown"


def _class_label_from_semantic_key(value: str | None) -> str | None:
    if value is None:
        return None
    marker = "/node:"
    if marker in value:
        tail = value.split(marker, 1)[1]
    else:
        tail = value
    tail = tail.split("/attribute:", 1)[0]
    return _short_name(tail)


def _attribute_name_from_semantic_key(value: str | None) -> str | None:
    if value is None or "/attribute:" not in value:
        return None
    return value.rsplit("/attribute:", 1)[1] or None


def _parent_semantic_key_from_attribute_key(value: str | None) -> str | None:
    if value is None or "/attribute:" not in value:
        return None
    return value.rsplit("/attribute:", 1)[0]


def _function_name_from_semantic_key(value: str | None) -> str | None:
    if value is None or "/node:" not in value:
        return None
    node_key = value.split("/node:", 1)[1]
    node_key = node_key.split("/function_impl:", 1)[0]
    if ":" in node_key or "." not in node_key:
        return None
    return node_key.rsplit(".", 1)[1] or None


def _parent_semantic_key_from_function_key(value: str | None) -> str | None:
    if value is None or "/node:" not in value:
        return None
    graph_key, node_key = value.split("/node:", 1)
    node_key = node_key.split("/function_impl:", 1)[0]
    if ":" in node_key or "." not in node_key:
        return None
    owner_key = node_key.rsplit(".", 1)[0]
    return f"{graph_key}/node:{owner_key}"


def _relationship_name_from_semantic_key(value: str | None) -> str | None:
    if value is None or "/node:" not in value:
        return None
    node_key = value.split("/node:", 1)[1]
    parts = node_key.split(":")
    if len(parts) >= 2:
        return parts[1]
    return None


def _relationship_endpoint_labels(
    *,
    semantic_key: str | None,
) -> tuple[str, str] | None:
    if semantic_key is None or "/node:" not in semantic_key:
        return None
    node_key = semantic_key.split("/node:", 1)[1]
    parts = node_key.split(":")
    if len(parts) < 4:
        return None
    return (_short_name(parts[0]), _short_name(parts[3]))


def _short_name(value: str) -> str:
    return value.rsplit(".", 1)[-1]


def _graph_fqn_from_semantic_key(value: str | None) -> str | None:
    if value is None:
        return None
    if not value.startswith("ocg:"):
        return None
    return value.removeprefix("ocg:").split("/", 1)[0] or None


def _human_graph_label(value: str) -> str:
    words = value.replace("_", "-").split("-")
    if words and words[0] == "aware":
        words = words[1:] or words
    return " ".join(words).title()


def _int_payload_value(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def _tuple_evidence(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


__all__ = [
    "_provider_delta_semantic_change_report",
    "_provider_delta_semantic_commit_evidence",
]
