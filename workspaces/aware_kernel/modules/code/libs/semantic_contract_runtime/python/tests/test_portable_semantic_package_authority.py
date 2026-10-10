from __future__ import annotations

import copy
import hashlib
import json
import pickle
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import pytest

from aware_code_semantic_contract_runtime import (
    CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_DIGEST,
    CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_SCHEMA,
    CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION,
    CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_MEDIA_TYPE,
    CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_REF_ROLE,
    CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA,
    CodeEmptySemanticMetadata,
    CodePortableCodePackage,
    CodePortableSemanticContract,
    CodePortableSemanticPackage,
    CodePortableSemanticPackageAuthority,
    CodePortableSemanticPackageAuthorityRef,
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
    code_portable_semantic_package_authority_body_ref,
    create_portable_semantic_package_authority,
)

_FIXTURE = (
    Path(__file__).parent / "fixtures/portable-semantic-package-authority-v1.json"
)
_AUTHORITY_DOMAIN = b"aware.code.portable-semantic-package-authority.v1\0"


def _authority(**changes: object) -> CodePortableSemanticPackageAuthority:
    values: dict[str, object] = {
        "manifest_contract_kind": "ontology",
        "manifest_relative_path": "aware.package.toml",
        "code_package": CodePortableCodePackage(
            name="aware-meta",
            language="python",
            manifest_kind="ontology",
            source_code_package_id="11111111-1111-4111-8111-111111111111",
            config_id="22222222-2222-4222-8222-222222222222",
            config_key="aware.meta",
            surface="runtime",
        ),
        "semantic_provider_key": "aware.meta",
        "semantic_package": CodePortableSemanticPackage(
            family="aware", kind="ontology", name="meta-ontology"
        ),
        "semantic_contract": CodePortableSemanticContract(
            role="ontology",
            name="meta-ontology",
            provider_key="aware.meta",
            coordinate="aware.meta.ontology",
        ),
        "semantic_version": "1.0.0",
        "package_ref": "package:meta-ontology@1.0.0",
        "fqn_prefix": "aware_meta",
        "sources_root": "src",
        "declared_source_paths": (
            "src/aware_meta/__init__.aware",
            "src/aware_meta/model.aware",
        ),
        "direct_dependency_package_refs": (
            "package:code-runtime@1.0.0",
            "package:ontology-runtime@1.0.0",
        ),
        "owned_semantic_root_refs": (
            "aware.meta.Class",
            "aware.meta.Relationship",
        ),
        "semantic_metadata": CodeEmptySemanticMetadata(),
    }
    values.update(changes)
    return create_portable_semantic_package_authority(**cast(Any, values))


def _golden() -> bytes:
    return _FIXTURE.read_bytes()


def _redigest(wire: dict[str, object]) -> None:
    payload = dict(wire)
    payload.pop("authority_digest", None)
    wire["authority_digest"] = (
        "sha256:"
        + hashlib.sha256(_AUTHORITY_DOMAIN + canonical_json_bytes(payload)).hexdigest()
    )


def _canonical(wire: dict[str, object]) -> bytes:
    return json.dumps(
        wire, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _seal(wire: Mapping[str, object]) -> str:
    return ContentDigest.of_bytes(canonical_json_bytes(wire)).value


def test_positive_golden_round_trip_and_content_reference() -> None:
    authority = _authority()
    assert authority.canonical_bytes() == _golden()
    assert authority.authority_digest.value == (
        "sha256:f9a4d776c803c4fe7311354c3ac0ac0d5a799c8cc14e42115aa74cfae3c32131"
    )
    assert CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_DIGEST.value == (
        "sha256:82ae1093f5368c7e707450f0af9c63ffe2f4ef5634e17fd65e741d5d01bc68f9"
    )
    assert (
        CodePortableSemanticPackageAuthority.from_wire(
            authority.to_wire()
        ).canonical_bytes()
        == _golden()
    )
    assert (
        CodePortableSemanticPackageAuthority.from_canonical_bytes(
            _golden()
        ).canonical_bytes()
        == _golden()
    )
    reference = code_portable_semantic_package_authority_body_ref(authority)
    assert reference.role == CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_REF_ROLE
    assert reference.schema == CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA
    assert reference.media_type == CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_MEDIA_TYPE
    assert (
        reference.codec_version
        == CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION
    )
    assert (
        reference.codec_digest.value
        == CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_DIGEST.value
    )
    assert reference.sha256.value == (
        "sha256:652ffc8845033b9cd3c3f4c433192f69a2946839fe6054ca158a5c985faa0487"
    )
    assert reference.size_bytes == 1141
    assert reference.ref == (
        "cas://aware.code/portable-semantic-package-authority/sha256/"
        "652ffc8845033b9cd3c3f4c433192f69a2946839fe6054ca158a5c985faa0487.json"
    )


def test_exact_public_surface_has_no_parallel_codec_aliases() -> None:
    import aware_code_semantic_contract_runtime as package

    expected = {
        "CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_DIGEST",
        "CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_SCHEMA",
        "CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION",
        "CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_MEDIA_TYPE",
        "CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_REF_ROLE",
        "CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA",
        "CodeEmptySemanticMetadata",
        "CodePortableCodePackage",
        "CodePortableSemanticContract",
        "CodePortableSemanticPackage",
        "CodePortableSemanticPackageAuthority",
        "CodePortableSemanticPackageAuthorityRef",
        "code_portable_semantic_package_authority_body_ref",
        "create_portable_semantic_package_authority",
    }
    assert expected <= set(package.__all__)
    assert not hasattr(package, "encode_code_portable_semantic_package_authority")
    assert not hasattr(package, "decode_code_portable_semantic_package_authority")
    assert not hasattr(package, "create_code_portable_semantic_package_authority")
    with pytest.raises(ContractViolation, match="strict decoder"):
        CodePortableSemanticPackageAuthority()
    with pytest.raises(ContractViolation, match="body_ref"):
        CodePortableSemanticPackageAuthorityRef()


def test_cross_workspace_context_is_inert_and_bytes_remain_identical() -> None:
    context_a = ("workspace-a", "origin-a", "/checkout/a")
    context_b = ("workspace-b", "origin-b", "/checkout/b")
    assert context_a != context_b
    first = _authority()
    second = _authority()
    assert first.canonical_bytes() == second.canonical_bytes()
    assert (
        code_portable_semantic_package_authority_body_ref(first).ref
        == code_portable_semantic_package_authority_body_ref(second).ref
    )


@pytest.mark.parametrize("field", ["schema", "code_package", "semantic_contract"])
def test_missing_and_extra_fields_fail(field: str) -> None:
    wire = _authority().to_wire()
    del wire[field]
    with pytest.raises(ContractViolation, match="field set"):
        CodePortableSemanticPackageAuthority.from_wire(wire)
    wire = _authority().to_wire()
    wire["workspace_id"] = "forbidden"
    with pytest.raises(ContractViolation, match="field set"):
        CodePortableSemanticPackageAuthority.from_wire(wire)


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        (b'{"codec_version":true}', "field set"),
        (_golden().replace(b'"codec_version":1', b'"codec_version":true'), "int"),
        (_golden().replace(b'"codec_version":1', b'"codec_version":1.0'), "floating"),
        (_golden().replace(b'"codec_version":1', b'"codec_version":NaN'), "constant"),
    ],
)
def test_boolean_float_and_constant_substitutions_fail(
    payload: bytes, error: str
) -> None:
    with pytest.raises((ContractViolation, TypeError), match=error):
        CodePortableSemanticPackageAuthority.from_canonical_bytes(payload)


def test_duplicate_keys_fail_at_top_level_and_nested_depth() -> None:
    top = _golden()[:-1] + b',"schema":"other"}'
    nested = _golden().replace(
        b'"name":"aware-meta"',
        b'"name":"aware-meta","name":"other"',
        1,
    )
    for payload in (top, nested):
        with pytest.raises(ContractViolation, match="duplicate"):
            CodePortableSemanticPackageAuthority.from_canonical_bytes(payload)


@pytest.mark.parametrize(
    "payload",
    [
        b"\xef\xbb\xbf" + _golden(),
        _golden() + b"\n",
        json.dumps(json.loads(_golden()), indent=2).encode(),
        _golden().replace(b"aware_meta", b"aware\\u005fmeta", 1),
    ],
)
def test_noncanonical_bytes_fail(payload: bytes) -> None:
    with pytest.raises(ContractViolation, match="canonical|invalid"):
        CodePortableSemanticPackageAuthority.from_canonical_bytes(payload)


@pytest.mark.parametrize(
    "changes",
    [
        {"manifest_relative_path": "/aware.package.toml"},
        {"manifest_relative_path": "a/../aware.package.toml"},
        {"manifest_relative_path": "aware\\package.toml"},
        {"manifest_relative_path": "aware//package.toml"},
        {"manifest_relative_path": "e\u0301.toml"},
        {"sources_root": "src/"},
        {"declared_source_paths": ("other/model.aware",)},
        {"fqn_prefix": " aware_meta"},
    ],
)
def test_text_path_and_containment_poisons_fail(changes: dict[str, object]) -> None:
    with pytest.raises(ContractViolation):
        _authority(**changes)


def test_uuid_and_nullable_field_poisoning_fails() -> None:
    with pytest.raises(ContractViolation, match="lowercase"):
        _authority(
            code_package=CodePortableCodePackage(
                name="aware-meta",
                language="python",
                manifest_kind="ontology",
                source_code_package_id="AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA",
                config_id=None,
                config_key=None,
                surface=None,
            )
        )
    wire = _authority().to_wire()
    cast(dict[str, object], wire["code_package"])["surface"] = 1
    _redigest(wire)
    with pytest.raises(TypeError):
        CodePortableSemanticPackageAuthority.from_wire(wire)


@pytest.mark.parametrize(
    "changes",
    [
        {"declared_source_paths": ["src/aware_meta/model.aware"]},
        {
            "declared_source_paths": (
                "src/aware_meta/model.aware",
                "src/aware_meta/__init__.aware",
            )
        },
        {
            "declared_source_paths": (
                "src/aware_meta/model.aware",
                "src/aware_meta/model.aware",
            )
        },
        {"direct_dependency_package_refs": ("package:meta-ontology@1.0.0",)},
    ],
)
def test_exact_ordered_tuple_and_self_dependency_poisons_fail(
    changes: dict[str, object],
) -> None:
    with pytest.raises((ContractViolation, TypeError)):
        _authority(**changes)


def test_package_provider_and_manifest_cross_field_laws_fail() -> None:
    with pytest.raises(ContractViolation, match="package_ref"):
        _authority(package_ref="package:other@1.0.0")
    with pytest.raises(ContractViolation, match="provider"):
        _authority(semantic_provider_key="aware.other")
    with pytest.raises(ContractViolation, match="manifest kind"):
        _authority(manifest_contract_kind="schema")


def test_digest_metadata_and_workspace_restamping_fail() -> None:
    wire = _authority().to_wire()
    wire["authority_digest"] = "sha256:" + "0" * 64
    with pytest.raises(ContractViolation, match="authority_digest"):
        CodePortableSemanticPackageAuthority.from_wire(wire)
    wire = _authority().to_wire()
    wire["semantic_metadata"] = {"workspace_id": "forbidden"}
    _redigest(wire)
    with pytest.raises(ContractViolation, match="field set"):
        CodePortableSemanticPackageAuthority.from_wire(wire)
    with pytest.raises(TypeError):
        _authority(code_package=cast(Any, {"name": "aware-meta"}))


def test_exact_and_nested_mutation_fail_even_after_public_digest_restamping() -> None:
    authority = _authority()
    changed_wire = authority.to_wire()
    changed_wire["fqn_prefix"] = "other"
    _redigest(changed_wire)
    object.__setattr__(authority, "fqn_prefix", "other")
    object.__setattr__(
        authority,
        "authority_digest",
        ContentDigest(cast(str, changed_wire["authority_digest"])),
    )
    object.__setattr__(authority, "_seal", _seal(changed_wire))
    with pytest.raises(ContractViolation, match="mutated"):
        authority.canonical_bytes()

    authority = _authority()
    changed_wire = authority.to_wire()
    cast(dict[str, object], changed_wire["code_package"])["name"] = "other"
    _redigest(changed_wire)
    object.__setattr__(authority.code_package, "name", "other")
    object.__setattr__(
        authority.code_package,
        "_seal",
        _seal(cast(dict[str, object], changed_wire["code_package"])),
    )
    object.__setattr__(
        authority,
        "authority_digest",
        ContentDigest(cast(str, changed_wire["authority_digest"])),
    )
    object.__setattr__(authority, "_seal", _seal(changed_wire))
    with pytest.raises(ContractViolation, match="mutated"):
        authority.code_package.__post_init__()
    with pytest.raises(ContractViolation, match="mutated"):
        authority.to_wire()


@pytest.mark.parametrize(
    ("value", "field_name", "replacement"),
    [
        (
            CodePortableSemanticPackage(
                family="aware", kind="ontology", name="meta-ontology"
            ),
            "family",
            "other",
        ),
        (
            CodePortableSemanticContract(
                role="ontology",
                name="meta-ontology",
                provider_key="aware.meta",
                coordinate="aware.meta.ontology",
            ),
            "coordinate",
            "aware.other.ontology",
        ),
    ],
)
def test_nested_values_cannot_reseal_after_mutation(
    value: object, field_name: str, replacement: str
) -> None:
    object.__setattr__(value, field_name, replacement)
    if type(value) is CodePortableSemanticPackage:
        wire = {
            "family": value.family,
            "kind": value.kind,
            "name": value.name,
        }
    else:
        contract = cast(CodePortableSemanticContract, value)
        wire = {
            "coordinate": contract.coordinate,
            "name": contract.name,
            "provider_key": contract.provider_key,
            "role": contract.role,
        }
    object.__setattr__(value, "_seal", _seal(wire))
    with pytest.raises(ContractViolation, match="mutated"):
        cast(Any, value).__post_init__()


def test_marker_and_seal_restamping_cannot_replace_issuance_state() -> None:
    authority = _authority()
    changed_wire = authority.to_wire()
    changed_wire["fqn_prefix"] = "other"
    _redigest(changed_wire)
    object.__setattr__(authority, "fqn_prefix", "other")
    object.__setattr__(
        authority,
        "authority_digest",
        ContentDigest(cast(str, changed_wire["authority_digest"])),
    )
    object.__setattr__(authority, "_marker", object())
    object.__setattr__(authority, "_seal", _seal(changed_wire))
    with pytest.raises(ContractViolation, match="incomplete|mutated"):
        authority.canonical_bytes()


def test_foreign_nested_and_authority_subclasses_dispatch_no_methods() -> None:
    class ForeignCodePackage(CodePortableCodePackage):
        calls = 0

        def __getattribute__(self, name: str) -> object:
            type(self).calls += 1
            return super().__getattribute__(name)

    foreign = object.__new__(ForeignCodePackage)
    authority = _authority()
    object.__setattr__(authority, "code_package", foreign)
    with pytest.raises(TypeError, match="exact"):
        authority.canonical_bytes()
    assert ForeignCodePackage.calls == 0

    class ForeignAuthority(CodePortableSemanticPackageAuthority):
        pass

    with pytest.raises(TypeError, match="exact"):
        ForeignAuthority.from_canonical_bytes(_golden())


def test_copy_pickle_and_incomplete_construction_fail() -> None:
    authority = _authority()
    for operation in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(ContractViolation):
            operation(authority)
    incomplete = object.__new__(CodePortableSemanticPackageAuthority)
    with pytest.raises(ContractViolation, match="incomplete"):
        incomplete.to_wire()
    empty = object.__new__(CodeEmptySemanticMetadata)
    with pytest.raises(ContractViolation, match="incomplete"):
        empty.__post_init__()


def test_content_reference_rejects_substitution_and_coherent_restamping() -> None:
    reference = code_portable_semantic_package_authority_body_ref(_authority())
    object.__setattr__(reference, "ref", reference.ref + ".other")
    with pytest.raises(ContractViolation, match="URI"):
        reference.__post_init__()

    reference = code_portable_semantic_package_authority_body_ref(_authority())
    other = ContentDigest("sha256:" + "e" * 64)
    object.__setattr__(reference, "sha256", other)
    object.__setattr__(
        reference,
        "ref",
        "cas://aware.code/portable-semantic-package-authority/sha256/"
        + "e" * 64
        + ".json",
    )
    object.__setattr__(reference, "size_bytes", 7)
    wire = {
        "codec_digest": reference.codec_digest.value,
        "codec_version": reference.codec_version,
        "media_type": reference.media_type,
        "ref": reference.ref,
        "role": reference.role,
        "schema": reference.schema,
        "sha256": reference.sha256.value,
        "size_bytes": reference.size_bytes,
    }
    object.__setattr__(reference, "_seal", _seal(wire))
    with pytest.raises(ContractViolation, match="mutated"):
        reference.__post_init__()


def test_from_wire_rejects_foreign_containers_and_nonempty_metadata() -> None:
    class ForeignDict(dict[str, object]):
        pass

    class ForeignList(list[object]):
        pass

    with pytest.raises(TypeError, match="exact dict"):
        CodePortableSemanticPackageAuthority.from_wire(
            ForeignDict(_authority().to_wire())
        )
    wire = _authority().to_wire()
    wire["declared_source_paths"] = ForeignList(
        cast(list[object], wire["declared_source_paths"])
    )
    with pytest.raises(TypeError, match="exact list"):
        CodePortableSemanticPackageAuthority.from_wire(wire)


def test_codec_declaration_constants_are_exact() -> None:
    assert CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA == (
        "aware.code.portable-semantic-package-authority.v1"
    )
    assert CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_SCHEMA == (
        "aware.code.portable-semantic-package-authority-codec.v1"
    )
    assert CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_VERSION == 1
    assert CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_MEDIA_TYPE.endswith("version=1")
