from __future__ import annotations

import json
from typing import Any, cast

import pytest

from aware_specification_fs_source_contract import (
    MAX_ENCODED_CLOSURE_BYTES,
    SpecificationFsContractError,
    SpecificationFsParserProfileCoordinate,
    SpecificationFsSourceClosure,
    SpecificationFsSourceMember,
    SpecificationFsSourceRole,
    decode_specification_fs_source_closure,
    encode_specification_fs_source_closure,
)
from aware_specification_fs_source_contract import codec as codec_module
from aware_specification_fs_source_contract.codec import _validate_encoded_closure_size


def value() -> SpecificationFsSourceClosure:
    return SpecificationFsSourceClosure(
        "specs/example",
        SpecificationFsParserProfileCoordinate(
            "aware.specification.fs-parser", "sha256:" + "1" * 64
        ),
        (
            SpecificationFsSourceMember(
                "aware.spec.toml", SpecificationFsSourceRole.MANIFEST, "aware = 1\n"
            ),
        ),
    )


def test_codec_round_trip_and_size_boundary() -> None:
    original = value()
    body = encode_specification_fs_source_closure(original)
    assert decode_specification_fs_source_closure(body) == original
    _validate_encoded_closure_size(MAX_ENCODED_CLOSURE_BYTES)
    with pytest.raises(SpecificationFsContractError):
        _validate_encoded_closure_size(MAX_ENCODED_CLOSURE_BYTES + 1)


def test_public_decoder_checks_size_before_utf8_and_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def utf8(body: bytes) -> str:
        calls.append("utf8")
        return body.decode()

    def json_decode(_: str) -> object:
        calls.append("json")
        return {}

    monkeypatch.setattr(codec_module, "_decode_utf8", utf8)
    monkeypatch.setattr(codec_module, "_decode_json", json_decode)
    monkeypatch.setattr(
        codec_module,
        "_encoded_closure_size",
        lambda _: MAX_ENCODED_CLOSURE_BYTES,
    )
    with pytest.raises(SpecificationFsContractError):
        decode_specification_fs_source_closure(b"{}")
    assert calls == ["utf8", "json"]

    calls.clear()
    monkeypatch.setattr(
        codec_module,
        "_encoded_closure_size",
        lambda _: MAX_ENCODED_CLOSURE_BYTES + 1,
    )
    with pytest.raises(SpecificationFsContractError):
        decode_specification_fs_source_closure(b"{}")
    assert calls == []


def test_ascii_escape_amplification_round_trip() -> None:
    escaped = SpecificationFsSourceClosure(
        "specs/example",
        value().profile,
        (
            SpecificationFsSourceMember(
                "aware.spec.toml", SpecificationFsSourceRole.MANIFEST, "é\n"
            ),
        ),
    )
    body = encode_specification_fs_source_closure(escaped)
    assert b"\\u00e9" in body
    assert decode_specification_fs_source_closure(body) == escaped


def mutate(path: tuple[str | int, ...], replacement: object) -> bytes:
    root = cast(
        dict[str, Any],
        json.loads(encode_specification_fs_source_closure(value())),
    )
    target: Any = root
    for part in path[:-1]:
        target = target[part]  # type: ignore[index]
    target[path[-1]] = replacement  # type: ignore[index]
    return json.dumps(
        root, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode()


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("closure_digest",), "sha256:" + "9" * 64),
        (("member_set_digest",), "sha256:" + "9" * 64),
        (("manifest_member_digest",), "sha256:" + "9" * 64),
        (("total_size_bytes",), True),
        (("members", 0, "size_bytes"), False),
        (("members", 0, "body_digest"), "sha256:" + "9" * 64),
        (("members", 0, "member_digest"), "sha256:" + "9" * 64),
        (("profile", "profile_coordinate_digest"), "sha256:" + "9" * 64),
    ],
)
def test_substitution_rejects(path: tuple[str | int, ...], replacement: object) -> None:
    with pytest.raises(SpecificationFsContractError):
        decode_specification_fs_source_closure(mutate(path, replacement))


@pytest.mark.parametrize(
    "codepoint", ["\u000b", "\u000c", "\u0085", "\u2028", "\u2029"]
)
@pytest.mark.parametrize("template", ["{}a\n", "a{}b\n", "a{}\n", "a{}"])
def test_decoded_alternative_line_breaks_reject(codepoint: str, template: str) -> None:
    poisoned = mutate(("members", 0, "canonical_body"), template.format(codepoint))
    with pytest.raises(SpecificationFsContractError):
        decode_specification_fs_source_closure(poisoned)


@pytest.mark.parametrize("codepoint", ["\u0085", "\u2028", "\u2029"])
def test_raw_utf8_alternative_line_breaks_reject(codepoint: str) -> None:
    root = cast(
        dict[str, object],
        json.loads(encode_specification_fs_source_closure(value())),
    )
    members = cast(list[dict[str, object]], root["members"])
    members[0]["canonical_body"] = f"a{codepoint}b\n"
    raw_utf8 = json.dumps(
        root, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    assert codepoint.encode("utf-8") in raw_utf8
    with pytest.raises(SpecificationFsContractError):
        decode_specification_fs_source_closure(raw_utf8)


@pytest.mark.parametrize("body", [b"{} ", b'{"x":NaN}', b'{"x":1,"x":2}', b"\xff"])
def test_invalid_json_rejects(body: bytes) -> None:
    with pytest.raises(SpecificationFsContractError):
        decode_specification_fs_source_closure(body)


def test_unknown_missing_and_noncanonical_reject() -> None:
    encoded = encode_specification_fs_source_closure(value())
    root = json.loads(encoded)
    root["unknown"] = 1
    unknown = json.dumps(
        root, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode()
    with pytest.raises(SpecificationFsContractError):
        decode_specification_fs_source_closure(unknown)
    root.pop("unknown")
    root.pop("closure_digest")
    missing = json.dumps(
        root, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode()
    with pytest.raises(SpecificationFsContractError):
        decode_specification_fs_source_closure(missing)
    with pytest.raises(SpecificationFsContractError):
        decode_specification_fs_source_closure(encoded.replace(b'":', b'": '))
