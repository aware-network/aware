"""Qualified host/epoch policy with original Code mechanics and fixture owner."""

import copy
import os
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor

import pytest
import test_direct_host as local
from aware_code_retained_registry_policy_runtime import direct_host as hosts
from aware_code_retained_registry_policy_runtime import epoch_participation as epochs
from aware_code_retained_registry_policy_runtime import qualified_host as qualified_module
from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
    _bind_direct_policy_epoch,
)
from aware_code_retained_registry_policy_runtime.qualified_calculation import (
    calculate_qualified_registry_policy,
)
from aware_code_retained_registry_policy_runtime.qualified_host import (
    _qualified_dependency_validator,
    operation_local_read_session,
    policy_source,
)
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    CatalogPublicationExpectation,
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from test_dependency_source_binding import SourceOwner
from test_direct_epoch_tracking import Owner, clearance
from test_profile_membership import fixture as closure_fixture


def qualified_closure(scope, provider_key="demo"):
    base = closure_fixture()
    module = scope.modules[0]
    raw = module.manifest.body.replace(b"aware = 2", b"aware = 3", 1).replace(
        b'value={module_id="demo", package_id="provider", registration_key="demo"}',
        b'value={scope={kind="dependency", workspace_handle="target"}, module_id="demo", package_id="provider", registration_key="demo"}',
    )
    consumer = replace(
        scope,
        modules=(
            replace(
                module,
                manifest=replace(
                    module.manifest,
                    body=raw,
                    content_digest=ContentDigest.of_bytes(raw),
                ),
            ),
        ),
    )
    raw = module.manifest.body.replace(b'value="home"', b'value="target_home"').replace(
        b'value=["home"]', b'value=["target_home"]'
    )
    target = replace(
        scope,
        modules=(
            replace(
                module,
                manifest=replace(
                    module.manifest,
                    body=raw,
                    content_digest=ContentDigest.of_bytes(raw),
                ),
            ),
        ),
        packages=tuple(
            replace(
                p,
                source_identity_digest=ContentDigest.of_bytes(
                    b"target:" + p.package_id.encode()
                ),
            )
            for p in scope.packages
        ),
    )
    edge = replace(
        base.edges[0],
        semantic_contract_provider_keys=replace(
            base.edges[0].semantic_contract_provider_keys, value=(provider_key,)
        ),
    )
    association = base.profile_associations[0]
    raw = association.manifest.body.replace(
        b'provider_key = "demo"', f'provider_key = "{provider_key}"'.encode()
    )
    association = replace(
        association,
        manifest=replace(
            association.manifest, body=raw, content_digest=ContentDigest.of_bytes(raw)
        ),
    )
    return replace(
        base,
        scopes=(
            replace(base.scopes[0], projection=consumer),
            replace(base.scopes[1], projection=target),
        ),
        edges=(edge,),
        profile_associations=(association,),
    )


def bind_epoch(owner, host, source):
    invocation = DirectInvocationExpectation(
        owner.expected.invocation_identity, owner.expected.epoch_identity, os.getpid()
    )
    digest = ContentDigest.of_bytes(b"qualified-epoch-fixture")
    owner.epoch = CatalogPairEpochExpectation(
        invocation, object(), hosts._HOSTS[host].catalog_digest, digest, digest
    )
    owner.successor = CatalogPublicationExpectation(
        object(),
        owner.epoch,
        replace(owner.epoch, publication_identity=object()),
        digest,
    )
    guard = owner.acquire_catalog_epoch_exclusion(owner.parent, expected=invocation)
    try:
        participant = epochs._assemble_code_epoch_participation(
            owner=owner,
            parent=owner.parent,
            invocation=invocation,
            epoch_owner=owner,
            guard=guard,
        )
        _bind_direct_policy_epoch(
            host,
            participant,
            owner.current,
            expected=owner.epoch,
            guard=guard,
            dependency_source=source.source,
        )
    finally:
        owner.release_catalog_epoch_exclusion(guard)
    source.validator = _qualified_dependency_validator(host)
    owner.participant = participant


def upgrade(monkeypatch, *, stages_only=False, provider_key="demo"):
    assemble = hosts._assemble_direct_command_bootstrap
    register = hosts.register_direct_workspace_origin

    def qualified_assemble(*, lifetime, expected):
        if stages_only and not expected.stage_runtime_bindings:
            return assemble(lifetime=lifetime, expected=expected)
        resources = {b.role: b.resource for b in expected.resources}
        owner = resources["composition_factory"]
        source = SourceOwner()
        source.source = owner.snapshot
        source.closure = qualified_closure(owner.projection, provider_key)
        owner.source = source
        replacements = {
            "scope_runtime": source,
            "scope_adapter": source,
            "policy_producer": calculate_qualified_registry_policy,
        }
        object.__setattr__(
            expected,
            "resources",
            tuple(
                replace(b, resource=replacements[b.role])
                if b.role in replacements
                else b
                for b in expected.resources
            ),
        )
        return assemble(lifetime=lifetime, expected=expected)

    def qualified_register(bootstrap, lifetime):
        host = register(bootstrap, lifetime)
        state = hosts._HOSTS[host]
        if state.qualified:
            owner = state.methods["factory"].receiver
            bind_epoch(owner, host, owner.source)
        return host

    monkeypatch.setattr(hosts, "_assemble_direct_command_bootstrap", qualified_assemble)
    monkeypatch.setattr(hosts, "register_direct_workspace_origin", qualified_register)


def fixture(monkeypatch):
    monkeypatch.setattr(local, "Owner", Owner)
    upgrade(monkeypatch)
    return local.registered()


def test_public_host_uses_qualified_policy_and_releases_use(monkeypatch):
    owner, host = fixture(monkeypatch)
    policy = hosts.produce_registry_policy(host, owner.snapshot)
    result = hosts.validate_admitted_registry_policy(host, policy)
    assert result.declaration_scope_digest == owner.source.closure.closure_digest
    assert len(result.grants) == 2
    assert owner.source.events == ["prepare", "bind", "release"] * 2
    assert not owner.source.active
    clearance(owner, owner.participant)


def test_qualified_host_never_reads_local_source(monkeypatch):
    owner, host = fixture(monkeypatch)
    owner.read_complete_scope_projection = lambda *a, **kw: pytest.fail(
        "local fallback"
    )
    policy = hosts.produce_registry_policy(host, owner.snapshot)
    hosts.validate_admitted_registry_policy(host, policy)


def test_operation_local_session_reuses_one_original_source_read(monkeypatch):
    reads = []
    original_read = SourceOwner.read_dependency_scope_closure

    def count_read(self, *args, **kwargs):
        reads.append(1)
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr(SourceOwner, "read_dependency_scope_closure", count_read)
    owner, host = fixture(monkeypatch)
    policy = hosts.produce_registry_policy(host, owner.snapshot)
    with operation_local_read_session(host, policy) as session:
        assert session is not None
        with policy_source(host, policy, purpose="policy_validation") as (
            _state,
            first,
            _admitted,
        ):
            assert first is owner.source.closure
        with policy_source(host, policy, purpose="authority_derivation") as (
            _state,
            second,
            _admitted,
        ):
            assert second is first
    # One source use belongs to policy production and one to the session. The
    # two session consumers do not bind or release a second owner operation.
    assert owner.source.events == ["prepare", "bind", "release"] * 2
    assert len(reads) == 2
    assert not owner.source.active
    clearance(owner, owner.participant)


def test_operation_local_session_rejects_foreign_and_replayed_use(monkeypatch):
    owner, host = fixture(monkeypatch)
    policy = hosts.produce_registry_policy(host, owner.snapshot)
    with operation_local_read_session(host, policy) as session:
        with pytest.raises(ContractViolation):
            with policy_source(
                host, policy, purpose="policy_validation", session=object()
            ):
                pass
        with pytest.raises(ContractViolation):
            with policy_source(
                object(), policy, purpose="policy_validation", session=session
            ):
                pass
    with pytest.raises(ContractViolation):
        with policy_source(host, policy, purpose="policy_validation", session=session):
            pass
    assert not owner.source.active
    clearance(owner, owner.participant)


def test_operation_local_session_rejects_process_change(monkeypatch):
    owner, host = fixture(monkeypatch)
    policy = hosts.produce_registry_policy(host, owner.snapshot)
    original_pid = qualified_module.getpid
    with pytest.raises(ContractViolation, match="process or thread"):
        with operation_local_read_session(host, policy) as session:
            with monkeypatch.context() as patch:
                patch.setattr(qualified_module, "getpid", lambda: original_pid() + 1)
                with policy_source(
                    host, policy, purpose="policy_validation", session=session
                ):
                    pass
    assert hosts._HOSTS[host].closed
    assert not owner.source.active


def test_operation_local_session_rejects_epoch_close(monkeypatch):
    owner, host = fixture(monkeypatch)
    policy = hosts.produce_registry_policy(host, owner.snapshot)
    with pytest.raises(ContractViolation):
        with operation_local_read_session(host, policy):
            hosts.close_direct_validation_host(host)
    assert host not in hosts._HOSTS
    assert not owner.source.active


def test_operation_local_session_rejects_changed_closure_before_use(monkeypatch):
    owner, host = fixture(monkeypatch)
    policy = hosts.produce_registry_policy(host, owner.snapshot)
    with pytest.raises(ContractViolation):
        with operation_local_read_session(host, policy):
            owner.source.closure = replace(
                owner.source.closure, consumer_scope_key="target"
            )
            with pytest.raises(ContractViolation):
                with policy_source(host, policy, purpose="policy_validation"):
                    pass
    assert hosts._HOSTS[host].closed
    assert not owner.source.active


def test_operation_local_session_cleanup_failure_preserves_uncertainty(monkeypatch):
    owner, host = fixture(monkeypatch)
    policy = hosts.produce_registry_policy(host, owner.snapshot)
    owner.source.fail_release = True
    with pytest.raises(ValueError, match="release failed"):
        with operation_local_read_session(host, policy):
            pass
    assert any(
        use.status == "uncertain"
        for use in epochs._state(owner.participant).uses.values()
    )
    assert hosts._HOSTS[host].closed


def test_operation_local_session_rejects_copy_and_cross_thread_use(monkeypatch):
    owner, host = fixture(monkeypatch)
    policy = hosts.produce_registry_policy(host, owner.snapshot)
    with operation_local_read_session(host, policy) as session:
        with pytest.raises(TypeError):
            copy.copy(session)

        def consume_on_other_thread():
            with policy_source(
                host, policy, purpose="policy_validation", session=session
            ):
                pass

        with ThreadPoolExecutor(max_workers=1) as executor:
            with pytest.raises(ContractViolation):
                executor.submit(consume_on_other_thread).result()
    assert not owner.source.active
    clearance(owner, owner.participant)


def test_foreign_source_rejects(monkeypatch):
    owner, host = fixture(monkeypatch)
    with pytest.raises(ContractViolation, match="original qualified source"):
        hosts.produce_registry_policy(host, object())
    assert not owner.source.events


def test_changed_closure_revokes_policy(monkeypatch):
    owner, host = fixture(monkeypatch)
    policy = hosts.produce_registry_policy(host, owner.snapshot)
    owner.source.closure = replace(owner.source.closure, consumer_scope_key="target")
    with pytest.raises(ContractViolation):
        hosts.validate_admitted_registry_policy(host, policy)
    assert hosts._HOSTS[host].closed
    assert not owner.source.active


def test_final_locked_source_refusal_prevents_publication(monkeypatch):
    original = SourceOwner.check_dependency_scope_closure_locked

    def refuse(self, *a, **kw):
        original(self, *a, **kw)
        raise ContractViolation("retired constituent")

    monkeypatch.setattr(SourceOwner, "check_dependency_scope_closure_locked", refuse)
    owner, host = fixture(monkeypatch)
    with pytest.raises(ContractViolation, match="retired constituent"):
        hosts.produce_registry_policy(host, owner.snapshot)
    assert all(record[0] is not host for record in hosts._POLICIES.values())
    assert not owner.source.active


def test_failed_source_cleanup_does_not_leave_a_published_policy(monkeypatch):
    owner, host = fixture(monkeypatch)
    owner.source.fail_release = True
    with pytest.raises(ValueError, match="release failed"):
        hosts.produce_registry_policy(host, owner.snapshot)
    assert all(record[0] is not host for record in hosts._POLICIES.values())
    assert hosts._HOSTS[host].closed
    assert any(
        use.status == "uncertain"
        for use in epochs._state(owner.participant).uses.values()
    )


def test_epoch_binding_is_not_replayable(monkeypatch):
    owner, host = fixture(monkeypatch)
    guard = owner.acquire_catalog_epoch_exclusion(
        owner.parent, expected=owner.epoch.invocation
    )
    try:
        with pytest.raises(ContractViolation, match="replayed"):
            _bind_direct_policy_epoch(
                host,
                owner.participant,
                owner.current,
                expected=owner.epoch,
                guard=guard,
                dependency_source=owner.snapshot,
            )
    finally:
        owner.release_catalog_epoch_exclusion(guard)
