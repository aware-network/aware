"""Qualified address leaf conformance; no complete v3 module or authority claim."""

from dataclasses import replace

import pytest
from aware_code_module_manifest_contract_runtime import AwareModuleTomlError
from aware_code_module_manifest_contract_runtime.v2_parser import address
from aware_code_module_manifest_contract_runtime.v3_parser import (
    parse_qualified_address,
    parse_qualified_targets,
    qualified_address_wire,
)


def target(handle=None):
    scope = {"kind": "local"} if handle is None else {"kind": "dependency", "workspace_handle": handle}
    return {"scope": scope, "module_id": "module", "package_id": "package"}


@pytest.mark.parametrize("handle", [None, "aware_kernel", "Kernel", "A" + "x" * 127])
@pytest.mark.parametrize("registration", [False, True])
def test_exact_address_roundtrip(handle, registration):
    wire = target(handle)
    if registration:
        wire["registration_key"] = "provider"
    value = parse_qualified_address(wire, registration=registration)
    assert qualified_address_wire(value, registration=registration) == wire


@pytest.mark.parametrize("handle", ["", " a", "a ", "a/b", "a:b", "a.b", "é", "1abc", "A" * 129, True])
def test_noncanonical_handle_rejects(handle):
    with pytest.raises(AwareModuleTomlError):
        parse_qualified_address(target(handle))


def test_same_named_targets_in_different_scopes_remain_distinct():
    values = [target("A"), target("a"), target()]
    assert len(parse_qualified_targets(values)) == 3
    with pytest.raises(AwareModuleTomlError):
        parse_qualified_targets(list(reversed(values)))
    with pytest.raises(AwareModuleTomlError):
        parse_qualified_targets([target("A"), target("A")])


def test_legacy_and_qualified_grammars_are_not_interchangeable():
    old = {"module_id": "module", "package_id": "package"}
    address(old)
    with pytest.raises(AwareModuleTomlError):
        parse_qualified_address(old)
    with pytest.raises(AwareModuleTomlError):
        address(target())


def test_extra_fields_and_hidden_model_fields_reject():
    wire = target()
    wire["scope"]["workspace_handle"] = "foreign"
    with pytest.raises(AwareModuleTomlError):
        parse_qualified_address(wire)
    value = parse_qualified_address(target())
    with pytest.raises(AwareModuleTomlError):
        qualified_address_wire(replace(value, workspace_handle="foreign"))
    with pytest.raises(AwareModuleTomlError):
        qualified_address_wire(replace(value, registration_key="hidden"))


def full_source():
    from test_module_manifest_v2 import HEADER
    return HEADER.replace("aware = 2", "aware = 3").replace(
        'value={module_id="demo", package_id="provider"',
        'value={scope={kind="dependency", workspace_handle="Kernel"}, module_id="demo", package_id="provider"',
    ).replace('targets=[{module_id=', 'targets=[{scope={kind="local"}, module_id=')


def test_full_v3_manifest_and_generic_codec_roundtrip():
    from aware_code_module_manifest_contract_runtime import (
        AwareModuleSpecV3,
        decode_module_manifest_meaning,
        encode_module_manifest_meaning,
        parse_module_manifest,
    )
    value = parse_module_manifest(full_source().encode())
    assert type(value) is AwareModuleSpecV3
    body = encode_module_manifest_meaning(value)
    assert b"aware.code.module-manifest-meaning.v3" in body
    assert decode_module_manifest_meaning(body) == value
    assert value.package_declarations[0].occurrence_declared is False
    assert value.package_declarations[1].occurrence_declared is True


@pytest.mark.parametrize("change", ["unqualified", "float", "version", "scope", "duplicate"])
def test_full_v3_rejects_invalid_declarations(change):
    from aware_code_module_manifest_contract_runtime import parse_module_manifest
    body = full_source()
    if change == "unqualified": body = body.replace('scope={kind="local"}, ', '')
    elif change == "float": body = body.replace('aware = 3', 'aware = 3.0')
    elif change == "version": body = body.replace('aware = 3', 'aware = 2')
    elif change == "scope": body = body.replace('workspace_handle="Kernel"', 'workspace_handle=" Kernel"')
    else: body = body.replace('scope={kind="local"}', 'scope={kind="local", kind="local"}')
    with pytest.raises(AwareModuleTomlError): parse_module_manifest(body.encode())


@pytest.mark.parametrize("change", ["contract", "aware", "presence", "unknown", "trailing", "duplicate"])
def test_full_v3_codec_rejects_substitution(change):
    import json

    from aware_code_module_manifest_contract_runtime import (
        ModuleManifestMeaningError,
        decode_module_manifest_meaning_v3,
        encode_module_manifest_meaning,
        parse_module_manifest,
    )
    body = encode_module_manifest_meaning(parse_module_manifest(full_source().encode()))
    wire = json.loads(body)
    if change == "contract": wire["contract"] = "aware.code.module-manifest-meaning.v2"
    elif change == "aware": wire["meaning"]["aware"] = 2
    elif change == "presence": wire["meaning"]["package_declarations"][1]["occurrence_declared"] = False
    elif change == "unknown": wire["meaning"]["extra"] = 1
    elif change == "trailing": body += b"\n"
    else: body = body.replace(b'{', b'{"contract":"duplicate",', 1)
    if change not in ("trailing", "duplicate"):
        body = json.dumps(wire, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(ModuleManifestMeaningError): decode_module_manifest_meaning_v3(body)


def test_v2_codec_refuses_v3_model():
    from aware_code_module_manifest_contract_runtime import (
        ModuleManifestMeaningError,
        encode_module_manifest_meaning_v2,
        parse_module_manifest,
    )
    with pytest.raises(ModuleManifestMeaningError):
        encode_module_manifest_meaning_v2(parse_module_manifest(full_source().encode()))
