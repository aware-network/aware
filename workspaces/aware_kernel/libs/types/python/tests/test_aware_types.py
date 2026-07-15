from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Annotated
from uuid import UUID

import pytest
from pydantic import BaseModel, ValidationError

from aware_types import (
    DecimalWire,
    JsonArray,
    JsonObject,
    Vector,
    canonical_decimal_text,
)


class _Payload(BaseModel):
    payload: JsonObject
    changes: JsonArray
    embedding: Vector


def test_json_helpers_validate_and_serialize_common_runtime_values() -> None:
    payload = _Payload.model_validate(
        {
            "payload": {
                "path": Path("docs/release.md"),
                "owner_id": UUID("00000000-0000-0000-0000-000000000001"),
            },
            "changes": [{"kind": "update"}, ("tuple", "value")],
            "embedding": [1, "2.5"],
        }
    )

    assert payload.payload == JsonObject(
        {
            "path": "docs/release.md",
            "owner_id": "00000000-0000-0000-0000-000000000001",
        }
    )
    assert payload.changes == JsonArray([{"kind": "update"}, ["tuple", "value"]])
    assert payload.embedding == Vector([1.0, 2.5])
    assert payload.model_dump(mode="json") == {
        "payload": {
            "path": "docs/release.md",
            "owner_id": "00000000-0000-0000-0000-000000000001",
        },
        "changes": [{"kind": "update"}, ["tuple", "value"]],
        "embedding": [1.0, 2.5],
    }


class _DecimalModel(BaseModel):
    value: Annotated[Decimal, DecimalWire()]


def test_decimal_wire_uses_decimal_and_canonical_json_text() -> None:
    model = _DecimalModel(value=Decimal("1.2300"))
    assert model.value == Decimal("1.23")
    assert isinstance(model.value, Decimal)
    assert model.model_dump_json() == '{"value":"1.23"}'
    assert canonical_decimal_text(Decimal("1E+3")) == "1000"


@pytest.mark.parametrize("value", [0.1, float("inf"), True, "NaN"])
def test_decimal_wire_rejects_inexact_or_non_finite_python_input(value: object) -> None:
    with pytest.raises(ValidationError):
        _DecimalModel(value=value)


@pytest.mark.parametrize("payload", ['{"value":1.25}', '{"value":1}'])
def test_decimal_wire_rejects_json_numbers(payload: str) -> None:
    with pytest.raises(ValidationError):
        _DecimalModel.model_validate_json(payload)


def test_decimal_wire_accepts_exact_json_text() -> None:
    model = _DecimalModel.model_validate_json('{"value":"1.2500"}')
    assert model.value == Decimal("1.25")
    assert model.model_dump_json() == '{"value":"1.25"}'
