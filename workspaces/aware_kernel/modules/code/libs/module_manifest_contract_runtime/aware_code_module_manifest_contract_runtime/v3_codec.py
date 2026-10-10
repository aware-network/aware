"""Distinct canonical v3 meaning using the shared complete module codec."""

from typing import cast

from .v2_codec import _decode_version, _encode_version
from .v3_models import AwareModuleSpecV3

CONTRACT_V3 = "aware.code.module-manifest-meaning.v3"


def encode_module_manifest_meaning_v3(value: AwareModuleSpecV3) -> bytes:
    return _encode_version(value, version=3)


def decode_module_manifest_meaning_v3(body: bytes) -> AwareModuleSpecV3:
    return cast(AwareModuleSpecV3, _decode_version(body, version=3))
