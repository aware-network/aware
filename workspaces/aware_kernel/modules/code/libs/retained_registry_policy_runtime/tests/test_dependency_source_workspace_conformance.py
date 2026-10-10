"""Real owner source and Code use; fixture catalog/factory, not fixed bootstrap."""

import asyncio
import importlib.util
from dataclasses import replace
from pathlib import Path

import pytest
from aware_code_retained_registry_policy_runtime import (
    dependency_scope_operation as ops,
)
from aware_code_retained_registry_policy_runtime import direct_host as hosts
from aware_code_retained_registry_policy_runtime.dependency_source_binding import (
    _bind_dependency_source,
    _capture_dependency_source,
)
from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
    _guard,
    _policy_epoch_use,
)
from aware_workspace_runtime.dependency_scope_operations import (
    _install_operation_origin,
)
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable
from test_direct_epoch_tracking import Owner, setup


def workspace_fixture(tmp_path):
    # Load the exact owner fixture without adding Workspace's test directory to
    # import search order (both owners have a test_contracts.py).
    path = (
        Path(__file__).resolve().parents[7]
        / "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_dependency_scope_admission.py"
    )
    spec = importlib.util.spec_from_file_location("workspace_dependency_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.fixture(tmp_path)


@pytest.mark.parametrize("purpose", ["source_planning", "authority_derivation"])
def test_real_preparation_bind_read_and_retirement(tmp_path, monkeypatch, purpose):
    asyncio.run(run_real_preparation(tmp_path, monkeypatch, purpose))


async def run_real_preparation(tmp_path, monkeypatch, purpose):
    async with workspace_fixture(tmp_path) as (
        _,
        source_runtime,
        observation,
        _,
        _,
        lifetime,
    ):
        source = source_runtime.capture(
            observation=observation, consumer_scope_key="consumer/aware.workspace.toml"
        )
        exclusion = source_runtime._exclusion
        original_init = Owner.__init__

        def initialize(owner, projection):
            original_init(owner, projection)
            owner.parent = exclusion._parent

        def acquire(owner, parent, *, expected):
            assert parent is exclusion._parent
            return lifetime.acquire_catalog_epoch_exclusion(parent, expected=expected)

        def validate(owner, guard, *, parent, expected):
            return lifetime.validate_catalog_epoch_exclusion(
                guard, parent=parent, expected=expected
            )

        def release(owner, guard):
            return lifetime.release_catalog_epoch_exclusion(guard)

        monkeypatch.setattr(Owner, "__init__", initialize)
        monkeypatch.setattr(Owner, "acquire_catalog_epoch_exclusion", acquire)
        monkeypatch.setattr(Owner, "validate_catalog_epoch_exclusion", validate)
        monkeypatch.setattr(Owner, "release_catalog_epoch_exclusion", release)
        original_assemble = hosts._assemble_direct_command_bootstrap

        def assemble(*, lifetime: object, expected):
            # The fixture catalog owner supplies context before Code bootstrap.
            # Actual source and epoch participant share the original parent guard.
            object.__setattr__(
                expected, "invocation_identity", exclusion._expected.invocation_identity
            )
            object.__setattr__(
                expected, "epoch_identity", exclusion._expected.lifetime_epoch_identity
            )
            object.__setattr__(
                expected,
                "resources",
                tuple(
                    replace(b, resource=source_runtime)
                    if b.role == "scope_runtime"
                    else b
                    for b in expected.resources
                ),
            )
            return original_assemble(lifetime=lifetime, expected=expected)

        monkeypatch.setattr(hosts, "_assemble_direct_command_bootstrap", assemble)
        owner, host, _ = setup(monkeypatch)
        validator = ops._create_dependency_scope_operation_validator(host)
        _install_operation_origin(
            source_runtime, validator=validator, epoch=owner.current
        )
        retained = _capture_dependency_source(validator, source)
        with _policy_epoch_use(host) as (binding, use):
            with _bind_dependency_source(retained, use, purpose=purpose) as bound:
                closure = bound.read()
                assert bound.expected.repository_membership_identity is observation
                assert bound.expected.closure_runtime_identity is source_runtime
                assert bound.expected.epoch_identity is owner.current
                assert len(closure.edges) == 1
                with _guard(binding) as guard:
                    bound.check_locked(
                        closure_digest=closure.closure_digest, guard=guard
                    )
            with pytest.raises(SourceObservationUnavailable):
                source_runtime.read_dependency_scope_closure(
                    source, expected=bound.expected
                )
        assert (
            source_runtime.read_preliminary_closure(source).closure_digest
            == closure.closure_digest
        )
        assert not ops._STATES[validator].operations
