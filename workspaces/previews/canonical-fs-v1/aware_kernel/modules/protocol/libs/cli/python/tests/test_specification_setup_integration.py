import copy
import hashlib
import importlib.util
import os
import stat
import subprocess
import tomllib
from dataclasses import replace
from pathlib import Path

import aware_file_system.retained_mutation as physical_owner
import aware_issue_fs_adapter.source_change as issue_owner
import pytest
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_protocol_cli.specification_setup import (
    IssueGovernedSpecificationSetupProvider,
)
from aware_protocol_fs_adapter import (
    admit_specification_selection,
    release_specification_selection,
)
from aware_protocol_sdk import (
    ProtocolSpecificationSetupClient,
    ProtocolSpecificationSetupError,
    ProtocolSpecificationSetupRequest,
)
from aware_specification_fs_sdk_adapter import SpecificationFsSdkProvider
from aware_specification_sdk import SpecificationObserveRequest, SpecificationSdkClient
from packaging.requirements import Requirement

_repo = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
_spec = importlib.util.spec_from_file_location(
    "protocol_setup_spec_fixtures",
    _repo
    / "workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/tests/test_provider.py",
)
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)
canonical_tree = _fixture.canonical_tree

_source = importlib.util.spec_from_file_location(
    "protocol_setup_manifest_fixtures",
    Path(__file__).parents[3] / "fs_adapter/python/tests/test_specification_setup.py",
)
_source_fixture = importlib.util.module_from_spec(_source)
_source.loader.exec_module(_source_fixture)


def digest(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


@pytest.fixture
def setup(canonical_tree, monkeypatch):
    root, old = canonical_tree
    (root / "contracts").mkdir()
    (root / old).rename(root / "contracts/example")
    monkeypatch.setenv("CODEX_THREAD_ID", "setup-integration")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    manifest = root / "aware.protocol.toml"
    manifest.write_bytes(_source_fixture.protocol_source())
    manifest.chmod(0o664)
    (root / "AGENTS.md").write_text("Fixture bootstrap\n")
    (root / "dirty.txt").write_text("Foreign work\n")
    issue = root / "issues/2026/10/06/fb-2026-10-06-setup.md"
    issue.parent.mkdir(parents=True)
    issue.write_text("""# Issue: Setup fixture
- Slug: setup
- Tag: fb/2026-10-06/setup
- Status: In Progress
- Owner: codex-setup-integration
- Priority: P1
- Captured: 2026-10-06
- Recorder: codex-setup-integration
- Source: Isolated integration fixture
## Ownership Scope
- `aware.protocol.toml`
- `contracts`
## Updates (append-only)
- Isolated input fixture.
""")
    request = ProtocolSpecificationSetupRequest(
        repository_root=str(root),
        manifest_path="aware.protocol.toml",
        expected_manifest_sha256=digest(manifest.read_bytes()),
        issue_ref="fb/2026-10-06/setup",
        expected_issue_sha256=digest(issue.read_bytes()),
        specification_root="contracts",
        directory_paths=("contracts",),
        client_intent_id="setup-integration-1",
    )
    return root, manifest, issue, request


def invoke(request):
    return ProtocolSpecificationSetupClient(
        IssueGovernedSpecificationSetupProvider()
    ).setup_specification(request)


def observe(root, manifest):
    admission = admit_specification_selection(
        repository_root=root,
        manifest_path=manifest,
        selected_manifest_paths=("contracts/example/aware.spec.toml",),
        expected_manifest_sha256=digest(manifest.read_bytes()),
    )
    assert admission.selection is not None
    provider = SpecificationFsSdkProvider.from_protocol_selection(admission.selection)
    try:
        return SpecificationSdkClient(provider).observe(SpecificationObserveRequest())
    finally:
        provider.close()
        release_specification_selection(admission.selection)


def test_real_preview_apply_then_fresh_spec_reader(setup):
    root, manifest, issue, request = setup
    original = manifest.read_bytes()
    issue_before = issue.read_bytes()
    preview = invoke(request)
    assert (
        preview.status == "planned"
        and preview.effect == "none"
        and preview.execution_ref is None
    )
    assert manifest.read_bytes() == original
    original_umask = os.umask(0o077)
    try:
        result = invoke(replace(request, dry_run=False))
    finally:
        os.umask(original_umask)
    assert result.status == "completed" and result.effect == "applied"
    assert (
        result.manifest_postimage_sha256
        == preview.manifest_postimage_sha256
        == digest(manifest.read_bytes())
    )
    assert stat.S_IMODE(manifest.stat().st_mode) == 0o664
    assert (
        issue.read_bytes() == issue_before
        and (root / "dirty.txt").read_text() == "Foreign work\n"
    )
    observation = observe(root, manifest)
    assert len(observation.snapshot.definitions) == 1
    assert observation.iterations[0].plan.iteration_key == "proof"


@pytest.mark.parametrize("absolute", [False, True])
def test_manifest_coordinates_resolve_once(setup, absolute):
    root, manifest, _, request = setup
    result = invoke(
        replace(
            request,
            manifest_path=str(manifest) if absolute else "aware.protocol.toml",
            dry_run=False,
        )
    )
    assert result.ordered_effect_paths[-1] == "aware.protocol.toml"
    observe(root, manifest)


def test_real_issue_admission_preview_and_apply_share_original_owner(
    setup, monkeypatch
):
    _, _, _, request = setup
    calls = []
    original = FilesystemIssueOperationProvider.admit_source_change

    def capture(provider, intent):
        handle = original(provider, intent)
        calls.append((provider, handle))
        return handle

    monkeypatch.setattr(
        FilesystemIssueOperationProvider, "admit_source_change", capture
    )
    invoke(request)
    invoke(replace(request, dry_run=False))
    assert calls[0][1].phase == "retired" and calls[1][1].phase == "consumed"
    assert calls[0][0] is not calls[1][0]


@pytest.mark.parametrize(
    "kind",
    [
        "owner",
        "lifecycle",
        "scope",
        "stale_issue",
        "stale_manifest",
        "ambiguous_execution",
    ],
)
def test_real_refusals_precede_effects(setup, monkeypatch, kind):
    root, manifest, issue, request = setup
    before = manifest.read_bytes()
    if kind == "owner":
        issue.write_text(
            issue.read_text().replace("codex-setup-integration", "codex-foreign")
        )
    elif kind == "lifecycle":
        issue.write_text(issue.read_text().replace("In Progress", "Closed"))
    elif kind == "scope":
        issue.write_text(
            issue.read_text().replace("- `aware.protocol.toml`", "- `other.toml`")
        )
    elif kind == "stale_issue":
        issue.write_text(issue.read_text() + "\nChanged bytes\n")
    elif kind == "stale_manifest":
        manifest.write_bytes(before + b"\n# changed\n")
    else:
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "other")
    if kind in {"owner", "lifecycle", "scope"}:
        request = replace(request, expected_issue_sha256=digest(issue.read_bytes()))
    expected = manifest.read_bytes()
    with pytest.raises(ProtocolSpecificationSetupError) as refusal:
        invoke(replace(request, dry_run=False))
    assert refusal.value.effect == "none" and manifest.read_bytes() == expected
    assert (root / "dirty.txt").read_text() == "Foreign work\n"


def test_explicit_missing_root_ancestors_create_only_admitted_directories(setup):
    root, manifest, _, request = setup
    result = invoke(
        replace(
            request,
            specification_root="contracts/new/specs",
            directory_paths=("contracts/new", "contracts/new/specs"),
            dry_run=False,
        )
    )
    assert [e.state for e in result.effects] == ["applied", "applied", "applied"]
    assert (root / "contracts/new/specs").is_dir()
    assert list((root / "contracts/new/specs").iterdir()) == []
    assert (
        tomllib.loads(manifest.read_text())["records"]["specification"]["root"]
        == "contracts/new/specs"
    )


def test_missing_ancestor_cannot_be_implicitly_created(setup):
    root, manifest, _, request = setup
    before = manifest.read_bytes()
    with pytest.raises(ProtocolSpecificationSetupError, match="missing_ancestor"):
        invoke(
            replace(
                request,
                specification_root="contracts/new/specs",
                directory_paths=("contracts/new/specs",),
                dry_run=False,
            )
        )
    assert manifest.read_bytes() == before and not (root / "contracts/new").exists()


def test_noop_preserves_manifest_identity_but_still_prepares_requested_directory(setup):
    _, manifest, _, request = setup
    request = replace(
        request, specification_root="contracts/new", directory_paths=(), dry_run=False
    )
    invoke(request)
    original_inode = manifest.stat().st_ino
    current = replace(
        request,
        expected_manifest_sha256=digest(manifest.read_bytes()),
        directory_paths=("contracts/new",),
    )
    result = invoke(current)
    assert result.effects[0].state == "applied" and result.effects[-1].state == "none"
    assert manifest.stat().st_ino == original_inode
    result = invoke(current)
    assert result.effect == "none" and manifest.stat().st_ino == original_inode


@pytest.mark.parametrize(
    "kind", ["issue_change", "replacement_unknown", "durability", "interruption"]
)
def test_post_effect_refusals_retain_real_evidence_without_rollback(
    setup, monkeypatch, kind
):
    _, manifest, issue, request = setup
    native_replace, native_fsync = os.replace, os.fsync

    def replace_then_fail(*args, **kwargs):
        value = native_replace(*args, **kwargs)
        if kind == "issue_change":
            issue.write_text(issue.read_text() + "\nChanged during write\n")
        elif kind == "replacement_unknown":
            raise OSError("replacement completion unknown")
        return value

    def directory_sync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            if kind == "interruption":
                raise KeyboardInterrupt("durability interrupted")
            if kind == "durability":
                raise OSError("durability failed")
        return native_fsync(fd)

    monkeypatch.setattr(os, "replace", replace_then_fail)
    monkeypatch.setattr(os, "fsync", directory_sync)
    with pytest.raises(ProtocolSpecificationSetupError) as refusal:
        invoke(replace(request, dry_run=False))
    assert refusal.value.effect == (
        "unknown" if kind == "replacement_unknown" else "applied"
    )
    assert (
        tomllib.loads(manifest.read_text())["records"]["specification"]["role"]
        == "authority"
    )
    assert refusal.value.effects[-1].state in {"unknown", "applied"}


def test_final_source_substitution_refuses_actual_consumption(setup, monkeypatch):
    root, manifest, _, request = setup
    native_read = issue_owner._read_issue
    native_finish = physical_owner.RetainedPhysicalMutation.finish
    consumed = False

    def finished(handle):
        nonlocal consumed
        value = native_finish(handle)
        consumed = True
        return value

    def read_then_swap(*args):
        value = native_read(*args)
        if consumed:
            replacement = root / "substitute"
            replacement.write_bytes(manifest.read_bytes())
            replacement.replace(manifest)
        return value

    monkeypatch.setattr(physical_owner.RetainedPhysicalMutation, "finish", finished)
    monkeypatch.setattr(issue_owner, "_read_issue", read_then_swap)
    with pytest.raises(ProtocolSpecificationSetupError) as refusal:
        invoke(replace(request, dry_run=False))
    assert refusal.value.effect == "applied"


def test_issue_admission_data_and_preview_cannot_be_substituted(setup, monkeypatch):
    _, manifest, _, request = setup
    before = manifest.read_bytes()
    preview = invoke(request)
    monkeypatch.setattr(
        FilesystemIssueOperationProvider, "admit_source_change", lambda *a: preview
    )
    with pytest.raises(ProtocolSpecificationSetupError):
        invoke(replace(request, dry_run=False))
    assert manifest.read_bytes() == before


def test_preserves_real_dirty_index_and_unrelated_work(setup):
    root, manifest, _, request = setup

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root)

    git("init", "-b", "main")
    git("add", "dirty.txt")
    before = git("ls-files", "--stage")
    invoke(replace(request, dry_run=False))
    assert git("ls-files", "--stage") == before
    assert (root / "dirty.txt").read_text() == "Foreign work\n"
    observe(root, manifest)


def test_noop_and_result_values_are_not_authority(setup):
    _, _, _, request = setup
    preview = invoke(request)
    assert copy.copy(preview) == preview
    assert preview.to_wire()["effect"] == "none"


def test_optional_dependencies_do_not_enter_neutral_protocol_packages():
    source = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    assert not any("aware-issue" in dep for dep in source["project"]["dependencies"])
    assert (
        "aware-issue-fs-adapter>=0.9.1,<0.10.0"
        in source["project"]["optional-dependencies"]["specification-setup"]
    )


def test_cli_successor_admits_actual_neutral_suppliers():
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())[
        "project"
    ]
    assert project["version"] == "0.3.2"
    requirements = {
        requirement.name: requirement
        for raw in (
            *project["dependencies"],
            *project["optional-dependencies"]["specification-setup"],
        )
        for requirement in (Requirement(raw),)
    }
    for path in (
        "workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/pyproject.toml",
        "workspaces/aware_coordination/modules/workflow/sdks/issue/python/pyproject.toml",
        "workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/pyproject.toml",
    ):
        supplier = tomllib.loads((_repo / path).read_text())["project"]
        requirement = requirements[supplier["name"]]
        assert supplier["version"] in requirement.specifier
        assert any(bound.operator == "<" for bound in requirement.specifier)
    assert "0.6.1" not in requirements["aware-protocol-fs-adapter"].specifier
    assert "0.9.1" not in requirements["aware-issue-sdk"].specifier
    assert "0.8.1" not in requirements["aware-issue-fs-adapter"].specifier


@pytest.mark.parametrize(
    "field",
    ["issue_ref", "client_intent_id", "manifest_postimage_sha256", "execution_ref"],
)
def test_malformed_completion_refuses_and_keeps_applied_effects(
    setup, monkeypatch, field
):
    _, manifest, _, request = setup
    native_finish = issue_owner.FilesystemIssueSourceChangeAdmission.finish

    def finish(handle):
        receipt = native_finish(handle)
        invalid = {
            "manifest_postimage_sha256": "sha256:" + "0" * 64,
            "execution_ref": "",
        }.get(field, "foreign")
        return replace(receipt, **{field: invalid})

    monkeypatch.setattr(
        issue_owner.FilesystemIssueSourceChangeAdmission, "finish", finish
    )
    with pytest.raises(ProtocolSpecificationSetupError) as refusal:
        invoke(replace(request, dry_run=False))
    assert refusal.value.effect == "applied"
    assert refusal.value.effects[-1].after_digest == digest(manifest.read_bytes())


def test_interrupted_cleanup_preserves_completion_evidence(setup, monkeypatch):
    _, manifest, _, request = setup
    native_release = issue_owner.FilesystemIssueSourceChangeAdmission.release

    def release(handle):
        native_release(handle)
        raise KeyboardInterrupt("cleanup interrupted")

    monkeypatch.setattr(
        issue_owner.FilesystemIssueSourceChangeAdmission, "release", release
    )
    with pytest.raises(
        ProtocolSpecificationSetupError, match="cleanup_failed"
    ) as refusal:
        invoke(replace(request, dry_run=False))
    assert refusal.value.effect == "applied"
    assert refusal.value.effects[-1].after_digest == digest(manifest.read_bytes())


def test_preview_does_not_admit_a_stale_apply(setup):
    _, manifest, _, request = setup
    invoke(request)
    manifest.write_bytes(manifest.read_bytes() + b"\n# comment-only change\n")
    with pytest.raises(
        ProtocolSpecificationSetupError, match="preimage_changed"
    ) as refusal:
        invoke(replace(request, dry_run=False))
    assert refusal.value.effect == "none"


def test_missing_optional_integration_refuses_without_fallback(setup, monkeypatch):
    import aware_protocol_cli.specification_setup as composition

    _, manifest, _, request = setup
    before = manifest.read_bytes()

    def missing(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(composition, "import_module", missing)
    with pytest.raises(
        ProtocolSpecificationSetupError, match="integration_unavailable"
    ) as refusal:
        invoke(replace(request, dry_run=False))
    assert refusal.value.effect == "none" and manifest.read_bytes() == before


def test_setup_keeps_all_spec_documents_bootstrap_and_issue_bytes(setup):
    root, manifest, issue, request = setup
    documents = {
        p.relative_to(root): p.read_bytes()
        for p in (root / "contracts").rglob("*")
        if p.is_file()
    }
    bootstrap, original_issue = (root / "AGENTS.md").read_bytes(), issue.read_bytes()
    invoke(replace(request, dry_run=False))
    assert documents == {
        p.relative_to(root): p.read_bytes()
        for p in (root / "contracts").rglob("*")
        if p.is_file()
    }
    assert (
        root / "AGENTS.md"
    ).read_bytes() == bootstrap and issue.read_bytes() == original_issue
    observe(root, manifest)


def test_symlink_directory_is_not_a_physical_setup_entrance(setup):
    root, manifest, _, request = setup
    before = manifest.read_bytes()
    (root / "contracts").rename(root / "actual")
    (root / "contracts").symlink_to("actual", target_is_directory=True)
    with pytest.raises(ProtocolSpecificationSetupError) as refusal:
        invoke(replace(request, dry_run=False))
    assert refusal.value.effect == "none" and manifest.read_bytes() == before


def test_directory_effect_survives_later_issue_refusal(setup, monkeypatch):
    root, manifest, issue, request = setup
    before = manifest.read_bytes()
    native_mkdir = os.mkdir

    def mkdir_then_change(*args, **kwargs):
        value = native_mkdir(*args, **kwargs)
        issue.write_text(issue.read_text() + "\nChanged after directory creation\n")
        return value

    monkeypatch.setattr(os, "mkdir", mkdir_then_change)
    with pytest.raises(ProtocolSpecificationSetupError) as refusal:
        invoke(
            replace(
                request,
                specification_root="contracts/new",
                directory_paths=("contracts/new",),
                dry_run=False,
            )
        )
    assert refusal.value.effect == "applied"
    assert (
        refusal.value.effects[0].kind == "directory"
        and refusal.value.effects[0].state == "applied"
    )
    assert (root / "contracts/new").is_dir() and manifest.read_bytes() == before


def test_issue_issuance_rejects_candidate_read_to_admission_race(setup, monkeypatch):
    _, manifest, _, request = setup
    native_admit = FilesystemIssueOperationProvider.admit_source_change

    def admit_after_change(provider, intent):
        manifest.write_bytes(manifest.read_bytes() + b"\n# concurrent writer\n")
        return native_admit(provider, intent)

    monkeypatch.setattr(
        FilesystemIssueOperationProvider, "admit_source_change", admit_after_change
    )
    with pytest.raises(ProtocolSpecificationSetupError) as refusal:
        invoke(replace(request, dry_run=False))
    assert refusal.value.effect == "none"
    assert (
        tomllib.loads(manifest.read_text())["records"]["specification"]["role"]
        == "unavailable"
    )


@pytest.mark.parametrize("kind", ["wrong_type", "wrong_root", "tampered_digest"])
def test_sdk_invalid_post_write_result_is_unknown_not_none(setup, kind):
    root, manifest, _, request = setup

    class MalformedResultProvider:
        def setup_specification(self, intent):
            result = IssueGovernedSpecificationSetupProvider().setup_specification(
                intent
            )
            if kind == "wrong_type":
                return result.to_wire()
            if kind == "wrong_root":
                return replace(result, specification_root="other")
            object.__setattr__(result, "manifest_postimage_sha256", "invalid")
            return result

    with pytest.raises(
        ProtocolSpecificationSetupError, match="provider_result_invalid"
    ) as refusal:
        ProtocolSpecificationSetupClient(MalformedResultProvider()).setup_specification(
            replace(request, dry_run=False)
        )
    assert refusal.value.effect == "unknown"
    assert (
        tomllib.loads(manifest.read_text())["records"]["specification"]["role"]
        == "authority"
    )
    observe(root, manifest)
