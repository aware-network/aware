"""Versioned exact product exposure without widening legacy profile meaning."""

import json
from dataclasses import replace

import pytest
from aware_code_module_manifest_contract_runtime.parser import AwareModuleTomlError
from aware_code_module_manifest_contract_runtime.profile_codec import (
    CONTRACT,
    CONTRACT_V2,
    decode_profile_manifest,
    encode_profile_manifest,
)
from aware_code_module_manifest_contract_runtime.profile_models import (
    CodeSemanticContractProfileManifestSpec,
    CodeSemanticContractProfileManifestSpecV2,
    CodeSemanticContractProfileProviderSpecV2,
)
from aware_code_module_manifest_contract_runtime.profile_parser import (
    parse_profile_manifest,
)

SOURCE = b"""aware_semantic_contract_profile = 2
[profile]
key = "custom.product"
package_key = "independent.package"
[[providers]]
module_id = "attention"
package_id = "definition_provider"
registration_key = "layout_definition"
provider_key = "attention-layout-definition"
exposure = "graph_product"
"""


def test_exact_product_key_and_registration_survive_canonical_roundtrip():
    model = parse_profile_manifest(SOURCE)
    assert type(model) is CodeSemanticContractProfileManifestSpecV2
    (row,) = model.providers
    assert type(row) is CodeSemanticContractProfileProviderSpecV2
    assert (
        row.module_id,
        row.package_id,
        row.registration_key,
        row.provider_key,
        row.exposure,
    ) == (
        "attention",
        "definition_provider",
        "layout_definition",
        "attention-layout-definition",
        "graph_product",
    )
    assert row.required is True and row.status == "active"
    body = encode_profile_manifest(model)
    assert json.loads(body)["contract"] == CONTRACT_V2
    assert decode_profile_manifest(body) == model


@pytest.mark.parametrize(
    "before,after",
    [
        (b"= 2", b"= true"),
        (b"= 2", b"= 2.0"),
        (b"= 2", b"= 3"),
        (b'package_id = "definition_provider"\n', b""),
        (b'registration_key = "layout_definition"\n', b""),
        (b'exposure = "graph_product"\n', b""),
        (b'exposure = "graph_product"', b'exposure = "owner"'),
        (b'exposure = "graph_product"', b'exposure = "stage_pair"'),
        (b'"attention-layout-definition"', b'"attention/layout-definition"'),
        (b'"attention-layout-definition"', b'"attention.layout-definition"'),
        (b'"attention-layout-definition"', b'"-attention"'),
        (b'"attention-layout-definition"', b'"Attention"'),
        (b'"attention-layout-definition"', b'" attention-layout-definition"'),
        (b'"definition_provider"', b'"provider/child"'),
        (b'"layout_definition"', b'"registration:layout"'),
        (b'"custom.product"', b'" custom.product "'),
        (b'exposure = "graph_product"', b'exposure = "graph_product"\nhidden = true'),
    ],
)
def test_v2_source_refuses_missing_noncanonical_or_unknown_exposure(before, after):
    with pytest.raises(AwareModuleTomlError):
        parse_profile_manifest(SOURCE.replace(before, after))


def test_v2_can_expose_an_exact_legacy_stage_pair_with_its_original_key():
    source = SOURCE.replace(b"attention-layout-definition", b"aware_attention").replace(
        b"graph_product", b"stage_pair"
    )
    row = parse_profile_manifest(source).providers[0]
    assert row.provider_key == "aware_attention"
    assert row.exposure == "stage_pair"


def test_v1_refuses_product_spelling_and_fields_and_preserves_original_wire():
    from test_profile_manifest import SOURCE as LEGACY

    old = parse_profile_manifest(LEGACY)
    assert type(old) is CodeSemanticContractProfileManifestSpec
    wire = encode_profile_manifest(old)
    assert json.loads(wire)["contract"] == CONTRACT
    assert "exposure" not in json.loads(wire)["providers"][0]
    with pytest.raises(AwareModuleTomlError):
        parse_profile_manifest(
            LEGACY.replace(b'" aware_code "', b'"attention-layout-definition"')
        )
    with pytest.raises(AwareModuleTomlError):
        parse_profile_manifest(SOURCE.replace(b"= 2", b"= 1", 1))


@pytest.mark.parametrize(
    "change",
    [
        "contract",
        "version",
        "boolean",
        "missing",
        "null",
        "extra",
        "duplicate",
        "trailing",
        "provider",
        "exposure",
    ],
)
def test_v2_canonical_codec_refuses_substituted_or_lossy_meaning(change):
    body = encode_profile_manifest(parse_profile_manifest(SOURCE))
    wire = json.loads(body)
    if change == "contract":
        wire["contract"] = CONTRACT
    elif change == "version":
        wire["aware_semantic_contract_profile"] = 1
    elif change == "boolean":
        wire["aware_semantic_contract_profile"] = True
    elif change == "missing":
        del wire["providers"][0]["registration_key"]
    elif change == "null":
        wire["providers"][0]["exposure"] = None
    elif change == "extra":
        wire["providers"][0]["unknown"] = 1
    elif change == "provider":
        wire["providers"][0]["provider_key"] = "foreign/key"
    elif change == "exposure":
        wire["providers"][0]["exposure"] = "stage_pair"
    elif change == "duplicate":
        body = body.replace(b"{", b'{"contract":"duplicate",', 1)
    else:
        body += b"\n"
    if change not in ("duplicate", "trailing"):
        body = json.dumps(wire, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(ValueError):
        decode_profile_manifest(body)


def test_model_version_row_type_and_exact_duplicate_closure_refuse():
    model = parse_profile_manifest(SOURCE)
    (row,) = model.providers
    with pytest.raises(ValueError):
        encode_profile_manifest(replace(model, aware_semantic_contract_profile=True))
    with pytest.raises(ValueError):
        encode_profile_manifest(replace(model, providers=(row, row)))
    with pytest.raises(ValueError):
        encode_profile_manifest(
            replace(model, providers=(replace(row, provider_key=" padded "),))
        )
    with pytest.raises(ValueError):
        encode_profile_manifest(
            CodeSemanticContractProfileManifestSpec(2, model.profile, model.providers)
        )
    with pytest.raises(AwareModuleTomlError):
        parse_profile_manifest(
            SOURCE.replace(b"attention-layout-definition", b"a" * 4097)
        )
