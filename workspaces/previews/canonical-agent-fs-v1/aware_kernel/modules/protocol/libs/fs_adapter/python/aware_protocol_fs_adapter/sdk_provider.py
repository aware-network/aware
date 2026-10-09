"""Filesystem authority provider for the canonical Protocol SDK operation."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path

from aware_protocol_runtime import (
    ProtocolAdmissionOutcomeKind,
    ProtocolAdmissionResult,
    ProtocolAuthorityMode,
)
from aware_protocol_sdk import (
    ProtocolTargetAdmissionRequest,
    ProtocolTargetAdmissionResult,
)

from .manifest import MANIFEST_FILENAME, admit_protocol_manifest

FILESYSTEM_PROTOCOL_PROVIDER_REF = "aware_protocol_fs_adapter.filesystem.v1"
FILESYSTEM_PROTOCOL_DISTRIBUTION = "aware-protocol-fs-adapter"


class FilesystemProtocolSdkProvider:
    """Admit an explicit repository target through filesystem authority only."""

    def admit_target(
        self,
        request: ProtocolTargetAdmissionRequest,
    ) -> ProtocolTargetAdmissionResult:
        if request.authority_mode is not ProtocolAuthorityMode.FILESYSTEM:
            return self._result(
                request=request,
                admission=ProtocolAdmissionResult(
                    outcome=ProtocolAdmissionOutcomeKind.AUTHORITY_UNAVAILABLE,
                    source_sha256=None,
                    diagnostics=("filesystem_provider_requires_filesystem_authority",),
                ),
                evidence=(f"requested_authority_mode:{request.authority_mode.value}",),
            )

        repository_root = Path(request.target_ref)
        source_path = Path(request.source_ref)
        manifest_path = (
            source_path if source_path.is_absolute() else repository_root / source_path
        )
        admitted = admit_protocol_manifest(
            manifest_path=manifest_path,
            repository_root=repository_root,
        )
        evidence = [
            "authority_mode:filesystem",
            f"manifest_filename:{MANIFEST_FILENAME}",
        ]
        if admitted.filesystem_profile is not None:
            # The adapter's canonical profile is inseparable from its manifest.
            assert admitted.manifest is not None
            evidence.extend(
                (
                    f"protocol_digest:{admitted.manifest.digest}",
                    "record_bindings:"
                    + ",".join(
                        binding.record_key
                        for binding in admitted.filesystem_profile.record_bindings
                    ),
                )
            )
        return self._result(
            request=request,
            admission=admitted.admission,
            evidence=tuple(evidence),
        )

    def _result(
        self,
        *,
        request: ProtocolTargetAdmissionRequest,
        admission: ProtocolAdmissionResult,
        evidence: tuple[str, ...],
    ) -> ProtocolTargetAdmissionResult:
        return ProtocolTargetAdmissionResult(
            request=request,
            provider_ref=FILESYSTEM_PROTOCOL_PROVIDER_REF,
            provider_distribution=FILESYSTEM_PROTOCOL_DISTRIBUTION,
            provider_version=_distribution_version(FILESYSTEM_PROTOCOL_DISTRIBUTION),
            admission=admission,
            evidence=evidence,
        )


def _distribution_version(distribution_name: str) -> str:
    try:
        return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        return "source"


__all__ = [
    "FILESYSTEM_PROTOCOL_DISTRIBUTION",
    "FILESYSTEM_PROTOCOL_PROVIDER_REF",
    "FilesystemProtocolSdkProvider",
]
