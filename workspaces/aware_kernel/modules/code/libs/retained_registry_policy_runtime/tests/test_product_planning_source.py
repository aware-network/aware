"""Original neutral owner -> retained product source -> existing graph source.

The fixture source owner is not installed Workspace authority. No real semantic
owner implementation, empty inventory substitution or stage pair is involved.
"""

import asyncio
import copy
import os
from contextlib import contextmanager
from dataclasses import fields, replace
from threading import Thread
from uuid import uuid4

import pytest
import test_product_runtime_retention as fixture
import test_single_product_declaration_host as fixed
from aware_code_retained_registry_policy_runtime import direct_host
from aware_code_retained_registry_policy_runtime import (
    product_planning_source as planning,
)
from aware_code_retained_registry_policy_runtime.planning_source_composition import (
    compose_retained_planning_sources,
    validate_composed_retained_planning_source,
)
from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticAuthoredDependency,
    SemanticDependencyPlanningInput,
    SemanticDependencyTarget,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    RetainedSemanticProductRuntimeExpectation,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DependencyPlanningInputCodec,
)
from aware_code_semantic_contract_runtime.runtime import (
    SemanticBody,
    SemanticContractRuntime,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputPackageIdentity,
    SemanticInputProducerDeclaration,
    SemanticInputProducerHost,
    SemanticInputProductionExpectation,
    SemanticInputSourceBody,
    SemanticInputSourceContract,
    SemanticInputSourceCoordinate,
)
from test_profile_runtime import JsonBodyCodec

_SOURCE_CONTRACT = SemanticContractRef(
    "example.source", "1", ContentDigest.of_bytes(b"source-contract")
)


class Owner(fixed.ProductOwner):
    def validate_semantic_input_source(self, source, *, expected):
        assert not self.guards
        if (
            source is not self.selected
            or not self.selected_live
            or expected is not self.input_expected
            or expected.operation_identity is not self.parent
        ):
            raise ContractViolation("original owner input source unavailable")
        callback = getattr(self, "on_validation", None)
        if callback is not None:
            callback()

    def read_semantic_input_sources(self, source, *, expected):
        self.validate_semantic_input_source(source, expected=expected)
        return (SemanticInputSourceBody(expected.source_coordinates[0], self.raw),)


@contextmanager
def setup(monkeypatch, *, missing=False, wrong_result=None, dependencies=()):
    calls, created, contributions = [], [], []
    on_call = [None]

    async def produce(value):
        calls.append(value)
        assert not created[0].guards
        await asyncio.sleep(0)
        if on_call[0]:
            on_call[0]()
        authored = DependencyPlanningInputCodec().decode(
            value.sources[0].canonical_body
        )
        package = authored.package
        assert package == value.package_identity.package
        digest = authored.source_identity_digest
        if wrong_result == "package":
            package = replace(package, package_ref="foreign")
        if wrong_result == "source":
            digest = ContentDigest.of_bytes(b"foreign")
        body = DependencyPlanningInputCodec().encode(
            SemanticDependencyPlanningInput(package, digest, authored.dependencies)
        )
        return SemanticBody(
            SemanticValueCoordinate(
                "planning_input",
                DependencyPlanningInputCodec.contract,
                "cas://owner-planning",
                ContentDigest.of_bytes(body),
                len(body),
            ),
            body,
        )

    def case():
        key = "product_" + uuid4().hex
        original = fixture._binding(provider_key=key, profile_ref="graph_product")
        provider = fixture._SelectedProvider()
        provider._declaration = original.profile_declaration.providers[0]
        profile = original.profile_declaration
        declared = provider.declaration
        contracts = {item.contract for item in profile.inputs} | {
            declared.result_role.contract,
            declared.transition_contract,
            declared.effect_contract,
            *(item.contract for item in declared.output_roles),
        }
        runtime = SemanticContractRuntime(
            profile, {key: provider}, {item: JsonBodyCodec(item) for item in contracts}
        )
        binding = replace(fixture._BINDING, provider_key=key)
        declaration = SemanticInputProducerDeclaration(
            key + ".planning",
            profile.profile_ref,
            binding.implementation,
            binding.configuration,
            (SemanticInputSourceContract("source", _SOURCE_CONTRACT),),
            "planning_input",
            DependencyPlanningInputCodec.contract,
        )

        def factory():
            return selected._SelectedProviderFactoryProduct(
                runtime,
                provider,
                binding,
                provider.execute,
                provider.input_closure,
                fixture._ARTIFACT,
                fixture._CONFIGURATION,
                planning_input_declaration=None if missing else declaration,
                planning_input_producer=None if missing else produce,
            )

        admission = selected._admit_selected_provider_factory(
            factory_ref=key, provider_key=key, selection_factory=factory
        )
        contribution = products.issue_selected_provider_product_contribution(admission)
        contributions.append(contribution)
        registration = products.read_selected_provider_product_contribution(
            contribution
        ).expected.registration
        values = {
            f.name: getattr(original, f.name)
            for f in fields(original)
            if f.name != "binding_digest"
        }
        values["provider_execution_bindings"] = (binding,)
        entry = CodeSemanticMaterializationProfileBinding.create(**values)
        catalog = fixture._catalog(entry)
        executables, planners = fixture._execution_closure(catalog)
        executables = tuple(
            (i, c, provider)
            if i == binding.implementation and c == binding.configuration
            else (i, c, p)
            for i, c, p in executables
        )
        live = [True]
        admitted = fixture._issue_code_semantic_contract_catalog(
            catalog=catalog,
            provider_executable_bindings=executables,
            dependency_planner_bindings=planners,
            host_liveness=lambda: live[0],
        )
        base = fixture.context()
        expected = replace(
            base,
            process_id=os.getpid(),
            runtime=runtime,
            catalog=admitted,
            resources=tuple(
                replace(
                    item, resource=runtime if item.role == "code_runtime" else admitted
                )
                if item.role in {"code_runtime", "catalog"}
                else item
                for item in base.resources
            ),
            product_runtime_bindings=(
                RetainedSemanticProductRuntimeExpectation(runtime, registration),
            ),
        )
        return (
            expected,
            fixture._capture_product_runtime_retention(expected),
            provider,
            live,
        )

    class TrackedOwner(Owner):
        def __init__(self, projection):
            super().__init__(projection)
            created.append(self)

    monkeypatch.setattr(fixed, "ProductOwner", TrackedOwner)
    monkeypatch.setattr(fixture, "_case", case)
    with fixed.product_host(monkeypatch) as (owner, host, _, provider, live):
        policy = direct_host.produce_registry_policy(host, owner.selected)
        original = owner.selected_value
        owner.raw = DependencyPlanningInputCodec().encode(
            SemanticDependencyPlanningInput(
                _package(owner),
                original.expectation.source_identity_digest,
                dependencies,
            )
        )
        coordinate = SemanticValueCoordinate(
            "source",
            _SOURCE_CONTRACT,
            "cas://original-source",
            ContentDigest.of_bytes(owner.raw),
            len(owner.raw),
        )
        owner.input_expected = SemanticInputProductionExpectation.create(
            use_ref="owner-planning-use",
            operation_ref="operation",
            stage="source_planning",
            package_identity=SemanticInputPackageIdentity(
                # Original source owner supplies package identity; never package id promotion.
                _package(owner),
                "consumer",
            ),
            operation_identity=owner.parent,
            source_identity=owner.selected,
            source_coordinates=(
                SemanticInputSourceCoordinate("manifest.toml", coordinate),
            ),
        )
        input_host = SemanticInputProducerHost()
        try:
            yield (
                owner,
                host,
                policy,
                contributions[0],
                input_host,
                calls,
                on_call,
                provider,
                live,
            )
        finally:
            planning.close_product_planning_sources(host)
            input_host.close()


def _package(owner):
    from aware_code_semantic_contract_runtime.contracts import SemanticPackageCoordinate

    return SemanticPackageCoordinate(
        "package:consumer@1",
        "ontology_package",
        owner.selected_value.expectation.manifest_content_digest,
    )


def execute(values):
    owner, host, policy, contribution, input_host, *_ = values
    registration = planning.register_product_planning_input_producer(
        host, policy, contribution, input_host=input_host
    )
    return asyncio.run(
        planning.execute_product_planning_input(
            host,
            policy,
            contribution,
            input_host=input_host,
            registration=registration,
            expected=owner.input_expected,
        )
    ), registration


def test_original_factory_source_composes_without_a_stage_pair(monkeypatch):
    with setup(monkeypatch) as values:
        owner, host, _, _, _, calls, _, provider, _ = values
        source, _ = execute(values)
        assert direct_host._HOSTS[host].stage_retention is None
        package = owner.input_expected.package_identity.package
        composed = compose_retained_planning_sources((source,))
        validate_composed_retained_planning_source(host, composed, (package,))
        assert composed.read_dependencies(package).dependencies == ()
        assert len(calls) == 1 and provider.calls == 0
        owner.selected_live = False
        with pytest.raises(ContractViolation):
            composed.read_dependencies(package)
        owner.selected_live = True
        with pytest.raises(ContractViolation):
            source.read_dependencies(package)


def test_missing_factory_producer_never_fabricates_planning(monkeypatch):
    with setup(monkeypatch, missing=True) as values:
        _, host, policy, contribution, input_host, calls, *_ = values
        with pytest.raises(ContractViolation, match="unavailable"):
            planning.register_product_planning_input_producer(
                host, policy, contribution, input_host=input_host
            )
        assert calls == []


@pytest.mark.parametrize("wrong_result", ["package", "source"])
def test_original_owner_must_bind_exact_package_and_source(monkeypatch, wrong_result):
    with (
        setup(monkeypatch, wrong_result=wrong_result) as values,
        pytest.raises(ContractViolation, match="package/source"),
    ):
        execute(values)


def test_owner_mutation_during_await_rejects_return(monkeypatch):
    with setup(monkeypatch) as values:
        owner = values[0]
        values[6][0] = lambda: setattr(owner, "selected_live", False)
        with pytest.raises(ContractViolation):
            execute(values)
        assert len(values[5]) == 1


@pytest.mark.parametrize(
    "change", ["body", "declaration", "catalog", "foreign_thread", "fork", "reader"]
)
def test_post_return_revalidation_rejects_substitution_and_retirement(
    monkeypatch, change
):
    with setup(monkeypatch) as values:
        owner, _host, _, contribution, _, _, _, _, live = values
        source, _ = execute(values)
        package = owner.input_expected.package_identity.package
        state = planning._SOURCES[source]
        if change == "body":
            object.__setattr__(state.result, "canonical_body", b"changed")
        elif change == "declaration":
            product = products._state(contribution).product
            object.__setattr__(
                product.planning_input_declaration, "producer_ref", "changed"
            )
        elif change == "catalog":
            live[0] = False
        elif change == "reader":
            object.__setattr__(source, "read_dependencies", lambda _package: None)
        elif change == "fork":
            pid = os.getpid()
            monkeypatch.setattr(os, "getpid", lambda: pid + 1)
        else:
            errors = []

            def read():
                try:
                    source.read_dependencies(package)
                except ContractViolation as error:
                    errors.append(error)

            thread = Thread(target=read)
            thread.start()
            thread.join()
            assert len(errors) == 1
            return
        try:
            with pytest.raises(ContractViolation):
                type(source).read_dependencies(source, package)
        finally:
            if change == "fork":
                monkeypatch.setattr(os, "getpid", lambda: pid)


def test_source_cannot_be_copied_or_reexecuted(monkeypatch):
    with setup(monkeypatch) as values:
        owner, host, policy, contribution, input_host, calls, *_ = values
        source, registration = execute(values)
        with pytest.raises(TypeError):
            copy.copy(source)
        with pytest.raises(ContractViolation, match="consumed"):
            asyncio.run(
                planning.execute_product_planning_input(
                    host,
                    policy,
                    contribution,
                    input_host=input_host,
                    registration=registration,
                    expected=owner.input_expected,
                )
            )
        assert len(calls) == 1


def test_running_owner_call_blocks_epoch_publication(monkeypatch):
    from aware_code_retained_registry_policy_runtime import (
        epoch_participation as epochs,
    )

    with setup(monkeypatch) as values:

        def check_running():
            binding = planning.hooks._BINDINGS[values[1]]
            assert any(
                use.status == "running"
                for use in epochs._state(binding.participant).uses.values()
            )

        values[6][0] = check_running
        execute(values)


def test_original_nonempty_dependencies_are_preserved(monkeypatch):
    from aware_code_semantic_contract_runtime.contracts import SemanticPackageCoordinate

    target = SemanticDependencyTarget(
        SemanticPackageCoordinate(
            "package:target@1",
            "ontology_package",
            ContentDigest.of_bytes(b"target"),
        ),
        ("root",),
    )
    dependencies = (SemanticAuthoredDependency("import", "direct-target", (target,)),)
    with setup(monkeypatch, dependencies=dependencies) as values:
        source, _ = execute(values)
        package = values[0].input_expected.package_identity.package
        assert (
            compose_retained_planning_sources((source,))
            .read_dependencies(package)
            .dependencies
            == dependencies
        )


def test_terminal_cleanup_preserves_borrowed_host_and_source(monkeypatch):
    with setup(monkeypatch) as values:
        owner, host, *_ = values
        source, registration = execute(values)
        planning.close_product_planning_sources(host)
        assert source not in planning._SOURCES
        assert owner.selected_live
        assert values[4]._registrations[registration].closed is False
        with pytest.raises(ContractViolation):
            source.read_dependencies(owner.input_expected.package_identity.package)


def test_uncertain_guard_release_defers_reference_disposal(monkeypatch):
    with setup(monkeypatch) as values:
        source, _ = execute(values)
        state = planning._SOURCES[source]
        binding = state.binding
        original = binding.release.method

        def fail_release(_guard):
            raise ContractViolation("injected held exclusion")

        object.__setattr__(binding.release, "method", fail_release)
        try:
            with pytest.raises(ContractViolation, match="injected"):
                planning.close_product_planning_sources(values[1])
            assert planning._SOURCES[source] is state and state.terminal
        finally:
            object.__setattr__(binding.release, "method", original)
            # The neutral fixture's outstanding guard belongs to the owner.
            for guard in tuple(values[0].guards):
                original(guard)
        planning.close_product_planning_sources(values[1])
        assert source not in planning._SOURCES


@pytest.mark.parametrize(
    "substitute", ["source", "parent", "expectation", "registration"]
)
def test_foreign_execution_inputs_refuse_before_owner_call(monkeypatch, substitute):
    with setup(monkeypatch) as values:
        owner, host, policy, contribution, input_host, calls, *_ = values
        registration = planning.register_product_planning_input_producer(
            host,
            policy,
            contribution,
            input_host=input_host,
        )
        expected = owner.input_expected
        if substitute == "source":
            expected = replace(expected, source_identity=object())
        elif substitute == "parent":
            expected = replace(expected, operation_identity=object())
        elif substitute == "expectation":
            expected = replace(expected)
        else:
            registration = object()
        with pytest.raises((ContractViolation, TypeError)):
            asyncio.run(
                planning.execute_product_planning_input(
                    host,
                    policy,
                    contribution,
                    input_host=input_host,
                    registration=registration,
                    expected=expected,
                )
            )
        assert calls == []


def test_product_planning_sources_from_other_commands_cannot_compose(monkeypatch):
    with setup(monkeypatch) as first:
        source, _ = execute(first)
        with setup(monkeypatch) as second:
            foreign, _ = execute(second)
            with pytest.raises(
                ContractViolation, match="different parent/epoch/catalog"
            ):
                compose_retained_planning_sources((source, foreign))


def test_host_closure_revokes_retained_source(monkeypatch):
    with setup(monkeypatch) as values:
        source, _ = execute(values)
        direct_host.close_direct_validation_host(values[1])
        with pytest.raises(ContractViolation):
            source.read_dependencies(values[0].input_expected.package_identity.package)


def test_owner_cancellation_yields_no_planning_source(monkeypatch):
    with setup(monkeypatch) as values:

        def cancel():
            raise asyncio.CancelledError()

        values[6][0] = cancel
        with pytest.raises(asyncio.CancelledError):
            execute(values)
        assert not any(state.host is values[1] for state in planning._SOURCES.values())


def test_active_read_defers_cleanup_until_validation_returns(monkeypatch):
    with setup(monkeypatch) as values:
        source, _ = execute(values)
        owner, host, *_ = values
        state = planning._SOURCES[source]
        owner.on_validation = lambda: planning.close_product_planning_sources(host)
        with pytest.raises(ContractViolation, match="read is active"):
            source.read_dependencies(owner.input_expected.package_identity.package)
        assert state.active == 0 and state.terminal and state.input_host is values[4]
        owner.on_validation = None
        planning.close_product_planning_sources(host)
        assert state.input_host is None
