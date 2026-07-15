from decimal import Decimal

from aware_orm.local_state.sqlite import sqlite_value_for_model


def test_sqlite_decimal_codec_uses_canonical_text() -> None:
    assert sqlite_value_for_model(Decimal("1.2300")) == "1.23"
    assert sqlite_value_for_model(Decimal("1E+3")) == "1000"
    assert sqlite_value_for_model(Decimal("-0.000")) == "0"
