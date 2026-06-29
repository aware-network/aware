from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256

from aware_meta.materialization.deltas.code_dto import (
    CodeGrammarAnchorRenderReplacement,
    CodeGrammarAnchorRenderSource,
    CodeGrammarAnchorRenderSpanTarget,
    CodeGrammarAnchorRenderTargetKind,
    CodeGraphFieldSelector,
    CodeLanguage,
    ResolveCodeGrammarAnchorRenderDeltaRequest,
)
from aware_types import JsonObject


@dataclass(frozen=True, slots=True)
class MetaGeneratedMaterializationTextSpanContext:
    target_key: str
    source_key: str
    relative_path: str
    language: CodeLanguage
    before_source_hash: str
    event_ref: str
    semantic_key: str


def meta_generated_materialization_text_span_replacement(
    *,
    context: MetaGeneratedMaterializationTextSpanContext,
    replacement_key: str,
    byte_start: int,
    byte_end: int,
    before_text: str,
    replacement_text: str,
    graph_selector: CodeGraphFieldSelector,
    metadata: JsonObject | None = None,
) -> CodeGrammarAnchorRenderReplacement:
    before_hash = _sha256_digest(before_text)
    return CodeGrammarAnchorRenderReplacement(
        replacement_key=replacement_key,
        source_key=context.source_key,
        target_kind=CodeGrammarAnchorRenderTargetKind.text_span,
        span_target=CodeGrammarAnchorRenderSpanTarget(
            target_key=context.target_key,
            source_key=context.source_key,
            relative_path=context.relative_path,
            language=context.language,
            byte_start=byte_start,
            byte_end=byte_end,
            before_text_hash=before_hash,
            before_source_hash=context.before_source_hash,
            graph_selector=graph_selector,
            metadata=metadata,
        ),
        replacement_text=replacement_text,
        before_text_hash=before_hash,
        event_ref=context.event_ref,
        semantic_key=context.semantic_key,
        metadata=metadata,
    )


def meta_generated_materialization_correlated_text_span_render_delta(
    *,
    package_name: str | None,
    package_root: str | None,
    sources_root: str | None,
    source_key: str,
    relative_path: str,
    language: CodeLanguage,
    before_source_hash: str,
    source_text: str | None = None,
    replacements: Sequence[CodeGrammarAnchorRenderReplacement],
    metadata: JsonObject | None = None,
) -> ResolveCodeGrammarAnchorRenderDeltaRequest:
    replacement_tuple = tuple(replacements)
    _validate_correlated_text_span_replacements(
        source_key=source_key,
        relative_path=relative_path,
        before_source_hash=before_source_hash,
        replacements=replacement_tuple,
    )
    return ResolveCodeGrammarAnchorRenderDeltaRequest(
        package_name=package_name,
        package_root=package_root,
        sources_root=sources_root,
        sources=[
            CodeGrammarAnchorRenderSource(
                source_key=source_key,
                language=language,
                relative_path=relative_path,
                source_text=source_text,
                before_hash=before_source_hash,
            )
        ],
        replacements=list(replacement_tuple),
        metadata=metadata,
    )


def missing_correlated_text_span_names(
    spans: Mapping[str, object | None],
) -> tuple[str, ...]:
    return tuple(name for name, span in spans.items() if span is None)


def _validate_correlated_text_span_replacements(
    *,
    source_key: str,
    relative_path: str,
    before_source_hash: str,
    replacements: tuple[CodeGrammarAnchorRenderReplacement, ...],
) -> None:
    if not replacements:
        raise ValueError("correlated generated-materialization span set is empty")
    ranges: list[tuple[int, int, str]] = []
    for replacement in replacements:
        span_target = replacement.span_target
        if span_target is None:
            raise ValueError(
                "correlated generated-materialization replacement must use "
                "a text span target"
            )
        if replacement.source_key != source_key or span_target.source_key != source_key:
            raise ValueError(
                "correlated generated-materialization replacements must target "
                f"one source_key: {source_key}"
            )
        if span_target.relative_path != relative_path:
            raise ValueError(
                "correlated generated-materialization replacements must target "
                f"one relative_path: {relative_path}"
            )
        if span_target.before_source_hash != before_source_hash:
            raise ValueError(
                "correlated generated-materialization replacements must share "
                "one before_source_hash"
            )
        if span_target.byte_start < 0 or span_target.byte_end < span_target.byte_start:
            raise ValueError(
                "correlated generated-materialization replacement has invalid "
                f"byte range: {replacement.replacement_key}"
            )
        replacement_key = replacement.replacement_key
        if not replacement_key:
            raise ValueError(
                "correlated generated-materialization replacement must have "
                "a replacement_key"
            )
        ranges.append(
            (
                span_target.byte_start,
                span_target.byte_end,
                replacement_key,
            )
        )
    ranges.sort()
    previous_end = -1
    previous_key = ""
    for byte_start, byte_end, replacement_key in ranges:
        if byte_start < previous_end:
            raise ValueError(
                "correlated generated-materialization replacements overlap: "
                f"{previous_key} and {replacement_key}"
            )
        previous_end = byte_end
        previous_key = replacement_key


def _sha256_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


__all__ = [
    "MetaGeneratedMaterializationTextSpanContext",
    "meta_generated_materialization_correlated_text_span_render_delta",
    "meta_generated_materialization_text_span_replacement",
    "missing_correlated_text_span_names",
]
