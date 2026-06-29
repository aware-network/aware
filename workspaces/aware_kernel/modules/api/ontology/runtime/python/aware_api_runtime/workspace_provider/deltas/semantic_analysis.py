from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aware_api_runtime.workspace_provider.deltas.transport import (
    code_package_delta_from_provider_delta_request,
)
from aware_api_runtime.source.semantic_analysis import (
    APISemanticAnalysisResult,
    analyze_api_code_package_delta,
)
from aware_api_runtime.workspace import APIWorkspace, APIWorkspaceSnapshot


API_PROVIDER_DELTA_CURRENT_SEMANTIC_ANALYSIS_CONTRACT_VERSION = (
    "aware.api.provider-delta.current-semantic-analysis.v1"
)


@dataclass(frozen=True, slots=True)
class ApiProviderDeltaCurrentSemanticAnalysis:
    manifest_path: Path
    snapshot: APIWorkspaceSnapshot
    analysis: APISemanticAnalysisResult

    @property
    def diagnostic_payloads(self) -> tuple[dict[str, object], ...]:
        return api_semantic_analysis_diagnostic_payloads(analysis=self.analysis)

    @property
    def applied_semantic_keys(self) -> tuple[str, ...]:
        return api_semantic_analysis_applied_semantic_keys(analysis=self.analysis)

    @property
    def current_semantic_delta_index(self) -> dict[str, dict[str, object]]:
        return api_current_semantic_delta_index(analysis=self.analysis)

    def evidence_payload(self) -> dict[str, object]:
        current_index = self.current_semantic_delta_index
        status, reason = _semantic_analysis_status_reason(
            diagnostic_payloads=self.diagnostic_payloads,
            applied_semantic_keys=self.applied_semantic_keys,
        )
        return {
            "analysis_kind": "api_provider_delta_current_semantic_analysis",
            "contract_version": (
                API_PROVIDER_DELTA_CURRENT_SEMANTIC_ANALYSIS_CONTRACT_VERSION
            ),
            "status": status,
            "reason": reason,
            "source": "aware_api.semantic_analysis",
            "manifest_path": self.manifest_path.as_posix(),
            "package_root": self.analysis.package_root,
            "source_files": self.analysis.source_files,
            "changed_source_files": (self.analysis.change_preview.changed_source_files),
            "affected_api_names": self.analysis.change_preview.affected_api_names,
            "affected_capability_names": (
                self.analysis.change_preview.affected_capability_names
            ),
            "semantic_delta_count": (len(self.analysis.change_preview.semantic_deltas)),
            "semantic_event_count": (len(self.analysis.change_preview.semantic_events)),
            "action_binding_count": (len(self.analysis.change_preview.action_bindings)),
            "applied_semantic_keys": self.applied_semantic_keys,
            "current_semantic_delta_index_available": bool(current_index),
            "current_semantic_delta_index_count": len(current_index),
            "current_semantic_delta_index_keys": tuple(sorted(current_index)),
            "current_semantic_delta_index": current_index,
            "diagnostics": self.diagnostic_payloads,
            "available": status == "semantic_analysis_ready",
            "blocked": status != "semantic_analysis_ready",
        }


def analyze_provider_delta_current_semantics(
    *,
    request: object,
    manifest_path: Path,
) -> ApiProviderDeltaCurrentSemanticAnalysis:
    snapshot = APIWorkspace.from_toml(toml_path=manifest_path).build_snapshot()
    delta = code_package_delta_from_provider_delta_request(request=request)
    analysis = analyze_api_code_package_delta(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
        code_package_delta=delta,
        fail_on_error=False,
    )
    return ApiProviderDeltaCurrentSemanticAnalysis(
        manifest_path=manifest_path,
        snapshot=snapshot,
        analysis=analysis,
    )


def api_semantic_analysis_diagnostic_payloads(
    *,
    analysis: APISemanticAnalysisResult,
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "severity": diagnostic.severity,
            "code": diagnostic.code,
            "message": diagnostic.message,
            "source_path": diagnostic.source_path,
        }
        for diagnostic in analysis.diagnostics
    )


def api_semantic_analysis_applied_semantic_keys(
    *,
    analysis: APISemanticAnalysisResult,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                semantic_key
                for semantic_key in (
                    _optional_text(delta.semantic_key)
                    for delta in analysis.change_preview.semantic_deltas
                )
                if semantic_key
            }
        )
    )


def api_current_semantic_delta_index(
    *,
    analysis: APISemanticAnalysisResult,
) -> dict[str, dict[str, object]]:
    indexed = {
        semantic_key: delta.evidence_payload()
        for semantic_key, delta in (
            (_optional_text(delta.semantic_key), delta)
            for delta in analysis.change_preview.semantic_deltas
        )
        if semantic_key
    }
    return dict(sorted(indexed.items()))


def _semantic_analysis_status_reason(
    *,
    diagnostic_payloads: tuple[dict[str, object], ...],
    applied_semantic_keys: tuple[str, ...],
) -> tuple[str, str]:
    if diagnostic_payloads:
        return (
            "semantic_analysis_diagnostics_present",
            "api_delta_semantic_analysis_diagnostics_present",
        )
    if not applied_semantic_keys:
        return (
            "semantic_analysis_empty",
            "api_delta_semantic_keys_unavailable",
        )
    return (
        "semantic_analysis_ready",
        "api_delta_semantic_analysis_ready",
    )


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "API_PROVIDER_DELTA_CURRENT_SEMANTIC_ANALYSIS_CONTRACT_VERSION",
    "ApiProviderDeltaCurrentSemanticAnalysis",
    "analyze_provider_delta_current_semantics",
    "api_current_semantic_delta_index",
    "api_semantic_analysis_applied_semantic_keys",
    "api_semantic_analysis_diagnostic_payloads",
]
