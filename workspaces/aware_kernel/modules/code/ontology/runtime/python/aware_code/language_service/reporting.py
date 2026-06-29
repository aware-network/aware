from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import CodePackageDelta

from aware_code.language_service.report_models import (
    LanguageServiceDiagnostic,
    LanguageServiceDiagnosticSeverity,
    LanguageServicePerfMetric,
    LanguageServicePosition,
    LanguageServiceQuickFix,
    LanguageServiceRange,
    LanguageServiceReport,
    LanguageServiceSnapshotInfo,
    LanguageServiceSnapshotMode,
    LanguageServiceTextEdit,
)
from aware_code.language_service.features.code_actions import LspCodeAction
from aware_code.language_service.features.diagnostics_capabilities.contracts import (
    AwareDiagnostic,
    DiagnosticDataValue,
    DiagnosticRangeDict,
)
from aware_code.language_service.service import LanguageService


_SEVERITY_BY_LSP = {
    1: LanguageServiceDiagnosticSeverity.error,
    2: LanguageServiceDiagnosticSeverity.warning,
    3: LanguageServiceDiagnosticSeverity.info,
    4: LanguageServiceDiagnosticSeverity.hint,
}


def _range_from_lsp(rng: DiagnosticRangeDict | None) -> LanguageServiceRange:
    if rng is None:
        return LanguageServiceRange(
            start=LanguageServicePosition(line=0, character=0),
            end=LanguageServicePosition(line=0, character=0),
        )
    start = rng["start"]
    end = rng["end"]
    return LanguageServiceRange(
        start=LanguageServicePosition(
            line=int(start["line"]),
            character=int(start["character"]),
        ),
        end=LanguageServicePosition(
            line=int(end["line"]),
            character=int(end["character"]),
        ),
    )


def _string_suggestions(data: Mapping[str, DiagnosticDataValue] | None) -> list[str]:
    suggestions: list[str] = []
    if data is None:
        return suggestions
    raw = data.get("suggestions")
    if not isinstance(raw, Sequence) or isinstance(raw, str):
        return suggestions
    for item in raw:
        if isinstance(item, str) and item.strip():
            suggestions.append(item)
    return suggestions


def _diagnostic_from_lsp(
    *, uri: str, diag: AwareDiagnostic
) -> LanguageServiceDiagnostic:
    severity_value = diag.get("severity")
    severity = _SEVERITY_BY_LSP.get(
        severity_value if isinstance(severity_value, int) else 1,
        LanguageServiceDiagnosticSeverity.error,
    )
    message = diag.get("message")
    source = diag.get("source")
    code = diag.get("code")
    return LanguageServiceDiagnostic(
        uri=uri,
        range=_range_from_lsp(diag.get("range")),
        severity=severity,
        code=code if isinstance(code, str) else None,
        message=message if isinstance(message, str) else "",
        source=source if isinstance(source, str) else None,
        suggestions=_string_suggestions(diag.get("data")),
    )


def _quick_fixes_from_actions(
    *, actions: Sequence[LspCodeAction] | None
) -> list[LanguageServiceQuickFix]:
    fixes: list[LanguageServiceQuickFix] = []
    if not actions:
        return fixes
    for action in actions:
        title = action.get("title")
        if not isinstance(title, str) or not title.strip():
            continue
        is_preferred = bool(action.get("isPreferred") is True)
        edits: list[LanguageServiceTextEdit] = []
        edit = action.get("edit")
        changes = edit.get("changes") if edit is not None else {}
        for change_uri, raw_edits in changes.items():
            for raw_edit in raw_edits:
                edits.append(
                    LanguageServiceTextEdit(
                        uri=change_uri,
                        range=_range_from_lsp(raw_edit["range"]),
                        new_text=raw_edit["newText"],
                    )
                )
        fixes.append(
            LanguageServiceQuickFix(title=title, edits=edits, is_preferred=is_preferred)
        )
    return fixes


def _snapshot_info(service: LanguageService) -> LanguageServiceSnapshotInfo | None:
    snapshot = service.snapshot
    if snapshot is None:
        return None
    mode = None
    if snapshot.context.mode == "package":
        mode = LanguageServiceSnapshotMode.package
    elif snapshot.context.mode == "fallback":
        mode = LanguageServiceSnapshotMode.fallback
    return LanguageServiceSnapshotInfo(
        mode=mode,
        workspace_root=str(service.workspace.workspace_root),
        env_root=(
            str(snapshot.context.env_root)
            if snapshot.context.env_root is not None
            else None
        ),
        package_name=snapshot.context.root_package_name,
        language_id=str(service.workspace.language.value),
    )


def build_language_service_report(
    *,
    service: LanguageService,
    uri_texts: dict[str, str],
    focus_uri: str | None = None,
    include_config: bool = True,
) -> LanguageServiceReport:
    metrics: list[LanguageServicePerfMetric] = []

    if not uri_texts:
        return LanguageServiceReport(
            snapshot=_snapshot_info(service), perf_metrics=metrics
        )

    for idx, (uri, text) in enumerate(uri_texts.items(), start=1):
        # Use the public service API so validation/state hooks stay consistent.
        service.open_document(uri=uri, version=idx, text=text)

    if focus_uri is None:
        focus_uri = next(iter(uri_texts.keys()))

    t0 = time.perf_counter()
    service.rebuild_snapshot(focus_uri=focus_uri)
    metrics.append(
        LanguageServicePerfMetric(
            name="snapshot_rebuild",
            duration_ms=(time.perf_counter() - t0) * 1000.0,
        )
    )

    diagnostics: list[LanguageServiceDiagnostic] = []
    quick_fixes: list[LanguageServiceQuickFix] = []

    for uri, text in uri_texts.items():
        raw_diags: list[AwareDiagnostic]
        if include_config and uri.endswith("aware.toml"):
            raw_diags = service.config_diagnostics_for_uri(uri=uri)
        else:
            raw_diags = service.diagnostics_for(uri=uri)

        for diag in raw_diags:
            diagnostics.append(_diagnostic_from_lsp(uri=uri, diag=diag))

        if raw_diags:
            actions = service.code_actions(
                uri=uri, document_text=text, context_diagnostics=raw_diags
            )
            quick_fixes.extend(_quick_fixes_from_actions(actions=actions))

    metrics.append(
        LanguageServicePerfMetric(
            name="report_total",
            duration_ms=(time.perf_counter() - t0) * 1000.0,
        )
    )

    return LanguageServiceReport(
        diagnostics=diagnostics,
        quick_fixes=quick_fixes,
        perf_metrics=metrics,
        snapshot=_snapshot_info(service),
    )


def _should_include_delta_path(
    *, path: str, language: CodeLanguage | None, is_structural: bool | None
) -> bool:
    if path.endswith("aware.toml"):
        return True
    if is_structural is True:
        return True
    if language == CodeLanguage.aware:
        return True
    if path.endswith(".aware"):
        return True
    return False


def _field(value: object, name: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _enum_value(value: object) -> str | None:
    if value is None:
        return None
    raw = getattr(value, "value", value)
    return raw if isinstance(raw, str) else str(raw)


def _extract_full_text_from_patches(patches: Sequence[object]) -> str | None:
    if not patches:
        return None
    for patch in patches:
        if (
            _enum_value(_field(patch, "op")) == "replace"
            and _field(patch, "pos") == 0
            and _field(patch, "text") is not None
        ):
            return str(_field(patch, "text"))
    return None


def build_language_service_report_from_code_package_delta(
    *,
    service: LanguageService,
    delta: CodePackageDelta | None,
    focus_uri: str | None = None,
    include_config: bool = True,
) -> LanguageServiceReport:
    if delta is None or not delta.paths:
        return build_language_service_report(
            service=service,
            uri_texts={},
            focus_uri=focus_uri,
            include_config=include_config,
        )

    workspace_root = Path(service.workspace.workspace_root)
    uri_texts: dict[str, str] = {}

    for path_delta in delta.paths:
        kind = _enum_value(path_delta.kind)
        if kind not in {"create", "update"}:
            continue
        rel_path = path_delta.relative_path
        if not _should_include_delta_path(
            path=rel_path,
            language=path_delta.language,
            is_structural=path_delta.is_structural,
        ):
            continue
        if path_delta.content_text is None:
            continue
        abs_path = (workspace_root / rel_path.lstrip("/")).resolve()
        uri_texts[service.workspace.path_to_uri(abs_path)] = path_delta.content_text

    if focus_uri is not None and focus_uri not in uri_texts:
        focus_uri = None

    return build_language_service_report(
        service=service,
        uri_texts=uri_texts,
        focus_uri=focus_uri,
        include_config=include_config,
    )


def _build_language_service_report_from_legacy_delta(
    *,
    service: LanguageService,
    delta: object,
    focus_uri: str | None = None,
    include_config: bool = True,
) -> LanguageServiceReport:
    operations = _field(delta, "operations")
    if not isinstance(operations, Sequence) or not operations:
        return build_language_service_report(
            service=service,
            uri_texts={},
            focus_uri=focus_uri,
            include_config=include_config,
        )

    workspace_root = Path(service.workspace.workspace_root)
    uri_texts: dict[str, str] = {}

    for op in operations:
        create = _field(op, "create")
        if create is not None:
            if not _should_include_delta_path(
                path=str(_field(create, "path")),
                language=_field(create, "language"),
                is_structural=_field(create, "is_structural"),
            ):
                continue
            abs_path = (
                workspace_root / str(_field(create, "path")).lstrip("/")
            ).resolve()
            uri_texts[service.workspace.path_to_uri(abs_path)] = str(
                _field(create, "content_text")
            )
            continue

        update = _field(op, "update")
        if update is not None:
            rel_path = _field(update, "move_to") or _field(update, "path")
            rel_path = str(rel_path)
            if not _should_include_delta_path(
                path=rel_path,
                language=_field(update, "language"),
                is_structural=_field(update, "is_structural"),
            ):
                continue
            patches = _field(update, "patches")
            text = _extract_full_text_from_patches(
                patches if isinstance(patches, Sequence) else ()
            )
            if text is None:
                continue
            abs_path = (workspace_root / rel_path.lstrip("/")).resolve()
            uri_texts[service.workspace.path_to_uri(abs_path)] = text
            continue

    if focus_uri is not None and focus_uri not in uri_texts:
        focus_uri = None

    return build_language_service_report(
        service=service,
        uri_texts=uri_texts,
        focus_uri=focus_uri,
        include_config=include_config,
    )


def build_language_service_report_from_delta(
    *,
    service: LanguageService,
    delta: object | None,
    focus_uri: str | None = None,
    include_config: bool = True,
) -> LanguageServiceReport:
    if isinstance(delta, CodePackageDelta):
        return build_language_service_report_from_code_package_delta(
            service=service,
            delta=delta,
            focus_uri=focus_uri,
            include_config=include_config,
        )
    if delta is not None and hasattr(delta, "paths"):
        return build_language_service_report_from_code_package_delta(
            service=service,
            delta=CodePackageDelta.model_validate(delta),
            focus_uri=focus_uri,
            include_config=include_config,
        )
    if delta is not None and hasattr(delta, "operations"):
        return _build_language_service_report_from_legacy_delta(
            service=service,
            delta=delta,
            focus_uri=focus_uri,
            include_config=include_config,
        )
    return build_language_service_report(
        service=service,
        uri_texts={},
        focus_uri=focus_uri,
        include_config=include_config,
    )


__all__ = [
    "build_language_service_report",
    "build_language_service_report_from_code_package_delta",
    "build_language_service_report_from_delta",
]
