from __future__ import annotations

from aware_code.language_service.text import (
    iter_annotation_path_ranges,
    parse_annotation_statement_tokens,
    split_double_colon_parts,
)
from aware_code.language_service.types import SpannedToken

from .collector import SemanticTokenCollector


def _line_bounds_for_offset(*, document_bytes: bytes, byte_offset: int) -> tuple[int, int]:
    start = document_bytes.rfind(b"\n", 0, max(byte_offset, 0))
    line_start = 0 if start == -1 else start + 1
    end = document_bytes.find(b"\n", max(byte_offset, 0))
    line_end = len(document_bytes) if end == -1 else end
    return line_start, line_end


def _is_quoted_literal_token(text: str) -> bool:
    if len(text) < 2:
        return False
    if text[0] == text[-1] and text[0] in {'"', "'"}:
        return True
    return False


def _collect_oneof_annotation_arg_tokens(
    *,
    collector: SemanticTokenCollector,
    args_tokens: tuple[SpannedToken, ...],
) -> None:
    tokens = [tok for tok in args_tokens if (tok.text or "").strip()]
    if not tokens:
        return

    mode_offset = 0
    mode = (tokens[0].text or "").strip().casefold()
    if mode in {"validation", "identity"}:
        modifier_names = ("identity",) if mode == "identity" else ()
        collector.add_token(
            byte_start=tokens[0].range.start,
            byte_end=tokens[0].range.end,
            token_type_name="keyword",
            modifier_names=modifier_names,
        )
        mode_offset = 1

    identity_tokens = tokens[mode_offset:]
    if not identity_tokens:
        return

    discriminator_pos = next(
        (idx for idx, tok in enumerate(identity_tokens) if (tok.text or "").strip().casefold() == "discriminator"),
        None,
    )
    if discriminator_pos is None:
        for token in identity_tokens:
            collector.add_token(
                byte_start=token.range.start,
                byte_end=token.range.end,
                token_type_name="property",
            )
        return

    for token in identity_tokens[:discriminator_pos]:
        collector.add_token(
            byte_start=token.range.start,
            byte_end=token.range.end,
            token_type_name="property",
        )

    discriminator_token = identity_tokens[discriminator_pos]
    collector.add_token(
        byte_start=discriminator_token.range.start,
        byte_end=discriminator_token.range.end,
        token_type_name="keyword",
    )

    discriminator_tail = identity_tokens[discriminator_pos + 1 :]
    if not discriminator_tail:
        return

    discriminator_attr = discriminator_tail[0]
    collector.add_token(
        byte_start=discriminator_attr.range.start,
        byte_end=discriminator_attr.range.end,
        token_type_name="property",
    )

    mapping_tokens = discriminator_tail[1:]
    for idx, token in enumerate(mapping_tokens):
        text = (token.text or "").strip()
        if not text:
            continue
        if idx % 2 == 0:
            if _is_quoted_literal_token(text=text):
                continue
            collector.add_token(
                byte_start=token.range.start,
                byte_end=token.range.end,
                token_type_name="enumMember",
            )
            continue
        collector.add_token(
            byte_start=token.range.start,
            byte_end=token.range.end,
            token_type_name="property",
        )


def _collect_identity_annotation_arg_tokens(
    *,
    collector: SemanticTokenCollector,
    args_tokens: tuple[SpannedToken, ...],
) -> None:
    tokens = [tok for tok in args_tokens if (tok.text or "").strip()]
    if not tokens:
        return

    mode = (tokens[0].text or "").strip().casefold()
    if mode in {"contained", "standalone"}:
        collector.add_token(
            byte_start=tokens[0].range.start,
            byte_end=tokens[0].range.end,
            token_type_name="keyword",
            modifier_names=("identity",),
        )

    if len(tokens) < 2:
        return

    structural_token = tokens[1]
    if (structural_token.text or "").strip().casefold() != "structural":
        return
    collector.add_token(
        byte_start=structural_token.range.start,
        byte_end=structural_token.range.end,
        token_type_name="keyword",
    )

    if len(tokens) < 3:
        return

    relation_token = tokens[2]
    collector.add_token(
        byte_start=relation_token.range.start,
        byte_end=relation_token.range.end,
        token_type_name="property",
    )


def collect_annotation_path_tokens(*, collector: SemanticTokenCollector) -> None:
    document_bytes = collector.document_bytes
    scope = collector.context.scope

    for annotation_range in iter_annotation_path_ranges(document_bytes):
        token_bytes = document_bytes[annotation_range.start:annotation_range.end]
        parts = split_double_colon_parts(token_bytes=token_bytes, token_range=annotation_range)
        if not parts:
            continue

        type_ref_part = parts[0]
        token_type_name = collector.resolve_identifier_token_type(token_str=type_ref_part.text)
        if token_type_name is not None:
            collector.add_token(
                byte_start=type_ref_part.range.start,
                byte_end=type_ref_part.range.end,
                token_type_name=token_type_name,
            )

        resolved_class = scope.try_resolve_class_with_fqn(type_ref_part.text)
        class_section = resolved_class[1].code_section_class if resolved_class is not None else None

        for index, part in enumerate(parts[1:]):
            if index == 0 and class_section is not None:
                if any(attribute.name == part.text for attribute in class_section.code_section_attributes):
                    collector.add_token(
                        byte_start=part.range.start,
                        byte_end=part.range.end,
                        token_type_name="property",
                    )
                    continue
                if any(function.name == part.text for function in class_section.code_section_functions):
                    collector.add_token(
                        byte_start=part.range.start,
                        byte_end=part.range.end,
                        token_type_name="method",
                    )
                    continue

            if scope.try_resolve_class_with_fqn(part.text) is not None:
                collector.add_token(
                    byte_start=part.range.start,
                    byte_end=part.range.end,
                    token_type_name="class",
                )
                continue
            if scope.try_resolve_enum_with_fqn(part.text) is not None:
                collector.add_token(
                    byte_start=part.range.start,
                    byte_end=part.range.end,
                    token_type_name="enum",
                )
                continue

        line_start, line_end = _line_bounds_for_offset(
            document_bytes=document_bytes,
            byte_offset=annotation_range.start,
        )
        stmt = parse_annotation_statement_tokens(
            document_bytes=document_bytes,
            segment_start=line_start,
            segment_end=line_end,
        )
        if stmt is None or stmt.verb is None:
            continue

        verb = (stmt.verb.text or "").strip().lower()
        modifier_names = ("identity",) if verb == "identity" else ()
        collector.add_token(
            byte_start=stmt.verb.range.start,
            byte_end=stmt.verb.range.end,
            token_type_name="keyword",
            modifier_names=modifier_names,
        )

        if verb == "identity":
            _collect_identity_annotation_arg_tokens(
                collector=collector,
                args_tokens=stmt.args,
            )
            continue

        if verb != "oneof":
            continue
        _collect_oneof_annotation_arg_tokens(
            collector=collector,
            args_tokens=stmt.args,
        )
