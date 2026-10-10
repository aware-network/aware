from __future__ import annotations

import json

import pytest
from aware_workspace_runtime.revision_preparation_codec import (
    WorkspaceRevisionPreparationContractError,
    canonical_revision_preparation_json_bytes,
    decode_revision_preparation_json_object,
    require_exact_keys,
)
from aware_workspace_runtime.revision_preparation_contracts import (
    WorkspaceRevisionPinSlot,
)
from test_revision_preparation_contracts import _portable_fixture


class _ForeignString(str):
    pass


class _ForeignDictionary(dict):
    pass


@pytest.mark.parametrize(
    "body",
    (
        b'{"a":1,"a":1}',
        b'{"a":1.0}',
        b'{"a":NaN}',
        b'{"a":1}\n',
        b'{ "a":1}',
        b'{"z":0,"a":1}',
        b"[]",
        b"\xff",
    ),
)
def test_strict_decoder_rejects_noncanonical_or_unsupported_bodies(
    body: bytes,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        decode_revision_preparation_json_object(body)


def test_encoder_rejects_float_and_foreign_containers_recursively() -> None:
    with pytest.raises(TypeError):
        canonical_revision_preparation_json_bytes({"value": 1.0})
    with pytest.raises(TypeError):
        canonical_revision_preparation_json_bytes(_ForeignDictionary(value=1))
    with pytest.raises(TypeError):
        canonical_revision_preparation_json_bytes({"value": (1,)})


def test_direct_wire_requires_exact_string_keys_at_every_level() -> None:
    slot = _portable_fixture()["slot"]
    assert isinstance(slot, WorkspaceRevisionPinSlot)
    wire = slot.to_wire()
    wire[_ForeignString("result_role")] = wire.pop("result_role")
    with pytest.raises(TypeError, match="exact str"):
        WorkspaceRevisionPinSlot.from_wire(wire)

    nested = slot.to_wire()
    contract = nested["semantic_contract"]
    assert isinstance(contract, dict)
    contract[_ForeignString("key")] = contract.pop("key")
    with pytest.raises(TypeError, match="exact str"):
        WorkspaceRevisionPinSlot.from_wire(nested)


def test_bool_cannot_substitute_for_integer() -> None:
    slot = _portable_fixture()["slot"]
    assert isinstance(slot, WorkspaceRevisionPinSlot)
    wire = slot.to_wire()
    wire["codec_version"] = True
    with pytest.raises(ValueError, match="codec_version"):
        WorkspaceRevisionPinSlot.from_wire(wire)


def test_unknown_missing_and_foreign_top_level_mapping_fail() -> None:
    slot = _portable_fixture()["slot"]
    assert isinstance(slot, WorkspaceRevisionPinSlot)
    extra = slot.to_wire()
    extra["extra"] = None
    with pytest.raises(ValueError, match="fields"):
        WorkspaceRevisionPinSlot.from_wire(extra)
    missing = slot.to_wire()
    del missing["result_role"]
    with pytest.raises(ValueError, match="fields"):
        WorkspaceRevisionPinSlot.from_wire(missing)
    with pytest.raises(TypeError, match="exact dict"):
        WorkspaceRevisionPinSlot.from_wire(_ForeignDictionary(slot.to_wire()))


def test_canonical_decoder_rejects_coherent_pretty_reencoding() -> None:
    slot = _portable_fixture()["slot"]
    assert isinstance(slot, WorkspaceRevisionPinSlot)
    pretty = json.dumps(slot.to_wire(), indent=2, sort_keys=True).encode()
    with pytest.raises(WorkspaceRevisionPreparationContractError, match="canonical"):
        WorkspaceRevisionPinSlot.from_canonical_bytes(pretty)


def test_exact_key_helper_rejects_string_subclass_before_set_equality() -> None:
    key = _ForeignString("value")
    with pytest.raises(TypeError, match="exact str"):
        require_exact_keys({key: 1}, frozenset({"value"}), "test")
