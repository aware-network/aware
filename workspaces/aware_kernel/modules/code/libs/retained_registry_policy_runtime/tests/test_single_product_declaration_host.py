"""One v3 product uses original catalog, source, parent and tracked execution.

The neutral owner here supplies fixture source authority, not Workspace or
installed-factory qualification. No semantic-owner runtime is imported.
"""

import os
import re
from contextlib import contextmanager
from dataclasses import fields, replace

import pytest
import test_product_runtime_retention as product_fixtures
from aware_code_retained_registry_policy_runtime import direct_host, product_execution
from aware_code_retained_registry_policy_runtime import epoch_participation as epochs
from aware_code_retained_registry_policy_runtime import (
    selected_catalog_eligibility as eligibility,
)
from aware_code_retained_registry_policy_runtime import selected_root_intent as roots
from aware_code_retained_registry_policy_runtime.declaration_eligibility import (
    calculate_declaration_eligibility,
)
from aware_code_retained_registry_policy_runtime.declaration_host import (
    _prepare_declaration_source,
    _selected_policy_source,
)
from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
    _bind_direct_policy_epoch,
)
from aware_code_semantic_contract_runtime import (
    ProviderDerivation,
    SemanticBody,
    SemanticBodyCodecBinding,
    SemanticValueCoordinate,
    TypedEmptyCoordinate,
)
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    DECLARATION_V3_RESOURCE_ROLES,
    DirectCommandResourceBinding,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeDeclarationScopeExpectation,
)
from test_contracts import (
    EFFECT_BODY,
    OUTPUT_BODY,
    RESULT_BODY,
    SOURCE_BODY,
    TRANSITION_BODY,
    body_coordinate,
    delta_result,
    invocation,
)
from test_declaration_host import OriginalEpochDeclarationOwner
from test_selected_participant_calculation import _body, _mixed_closure


def _product_closure(entry, *, declared_digest=None):
    closure = _mixed_closure(direct_target=False)
    key = entry.semantic_provider_key
    profile = entry.profile_declaration
    scopes = []
    for scope in closure.scopes:
        modules = []
        for module in scope.projection.modules:
            raw = module.manifest.body.decode()
            if module.module_id == "demo":
                raw = raw.replace('provider_key = "demo"', f'provider_key = "{key}"')
                digest = declared_digest or profile.digest.to_wire()
                raw = re.sub(
                    r"profiles = \[.*?\n\]",
                    (
                        'profiles = [{stage="graph_product", profile_ref="'
                        + profile.profile_ref
                        + '", profile_version="'
                        + profile.version
                        + '", profile_digest="'
                        + digest
                        + '"}]'
                    ),
                    raw,
                    flags=re.DOTALL,
                )
            modules.append(
                replace(
                    module, manifest=_body(module.manifest.relative_path, raw.encode())
                )
            )
        scopes.append(
            replace(scope, projection=replace(scope.projection, modules=tuple(modules)))
        )
    profile_body = closure.local_profiles[0].manifest
    retained = _body(
        profile_body.relative_path,
        profile_body.body.replace(
            b'provider_key = "demo"', f'provider_key = "{key}"'.encode()
        ),
    )
    edges = tuple(
        replace(
            edge,
            semantic_contract_provider_keys=replace(
                edge.semantic_contract_provider_keys, value=(key,)
            ),
        )
        for edge in closure.edges
    )
    return replace(
        closure,
        scopes=tuple(scopes),
        edges=edges,
        local_profiles=(replace(closure.local_profiles[0], manifest=retained),),
        profile_associations=(
            replace(closure.profile_associations[0], manifest=retained),
        ),
    )


class ProductOwner(OriginalEpochDeclarationOwner):
    def __init__(self, projection):
        super().__init__(projection)
        self.node = object()
        self.node_live = True
        self.closure = None

    def validate_selected_graph_node_use(self, source, *, closure=None):
        assert not self.guards
        if source is not self.node or not self.node_live or not self.selected_live:
            raise ContractViolation("original node source unavailable")
        if closure is not None and closure is not self.closure:
            raise ContractViolation("original node input changed")

    def check_selected_graph_node_use_locked(self, source):
        assert self.guards
        if source is not self.node or not self.node_live or not self.selected_live:
            raise ContractViolation("original node source unavailable")


class Provider(product_fixtures._SelectedProvider):
    def __init__(self):
        self.calls = 0
        self.on_execute = None

    def input_closure(self, value):
        return value

    def execute(self, step, value):
        assert value.invocation is step.invocation
        self.calls += 1
        if self.on_execute:
            self.on_execute()
        declared = self.declaration
        raw = delta_result(step.invocation, step.input_closure_digest)
        candidate = body_coordinate(
            "result", declared.result_role.contract, "product-result", RESULT_BODY
        )
        transition = replace(
            raw.transition,
            provider_key=declared.provider_key,
            result_contract=declared.result_role.contract,
            transition_contract=declared.transition_contract,
            result=candidate,
            transition_body=body_coordinate(
                "transition-body",
                declared.transition_contract,
                "product-transition",
                TRANSITION_BODY,
            ),
        )
        effect = replace(
            raw.effect,
            provider_key=declared.provider_key,
            effect_contract=declared.effect_contract,
            transition_digest=transition.digest,
            candidate_state=candidate,
            effect_body=body_coordinate(
                "effect", declared.effect_contract, "product-effect", EFFECT_BODY
            ),
        )
        bodies = [
            SemanticBody(candidate, RESULT_BODY),
            SemanticBody(transition.transition_body, TRANSITION_BODY),
            SemanticBody(effect.effect_body, EFFECT_BODY),
        ]
        outputs = ()
        if declared.output_roles:
            output = replace(
                raw.outputs[0],
                provider_key=declared.provider_key,
                output=body_coordinate(
                    "python_sdk",
                    declared.output_roles[0].contract,
                    "product-output",
                    OUTPUT_BODY,
                ),
                prepared_effect_digest=effect.digest,
            )
            outputs = (output,)
            bodies.append(SemanticBody(output.output, OUTPUT_BODY))
        return ProviderDerivation(
            replace(raw, transition=transition, effect=effect, outputs=outputs),
            tuple(sorted(bodies, key=lambda body: body.coordinate.role)),
        )


@contextmanager
def product_host(monkeypatch, *, singleton=True, declared_digest=None):
    original_binding = product_fixtures._binding

    def binding(**kwargs):
        entry = original_binding(**kwargs)
        profile = replace(
            entry.profile_declaration,
            providers=(
                replace(
                    entry.profile_declaration.providers[0],
                    allows_typed_empty=True,
                    counter_keys=("movements",),
                    output_roles=()
                    if singleton
                    else entry.profile_declaration.providers[0].output_roles,
                ),
            ),
            terminal_output_roles=()
            if singleton
            else entry.profile_declaration.terminal_output_roles,
        )
        values = {
            field.name: getattr(entry, field.name)
            for field in fields(entry)
            if field.name != "binding_digest"
        }
        values["profile_declaration"] = profile
        if singleton:
            values["result_product_contracts"] = tuple(
                product
                for product in entry.result_product_contracts
                if product.role != "python_sdk"
            )
        return CodeSemanticMaterializationProfileBinding.create(**values)

    monkeypatch.setattr(product_fixtures, "_binding", binding)
    monkeypatch.setattr(product_fixtures, "_SelectedProvider", Provider)
    base, retained, provider, live = product_fixtures._case()
    entry = retained.resolver.catalog.entries[0]
    owner = ProductOwner(_product_closure(entry, declared_digest=declared_digest))
    by_role = {item.role: item.resource for item in base.resources}
    by_role.update(
        composition_factory=owner,
        lifetime_runtime=owner,
        declaration_scope_runtime=owner,
        policy_producer=calculate_declaration_eligibility,
    )
    expected = replace(
        base,
        source_rail="declaration_v3",
        resources=tuple(
            DirectCommandResourceBinding(role, by_role[role], "borrowed")
            for role in DECLARATION_V3_RESOURCE_ROLES
        ),
    )
    owner.expected = expected
    registration = expected.product_runtime_bindings[0].registration
    bootstrap = direct_host._assemble_direct_command_bootstrap(
        lifetime=owner.lifetime, expected=expected
    )
    host = direct_host.register_direct_workspace_origin(bootstrap, owner.lifetime)
    try:
        closure = owner.projection
        owner.declaration_expectation = CodeDeclarationScopeExpectation(
            closure.repository_binding_ref, "parent", os.getpid(), "operation", "epoch"
        )
        prepared = _prepare_declaration_source(
            host, owner.snapshot, owner.declaration_expectation
        )
        parent = DirectInvocationExpectation(
            expected.invocation_identity, expected.epoch_identity, os.getpid()
        )
        digest = ContentDigest.of_bytes(b"product-membership")
        owner.epoch = CatalogPairEpochExpectation(
            parent, object(), direct_host._HOSTS[host].catalog_digest, digest, digest
        )
        guard = owner.acquire_catalog_epoch_exclusion(owner.parent, expected=parent)
        try:
            tracker = epochs._assemble_code_epoch_participation(
                owner=owner,
                parent=owner.parent,
                invocation=parent,
                epoch_owner=owner,
                guard=guard,
            )
            _bind_direct_policy_epoch(
                host,
                tracker,
                owner.current,
                expected=owner.epoch,
                guard=guard,
                declaration_source=prepared,
            )
        finally:
            owner.release_catalog_epoch_exclusion(guard)
        yield owner, host, registration, provider, live
    finally:
        direct_host.close_direct_validation_host(host)
        state = selected._registration_state(registration)
        for admission, execution in tuple(selected._EXECUTIONS.values()):
            if (
                execution.registration is registration
                and execution.lifecycle == "active"
            ):
                selected._abort_selected_provider_execution(state.runtime, admission)
        selected.close_selected_provider_registration(state.runtime, registration)


def test_product_only_policy_root_and_publication_use_original_registration(
    monkeypatch,
):
    with product_host(monkeypatch) as (owner, host, registration, provider, _):
        policy = direct_host.produce_registry_policy(host, owner.selected)
        state = direct_host._HOSTS[host]
        assert state.stage_retention is None
        assert state.expected.stage_runtime_bindings == ()
        intent, requirement = roots.derive_selected_root_intent(host, policy)
        assert intent.requested_semantic_root_refs == ("consumer_home",)
        assert intent.requested_terminal_output_roles == ("result",)
        assert requirement.contract == provider.declaration.result_role.contract
        handle = eligibility.issue_selected_product_catalog_eligibility(
            host, policy, registration
        )
        view = eligibility.read_selected_product_catalog_eligibility(handle)
        assert view.terminal_roles == ("result",)
        parent = state.expected
        invocation_context = DirectInvocationExpectation(
            parent.invocation_identity, parent.epoch_identity, os.getpid()
        )
        guard = owner.acquire_catalog_epoch_exclusion(
            owner.parent, expected=invocation_context
        )
        try:
            eligibility.check_selected_product_catalog_eligibility_locked(
                handle, guard=guard
            )
        finally:
            owner.release_catalog_epoch_exclusion(guard)
        assert provider.calls == 0


def test_product_only_ambiguous_default_requires_explicit_role(monkeypatch):
    with product_host(monkeypatch, singleton=False) as (
        owner,
        host,
        registration,
        _,
        _,
    ):
        policy = direct_host.produce_registry_policy(host, owner.selected)
        intent, requirement, key = roots.derive_selected_product_root_intent(
            host,
            policy,
            requested_role="python_sdk",
            selected_product_registration=registration,
        )
        assert intent.requested_terminal_output_roles == ("python_sdk",)
        assert requirement.role == "python_sdk"
        assert key == selected._registration_state(registration).provider_key
        with pytest.raises(ContractViolation, match="ambiguous"):
            roots.derive_selected_root_intent(host, policy)


@pytest.mark.parametrize(
    "role,foreign", [("effect", False), ("unknown", False), ("python_sdk", True)]
)
def test_product_only_role_and_original_registration_refusals(
    monkeypatch, role, foreign
):
    with product_host(monkeypatch, singleton=False) as (
        owner,
        host,
        registration,
        provider,
        _,
    ):
        policy = direct_host.produce_registry_policy(host, owner.selected)
        with pytest.raises(ContractViolation):
            roots.derive_selected_product_root_intent(
                host,
                policy,
                requested_role=role,
                selected_product_registration=object() if foreign else registration,
            )
        assert provider.calls == 0


def test_product_only_declaration_cannot_restamp_profile_digest(monkeypatch):
    with product_host(
        monkeypatch, declared_digest=ContentDigest.of_bytes(b"foreign").to_wire()
    ) as (owner, host, _, provider, _):
        with pytest.raises(ContractViolation, match="declared live product"):
            direct_host.produce_registry_policy(host, owner.selected)
        assert provider.calls == 0


@pytest.mark.parametrize(
    "change", ["source", "catalog", "registration", "parent", "epoch"]
)
def test_product_policy_lifetime_refuses_changed_originals(monkeypatch, change):
    with product_host(monkeypatch) as (owner, host, _registration, provider, live):
        policy = direct_host.produce_registry_policy(host, owner.selected)
        if change == "source":
            owner.selected_live = False
        elif change == "catalog":
            live[0] = False
        elif change == "registration":
            original = owner.expected.product_runtime_bindings[0]
            object.__setattr__(original, "registration", object())
        elif change == "parent":
            owner.live = False
        else:
            owner.current = object()
        with pytest.raises((TypeError, ContractViolation)):
            roots.derive_selected_root_intent(host, policy)
        assert provider.calls == 0
        if change == "parent":
            # This fixture's guard has no retiring mode. Restore it only for
            # teardown; the original Code host remains terminal after refusal.
            owner.live = True
            with pytest.raises(ContractViolation, match="unavailable"):
                roots.derive_selected_root_intent(host, policy)


def test_product_registration_rechecked_after_policy_owner_work(monkeypatch):
    with product_host(monkeypatch) as (owner, host, registration, _, _):
        policy = direct_host.produce_registry_policy(host, owner.selected)
        original = owner.expected.product_runtime_bindings[0]
        with (
            pytest.raises((TypeError, ContractViolation)),
            _selected_policy_source(host, policy),
        ):
            object.__setattr__(original, "registration", object())
        object.__setattr__(original, "registration", registration)


@pytest.mark.parametrize("mutate_during_call", [False, True])
def test_original_product_host_runs_tracked_selected_completion(
    monkeypatch, mutate_during_call
):
    with product_host(monkeypatch) as (owner, host, registration, provider, _):
        policy = direct_host.produce_registry_policy(host, owner.selected)
        roots.derive_selected_root_intent(host, policy)
        runtime = selected._registration_state(registration).runtime
        body = SemanticBody(
            SemanticValueCoordinate(
                "source",
                runtime.profile.inputs[0].contract,
                "original",
                ContentDigest.of_bytes(SOURCE_BODY),
                len(SOURCE_BODY),
            ),
            SOURCE_BODY,
        )
        entry = direct_host._HOSTS[host].product_retention.resolver.catalog.entries[0]
        call = replace(
            invocation(),
            profile_ref=runtime.profile.profile_ref,
            profile_digest=runtime.profile.digest,
            inputs=(body.coordinate,),
            predecessor=TypedEmptyCoordinate(provider.declaration.result_role.contract),
            provider_bindings=entry.provider_execution_bindings,
            requested_output_roles=(),
            body_codec_bindings=tuple(
                sorted(
                    (
                        SemanticBodyCodecBinding(contract, codec.implementation)
                        for contract, codec in runtime._body_codecs.items()
                    ),
                    key=lambda item: item.contract.key,
                )
            ),
        )
        owner.closure = selected.SelectedProviderInvocationClosure(call, (body,), None)
        product_execution.bind_product_execution_origin(host, registration)
        admission = selected.issue_selected_provider_execution(
            runtime, registration, owner.closure, operation_context=owner.node
        )
        if mutate_during_call:
            provider.on_execute = lambda: setattr(owner, "selected_live", False)
            with pytest.raises(ContractViolation, match="source unavailable"):
                selected.execute_selected_provider(runtime, admission)
        else:
            completion = selected.execute_selected_provider(runtime, admission)
            assert runtime.owns_completion(completion)
            assert (
                completion.result.transition.result.contract
                == provider.declaration.result_role.contract
            )
            with pytest.raises(ContractViolation, match="replay"):
                selected.issue_selected_provider_execution(
                    runtime, registration, owner.closure, operation_context=owner.node
                )
        assert provider.calls == 1
