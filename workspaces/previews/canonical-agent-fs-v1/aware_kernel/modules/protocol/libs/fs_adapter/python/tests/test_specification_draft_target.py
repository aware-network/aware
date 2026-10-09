"""Original Protocol/FileSystem/Issue proofs, without a Protocol transition shim.

These do not claim SPEC semantic validation, installed authoring or metadata
qualification. SPEC's governed composition must add actual staged validation.
"""

from __future__ import annotations

import copy
import gc
import hashlib
import importlib.util
import os
import pickle
import subprocess
import sys
from pathlib import Path

import pytest
from aware_file_system.retained_package import retain_package_publication
from aware_protocol_fs_adapter import (
    SpecificationDraftSelectionError,
    SpecificationDraftTargetSelection,
    SpecificationSelectionError,
    admit_specification_draft_published_read,
    admit_specification_draft_target,
    admit_specification_selection,
    bind_specification_draft_physical_plan,
    finish_specification_draft_target,
    release_specification_draft_target,
    release_specification_selection,
    require_specification_draft_target,
    require_specification_selection,
    spend_specification_draft_publication,
)
from aware_protocol_fs_adapter import specification_draft_target as implementation
from test_specification_selection import TARGET, source


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def test_draft_admission_retains_real_manifest_guard_reason_without_effects(tmp_path):
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source())
    (tmp_path / "customer/specs").mkdir(parents=True)
    before = manifest.read_bytes()
    descriptors = set(os.listdir("/proc/self/fd"))
    with pytest.raises(SpecificationDraftSelectionError) as caught:
        admit_specification_draft_target(
            repository_root=tmp_path,
            manifest_path=manifest,
            selected_manifest_path=TARGET,
            expected_manifest_sha256="sha256:" + "a" * 64,
        )
    error = caught.value
    assert error.code == "specification_draft_admission_failed"
    assert isinstance(error.__cause__, SpecificationSelectionError)
    assert error.__cause__.code == "specification_selection_manifest_changed"
    assert error.__cause__.diagnostics == ("specification_selection_manifest_changed",)
    assert error.diagnostics == (
        "specification_draft_admission_failed",
        "source_detail:SpecificationSelectionError",
        *error.__cause__.diagnostics,
    )
    assert manifest.read_bytes() == before
    assert not (tmp_path / "customer/specs/widget").exists()
    assert set(os.listdir("/proc/self/fd")) == descriptors


def test_draft_admission_preserves_typed_owner_diagnostics_and_notes(monkeypatch):
    original = SpecificationSelectionError(
        "specification_selection_paths_invalid", diagnostics=("owner_detail:retained",)
    )
    original.add_note("selection_cleanup_failed:OSError")

    def refuse(**kwargs):
        raise original

    monkeypatch.setattr(implementation, "admit_specification_selection", refuse)
    with pytest.raises(SpecificationDraftSelectionError) as caught:
        admit_specification_draft_target(
            repository_root=Path("."),
            manifest_path=Path("aware.protocol.toml"),
            selected_manifest_path=TARGET,
            expected_manifest_sha256="sha256:" + "a" * 64,
        )
    assert caught.value.__cause__ is original
    assert caught.value.diagnostics == (
        "specification_draft_admission_failed",
        "source_detail:SpecificationSelectionError",
        *original.diagnostics,
        "selection_cleanup_failed:OSError",
    )


def test_draft_admission_cleanup_failure_does_not_erase_original_cause(
    tmp_path, monkeypatch
):
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source())
    (tmp_path / "customer/specs").mkdir(parents=True)
    original = SpecificationSelectionError("specification_selection_source_unavailable")
    release = implementation._release_owned_selection
    releases = []
    descriptors = set(os.listdir("/proc/self/fd"))

    def refuse(selection):
        raise original

    def interrupted(selection):
        releases.append(selection)
        release(selection)
        raise KeyboardInterrupt()

    monkeypatch.setattr(implementation, "_retained", refuse)
    monkeypatch.setattr(implementation, "_release_owned_selection", interrupted)
    with pytest.raises(SpecificationDraftSelectionError) as caught:
        admit_specification_draft_target(
            repository_root=tmp_path,
            manifest_path=manifest,
            selected_manifest_path=TARGET,
            expected_manifest_sha256=digest(manifest.read_bytes()),
        )
    assert caught.value.__cause__ is original
    assert caught.value.code == "specification_draft_admission_failed"
    assert original.code in caught.value.diagnostics
    assert (
        "draft_admission_cleanup_failed:KeyboardInterrupt" in caught.value.diagnostics
    )
    assert len(releases) == 1
    assert set(os.listdir("/proc/self/fd")) == descriptors
    assert not (tmp_path / "customer/specs/widget").exists()


def test_draft_admission_does_not_promote_generic_diagnostics_or_raw_error(monkeypatch):
    original = OSError("private-input-body-must-not-be-emitted")
    original.diagnostics = ("caller_supplied_authority",)

    def refuse(**kwargs):
        raise original

    monkeypatch.setattr(implementation, "admit_specification_selection", refuse)
    with pytest.raises(SpecificationDraftSelectionError) as caught:
        admit_specification_draft_target(
            repository_root=Path("."),
            manifest_path=Path("aware.protocol.toml"),
            selected_manifest_path=TARGET,
            expected_manifest_sha256="sha256:" + "a" * 64,
        )
    assert caught.value.__cause__ is original
    assert caught.value.diagnostics == (
        "specification_draft_admission_failed",
        "source_detail:OSError",
    )


@pytest.mark.parametrize("original", [KeyboardInterrupt(), SystemExit(2)])
def test_draft_admission_preserves_original_interruption(monkeypatch, original):
    def refuse(**kwargs):
        raise original

    monkeypatch.setattr(implementation, "admit_specification_selection", refuse)
    with pytest.raises(type(original)) as caught:
        admit_specification_draft_target(
            repository_root=Path("."),
            manifest_path=Path("aware.protocol.toml"),
            selected_manifest_path=TARGET,
            expected_manifest_sha256="sha256:" + "a" * 64,
        )
    assert caught.value is original


def new_context(tmp_path, *, manifest_locator="aware.protocol.toml", absolute=False):
    manifest = tmp_path / manifest_locator
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(source())
    (tmp_path / "customer/specs").mkdir(parents=True)
    target = admit_specification_draft_target(
        repository_root=tmp_path,
        manifest_path=manifest if absolute else Path(manifest_locator),
        selected_manifest_path=TARGET,
        expected_manifest_sha256=digest(manifest.read_bytes()),
    )
    plan = retain_package_publication(
        root=tmp_path,
        target_path="customer/specs/widget",
        scratch_path="customer/specs/.aware-spec-draft-" + "a" * 32,
        ordered_members=(
            ("README.md", b"draft"),
            ("aware.spec.toml", b"owned parser input"),
        ),
    )
    return tmp_path, manifest, target, plan


@pytest.fixture
def context(tmp_path):
    values = new_context(tmp_path)
    _, _, target, plan = values
    yield values
    release_specification_draft_target(target)
    plan.release()


def publish(context):
    _, _, target, plan = context
    bind_specification_draft_physical_plan(target, physical_plan=plan)
    while plan.phase != "staged":
        plan.stage_next_effect()
        require_specification_draft_target(target)
    spend_specification_draft_publication(target)
    require_specification_draft_target(target)  # Known not submitted yet.
    image = plan.publish_package()
    require_specification_draft_target(target)  # Actual original postimage.
    return image


def test_default_manifest_locator_is_distinct_from_spec_target_and_effect_free(context):
    root, manifest, target, plan = context
    before = {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    descriptors = set(os.listdir("/proc/self/fd"))
    assert target.manifest_locator == "aware.protocol.toml"
    assert target.manifest_sha256 == digest(manifest.read_bytes())
    assert target.selected_manifest_path == TARGET
    assert target.target_locator == "customer/specs/widget"
    assert target.manifest_locator != target.selected_manifest_path
    assert target.phase == "absent" and plan.phase == "planned"
    assert before == {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    assert set(os.listdir("/proc/self/fd")) == descriptors


@pytest.mark.parametrize("absolute", [False, True])
def test_nested_manifest_locator_comes_from_original_admission(tmp_path, absolute):
    locator = "configuration/team/aware.protocol.toml"
    _, _, target, plan = new_context(
        tmp_path, manifest_locator=locator, absolute=absolute
    )
    try:
        assert target.manifest_locator == locator
        assert target.phase == "absent" and plan.phase == "planned"
        assert not (tmp_path / "aware.protocol.toml").exists()
    finally:
        release_specification_draft_target(target)
        plan.release()


def test_same_byte_different_manifest_coordinates_are_not_equivalent(context):
    root, manifest, first, _ = context
    second_path = root / "configuration/aware.protocol.toml"
    second_path.parent.mkdir()
    second_path.write_bytes(manifest.read_bytes())
    second = admit_specification_draft_target(
        repository_root=root,
        manifest_path=second_path,
        selected_manifest_path=TARGET,
        expected_manifest_sha256=first.manifest_sha256,
    )
    try:
        assert first.manifest_sha256 == second.manifest_sha256
        assert first.target_locator == second.target_locator
        assert first.selected_manifest_path == second.selected_manifest_path
        assert first.manifest_locator == "aware.protocol.toml"
        assert second.manifest_locator == "configuration/aware.protocol.toml"
        assert first.manifest_locator != second.manifest_locator
        assert first.phase == second.phase == "absent"
    finally:
        release_specification_draft_target(second)
    # This proves distinct Protocol projections, not the Issue owner's pending
    # request-locator refusal. Do not reproduce its join policy in this test.


@pytest.mark.parametrize("kind", ["forged", "wrong-type"])
def test_manifest_locator_requires_original_target(kind):
    value = (
        object.__new__(SpecificationDraftTargetSelection)
        if kind == "forged"
        else object()
    )
    with pytest.raises(SpecificationDraftSelectionError, match="original_required"):
        SpecificationDraftTargetSelection.manifest_locator.fget(value)


@pytest.mark.parametrize("terminal", ["released", "retired"])
def test_manifest_locator_refuses_terminal_target(context, terminal):
    _, manifest, target, _ = context
    if terminal == "released":
        release_specification_draft_target(target)
    else:
        original = manifest.read_bytes()
        manifest.write_bytes(original + b"\n# stale\n")
        with pytest.raises(SpecificationDraftSelectionError):
            target.revalidate()
        manifest.write_bytes(original)
    with pytest.raises(SpecificationDraftSelectionError, match="terminal"):
        _ = target.manifest_locator
    assert target.phase == terminal


def test_detached_locator_survives_cleanup_without_reopening_target(context):
    _, _, target, _ = context
    locator = target.manifest_locator
    release_specification_draft_target(target)
    assert locator == "aware.protocol.toml"
    with pytest.raises(SpecificationDraftSelectionError, match="terminal"):
        require_specification_draft_target(target)
    with pytest.raises(SpecificationDraftSelectionError, match="original_required"):
        require_specification_draft_target(locator)


def test_manifest_locator_checks_original_source_identity_and_retires(context):
    _, manifest, target, _ = context
    replacement = manifest.with_name("replacement")
    replacement.write_bytes(manifest.read_bytes())
    replacement.replace(manifest)
    with pytest.raises(SpecificationDraftSelectionError, match="currentness_failed"):
        _ = target.manifest_locator
    assert target.phase == "retired"
    with pytest.raises(SpecificationDraftSelectionError, match="terminal"):
        _ = target.manifest_locator


def test_manifest_locator_interrupted_check_retires_and_releases(context, monkeypatch):
    _, _, target, _ = context
    descriptors = set(os.listdir("/proc/self/fd"))

    def interrupted(_selection):
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        implementation.SpecificationSourceSelection, "revalidate", interrupted
    )
    with pytest.raises(KeyboardInterrupt):
        _ = target.manifest_locator
    assert target.phase == "retired"
    assert set(os.listdir("/proc/self/fd")) < descriptors


def test_manifest_locator_consumed_read_does_not_renew_write_authority(context):
    _, _, target, plan = context
    image = publish(context)
    selection = admit_specification_draft_published_read(
        target, physical_postimage=image
    )
    try:
        finish_specification_draft_target(target, read_selection=selection)
        plan.finish(image)
        plan.release()
        assert target.manifest_locator == "aware.protocol.toml"
        assert target.phase == "consumed"
        with pytest.raises(SpecificationDraftSelectionError, match="binding_replay"):
            bind_specification_draft_physical_plan(target, physical_plan=plan)
    finally:
        release_specification_selection(selection)


def test_manifest_locator_is_original_process_only(context):
    _, _, target, _ = context
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        try:
            _ = target.manifest_locator
        except SpecificationDraftSelectionError as error:
            os.write(write_fd, error.code.encode())
            os._exit(0)
        os._exit(1)
    os.close(write_fd)
    try:
        observed = os.read(read_fd, 1024)
        _, status = os.waitpid(child, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        assert observed == b"specification_draft_foreign_process"
        assert target.manifest_locator == "aware.protocol.toml"
        assert target.phase == "absent"
    finally:
        os.close(read_fd)


def test_nested_original_locator_constructs_genuine_issue_request(
    tmp_path, monkeypatch
):
    from aware_issue_fs_adapter import FilesystemIssueOperationProvider
    from aware_issue_sdk import IssueDraftPackageRequest

    locator = "configuration/team/aware.protocol.toml"
    root, manifest, target, plan = new_context(tmp_path, manifest_locator=locator)
    monkeypatch.setenv("CODEX_THREAD_ID", "protocol-locator-proof")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    issue = root / "work/issues/2026/10/06/fb-2026-10-06-proof.md"
    issue.parent.mkdir(parents=True)
    issue.write_text("""# Issue: Proof
- Slug: proof
- Tag: fb/2026-10-06/proof
- Status: In Progress
- Owner: codex-protocol-locator-proof
- Captured: 2026-10-06
- Recorder: codex-protocol-locator-proof
## Ownership Scope
- `customer/specs`
## Updates (append-only)
""")
    handle = None
    try:
        before = {
            str(p.relative_to(root)): p.read_bytes()
            for p in root.rglob("*")
            if p.is_file()
        }
        request = IssueDraftPackageRequest(
            issue_ref="fb/2026-10-06/proof",
            expected_issue_sha256=digest(issue.read_bytes()),
            manifest_locator=target.manifest_locator,
            expected_manifest_sha256=digest(manifest.read_bytes()),
            target_locator=target.target_locator,
            scratch_locator=plan.scratch_path,
            ordered_members=(
                ("README.md", b"draft"),
                ("aware.spec.toml", b"owned parser input"),
            ),
            authoring_intent_ref="spec-draft-proof",
            client_intent_id="one-attempt",
        )
        provider = FilesystemIssueOperationProvider(
            repository_root=root, protocol_source_ref=locator
        )
        handle = provider.admit_draft_package(
            request, protocol_target=target, physical_plan=plan
        )
        snapshot = handle.observe_binding()
        assert snapshot.request.manifest_locator == target.manifest_locator == locator
        assert snapshot.execution_ref == "codex-protocol-locator-proof"
        assert plan.phase == "planned"
        assert before == {
            str(p.relative_to(root)): p.read_bytes()
            for p in root.rglob("*")
            if p.is_file()
        }
        handle.release()
        assert snapshot.request.manifest_locator == locator
    finally:
        if handle is not None:
            handle.release()
        release_specification_draft_target(target)
        plan.release()


def test_original_transition_and_independent_read(context):
    root, manifest, target, plan = context
    before = manifest.read_bytes()
    image = publish(context)
    selection = admit_specification_draft_published_read(
        target, physical_postimage=image
    )
    try:
        finish_specification_draft_target(target, read_selection=selection)
        plan.finish(image)
        require_specification_draft_target(target)
        plan.release()
        require_specification_draft_target(target)  # Must not revalidate released plan.
        release_specification_draft_target(target)
        require_specification_selection(selection)
        assert manifest.read_bytes() == before
        assert (root / TARGET).read_bytes() == b"owned parser input"
    finally:
        release_specification_selection(selection)


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_target_cannot_be_copied(context, operation):
    with pytest.raises(TypeError):
        operation(context[2])


def test_original_target_required(context):
    with pytest.raises(TypeError):
        SpecificationDraftTargetSelection()
    forged = object.__new__(SpecificationDraftTargetSelection)
    for value in (object(), forged, context[3]):
        with pytest.raises(SpecificationDraftSelectionError, match="original_required"):
            require_specification_draft_target(value)


@pytest.mark.parametrize("kind", ["directory", "file", "dangling", "fifo"])
def test_existing_target_never_admitted(tmp_path, kind):
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source())
    parent = tmp_path / "customer/specs"
    parent.mkdir(parents=True)
    target = parent / "widget"
    if kind == "directory":
        target.mkdir()
    elif kind == "file":
        target.write_text("existing")
    elif kind == "dangling":
        target.symlink_to("missing")
    else:
        os.mkfifo(target)
    with pytest.raises(SpecificationDraftSelectionError):
        admit_specification_draft_target(
            repository_root=tmp_path,
            manifest_path=manifest,
            selected_manifest_path=TARGET,
            expected_manifest_sha256=digest(manifest.read_bytes()),
        )


@pytest.mark.parametrize("delta", ["comment", "identity", "parent", "mode"])
def test_admission_currentness_is_terminal(context, delta):
    root, manifest, target, _ = context
    original = manifest.read_bytes()
    if delta == "comment":
        manifest.write_bytes(original + b"\n# change\n")
    elif delta == "identity":
        replacement = manifest.with_name("replacement")
        replacement.write_bytes(original)
        replacement.replace(manifest)
    elif delta == "parent":
        (root / "customer/specs").rename(root / "customer/previous")
        (root / "customer/specs").mkdir()
    else:
        (root / "customer/specs").chmod(0o700)
    with pytest.raises(SpecificationDraftSelectionError):
        require_specification_draft_target(target)
    manifest.write_bytes(original)
    assert target.phase == "retired"
    with pytest.raises(SpecificationDraftSelectionError, match="terminal"):
        require_specification_draft_target(target)


def test_missing_parent_and_digest_required(tmp_path):
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source())
    for expected in (None, "sha256:" + "0" * 64, digest(manifest.read_bytes())):
        with pytest.raises(SpecificationDraftSelectionError):
            admit_specification_draft_target(
                repository_root=tmp_path,
                manifest_path=manifest,
                selected_manifest_path=TARGET,
                expected_manifest_sha256=expected,
            )


def test_foreign_physical_plan_refuses_without_effect(context):
    root, _, target, _ = context
    foreign = retain_package_publication(
        root=root, target_path="customer/specs/other", ordered_members=(("a", b"a"),)
    )
    try:
        with pytest.raises(SpecificationDraftSelectionError, match="plan_mismatch"):
            bind_specification_draft_physical_plan(target, physical_plan=foreign)
        assert not (root / "customer/specs/widget").exists()
        assert foreign.phase == "planned"
    finally:
        foreign.release()


def test_missing_owner_export_is_typed_and_no_effect(context, monkeypatch):
    root, _, target, plan = context
    real_import = implementation.import_module

    def missing(name):
        if name == "aware_file_system.retained_package":
            raise ImportError("not supplied")
        return real_import(name)

    monkeypatch.setattr(implementation, "import_module", missing)
    with pytest.raises(
        SpecificationDraftSelectionError, match="integration_unavailable"
    ):
        bind_specification_draft_physical_plan(target, physical_plan=plan)
    assert list((root / "customer/specs").iterdir()) == []


@pytest.mark.parametrize("operation", ["bind", "spend", "read", "finish"])
def test_consumed_target_never_replays_effects(context, operation):
    root, _, target, plan = context
    image = publish(context)
    selection = admit_specification_draft_published_read(
        target, physical_postimage=image
    )
    finish_specification_draft_target(target, read_selection=selection)
    try:
        with pytest.raises(SpecificationDraftSelectionError):
            if operation == "bind":
                bind_specification_draft_physical_plan(target, physical_plan=plan)
            elif operation == "spend":
                spend_specification_draft_publication(target)
            elif operation == "read":
                admit_specification_draft_published_read(
                    target, physical_postimage=image
                )
            else:
                finish_specification_draft_target(target, read_selection=selection)
        assert target.phase == "retired"
        require_specification_selection(selection)
        assert (root / TARGET).exists()
    finally:
        release_specification_selection(selection)


def test_finish_requires_exact_correlated_selection(context):
    root, manifest, target, _ = context
    image = publish(context)
    selected = admit_specification_draft_published_read(
        target, physical_postimage=image
    )
    ordinary = admit_specification_selection(
        repository_root=root, manifest_path=manifest, selected_manifest_paths=(TARGET,)
    ).selection
    try:
        with pytest.raises(SpecificationDraftSelectionError, match="finish_refused"):
            finish_specification_draft_target(target, read_selection=ordinary)
        require_specification_selection(selected)
    finally:
        release_specification_selection(selected)
        release_specification_selection(ordinary)


@pytest.mark.parametrize("changed", ["manifest", "member", "extra", "directory"])
def test_consumed_read_detects_stale_postimage(context, changed):
    root, manifest, target, plan = context
    image = publish(context)
    selected = admit_specification_draft_published_read(
        target, physical_postimage=image
    )
    finish_specification_draft_target(target, read_selection=selected)
    plan.finish(image)
    plan.release()
    if changed == "manifest":
        manifest.write_bytes(manifest.read_bytes() + b"\n# stale\n")
    elif changed == "member":
        (root / TARGET).write_bytes(b"changed")
    elif changed == "extra":
        (root / "customer/specs/widget/extra").write_bytes(b"unadmitted")
    else:
        (root / "customer/specs/widget").rename(root / "customer/specs/original")
        (root / "customer/specs/widget").mkdir()
    with pytest.raises(SpecificationDraftSelectionError):
        require_specification_draft_target(target)
    assert target.phase == "retired"
    # Correlated read is terminally retired; no cleanup deletes public files.
    with pytest.raises(SpecificationSelectionError):
        require_specification_selection(selected)
    assert (root / "customer/specs/widget").exists()


def test_reader_outlives_target_gc(tmp_path):
    values = new_context(tmp_path)
    _, _, target, plan = values
    image = publish(values)
    selection = admit_specification_draft_published_read(
        target, physical_postimage=image
    )
    plan.release()
    release_specification_draft_target(target)
    del values
    del target
    gc.collect()
    try:
        require_specification_selection(selection)
    finally:
        release_specification_selection(selection)


@pytest.mark.parametrize("entrance", ["require", "bind", "spend", "read", "finish"])
def test_interrupted_target_check_is_terminal(context, monkeypatch, entrance):
    _, _, target, plan = context

    def interrupted():
        raise KeyboardInterrupt()

    monkeypatch.setattr(implementation, "_owner", interrupted)
    if entrance == "bind":
        action = lambda: bind_specification_draft_physical_plan(
            target, physical_plan=plan
        )
    else:
        monkeypatch.undo()
        bind_specification_draft_physical_plan(target, physical_plan=plan)
        monkeypatch.setattr(implementation, "_owner", interrupted)
        if entrance == "require":
            action = lambda: require_specification_draft_target(target)
        elif entrance == "spend":
            action = lambda: spend_specification_draft_publication(target)
        elif entrance == "read":
            action = lambda: admit_specification_draft_published_read(
                target, physical_postimage=object()
            )
        else:
            action = lambda: finish_specification_draft_target(
                target, read_selection=object()
            )
    with pytest.raises(KeyboardInterrupt):
        action()
    assert target.phase == "retired"


def test_genuine_issue_chain_uses_real_protocol(context, monkeypatch):
    from aware_issue_fs_adapter import FilesystemIssueOperationProvider
    from aware_issue_sdk import IssueDraftPackageRequest

    root, manifest, target, plan = context
    monkeypatch.setenv("CODEX_THREAD_ID", "protocol-draft-proof")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    issue = root / "work/issues/2026/10/06/fb-2026-10-06-proof.md"
    issue.parent.mkdir(parents=True)
    issue.write_text("""# Issue: Proof
- Slug: proof
- Tag: fb/2026-10-06/proof
- Status: In Progress
- Owner: codex-protocol-draft-proof
- Captured: 2026-10-06
- Recorder: codex-protocol-draft-proof
## Ownership Scope
- `customer/specs`
## Updates (append-only)
""")
    request = IssueDraftPackageRequest(
        issue_ref="fb/2026-10-06/proof",
        expected_issue_sha256=digest(issue.read_bytes()),
        manifest_locator="aware.protocol.toml",
        expected_manifest_sha256=digest(manifest.read_bytes()),
        target_locator="customer/specs/widget",
        scratch_locator=plan.scratch_path,
        ordered_members=(
            ("README.md", b"draft"),
            ("aware.spec.toml", b"owned parser input"),
        ),
        authoring_intent_ref="spec-draft-proof",
        client_intent_id="one-attempt",
    )
    provider = FilesystemIssueOperationProvider(repository_root=root)
    handle = provider.admit_draft_package(
        request, protocol_target=target, physical_plan=plan
    )
    while handle.phase != "staged":
        handle.stage_next_effect()
    lens = handle.lend_staged_source()
    fd = lens.duplicate_parent_descriptor()
    os.close(fd)
    image = handle.publish_package()
    selection = admit_specification_draft_published_read(
        target, physical_postimage=image
    )
    try:
        receipt = handle.finish(physical_postimage=image, read_selection=selection)
        handle.validate_completed_current()
        evidence = handle.release()
        assert (
            receipt.evidence.package_outcome == evidence.package_outcome == "published"
        )
        require_specification_draft_target(target)
        require_specification_selection(selection)
        assert sys.modules[implementation.__name__] is implementation
    finally:
        release_specification_selection(selection)
        handle.release()


def test_real_fork_refuses_and_closes_child_target_only(context):
    _, _, target, _ = context
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        before = len(os.listdir("/proc/self/fd"))
        try:
            require_specification_draft_target(target)
        except SpecificationDraftSelectionError as error:
            after = len(os.listdir("/proc/self/fd"))
            os.write(write_fd, f"{error.code}:{before - after}".encode())
            os._exit(0)
        os._exit(1)
    os.close(write_fd)
    try:
        observed = os.read(read_fd, 1024)
        _, status = os.waitpid(child, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        assert observed == b"specification_draft_foreign_process:1"
        require_specification_draft_target(target)
    finally:
        os.close(read_fd)


def test_failed_final_read_construction_closes_issued_descriptors(context, monkeypatch):
    root, _, target, plan = context
    image = publish(context)
    before = set(os.listdir("/proc/self/fd"))
    original = implementation._attach_original_postimage

    def interrupted(selection, **kwargs):
        original(selection, **kwargs)
        raise KeyboardInterrupt()

    monkeypatch.setattr(implementation, "_attach_original_postimage", interrupted)
    with pytest.raises(KeyboardInterrupt):
        admit_specification_draft_published_read(target, physical_postimage=image)
    assert target.phase == "retired"
    assert set(os.listdir("/proc/self/fd")) <= before
    assert (root / TARGET).read_bytes() == b"owned parser input"
    assert plan.evidence.package_outcome == "published"


def test_unknown_publication_cannot_issue_reader(context, monkeypatch):
    from aware_file_system import retained_package as physical_owner

    _, _, target, plan = context
    bind_specification_draft_physical_plan(target, physical_plan=plan)
    plan.stage()
    spend_specification_draft_publication(target)

    def uncertain(*args):
        raise OSError("submission outcome unknown")

    monkeypatch.setattr(physical_owner, "_rename_no_replace", uncertain)
    with pytest.raises(physical_owner.PackagePublicationRefusal):
        plan.publish_package()
    with pytest.raises(SpecificationDraftSelectionError):
        admit_specification_draft_published_read(target, physical_postimage=object())
    assert target.phase == "retired"
    assert plan.evidence.package_outcome == "unknown"


def test_default_import_remains_neutral_and_owner_integration_lazy():
    root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
    roots = [
        root / p
        for p in (
            "workspaces/aware_kernel/modules/protocol/libs/runtime/python",
            "workspaces/aware_kernel/modules/protocol/sdks/protocol/python",
            "workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python",
        )
    ]
    code = f"""
import sys
sys.path[:0] = {[str(p) for p in roots]!r}
class BlockOwners:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('aware_file_system', 'aware_issue', 'aware_specification')):
            raise ModuleNotFoundError(fullname)
sys.meta_path.insert(0, BlockOwners())
import aware_protocol_fs_adapter
assert not any(n.startswith(('aware_file_system', 'aware_issue', 'aware_specification')) for n in sys.modules)
"""
    subprocess.run([sys.executable, "-I", "-B", "-c", code], check=True)


def test_cleanup_failure_remains_in_typed_target_diagnostics(context, monkeypatch):
    _, manifest, target, _ = context
    original = implementation._release_owned_selection

    def interrupted(selection):
        original(selection)
        raise KeyboardInterrupt()

    monkeypatch.setattr(implementation, "_release_owned_selection", interrupted)
    manifest.write_bytes(manifest.read_bytes() + b"\n# stale\n")
    with pytest.raises(SpecificationDraftSelectionError) as caught:
        require_specification_draft_target(target)
    assert "draft_target_cleanup_failed:KeyboardInterrupt" in caught.value.diagnostics
    assert target.phase == "retired"


def test_published_qualified_fixture_reaches_real_spec_reader(tmp_path, monkeypatch):
    """Real parser/reader integration, not SPEC's unimplemented draft writer."""
    from aware_issue_fs_adapter import FilesystemIssueOperationProvider
    from aware_issue_sdk import IssueDraftPackageRequest
    from aware_specification_fs_sdk_adapter import SpecificationFsSdkProvider
    from aware_specification_sdk import (
        SpecificationObserveRequest,
        SpecificationSdkClient,
    )

    repo = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
    fixture_path = (
        repo
        / "workspaces/aware_kernel/modules/specification/libs/fs_adapter/python/tests/conftest.py"
    )
    spec = importlib.util.spec_from_file_location(
        "draft_protocol_spec_fixture", fixture_path
    )
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    fixture_base = tmp_path / "fixture"
    fixture_base.mkdir()
    fixture_root, fixture_relative = fixture.canonical_tree.__wrapped__(fixture_base)
    package = fixture_root / fixture_relative
    members = tuple(
        sorted(
            (p.relative_to(package).as_posix(), p.read_bytes())
            for p in package.rglob("*")
            if p.is_file()
        )
    )
    root = tmp_path / "consumer"
    root.mkdir()
    manifest = root / "aware.protocol.toml"
    manifest.write_text(source())
    (root / "customer/specs").mkdir(parents=True)
    target = admit_specification_draft_target(
        repository_root=root,
        manifest_path=manifest,
        selected_manifest_path=TARGET,
        expected_manifest_sha256=digest(manifest.read_bytes()),
    )
    plan = retain_package_publication(
        root=root, target_path="customer/specs/widget", ordered_members=members
    )
    monkeypatch.setenv("CODEX_THREAD_ID", "spec-read-proof")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    issue = root / "work/issues/2026/10/06/fb-2026-10-06-read.md"
    issue.parent.mkdir(parents=True)
    issue.write_text("""# Issue: Read fixture
- Slug: read
- Tag: fb/2026-10-06/read
- Status: In Progress
- Owner: codex-spec-read-proof
- Captured: 2026-10-06
- Recorder: codex-spec-read-proof
## Ownership Scope
- `customer/specs`
## Updates (append-only)
""")
    (root / "foreign.txt").write_bytes(b"preserve me")
    issuer = FilesystemIssueOperationProvider(repository_root=root)
    admission = issuer.admit_draft_package(
        IssueDraftPackageRequest(
            issue_ref="fb/2026-10-06/read",
            expected_issue_sha256=digest(issue.read_bytes()),
            manifest_locator="aware.protocol.toml",
            expected_manifest_sha256=digest(manifest.read_bytes()),
            target_locator="customer/specs/widget",
            scratch_locator=plan.scratch_path,
            ordered_members=members,
            authoring_intent_ref="qualified-fixture",
            client_intent_id="one",
        ),
        protocol_target=target,
        physical_plan=plan,
    )
    selection = None
    provider = None
    try:
        while admission.phase != "staged":
            admission.stage_next_effect()
        lens = admission.lend_staged_source()
        parent = lens.duplicate_parent_descriptor()
        try:
            staged = SpecificationFsSdkProvider(parent, (lens.stage_name,))
            try:
                staged_observation = SpecificationSdkClient(staged).observe(
                    SpecificationObserveRequest()
                )
            finally:
                staged.close()
        finally:
            os.close(parent)
        image = admission.publish_package()
        selection = admit_specification_draft_published_read(
            target, physical_postimage=image
        )
        provider = SpecificationFsSdkProvider.from_protocol_selection(selection)
        observed = SpecificationSdkClient(provider).observe(
            SpecificationObserveRequest()
        )
        assert observed.snapshot == staged_observation.snapshot
        assert observed.snapshot.definitions[0].key == "example.spec"
        receipt = admission.finish(physical_postimage=image, read_selection=selection)
        admission.validate_completed_current()
        admission.release()
        assert receipt.evidence.package_outcome == "published"
        assert (
            SpecificationSdkClient(provider).observe(SpecificationObserveRequest())
            == observed
        )
        assert (root / "foreign.txt").read_bytes() == b"preserve me"
        provider.close()
        provider = None
        require_specification_selection(
            selection
        )  # Provider does not own selection lifetime.
    finally:
        if provider is not None:
            provider.close()
        if selection is not None:
            release_specification_selection(selection)
        admission.release()
        release_specification_draft_target(target)
        plan.release()
