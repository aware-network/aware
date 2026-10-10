"""Real Workspace handles behind a fixture Code parent; no installed-host claim."""

import copy
from contextlib import asynccontextmanager
from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import operation_context as contexts
from aware_code_retained_registry_policy_runtime.retained_input_admission import (
    assemble_retained_input_admission_origin,
)
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    DirectCommandResourceBinding,
)
from aware_workspace_runtime import SourceObservationUnavailable
from test_direct_host import Owner
from test_semantic_issuer_factory import assembled as workspace_assembled

pytestmark = pytest.mark.asyncio


@asynccontextmanager
async def assembled(tmp_path, *, owner_type=Owner, before_policy=None):
    async with workspace_assembled(tmp_path) as (
        root,
        issuer,
        membership,
        old_context,
        _,
        _,
        old_host,
        _,
    ):
        old_state = direct._state(old_host)
        record = contexts._CONTEXTS[old_context]
        owner = owner_type(old_state.methods["read"].receiver.projection)
        resources = {r.role: r.resource for r in old_state.expected.resources}
        resources.update(
            lifetime_runtime=owner,
            composition_factory=owner,
            scope_adapter=owner,
            semantic_issuer=issuer,
            observation_runtime=issuer.observation_runtime,
            membership_runtime=issuer.membership_runtime,
        )
        owner.expected = replace(
            old_state.expected,
            invocation_identity=object(),
            epoch_identity=object(),
            resources=tuple(
                DirectCommandResourceBinding(role, resource, "borrowed")
                for role, resource in sorted(resources.items())
            ),
        )
        bootstrap = direct._assemble_direct_command_bootstrap(
            lifetime=owner.lifetime, expected=owner.expected
        )
        host = direct.register_direct_workspace_origin(bootstrap, owner.lifetime)
        try:
            if before_policy is not None:
                before_policy(owner, host)
            policy = direct.produce_registry_policy(host, owner.snapshot)
            context = contexts.begin_source_planning_operation(
                host, policy, record.registration, record.request
            )
            expected = contexts.source_planning_expectation(host, context)
            issuer._bind_original_code_validator(
                contexts.source_planning_context_validator(host)
            )
            package, inventory = issuer.issue_source_planning_pair(
                membership, context=context, expected=expected
            )
            origin = assemble_retained_input_admission_origin(host)
            yield (
                root,
                owner,
                host,
                issuer,
                origin,
                context,
                expected,
                package,
                inventory,
            )
        finally:
            direct.close_direct_validation_host(host)


async def test_real_three_admissions_join_and_revalidate(tmp_path):
    async with assembled(tmp_path) as (
        _,
        _,
        host,
        _,
        origin,
        context,
        expected,
        package,
        inventory,
    ):
        registry = origin.issue_registry_package_admission(context, package)
        origin.validate_registry_package_admission(registry, expected=expected)
        joined = origin.join(context, registry, package, inventory)
        origin.validate(joined)
        origin.validate(joined)
        for value, validate in (
            (
                registry,
                lambda v: origin.validate_registry_package_admission(
                    v, expected=expected
                ),
            ),
            (joined, origin.validate),
        ):
            with pytest.raises(ContractViolation, match="foreign"):
                validate(object.__new__(type(value)))
        with pytest.raises(ContractViolation, match="replay"):
            assemble_retained_input_admission_origin(host)
        for value in (registry, joined):
            with pytest.raises(TypeError):
                copy.copy(value)
        direct.close_direct_validation_host(host)
        with pytest.raises(ContractViolation):
            origin.validate(joined)


async def test_foreign_inventory_never_joins(tmp_path):
    async with assembled(tmp_path) as (_, _, _, _, origin, context, _, package, _):
        registry = origin.issue_registry_package_admission(context, package)
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            origin.join(context, registry, package, object())


async def test_foreign_package_never_issues_registry(tmp_path):
    async with assembled(tmp_path) as (_, _, _, _, origin, context, _, _, _):
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            origin.issue_registry_package_admission(context, object())


async def test_registry_and_join_replay_reject(tmp_path):
    async with assembled(tmp_path) as (
        _,
        _,
        _,
        _,
        origin,
        context,
        _,
        package,
        inventory,
    ):
        registry = origin.issue_registry_package_admission(context, package)
        with pytest.raises(ContractViolation, match="replay"):
            origin.issue_registry_package_admission(context, package)
        joined = origin.join(context, registry, package, inventory)
        with pytest.raises(ContractViolation, match="replay"):
            origin.join(context, registry, package, inventory)
        origin.validate(joined)


async def test_original_workspace_method_substitution_refuses(tmp_path):
    async with assembled(tmp_path) as (_, _, _, issuer, origin, context, _, package, _):
        issuer.validate_package_context_admission = lambda *a, **kw: None
        with pytest.raises(ContractViolation, match="substituted"):
            origin.issue_registry_package_admission(context, package)


async def test_changed_retained_source_invalidates_join(tmp_path):
    async with assembled(tmp_path) as (
        root,
        _,
        _,
        _,
        origin,
        context,
        _,
        package,
        inventory,
    ):
        registry = origin.issue_registry_package_admission(context, package)
        joined = origin.join(context, registry, package, inventory)
        (root / "demo/home/aware.demo.toml").write_bytes(b"changed")
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            origin.validate(joined)


async def test_fork_rejects_before_parent_acquisition(tmp_path, monkeypatch):
    import os

    async with assembled(tmp_path) as (_, _, _, _, origin, context, _, package, _):
        parent_pid = os.getpid()
        monkeypatch.setattr(os, "getpid", lambda: parent_pid + 1)
        try:
            with pytest.raises(ContractViolation, match="process"):
                origin.issue_registry_package_admission(context, package)
        finally:
            monkeypatch.undo()


async def test_issuer_resource_substitution_refuses(tmp_path):
    async with assembled(tmp_path) as (_, _, _, issuer, origin, context, _, package, _):
        original = issuer._membership_runtime
        issuer._membership_runtime = object()
        try:
            with pytest.raises(ContractViolation, match="resource substituted"):
                origin.issue_registry_package_admission(context, package)
        finally:
            issuer._membership_runtime = original


@pytest.mark.parametrize("operation", ["join", "validate"])
async def test_context_revocation_during_inventory_validation_rejects(
    tmp_path, monkeypatch, operation
):
    async with assembled(tmp_path) as (
        _root,
        _,
        _,
        issuer,
        origin,
        context,
        _,
        package,
        inventory,
    ):
        registry = origin.issue_registry_package_admission(context, package)
        joined = (
            origin.join(context, registry, package, inventory)
            if operation == "validate"
            else None
        )
        original = issuer._validate

        def change(admission, expected, kind):
            result = original(admission, expected, kind)
            if admission is inventory:
                contexts._CONTEXTS.pop(context, None)
            return result

        monkeypatch.setattr(issuer, "_validate", change)
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            if operation == "join":
                origin.join(context, registry, package, inventory)
            else:
                origin.validate(joined)


async def test_registry_record_replacement_during_owner_validation_rejects(
    tmp_path, monkeypatch
):
    from aware_code_retained_registry_policy_runtime import (
        retained_input_admission as admissions,
    )

    async with assembled(tmp_path) as (
        _,
        _,
        _,
        issuer,
        origin,
        context,
        expected,
        package,
        _inventory,
    ):
        registry = origin.issue_registry_package_admission(context, package)
        state = admissions._ORIGINS[origin]
        original = issuer._validate

        def change(admission, comparison, kind):
            result = original(admission, comparison, kind)
            state.registries[registry] = (*state.registries[registry],)
            return result

        monkeypatch.setattr(issuer, "_validate", change)
        with pytest.raises(
            ContractViolation, match="original registry context changed"
        ):
            origin.validate_registry_package_admission(registry, expected=expected)


async def test_missing_expected_context_refuses_before_owner_contact(
    tmp_path, monkeypatch
):
    async with assembled(tmp_path) as (_, _, _, issuer, origin, context, _, package, _):
        registry = origin.issue_registry_package_admission(context, package)

        def forbidden(*args, **kwargs):
            raise AssertionError("invalid expected value contacted owner")

        monkeypatch.setattr(issuer, "_validate", forbidden)
        with pytest.raises(TypeError, match="exact retained semantic expectation"):
            origin.validate_registry_package_admission(registry, expected=None)


async def test_registry_uses_one_complete_original_assignment_interval(
    tmp_path, monkeypatch
):
    async with assembled(tmp_path) as (_, _, _, issuer, origin, context, _, package, _):
        calls = []
        original = type(issuer)._validate

        def count_original(self, admission, expected, kind):
            calls.append(admission)
            return original(self, admission, expected, kind)

        monkeypatch.setattr(type(issuer), "_validate", count_original)
        origin.issue_registry_package_admission(context, package)
        assert calls == [package]


async def test_joined_validation_coalesces_adjacent_owner_callbacks(
    tmp_path, monkeypatch
):
    from aware_code_retained_registry_policy_runtime import (
        retained_input_admission as admissions,
    )

    async with assembled(tmp_path) as (
        _,
        _,
        _,
        _,
        origin,
        context,
        _,
        package,
        inventory,
    ):
        registry = origin.issue_registry_package_admission(context, package)
        joined = origin.join(context, registry, package, inventory)
        original = admissions._expectation
        calls = []

        def count(host, current):
            calls.append(current)
            return original(host, current)

        monkeypatch.setattr(admissions, "_expectation", count)
        origin.validate(joined)
        assert calls == [context, context]
