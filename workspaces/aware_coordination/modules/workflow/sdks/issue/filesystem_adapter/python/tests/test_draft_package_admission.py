"""Real Issue/physical proofs; most transitions use a labelled Protocol seam.

The binding-observation case uses genuine Protocol admission. Neither that case
nor the unit transitions qualify SPEC semantic validation or installed authoring.
"""

import copy
import gc
import hashlib
import os
import pickle
import sys
import weakref
from dataclasses import FrozenInstanceError, replace
from types import ModuleType

import pytest
from aware_file_system.retained_package import retain_package_publication
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_fs_adapter import draft_package as issuer
from aware_issue_sdk import IssueDraftPackageRefusal, IssueDraftPackageRequest
from test_provider import ISSUE_REF, _repository


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


@pytest.fixture
def context(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "draft-test-session")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    root = _repository(tmp_path)
    issue = root / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    body = issue.read_text().replace("codex-example", "codex-draft-test-session")
    start = body.index("## Ownership Scope")
    end = body.index("\n## ", start + 3)
    issue.write_text(
        body[:start] + "## Ownership Scope\n- `docs/public`\n" + body[end:]
    )
    (root / "docs/public").mkdir()
    physical = retain_package_publication(
        root=root,
        target_path="docs/public/example",
        scratch_path="docs/public/.aware-spec-draft-" + "a" * 32,
        ordered_members=(("README.md", b"real bytes"), ("nested/a.txt", b"two")),
    )
    request = IssueDraftPackageRequest(
        issue_ref=ISSUE_REF,
        expected_issue_sha256=digest(issue.read_bytes()),
        manifest_locator="aware.protocol.toml",
        expected_manifest_sha256=digest((root / "aware.protocol.toml").read_bytes()),
        target_locator="docs/public/example",
        scratch_locator=physical.scratch_path,
        ordered_members=(("README.md", b"real bytes"), ("nested/a.txt", b"two")),
        authoring_intent_ref="draft-example",
        client_intent_id="draft-attempt-1",
    )
    provider = FilesystemIssueOperationProvider(repository_root=root)
    yield root, issue, request, provider, physical
    dispose_test_original(physical)


def dispose_test_original(physical):
    """Fixture-owned cleanup through Issue custody, not a consumer fallback."""
    claim = issuer._PLANS.get(physical)
    state = None if claim is None or claim.state is None else claim.state()
    if state is not None:
        issuer._release(state)
    for custody in list(issuer._CUSTODIES.values()) + list(issuer._CONTEXTS.values()):
        if custody.physical is physical:
            issuer._release_custody(custody)
    if not physical.observe_cleanup().attempted:
        from aware_file_system import retained_package as owner

        # Fault tests may interrupt the public release before the owner body.
        # After restoring that fault, teardown uses its genuine original ticket,
        # not raw disposal or a negative observation as consumer permission.
        tickets = [
            ticket
            for ticket, entry in owner._INPUTS.items()
            if entry.plan is physical and type(ticket) is owner.PackageInputClaim
        ]
        if tickets:
            owner.release_package_input(tickets[0])
        else:
            physical.release()


def unit_read(handle):
    return handle.admit_published_read(
        physical_postimage=issuer._ADMISSIONS[handle].postimage
    )


@pytest.fixture
def protocol(context, monkeypatch):
    from types import SimpleNamespace

    from aware_file_system import retained_package as fs

    _, _, request, _, physical = context
    shim = ModuleType("aware_protocol_fs_adapter.specification_draft_target")

    class Target:
        manifest_sha256 = request.expected_manifest_sha256
        manifest_locator = request.manifest_locator
        target_locator = request.target_locator
        phase = "absent"
        bound = None

    target = Target()
    selection = object()
    records = {}

    def observe(value):
        record = records[value]
        physical_observation = fs.observe_package_input(
            record.claim if record.claim is not None else record.physical_reservation
        )
        return SimpleNamespace(
            attempt_ref=record.attempt,
            client_intent_id=record.intent,
            resource_state=record.resource_state,
            transfer_state=record.transfer_state,
            release_invocation=record.release_invocation,
            owner_cleanup_attempted=None,
            owner_cleanup_outcome="unknown",
            diagnostics=(),
            root_locator=physical_observation.binding.root_locator,
            manifest_locator=target.manifest_locator,
            manifest_sha256=target.manifest_sha256,
            target_locator=target.target_locator,
            physical=physical_observation,
        )

    def reserve(value, *, physical_plan, attempt_ref, client_intent_id):
        assert value is target and physical_plan is physical
        physical_reservation = fs.reserve_package_input(
            physical_plan, attempt_ref=attempt_ref, client_intent_id=client_intent_id
        )
        record = type("UnitJointReservation", (), {})()
        record.__dict__.update(
            attempt=attempt_ref,
            intent=client_intent_id,
            physical_reservation=physical_reservation,
            claim=None,
            receiver=None,
            resource_state="reserved",
            transfer_state="not_attempted",
            release_invocation="not_invoked",
        )
        records[record] = record
        return record

    def transfer(reservation, *, physical_claim, receiver):
        record = records[reservation]
        fs.require_package_input_claim(physical_claim, plan=physical, receiver=receiver)
        claim = object()
        record.claim = physical_claim
        record.receiver = receiver
        record.resource_state, record.transfer_state = "transferred", "completed"
        records[claim] = record
        target.claim = claim
        return claim

    def release(value):
        record = records[value]
        if record.release_invocation == "not_invoked":
            if record.claim is None:
                fs.release_package_input(record.physical_reservation)
            record.release_invocation, record.resource_state = "returned", "released"
            target.phase = "released"
        return observe(value)

    def require(value, *, input_claim=None):
        if value is not target or value.phase in {"retired", "released"}:
            raise IssueDraftPackageRefusal("unit_protocol_original_required")
        assert records[input_claim].claim is not None
        return value

    def bind(value, *, physical_plan, input_claim=None, physical_input_claim=None):
        require(value, input_claim=input_claim)
        assert value.phase == "absent" and physical_plan is physical
        fs.require_retained_package_plan(
            physical_plan, input_claim=physical_input_claim
        )
        value.bound = physical_plan
        value.phase = "bound"

    def spend(value, *, input_claim=None):
        require(value, input_claim=input_claim)
        assert value.phase == "bound" and value.bound.phase == "staged"
        value.phase = "publication_spent"

    def published_read(value, *, physical_postimage, input_claim=None):
        require(value, input_claim=input_claim)
        fs.require_retained_package_postimage(
            physical_postimage, plan=physical, input_claim=records[input_claim].claim
        )
        return selection

    def finish(value, *, read_selection, input_claim=None):
        require(value, input_claim=input_claim)
        if value.phase != "publication_spent" or read_selection is not selection:
            raise IssueDraftPackageRefusal("unit_correlated_read_required")
        value.phase = "consumed"

    shim.reserve_specification_draft_input = reserve
    shim.observe_specification_draft_input = observe
    shim.transfer_specification_draft_input = transfer
    shim.release_specification_draft_input = release
    shim.require_specification_draft_target = require
    shim.bind_specification_draft_physical_plan = bind
    shim.spend_specification_draft_publication = spend
    shim.admit_specification_draft_published_read = published_read
    shim.finish_specification_draft_target = finish
    monkeypatch.setitem(sys.modules, shim.__name__, shim)
    return target, selection, shim


def admit(context, protocol):
    _, _, request, provider, physical = context
    target, _, _ = protocol
    return provider.admit_draft_package(
        request, protocol_target=target, physical_plan=physical
    )


def stage(handle):
    while handle.phase != "staged":
        handle.stage_next_effect()


def test_real_protocol_missing_refuses_before_any_effect(context, monkeypatch):
    root, _, request, provider, physical = context
    monkeypatch.setitem(
        sys.modules, "aware_protocol_fs_adapter.specification_draft_target", None
    )
    with pytest.raises(IssueDraftPackageRefusal, match="integration_unavailable"):
        provider.admit_draft_package(
            request, protocol_target=object(), physical_plan=physical
        )
    assert list((root / "docs/public").iterdir()) == []
    assert physical.phase == "planned"


def test_actual_issue_and_physical_loop_with_unit_protocol_seam(context, protocol):
    root, issue, _, provider, physical = context
    before = issue.read_bytes()
    handle = admit(context, protocol)
    provider.validate_draft_package(handle)
    stage(handle)
    lens = handle.lend_staged_source()
    borrowed = lens.duplicate_parent_descriptor()
    os.close(borrowed)
    image = handle.publish_package()
    receipt = handle.finish(physical_postimage=image, read_selection=unit_read(handle))
    handle.validate_completed_current()
    assert receipt.evidence.package_outcome == "published"
    assert receipt.candidate_sha256 == context[2].candidate_sha256
    assert (root / "docs/public/example/README.md").read_bytes() == b"real bytes"
    assert issue.read_bytes() == before
    assert physical.phase == "consumed"
    for method in (
        "validate_current",
        "stage_next_effect",
        "lend_staged_source",
        "publish_package",
    ):
        with pytest.raises(IssueDraftPackageRefusal, match="terminal"):
            getattr(handle, method)()
    evidence = handle.release()
    assert evidence.package_outcome == "published"
    assert handle.release() == evidence
    assert not hasattr(handle, "replace_manifest")


@pytest.mark.parametrize(
    "method",
    ["validate_current", "stage_next_effect", "lend_staged_source", "publish_package"],
)
def test_changed_issue_retires_at_each_entrance(context, protocol, method):
    root, issue, _, _, _ = context
    handle = admit(context, protocol)
    if method in {"lend_staged_source", "publish_package"}:
        stage(handle)
    issue.write_bytes(issue.read_bytes() + b"\n# changed\n")
    with pytest.raises(IssueDraftPackageRefusal):
        getattr(handle, method)()
    assert handle.phase == "retired"
    assert not (root / "docs/public/example").exists()
    with pytest.raises(IssueDraftPackageRefusal, match="terminal"):
        handle.stage_next_effect()


@pytest.mark.parametrize(
    "change", ["scope", "owner", "status", "missing", "fifo", "manifest", "execution"]
)
def test_issuance_refuses_authority_defects_effect_free(
    context, protocol, change, monkeypatch
):
    root, issue, request, provider, physical = context
    if change == "scope":
        issue.write_text(
            issue.read_text().replace("`docs/public`", "`docs/public/example`")
        )
    elif change == "owner":
        issue.write_text(
            issue.read_text().replace("codex-draft-test-session", "codex-other")
        )
    elif change == "status":
        issue.write_text(issue.read_text().replace("In Progress", "Closed"))
    elif change == "missing":
        issue.unlink()
    elif change == "fifo":
        issue.unlink()
        os.mkfifo(issue)
    elif change == "manifest":
        (root / "aware.protocol.toml").write_bytes(b"changed")
    else:
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "ambiguous")
    if change in {"scope", "owner", "status"}:
        request = replace(request, expected_issue_sha256=digest(issue.read_bytes()))
    with pytest.raises(IssueDraftPackageRefusal):
        provider.admit_draft_package(
            request, protocol_target=protocol[0], physical_plan=physical
        )
    assert physical.phase == (
        "planned" if change in {"ambiguous", "execution"} else "released"
    )
    assert physical.evidence.effects == ()
    assert list((root / "docs/public").iterdir()) == []


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_original_admission_refuses_copy_and_serialization(
    context, protocol, operation
):
    handle = admit(context, protocol)
    try:
        with pytest.raises(TypeError):
            operation(handle)
    finally:
        handle.release()


def test_forged_and_foreign_provider_refuse(context, protocol):
    root, _, _, provider, _ = context
    with pytest.raises(TypeError):
        issuer.FilesystemIssueDraftPackageAdmission()
    with pytest.raises(TypeError):
        type("Forged", (issuer.FilesystemIssueDraftPackageAdmission,), {})
    with pytest.raises(IssueDraftPackageRefusal, match="original"):
        provider.validate_draft_package(
            object.__new__(issuer.FilesystemIssueDraftPackageAdmission)
        )
    handle = admit(context, protocol)
    other = FilesystemIssueOperationProvider(repository_root=root)
    with pytest.raises(IssueDraftPackageRefusal, match="foreign"):
        other.validate_draft_package(handle)
    assert handle.phase == "issued"
    handle.release()


def test_second_admission_does_not_release_foreign_active_plan(context, protocol):
    handle = admit(context, protocol)
    with pytest.raises(IssueDraftPackageRefusal):
        admit(context, protocol)
    assert context[4].phase == "planned"
    handle.validate_current()
    handle.release()


def test_wrong_postimage_and_read_preserve_known_publication(context, protocol):
    root, _, _, _, _ = context
    handle = admit(context, protocol)
    stage(handle)
    image = handle.publish_package()
    with pytest.raises(IssueDraftPackageRefusal):
        handle.finish(physical_postimage=image, read_selection=object())
    assert handle.phase == "retired"
    assert handle.evidence.package_outcome == "published"
    assert (root / "docs/public/example/README.md").read_bytes() == b"real bytes"


def test_validation_interruption_retires_and_preserves_effects(
    context, protocol, monkeypatch
):
    handle = admit(context, protocol)
    handle.stage_next_effect()

    def interrupted(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr(issuer, "_read_issue", interrupted)
    with pytest.raises(IssueDraftPackageRefusal) as refusal:
        handle.validate_current()
    assert handle.phase == "retired"
    assert any(effect.kind == "directory" for effect in refusal.value.evidence.effects)
    assert not list((context[0] / "docs/public").iterdir())


def test_setup_request_is_not_draft_admission(context, protocol):
    from aware_issue_sdk import IssueSourceChangeRequest

    request = IssueSourceChangeRequest(
        issue_ref=context[2].issue_ref,
        expected_issue_sha256=context[2].expected_issue_sha256,
        manifest_locator="aware.protocol.toml",
        expected_manifest_sha256=context[2].expected_manifest_sha256,
        candidate=b"setup",
        directory_paths=(),
        client_intent_id="setup",
    )
    with pytest.raises(TypeError):
        context[3].admit_draft_package(
            request, protocol_target=protocol[0], physical_plan=context[4]
        )
    assert context[4].phase == "planned"


def test_scope_refusal_reports_exact_scratch_and_public_footprint(context, protocol):
    _, issue, request, provider, physical = context
    issue.write_text(
        issue.read_text().replace("`docs/public`", "`docs/public/example`")
    )
    request = replace(request, expected_issue_sha256=digest(issue.read_bytes()))
    with pytest.raises(IssueDraftPackageRefusal) as refusal:
        provider.admit_draft_package(
            request, protocol_target=protocol[0], physical_plan=physical
        )
    assert refusal.value.required_effect_paths == request.ordered_effect_paths


def test_manifest_comment_drift_retires_at_use(context, protocol):
    handle = admit(context, protocol)
    manifest = context[0] / "aware.protocol.toml"
    manifest.write_bytes(manifest.read_bytes() + b"\n# semantic no-op\n")
    with pytest.raises(IssueDraftPackageRefusal, match="manifest_authority_changed"):
        handle.stage_next_effect()
    assert handle.phase == "retired"
    assert not list((context[0] / "docs/public").iterdir())


def test_real_fork_refuses_borrowed_admission_and_preserves_parent(context, protocol):
    handle = admit(context, protocol)
    receive, send = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(receive)
        try:
            try:
                handle.stage_next_effect()
            except IssueDraftPackageRefusal as error:
                os.write(
                    send, (error.code + ":" + error.evidence.package_outcome).encode()
                )
        finally:
            os.close(send)
            os._exit(0)
    os.close(send)
    try:
        result = os.read(receive, 1024)
    finally:
        os.close(receive)
        os.waitpid(pid, 0)
    assert result == b"draft_admission_foreign_process:none"
    handle.validate_current()
    handle.release()


def test_interrupted_release_returns_typed_evidence(context, protocol, monkeypatch):
    handle = admit(context, protocol)
    from aware_file_system import retained_package as physical_owner

    original = physical_owner.release_package_input

    def interrupted(value):
        original(value)
        raise KeyboardInterrupt

    monkeypatch.setattr(physical_owner, "release_package_input", interrupted)
    with pytest.raises(IssueDraftPackageRefusal, match="release_incomplete") as refusal:
        handle.release()
    assert handle.phase == "released"
    assert (
        "physical_release_failed:KeyboardInterrupt"
        in refusal.value.evidence.cleanup_diagnostics
    )
    monkeypatch.setattr(physical_owner, "release_package_input", original)


def test_advertised_neutral_draft_exports_resolve_without_owner_graph():
    import aware_issue_sdk

    names = (
        "ISSUE_DRAFT_PACKAGE_OPERATION_REF",
        "IssueDraftPackageEffect",
        "IssueDraftPackageEvidence",
        "IssueDraftPackageReceipt",
        "IssueDraftPackageRefusal",
        "IssueDraftPackageAdmission",
        "IssueDraftPackageProvider",
    )
    for name in names:
        assert name in aware_issue_sdk.__all__
        assert getattr(aware_issue_sdk, name) is not None


@pytest.mark.parametrize(
    "method",
    ["validate_current", "stage_next_effect", "lend_staged_source", "publish_package"],
)
def test_at_use_fifo_refusal_is_typed_and_terminal(context, protocol, method):
    handle = admit(context, protocol)
    if method in {"lend_staged_source", "publish_package"}:
        stage(handle)
    issue = context[1]
    issue.unlink()
    os.mkfifo(issue)
    with pytest.raises(IssueDraftPackageRefusal):
        getattr(handle, method)()
    assert handle.phase == "retired"


def test_completion_checks_do_not_renew_authority(context, protocol):
    handle = admit(context, protocol)
    stage(handle)
    image = handle.publish_package()
    handle.finish(physical_postimage=image, read_selection=unit_read(handle))
    context[1].write_bytes(context[1].read_bytes() + b"changed")
    with pytest.raises(IssueDraftPackageRefusal) as refusal:
        handle.validate_completed_current()
    assert refusal.value.evidence.package_outcome == "published"
    assert handle.phase == "retired"


def test_initial_permission_failure_is_typed_and_effect_free(
    context, protocol, monkeypatch
):
    def denied(*args):
        raise PermissionError("denied")

    monkeypatch.setattr(issuer, "_read_issue", denied)
    with pytest.raises(IssueDraftPackageRefusal) as refusal:
        admit(context, protocol)
    assert isinstance(refusal.value.__cause__, PermissionError)
    assert context[4].phase == "released"


def test_wrong_original_postimage_preserves_publication(context, protocol):
    handle = admit(context, protocol)
    stage(handle)
    handle.publish_package()
    with pytest.raises(IssueDraftPackageRefusal):
        handle.finish(physical_postimage=object(), read_selection=unit_read(handle))
    assert handle.evidence.package_outcome == "published"
    assert handle.phase == "retired"


def test_changed_physical_candidate_refuses_before_claim(context, protocol):
    request = replace(context[2], ordered_members=(("README.md", b"different"),))
    with pytest.raises(IssueDraftPackageRefusal, match="draft_input_binding_mismatch"):
        context[3].admit_draft_package(
            request, protocol_target=protocol[0], physical_plan=context[4]
        )
    assert context[4].phase == "released"


def test_spent_setup_admission_cannot_be_validated_as_draft(context):
    from aware_issue_fs_adapter.source_change import (
        FilesystemIssueSourceChangeAdmission,
    )

    forged_setup = object.__new__(FilesystemIssueSourceChangeAdmission)
    with pytest.raises(
        IssueDraftPackageRefusal, match="original_draft_admission_required"
    ):
        context[3].validate_draft_package(forged_setup)


def test_completed_release_rechecks_issue_after_cleanup(context, protocol):
    handle = admit(context, protocol)
    stage(handle)
    image = handle.publish_package()
    handle.finish(physical_postimage=image, read_selection=unit_read(handle))
    context[1].write_bytes(context[1].read_bytes() + b"changed")
    with pytest.raises(IssueDraftPackageRefusal) as refusal:
        handle.release()
    assert refusal.value.evidence.package_outcome == "published"
    assert handle.phase == "retired"


def test_unavailable_ledger_does_not_erase_known_publication(
    context, protocol, monkeypatch
):
    handle = admit(context, protocol)
    stage(handle)
    handle.publish_package()

    def unavailable(value):
        raise OSError("unavailable ledger")

    monkeypatch.setattr(type(context[4]), "evidence", property(unavailable))
    evidence = handle.evidence
    assert evidence.package_outcome == "published"
    assert evidence.ledger_complete is False
    handle.release()


def test_interrupted_postimage_return_then_unavailable_ledger_preserves_publication(
    context, protocol, monkeypatch
):
    handle = admit(context, protocol)
    stage(handle)
    original = type(context[4]).publish_package

    def interrupted(value, **kwargs):
        original(value, **kwargs)
        raise KeyboardInterrupt

    monkeypatch.setattr(type(context[4]), "publish_package", interrupted)
    with pytest.raises(IssueDraftPackageRefusal) as refusal:
        handle.publish_package()
    assert refusal.value.evidence.package_outcome == "published"
    assert issuer._ADMISSIONS[handle].postimage is None

    def unavailable(value):
        raise OSError("unavailable ledger")

    monkeypatch.setattr(type(context[4]), "evidence", property(unavailable))
    for _ in range(2):
        evidence = handle.evidence
        assert evidence.package_outcome == "published"
        assert evidence.ledger_complete is False
    assert (context[0] / "docs/public/example/README.md").read_bytes() == b"real bytes"
    with pytest.raises(IssueDraftPackageRefusal, match="terminal"):
        handle.publish_package()


@pytest.mark.parametrize("interrupt_before_close", [True, False])
def test_actual_physical_close_diagnostics_are_typed_release_refusals(
    context, protocol, monkeypatch, interrupt_before_close
):
    from aware_file_system import retained_package as physical_module

    handle = admit(context, protocol)
    stage(handle)
    handle.publish_package()
    descriptors = tuple(physical_module._HANDLES[context[4]].fds.values())
    interrupted_fd = descriptors[0]
    original_close = os.close
    attempted = []

    def interrupted_close(descriptor):
        attempted.append(descriptor)
        if descriptor == interrupted_fd and interrupt_before_close:
            raise KeyboardInterrupt
        original_close(descriptor)
        if descriptor == interrupted_fd:
            raise KeyboardInterrupt

    monkeypatch.setattr(physical_module.os, "close", interrupted_close)
    try:
        with pytest.raises(
            IssueDraftPackageRefusal, match="draft_release_incomplete"
        ) as refusal:
            handle.release()
        assert (
            "descriptor_close:KeyboardInterrupt"
            in refusal.value.evidence.cleanup_diagnostics
        )
        assert refusal.value.evidence.package_outcome == "published"
        assert handle.phase == "released"
        assert set(descriptors).issubset(attempted)
        repeated = handle.release()
        assert repeated.package_outcome == "published"
        assert (
            repeated.cleanup_diagnostics == refusal.value.evidence.cleanup_diagnostics
        )
        assert (
            context[0] / "docs/public/example/README.md"
        ).read_bytes() == b"real bytes"
        with pytest.raises(IssueDraftPackageRefusal, match="terminal"):
            handle.stage_next_effect()
    finally:
        monkeypatch.setattr(physical_module.os, "close", original_close)
        # Only the test owns certainty about the injected pre-close fault.
        # Production cannot retry an uncertain descriptor number safely.
        if interrupt_before_close:
            original_close(interrupted_fd)


def test_initial_binding_uses_recorded_execution_and_detached_request(
    context, protocol, monkeypatch
):
    handle = admit(context, protocol)
    initial = handle.observe_binding()
    assert initial.execution_ref == "codex-draft-test-session"
    assert initial.request == context[2]
    assert initial.request is not issuer._ADMISSIONS[handle].request
    assert initial.authority_grade == "filesystem_harness_observed_v1"
    assert context[3].observe_draft_package_binding(handle) == initial

    def forbidden(*args):
        raise AssertionError("Snapshot must not rediscover or validate authority")

    monkeypatch.setattr(issuer, "_execution", forbidden)
    monkeypatch.setattr(issuer, "_read_issue", forbidden)
    monkeypatch.setattr(issuer, "_check_owners", forbidden)
    monkeypatch.setenv("CODEX_THREAD_ID", "later-not-bound-execution")
    assert handle.observe_binding() == initial
    assert handle.phase == "issued"
    assert context[4].phase == "planned"
    with pytest.raises(FrozenInstanceError):
        initial.execution_ref = "other"
    with pytest.raises(FrozenInstanceError):
        initial.request.client_intent_id = "other"
    with pytest.raises(
        IssueDraftPackageRefusal, match="original_draft_admission_required"
    ):
        context[3].validate_draft_package(initial)
    handle.release()


@pytest.mark.parametrize("phase", ["issued", "retired", "released", "consumed"])
def test_binding_snapshot_survives_cleanup_without_renewing_authority(
    context, protocol, phase
):
    handle = admit(context, protocol)
    initial = handle.observe_binding()
    if phase == "retired":
        context[1].write_bytes(context[1].read_bytes() + b"changed")
        with pytest.raises(IssueDraftPackageRefusal):
            handle.validate_current()
    elif phase == "released":
        handle.release()
    elif phase == "consumed":
        stage(handle)
        image = handle.publish_package()
        handle.finish(physical_postimage=image, read_selection=unit_read(handle))
    assert handle.phase == phase
    assert handle.observe_binding() == initial
    assert context[3].observe_draft_package_binding(handle) == initial
    assert initial.request.candidate_sha256 == context[2].candidate_sha256
    assert handle.phase == phase
    if phase != "issued":
        with pytest.raises(IssueDraftPackageRefusal, match="terminal"):
            handle.stage_next_effect()
    handle.release()
    assert handle.observe_binding() == initial


def test_binding_observation_rejects_foreign_provider_without_retirement(
    context, protocol
):
    handle = admit(context, protocol)
    foreign = FilesystemIssueOperationProvider(repository_root=context[0])
    with pytest.raises(IssueDraftPackageRefusal, match="foreign_issue_provider"):
        foreign.observe_draft_package_binding(handle)
    for forged in (
        object(),
        object.__new__(issuer.FilesystemIssueDraftPackageAdmission),
    ):
        with pytest.raises(
            IssueDraftPackageRefusal, match="original_draft_admission_required"
        ):
            context[3].observe_draft_package_binding(forged)
    handle.validate_current()
    handle.release()


def test_real_fork_cannot_observe_original_admission_binding(context, protocol):
    handle = admit(context, protocol)
    receive, send = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(receive)
        try:
            try:
                handle.observe_binding()
            except IssueDraftPackageRefusal as error:
                os.write(send, error.code.encode())
        finally:
            os.close(send)
            os._exit(0)
    os.close(send)
    try:
        result = os.read(receive, 1024)
    finally:
        os.close(receive)
        os.waitpid(pid, 0)
    assert result == b"draft_admission_foreign_process"
    assert handle.observe_binding().execution_ref == "codex-draft-test-session"
    handle.validate_current()
    handle.release()


def test_binding_export_is_advertised_and_resolves():
    import aware_issue_sdk

    assert "IssueDraftPackageBinding" in aware_issue_sdk.__all__
    assert aware_issue_sdk.IssueDraftPackageBinding is issuer.IssueDraftPackageBinding


def test_binding_snapshot_does_not_retain_writer_lifetime(context, protocol):
    handle = admit(context, protocol)
    snapshot = handle.observe_binding()
    original = weakref.ref(handle)
    del handle
    gc.collect()
    assert original() is None
    assert context[4].phase == "released"
    assert snapshot.execution_ref == "codex-draft-test-session"
    assert snapshot.request == context[2]
    with pytest.raises(
        IssueDraftPackageRefusal, match="original_draft_admission_required"
    ):
        context[3].validate_draft_package(snapshot)


def test_binding_observation_with_genuine_protocol_admission(tmp_path, monkeypatch):
    from aware_protocol_fs_adapter import release_specification_draft_target
    from test_specification_draft_target import new_context

    root, manifest, target, physical = new_context(tmp_path)
    monkeypatch.setenv("CODEX_THREAD_ID", "real-binding-proof")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    issue = root / "work/issues/2026/10/06/fb-2026-10-06-binding-proof.md"
    issue.parent.mkdir(parents=True)
    issue.write_text("""# Issue: Binding proof
- Slug: binding-proof
- Tag: fb/2026-10-06/binding-proof
- Status: In Progress
- Owner: codex-real-binding-proof
- Captured: 2026-10-06
- Recorder: codex-real-binding-proof
## Ownership Scope
- `customer/specs`
## Updates (append-only)
""")
    request = IssueDraftPackageRequest(
        issue_ref="fb/2026-10-06/binding-proof",
        expected_issue_sha256=digest(issue.read_bytes()),
        manifest_locator="aware.protocol.toml",
        expected_manifest_sha256=digest(manifest.read_bytes()),
        target_locator="customer/specs/widget",
        scratch_locator=physical.scratch_path,
        ordered_members=(
            ("README.md", b"draft"),
            ("aware.spec.toml", b"owned parser input"),
        ),
        authoring_intent_ref="binding-proof",
        client_intent_id="initial-real-attempt",
    )
    provider = FilesystemIssueOperationProvider(repository_root=root)
    handle = None
    try:
        handle = provider.admit_draft_package(
            request, protocol_target=target, physical_plan=physical
        )
        snapshot = provider.observe_draft_package_binding(handle)
        assert snapshot.execution_ref == "codex-real-binding-proof"
        assert snapshot.request == request
        assert not list((root / "customer/specs").iterdir())
        handle.release()
        assert handle.observe_binding() == snapshot
        assert not list((root / "customer/specs").iterdir())
    finally:
        if handle is not None:
            handle.release()
        dispose_test_original(physical)
        if target.phase != "released":
            release_specification_draft_target(target)


def real_locator_context(tmp_path, monkeypatch, *, target_locator, request_locator):
    from test_specification_draft_target import new_context

    root, manifest, target, physical = new_context(
        tmp_path, manifest_locator=target_locator
    )
    request_source = root / request_locator
    if request_source != manifest:
        request_source.parent.mkdir(parents=True, exist_ok=True)
        request_source.write_bytes(manifest.read_bytes())
    monkeypatch.setenv("CODEX_THREAD_ID", "real-locator-equality-proof")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    issue = root / "work/issues/2026/10/06/fb-2026-10-06-locator-proof.md"
    issue.parent.mkdir(parents=True)
    issue.write_text("""# Issue: Locator proof
- Slug: locator-proof
- Tag: fb/2026-10-06/locator-proof
- Status: In Progress
- Owner: codex-real-locator-equality-proof
- Captured: 2026-10-06
- Recorder: codex-real-locator-equality-proof
## Ownership Scope
- `customer/specs`
## Updates (append-only)
""")
    request = IssueDraftPackageRequest(
        issue_ref="fb/2026-10-06/locator-proof",
        expected_issue_sha256=digest(issue.read_bytes()),
        manifest_locator=request_locator,
        expected_manifest_sha256=digest(request_source.read_bytes()),
        target_locator="customer/specs/widget",
        scratch_locator=physical.scratch_path,
        ordered_members=(
            ("README.md", b"draft"),
            ("aware.spec.toml", b"owned parser input"),
        ),
        authoring_intent_ref="locator-proof",
        client_intent_id="exact-locator-attempt",
    )
    provider = FilesystemIssueOperationProvider(
        repository_root=root, protocol_source_ref=request_locator
    )
    return root, manifest, target, physical, request, provider


@pytest.mark.parametrize(
    "target_locator,request_locator",
    [
        ("aware.protocol.toml", "configuration/team/aware.protocol.toml"),
        ("configuration/team/aware.protocol.toml", "aware.protocol.toml"),
    ],
)
def test_genuine_equal_byte_different_manifest_locators_refuse_before_effects(
    tmp_path, monkeypatch, target_locator, request_locator
):
    from aware_protocol_fs_adapter import release_specification_draft_target

    root, manifest, target, physical, request, provider = real_locator_context(
        tmp_path,
        monkeypatch,
        target_locator=target_locator,
        request_locator=request_locator,
    )
    try:
        assert manifest.read_bytes() == (root / request_locator).read_bytes()
        assert target.manifest_sha256 == request.expected_manifest_sha256
        with pytest.raises(
            IssueDraftPackageRefusal, match="draft_input_binding_mismatch"
        ):
            provider.admit_draft_package(
                request, protocol_target=target, physical_plan=physical
            )
        assert target.phase == "released"
        assert physical.phase == "released"
        assert not list((root / "customer/specs").iterdir())
    finally:
        dispose_test_original(physical)
        if target.phase != "released":
            release_specification_draft_target(target)


def test_genuine_nested_manifest_equality_completes_original_owner_loop(
    tmp_path, monkeypatch
):
    from aware_protocol_fs_adapter import (
        release_specification_draft_target,
        release_specification_selection,
        require_specification_selection,
    )

    locator = "configuration/team/aware.protocol.toml"
    root, _, target, physical, request, provider = real_locator_context(
        tmp_path, monkeypatch, target_locator=locator, request_locator=locator
    )
    handle = selection = None
    try:
        handle = provider.admit_draft_package(
            request, protocol_target=target, physical_plan=physical
        )
        assert (
            handle.observe_binding().request.manifest_locator
            == handle.observe_input_custody().manifest_locator
            == locator
        )
        stage(handle)
        image = handle.publish_package()
        selection = handle.admit_published_read(physical_postimage=image)
        receipt = handle.finish(physical_postimage=image, read_selection=selection)
        handle.validate_completed_current()
        assert receipt.evidence.package_outcome == "published"
        handle.release()
        require_specification_selection(selection)
        assert (root / "customer/specs/widget/README.md").read_bytes() == b"draft"
    finally:
        if selection is not None:
            release_specification_selection(selection)
        if handle is not None:
            handle.release()
        dispose_test_original(physical)
        if target.phase != "released":
            release_specification_draft_target(target)


@pytest.mark.parametrize(
    "entrance",
    [
        "validate_current",
        "stage_next_effect",
        "lend_staged_source",
        "publish_package",
        "finish",
        "validate_completed_current",
    ],
)
def test_changed_locator_refuses_at_each_entrance(context, protocol, entrance):
    handle = admit(context, protocol)
    if entrance in {
        "lend_staged_source",
        "publish_package",
        "finish",
        "validate_completed_current",
    }:
        stage(handle)
    image = None
    if entrance in {"finish", "validate_completed_current"}:
        image = handle.publish_package()
    if entrance == "validate_completed_current":
        handle.finish(physical_postimage=image, read_selection=unit_read(handle))
    protocol[0].manifest_locator = "other/aware.protocol.toml"
    with pytest.raises(
        IssueDraftPackageRefusal, match="protocol_manifest_locator_mismatch"
    ):
        if entrance == "finish":
            handle.finish(physical_postimage=image, read_selection=unit_read(handle))
        else:
            getattr(handle, entrance)()
    assert handle.phase == "retired"
    expected_outcome = "published" if image is not None else "none"
    assert handle.evidence.package_outcome == expected_outcome
