from decimal import Decimal

import pytest

from aware_code.decimal_value import DecimalValueError
from aware_meta.runtime.testing.proof import _jsonify_value


def test_meta_proof_jsonifies_decimal_values_as_canonical_text() -> None:
    assert _jsonify_value(Decimal("1.2300")) == "1.23"
    assert _jsonify_value(
        {
            "scalar": Decimal("20.00"),
            "tuple": (Decimal("0.10"),),
            "list": [Decimal("1E+3")],
        }
    ) == {
        "scalar": "20",
        "tuple": ["0.1"],
        "list": ["1000"],
    }


@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("Infinity")])
def test_meta_proof_rejects_non_finite_decimal_values(value: Decimal) -> None:
    with pytest.raises(DecimalValueError, match="must be finite"):
        _jsonify_value(value)
