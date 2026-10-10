"""Private-stage root mechanics; owner barrier and command origin are fixtures."""

import copy
from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace

import pytest
from aware_code_retained_registry_policy_runtime import (
    private_stage_operation as stages,
)
from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    TerminalStatus,
)
from aware_code_semantic_contract_runtime.private_stage_contract import (
    PrivateStageRoleContract,
)
from test_product_contribution import _catalog_product, _factory, _private_plan


class Owner:
    def __init__(self):
        self.live = True
        self.node = object()
        self.node_checks = 0
        self.semantic_input = object()
        self.approval_live = True
        self.read_checks = 0

    def validate_private_stage_input_use(self, node, semantic_input):
        if (
            node is not self.node or semantic_input is not self.semantic_input
            or not self.approval_live or not self.live
        ):
            raise ContractViolation("original private input approval unavailable")
        self.read_checks += 1

    def check_private_stage_input_use_locked(self, node, semantic_input):
        self.validate_private_stage_input_use(node, semantic_input)

    def prepare_private_stage_read_input(self, node, semantic_input):
        self.validate_private_stage_input_use(node, semantic_input)

    def spend_private_stage_read_input_locked(self, node, semantic_input, guard):
        assert guard is not None
        self.validate_private_stage_input_use(node, semantic_input)

    def abort_private_stage_read_input(self, node):
        assert node is self.node

    def validate_committed_private_product(self, root, completion, product):
        del root, completion, product
        raise AssertionError("fixture must not grant a committed product")

    def check_committed_private_product_locked(self, root, completion, product):
        del root, completion, product
        raise AssertionError("fixture must not grant a committed product")

    def validate_selected_graph_node_use(self, source, *, closure=None):
        if source is not self.node or closure is not None or not self.live:
            raise ContractViolation("original graph node unavailable")
        self.node_checks += 1

    def check_selected_graph_node_use_locked(self, source):
        if source is not self.node or not self.live:
            raise ContractViolation("original locked graph node unavailable")


def _fixture(monkeypatch, private_plan_producer=_private_plan):
    factory, _ = _factory(private_plan_producer=private_plan_producer)
    contribution = products.issue_selected_provider_product_contribution(factory)
    plan = products.produce_selected_provider_private_stage_plan(contribution)
    public = products.read_selected_provider_product_contribution(contribution)
    host = object()
    policy = object.__new__(stages.hosts.AdmittedRegistryPolicy)
    source = object()
    epoch = object()
    private_registration = object()
    owner = Owner()
    state = SimpleNamespace(
        source_rail="declaration_v3",
        methods={"factory": SimpleNamespace(receiver=owner)},
        closed=False,
    )
    digest = object()
    eligible = object()
    view = SimpleNamespace(
        source_identity_digest=digest,
        profile_ref=plan.public_profile.profile_ref,
        semantic_provider_key=plan.stages[1].provider_key,
        terminal_roles=(plan.stages[1].terminal.role,),
    )
    monkeypatch.setattr(
        stages.hosts, "_state", lambda value: state if value is host else None
    )
    monkeypatch.setattr(stages, "_BINDINGS", {host: epoch})
    monkeypatch.setattr(
        stages.hosts, "_POLICIES",
        {policy: (host, source, None, None, None, None, epoch)},
    )
    monkeypatch.setattr(
        stages, "_live_stage",
        lambda _state, item: (
            private_registration if item.access == "private"
            else public.expected.registration
        ),
    )
    def validate_port(registration):
        if registration is not private_registration:
            raise ContractViolation("foreign predecessor port")

    monkeypatch.setattr(
        stages.selected, "_validate_selected_private_stage_predecessor_port",
        validate_port,
    )
    monkeypatch.setattr(
        stages.eligibility, "issue_selected_product_catalog_eligibility",
        lambda _host, _policy, _registration: eligible,
    )
    monkeypatch.setattr(
        stages.eligibility, "read_selected_product_catalog_eligibility",
        lambda value: view if value is eligible else None,
    )
    def check_eligibility(value, *, guard):
        if value is not eligible or guard is not epoch:
            raise ContractViolation("foreign guarded eligibility")

    monkeypatch.setattr(
        stages.eligibility, "check_selected_product_catalog_eligibility_locked",
        check_eligibility,
    )

    @contextmanager
    def guard(value):
        if value is not epoch:
            raise ContractViolation("foreign parent exclusion")
        yield epoch

    monkeypatch.setattr(stages, "_guard", guard)

    @contextmanager
    def selected_source(_host, _policy):
        if not owner.live:
            raise ContractViolation("original selected source unavailable")
        yield (
            state, object(), SimpleNamespace(grants=(object(),)),
            SimpleNamespace(expectation=SimpleNamespace(source_identity_digest=digest)),
        )
        if not owner.live:
            raise ContractViolation("original selected source unavailable")

    monkeypatch.setattr(stages, "_selected_policy_source", selected_source)
    return host, policy, contribution, owner, plan


def test_original_root_issues_one_unspent_child_and_rejects_replay(monkeypatch):
    host, policy, contribution, owner, plan = _fixture(monkeypatch)
    try:
        root = stages.bind_private_stage_plan(host, policy, contribution)
        with pytest.raises(ContractViolation, match="already bound"):
            stages.bind_private_stage_plan(host, policy, contribution)
        with pytest.raises(TypeError, match="copied"):
            copy.copy(root)
        child = stages.admit_private_child(
            root, operation_use=owner.node, declared_inputs=plan.stages[0].inputs
        )
        stages.validate_private_child(child)
        assert owner.node_checks >= 2
        with pytest.raises(ContractViolation, match="already admitted"):
            stages.admit_private_child(
                root, operation_use=owner.node, declared_inputs=plan.stages[0].inputs
            )
        with pytest.raises(TypeError, match="Code-issued"):
            stages.PrivateStageChildUse()
        stages.close_private_stage_plan(root)
        with pytest.raises(ContractViolation, match="unavailable"):
            stages.validate_private_child(child)
    finally:
        products.close_selected_provider_product_contribution(contribution)


def test_private_child_rejects_wrong_inputs_source_and_substituted_entrance(
    monkeypatch,
):
    host, policy, contribution, owner, plan = _fixture(monkeypatch)
    try:
        root = stages.bind_private_stage_plan(host, policy, contribution)
        with pytest.raises(ContractViolation, match="declared inputs"):
            stages.admit_private_child(
                root,
                operation_use=owner.node,
                declared_inputs=(PrivateStageRoleContract(
                    "wrong", plan.stages[0].terminal.contract
                ),),
            )
        with pytest.raises(ContractViolation, match="graph node"):
            stages.admit_private_child(
                root, operation_use=object(), declared_inputs=plan.stages[0].inputs
            )
        child = stages.admit_private_child(
            root, operation_use=owner.node, declared_inputs=plan.stages[0].inputs
        )
        owner.validate_committed_private_product = lambda *args: None
        with pytest.raises(ContractViolation, match="entrance substituted"):
            stages.validate_private_child(child)
        stages.close_private_stage_plan(root)
    finally:
        products.close_selected_provider_product_contribution(contribution)


def test_parent_or_source_revocation_refuses_without_leaking_child(monkeypatch):
    host, policy, contribution, owner, plan = _fixture(monkeypatch)
    try:
        root = stages.bind_private_stage_plan(host, policy, contribution)
        child = stages.admit_private_child(
            root, operation_use=owner.node, declared_inputs=plan.stages[0].inputs
        )
        owner.live = False
        with pytest.raises(ContractViolation, match="selected source unavailable"):
            stages.validate_private_child(child)
        stages.close_private_stage_plan(root)
        with pytest.raises(ContractViolation, match="unavailable"):
            stages.validate_private_child(child)
    finally:
        products.close_selected_provider_product_contribution(contribution)


def test_missing_predecessor_port_refuses_root_before_child(monkeypatch):
    host, policy, contribution, _owner, _plan = _fixture(monkeypatch)

    def no_port(registration):
        del registration
        raise ContractViolation("original predecessor port unavailable")

    monkeypatch.setattr(
        stages.selected, "_validate_selected_private_stage_predecessor_port",
        no_port,
    )
    try:
        with pytest.raises(ContractViolation, match="predecessor port unavailable"):
            stages.bind_private_stage_plan(host, policy, contribution)
        assert contribution not in stages._BOUND
    finally:
        products.close_selected_provider_product_contribution(contribution)


def test_live_stage_checks_original_registration_and_complete_inputs():
    factory, _ = _factory()
    contribution = products.issue_selected_provider_product_contribution(factory)
    try:
        public = products.read_selected_provider_product_contribution(contribution)
        catalog_entry = _catalog_product(contribution).entries[0]
        profile = public.profile
        binding = public.binding
        registration = public.expected.registration
        retained = SimpleNamespace(
            products=((public.expected.runtime, registration),),
            entries=((
                binding.provider_key, profile, profile.providers[0], binding,
                catalog_entry.binding_digest,
            ),),
            resolver=SimpleNamespace(
                read_profile_binding=lambda **kwargs: catalog_entry
            ),
            validate=lambda: products.read_selected_provider_product_contribution(
                contribution
            ),
        )
        state = SimpleNamespace(product_retention=retained)
        plan_stage = _private_plan(contribution).stages[1]
        declared = tuple(
            PrivateStageRoleContract(item.role, item.contract)
            for item in profile.inputs
        )
        plan_stage = replace(plan_stage, inputs=declared)
        assert stages._live_stage(state, plan_stage) is registration
        with pytest.raises(ContractViolation, match="live profile"):
            stages._live_stage(state, replace(plan_stage, inputs=()))
        with pytest.raises(ContractViolation, match="unique original"):
            stages._live_stage(state, replace(plan_stage, provider_key="foreign"))
    finally:
        products.close_selected_provider_product_contribution(contribution)


def _tracked_execution(
    monkeypatch, owner, plan, private_registration, *, before_complete=None,
):
    """Exercise the Code lifecycle callback sequence without a Meta store."""
    completion = object()
    origin = None
    calls = []

    class Runtime:
        def owns_completion(self, value):
            return value is completion

        def snapshot_completion(self, value):
            if value is not completion:
                raise ContractViolation("foreign completion")
            return SimpleNamespace(
                invocation_digest="invocation:digest",
                profile_digest=plan.stages[0].profile.digest,
                result=SimpleNamespace(
                    status=TerminalStatus.DELTA,
                    transition=SimpleNamespace(
                        result=SimpleNamespace(
                            role=plan.stages[0].terminal.role,
                            contract=plan.stages[0].terminal.contract
                        )
                    ),
                ),
            )

    class Closure:
        def __init__(self):
            self.invocation = SimpleNamespace(
                profile_ref=plan.stages[0].profile.profile_ref,
                digest="invocation:digest",
            )

        def __post_init__(self):
            return None

    runtime = Runtime()
    original_registration_state = stages.selected._registration_state
    monkeypatch.setattr(
        stages.selected, "_registration_state",
        lambda registration: (
            SimpleNamespace(runtime=runtime, private_stage_predecessor_input=object())
            if registration is private_registration
            else original_registration_state(registration)
        ),
    )
    monkeypatch.setattr(stages.selected, "SelectedProviderInvocationClosure", Closure)

    def bind(_runtime, _registration, admitted_origin, *, terminal_mode):
        nonlocal origin
        assert _runtime is runtime and terminal_mode == "runtime_completion"
        origin = admitted_origin

    def issue(_runtime, _registration, semantic_input, *, operation_context):
        assert _runtime is runtime
        assert semantic_input is not None
        stage = origin.adopt(operation_context)
        origin.validate(stage, Closure())
        calls.append("issue")
        return stage

    def execute(_runtime, stage):
        assert _runtime is runtime
        origin.validate(stage, Closure())
        calls.append("execute")
        if before_complete is not None:
            before_complete()
        origin.complete(stage, completion)
        return completion

    monkeypatch.setattr(stages.selected, "_bind_selected_execution_lifecycle", bind)
    monkeypatch.setattr(stages.selected, "issue_selected_provider_execution", issue)
    monkeypatch.setattr(stages.selected, "execute_selected_provider", execute)
    # This existing fixture tests lifecycle only. The separate read-grant tests
    # use original Code registration, admissions and port execution.
    from aware_code_retained_registry_policy_runtime import private_predecessor_read

    def read_port(child, semantic_input, admission):
        assert child is admission.child and semantic_input is owner.semantic_input
        admission.read_phase = "complete"

    monkeypatch.setattr(private_predecessor_read, "invoke_private_predecessor_port", read_port)
    return completion, calls


def test_tracked_private_child_spends_once_with_original_read_checks(monkeypatch):
    host, policy, contribution, owner, plan = _fixture(monkeypatch)
    try:
        root = stages.bind_private_stage_plan(host, policy, contribution)
        completion, calls = _tracked_execution(
            monkeypatch, owner, plan, stages._ROOTS[root].private_registration
        )
        stages.bind_private_stage_execution(root)
        child = stages.admit_private_child(
            root, operation_use=owner.node, declared_inputs=plan.stages[0].inputs
        )
        with pytest.raises(TypeError, match="read_approval"):
            stages.execute_private_child(
                child, semantic_input=owner.semantic_input, read_approval=object()
            )
        assert stages.execute_private_child(
            child, semantic_input=owner.semantic_input,
        ) is completion
        assert calls == ["issue", "execute"]
        assert owner.read_checks >= 6
        with pytest.raises(ContractViolation, match="unavailable"):
            stages.execute_private_child(
                child, semantic_input=owner.semantic_input,
            )
        stages.close_private_stage_plan(root)
    finally:
        products.close_selected_provider_product_contribution(contribution)


def test_private_execution_rejects_foreign_input_before_provider(monkeypatch):
    host, policy, contribution, owner, plan = _fixture(monkeypatch)
    try:
        root = stages.bind_private_stage_plan(host, policy, contribution)
        _completion, calls = _tracked_execution(
            monkeypatch, owner, plan, stages._ROOTS[root].private_registration
        )
        stages.bind_private_stage_execution(root)
        child = stages.admit_private_child(
            root, operation_use=owner.node, declared_inputs=plan.stages[0].inputs
        )
        with pytest.raises(ContractViolation, match="input approval unavailable"):
            stages.execute_private_child(
                child, semantic_input=object()
            )
        assert calls == []
        with pytest.raises(ContractViolation, match="unavailable"):
            stages.execute_private_child(
                child, semantic_input=owner.semantic_input,
            )
        stages.close_private_stage_plan(root)
    finally:
        products.close_selected_provider_product_contribution(contribution)


def test_owner_local_approval_revocation_rejects_before_provider(monkeypatch):
    host, policy, contribution, owner, plan = _fixture(monkeypatch)
    try:
        root = stages.bind_private_stage_plan(host, policy, contribution)
        _completion, calls = _tracked_execution(
            monkeypatch, owner, plan, stages._ROOTS[root].private_registration
        )
        stages.bind_private_stage_execution(root)
        child = stages.admit_private_child(
            root, operation_use=owner.node, declared_inputs=plan.stages[0].inputs
        )
        owner.approval_live = False
        with pytest.raises(ContractViolation, match="input approval unavailable"):
            stages.execute_private_child(child, semantic_input=owner.semantic_input)
        assert calls == []
        stages.close_private_stage_plan(root)
    finally:
        products.close_selected_provider_product_contribution(contribution)


def test_private_execution_requires_original_input_port(monkeypatch):
    host, policy, contribution, owner, _plan = _fixture(monkeypatch)
    try:
        root = stages.bind_private_stage_plan(host, policy, contribution)
        owner.validate_private_stage_input_use = lambda *args: None
        with pytest.raises(ContractViolation, match="bound direct entrance"):
            stages.bind_private_stage_execution(root)
        stages.close_private_stage_plan(root)
    finally:
        products.close_selected_provider_product_contribution(contribution)


def test_private_execution_refuses_host_without_input_port(monkeypatch):
    host, policy, contribution, _owner, _plan = _fixture(monkeypatch)
    try:
        root = stages.bind_private_stage_plan(host, policy, contribution)
        monkeypatch.delattr(Owner, "validate_private_stage_input_use")
        with pytest.raises(ContractViolation, match="entrances unavailable"):
            stages.bind_private_stage_execution(root)
        stages.close_private_stage_plan(root)
    finally:
        products.close_selected_provider_product_contribution(contribution)


def test_private_execution_rechecks_source_after_owner_call(monkeypatch):
    host, policy, contribution, owner, plan = _fixture(monkeypatch)
    try:
        root = stages.bind_private_stage_plan(host, policy, contribution)
        _completion, calls = _tracked_execution(
            monkeypatch, owner, plan, stages._ROOTS[root].private_registration,
            before_complete=lambda: setattr(owner, "live", False),
        )
        stages.bind_private_stage_execution(root)
        child = stages.admit_private_child(
            root, operation_use=owner.node, declared_inputs=plan.stages[0].inputs
        )
        with pytest.raises(ContractViolation, match="input approval unavailable"):
            stages.execute_private_child(
                child, semantic_input=owner.semantic_input,
            )
        assert calls == ["issue", "execute"]
        assert stages._ROOTS[root].status == "failed"
        owner.live = True
        with pytest.raises(ContractViolation, match="unavailable"):
            stages.execute_private_child(
                child, semantic_input=owner.semantic_input,
            )
        stages.close_private_stage_plan(root)
    finally:
        products.close_selected_provider_product_contribution(contribution)
