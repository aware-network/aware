from __future__ import annotations

import json

import pytest
from aware_meta_type_schema import (
    FieldDefinition,
    ScalarKind,
    TypeDefinition,
    TypeKind,
    TypeSchemaBundle,
    TypeSchemaSlice,
    ValueShape,
)
from aware_sdk_contract_runtime import (
    SdkContractDecodeError,
    SdkContractManifest,
    SdkMethodContract,
    SdkOperationContract,
    SdkTargetContract,
    decode_sdk_contract_manifest,
    encode_sdk_contract_manifest,
)


def _slice(type_ref: str) -> TypeSchemaSlice:
    name = type_ref.rsplit(".", 1)[-1]
    bundle = TypeSchemaBundle.create(
        namespace="proof",
        semantic_version="1",
        types=(
            TypeDefinition(
                type_ref,
                name,
                TypeKind.VALUE_OBJECT,
                fields=(
                    FieldDefinition(
                        f"{type_ref}.value",
                        "value",
                        ValueShape.scalar(ScalarKind.STRING),
                    ),
                ),
            ),
        ),
    )
    return TypeSchemaSlice.create(bundle, root_type_refs=(type_ref,))


def _manifest() -> SdkContractManifest:
    request = _slice("proof.Request")
    result = _slice("proof.Result")
    error = _slice("proof.Error")
    operation = SdkOperationContract(
        "proof_sdk.release_request",
        request.slice_digest,
        result.slice_digest,
        (error.slice_digest,),
        "development.release.request",
    )
    method = SdkMethodContract(
        "proof_sdk.release.request",
        operation.operation_ref,
        "create",
        "write",
        "service_state",
        "none",
        "request_response",
    )
    return SdkContractManifest.create(
        sdk_ref="proof_sdk",
        semantic_version="1",
        targets=(
            SdkTargetContract("python", "python", "proof_sdk"),
            SdkTargetContract("dart", "dart", "lib"),
        ),
        schema_slices=(request, result, error),
        operations=(operation,),
        methods=(method,),
    )


def test_manifest_round_trip_binds_python_and_dart_to_one_digest() -> None:
    manifest = _manifest()
    decoded = decode_sdk_contract_manifest(encode_sdk_contract_manifest(manifest))

    assert decoded == manifest
    assert tuple(value.language for value in decoded.targets) == ("dart", "python")
    assert decoded.operations[0].provider_operation_ref == "development.release.request"


def test_decoder_rejects_unknown_fields_and_digest_substitution() -> None:
    manifest = _manifest()
    wire = json.loads(encode_sdk_contract_manifest(manifest))
    wire["unexpected"] = True
    with pytest.raises(SdkContractDecodeError, match="unknown"):
        decode_sdk_contract_manifest(json.dumps(wire))

    wire.pop("unexpected")
    wire["manifest_digest"] = "sha256:" + "0" * 64
    with pytest.raises(SdkContractDecodeError, match="manifest_digest mismatch"):
        decode_sdk_contract_manifest(json.dumps(wire))
