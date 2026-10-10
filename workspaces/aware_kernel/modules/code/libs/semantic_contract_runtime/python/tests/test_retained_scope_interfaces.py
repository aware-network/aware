import ast
from dataclasses import replace
from pathlib import Path

import pytest
from aware_code_semantic_contract_runtime import retained_scope_interfaces as scope
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)


def body(path, data=b"retained bytes"):
    return scope.CodeRetainedScopeBody(
        path, "body:" + path, ContentDigest.of_bytes(data), data
    )


def fixture():
    module = scope.CodeRetainedScopeModule("demo", body("demo/aware.module.toml"))
    package = scope.CodeRetainedScopePackage(
        "demo",
        "home",
        "environment",
        module.manifest.relative_path,
        "demo/home",
        "aware.environment.toml",
        ContentDigest.of_bytes(b"source"),
        body("demo/home/aware.environment.toml"),
    )
    return scope.CodeRetainedScopeProjection(
        "repository:original",
        ContentDigest.of_bytes(b"observation"),
        body("aware.workspace.toml"),
        (module,),
        (package,),
    )


def test_deterministic_complete_digest_and_raw_bytes():
    value = fixture()
    assert value == fixture()
    assert value.projection_digest == fixture().projection_digest
    assert value.projection_digest == ContentDigest.of_bytes(
        scope.encode_retained_scope_projection(value)
    )
    binary = body("arbitrary", b"\x00\xff\r\n")
    assert binary.to_wire()["body_hex"] == "00ff0d0a"


@pytest.mark.parametrize(
    "field,value",
    [
        ("relative_path", "../escape"),
        ("relative_path", "/absolute"),
        ("body_ref", ""),
        ("content_digest", ContentDigest.of_bytes(b"substitute")),
        ("body", bytearray(b"retained bytes")),
    ],
)
def test_body_rejections(field, value):
    with pytest.raises((ContractViolation, TypeError)):
        replace(body("file"), **{field: value})


def test_projection_digest_covers_all_fields_and_unfiltered_rows():
    value = fixture()
    changes = [
        replace(value, repository_binding_ref="repository:other"),
        replace(value, observation_digest=ContentDigest.of_bytes(b"other")),
        replace(value, workspace_manifest=body("aware.workspace.toml", b"comment")),
        replace(value, packages=()),
        replace(value, packages=(replace(value.packages[0], package_kind="other"),)),
        replace(
            value,
            packages=(
                replace(
                    value.packages[0],
                    source_identity_digest=ContentDigest.of_bytes(b"other"),
                ),
            ),
        ),
        replace(
            value,
            modules=(
                replace(
                    value.modules[0],
                    manifest=body("demo/aware.module.toml", b"comment"),
                ),
            ),
        ),
        replace(
            value,
            packages=(
                replace(
                    value.packages[0],
                    manifest=body("demo/home/aware.environment.toml", b"comment"),
                ),
            ),
        ),
    ]
    assert all(
        change.projection_digest != value.projection_digest for change in changes
    )
    # Portable omission is constructible, but has a different digest. Only the
    # original validator can prove enumeration completeness.
    assert replace(value, packages=()).packages == ()


@pytest.mark.parametrize(
    "change",
    ["duplicate_module", "duplicate_package", "foreign_module", "wrong_path", "list"],
)
def test_correspondence_rejections(change):
    value = fixture()
    with pytest.raises(ContractViolation):
        if change == "duplicate_module":
            replace(value, modules=value.modules * 2)
        elif change == "duplicate_package":
            replace(value, packages=value.packages * 2)
        elif change == "foreign_module":
            replace(value, packages=(replace(value.packages[0], module_id="foreign"),))
        elif change == "wrong_path":
            replace(value.packages[0], manifest_relative_path="different.toml")
        else:
            replace(value, modules=list(value.modules))


def test_ordering_is_not_normalized():
    value = fixture()
    other = replace(value.packages[0], package_id="aaa")
    with pytest.raises(ContractViolation):
        replace(value, packages=(value.packages[0], other))
    assert len(replace(value, packages=(other, value.packages[0])).packages) == 2


def test_retained_reference_substitution_rejects():
    value = fixture()
    forged = replace(
        body(value.packages[0].manifest.relative_path, b"different content"),
        body_ref=value.workspace_manifest.body_ref,
    )
    with pytest.raises(ContractViolation):
        replace(value, packages=(replace(value.packages[0], manifest=forged),))


@pytest.mark.parametrize(
    "bound",
    [
        "MAX_SCOPE_ITEMS",
        "MAX_SCOPE_BODY_BYTES",
        "MAX_SCOPE_TOTAL_BYTES",
        "MAX_SCOPE_CANONICAL_BYTES",
    ],
)
def test_bounds_at_encoding_revalidation(monkeypatch, bound):
    value = fixture()
    monkeypatch.setattr(scope, bound, 0)
    with pytest.raises(ContractViolation):
        scope.encode_retained_scope_projection(value)


def test_no_workspace_or_module_parser_dependency():
    tree = ast.parse(Path(scope.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 1 or node.module in {
                "__future__",
                "dataclasses",
                "typing",
            }
        elif isinstance(node, ast.Import):
            pytest.fail("unexpected absolute import")


def test_identical_content_shares_original_ref_across_paths():
    value = fixture()
    shared = replace(
        value.packages[0].manifest, body_ref=value.workspace_manifest.body_ref
    )
    result = replace(value, packages=(replace(value.packages[0], manifest=shared),))
    assert result.workspace_manifest.body_ref == result.packages[0].manifest.body_ref
    assert (
        result.workspace_manifest.relative_path
        != result.packages[0].manifest.relative_path
    )
    wire = result.to_wire()
    assert wire["workspace_manifest"]["relative_path"] == "aware.workspace.toml"
    assert (
        wire["packages"][0]["manifest"]["relative_path"]
        == "demo/home/aware.environment.toml"
    )
    assert result.projection_digest != value.projection_digest


def test_shared_reference_does_not_relax_path_consistency():
    value = fixture()
    package = replace(
        value.packages[0],
        package_root=".",
        manifest_relative_path="aware.workspace.toml",
        manifest=body("aware.workspace.toml", b"different content"),
    )
    with pytest.raises(ContractViolation, match="path substitution"):
        replace(value, packages=(package,))
