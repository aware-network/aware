"""Original factory recipe -> source production -> verified selected inputs."""

import asyncio
from contextlib import contextmanager
from dataclasses import replace

import pytest
import test_product_planning_source as sources
from aware_code_retained_registry_policy_runtime import (
    product_execution_inputs as execution,
)
from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticBodyCodecBinding,
    SemanticContractRef,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    TypedEmptyCoordinate,
)
from aware_code_semantic_contract_runtime.product_execution_input_plan import (
    ProductExecutionInputPlan,
    ProductExecutionInputSourceScope,
    ProductExecutionInputStep,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputJoinedProducerDeclaration,
    SemanticInputPackageIdentity,
    SemanticInputProducerDeclaration,
    SemanticInputProducerHost,
    SemanticInputProductionExpectation,
    SemanticInputSourceBody,
    SemanticInputSourceContract,
    SemanticInputSourceCoordinate,
)
from test_contracts import SOURCE_BODY, invocation

RAW = SemanticContractRef("fixture.raw", "1", ContentDigest.of_bytes(b"raw"))
AUX = SemanticContractRef("fixture.aux", "1", ContentDigest.of_bytes(b"aux"))


class Owner(sources.Owner):
    def __init__(self, projection):
        super().__init__(projection)
        class Node:
            pass
        self.node = Node()

    def validate_semantic_input_source(self, source, *, expected):
        assert not self.guards
        if (
            source is not self.selected
            or not self.selected_live
            or not any(expected is value for value in self.expected_inputs)
        ):
            raise ContractViolation("original recipe source unavailable")

    def read_semantic_input_sources(self, source, *, expected):
        self.validate_semantic_input_source(source, expected=expected)
        return tuple(
            SemanticInputSourceBody(row, self.recipe_raw)
            for row in expected.source_coordinates
        )

    def validate_selected_input_node_use(self, node, *, assembly=None, closure=None):
        assert not self.guards
        if node is not self.node or not self.node_live or assembly is not self.assembly:
            raise ContractViolation("original recipe node unavailable")

    def check_selected_input_node_use_locked(self, node):
        assert self.guards
        if node is not self.node or not self.node_live:
            raise ContractViolation("original recipe node retired")


@contextmanager
def setup(monkeypatch):
    calls, owner_holder, callback = [], [], [None]
    old_admit = selected._admit_selected_provider_factory

    def prefix(value):
        calls.append("prefix")
        assert value.sources[0].canonical_body == owner_holder[0].recipe_raw
        if callback[0]:
            callback[0]()
        raw = b'{"prefix":true}'
        return SemanticBody(
            SemanticValueCoordinate(
                "aux", AUX, "cas://aux", ContentDigest.of_bytes(raw), len(raw)
            ),
            raw,
        )

    def joined(value):
        calls.append("joined")
        assert value.predecessors[0].canonical_body == b'{"prefix":true}'
        contract = value.ordinary.sources[0].source.coordinate.contract
        # The selected profile, rather than the raw source contract, declares output.
        contract = (
            products.read_selected_provider_product_contribution(
                owner_holder[0].contribution
            )
            .profile.inputs[0]
            .contract
        )
        return SemanticBody(
            SemanticValueCoordinate(
                "source",
                contract,
                "cas://source-input",
                ContentDigest.of_bytes(SOURCE_BODY),
                len(SOURCE_BODY),
            ),
            SOURCE_BODY,
        )

    def assembler(value):
        original = products.read_selected_provider_product_contribution(
            owner_holder[0].contribution
        )
        profile = original.profile
        call = replace(
            invocation(),
            invocation_ref=value.invocation_ref,
            idempotency_key=value.idempotency_key,
            target_package=value.package,
            profile_ref=profile.profile_ref,
            profile_digest=profile.digest,
            inputs=tuple(x.coordinate for x in value.input_bodies),
            requested_output_roles=(),
            provider_bindings=(original.binding,),
            predecessor=TypedEmptyCoordinate(profile.providers[0].result_role.contract),
            body_codec_bindings=tuple(SemanticBodyCodecBinding(contract, implementation)
                for contract, implementation in sorted(original.expected.runtime._codec_implementations.items(), key=lambda row: row[0].key)),
        )
        return selected.SelectedProviderInvocationClosure(
            call, value.input_bodies, value.predecessor_body
        )

    def builder(contribution):
        original = products.read_selected_provider_product_contribution(contribution)
        binding = original.binding
        profile = original.profile

        def declaration(ref, role, contract):
            return SemanticInputProducerDeclaration(
                ref,
                profile.profile_ref,
                binding.implementation,
                binding.configuration,
                (SemanticInputSourceContract("raw", RAW),),
                role,
                contract,
            )

        first = declaration("fixture.prefix", "aux", AUX)
        final = SemanticInputJoinedProducerDeclaration(
            declaration("fixture.final", "source", profile.inputs[0].contract),
            (SemanticInputSourceContract("aux", AUX),),
            ("prefix",),
        )
        scope = (ProductExecutionInputSourceScope("raw"),)
        return ProductExecutionInputPlan(
            (
                ProductExecutionInputStep("prefix", first, prefix, scope),
                ProductExecutionInputStep("joined", final, joined, scope),
            ),
            (1,),
            assembler,
        )

    def admit(*, selection_factory, **kwargs):
        def wrapped():
            return replace(
                selection_factory(), execution_input_contribution_producer=builder
            )

        return old_admit(selection_factory=wrapped, **kwargs)

    monkeypatch.setattr(selected, "_admit_selected_provider_factory", admit)
    monkeypatch.setattr(sources, "Owner", Owner)
    with sources.setup(monkeypatch) as values:
        owner, host, policy, contribution, *_ = values
        owner_holder.append(owner)
        owner.contribution = contribution
        manifest = owner.projection.scopes[0].projection.packages[0].manifest
        owner.recipe_raw = manifest.body
        package = SemanticPackageCoordinate(
            "package:consumer@1", "sdk", manifest.content_digest
        )
        coordinate = SemanticInputSourceCoordinate(
            owner.selected_value.expectation.manifest_relative_path,
            SemanticValueCoordinate(
                "raw",
                RAW,
                "cas://original",
                manifest.content_digest,
                len(manifest.body),
            ),
        )
        owner.expected_inputs = tuple(
            SemanticInputProductionExpectation.create(
                use_ref="recipe-" + stage,
                operation_ref="operation",
                stage=stage,
                package_identity=SemanticInputPackageIdentity(package, "consumer"),
                operation_identity=owner.parent,
                source_identity=owner.selected,
                source_coordinates=(coordinate,),
            )
            for stage in ("prefix", "joined")
        )
        input_host = SemanticInputProducerHost()
        try:
            plan = execution.enroll_product_execution_inputs(host, policy, contribution)
            registrations = execution.register_product_execution_input_producers(
                host, policy, contribution, input_host=input_host
            )
            yield values, input_host, registrations, plan, calls, callback
        finally:
            input_host.close()


def produce(case):
    values, input_host, registrations, *_ = case
    owner, host, policy, contribution, *_ = values
    return asyncio.run(
        execution.execute_product_execution_inputs(
            host,
            policy,
            contribution,
            input_host=input_host,
            registrations=registrations,
            expectations=owner.expected_inputs,
        )
    )


def assemble(case, results):
    values, input_host, registrations, *_ = case
    owner, host, policy, contribution, *_ = values
    return execution.assemble_product_execution_inputs(
        host,
        policy,
        contribution,
        input_host=input_host,
        registrations=registrations,
        expectations=owner.expected_inputs,
        results=results,
        invocation_ref="invocation-1",
        idempotency_key="idem-1",
    )


def altered(expected, **changes):
    values = {
        name: getattr(expected, name)
        for name in (
            "use_ref",
            "operation_ref",
            "stage",
            "package_identity",
            "operation_identity",
            "source_identity",
            "source_coordinates",
            "context_bodies",
        )
    }
    values.update(changes)
    return SemanticInputProductionExpectation.create(**values)


def test_original_prefix_join_and_body_assembly(monkeypatch):
    with setup(monkeypatch) as case:
        results = produce(case)
        assembly = assemble(case, results)
        assert assembly.input_bodies == (results[1],)
        assert assembly.input_bodies[0] is results[1]
        assert tuple(x.result for x in assembly.source_results) == results
        assert assembly.source_input_roles == (("source", 1),)
        assert case[4] == ["prefix", "joined"]
        owner, host, policy, contribution, *_ = case[0]
        execution.validate_execution_input_assembly(
            host, policy, contribution, assembly
        )
        owner.selected_live = False
        with pytest.raises(ContractViolation):
            execution.validate_execution_input_assembly(
                host, policy, contribution, assembly
            )


@pytest.mark.parametrize(
    "change", ["path", "pin", "stage", "source", "parent", "reorder", "registration"]
)
def test_foreign_or_incomplete_input_refuses_before_owner_call(monkeypatch, change):
    with setup(monkeypatch) as case:
        owner = case[0][0]
        expected = owner.expected_inputs[0]
        if change == "path":
            expected = altered(expected, source_coordinates=())
        elif change == "pin":
            row = expected.source_coordinates[0]
            expected = altered(
                expected,
                source_coordinates=(
                    replace(
                        row,
                        coordinate=replace(
                            row.coordinate, digest=ContentDigest.of_bytes(b"wrong")
                        ),
                    ),
                ),
            )
        elif change == "stage":
            expected = altered(expected, stage="foreign")
        elif change == "source":
            expected = altered(expected, source_identity=object())
        elif change == "parent":
            expected = altered(expected, operation_identity=object())
        if change == "reorder":
            owner.expected_inputs = tuple(reversed(owner.expected_inputs))
        elif change == "registration":
            case = (case[0], case[1], tuple(reversed(case[2])), *case[3:])
        else:
            owner.expected_inputs = (expected, owner.expected_inputs[1])
        with pytest.raises((ContractViolation, TypeError)):
            produce(case)
        assert case[4] == []


def test_copied_result_is_not_an_original_return(monkeypatch):
    with setup(monkeypatch) as case:
        results = produce(case)
        with pytest.raises(ContractViolation):
            assemble(case, (results[0], replace(results[1])))


def test_source_mutation_during_prefix_prevents_joined_owner_call(monkeypatch):
    with setup(monkeypatch) as case:
        case[5][0] = lambda: setattr(case[0][0], "selected_live", False)
        with pytest.raises(ContractViolation):
            produce(case)
        assert case[4] == ["prefix"]


def test_replay_does_not_rerun_producers(monkeypatch):
    with setup(monkeypatch) as case:
        produce(case)
        with pytest.raises(ContractViolation):
            produce(case)
        assert case[4] == ["prefix", "joined"]


def test_recipe_qualified_binding_needs_no_fabricated_observer(monkeypatch):
    from aware_code_retained_registry_policy_runtime import product_execution

    with setup(monkeypatch) as case:
        owner, host, policy, contribution, *_ = case[0]
        registration = products.read_selected_provider_product_contribution(
            contribution
        ).expected.registration
        assert (
            selected._registration_state(registration).selected_invocation_observer
            is None
        )
        with pytest.raises(ContractViolation, match="observer"):
            product_execution.bind_selected_input_verification_origin(
                host, registration
            )
        origin = execution.bind_product_execution_input_origin(
            host, policy, contribution
        )
        assert origin is not None
        results = produce(case)
        assembly = assemble(case, results)
        owner.assembly = assembly
        product_execution.prepare_selected_input_verification(
            host, owner.node, registration, assembly=assembly
        )
        runtime = selected._registration_state(registration).runtime
        admission = selected.issue_selected_provider_execution(
            runtime, registration, assembly.semantic_input, operation_context=owner.node
        )
        completion = selected.execute_selected_provider(runtime, admission)
        assert runtime.owns_completion(completion)
