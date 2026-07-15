from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class DecimalValueError(ValueError):
    pass


def decimal_value(value: object, *, field_name: str = "decimal") -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise DecimalValueError(
            f"{field_name} must be Decimal, int, or decimal text; "
            "binary float is not allowed"
        )

    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, int):
        parsed = Decimal(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise DecimalValueError(f"{field_name} must not be empty")
        try:
            parsed = Decimal(text)
        except InvalidOperation as exc:
            raise DecimalValueError(
                f"{field_name} must be an exact base-10 number"
            ) from exc
    else:
        raise DecimalValueError(
            f"{field_name} must be Decimal, int, or decimal text; "
            f"got {type(value).__name__}"
        )

    if not parsed.is_finite():
        raise DecimalValueError(f"{field_name} must be finite")
    return parsed


def canonical_decimal_text(value: object, *, field_name: str = "decimal") -> str:
    parsed = decimal_value(value, field_name=field_name)
    if parsed.is_zero():
        return "0"

    # Fixed-point formatting preserves all coefficient digits without applying
    # the ambient Decimal context. Scale is presentation metadata, not value.
    text = format(parsed, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def canonical_decimal_literal(literal: str, *, field_name: str = "decimal") -> str:
    return canonical_decimal_text(literal, field_name=field_name)


def is_canonical_decimal_text(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return canonical_decimal_text(value) == value
    except DecimalValueError:
        return False


def _validate_decimal_wire(value: object, info: core_schema.ValidationInfo) -> Decimal:
    if info.mode == "json" and not isinstance(value, str):
        raise DecimalValueError("decimal JSON input must be canonical decimal text")
    return Decimal(canonical_decimal_text(value))


@dataclass(frozen=True, slots=True)
class DecimalWire:
    """Pydantic metadata for exact Decimal validation and JSON text encoding."""

    def __get_pydantic_core_schema__(
        self,
        source_type: object,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.with_info_before_validator_function(
            _validate_decimal_wire,
            handler(source_type),
            serialization=core_schema.plain_serializer_function_ser_schema(
                canonical_decimal_text,
                return_schema=core_schema.str_schema(),
                when_used="json",
            ),
        )


__all__ = [
    "DecimalValueError",
    "DecimalWire",
    "canonical_decimal_literal",
    "canonical_decimal_text",
    "decimal_value",
    "is_canonical_decimal_text",
]
