from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import inspect
from typing import Any


RAW_SEGMENT_TEXT_DOMAIN = "raw_segment_text"
SEMANTIC_SEGMENT_VALUE_DOMAIN = "semantic_segment_value"


@dataclass(frozen=True, slots=True)
class CodeSegmentRenderPolicy:
    policy_key: str
    language: str
    section_type: str
    segment_name: str
    content_text_domain: str
    rendered_content_text_domain: str
    before_hash_domains: tuple[str, ...]
    after_hash_domain: str
    parser_segment_scope: str
    renderer_key: str
    metadata: Mapping[str, object]

    def raw_segment_is_policy_owned(self, text: str) -> bool:
        stripped = text.strip()
        return (
            _triple_quote_token(stripped) is not None
            or _line_doc_comment_text(stripped) is not None
        )

    def semantic_text_from_raw_segment(self, text: str) -> str:
        stripped = text.strip()
        line_doc_text = _line_doc_comment_text(stripped)
        if line_doc_text is not None:
            return _normalize_doc_text(line_doc_text)
        token = _triple_quote_token(stripped)
        if token is None:
            return _normalize_doc_text(stripped)
        return _normalize_doc_text(stripped[len(token) : -len(token)])

    def semantic_text_from_content_text(self, text: str) -> str:
        if self.raw_segment_is_policy_owned(text):
            return self.semantic_text_from_raw_segment(text)
        return _normalize_doc_text(text)

    def render_raw_segment(
        self,
        *,
        semantic_text: str,
        current_raw_segment: str,
    ) -> str:
        stripped_current = current_raw_segment.strip()
        if _line_doc_comment_text(stripped_current) is not None:
            return _render_line_doc_comment_segment(
                semantic_text=_normalize_doc_text(semantic_text),
                current_raw_segment=current_raw_segment,
            )
        token = _triple_quote_token(stripped_current)
        normalized_semantic_text = _normalize_doc_text(semantic_text)
        if token is None:
            return _render_doc_content_segment(
                semantic_text=normalized_semantic_text,
                current_raw_segment=current_raw_segment,
            )
        if (
            "\n" not in current_raw_segment
            and "\n" not in normalized_semantic_text
        ):
            prefix = _line_prefix(current_raw_segment)
            return f"{prefix}{token}{normalized_semantic_text}{token}"

        first_line_prefix = _line_prefix(current_raw_segment)
        content_prefix = _doc_content_prefix(current_raw_segment)
        closing_prefix = _doc_closing_prefix(current_raw_segment) or content_prefix
        lines = normalized_semantic_text.splitlines() or [""]
        rendered_lines = [f"{first_line_prefix}{token}"]
        rendered_lines.extend(f"{content_prefix}{line}" for line in lines)
        rendered_lines.append(f"{closing_prefix}{token}")
        return "\n".join(rendered_lines)


def _aware_description_comment_policy(
    *,
    section_type: str,
    parser_segment_scope: str,
    renderer_key: str,
) -> CodeSegmentRenderPolicy:
    return CodeSegmentRenderPolicy(
        policy_key=(
            "code.segment_render_policy.aware."
            f"{section_type}.description_comment"
        ),
        language="aware",
        section_type=section_type,
        segment_name="description_comment",
        content_text_domain=SEMANTIC_SEGMENT_VALUE_DOMAIN,
        rendered_content_text_domain=RAW_SEGMENT_TEXT_DOMAIN,
        before_hash_domains=(
            SEMANTIC_SEGMENT_VALUE_DOMAIN,
            RAW_SEGMENT_TEXT_DOMAIN,
        ),
        after_hash_domain=SEMANTIC_SEGMENT_VALUE_DOMAIN,
        parser_segment_scope=parser_segment_scope,
        renderer_key=renderer_key,
        metadata={
            "source": "aware_code.segment.render_policy",
            "parser_segment_authority": "aware_code.segment.scanner",
            "preserves_segment_trivia": True,
        },
    )


_AWARE_FUNCTION_DESCRIPTION_POLICY = _aware_description_comment_policy(
    section_type="function",
    parser_segment_scope="doc_comment_content_span",
    renderer_key="aware.function.description_comment.doc_content",
)
_AWARE_CLASS_DESCRIPTION_POLICY = _aware_description_comment_policy(
    section_type="class",
    parser_segment_scope="doc_comment_raw_span",
    renderer_key="aware.class.description_comment.doc_comment",
)
_POLICIES = (
    _AWARE_FUNCTION_DESCRIPTION_POLICY,
    _AWARE_CLASS_DESCRIPTION_POLICY,
)


def code_segment_render_policies(
    *,
    language: str | None = None,
    section_type: str | None = None,
    segment_name: str | None = None,
) -> tuple[CodeSegmentRenderPolicy, ...]:
    return tuple(
        policy
        for policy in _POLICIES
        if (language is None or policy.language == language)
        and (section_type is None or policy.section_type == section_type)
        and (segment_name is None or policy.segment_name == segment_name)
    )


def resolve_code_segment_render_policy(
    *,
    language: str,
    section_type: str,
    segment_name: str,
) -> CodeSegmentRenderPolicy | None:
    policies = code_segment_render_policies(
        language=language,
        section_type=section_type,
        segment_name=segment_name,
    )
    return policies[0] if policies else None


def sha256_text_digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def digest_matches(expected: str | None, actual: str) -> bool:
    normalized_expected = _normalize_sha256_digest(expected)
    if normalized_expected is None:
        return True
    normalized_actual = _normalize_sha256_digest(actual)
    return normalized_actual == normalized_expected


def _normalize_doc_text(text: str) -> str:
    return inspect.cleandoc(text).strip()


def _triple_quote_token(text: str) -> str | None:
    if len(text) < 6:
        return None
    if text.startswith('"""') and text.endswith('"""'):
        return '"""'
    if text.startswith("'''") and text.endswith("'''"):
        return "'''"
    return None


def _line_doc_comment_text(text: str) -> str | None:
    lines = text.splitlines()
    if not lines:
        return None
    content_lines: list[str] = []
    for line in lines:
        stripped = line.lstrip(" \t")
        if not stripped:
            content_lines.append("")
            continue
        if not stripped.startswith("///"):
            return None
        content = stripped[3:]
        if content.startswith(" "):
            content = content[1:]
        content_lines.append(content)
    return "\n".join(content_lines)


def _line_prefix(text: str) -> str:
    line = text.splitlines()[0] if text.splitlines() else text
    return line[: len(line) - len(line.lstrip(" \t"))]


def _doc_content_prefix(text: str) -> str:
    lines = text.splitlines()
    for line in lines[1:]:
        stripped = line.strip()
        if stripped and _triple_quote_token(stripped) is None:
            return line[: len(line) - len(line.lstrip(" \t"))]
    return _line_prefix(text)


def _doc_closing_prefix(text: str) -> str | None:
    lines = text.splitlines()
    for line in reversed(lines[1:]):
        stripped = line.strip()
        if _triple_quote_token(stripped) is not None:
            return line[: len(line) - len(line.lstrip(" \t"))]
    return None


def _render_doc_content_segment(
    *,
    semantic_text: str,
    current_raw_segment: str,
) -> str:
    if "\n" not in current_raw_segment:
        return semantic_text
    prefix = _doc_content_prefix(current_raw_segment)
    suffix = _trailing_line_suffix(current_raw_segment)
    leading_newline = "\n" if current_raw_segment.startswith(("\n", "\r\n")) else ""
    lines = semantic_text.splitlines() or [""]
    return (
        leading_newline
        + "\n".join(f"{prefix}{line}" for line in lines)
        + suffix
    )


def _render_line_doc_comment_segment(
    *,
    semantic_text: str,
    current_raw_segment: str,
) -> str:
    lines = current_raw_segment.splitlines()
    first_line = lines[0] if lines else current_raw_segment
    prefix = _line_prefix(first_line)
    marker_gap = _line_doc_marker_gap(first_line)
    semantic_lines = semantic_text.splitlines() or [""]
    rendered = [
        (
            f"{prefix}///{marker_gap}{line}"
            if line
            else f"{prefix}///"
        )
        for line in semantic_lines
    ]
    return "\n".join(rendered) + _trailing_line_suffix(current_raw_segment)


def _line_doc_marker_gap(line: str) -> str:
    marker_index = line.find("///")
    if marker_index < 0:
        return " "
    after_marker = line[marker_index + 3 :]
    return " " if after_marker.startswith(" ") else ""


def _trailing_line_suffix(text: str) -> str:
    newline_index = text.rfind("\n")
    if newline_index < 0:
        return ""
    suffix = text[newline_index:]
    return suffix if suffix.strip() == "" else ""


def _normalize_sha256_digest(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    if text.startswith("sha256:"):
        text = text.split(":", 1)[1]
    if len(text) != 64:
        return None
    if not all(ch in "0123456789abcdef" for ch in text):
        return None
    return text


def jsonable_policy_metadata(policy: CodeSegmentRenderPolicy) -> dict[str, Any]:
    return {str(key): value for key, value in policy.metadata.items()}
