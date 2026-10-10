"""Existing portable package authority on Code bodies; bytes remain unchanged."""

from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractInvocation,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from .portable_semantic_package_authority import (
    CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_DIGEST,
    CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA,
    CodePortableSemanticPackageAuthority,
    code_portable_semantic_package_authority_body_ref,
)
from .runtime import SemanticBody

PACKAGE_AUTHORITY_BODY_REF = SemanticContractRef(
    CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_SCHEMA,
    "1",
    CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_DIGEST,
)
PACKAGE_AUTHORITY_BODY_CODEC_IMPLEMENTATION = SemanticImplementationCoordinate(
    "aware.code.package-authority-body-codec.v1",
    ContentDigest.of_bytes(
        canonical_json_bytes(
            {
                "revision": "unchanged-owner-body.v1",
                "codec": CODE_PORTABLE_SEMANTIC_PACKAGE_AUTHORITY_CODEC_DIGEST.to_wire(),
            }
        )
    ),
)


class PackageAuthorityBodyCodec:
    contract = PACKAGE_AUTHORITY_BODY_REF
    implementation = PACKAGE_AUTHORITY_BODY_CODEC_IMPLEMENTATION

    def encode(self, value: object) -> bytes:
        if type(value) is not CodePortableSemanticPackageAuthority:
            raise TypeError("exact Code portable package authority required")
        return value.canonical_bytes()

    def decode(self, canonical_body: bytes) -> object:
        return CodePortableSemanticPackageAuthority.from_canonical_bytes(canonical_body)

    def validate_invocation(
        self, value: object, invocation: SemanticContractInvocation
    ) -> None:
        if type(value) is not CodePortableSemanticPackageAuthority:
            raise TypeError("exact Code portable package authority required")
        value.__post_init__()
        if value.package_ref != invocation.target_package.package_ref:
            raise ContractViolation("package authority differs from invocation target")
        # Manifest raw SHA and kind mappings belong to the selected owner/host
        # contract, not this domain-independent transport codec.


def package_authority_body(value: CodePortableSemanticPackageAuthority) -> SemanticBody:
    wire = PackageAuthorityBodyCodec().encode(value)
    ref = code_portable_semantic_package_authority_body_ref(value)
    return SemanticBody(
        SemanticValueCoordinate(
            "package_authority",
            PACKAGE_AUTHORITY_BODY_REF,
            ref.ref,
            ref.sha256,
            ref.size_bytes,
        ),
        wire,
    )
