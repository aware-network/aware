from __future__ import annotations

import hashlib
import json
import os
import signal
from dataclasses import replace
from pathlib import Path

import pytest
from aware_workspace_runtime.operational_validation import (
    OperationalValidationError,
    OperationalValidationPlan,
    OperationalValidationProfile,
    OperationalValidationReceipt,
    OperationalValidationSourceSelection,
    OperationalValidationSuite,
    OperationalValidationSuiteReceipt,
    SourcePackageCoordinate,
    ValidationCurrentnessPolicy,
    ValidationEffectClass,
    ValidationExecutionStatus,
    WorkspaceValidationSourceCoordinate,
    read_retained_validation_chunk,
    validate_test_resource_outcome,
)


def _sha(character: str) -> str:
    return "sha256:" + character * 64


def _retained_member(observer, handle, name="plain.bin"):
    evidence = observer.evidence(handle)
    body = next(row for row in evidence.bodies if row.relative_path == name)
    payload = {
        "relative_path": str(Path(evidence.root_relative_path) / body.relative_path),
        "body_ref": body.body_ref,
        "content_digest": body.content_digest,
        "size_bytes": body.size_bytes,
    }
    return (
        "platform-source-member:sha256:"
        + hashlib.sha256(
            json.dumps(
                payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
            + b"\n"
        ).hexdigest()
    )


async def test_original_retained_chunks_rebuild_exact_bytes_not_checkout(tmp_path):
    from test_source_observation import runtime

    original = b"captured" * 12289
    async with runtime(tmp_path) as (observer, _, _, package):
        (package / "plain.bin").write_bytes(original)
        handle = observer.observe(root_relative_path="package")
        member = _retained_member(observer, handle)
        (package / "plain.bin").write_bytes(b"different checkout")
        parts = []
        offset = 0
        while offset < len(original):
            chunk = read_retained_validation_chunk(
                observer, handle, member_ref=member, offset_bytes=offset
            )
            assert (
                chunk.chunk_digest == "sha256:" + hashlib.sha256(chunk.data).hexdigest()
            )
            assert (
                chunk.member_digest == "sha256:" + hashlib.sha256(original).hexdigest()
            )
            assert chunk.relative_path == "package/plain.bin"
            assert chunk == read_retained_validation_chunk(
                observer, handle, member_ref=member, offset_bytes=offset
            )
            assert not hasattr(chunk, "allocation_ref") and not hasattr(
                chunk, "authorization_ref"
            )
            parts.append(chunk.data)
            offset = chunk.next_offset_bytes
        assert chunk.member_complete and b"".join(parts) == original


async def test_original_empty_retained_member_has_one_exact_chunk(tmp_path):
    from test_source_observation import runtime

    async with runtime(tmp_path) as (observer, _, _, package):
        (package / "plain.bin").write_bytes(b"")
        handle = observer.observe(root_relative_path="package")
        chunk = read_retained_validation_chunk(
            observer,
            handle,
            member_ref=_retained_member(observer, handle),
            offset_bytes=0,
        )
        assert chunk.data == b"" and chunk.member_complete
        assert chunk.next_offset_bytes == 0


@pytest.mark.parametrize("offset", [-1, True, 1, 6, 32768])
async def test_retained_chunk_rejects_invalid_offsets(tmp_path, offset):
    from test_source_observation import runtime

    async with runtime(tmp_path) as (observer, _, _, _):
        handle = observer.observe(root_relative_path="package")
        with pytest.raises(OperationalValidationError):
            read_retained_validation_chunk(
                observer,
                handle,
                member_ref=_retained_member(observer, handle),
                offset_bytes=offset,
            )


@pytest.mark.parametrize(
    "member", ["file:/tmp/private", "platform-source-member:" + _sha("a")]
)
async def test_retained_chunk_rejects_foreign_member_or_path(tmp_path, member):
    from test_source_observation import runtime

    async with runtime(tmp_path) as (observer, _, _, _):
        handle = observer.observe(root_relative_path="package")
        with pytest.raises(OperationalValidationError, match="member_unavailable"):
            read_retained_validation_chunk(
                observer, handle, member_ref=member, offset_bytes=0
            )


async def test_retained_chunk_rejects_foreign_handle_owner_and_epoch(tmp_path):
    from aware_workspace_runtime import (
        SourceObservationUnavailable,
        WorkspaceSourceObservationRuntime,
    )
    from test_source_observation import runtime

    async with runtime(tmp_path) as (observer, session, store, _):
        handle = observer.observe(root_relative_path="package")
        member = _retained_member(observer, handle)
        other = WorkspaceSourceObservationRuntime(session=session, store=store)
        try:
            with pytest.raises(SourceObservationUnavailable):
                read_retained_validation_chunk(
                    other, handle, member_ref=member, offset_bytes=0
                )
        finally:
            other.close()
        await session.stop()
        await session.start(background=False)
        with pytest.raises(SourceObservationUnavailable):
            read_retained_validation_chunk(
                observer, handle, member_ref=member, offset_bytes=0
            )


async def test_retained_chunk_rejects_lost_body_without_recapture(tmp_path):
    from aware_workspace_runtime import SourceObservationUnavailable
    from test_source_observation import runtime

    async with runtime(tmp_path, capacity=2) as (observer, _, store, package):
        handle = observer.observe(root_relative_path="package")
        member = _retained_member(observer, handle)
        store.record_bodies((b"evict-one", b"evict-two"))
        with pytest.raises(SourceObservationUnavailable):
            read_retained_validation_chunk(
                observer, handle, member_ref=member, offset_bytes=0
            )
        assert (package / "plain.bin").read_bytes() == b"initial"


async def test_retained_chunk_bypasses_caller_instance_reader_callback(
    tmp_path, monkeypatch
):
    from test_source_observation import runtime

    async with runtime(tmp_path) as (observer, _, _, _):
        handle = observer.observe(root_relative_path="package")
        member = _retained_member(observer, handle)
        monkeypatch.setattr(
            observer, "read", lambda *a, **k: pytest.fail("caller callback used")
        )
        chunk = read_retained_validation_chunk(
            observer, handle, member_ref=member, offset_bytes=0
        )
        assert chunk.data == b"initial"


def test_retained_chunk_rejects_fake_reader_before_effect():
    with pytest.raises(OperationalValidationError):
        read_retained_validation_chunk(
            {}, object(), member_ref="foreign", offset_bytes=0
        )


async def test_retained_chunk_fork_rejects_before_inherited_lock(tmp_path):
    from test_source_observation import runtime

    async with runtime(tmp_path) as (observer, _, _, _):
        handle = observer.observe(root_relative_path="package")
        member = _retained_member(observer, handle)
        with observer._lock:
            pid = os.fork()
            if pid == 0:
                signal.alarm(2)
                try:
                    read_retained_validation_chunk(
                        observer, handle, member_ref=member, offset_bytes=0
                    )
                except OperationalValidationError as error:
                    os._exit(
                        0 if str(error) == "retained_chunk_owner_unavailable" else 2
                    )
                except Exception:  # noqa: BLE001 -- child must exit, not resume pytest
                    os._exit(3)
                os._exit(4)
            _, status = os.waitpid(pid, 0)  # noqa: ASYNC222 -- bounded two-second child
            assert os.waitstatus_to_exitcode(status) == 0
        assert (
            read_retained_validation_chunk(
                observer, handle, member_ref=member, offset_bytes=0
            ).data
            == b"initial"
        )


async def test_retained_chunk_refuses_oversized_original_capture(tmp_path, monkeypatch):
    from aware_workspace_runtime import (
        SourceObservationLimits,
        WorkspaceSourceObservationRuntime,
    )
    from test_source_observation import runtime

    async with runtime(
        tmp_path, limits=SourceObservationLimits(maximum_body_bytes=16 * 1024 * 1024)
    ) as (observer, _, _, package):
        (package / "plain.bin").write_bytes(b"x" * (8 * 1024 * 1024 + 1))
        handle = observer.observe(root_relative_path="package")
        member = _retained_member(observer, handle)
        monkeypatch.setattr(
            WorkspaceSourceObservationRuntime,
            "read",
            lambda *a, **k: pytest.fail("oversized body read"),
        )
        with pytest.raises(OperationalValidationError, match="capture_limit"):
            read_retained_validation_chunk(
                observer, handle, member_ref=member, offset_bytes=0
            )


async def test_retained_chunk_revalidates_exact_small_member_on_construction(tmp_path):
    from test_source_observation import runtime

    async with runtime(tmp_path) as (observer, _, _, _):
        handle = observer.observe(root_relative_path="package")
        chunk = read_retained_validation_chunk(
            observer,
            handle,
            member_ref=_retained_member(observer, handle),
            offset_bytes=0,
        )
        with pytest.raises(OperationalValidationError, match="member_mismatch"):
            replace(chunk, data=b"altered")
        with pytest.raises(OperationalValidationError):
            replace(chunk, total_size_bytes=True)


def _resource(output: str = "1 passed") -> dict[str, object]:
    size = len(output.encode())
    return {
        "contract": "aware.code.test-resource-outcome.v1",
        "capture_status": "complete",
        "capture_limit_bytes": 4000,
        "stdout_observed_bytes": size,
        "stderr_observed_bytes": 0,
        "stdout_retained_bytes": size,
        "stderr_retained_bytes": 0,
        "stdout_dropped_bytes": 0,
        "stderr_dropped_bytes": 0,
        "output_tail_bytes": size,
        "output_tail_digest": "sha256:" + hashlib.sha256(output.encode()).hexdigest(),
        "cleanup_status": "cleanup_pending",
        "cleanup_reason": "writer_exclusion_unavailable",
        "allocation_status": "unadmitted_compatibility_scratch",
        "retention_status": "retained_pending",
        "diagnostic_code": None,
    }


def _profile() -> OperationalValidationProfile:
    return OperationalValidationProfile(
        key="agent-operational-core",
        revision="v1",
        suites=(
            OperationalValidationSuite(
                key="first-person-governance",
                project_root=".",
                interpreter_path=".venv/bin/python",
                test_paths=("tests/test_first_person.py",),
                effect_class=ValidationEffectClass.TEMPORARY_FILESYSTEM,
                timeout_seconds=30,
            ),
        ),
        lock_paths=("uv.lock",),
        currentness_policy=ValidationCurrentnessPolicy.AUTHORED_COMPLETE_SELECTION,
        source_selections=(
            OperationalValidationSourceSelection(
                key="root",
                package_root=".",
                manifest_path="pyproject.toml",
                language_key="python",
                toolchain_key="uv-pytest",
                source_paths=("tests/test_first_person.py",),
                test_paths=("tests/test_first_person.py",),
            ),
        ),
    )


def _plan() -> OperationalValidationPlan:
    return OperationalValidationPlan(
        source=WorkspaceValidationSourceCoordinate(
            repository_binding_ref="local-root:test",
            epoch="epoch-1",
            cursor=4,
            snapshot_digest=_sha("a"),
        ),
        profile=_profile(),
        selected_source_digests=(
            ("pyproject.toml", _sha("e")),
            ("tests/test_first_person.py", _sha("f")),
            ("uv.lock", _sha("b")),
        ),
        package_coordinates=(
            SourcePackageCoordinate(
                package_root=".",
                manifest_path="pyproject.toml",
                manifest_digest=_sha("e"),
                language_key="python",
                toolchain_key="uv-pytest",
            ),
        ),
        lock_digests=(("uv.lock", _sha("b")),),
        runner_fingerprint=_sha("c"),
        environment_fingerprint=_sha("d"),
    )


def test_plan_identity_is_stable_and_source_bound() -> None:
    first = _plan()
    replay = _plan()

    assert replay.plan_ref == first.plan_ref
    assert replay.plan_digest == first.plan_digest
    assert first.to_payload()["source"] == {
        "repository_binding_ref": "local-root:test",
        "epoch": "epoch-1",
        "cursor": 4,
        "snapshot_digest": _sha("a"),
    }


def test_currentness_policy_requires_explicit_complete_selection() -> None:
    selected = _plan()
    full_repository = replace(
        selected,
        profile=replace(
            selected.profile,
            currentness_policy=ValidationCurrentnessPolicy.FULL_REPOSITORY,
        ),
    )

    assert selected.currentness_state_digest == selected.selection_state_digest
    assert full_repository.currentness_state_digest == selected.source.snapshot_digest


def test_source_package_coordinate_does_not_claim_canonical_identity() -> None:
    coordinate = SourcePackageCoordinate(
        package_root="workspaces/example",
        manifest_path="workspaces/example/pyproject.toml",
        manifest_digest=_sha("e"),
        language_key="python",
        toolchain_key="uv",
    )

    assert coordinate.to_payload()["canonical_code_package_ref"] is None


def test_authored_selection_is_exact_and_package_confined() -> None:
    selection = _profile().source_selections[0]

    assert selection.selection_digest.startswith("sha256:")
    assert _profile().source_paths == ("tests/test_first_person.py",)
    with pytest.raises(OperationalValidationError, match="package_root"):
        OperationalValidationSourceSelection(
            key="escaped",
            package_root="workspaces/example",
            manifest_path="workspaces/example/pyproject.toml",
            language_key="python",
            toolchain_key="uv-pytest",
            source_paths=("outside/test.py",),
            test_paths=("outside/test.py",),
        )


def test_receipt_retains_plan_and_atomic_suite_truth() -> None:
    plan = _plan()
    receipt = OperationalValidationReceipt(
        plan=plan,
        status=ValidationExecutionStatus.PASSED,
        suite_receipts=(
            OperationalValidationSuiteReceipt(
                suite_key="first-person-governance",
                status=ValidationExecutionStatus.PASSED,
                command=plan.profile.suites[0].command,
                exit_code=0,
                duration_ms=12,
                output_tail="1 passed",
            ),
        ),
        completed_source=plan.source,
        completed_currentness_state_digest=plan.currentness_state_digest,
        started_at="2026-08-27T00:00:00+00:00",
        completed_at="2026-08-27T00:00:01+00:00",
        worker_generation_ref="validation-worker:test",
    )

    assert receipt.receipt_ref.startswith("validation-receipt:sha256:")
    assert receipt.to_payload()["plan_digest"] == plan.plan_digest
    assert receipt.to_payload()["profile_revision"] == plan.profile.revision
    assert receipt.to_payload()["profile_digest"] == plan.profile.profile_digest
    assert receipt.to_payload()["suites"] == [
        suite.to_payload() for suite in plan.profile.suites
    ]
    assert receipt.to_payload()["package_coordinates"] == [
        coordinate.to_payload() for coordinate in plan.package_coordinates
    ]
    assert receipt.to_payload()["runner_fingerprint"] == plan.runner_fingerprint
    assert receipt.to_payload()["environment_fingerprint"] == (
        plan.environment_fingerprint
    )


def test_contract_rejects_mismatched_lock_or_suite_receipts() -> None:
    with pytest.raises(OperationalValidationError, match="lock digests"):
        OperationalValidationPlan(
            source=_plan().source,
            profile=_profile(),
            selected_source_digests=_plan().selected_source_digests,
            package_coordinates=_plan().package_coordinates,
            lock_digests=(("other.lock", _sha("f")),),
            runner_fingerprint=_sha("c"),
            environment_fingerprint=_sha("d"),
        )


def test_contract_module_has_no_ontology_or_orm_dependency() -> None:
    source = (
        Path(__file__).parents[1]
        / "aware_workspace_runtime"
        / "operational_validation.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "aware_orm",
        "aware_meta",
        "aware_code_ontology",
        "aware_workspace_ontology",
    ):
        assert f"import {forbidden}" not in source
        assert f"from {forbidden}" not in source


def test_resource_extension_changes_receipt_identity_but_legacy_is_absent() -> None:
    plan = _plan()
    suite = OperationalValidationSuiteReceipt(
        suite_key=plan.profile.suites[0].key,
        status=ValidationExecutionStatus.PASSED,
        command=plan.profile.suites[0].command,
        exit_code=0,
        duration_ms=1,
        output_tail="1 passed",
    )
    legacy = OperationalValidationReceipt(
        plan=plan,
        status=ValidationExecutionStatus.PASSED,
        suite_receipts=(suite,),
        completed_source=plan.source,
        completed_currentness_state_digest=plan.currentness_state_digest,
        started_at="2026-10-05T00:00:00+00:00",
        completed_at="2026-10-05T00:00:01+00:00",
        worker_generation_ref="validation-worker:test",
    )
    observed = replace(
        legacy, suite_receipts=(replace(suite, resource_outcome=_resource()),)
    )
    assert suite.resource_outcome_posture == "resource_outcome_unobserved"
    assert "resource_outcome" not in suite.to_payload()
    assert legacy.receipt_ref == replace(legacy).receipt_ref
    # Reproduced with the byte-exact pre-extension contract at ffc115690383.
    assert legacy.receipt_ref == (
        "validation-receipt:sha256:"
        "6796b255c5c4d43cbd289f24c8606a9cd57e8c2ebfb3c6926c3cb2845b5e9587"
    )
    assert observed.receipt_ref != legacy.receipt_ref
    assert (
        OperationalValidationReceipt.validate_payload_identity(
            legacy.to_payload(), expected_ref=legacy.receipt_ref
        )
        == legacy.receipt_ref
    )
    assert (
        OperationalValidationReceipt.validate_payload_identity(
            observed.to_payload(), expected_ref=observed.receipt_ref
        )
        == observed.receipt_ref
    )
    substituted = observed.to_payload()
    substituted["suite_receipts"][0].pop("resource_outcome")
    with pytest.raises(OperationalValidationError, match="identity_mismatch"):
        OperationalValidationReceipt.validate_payload_identity(
            substituted, expected_ref=observed.receipt_ref
        )
    substituted = observed.to_payload()
    substituted["suite_receipts"][0]["resource_outcome"]["cleanup_reason"] = (
        "termination_unconfirmed"
    )
    with pytest.raises(OperationalValidationError, match="identity_mismatch"):
        OperationalValidationReceipt.validate_payload_identity(
            substituted, expected_ref=observed.receipt_ref
        )
    assert observed.suite_receipts[0].to_payload()["resource_outcome"] == _resource()
    changed = _resource()
    changed["cleanup_reason"] = "termination_unconfirmed"
    assert (
        replace(
            observed, suite_receipts=(replace(suite, resource_outcome=changed),)
        ).receipt_ref
        != observed.receipt_ref
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("stdout_observed_bytes", True),
        ("stderr_dropped_bytes", -1),
        ("stdout_observed_bytes", 2**63),
        ("cleanup_status", "cleanup_succeeded"),
        ("output_tail_digest", "sha256:" + "A" * 64),
        ("stdout_dropped_bytes", 1),
        ("capture_status", []),
    ],
)
def test_resource_codec_rejects_malformed_portable_evidence(
    field: str, value: object
) -> None:
    resource = _resource()
    resource[field] = value
    with pytest.raises(OperationalValidationError):
        validate_test_resource_outcome(resource, "1 passed")


def test_resource_public_encoder_revalidates_mutated_extension() -> None:
    suite = OperationalValidationSuiteReceipt(
        suite_key="test",
        status=ValidationExecutionStatus.PASSED,
        command=("python",),
        exit_code=0,
        duration_ms=1,
        output_tail="1 passed",
        resource_outcome=_resource(),
    )
    assert isinstance(suite.resource_outcome, dict)
    suite.resource_outcome["cleanup_status"] = "retired"
    with pytest.raises(OperationalValidationError):
        suite.to_payload()
