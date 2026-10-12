"""Real read-only original binding/currentness/cleanup through the SDK."""

import os
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest
from aware_protocol_fs_adapter import FilesystemProtocolSpecificationTargetFitProvider
from aware_protocol_fs_adapter import specification_selection as owner
from aware_protocol_fs_adapter import specification_target_fit as implementation
from aware_protocol_sdk import specification_target_fit as sdk
from test_specification_selection import TARGET, fd_count, source


def prepare(root, *, target=TARGET, body=None, locator="aware.protocol.toml"):
    manifest = root / locator
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(source() if body is None else body)
    return sdk.ProtocolSpecificationTargetFitRequest(
        str(root),
        locator,
        target,
        "sha256:" + sha256(manifest.read_bytes()).hexdigest(),
    )


def observe(request):
    return sdk.ProtocolSpecificationTargetFitClient(
        FilesystemProtocolSpecificationTargetFitProvider()
    ).observe(request)


@pytest.mark.parametrize(
    "target,fit,key",
    [
        (TARGET, "match", "widget"),
        ("customer/specs/aware.spec.toml", "mismatch", None),
        ("other/widget/aware.spec.toml", "mismatch", None),
        ("customer/specs/a/b/aware.spec.toml", "mismatch", None),
        ("customer/specs/widget/other.toml", "mismatch", None),
    ],
)
def test_original_policy_matches_and_explains_missing_segment(
    tmp_path, target, fit, key
):
    request = prepare(tmp_path, target=target)
    initial = sorted(tmp_path.rglob("*"))
    count = fd_count()
    value = observe(request)
    assert value.fit.value == fit and value.matched_spec_key == key
    assert value.configured_root == "customer/specs"
    assert value.expected_shape == "customer/specs/<spec-key>/aware.spec.toml"
    assert value.cleanup.value == "closed" and value.effect.value == "none"
    assert sorted(tmp_path.rglob("*")) == initial
    assert fd_count() == count


def test_layout_does_not_read_spec_or_check_destination_topology(tmp_path, monkeypatch):
    request = prepare(tmp_path)
    target = tmp_path / TARGET
    target.parent.mkdir(parents=True)
    target.symlink_to("missing-source")

    def forbidden(*_):
        pytest.fail("layout observer called topology/authority selection")

    monkeypatch.setattr(owner, "_selected_topology", forbidden)
    monkeypatch.setattr(owner, "admit_specification_selection", forbidden)
    assert observe(request).fit.value == "match"
    assert target.is_symlink()


@pytest.mark.parametrize(
    "locator", ["aware.protocol.toml", "config/aware.protocol.toml"]
)
def test_nested_and_absolute_protocol_coordinates(tmp_path, locator):
    request = prepare(tmp_path, locator=locator)
    assert observe(request).fit.value == "match"
    assert (
        observe(
            replace(request, protocol_manifest_locator=str(tmp_path / locator))
        ).fit.value
        == "match"
    )


@pytest.mark.parametrize(
    "target",
    [
        "/absolute/aware.spec.toml",
        "../widget/aware.spec.toml",
        "customer//specs/widget/aware.spec.toml",
        "customer/specs/\u0085/aware.spec.toml",
    ],
)
def test_invalid_locator_refuses_before_manifest_open(tmp_path, monkeypatch, target):
    request = prepare(tmp_path, target=target)

    def forbidden(*args, **kwargs):
        pytest.fail("invalid locator reached source acquisition")

    monkeypatch.setattr(implementation.os, "open", forbidden)
    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        observe(request)
    assert caught.value.code == "specification_selection_paths_invalid"
    assert caught.value.cleanup.value == "not_acquired"


@pytest.mark.parametrize("role", ["projection", "unavailable"])
def test_role_unavailability_is_typed_error_not_mismatch(tmp_path, role):
    request = prepare(tmp_path, body=source(role=role))
    count = fd_count()
    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        observe(request)
    assert caught.value.code == "specification_selection_authority_required"
    assert caught.value.evidence.observed_fit is None
    assert caught.value.cleanup.value == "closed" and fd_count() == count


def test_guard_comment_drift_refuses_without_refresh(tmp_path):
    request = prepare(tmp_path)
    manifest = tmp_path / request.protocol_manifest_locator
    manifest.write_text(manifest.read_text() + "\n# byte drift\n")
    count = fd_count()
    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        observe(request)
    assert caught.value.code == "specification_selection_manifest_changed"
    assert caught.value.evidence.request == request
    assert (
        caught.value.evidence.observed_source_sha256 != request.expected_manifest_sha256
    )
    assert caught.value.cleanup.value == "closed" and fd_count() == count


def test_late_byte_drift_cannot_return_match(tmp_path, monkeypatch):
    request = prepare(tmp_path)
    original = implementation.version

    def mutate(name):
        (tmp_path / request.protocol_manifest_locator).write_text(
            source() + "\n# late drift\n"
        )
        return original(name)

    monkeypatch.setattr(implementation, "version", mutate)
    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        observe(request)
    assert caught.value.code == "specification_selection_manifest_changed"
    assert caught.value.evidence.observed_fit.value == "match"
    assert caught.value.cleanup.value == "closed"


def test_original_helper_is_used_by_observer_and_issuer(tmp_path, monkeypatch):
    request = prepare(tmp_path)
    original = owner._specification_binding_layout
    calls = []

    def spy(profile, paths):
        calls.append(paths)
        return original(profile, paths)

    monkeypatch.setattr(owner, "_specification_binding_layout", spy)
    observe(request)
    admitted = owner.admit_specification_selection(
        repository_root=tmp_path,
        manifest_path=Path(request.protocol_manifest_locator),
        selected_manifest_paths=(TARGET,),
        expected_manifest_sha256=request.expected_manifest_sha256,
    )
    owner.release_specification_selection(admitted.selection)
    assert calls == [(), (TARGET,), (TARGET,)]


@pytest.mark.parametrize("error", [OSError, KeyboardInterrupt])
def test_interrupted_read_restores_root_descriptor_and_refuses(
    tmp_path, monkeypatch, error
):
    request = prepare(tmp_path)
    count = fd_count()

    def interrupted(*_):
        raise error("interrupted")

    monkeypatch.setattr(owner, "_manifest_source", interrupted)
    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        observe(request)
    assert caught.value.cleanup.value == "unknown"
    assert caught.value.effect.value == "unknown"
    assert fd_count() == count


def test_original_root_close_failure_never_upgrades_or_retries(tmp_path, monkeypatch):
    request = prepare(tmp_path)
    original_open, original_close = os.open, os.close
    original_descriptor = None
    closes = []

    def opened(path, flags, *args, **kwargs):
        nonlocal original_descriptor
        descriptor = original_open(path, flags, *args, **kwargs)
        if original_descriptor is None:
            original_descriptor = descriptor
        return descriptor

    def closed(descriptor):
        original_close(descriptor)
        if descriptor == original_descriptor:
            closes.append(descriptor)
            raise KeyboardInterrupt("original close acknowledgement interrupted")

    count = fd_count()
    monkeypatch.setattr(implementation.os, "open", opened)
    monkeypatch.setattr(implementation.os, "close", closed)
    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        observe(request)
    assert caught.value.code == "specification_target_fit_cleanup_unverified"
    assert (
        caught.value.cleanup.value == "unknown"
        and caught.value.effect.value == "unknown"
    )
    assert closes == [original_descriptor]
    assert fd_count() == count


def test_file_close_interruption_still_closes_parent_and_root(tmp_path, monkeypatch):
    import stat

    request = prepare(tmp_path)
    original_close = os.close
    interrupted = []
    count = fd_count()

    def closed(descriptor):
        regular = stat.S_ISREG(os.fstat(descriptor).st_mode)
        original_close(descriptor)
        if regular and not interrupted:
            interrupted.append(descriptor)
            raise KeyboardInterrupt("file close acknowledgement interrupted")

    monkeypatch.setattr(owner.os, "close", closed)
    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        observe(request)
    assert caught.value.code == "specification_selection_manifest_cleanup_unverified"
    assert caught.value.cleanup.value == "unknown"
    assert caught.value.effect.value == "unknown"
    assert len(interrupted) == 1 and fd_count() == count


def test_late_result_failure_keeps_closed_observation(tmp_path, monkeypatch):
    request = prepare(tmp_path)
    original = implementation._detached
    count = fd_count()

    def fail_return(value):
        if type(value) is sdk.ProtocolSpecificationTargetFitResult:
            raise KeyboardInterrupt("final snapshot interrupted")
        return original(value)

    monkeypatch.setattr(implementation, "_detached", fail_return)
    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        observe(request)
    assert caught.value.code == "specification_target_fit_result_unverified"
    assert (
        caught.value.cleanup.value == "closed" and caught.value.effect.value == "none"
    )
    assert (
        caught.value.evidence.observed_source_sha256 == request.expected_manifest_sha256
    )
    assert caught.value.evidence.observed_fit.value == "match"
    assert fd_count() == count
