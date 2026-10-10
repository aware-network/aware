"""Real Protocol issuance/borrowing tests; consumers are not a SPEC factory proof."""

from __future__ import annotations

import ast
import copy
import gc
import os
import pickle
from pathlib import Path

import pytest
from aware_protocol_fs_adapter import (
    FilesystemRecordBinding,
    SpecificationSelectionError,
    SpecificationSourceSelection,
    admit_specification_selection,
    consume_specification_selection,
    release_specification_selection,
    require_specification_selection,
)
from aware_protocol_fs_adapter import specification_selection as implementation
from aware_protocol_runtime import ProtocolAdmissionOutcomeKind

TARGET = "customer/specs/widget/aware.spec.toml"


def source(*, role="authority", template="<spec-key>/aware.spec.toml"):
    binding = (
        f'root = "customer/specs"\npath_template = "{template}"\n'
        if role != "unavailable"
        else ""
    )
    return f'''aware = 1
[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v1"
semantic_version = 1
[target]
kind = "repository"
authority_mode = "filesystem"
[bootstrap]
agent_contract = "AGENTS.md"
[records.goal]
profile = "aware.goal.markdown.v1"
role = "unavailable"
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
role = "{role}"
{binding}[records.evidence]
profile = "aware.protocol.evidence.v1"
role = "unavailable"
'''


def issue(root: Path, *, paths=(TARGET,), body=None, manifest=None):
    manifest = manifest or root / "aware.protocol.toml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(source() if body is None else body)
    result = admit_specification_selection(
        repository_root=root,
        manifest_path=manifest,
        selected_manifest_paths=paths,
    )
    assert result.admission.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1
    assert result.selection is not None
    return result.selection


class Consumer:
    """Lifecycle probe only, never domain parsing/refusal logic."""

    def __init__(self, fd, roots, guard):
        self.fd = os.dup(fd)
        self.borrowed = fd
        self.roots = roots
        self.guard = guard
        self.closed = False
        self.admissions = []

    def close(self):
        if not self.closed:
            self.closed = True
            os.close(self.fd)
            self.admissions.clear()


def fd_count():
    return len(tuple(Path("/proc/self/fd").iterdir()))


def test_fresh_selection_never_reads_or_parses_spec_content(tmp_path, monkeypatch):
    target = tmp_path / TARGET
    target.parent.mkdir(parents=True)
    target.write_text("not a canonical SPEC; Protocol must not parse me")
    read_bytes = Path.read_bytes

    def bounded_read(path):
        if path.name == "aware.spec.toml":
            pytest.fail("Protocol read SPEC source bytes")
        return read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", bounded_read)
    selection = issue(tmp_path)
    try:
        assert require_specification_selection(selection) is selection
        assert selection.repository_root == tmp_path
        assert selection.selected_manifest_paths == (TARGET,)
        assert selection.manifest_sha256.startswith("sha256:")
    finally:
        release_specification_selection(selection)


def test_missing_record_directories_do_not_invent_source_availability(tmp_path):
    selection = issue(tmp_path)
    try:
        assert not (tmp_path / TARGET).exists()
        consumer = consume_specification_selection(selection, Consumer)
        try:
            assert consumer.roots == ("customer/specs/widget",)
            assert os.fstat(consumer.fd).st_ino == tmp_path.stat().st_ino
            with pytest.raises(OSError):
                os.fstat(consumer.borrowed)
        finally:
            consumer.close()
    finally:
        release_specification_selection(selection)


def test_roots_are_explicit_ordered_not_dependency_discovery(tmp_path):
    paths = (
        "customer/specs/alpha/aware.spec.toml",
        "customer/specs/beta/aware.spec.toml",
    )
    selection = issue(tmp_path, paths=paths)
    try:
        consumer = consume_specification_selection(selection, Consumer)
        try:
            assert consumer.roots == ("customer/specs/alpha", "customer/specs/beta")
        finally:
            consumer.close()
    finally:
        release_specification_selection(selection)


@pytest.mark.parametrize(
    "paths",
    [
        [],
        (),
        (TARGET, TARGET),
        (TARGET, "customer/specs/alpha/aware.spec.toml"),
        ("../" + TARGET,),
        ("/" + TARGET,),
        ("customer//specs/a/aware.spec.toml",),
        ("customer/specs/./a/aware.spec.toml",),
        ("customer\\specs/a/aware.spec.toml",),
        ("customer/specs/\u0085/aware.spec.toml",),
        ("customer/specs/e\u0301/aware.spec.toml",),
        (None,),
        ("customer/specs/\ud800/aware.spec.toml",),
        tuple(f"customer/specs/{n:03}/aware.spec.toml" for n in range(65)),
    ],
)
def test_invalid_selection_locators_refuse_before_manifest_read(tmp_path, paths):
    with pytest.raises(SpecificationSelectionError, match="selection_paths_invalid"):
        admit_specification_selection(
            repository_root=tmp_path,
            manifest_path=tmp_path / "aware.protocol.toml",
            selected_manifest_paths=paths,
        )


@pytest.mark.parametrize(
    "path",
    [
        "foreign/widget/aware.spec.toml",
        "customer/specs/widget/SPEC.md",
        "customer/specs/group/widget/aware.spec.toml",
        "customer/specs/aware.spec.toml",
    ],
)
def test_targets_must_match_exact_admitted_template(tmp_path, path):
    with pytest.raises(SpecificationSelectionError, match="target_outside_binding"):
        issue(tmp_path, paths=(path,))


@pytest.mark.parametrize("role", ["unavailable", "projection", "bootstrap"])
def test_available_profile_is_not_authority(tmp_path, role):
    with pytest.raises(SpecificationSelectionError, match="authority_required"):
        issue(tmp_path, body=source(role=role))


def test_profile_envelope_does_not_admit_other_collaboration_profiles(tmp_path):
    body = (
        source()
        .replace("aware.collaboration.fs_v1", "aware.collaboration.fs_v2")
        .replace("semantic_version = 1", "semantic_version = 2")
    )
    body = body.replace(
        'profile = "aware.goal.markdown.v1"\nrole = "unavailable"',
        'profile = "aware.goal.phase.markdown.v1"\nrole = "authority"\n'
        'root = "objectives"\npath_template = "goal-YYYY-MM-DD-<slug>.md"',
    )
    with pytest.raises(SpecificationSelectionError, match="profile_unsupported"):
        issue(tmp_path, body=body)


@pytest.mark.parametrize(
    "body",
    [
        "not toml",
        source().replace("specification_fs_v1", "unknown_spec_v7"),
        source().replace(
            'authority_mode = "filesystem"',
            'authority_mode = "service_api"\nauthority_ref = "service:test"',
        ),
    ],
)
def test_failed_admission_never_issues_selection(tmp_path, body):
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(body)
    result = admit_specification_selection(
        repository_root=tmp_path,
        manifest_path=manifest,
        selected_manifest_paths=(TARGET,),
    )
    assert result.selection is None
    assert result.admission.outcome is not ProtocolAdmissionOutcomeKind.CANONICAL_V1


def test_unsupported_template_refuses(tmp_path):
    with pytest.raises(SpecificationSelectionError, match="binding_unsupported"):
        issue(tmp_path, body=source(template="<spec-key>/SPEC.md"))


@pytest.mark.parametrize(
    "value",
    [
        None,
        {},
        TARGET,
        FilesystemRecordBinding(
            "specification", "customer/specs", "<spec-key>/aware.spec.toml"
        ),
    ],
)
def test_caller_values_cannot_substitute_for_issuance(value):
    with pytest.raises(SpecificationSelectionError, match="selection_invalid"):
        require_specification_selection(value)


def test_nominal_forgery_and_public_construction_refuse():
    with pytest.raises(TypeError, match="use admit"):
        SpecificationSourceSelection()
    forged = object.__new__(SpecificationSourceSelection)
    with pytest.raises(SpecificationSelectionError, match="invalid_or_released"):
        require_specification_selection(forged)
    with pytest.raises(TypeError, match="cannot be subclassed"):
        type("Forged", (SpecificationSourceSelection,), {})


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_capability_cannot_be_copied_or_serialized(tmp_path, operation):
    selection = issue(tmp_path)
    try:
        with pytest.raises(TypeError, match="cannot be copied or serialized"):
            operation(selection)
    finally:
        release_specification_selection(selection)


def test_expected_manifest_bytes_not_semantic_digest(tmp_path):
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source())
    before = fd_count()
    with pytest.raises(SpecificationSelectionError, match="manifest_changed"):
        admit_specification_selection(
            repository_root=tmp_path,
            manifest_path=manifest,
            selected_manifest_paths=(TARGET,),
            expected_manifest_sha256="sha256:" + "0" * 64,
        )
    assert fd_count() == before


@pytest.mark.parametrize("edit", ["\n", "\n# same semantics\n"])
def test_any_manifest_byte_drift_refuses(tmp_path, edit):
    selection = issue(tmp_path)
    try:
        with (tmp_path / "aware.protocol.toml").open("a") as stream:
            stream.write(edit)
        with pytest.raises(SpecificationSelectionError, match="manifest_changed"):
            require_specification_selection(selection)
    finally:
        release_specification_selection(selection)


def test_same_bytes_replacement_manifest_is_not_retained_source(tmp_path):
    selection = issue(tmp_path)
    try:
        replacement = tmp_path / "replacement"
        replacement.write_text(source())
        replacement.replace(tmp_path / "aware.protocol.toml")
        with pytest.raises(SpecificationSelectionError, match="manifest_changed"):
            require_specification_selection(selection)
    finally:
        release_specification_selection(selection)


def test_same_file_in_replaced_manifest_parent_refuses(tmp_path):
    manifest = tmp_path / "config/aware.protocol.toml"
    selection = issue(tmp_path, manifest=manifest)
    try:
        old = tmp_path / "old-config"
        manifest.parent.rename(old)
        manifest.parent.mkdir()
        os.link(old / manifest.name, manifest)
        with pytest.raises(SpecificationSelectionError, match="topology_changed"):
            require_specification_selection(selection)
    finally:
        release_specification_selection(selection)


def test_repository_replacement_refuses(tmp_path):
    root = tmp_path / "repository"
    root.mkdir()
    selection = issue(root)
    try:
        root.rename(tmp_path / "old")
        root.mkdir()
        (root / "aware.protocol.toml").write_text(source())
        with pytest.raises(SpecificationSelectionError, match="repository_changed"):
            require_specification_selection(selection)
    finally:
        release_specification_selection(selection)


def test_existing_selected_directory_replacement_refuses(tmp_path):
    package = tmp_path / "customer/specs/widget"
    package.mkdir(parents=True)
    selection = issue(tmp_path)
    try:
        package.rename(package.with_name("old"))
        package.mkdir()
        with pytest.raises(SpecificationSelectionError, match="topology_changed"):
            require_specification_selection(selection)
    finally:
        release_specification_selection(selection)


def test_newly_observed_missing_tail_identity_is_retained(tmp_path):
    selection = issue(tmp_path)
    package = tmp_path / "customer/specs/widget"
    package.mkdir(parents=True)
    try:
        require_specification_selection(selection)
        package.rename(package.with_name("old"))
        package.mkdir()
        with pytest.raises(SpecificationSelectionError, match="topology_changed"):
            require_specification_selection(selection)
    finally:
        release_specification_selection(selection)


@pytest.mark.parametrize(
    "kind", ["fifo", "directory", "symlink", "wrong_name", "outside"]
)
def test_manifest_pre_read_type_and_location_refusals(tmp_path, kind):
    manifest = tmp_path / "aware.protocol.toml"
    if kind == "fifo":
        os.mkfifo(manifest)
    elif kind == "directory":
        manifest.mkdir()
    elif kind == "symlink":
        target = tmp_path / "source"
        target.write_text(source())
        manifest.symlink_to(target)
    elif kind == "wrong_name":
        manifest = tmp_path / "wrong.toml"
        manifest.write_text(source())
    else:
        manifest = tmp_path.parent / (tmp_path.name + "-outside.toml")
        manifest.write_text(source())
    before = fd_count()
    with pytest.raises(
        SpecificationSelectionError, match="manifest_(unresolvable|outside_repository)"
    ):
        admit_specification_selection(
            repository_root=tmp_path,
            manifest_path=manifest,
            selected_manifest_paths=(TARGET,),
        )
    assert fd_count() == before


def test_manifest_size_is_bounded_before_lowering(tmp_path):
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source() + "#" + "x" * 1_048_576)
    before = fd_count()
    with pytest.raises(SpecificationSelectionError, match="manifest_too_large"):
        admit_specification_selection(
            repository_root=tmp_path,
            manifest_path=manifest,
            selected_manifest_paths=(TARGET,),
        )
    assert fd_count() == before


@pytest.mark.parametrize(
    "kind", ["contained", "outside", "broken", "loop", "file", "manifest_link"]
)
def test_selected_source_topology_refuses_before_consumption(tmp_path, kind):
    package = tmp_path / "customer/specs/widget"
    package.parent.mkdir(parents=True)
    if kind == "contained":
        target = tmp_path / "other"
        target.mkdir()
        package.symlink_to(target, target_is_directory=True)
    elif kind == "outside":
        package.symlink_to(tmp_path.parent, target_is_directory=True)
    elif kind == "broken":
        package.symlink_to(tmp_path / "missing", target_is_directory=True)
    elif kind == "loop":
        package.symlink_to(package, target_is_directory=True)
    elif kind == "file":
        package.write_text("file")
    else:
        package.mkdir()
        (package / "aware.spec.toml").symlink_to(tmp_path / "missing")
    before = fd_count()
    with pytest.raises(SpecificationSelectionError, match="path_unresolvable"):
        issue(tmp_path)
    assert fd_count() == before


def test_released_selection_cannot_be_reused_or_double_released(tmp_path):
    selection = issue(tmp_path)
    release_specification_selection(selection)
    for operation in (require_specification_selection, release_specification_selection):
        with pytest.raises(SpecificationSelectionError, match="invalid_or_released"):
            operation(selection)


def test_gc_releases_issuer_descriptor(tmp_path):
    before = fd_count()
    selection = issue(tmp_path)
    assert fd_count() == before + 1
    del selection
    gc.collect()
    assert fd_count() == before


def test_fresh_duplicate_lifetime_shared_selection_is_independent(tmp_path):
    before = fd_count()
    selection = issue(tmp_path)
    first = consume_specification_selection(selection, Consumer)
    second = consume_specification_selection(selection, Consumer)
    try:
        assert fd_count() == before + 3
        first.close()
        assert require_specification_selection(selection) is selection
        second.guard()
        assert os.fstat(second.fd).st_ino == tmp_path.stat().st_ino
        release_specification_selection(selection)
        with pytest.raises(SpecificationSelectionError, match="invalid_or_released"):
            second.guard()
    finally:
        first.close()
        second.close()
    assert fd_count() == before


def test_post_construction_failure_closes_new_consumer_and_retires_admissions(tmp_path):
    selection = issue(tmp_path)
    baseline = fd_count()
    consumers = []

    def factory(fd, roots, guard):
        consumer = Consumer(fd, roots, guard)
        consumer.admissions.append("new provider-owned admission probe")
        consumers.append(consumer)
        with (tmp_path / "aware.protocol.toml").open("a") as stream:
            stream.write("\n# race\n")
        return consumer

    try:
        with pytest.raises(SpecificationSelectionError, match="manifest_changed"):
            consume_specification_selection(selection, factory)
        assert consumers[0].closed
        assert consumers[0].admissions == []
        assert fd_count() == baseline
    finally:
        release_specification_selection(selection)


def test_factory_exception_closes_only_borrowed_duplicate(tmp_path):
    selection = issue(tmp_path)
    baseline = fd_count()

    def factory(fd, roots, guard):
        raise ValueError("factory failed before returning a consumer")

    try:
        with pytest.raises(ValueError, match="factory failed"):
            consume_specification_selection(selection, factory)
        assert fd_count() == baseline
        assert require_specification_selection(selection) is selection
    finally:
        release_specification_selection(selection)


def test_cleanup_error_does_not_replace_original_refusal(tmp_path):
    selection = issue(tmp_path)
    baseline = fd_count()

    class FailingClose(Consumer):
        def close(self):
            super().close()
            raise ValueError("cleanup failed")

    def factory(fd, roots, guard):
        consumer = FailingClose(fd, roots, guard)
        (tmp_path / "aware.protocol.toml").write_text(source() + "\n")
        return consumer

    try:
        with pytest.raises(
            SpecificationSelectionError, match="manifest_changed"
        ) as refusal:
            consume_specification_selection(selection, factory)
        assert "selection_consumer_cleanup_failed:ValueError" in refusal.value.__notes__
        assert fd_count() == baseline
    finally:
        release_specification_selection(selection)


def test_failed_final_issuance_validation_closes_issuer_descriptor(
    tmp_path, monkeypatch
):
    before = fd_count()

    def refuse(self):
        raise SpecificationSelectionError("injected_final_validation_refusal")

    monkeypatch.setattr(SpecificationSourceSelection, "revalidate", refuse)
    with pytest.raises(SpecificationSelectionError, match="injected_final"):
        issue(tmp_path)
    assert fd_count() == before


def test_namespace_substitution_refuses(tmp_path, monkeypatch):
    selection = issue(tmp_path)
    try:
        monkeypatch.setattr(
            implementation, "_namespace", lambda: (0, 0, b"substituted")
        )
        with pytest.raises(SpecificationSelectionError, match="topology_changed"):
            require_specification_selection(selection)
    finally:
        release_specification_selection(selection)


def test_prefix_permission_failure_is_typed_and_closes_descriptors(
    tmp_path, monkeypatch
):
    (tmp_path / "customer").mkdir()
    selection = issue(tmp_path)
    baseline = fd_count()
    open_file = os.open

    def refuse(path, *args, **kwargs):
        if path == "customer":
            raise PermissionError("simulated prefix denial")
        return open_file(path, *args, **kwargs)

    try:
        monkeypatch.setattr(os, "open", refuse)
        with pytest.raises(SpecificationSelectionError, match="source_unavailable"):
            require_specification_selection(selection)
        assert fd_count() == baseline
    finally:
        release_specification_selection(selection)


def test_fork_requires_fresh_issuance(tmp_path):
    selection = issue(tmp_path)
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        try:
            require_specification_selection(selection)
        except SpecificationSelectionError as error:
            os.write(write_fd, error.code.encode())
        else:
            os.write(write_fd, b"unexpected_success")
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    try:
        assert os.read(read_fd, 256) == b"specification_selection_foreign_process"
        os.waitpid(child, 0)
        assert require_specification_selection(selection) is selection
    finally:
        os.close(read_fd)
        release_specification_selection(selection)


def test_selection_module_has_no_spec_parser_sdk_or_service_import():
    tree = ast.parse(Path(implementation.__file__).read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            imports.extend(item.name for item in node.names)
    assert not any(
        name.startswith(
            (
                "aware_specification",
                "aware_workflow",
                "aware_service",
                "aware_experience",
            )
        )
        for name in imports
    )
