from decimal import Decimal, localcontext

import pytest

from aware_code.decimal_value import (
    DecimalValueError,
    canonical_decimal_literal,
    canonical_decimal_text,
    decimal_value,
    is_canonical_decimal_text,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "0"),
        (Decimal("-0.000"), "0"),
        (Decimal("1"), "1"),
        (Decimal("1.0"), "1"),
        ("1.00", "1"),
        ("-120.3400", "-120.34"),
        ("1E+3", "1000"),
        ("1E-3", "0.001"),
    ],
)
def test_canonical_decimal_text_converges_equivalent_values(
    value: object,
    expected: str,
) -> None:
    assert canonical_decimal_text(value) == expected
    assert canonical_decimal_literal(str(value)) == expected


def test_canonical_decimal_text_is_independent_of_decimal_context() -> None:
    value = Decimal("123456789012345678901234567890.1234500")
    with localcontext() as context:
        context.prec = 6
        assert canonical_decimal_text(value) == ("123456789012345678901234567890.12345")


@pytest.mark.parametrize(
    "value",
    [True, False, 0.1, float("inf"), "NaN", "Infinity", "", "not-a-number"],
)
def test_decimal_value_rejects_inexact_or_non_finite_values(value: object) -> None:
    with pytest.raises(DecimalValueError):
        decimal_value(value)


def test_canonical_decimal_text_guard_requires_exact_canonical_text() -> None:
    assert is_canonical_decimal_text("0")
    assert is_canonical_decimal_text("-12.34")
    assert not is_canonical_decimal_text("1.0")
    assert not is_canonical_decimal_text(Decimal("1"))
