import json
from dataclasses import FrozenInstanceError

import pytest
from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV2,
    AwareModuleTomlError,
    decode_module_manifest_meaning,
    encode_module_manifest_meaning,
    parse_module_manifest,
)

HEADER = """aware = 2
[[plugins]]
kind = "code.module_plugin"
provider_key = "demo"
[[packages]]
id = "provider"
kind = "code"
manifest = "provider/pyproject.toml"
[packages.semantic_contract]
role = "demo.provider"
contract = "aware.semantic_provider"
provider_key = "demo"
module = "demo.provider"
owns_manifest_kinds = ["demo_toml"]
capabilities = ["materialize"]
[[packages.semantic_contract.registrations]]
key = "demo"
manifest_contract_kind = "demo_toml"
manifest_filename = "aware.demo.toml"
semantic_package_family = "demo"
semantic_package_kind = "demo_package"
semantic_contract = { role = "demo", name = "demo", provider_key = "demo", coordinate = "contract:demo" }
supported_languages = ["aware"]
code_package_surface = { state = "absent" }
profiles = [
 {stage="authority_derivation", profile_ref="demo.authority", profile_version="1", profile_digest="sha256:AAAAAAAA"},
 {stage="source_planning", profile_ref="demo.planning", profile_version="1", profile_digest="sha256:AAAAAAAA"}
]
[[packages]]
id = "home"
kind = "demo"
manifest = "home/aware.demo.toml"
[packages.semantic_admission]
registration = {state="present", value={module_id="demo", package_id="provider", registration_key="demo"}}
semantic_version = {state="present", value="1.0"}
semantic_package_name = {state="present", value="home-demo"}
code_package_name = {state="present", value="home-code"}
source_code_package_id = {state="absent"}
configuration = {state="absent"}
namespace = {state="present", value="home"}
owned_roots = {state="present", value=["home"]}
dependency_targets = {state="present", value=[{dependency_kind="module", dependency_ref="target", targets=[{module_id="demo", package_id="target"}], constraints=[{constraint_kind="package_kind", constraint_value="demo_package"}]}]}
""".replace("AAAAAAAA", "a" * 64)


def test_full_v2_roundtrip_and_genesis_claims():
    value = parse_module_manifest(HEADER.encode())
    assert type(value) is AwareModuleSpecV2
    assert value.aware == 2
    assert (
        value.package_declarations[1].occurrence.semantic_package_name.value
        == "home-demo"
    )
    assert (
        value.package_declarations[0].occurrence.semantic_package_name.state
        == "unavailable"
    )
    wire = encode_module_manifest_meaning(value)
    assert decode_module_manifest_meaning(wire) == value
    assert b"aware.code.module-manifest-meaning.v2" in wire
    with pytest.raises(FrozenInstanceError):
        value.package_declarations[1].occurrence.namespace.state = "absent"


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("aware = 2", "aware = 2.0"),
        ("aware = 2", "aware = 1"),
        ('semantic_package_name = {state="present", value="home-demo"}\n', ""),
        (
            'semantic_package_name = {state="present", value="home-demo"}',
            'semantic_package_name = {state="absent"}',
        ),
        (
            'source_code_package_id = {state="absent"}',
            'source_code_package_id = {state="absent", value="x"}',
        ),
        (
            'configuration = {state="absent"}',
            'configuration = {state="present", value={config_key="x"}}',
        ),
        (
            'namespace = {state="present", value="home"}',
            'namespace = {state="present", value=" home"}',
        ),
        ('value=["home"]', 'value=["home", "home"]'),
        ('value=["home"]', 'value=["z", "a"]'),
        (
            'module_id="demo", package_id="target"',
            'module_id="../demo", package_id="target"',
        ),
        (
            'module_id="demo", package_id="target"',
            'module_id="demo", package_id="package:target@1"',
        ),
        ('constraint_kind="package_kind"', 'constraint_kind="unknown"'),
        ('stage="source_planning"', 'stage="authority_derivation"'),
        ('supported_languages = ["aware"]', "supported_languages = []"),
        (
            'manifest_filename = "aware.demo.toml"',
            'manifest_filename = "../aware.demo.toml"',
        ),
        (
            'manifest_contract_kind = "demo_toml"',
            'manifest_contract_kind = "foreign_toml"',
        ),
        ('coordinate = "contract:demo"', 'coordinate = "contract:demo", extra=true'),
    ],
)
def test_v2_source_rejections(old, new):
    with pytest.raises((AwareModuleTomlError, ValueError)):
        parse_module_manifest(HEADER.replace(old, new).encode())


def test_unavailable_absent_present_empty_are_distinct():
    source = HEADER.replace(
        'owned_roots = {state="present", value=["home"]}',
        'owned_roots = {state="present", value=[]}',
    ).replace(
        'configuration = {state="absent"}', 'configuration = {state="unavailable"}'
    )
    occurrence = (
        parse_module_manifest(source.encode()).package_declarations[1].occurrence
    )
    assert occurrence.owned_roots.value == ()
    assert occurrence.configuration.state == "unavailable"
    assert occurrence.source_code_package_id.state == "absent"


@pytest.mark.parametrize(
    "mutation", ["extra", "missing", "stage", "version", "order", "scalar"]
)
def test_codec_validates_full_v2_structure(mutation):
    raw = json.loads(
        encode_module_manifest_meaning(parse_module_manifest(HEADER.encode()))
    )
    declaration = raw["meaning"]["package_declarations"][1]
    if mutation == "extra":
        declaration["extra"] = True
    elif mutation == "missing":
        del declaration["occurrence"]["semantic_package_name"]
    elif mutation == "stage":
        raw["meaning"]["package_declarations"][0]["registrations"][0]["profiles"][0][
            "stage"
        ] = "source_planning"
    elif mutation == "version":
        raw["meaning"]["aware"] = True
    elif mutation == "order":
        raw["meaning"]["package_declarations"].reverse()
    else:
        declaration["occurrence"]["semantic_version"]["value"] = 1
    with pytest.raises(ValueError):
        decode_module_manifest_meaning(
            json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
        )


def test_noncanonical_wire_and_utf8_bounds():
    wire = encode_module_manifest_meaning(parse_module_manifest(HEADER.encode()))
    with pytest.raises(ValueError):
        decode_module_manifest_meaning(wire + b"\n")
    with pytest.raises(ValueError):
        parse_module_manifest(
            HEADER.replace('value="home"', 'value="' + "x" * 4097 + '"').encode()
        )


def test_count_and_body_bounds():
    from aware_code_module_manifest_contract_runtime.v2_parser import (
        MAX_BODY,
        MAX_ITEMS,
    )

    too_many = ",".join('"root' + str(i).zfill(5) + '"' for i in range(MAX_ITEMS + 1))
    source = HEADER.replace('value=["home"]', "value=[" + too_many + "]")
    with pytest.raises(ValueError):
        parse_module_manifest(source.encode())
    with pytest.raises(ValueError):
        parse_module_manifest(HEADER.encode() + b"#" + b"x" * MAX_BODY)


def test_explicit_empty_v2_module_extensions():
    source = b'aware=2\n[[packages]]\nid="x"\nkind="code"\nmanifest="pyproject.toml"'
    value = parse_module_manifest(source)
    assert value.package_declarations[0].registrations == ()
    assert value.package_declarations[0].occurrence.registration.state == "unavailable"
    assert (
        decode_module_manifest_meaning(encode_module_manifest_meaning(value)) == value
    )


def test_occurrence_presence_survives_model_and_canonical_roundtrip():
    from dataclasses import fields

    omitted = HEADER.split("[packages.semantic_admission]")[0]
    missing = parse_module_manifest(omitted.encode())
    tags = "\n".join(
        f'{field.name} = {{state="unavailable"}}'
        for field in fields(missing.package_declarations[1].occurrence)
    )
    explicit = parse_module_manifest(
        (omitted + "[packages.semantic_admission]\n" + tags + "\n").encode()
    )
    assert (
        missing.package_declarations[1].occurrence
        == explicit.package_declarations[1].occurrence
    )
    assert missing.package_declarations[1].occurrence_declared is False
    assert explicit.package_declarations[1].occurrence_declared is True
    assert missing != explicit
    assert encode_module_manifest_meaning(missing) != encode_module_manifest_meaning(
        explicit
    )
    for value in (missing, explicit):
        assert (
            decode_module_manifest_meaning(encode_module_manifest_meaning(value))
            == value
        )


@pytest.mark.parametrize("presence", [False, 0, 1, None, "true"])
def test_reject_invalid_occurrence_presence_in_model_and_wire(presence):
    from dataclasses import replace

    value = parse_module_manifest(HEADER.encode())
    declaration = replace(value.package_declarations[1], occurrence_declared=presence)
    forged = replace(
        value, package_declarations=(value.package_declarations[0], declaration)
    )
    with pytest.raises(ValueError):
        encode_module_manifest_meaning(forged)
    raw = json.loads(encode_module_manifest_meaning(value))
    raw["meaning"]["package_declarations"][1]["occurrence_declared"] = presence
    with pytest.raises(ValueError):
        decode_module_manifest_meaning(
            json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
        )


def test_reject_missing_occurrence_presence_in_wire():
    raw = json.loads(
        encode_module_manifest_meaning(parse_module_manifest(HEADER.encode()))
    )
    del raw["meaning"]["package_declarations"][0]["occurrence_declared"]
    with pytest.raises(ValueError):
        decode_module_manifest_meaning(
            json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
        )
