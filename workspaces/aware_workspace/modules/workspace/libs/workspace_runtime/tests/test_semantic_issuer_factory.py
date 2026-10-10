"""Real nominal Code contexts with real retained Workspace source.

Code's parent fixture remains isolated; this proves issuer mechanics, not installed
or fixed-application trust. The Workspace issuer never invokes the isolated factory.
"""

from contextlib import asynccontextmanager
from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import direct_host
from aware_code_retained_registry_policy_runtime import operation_context as op
from aware_code_semantic_contract_runtime import ContractViolation
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    retained_projection_body,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    semantic_candidate_listing_body,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime.semantic_issuer_factory import (
    WorkspaceSourcePlanningSemanticIssuerRuntime,
)
from test_direct_command_composition import fenced_direct_sources
from test_observed_membership import fixture as repository_fixture
from test_operation_context import setup as code_setup


@asynccontextmanager
async def assembled(tmp_path):
    owner, host, _, provider, registration, request = code_setup()
    projection = owner.projection
    try:
        async with repository_fixture(tmp_path) as (root, session, observer, _):
            (root / "aware.workspace.toml").write_text(
                'aware=1\n[workspace]\nhandle="demo"\n'
                '[[workspace.modules]]\nid="demo"\npath="demo"\n'
            )
            for body in [
                projection.modules[0].manifest,
                *(p.manifest for p in projection.packages),
            ]:
                path = root / body.relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body.body)
            with fenced_direct_sources(
                session=session,
                store=observer._store,
                workspace_manifest_path="aware.workspace.toml",
            ) as sources:
                issuer = WorkspaceSourcePlanningSemanticIssuerRuntime._assemble(
                    observation_runtime=sources.observation_runtime,
                    membership_runtime=sources.membership_runtime,
                    observation=sources.observation,
                )
                try:
                    membership = sources.membership_runtime.admit(
                        observation=sources.observation,
                        workspace_manifest_path="aware.workspace.toml",
                        module_id="demo",
                        package_id="home",
                    )
                    context_input, inventory = issuer.inspect_inputs(membership)
                    candidates = sources.membership_runtime.evidence(
                        membership
                    ).candidate_listing
                    owner.projection = (
                        sources.scope_adapter.read_complete_scope_projection(
                            sources.scope_snapshot
                        )
                    )
                    policy = direct_host.produce_registry_policy(host, owner.snapshot)
                    request = replace(
                        request,
                        candidate_listing=semantic_candidate_listing_body(candidates),
                        package_context=retained_projection_body(context_input),
                        declaration_inventory=retained_projection_body(inventory),
                    )
                    context = op.begin_source_planning_operation(
                        host, policy, registration, request
                    )
                    expected = op.source_planning_expectation(host, context)
                    validator = op.source_planning_context_validator(host)
                    yield (
                        root,
                        issuer,
                        membership,
                        context,
                        expected,
                        validator,
                        host,
                        provider,
                    )
                finally:
                    issuer.close()
    finally:
        direct_host.close_direct_validation_host(host)


async def test_original_nominal_context_issues_both_handles(tmp_path):
    async with assembled(tmp_path) as (
        _,
        issuer,
        membership,
        context,
        expected,
        validator,
        _,
        provider,
    ):
        assert not hasattr(issuer, "issue_isolated_pair")
        assert not hasattr(issuer, "for_isolated_proof")
        with pytest.raises(SourceObservationUnavailable, match="validator_unavailable"):
            issuer.issue_source_planning_pair(
                membership, context=context, expected=expected
            )
        issuer._bind_original_code_validator(validator)
        package, inventory = issuer.issue_source_planning_pair(
            membership, context=context, expected=expected
        )
        issuer.validate_package_context_admission(package, expected=expected)
        issuer.validate_declaration_inventory_admission(inventory, expected=expected)
        issuer.validate_occurrence_assignments(
            package, expected=expected, namespace="home", owned_roots=("home",)
        )
        assert provider.calls == 0
        with pytest.raises(SourceObservationUnavailable, match="replay"):
            issuer.issue_source_planning_pair(
                membership, context=context, expected=expected
            )
        with pytest.raises(SourceObservationUnavailable, match="binding"):
            issuer._bind_original_code_validator(validator)


@pytest.mark.parametrize(
    "change",
    ["foreign", "expectation", "authority_stage", "host_closed", "source", "validator"],
)
async def test_context_and_source_fail_closed(tmp_path, change, monkeypatch):
    async with assembled(tmp_path) as (
        root,
        issuer,
        membership,
        context,
        expected,
        validator,
        host,
        _,
    ):
        issuer._bind_original_code_validator(validator)
        if change == "foreign":
            context = object()
        elif change == "expectation":
            expected = replace(expected, operation_identity=object())
        elif change == "authority_stage":
            expected = replace(expected, stage="authority_derivation")
        elif change == "host_closed":
            direct_host.close_direct_validation_host(host)
        elif change == "source":
            (root / "demo/home/aware.demo.toml").write_bytes(b"changed")
        else:
            monkeypatch.setattr(
                validator,
                "validate_retained_semantic_operation_context",
                lambda *a, **k: None,
            )
        with pytest.raises((ContractViolation, RuntimeError, TypeError)):
            issuer.issue_source_planning_pair(
                membership, context=context, expected=expected
            )


async def test_later_code_expiry_retires_both_workspace_handles(tmp_path):
    async with assembled(tmp_path) as (
        _,
        issuer,
        membership,
        context,
        expected,
        validator,
        host,
        _,
    ):
        issuer._bind_original_code_validator(validator)
        package, inventory = issuer.issue_source_planning_pair(
            membership, context=context, expected=expected
        )
        direct_host.close_direct_validation_host(host)
        with pytest.raises((ContractViolation, RuntimeError)):
            issuer.validate_package_context_admission(package, expected=expected)
        with pytest.raises(SourceObservationUnavailable, match="foreign"):
            issuer.validate_declaration_inventory_admission(
                inventory, expected=expected
            )


async def test_forked_issuer_cannot_bind_validator(tmp_path, monkeypatch):
    import os

    async with assembled(tmp_path) as (_, issuer, _, _, _, validator, _, _):
        with monkeypatch.context() as patch:
            patch.setattr(os, "getpid", lambda: -1)
            with pytest.raises(SourceObservationUnavailable, match="binding"):
                issuer._bind_original_code_validator(validator)
