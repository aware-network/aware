"""Real original-reader composition, not operation replay or installed proof."""

import hashlib
import json
import os
import subprocess
import sys
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest
from aware_file_system import confined_mutation as physical
from aware_specification_fs_sdk_adapter import SpecificationFsSavedReceiptProvider
from aware_specification_fs_sdk_adapter import saved_receipt as owner
from aware_specification_sdk import (
    SpecificationSavedReceiptClient,
    SpecificationSavedReceiptError,
    SpecificationSavedReceiptRequest,
)
from packaging.requirements import Requirement


def capture():
    return (
        json.dumps(
            {
                "effect": "none",
                "consumer_completion_verified": False,
                "retained_capability_exported": False,
                "cleanup_evidence": None,
                "input_custody": None,
                "caller_cleanup": {},
                "cleanup_diagnostics": [],
                "protocol_owner_completion": "unknown",
                "error": "historical_refusal",
            },
            indent=2,
        )
        + "\n"
    ).encode()


def request(root, source="receipt.json", content=None, **changes):
    content = capture() if content is None else content
    return replace(
        SpecificationSavedReceiptRequest(
            str(root), source, "sha256:" + hashlib.sha256(content).hexdigest()
        ),
        **changes,
    )


def client():
    return SpecificationSavedReceiptClient(SpecificationFsSavedReceiptProvider())


def descriptors():
    return set(os.listdir("/proc/self/fd"))


@pytest.mark.parametrize("view", ["summary", "full"])
@pytest.mark.parametrize("depth", [0, 2, 63])
def test_original_reader_and_sdk_preserve_bytes_counts_and_no_operation(
    tmp_path, monkeypatch, view, depth
):
    parts = ["d"] * depth
    directory = tmp_path
    for part in parts:
        directory /= part
        directory.mkdir()
    content = capture()
    source = "/".join([*parts, "receipt.json"])
    (directory / "receipt.json").write_bytes(content)
    original = physical.observe_confined_file_with_cleanup
    calls = []

    def read(*, root, path, maximum_bytes):
        calls.append((root, path, maximum_bytes))
        return original(root=root, path=path, maximum_bytes=maximum_bytes)

    monkeypatch.setattr(physical, "observe_confined_file_with_cleanup", read)
    monkeypatch.chdir("/")
    before = descriptors()
    result = client().present_draft_receipt(request(tmp_path, source, view=view))
    assert calls == [(tmp_path, source, 16 * 1024**2)]
    assert bytes.fromhex(result.full_body_hex) == content
    assert result.source.cleanup.acquired_count == depth + 2
    assert result.source.cleanup.release_attempted_count == depth + 2
    assert result.source.cleanup.closed_count == depth + 2
    assert result.operation_invoked is False and result.authorizes_retry is False
    assert result.currentness == "not_revalidated"
    assert result.record == (None if view == "full" else json.loads(content))
    assert (directory / "receipt.json").read_bytes() == content
    assert descriptors() == before


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "missing_parent",
        "directory",
        "fifo",
        "leaf_symlink",
        "parent_symlink",
        "root_alias",
        "large",
        "invalid_json",
        "stale",
    ],
)
def test_real_read_refusals_preserve_guard_and_original_cleanup(tmp_path, kind):
    content = capture()
    source = "receipt.json"
    path = tmp_path / source
    root = tmp_path
    if kind == "missing_parent":
        source = "missing/receipt.json"
    elif kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "leaf_symlink":
        (tmp_path / "other").write_bytes(content)
        path.symlink_to(tmp_path / "other")
    elif kind == "parent_symlink":
        (tmp_path / "other").mkdir()
        (tmp_path / "other/receipt.json").write_bytes(content)
        (tmp_path / "link").symlink_to(tmp_path / "other", target_is_directory=True)
        source = "link/receipt.json"
    elif kind == "root_alias":
        (tmp_path / "real").mkdir()
        (tmp_path / "real/receipt.json").write_bytes(content)
        (tmp_path / "alias").symlink_to(tmp_path / "real", target_is_directory=True)
        root = tmp_path / "alias"
    elif kind == "large":
        path.write_bytes(b"x" * (16 * 1024**2 + 1))
    elif kind == "invalid_json":
        content = b"broken"
        path.write_bytes(content)
    elif kind == "stale":
        path.write_bytes(content + b" ")
    elif kind != "missing":
        path.write_bytes(content)
    original = request(root, source, content)
    before = descriptors()
    with pytest.raises(SpecificationSavedReceiptError) as caught:
        client().present_draft_receipt(original)
    evidence = caught.value.evidence
    assert evidence.request == original
    assert evidence.provider_invoked is True
    assert evidence.effect == "none"
    assert evidence.cleanup == ("not_acquired" if kind == "root_alias" else "closed")
    assert evidence.evidence_grade == "provider_observation"
    assert evidence.operation_invoked is False and evidence.authorizes_retry is False
    if kind in {"invalid_json", "stale"}:
        assert evidence.observed_source is not None
        assert evidence.observed_source.cleanup.closed_count == 2
        assert caught.value.code == (
            "receipt_json_invalid"
            if kind == "invalid_json"
            else "receipt_source_correlation_failed"
        )
    if kind == "stale":
        assert evidence.observed_source.source_sha256 != original.expected_source_sha256
    assert descriptors() == before


@pytest.mark.parametrize("fault", [KeyboardInterrupt, SystemExit, OSError])
def test_original_read_interruption_keeps_primary_and_closed_cleanup(
    tmp_path, monkeypatch, fault
):
    (tmp_path / "receipt.json").write_bytes(capture())
    problem = fault("original interrupted read")

    def stop(*args):
        raise problem

    monkeypatch.setattr(physical.os, "read", stop)
    before = descriptors()
    with pytest.raises(SpecificationSavedReceiptError) as caught:
        client().present_draft_receipt(request(tmp_path))
    assert caught.value.evidence.cleanup == "closed"
    assert caught.value.evidence.effect == "none"
    assert caught.value.__cause__.__cause__.__cause__ is problem
    assert descriptors() == before


@pytest.mark.parametrize("fault", [KeyboardInterrupt, OSError])
def test_original_close_unknown_preserves_observation_without_reclose(
    tmp_path, monkeypatch, fault
):
    content = capture()
    (tmp_path / "receipt.json").write_bytes(content)
    real_close = physical.os.close
    calls = []

    def interrupted(descriptor):
        assert descriptor not in calls
        calls.append(descriptor)
        real_close(descriptor)
        if len(calls) == 1:
            raise fault("unverified close")

    monkeypatch.setattr(physical.os, "close", interrupted)
    before = descriptors()
    with pytest.raises(SpecificationSavedReceiptError) as caught:
        client().present_draft_receipt(request(tmp_path))
    evidence = caught.value.evidence
    assert evidence.cleanup == "unknown" and evidence.effect == "unknown"
    assert (
        evidence.observed_source.source_sha256
        == request(tmp_path).expected_source_sha256
    )
    assert len(calls) == 2
    assert descriptors() == before


@pytest.mark.parametrize("fault", [KeyboardInterrupt, ValueError])
def test_late_presentation_failure_preserves_known_original_read(
    tmp_path, monkeypatch, fault
):
    content = capture()
    (tmp_path / "receipt.json").write_bytes(content)
    problem = fault("late presentation failure")

    def fail(*args, **kwargs):
        raise problem

    monkeypatch.setattr(owner, "present_saved_draft_capture", fail)
    before = descriptors()
    with pytest.raises(SpecificationSavedReceiptError) as caught:
        client().present_draft_receipt(request(tmp_path))
    assert caught.value.evidence.cleanup == "closed"
    assert (
        caught.value.evidence.observed_source.source_sha256
        == request(tmp_path).expected_source_sha256
    )
    assert caught.value.__cause__.__cause__ is problem
    assert descriptors() == before


@pytest.mark.parametrize("fault", ["missing", "signature", "values"])
def test_missing_or_incompatible_integration_refuses_before_open(
    tmp_path, monkeypatch, fault
):
    if fault == "missing":

        def absent(*args):
            raise ImportError("optional owner missing")

        monkeypatch.setattr(owner, "import_module", absent)
    elif fault == "signature":
        monkeypatch.setattr(
            physical, "observe_confined_file_with_cleanup", lambda *args, **kwargs: None
        )
    else:
        monkeypatch.setattr(physical, "ConfinedFileReadCleanup", dict)

    def forbidden(*args, **kwargs):
        pytest.fail("Source was opened despite unavailable integration")

    monkeypatch.setattr(physical.os, "open", forbidden)
    with pytest.raises(SpecificationSavedReceiptError) as caught:
        client().present_draft_receipt(request(tmp_path))
    assert caught.value.code == "receipt_reader_integration_unavailable"
    assert caught.value.evidence.cleanup == "not_acquired"
    assert caught.value.evidence.effect == "none"


@pytest.mark.parametrize(
    "tamper",
    ["dict", "foreign_root", "foreign_path", "digest", "cleanup", "raw_interrupt"],
)
def test_malformed_reader_returns_are_unvalidated_and_never_retried(
    tmp_path, monkeypatch, tamper
):
    (tmp_path / "receipt.json").write_bytes(capture())
    real_read = physical.observe_confined_file_with_cleanup
    calls = []

    def read(*, root, path, maximum_bytes):
        calls.append(path)
        result = real_read(root=root, path=path, maximum_bytes=maximum_bytes)
        if tamper == "dict":
            return {"foreign": "report"}
        if tamper == "raw_interrupt":
            raise KeyboardInterrupt("lost owner return")
        if tamper == "foreign_root":
            return replace(result, root_locator=str(tmp_path / "foreign"))
        if tamper == "foreign_path":
            return replace(
                result,
                path="foreign.json",
                observation=replace(result.observation, path="foreign.json"),
            )
        if tamper == "digest":
            object.__setattr__(
                result.observation, "content_digest", "sha256:" + "0" * 64
            )
        else:
            object.__setattr__(result.cleanup, "closed_count", 0)
        return result

    monkeypatch.setattr(physical, "observe_confined_file_with_cleanup", read)
    before = descriptors()
    with pytest.raises(SpecificationSavedReceiptError) as caught:
        client().present_draft_receipt(request(tmp_path))
    evidence = caught.value.evidence
    assert evidence.evidence_grade == "unvalidated_provider_report"
    assert evidence.cleanup == "unknown" and evidence.effect == "unknown"
    assert evidence.observed_source is None and evidence.authorizes_retry is False
    if tamper == "dict":
        assert evidence.reported_result == {"foreign": "report"}
    assert calls == ["receipt.json"]
    assert descriptors() == before


@pytest.mark.parametrize(
    "tamper",
    ["missing_cleanup", "foreign_root", "foreign_path", "absent_root", "absent_path"],
)
def test_malformed_original_reader_errors_remain_typed_with_primary(
    tmp_path, monkeypatch, tamper
):
    (tmp_path / "receipt.json").write_bytes(capture())
    real_read = physical.observe_confined_file_with_cleanup
    calls = []
    errors = []

    def read(*, root, path, maximum_bytes):
        calls.append(path)
        result = real_read(root=root, path=path, maximum_bytes=maximum_bytes)
        error = physical.ConfinedFileObservationError(
            "original_late_failure",
            stage="result",
            cause_kind="ValueError",
            root_locator=str(root),
            path=path,
            observation=result.observation,
            cleanup=result.cleanup,
        )
        if tamper == "missing_cleanup":
            del error.cleanup
        elif tamper == "foreign_root":
            error.root_locator = str(tmp_path / "foreign")
        elif tamper == "absent_root":
            error.root_locator = None
        elif tamper == "absent_path":
            error.path = None
        else:
            error.path = "foreign.json"
        errors.append(error)
        raise error

    monkeypatch.setattr(physical, "observe_confined_file_with_cleanup", read)
    with pytest.raises(SpecificationSavedReceiptError) as caught:
        client().present_draft_receipt(request(tmp_path))
    assert caught.value.evidence.evidence_grade == "unvalidated_provider_report"
    assert caught.value.__cause__.__cause__ is errors[0]
    assert len(calls) == 1


@pytest.mark.parametrize("view", ["summary", "full"])
@pytest.mark.parametrize("tamper", ["digest", "same_length_content"])
def test_error_source_requires_original_byte_digest_validation(
    tmp_path, monkeypatch, view, tamper
):
    content = capture()
    (tmp_path / "receipt.json").write_bytes(content)
    real_read, real_close = (
        physical.observe_confined_file_with_cleanup,
        physical.os.close,
    )
    calls, closes, errors = [], [], []
    primary = OSError("original late failure")

    def close(descriptor):
        closes.append(descriptor)
        real_close(descriptor)

    def read(*, root, path, maximum_bytes):
        calls.append(path)
        result = real_read(root=root, path=path, maximum_bytes=maximum_bytes)
        error = physical.ConfinedFileObservationError(
            "original_late_failure",
            stage="result",
            cause_kind="OSError",
            root_locator=str(root),
            path=path,
            observation=result.observation,
            cleanup=result.cleanup,
        )
        if tamper == "digest":
            object.__setattr__(
                error.observation, "content_digest", "sha256:" + "0" * 64
            )
        else:
            object.__setattr__(error.observation, "content", b"x" * len(content))
        errors.append(error)
        raise error from primary

    monkeypatch.setattr(physical.os, "close", close)
    monkeypatch.setattr(physical, "observe_confined_file_with_cleanup", read)
    before = descriptors()
    with pytest.raises(SpecificationSavedReceiptError) as caught:
        client().present_draft_receipt(request(tmp_path, view=view))
    evidence = caught.value.evidence
    assert evidence.evidence_grade == "unvalidated_provider_report"
    assert evidence.observed_source is None
    assert evidence.cleanup == "unknown" and evidence.effect == "unknown"
    assert evidence.authorizes_retry is False and evidence.operation_invoked is False
    assert caught.value.__cause__.__cause__ is errors[0]
    assert errors[0].__cause__ is primary
    assert calls == ["receipt.json"] and len(closes) == len(set(closes)) == 2
    assert descriptors() == before
    assert (tmp_path / "receipt.json").read_bytes() == content


@pytest.mark.parametrize("fault", [KeyboardInterrupt, ValueError])
def test_error_source_validation_failure_keeps_original_cause_without_reclose(
    tmp_path, monkeypatch, fault
):
    content = capture()
    (tmp_path / "receipt.json").write_bytes(content)
    real_read = physical.observe_confined_file_with_cleanup
    errors, calls = [], []
    primary = OSError("primary late read failure")

    def validation_failure(*args):
        raise fault("retained byte validation interrupted")

    def read(*, root, path, maximum_bytes):
        calls.append(path)
        result = real_read(root=root, path=path, maximum_bytes=maximum_bytes)
        error = physical.ConfinedFileObservationError(
            "original_late_failure",
            stage="result",
            cause_kind="OSError",
            root_locator=str(root),
            path=path,
            observation=result.observation,
            cleanup=result.cleanup,
        )
        monkeypatch.setattr(physical, "_content_digest", validation_failure)
        errors.append(error)
        raise error from primary

    monkeypatch.setattr(physical, "observe_confined_file_with_cleanup", read)
    before = descriptors()
    with pytest.raises(SpecificationSavedReceiptError) as caught:
        client().present_draft_receipt(request(tmp_path))
    assert caught.value.evidence.evidence_grade == "unvalidated_provider_report"
    assert caught.value.evidence.observed_source is None
    assert caught.value.evidence.cleanup == "unknown"
    assert caught.value.__cause__.__cause__ is errors[0]
    assert errors[0].__cause__ is primary
    assert len(calls) == 1 and descriptors() == before


@pytest.mark.parametrize("stale", [False, True])
def test_genuine_late_error_source_is_valid_even_when_different_from_request_guard(
    tmp_path, monkeypatch, stale
):
    content = capture() + (b" " if stale else b"")
    (tmp_path / "receipt.json").write_bytes(content)
    real_read = physical.observe_confined_file_with_cleanup
    errors = []
    primary = OSError("original late failure")

    def read(*, root, path, maximum_bytes):
        result = real_read(root=root, path=path, maximum_bytes=maximum_bytes)
        error = physical.ConfinedFileObservationError(
            "original_late_failure",
            stage="result",
            cause_kind="OSError",
            root_locator=str(root),
            path=path,
            observation=result.observation,
            cleanup=result.cleanup,
        )
        errors.append(error)
        raise error from primary

    monkeypatch.setattr(physical, "observe_confined_file_with_cleanup", read)
    original = request(tmp_path)
    before = descriptors()
    with pytest.raises(SpecificationSavedReceiptError) as caught:
        client().present_draft_receipt(original)
    evidence = caught.value.evidence
    assert evidence.evidence_grade == "provider_observation"
    assert (
        evidence.observed_source.source_sha256
        == "sha256:" + hashlib.sha256(content).hexdigest()
    )
    assert (
        evidence.observed_source.source_sha256 != original.expected_source_sha256
    ) is stale
    assert (
        evidence.cleanup == "closed"
        and evidence.observed_source.cleanup.closed_count == 2
    )
    assert caught.value.code == "original_late_failure"
    assert (
        caught.value.__cause__.__cause__ is errors[0] and errors[0].__cause__ is primary
    )
    assert descriptors() == before


def test_facade_stays_optional_with_missing_physical_and_writer_owners():
    script = """
import importlib.abc, sys
class Deny(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'aware_file_system','aware_issue_sdk','aware_issue_fs_adapter','aware_protocol_fs_adapter'}:
            raise ImportError('optional_owner_forbidden:'+fullname)
sys.meta_path.insert(0,Deny())
from aware_specification_fs_sdk_adapter import SpecificationFsSavedReceiptProvider
from aware_specification_sdk import SpecificationSavedReceiptClient, SpecificationSavedReceiptRequest, SpecificationSavedReceiptError
try:
    SpecificationSavedReceiptClient(SpecificationFsSavedReceiptProvider()).present_draft_receipt(
        SpecificationSavedReceiptRequest('/explicit/root','capture.json','sha256:'+'1'*64))
except SpecificationSavedReceiptError as error:
    assert error.code=='receipt_reader_integration_unavailable'
    assert error.evidence.cleanup=='not_acquired'
else:
    raise AssertionError('Missing owner became success')
"""
    subprocess.run([sys.executable, "-B", "-c", script], check=True, timeout=20)


@pytest.mark.parametrize("view", ["summary", "full"])
def test_untouched_accepted_recovery_capture_through_real_reader(view):
    coordinate = os.environ.get("AWARE_SAVED_RECEIPT_ACCEPTED_R_CAPTURE")
    assert coordinate, "Supply the accepted r27 capture explicitly"
    path = Path(coordinate)
    content = path.read_bytes()
    assert len(content) == 121484
    assert (
        hashlib.sha256(content).hexdigest()
        == "5b82f485682523d9afd8aa105dd0f7da7a5a66d7ec21de7b1fcd10a2ecc33007"
    )
    before = descriptors()
    result = client().present_draft_receipt(
        request(path.parent, path.name, content, view=view)
    )
    assert bytes.fromhex(result.full_body_hex) == content
    assert result.source.cleanup.closed_count == 2
    if view == "summary":
        assert (
            result.record["input_custody"]["physical_evidence"]["ledger_complete"]
            is True
        )
    else:
        assert result.record is None
    assert path.read_bytes() == content
    assert descriptors() == before


@pytest.mark.parametrize("fault", [KeyboardInterrupt, ValueError])
def test_direct_provider_snapshot_failure_is_local_without_dispatch(
    tmp_path, monkeypatch, fault
):
    original = request(tmp_path)

    def stop(*args, **kwargs):
        raise fault("snapshot interrupted")

    monkeypatch.setattr(owner, "replace", stop)
    monkeypatch.setattr(
        owner, "_reader", lambda: pytest.fail("Reader loaded after failed snapshot")
    )
    with pytest.raises(SpecificationSavedReceiptError) as caught:
        SpecificationFsSavedReceiptProvider().present_draft_receipt(original)
    assert caught.value.evidence.provider_invoked is False
    assert caught.value.evidence.cleanup == "not_acquired"
    assert caught.value.evidence.effect == "none"
    assert caught.value.evidence.evidence_grade == "local_not_observed"


def test_caller_mutation_during_original_read_cannot_refresh_guard(
    tmp_path, monkeypatch
):
    content = capture()
    (tmp_path / "receipt.json").write_bytes(content)
    original = request(tmp_path)
    expected = replace(original)
    read = physical.observe_confined_file_with_cleanup

    def mutate(*, root, path, maximum_bytes):
        object.__setattr__(original, "expected_source_sha256", "sha256:" + "0" * 64)
        object.__setattr__(original, "source_ref", "foreign.json")
        return read(root=root, path=path, maximum_bytes=maximum_bytes)

    monkeypatch.setattr(physical, "observe_confined_file_with_cleanup", mutate)
    result = client().present_draft_receipt(original)
    assert result.request == expected and bytes.fromhex(result.full_body_hex) == content


def test_sixteen_original_cleanup_diagnostics_are_not_lost_or_promoted(
    tmp_path, monkeypatch
):
    (tmp_path / "receipt.json").write_bytes(capture())
    read = physical.observe_confined_file_with_cleanup
    diagnostics = tuple("original_unknown_close:" + str(i) for i in range(16))

    def fail(*, root, path, maximum_bytes):
        result = read(root=root, path=path, maximum_bytes=maximum_bytes)
        cleanup = physical.ConfinedFileReadCleanup("unknown", 2, 2, None, diagnostics)
        raise physical.ConfinedFileObservationError(
            "filesystem_read_cleanup_unverified",
            stage="cleanup",
            cause_kind="OSError",
            root_locator=str(root),
            path=path,
            observation=result.observation,
            cleanup=cleanup,
        )

    monkeypatch.setattr(physical, "observe_confined_file_with_cleanup", fail)
    with pytest.raises(SpecificationSavedReceiptError) as caught:
        client().present_draft_receipt(request(tmp_path))
    evidence = caught.value.evidence
    assert evidence.evidence_grade == "provider_observation"
    assert evidence.cleanup == "unknown" and evidence.effect == "unknown"
    assert evidence.diagnostics == diagnostics
    assert evidence.observed_source.cleanup.diagnostics == diagnostics
    assert evidence.observed_source.cleanup.closed_count is None


@pytest.mark.parametrize("size", [0, 65536, 16 * 1024**2])
def test_original_byte_bound_is_not_truncation(tmp_path, size):
    content = b"" if size == 0 else capture() + b" " * (size - len(capture()))
    (tmp_path / "receipt.json").write_bytes(content)
    before = descriptors()
    if size == 0:
        with pytest.raises(SpecificationSavedReceiptError) as caught:
            client().present_draft_receipt(request(tmp_path, content=content))
        assert caught.value.evidence.observed_source.byte_count == 0
    else:
        result = client().present_draft_receipt(
            request(tmp_path, content=content, view="full")
        )
        assert bytes.fromhex(result.full_body_hex) == content
        assert result.source.byte_count == size
    assert descriptors() == before


@pytest.mark.parametrize(
    "version, admitted",
    [("0.3.5", False), ("0.3.6", True), ("0.3.99", True), ("0.4.0", False)],
)
def test_finite_receipts_extra_preserves_default_and_governed_edges(version, admitted):
    metadata = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()
    )
    assert metadata["project"]["version"] == "0.4.4"
    assert metadata["project"]["dependencies"] == [
        "aware-specification-sdk>=0.3.4,<0.4.0",
        "aware-specification-fs-adapter",
    ]
    extra = metadata["project"]["optional-dependencies"]["receipts"]
    assert extra == ["aware-file-system>=0.3.6,<0.4.0"]
    assert (version in Requirement(extra[0]).specifier) is admitted
    assert (
        "aware-file-system>=0.3.1,<0.4.0"
        in metadata["project"]["optional-dependencies"]["governed"]
    )
