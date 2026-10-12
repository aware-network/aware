"""Portable SDK manifest meaning; parsing consumes bytes, not source authority."""

from .codec import (
    SdkManifestMeaningCodecError,
    decode_sdk_manifest_meaning,
    encode_sdk_manifest_meaning,
)
from .model import (
    AwareSdkCompilationMode,
    AwareSdkDependencyKind,
    AwareSdkTomlBuildSpec,
    AwareSdkTomlDartProductTargetSpec,
    AwareSdkTomlDartTargetSpec,
    AwareSdkTomlDependencySpec,
    AwareSdkTomlGenerationProfileSpec,
    AwareSdkTomlObjectConfigGraphPackageSpec,
    AwareSdkTomlPackageSpec,
    AwareSdkTomlPythonProductTargetSpec,
    AwareSdkTomlPythonTargetSpec,
    AwareSdkTomlSpec,
    AwareSdkTomlTargetsSpec,
)
from .parser import (
    AwareSdkTomlError,
    load_aware_sdk_toml_spec_from_text,
    parse_sdk_manifest_bytes,
)

__all__ = [
    "AwareSdkCompilationMode",
    "AwareSdkDependencyKind",
    "AwareSdkTomlBuildSpec",
    "AwareSdkTomlDartProductTargetSpec",
    "AwareSdkTomlDartTargetSpec",
    "AwareSdkTomlDependencySpec",
    "AwareSdkTomlGenerationProfileSpec",
    "AwareSdkTomlError",
    "AwareSdkTomlObjectConfigGraphPackageSpec",
    "AwareSdkTomlPackageSpec",
    "AwareSdkTomlPythonProductTargetSpec",
    "AwareSdkTomlPythonTargetSpec",
    "AwareSdkTomlSpec",
    "AwareSdkTomlTargetsSpec",
    "SdkManifestMeaningCodecError",
    "decode_sdk_manifest_meaning",
    "encode_sdk_manifest_meaning",
    "load_aware_sdk_toml_spec_from_text",
    "parse_sdk_manifest_bytes",
]
