"""Real Code executors; Workspace admission/store custody are explicit fixtures."""

import copy
import gc
import os
import signal
from dataclasses import replace
from threading import Event, Thread
from weakref import ref

import pytest
from aware_code_retained_registry_policy_runtime import (
    private_stage_operation as stages,
)
from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    TerminalStatus,
)
from aware_code_semantic_contract_runtime.private_stage_contract import (
    PrivateStageRoleContract,
)
from aware_code_semantic_contract_runtime.runtime import (
    ProviderDerivation,
    SemanticBody,
)
from test_contracts import delta_bodies, delta_result
from test_private_predecessor_read import joined, run  # noqa: F401
from test_private_stage_operation import Owner
from test_selected_provider import _SelectedProvider


@pytest.fixture
def terminal(monkeypatch, request):
    import test_private_predecessor_read as private_tests
    import test_product_contribution as product_tests

    calls = []
    faults = {}

    class PublicProvider(_SelectedProvider):
        def execute(self, step, semantic_input):
            self.calls += 1
            calls.append("terminal_execute")
            if faults.get("execute"):
                faults["execute"]()
            result = delta_result(step.invocation, step.input_closure_digest)
            key = self.declaration.provider_key
            transition = replace(result.transition, provider_key=key)
            effect = replace(
                result.effect, provider_key=key, transition_digest=transition.digest
            )
            result = replace(
                result,
                transition=transition,
                effect=effect,
                outputs=tuple(
                    replace(
                        item, provider_key=key, prepared_effect_digest=effect.digest
                    )
                    for item in result.outputs
                ),
            )
            return ProviderDerivation(result, delta_bodies(result))

    monkeypatch.setattr(product_tests, "_SelectedProvider", PublicProvider)
    original_plan = private_tests._private_plan

    def plan(original):
        base = original_plan(original)
        public = products.read_selected_provider_product_contribution(original)
        inputs = tuple(
            PrivateStageRoleContract(i.role, i.contract) for i in public.profile.inputs
        )
        candidate = PrivateStageRoleContract(
            "candidate", public.profile.providers[0].result_role.contract
        )
        return replace(
            base,
            stages=(
                replace(base.stages[0], terminal=candidate),
                replace(base.stages[1], inputs=inputs),
            ),
            barrier=replace(
                base.barrier,
                candidate=candidate,
                committed_product=PrivateStageRoleContract(
                    "committed", inputs[0].contract
                ),
                consumer_input_role=inputs[0].role,
            ),
        )

    monkeypatch.setattr(private_tests, "_private_plan", plan)

    def full(self, root, completion, product):
        assert not faults.get("guard_active")
        if (
            not self.live
            or root is not self.barrier_root
            or completion is not self.barrier_completion
            or product is not self.barrier_admission
            or faults.get("stale")
        ):
            raise ContractViolation("original committed product unavailable")
        calls.append("barrier_full")
        if faults.get("full"):
            faults["full"]()
        return faults.get("full_return")

    def locked(self, root, completion, product):
        assert faults.get("guard_active")
        if (
            not self.live
            or root is not self.barrier_root
            or completion is not self.barrier_completion
            or product is not self.barrier_admission
            or faults.get("stale")
        ):
            raise ContractViolation("locked committed product unavailable")
        calls.append("barrier_locked")
        if faults.get("locked"):
            faults["locked"]()
        return faults.get("locked_return")

    def node(self, source, *, closure=None):
        if source is not self.node or not self.live:
            raise ContractViolation("original node unavailable")
        if closure is not None:
            assert closure.invocation.profile_ref == self.terminal_profile
            original = self.barrier_product
            delivered = closure.input_bodies[0]
            if (
                delivered.canonical_body != original.canonical_body
                or delivered.coordinate.value_ref != original.coordinate.value_ref
            ):
                raise ContractViolation(
                    "node input differs from original product admission"
                )

    monkeypatch.setattr(Owner, "validate_committed_private_product", full)
    monkeypatch.setattr(Owner, "check_committed_private_product_locked", locked)
    monkeypatch.setattr(Owner, "validate_selected_graph_node_use", node)
    values = request.getfixturevalue("joined")
    (
        root,
        _child,
        owner,
        _provider,
        _runtime,
        _registration,
        _events,
        _retained,
        private_faults,
    ) = values
    # The genuine selected private executor and grant run unchanged.
    completion = run(values)
    record = stages._ROOTS[root]
    public = products.read_selected_provider_product_contribution(record.contribution)
    runtime = selected._registration_state(public.expected.registration).runtime
    from test_selected_provider import _call

    invocation, bodies = _call(runtime)
    invocation = replace(
        invocation,
        profile_ref=runtime.profile.profile_ref,
        provider_bindings=(public.binding,),
    )
    product = SemanticBody(
        replace(bodies[0].coordinate, role="committed"), bodies[0].canonical_body
    )
    owner.barrier_root, owner.barrier_completion, owner.barrier_product = (
        root,
        completion,
        product,
    )
    owner.terminal_profile = runtime.profile.profile_ref

    class Admission:
        pass

    owner.barrier_admission = Admission()
    # Keep assertions tied to the very same original exclusion fixture.
    faults = private_faults
    yield root, completion, product, owner, (invocation, bodies), runtime, calls, faults


def admit(value, **changes):
    root, completion, product, owner, *_ = value
    args = {
        "operation_use": owner.node,
        "private_completion": completion,
        "admitted_committed_product": owner.barrier_admission,
        "committed_product_body": product,
    }
    args.update(changes)
    return stages.admit_terminal_child(root, **args)


def test_real_two_selected_calls_and_original_barrier(terminal):
    root, private_completion, _product, _owner, value, runtime, calls, _faults = (
        terminal
    )
    assert stages._ROOTS[root].private_completion is private_completion
    child = admit(terminal)
    with pytest.raises(TypeError, match="copied"):
        copy.copy(child)
    result = stages.execute_terminal_child(child, semantic_input=value)
    assert runtime.owns_completion(result)
    assert runtime.snapshot_completion(result).result.status is TerminalStatus.DELTA
    assert stages._ROOTS[root].status == "terminal_completed"
    assert stages._ROOTS[root].private_completion is None
    assert child not in stages._TERMINALS
    assert calls.count("terminal_execute") == 1
    assert calls.count("barrier_full") >= 4
    assert calls.count("barrier_locked") >= 4
    with pytest.raises(ContractViolation):
        stages.execute_terminal_child(child, semantic_input=value)


@pytest.mark.parametrize(
    "change", ["completion", "node", "copy", "candidate", "contract", "role"]
)
def test_barrier_refuses_before_public_contact_and_restoration(terminal, change):
    root, _completion, product, _owner, _value, _runtime, calls, _faults = terminal
    changes = {}
    if change == "completion":
        changes["private_completion"] = object()
    elif change == "node":
        changes["operation_use"] = object()
    elif change == "copy":
        changes["admitted_committed_product"] = object()
    else:
        plan = products.read_selected_provider_private_stage_plan(
            stages._ROOTS[root].contribution
        )
        coordinate = (
            replace(
                product.coordinate,
                role=plan.barrier.candidate.role,
                contract=plan.barrier.candidate.contract,
            )
            if change == "candidate"
            else (
                replace(product.coordinate, contract=plan.barrier.candidate.contract)
                if change == "contract"
                else replace(product.coordinate, role="foreign")
            )
        )
        changes["committed_product_body"] = SemanticBody(
            coordinate, product.canonical_body
        )
    with pytest.raises((TypeError, ContractViolation)):
        admit(terminal, **changes)
    assert calls.count("terminal_execute") == 0
    assert stages._ROOTS[root].status == "failed"
    assert stages._ROOTS[root].private_completion is None
    with pytest.raises(ContractViolation):
        admit(terminal)


@pytest.mark.parametrize("boundary", ["admission", "execution", "owner_return"])
def test_fresh_barrier_rejects_revocation_at_each_boundary(terminal, boundary):
    root, _completion, _product, _owner, value, _runtime, calls, faults = terminal
    if boundary == "admission":
        faults["stale"] = True
        with pytest.raises(ContractViolation):
            admit(terminal)
    else:
        child = admit(terminal)
        if boundary == "execution":
            faults["stale"] = True
        else:
            faults["execute"] = lambda: faults.update(stale=True)
        with pytest.raises(ContractViolation):
            stages.execute_terminal_child(child, semantic_input=value)
    assert calls.count("terminal_execute") == int(boundary == "owner_return")
    assert stages._ROOTS[root].status == "failed"
    faults.pop("stale", None)
    with pytest.raises(ContractViolation):
        admit(terminal)


@pytest.mark.parametrize(
    "name",
    ["validate_committed_private_product", "check_committed_private_product_locked"],
)
def test_original_barrier_substitution_has_zero_hostile_calls(terminal, name):
    root, _completion, _product, owner, value, _runtime, calls, _faults = terminal
    child = admit(terminal)
    hostile_calls = []
    original = getattr(owner, name)

    def hostile(*args):
        hostile_calls.append(args)
        setattr(owner, name, original)

    setattr(owner, name, hostile)
    with pytest.raises(ContractViolation):
        stages.execute_terminal_child(child, semantic_input=value)
    assert hostile_calls == [] and "terminal_execute" not in calls
    delattr(owner, name)
    assert stages._ROOTS[root].status == "failed"


@pytest.mark.parametrize("mutation", ["body", "coordinate", "missing", "changed_input"])
def test_input_or_retained_product_mutation_cannot_authorize_execution(
    terminal, mutation
):
    _root, _completion, product, _owner, value, _runtime, calls, _faults = terminal
    child = admit(terminal)
    if mutation == "body":
        object.__setattr__(product, "canonical_body", b"{}")
    elif mutation == "coordinate":
        object.__setattr__(product, "coordinate", replace(product.coordinate))
    elif mutation == "missing":
        value = (replace(value[0], inputs=()), ())
    else:
        replacement = replace(value[1][0].coordinate, value_ref="foreign")
        value = (
            replace(value[0], inputs=(replacement,)),
            (SemanticBody(replacement, value[1][0].canonical_body),),
        )
    with pytest.raises((TypeError, ContractViolation, IndexError)):
        stages.execute_terminal_child(child, semantic_input=value)
    assert "terminal_execute" not in calls


@pytest.mark.parametrize("entrance", ["full_return", "locked_return"])
def test_validator_must_return_none(terminal, entrance):
    terminal[-1][entrance] = object()
    with pytest.raises(ContractViolation, match="returned a value"):
        admit(terminal)
    assert "terminal_execute" not in terminal[-2]


def test_foreign_root_rejection_preserves_registered_family(terminal):
    with pytest.raises(TypeError):
        stages.admit_terminal_child(
            object(),
            operation_use=object(),
            private_completion=object(),
            admitted_committed_product=object(),
            committed_product_body=object(),
        )
    assert stages._ROOTS[terminal[0]].status == "private_completed"
    result = stages.execute_terminal_child(admit(terminal), semantic_input=terminal[4])
    assert terminal[5].owns_completion(result)


def test_close_revokes_terminal_without_owner_execution(terminal):
    child = admit(terminal)
    stages.close_private_stage_plan(terminal[0])
    with pytest.raises(ContractViolation):
        stages.execute_terminal_child(child, semantic_input=terminal[4])
    assert child not in stages._TERMINALS and "terminal_execute" not in terminal[-2]


def test_cross_thread_cannot_execute_original_use(terminal):
    child = admit(terminal)
    errors = []

    def call():
        try:
            stages.execute_terminal_child(child, semantic_input=terminal[4])
        except (ContractViolation, TypeError) as error:
            errors.append(error)

    thread = Thread(target=call)
    thread.start()
    thread.join(2)
    assert not thread.is_alive() and len(errors) == 1
    assert "terminal_execute" not in terminal[-2]


def test_post_completion_selected_return_is_revalidated(terminal, monkeypatch):
    child = admit(terminal)
    original = stages.selected.execute_selected_provider

    def revoke_after_return(*args, **kwargs):
        completion = original(*args, **kwargs)
        terminal[-1]["stale"] = True
        return completion

    monkeypatch.setattr(
        stages.selected, "execute_selected_provider", revoke_after_return
    )
    with pytest.raises(ContractViolation):
        stages.execute_terminal_child(child, semantic_input=terminal[4])
    assert stages._ROOTS[terminal[0]].status == "failed"
    assert child not in stages._TERMINALS
    assert terminal[-2].count("terminal_execute") == 1


def test_registered_restamping_is_terminal_without_hostile_behavior(terminal):
    child = admit(terminal)
    calls = []

    class Hostile:
        __slots__ = ("__weakref__",)

        def __hash__(self):
            calls.append("hash")
            raise AssertionError("hostile hash")

        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("hostile equality")

    child.__class__ = Hostile
    with pytest.raises(TypeError):
        stages.execute_terminal_child(child, semantic_input=terminal[4])
    child.__class__ = stages.TerminalStageChildUse
    assert calls == []
    assert stages._ROOTS[terminal[0]].status == "failed"
    with pytest.raises(ContractViolation):
        stages.execute_terminal_child(child, semantic_input=terminal[4])


def test_reentrant_barrier_admission_cannot_publish_a_child(terminal):
    root = terminal[0]
    terminal[-1]["full"] = lambda: admit(terminal)
    with pytest.raises(ContractViolation):
        admit(terminal)
    assert stages._ROOTS[root].status == "failed"
    assert stages._ROOTS[root].terminal_child is None
    assert "terminal_execute" not in terminal[-2]


@pytest.mark.parametrize("boundary", ["admission", "execution"])
def test_changed_body_validator_never_runs(terminal, monkeypatch, boundary):
    calls = []
    original = SemanticBody.__post_init__
    child = admit(terminal) if boundary == "execution" else None

    def hostile(self):
        calls.append(self)
        monkeypatch.setattr(SemanticBody, "__post_init__", original)

    monkeypatch.setattr(SemanticBody, "__post_init__", hostile)
    with pytest.raises(ContractViolation, match="body validator changed"):
        if child is None:
            admit(terminal)
        else:
            stages.execute_terminal_child(child, semantic_input=terminal[4])
    assert calls == []
    assert stages._ROOTS[terminal[0]].status == "failed"


def test_portable_body_cannot_replace_nominal_admission(terminal):
    with pytest.raises(ContractViolation):
        admit(terminal, admitted_committed_product=terminal[2])
    assert "terminal_execute" not in terminal[-2]


def test_admitted_product_and_selected_body_must_share_owner_correspondence(terminal):
    original = terminal[2]
    wrong = replace(
        original, coordinate=replace(original.coordinate, value_ref="foreign")
    )
    child = admit(terminal, committed_product_body=wrong)
    # Equal generic role/contract cannot bridge an independently admitted product
    # to another input body; the selected closure and original node both check.
    with pytest.raises(ContractViolation):
        stages.execute_terminal_child(child, semantic_input=terminal[4])
    assert "terminal_execute" not in terminal[-2]


def test_held_code_rejection_releases_borrowed_admission(terminal, monkeypatch):
    child = admit(terminal)
    state = stages._TERMINALS[child]
    admission = ref(terminal[3].barrier_admission)
    monkeypatch.setattr(SemanticBody, "__post_init__", lambda self: None)
    error = None
    try:
        stages.execute_terminal_child(child, semantic_input=terminal[4])
    except ContractViolation as caught:
        error = caught
    assert error is not None
    assert (
        state.product
        is state.product_tree
        is state.admission
        is state.operation_use
        is None
    )
    # Only the fixture owner releases its own admission. Code neither cancels
    # it nor clears the owner's fields; the held Code exception cannot pin it.
    del terminal[3].barrier_admission
    gc.collect()
    assert admission() is None


@pytest.mark.skipif(not hasattr(os, "fork"), reason="requires real fork")
def test_fork_refuses_before_inherited_lock_and_preserves_parent(terminal):
    child = admit(terminal)
    locked, release = Event(), Event()

    def holder():
        with stages._LOCK:
            locked.set()
            release.wait(5)

    thread = Thread(target=holder)
    thread.start()
    assert locked.wait(2)
    reader, writer = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(reader)
        signal.alarm(2)
        try:
            stages.execute_terminal_child(child, semantic_input=terminal[4])
        except ContractViolation:
            os.write(writer, b"refused")
            os._exit(0)
        os._exit(1)
    os.close(writer)
    try:
        _pid, status = os.waitpid(pid, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        assert os.read(reader, 16) == b"refused"
        assert "terminal_execute" not in terminal[-2]
    finally:
        os.close(reader)
        release.set()
        thread.join(2)
    completion = stages.execute_terminal_child(child, semantic_input=terminal[4])
    assert terminal[5].owns_completion(completion)
