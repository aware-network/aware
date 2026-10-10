"""Real Code registration/admission; owner approval/store are instrumented fixtures."""

import copy
from dataclasses import replace
from threading import Thread
from uuid import uuid4

import pytest
from aware_code_retained_registry_policy_runtime import (
    private_predecessor_read as reads,
)
from aware_code_retained_registry_policy_runtime import (
    private_stage_operation as stages,
)
from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.private_stage_contract import (
    PrivateStageProfileIdentity,
    PrivateStageRoleContract,
)
from aware_code_semantic_contract_runtime.runtime import (
    ProviderDerivation,
    SemanticContractRuntime,
)
from test_contracts import delta_bodies, delta_result
from test_private_stage_operation import Owner, _fixture
from test_product_contribution import _private_plan
from test_profile_runtime import profile
from test_selected_provider import (
    _ARTIFACT,
    _BINDING,
    _CONFIGURATION,
    _call,
    _codecs,
    _SelectedProvider,
)


@pytest.fixture
def joined(monkeypatch, request):
    events = []
    guards = []
    retained = []
    faults = {}
    observed = getattr(request, "param", None) == "observed"
    key = "read_" + uuid4().hex
    binding = replace(_BINDING, provider_key=key)

    class Provider(_SelectedProvider):
        def observe(self, event, use):
            assert not guards, "observation must run after parent guard release"
            if event == "associated":
                self.original_use = use
            events.append("observed_" + event)
            evidence = selected.require_selected_invocation(use, self)
            assert evidence.provider is self
            if faults.get("observe_" + event):
                faults["observe_" + event](use)

        def predecessor(self, role, body, grant):
            assert not guards, "port must run after parent guard release"
            events.append("port")
            retained.append(grant)
            if faults.get("before_verify"):
                faults["before_verify"](self, role, body, grant)
            if faults.get("skip_verify"):
                return None
            if observed:
                use = faults.get("foreign_use", self.original_use)
                reads.spend_private_predecessor_grant_for_invocation(use, grant, self, role, body)
            else:
                reads.verify_and_spend_private_predecessor_grant(grant, self, role, body)
            if faults.get("after_verify"):
                faults["after_verify"](self, role, body, grant)
            events.append("store_read")
            if faults.get("after_read"):
                faults["after_read"]()
            return faults.get("port_return")

        def execute(self, step, semantic_input):
            self.calls += 1
            events.append("execute")
            assert semantic_input is owner.semantic_input
            result = delta_result(step.invocation, step.input_closure_digest)
            transition = replace(result.transition, provider_key=key)
            effect = replace(result.effect, provider_key=key, transition_digest=transition.digest)
            result = replace(result, transition=transition, effect=effect, outputs=tuple(
                replace(item, provider_key=key, prepared_effect_digest=effect.digest) for item in result.outputs
            ))
            return ProviderDerivation(result, delta_bodies(result))

    created = []

    def factory():
        provider = Provider()
        provider._declaration = replace(provider.declaration, provider_key=key)
        base = profile()
        declared_profile = replace(base, profile_ref=key, providers=(provider.declaration,),
                                   steps=(replace(base.steps[0], provider_key=key),))
        runtime = SemanticContractRuntime(declared_profile, {key: provider}, _codecs())
        created.append((runtime, provider))
        return selected._SelectedProviderFactoryProduct(
            runtime, provider, binding, provider.execute, provider.input_closure,
            _ARTIFACT, _CONFIGURATION,
            private_stage_predecessor_port=provider.predecessor,
            private_stage_predecessor_input=PrivateStageRoleContract(
                runtime.profile.inputs[0].role, runtime.profile.inputs[0].contract
            ),
            selected_invocation_observer=provider.observe if observed else None,
        )

    admitted_factory = selected._admit_selected_provider_factory(
        factory_ref=key, provider_key=key, selection_factory=factory
    )
    selection = selected._issue_selected_provider_selection_root(admitted_factory)
    runtime, provider = created[0]
    registration = selected.register_selected_provider(runtime, selection)

    def plan(original):
        base = _private_plan(original)
        entry = replace(
            base.stages[0], provider_key=key,
            profile=PrivateStageProfileIdentity(
                runtime.profile.profile_ref, runtime.profile.version, runtime.profile.digest
            ), implementation=binding.implementation, configuration=binding.configuration,
            inputs=tuple(PrivateStageRoleContract(i.role, i.contract) for i in runtime.profile.inputs),
            terminal=PrivateStageRoleContract(
                provider.declaration.result_role.role, provider.declaration.result_role.contract
            ),
        )
        return replace(base, stages=(entry, base.stages[1]),
                       barrier=replace(base.barrier, candidate=entry.terminal))

    original_port_check = selected._validate_selected_private_stage_predecessor_port
    host, policy, contribution, owner, declared = _fixture(monkeypatch, plan)
    monkeypatch.setattr(selected, "_validate_selected_private_stage_predecessor_port", original_port_check)
    public = products.read_selected_provider_product_contribution(contribution)
    monkeypatch.setattr(stages, "_live_stage", lambda state, entry: (
        registration if entry.access == "private" else public.expected.registration
    ))
    host_state = stages.hosts._state(host)
    monkeypatch.setattr(stages.hosts, "_HOSTS", {host: host_state})
    call, bodies = _call(runtime)
    call = replace(call, profile_ref=runtime.profile.profile_ref, provider_bindings=(binding,))
    owner.semantic_input = (call, bodies)
    owner.prepared = False
    owner.spent = False
    owner.aborts = 0

    def prepare(self, node, semantic_input):
        assert not guards
        self.validate_private_stage_input_use(node, semantic_input)
        if self.prepared:
            raise ContractViolation("preparation replay")
        self.prepared = True
        events.append("prepare")
        if faults.get("prepare"):
            faults["prepare"]()
        return faults.get("prepare_return")

    def spend(self, node, semantic_input, guard):
        assert guards and guard is guards[-1]
        self.validate_private_stage_input_use(node, semantic_input)
        if not self.prepared or self.spent:
            raise ContractViolation("spend replay")
        self.spent = True
        events.append("workspace_spend")
        return faults.get("spend_return")

    def abort(self, node):
        assert not guards and node is self.node
        self.aborts += 1
        self.approval_live = False
        events.append("abort")
        if faults.get("abort"):
            raise RuntimeError("cleanup failure")

    monkeypatch.setattr(Owner, "prepare_private_stage_read_input", prepare)
    monkeypatch.setattr(Owner, "spend_private_stage_read_input_locked", spend)
    monkeypatch.setattr(Owner, "abort_private_stage_read_input", abort)
    old_guard = stages._guard
    from contextlib import contextmanager

    @contextmanager
    def guarded(epoch):
        with old_guard(epoch) as guard:
            guards.append(guard)
            faults["guard_active"] = True
            try:
                yield guard
            finally:
                assert guards.pop() is guard
                faults["guard_active"] = False

    monkeypatch.setattr(stages, "_guard", guarded)
    root = stages.bind_private_stage_plan(host, policy, contribution)
    stages.bind_private_stage_execution(root)
    child = stages.admit_private_child(root, operation_use=owner.node, declared_inputs=declared.stages[0].inputs)
    value = (root, child, owner, provider, runtime, registration, events, retained, faults)
    try:
        yield value
    finally:
        if root in stages._ROOTS:
            stages.close_private_stage_plan(root)
        selected.close_selected_provider_registration(runtime, registration)
        products.close_selected_provider_product_contribution(contribution)


def run(joined):
    return stages.execute_private_child(joined[1], semantic_input=joined[2].semantic_input)


def test_original_admission_port_and_dispatch_share_one_use(joined):
    completion = run(joined)
    root, child, owner, provider, runtime, _, events, retained, _ = joined
    assert runtime.owns_completion(completion)
    assert events == ["prepare", "workspace_spend", "port", "store_read", "execute"]
    assert owner.spent and provider.calls == 1
    assert stages._ROOTS[root].status == "private_completed"
    assert retained[0] not in reads._GRANTS
    with pytest.raises(ContractViolation):
        reads.verify_and_spend_private_predecessor_grant(retained[0], provider, "source", b"{}")
    with pytest.raises(ContractViolation):
        run(joined)


def test_grant_binding_checks_do_not_encode_under_exclusion(joined, monkeypatch):
    original_encode = selected.canonical_json_bytes

    def encode(value):
        assert not joined[-1].get("guard_active"), "encoding under original exclusion"
        return original_encode(value)

    monkeypatch.setattr(selected, "canonical_json_bytes", encode)
    completion = run(joined)
    assert joined[4].owns_completion(completion)


@pytest.mark.parametrize("field", ["prepare_return", "spend_return"])
def test_foreign_workspace_records_never_authorize_port(joined, field):
    joined[-1][field] = (object(), "looks-correct", b"{}")
    with pytest.raises(ContractViolation, match="must return None"):
        run(joined)
    assert "port" not in joined[6] and joined[3].calls == 0
    assert joined[2].aborts == 1


@pytest.mark.parametrize("fault", [
    "wrong_role", "wrong_body", "foreign_provider", "copied_grant", "duplicate",
    "wrong_thread", "fork", "changed_input", "closed_host", "epoch", "admission",
    "foreign_grant", "root_epoch", "use", "input_identity", "registration",
    "step_tuple", "step_wrapper", "binding_contract", "binding_slot",
])
def test_port_refusal_performs_zero_store_access_and_no_dispatch(joined, fault, monkeypatch):
    root, _, owner, _, _, _, events, retained, faults = joined

    def poison(provider, role, body, grant):
        if fault == "wrong_role":
            reads.verify_and_spend_private_predecessor_grant(grant, provider, "foreign", body)
        elif fault == "wrong_body":
            reads.verify_and_spend_private_predecessor_grant(grant, provider, role, b"{}")
        elif fault == "foreign_provider":
            reads.verify_and_spend_private_predecessor_grant(grant, object(), role, body)
        elif fault == "copied_grant":
            copy.copy(grant)
        elif fault == "duplicate":
            reads.verify_and_spend_private_predecessor_grant(grant, provider, role, body)
        elif fault == "wrong_thread":
            errors = []
            def worker():
                try:
                    reads.verify_and_spend_private_predecessor_grant(grant, provider, role, body)
                except BaseException as error:
                    errors.append(error)
            thread = Thread(target=worker)
            thread.start()
            thread.join()
            assert errors
        elif fault == "fork":
            with monkeypatch.context() as inherited:
                inherited.setattr(reads.os, "getpid", lambda: -1)
                reads.verify_and_spend_private_predecessor_grant(grant, provider, role, body)
        elif fault == "changed_input":
            object.__setattr__(owner.semantic_input[1][0], "canonical_body", b"{}")
        elif fault == "closed_host":
            stages.hosts._HOSTS[stages._ROOTS[root].host].closed = True
        elif fault == "epoch":
            stages._BINDINGS[stages._ROOTS[root].host] = object()
        elif fault == "admission":
            reads._GRANTS[grant].stage.selected_admission = object()
        elif fault == "foreign_grant":
            reads.verify_and_spend_private_predecessor_grant(object(), provider, role, body)
        elif fault == "root_epoch":
            record = stages._ROOTS[root]
            record.epoch = object()
            stages._BINDINGS[record.host] = record.epoch
        elif fault == "use":
            reads._GRANTS[grant].child.operation_use = object()
        elif fault == "input_identity":
            record = reads._GRANTS[grant]
            equal_input = tuple(list(owner.semantic_input))
            record.stage.semantic_input = record.execution.semantic_input = equal_input
        elif fault == "registration":
            selected.close_selected_provider_registration(joined[4], joined[5])
        elif fault in ("step_tuple", "step_wrapper"):
            read = reads._GRANTS[grant]
            step = read.execution.step_invocation
            original_inputs = step.inputs
            assert any(node is original_inputs for node in read.step_identities)
            changed_inputs = tuple(list(original_inputs))
            if fault == "step_wrapper":
                assert any(node is original_inputs[0] for node in read.step_identities)
                changed_inputs = (replace(original_inputs[0]), *original_inputs[1:])
            object.__setattr__(step, "inputs", changed_inputs)
            # Even coherently replacing the old numeric guard cannot erase the
            # strongly retained original nodes or satisfy their `is` checks.
            read.execution.step_guard = selected._step_identity_guard(step)
        elif fault == "binding_contract":
            binding = reads._GRANTS[grant].binding
            object.__setattr__(binding, "contract", replace(binding.contract))
        elif fault == "binding_slot":
            def hostile(_self):
                events.append("hostile_binding_called")
                raise AssertionError("hostile binding descriptor called")
            monkeypatch.setattr(PrivateStageRoleContract, "role", property(hostile))

    faults["before_verify"] = poison
    with pytest.raises((ContractViolation, TypeError)):
        run(joined)
    assert "store_read" not in events and "execute" not in events
    assert "hostile_binding_called" not in events
    assert owner.aborts == 1 and not reads._GRANTS


def test_port_cannot_return_success_without_spending_grant(joined):
    joined[-1]["skip_verify"] = True
    with pytest.raises(ContractViolation, match="must spend once"):
        run(joined)
    assert "store_read" not in joined[6] and joined[3].calls == 0


def test_changed_source_after_port_refuses_dispatch(joined):
    joined[-1]["after_read"] = lambda: setattr(joined[2], "live", False)
    with pytest.raises(ContractViolation):
        run(joined)
    assert joined[6].count("store_read") == 1 and joined[3].calls == 0
    assert joined[2].aborts == 1


def test_cleanup_failure_does_not_refund_spends(joined):
    joined[-1]["skip_verify"] = True
    joined[-1]["abort"] = True
    with pytest.raises(ContractViolation, match="must spend once"):
        run(joined)
    assert joined[2].spent and joined[2].aborts == 1
    with pytest.raises(ContractViolation):
        run(joined)


def test_original_verifier_substitution_refuses_before_port(joined, monkeypatch):
    joined[-1]["prepare"] = lambda: monkeypatch.setattr(
        reads, "verify_and_spend_private_predecessor_grant", lambda *args: None
    )
    with pytest.raises(ContractViolation, match="verifier substituted"):
        run(joined)
    assert "port" not in joined[6] and joined[3].calls == 0
    assert joined[2].spent and joined[2].aborts == 1


def test_port_substitution_refuses_before_prepare(joined, monkeypatch):
    monkeypatch.setattr(joined[3], "predecessor", lambda *args: None)
    with pytest.raises((ContractViolation, TypeError)):
        run(joined)
    assert joined[6] == []


@pytest.mark.parametrize("joined", ["observed"], indirect=True)
def test_original_invocation_observer_and_grant_share_exact_admission(joined):
    completion = run(joined)
    _, _, _, provider, runtime, registration, events, _, _ = joined
    evidence = selected.require_selected_invocation(provider.original_use, provider)
    assert evidence.completion is completion and evidence.terminal_success
    assert evidence.registration is registration
    assert runtime.owns_completion(completion)
    assert events == ["observed_associated", "prepare", "workspace_spend", "port", "store_read",
                      "observed_dispatch", "execute", "observed_complete"]


@pytest.mark.parametrize("joined", ["observed"], indirect=True)
def test_equal_claim_foreign_invocation_cannot_spend_original_grant(joined):
    _, _, _, provider, _, _, events, _, faults = joined
    faults["foreign_use"] = object.__new__(selected.SelectedInvocationUse)
    with pytest.raises(ContractViolation):
        run(joined)
    assert provider.calls == 0
    assert "store_read" not in events
    assert "observed_failed" in events
    with pytest.raises(ContractViolation):
        selected.require_selected_invocation(provider.original_use, provider)


@pytest.mark.parametrize("joined", ["observed"], indirect=True)
def test_port_refusal_retires_observed_use_before_dispatch(joined):
    faults = joined[-1]
    def refuse(*args):
        raise RuntimeError("original port refusal")
    faults["before_verify"] = refuse
    with pytest.raises(RuntimeError, match="original port refusal"):
        run(joined)
    assert joined[3].calls == 0 and "store_read" not in joined[6]
    assert "observed_failed" in joined[6]
    assert joined[2].aborts == 1
    with pytest.raises(ContractViolation):
        selected.require_selected_invocation(joined[3].original_use, joined[3])


@pytest.mark.parametrize("joined", ["observed"], indirect=True)
def test_substituted_original_invocation_helper_never_runs(joined, monkeypatch):
    calls = []
    def hostile(*args):
        calls.append("foreign")
        raise AssertionError("substituted verifier")
    monkeypatch.setattr(selected, "_require_observed_invocation", hostile)
    with pytest.raises(ContractViolation):
        run(joined)
    assert calls == [] and joined[3].calls == 0
    assert "store_read" not in joined[6]
