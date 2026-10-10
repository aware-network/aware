"""Real Workspace source issuer behind Code's explicitly isolated host.

The Code runtime is real; the inert provider/profile is a host-mechanics fixture.
No selected-provider execution or namespace entitlement is admitted by this test.
"""

from contextlib import asynccontextmanager
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    ProducedRoleDeclaration,
    ProfileStepDeclaration,
    ProviderExecutionBinding,
    SemanticCandidateListingCodec,
    SemanticConfigurationCoordinate,
    SemanticContractProfileDeclaration,
    SemanticContractProviderDeclaration,
    SemanticContractRuntime,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.isolated_validation_host import (
    IsolatedWorkspaceOriginProduct,
    bind_isolated_workspace_validation_origin,
    close_isolated_validation_host,
    install_isolated_validation_host,
    require_trusted_validation_origin,
    validate_isolated_workspace_admission,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    SEMANTIC_CANDIDATE_LISTING_REF as CONTRACT,
)
from aware_workspace_runtime import (
    SourceObservationUnavailable,
    WorkspacePackageContextAdmission,
)
from test_observed_semantic_issuers import expectation, setup


class InertProvider:
    declaration = SemanticContractProviderDeclaration(
        provider_key="fixture",
        provider_contract=CONTRACT,
        package_kinds=("example",),
        operation_kinds=("materialize",),
        consumed_roles=(),
        result_role=ProducedRoleDeclaration("result", CONTRACT),
        transition_contract=CONTRACT,
        effect_role=ProducedRoleDeclaration("effect", CONTRACT),
        effect_contract=CONTRACT,
    )

    async def derive(self, invocation):
        raise AssertionError("host conformance must not execute semantic owners")


class Factory:
    def __init__(self, observation, membership, issuer):
        self.product = IsolatedWorkspaceOriginProduct(observation, membership, issuer)
        self.calls = 0

    def make(self):
        self.calls += 1
        return self.product


def code_runtime():
    provider = InertProvider()
    profile = SemanticContractProfileDeclaration(
        profile_ref="fixture-host",
        version="1",
        package_kinds=("example",),
        operation_kinds=("materialize",),
        inputs=(),
        providers=(provider.declaration,),
        steps=(ProfileStepDeclaration("fixture", "fixture", ()),),
        terminal_result_role="result",
        terminal_effect_role="effect",
    )
    return SemanticContractRuntime(
        profile, {"fixture": provider}, {CONTRACT: SemanticCandidateListingCodec()}
    )


@asynccontextmanager
async def joined(tmp_path):
    async with setup(tmp_path) as (root, _, observation, membership, _, handle, issuer):
        runtime, generation = code_runtime(), object()
        factory = Factory(observation, membership, issuer)
        host = install_isolated_validation_host(
            runtime=runtime,
            generation_identity=generation,
            observation_runtime=observation,
            membership_runtime=membership,
            factory_owner=factory,
            factory_method="make",
        )
        origin = bind_isolated_workspace_validation_origin(host)
        digest = ContentDigest.of_bytes(b"isolated-inert-provider")
        expected = replace(
            expectation(issuer, membership, handle),
            runtime=runtime,
            generation_identity=generation,
            profile=runtime.profile,
            provider_declaration=InertProvider.declaration,
            binding=ProviderExecutionBinding(
                "fixture",
                SemanticImplementationCoordinate("fixture", digest),
                SemanticConfigurationCoordinate("fixture", digest),
            ),
        )
        package, inventory = issuer.issue_isolated_pair(handle, expected=expected)
        try:
            yield (
                root,
                observation,
                membership,
                issuer,
                factory,
                host,
                origin,
                expected,
                package,
                inventory,
            )
        finally:
            try:
                close_isolated_validation_host(host)
            except ContractViolation:
                # Rejection cases intentionally close or invalidate the host.
                pass


def validate(origin, expected, package, inventory):
    validate_isolated_workspace_admission(
        origin, package, expected=expected, kind="package_context"
    )
    validate_isolated_workspace_admission(
        origin, inventory, expected=expected, kind="declaration_inventory"
    )
    validate_isolated_workspace_admission(
        origin,
        package,
        expected=expected,
        kind="occurrence_assignments",
        namespace="demo",
        owned_roots=("demo.a", "demo.b"),
    )


async def test_real_workspace_validators_behind_code_host(tmp_path):
    async with joined(tmp_path) as (
        _,
        observation,
        membership,
        issuer,
        factory,
        _,
        origin,
        expected,
        package,
        inventory,
    ):
        assert issuer.observation_runtime is observation
        assert issuer.membership_runtime is membership
        assert factory.calls == 1
        for _ in range(2):
            validate(origin, expected, package, inventory)
        assert factory.calls == 1
        with pytest.raises(ContractViolation, match="trusted bootstrap unavailable"):
            require_trusted_validation_origin(origin)


@pytest.mark.parametrize(
    "change",
    [
        "validator",
        "factory",
        "host_closed",
        "issuer_closed",
        "source",
        "foreign_handle",
        "runtime",
        "generation",
        "operation",
        "stage",
        "roots",
    ],
)
async def test_join_rejects_original_context_substitution(
    tmp_path, monkeypatch, change
):
    async with joined(tmp_path) as (
        root,
        _,
        _,
        issuer,
        factory,
        host,
        origin,
        expected,
        package,
        inventory,
    ):
        if change == "validator":
            monkeypatch.setattr(
                issuer, "validate_package_context_admission", lambda *a, **k: None
            )
        elif change == "factory":
            monkeypatch.setattr(factory, "make", lambda: factory.product)
        elif change == "host_closed":
            close_isolated_validation_host(host)
        elif change == "issuer_closed":
            issuer.close()
        elif change == "source":
            (root / "target/aware.example.toml").write_bytes(b"changed")
        elif change == "foreign_handle":
            package = object.__new__(WorkspacePackageContextAdmission)
        elif change in ("runtime", "generation", "operation"):
            field = {
                "runtime": "runtime",
                "generation": "generation_identity",
                "operation": "operation_identity",
            }[change]
            expected = replace(expected, **{field: object()})
        elif change == "stage":
            expected = replace(expected, stage="authority_derivation")
        else:
            with pytest.raises(SourceObservationUnavailable):
                validate_isolated_workspace_admission(
                    origin,
                    package,
                    expected=expected,
                    kind="occurrence_assignments",
                    namespace="demo",
                    owned_roots=("demo.a",),
                )
            return
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            validate(origin, expected, package, inventory)


async def test_factory_context_substitution_rejects_before_origin(tmp_path):
    async with setup(tmp_path) as (_, _, observation, membership, _, _, issuer):
        factory = Factory(object(), membership, issuer)
        host = install_isolated_validation_host(
            runtime=code_runtime(),
            generation_identity=object(),
            observation_runtime=observation,
            membership_runtime=membership,
            factory_owner=factory,
            factory_method="make",
        )
        try:
            with pytest.raises(ContractViolation, match="substituted original context"):
                bind_isolated_workspace_validation_origin(host)
        finally:
            close_isolated_validation_host(host)
