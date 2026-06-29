from __future__ import annotations

from collections.abc import Mapping
from difflib import get_close_matches
import re
from typing import Protocol, cast

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code.primitive_codec import CodePrimitiveCodec

from aware_code.language_service.position import Utf16PositionMapper

from .contracts import AwareDiagnostic, DiagnosticDataValue


class DefaultsPluginContract(Protocol):
    primitive_codec: CodePrimitiveCodec


def collect_default_value_diagnostics(
    *,
    code: Code,
    mapper: Utf16PositionMapper,
    plugin: DefaultsPluginContract,
) -> list[AwareDiagnostic]:
    diagnostics: list[AwareDiagnostic] = []

    ident_rx = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def _suggest(value: str, options: list[str]) -> list[str]:
        v = (value or "").strip()
        if not v:
            return []
        try:
            return list(get_close_matches(v, options, n=3, cutoff=0.6))
        except Exception:
            return []

    def _is_ident(text: str) -> bool:
        return bool(ident_rx.match(text.strip()))

    def _add(
        *,
        start_byte: int,
        end_byte: int,
        message: str,
        code: str,
        data: Mapping[str, DiagnosticDataValue] | None = None,
    ) -> None:
        if end_byte <= start_byte:
            return
        start = mapper.byte_offset_to_position(start_byte)
        end = mapper.byte_offset_to_position(end_byte)
        diag: AwareDiagnostic = {
            "message": message,
            "severity": 1,
            "source": "aware",
            "code": code,
            "range": {
                "start": {"line": start.line, "character": start.character},
                "end": {"line": end.line, "character": end.character},
            },
        }
        if data is not None:
            diag["data"] = data
        diagnostics.append(diag)

    for section in code.code_sections:
        if section.type != CodeSectionType.attribute:
            continue
        attr = section.code_section_attribute
        if attr is None:
            continue

        type_text = attr.type_text
        if not isinstance(type_text, str) or not type_text.strip():
            continue

        default_text = attr.default_value_text
        seg = attr.default_value_segment
        if not isinstance(default_text, str) or not default_text.strip():
            continue
        if seg is None or seg.byte_start is None or seg.byte_end is None:
            continue
        if seg.byte_end <= seg.byte_start:
            continue

        # `null` requires an optional type (except for explicit Null).
        if default_text.strip().lower() == "null":
            is_optional = type_text.strip().endswith("?")
            prim_for_null = None
            try:
                prim_for_null = plugin.primitive_codec.parse(type_text)
            except Exception:
                prim_for_null = None
            if prim_for_null is not None and prim_for_null.base_type == CodePrimitiveBaseType.null:
                continue
            if not is_optional:
                _add(
                    start_byte=seg.byte_start,
                    end_byte=seg.byte_end,
                    message="Default `null` requires an optional type (append `?`).",
                    code="aware.default.null_requires_optional",
                )
            continue

        prim = None
        try:
            prim = plugin.primitive_codec.parse(type_text)
        except Exception:
            prim = None
        if prim is None:
            continue

        try:
            value = cast(DiagnosticDataValue, plugin.primitive_codec.parse_literal(default_text))
        except Exception as e:
            _add(
                start_byte=seg.byte_start,
                end_byte=seg.byte_end,
                message=str(e),
                code="aware.default.literal_invalid",
            )
            continue

        # Type-aware validation.
        if prim.base_type == CodePrimitiveBaseType.boolean:
            if not isinstance(value, bool):
                _add(
                    start_byte=seg.byte_start,
                    end_byte=seg.byte_end,
                    message="Bool default must be `true` or `false`.",
                    code="aware.default.kind_mismatch",
                    data={"suggestions": _suggest(default_text, ["true", "false"])},
                )
            continue

        if prim.base_type == CodePrimitiveBaseType.integer:
            if not (isinstance(value, int) and not isinstance(value, bool)):
                _add(
                    start_byte=seg.byte_start,
                    end_byte=seg.byte_end,
                    message="Int default must be an integer literal.",
                    code="aware.default.kind_mismatch",
                )
            continue

        if prim.base_type == CodePrimitiveBaseType.float:
            if not ((isinstance(value, int) and not isinstance(value, bool)) or isinstance(value, float)):
                _add(
                    start_byte=seg.byte_start,
                    end_byte=seg.byte_end,
                    message="Float default must be a numeric literal.",
                    code="aware.default.kind_mismatch",
                )
            continue

        if prim.base_type == CodePrimitiveBaseType.datetime:
            stripped = default_text.strip()
            lower = stripped.lower()

            # `now()` is a canonical DateTime factory default and should be expressed as a call,
            # not as a quoted string.
            if lower in {'"now()"', "'now()'"}:
                _add(
                    start_byte=seg.byte_start,
                    end_byte=seg.byte_end,
                    message="DateTime default `now()` must be an unquoted call expression (use `now()`).",
                    code="aware.default.datetime_now_requires_call",
                    data={"suggestions": ["now()"]},
                )
                continue

            # Accept the canonical factory call (parsed as a raw string by the literal codec).
            if isinstance(value, str) and value.strip().lower() == "now()":
                continue

            # Also accept explicit string literals (e.g., ISO timestamps).
            if (stripped.startswith('"') and stripped.endswith('"')) or (
                stripped.startswith("'") and stripped.endswith("'")
            ):
                continue

            _add(
                start_byte=seg.byte_start,
                end_byte=seg.byte_end,
                message="DateTime default must be `now()` or a quoted ISO string literal.",
                code="aware.default.kind_mismatch",
                data={"suggestions": ["now()"]},
            )
            continue

        if prim.base_type == CodePrimitiveBaseType.string:
            # Require an explicit string literal for String defaults (avoid enum-like identifiers).
            if _is_ident(default_text):
                _add(
                    start_byte=seg.byte_start,
                    end_byte=seg.byte_end,
                    message="String default must be a quoted string literal.",
                    code="aware.default.string_requires_quotes",
                    data={"suggestions": [f'"{default_text.strip()}"']},
                )
            continue

        if prim.base_type == CodePrimitiveBaseType.json:
            constraints = cast(Mapping[str, str] | None, prim.constraints)
            kind = None
            if constraints is not None:
                kind_val = constraints.get("json_kind")
                if kind_val is not None:
                    kind = kind_val.lower()

            # Treat raw Json as "value".
            if kind is None:
                kind = "value"

            if kind == "object":
                if isinstance(value, Mapping):
                    continue
                suggestions: list[str] = []
                if default_text.strip() in {'"{}"', "'{}'"}:
                    suggestions = ["{}"]
                _add(
                    start_byte=seg.byte_start,
                    end_byte=seg.byte_end,
                    message="JsonObject default must be a JSON object literal (e.g., `{}`).",
                    code="aware.default.json_object_expected",
                    data={"suggestions": suggestions} if suggestions else None,
                )
                continue

            if kind == "array":
                if isinstance(value, list):
                    continue
                suggestions = []
                if default_text.strip() in {'"[]"', "'[]'"}:
                    suggestions = ["[]"]
                _add(
                    start_byte=seg.byte_start,
                    end_byte=seg.byte_end,
                    message="JsonArray default must be a JSON array literal (e.g., `[]`).",
                    code="aware.default.json_array_expected",
                    data={"suggestions": suggestions} if suggestions else None,
                )
                continue

            # JsonValue: require strict JSON for strings (double quotes) and reject bare identifiers.
            if isinstance(value, str):
                stripped = default_text.strip()
                if _is_ident(stripped):
                    _add(
                        start_byte=seg.byte_start,
                        end_byte=seg.byte_end,
                        message="JsonValue string defaults must be strict JSON (quote the string).",
                        code="aware.default.json_string_requires_quotes",
                        data={"suggestions": [f'"{stripped}"']},
                    )
                    continue
                if stripped.startswith("'") and stripped.endswith("'") and len(stripped) >= 2:
                    inner = stripped[1:-1].replace('"', '\\"')
                    _add(
                        start_byte=seg.byte_start,
                        end_byte=seg.byte_end,
                        message="JsonValue string defaults must use double quotes (strict JSON).",
                        code="aware.default.json_string_requires_double_quotes",
                        data={"suggestions": [f'"{inner}"']},
                    )
                    continue

    return diagnostics
