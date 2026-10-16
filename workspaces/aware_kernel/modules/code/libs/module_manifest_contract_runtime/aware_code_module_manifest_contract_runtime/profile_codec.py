"""Strict, complete profile meaning codec; portable data only."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import cast

from .profile_models import (
    CodeSemanticContractProfileDescriptorSpec,
    CodeSemanticContractProfileManifestSpec,
    CodeSemanticContractProfileManifestSpecV2,
    CodeSemanticContractProfileProviderSpec,
    CodeSemanticContractProfileProviderSpecV2,
)
from .profile_parser import _parse_profile_table  # pyright: ignore[reportPrivateUsage]

CONTRACT = "aware.code.semantic-contract-profile-manifest.v1"
CONTRACT_V2 = "aware.code.semantic-contract-profile-manifest.v2"


def _wire(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate profile meaning key: {key}")
        result[key] = value
    return result


def encode_profile_manifest(value: CodeSemanticContractProfileManifestSpec) -> bytes:
    v2 = type(value) is CodeSemanticContractProfileManifestSpecV2
    if (
        type(value) not in (CodeSemanticContractProfileManifestSpec, CodeSemanticContractProfileManifestSpecV2)
        or type(value.profile) is not CodeSemanticContractProfileDescriptorSpec
        or type(value.providers) is not tuple
        or any(
            type(p) is not (CodeSemanticContractProfileProviderSpecV2 if v2 else CodeSemanticContractProfileProviderSpec)
            for p in value.providers
        )
    ):
        raise ValueError("exact profile meaning model required")
    if v2 and (type(value.aware_semantic_contract_profile) is not int or value.aware_semantic_contract_profile != 2):
        raise ValueError("exact v2 profile version required")
    if not v2 and value.aware_semantic_contract_profile != 1:
        raise ValueError("v1 profile model cannot carry v2 meaning")
    meaning = asdict(value)
    # The shared grammar validates meaning; a wire comparison rejects normalization,
    # omitted/default substitutes and bool/int equality without a second grammar.
    body = _wire({"contract": CONTRACT_V2 if v2 else CONTRACT, **meaning})
    decode_profile_manifest(body)
    return body


def decode_profile_manifest(body: bytes) -> CodeSemanticContractProfileManifestSpec:
    if type(body) is not bytes:
        raise TypeError("profile meaning must be bytes")
    raw = cast(object, json.loads(body.decode("utf-8"), object_pairs_hook=_pairs))
    if not isinstance(raw, dict):
        raise TypeError("profile meaning must be an object")
    value = cast(dict[str, object], raw)
    if set(value) != {
        "contract",
        "aware_semantic_contract_profile",
        "profile",
        "providers",
    }:
        raise ValueError("invalid profile meaning fields")
    if value["contract"] not in (CONTRACT, CONTRACT_V2):
        raise ValueError("unsupported profile meaning contract")
    meaning = {k: v for k, v in value.items() if k != "contract"}
    model = _parse_profile_table(meaning, source_label="<profile-meaning>")
    expected = CONTRACT_V2 if type(model) is CodeSemanticContractProfileManifestSpecV2 else CONTRACT
    if value["contract"] != expected or _wire({"contract": expected, **asdict(model)}) != body:
        raise ValueError("noncanonical or incomplete profile meaning")
    return model
