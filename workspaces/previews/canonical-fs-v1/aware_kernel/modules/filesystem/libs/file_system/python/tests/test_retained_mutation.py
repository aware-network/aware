from __future__ import annotations

import copy
import errno
import hashlib
import os
import pickle
import stat
from types import SimpleNamespace

import aware_file_system.retained_mutation as owner
import pytest
from aware_file_system.confined_mutation import ConfinedMutationEffectState as Effect
from aware_file_system.confined_mutation import ConfinedMutationProfile


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def retain(root, directories=(), candidate=b"after"):
    return owner.retain_confined_manifest_replacement(
        root=root,
        target_path="manifest.toml",
        expected_content_digest=digest(b"before"),
        content=candidate,
        directory_paths=directories,
    )


@pytest.fixture
def root(tmp_path):
    (tmp_path / "manifest.toml").write_bytes(b"before")
    return tmp_path


def test_explicit_directories_then_exact_replacement_and_single_consumption(root):
    (root / "existing").mkdir(mode=0o755)
    manifest = root / "manifest.toml"
    manifest.chmod(0o664)
    handle = retain(root, ("existing", "private", "private/specs"))
    assert handle.phase == "issued" and handle.effects == ()
    first = handle.prepare_next_directory()
    assert first.state is Effect.NONE
    second = handle.prepare_next_directory()
    third = handle.prepare_next_directory()
    assert second.state is third.state is Effect.APPLIED
    assert second.durability_confirmed and third.durability_confirmed
    original_mask = os.umask(0o077)
    try:
        replacement = handle.replace_manifest()
    finally:
        os.umask(original_mask)
    assert replacement.state is Effect.APPLIED
    assert replacement.before_digest == digest(b"before")
    assert replacement.after_digest == digest(b"after")
    assert replacement.after_identity == (
        manifest.stat().st_dev,
        manifest.stat().st_ino,
    )
    assert stat.S_IMODE(manifest.stat().st_mode) == 0o664
    assert stat.S_IMODE((root / "private").stat().st_mode) == 0o700
    assert stat.S_IMODE((root / "existing").stat().st_mode) == 0o755
    assert len(handle.finish()) == 4
    assert handle.phase == "consumed"
    with pytest.raises(owner.RetainedPhysicalMutationRefusal, match="terminal"):
        handle.replace_manifest()


def test_consumed_identity_revalidation_cannot_restore_effect_authority(root):
    handle = retain(root)
    handle.replace_manifest()
    original = handle.finish()
    handle.validate_consumed_current()
    handle.validate_consumed_current()
    assert handle.phase == "consumed" and handle.effects == original
    assert owner._issued(handle).root_fd is None
    with pytest.raises(owner.RetainedPhysicalMutationRefusal, match="terminal"):
        handle.replace_manifest()


def test_consumed_equal_byte_substitution_retires_with_existing_effects(root):
    handle = retain(root)
    handle.replace_manifest()
    original = handle.finish()
    substitute = root / "substitute"
    substitute.write_bytes(b"after")
    substitute.replace(root / "manifest.toml")
    with pytest.raises(owner.RetainedPhysicalMutationRefusal) as failure:
        handle.validate_consumed_current()
    assert handle.phase == "retired" and failure.value.effects == original
    assert owner._issued(handle).root_fd is None


def test_interrupted_consumed_revalidation_closes_all_read_descriptors(
    root, monkeypatch
):
    handle = retain(root)
    handle.replace_manifest()
    original = handle.finish()
    real_open = os.open
    opened = []

    def record_open(*args, **kwargs):
        descriptor = real_open(*args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def interrupt(*args):
        raise KeyboardInterrupt()

    monkeypatch.setattr(os, "open", record_open)
    monkeypatch.setattr(owner, "_verify", interrupt)
    with pytest.raises(owner.RetainedPhysicalMutationRefusal):
        handle.validate_consumed_current()
    assert handle.phase == "retired" and handle.effects == original
    assert opened and owner._issued(handle).root_fd is None
    for descriptor in opened:
        with pytest.raises(OSError):
            os.fstat(descriptor)


def test_active_handle_cannot_use_consumed_read_entrance(root):
    handle = retain(root)
    with pytest.raises(
        owner.RetainedPhysicalMutationRefusal, match="consumed_identity_required"
    ):
        handle.validate_consumed_current()
    assert handle.phase == "retired" and handle.effects == ()


def test_missing_ancestor_must_be_explicit_and_ordered(root):
    for paths in (("a/b",), ("a/b", "a")):
        with pytest.raises(
            owner.RetainedPhysicalMutationRefusal, match="missing_ancestor_not_explicit"
        ):
            retain(root, paths)
    assert not (root / "a").exists()


@pytest.mark.parametrize("action", ["finish", "replace_manifest"])
def test_invalid_transition_is_irreversibly_retired(root, action):
    handle = retain(root, ("private",))
    with pytest.raises(
        owner.RetainedPhysicalMutationRefusal, match="transition_invalid"
    ):
        getattr(handle, action)()
    assert handle.phase == "retired" and not (root / "private").exists()
    with pytest.raises(owner.RetainedPhysicalMutationRefusal, match="terminal"):
        handle.prepare_next_directory()


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_handle_cannot_be_copied_or_serialized(root, operation):
    handle = retain(root)
    with pytest.raises(TypeError):
        operation(handle)
    handle.release()


def test_constructor_and_forged_object_cannot_mint_authority(root):
    with pytest.raises(TypeError):
        owner.RetainedPhysicalMutation()
    forged = object.__new__(owner.RetainedPhysicalMutation)
    with pytest.raises(owner.RetainedPhysicalMutationRefusal, match="not_issued"):
        forged.replace_manifest()
    assert (root / "manifest.toml").read_bytes() == b"before"


def test_foreign_process_refuses_before_mutation(root, monkeypatch):
    handle = retain(root)
    real_pid = os.getpid()
    monkeypatch.setattr(owner.os, "getpid", lambda: real_pid + 1)
    with pytest.raises(owner.RetainedPhysicalMutationRefusal, match="foreign_process"):
        handle.replace_manifest()
    monkeypatch.undo()
    handle.release()
    assert (root / "manifest.toml").read_bytes() == b"before"


@pytest.mark.parametrize("after_write", [False, True])
def test_equal_bytes_substitution_is_not_authorized_replacement(root, after_write):
    handle = retain(root)
    if after_write:
        handle.replace_manifest()
    body = b"after" if after_write else b"before"
    substitute = root / "substitute"
    substitute.write_bytes(body)
    substitute.replace(root / "manifest.toml")
    with pytest.raises(
        owner.RetainedPhysicalMutationRefusal, match="identity_or_bytes_changed"
    ) as failure:
        handle.finish() if after_write else handle.replace_manifest()
    assert handle.phase == "retired"
    assert len(failure.value.effects) == (1 if after_write else 0)
    assert (root / "manifest.toml").read_bytes() == body


def test_root_substitution_retires_before_effect(root):
    handle = retain(root)
    relocated = root.with_name(root.name + "-relocated")
    root.rename(relocated)
    root.mkdir()
    (root / "manifest.toml").write_bytes(b"before")
    with pytest.raises(
        owner.RetainedPhysicalMutationRefusal, match="root_identity_changed"
    ):
        handle.replace_manifest()
    assert (relocated / "manifest.toml").read_bytes() == b"before"
    assert (root / "manifest.toml").read_bytes() == b"before"


def test_directory_substitution_is_not_accepted(root):
    (root / "specs").mkdir()
    handle = retain(root, ("specs",))
    (root / "specs").rename(root / "old-specs")
    (root / "specs").mkdir()
    with pytest.raises(
        owner.RetainedPhysicalMutationRefusal, match="directory_identity_changed"
    ):
        handle.prepare_next_directory()


@pytest.mark.parametrize("kind", ["directory", "manifest"])
def test_durability_failure_preserves_applied_effect_without_rollback(
    root, monkeypatch, kind
):
    handle = retain(root, ("private",) if kind == "directory" else ())
    original = os.fsync

    def fail_directory(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("injected durability failure")
        return original(fd)

    monkeypatch.setattr(os, "fsync", fail_directory)
    with pytest.raises(owner.RetainedPhysicalMutationRefusal) as failure:
        handle.prepare_next_directory() if kind == "directory" else handle.replace_manifest()
    assert handle.phase == "retired"
    assert failure.value.effects[-1].state is Effect.APPLIED
    assert not failure.value.effects[-1].durability_confirmed
    if kind == "directory":
        assert (root / "private").is_dir()
    else:
        assert (root / "manifest.toml").read_bytes() == b"after"


def test_uncertain_replace_reports_unknown_not_none(root, monkeypatch):
    handle = retain(root)
    original = os.replace

    def replace_then_fail(*args, **kwargs):
        original(*args, **kwargs)
        raise OSError("completion unknown")

    monkeypatch.setattr(os, "replace", replace_then_fail)
    with pytest.raises(owner.RetainedPhysicalMutationRefusal) as failure:
        handle.replace_manifest()
    assert failure.value.effects[-1].state is Effect.UNKNOWN
    assert (root / "manifest.toml").read_bytes() == b"after"


def test_unchanged_candidate_is_noop_but_requested_directories_still_count(root):
    original_inode = (root / "manifest.toml").stat().st_ino
    handle = retain(root, ("private",), candidate=b"before")
    handle.prepare_next_directory()
    assert handle.replace_manifest().state is Effect.NONE
    effects = handle.finish()
    assert (root / "manifest.toml").stat().st_ino == original_inode
    assert effects[0].state is Effect.APPLIED


def test_stronger_profile_refuses_before_io(root, monkeypatch):
    monkeypatch.setattr(os, "open", lambda *a, **k: pytest.fail("must not open"))
    with pytest.raises(
        owner.RetainedPhysicalMutationRefusal,
        match="continuous_root_confinement_unavailable",
    ):
        owner.retain_confined_manifest_replacement(
            root=root,
            target_path="manifest.toml",
            expected_content_digest=digest(b"before"),
            content=b"after",
            confinement_profile=ConfinedMutationProfile.CONTINUOUS_ROOT_V1,
        )


def test_hardlinked_manifest_is_not_qualified(root):
    os.link(root / "manifest.toml", root / "alias")
    with pytest.raises(owner.RetainedPhysicalMutationRefusal, match="alias_or_mount"):
        retain(root)


def test_scratch_cleanup_fault_is_reported_without_authorized_success(
    root, monkeypatch
):
    handle = retain(root)
    original_write = owner._write_temporary
    original_unlink = os.unlink

    def write_then_fail(**kwargs):
        original_write(**kwargs)
        raise OSError("scratch preparation interrupted")

    def fail_scratch_cleanup(path, **kwargs):
        if str(path).startswith(".aware-cas-"):
            raise OSError("scratch cleanup refused")
        return original_unlink(path, **kwargs)

    monkeypatch.setattr(owner, "_write_temporary", write_then_fail)
    monkeypatch.setattr(os, "unlink", fail_scratch_cleanup)
    with pytest.raises(
        owner.RetainedPhysicalMutationRefusal, match="scratch_cleanup_failed"
    ) as failure:
        handle.replace_manifest()
    assert handle.phase == "retired"
    assert failure.value.effects[-1].state is Effect.NONE
    assert len(failure.value.residual_scratch_paths) == 1
    assert (root / failure.value.residual_scratch_paths[0]).read_bytes() == b"after"
    assert (root / "manifest.toml").read_bytes() == b"before"


def test_interruption_after_mkdir_preserves_effect_and_retires(root, monkeypatch):
    handle = retain(root, ("private",))

    def interrupt(fd):
        raise KeyboardInterrupt()

    monkeypatch.setattr(os, "fsync", interrupt)
    with pytest.raises(owner.RetainedPhysicalMutationRefusal) as failure:
        handle.prepare_next_directory()
    assert handle.phase == "retired"
    assert failure.value.effects[-1].state is Effect.APPLIED
    assert (root / "private").is_dir()


@pytest.mark.parametrize("position", ["directory", "manifest"])
def test_symlinks_are_not_qualified(root, position):
    if position == "directory":
        (root / "private").symlink_to(root, target_is_directory=True)
        directories = ("private",)
    else:
        (root / "manifest.toml").rename(root / "real-manifest")
        (root / "manifest.toml").symlink_to(root / "real-manifest")
        directories = ()
    with pytest.raises((OSError, owner.RetainedPhysicalMutationRefusal)):
        retain(root, directories)


def test_restoring_bytes_does_not_revive_refused_handle(root):
    handle = retain(root)
    (root / "manifest.toml").write_bytes(b"foreign")
    with pytest.raises(owner.RetainedPhysicalMutationRefusal):
        handle.validate_current()
    (root / "manifest.toml").write_bytes(b"before")
    with pytest.raises(owner.RetainedPhysicalMutationRefusal, match="terminal"):
        handle.replace_manifest()


def test_previous_directory_effect_is_retained_after_later_refusal(root):
    handle = retain(root, ("private", "private/specs"))
    first = handle.prepare_next_directory()
    (root / "manifest.toml").write_bytes(b"foreign")
    with pytest.raises(owner.RetainedPhysicalMutationRefusal) as failure:
        handle.prepare_next_directory()
    assert failure.value.effects == (first,)
    assert (root / "private").is_dir() and not (root / "private/specs").exists()


def test_cross_device_directory_is_not_qualified(root, monkeypatch):
    (root / "private").mkdir()
    original = os.fstat
    root_inode = root.stat().st_ino

    def different_device(fd):
        value = original(fd)
        if stat.S_ISDIR(value.st_mode) and value.st_ino != root_inode:
            values = list(value)
            values[2] = value.st_dev + 1
            return os.stat_result(values)
        return value

    monkeypatch.setattr(os, "fstat", different_device)
    with pytest.raises(
        owner.RetainedPhysicalMutationRefusal, match="mount_boundary_unavailable"
    ):
        retain(root, ("private",))


def observed_signature(value):
    return tuple(
        getattr(value, name)
        for name in (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
        )
    )


def test_same_inode_equal_byte_rewrite_obeys_actual_observation_boundary(
    root, monkeypatch
):
    handle = retain(root)
    handle.replace_manifest()
    expected = owner._issued(handle).replacement
    original_read = owner._read_current
    observations = []

    def record_actual_read(**kwargs):
        current = original_read(**kwargs)
        observations.append(current)
        return current  # No clocks, timestamps or filesystem observations altered.

    (root / "manifest.toml").write_bytes(b"after")
    monkeypatch.setattr(owner, "_read_current", record_actual_read)
    try:
        effects = handle.finish()
    except owner.RetainedPhysicalMutationRefusal as failure:
        assert failure.code == "manifest_identity_or_bytes_changed"
        assert handle.phase == "retired"
        effects = failure.effects
        refused = True
    else:
        assert handle.phase == "consumed"
        refused = False
    assert len(observations) == 1
    body, observed = observations[0]
    assert body == b"after" and observed.st_nlink == 1
    assert (observed.st_dev, observed.st_ino) == (expected.st_dev, expected.st_ino)
    assert refused == (observed_signature(observed) != observed_signature(expected))
    assert effects[-1].state is Effect.APPLIED
    assert owner._issued(handle).root_fd is None


@pytest.mark.parametrize("entrance", ["finish", "validate_consumed_current"])
@pytest.mark.parametrize(
    "field",
    [
        "st_dev",
        "st_ino",
        "st_mode",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
        "st_nlink",
    ],
)
def test_changed_observation_field_refuses_deterministically(
    root, monkeypatch, entrance, field
):
    handle = retain(root)
    handle.replace_manifest()
    if entrance == "validate_consumed_current":
        handle.finish()
    expected = owner._issued(handle).replacement
    original_read = owner._read_current
    values = {
        name: getattr(expected, name)
        for name in (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
            "st_nlink",
        )
    }
    values[field] += 1

    def changed_observation(**kwargs):
        body, _ = original_read(**kwargs)
        # Synthetic observed-field fixture; not a host timestamp manipulation.
        return body, SimpleNamespace(**values)

    monkeypatch.setattr(owner, "_read_current", changed_observation)
    with pytest.raises(
        owner.RetainedPhysicalMutationRefusal, match="identity_or_bytes_changed"
    ) as failure:
        getattr(handle, entrance)()
    assert failure.value.effects[-1].state is Effect.APPLIED
    assert handle.phase == "retired" and owner._issued(handle).root_fd is None
    with pytest.raises(owner.RetainedPhysicalMutationRefusal):
        handle.validate_current()


@pytest.mark.parametrize("entrance", ["finish", "validate_consumed_current"])
@pytest.mark.parametrize("body", [b"after", b"other"])
def test_equal_observation_signature_is_not_write_history_or_byte_bypass(
    root, monkeypatch, entrance, body
):
    handle = retain(root)
    handle.replace_manifest()
    if entrance == "validate_consumed_current":
        handle.finish()
    expected = owner._issued(handle).replacement
    original_read = owner._read_current
    (root / "manifest.toml").write_bytes(body)

    def equal_signature(**kwargs):
        actual_body, actual_stat = original_read(**kwargs)
        assert (actual_stat.st_dev, actual_stat.st_ino) == (
            expected.st_dev,
            expected.st_ino,
        )
        # Deliberately model a metadata collision; preserve actual file bytes.
        return actual_body, expected

    monkeypatch.setattr(owner, "_read_current", equal_signature)
    if body == b"after":
        getattr(handle, entrance)()
        assert handle.phase == "consumed"
        assert handle.effects[-1].state is Effect.APPLIED
    else:
        with pytest.raises(
            owner.RetainedPhysicalMutationRefusal, match="identity_or_bytes_changed"
        ) as failure:
            getattr(handle, entrance)()
        assert failure.value.effects[-1].state is Effect.APPLIED
        assert handle.phase == "retired"
    assert owner._issued(handle).root_fd is None


def test_descriptor_cleanup_failure_keeps_applied_replacement(root, monkeypatch):
    handle = retain(root)
    original_close = os.close
    original_replace = os.replace
    replaced = False
    already_failed = False

    def replace_and_mark(*args, **kwargs):
        nonlocal replaced
        result = original_replace(*args, **kwargs)
        replaced = True
        return result

    def close_then_fail(fd):
        nonlocal already_failed
        original_close(fd)
        if replaced and not already_failed:
            already_failed = True
            raise OSError("close completion unavailable")

    monkeypatch.setattr(os, "replace", replace_and_mark)
    monkeypatch.setattr(os, "close", close_then_fail)
    with pytest.raises(owner.RetainedPhysicalMutationRefusal) as failure:
        handle.replace_manifest()
    assert failure.value.effects[-1].state is Effect.APPLIED
    assert handle.phase == "retired"
    assert (root / "manifest.toml").read_bytes() == b"after"


def test_relocation_at_actual_replace_retains_effect_but_refuses_success(
    root, monkeypatch
):
    parent = root / "specs"
    parent.mkdir()
    (parent / "manifest.toml").write_bytes(b"before")
    handle = owner.retain_confined_manifest_replacement(
        root=root,
        target_path="specs/manifest.toml",
        expected_content_digest=digest(b"before"),
        content=b"after",
    )
    outside = root.with_name(root.name + "-external")
    original = os.replace

    def relocate_and_replace(*args, **kwargs):
        parent.rename(outside)
        parent.mkdir()
        return original(*args, **kwargs)

    monkeypatch.setattr(os, "replace", relocate_and_replace)
    with pytest.raises(owner.RetainedPhysicalMutationRefusal) as failure:
        handle.replace_manifest()
    assert handle.phase == "retired"
    assert failure.value.effects[-1].state is Effect.APPLIED
    # Demonstrates the cooperative limit, not continuous confinement.
    assert (outside / "manifest.toml").read_bytes() == b"after"
    assert not (parent / "manifest.toml").exists()


@pytest.mark.parametrize(
    ("entrance", "preparation", "interrupt_check"),
    [
        ("validate_current", "issued", 1),
        ("validate_current", "preparing", 1),
        ("validate_current", "replaced", 1),
        ("prepare_next_directory", "issued", 1),
        ("prepare_next_directory", "issued", 2),
        ("prepare_next_directory", "preparing", 1),
        ("prepare_next_directory", "preparing", 2),
        ("replace_manifest", "prepared", 1),
        ("replace_manifest", "prepared", 2),
        ("replace_manifest", "prepared", 3),
        ("replace_manifest", "prepared", 4),
        ("finish", "replaced", 1),
    ],
)
def test_interrupted_freshness_retires_each_public_entrance(
    root, monkeypatch, entrance, preparation, interrupt_check
):
    directories = ("private", "private/specs")
    handle = retain(root, directories)
    if preparation in {"preparing", "prepared", "replaced"}:
        handle.prepare_next_directory()
    if preparation in {"prepared", "replaced"}:
        handle.prepare_next_directory()
    if preparation == "replaced":
        handle.replace_manifest()
    prior_effects = handle.effects
    state = owner._issued(handle)
    root_fd = state.root_fd
    assert root_fd is not None
    retained_fds = {root_fd}
    real_open, real_dup, real_close = os.open, os.dup, os.close

    def track_open(*args, **kwargs):
        descriptor = real_open(*args, **kwargs)
        retained_fds.add(descriptor)
        return descriptor

    def track_dup(descriptor):
        duplicated = real_dup(descriptor)
        retained_fds.add(duplicated)
        return duplicated

    def track_close(descriptor):
        real_close(descriptor)
        retained_fds.discard(descriptor)

    checks = 0
    real_verify = owner._verify
    interruption = KeyboardInterrupt("freshness interrupted")

    def interrupt_freshness(current):
        nonlocal checks
        checks += 1
        if checks == interrupt_check:
            raise interruption
        return real_verify(current)

    monkeypatch.setattr(os, "open", track_open)
    monkeypatch.setattr(os, "dup", track_dup)
    monkeypatch.setattr(os, "close", track_close)
    monkeypatch.setattr(owner, "_verify", interrupt_freshness)
    with pytest.raises(owner.RetainedPhysicalMutationRefusal) as failure:
        getattr(handle, entrance)()
    assert checks == interrupt_check
    assert failure.value.code == "physical_currentness_unavailable"
    cause = failure.value.__cause__
    while isinstance(cause, owner.RetainedPhysicalMutationRefusal):
        cause = cause.__cause__
    assert cause is interruption
    assert handle.phase == "retired" and state.root_fd is None
    assert retained_fds == set()
    with pytest.raises(OSError) as closed:
        os.fstat(root_fd)
    assert closed.value.errno == errno.EBADF
    assert failure.value.effects[: len(prior_effects)] == prior_effects
    assert failure.value.effects == handle.effects
    if entrance == "prepare_next_directory" and interrupt_check == 2:
        assert len(handle.effects) == len(prior_effects) + 1
        assert handle.effects[-1].state is Effect.APPLIED
        assert (root / handle.effects[-1].path).is_dir()
    manifest_written = preparation == "replaced" or (
        entrance == "replace_manifest" and interrupt_check >= 3
    )
    assert (root / "manifest.toml").read_bytes() == (
        b"after" if manifest_written else b"before"
    )
    if manifest_written:
        assert handle.effects[-1].state is Effect.APPLIED
    for replay in (
        "validate_current",
        "prepare_next_directory",
        "replace_manifest",
        "finish",
    ):
        with pytest.raises(owner.RetainedPhysicalMutationRefusal, match="terminal"):
            getattr(handle, replay)()
    assert checks == interrupt_check
