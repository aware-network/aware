"""Canonical v2 full-meaning codec, isolated from the v1 wire contract."""

import json
from dataclasses import fields
from typing import Any, cast

from .codec import ModuleManifestMeaningError, _convert, _pairs
from .models import AwareModuleSpec
from .v2_models import AwareModuleSpecV2, PackageDeclarationV2
from .v2_parser import (
    MAX_BODY,
    canonical,
    occurrence,
    occurrence_wire,
    registrations,
    table,
    thaw,
)

CONTRACT_V2 = "aware.code.module-manifest-meaning.v2"


def encode_module_manifest_meaning_v2(value: AwareModuleSpecV2) -> bytes:
    return _encode_version(value, version=2)


def _model(version):
    from .v3_models import AwareModuleSpecV3
    if type(version) is not int or version not in (2, 3):
        raise ModuleManifestMeaningError("unsupported module meaning version")
    return AwareModuleSpecV2 if version == 2 else AwareModuleSpecV3


def _encode_version(value, *, version) -> bytes:
    model = _model(version)
    if (
        type(value) is not model
        or type(value.aware) is not int
        or value.aware != version
    ):
        raise ModuleManifestMeaningError("exact version-2 module meaning required")
    base = AwareModuleSpec(
        **{f.name: getattr(value, f.name) for f in fields(AwareModuleSpec)}
    )
    meaning = cast(dict[str, Any], _convert(base, AwareModuleSpec, decode=False))
    if type(value.package_declarations) is not tuple or len(
        value.package_declarations
    ) != len(value.packages):
        raise ModuleManifestMeaningError("v2 package declarations differ")
    extension = []
    for package, declaration in zip(
        value.packages, value.package_declarations, strict=True
    ):
        if (
            type(declaration) is not PackageDeclarationV2
            or declaration.package_id != package.id
            or type(declaration.registrations) is not tuple
        ):
            raise ModuleManifestMeaningError("v2 declaration package differs")
        if type(declaration.occurrence_declared) is not bool:
            raise ModuleManifestMeaningError("v2 occurrence presence must be boolean")
        if not declaration.occurrence_declared and declaration.occurrence != occurrence(
            None, _version=version
        ):
            raise ModuleManifestMeaningError(
                "omitted v2 occurrence must be unavailable"
            )
        reg_wire = [thaw(v) for v in declaration.registrations]
        reg = registrations(
            reg_wire, package.semantic_contract, package.kind, value.plugins
        )
        occ_wire = occurrence_wire(declaration.occurrence)
        occ = occurrence(occ_wire, _version=version)
        if reg != declaration.registrations or occ != declaration.occurrence:
            raise ModuleManifestMeaningError("v2 declaration model is not canonical")
        extension.append(
            {
                "package_id": package.id,
                "registrations": reg_wire,
                "occurrence": occ_wire,
                "occurrence_declared": declaration.occurrence_declared,
            }
        )
    meaning["package_declarations"] = extension
    body = canonical({"contract": f"aware.code.module-manifest-meaning.v{version}", "meaning": meaning})
    if len(body) > MAX_BODY:
        raise ModuleManifestMeaningError("v2 meaning exceeds bound")
    return body


def decode_module_manifest_meaning_v2(body: bytes) -> AwareModuleSpecV2:
    return cast(AwareModuleSpecV2, _decode_version(body, version=2))


def _decode_version(body: bytes, *, version):
    model = _model(version)
    if type(body) is not bytes or len(body) > MAX_BODY:
        raise ModuleManifestMeaningError("v2 meaning byte type or bound differs")
    try:
        raw = json.loads(body.decode("utf-8"), object_pairs_hook=_pairs)
        table(raw, ("contract", "meaning"))
        if raw["contract"] != f"aware.code.module-manifest-meaning.v{version}":
            raise ModuleManifestMeaningError("v2 contract differs")
        meaning = table(
            raw["meaning"],
            tuple(f.name for f in fields(AwareModuleSpec)) + ("package_declarations",),
        )
        if type(meaning["aware"]) is not int or meaning["aware"] != version:
            raise ModuleManifestMeaningError("v2 meaning version differs")
        base_wire = {k: v for k, v in meaning.items() if k != "package_declarations"}
        base = cast(AwareModuleSpec, _convert(base_wire, AwareModuleSpec, decode=True))
        declarations = meaning["package_declarations"]
        if type(declarations) is not list or len(declarations) != len(base.packages):
            raise ModuleManifestMeaningError("v2 declaration count differs")
        parsed = []
        for package, declaration in zip(base.packages, declarations, strict=True):
            table(
                declaration,
                ("package_id", "registrations", "occurrence", "occurrence_declared"),
            )
            if declaration["package_id"] != package.id:
                raise ModuleManifestMeaningError("v2 package order differs")
            parsed.append(
                PackageDeclarationV2(
                    package.id,
                    registrations(
                        declaration["registrations"],
                        package.semantic_contract,
                        package.kind,
                        base.plugins,
                    ),
                    occurrence(declaration["occurrence"], _version=version),
                    declaration["occurrence_declared"],
                )
            )
        value = model(
            **{f.name: getattr(base, f.name) for f in fields(AwareModuleSpec)},
            package_declarations=tuple(parsed),
        )
        if _encode_version(value, version=version) != body:
            raise ModuleManifestMeaningError("noncanonical v2 meaning")
        return value
    except (ValueError, TypeError, UnicodeError, RecursionError, KeyError) as exc:
        raise ModuleManifestMeaningError(str(exc)) from exc
