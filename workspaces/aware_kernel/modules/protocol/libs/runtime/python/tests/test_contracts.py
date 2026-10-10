from __future__ import annotations

import pytest

from aware_protocol_runtime import (
    ProtocolAdmissionOutcomeKind,
    ProtocolAdmissionResult,
    ProtocolAuthorityMode,
    ProtocolBootstrap,
    ProtocolContractError,
    ProtocolIdentity,
    ProtocolManifest,
    ProtocolRecordBinding,
    ProtocolRecordRole,
    ProtocolTarget,
    ProtocolTargetKind,
)


def _manifest() -> ProtocolManifest:
    return ProtocolManifest.from_mapping(
        protocol=ProtocolIdentity(
            name="aware.collaboration",
            profile="aware.collaboration.fs_v1",
            semantic_version=1,
        ),
        target=ProtocolTarget(
            kind=ProtocolTargetKind.REPOSITORY,
            authority_mode=ProtocolAuthorityMode.FILESYSTEM,
        ),
        bootstrap=ProtocolBootstrap(agent_contract_ref="repository:AGENTS.md"),
        records={
            "goal": ProtocolRecordBinding(
                record_key="goal",
                profile="aware.goal.markdown.v1",
                role=ProtocolRecordRole.AUTHORITY,
            ),
            "feed": ProtocolRecordBinding(
                record_key="feed",
                profile="aware.feed.projection.v1",
                role=ProtocolRecordRole.UNAVAILABLE,
            ),
        },
    )


def test_manifest_is_stable_and_representation_neutral() -> None:
    manifest = _manifest()
    assert manifest.target.authority_mode is ProtocolAuthorityMode.FILESYSTEM
    assert tuple(item.record_key for item in manifest.records) == ("feed", "goal")
    assert manifest.digest.startswith("sha256:")
    assert manifest.to_wire()["records"]["feed"] == {
        "profile": "aware.feed.projection.v1",
        "role": "unavailable",
    }
    assert "root" not in str(manifest.to_wire())
    assert "path_template" not in str(manifest.to_wire())


def test_service_target_requires_explicit_authority_ref() -> None:
    with pytest.raises(ProtocolContractError, match="requires authority_ref"):
        ProtocolTarget(
            kind=ProtocolTargetKind.REPOSITORY,
            authority_mode=ProtocolAuthorityMode.SERVICE_API,
        )


def test_filesystem_location_is_not_a_neutral_record_field() -> None:
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        ProtocolRecordBinding(
            record_key="goal",
            profile="aware.goal.markdown.v1",
            role=ProtocolRecordRole.AUTHORITY,
            root="docs/goals",  # type: ignore[call-arg]
        )


def test_manifest_defensively_freezes_caller_owned_records() -> None:
    records = [
        ProtocolRecordBinding(
            record_key="goal",
            profile="aware.goal.markdown.v1",
            role=ProtocolRecordRole.AUTHORITY,
        )
    ]
    manifest = ProtocolManifest(
        protocol=ProtocolIdentity(
            name="aware.collaboration",
            profile="aware.collaboration.fs_v1",
            semantic_version=1,
        ),
        target=ProtocolTarget(
            kind=ProtocolTargetKind.REPOSITORY,
            authority_mode=ProtocolAuthorityMode.FILESYSTEM,
        ),
        bootstrap=ProtocolBootstrap(agent_contract_ref="repository:AGENTS.md"),
        records=records,  # type: ignore[arg-type]
    )
    digest = manifest.digest

    records.append(
        ProtocolRecordBinding(
            record_key="goal",
            profile="aware.goal.markdown.v1",
            role=ProtocolRecordRole.UNAVAILABLE,
        )
    )

    assert type(manifest.records) is tuple
    assert len(manifest.records) == 1
    assert manifest.digest == digest


def test_admission_defensively_freezes_diagnostics() -> None:
    diagnostics: list[str] = []
    result = ProtocolAdmissionResult(
        outcome=ProtocolAdmissionOutcomeKind.CANONICAL_V1,
        source_sha256=f"sha256:{'0' * 64}",
        manifest=_manifest(),
        diagnostics=diagnostics,  # type: ignore[arg-type]
    )

    diagnostics.append("late_mutation")

    assert result.diagnostics == ()


def test_admission_rejects_wrong_nested_manifest_type() -> None:
    with pytest.raises(ProtocolContractError, match="manifest must be"):
        ProtocolAdmissionResult(
            outcome=ProtocolAdmissionOutcomeKind.CANONICAL_V1,
            source_sha256=f"sha256:{'0' * 64}",
            manifest="not-a-manifest",  # type: ignore[arg-type]
        )


def test_pre_read_refusal_can_honestly_omit_source_digest() -> None:
    result = ProtocolAdmissionResult(
        outcome=ProtocolAdmissionOutcomeKind.SOURCE_UNAVAILABLE,
        source_sha256=None,
        diagnostics=("manifest_missing",),
    )

    assert result.to_wire()["source_sha256"] is None


def test_canonical_admission_requires_source_digest() -> None:
    with pytest.raises(ProtocolContractError, match="requires source digest"):
        ProtocolAdmissionResult(
            outcome=ProtocolAdmissionOutcomeKind.CANONICAL_V1,
            source_sha256=None,
            manifest=_manifest(),
        )
