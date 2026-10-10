"""Portable candidate boundaries do not issue observation authority."""

import json

import pytest
from aware_code_semantic_contract_runtime import (
    CodeSemanticCandidate as Candidate,
)
from aware_code_semantic_contract_runtime import (
    CodeSemanticCandidateListing as Listing,
)
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    SemanticCandidateListingCodec,
    semantic_candidate_listing_body,
)
from aware_code_semantic_contract_runtime import (
    decode_semantic_candidate_listing as decode,
)
from aware_code_semantic_contract_runtime import (
    encode_semantic_candidate_listing as encode,
)

D = ContentDigest.of_bytes(b"earlier observation closure")


def test_roundtrip_body_and_portable_empty():
    for rows in (
        (),
        (Candidate("aware.environment.toml", D), Candidate("notes.txt", D)),
    ):
        value = Listing(D, rows)
        assert decode(encode(value)) == value
        body = semantic_candidate_listing_body(value)
        assert body.canonical_body == encode(value)
        assert SemanticCandidateListingCodec().decode(body.canonical_body) == value
    assert set(json.loads(encode(Listing(D, ())))) == {
        "contract",
        "source_identity_digest",
        "candidates",
    }


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/x",
        "x/",
        "x//y",
        ".",
        "..",
        "x/../y",
        "x/./y",
        "x/ /y",
        "x\\y",
        "x\0y",
        "e\u0301",
        "\ud800",
        "x" * 256,
        "/".join(["x"] * 129),
    ],
)
def test_reject_noncanonical_paths(path):
    with pytest.raises(ContractViolation):
        Candidate(path, D)


def test_path_byte_limits_and_nfc():
    Candidate("é" * 127, D)
    with pytest.raises(ContractViolation):
        Candidate("é" * 128, D)
    Candidate("/".join(["x" * 255] * 15 + ["x" * 254]) + "/x", D)
    with pytest.raises(ContractViolation):
        Candidate("/".join(["x" * 255] * 16) + "/x", D)


def test_order_duplicates_and_exact_types():
    for rows in (
        (Candidate("b", D), Candidate("a", D)),
        (Candidate("a", D), Candidate("a", D)),
    ):
        with pytest.raises(ContractViolation):
            Listing(D, rows)
    with pytest.raises(ContractViolation):
        Listing(D, [])
    with pytest.raises(ContractViolation):
        Candidate("a", D.value)
    with pytest.raises(ContractViolation):
        Listing(D.value, ())


def test_count_bound():
    rows = tuple(Candidate(f"{n:05}", D) for n in range(16_384))
    assert len(Listing(D, rows).candidates) == 16_384
    with pytest.raises(ContractViolation):
        Listing(D, rows + (Candidate("99999", D),))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda b: b + b"\n",
        lambda b: b"\xef\xbb\xbf" + b,
        lambda b: b.replace(b'"candidates":', b'"candidates":[],"candidates":'),
        lambda b: b.replace(b"{", b'{"root":"/tmp",', 1),
        lambda b: b.replace(b'"candidates":[]', b'"candidates":null'),
        lambda b: b.replace(
            b'"candidates":[]',
            b'"candidates":[{"relative_path":"a","content_digest":"bad"}]',
        ),
    ],
)
def test_wire_rejection(mutation):
    with pytest.raises((ContractViolation, TypeError)):
        decode(mutation(encode(Listing(D, ()))))


def test_total_body_bound_constructor_and_decoder():
    prefix = "/".join(["x" * 255] * 4)
    rows = tuple(Candidate(f"{n:05}/{prefix}", D) for n in range(8000))
    with pytest.raises(ContractViolation):
        Listing(D, rows)
    with pytest.raises(ContractViolation):
        decode(b" " * 8_388_609)
