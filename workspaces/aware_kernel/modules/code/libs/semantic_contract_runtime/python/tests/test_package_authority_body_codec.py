"""Thin generic adapter preserves existing Code bytes across semantic owners."""

import pytest
from aware_code_semantic_contract_runtime import (
    CodePortableSemanticPackage,
    ContentDigest,
)
from aware_code_semantic_contract_runtime.package_authority_body_codec import (
    PackageAuthorityBodyCodec,
    package_authority_body,
)
from test_portable_semantic_package_authority import _authority


@pytest.mark.parametrize("kind", ["ontology", "experience_package"])
def test_existing_codec_bytes_and_domain_separated_digests(kind):
    authority = _authority(
        semantic_package=CodePortableSemanticPackage("neutral", kind, "meta-ontology")
    )
    codec = PackageAuthorityBodyCodec()
    body = package_authority_body(authority)
    assert body.canonical_body == authority.canonical_bytes()
    decoded = codec.decode(body.canonical_body)
    assert codec.encode(decoded) == body.canonical_body
    assert body.coordinate.digest == ContentDigest.of_bytes(body.canonical_body)
    assert body.coordinate.digest != authority.authority_digest
    assert body.coordinate.role == "package_authority"


def test_strict_owner_rejection_is_preserved():
    codec = PackageAuthorityBodyCodec()
    with pytest.raises(TypeError):
        codec.encode({})
    with pytest.raises(ValueError):
        codec.decode(_authority().canonical_bytes() + b"\n")
