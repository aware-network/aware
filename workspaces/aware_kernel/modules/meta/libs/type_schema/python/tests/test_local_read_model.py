"""Independent owning-schema equivalence and original local model lifecycle."""

import copy
import json
import threading
import time

import pytest
from aware_meta_type_schema import codec, encoding, model, validation
from aware_meta_type_schema.local_read_model import (
    LocalReadModelEvidence,
    create_local_model_owner,
    validate_local_model_owner,
    verify_local_model,
)


def original_model(*, scalar=model.ScalarKind.STRING, reverse=False):
    fields = (
        model.FieldDefinition(
            "local.Root.identity",
            "identity",
            model.ValueShape.scalar(scalar),
            required=True,
        ),
        model.FieldDefinition(
            "local.Root.label",
            "label",
            model.ValueShape.scalar(model.ScalarKind.STRING),
            required=True,
        ),
    )
    root = model.TypeDefinition(
        "local.Root",
        "Root",
        model.TypeKind.GRAPH_OBJECT,
        fields=fields[::-1] if reverse else fields,
        identity=model.IdentityDefinition(("local.Root.identity",)),
    )
    bundle = model.TypeSchemaBundle.create(
        namespace="local", semantic_version="1.0.0", types=(root,)
    )
    derived = model.TypeSchemaSlice.create(bundle, root_type_refs=("local.Root",))
    return bundle, derived


def appointment(
    *,
    scalar=model.ScalarKind.STRING,
    reverse=False,
    topology=b'{"contract":"opaque-original-topology"}',
    model_ref="local:model",
):
    bundle, derived = original_model(scalar=scalar, reverse=reverse)
    assert validation.validate_schema_bundle(bundle).is_valid
    return {
        "model_ref": model_ref,
        "model_revision_ref": "local:revision",
        "root_type_ref": "local.Root",
        "projection_ref": "local:projection",
        "bundle_bytes": codec.encode_schema_bundle(bundle),
        "slice_bytes": codec.encode_schema_slice(derived),
        "topology_bytes": topology,
    }


def owner():
    return create_local_model_owner(
        owner_ref="meta:local",
        owner_generation="local:generation",
        source_definition_ref="local:source-definition",
    )


def wire(value):
    return encoding.canonical_json(value).encode("utf-8")


@pytest.mark.parametrize(
    "scalar",
    (model.ScalarKind.STRING, model.ScalarKind.INTEGER, model.ScalarKind.BOOLEAN),
)
@pytest.mark.parametrize("reverse", (False, True))
def test_exact_original_model_and_slice_equivalence(scalar, reverse):
    args = appointment(scalar=scalar, reverse=reverse)
    bundle = codec.decode_schema_bundle(args["bundle_bytes"])
    supplied = codec.decode_schema_slice(args["slice_bytes"])
    assert codec.encode_schema_bundle(bundle) == args["bundle_bytes"]
    assert (
        codec.encode_schema_slice(
            model.TypeSchemaSlice.create(bundle, root_type_refs=("local.Root",))
        )
        == args["slice_bytes"]
    )
    assert validation.validate_schema_bundle(bundle).is_valid
    assert supplied.bundle_digest == bundle.schema_digest
    o = owner()
    h = o.appoint(**args)
    validate_local_model_owner(o)
    e = verify_local_model(o, h)
    assert (
        e.bundle_bytes is args["bundle_bytes"] and e.slice_bytes is args["slice_bytes"]
    )
    assert e.topology_bytes is args["topology_bytes"]
    assert (
        json.loads(e.model_admission_bytes)["profile"]
        == "aware.meta.local-single-graph-scalar-read-model.v1"
    )
    o.release(h)
    o.close()


@pytest.mark.parametrize(
    "change",
    (
        "unknown_bundle_key",
        "bundle_digest",
        "field_duplicate_ref",
        "field_duplicate_name",
        "identity_absent",
        "identity_foreign",
        "identity_duplicate",
        "scalar_inactive_key",
        "root_kind",
        "required_integer",
        "has_default_integer",
        "slice_digest",
    ),
)
def test_structural_refusals_match_original_owning_grammar(change):
    args = appointment()
    body = json.loads(args["bundle_bytes"])
    root = body["types"][0]
    if change == "unknown_bundle_key":
        body["extra"] = None
    elif change == "bundle_digest":
        body["schema_digest"] = "sha256:" + "0" * 64
    elif change == "field_duplicate_ref":
        root["fields"][1]["field_ref"] = root["fields"][0]["field_ref"]
    elif change == "field_duplicate_name":
        root["fields"][1]["name"] = root["fields"][0]["name"]
    elif change == "identity_absent":
        root["identity"]["field_refs"] = []
    elif change == "identity_foreign":
        root["identity"]["field_refs"] = ["local.Root.absent"]
    elif change == "identity_duplicate":
        root["identity"]["field_refs"] *= 2
    elif change == "scalar_inactive_key":
        root["fields"][0]["shape"]["type_ref"] = "local.Foreign"
    elif change == "root_kind":
        root["kind"] = "enum"
    elif change == "required_integer":
        root["fields"][0]["required"] = 1
    elif change == "has_default_integer":
        root["fields"][0]["has_default"] = 0
    else:
        body = json.loads(args["slice_bytes"])
        body["slice_digest"] = "sha256:" + "0" * 64
        args["slice_bytes"] = wire(body)
    if change != "slice_digest":
        args["bundle_bytes"] = wire(body)
    decoder = (
        codec.decode_schema_slice
        if change == "slice_digest"
        else codec.decode_schema_bundle
    )
    with pytest.raises((TypeError, ValueError)):
        decoder(
            args["slice_bytes"] if change == "slice_digest" else args["bundle_bytes"]
        )
    o = owner()
    with pytest.raises(ValueError):
        o.appoint(**args)
    o.close()


def test_valid_independently_restamped_slice_cannot_replace_derived_closure():
    args = appointment()
    _, other_slice = original_model(scalar=model.ScalarKind.BOOLEAN)
    altered = model.TypeSchemaSlice.create(
        codec.decode_schema_bundle(args["bundle_bytes"]), root_type_refs=("local.Root",)
    ).to_wire()
    altered["types"] = other_slice.to_wire()["types"]
    semantic = {k: v for k, v in altered.items() if k != "slice_digest"}
    altered["slice_digest"] = encoding.digest_payload(model.SLICE_CONTRACT, semantic)
    supplied = codec.decode_schema_slice(wire(altered))
    assert (
        supplied.bundle_digest
        == codec.decode_schema_bundle(args["bundle_bytes"]).schema_digest
    )
    o = owner()
    with pytest.raises(ValueError, match="model_slice_not_original_closure"):
        o.appoint(**dict(args, slice_bytes=wire(altered)))
    o.close()


@pytest.mark.parametrize(
    "unsupported", ("nullable", "optional", "constraints", "aliases")
)
def test_original_valid_wider_features_are_explicitly_unsupported(unsupported):
    bundle, _ = original_model()
    root = bundle.types[0]
    field = root.fields[0]
    kwargs = {
        "field_ref": field.field_ref,
        "name": field.name,
        "shape": field.shape,
        "required": True,
    }
    if unsupported == "nullable":
        kwargs["nullable"] = True
    elif unsupported == "optional":
        kwargs["required"] = False
    elif unsupported == "constraints":
        kwargs["constraints"] = encoding.FrozenJson.from_value({"min_length": 1})
    else:
        kwargs["aliases"] = ("old_identity",)
    new_root = model.TypeDefinition(
        root.type_ref,
        root.name,
        root.kind,
        fields=(model.FieldDefinition(**kwargs), root.fields[1]),
        identity=root.identity,
    )
    wider = model.TypeSchemaBundle.create(
        namespace=bundle.namespace,
        semantic_version=bundle.semantic_version,
        types=(new_root,),
    )
    assert validation.validate_schema_bundle(wider).is_valid
    sl = model.TypeSchemaSlice.create(wider, root_type_refs=("local.Root",))
    args = appointment()
    o = owner()
    with pytest.raises(ValueError, match="model_profile_unsupported"):
        o.appoint(
            **dict(
                args,
                bundle_bytes=codec.encode_schema_bundle(wider),
                slice_bytes=codec.encode_schema_slice(sl),
            )
        )
    o.close()


@pytest.mark.parametrize(
    "payload",
    (
        b"{} ",
        b'{"a":0,"a":0}',
        b'{"a":1,}',
        b"{}{}",
        b"\xff",
        b'{"a":01}',
        b'{"a":1.0}',
        b'{"a":NaN}',
    ),
)
def test_native_schema_grammar_refuses_noncanonical_or_invalid_bytes(payload):
    o = owner()
    with pytest.raises((TypeError, ValueError)):
        o.appoint(**dict(appointment(), bundle_bytes=payload))
    o.close()


def test_native_nominal_ports_do_not_read_foreign_owner_attributes():
    touched = []

    class Foreign:
        @property
        def verify(self):
            touched.append(True)
            raise AssertionError("foreign dispatch")

    with pytest.raises(ValueError):
        validate_local_model_owner(Foreign())
    with pytest.raises(ValueError):
        verify_local_model(Foreign(), object())
    assert touched == []


def test_original_issuance_and_terminal_release():
    o, other = owner(), owner()
    h = o.appoint(**appointment())
    with pytest.raises(ValueError):
        type(h)()
    with pytest.raises(ValueError):
        copy.copy(h)
    with pytest.raises(ValueError):
        verify_local_model(other, h)
    o.release(h)
    o.release(h)
    with pytest.raises(ValueError):
        verify_local_model(o, h)
    o.close()
    other.close()


def test_revision_retirement_clears_all_handles_without_restoration():
    o = owner()
    args = appointment()
    first, second = o.appoint(**args), o.appoint(**args)
    with pytest.raises(ValueError, match="model_revision_changed"):
        o.appoint(**dict(args, model_revision_ref="new:revision"))
    for h in (first, second):
        with pytest.raises(ValueError):
            verify_local_model(o, h)
        o.release(h)
    with pytest.raises(ValueError):
        o.appoint(**args)
    o.close()


def test_unissued_retirement_does_not_consume_capacity():
    o = owner()
    for i in range(70):
        with pytest.raises(ValueError, match="model_not_appointed"):
            o.retire_model(f"foreign:model:{i}")
    h = o.appoint(**appointment())
    assert verify_local_model(o, h).model_ref == "local:model"
    o.release(h)
    o.close()


def test_live_and_retired_original_model_identities_have_a_fixed_bound():
    o = owner()
    args = appointment()
    for i in range(64):
        name = f"local:model:{i}"
        h = o.appoint(**dict(args, model_ref=name))
        o.retire_model(name)
        o.release(h)
    with pytest.raises(ValueError, match="model_capacity_unavailable"):
        o.appoint(**dict(args, model_ref="local:model:65"))
    o.close()


def test_aggregate_retained_original_bytes_are_bounded_and_release_recovers_capacity():
    o = owner()
    args = appointment(topology=b"x" * 1048576)
    first = o.appoint(**dict(args, model_ref="local:large:1"))
    second = o.appoint(**dict(args, model_ref="local:large:2"))
    with pytest.raises(ValueError, match="model_retained_capacity_unavailable"):
        o.appoint(**dict(args, model_ref="local:large:3"))
    o.release(first)
    o.release(second)
    third = o.appoint(**dict(args, model_ref="local:large:3"))
    o.release(third)
    o.close()


def test_expiry_and_context_failure_are_terminal():
    o = owner()
    h = o.appoint(**dict(appointment(), lifetime_ms=1))
    time.sleep(0.01)
    with pytest.raises(ValueError):
        verify_local_model(o, h)
    o.release(h)
    h = o.appoint(**appointment())
    replies = []

    def run():
        try:
            verify_local_model(o, h)
        except ValueError as error:
            replies.append(str(error))

    t = threading.Thread(target=run)
    t.start()
    t.join()
    assert replies == ["model_owner_context_changed"]
    with pytest.raises(ValueError):
        verify_local_model(o, h)
    o.release(h)
    o.close()


def test_in_place_evidence_annotations_change_terminally_retires_original_owner():
    o = owner()
    h = o.appoint(**appointment())
    annotations = LocalReadModelEvidence.__annotations__
    original = annotations["owner_ref"]
    try:
        annotations["owner_ref"] = int
        with pytest.raises(ValueError, match="model_owner_changed"):
            verify_local_model(o, h)
    finally:
        annotations["owner_ref"] = original
    with pytest.raises(ValueError):
        verify_local_model(o, h)
    o.release(h)
    o.close()
