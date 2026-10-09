import copy
import gc
import os
import pickle
import threading
import weakref

import pytest
from aware_file_system import retained_package as module
from aware_file_system.retained_package import (
    PackagePublicationPostimage,
    PackagePublicationRefusal,
    RetainedPackagePublication,
    RetainedPackageReadPostimage,
    StagedPackageSource,
    observe_package_plan,
    release_package_postimage_read,
    require_package_postimage_read,
    require_retained_package_plan,
    retain_package_postimage_read,
    retain_package_publication,
    validate_package_plan,
    validate_package_postimage,
    validate_package_postimage_read,
    validate_staged_package_source,
)


def plan(tmp_path, **changes):
    values = {
        "root": tmp_path,
        "target_path": "package",
        "ordered_members": (("a.txt", b"one"), ("nested/b.txt", b"two")),
    }
    values.update(changes)
    return retain_package_publication(**values)


def published(tmp_path, **changes):
    handle = plan(tmp_path, **changes)
    handle.stage()
    return handle, handle.publish_package()


def test_independent_readers_survive_writer_release(tmp_path):
    handle, image = published(tmp_path)
    first = retain_package_postimage_read(image)
    second = retain_package_postimage_read(image)
    handle.finish(image)
    assert require_retained_package_plan(handle) is handle
    handle.release()
    for reader in (first, second):
        assert require_package_postimage_read(reader) is reader
        validate_package_postimage_read(reader, plan=handle)
        assert reader.observe_binding().target_path == "package"
    first.release()
    second.validate_current()
    descriptor = second.duplicate_package_descriptor()
    second.release()
    try:
        assert os.stat("a.txt", dir_fd=descriptor).st_size == 3
    finally:
        os.close(descriptor)
    with pytest.raises(PackagePublicationRefusal):
        retain_package_postimage_read(image)
    assert handle.phase == "released"


def test_reader_does_not_retain_writer_lifetime(tmp_path):
    handle, image = published(tmp_path)
    reader = retain_package_postimage_read(image)
    reference = weakref.ref(handle)
    del image, handle
    gc.collect()
    assert reference() is None
    reader.validate_current()
    reader.release()


@pytest.mark.parametrize("change", ["bytes", "inode", "link", "addition", "relocate"])
def test_reader_mismatch_retires_only_read_authority(tmp_path, change):
    handle, image = published(tmp_path)
    reader = retain_package_postimage_read(image)
    handle.release()
    evidence = handle.evidence
    member = tmp_path / "package/a.txt"
    if change == "bytes":
        member.write_bytes(b"bad")
    elif change == "inode":
        member.unlink()
        member.write_bytes(b"one")
    elif change == "link":
        os.link(member, tmp_path / "link")
    elif change == "addition":
        (tmp_path / "package/foreign").write_bytes(b"foreign")
    else:
        (tmp_path / "package").rename(tmp_path / "relocated")
    state = module._READERS[reader]
    descriptors = tuple(state.fds.values())
    with pytest.raises(PackagePublicationRefusal):
        reader.validate_current()
    assert reader.phase == "retired"
    assert not state.fds
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)
    assert handle.evidence == evidence
    assert (tmp_path / ("relocated" if change == "relocate" else "package")).exists()
    with pytest.raises(PackagePublicationRefusal):
        reader.validate_current()
    reader.release()


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_readers_cannot_be_copied_or_serialized(tmp_path, operation):
    handle, image = published(tmp_path)
    reader = retain_package_postimage_read(image)
    try:
        with pytest.raises(TypeError):
            operation(reader)
    finally:
        reader.release()
        handle.release()


def test_reader_requires_original_and_has_no_writer_entrance(tmp_path):
    with pytest.raises(TypeError):
        RetainedPackageReadPostimage()
    with pytest.raises(TypeError):
        type("Forged", (RetainedPackageReadPostimage,), {})
    handle, image = published(tmp_path)
    reader = retain_package_postimage_read(image)
    for value in (
        object(),
        handle.evidence,
        object.__new__(RetainedPackageReadPostimage),
    ):
        with pytest.raises(PackagePublicationRefusal):
            require_package_postimage_read(value)
        with pytest.raises(PackagePublicationRefusal):
            retain_package_postimage_read(value)
    for name in ("stage", "publish_package", "finish"):
        assert not hasattr(reader, name)
    release_package_postimage_read(reader)
    release_package_postimage_read(reader)
    with pytest.raises(PackagePublicationRefusal, match="terminal"):
        require_package_postimage_read(reader)
    handle.release()


def test_foreign_plan_retires_reader_without_retiring_writer(tmp_path):
    handle, image = published(tmp_path)
    other = plan(tmp_path, target_path="other")
    reader = retain_package_postimage_read(image)
    with pytest.raises(PackagePublicationRefusal, match="provenance"):
        validate_package_postimage_read(reader, plan=other)
    assert reader.phase == "retired"
    assert handle.phase == "published"
    validate_package_postimage(handle, image)
    reader.release()
    handle.release()
    other.release()


def test_interrupted_reader_check_closes_only_reader_descriptors(tmp_path, monkeypatch):
    handle, image = published(tmp_path)
    reader = retain_package_postimage_read(image)
    original = module._verify

    def interrupted(state):
        if state is module._READERS[reader]:
            raise KeyboardInterrupt
        return original(state)

    monkeypatch.setattr(module, "_verify", interrupted)
    with pytest.raises(PackagePublicationRefusal):
        reader.validate_current()
    assert reader.phase == "retired"
    assert not module._READERS[reader].fds
    validate_package_postimage(handle, image)
    reader.release()
    handle.release()


def test_partial_duplication_failure_closes_clones_not_writer(tmp_path, monkeypatch):
    handle, image = published(tmp_path)
    original = os.dup
    duplicates = []

    def failing(descriptor):
        if duplicates:
            raise OSError("duplication failed")
        result = original(descriptor)
        duplicates.append(result)
        return result

    monkeypatch.setattr(os, "dup", failing)
    with pytest.raises(PackagePublicationRefusal) as refusal:
        retain_package_postimage_read(image)
    assert isinstance(refusal.value.__cause__, OSError)
    for descriptor in duplicates:
        with pytest.raises(OSError):
            os.fstat(descriptor)
    validate_package_postimage(handle, image)
    assert handle.phase == "published"
    handle.release()


def test_reader_can_be_retained_after_consumption_before_release(tmp_path):
    handle, image = published(tmp_path)
    handle.finish(image)
    reader = retain_package_postimage_read(image)
    handle.release()
    reader.validate_current()
    reader.release()


def test_actual_staging_publication_original_postimage_and_single_consumption(tmp_path):
    handle = plan(tmp_path)
    assert list(tmp_path.iterdir()) == []
    assert handle.phase == "planned"
    lens = handle.stage()
    validate_staged_package_source(handle, lens)
    borrowed = lens.duplicate_parent_descriptor()
    try:
        assert os.stat(lens.stage_name, dir_fd=borrowed).st_mode & 0o077 == 0
    finally:
        os.close(borrowed)
    image = handle.publish_package()
    assert (tmp_path / "package/a.txt").read_bytes() == b"one"
    assert (tmp_path / "package/nested/b.txt").read_bytes() == b"two"
    validate_package_postimage(handle, image)
    evidence = handle.finish(image)
    assert evidence.package_outcome == "published"
    assert evidence.durability_confirmed is False
    assert not evidence.residual_scratch_paths
    validate_package_postimage(handle, image)
    with pytest.raises(PackagePublicationRefusal, match="terminal"):
        handle.publish_package()
    handle.release()
    assert (tmp_path / "package/a.txt").read_bytes() == b"one"


@pytest.mark.parametrize(
    "cls",
    [RetainedPackagePublication, StagedPackageSource, PackagePublicationPostimage],
)
def test_public_holders_cannot_be_constructed_or_subclassed(cls):
    with pytest.raises(TypeError):
        cls()
    with pytest.raises(TypeError):
        type("Forged", (cls,), {})


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_handle_not_copyable_or_serializable(tmp_path, operation):
    handle = plan(tmp_path)
    try:
        with pytest.raises(TypeError):
            operation(handle)
    finally:
        handle.release()


def test_forged_and_foreign_lenses_postimages_are_not_evidence(tmp_path):
    first = plan(tmp_path)
    second = plan(tmp_path, target_path="other")
    lens = first.stage()
    with pytest.raises(PackagePublicationRefusal, match="foreign_staged"):
        validate_staged_package_source(second, lens)
    assert second.phase == "retired"
    image = first.publish_package()
    fake = object.__new__(PackagePublicationPostimage)
    with pytest.raises(PackagePublicationRefusal, match="original_publication"):
        validate_package_postimage(first, fake)
    assert first.phase == "retired"
    assert image is not fake
    assert (tmp_path / "package/a.txt").read_bytes() == b"one"


@pytest.mark.parametrize(
    "path", ["../outside", "/outside", "a//b", "e\u0301/file", "a\u0080b/file", " a"]
)
def test_noncanonical_paths_refuse_before_effects(tmp_path, path):
    with pytest.raises(ValueError):
        plan(tmp_path, ordered_members=((path, b""),))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("kind", ["file", "directory", "symlink"])
def test_occupied_target_never_overwritten(tmp_path, kind):
    target = tmp_path / "package"
    if kind == "file":
        target.write_bytes(b"foreign")
    elif kind == "directory":
        target.mkdir()
    else:
        target.symlink_to("missing")
    with pytest.raises(PackagePublicationRefusal, match="occupied"):
        plan(tmp_path)
    assert target.exists() or target.is_symlink()


def test_missing_and_symlink_parent_not_prepared(tmp_path):
    with pytest.raises(PackagePublicationRefusal):
        plan(tmp_path, target_path="missing/package")
    assert list(tmp_path.iterdir()) == []
    (tmp_path / "link").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(PackagePublicationRefusal):
        plan(tmp_path, target_path="link/package")


def test_original_plan_binding_mismatch_retires_before_effects(tmp_path):
    handle = plan(tmp_path)
    with pytest.raises(PackagePublicationRefusal, match="binding_mismatch"):
        validate_package_plan(
            handle,
            root=tmp_path,
            target_path="wrong",
            scratch_path=handle.scratch_path,
            ordered_members=(("a", b""),),
        )
    assert handle.phase == "retired"
    assert list(tmp_path.iterdir()) == []


def test_original_plan_inspection_matches_retained_coordinates_and_identities(tmp_path):
    handle = plan(tmp_path)
    try:
        observed = observe_package_plan(handle)
        current = tmp_path.stat()
        assert observed.root_identity == (
            current.st_dev,
            current.st_ino,
            current.st_mode,
        )
        assert observed.parent_identity == observed.root_identity
        assert observed.target_path == "package"
        assert observed.scratch_path == handle.scratch_path
        validate_package_plan(
            handle,
            root=tmp_path,
            target_path=observed.target_path,
            scratch_path=observed.scratch_path,
            ordered_members=observed.ordered_members,
        )
        fake = object.__new__(RetainedPackagePublication)
        with pytest.raises(PackagePublicationRefusal, match="original_package"):
            observe_package_plan(fake)
    finally:
        handle.release()


def test_release_removes_only_matching_owned_stage(tmp_path):
    handle = plan(tmp_path)
    handle.stage()
    evidence = handle.release()
    assert evidence.package_outcome == "none"
    assert evidence.effects
    assert not evidence.residual_scratch_paths
    assert list(tmp_path.iterdir()) == []


def test_modified_member_and_foreign_addition_preserved(tmp_path):
    handle = plan(tmp_path)
    handle.stage()
    stage = tmp_path / handle.scratch_path
    (stage / "a.txt").write_bytes(b"changed")
    (stage / "foreign").write_bytes(b"foreign")
    evidence = handle.release()
    assert (stage / "a.txt").read_bytes() == b"changed"
    assert (stage / "foreign").read_bytes() == b"foreign"
    assert not (stage / "nested").exists()
    assert evidence.residual_scratch_paths
    assert evidence.cleanup_diagnostics


def test_foreign_entry_refuses_publication_and_is_not_deleted(tmp_path):
    handle = plan(tmp_path)
    handle.stage()
    stage = tmp_path / handle.scratch_path
    (stage / "foreign").write_bytes(b"foreign")
    with pytest.raises(PackagePublicationRefusal, match="foreign_entry"):
        handle.publish_package()
    assert not (tmp_path / "package").exists()
    assert (stage / "foreign").read_bytes() == b"foreign"


def test_competing_target_after_stage_refuses_without_replace(tmp_path):
    handle = plan(tmp_path)
    handle.stage()
    (tmp_path / "package").mkdir()
    with pytest.raises(PackagePublicationRefusal, match="occupied"):
        handle.publish_package()
    assert (tmp_path / "package").is_dir()


def test_unknown_rename_after_actual_effect_never_cleans_published_members(
    tmp_path, monkeypatch
):
    handle = plan(tmp_path)
    handle.stage()
    original = module._rename_no_replace

    def uncertain(*args):
        original(*args)
        raise KeyboardInterrupt()

    monkeypatch.setattr(module, "_rename_no_replace", uncertain)
    with pytest.raises(PackagePublicationRefusal) as result:
        handle.publish_package()
    assert result.value.evidence.package_outcome == "unknown"
    assert (tmp_path / "package/a.txt").read_bytes() == b"one"
    assert (tmp_path / "package/nested/b.txt").read_bytes() == b"two"
    assert handle.phase == "retired"
    with pytest.raises(PackagePublicationRefusal):
        handle.publish_package()


def test_postpublication_member_change_preserves_known_effect(tmp_path):
    handle = plan(tmp_path)
    handle.stage()
    image = handle.publish_package()
    (tmp_path / "package/a.txt").write_bytes(b"changed")
    with pytest.raises(PackagePublicationRefusal) as result:
        validate_package_postimage(handle, image)
    assert result.value.evidence.package_outcome == "published"
    assert (tmp_path / "package/a.txt").read_bytes() == b"changed"


@pytest.mark.parametrize("entrance", ["validate", "stage", "publish", "finish"])
def test_interrupted_guard_terminally_retires_and_closes_owned_fds(
    tmp_path, monkeypatch, entrance
):
    handle = plan(tmp_path)
    image = None
    if entrance in {"publish", "finish"}:
        handle.stage()
    if entrance == "finish":
        image = handle.publish_package()
    state = module._HANDLES[handle]
    descriptors = tuple(state.fds.values())
    original = module._topology

    def interrupt(state):
        raise KeyboardInterrupt()

    monkeypatch.setattr(module, "_topology", interrupt)
    with pytest.raises(PackagePublicationRefusal):
        if entrance == "validate":
            handle.validate_current()
        elif entrance == "stage":
            handle.stage()
        elif entrance == "publish":
            handle.publish_package()
        else:
            handle.finish(image)
    assert handle.phase == "retired"
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)
    monkeypatch.setattr(module, "_topology", original)
    with pytest.raises(PackagePublicationRefusal):
        handle.validate_current()
    if entrance == "finish":
        assert (tmp_path / "package/a.txt").read_bytes() == b"one"


def test_unavailable_primitive_has_no_public_effect(tmp_path, monkeypatch):
    handle = plan(tmp_path)
    handle.stage()

    def unavailable(*args):
        raise module._RenameRefusal("atomic_package_publication_unavailable")

    monkeypatch.setattr(module, "_rename_no_replace", unavailable)
    with pytest.raises(PackagePublicationRefusal) as result:
        handle.publish_package()
    assert result.value.evidence.package_outcome == "none"
    assert not (tmp_path / "package").exists()


def test_partial_write_failure_cleans_only_known_matching_prefix(tmp_path, monkeypatch):
    handle = plan(tmp_path)
    original = module.os.write
    calls = 0

    def fail(descriptor, body):
        nonlocal calls
        calls += 1
        if calls == 1:
            return original(descriptor, body[:1])
        raise OSError("write fault")

    monkeypatch.setattr(module.os, "write", fail)
    with pytest.raises(PackagePublicationRefusal) as result:
        handle.stage()
    assert result.value.evidence.package_outcome == "none"
    assert result.value.evidence.effects
    assert list(tmp_path.iterdir()) == []


def test_uncertain_write_preserves_unmatched_bytes_and_residue(tmp_path, monkeypatch):
    handle = plan(tmp_path)
    original = module.os.write

    def uncertain(descriptor, body):
        original(descriptor, body)
        raise KeyboardInterrupt()

    monkeypatch.setattr(module.os, "write", uncertain)
    with pytest.raises(PackagePublicationRefusal) as result:
        handle.stage()
    assert result.value.evidence.residual_scratch_paths
    assert (tmp_path / handle.scratch_path / "a.txt").read_bytes() == b"one"
    assert not (tmp_path / "package").exists()


def test_unknown_stage_creation_does_not_delete_unverified_tree(tmp_path, monkeypatch):
    handle = plan(tmp_path)
    original = module.os.mkdir

    def uncertain(*args, **kwargs):
        original(*args, **kwargs)
        raise KeyboardInterrupt()

    monkeypatch.setattr(module.os, "mkdir", uncertain)
    with pytest.raises(PackagePublicationRefusal) as result:
        handle.stage()
    assert result.value.evidence.residual_scratch_paths == (handle.scratch_path,)
    assert (tmp_path / handle.scratch_path).is_dir()


def test_native_no_replace_refuses_open_time_competitor(tmp_path, monkeypatch):
    handle = plan(tmp_path)
    handle.stage()
    original = module._rename_no_replace

    def compete(*args):
        (tmp_path / "package").mkdir()
        (tmp_path / "package/foreign").write_bytes(b"foreign")
        original(*args)

    monkeypatch.setattr(module, "_rename_no_replace", compete)
    with pytest.raises(PackagePublicationRefusal) as result:
        handle.publish_package()
    assert result.value.evidence.package_outcome == "none"
    assert (tmp_path / "package/foreign").read_bytes() == b"foreign"


def test_publication_return_mismatch_preserves_applied_outcome(tmp_path, monkeypatch):
    handle = plan(tmp_path)
    handle.stage()
    original = module._rename_no_replace

    def change(*args):
        original(*args)
        (tmp_path / "package/a.txt").write_bytes(b"changed")

    monkeypatch.setattr(module, "_rename_no_replace", change)
    with pytest.raises(PackagePublicationRefusal) as result:
        handle.publish_package()
    assert result.value.evidence.package_outcome == "published"
    assert not result.value.evidence.residual_scratch_paths
    assert (tmp_path / "package/a.txt").read_bytes() == b"changed"


def test_relocated_parent_prevents_cleanup_outside_declared_topology(tmp_path):
    (tmp_path / "parent").mkdir()
    handle = plan(tmp_path, target_path="parent/package")
    handle.stage()
    stage_name = os.path.basename(handle.scratch_path)
    (tmp_path / "parent").rename(tmp_path / "moved")
    with pytest.raises(PackagePublicationRefusal):
        handle.validate_current()
    assert (tmp_path / "moved" / stage_name / "a.txt").read_bytes() == b"one"
    assert handle.evidence.cleanup_diagnostics


def test_borrowed_parent_descriptor_has_independent_lifetime(tmp_path):
    handle = plan(tmp_path)
    lens = handle.stage()
    descriptor = lens.duplicate_parent_descriptor()
    handle.release()
    try:
        assert os.fstat(descriptor).st_ino == tmp_path.stat().st_ino
        with pytest.raises(PackagePublicationRefusal):
            lens.duplicate_parent_descriptor()
    finally:
        os.close(descriptor)


def test_all_other_descriptors_attempted_after_close_interruption(
    tmp_path, monkeypatch
):
    handle = plan(tmp_path)
    handle.stage()
    image = handle.publish_package()
    handle.finish(image)
    descriptors = set(module._HANDLES[handle].fds.values())
    original = module.os.close
    attempted = []

    def interrupted(descriptor):
        attempted.append(descriptor)
        original(descriptor)
        if len(attempted) == 1:
            raise KeyboardInterrupt()

    monkeypatch.setattr(module.os, "close", interrupted)
    evidence = handle.release()
    assert set(attempted) == descriptors
    assert evidence.cleanup_diagnostics
    assert evidence.package_outcome == "published"


@pytest.mark.parametrize(
    "member",
    [(("a", b""), ("a/b", b"")), (("b", b""), ("a", b"")), (("a", bytearray()),), ()],
)
def test_bounded_member_shape_before_reads_and_effects(tmp_path, member):
    with pytest.raises(ValueError):
        plan(tmp_path, ordered_members=member)
    assert list(tmp_path.iterdir()) == []


def test_each_incremental_stage_entrance_has_at_most_one_source_submission(
    tmp_path, monkeypatch
):
    handle = plan(tmp_path)
    calls = []
    original_open = module.os.open
    original_mkdir = module.os.mkdir
    original_write = module.os.write

    def opened(path, flags, *args, **kwargs):
        if flags & os.O_CREAT:
            calls.append("create")
        return original_open(path, flags, *args, **kwargs)

    def made(*args, **kwargs):
        calls.append("mkdir")
        return original_mkdir(*args, **kwargs)

    def written(*args, **kwargs):
        calls.append("write")
        return original_write(*args, **kwargs)

    monkeypatch.setattr(module.os, "open", opened)
    monkeypatch.setattr(module.os, "mkdir", made)
    monkeypatch.setattr(module.os, "write", written)
    try:
        while handle.phase != "staged":
            before = len(calls)
            handle.stage_next_effect()
            assert len(calls) - before <= 1
        assert calls == ["mkdir", "mkdir", "create", "write", "create", "write"]
        validate_staged_package_source(handle, handle.lend_staged_source())
    finally:
        handle.release()


def test_fifo_substitution_between_stat_and_read_refuses_without_blocking(
    tmp_path, monkeypatch
):
    handle = plan(tmp_path)
    handle.stage()
    target = tmp_path / handle.scratch_path / "a.txt"
    original = module.os.open
    swapped = False

    def substitute(path, flags, *args, **kwargs):
        nonlocal swapped
        if path == "a.txt" and flags & os.O_NONBLOCK and not swapped:
            swapped = True
            target.unlink()
            os.mkfifo(target)
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", substitute)
    with pytest.raises(PackagePublicationRefusal):
        handle.validate_current()
    assert swapped
    assert handle.phase == "retired"
    assert target.exists()


def test_evidence_read_serializes_with_original_effect_advancement(
    tmp_path, monkeypatch
):
    handle = plan(tmp_path)
    state = module._HANDLES[handle]
    started = threading.Event()
    captured = threading.Event()
    observed = []
    errors = []
    original = module._evidence

    def capture(current):
        captured.set()
        return original(current)

    def reader():
        started.set()
        try:
            observed.append(handle.evidence)
        except BaseException as error:  # noqa: BLE001 - report thread failures to the test owner
            errors.append(error)

    monkeypatch.setattr(module, "_evidence", capture)
    thread = threading.Thread(target=reader, daemon=True)
    try:
        with state.lock:
            thread.start()
            assert started.wait(2)
            assert not captured.wait(0.05)
            handle.stage_next_effect()
            expected = original(state)
        thread.join(2)
        assert not thread.is_alive()
        assert not errors
        assert observed == [expected]
        assert expected.effects
    finally:
        handle.release()


def test_evidence_snapshots_survive_consumption_release_and_later_reader_close(
    tmp_path,
):
    handle = plan(tmp_path)
    initialized = handle.evidence
    handle.stage()
    staged = handle.evidence
    image = handle.publish_package()
    consumed = handle.finish(image)
    released = handle.release()
    assert initialized.package_outcome == "none" and initialized.effects == ()
    assert staged.package_outcome == "none" and staged.effects
    assert consumed.package_outcome == released.package_outcome == "published"
    assert handle.evidence == released
    with pytest.raises(PackagePublicationRefusal):
        validate_package_postimage(handle, image)
    assert initialized.effects == ()
    assert consumed.effects == released.effects


def test_retired_cleanup_snapshot_remains_readable_without_authority_renewal(tmp_path):
    handle = plan(tmp_path)
    handle.stage()
    (tmp_path / handle.scratch_path / "a.txt").write_bytes(b"changed")
    with pytest.raises(PackagePublicationRefusal) as error:
        handle.validate_current()
    retained = handle.evidence
    assert handle.phase == "retired"
    assert retained == error.value.evidence
    assert retained.residual_scratch_paths
    with pytest.raises(PackagePublicationRefusal):
        handle.stage_next_effect()
    assert handle.evidence == retained
