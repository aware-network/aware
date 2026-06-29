from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import cast

from aware_code_service_dto.code.features.grammar_anchor_binding import (
    CodeGrammarAnchorBinding,
    CodeGrammarAnchorBindingResolutionStatus,
    CodeGrammarAnchorTextEvidence,
    CodeGrammarAnchorTextTargetEvidence,
)
from aware_code_service_dto.code.features.grammar_anchor_render_delta import (
    CodeGrammarAnchorRenderEntry,
    CodeGrammarAnchorRenderReplacement,
    CodeGrammarAnchorRenderSource,
    CodeGrammarAnchorRenderSpanTarget,
    CodeGrammarAnchorRenderTargetKind,
    ResolveCodeGrammarAnchorRenderDeltaRequest,
    ResolveCodeGrammarAnchorRenderDeltaResponse,
)
from aware_code_service_dto.code.features.package_common import (
    CodePackagePathRole,
)
from aware_code_service_dto.code.features.package_delta import (
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_code_service_dto.code.features.package_distribution import (
    CodeLanguage,
)
from aware_code.source_index import (
    CodeGrammarSource,
    CodeGrammarSourceIndex,
    CodeGrammarSourceIndexCache,
)
from aware_code.semantic_materialization import (
    SEMANTIC_SOURCE_SESSION_CONTEXT_KEY,
    SemanticSourceSessionContext,
)
from aware_types import JsonObject, JsonValue

from aware_code.grammar_anchor.binding import (
    resolve_code_grammar_anchor_text_evidence_from_source_index,
)


_SOURCE_INDEX_CACHE = CodeGrammarSourceIndexCache(max_entries=32)


@dataclass(frozen=True, slots=True)
class _SourceState:
    source: CodeGrammarAnchorRenderSource
    text: str
    relative_path: str
    before_hash: str


@dataclass(frozen=True, slots=True)
class _ResolvedReplacement:
    replacement: CodeGrammarAnchorRenderReplacement
    source: _SourceState
    target_kind: str
    binding: CodeGrammarAnchorBinding | None
    evidence: CodeGrammarAnchorTextEvidence | None
    text_target: CodeGrammarAnchorTextTargetEvidence | None
    span_target: CodeGrammarAnchorRenderSpanTarget | None


def resolve_code_grammar_anchor_render_delta(
    *,
    request: ResolveCodeGrammarAnchorRenderDeltaRequest,
) -> ResolveCodeGrammarAnchorRenderDeltaResponse:
    diagnostics = _validate_request_shape(request=request)
    bindings_by_key = _binding_by_key(request.bindings)
    sources_by_key, source_diagnostics = _source_states_by_key(request=request)
    diagnostics.extend(source_diagnostics)
    source_session_context = _source_session_context_from_request(request)
    source_index = _source_index_from_states(
        sources_by_key,
        source_session_context=source_session_context,
    )

    resolved_replacements: list[_ResolvedReplacement] = []
    for index, replacement in enumerate(request.replacements):
        resolved, replacement_diagnostics = _resolve_replacement(
            replacement=replacement,
            index=index,
            bindings_by_key=bindings_by_key,
            sources_by_key=sources_by_key,
            source_index=source_index,
            request=request,
        )
        diagnostics.extend(replacement_diagnostics)
        if resolved is not None:
            resolved_replacements.append(resolved)

    overlap_diagnostics = _validate_non_overlapping_replacements(
        resolved_replacements,
    )
    diagnostics.extend(overlap_diagnostics)

    if diagnostics:
        return _response(
            request=request,
            diagnostics=diagnostics,
            resolved_replacements=resolved_replacements,
            package_delta=None,
        )

    package_delta, render_entries = _package_delta_from_replacements(
        request=request,
        resolved_replacements=resolved_replacements,
        source_index=source_index,
    )
    return _response(
        request=request,
        diagnostics=[],
        resolved_replacements=resolved_replacements,
        package_delta=package_delta,
        render_entries=render_entries,
    )


def _validate_request_shape(
    *,
    request: ResolveCodeGrammarAnchorRenderDeltaRequest,
) -> list[str]:
    diagnostics: list[str] = []
    if (
        request.strict
        and _has_grammar_anchor_replacements(request.replacements)
        and not request.bindings
    ):
        diagnostics.append("bindings must include at least one grammar anchor binding.")
    if request.strict and not request.sources:
        diagnostics.append("sources must include at least one render source.")
    if request.strict and not request.replacements:
        diagnostics.append("replacements must include at least one render replacement.")
    if request.baseline_fingerprint_algorithm != "sha256":
        diagnostics.append("baseline_fingerprint_algorithm must be sha256.")
    return diagnostics


def _source_states_by_key(
    *,
    request: ResolveCodeGrammarAnchorRenderDeltaRequest,
) -> tuple[dict[str, _SourceState], list[str]]:
    diagnostics: list[str] = []
    states: dict[str, _SourceState] = {}
    for index, source in enumerate(request.sources):
        prefix = f"sources[{index}]"
        source_key = source.source_key.strip()
        if not source_key:
            diagnostics.append(f"{prefix}.source_key is required.")
            continue
        if source_key in states:
            diagnostics.append(f"{prefix}.source_key {source_key!r} is duplicated.")
            continue
        if _code_language(source.language) is None:
            diagnostics.append(f"{prefix}.language is unsupported.")
            continue
        relative_path = _safe_relative_path(
            source.relative_path or source.source_key,
            context=f"{prefix}.relative_path",
        )
        if relative_path is None:
            diagnostics.append(f"{prefix}.relative_path is invalid.")
            continue
        source_text, text_diagnostics = _source_text(
            source=source,
            request=request,
            prefix=prefix,
            relative_path=relative_path,
        )
        diagnostics.extend(text_diagnostics)
        if source_text is None:
            continue
        before_hash = _sha256_text(source_text)
        if source.before_hash is not None and not _sha256_matches(
            source.before_hash,
            before_hash,
        ):
            diagnostics.append(f"{prefix}.before_hash mismatch.")
            continue
        states[source_key] = _SourceState(
            source=source,
            text=source_text,
            relative_path=relative_path,
            before_hash=before_hash,
        )
    return states, diagnostics


def _source_text(
    *,
    source: CodeGrammarAnchorRenderSource,
    request: ResolveCodeGrammarAnchorRenderDeltaRequest,
    prefix: str,
    relative_path: str,
) -> tuple[str | None, list[str]]:
    if source.source_text is not None:
        return source.source_text, []
    if request.package_root is None:
        return None, [f"{prefix}.source_text or request.package_root is required."]
    base_path = _package_base_path(
        package_root=request.package_root,
        sources_root=request.sources_root,
    )
    resolved_path = _resolve_safe_child(
        base=base_path,
        relative_path=relative_path,
    )
    if resolved_path is None:
        return None, [f"{prefix}.relative_path escapes package root."]
    if not resolved_path.is_file():
        return None, [f"{prefix}.relative_path does not exist: {relative_path}"]
    return resolved_path.read_text(encoding="utf-8"), []


def _resolve_replacement(
    *,
    replacement: CodeGrammarAnchorRenderReplacement,
    index: int,
    bindings_by_key: Mapping[str, CodeGrammarAnchorBinding],
    sources_by_key: Mapping[str, _SourceState],
    source_index: CodeGrammarSourceIndex,
    request: ResolveCodeGrammarAnchorRenderDeltaRequest,
) -> tuple[_ResolvedReplacement | None, list[str]]:
    prefix = f"replacements[{index}]"
    target_kind = _replacement_target_kind(replacement)
    if target_kind == CodeGrammarAnchorRenderTargetKind.text_span.value:
        return _resolve_span_replacement(
            replacement=replacement,
            index=index,
            sources_by_key=sources_by_key,
        )

    diagnostics: list[str] = []
    binding = (
        bindings_by_key.get(replacement.binding_key)
        if replacement.binding_key is not None
        else None
    )
    if binding is None:
        return None, [
            f"{prefix}.binding_key {replacement.binding_key!r} does not match a binding."
        ]
    source = _source_for_replacement(
        replacement=replacement,
        sources_by_key=sources_by_key,
    )
    if source is None:
        return None, [f"{prefix}.source_key does not resolve to one source."]
    if _language_value(source.source.language) != CodeLanguage.aware.value:
        return None, [f"{prefix}.grammar_anchor target requires aware source language."]

    evidence = resolve_code_grammar_anchor_text_evidence_from_source_index(
        binding=binding,
        source_index=source_index,
        source_key=source.source.source_key,
    )
    if evidence is None:
        return None, [f"{prefix}.binding did not resolve evidence."]
    evidence = evidence.model_copy(update={"relative_path": source.relative_path})
    if replacement.before_text_hash is not None and not _sha256_matches(
        replacement.before_text_hash,
        evidence.text_hash,
    ):
        return None, [f"{prefix}.before_text_hash mismatch."]

    text_target = CodeGrammarAnchorTextTargetEvidence(
        binding_key=binding.binding_key,
        graph_selector=binding.graph_selector,
        text_evidence=evidence,
        replacement_text=replacement.replacement_text,
        before_hash=evidence.text_hash,
        after_hash=_sha256_text(replacement.replacement_text),
        metadata=JsonObject(
            {
                "source": "aware_code.grammar_anchor.render_delta",
                "render_contract": "grammar_anchor",
                "event_ref": replacement.event_ref,
                "semantic_key": replacement.semantic_key,
            }
        ),
    )
    return (
        _ResolvedReplacement(
            replacement=replacement,
            source=source,
            target_kind=CodeGrammarAnchorRenderTargetKind.grammar_anchor.value,
            binding=binding,
            evidence=evidence,
            text_target=text_target,
            span_target=None,
        ),
        diagnostics,
    )


def _resolve_span_replacement(
    *,
    replacement: CodeGrammarAnchorRenderReplacement,
    index: int,
    sources_by_key: Mapping[str, _SourceState],
) -> tuple[_ResolvedReplacement | None, list[str]]:
    prefix = f"replacements[{index}]"
    span_target = replacement.span_target
    if span_target is None:
        return None, [f"{prefix}.span_target is required for text_span target."]
    source = _source_for_span_replacement(
        replacement=replacement,
        span_target=span_target,
        sources_by_key=sources_by_key,
    )
    if source is None:
        return None, [f"{prefix}.span_target source does not resolve to one source."]
    diagnostics = _validate_span_target(
        prefix=prefix,
        span_target=span_target,
        source=source,
    )
    if diagnostics:
        return None, diagnostics
    return (
        _ResolvedReplacement(
            replacement=replacement,
            source=source,
            target_kind=CodeGrammarAnchorRenderTargetKind.text_span.value,
            binding=None,
            evidence=None,
            text_target=None,
            span_target=span_target,
        ),
        [],
    )


def _source_for_replacement(
    *,
    replacement: CodeGrammarAnchorRenderReplacement,
    sources_by_key: Mapping[str, _SourceState],
) -> _SourceState | None:
    if replacement.source_key is not None:
        return sources_by_key.get(replacement.source_key)
    if len(sources_by_key) == 1:
        return next(iter(sources_by_key.values()))
    return None


def _source_for_span_replacement(
    *,
    replacement: CodeGrammarAnchorRenderReplacement,
    span_target: CodeGrammarAnchorRenderSpanTarget,
    sources_by_key: Mapping[str, _SourceState],
) -> _SourceState | None:
    source_key = span_target.source_key or replacement.source_key
    if source_key is not None:
        return sources_by_key.get(source_key)
    if span_target.relative_path is not None:
        relative_path = _safe_relative_path(
            span_target.relative_path,
            context="span_target.relative_path",
        )
        if relative_path is None:
            return None
        matches = [
            source
            for source in sources_by_key.values()
            if source.relative_path == relative_path
        ]
        if len(matches) == 1:
            return matches[0]
        return None
    if len(sources_by_key) == 1:
        return next(iter(sources_by_key.values()))
    return None


def _validate_span_target(
    *,
    prefix: str,
    span_target: CodeGrammarAnchorRenderSpanTarget,
    source: _SourceState,
) -> list[str]:
    diagnostics: list[str] = []
    if span_target.language is not None and _language_value(
        span_target.language,
    ) != _language_value(source.source.language):
        diagnostics.append(f"{prefix}.span_target.language mismatch.")
    if span_target.relative_path is not None:
        relative_path = _safe_relative_path(
            span_target.relative_path,
            context=f"{prefix}.span_target.relative_path",
        )
        if relative_path is None:
            diagnostics.append(f"{prefix}.span_target.relative_path is invalid.")
        elif relative_path != source.relative_path:
            diagnostics.append(f"{prefix}.span_target.relative_path mismatch.")
    if span_target.before_source_hash is not None and not _sha256_matches(
        span_target.before_source_hash,
        source.before_hash,
    ):
        diagnostics.append(f"{prefix}.span_target.before_source_hash mismatch.")
    source_bytes = source.text.encode("utf-8")
    if (
        span_target.byte_start < 0
        or span_target.byte_end < span_target.byte_start
        or span_target.byte_end > len(source_bytes)
    ):
        diagnostics.append(f"{prefix}.span_target byte range is invalid.")
        return diagnostics
    try:
        before_text = source_bytes[
            span_target.byte_start : span_target.byte_end
        ].decode("utf-8")
    except UnicodeDecodeError:
        diagnostics.append(f"{prefix}.span_target byte range is not utf-8 aligned.")
        return diagnostics
    if replacement_hash := span_target.before_text_hash:
        if not _sha256_matches(replacement_hash, _sha256_text(before_text)):
            diagnostics.append(f"{prefix}.span_target.before_text_hash mismatch.")
    return diagnostics


def _validate_non_overlapping_replacements(
    replacements: Iterable[_ResolvedReplacement],
) -> list[str]:
    diagnostics: list[str] = []
    by_source: dict[str, list[_ResolvedReplacement]] = {}
    for replacement in replacements:
        by_source.setdefault(replacement.source.source.source_key, []).append(
            replacement
        )
    for source_key, source_replacements in by_source.items():
        ordered = sorted(
            source_replacements,
            key=_replacement_byte_start,
        )
        previous: _ResolvedReplacement | None = None
        for current in ordered:
            if (
                previous is not None
                and _replacement_byte_start(current) < _replacement_byte_end(previous)
            ):
                diagnostics.append(
                    f"source {source_key!r} has overlapping grammar-anchor replacements."
                )
                break
            previous = current
    return diagnostics


def _package_delta_from_replacements(
    *,
    request: ResolveCodeGrammarAnchorRenderDeltaRequest,
    resolved_replacements: Iterable[_ResolvedReplacement],
    source_index: CodeGrammarSourceIndex,
) -> tuple[CodePackageDelta | None, list[CodeGrammarAnchorRenderEntry]]:
    replacements_by_source: dict[str, list[_ResolvedReplacement]] = {}
    for replacement in resolved_replacements:
        replacements_by_source.setdefault(
            replacement.source.source.source_key,
            [],
        ).append(replacement)

    paths: list[CodePackageDeltaPath] = []
    render_entries: list[CodeGrammarAnchorRenderEntry] = []
    for source_key, source_replacements in sorted(replacements_by_source.items()):
        source = source_replacements[0].source
        updated_text = _apply_source_replacements(
            source_text=source.text,
            replacements=source_replacements,
        )
        after_source_hash = _sha256_text(updated_text)
        render_entries.extend(
            _render_entry(
                replacement=replacement,
                after_source_hash=after_source_hash,
                source_index=source_index,
            )
            for replacement in sorted(
                source_replacements,
                key=_replacement_byte_start,
            )
        )
        target_kind_counts: dict[str, int] = {}
        for replacement in source_replacements:
            target_kind_counts[replacement.target_kind] = (
                target_kind_counts.get(replacement.target_kind, 0) + 1
            )
        paths.append(
            CodePackageDeltaPath(
                relative_path=source.relative_path,
                kind=CodePackageDeltaKind.update,
                content_text=updated_text,
                before_hash=source.before_hash,
                after_hash=after_source_hash,
                size_bytes=len(updated_text.encode("utf-8")),
                language=_code_language(source.source.language) or CodeLanguage.aware,
                is_structural=True,
                path_role=CodePackagePathRole.authored_source,
                metadata=JsonObject(
                    cast(
                        dict[str, JsonValue],
                        {
                            "source": "aware_code.grammar_anchor.render_delta",
                            "source_key": source_key,
                            "render_contract": "grammar_anchor",
                            "replacement_count": len(source_replacements),
                            "target_kind_counts": target_kind_counts,
                            "source_index": source_index.evidence_payload(),
                        },
                    )
                ),
            )
        )

    if not paths:
        return None, render_entries
    return (
        CodePackageDelta(
            package_name=request.package_name,
            package_root=request.package_root,
            sources_root=request.sources_root,
            authority=CodePackageDeltaAuthorityKind.code_package_delta,
            authority_kind=CodePackageDeltaAuthorityKind.code_package_delta.value,
            paths=paths,
            metadata=JsonObject(
                cast(
                    dict[str, JsonValue],
                    {
                        "source": "aware_code.grammar_anchor.render_delta",
                        "resolver": "grammar_anchor",
                        "baseline_fingerprint": request.baseline_fingerprint,
                        "baseline_fingerprint_algorithm": (
                            request.baseline_fingerprint_algorithm
                        ),
                        "source_index": source_index.evidence_payload(),
                    },
                ),
            )
        ),
        render_entries,
    )


def _apply_source_replacements(
    *,
    source_text: str,
    replacements: Iterable[_ResolvedReplacement],
) -> str:
    source_bytes = source_text.encode("utf-8")
    updated = source_bytes
    for replacement in sorted(
        replacements,
        key=_replacement_byte_start,
        reverse=True,
    ):
        byte_start = _replacement_byte_start(replacement)
        byte_end = _replacement_byte_end(replacement)
        updated = (
            updated[:byte_start]
            + replacement.replacement.replacement_text.encode("utf-8")
            + updated[byte_end:]
        )
    return updated.decode("utf-8")


def _render_entry(
    *,
    replacement: _ResolvedReplacement,
    after_source_hash: str,
    source_index: CodeGrammarSourceIndex,
) -> CodeGrammarAnchorRenderEntry:
    return CodeGrammarAnchorRenderEntry(
        replacement_key=replacement.replacement.replacement_key,
        binding_key=(
            replacement.binding.binding_key
            if replacement.binding is not None
            else replacement.replacement.binding_key
        ),
        source_key=replacement.source.source.source_key,
        relative_path=replacement.source.relative_path,
        target_kind=CodeGrammarAnchorRenderTargetKind(replacement.target_kind),
        span_target=replacement.span_target,
        text_evidence=replacement.evidence,
        text_target=replacement.text_target,
        before_source_hash=replacement.source.before_hash,
        after_source_hash=after_source_hash,
        applied=True,
        metadata=JsonObject(
            {
                "source": "aware_code.grammar_anchor.render_delta",
                "render_contract": "grammar_anchor",
                "target_kind": replacement.target_kind,
                "event_ref": replacement.replacement.event_ref,
                "semantic_key": replacement.replacement.semantic_key,
                "grammar_rule_name": (
                    replacement.binding.grammar_rule_name
                    if replacement.binding is not None
                    else None
                ),
                "anchor_field_path": (
                    replacement.binding.anchor_field_path
                    if replacement.binding is not None
                    else None
                ),
                "source_index": source_index.evidence_payload(),
            }
        ),
    )


def _response(
    *,
    request: ResolveCodeGrammarAnchorRenderDeltaRequest,
    diagnostics: list[str],
    resolved_replacements: Iterable[_ResolvedReplacement],
    package_delta: CodePackageDelta | None,
    render_entries: list[CodeGrammarAnchorRenderEntry] | None = None,
) -> ResolveCodeGrammarAnchorRenderDeltaResponse:
    entries = render_entries if render_entries is not None else []
    resolved = package_delta is not None and not diagnostics
    return ResolveCodeGrammarAnchorRenderDeltaResponse(
        request_id=request.request_id,
        success=resolved,
        resolved=resolved,
        status=(
            CodeGrammarAnchorBindingResolutionStatus.resolved
            if resolved
            else CodeGrammarAnchorBindingResolutionStatus.blocked
        ),
        diagnostics=diagnostics,
        render_entries=entries,
        package_delta=package_delta,
        binding_count=len(request.bindings),
        source_count=len(request.sources),
        replacement_count=len(request.replacements),
        render_entry_count=len(entries),
        path_count=len(package_delta.paths) if package_delta is not None else 0,
        error=diagnostics[0] if diagnostics else None,
    )


def _binding_by_key(
    bindings: Iterable[CodeGrammarAnchorBinding],
) -> dict[str, CodeGrammarAnchorBinding]:
    return {binding.binding_key: binding for binding in bindings}


def _source_index_from_states(
    sources_by_key: Mapping[str, _SourceState],
    *,
    source_session_context: SemanticSourceSessionContext | None = None,
) -> CodeGrammarSourceIndex:
    aware_sources = tuple(
        source
        for source in sources_by_key.values()
        if _language_value(source.source.language) == CodeLanguage.aware.value
    )
    return _SOURCE_INDEX_CACHE.get_or_build(
        sources=(
            CodeGrammarSource(
                source_key=source.source.source_key,
                source_text=source.text,
                language=_language_value(source.source.language),
                relative_path=source.relative_path,
            )
            for source in aware_sources
        ),
        session_context=source_session_context,
    )


def _source_session_context_from_request(
    request: ResolveCodeGrammarAnchorRenderDeltaRequest,
) -> SemanticSourceSessionContext | None:
    metadata = request.metadata
    if not isinstance(metadata, Mapping):
        return None
    payload = metadata.get(SEMANTIC_SOURCE_SESSION_CONTEXT_KEY)
    if payload is None:
        return None
    return SemanticSourceSessionContext.from_payload(payload)


def _package_base_path(*, package_root: str, sources_root: str | None) -> Path:
    base = Path(package_root)
    source_prefix = _safe_relative_path(sources_root, context="sources_root")
    if source_prefix is None:
        return base
    return base / source_prefix


def _safe_relative_path(value: str | None, *, context: str) -> str | None:
    _ = context
    if value is None:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part == ".." for part in path.parts):
        return None
    normalized = path.as_posix()
    if not normalized or normalized == ".":
        return None
    return normalized


def _resolve_safe_child(*, base: Path, relative_path: str) -> Path | None:
    base_resolved = base.expanduser().resolve()
    candidate = (base_resolved / relative_path).resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError:
        return None
    return candidate


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _normalize_sha256_digest(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if len(stripped) == 64 and all(char in "0123456789abcdef" for char in stripped):
        return "sha256:" + stripped
    if (
        len(stripped) == 71
        and stripped.startswith("sha256:")
        and all(char in "0123456789abcdef" for char in stripped[7:])
    ):
        return stripped
    return None


def _sha256_matches(expected: str | None, actual: str | None) -> bool:
    normalized_expected = _normalize_sha256_digest(expected)
    if normalized_expected is None:
        return expected is None
    return normalized_expected == _normalize_sha256_digest(actual)


def _has_grammar_anchor_replacements(
    replacements: Iterable[CodeGrammarAnchorRenderReplacement],
) -> bool:
    return any(
        _replacement_target_kind(replacement)
        == CodeGrammarAnchorRenderTargetKind.grammar_anchor.value
        for replacement in replacements
    )


def _replacement_target_kind(
    replacement: CodeGrammarAnchorRenderReplacement,
) -> str:
    if replacement.span_target is not None:
        return CodeGrammarAnchorRenderTargetKind.text_span.value
    return _language_value(replacement.target_kind)


def _replacement_byte_start(replacement: _ResolvedReplacement) -> int:
    if replacement.evidence is not None:
        return replacement.evidence.byte_start
    if replacement.span_target is not None:
        return replacement.span_target.byte_start
    raise ValueError("Resolved replacement is missing target byte range.")


def _replacement_byte_end(replacement: _ResolvedReplacement) -> int:
    if replacement.evidence is not None:
        return replacement.evidence.byte_end
    if replacement.span_target is not None:
        return replacement.span_target.byte_end
    raise ValueError("Resolved replacement is missing target byte range.")


def _code_language(value: object) -> CodeLanguage | None:
    try:
        return CodeLanguage(_language_value(value))
    except ValueError:
        return None


def _language_value(value: object) -> str:
    enum_value = getattr(value, "value", value)
    return str(enum_value)


__all__ = ["resolve_code_grammar_anchor_render_delta"]
