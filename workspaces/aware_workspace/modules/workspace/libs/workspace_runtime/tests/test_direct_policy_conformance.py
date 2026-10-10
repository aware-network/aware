"""Real Workspace mechanics under an ISOLATED parent; no application trust proof.

The fixture issuer is never promoted or used for semantic execution. Catalogs
come from the single joint operation, not a direct private Code issuer call.
"""

import os
from contextlib import asynccontextmanager
from dataclasses import replace
from threading import RLock

import pytest
from aware_code_retained_registry_policy_runtime import direct_host
from aware_code_retained_registry_policy_runtime.calculation import (
    calculate_registry_policy,
)
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractRuntime,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    RESOURCE_ROLES,
    DirectCommandExpectedContext,
    DirectCommandResourceBinding,
    DirectWorkspaceOriginProduct,
)
from aware_workspace_runtime import (
    WorkspaceCommandLifetimeRuntime,
    WorkspaceObservedSemanticIssuerRuntime,
    WorkspaceSemanticMaterializationMembershipCatalog,
)
from aware_workspace_runtime.semantic_catalog_host import (
    _assemble_authenticated_catalog_host,
)
from test_calculation import fixture as code_fixture
from test_direct_command_composition import fenced_direct_sources
from test_materialization_catalog import _execution_closure
from test_observed_membership import fixture as repository_fixture


class NoExecutionProvider:
    def __init__(self, declaration):
        self.declaration = declaration

    async def execute(self, *args, **kwargs):
        raise AssertionError("policy conformance must not execute a provider")


class NoExecutionCodec:
    def __init__(self, contract):
        self.contract = contract
        self.implementation = SemanticImplementationCoordinate(
            "fixture-codec", ContentDigest.of_bytes(b"fixture-codec")
        )

    def encode(self, value):
        raise AssertionError("policy conformance must not encode semantic values")

    def decode(self, value):
        raise AssertionError("policy conformance must not decode semantic values")


class IsolatedParent:
    def __init__(self):
        self.live = True
        self.lock = RLock()

    def validate_catalog_parent(self):
        if not self.live:
            raise RuntimeError("isolated parent closed")


class IsolatedFactory:
    def __init__(self, lifetime_runtime):
        self.owner = lifetime_runtime
        self.expected = None
        self.calls = 0

    def create_direct_semantic_origin(self, lifetime):
        self.owner.validate_command_lifetime(lifetime, expected=self.expected)
        self.calls += 1
        return DirectWorkspaceOriginProduct(lifetime, self.expected)


@asynccontextmanager
async def assembly(tmp_path):
    scope, catalog = code_fixture()
    async with repository_fixture(tmp_path) as (root, session, original, _):
        (root / "aware.workspace.toml").write_text(
            'aware=1\n[workspace]\nhandle="demo"\n'
            '[[workspace.modules]]\nid="demo"\npath="demo"\n'
        )
        for body in [scope.modules[0].manifest, *(p.manifest for p in scope.packages)]:
            path = root / body.relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body.body)
        with fenced_direct_sources(
            session=session,
            store=original._store,
            workspace_manifest_path="aware.workspace.toml",
        ) as sources:
            parent = IsolatedParent()
            joint = _assemble_authenticated_catalog_host(
                parent=parent, publication_lock=parent.lock
            )
            lifetime_runtime = WorkspaceCommandLifetimeRuntime()
            semantic_issuer = WorkspaceObservedSemanticIssuerRuntime.for_isolated_proof(
                observation_runtime=sources.observation_runtime,
                membership_runtime=sources.membership_runtime,
                observation=sources.observation,
            )
            host = None
            try:
                providers, planners = _execution_closure(catalog)
                membership_catalog = (
                    WorkspaceSemanticMaterializationMembershipCatalog.create(
                        catalog_ref="fixture.empty-membership",
                        catalog_generation=1,
                        entries=(),
                    )
                )
                pair = joint.admit_catalogs(
                    code_catalog=catalog,
                    workspace_catalog_reader=lambda: membership_catalog,
                    provider_executable_bindings=providers,
                    dependency_planner_bindings=planners,
                )
                profile = catalog.entries[0].profile_declaration
                runtime = SemanticContractRuntime(
                    profile,
                    {p.provider_key: NoExecutionProvider(p) for p in profile.providers},
                    {
                        c: NoExecutionCodec(c)
                        for c in SemanticContractRuntime._profile_body_contracts(
                            profile
                        )
                    },
                )
                factory = IsolatedFactory(lifetime_runtime)
                objects = dict(
                    catalog=pair.code_admission,
                    code_runtime=runtime,
                    composition_factory=factory,
                    lifetime_runtime=lifetime_runtime,
                    membership_runtime=sources.membership_runtime,
                    observation_runtime=sources.observation_runtime,
                    policy_producer=calculate_registry_policy,
                    repository_store=original._store,
                    scope_adapter=sources.scope_adapter,
                    scope_runtime=sources.scope_runtime,
                    semantic_issuer=semantic_issuer,
                )
                digest = ContentDigest.of_bytes(b"isolated-conformance-only")
                expected = DirectCommandExpectedContext(
                    lifetime_runtime.invocation_identity,
                    lifetime_runtime.epoch_identity,
                    os.getpid(),
                    runtime,
                    pair.code_admission,
                    SemanticImplementationCoordinate("fixture-composition", digest),
                    SemanticConfigurationCoordinate("fixture-composition", digest),
                    SemanticImplementationCoordinate("fixture-policy", digest),
                    SemanticConfigurationCoordinate("fixture-policy", digest),
                    tuple(
                        DirectCommandResourceBinding(role, objects[role], "borrowed")
                        for role in RESOURCE_ROLES
                    ),
                )
                lifetime = lifetime_runtime.bind_command_lifetime(expected=expected)
                factory.expected = expected
                bootstrap = direct_host._assemble_direct_command_bootstrap(
                    lifetime=lifetime, expected=expected
                )
                host = direct_host.register_direct_workspace_origin(bootstrap, lifetime)
                yield (
                    root,
                    sources,
                    lifetime_runtime,
                    lifetime,
                    expected,
                    joint,
                    host,
                    factory,
                )
            finally:
                lifetime_runtime.close()
                if host is not None:
                    direct_host.close_direct_validation_host(host)
                semantic_issuer.close()
                parent.live = False
                joint.close()


async def test_real_lifetime_scope_and_joint_catalog_produce_bound_policy(tmp_path):
    async with assembly(tmp_path) as (_, sources, owner, _, _, _, host, factory):
        admission = direct_host.produce_registry_policy(host, sources.scope_snapshot)
        policy = direct_host.validate_admitted_registry_policy(host, admission)
        projection = sources.scope_adapter.read_complete_scope_projection(
            sources.scope_snapshot
        )
        assert policy.declaration_scope_digest == projection.projection_digest
        assert len(policy.grants) == 1
        assert factory.calls == 1
        owner.close()
        with pytest.raises((ContractViolation, RuntimeError)):
            direct_host.validate_admitted_registry_policy(host, admission)


@pytest.mark.parametrize(
    "change", ["source", "scope_close", "catalog_close", "factory", "resource"]
)
async def test_original_dependencies_remain_required(tmp_path, change, monkeypatch):
    async with assembly(tmp_path) as (
        root,
        sources,
        _,
        _,
        expected,
        joint,
        host,
        factory,
    ):
        admission = direct_host.produce_registry_policy(host, sources.scope_snapshot)
        if change == "source":
            (root / "demo/home/aware.demo.toml").write_bytes(b"changed")
        elif change == "scope_close":
            sources.scope_runtime.close()
        elif change == "catalog_close":
            joint.close()
        elif change == "factory":
            monkeypatch.setattr(
                factory, "create_direct_semantic_origin", lambda value: None
            )
        else:
            resources = tuple(
                replace(b, resource=object()) if b.role == "repository_store" else b
                for b in expected.resources
            )
            object.__setattr__(expected, "resources", resources)
        with pytest.raises((ContractViolation, RuntimeError)):
            direct_host.validate_admitted_registry_policy(host, admission)


async def test_lifetime_closes_during_calculation_no_usable_policy(
    tmp_path, monkeypatch
):
    async with assembly(tmp_path) as (_, sources, owner, _, _, _, host, _):
        original = direct_host.calculate_registry_policy

        def close_during(scope, catalog):
            value = original(scope, catalog)
            owner.close()
            return value

        monkeypatch.setattr(direct_host, "calculate_registry_policy", close_during)
        with pytest.raises((ContractViolation, RuntimeError)):
            direct_host.produce_registry_policy(host, sources.scope_snapshot)
