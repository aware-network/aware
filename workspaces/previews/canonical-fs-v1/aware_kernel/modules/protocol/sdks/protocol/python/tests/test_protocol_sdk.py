from __future__ import annotations

from aware_protocol_runtime import (
    ProtocolAdmissionOutcomeKind,
    ProtocolAdmissionResult,
    ProtocolAuthorityMode,
)
from aware_protocol_sdk import (
    PROTOCOL_ADMIT_TARGET_OPERATION_REF,
    ProtocolSdkClient,
    ProtocolTargetAdmissionRequest,
    ProtocolTargetAdmissionResult,
)


class _Provider:
    def admit_target(
        self,
        request: ProtocolTargetAdmissionRequest,
    ) -> ProtocolTargetAdmissionResult:
        return ProtocolTargetAdmissionResult(
            provider_ref="test.filesystem",
            provider_distribution="test-provider",
            provider_version="1",
            admission=ProtocolAdmissionResult(
                outcome=ProtocolAdmissionOutcomeKind.SOURCE_UNAVAILABLE,
                source_sha256=None,
                diagnostics=(request.source_ref,),
            ),
            evidence=(request.authority_mode.value,),
        )


def test_client_dispatches_canonical_operation_to_injected_provider() -> None:
    result = ProtocolSdkClient(provider=_Provider()).admit_target(
        ProtocolTargetAdmissionRequest(
            authority_mode=ProtocolAuthorityMode.FILESYSTEM,
            target_ref="/customer",
            source_ref="aware.protocol.toml",
        )
    )

    assert result.operation_ref == PROTOCOL_ADMIT_TARGET_OPERATION_REF
    assert result.provider_ref == "test.filesystem"
    assert result.admission.outcome is ProtocolAdmissionOutcomeKind.SOURCE_UNAVAILABLE
    assert result.evidence == ("filesystem",)


def test_result_wire_separates_operation_provider_and_admission() -> None:
    result = _Provider().admit_target(
        ProtocolTargetAdmissionRequest(
            authority_mode=ProtocolAuthorityMode.FILESYSTEM,
            target_ref="/customer",
            source_ref="aware.protocol.toml",
        )
    ).to_wire()

    assert result["operation_ref"] == "protocol_sdk.admit_target"
    assert result["provider_ref"] == "test.filesystem"
    assert result["admission"]["outcome"] == "source_unavailable"
