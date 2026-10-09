from __future__ import annotations

from pathlib import Path

from aware_protocol_fs_adapter import FilesystemProtocolSdkProvider
from aware_protocol_runtime import (
    ProtocolAdmissionOutcomeKind,
    ProtocolAuthorityMode,
)
from aware_protocol_sdk import ProtocolSdkClient, ProtocolTargetAdmissionRequest


def _manifest() -> str:
    return """aware = 1

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
root = "docs/goals"
role = "authority"
path_template = "YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md"

[records.issue]
profile = "aware.issue.markdown.v1"
root = "docs/issues"
role = "authority"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"

[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"

[records.specification]
profile = "specification_fs_v1"
root = "docs/specs"
role = "authority"
path_template = "<spec-key>/aware.spec.toml"

[records.evidence]
profile = "aware.protocol.evidence.v1"
root = "docs/coordination/evidence"
role = "authority"
path_template = "<kind>/<stable-id>.json"
"""


def test_sdk_provider_calls_existing_filesystem_admission(tmp_path: Path) -> None:
    (tmp_path / "aware.protocol.toml").write_text(_manifest(), encoding="utf-8")

    result = ProtocolSdkClient(provider=FilesystemProtocolSdkProvider()).admit_target(
        ProtocolTargetAdmissionRequest(
            authority_mode=ProtocolAuthorityMode.FILESYSTEM,
            target_ref=str(tmp_path),
            source_ref="aware.protocol.toml",
        )
    )

    assert result.operation_ref == "protocol_sdk.admit_target"
    assert result.admission.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1
    assert result.request.target_ref == str(tmp_path)
    assert result.request.source_ref == "aware.protocol.toml"
    assert result.to_wire()["contract"] == "aware.protocol.target-admission-result.v2"
    assert "record_bindings:evidence,goal,issue,specification" in result.evidence


def test_sdk_provider_does_not_fallback_to_filesystem(tmp_path: Path) -> None:
    result = ProtocolSdkClient(provider=FilesystemProtocolSdkProvider()).admit_target(
        ProtocolTargetAdmissionRequest(
            authority_mode=ProtocolAuthorityMode.SERVICE_API,
            target_ref=str(tmp_path),
            source_ref="aware.protocol.toml",
        )
    )

    assert (
        result.admission.outcome is ProtocolAdmissionOutcomeKind.AUTHORITY_UNAVAILABLE
    )
    assert result.admission.source_sha256 is None
    assert result.request.authority_mode is ProtocolAuthorityMode.SERVICE_API
    assert result.admission.diagnostics == (
        "filesystem_provider_requires_filesystem_authority",
    )
