from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import TypeAlias

CapitalAmount: TypeAlias = Decimal
ZERO_AMOUNT = Decimal("0")


def capital_amount(value: object, *, field_name: str = "amount") -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an exact decimal amount")
    if isinstance(value, float):
        raise ValueError(
            f"{field_name} must be Decimal, int, or decimal text; float is not allowed"
        )
    if isinstance(value, Decimal):
        parsed = value
    else:
        try:
            parsed = Decimal(str(value).strip())
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"{field_name} must be an exact decimal amount") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return parsed


def non_negative_amount(value: object, *, field_name: str = "amount") -> Decimal:
    parsed = capital_amount(value, field_name=field_name)
    if parsed < ZERO_AMOUNT:
        raise ValueError(f"{field_name} must be >= 0")
    return parsed


def positive_amount(value: object, *, field_name: str = "amount") -> Decimal:
    parsed = capital_amount(value, field_name=field_name)
    if parsed <= ZERO_AMOUNT:
        raise ValueError(f"{field_name} must be > 0")
    return parsed


def canonical_amount_text(value: object, *, field_name: str = "amount") -> str:
    parsed = capital_amount(value, field_name=field_name)
    return format(parsed.normalize(), "f")


def amount_equal(left: object, right: object) -> bool:
    return capital_amount(left, field_name="left") == capital_amount(
        right, field_name="right"
    )


__all__ = [
    "CapitalAmount",
    "ZERO_AMOUNT",
    "amount_equal",
    "canonical_amount_text",
    "capital_amount",
    "non_negative_amount",
    "positive_amount",
]
