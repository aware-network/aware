from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_reactivity.condition.evaluator import (
    ConditionEvaluationTraceEntry,
    LaneMaterializedConditionEvaluator,
    _AttributePolicy,
    _ClassPolicy,
    _CommitChangeSet,
    _ConditionPolicy,
    _GraphState,
    _PrimitivePolicy,
    _ReceiptContext,
    _RelationshipPolicy,
    _evaluate_operator,
)


def _eval(operator: str, **overrides: object) -> bool:
    args: dict[str, object] = {
        "operator": operator,
        "pre_value": None,
        "post_value": None,
        "pre_exists": False,
        "post_exists": False,
        "changed": False,
        "expected": None,
        "range_min": None,
        "range_max": None,
    }
    args.update(overrides)
    return _evaluate_operator(**args)


@pytest.mark.parametrize(
    ("operator", "kwargs", "expected"),
    [
        ("create", {"pre_exists": False, "post_exists": True}, True),
        ("create", {"pre_exists": True, "post_exists": True}, False),
        ("create", {"pre_exists": False, "post_exists": False}, False),
        ("created", {"pre_exists": False, "post_exists": True}, True),
        ("changed", {"changed": True}, True),
        ("changed", {"changed": False}, False),
        ("not_changed", {"changed": False}, True),
        ("exists", {"post_exists": True}, True),
        ("exists", {"post_exists": False}, False),
        ("not_exists", {"post_exists": False}, True),
        ("is_null", {"post_value": None}, True),
        ("is_not_null", {"post_value": "x"}, True),
    ],
)
def test_evaluate_operator_state_flags(operator: str, kwargs: dict[str, object], expected: bool) -> None:
    assert _eval(operator, **kwargs) is expected


@pytest.mark.parametrize(
    ("operator", "post_value", "expected_value", "expected"),
    [
        ("equals", "10", 10, True),
        ("not_equals", "10", 10, False),
        ("greater_than", "10", 2, True),
        ("greater_or_equal", "10", 10, True),
        ("less_than", "3", 10, True),
        ("less_or_equal", "10", 10, True),
    ],
)
def test_evaluate_operator_numeric_and_coercion(
    operator: str, post_value: object, expected_value: object, expected: bool
) -> None:
    assert _eval(operator, post_value=post_value, expected=expected_value) is expected


def test_evaluate_operator_respects_numeric_range_bounds() -> None:
    assert (
        _eval(
            "equals",
            post_value=5,
            expected=5,
            range_min=1,
            range_max=10,
        )
        is True
    )
    assert (
        _eval(
            "equals",
            post_value=5,
            expected=5,
            range_min=6,
            range_max=10,
        )
        is False
    )
    assert (
        _eval(
            "equals",
            post_value=5,
            expected=5,
            range_min=1,
            range_max=4,
        )
        is False
    )


@pytest.mark.parametrize(
    ("operator", "kwargs", "expected"),
    [
        (
            "contains",
            {"post_value": "conversation.message.created", "expected": "message"},
            True,
        ),
        ("not_contains", {"post_value": [1, 2, 3], "expected": 9}, True),
        ("in", {"post_value": "a", "expected": ["a", "b"]}, True),
        ("not_in", {"post_value": "z", "expected": ["a", "b"]}, True),
        (
            "starts_with",
            {"post_value": "agent.turn.execute", "expected": "agent"},
            True,
        ),
        (
            "ends_with",
            {"post_value": "agent.turn.execute", "expected": "execute"},
            True,
        ),
        (
            "matches_regex",
            {"post_value": "conversation.created", "expected": r"conversation\..+"},
            True,
        ),
        ("matches_regex", {"post_value": "x", "expected": "["}, False),
    ],
)
def test_evaluate_operator_collection_and_string_ops(operator: str, kwargs: dict[str, object], expected: bool) -> None:
    assert _eval(operator, **kwargs) is expected


@pytest.mark.parametrize(
    ("operator", "kwargs"),
    [
        ("contains", {"post_value": "conversation.message.created"}),
        (
            "contains",
            {"post_value": "conversation.message.created", "expected": ""},
        ),
        ("not_contains", {"post_value": "conversation.message.created"}),
        (
            "not_contains",
            {"post_value": "conversation.message.created", "expected": ""},
        ),
        ("starts_with", {"post_value": "agent.turn.execute"}),
        ("starts_with", {"post_value": "agent.turn.execute", "expected": ""}),
        ("ends_with", {"post_value": "agent.turn.execute"}),
        ("ends_with", {"post_value": "agent.turn.execute", "expected": ""}),
        ("matches_regex", {"post_value": "conversation.created"}),
        ("matches_regex", {"post_value": "conversation.created", "expected": ""}),
        ("in", {"post_value": "a"}),
        ("in", {"post_value": "a", "expected": []}),
        ("not_in", {"post_value": "a"}),
        ("not_in", {"post_value": "a", "expected": []}),
    ],
)
def test_evaluate_operator_payload_ops_fail_closed_without_expected_operand(
    operator: str, kwargs: dict[str, object]
) -> None:
    assert _eval(operator, **kwargs) is False


@pytest.mark.parametrize(
    ("operator", "post_value"),
    [
        ("equals", None),
        ("not_equals", "x"),
        ("greater_than", 1),
        ("greater_or_equal", 1),
        ("less_than", 1),
        ("less_or_equal", 1),
    ],
)
def test_evaluate_operator_value_comparisons_fail_closed_without_expected_operand(
    operator: str, post_value: object
) -> None:
    assert _eval(operator, post_value=post_value) is False


def test_evaluate_operator_delta_ops_require_pre_and_post_existence() -> None:
    assert (
        _eval(
            "increased",
            pre_value=1,
            post_value=2,
            pre_exists=True,
            post_exists=True,
        )
        is True
    )
    assert (
        _eval(
            "decreased",
            pre_value=2,
            post_value=1,
            pre_exists=True,
            post_exists=True,
        )
        is True
    )
    assert (
        _eval(
            "increased",
            pre_value=1,
            post_value=2,
            pre_exists=False,
            post_exists=True,
        )
        is False
    )


def test_unknown_operator_fails_closed_even_when_values_match() -> None:
    assert _eval("custom_op", post_value="10", expected=10) is False
    assert _eval("", post_value="10", expected=10) is False


def _graph_state(
    *,
    class_instances: dict[UUID, UUID],
    values: dict[tuple[UUID, UUID], object] | None = None,
    relationships: dict[tuple[UUID, UUID], list[UUID]] | None = None,
) -> _GraphState:
    class_instance_ids_by_class_config: dict[UUID, set[UUID]] = {}
    for instance_id, class_config_id in class_instances.items():
        class_instance_ids_by_class_config.setdefault(class_config_id, set()).add(instance_id)

    value_by_instance_and_config = dict(values or {})
    attribute_id_by_instance_and_config = {key: uuid4() for key in value_by_instance_and_config}
    return _GraphState(
        class_instances_by_id={instance_id: object() for instance_id in class_instances},
        class_instance_ids_by_class_config=class_instance_ids_by_class_config,
        attribute_by_id={},
        attribute_id_by_instance_and_config=attribute_id_by_instance_and_config,
        value_by_instance_and_config=value_by_instance_and_config,
        relationships_by_source_and_config=dict(relationships or {}),
    )


def _change_set(
    *,
    class_instance_ids: set[UUID] | None = None,
    changed_instance_attr_configs: set[tuple[UUID, UUID]] | None = None,
    changed_relationship_keys: set[tuple[UUID, UUID]] | None = None,
) -> _CommitChangeSet:
    return _CommitChangeSet(
        class_instance_ids=set(class_instance_ids or set()),
        changed_attribute_ids=set(),
        changed_instance_attr_configs=set(changed_instance_attr_configs or set()),
        changed_relationship_keys=set(changed_relationship_keys or set()),
    )


def _receipt_context(
    *,
    pre: _GraphState,
    post: _GraphState,
    changes: _CommitChangeSet,
    trigger_candidate_instance_ids: set[UUID],
) -> _ReceiptContext:
    return _ReceiptContext(
        pre=pre,
        post=post,
        changes=changes,
        trigger_candidate_instance_ids=trigger_candidate_instance_ids,
    )


def _evaluator(
    *,
    policies: list[_ConditionPolicy],
    descendants: dict[UUID, set[UUID]],
) -> LaneMaterializedConditionEvaluator:
    evaluator = object.__new__(LaneMaterializedConditionEvaluator)
    evaluator._condition_policies_by_id = {policy.id: policy for policy in policies}
    evaluator._descendants_by_class_config = descendants
    return evaluator


def _trace(
    evaluator: LaneMaterializedConditionEvaluator,
    *,
    condition_id: UUID,
    ctx: _ReceiptContext,
    allowed_instance_ids: set[UUID] | None = None,
) -> tuple[bool, tuple[ConditionEvaluationTraceEntry, ...]]:
    entries: list[ConditionEvaluationTraceEntry] = []
    result = evaluator._evaluate_condition_policy_trace(
        condition_config_id=condition_id,
        ctx=ctx,
        allowed_instance_ids=allowed_instance_ids,
        visited=set(),
        entries=entries,
        path="test",
    )
    return result, tuple(entries)


def _entries_by_kind(
    entries: tuple[ConditionEvaluationTraceEntry, ...], kind: str
) -> list[ConditionEvaluationTraceEntry]:
    return [entry for entry in entries if entry.kind == kind]


def _status_condition(
    *,
    condition_id: UUID,
    class_config_id: UUID,
    attribute_config_id: UUID,
    expected: object,
) -> _ConditionPolicy:
    return _ConditionPolicy(
        id=condition_id,
        is_enabled=True,
        logic_strategy="all",
        classes=(
            _ClassPolicy(
                id=uuid4(),
                class_config_id=class_config_id,
                class_selection="specific_class",
                class_logic="all",
                require_existence=True,
                attributes=(
                    _AttributePolicy(
                        id=uuid4(),
                        attribute_config_id=attribute_config_id,
                        operator="equals",
                        negate=False,
                        primitive=_PrimitivePolicy(
                            primitive_value=expected,
                            range_min=None,
                            range_max=None,
                        ),
                        enum=None,
                        relationship=None,
                    ),
                ),
            ),
        ),
    )


def test_condition_static_predicates_are_scoped_to_trigger_candidates() -> None:
    class_config_id = uuid4()
    status_attr_id = uuid4()
    condition_id = uuid4()
    active_instance_id = uuid4()
    changed_instance_id = uuid4()
    pre = _graph_state(
        class_instances={
            active_instance_id: class_config_id,
            changed_instance_id: class_config_id,
        },
        values={
            (active_instance_id, status_attr_id): "active",
            (changed_instance_id, status_attr_id): "idle",
        },
    )
    post = _graph_state(
        class_instances={
            active_instance_id: class_config_id,
            changed_instance_id: class_config_id,
        },
        values={
            (active_instance_id, status_attr_id): "active",
            (changed_instance_id, status_attr_id): "idle",
        },
    )
    ctx = _receipt_context(
        pre=pre,
        post=post,
        changes=_change_set(
            class_instance_ids={changed_instance_id},
            changed_instance_attr_configs={(changed_instance_id, status_attr_id)},
        ),
        trigger_candidate_instance_ids={changed_instance_id},
    )
    policy = _status_condition(
        condition_id=condition_id,
        class_config_id=class_config_id,
        attribute_config_id=status_attr_id,
        expected="active",
    )
    evaluator = _evaluator(
        policies=[policy],
        descendants={class_config_id: {class_config_id}},
    )

    assert (
        evaluator._evaluate_condition_policy(
            condition_config_id=condition_id,
            ctx=ctx,
            allowed_instance_ids=None,
            visited=set(),
        )
        is False
    )


def test_condition_trace_records_trigger_scope_skipped_candidates() -> None:
    class_config_id = uuid4()
    status_attr_id = uuid4()
    condition_id = uuid4()
    active_instance_id = uuid4()
    changed_instance_id = uuid4()
    state = _graph_state(
        class_instances={
            active_instance_id: class_config_id,
            changed_instance_id: class_config_id,
        },
        values={
            (active_instance_id, status_attr_id): "active",
            (changed_instance_id, status_attr_id): "idle",
        },
    )
    ctx = _receipt_context(
        pre=state,
        post=state,
        changes=_change_set(changed_instance_attr_configs={(changed_instance_id, status_attr_id)}),
        trigger_candidate_instance_ids={changed_instance_id},
    )
    policy = _status_condition(
        condition_id=condition_id,
        class_config_id=class_config_id,
        attribute_config_id=status_attr_id,
        expected="active",
    )
    evaluator = _evaluator(
        policies=[policy],
        descendants={class_config_id: {class_config_id}},
    )

    result, entries = _trace(evaluator, condition_id=condition_id, ctx=ctx)

    assert result is False
    class_entry = _entries_by_kind(entries, "class")[-1]
    assert class_entry.reason == "logic_all"
    assert class_entry.metadata["scope_reason"] == "trigger_candidate_scope"
    assert str(active_instance_id) in class_entry.metadata["base_candidate_instance_ids"]
    assert str(active_instance_id) not in class_entry.metadata["scoped_candidate_instance_ids"]
    assert class_entry.metadata["scoped_candidate_instance_ids"] == [str(changed_instance_id)]


def test_trigger_candidate_scope_collects_root_changes_and_relationship_endpoints() -> None:
    class_config_id = uuid4()
    status_attr_id = uuid4()
    relationship_config_id = uuid4()
    root_instance_id = uuid4()
    changed_instance_id = uuid4()
    source_instance_id = uuid4()
    old_target_instance_id = uuid4()
    new_target_instance_id = uuid4()
    pre = _graph_state(
        class_instances={
            root_instance_id: class_config_id,
            changed_instance_id: class_config_id,
            source_instance_id: class_config_id,
            old_target_instance_id: class_config_id,
        },
        relationships={(source_instance_id, relationship_config_id): [old_target_instance_id]},
    )
    post = _graph_state(
        class_instances={
            root_instance_id: class_config_id,
            changed_instance_id: class_config_id,
            source_instance_id: class_config_id,
            new_target_instance_id: class_config_id,
        },
        relationships={(source_instance_id, relationship_config_id): [new_target_instance_id]},
    )
    candidates = LaneMaterializedConditionEvaluator._trigger_candidate_instance_ids(
        receipt_root_object_id=root_instance_id,
        pre=pre,
        post=post,
        changes=_change_set(
            class_instance_ids={changed_instance_id},
            changed_instance_attr_configs={(changed_instance_id, status_attr_id)},
            changed_relationship_keys={(source_instance_id, relationship_config_id)},
        ),
    )

    assert candidates == {
        root_instance_id,
        changed_instance_id,
        source_instance_id,
        old_target_instance_id,
        new_target_instance_id,
    }


def test_condition_static_predicates_can_match_receipt_root_candidate() -> None:
    class_config_id = uuid4()
    status_attr_id = uuid4()
    condition_id = uuid4()
    root_instance_id = uuid4()
    state = _graph_state(
        class_instances={root_instance_id: class_config_id},
        values={(root_instance_id, status_attr_id): "active"},
    )
    ctx = _receipt_context(
        pre=state,
        post=state,
        changes=_change_set(),
        trigger_candidate_instance_ids={root_instance_id},
    )
    policy = _status_condition(
        condition_id=condition_id,
        class_config_id=class_config_id,
        attribute_config_id=status_attr_id,
        expected="active",
    )
    evaluator = _evaluator(
        policies=[policy],
        descendants={class_config_id: {class_config_id}},
    )

    assert (
        evaluator._evaluate_condition_policy(
            condition_config_id=condition_id,
            ctx=ctx,
            allowed_instance_ids=None,
            visited=set(),
        )
        is True
    )


def test_condition_candidates_include_pre_state_for_deleted_root_not_exists() -> None:
    class_config_id = uuid4()
    status_attr_id = uuid4()
    condition_id = uuid4()
    deleted_instance_id = uuid4()
    pre = _graph_state(
        class_instances={deleted_instance_id: class_config_id},
        values={(deleted_instance_id, status_attr_id): "active"},
    )
    post = _graph_state(class_instances={})
    ctx = _receipt_context(
        pre=pre,
        post=post,
        changes=_change_set(class_instance_ids={deleted_instance_id}),
        trigger_candidate_instance_ids={deleted_instance_id},
    )
    policy = _ConditionPolicy(
        id=condition_id,
        is_enabled=True,
        logic_strategy="all",
        classes=(
            _ClassPolicy(
                id=uuid4(),
                class_config_id=class_config_id,
                class_selection="specific_class",
                class_logic="all",
                require_existence=True,
                attributes=(
                    _AttributePolicy(
                        id=uuid4(),
                        attribute_config_id=status_attr_id,
                        operator="not_exists",
                        negate=False,
                        primitive=None,
                        enum=None,
                        relationship=None,
                    ),
                ),
            ),
        ),
    )
    evaluator = _evaluator(
        policies=[policy],
        descendants={class_config_id: {class_config_id}},
    )

    assert (
        evaluator._evaluate_condition_policy(
            condition_config_id=condition_id,
            ctx=ctx,
            allowed_instance_ids=None,
            visited=set(),
        )
        is True
    )


def test_condition_trace_records_deleted_root_not_exists() -> None:
    class_config_id = uuid4()
    status_attr_id = uuid4()
    condition_id = uuid4()
    deleted_instance_id = uuid4()
    pre = _graph_state(
        class_instances={deleted_instance_id: class_config_id},
        values={(deleted_instance_id, status_attr_id): "active"},
    )
    post = _graph_state(class_instances={})
    ctx = _receipt_context(
        pre=pre,
        post=post,
        changes=_change_set(class_instance_ids={deleted_instance_id}),
        trigger_candidate_instance_ids={deleted_instance_id},
    )
    policy = _ConditionPolicy(
        id=condition_id,
        is_enabled=True,
        logic_strategy="all",
        classes=(
            _ClassPolicy(
                id=uuid4(),
                class_config_id=class_config_id,
                class_selection="specific_class",
                class_logic="all",
                require_existence=True,
                attributes=(
                    _AttributePolicy(
                        id=uuid4(),
                        attribute_config_id=status_attr_id,
                        operator="not_exists",
                        negate=False,
                        primitive=None,
                        enum=None,
                        relationship=None,
                    ),
                ),
            ),
        ),
    )
    evaluator = _evaluator(
        policies=[policy],
        descendants={class_config_id: {class_config_id}},
    )

    result, entries = _trace(evaluator, condition_id=condition_id, ctx=ctx)

    assert result is True
    attribute_entry = _entries_by_kind(entries, "attribute")[0]
    assert attribute_entry.reason == "operator"
    assert attribute_entry.result is True
    assert attribute_entry.metadata["pre_exists"] is True
    assert attribute_entry.metadata["post_exists"] is False
    assert attribute_entry.metadata["pre_value"] == "active"
    assert attribute_entry.metadata["post_value"] is None


def test_nested_relationship_condition_targets_bypass_top_level_trigger_scope() -> None:
    source_class_id = uuid4()
    target_class_id = uuid4()
    status_attr_id = uuid4()
    relationship_attr_id = uuid4()
    relationship_config_id = uuid4()
    source_condition_id = uuid4()
    target_condition_id = uuid4()
    source_instance_id = uuid4()
    target_instance_id = uuid4()
    post = _graph_state(
        class_instances={
            source_instance_id: source_class_id,
            target_instance_id: target_class_id,
        },
        values={(target_instance_id, status_attr_id): "active"},
        relationships={(source_instance_id, relationship_config_id): [target_instance_id]},
    )
    ctx = _receipt_context(
        pre=_graph_state(class_instances={}),
        post=post,
        changes=_change_set(class_instance_ids={source_instance_id}),
        trigger_candidate_instance_ids={source_instance_id},
    )
    target_policy = _status_condition(
        condition_id=target_condition_id,
        class_config_id=target_class_id,
        attribute_config_id=status_attr_id,
        expected="active",
    )
    source_policy = _ConditionPolicy(
        id=source_condition_id,
        is_enabled=True,
        logic_strategy="all",
        classes=(
            _ClassPolicy(
                id=uuid4(),
                class_config_id=source_class_id,
                class_selection="specific_class",
                class_logic="all",
                require_existence=True,
                attributes=(
                    _AttributePolicy(
                        id=uuid4(),
                        attribute_config_id=relationship_attr_id,
                        operator="equals",
                        negate=False,
                        primitive=None,
                        enum=None,
                        relationship=_RelationshipPolicy(
                            class_config_relationship_id=relationship_config_id,
                            eval_mode="any_match",
                            count_threshold=None,
                            nested_condition_config_id=target_condition_id,
                        ),
                    ),
                ),
            ),
        ),
    )
    evaluator = _evaluator(
        policies=[source_policy, target_policy],
        descendants={
            source_class_id: {source_class_id},
            target_class_id: {target_class_id},
        },
    )

    assert (
        evaluator._evaluate_condition_policy(
            condition_config_id=source_condition_id,
            ctx=ctx,
            allowed_instance_ids=None,
            visited=set(),
        )
        is True
    )


def test_condition_trace_records_nested_relationship_target_scope() -> None:
    source_class_id = uuid4()
    target_class_id = uuid4()
    status_attr_id = uuid4()
    relationship_attr_id = uuid4()
    relationship_config_id = uuid4()
    source_condition_id = uuid4()
    target_condition_id = uuid4()
    source_instance_id = uuid4()
    target_instance_id = uuid4()
    post = _graph_state(
        class_instances={
            source_instance_id: source_class_id,
            target_instance_id: target_class_id,
        },
        values={(target_instance_id, status_attr_id): "active"},
        relationships={(source_instance_id, relationship_config_id): [target_instance_id]},
    )
    ctx = _receipt_context(
        pre=_graph_state(class_instances={}),
        post=post,
        changes=_change_set(class_instance_ids={source_instance_id}),
        trigger_candidate_instance_ids={source_instance_id},
    )
    target_policy = _status_condition(
        condition_id=target_condition_id,
        class_config_id=target_class_id,
        attribute_config_id=status_attr_id,
        expected="active",
    )
    source_policy = _ConditionPolicy(
        id=source_condition_id,
        is_enabled=True,
        logic_strategy="all",
        classes=(
            _ClassPolicy(
                id=uuid4(),
                class_config_id=source_class_id,
                class_selection="specific_class",
                class_logic="all",
                require_existence=True,
                attributes=(
                    _AttributePolicy(
                        id=uuid4(),
                        attribute_config_id=relationship_attr_id,
                        operator="equals",
                        negate=False,
                        primitive=None,
                        enum=None,
                        relationship=_RelationshipPolicy(
                            class_config_relationship_id=relationship_config_id,
                            eval_mode="any_match",
                            count_threshold=None,
                            nested_condition_config_id=target_condition_id,
                        ),
                    ),
                ),
            ),
        ),
    )
    evaluator = _evaluator(
        policies=[source_policy, target_policy],
        descendants={
            source_class_id: {source_class_id},
            target_class_id: {target_class_id},
        },
    )

    result, entries = _trace(evaluator, condition_id=source_condition_id, ctx=ctx)

    assert result is True
    relationship_entry = [
        entry for entry in _entries_by_kind(entries, "relationship") if entry.reason == "relationship_nested_any_match"
    ][0]
    assert relationship_entry.metadata["target_instance_ids"] == [str(target_instance_id)]
    target_class_entry = [
        entry
        for entry in _entries_by_kind(entries, "class")
        if entry.metadata.get("class_config_id") == str(target_class_id)
    ][0]
    assert target_class_entry.metadata["scope_reason"] == "relationship_target_scope"
    assert target_class_entry.metadata["scoped_candidate_instance_ids"] == [str(target_instance_id)]


def test_condition_trace_records_sequence_as_ordered_all() -> None:
    class_config_id = uuid4()
    status_attr_id = uuid4()
    condition_id = uuid4()
    root_instance_id = uuid4()
    state = _graph_state(
        class_instances={root_instance_id: class_config_id},
        values={(root_instance_id, status_attr_id): "active"},
    )
    ctx = _receipt_context(
        pre=state,
        post=state,
        changes=_change_set(),
        trigger_candidate_instance_ids={root_instance_id},
    )
    policy = _status_condition(
        condition_id=condition_id,
        class_config_id=class_config_id,
        attribute_config_id=status_attr_id,
        expected="active",
    )
    policy = _ConditionPolicy(
        id=policy.id,
        is_enabled=policy.is_enabled,
        logic_strategy="sequence",
        classes=policy.classes,
    )
    evaluator = _evaluator(
        policies=[policy],
        descendants={class_config_id: {class_config_id}},
    )

    result, entries = _trace(evaluator, condition_id=condition_id, ctx=ctx)

    assert result is True
    condition_entry = _entries_by_kind(entries, "condition")[-1]
    assert condition_entry.reason == "sequence_ordered_all"
    assert condition_entry.metadata["logic_strategy"] == "sequence"
