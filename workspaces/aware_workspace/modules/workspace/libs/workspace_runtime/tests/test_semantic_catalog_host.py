"""Paired transaction mechanics. Inert parent fixtures are not bootstrap proof."""

import threading

import pytest
from aware_code_semantic_contract_runtime import (
    CodeSemanticContractCatalog,
    ContractViolation,
)
from aware_workspace_runtime import WorkspaceSemanticMaterializationMembershipCatalog
from aware_workspace_runtime import semantic_catalog_host as joint


class Parent:
    def __init__(self):
        self.live = True
        self.lock = threading.RLock()

    def validate_catalog_parent(self):
        if not self.live:
            raise RuntimeError("parent_closed")


def setup():
    parent = Parent()
    host = joint._assemble_authenticated_catalog_host(
        parent=parent, publication_lock=parent.lock
    )
    code = CodeSemanticContractCatalog.create(
        catalog_ref="code.empty", catalog_generation=1, entries=()
    )
    workspace = WorkspaceSemanticMaterializationMembershipCatalog.create(
        catalog_ref="workspace.empty", catalog_generation=1, entries=()
    )
    return parent, host, code, workspace


def admit(host, code, reader):
    executable_bindings, planner_bindings = (), ()
    if code.entries:
        from test_materialization_graph_planner import _DomainPlanner
        from test_semantic_materialization_publication import _Provider

        binding = code.entries[0]
        executable_bindings = tuple(
            (b.implementation, b.configuration, _Provider())
            for b in binding.provider_execution_bindings
        )
        planner_bindings = (
            (
                binding.dependency_planner_implementation,
                binding.dependency_planner_configuration,
                _DomainPlanner(binding, None),
            ),
        )
    return host.admit_catalogs(
        code_catalog=code,
        workspace_catalog_reader=reader,
        provider_executable_bindings=executable_bindings,
        dependency_planner_bindings=planner_bindings,
    )


def test_pair_published_then_revoked():
    parent, host, code, workspace = setup()
    result = admit(host, code, lambda: workspace)
    assert result.code.catalog == code
    assert result.workspace.catalog == workspace
    assert result.code.catalog is not code
    with pytest.raises(RuntimeError):
        admit(host, code, lambda: workspace)
    with parent.lock:
        parent.live = False
    host.close()
    host.close()
    for resolver in (result.code, result.workspace):
        with pytest.raises(ContractViolation):
            resolver.catalog


@pytest.mark.parametrize("stage", [2, 3, 4])
def test_movement_each_reread_rolls_back_and_is_terminal(stage):
    _, host, code, workspace = setup()
    reads = 0

    def reader():
        nonlocal reads
        reads += 1
        if reads == stage:
            return WorkspaceSemanticMaterializationMembershipCatalog.create(
                catalog_ref="workspace.empty", catalog_generation=2, entries=()
            )
        return workspace

    with pytest.raises(RuntimeError, match="source_moved"):
        admit(host, code, reader)
    with pytest.raises(RuntimeError):
        admit(host, code, lambda: workspace)


def test_cleanup_failure_still_revokes_code(monkeypatch):
    _, host, code, workspace = setup()
    result = admit(host, code, lambda: workspace)
    calls = []
    original = joint.revoke_code_catalog_leg

    def revoke_code(value):
        calls.append("code")
        original(value)

    def fail_workspace(value):
        calls.append("workspace")
        raise RuntimeError("cleanup_failure")

    monkeypatch.setattr(joint, "revoke_code_catalog_leg", revoke_code)
    monkeypatch.setattr(
        joint,
        "_revoke_workspace_semantic_materialization_membership_catalog",
        fail_workspace,
    )
    with pytest.raises(RuntimeError, match="cleanup_failure"):
        host.close()
    assert calls == ["workspace", "code"]
    for resolver in (result.code, result.workspace):
        with pytest.raises(ContractViolation):
            resolver.catalog


def test_close_before_publication_rolls_back(monkeypatch):
    parent, host, code, workspace = setup()
    captured = []
    original = joint._issue_workspace_semantic_materialization_membership_catalog

    def issue(**kw):
        child = original(**kw)
        captured.append(child)
        with parent.lock:
            parent.live = False
        return child

    monkeypatch.setattr(
        joint, "_issue_workspace_semantic_materialization_membership_catalog", issue
    )
    with pytest.raises((RuntimeError, ContractViolation)):
        admit(host, code, lambda: workspace)
    with pytest.raises(ContractViolation):
        joint.WorkspaceSemanticMaterializationMembershipResolver(captured[0])


def test_parent_method_substitution_refuses(monkeypatch):
    parent, host, code, workspace = setup()
    monkeypatch.setattr(parent, "validate_catalog_parent", lambda: None)
    with pytest.raises(RuntimeError, match="substituted"):
        admit(host, code, lambda: workspace)


def test_concurrent_admission_refuses_without_revoking_winner():
    _, host, code, workspace = setup()
    entered, proceed = threading.Event(), threading.Event()
    results, errors = [], []

    def reader():
        entered.set()
        assert proceed.wait(3)
        return workspace

    def worker():
        try:
            results.append(admit(host, code, reader))
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=worker)
    thread.start()
    try:
        assert entered.wait(3)
        with pytest.raises(RuntimeError, match="already_admitted"):
            admit(host, code, lambda: workspace)
    finally:
        proceed.set()
        thread.join(3)
    assert not thread.is_alive() and not errors
    assert results[0].code.catalog == code
    host.close()


def test_contribution_digest_preserves_original_wire():
    import hashlib
    import json

    _, host, code, workspace = setup()
    result = admit(host, code, lambda: workspace)
    payload = {
        "code_catalog_root": code.catalog_root_digest.to_wire(),
        "dependency_planners": [],
        "provider_executables": [],
        "workspace_catalog_root": workspace.catalog_root_digest.to_wire(),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    assert result.contribution_digest == "sha256:" + hashlib.sha256(encoded).hexdigest()
    host.close()


def test_close_between_publication_and_result_returns_no_pair(monkeypatch):
    parent, host, code, workspace = setup()
    entered, proceed = threading.Event(), threading.Event()
    original = joint.published_code_catalog_leg
    results, errors = [], []

    def paused(leg):
        entered.set()
        assert proceed.wait(3)
        return original(leg)

    def worker():
        try:
            results.append(admit(host, code, lambda: workspace))
        except (RuntimeError, ContractViolation) as exc:
            errors.append(exc)

    monkeypatch.setattr(joint, "published_code_catalog_leg", paused)
    thread = threading.Thread(target=worker)
    thread.start()
    try:
        assert entered.wait(3)
        with parent.lock:
            parent.live = False
        host.close()
    finally:
        proceed.set()
        thread.join(3)
    assert not thread.is_alive() and not results and len(errors) == 1


def test_parent_substitution_during_validation_rejects():
    class ChangingParent(Parent):
        def validate_catalog_parent(self):
            super().validate_catalog_parent()
            if getattr(self, "change", False):
                self.validate_catalog_parent = lambda: None

    parent = ChangingParent()
    host = joint._assemble_authenticated_catalog_host(
        parent=parent, publication_lock=parent.lock
    )
    parent.change = True
    with pytest.raises(RuntimeError, match="substituted"):
        host.validate_catalog_parent()


def command_setup():
    import os

    from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
        DirectInvocationExpectation,
    )
    from aware_workspace_runtime.command_lifetime import WorkspaceCommandLifetimeRuntime

    owner = WorkspaceCommandLifetimeRuntime()
    parent = owner._retain_direct_invocation_parent()
    invocation = DirectInvocationExpectation(
        owner.invocation_identity, owner.epoch_identity, os.getpid()
    )
    host = joint._assemble_command_catalog_host(
        owner=owner, parent=parent, invocation=invocation
    )
    from aware_code_semantic_contract_runtime import (
        CodeSemanticMaterializationProfileBinding,
        CodeSemanticRequiredResultProduct,
        ProviderExecutionBinding,
    )
    from test_materialization_graph_planner import (
        _configuration,
        _contract,
        _implementation,
    )
    from test_semantic_materialization_publication import (
        PROVIDER_CONFIGURATION,
        PROVIDER_IMPLEMENTATION,
        _profile,
    )

    profile = _profile()
    declaration = profile.providers[0]
    binding = CodeSemanticMaterializationProfileBinding.create(
        semantic_owner_key="test.sdk",
        semantic_provider_key="test.sdk",
        package_families=("public",),
        package_roles=("sdk",),
        manifest_contracts=(_contract("test.sdk.manifest"),),
        profile_declaration=profile,
        provider_execution_bindings=(
            ProviderExecutionBinding(
                declaration.provider_key,
                PROVIDER_IMPLEMENTATION,
                PROVIDER_CONFIGURATION,
            ),
        ),
        dependency_planner_contract=_contract("test.sdk.planner"),
        dependency_planner_implementation=_implementation("test.sdk.planner"),
        dependency_planner_configuration=_configuration("test.sdk.planner"),
        dependency_demand_contract=_contract("aware.code.dependency-demand"),
        dependency_target_intent_contract=_contract("aware.code.target-intent"),
        result_product_contracts=tuple(
            CodeSemanticRequiredResultProduct.create(role=v.role, contract=v.contract)
            for v in sorted(
                (
                    declaration.result_role,
                    declaration.effect_role,
                    *declaration.output_roles,
                ),
                key=lambda value: value.role,
            )
        ),
        priority=10,
    )
    code = CodeSemanticContractCatalog.create(
        catalog_ref="code.initial", catalog_generation=1, entries=(binding,)
    )
    workspace = WorkspaceSemanticMaterializationMembershipCatalog.create(
        catalog_ref="workspace.initial", catalog_generation=1, entries=()
    )
    return owner, parent, invocation, host, code, workspace


def test_original_initial_publication_retains_actual_pair():
    from dataclasses import replace

    owner, parent, invocation, host, code, workspace = command_setup()
    with pytest.raises(RuntimeError, match="unavailable"):
        host.read_initial_publication()
    result = admit(host, code, lambda: workspace)
    expected = host.read_initial_publication()
    assert expected.invocation.invocation_identity is invocation.invocation_identity
    assert (
        expected.invocation.lifetime_epoch_identity
        is invocation.lifetime_epoch_identity
    )
    assert expected.code_catalog_digest == code.catalog_root_digest
    assert expected.membership_catalog_digest == workspace.catalog_root_digest
    record = host._command_parent.current_record(expected)
    assert record.attempt.pair[0] is host._code_leg
    assert record.attempt.pair[1] is result.workspace_admission
    assert record.transfer is None and record.previous is None
    host.validate_initial_publication(
        expected,
        command_owner=owner,
        command_parent=parent,
        code_admission=result.code_admission,
        workspace_admission=result.workspace_admission,
    )
    with pytest.raises(RuntimeError):
        host.validate_initial_publication(
            replace(expected, publication_identity=object()),
            command_owner=owner,
            command_parent=parent,
            code_admission=result.code_admission,
            workspace_admission=result.workspace_admission,
        )
    assert host.read_initial_publication() is not expected
    with pytest.raises(RuntimeError):
        admit(host, code, lambda: workspace)
    owner.close()
    with pytest.raises(RuntimeError):
        host.read_initial_publication()
    host.close()
    for resolver in (result.code, result.workspace):
        with pytest.raises(ContractViolation):
            resolver.catalog


@pytest.mark.parametrize(
    "replacement", ["owner", "parent", "code", "workspace", "digest"]
)
def test_initial_publication_refuses_substitution(replacement):
    from dataclasses import replace

    from aware_code_semantic_contract_runtime import ContentDigest

    owner, parent, _, host, code, workspace = command_setup()
    result = admit(host, code, lambda: workspace)
    expected = host.read_initial_publication()
    args = dict(
        command_owner=owner,
        command_parent=parent,
        code_admission=result.code_admission,
        workspace_admission=result.workspace_admission,
    )
    if replacement == "digest":
        expected = replace(
            expected, contribution_digest=ContentDigest.of_bytes(b"changed")
        )
    else:
        args[
            {
                "owner": "command_owner",
                "parent": "command_parent",
                "code": "code_admission",
                "workspace": "workspace_admission",
            }[replacement]
        ] = object()
    with pytest.raises(RuntimeError):
        host.validate_initial_publication(expected, **args)
    host.close()
    owner.close()


def test_legacy_parent_cannot_claim_command_publication():
    _, host, code, workspace = setup()
    admit(host, code, lambda: workspace)
    with pytest.raises(RuntimeError, match="unavailable"):
        host.read_initial_publication()
    host.close()


def test_initial_publication_failure_retires_pair(monkeypatch):
    owner, _, _, host, code, workspace = command_setup()
    captured = []
    original = joint.published_code_catalog_leg

    def fail(leg):
        captured.append(original(leg))
        raise RuntimeError("injected final accessor failure")

    monkeypatch.setattr(joint, "published_code_catalog_leg", fail)
    with pytest.raises(RuntimeError, match="injected"):
        admit(host, code, lambda: workspace)
    with pytest.raises(RuntimeError):
        host.read_initial_publication()
    with pytest.raises(ContractViolation):
        captured[0][1].catalog
    with pytest.raises(RuntimeError):
        host._command_parent.current_record(host._command_parent.expected)
    owner.close()


def test_command_parent_validator_replacement_refuses(monkeypatch):
    owner, _, _, host, code, workspace = command_setup()
    monkeypatch.setattr(
        owner, "validate_direct_invocation_parent", lambda *a, **k: None
    )
    with pytest.raises(RuntimeError, match="substituted"):
        admit(host, code, lambda: workspace)


def test_initial_command_publication_refuses_membership_bootstrap():
    from test_materialization_graph_planner import _entry

    owner, _, _, host, code, _ = command_setup()
    workspace = WorkspaceSemanticMaterializationMembershipCatalog.create(
        catalog_ref="workspace.not.initial",
        catalog_generation=1,
        entries=(_entry("package:api", "api"),),
    )
    with pytest.raises(RuntimeError, match="must be empty"):
        admit(host, code, lambda: workspace)
    with pytest.raises(RuntimeError):
        host.read_initial_publication()
    owner.close()


def test_initial_parent_closure_during_catalog_read_refuses():
    owner, _, _, host, code, workspace = command_setup()

    def reader():
        owner.close()
        return workspace

    with pytest.raises((RuntimeError, ContractViolation)):
        admit(host, code, reader)
    with pytest.raises(RuntimeError):
        host.read_initial_publication()


def test_initial_pair_replacement_during_validation_refuses(monkeypatch):
    owner, parent, _, host, code, workspace = command_setup()
    result = admit(host, code, lambda: workspace)
    expected = host.read_initial_publication()
    validate = result.code.validate_catalog

    def replace_pair():
        validate()
        host._code_admission = object()

    monkeypatch.setattr(result.code, "validate_catalog", replace_pair)
    with pytest.raises(RuntimeError, match="moved"):
        host.validate_initial_publication(
            expected,
            command_owner=owner,
            command_parent=parent,
            code_admission=result.code_admission,
            workspace_admission=result.workspace_admission,
        )
    host.close()
    owner.close()


def test_command_initial_publication_requires_code_contributions():
    owner, _, _, host, _, workspace = command_setup()
    empty = CodeSemanticContractCatalog.create(
        catalog_ref="code.absent", catalog_generation=1, entries=()
    )
    with pytest.raises(RuntimeError, match="requires Code contributions"):
        admit(host, empty, lambda: workspace)
    with pytest.raises(RuntimeError):
        host.read_initial_publication()
    owner.close()


def test_original_code_participant_uses_original_workspace_epoch():
    from dataclasses import replace

    from aware_code_retained_registry_policy_runtime.epoch_participation import (
        _assemble_code_epoch_participation,
    )
    from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
        CatalogPublicationExpectation,
    )

    owner, parent, invocation, host, code, workspace = command_setup()
    result = admit(host, code, lambda: workspace)
    expected = host.read_initial_publication()
    epoch = host.read_initial_epoch()
    guard = owner.acquire_catalog_epoch_exclusion(parent, expected=invocation)
    try:
        participant = _assemble_code_epoch_participation(
            owner=owner,
            parent=parent,
            invocation=invocation,
            epoch_owner=host,
            guard=guard,
        )
        participant._register_epoch(guard, epoch, expected=expected)
        assert (
            host.read_code_catalog_for_epoch(epoch, expected=expected)
            is result.code_admission
        )
        assert owner._guard is guard
        with pytest.raises(RuntimeError, match="original current pair"):
            host.validate_current_catalog_epoch(object(), expected=expected)
        successor = CatalogPublicationExpectation(
            object(),
            expected,
            replace(expected, publication_identity=object()),
            expected.contribution_digest,
        )
        use = participant._begin_epoch_use(guard, epoch, expected=expected)
        with pytest.raises(Exception, match="active or unresolved"):
            participant.validate_catalog_publication_exclusion(
                guard, expected=successor
            )
        participant._start_epoch_use(guard, use)
        with pytest.raises(Exception, match="active or unresolved"):
            participant.validate_catalog_publication_exclusion(
                guard, expected=successor
            )
        participant._finish_epoch_use(guard, use)
        participant.validate_catalog_publication_exclusion(guard, expected=successor)
        with pytest.raises(Exception):
            participant._finish_epoch_use(guard, use)
        participant._close_under_exclusion(guard)
    finally:
        owner.release_catalog_epoch_exclusion(guard)
    owner.close()
    with pytest.raises(Exception):
        host.validate_current_catalog_epoch(epoch, expected=expected)
    with pytest.raises(Exception):
        result.code.validate_catalog()
    host.close()


def test_epoch_bound_leg_rejects_original_preparation_substitution():
    from dataclasses import replace

    owner, _, _, host, code, workspace = command_setup()
    result = admit(host, code, lambda: workspace)
    command = host._command_parent
    record = command.records._current
    command.records._current = replace(record, preparation=object())
    with pytest.raises(Exception):
        result.code.validate_catalog()
    owner.close()
    host.close()


def successor_workspace_catalog(generation=2):
    from test_materialization_graph_planner import _entry

    return WorkspaceSemanticMaterializationMembershipCatalog.create(
        catalog_ref="workspace.successor",
        catalog_generation=generation,
        entries=(_entry("package:api", "api"),),
    )


def test_product_eligible_successor_requires_original_source_correspondence():
    from aware_workspace_runtime.materialization_membership_catalog import (
        WorkspaceSemanticMaterializationPackageEntry,
    )
    from aware_workspace_runtime.materialization_selection import (
        WorkspaceSemanticMaterializationParticipationPolicy,
    )

    owner, _, _, host, code, initial_workspace = command_setup()
    admit(host, code, lambda: initial_workspace)
    original_epoch = host.read_initial_publication()
    original = successor_workspace_catalog().entries[0]
    policy = original.participation_policy
    product_policy = WorkspaceSemanticMaterializationParticipationPolicy.create(
        policy_ref=policy.policy_ref,
        policy_revision=2,
        package_ref=policy.package_ref,
        allowed_operation_kinds=policy.allowed_operation_kinds,
        allowed_semantic_root_refs=policy.allowed_semantic_root_refs,
        allowed_terminal_output_roles=policy.allowed_terminal_output_roles,
        allow_unconfigured=policy.allow_unconfigured,
        allowed_semantic_configuration_coordinates=(
            policy.allowed_semantic_configuration_coordinates
        ),
    )
    entry = WorkspaceSemanticMaterializationPackageEntry.create(
        repository_ref=original.repository_ref,
        workspace_ref=original.workspace_ref,
        module_ref=original.module_ref,
        package=original.package,
        package_family=original.package_family,
        package_role=original.package_role,
        manifest_contract=original.manifest_contract,
        manifest_relative_path=original.manifest_relative_path,
        source_authority_ref=original.source_authority_ref,
        source_authority_digest=original.source_authority_digest,
        owned_semantic_root_refs=original.owned_semantic_root_refs,
        authored_dependencies=original.authored_dependencies,
        participation_policy=product_policy,
        allowed_profile_refs=original.allowed_profile_refs,
    )
    successor = WorkspaceSemanticMaterializationMembershipCatalog.create(
        catalog_ref="workspace.product-successor",
        catalog_generation=2,
        entries=(entry,),
    )
    with pytest.raises(
        RuntimeError, match="product-eligible entry lacks original source correspondence"
    ):
        prepare_successor(host, code, lambda: successor)
    assert (
        host.read_initial_publication().publication_identity
        is original_epoch.publication_identity
    )
    owner.close()
    host.close()


def prepare_successor(host, code, reader):
    _, _, _, providers, planners = host._contribution
    return host.prepare_successor_catalogs(
        code_catalog=code,
        workspace_catalog_reader=reader,
        provider_executable_bindings=providers,
        dependency_planner_bindings=planners,
    )


def test_real_successor_pair_is_hidden_and_predecessor_remains_current():
    from aware_code_semantic_contract_runtime.catalog_host_leg import (
        published_code_catalog_leg,
    )
    from aware_workspace_runtime.materialization_membership_catalog import (
        WorkspaceSemanticMaterializationMembershipResolver,
    )

    owner, _, _, host, code, initial_workspace = command_setup()
    initial = admit(host, code, lambda: initial_workspace)
    predecessor = host.read_initial_publication()
    successor_workspace = successor_workspace_catalog()
    preparation, expected = prepare_successor(host, code, lambda: successor_workspace)
    assert expected.predecessor is not None
    assert expected.predecessor.publication_identity is predecessor.publication_identity
    assert (
        expected.successor.publication_identity is not predecessor.publication_identity
    )
    assert expected.successor.code_catalog_digest == code.catalog_root_digest
    assert (
        expected.successor.membership_catalog_digest
        == successor_workspace.catalog_root_digest
    )
    host.validate_prepared_catalog_publication(preparation, expected=expected)
    retained = host._successor_attempts[preparation]
    with pytest.raises(ContractViolation):
        published_code_catalog_leg(retained.code_leg)
    with pytest.raises(ContractViolation):
        WorkspaceSemanticMaterializationMembershipResolver(
            retained.workspace_admission
        ).catalog
    assert initial.code.catalog == code
    assert initial.workspace.catalog == initial_workspace
    assert (
        host.read_initial_publication().publication_identity
        is predecessor.publication_identity
    )
    host.discard_successor_catalogs(preparation, expected=expected)
    assert initial.code.catalog == code
    assert initial.workspace.catalog == initial_workspace
    with pytest.raises(RuntimeError):
        host.validate_prepared_catalog_publication(preparation, expected=expected)
    host.close()
    owner.close()


def test_successor_validation_rereads_source_but_guard_validation_is_in_memory():
    owner, parent, invocation, host, code, initial_workspace = command_setup()
    admit(host, code, lambda: initial_workspace)
    current = [successor_workspace_catalog()]

    def reader():
        value = current[0]
        if isinstance(value, BaseException):
            raise value
        return value

    preparation, expected = prepare_successor(host, code, reader)
    guard = owner.acquire_catalog_epoch_exclusion(parent, expected=invocation)
    try:
        current[0] = RuntimeError("source read forbidden under final guard")
        host.validate_catalog_epoch_publication_guard(
            guard, preparation=preparation, expected=expected
        )
    finally:
        owner.release_catalog_epoch_exclusion(guard)
    with pytest.raises(RuntimeError, match="source read forbidden"):
        host.validate_prepared_catalog_publication(preparation, expected=expected)
    current[0] = successor_workspace_catalog(generation=3)
    with pytest.raises(RuntimeError, match="source_moved"):
        host.validate_prepared_catalog_publication(preparation, expected=expected)
    host.discard_successor_catalogs(preparation, expected=expected)
    assert (
        host.read_initial_publication().publication_identity
        is expected.predecessor.publication_identity
    )
    host.close()
    owner.close()


@pytest.mark.parametrize("change", ["expected", "preparation", "close"])
def test_successor_preparation_rejects_substitution_and_closure(change):
    from dataclasses import replace

    owner, _, _, host, code, initial_workspace = command_setup()
    initial = admit(host, code, lambda: initial_workspace)
    successor_workspace = successor_workspace_catalog()
    preparation, expected = prepare_successor(host, code, lambda: successor_workspace)
    if change == "expected":
        with pytest.raises(Exception):
            host.validate_prepared_catalog_publication(
                preparation,
                expected=replace(expected, preparation_identity=object()),
            )
    elif change == "preparation":
        with pytest.raises(Exception):
            host.validate_prepared_catalog_publication(object(), expected=expected)
    else:
        host.close()
        with pytest.raises(Exception):
            host.validate_prepared_catalog_publication(preparation, expected=expected)
    if change != "close":
        assert initial.code.catalog == code
        assert initial.workspace.catalog == initial_workspace
        host.discard_successor_catalogs(preparation, expected=expected)
        host.close()
    owner.close()


def test_workspace_commits_successor_pair_once_and_advances_current(monkeypatch):
    from dataclasses import replace

    from aware_code_retained_registry_policy_runtime.catalog_completion_transfer import (
        AuthorityCatalogCompletionTransferRuntime,
        CatalogCompletionTransfer,
    )

    owner, parent, invocation, host, code, initial_workspace = command_setup()
    predecessor_pair = admit(host, code, lambda: initial_workspace)
    successor_workspace = successor_workspace_catalog()
    preparation, publication = prepare_successor(
        host, code, lambda: successor_workspace
    )
    runtime = object.__new__(AuthorityCatalogCompletionTransferRuntime)
    transfer = object.__new__(CatalogCompletionTransfer)
    monkeypatch.setattr(
        AuthorityCatalogCompletionTransferRuntime,
        "validate_catalog_completion_transfer",
        lambda self, value, *, expected: None,
    )
    monkeypatch.setattr(
        AuthorityCatalogCompletionTransferRuntime,
        "seal_catalog_completion_transfer",
        lambda self, value, guard, *, expected: None,
    )
    monkeypatch.setattr(
        AuthorityCatalogCompletionTransferRuntime,
        "validate_committed_catalog_completion_transfer",
        lambda self, value, *, expected: None,
    )
    pair = host.publish_successor_catalogs(
        preparation,
        transfer,
        publication_expected=publication,
        transfer_expected=object(),
        transfer_runtime=runtime,
    )
    guard = owner.acquire_catalog_epoch_exclusion(parent, expected=invocation)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(
                type(owner),
                "acquire_catalog_epoch_exclusion",
                lambda *args, **kwargs: pytest.fail("guard reacquired"),
            )
            host.validate_committed_successor_epoch_guard(
                guard, preparation, transfer, expected=publication
            )
        with pytest.raises(RuntimeError):
            host.validate_committed_successor_epoch_guard(
                guard, preparation, object(), expected=publication
            )
        with pytest.raises(RuntimeError):
            host.validate_committed_successor_epoch_guard(
                guard, object(), transfer, expected=publication
            )
        with pytest.raises(RuntimeError):
            host.validate_committed_successor_epoch_guard(
                guard,
                preparation,
                transfer,
                expected=replace(publication, preparation_identity=object()),
            )
    finally:
        owner.release_catalog_epoch_exclusion(guard)
    with pytest.raises(Exception):
        host.validate_committed_successor_epoch_guard(
            guard, preparation, transfer, expected=publication
        )
    current = host.read_initial_publication()
    assert current.publication_identity is publication.successor.publication_identity
    assert pair.workspace.catalog == successor_workspace
    pair.code.validate_catalog()
    with pytest.raises(ContractViolation):
        predecessor_pair.code.validate_catalog()
    with pytest.raises(ContractViolation):
        predecessor_pair.workspace.catalog
    with pytest.raises(RuntimeError):
        host.publish_successor_catalogs(
            preparation,
            transfer,
            publication_expected=publication,
            transfer_expected=object(),
            transfer_runtime=runtime,
        )
    host.close()
    owner.close()
