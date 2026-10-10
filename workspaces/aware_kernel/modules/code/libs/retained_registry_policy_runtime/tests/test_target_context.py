"""Code original mechanics with an isolated owner validator, not Workspace trust."""

import copy
from contextlib import contextmanager
from dataclasses import fields, replace
from types import SimpleNamespace

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import operation_context as contexts
from aware_code_retained_registry_policy_runtime import target_context as target
from aware_code_semantic_contract_runtime import ContentDigest
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    DirectCommandResourceBinding,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
    _issue_code_semantic_contract_catalog,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    PackageContextInputCodec,
)
from test_calculation import _catalog
from test_contracts import SOURCE
from test_direct_host import Owner
from test_materialization_catalog import _execution_closure
from test_operation_context import setup as source_setup


class TargetOwner:
    def __init__(self, observation, membership, package, identity):
        self.observation_runtime = observation
        self.membership_runtime = membership
        self.package = package
        self.identity = identity
        self.inventory = object()
        self.target = object()
        self.live = True
        self.calls = 0
        self.change_expected = False

    def validate_dependency_target_admission(
        self, admission, *, inventory_admission, expected
    ):
        self.calls += 1
        if (
            not self.live
            or admission is not self.target
            or inventory_admission is not self.inventory
            or expected.target_package != self.package
            or expected.target_source_identity_digest != self.identity
        ):
            raise ContractViolation("original fixture target unavailable")
        if self.change_expected:
            object.__setattr__(expected.target_package, "package_ref", "foreign@1")


def assembled(*, manifest_supported=True):
    previous = source_setup()
    old_owner, old_host, _, _, registration, request = previous
    old_state = direct._state(old_host)
    owner = Owner(old_owner.projection)
    source = contexts._decode(request.package_context, PackageContextInputCodec())
    resources = {b.role: b.resource for b in old_state.expected.resources}
    issuer = TargetOwner(
        resources["observation_runtime"],
        resources["membership_runtime"],
        source.package,
        source.source_identity_digest,
    )
    entries = []
    for entry in old_state.check().entries:
        values = {
            f.name: getattr(entry, f.name)
            for f in fields(entry)
            if f.name != "binding_digest"
        }
        if entry.profile_declaration.profile_ref == "planning" and manifest_supported:
            values["manifest_contracts"] = (SOURCE,)
        entries.append(CodeSemanticMaterializationProfileBinding.create(**values))
    catalog = _catalog(*entries)
    providers, planners = _execution_closure(catalog)
    admitted = _issue_code_semantic_contract_catalog(
        catalog=catalog,
        provider_executable_bindings=providers,
        dependency_planner_bindings=planners,
        host_liveness=lambda: owner.catalog_live,
    )
    resources.update(
        lifetime_runtime=owner,
        composition_factory=owner,
        scope_adapter=owner,
        semantic_issuer=issuer,
        catalog=admitted,
    )
    owner.expected = replace(
        old_state.expected,
        invocation_identity=object(),
        epoch_identity=object(),
        catalog=admitted,
        resources=tuple(
            DirectCommandResourceBinding(role, resource, "borrowed")
            for role, resource in sorted(resources.items())
        ),
    )
    bootstrap = direct._assemble_direct_command_bootstrap(
        lifetime=owner.lifetime, expected=owner.expected
    )
    host = direct.register_direct_workspace_origin(bootstrap, owner.lifetime)
    policy = direct.produce_registry_policy(host, owner.snapshot)
    context = contexts.begin_source_planning_operation(
        host, policy, registration, request
    )
    origin = target.assemble_target_context_origin(host)
    direct.close_direct_validation_host(old_host)
    return owner, host, context, issuer, origin


def issue(values):
    _, _, context, issuer, origin = values
    return origin.issue(
        context,
        issuer.inventory,
        issuer.target,
        target_source_identity_digest=issuer.identity,
        target_package=issuer.package,
    )


def read(values, admission, **changes):
    _, _, context, issuer, origin = values
    args = {
        "source_context": context,
        "inventory_admission": issuer.inventory,
        "target_admission": issuer.target,
    }
    args.update(changes)
    return origin.read(admission, **args)


def test_original_target_context_is_detached_and_revalidated():
    values = assembled()
    _, host, _, issuer, origin = values
    try:
        admission = issue(values)
        result = read(values, admission)
        assert (
            result.package_family,
            result.package_role,
            result.manifest_contract,
        ) == ("public", "sdk", SOURCE)
        object.__setattr__(result.manifest_contract, "version", "substitute")
        assert read(values, admission).manifest_contract.version == "1"
        assert issuer.calls >= 6
        for field in ("source_context", "inventory_admission", "target_admission"):
            with pytest.raises(ContractViolation):
                read(values, admission, **{field: object()})
        with pytest.raises(ContractViolation):
            read(values, object.__new__(target.TargetContextAdmission))
        with pytest.raises(TypeError):
            copy.copy(admission)
        with pytest.raises(ContractViolation):
            target.assemble_target_context_origin(host)
        with pytest.raises(ContractViolation):
            target.assemble_target_context_origin(
                object.__new__(direct.DirectValidationHost)
            )
        assert read(values, admission).package_role == "sdk"
        assert origin is not None
    finally:
        direct.close_direct_validation_host(host)


def test_qualified_target_derivation_brackets_recursive_code_reads(monkeypatch):
    values = assembled()
    _, host, context, issuer, _ = values
    events = []

    @contextmanager
    def validation_window(actual_host, actual_context):
        assert actual_host is host and actual_context is context
        events.append("validate_enter")
        try:
            yield
        finally:
            events.append("validate_exit")

    @contextmanager
    def read_session(actual_host, policy):
        assert actual_host is host and policy is contexts._CONTEXTS[context].policy
        events.append("session_enter")
        try:
            yield object()
        finally:
            events.append("session_exit")

    @contextmanager
    def policy_source(actual_host, policy, *, purpose):
        assert actual_host is host and policy is contexts._CONTEXTS[context].policy
        assert purpose == "source_planning"
        events.append("policy_enter")
        try:
            yield object()
        finally:
            events.append("policy_exit")

    def derive_body(*args, **kwargs):
        events.append("body")
        return "derived"

    from aware_code_retained_registry_policy_runtime import qualified_host

    monkeypatch.setattr(contexts, "_synchronous_validation_window", validation_window)
    monkeypatch.setattr(qualified_host, "operation_local_read_session", read_session)
    monkeypatch.setattr(qualified_host, "policy_source", policy_source)
    monkeypatch.setattr(target, "_derive_body", derive_body)
    state = SimpleNamespace(host=host, check=lambda: SimpleNamespace(qualified=True))
    try:
        assert (
            target._derive(
                state,
                context,
                issuer.inventory,
                issuer.target,
                issuer.identity,
                issuer.package,
            )
            == "derived"
        )
        assert events == [
            "validate_enter",
            "session_enter",
            "policy_enter",
            "body",
            "policy_exit",
            "session_exit",
            "validate_exit",
        ]
    finally:
        direct.close_direct_validation_host(host)


@pytest.mark.parametrize(
    "change",
    [
        "target",
        "scope",
        "catalog",
        "lifetime",
        "method",
        "resource",
        "origin_method",
        "process",
        "expected",
    ],
)
def test_changed_original_evidence_rejects(change, monkeypatch):
    values = assembled()
    owner, host, _, issuer, origin = values
    admission = issue(values)
    if change == "target":
        issuer.live = False
    elif change == "scope":
        owner.projection = replace(
            owner.projection,
            observation_digest=ContentDigest.of_bytes(b"changed"),
        )
    elif change == "catalog":
        owner.catalog_live = False
    elif change == "lifetime":
        owner.live = False
    elif change == "method":
        monkeypatch.setattr(
            issuer, "validate_dependency_target_admission", lambda *a, **k: None
        )
    elif change == "resource":
        issuer.membership_runtime = object()
    elif change == "origin_method":
        monkeypatch.setattr(origin, "issue", lambda *a, **k: None)
    elif change == "process":
        monkeypatch.setattr(target.os, "getpid", lambda: -1)
    else:
        issuer.change_expected = True
    with pytest.raises(ContractViolation):
        read(values, admission)
    monkeypatch.undo()
    direct.close_direct_validation_host(host)


def test_missing_manifest_correspondence_and_wrong_coordinates_reject():
    values = assembled(manifest_supported=False)
    _, host, context, issuer, origin = values
    try:
        with pytest.raises(ContractViolation, match="manifest_source"):
            issue(values)
        with pytest.raises(ContractViolation):
            origin.issue(
                context,
                issuer.inventory,
                issuer.target,
                target_source_identity_digest=issuer.identity,
                target_package=replace(issuer.package, package_ref="foreign@1"),
            )
    finally:
        direct.close_direct_validation_host(host)


def test_parent_closure_during_publication_rejects():
    values = assembled()
    owner, host, _, _, _ = values
    owner.close_on_acquire = True
    with pytest.raises(ContractViolation):
        issue(values)
    direct.close_direct_validation_host(host)


def source_issue(values):
    _, _, context, issuer, origin = values
    return origin.issue_source(
        context,
        issuer.inventory,
        issuer.target,
        target_source_identity_digest=issuer.identity,
        target_package=issuer.package,
    )


def source_read(values, admission):
    _, _, context, issuer, origin = values
    return origin.read_source(
        admission,
        source_context=context,
        inventory_admission=issuer.inventory,
        target_admission=issuer.target,
    )


def test_source_registration_needs_no_target_capability_correspondence(monkeypatch):
    values = assembled(manifest_supported=False)
    _, host, _, issuer, _ = values
    try:

        def unavailable(*args, **kwargs):
            raise ContractViolation("target executable catalog unavailable")

        monkeypatch.setattr(target, "_catalog_correspondence", unavailable)
        admission = source_issue(values)
        result = source_read(values, admission)
        assert result.package_family == "public"
        assert result.package_role == "sdk"
        assert result.semantic_provider_key == "planning_test"
        assert result.semantic_package_kind == "sdk"
        assert result.manifest_filename == "aware.demo.toml"
        assert not hasattr(result, "manifest_contract")
        object.__setattr__(result, "package_role", "foreign")
        assert source_read(values, admission).package_role == "sdk"
        assert issuer.calls >= 6
        with pytest.raises(ContractViolation, match="target executable"):
            issue(values)
    finally:
        direct.close_direct_validation_host(host)


def test_source_and_result_contexts_cannot_be_interchanged():
    values = assembled()
    _, host, _, _, _ = values
    try:
        source = source_issue(values)
        result = issue(values)
        with pytest.raises(TypeError):
            read(values, source)
        with pytest.raises(TypeError):
            source_read(values, result)
        with pytest.raises(TypeError):
            copy.copy(source)
        with pytest.raises(ContractViolation):
            source_read(values, object.__new__(target.SourceTargetContextAdmission))
    finally:
        direct.close_direct_validation_host(host)


@pytest.mark.parametrize(
    "change", ["target", "scope", "lifetime", "method", "expected"]
)
def test_source_registration_revalidates_original_evidence(change, monkeypatch):
    values = assembled()
    owner, host, _, issuer, _ = values
    admission = source_issue(values)
    if change == "target":
        issuer.live = False
    elif change == "scope":
        owner.projection = replace(
            owner.projection,
            observation_digest=ContentDigest.of_bytes(b"changed"),
        )
    elif change == "lifetime":
        owner.live = False
    elif change == "method":
        monkeypatch.setattr(
            issuer, "validate_dependency_target_admission", lambda *a, **k: None
        )
    else:
        issuer.change_expected = True
    try:
        with pytest.raises(ContractViolation):
            source_read(values, admission)
    finally:
        monkeypatch.undo()
        direct.close_direct_validation_host(host)
