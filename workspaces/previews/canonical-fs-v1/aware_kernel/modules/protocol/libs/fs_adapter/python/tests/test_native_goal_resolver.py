from __future__ import annotations

import copy
import os
import pickle
from pathlib import Path

import pytest

from aware_protocol_fs_adapter import (
    FilesystemRecordBinding,
    NativeGoalResolverCapability,
    NativeGoalResolverError,
    admit_native_goal_resolver,
    admit_protocol_manifest,
    require_native_goal_resolver,
)
from aware_protocol_runtime import ProtocolAdmissionOutcomeKind

_TARGET = "customer/objectives/2026/09/27/goal-2026-09-27-example.md"


def _source(*, template: str = "YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md") -> str:
    return f'''aware = 1
[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v2"
semantic_version = 2
[target]
kind = "repository"
authority_mode = "filesystem"
[bootstrap]
agent_contract = "AGENTS.md"
[records.goal]
profile = "aware.goal.phase.markdown.v1"
role = "authority"
root = "customer/objectives"
path_template = "{template}"
[records.issue]
profile = "aware.issue.markdown.v1"
role = "authority"
root = "work/issues"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"
[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"
[records.specification]
profile = "specification_fs_v1"
role = "unavailable"
[records.evidence]
profile = "aware.protocol.evidence.v1"
role = "unavailable"
'''


def _issue(root: Path, source: str | None = None) -> NativeGoalResolverCapability:
    manifest = root / "aware.protocol.toml"
    manifest.write_text(_source() if source is None else source)
    result = admit_native_goal_resolver(repository_root=root, manifest_path=manifest)
    assert result.admission.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1
    assert result.capability is not None
    return result.capability


def test_fresh_native_admission_retains_binding_without_goal_read(tmp_path: Path) -> None:
    capability = _issue(tmp_path)
    assert require_native_goal_resolver(capability) is capability
    assert capability.repository_root == tmp_path.resolve()
    assert capability.goal_root == "customer/objectives"
    assert capability.goal_template == "YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md"
    assert capability.manifest_sha256.startswith("sha256:")
    assert capability.protocol_digest.startswith("sha256:")
    location = capability.resolve_goal_path(_TARGET)
    assert location.resolved_path == tmp_path / _TARGET
    assert (location.location_date, location.location_slug) == ("2026-09-27", "example")
    assert not location.resolved_path.exists()  # Admission is not source availability.


@pytest.mark.parametrize("value", [None, {}, "customer/objectives", FilesystemRecordBinding("goal", "customer/objectives", "YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md")])
def test_caller_values_cannot_be_capabilities(value: object) -> None:
    with pytest.raises(NativeGoalResolverError, match="native_goal_capability_invalid"):
        require_native_goal_resolver(value)


def test_nominal_object_forgery_and_public_construction_refuse() -> None:
    with pytest.raises(TypeError, match="use admit_native_goal_resolver"):
        NativeGoalResolverCapability()
    forged = object.__new__(NativeGoalResolverCapability)
    with pytest.raises(NativeGoalResolverError, match="native_goal_capability_invalid"):
        require_native_goal_resolver(forged)
    with pytest.raises(TypeError, match="cannot be subclassed"):
        type("Forged", (NativeGoalResolverCapability,), {})


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_capability_cannot_be_copied_or_serialized(tmp_path: Path, operation) -> None:
    capability = _issue(tmp_path)
    with pytest.raises(TypeError, match="cannot be copied or serialized"):
        operation(capability)


@pytest.mark.skipif(not hasattr(os, "fork"), reason="requires fork")
def test_forked_process_must_freshly_admit_instead_of_inheriting_capability(tmp_path: Path) -> None:
    capability = _issue(tmp_path)
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        try:
            require_native_goal_resolver(capability)
        except NativeGoalResolverError as error:
            os.write(write_fd, error.code.encode())
        else:
            os.write(write_fd, b"unexpected_success")
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    try:
        result = os.read(read_fd, 256)
    finally:
        os.close(read_fd)
        os.waitpid(child, 0)
    assert result == b"native_goal_capability_foreign_process"
    assert require_native_goal_resolver(capability) is capability


def test_properties_cannot_be_substituted_and_decoded_result_cannot_admit(tmp_path: Path) -> None:
    capability = _issue(tmp_path)
    with pytest.raises(AttributeError):
        capability.goal_root = "elsewhere"
    result = admit_protocol_manifest(repository_root=tmp_path, manifest_path=capability.manifest_path)
    with pytest.raises(NativeGoalResolverError, match="native_goal_capability_invalid"):
        require_native_goal_resolver(result)
    with pytest.raises(NativeGoalResolverError, match="native_goal_capability_invalid"):
        require_native_goal_resolver(result.admission.to_wire())


@pytest.mark.parametrize("edit", ["\n", "\n# comment\n"])
def test_even_semantically_equal_manifest_bytes_stale_the_capability(tmp_path: Path, edit: str) -> None:
    capability = _issue(tmp_path)
    with capability.manifest_path.open("a") as source:
        source.write(edit)
    with pytest.raises(NativeGoalResolverError, match="native_goal_manifest_changed"):
        capability.resolve_goal_path(_TARGET)


@pytest.mark.parametrize("old,new", [
    ("customer/objectives", "other/goals"),
    ("YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md", "goal-YYYY-MM-DD-<slug>.md"),
    ("aware.collaboration.fs_v2", "aware.collaboration.fs_v1"),
])
def test_root_template_or_profile_change_refuses(tmp_path: Path, old: str, new: str) -> None:
    capability = _issue(tmp_path)
    capability.manifest_path.write_text(_source().replace(old, new))
    with pytest.raises(NativeGoalResolverError):
        capability.revalidate()


def test_repository_replacement_with_identical_manifest_refuses(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    capability = _issue(root)
    root.rename(tmp_path / "prior")
    root.mkdir()
    (root / "aware.protocol.toml").write_text(_source())
    with pytest.raises(NativeGoalResolverError, match="native_goal_repository_changed"):
        capability.revalidate()


def test_manifest_coordinate_substitution_with_same_bytes_refuses(tmp_path: Path) -> None:
    capability = _issue(tmp_path)
    second = tmp_path / "other" / "aware.protocol.toml"
    second.parent.mkdir()
    second.write_text(_source())
    capability.manifest_path.unlink()
    capability.manifest_path.symlink_to(second)
    with pytest.raises(NativeGoalResolverError, match="native_goal_manifest_source_changed"):
        capability.revalidate()


@pytest.mark.parametrize("target", [
    "other/objectives/2026/09/27/goal-2026-09-27-example.md",
    "customer/objectives-extra/2026/09/27/goal-2026-09-27-example.md",
    "customer/objectives/2026/09/26/goal-2026-09-27-example.md",
    "customer/objectives/2026/02/30/goal-2026-02-30-example.md",
    "customer/objectives/./2026/09/27/goal-2026-09-27-example.md",
    "customer/objectives/../2026/09/27/goal-2026-09-27-example.md",
    "customer/objectives//2026/09/27/goal-2026-09-27-example.md",
    "customer/objectives/2026/09/27/goal-2026-09-27-EXAMPLE.md",
    "customer/objectives/2026/09/27/goal-2026-09-27-example.md\n",
    "/customer/objectives/2026/09/27/goal-2026-09-27-example.md",
])
def test_target_must_match_the_exact_admitted_grammar(tmp_path: Path, target: str) -> None:
    capability = _issue(tmp_path)
    assert capability.match_goal_path(target) is None
    with pytest.raises(NativeGoalResolverError, match="native_goal_target_outside_binding"):
        capability.resolve_goal_path(target)


def test_flat_template_is_explicit_not_inferred(tmp_path: Path) -> None:
    capability = _issue(tmp_path, _source(template="goal-YYYY-MM-DD-<slug>.md"))
    assert capability.match_goal_path(_TARGET) is None
    location = capability.resolve_goal_path("customer/objectives/goal-2026-09-27-example.md")
    assert location.location_slug == "example"


@pytest.mark.parametrize("template", ["<slug>.md", "**/*.md", "custom/<goal>.md"])
def test_unsupported_templates_fail_strict_native_admission(tmp_path: Path, template: str) -> None:
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(_source(template=template))
    result = admit_native_goal_resolver(repository_root=tmp_path, manifest_path=manifest)
    assert result.capability is None
    assert "native_goal_template_unsupported" in result.admission.diagnostics


@pytest.mark.parametrize("replacement", [
    'profile = "aware.goal.markdown.v1"',
    'profile = "aware.goal.phase.markdown.v999"',
    'profile = "aware.issue.markdown.v1"',
])
def test_native_record_profile_cannot_be_swapped(tmp_path: Path, replacement: str) -> None:
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(_source().replace('profile = "aware.goal.phase.markdown.v1"', replacement))
    result = admit_native_goal_resolver(repository_root=tmp_path, manifest_path=manifest)
    assert result.admission.outcome is ProtocolAdmissionOutcomeKind.FOREIGN_PROFILE
    assert result.capability is None


def test_legacy_admission_still_works_but_cannot_issue_native_capability(tmp_path: Path) -> None:
    source = _source().replace("fs_v2", "fs_v1").replace("semantic_version = 2", "semantic_version = 1").replace("aware.goal.phase.markdown.v1", "aware.goal.markdown.v1")
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source)
    assert admit_protocol_manifest(repository_root=tmp_path, manifest_path=manifest).outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1
    with pytest.raises(NativeGoalResolverError, match="native_goal_profile_required"):
        admit_native_goal_resolver(repository_root=tmp_path, manifest_path=manifest)


def test_fs_v3_issues_the_same_native_goal_capability_type(tmp_path: Path) -> None:
    source = _source().replace(
        'profile = "aware.collaboration.fs_v2"',
        'profile = "aware.collaboration.fs_v3"',
    ).replace("semantic_version = 2", "semantic_version = 3")
    source += '''[records.project]
profile = "aware.project.context.toml.v1"
role = "authority"
root = "customer/projects"
path_template = "project-<slug>.toml"
'''
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source)
    selected = admit_native_goal_resolver(repository_root=tmp_path, manifest_path=manifest)
    assert selected.admission.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1
    assert type(selected.capability) is NativeGoalResolverCapability
    assert selected.capability is not None
    assert require_native_goal_resolver(selected.capability) is selected.capability
    assert selected.capability.resolve_goal_path(_TARGET).location_slug == "example"


@pytest.mark.parametrize("scenario", ["outside", "loop", "sibling"])
def test_at_use_symlink_changes_refuse(tmp_path: Path, scenario: str) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    capability = _issue(root)
    target = root / _TARGET
    target.parent.mkdir(parents=True)
    destination = tmp_path / "outside.md" if scenario == "outside" else root / "sibling.md"
    destination.write_text("not a Goal source")
    target.symlink_to(target if scenario == "loop" else destination)
    with pytest.raises(NativeGoalResolverError):
        capability.resolve_goal_path(_TARGET)


def test_manifest_deleted_after_issuance_refuses(tmp_path: Path) -> None:
    capability = _issue(tmp_path)
    capability.manifest_path.unlink()
    with pytest.raises(NativeGoalResolverError, match="native_goal_admission_unavailable"):
        capability.revalidate()


@pytest.mark.parametrize("key", ["goal", "issue"])
def test_native_required_records_cannot_be_projections(tmp_path: Path, key: str) -> None:
    source = _source().replace(
        f'[records.{key}]\nprofile = "aware.{"goal.phase" if key == "goal" else "issue"}.markdown.v1"\nrole = "authority"',
        f'[records.{key}]\nprofile = "aware.{"goal.phase" if key == "goal" else "issue"}.markdown.v1"\nrole = "projection"',
    )
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source)
    result = admit_native_goal_resolver(repository_root=tmp_path, manifest_path=manifest)
    assert result.capability is None
    assert f"native_record_requires_authority:{key}" in result.admission.diagnostics


def test_existing_file_cannot_be_admitted_as_goal_root(tmp_path: Path) -> None:
    (tmp_path / "customer").mkdir()
    (tmp_path / "customer/objectives").write_text("not a directory")
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(_source())
    result = admit_native_goal_resolver(repository_root=tmp_path, manifest_path=manifest)
    assert result.capability is None
    assert "native_goal_root_not_directory" in result.admission.diagnostics


def test_service_mode_cannot_issue_filesystem_capability(tmp_path: Path) -> None:
    source = _source().replace('authority_mode = "filesystem"', 'authority_mode = "service_api"\nauthority_ref = "service:goal"')
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source)
    result = admit_native_goal_resolver(repository_root=tmp_path, manifest_path=manifest)
    assert result.admission.outcome is ProtocolAdmissionOutcomeKind.AUTHORITY_UNAVAILABLE
    assert result.capability is None


def test_repeated_use_preserves_source_and_dirty_work(tmp_path: Path) -> None:
    capability = _issue(tmp_path)
    target = tmp_path / _TARGET
    target.parent.mkdir(parents=True)
    target.write_bytes(b"customer Goal bytes")
    dirty = tmp_path / "dirty.txt"
    dirty.write_bytes(b"unrelated work")
    before = {path: path.read_bytes() for path in (target, dirty, capability.manifest_path)}
    for _ in range(3):
        capability.resolve_goal_path(_TARGET)
    assert all(path.read_bytes() == content for path, content in before.items())
