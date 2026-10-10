"""Neutral supplier registration through the real Code catalog contract."""

import tomllib
from pathlib import Path

import pytest
from aware_code_module_manifest_contract_runtime import (
    decode_module_manifest_meaning,
    encode_module_manifest_meaning,
    parse_module_manifest,
)
from packaging.requirements import Requirement

MODULE = Path(__file__).resolve().parents[5]
KERNEL = MODULE.parents[1]
SUPPLIERS = {
    "specification_sdk_python": (
        "sdks/specification/python/public/pyproject.toml",
        "aware-specification-sdk",
    ),
    "specification_fs_sdk_adapter": (
        "sdks/specification/python/fs_adapter/pyproject.toml",
        "aware-specification-fs-sdk-adapter",
    ),
    "specification_cli_python": (
        "sdks/specification/python/cli/pyproject.toml",
        "aware-specification-cli",
    ),
}


def descriptor():
    return parse_module_manifest(
        (MODULE / "aware.module.toml").read_bytes(),
        source_label="specification/aware.module.toml",
    )


def test_actual_code_catalog_codec_preserves_authored_declarations():
    value = descriptor()
    wire = encode_module_manifest_meaning(value)
    assert decode_module_manifest_meaning(wire) == value
    assert encode_module_manifest_meaning(decode_module_manifest_meaning(wire)) == wire


@pytest.mark.parametrize("key", SUPPLIERS)
def test_neutral_supplier_manifest_is_exact_registered_package(key):
    path, name = SUPPLIERS[key]
    packages = [item for item in descriptor().packages if item.id == key]
    assert len(packages) == 1
    assert (packages[0].kind, packages[0].manifest, packages[0].visibility) == (
        "code",
        path,
        "module",
    )
    metadata = tomllib.loads((MODULE / path).read_text())
    assert metadata["project"]["name"] == name
    assert metadata["project"]["requires-python"] == ">=3.12"
    assert {Requirement(item).name for item in metadata["project"]["dependencies"]} <= {
        "aware-specification-sdk",
        "aware-specification-fs-sdk-adapter",
        "aware-specification-runtime",
        "aware-specification-fs-adapter",
        "aware-command-runtime",
    }
    for source in metadata["tool"]["uv"]["sources"].values():
        assert source == {"workspace": True}


def test_protocol_read_extra_is_optional_and_current_cli_bound_admits_patch_successor():
    adapter = tomllib.loads(
        (MODULE / SUPPLIERS["specification_fs_sdk_adapter"][0]).read_text()
    )
    cli = tomllib.loads((MODULE / SUPPLIERS["specification_cli_python"][0]).read_text())
    assert adapter["project"]["version"] == "0.4.2"
    assert adapter["project"]["optional-dependencies"]["protocol"] == [
        "aware-protocol-fs-adapter>=0.3.0,<0.7.0"
    ]
    assert not any("protocol" in item for item in adapter["project"]["dependencies"])
    assert (
        "aware-specification-fs-sdk-adapter[protocol]>=0.4.1,<0.5.0"
        in cli["project"]["dependencies"]
    )
    selected = next(
        Requirement(value)
        for value in cli["project"]["dependencies"]
        if Requirement(value).name == "aware-specification-fs-sdk-adapter"
    )
    # Compatible metadata does not implement consumer success handling or qualify
    # installed delivery; CLI source and its entrypoint remain unchanged here.
    assert adapter["project"]["version"] in selected.specifier


def test_adapter_sdk03_dependency_is_exact_without_new_mandatory_edges():
    adapter = tomllib.loads(
        (MODULE / SUPPLIERS["specification_fs_sdk_adapter"][0]).read_text()
    )
    assert adapter["project"]["dependencies"] == [
        "aware-specification-sdk>=0.3.1,<0.4.0",
        "aware-specification-fs-adapter",
    ]


@pytest.mark.parametrize(
    ("version", "supported"),
    [
        ("0.1.99", False),
        ("0.2.0", False),
        ("0.2.1", False),
        ("0.2.99", False),
        ("0.3.0rc1", False),
        ("0.3.0", False),
        ("0.3.1", True),
        ("0.3.99", True),
        ("0.4.0", False),
    ],
)
def test_adapter_sdk_bounds_admit_only_qualified_minor_series(version, supported):
    adapter = tomllib.loads(
        (MODULE / SUPPLIERS["specification_fs_sdk_adapter"][0]).read_text()
    )
    requirement = Requirement(adapter["project"]["dependencies"][0])
    assert requirement.name == "aware-specification-sdk"
    assert (version in requirement.specifier) is supported


def test_cli_successor_dependencies_are_exact_qualified_neutral_suppliers():
    cli = tomllib.loads((MODULE / SUPPLIERS["specification_cli_python"][0]).read_text())
    assert cli["project"]["version"] == "0.2.2"
    assert cli["project"]["dependencies"] == [
        "aware-specification-sdk>=0.2.0,<0.3.0",
        "aware-specification-fs-sdk-adapter[protocol]>=0.3.0,<0.4.0",
        "aware-command-runtime>=0.1.1,<0.2.0",
    ]


@pytest.mark.parametrize(
    ("version", "supported"),
    [
        ("0.2.99", False),
        ("0.3.0", True),
        ("0.3.1", True),
        ("0.4.0", True),
        ("0.4.1", True),
        ("0.5.0rc1", False),
        ("0.5.0", True),
        ("0.5.99", True),
        ("0.6.0", True),
        ("0.6.99", True),
        ("0.7.0", False),
    ],
)
def test_protocol_extra_bounds_admit_only_qualified_minor_series(version, supported):
    adapter = tomllib.loads(
        (MODULE / SUPPLIERS["specification_fs_sdk_adapter"][0]).read_text()
    )
    requirement = Requirement(
        adapter["project"]["optional-dependencies"]["protocol"][0]
    )
    assert requirement.name == "aware-protocol-fs-adapter"
    assert (version in requirement.specifier) is supported


def test_governed_extra_selects_only_direct_neutral_owner_edges():
    metadata = tomllib.loads(
        (MODULE / SUPPLIERS["specification_fs_sdk_adapter"][0]).read_text()
    )
    assert metadata["project"]["optional-dependencies"]["governed"] == [
        "aware-protocol-fs-adapter[draft]>=0.6.1,<0.7.0",
        "aware-issue-sdk>=0.10.1,<0.11.0",
        "aware-issue-fs-adapter>=0.9.1,<0.10.0",
        "aware-file-system>=0.3.1,<0.4.0",
    ]
    for value in metadata["project"]["optional-dependencies"]["governed"]:
        requirement = Requirement(value)
        assert metadata["tool"]["uv"]["sources"][requirement.name] == {
            "workspace": True
        }
        assert requirement.extras == (
            {"draft"} if requirement.name == "aware-protocol-fs-adapter" else set()
        )


@pytest.mark.parametrize(
    ("name", "floor", "old", "ceiling"),
    [
        ("aware-protocol-fs-adapter", "0.6.1", "0.6.0", "0.7.0"),
        ("aware-issue-sdk", "0.10.1", "0.10.0", "0.11.0"),
        ("aware-issue-fs-adapter", "0.9.1", "0.9.0", "0.10.0"),
        ("aware-file-system", "0.3.1", "0.3.0", "0.4.0"),
    ],
)
def test_governed_bounds_admit_selected_profile_not_older_or_next_minor(
    name, floor, old, ceiling
):
    metadata = tomllib.loads(
        (MODULE / SUPPLIERS["specification_fs_sdk_adapter"][0]).read_text()
    )
    requirement = next(
        Requirement(value)
        for value in metadata["project"]["optional-dependencies"]["governed"]
        if Requirement(value).name == name
    )
    assert floor in requirement.specifier
    assert floor + "+draft.1" in requirement.specifier
    assert old not in requirement.specifier
    assert ceiling not in requirement.specifier
    assert ceiling + "rc1" not in requirement.specifier


def test_kernel_selects_neutral_code_without_unmaterialized_ontology_module():
    metadata = tomllib.loads((KERNEL / "aware.workspace.toml").read_text())
    assert not [
        m for m in metadata["workspace"]["modules"] if m["id"] == "specification"
    ]
    codes = metadata["workspace"]["codes"]
    for path, _ in SUPPLIERS.values():
        assert codes.count("modules/specification/" + path) == 1


def test_canonical_kernel_projection_selects_only_neutral_spec_code():
    metadata = tomllib.loads((KERNEL / "pyproject.toml").read_text())
    uv = metadata["tool"]["uv"]
    members = [
        p for p in uv["workspace"]["members"] if p.startswith("modules/specification/")
    ]
    assert set(members) == {
        "modules/specification/libs/runtime/python",
        "modules/specification/libs/fs_source_contract/python",
        "modules/specification/libs/fs_adapter/python",
        "modules/specification/sdks/specification/python/public",
        "modules/specification/sdks/specification/python/fs_adapter",
        "modules/specification/sdks/specification/python/cli",
    }
    assert len(members) == 6
    for _, name in SUPPLIERS.values():
        assert uv["sources"][name] == {"workspace": True}
    assert not any("ontology" in p or "apis" in p or "services" in p for p in members)
