from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from aware_meta_type_schema.codec import TypeSchemaDecodeError, decode_schema_bundle
from aware_meta_type_schema.composition import (
    TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT,
    TypeOwnerBinding,
    resolve_composed_slice,
)
from aware_meta_type_schema.composition_codec import (
    TypeSchemaCompositionDecodeError,
    decode_catalog_root,
    decode_composed_slice,
    decode_definition_fragment,
    decode_package_root,
    decode_source_attribution_fragment,
    decode_type_owner_binding,
    encode_composition_value,
    negotiate_composition_contract,
)
from aware_meta_type_schema.composition_transition import (
    DefinitionFragmentMovement,
    PackageRootMovement,
    SourceAttributionFragmentMovement,
    TypeOwnerBindingMovement,
    create_typed_empty_catalog,
    create_typed_empty_package,
    transition_catalog,
    transition_package,
)
from aware_meta_type_schema.definition_fragment import (
    SourceDefinitionBinding,
    TypeDefinitionFragment,
    TypeSchemaSourceAttributionFragment,
)
from aware_meta_type_schema.encoding import canonical_json, digest_payload
from aware_meta_type_schema.model import ScalarKind, TypeDefinition, TypeKind
from aware_meta_type_schema.persistent_index import PersistentBodyAuthority
from aware_meta_type_schema.positive_reader import (
    PositiveBodyRead,
    TypeSchemaPositiveReaderCapability,
)


@dataclass
class _Store:
    bodies: dict[str, PersistentBodyAuthority]

    def ingest(self, values: tuple[PersistentBodyAuthority, ...]) -> None:
        self.bodies.update((value.coordinate.body_ref, value) for value in values)

    def reader(self) -> TypeSchemaPositiveReaderCapability:
        def read(expected):
            body = self.bodies[expected.body_ref]
            return PositiveBodyRead(
                body.coordinate.body_ref,
                body.coordinate.body_digest,
                body.coordinate.size_bytes,
                body.coordinate.schema,
                body.canonical_bytes,
            )

        return TypeSchemaPositiveReaderCapability(
            request_ref="request:codec", read_body=read
        )


def _values():
    fragment = TypeDefinitionFragment.create(
        TypeDefinition(
            type_ref="content.Text",
            name="Text",
            kind=TypeKind.SCALAR_ALIAS,
            scalar_target=ScalarKind.STRING,
        )
    )
    attribution = TypeSchemaSourceAttributionFragment.create(
        package_ref="package:content@1.0.0",
        source_path="text/text.aware",
        document_coordinate_ref="coordinate:content",
        bindings=(
            SourceDefinitionBinding(fragment.type_ref, fragment.to_body().coordinate),
        ),
    )
    store = _Store({})
    empty_package, empty_package_bodies = create_typed_empty_package(
        package_ref="package:content@1.0.0",
        package_name="content",
        namespace="content",
        semantic_version="1.0.0",
    )
    store.ingest(empty_package_bodies)
    package_transition = transition_package(
        empty_package,
        definition_movements=(
            DefinitionFragmentMovement(fragment.type_ref, None, fragment),
        ),
        attribution_movements=(
            SourceAttributionFragmentMovement(
                attribution.source_path, None, attribution
            ),
        ),
        reader=store.reader(),
        request_ref="request:codec",
    )
    store.ingest(package_transition.emitted_bodies)
    package = package_transition.successor
    owner = TypeOwnerBinding.create(
        type_ref=fragment.type_ref,
        package_ref=package.package_ref,
    )
    empty_catalog, empty_catalog_bodies = create_typed_empty_catalog(
        target_package_ref=package.package_ref
    )
    store.ingest(empty_catalog_bodies)
    catalog_transition = transition_catalog(
        empty_catalog,
        package_movements=(
            PackageRootMovement(package.package_ref, None, package, package_transition),
        ),
        owner_movements=(TypeOwnerBindingMovement(owner.type_ref, None, owner),),
        reader=store.reader(),
        request_ref="request:codec",
    )
    store.ingest(catalog_transition.emitted_bodies)
    catalog = catalog_transition.successor
    composed = resolve_composed_slice(
        catalog,
        root_type_refs=(fragment.type_ref,),
        reader=store.reader(),
        request_ref="request:codec",
    ).slice
    return fragment, attribution, package, owner, catalog, composed


def test_all_composition_authorities_round_trip_canonical_bytes() -> None:
    values = _values()
    decoders = (
        decode_definition_fragment,
        decode_source_attribution_fragment,
        decode_package_root,
        decode_type_owner_binding,
        decode_catalog_root,
        decode_composed_slice,
    )
    for value, decoder in zip(values, decoders, strict=True):
        encoded = encode_composition_value(value)
        decoded = decoder(encoded)
        assert decoded == value
        assert encode_composition_value(decoded) == encoded


def test_composed_slice_codec_rejects_coherently_restamped_evidence() -> None:
    composed = _values()[-1]
    wire = json.loads(encode_composition_value(composed))
    wire["owners"][0]["definition"] = wire["owners"][0]["owner"]
    semantic = {key: value for key, value in wire.items() if key != "slice_ref"}
    wire["slice_ref"] = digest_payload(composed.contract, semantic)
    with pytest.raises(TypeSchemaCompositionDecodeError, match="definition coordinate"):
        decode_composed_slice(canonical_json(wire).encode())

    wire = json.loads(encode_composition_value(composed))
    wire["packages"][0]["coordinate"] = wire["owners"][0]["owner"]
    semantic = {key: value for key, value in wire.items() if key != "slice_ref"}
    wire["slice_ref"] = digest_payload(composed.contract, semantic)
    with pytest.raises(TypeSchemaCompositionDecodeError, match="exact package root"):
        decode_composed_slice(canonical_json(wire).encode())

    wire = json.loads(encode_composition_value(composed))
    empty_catalog, _ = create_typed_empty_catalog(
        target_package_ref=composed.target_package_ref
    )
    wire["catalog"] = empty_catalog.catalog.to_wire()
    semantic = {key: value for key, value in wire.items() if key != "slice_ref"}
    wire["slice_ref"] = digest_payload(composed.contract, semantic)
    with pytest.raises(TypeSchemaCompositionDecodeError, match="membership proofs"):
        decode_composed_slice(canonical_json(wire).encode())

    wire = json.loads(encode_composition_value(composed))
    package_root_ref = wire["catalog"]["package_index"]["root_ref"]
    membership = next(
        value
        for value in wire["membership_proofs"]["memberships"]
        if value["root"]["root_ref"] == package_root_ref
    )
    membership["value"] = wire["owners"][0]["owner"]
    membership_semantic = {
        key: value for key, value in membership.items() if key != "membership_ref"
    }
    membership["membership_ref"] = digest_payload(
        membership["contract"], membership_semantic
    )
    bundle = wire["membership_proofs"]
    bundle_semantic = {
        key: value for key, value in bundle.items() if key != "bundle_ref"
    }
    bundle["bundle_ref"] = digest_payload(bundle["contract"], bundle_semantic)
    semantic = {key: value for key, value in wire.items() if key != "slice_ref"}
    wire["slice_ref"] = digest_payload(composed.contract, semantic)
    with pytest.raises(TypeSchemaCompositionDecodeError):
        decode_composed_slice(canonical_json(wire).encode())


def test_codec_rejects_unknown_duplicate_noncanonical_and_unsupported_contract() -> (
    None
):
    fragment = _values()[0]
    payload = fragment.to_wire()
    payload["unknown"] = True
    with pytest.raises(TypeSchemaCompositionDecodeError, match="fields"):
        decode_definition_fragment(
            json.dumps(payload, sort_keys=True, separators=(",", ":"))
        )
    with pytest.raises(TypeSchemaCompositionDecodeError, match="duplicate"):
        decode_definition_fragment(b'{"contract":"a","contract":"b"}')
    with pytest.raises(TypeSchemaCompositionDecodeError, match="canonical"):
        decode_definition_fragment(b" " + encode_composition_value(fragment))
    with pytest.raises(TypeSchemaCompositionDecodeError, match="no supported"):
        negotiate_composition_contract(("aware.meta.type-schema.future.v2",))


def test_recomputed_ref_substitution_and_v1_cross_decode_fail_closed() -> None:
    fragment = _values()[0]
    payload = fragment.to_wire()
    payload["referenced_type_refs"] = ["substituted.Type"]
    semantic = {key: value for key, value in payload.items() if key != "fragment_ref"}
    payload["fragment_ref"] = digest_payload(fragment.contract, semantic)
    with pytest.raises(TypeSchemaCompositionDecodeError):
        decode_definition_fragment(
            json.dumps(payload, sort_keys=True, separators=(",", ":"))
        )

    with pytest.raises(TypeSchemaDecodeError):
        decode_schema_bundle(encode_composition_value(fragment))
    v1_shaped = {
        "contract": "aware.meta.semantic-type-schema.v1",
        "namespace": "content",
        "semantic_version": "1.0.0",
        "types": [],
        "schema_digest": "sha256:" + "0" * 64,
    }
    with pytest.raises(TypeSchemaCompositionDecodeError):
        decode_package_root(
            json.dumps(v1_shaped, sort_keys=True, separators=(",", ":"))
        )


def test_package_decoder_rejects_recomputed_contract_substitution() -> None:
    package = _values()[2]
    payload = package.to_wire()
    payload["contract"] = "aware.meta.type-schema.package-root.v2"
    semantic = {
        key: value for key, value in payload.items() if key != "package_root_ref"
    }
    payload["package_root_ref"] = digest_payload(
        TYPE_SCHEMA_PACKAGE_ROOT_CONTRACT,
        semantic,
    )
    with pytest.raises(TypeSchemaCompositionDecodeError):
        decode_package_root(json.dumps(payload, sort_keys=True, separators=(",", ":")))
