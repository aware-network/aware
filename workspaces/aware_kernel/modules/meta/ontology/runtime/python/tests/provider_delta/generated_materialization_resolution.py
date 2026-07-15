from __future__ import annotations

from aware_code.grammar_anchor import resolve_code_grammar_anchor_render_delta
from aware_meta.materialization.deltas.code_dto import (
    CodeGeneratedMaterializationDeltaEntry,
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedMaterializationDeltaRequest,
    CodeGeneratedMaterializationDeltaResult,
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaPath,
    ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    ResolveCodeGeneratedMaterializationPackageDeltaResponse,
)
from aware_types import JsonObject


def resolve_code_ready_grammar_anchor_package_delta(
    request: ResolveCodeGeneratedMaterializationPackageDeltaRequest,
) -> ResolveCodeGeneratedMaterializationPackageDeltaResponse:
    delta_request = request.delta_request
    result = request.result
    diagnostics = _validate_grammar_anchor_resolution_request(
        delta_request=delta_request,
        result=result,
    )
    if diagnostics:
        return _response(
            request=request,
            package_delta=None,
            diagnostics=diagnostics,
        )

    deltas: list[CodePackageDelta] = []
    for index, entry in enumerate(result.entries):
        entry_delta, entry_diagnostics = _resolve_grammar_anchor_entry(
            delta_request=delta_request,
            entry=entry,
            index=index,
        )
        if entry_diagnostics:
            return _response(
                request=request,
                package_delta=None,
                diagnostics=[
                    f"result.entries[{index}].grammar_anchor_render_delta.{diagnostic}"
                    for diagnostic in entry_diagnostics
                ],
            )
        assert entry_delta is not None
        deltas.append(entry_delta)

    merged, merge_diagnostics = _merge_package_deltas(
        delta_request=delta_request,
        result=result,
        deltas=deltas,
    )
    return _response(
        request=request,
        package_delta=merged,
        diagnostics=merge_diagnostics,
    )


def _validate_grammar_anchor_resolution_request(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    result: CodeGeneratedMaterializationDeltaResult,
) -> list[str]:
    diagnostics: list[str] = []
    if delta_request.provider_key != result.provider_key:
        diagnostics.append("result.provider_key must match delta_request.provider_key.")
    if not result.available:
        diagnostics.append("result.available must be true.")
    if not result.entries:
        diagnostics.append("result.entries must include grammar-anchor evidence.")
    for index, entry in enumerate(result.entries):
        if entry.grammar_anchor_render_delta is None:
            diagnostics.append(
                "result.entries["
                f"{index}] must include grammar_anchor_render_delta evidence."
            )
        if entry.mode not in (
            CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready,
            CodeGeneratedMaterializationDeltaMode.package_delta_ready,
        ):
            diagnostics.append(
                f"result.entries[{index}].mode must be grammar_anchor_render_ready."
            )
    return diagnostics


def _resolve_grammar_anchor_entry(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    entry: CodeGeneratedMaterializationDeltaEntry,
    index: int,
) -> tuple[CodePackageDelta | None, list[str]]:
    if entry.package_delta is not None:
        return entry.package_delta, []
    if entry.grammar_anchor_render_delta is None:
        return None, ["grammar_anchor_render_delta is required."]
    grammar_request = entry.grammar_anchor_render_delta.model_copy(
        update={
            "package_name": (
                entry.grammar_anchor_render_delta.package_name
                or entry.target.package_name
                or delta_request.package_name
            ),
            "package_root": (
                entry.grammar_anchor_render_delta.package_root
                or entry.target.package_root
                or delta_request.package_root
            ),
            "sources_root": (
                entry.grammar_anchor_render_delta.sources_root
                or entry.target.sources_root
                or delta_request.sources_root
            ),
            "baseline_fingerprint": (
                entry.grammar_anchor_render_delta.baseline_fingerprint
                or delta_request.baseline_fingerprint
            ),
            "baseline_fingerprint_algorithm": (
                entry.grammar_anchor_render_delta.baseline_fingerprint_algorithm
                or delta_request.baseline_fingerprint_algorithm
                or "sha256"
            ),
        }
    )
    grammar_response = resolve_code_grammar_anchor_render_delta(request=grammar_request)
    if (
        grammar_response.package_delta is None
        or not grammar_response.success
        or not grammar_response.resolved
    ):
        diagnostics = list(grammar_response.diagnostics)
        if not diagnostics:
            diagnostics.append("grammar-anchor render delta did not resolve.")
        return None, diagnostics
    metadata = dict(grammar_response.package_delta.metadata or {})
    metadata.update(
        {
            "source": "meta.provider_delta.generated_materialization_test",
            "resolver": "aware_code.grammar_anchor",
            "entry_index": index,
            "entry_key": entry.entry_key,
            "entry_mode": entry.mode.value,
            "generated_materialization_renderer": "grammar_anchor_render_delta",
            "render_entry_count": grammar_response.render_entry_count,
        }
    )
    return (
        grammar_response.package_delta.model_copy(
            update={
                "package_name": (
                    grammar_response.package_delta.package_name
                    or entry.target.package_name
                    or delta_request.package_name
                ),
                "package_root": (
                    grammar_response.package_delta.package_root
                    or entry.target.package_root
                    or delta_request.package_root
                ),
                "sources_root": (
                    grammar_response.package_delta.sources_root
                    or entry.target.sources_root
                    or delta_request.sources_root
                ),
                "authority": CodePackageDeltaAuthorityKind.code_package_delta,
                "authority_kind": (
                    CodePackageDeltaAuthorityKind.code_package_delta.value
                ),
                "metadata": JsonObject(metadata),
            }
        ),
        [],
    )


def _merge_package_deltas(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    result: CodeGeneratedMaterializationDeltaResult,
    deltas: list[CodePackageDelta],
) -> tuple[CodePackageDelta | None, list[str]]:
    package_name = _single_identity_value(
        deltas=deltas,
        attr="package_name",
        fallback=delta_request.package_name,
    )
    package_root = _single_identity_value(
        deltas=deltas,
        attr="package_root",
        fallback=delta_request.package_root,
    )
    sources_root = _single_identity_value(
        deltas=deltas,
        attr="sources_root",
        fallback=delta_request.sources_root,
    )
    paths_by_relative_path: dict[str, CodePackageDeltaPath] = {}
    warnings: list[str] = []
    diagnostics: list[str] = []
    for delta_index, delta in enumerate(deltas):
        warnings.extend(delta.warnings)
        for path in delta.paths:
            existing = paths_by_relative_path.get(path.relative_path)
            if existing is not None and existing != path:
                diagnostics.append(
                    "generated materialization package-delta conflict for "
                    f"path {path.relative_path!r} at delta index {delta_index}."
                )
                continue
            paths_by_relative_path[path.relative_path] = path
    if diagnostics:
        return None, diagnostics
    return (
        CodePackageDelta(
            package_name=package_name,
            package_root=package_root,
            sources_root=sources_root,
            authority=CodePackageDeltaAuthorityKind.code_package_delta,
            authority_kind=CodePackageDeltaAuthorityKind.code_package_delta.value,
            production=deltas[0].production if deltas else None,
            paths=[
                paths_by_relative_path[key] for key in sorted(paths_by_relative_path)
            ],
            warnings=sorted(set(warnings)),
            metadata=JsonObject(
                {
                    "source": "meta.provider_delta.generated_materialization_test",
                    "resolver": "aware_code.grammar_anchor",
                    "provider_key": result.provider_key,
                }
            ),
        ),
        [],
    )


def _single_identity_value(
    *,
    deltas: list[CodePackageDelta],
    attr: str,
    fallback: str | None,
) -> str | None:
    values = {
        value
        for delta in deltas
        if isinstance(value := getattr(delta, attr), str) and value
    }
    if len(values) == 1:
        return next(iter(values))
    if not values:
        return fallback
    return fallback


def _response(
    *,
    request: ResolveCodeGeneratedMaterializationPackageDeltaRequest,
    package_delta: CodePackageDelta | None,
    diagnostics: list[str],
) -> ResolveCodeGeneratedMaterializationPackageDeltaResponse:
    result = request.result
    resolved = package_delta is not None and not diagnostics
    return ResolveCodeGeneratedMaterializationPackageDeltaResponse(
        request_id=request.request_id,
        success=resolved,
        resolved=resolved,
        package_delta=package_delta,
        diagnostics=diagnostics,
        event_count=len(request.delta_request.events),
        action_count=len(request.delta_request.action_bindings),
        target_count=len(request.delta_request.targets),
        skipped_target_count=len(result.skipped_targets),
        entry_count=len(result.entries),
        path_count=len(package_delta.paths) if package_delta is not None else 0,
        renderer_operation_count=sum(
            len(entry.renderer_operations) for entry in result.entries
        ),
        package_delta_entry_count=sum(
            1 for entry in result.entries if entry.package_delta is not None
        ),
        grammar_anchor_render_entry_count=sum(
            1
            for entry in result.entries
            if entry.grammar_anchor_render_delta is not None
        ),
        section_delta_entry_count=sum(
            1 for entry in result.entries if entry.section_delta is not None
        ),
    )
