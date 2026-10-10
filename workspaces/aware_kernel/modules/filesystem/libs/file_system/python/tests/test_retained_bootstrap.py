from __future__ import annotations

import copy
import gc
import os
import pickle
import stat
import threading
from concurrent.futures import ThreadPoolExecutor

import aware_file_system.confined_mutation as confined
import aware_file_system.retained_bootstrap as owner
import pytest
from aware_file_system.confined_mutation import ConfinedMutationEffectState as Effect
from aware_file_system.confined_mutation import ConfinedMutationProfile
from aware_file_system.retained_mutation import (
    RetainedPhysicalMutationRefusal as Refusal,
)


def retain(root, directories=(), files=None):
    return owner.retain_confined_bootstrap_creation(
        root=root,
        files=files
        or (owner.BootstrapFileCreation("manifest.toml", b"profile = 'fs'"),),
        directory_paths=directories,
    )


def descriptors():
    return set(os.listdir("/proc/self/fd"))


def test_readonly_admission_explicit_directories_files_and_once_only_finish(tmp_path):
    (tmp_path / "existing").mkdir(mode=0o755)
    files = (
        owner.BootstrapFileCreation("manifest.toml", b"profile"),
        owner.BootstrapFileCreation("AGENTS.md", b"agents"),
        owner.BootstrapFileCreation("docs/issues/PROTOCOL.md", b"issues"),
    )
    baseline = descriptors()
    handle = retain(tmp_path, ("existing", "docs", "docs/issues"), files)
    assert handle.observe_effects() == () and not (tmp_path / "docs").exists()
    first, second, third = (handle.prepare_next_directory() for _ in range(3))
    assert first.state is Effect.NONE
    assert second.state is third.state is Effect.APPLIED
    assert stat.S_IMODE((tmp_path / "existing").stat().st_mode) == 0o755
    assert stat.S_IMODE((tmp_path / "docs/issues").stat().st_mode) == 0o700
    old_umask = os.umask(0o077)
    try:
        for item in files:
            effect = handle.create_next_file()
            assert effect.state is Effect.APPLIED and effect.durability_confirmed
            assert (tmp_path / item.path).read_bytes() == item.content
            assert stat.S_IMODE((tmp_path / item.path).stat().st_mode) == 0o644
    finally:
        os.umask(old_umask)
    results = handle.finish()
    assert len(results) == 6 and handle.phase == "consumed"
    assert handle.observe_effects() == results and descriptors() == baseline
    for name in (
        "create_next_file",
        "prepare_next_directory",
        "finish",
        "validate_current",
    ):
        with pytest.raises(Refusal, match="terminal"):
            getattr(handle, name)()
    handle.release()


@pytest.mark.parametrize("paths", [("a/b",), ("a/b", "a"), ()])
def test_every_missing_ancestor_must_be_explicit_and_ordered(tmp_path, paths):
    baseline = descriptors()
    with pytest.raises(Refusal, match="missing_ancestor_not_explicit"):
        retain(tmp_path, paths, (owner.BootstrapFileCreation("a/b/input.md", b"x"),))
    assert not (tmp_path / "a").exists() and descriptors() == baseline


@pytest.mark.parametrize("kind", ["file", "directory", "symlink", "broken", "fifo"])
def test_existing_target_never_adopted_or_replaced(tmp_path, kind):
    target = tmp_path / "manifest.toml"
    if kind == "file":
        target.write_bytes(b"profile = 'fs'")
    elif kind == "directory":
        target.mkdir()
    elif kind in {"symlink", "broken"}:
        target.symlink_to(tmp_path / ("present" if kind == "symlink" else "absent"))
        if kind == "symlink":
            (tmp_path / "present").write_bytes(b"foreign")
    else:
        os.mkfifo(target)
    baseline = descriptors()
    with pytest.raises(Refusal, match="bootstrap_target_not_absent"):
        retain(tmp_path)
    assert target.lstat() and descriptors() == baseline


@pytest.mark.parametrize(
    "path",
    ["../escape", "/absolute", ".", "a//b", "a/./b", ".git/config", "a/.git/config"],
)
def test_invalid_paths_refuse_before_filesystem_effects(path):
    with pytest.raises(ValueError):
        owner.BootstrapFileCreation(path, b"x")


@pytest.mark.parametrize("mode", [0o600, 0o755, True, "0644"])
def test_only_exact_bootstrap_file_mode_is_admitted(mode):
    with pytest.raises(ValueError):
        owner.BootstrapFileCreation("x", b"x", mode)


def test_bounds_and_colliding_paths_refuse_without_effects(tmp_path):
    item = owner.BootstrapFileCreation("x", b"x")
    for files, directories in (
        ((), ()),
        ((item,) * 4, ()),
        ((item, item), ()),
        ((item,), ("x",)),
        ((item,), tuple(f"d{i}" for i in range(65))),
    ):
        with pytest.raises(ValueError):
            owner.retain_confined_bootstrap_creation(
                root=tmp_path, files=files, directory_paths=directories
            )
    with pytest.raises(ValueError):
        owner.BootstrapFileCreation(
            "x", b"x" * (confined.DEFAULT_CONFINED_MUTATION_MAX_BYTES + 1)
        )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("action", ["finish", "create_next_file"])
def test_early_transition_refuses_and_retires(tmp_path, action):
    handle = retain(tmp_path, ("docs",))
    with pytest.raises(Refusal, match="transition_invalid"):
        getattr(handle, action)()
    assert handle.phase == "retired" and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "entrance",
    ["validate_current", "prepare_next_directory", "create_next_file", "finish"],
)
def test_interrupted_currentness_is_terminal_and_closes_descriptor(
    tmp_path, monkeypatch, entrance
):
    handle = retain(tmp_path, ("docs",))
    root_fd = owner._issued(handle).root_fd
    monkeypatch.setattr(
        owner, "_verify", lambda state: (_ for _ in ()).throw(KeyboardInterrupt())
    )
    with pytest.raises(Refusal):
        getattr(handle, entrance)()
    assert handle.phase == "retired" and handle.observe_effects() == ()
    with pytest.raises(OSError):
        os.fstat(root_fd)
    with pytest.raises(Refusal, match="terminal"):
        handle.validate_current()


def test_prior_success_survives_interrupted_freshness(tmp_path, monkeypatch):
    handle = retain(
        tmp_path,
        files=(
            owner.BootstrapFileCreation("one", b"1"),
            owner.BootstrapFileCreation("two", b"2"),
        ),
    )
    first = handle.create_next_file()
    monkeypatch.setattr(
        owner, "_verify", lambda state: (_ for _ in ()).throw(KeyboardInterrupt())
    )
    with pytest.raises(Refusal) as failed:
        handle.create_next_file()
    assert failed.value.effects == (first,) and (tmp_path / "one").read_bytes() == b"1"
    assert not (tmp_path / "two").exists()


@pytest.mark.parametrize("action", [copy.copy, copy.deepcopy, pickle.dumps])
def test_handles_cannot_be_copied_or_serialized(tmp_path, action):
    handle = retain(tmp_path)
    with pytest.raises(TypeError):
        action(handle)
    handle.release()


def test_forged_holder_and_foreign_process_refuse(tmp_path, monkeypatch):
    with pytest.raises(TypeError):
        owner.RetainedBootstrapCreation()
    with pytest.raises(Refusal, match="not_issued"):
        object.__new__(owner.RetainedBootstrapCreation).create_next_file()
    handle = retain(tmp_path)
    pid = os.getpid()
    monkeypatch.setattr(owner.os, "getpid", lambda: pid + 1)
    with pytest.raises(Refusal, match="foreign_process"):
        handle.create_next_file()
    monkeypatch.undo()
    assert handle.phase == "retired" and list(tmp_path.iterdir()) == []


def test_release_is_idempotent_and_finalizer_closes_without_deleting_work(tmp_path):
    baseline = descriptors()
    handle = retain(tmp_path)
    handle.create_next_file()
    handle.release()
    handle.release()
    assert descriptors() == baseline and (tmp_path / "manifest.toml").exists()
    abandoned = retain(tmp_path, files=(owner.BootstrapFileCreation("new", b"x"),))
    del abandoned
    gc.collect()
    assert descriptors() == baseline


def test_absent_target_race_refuses_without_overwriting_foreign_bytes(
    tmp_path, monkeypatch
):
    handle = retain(tmp_path)
    link = os.link

    def compete(*args, **kwargs):
        (tmp_path / "manifest.toml").write_bytes(b"foreign")
        return link(*args, **kwargs)

    monkeypatch.setattr(owner.os, "link", compete)
    with pytest.raises(Refusal) as failed:
        handle.create_next_file()
    assert failed.value.effects[-1].state is Effect.NONE
    assert (tmp_path / "manifest.toml").read_bytes() == b"foreign"
    assert not list(tmp_path.glob(".aware-cas-*")) and handle.phase == "retired"


@pytest.mark.parametrize("applied", [False, True])
def test_interrupted_link_remains_unknown_even_if_bytes_exist(
    tmp_path, monkeypatch, applied
):
    handle = retain(tmp_path)
    link = os.link

    def interrupt(*args, **kwargs):
        if applied:
            link(*args, **kwargs)
        raise KeyboardInterrupt()

    monkeypatch.setattr(owner.os, "link", interrupt)
    with pytest.raises(Refusal) as failed:
        handle.create_next_file()
    assert failed.value.effects[-1].state is Effect.UNKNOWN
    assert (tmp_path / "manifest.toml").exists() is applied
    assert not list(tmp_path.glob(".aware-cas-*"))
    with pytest.raises(Refusal, match="terminal"):
        handle.create_next_file()


def test_late_readback_failure_preserves_known_publication(tmp_path, monkeypatch):
    handle = retain(tmp_path)
    monkeypatch.setattr(owner, "_read_current", lambda **kwargs: "unavailable")
    with pytest.raises(Refusal) as failed:
        handle.create_next_file()
    assert failed.value.effects[-1].state is Effect.APPLIED
    assert not failed.value.effects[-1].durability_confirmed
    assert (tmp_path / "manifest.toml").read_bytes() == b"profile = 'fs'"


def test_directory_durability_failure_preserves_created_ancestor(tmp_path, monkeypatch):
    handle = retain(tmp_path, ("docs", "docs/issues"))
    monkeypatch.setattr(
        owner.os, "fsync", lambda fd: (_ for _ in ()).throw(OSError("durability"))
    )
    with pytest.raises(Refusal) as failed:
        handle.prepare_next_directory()
    assert failed.value.effects[-1].state is Effect.APPLIED
    assert not failed.value.effects[-1].durability_confirmed
    assert (tmp_path / "docs").is_dir() and not (tmp_path / "docs/issues").exists()


def test_equal_byte_substitution_refuses_original_postimage(tmp_path):
    handle = retain(tmp_path)
    original = handle.create_next_file()
    substitute = tmp_path / "foreign"
    substitute.write_bytes((tmp_path / "manifest.toml").read_bytes())
    substitute.replace(tmp_path / "manifest.toml")
    with pytest.raises(Refusal) as failed:
        handle.finish()
    assert failed.value.effects == (original,) and (tmp_path / "manifest.toml").exists()


def test_directory_substitution_and_symlinks_refuse_without_escape(tmp_path):
    existing = tmp_path / "docs"
    existing.mkdir()
    handle = retain(
        tmp_path, ("docs",), (owner.BootstrapFileCreation("docs/input", b"x"),)
    )
    existing.rename(tmp_path / "moved")
    existing.symlink_to(tmp_path / "moved", target_is_directory=True)
    with pytest.raises(Refusal):
        handle.prepare_next_directory()
    assert not (tmp_path / "moved/input").exists()


def test_fifo_substitution_readback_uses_nonblocking_shared_reader(
    tmp_path, monkeypatch
):
    handle = retain(tmp_path)
    real_open = os.open
    triggered = False

    def replace_before_open(path, flags, *args, **kwargs):
        nonlocal triggered
        if path == "manifest.toml" and not triggered:
            triggered = True
            assert flags & os.O_NONBLOCK
            (tmp_path / "manifest.toml").unlink()
            os.mkfifo(tmp_path / "manifest.toml")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(owner.os, "open", replace_before_open)
    with pytest.raises(Refusal) as failed:
        handle.create_next_file()
    assert triggered and failed.value.effects[-1].state is Effect.APPLIED
    assert stat.S_ISFIFO((tmp_path / "manifest.toml").stat().st_mode)


def test_stronger_confinement_is_not_claimed(tmp_path):
    unsupported = next(
        profile
        for profile in ConfinedMutationProfile
        if profile is not ConfinedMutationProfile.DESCRIPTOR_WALK_V1
    )
    with pytest.raises(Refusal, match="continuous_root_confinement_unavailable"):
        owner.retain_confined_bootstrap_creation(
            root=tmp_path,
            files=(owner.BootstrapFileCreation("x", b"x"),),
            directory_paths=(),
            confinement_profile=unsupported,
        )


def test_two_genuine_handles_do_not_adopt_each_others_publication(tmp_path):
    first, second = retain(tmp_path), retain(tmp_path)
    original = first.create_next_file()
    with pytest.raises(Refusal, match="bootstrap_target_not_absent"):
        second.create_next_file()
    assert second.observe_effects() == () and second.phase == "retired"
    assert first.finish() == (original,)


@pytest.mark.parametrize("published", [False, True])
def test_root_substitution_retires_without_writing_into_replacement(
    tmp_path, published
):
    root = tmp_path / "root"
    root.mkdir()
    handle = retain(root)
    if published:
        handle.create_next_file()
    root.rename(tmp_path / "original")
    root.mkdir()
    with pytest.raises(Refusal, match="root_identity_changed"):
        handle.finish() if published else handle.create_next_file()
    assert list(root.iterdir()) == []
    assert (tmp_path / "original/manifest.toml").exists() is published


@pytest.mark.parametrize("applied", [False, True])
def test_interrupted_directory_submission_stays_unknown(tmp_path, monkeypatch, applied):
    handle = retain(tmp_path, ("docs",))
    mkdir = os.mkdir

    def interrupt(*args, **kwargs):
        if applied:
            mkdir(*args, **kwargs)
        raise KeyboardInterrupt()

    monkeypatch.setattr(owner.os, "mkdir", interrupt)
    with pytest.raises(Refusal) as failed:
        handle.prepare_next_directory()
    assert failed.value.effects[-1].state is Effect.UNKNOWN
    assert (tmp_path / "docs").exists() is applied and handle.phase == "retired"


def test_late_parent_fsync_failure_preserves_published_bytes(tmp_path, monkeypatch):
    handle = retain(tmp_path)
    fsync = os.fsync

    def fail_parent(descriptor):
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise OSError("parent durability unavailable")
        return fsync(descriptor)

    monkeypatch.setattr(owner.os, "fsync", fail_parent)
    with pytest.raises(Refusal) as failed:
        handle.create_next_file()
    assert failed.value.effects[-1].state is Effect.APPLIED
    assert not failed.value.effects[-1].durability_confirmed
    assert (tmp_path / "manifest.toml").read_bytes() == b"profile = 'fs'"


def test_failed_temporary_write_reports_residue_without_assuming_custody(
    tmp_path, monkeypatch
):
    handle = retain(tmp_path)
    write = owner._write_temporary

    def fail_after_write(**kwargs):
        write(**kwargs)
        raise OSError("write completion unverified")

    monkeypatch.setattr(owner, "_write_temporary", fail_after_write)
    with pytest.raises(Refusal, match="scratch_cleanup_identity_unverified") as failed:
        handle.create_next_file()
    assert failed.value.effects[-1].state is Effect.NONE
    assert len(failed.value.residual_scratch_paths) == 1
    assert (tmp_path / failed.value.residual_scratch_paths[0]).is_file()
    assert not (tmp_path / "manifest.toml").exists()


@pytest.mark.parametrize("remove_first", [False, True])
def test_interrupted_scratch_disposal_retains_publication_and_unknown_cleanup(
    tmp_path, monkeypatch, remove_first
):
    baseline = descriptors()
    handle = retain(tmp_path)
    unlink = os.unlink
    attempts = 0

    def interrupt(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if remove_first:
            unlink(*args, **kwargs)
        raise KeyboardInterrupt()

    monkeypatch.setattr(owner.os, "unlink", interrupt)
    with pytest.raises(Refusal) as failed:
        handle.create_next_file()
    assert failed.value.effects[-1].state is Effect.APPLIED
    assert failed.value.residual_scratch_paths
    assert (tmp_path / "manifest.toml").exists() and handle.phase == "retired"
    assert descriptors() == baseline
    assert attempts == 1


@pytest.mark.parametrize("method", ["release", "finish"])
def test_interrupted_root_release_never_completes_or_restores_authority(
    tmp_path, monkeypatch, method
):
    baseline = descriptors()
    handle = retain(tmp_path)
    effect = handle.create_next_file()
    root_fd = owner._issued(handle).root_fd
    close = os.close

    def interrupt_after_close(descriptor):
        close(descriptor)
        if descriptor == root_fd:
            raise KeyboardInterrupt()

    monkeypatch.setattr(owner.os, "close", interrupt_after_close)
    with pytest.raises(Refusal, match="descriptor_cleanup_failed") as failed:
        getattr(handle, method)()
    assert failed.value.effects == (effect,) and handle.phase == "retired"
    assert (tmp_path / "manifest.toml").exists() and descriptors() == baseline
    with pytest.raises(Refusal, match="terminal"):
        handle.finish()


def test_return_time_change_preserves_effect_and_refuses_success(tmp_path, monkeypatch):
    handle = retain(tmp_path)
    verify = owner._verify

    def mutate_after_creation(state):
        if state.created:
            (tmp_path / "manifest.toml").write_bytes(b"changed")
        return verify(state)

    monkeypatch.setattr(owner, "_verify", mutate_after_creation)
    with pytest.raises(
        Refusal, match="created_file_identity_or_bytes_changed"
    ) as failed:
        handle.create_next_file()
    assert len(failed.value.effects) == 1
    assert failed.value.effects[0].state is Effect.APPLIED
    assert handle.phase == "retired" and (tmp_path / "manifest.toml").exists()


def test_retained_file_values_are_detached_from_caller_mutation(tmp_path):
    value = owner.BootstrapFileCreation("original", b"approved")
    handle = retain(tmp_path, files=(value,))
    object.__setattr__(value, "path", "changed")
    object.__setattr__(value, "content", b"substituted")
    handle.create_next_file()
    handle.finish()
    assert (tmp_path / "original").read_bytes() == b"approved"
    assert not (tmp_path / "changed").exists()


def test_forged_file_data_is_revalidated_without_minting_authority(tmp_path):
    value = owner.BootstrapFileCreation("valid", b"x")
    object.__setattr__(value, "path", "../escape")
    with pytest.raises(ValueError):
        retain(tmp_path, files=(value,))
    assert list(tmp_path.iterdir()) == []


def test_foreign_scratch_substitution_is_not_deleted(tmp_path, monkeypatch):
    handle = retain(tmp_path)
    link = os.link

    def substitute_after_link(source, target, **kwargs):
        result = link(source, target, **kwargs)
        scratch = tmp_path / source
        scratch.unlink()
        scratch.write_bytes(b"foreign scratch")
        return result

    monkeypatch.setattr(owner.os, "link", substitute_after_link)
    with pytest.raises(Refusal, match="scratch_cleanup_identity_unverified") as failed:
        handle.create_next_file()
    assert failed.value.effects[-1].state is Effect.APPLIED
    assert (tmp_path / "manifest.toml").read_bytes() == b"profile = 'fs'"
    assert len(failed.value.residual_scratch_paths) == 1
    assert (
        tmp_path / failed.value.residual_scratch_paths[0]
    ).read_bytes() == b"foreign scratch"


def test_real_concurrent_no_replace_has_one_original_winner(tmp_path, monkeypatch):
    handles = (retain(tmp_path), retain(tmp_path))
    barrier = threading.Barrier(2)
    link = os.link

    def simultaneous_link(*args, **kwargs):
        barrier.wait(timeout=5)
        return link(*args, **kwargs)

    def publish(handle):
        try:
            return handle.create_next_file()
        except Refusal as error:
            return error

    monkeypatch.setattr(owner.os, "link", simultaneous_link)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(publish, handles))
    winners = [
        index for index, value in enumerate(results) if not isinstance(value, Refusal)
    ]
    assert len(winners) == 1
    winner = winners[0]
    loser = 1 - winner
    assert handles[winner].finish() == (results[winner],)
    assert results[loser].effects[-1].state is Effect.NONE
    assert handles[loser].phase == "retired"
    assert (tmp_path / "manifest.toml").read_bytes() == b"profile = 'fs'"
    assert not list(tmp_path.glob(".aware-cas-*"))
