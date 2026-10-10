"""Real Issue/Protocol/FileSystem/SPEC source integration, not installation.

Fault injection wraps genuine owner methods; no mocked policy or publisher.
"""

# ruff: noqa: SIM117 - keep refusal observation outside the tested context exit

import hashlib
import os
from dataclasses import replace

import pytest
from aware_file_system import retained_package as physical
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_fs_adapter.draft_package import FilesystemIssueDraftPackageAdmission
from aware_protocol_fs_adapter import (
    SpecificationDraftTargetSelection,
    admit_specification_draft_target,
    release_specification_draft_target,
)
from aware_specification_fs_adapter import SpecificationFsSchemaResolutionContext
from aware_specification_fs_sdk_adapter import (
    SpecificationFsSdkProvider,
    open_governed_specification_draft,
)
from aware_specification_fs_sdk_adapter import governed_draft as implementation
from aware_specification_fs_sdk_adapter.draft import render_draft
from aware_specification_runtime import (
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationPhaseDefinition,
    SpecificationPhaseGateDefinition,
)
from aware_specification_sdk import (
    SpecificationDraftRequest,
    SpecificationObserveRequest,
    SpecificationOperationError,
)
from test_specification_selection import source


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def draft_request():
    invariant = SpecificationInvariantDefinition("safe", "Preserve unrelated work.")
    gate = SpecificationPhaseGateDefinition(
        "reviewed",
        "The bounded contract is independently reviewed.",
        "aware.specification.gate.evidence-accepted.v1",
        "example.evidence.v1",
        ("specification:widget/invariant:safe",),
    )
    definition = SpecificationDefinition(
        "widget",
        "Widget",
        1,
        SpecificationFsSchemaResolutionContext().semantic_resolution_digest,
        (invariant,),
        (
            SpecificationPhaseDefinition(
                "first", "First", 0, gate, description="Deliver a bounded increment."
            ),
        ),
        "Coordinate safe changes.",
    )
    return SpecificationDraftRequest(
        definition, "declared-author", "approved-draft-intent"
    )


@pytest.fixture
def context(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "spec-governed-real-source-proof")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    root = tmp_path
    manifest = root / "configuration/team/aware.protocol.toml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(source())
    (root / "customer/specs").mkdir(parents=True)
    (root / "unrelated.txt").write_text("untouched dirty work\n")
    issue = root / "work/issues/2026/10/06/fb-2026-10-06-draft.md"
    issue.parent.mkdir(parents=True)
    issue.write_text("""# Issue: Draft
- Slug: draft
- Tag: fb/2026-10-06/draft
- Status: In Progress
- Owner: codex-spec-governed-real-source-proof
- Captured: 2026-10-06
- Recorder: codex-spec-governed-real-source-proof
## Ownership Scope
- `customer/specs`
## Updates (append-only)
""")
    request = draft_request()
    plan = physical.retain_package_publication(
        root=root,
        target_path="customer/specs/widget",
        scratch_path="customer/specs/.aware-spec-draft-" + "a" * 32,
        ordered_members=tuple(sorted(render_draft(request).items())),
    )
    target = admit_specification_draft_target(
        repository_root=root,
        manifest_path=manifest,
        selected_manifest_path="customer/specs/widget/aware.spec.toml",
        expected_manifest_sha256=digest(manifest.read_bytes()),
    )
    kwargs = {
        "request": request,
        "issue_provider": FilesystemIssueOperationProvider(
            repository_root=root,
            protocol_source_ref="configuration/team/aware.protocol.toml",
        ),
        "issue_ref": "fb/2026-10-06/draft",
        "expected_issue_sha256": digest(issue.read_bytes()),
        "protocol_draft_target": target,
        "physical_package_plan": plan,
        "client_intent_id": "bounded-client-attempt",
    }
    yield root, manifest, issue, kwargs
    # Successor admissions own the originals; test-only unreserved disposal
    # must not bypass their guards. Product cleanup is asserted by each test.
    for dispose, expected in (
        (
            lambda: release_specification_draft_target(target),
            "specification_draft_input_claim_required",
        ),
        (plan.release, "package_input_claim_required"),
    ):
        try:
            dispose()
        except (RuntimeError, ValueError) as error:
            if getattr(error, "code", None) != expected:
                raise


def no_package(root):
    assert not (root / "customer/specs/widget").exists()
    assert not list((root / "customer/specs").iterdir())
    assert (root / "unrelated.txt").read_text() == "untouched dirty work\n"


def test_real_loop_validates_actual_stage_and_observes_after_writer_release(
    context, monkeypatch
):
    root, _, issue, kwargs = context
    original_issue = issue.read_bytes()
    events = []
    original_observe = SpecificationFsSdkProvider._observe_adaptation

    def observe(provider, request):
        events.append((provider._roots, kwargs["physical_package_plan"].phase))
        return original_observe(provider, request)

    monkeypatch.setattr(SpecificationFsSdkProvider, "_observe_adaptation", observe)
    manager = open_governed_specification_draft(**kwargs)
    with manager as client:
        initialized = manager.observe_draft_evidence()
        assert initialized.execution_ref == "codex-spec-governed-real-source-proof"
        assert initialized.effects == () and initialized.package_outcome == "none"
        no_package(root)
        result = client.create_draft(kwargs["request"])
        assert result.observation.snapshot.definitions == (
            kwargs["request"].definition,
        )
        assert result.observation.iterations == ()
        assert result.evidence.completion_verified and result.evidence.ledger_complete
        assert result.evidence.package_outcome == "published"
        assert result.evidence.effects
        assert not result.evidence.durability_confirmed
        assert all(e.before_identity is None for e in result.evidence.effects)
        assert kwargs["physical_package_plan"].phase == "released"
        assert client.observe(SpecificationObserveRequest()) == result.observation
        assert (
            manager.binding.request.manifest_locator
            == "configuration/team/aware.protocol.toml"
        )
    assert any(
        roots[0].startswith(".aware-spec-draft-") and phase == "staged"
        for roots, phase in events
    )
    assert any(
        roots == ("customer/specs/widget",) and phase == "released"
        for roots, phase in events
    )
    assert manager.observe_draft_evidence().completion_verified
    assert issue.read_bytes() == original_issue
    assert (root / "unrelated.txt").read_text() == "untouched dirty work\n"
    assert not (root / ".git").exists()
    with pytest.raises(SpecificationOperationError, match="context_terminal"):
        client.observe(SpecificationObserveRequest())


def test_abandonment_closes_owned_holders_without_source_effects(context):
    root, _, _, kwargs = context
    manager = open_governed_specification_draft(**kwargs)
    with manager:
        no_package(root)
    assert kwargs["physical_package_plan"].phase == "released"
    assert manager.observe_draft_evidence().package_outcome == "none"
    no_package(root)
    with pytest.raises(SpecificationOperationError, match="context_terminal"):
        manager.__enter__()


@pytest.mark.parametrize(
    "operand", ["issue_provider", "protocol_draft_target", "physical_package_plan"]
)
def test_data_only_inputs_refuse_before_effects(context, operand):
    root, _, _, kwargs = context
    with pytest.raises(SpecificationOperationError):
        with open_governed_specification_draft(**{**kwargs, operand: object()}):
            pytest.fail("data-only input admitted")
    no_package(root)
    assert kwargs["physical_package_plan"].phase == "planned"


def test_forged_original_target_refuses(context):
    root, _, _, kwargs = context
    with pytest.raises(SpecificationOperationError):
        with open_governed_specification_draft(
            **{
                **kwargs,
                "protocol_draft_target": object.__new__(
                    SpecificationDraftTargetSelection
                ),
            }
        ):
            pytest.fail("forged target admitted")
    no_package(root)


def test_candidate_member_mismatch_keeps_caller_plan(context):
    root, _, _, kwargs = context
    other = replace(kwargs["request"], author_ref="other-declared-author")
    with pytest.raises(SpecificationOperationError, match="candidate_binding_mismatch"):
        with open_governed_specification_draft(**{**kwargs, "request": other}):
            pytest.fail("different candidate admitted")
    assert kwargs["physical_package_plan"].phase == "planned"
    no_package(root)


@pytest.mark.parametrize("change", ["issue", "manifest", "owner", "scope", "harness"])
def test_stale_authority_before_invocation_refuses_without_stage(
    context, monkeypatch, change
):
    root, manifest, issue, kwargs = context
    manager = open_governed_specification_draft(**kwargs)
    with pytest.raises(SpecificationOperationError) as caught, manager as client:
        if change == "issue":
            issue.write_bytes(issue.read_bytes() + b"\nchanged\n")
        elif change == "manifest":
            manifest.write_bytes(manifest.read_bytes() + b"\n# changed\n")
        elif change == "owner":
            issue.write_text(
                issue.read_text().replace(
                    "Owner: codex-spec", "Owner: codex-other-spec"
                )
            )
        elif change == "scope":
            issue.write_text(
                issue.read_text().replace("`customer/specs`", "`elsewhere`")
            )
        else:
            monkeypatch.setenv("CODEX_THREAD_ID", "different-real-execution")
        client.create_draft(kwargs["request"])
    assert caught.value.evidence.package_outcome == "none"
    assert caught.value.evidence.effects == ()
    no_package(root)


@pytest.mark.parametrize("field", ["author_ref", "authoring_intent_ref", "definition"])
def test_different_request_is_terminal_not_a_new_attempt(context, field):
    root, _, _, kwargs = context
    changed = (
        replace(
            kwargs["request"],
            definition=replace(kwargs["request"].definition, title="Different"),
        )
        if field == "definition"
        else replace(kwargs["request"], **{field: "different"})
    )
    with pytest.raises(SpecificationOperationError):
        with open_governed_specification_draft(**kwargs) as client:
            client.create_draft(changed)
    no_package(root)


def test_request_snapshot_cannot_be_mutated_after_factory_construction(context):
    root, _, _, kwargs = context
    manager = open_governed_specification_draft(**kwargs)
    request = kwargs["request"]
    object.__setattr__(request, "author_ref", "tampered")
    with pytest.raises(SpecificationOperationError, match="binding_mismatch"):
        with manager as client:
            client.create_draft(request)
    no_package(root)


def test_repeated_publication_refuses_without_changing_published_bytes(context):
    root, _, _, kwargs = context
    manager = open_governed_specification_draft(**kwargs)
    with (
        pytest.raises(SpecificationOperationError, match="invocation_replay") as caught,
        manager as client,
    ):
        result = client.create_draft(kwargs["request"])
        before = {p: (root / p).read_bytes() for p in result.created_paths}
        client.create_draft(kwargs["request"])
    assert caught.value.effect == "published"
    assert caught.value.evidence.package_outcome == "published"
    assert before == {p: (root / p).read_bytes() for p in result.created_paths}


def test_strict_staged_meaning_failure_is_before_publication(context, monkeypatch):
    root, _, _, kwargs = context
    original = SpecificationFsSdkProvider._observe_adaptation

    def reject_stage(provider, request):
        if provider._roots[0].startswith(".aware-spec-draft-"):
            raise SpecificationOperationError("strict_stage_fault_probe")
        return original(provider, request)

    monkeypatch.setattr(SpecificationFsSdkProvider, "_observe_adaptation", reject_stage)
    with (
        pytest.raises(
            SpecificationOperationError, match="strict_stage_fault_probe"
        ) as caught,
        open_governed_specification_draft(**kwargs) as client,
    ):
        client.create_draft(kwargs["request"])
    assert caught.value.effect == "none"
    assert caught.value.evidence.effects  # none package is not zero scratch effects.
    assert any(e.kind == "cleanup_file" for e in caught.value.evidence.effects)
    no_package(root)


def test_unexpected_stage_entry_is_preserved_and_never_published(context, monkeypatch):
    root, _, _, kwargs = context
    original = FilesystemIssueDraftPackageAdmission.lend_staged_source

    def add_foreign(handle):
        # Fault just before lender verifies exact known entry set.
        (
            root / kwargs["physical_package_plan"].scratch_path / "foreign.txt"
        ).write_text("foreign")
        return original(handle)

    monkeypatch.setattr(
        FilesystemIssueDraftPackageAdmission, "lend_staged_source", add_foreign
    )
    with pytest.raises(SpecificationOperationError) as caught:
        with open_governed_specification_draft(**kwargs) as client:
            client.create_draft(kwargs["request"])
    assert not (root / "customer/specs/widget").exists()
    assert (
        root / kwargs["physical_package_plan"].scratch_path / "foreign.txt"
    ).read_text() == "foreign"
    assert caught.value.evidence.residual_scratch_paths
    assert caught.value.evidence.cleanup_diagnostics


@pytest.mark.parametrize("change", ["manifest", "published_member", "issue"])
def test_late_authority_failure_keeps_known_publication(context, monkeypatch, change):
    root, manifest, issue, kwargs = context
    original = FilesystemIssueDraftPackageAdmission.release
    changed = False

    def late_change(handle):
        nonlocal changed
        # Issue's successful return horizon is its final check during release.
        # Inject before that owner check; later SPEC/Protocol reads are separate
        # sequential checks, not an atomic cross-owner transaction.
        if change == "issue" and not changed and handle.phase == "consumed":
            changed = True
            issue.write_bytes(issue.read_bytes() + b"\nlate change\n")
        result = original(handle)
        if not changed and result.package_outcome == "published":
            changed = True
            path = (
                manifest
                if change == "manifest"
                else issue
                if change == "issue"
                else root / "customer/specs/widget/SPEC.md"
            )
            path.write_bytes(path.read_bytes() + b"\nlate change\n")
        return result

    monkeypatch.setattr(FilesystemIssueDraftPackageAdmission, "release", late_change)
    with pytest.raises(SpecificationOperationError) as caught:
        with open_governed_specification_draft(**kwargs) as client:
            client.create_draft(kwargs["request"])
    assert caught.value.effect == "published"
    assert caught.value.evidence.package_outcome == "published"
    assert not caught.value.evidence.completion_verified
    assert (root / "customer/specs/widget/aware.spec.toml").is_file()


def test_return_time_change_refuses_context_exit(context):
    root, manifest, _, kwargs = context
    with pytest.raises(SpecificationOperationError) as caught:
        with open_governed_specification_draft(**kwargs) as client:
            client.create_draft(kwargs["request"])
            manifest.write_bytes(manifest.read_bytes() + b"\n# return race\n")
    assert caught.value.effect == "published"
    assert not caught.value.evidence.completion_verified
    assert (root / "customer/specs/widget").is_dir()


def test_cleanup_failure_does_not_turn_into_success(context, monkeypatch):
    root, _, _, kwargs = context
    manager = open_governed_specification_draft(**kwargs)
    with (
        pytest.raises(
            SpecificationOperationError, match="draft_cleanup_failed"
        ) as caught,
        manager as client,
    ):
        client.create_draft(kwargs["request"])
        original = manager.reader.close

        def fail_close():
            original()
            raise OSError("injected close diagnostic")

        monkeypatch.setattr(manager.reader, "close", fail_close)
    assert caught.value.effect == "published"
    assert not caught.value.evidence.completion_verified
    assert (
        "spec_reader_close_failed:OSError" in caught.value.evidence.cleanup_diagnostics
    )
    assert (root / "customer/specs/widget").is_dir()


def test_unavailable_ledger_preserves_prior_publication(context, monkeypatch):
    _, _, _, kwargs = context
    manager = open_governed_specification_draft(**kwargs)
    with (
        pytest.raises(SpecificationOperationError, match="completion_unverified"),
        manager as client,
    ):
        client.create_draft(kwargs["request"])
        original = FilesystemIssueDraftPackageAdmission.evidence

        def unavailable(handle):
            raise OSError("ledger unavailable")

        monkeypatch.setattr(
            FilesystemIssueDraftPackageAdmission, "evidence", property(unavailable)
        )
        with pytest.raises(SpecificationOperationError) as caught:
            manager.observe_draft_evidence()
        assert caught.value.evidence.package_outcome == "published"
        assert caught.value.effect == "unknown"
        assert not caught.value.evidence.ledger_complete
        monkeypatch.setattr(FilesystemIssueDraftPackageAdmission, "evidence", original)


def test_real_parser_rejects_semantic_profile_mismatch_before_publication(context):
    root, _, _, kwargs = context
    original = kwargs["request"]
    changed = replace(
        original,
        definition=replace(
            original.definition, semantic_resolution_digest="sha256:" + "0" * 64
        ),
    )
    # Renderer does not put this contextual digest in source. The existing strict
    # lowerer supplies the real profile; meaning comparison must detect the join.
    assert render_draft(changed) == render_draft(original)
    with pytest.raises(SpecificationOperationError, match="meaning_mismatch") as caught:
        with open_governed_specification_draft(
            **{**kwargs, "request": changed}
        ) as client:
            client.create_draft(changed)
    assert caught.value.evidence.effects and caught.value.effect == "none"
    no_package(root)


def test_ordinary_selection_cannot_replace_correlated_original(context, monkeypatch):
    import aware_protocol_fs_adapter as protocol

    root, manifest, _, kwargs = context
    original = FilesystemIssueDraftPackageAdmission.admit_published_read
    retained = []

    def substitute(admission, *, physical_postimage):
        retained.append(original(admission, physical_postimage=physical_postimage))
        ordinary = protocol.admit_specification_selection(
            repository_root=root,
            manifest_path=manifest,
            selected_manifest_paths=("customer/specs/widget/aware.spec.toml",),
        ).selection
        retained.append(ordinary)
        return ordinary

    monkeypatch.setattr(
        FilesystemIssueDraftPackageAdmission, "admit_published_read", substitute
    )
    try:
        with pytest.raises(SpecificationOperationError) as caught:
            with open_governed_specification_draft(**kwargs) as client:
                client.create_draft(kwargs["request"])
        assert caught.value.evidence.package_outcome == "published"
        assert not caught.value.evidence.completion_verified
        assert (root / "customer/specs/widget").is_dir()
    finally:
        for selection in retained:
            protocol.release_specification_selection(selection)


def test_known_image_survives_ledger_failure_immediately_after_publication(
    context, monkeypatch
):
    root, _, _, kwargs = context
    original = FilesystemIssueDraftPackageAdmission.evidence.fget

    def unavailable_after_image(handle):
        if kwargs["physical_package_plan"].phase == "published":
            raise OSError("post-publication ledger unavailable")
        return original(handle)

    monkeypatch.setattr(
        FilesystemIssueDraftPackageAdmission,
        "evidence",
        property(unavailable_after_image),
    )
    with pytest.raises(SpecificationOperationError) as caught:
        with open_governed_specification_draft(**kwargs) as client:
            client.create_draft(kwargs["request"])
    assert caught.value.evidence.package_outcome == "published"
    assert not caught.value.evidence.completion_verified
    assert (root / "customer/specs/widget").is_dir()


def test_interrupt_releases_owned_holders_and_preserves_interrupt(context):
    root, _, _, kwargs = context
    manager = open_governed_specification_draft(**kwargs)
    with pytest.raises(KeyboardInterrupt):
        with manager:
            raise KeyboardInterrupt("user interrupted before invocation")
    assert kwargs["physical_package_plan"].phase == "released"
    assert manager.observe_draft_evidence().effects == ()
    no_package(root)


def test_staged_source_malformed_snapshot_cannot_publish(context, monkeypatch):
    root, _, _, kwargs = context
    original = SpecificationFsSdkProvider._observe_adaptation

    def incomplete(provider, request):
        if provider._roots[0].startswith(".aware-spec-draft-"):
            return object()
        return original(provider, request)

    monkeypatch.setattr(SpecificationFsSdkProvider, "_observe_adaptation", incomplete)
    with pytest.raises(SpecificationOperationError) as caught:
        with open_governed_specification_draft(**kwargs) as client:
            client.create_draft(kwargs["request"])
    assert caught.value.evidence.effects
    assert caught.value.effect == "none"
    no_package(root)


def test_missing_supplier_never_falls_back(context, monkeypatch):
    root, _, _, kwargs = context
    original = implementation.import_module

    def missing(name):
        if name == "aware_issue_fs_adapter":
            raise ImportError("not installed")
        return original(name)

    monkeypatch.setattr(implementation, "import_module", missing)
    with pytest.raises(SpecificationOperationError, match="integration_unavailable"):
        with open_governed_specification_draft(**kwargs):
            pytest.fail("missing supplier admitted")
    no_package(root)


def test_context_does_not_leak_descriptors(context):
    _, _, _, kwargs = context
    before = len(os.listdir("/proc/self/fd"))
    with open_governed_specification_draft(**kwargs) as client:
        client.create_draft(kwargs["request"])
    # Factory owns and releases the originally retained plan/target descriptors.
    assert len(os.listdir("/proc/self/fd")) < before


def test_malformed_result_after_real_publication_retains_unknown_qualification(
    context, monkeypatch
):
    root, _, _, kwargs = context
    original = implementation._GovernedDraft.create_draft

    def malformed(provider, request):
        original(provider, request)
        return object()

    monkeypatch.setattr(implementation._GovernedDraft, "create_draft", malformed)
    with pytest.raises(
        SpecificationOperationError, match="invalid_draft_result"
    ) as caught:
        with open_governed_specification_draft(**kwargs) as client:
            client.create_draft(kwargs["request"])
    assert caught.value.effect == "unknown"
    assert caught.value.evidence.package_outcome == "published"
    assert (root / "customer/specs/widget").is_dir()


@pytest.mark.parametrize("moved", [False, True])
def test_uncertain_submission_never_retries_or_deletes_possible_publication(
    context, monkeypatch, moved
):
    root, _, _, kwargs = context
    original = physical._rename_no_replace
    calls = []

    def uncertain(parent, source_name, target_name):
        calls.append(target_name)
        if moved:
            original(parent, source_name, target_name)
        raise OSError("uncertain submission probe")

    monkeypatch.setattr(physical, "_rename_no_replace", uncertain)
    with pytest.raises(SpecificationOperationError) as caught:
        with open_governed_specification_draft(**kwargs) as client:
            client.create_draft(kwargs["request"])
    assert calls == ["widget"]
    assert caught.value.effect == "unknown"
    assert caught.value.evidence.package_outcome == "unknown"
    assert not caught.value.evidence.completion_verified
    assert any(
        e.kind == "package_publication" and e.state == "unknown"
        for e in caught.value.evidence.effects
    )
    assert (root / "customer/specs/widget").exists() is moved


def test_racing_foreign_target_is_not_replaced_or_cleaned(context, monkeypatch):
    root, _, _, kwargs = context
    original = physical._rename_no_replace

    def compete(parent, source_name, target_name):
        target = root / "customer/specs/widget"
        target.mkdir()
        (target / "foreign.txt").write_text("foreign competing target")
        original(parent, source_name, target_name)

    monkeypatch.setattr(physical, "_rename_no_replace", compete)
    with pytest.raises(SpecificationOperationError) as caught:
        with open_governed_specification_draft(**kwargs) as client:
            client.create_draft(kwargs["request"])
    assert caught.value.evidence.package_outcome == "none"
    assert (
        root / "customer/specs/widget/foreign.txt"
    ).read_text() == "foreign competing target"


def test_successful_evidence_losslessly_carries_original_physical_ledger(context):
    _, _, _, kwargs = context
    manager = open_governed_specification_draft(**kwargs)
    with manager as client:
        client.create_draft(kwargs["request"])
    projected = manager.observe_draft_evidence()
    original = kwargs["physical_package_plan"].evidence
    assert projected.package_outcome == original.package_outcome
    assert projected.residual_scratch_paths == original.residual_scratch_paths
    assert projected.cleanup_diagnostics == original.cleanup_diagnostics
    assert projected.durability_confirmed == original.durability_confirmed
    assert len(projected.effects) == len(original.effects)
    for actual, expected in zip(projected.effects, original.effects, strict=True):
        assert (
            actual.path,
            actual.kind,
            actual.state,
            actual.mode,
            actual.before_digest,
            actual.after_digest,
            actual.after_identity,
            actual.durability_confirmed,
        ) == (
            expected.path,
            expected.kind,
            expected.state.value,
            expected.mode,
            expected.before_digest,
            expected.after_digest,
            expected.after_identity,
            expected.durability_confirmed,
        )
        assert actual.before_identity is None


@pytest.mark.parametrize("primary", [True, False])
@pytest.mark.parametrize("fault", ["reader", "descriptor", "both"])
def test_staged_cleanup_preserves_primary_and_attempts_each_once(
    context, monkeypatch, primary, fault
):
    root, _, _, kwargs = context
    original_observe = SpecificationFsSdkProvider._observe_adaptation
    original_close = SpecificationFsSdkProvider.close
    original_lend = physical.StagedPackageSource.duplicate_parent_descriptor
    borrowed = []
    cleanups = []

    def observe(provider, request):
        checked = original_observe(provider, request)  # actual strict source read
        if primary and provider._roots[0].startswith(".aware-spec-draft-"):
            raise SpecificationOperationError("strict_stage_primary")
        return checked

    def lend(lens):
        fd = original_lend(lens)
        borrowed.append(fd)
        return fd

    def close(provider):
        original_close(provider)
        if provider._roots[0].startswith(".aware-spec-draft-"):
            cleanups.append("reader")
            if fault in {"reader", "both"}:
                raise OSError("reader closed, then failed probe")

    class BorrowedDescriptorOs:
        """Local borrower fault seam; original owners retain real os.close."""

        def __getattr__(self, name):
            return getattr(os, name)

        def close(self, fd):
            assert borrowed == [fd]
            cleanups.append("descriptor")
            os.close(fd)
            if fault in {"descriptor", "both"}:
                raise OSError("borrowed descriptor closed, then failed probe")

    monkeypatch.setattr(SpecificationFsSdkProvider, "_observe_adaptation", observe)
    monkeypatch.setattr(SpecificationFsSdkProvider, "close", close)
    monkeypatch.setattr(
        physical.StagedPackageSource, "duplicate_parent_descriptor", lend
    )
    monkeypatch.setattr(implementation, "os", BorrowedDescriptorOs())
    with pytest.raises(SpecificationOperationError) as caught:
        with open_governed_specification_draft(**kwargs) as client:
            client.create_draft(kwargs["request"])
    assert caught.value.code == (
        "strict_stage_primary" if primary else "draft_staged_cleanup_failed"
    )
    assert caught.value.effect == "unknown"
    evidence = caught.value.evidence
    assert evidence.package_outcome == "none"
    assert evidence.effects and not evidence.completion_verified
    diagnostics = evidence.cleanup_diagnostics
    assert ("staged_reader_close_failed:OSError" in diagnostics) == (
        fault in {"reader", "both"}
    )
    assert ("staged_descriptor_close_failed:OSError" in diagnostics) == (
        fault in {"descriptor", "both"}
    )
    assert cleanups == ["reader", "descriptor"]  # no retries after ambiguous close
    with pytest.raises(OSError):
        os.fstat(borrowed[0])
    no_package(root)
