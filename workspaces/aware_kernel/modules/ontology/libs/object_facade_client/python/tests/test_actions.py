"""Instance operation consistency/lifetime tests; no evaluator or store proof."""

import asyncio
import time
from dataclasses import replace

import pytest
from aware_meta_type_schema import TypeDefinition, TypeKind, TypeSchemaBundle
from aware_ontology_object_facade_client import owner_values as v
from aware_ontology_object_facade_client.actions import (
    ObjectActionContext,
    ObjectActionError,
    ObjectActionReceipt,
    ObjectActionResult,
    OntologyObjectActions,
)

DIGEST = "sha256:" + "d" * 64
TYPE = "workflow.Issue"
ACTION = TYPE + ".start_progress"


def fixture(
    *, parameters=(), result_shape=None, result_value_mode=v.ActionValueMode.VALUE
):
    enum = TypeDefinition(
        "workflow.IssueStatus",
        "IssueStatus",
        TypeKind.ENUM,
        enum_values=("open", "in_progress", "blocked", "closed"),
    )
    schema = TypeSchemaBundle.create(
        namespace="workflow", semantic_version="1", types=(enum,)
    )
    binding = v.OntologyObjectClassBinding.create(
        type_ref=TYPE,
        class_name="Issue",
        relationships=(),
        fields=(
            v.OntologyObjectFieldBinding(
                TYPE + ".status",
                "status",
                v.ValueShape.named(enum.type_ref),
                True,
                False,
            ),
        ),
        actions=(v.OntologyObjectActionBinding(ACTION, "start_progress", parameters),),
    )
    definition = v.SchemaActionDefinition(
        ACTION,
        TYPE,
        tuple(
            v.SchemaActionParameterDefinition(
                p.parameter_ref,
                p.position,
                p.shape,
                p.required,
                p.nullable,
                p.value_mode,
            )
            for p in parameters
        ),
        result_shape,
        result_value_mode=result_value_mode,
    )

    class Port:
        def __init__(self):
            self.calls = []
            self.failure = None
            self.change = None

        async def invoke_action(self, request):
            self.calls.append(request)
            if self.failure:
                raise self.failure
            result = ObjectActionResult(
                request,
                ObjectActionReceipt(
                    "invocation:1",
                    "attempt:1",
                    DIGEST,
                    "committed",
                    "R1",
                    "R2",
                    None,
                ),
                b"original-history",
                True,
                True,
                True,
            )
            return self.change(result) if self.change else result

    port = Port()
    context = ObjectActionContext(
        binding,
        schema,
        (definition,),
        DIGEST,
        "provider",
        "generation",
        "branch",
        "projection",
        b"original-config",
        port,
    )

    class Issue(OntologyObjectActions):
        __ontology_type_ref__ = TYPE
        __ontology_binding_digest__ = binding.binding_digest
        __ontology_dependency_closure_digest__ = DIGEST
        __ontology_schema_digest__ = schema.schema_digest
        __ontology_action_bindings__ = ((ACTION, "start_progress"),)

        async def start_progress(self):
            return await self._invoke_action(ACTION)

    target = v.OntologyRuntimeActionInstanceRefTarget(
        TYPE, "provider", "generation", "issue:1"
    )
    return context, port, Issue, target


def operation(context, cls, target, **changes):
    kwargs = {
        "action_ref": ACTION,
        "invocation_key": "business:1",
        "expected_revision_ref": "R1",
        "deadline": time.monotonic() + 30.0,
    }
    kwargs.update(changes)
    return context.bind(cls, target, **kwargs)


def test_receiver_result_uses_original_returned_reference_and_preserves_settlement():
    from dataclasses import FrozenInstanceError

    context, port, cls, target = fixture(
        result_shape=v.ValueShape.named(TYPE),
        result_value_mode=v.ActionValueMode.INSTANCE_REF,
    )
    original = replace(target)
    port.change = lambda result: replace(result, returned_object=original)
    obj = operation(context, cls, target)
    returned = asyncio.run(obj.start_progress())
    assert returned.object_reference is original and original is not target
    assert returned.invocation_receipt is obj.invocation_receipt
    assert returned.history_correspondence == b"original-history"
    assert obj.invocation_state == "complete" and len(port.calls) == 1
    assert not hasattr(returned, "status") and not hasattr(returned, "start_progress")
    with pytest.raises(FrozenInstanceError):
        returned.object_reference = target
    with pytest.raises(ObjectActionError, match="operation_consumed"):
        asyncio.run(obj.start_progress())


@pytest.mark.parametrize(
    "change",
    [
        None,
        {},
        {"type_ref": "other.Type"},
        {"provider_key": "other"},
        {"provider_generation": "other"},
        {"instance_ref": "other"},
    ],
)
def test_missing_or_foreign_receiver_result_refuses_and_retains_known_commit(change):
    context, port, cls, target = fixture(
        result_shape=v.ValueShape.named(TYPE),
        result_value_mode=v.ActionValueMode.INSTANCE_REF,
    )
    value = (
        None
        if change is None
        else "not-an-original-target"
        if change == {}
        else replace(target, **change)
    )
    port.change = lambda result: replace(result, returned_object=value)
    obj = operation(context, cls, target)
    with pytest.raises(ObjectActionError, match="invalid_returned_object") as caught:
        asyncio.run(obj.start_progress())
    assert caught.value.recovery_ref == "attempt:1"
    assert obj.invocation_receipt.result_revision_ref == "R2"
    assert obj.invocation_state == "failed" and len(port.calls) == 1


def test_void_result_cannot_silently_discard_an_object():
    context, port, cls, target = fixture()
    port.change = lambda result: replace(result, returned_object=target)
    obj = operation(context, cls, target)
    with pytest.raises(ObjectActionError, match="unexpected_returned_object") as caught:
        asyncio.run(obj.start_progress())
    assert caught.value.recovery_ref == "attempt:1"
    assert obj.invocation_receipt.result_revision_ref == "R2"


@pytest.mark.parametrize(
    "shape,mode",
    [
        (v.ValueShape.named(TYPE), v.ActionValueMode.VALUE),
        (v.ValueShape.named("other.Type"), v.ActionValueMode.INSTANCE_REF),
    ],
)
def test_non_receiver_object_profiles_refuse_before_contact(shape, mode):
    with pytest.raises(ObjectActionError, match="unsupported_profile"):
        fixture(result_shape=shape, result_value_mode=mode)


def parameter(
    name="number",
    *,
    kind=v.ScalarKind.INTEGER,
    required=True,
    nullable=False,
    shape=None,
):
    return v.OntologyObjectActionParameterBinding(
        ACTION + "." + name,
        0,
        shape or v.ValueShape.scalar(kind),
        required,
        nullable,
        v.ActionValueMode.VALUE,
    )


def test_instance_action_has_fields_but_never_reads_them_and_retains_original_receipt():
    context, port, cls, target = fixture()
    obj = operation(context, cls, target)
    assert port.calls == [] and not hasattr(obj, "status")
    assert asyncio.run(obj.start_progress()) is None
    assert obj.invocation_state == "complete" and obj.object_reference is target
    assert obj.invocation_receipt.result_revision_ref == "R2"
    assert obj.invocation_receipt.canonical_commit_ref is None
    assert obj.invocation_result.history_correspondence == b"original-history"
    request = port.calls[0]
    assert (
        request.target,
        request.expected_revision_ref,
        request.configuration_binding,
    ) == (target, "R1", b"original-config")
    with pytest.raises(ObjectActionError, match="operation_consumed"):
        asyncio.run(obj.start_progress())
    fresh = operation(context, cls, target, invocation_key="business:2")
    assert fresh.invocation_receipt is None and fresh.invocation_state == "ready"


@pytest.mark.parametrize(
    "changes",
    [
        {"invocation_key": ""},
        {"expected_revision_ref": ""},
        {"deadline": float("nan")},
        {"deadline": float("inf")},
        {"deadline": True},
    ],
)
def test_operation_metadata_refuses_without_contact(changes):
    context, port, cls, target = fixture()
    with pytest.raises(ObjectActionError):
        operation(context, cls, target, **changes)
    assert not port.calls


@pytest.mark.parametrize(
    "field,value",
    [
        ("__ontology_binding_digest__", "sha256:" + "a" * 64),
        ("__ontology_schema_digest__", "sha256:" + "a" * 64),
        ("__ontology_dependency_closure_digest__", "sha256:" + "a" * 64),
        ("__ontology_action_bindings__", (("other.action", "start_progress"),)),
    ],
)
def test_wrong_generated_configuration_refuses_before_contact(field, value):
    context, port, cls, target = fixture()
    setattr(cls, field, value)
    with pytest.raises(ObjectActionError, match="binding_mismatch"):
        operation(context, cls, target)
    assert not port.calls


@pytest.mark.parametrize(
    "changes",
    [
        {"provider_generation": "other"},
        {"provider_key": "other"},
        {"type_ref": "Other"},
    ],
)
def test_wrong_receiver_admission_coordinates_refuse(changes):
    context, port, cls, target = fixture()
    with pytest.raises(ObjectActionError, match="invalid_binding"):
        operation(context, cls, replace(target, **changes))
    assert not port.calls


@pytest.mark.parametrize(
    "change",
    [
        lambda r: replace(
            r,
            request=replace(
                r.request, target=replace(r.request.target, instance_ref="other")
            ),
        ),
        lambda r: replace(r, request=replace(r.request, action_ref="other")),
        lambda r: replace(r, request=replace(r.request, invocation_key="other")),
        lambda r: replace(r, request=replace(r.request, expected_revision_ref="R0")),
        lambda r: replace(r, request=replace(r.request, branch_ref="other")),
        lambda r: replace(
            r, request=replace(r.request, configuration_binding=b"other")
        ),
        lambda r: replace(r, history_correspondence=b""),
        lambda r: replace(r, settled=False),
        lambda r: replace(r, worker_cleaned=False),
        lambda r: replace(r, reread_verified=False),
        lambda r: replace(r, settled=1),
        lambda r: replace(r, receipt=replace(r.receipt, base_revision_ref="R0")),
    ],
)
def test_foreign_or_unsettled_outcome_never_becomes_success(change):
    context, port, cls, target = fixture()
    port.change = change
    obj = operation(context, cls, target)
    with pytest.raises(ObjectActionError, match="invalid_result"):
        asyncio.run(obj.start_progress())
    assert obj.invocation_state == "failed" and obj.invocation_receipt is None
    assert len(port.calls) == 1


@pytest.mark.parametrize(
    "failure",
    [
        RuntimeError("transport"),
        TimeoutError("original deadline"),
        asyncio.CancelledError(),
    ],
)
def test_transport_failures_propagate_unchanged_and_never_retry(failure):
    context, port, cls, target = fixture()
    port.failure = failure
    obj = operation(context, cls, target)
    with pytest.raises(type(failure)) as observed:
        asyncio.run(obj.start_progress())
    assert observed.value is failure and obj.invocation_state == "failed"
    assert len(port.calls) == 1 and obj._context is None
    with pytest.raises(ObjectActionError, match="operation_consumed"):
        asyncio.run(obj.start_progress())


def test_closing_context_blocks_pending_response_but_preserves_known_commit():
    context, port, cls, target = fixture()

    def close(result):
        context.close()
        return result

    port.change = close
    obj = operation(context, cls, target)
    with pytest.raises(ObjectActionError, match="context_closed") as observed:
        asyncio.run(obj.start_progress())
    assert observed.value.recovery_ref == "attempt:1"
    assert obj.invocation_receipt.result_revision_ref == "R2" and len(port.calls) == 1
    with pytest.raises(ObjectActionError, match="context_closed"):
        operation(context, cls, target)


def test_elapsed_deadline_before_dispatch_is_terminal():
    context, port, cls, target = fixture()
    obj = operation(context, cls, target, deadline=time.monotonic() - 1.0)
    with pytest.raises(TimeoutError):
        asyncio.run(obj.start_progress())
    assert obj.invocation_state == "failed" and not port.calls


def test_local_retirement_is_private_and_does_not_shadow_domain_close():
    context, port, cls, target = fixture()
    obj = operation(context, cls, target)
    assert not hasattr(obj, "close")
    obj._close_operation()
    assert obj.invocation_state == "closed" and obj._context is None
    with pytest.raises(ObjectActionError, match="operation_consumed"):
        asyncio.run(obj.start_progress())
    assert not port.calls


def test_late_success_retains_receipt_without_claiming_rollback(monkeypatch):
    context, port, cls, target = fixture()
    now = [100.0]
    monkeypatch.setattr(
        "aware_ontology_object_facade_client.actions.time.monotonic", lambda: now[0]
    )

    def finish_late(result):
        now[0] = 201.0
        return result

    port.change = finish_late
    obj = operation(context, cls, target, deadline=200.0)
    with pytest.raises(TimeoutError) as caught:
        asyncio.run(obj.start_progress())
    assert caught.value.attempt_ref == obj.invocation_receipt.attempt_ref
    assert caught.value.recovery_ref == obj.invocation_receipt.attempt_ref
    assert (
        obj.invocation_receipt.result_revision_ref == "R2"
        and obj.invocation_state == "failed"
    )


def test_concurrent_duplicate_does_not_cancel_or_dispatch_again():
    async def run():
        context, port, cls, target = fixture()
        entered, release = asyncio.Event(), asyncio.Event()
        original = port.invoke_action

        async def suspended(request):
            entered.set()
            await release.wait()
            return await original(request)

        port.invoke_action = suspended
        obj = operation(context, cls, target)
        task = asyncio.create_task(obj.start_progress())
        await entered.wait()
        with pytest.raises(ObjectActionError, match="operation_consumed"):
            await obj.start_progress()
        release.set()
        await task
        assert obj.invocation_state == "complete" and len(port.calls) == 1

    asyncio.run(run())


@pytest.mark.parametrize("value", [True, None, "42", 2**54])
def test_argument_refusal_consumes_without_contact(value):
    p = parameter()
    context, port, cls, target = fixture(parameters=(p,))
    obj = operation(context, cls, target)
    with pytest.raises(ObjectActionError, match="invalid_arguments"):
        asyncio.run(obj._invoke_action(ACTION, **{p.parameter_ref: value}))
    assert not port.calls and obj.invocation_state == "failed"


def test_optional_enum_omission_and_null_are_distinct():
    p = parameter(
        "status",
        required=False,
        nullable=True,
        shape=v.ValueShape.named("workflow.IssueStatus"),
    )
    context, port, cls, target = fixture(parameters=(p,))
    for key, arguments in (
        ("omitted", {}),
        ("null", {p.parameter_ref: None}),
        ("enum", {p.parameter_ref: "open"}),
    ):
        obj = operation(context, cls, target, invocation_key=key)
        asyncio.run(obj._invoke_action(ACTION, **arguments))
    assert [r.arguments for r in port.calls] == [
        (),
        ((p.parameter_ref, None),),
        ((p.parameter_ref, "open"),),
    ]
    with pytest.raises(ObjectActionError):
        asyncio.run(
            operation(context, cls, target)._invoke_action(
                ACTION, **{p.parameter_ref: "invented"}
            )
        )


def test_nonvoid_definition_cannot_be_relabelled_as_a_void_action():
    with pytest.raises(ObjectActionError, match="unsupported_profile"):
        fixture(result_shape=v.ValueShape.scalar(v.ScalarKind.INTEGER))


def test_canonical_identity_is_retained_when_original_outcome_supplies_it():
    context, port, cls, target = fixture()
    port.change = lambda r: replace(
        r, receipt=replace(r.receipt, canonical_commit_ref="canonical:original")
    )
    obj = operation(context, cls, target)
    asyncio.run(obj.start_progress())
    assert obj.invocation_receipt.canonical_commit_ref == "canonical:original"


def test_noop_retains_same_revision_without_fabricating_a_commit():
    context, port, cls, target = fixture()
    port.change = lambda r: replace(
        r, receipt=replace(r.receipt, outcome="no_op", result_revision_ref="R1")
    )
    obj = operation(context, cls, target)
    asyncio.run(obj.start_progress())
    assert obj.invocation_receipt.outcome == "no_op"
    assert (
        obj.invocation_receipt.result_revision_ref
        == obj.invocation_receipt.base_revision_ref
    )
    assert obj.invocation_receipt.canonical_commit_ref is None


@pytest.mark.parametrize(
    "outcome,base,result",
    [("no_op", "R1", "R2"), ("committed", "R1", "R1"), ("uncertain", "R1", "R2")],
)
def test_receipt_outcomes_keep_revision_meaning(outcome, base, result):
    with pytest.raises(ObjectActionError, match="invalid_receipt"):
        ObjectActionReceipt("call", "attempt", DIGEST, outcome, base, result, None)
