"""Constructor data/lifecycle conformance; no backend, journal or store executes."""

from __future__ import annotations

import asyncio
import gc
from dataclasses import replace
from weakref import ref

import pytest
from aware_ontology_object_facade_client import (
    ActionValueMode,
    ObjectConstructorContext,
    ObjectConstructorError,
    ObjectCreationReceipt,
    ObjectCreationResult,
    OntologyObjectActionBinding,
    OntologyObjectActionParameterBinding,
    OntologyObjectActionRole,
    OntologyObjectClassBinding,
    OntologyObjectConstructor,
    OntologyRuntimeActionInstanceRefTarget,
    ScalarKind,
    ValueShape,
)

DIGEST = "sha256:" + "a" * 64


def binding():
    return OntologyObjectClassBinding.create(
        type_ref="storage.StorageBlob", class_name="StorageBlob", fields=(), relationships=(),
        actions=(OntologyObjectActionBinding("storage.StorageBlob.create", "create", (
            OntologyObjectActionParameterBinding("create.sha", 0,
                ValueShape.scalar(ScalarKind.STRING), True, False, ActionValueMode.VALUE),
            OntologyObjectActionParameterBinding("create.mime_type", 1,
                ValueShape.scalar(ScalarKind.STRING), True, False, ActionValueMode.VALUE),
            OntologyObjectActionParameterBinding("create.size_bytes", 2,
                ValueShape.scalar(ScalarKind.INTEGER), True, False, ActionValueMode.VALUE),
        ), OntologyObjectActionRole.CONSTRUCTOR),),
    )


def result(selected):
    return ObjectCreationResult(
        selected.type_ref, selected.actions[0].action_ref, "business/1",
        selected.binding_digest, DIGEST,
        OntologyRuntimeActionInstanceRefTarget(selected.type_ref, "provider:1", "generation:1", "object:blob"),
        ObjectCreationReceipt("invocation:1", "attempt:1", DIGEST, "committed",
                              "provider:1", "generation:1", "revision:2", "commit:2"),
        True, True, True,
    )


def setup(*, returned=None, failure=None):
    selected = binding()

    class StorageBlob(OntologyObjectConstructor):
        __ontology_type_ref__ = selected.type_ref
        __ontology_binding_digest__ = selected.binding_digest
        __ontology_dependency_closure_digest__ = DIGEST
        __ontology_action_bindings__ = ((selected.actions[0].action_ref, "create"),)

    class Invoker:
        def __init__(self):
            self.calls = []

        async def invoke_constructor(self, **values):
            self.calls.append(values)
            if failure is not None:
                raise failure
            return result(selected) if returned is None else returned

    invoker = Invoker()
    context = ObjectConstructorContext(selected, DIGEST, invoker, "provider:1", "generation:1")
    return context.bind(StorageBlob, invocation_key="business/1"), invoker


def invoke(operation, **values):
    return asyncio.run(operation._invoke_constructor("storage.StorageBlob.create", **values))


VALUES = {"create.sha": " A" * 32, "create.mime_type": " ", "create.size_bytes": 7}


def test_raw_declared_arguments_are_ordered_and_owner_controls_normalization():
    operation, invoker = setup()
    created = invoke(operation, **VALUES)
    assert type(created) is type(operation) and created is not operation
    assert operation.invocation_state == "complete" and created.invocation_state == "created"
    assert created.object_reference.instance_ref == "object:blob"
    assert created.invocation_receipt == operation.invocation_receipt
    assert invoker.calls == [{
        "type_ref": "storage.StorageBlob", "action_ref": "storage.StorageBlob.create",
        "arguments": tuple(VALUES.items()), "invocation_key": "business/1",
        "binding_digest": binding().binding_digest, "fragment_closure_digest": DIGEST,
    }]
    for consumed in (operation, created):
        with pytest.raises(ObjectConstructorError, match="operation_consumed"):
            invoke(consumed, **VALUES)
    assert len(invoker.calls) == 1


@pytest.mark.parametrize("replacement", [None, True, 1.5, "7"])
def test_bad_integer_and_null_consume_before_contact(replacement):
    operation, invoker = setup()
    with pytest.raises(ObjectConstructorError, match="invalid_arguments"):
        invoke(operation, **(VALUES | {"create.size_bytes": replacement}))
    assert operation.invocation_state == "failed" and not invoker.calls
    with pytest.raises(ObjectConstructorError, match="operation_consumed"):
        invoke(operation, **VALUES)


@pytest.mark.parametrize("values", [{}, VALUES | {"extra": 1}, {"create.sha": "a" * 64}])
def test_omitted_or_unknown_inputs_do_not_dispatch(values):
    operation, invoker = setup()
    with pytest.raises(ObjectConstructorError, match="invalid_arguments"):
        invoke(operation, **values)
    assert not invoker.calls and operation.invocation_state == "failed"


@pytest.mark.parametrize("field,value", [
    ("type_ref", "other.Type"), ("action_ref", "other.action"),
    ("invocation_key", "business/2"), ("binding_digest", "sha256:" + "b" * 64),
    ("fragment_closure_digest", "sha256:" + "b" * 64),
    ("settled", False), ("worker_cleaned", False), ("reread_verified", False),
    ("settled", 1), ("target", 42), ("receipt", 42),
])
def test_mismatched_or_incomplete_result_never_issues_a_handle(field, value):
    returned = replace(result(binding()), **{field: value})
    operation, invoker = setup(returned=returned)
    with pytest.raises(ObjectConstructorError, match="invalid_result|result_mismatch"):
        invoke(operation, **VALUES)
    assert len(invoker.calls) == 1 and operation.invocation_state == "failed"
    assert operation.invocation_receipt is None


def test_target_provider_must_join_receipt_provider():
    returned = result(binding())
    returned = replace(returned, target=replace(returned.target, provider_generation="generation:2"))
    operation, _ = setup(returned=returned)
    with pytest.raises(ObjectConstructorError, match="result_mismatch"):
        invoke(operation, **VALUES)


def test_coherent_foreign_provider_result_does_not_match_bound_context():
    returned = result(binding())
    returned = replace(returned, target=replace(returned.target, provider_generation="generation:2"),
                       receipt=replace(returned.receipt, provider_generation="generation:2"))
    operation, _ = setup(returned=returned)
    with pytest.raises(ObjectConstructorError, match="result_mismatch"):
        invoke(operation, **VALUES)


def test_completed_operation_and_created_handle_do_not_retain_the_host_port():
    operation, invoker = setup()
    observed = ref(invoker)
    created = invoke(operation, **VALUES)
    del invoker
    gc.collect()
    assert observed() is None
    assert created.object_reference.instance_ref == "object:blob"
    assert operation.invocation_state == "complete"


def test_concurrent_use_of_same_operation_dispatches_once():
    operation, invoker = setup()

    async def run():
        pending = asyncio.Event()
        release = asyncio.Event()
        original = invoker.invoke_constructor

        async def held(**values):
            pending.set()
            await release.wait()
            return await original(**values)

        invoker.invoke_constructor = held
        first = asyncio.create_task(operation._invoke_constructor("storage.StorageBlob.create", **VALUES))
        await pending.wait()
        with pytest.raises(ObjectConstructorError, match="operation_consumed"):
            await operation._invoke_constructor("storage.StorageBlob.create", **VALUES)
        release.set()
        return await first

    assert asyncio.run(run()).invocation_state == "created"
    assert len(invoker.calls) == 1


def test_failure_preserves_original_recovery_ref_and_cannot_retry():
    failure = ObjectConstructorError("backend.uncertain", recovery_ref="attempt:original")
    operation, invoker = setup(failure=failure)
    with pytest.raises(ObjectConstructorError) as caught:
        invoke(operation, **VALUES)
    assert caught.value is failure and caught.value.recovery_ref == "attempt:original"
    with pytest.raises(ObjectConstructorError, match="operation_consumed"):
        invoke(operation, **VALUES)
    assert len(invoker.calls) == 1


def test_cancellation_is_not_converted_to_success_or_retry():
    operation, invoker = setup(failure=asyncio.CancelledError())
    with pytest.raises(asyncio.CancelledError):
        invoke(operation, **VALUES)
    assert operation.invocation_state == "failed" and len(invoker.calls) == 1


def test_context_and_created_identity_are_not_live_operation_authority():
    operation, invoker = setup()
    with pytest.raises(ObjectConstructorError, match="result_unavailable"):
        _ = operation.object_reference
    operation.close()
    with pytest.raises(ObjectConstructorError, match="operation_consumed"):
        invoke(operation, **VALUES)
    assert not invoker.calls


@pytest.mark.parametrize("outcome", ["committed", "no_op"])
def test_local_operational_receipt_preserves_revision_without_canonical_commit(outcome):
    returned = result(binding())
    receipt = replace(returned.receipt, outcome=outcome, canonical_commit_ref=None)
    operation, invoker = setup(returned=replace(returned, receipt=receipt))
    created = invoke(operation, **VALUES)
    assert created.invocation_receipt is receipt
    assert receipt.result_revision_ref == "revision:2"
    assert receipt.canonical_commit_ref is None
    assert receipt.attempt_ref == "attempt:1" and receipt.receipt_digest == DIGEST
    assert created.object_reference.instance_ref == "object:blob"
    with pytest.raises(ObjectConstructorError, match="operation_consumed"):
        invoke(operation, **VALUES)
    assert len(invoker.calls) == 1


@pytest.mark.parametrize("field,value", [("canonical_commit_ref", ""),
                                       ("canonical_commit_ref", False), ("canonical_commit_ref", 42),
                                       ("result_revision_ref", None), ("result_revision_ref", ""),
                                       ("outcome", "pending"), ("receipt_digest", "invalid")])
def test_uncommitted_receipt_is_not_a_success(field, value):
    with pytest.raises(ObjectConstructorError, match="invalid_receipt"):
        replace(result(binding()).receipt, **{field: value})
