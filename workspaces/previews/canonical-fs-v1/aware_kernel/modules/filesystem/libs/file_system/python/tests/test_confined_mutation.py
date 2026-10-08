from __future__ import annotations

import ast
import hashlib
import os
import stat
from pathlib import Path

import pytest
import aware_file_system.confined_mutation as physical
from aware_file_system.confined_mutation import (
    ConfinedFileObservation,
    ConfinedFileMutationRequest,
    ConfinedMutationKind,
    ConfinedMutationOutcome,
    ConfinedObservationOutcome,
    ConfinedTextReplacement,
    mutate_confined_file,
    observe_confined_file,
)


def _digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


@pytest.mark.parametrize("mode", [0o600, 0o640, 0o664, 0o755])
def test_update_preserves_mode_under_restrictive_umask(tmp_path, mode):
    target = tmp_path / "manifest"
    target.write_bytes(b"before")
    target.chmod(mode)
    original_umask = os.umask(0o077)
    try:
        result = mutate_confined_file(root=tmp_path, request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.UPDATE, path="manifest", expected_exists=True,
            expected_content_digest=_digest(b"before"), content=b"after",
        ))
    finally:
        os.umask(original_umask)
    assert result.outcome is ConfinedMutationOutcome.APPLIED
    assert result.effect_applied and result.durability_confirmed
    assert stat.S_IMODE(target.stat().st_mode) == mode


@pytest.mark.parametrize("kind", list(ConfinedMutationKind))
@pytest.mark.parametrize("error_type", [OSError, PermissionError])
def test_failure_after_application_preserves_known_effect(tmp_path, monkeypatch, kind, error_type):
    target = tmp_path / "manifest"
    before = None if kind is ConfinedMutationKind.CREATE else b"before"
    if before is not None:
        target.write_bytes(before)
    original_fsync = os.fsync

    def fail_directory_fsync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise error_type("injected directory durability failure")
        return original_fsync(fd)

    monkeypatch.setattr(os, "fsync", fail_directory_fsync)
    result = mutate_confined_file(root=tmp_path, request=ConfinedFileMutationRequest(
        kind=kind, path="manifest", expected_exists=before is not None,
        expected_content_digest=None if before is None else _digest(before),
        content=None if kind is ConfinedMutationKind.DELETE else b"after",
    ))
    assert result.outcome is ConfinedMutationOutcome.FAILED
    assert result.effect_applied and not result.durability_confirmed
    assert result.before_content == before
    assert result.before_exists is (before is not None)
    if kind is ConfinedMutationKind.DELETE:
        assert not target.exists() and not result.after_exists
    else:
        assert target.read_bytes() == result.after_content == b"after"
        assert result.after_content_digest == _digest(b"after")
    assert sorted(p.name for p in tmp_path.iterdir()) == ([] if kind is ConfinedMutationKind.DELETE else ["manifest"])


def test_create_cleanup_failure_does_not_erase_successful_link(tmp_path, monkeypatch):
    original_unlink = os.unlink

    def fail_scratch_unlink(path, **kwargs):
        if str(path).startswith(".aware-cas-"):
            raise OSError("injected scratch cleanup failure")
        return original_unlink(path, **kwargs)

    monkeypatch.setattr(os, "unlink", fail_scratch_unlink)
    result = mutate_confined_file(root=tmp_path, request=ConfinedFileMutationRequest(
        kind=ConfinedMutationKind.CREATE, path="manifest", expected_exists=False,
        expected_content_digest=None, content=b"after",
    ))
    assert result.outcome is ConfinedMutationOutcome.FAILED
    assert result.error_code == "filesystem_cleanup_failed"
    assert result.effect_applied and not result.durability_confirmed
    assert (tmp_path / "manifest").read_bytes() == result.after_content == b"after"
    assert len(list(tmp_path.glob(".aware-cas-*"))) == 1


def test_uncertain_replacement_is_not_reported_as_no_effect(tmp_path, monkeypatch):
    target = tmp_path / "manifest"
    target.write_bytes(b"before")
    original_replace = os.replace

    def replace_then_fail(*args, **kwargs):
        original_replace(*args, **kwargs)
        raise OSError("effect result unavailable")

    monkeypatch.setattr(os, "replace", replace_then_fail)
    result = mutate_confined_file(root=tmp_path, request=ConfinedFileMutationRequest(
        kind=ConfinedMutationKind.UPDATE, path="manifest", expected_exists=True,
        expected_content_digest=_digest(b"before"), content=b"after",
    ))
    assert result.outcome is ConfinedMutationOutcome.FAILED
    assert result.effect_state is physical.ConfinedMutationEffectState.UNKNOWN
    assert not result.effect_applied and not result.durability_confirmed
    assert result.before_content == b"before"
    assert target.read_bytes() == b"after"


def test_create_update_delete_are_exact_and_preserve_bodies(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    created = mutate_confined_file(
        root=tmp_path,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.CREATE,
            path="src/app.py",
            expected_exists=False,
            expected_content_digest=None,
            content=b"print('one')\n",
        ),
    )
    assert created.outcome is ConfinedMutationOutcome.APPLIED
    assert created.before_content is None
    assert created.after_content == b"print('one')\n"
    assert created.after_content_digest == _digest(created.after_content)

    updated = mutate_confined_file(
        root=tmp_path,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.UPDATE,
            path="src/app.py",
            expected_exists=True,
            expected_content_digest=created.after_content_digest,
            content=b"print('two')\n",
        ),
    )
    assert updated.outcome is ConfinedMutationOutcome.APPLIED
    assert updated.before_content == created.after_content
    assert updated.after_content == b"print('two')\n"

    deleted = mutate_confined_file(
        root=tmp_path,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.DELETE,
            path="src/app.py",
            expected_exists=True,
            expected_content_digest=updated.after_content_digest,
        ),
    )
    assert deleted.outcome is ConfinedMutationOutcome.APPLIED
    assert deleted.before_content == updated.after_content
    assert deleted.after_exists is False
    assert not (tmp_path / "src/app.py").exists()


def test_nested_create_securely_creates_missing_parents_and_observes_exactly(
    tmp_path: Path,
) -> None:
    before = observe_confined_file(root=tmp_path, path="generated/sdk/client.py")
    assert before == ConfinedFileObservation(
        "generated/sdk/client.py", ConfinedObservationOutcome.OBSERVED, False
    )

    created = mutate_confined_file(
        root=tmp_path,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.CREATE,
            path="generated/sdk/client.py",
            expected_exists=False,
            expected_content_digest=None,
            content=b"class Client:\n    pass\n",
        ),
    )
    assert created.outcome is ConfinedMutationOutcome.APPLIED

    after = observe_confined_file(root=tmp_path, path="generated/sdk/client.py")
    assert after.outcome is ConfinedObservationOutcome.OBSERVED
    assert after.exists
    assert after.content == b"class Client:\n    pass\n"
    assert after.content_digest == _digest(after.content)
    assert after.size_bytes == len(after.content)


def test_baseline_conflicts_do_not_mutate(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_bytes(b"current")

    stale = mutate_confined_file(
        root=tmp_path,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.UPDATE,
            path="source.txt",
            expected_exists=True,
            expected_content_digest=_digest(b"stale"),
            content=b"replacement",
        ),
    )
    assert stale.outcome is ConfinedMutationOutcome.CONFLICT
    assert stale.error_code == "expected_content_digest_mismatch"
    assert source.read_bytes() == b"current"

    exists = mutate_confined_file(
        root=tmp_path,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.CREATE,
            path="source.txt",
            expected_exists=False,
            expected_content_digest=None,
            content=b"replacement",
        ),
    )
    assert exists.outcome is ConfinedMutationOutcome.CONFLICT
    assert source.read_bytes() == b"current"


def test_ordered_text_replacements_use_the_exact_cas_preimage(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    before = b"value = 'one'\nprint(value)\n"
    source.write_bytes(before)

    result = mutate_confined_file(
        root=tmp_path,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.UPDATE,
            path="source.py",
            expected_exists=True,
            expected_content_digest=_digest(before),
            text_replacements=(
                ConfinedTextReplacement("'one'", "'two'"),
                ConfinedTextReplacement("print(value)", "print(value.upper())"),
            ),
        ),
    )

    assert result.outcome is ConfinedMutationOutcome.APPLIED
    assert result.before_content == before
    assert result.after_content == b"value = 'two'\nprint(value.upper())\n"
    assert source.read_bytes() == result.after_content


@pytest.mark.parametrize(
    ("before", "replacement", "error_code"),
    (
        (
            b"same same",
            ConfinedTextReplacement("same", "new"),
            "text_replacement_not_unique",
        ),
        (
            b"present",
            ConfinedTextReplacement("missing", "new"),
            "text_replacement_not_unique",
        ),
        (
            b"\xffbinary",
            ConfinedTextReplacement("binary", "text"),
            "text_replacement_source_not_utf8",
        ),
    ),
)
def test_text_replacement_failures_preserve_source(
    tmp_path: Path,
    before: bytes,
    replacement: ConfinedTextReplacement,
    error_code: str,
) -> None:
    source = tmp_path / "source.txt"
    source.write_bytes(before)
    result = mutate_confined_file(
        root=tmp_path,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.UPDATE,
            path="source.txt",
            expected_exists=True,
            expected_content_digest=_digest(before),
            text_replacements=(replacement,),
        ),
    )
    assert result.outcome is ConfinedMutationOutcome.CONFLICT
    assert result.error_code == error_code
    assert source.read_bytes() == before


def test_text_replacement_result_byte_bound_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    before = b"x"
    source.write_bytes(before)
    result = mutate_confined_file(
        root=tmp_path,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.UPDATE,
            path="source.txt",
            expected_exists=True,
            expected_content_digest=_digest(before),
            text_replacements=(ConfinedTextReplacement("x", "oversize"),),
            maximum_bytes=4,
        ),
    )
    assert result.outcome is ConfinedMutationOutcome.CONFLICT
    assert result.error_code == "text_replacement_exceeds_byte_bound"
    assert source.read_bytes() == before


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink unavailable")
def test_symlinked_parent_and_leaf_are_denied(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (outside / "secret.txt").write_bytes(b"secret")
    (tmp_path / "link").symlink_to(outside, target_is_directory=True)
    parent = mutate_confined_file(
        root=tmp_path,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.UPDATE,
            path="link/secret.txt",
            expected_exists=True,
            expected_content_digest=_digest(b"secret"),
            content=b"leaked",
        ),
    )
    assert parent.outcome is ConfinedMutationOutcome.DENIED
    observed_parent = observe_confined_file(root=tmp_path, path="link/secret.txt")
    assert observed_parent.outcome is ConfinedObservationOutcome.DENIED
    assert (outside / "secret.txt").read_bytes() == b"secret"

    (tmp_path / "leaf.txt").symlink_to(outside / "secret.txt")
    leaf = mutate_confined_file(
        root=tmp_path,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.DELETE,
            path="leaf.txt",
            expected_exists=True,
            expected_content_digest=_digest(b"secret"),
        ),
    )
    assert leaf.outcome is ConfinedMutationOutcome.DENIED
    observed_leaf = observe_confined_file(root=tmp_path, path="leaf.txt")
    assert observed_leaf.outcome is ConfinedObservationOutcome.DENIED
    assert (outside / "secret.txt").exists()


@pytest.mark.parametrize("path", ("../escape", "/absolute", "a/../b", "a\\b"))
def test_unconfined_paths_are_rejected(path: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="path"):
        mutate_confined_file(
            root=tmp_path,
            request=ConfinedFileMutationRequest(
                kind=ConfinedMutationKind.CREATE,
                path=path,
                expected_exists=False,
                expected_content_digest=None,
                content=b"content",
            ),
        )


def test_oversized_existing_body_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "large.bin").write_bytes(b"12345")
    result = mutate_confined_file(
        root=tmp_path,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.UPDATE,
            path="large.bin",
            expected_exists=True,
            expected_content_digest=_digest(b"12345"),
            content=b"new",
            maximum_bytes=4,
        ),
    )
    assert result.outcome is ConfinedMutationOutcome.DENIED
    assert result.error_code == "target_changed_or_exceeds_byte_bound"
    assert (tmp_path / "large.bin").read_bytes() == b"12345"


def test_confined_mutation_primitive_is_stdlib_only() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "aware_file_system"
        / "confined_mutation.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    absolute_roots = {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 0
    }
    absolute_roots.update(
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert absolute_roots <= {
        "__future__",
        "dataclasses",
        "enum",
        "hashlib",
        "os",
        "pathlib",
        "stat",
        "uuid",
    }


def test_legacy_descriptor_profile_does_not_claim_continuous_confinement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Characterize the existing profile, not a safe-installation proof. All
    # paths, including the external sibling, are inside this disposable fixture.
    repository = tmp_path / "repository"
    parent = repository / "goals"
    parent.mkdir(parents=True)
    target = parent / "goal.md"
    target.write_bytes(b"before")
    outside = tmp_path / "external-directory"
    read_current = physical._read_current

    def read_then_relocate(**kwargs):
        result = read_current(**kwargs)
        parent.rename(outside)
        return result

    monkeypatch.setattr(physical, "_read_current", read_then_relocate)
    result = mutate_confined_file(
        root=repository,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.UPDATE, path="goals/goal.md",
            expected_exists=True, expected_content_digest=_digest(b"before"),
            content=b"after",
        ),
    )
    assert result.outcome is ConfinedMutationOutcome.APPLIED
    assert (outside / "goal.md").read_bytes() == b"after"
    assert result.confinement_profile is physical.ConfinedMutationProfile.DESCRIPTOR_WALK_V1


@pytest.mark.parametrize("kind", tuple(ConfinedMutationKind))
def test_continuous_confinement_refuses_before_traversal_or_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: ConfinedMutationKind,
) -> None:
    before = b"before"
    target = tmp_path / "goal.md"
    if kind is not ConfinedMutationKind.CREATE:
        target.write_bytes(before)
    calls = []

    def forbidden_traversal(**kwargs):
        calls.append(kwargs)
        raise AssertionError("unsupported confinement must not reach filesystem traversal")

    monkeypatch.setattr(physical, "_open_parent", forbidden_traversal)
    request = ConfinedFileMutationRequest(
        kind=kind, path="goal.md", expected_exists=kind is not ConfinedMutationKind.CREATE,
        expected_content_digest=None if kind is ConfinedMutationKind.CREATE else _digest(before),
        content=None if kind is ConfinedMutationKind.DELETE else b"after",
    )
    result = mutate_confined_file(root=tmp_path, request=request,
        confinement_profile=physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1)
    assert result.outcome is ConfinedMutationOutcome.DENIED
    assert result.error_code == "continuous_root_confinement_unavailable"
    assert result.confinement_profile is physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1
    assert result.before_content is result.after_content is None
    assert calls == []
    assert target.exists() == (kind is not ConfinedMutationKind.CREATE)
    if target.exists():
        assert target.read_bytes() == before
    assert not list(tmp_path.glob(".aware-cas-*"))


@pytest.mark.parametrize("invalid", ["continuous_root_v1", "unknown", True, None])
def test_unqualified_profile_tokens_do_not_reach_the_filesystem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, invalid,
) -> None:
    def forbidden_traversal(**kwargs):
        raise AssertionError("invalid profile reached filesystem traversal")

    monkeypatch.setattr(physical, "_open_parent", forbidden_traversal)
    request = ConfinedFileMutationRequest(
        kind=ConfinedMutationKind.CREATE, path="missing/goal.md",
        expected_exists=False, expected_content_digest=None, content=b"after",
    )
    with pytest.raises(TypeError, match="profile must be exact"):
        mutate_confined_file(root=tmp_path, request=request, confinement_profile=invalid)
    assert not (tmp_path / "missing").exists()


def test_unavailable_profile_does_not_resolve_or_create_a_root(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing-root"
    request = ConfinedFileMutationRequest(
        kind=ConfinedMutationKind.CREATE, path="missing/goal.md",
        expected_exists=False, expected_content_digest=None, content=b"after",
    )
    result = mutate_confined_file(root=missing_root, request=request,
        confinement_profile=physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1)
    assert result.outcome is ConfinedMutationOutcome.DENIED
    assert result.error_code == "continuous_root_confinement_unavailable"
    assert not missing_root.exists()


@pytest.mark.parametrize("stage", ["_open_parent", "_read_current", "_write_temporary"])
def test_continuous_profile_never_reaches_a_relocation_interleaving(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str,
) -> None:
    repository = tmp_path / "repository"
    parent = repository / "goals"
    parent.mkdir(parents=True)
    target = parent / "goal.md"
    target.write_bytes(b"before")
    outside = tmp_path / "external-directory"
    original = getattr(physical, stage)
    reached = []

    def relocate_then_call(**kwargs):
        reached.append(stage)
        parent.rename(outside)
        return original(**kwargs)

    monkeypatch.setattr(physical, stage, relocate_then_call)
    result = mutate_confined_file(root=repository,
        request=ConfinedFileMutationRequest(
            kind=ConfinedMutationKind.UPDATE, path="goals/goal.md",
            expected_exists=True, expected_content_digest=_digest(b"before"), content=b"after",
        ), confinement_profile=physical.ConfinedMutationProfile.CONTINUOUS_ROOT_V1)
    assert result.outcome is ConfinedMutationOutcome.DENIED
    assert reached == [] and not outside.exists()
    assert target.read_bytes() == b"before"
    assert sorted(child.name for child in parent.iterdir()) == ["goal.md"]
