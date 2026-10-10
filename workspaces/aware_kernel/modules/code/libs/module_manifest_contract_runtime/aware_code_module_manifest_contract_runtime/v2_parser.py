"""Version-2 extension validation over the single legacy module grammar."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import fields
from typing import Any, Never
from uuid import UUID

from .v2_models import (
    AwareModuleSpecV2,
    DeclarationTable,
    DeclarationTag,
    PackageDeclarationV2,
    PackageOccurrenceDeclaration,
)

MAX_BODY = 16_777_216
MAX_EXTENSION = 8_388_608
MAX_ITEMS = 16_384
OCCURRENCE_FIELDS = tuple(f.name for f in fields(PackageOccurrenceDeclaration))
ID = re.compile(r"^[a-z_][a-z0-9_]*$")
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
VERSION = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+_-]*$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
CONSTRAINT_KINDS = {
    "module_ref",
    "package_family",
    "package_kind",
    "package_ref",
    "semantic_provider_key",
    "semantic_root_ref",
}


def fail(message) -> Never:
    from .parser import AwareModuleTomlError

    raise AwareModuleTomlError(message)


def token(value, pattern=None):
    if type(value) is not str:
        fail("v2 token must be exact string")
    if (
        not 1 <= len(value.encode("utf-8")) <= 4096
        or unicodedata.normalize("NFC", value) != value
        or any(c.isspace() for c in value)
        or "\0" in value
    ):
        fail("v2 token is not canonical or exceeds bounds")
    if pattern is not None and not pattern.fullmatch(value):
        fail("v2 token syntax differs")
    return value


def table(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        fail("v2 table field set differs")
    return value


def rows(value):
    if type(value) is not list or len(value) > MAX_ITEMS:
        fail("v2 array type or bound differs")
    return value


def ordered(keys):
    if keys != sorted(set(keys)):
        fail("v2 collection must be sorted and unique")


def strings(value, nonempty=False):
    values = [token(v) for v in rows(value)]
    ordered([v.encode() for v in values])
    if nonempty and not values:
        fail("v2 collection must not be empty")


def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def freeze(value) -> Any:
    if type(value) is dict:
        return DeclarationTable(tuple((k, freeze(v)) for k, v in sorted(value.items())))
    if type(value) is list:
        return tuple(freeze(v) for v in value)
    return value


def thaw(value) -> Any:
    if type(value) is DeclarationTable:
        return {k: thaw(v) for k, v in value.entries}
    if type(value) is tuple:
        return [thaw(v) for v in value]
    return value


def tag(value, validate, absent=False):
    if type(value) is not dict:
        fail("v2 tag must be table")
    state = value.get("state")
    if type(state) is not str:
        fail("v2 tag state must be exact string")
    if state == "present":
        table(value, ("state", "value"))
        validate(value["value"])
        return DeclarationTag(state, freeze(value["value"]))
    table(value, ("state",))
    if state != "unavailable" and not (absent and state == "absent"):
        fail("v2 tag state is not permitted")
    return DeclarationTag(state)


def uuid(value):
    token(value)
    try:
        if str(UUID(value)) != value:
            fail("v2 UUID is not canonical")
    except ValueError:
        fail("v2 UUID syntax differs")


def address(value, registration=False):
    keys = (
        ("module_id", "package_id", "registration_key")
        if registration
        else ("module_id", "package_id")
    )
    table(value, keys)
    module = token(value["module_id"])
    if any(c in module for c in "/\\:") or module in (".", ".."):
        fail("v2 module address is not a membership token")
    token(value["package_id"], ID)
    if registration:
        token(value["registration_key"], ID)


def configuration(value):
    table(value, ("config_id", "config_key"))
    uuid(value["config_id"])
    token(value["config_key"])


def mappings(value, *, _version=2):
    keys = []
    for item in rows(value):
        table(item, ("dependency_kind", "dependency_ref", "targets", "constraints"))
        keys.append(
            (
                token(item["dependency_kind"]).encode(),
                token(item["dependency_ref"]).encode(),
            )
        )
        targets = rows(item["targets"])
        if not targets:
            fail("v2 dependency mapping requires targets")
        if _version == 3:
            from .v3_parser import parse_qualified_targets
            parse_qualified_targets(targets)
        else:
            for target in targets:
                address(target)
            ordered([(t["module_id"].encode(), t["package_id"].encode()) for t in targets])
        seen = set()
        for constraint in rows(item["constraints"]):
            table(constraint, ("constraint_kind", "constraint_value"))
            key = (
                token(constraint["constraint_kind"]),
                token(constraint["constraint_value"]),
            )
            if key[0] not in CONSTRAINT_KINDS or key in seen:
                fail("v2 constraint unsupported or duplicated")
            seen.add(key)
    ordered(keys)


def occurrence(value, *, _version=2):
    if type(_version) is not int or _version not in (2, 3):
        fail("unsupported occurrence grammar")
    if value is None:
        return PackageOccurrenceDeclaration(
            **{k: DeclarationTag("unavailable") for k in OCCURRENCE_FIELDS}
        )
    table(value, OCCURRENCE_FIELDS)
    def registration_address(v):
        if _version == 3:
            from .v3_parser import parse_qualified_address
            parse_qualified_address(v, registration=True)
        else:
            address(v, True)

    validators = {
        "registration": registration_address,
        "semantic_version": lambda v: token(v, VERSION),
        "semantic_package_name": lambda v: token(v, NAME),
        "code_package_name": lambda v: token(v, NAME),
        "source_code_package_id": uuid,
        "configuration": configuration,
        "namespace": token,
        "owned_roots": strings,
        "dependency_targets": lambda v: mappings(v, _version=_version),
    }
    result = PackageOccurrenceDeclaration(
        **{
            k: tag(value[k], check, k in ("source_code_package_id", "configuration"))
            for k, check in validators.items()
        }
    )
    if len(canonical(occurrence_wire(result))) > MAX_EXTENSION:
        fail("v2 occurrence exceeds bound")
    return result


def occurrence_wire(value):
    if type(value) is not PackageOccurrenceDeclaration:
        fail("exact v2 occurrence required")
    result = {}
    for name in OCCURRENCE_FIELDS:
        item = getattr(value, name)
        if type(item) is not DeclarationTag:
            fail("exact v2 tag required")
        if item.state != "present" and item.value is not None:
            fail("non-present tag cannot carry value")
        result[name] = {
            "state": item.state,
            **({"value": thaw(item.value)} if item.state == "present" else {}),
        }
    return result


def registrations(value, parent, kind, plugins):
    result = []
    for item in rows(value):
        table(
            item,
            (
                "key",
                "manifest_contract_kind",
                "manifest_filename",
                "semantic_package_family",
                "semantic_package_kind",
                "semantic_contract",
                "supported_languages",
                "code_package_surface",
                "profiles",
            )
            + (
                ("declared_package_kinds",)
                if type(item) is dict and "declared_package_kinds" in item
                else ()
            ),
        )
        if "declared_package_kinds" in item:
            strings(item["declared_package_kinds"], True)
        token(item["key"], ID)
        for key in (
            "manifest_contract_kind",
            "manifest_filename",
            "semantic_package_family",
            "semantic_package_kind",
        ):
            token(item[key])
        filename = item["manifest_filename"]
        if (
            filename in (".", "..")
            or any(c in filename for c in "/\\")
            or len(filename.encode()) > 255
        ):
            fail("v2 manifest filename must be canonical basename")
        contract = table(
            item["semantic_contract"], ("role", "name", "provider_key", "coordinate")
        )
        for v in contract.values():
            token(v)
        if (
            parent is None
            or kind != "code"
            or parent.contract != "aware.semantic_provider"
            or item["manifest_contract_kind"] not in parent.owns_manifest_kinds
            or contract["provider_key"] != parent.provider_key
        ):
            fail("v2 registration differs from parent provider")
        matches = [
            p
            for p in plugins
            if p.kind == "code.module_plugin" and p.provider_key == parent.provider_key
        ]
        if len(matches) != 1:
            fail("v2 registration requires unique plugin")
        strings(item["supported_languages"], True)
        tag(item["code_package_surface"], token, True)
        profiles = rows(item["profiles"])
        if [p.get("stage") for p in profiles if type(p) is dict] != [
            "authority_derivation",
            "source_planning",
        ] or len(profiles) != 2:
            fail("v2 profiles require exact ordered stages")
        for profile in profiles:
            table(
                profile, ("stage", "profile_ref", "profile_version", "profile_digest")
            )
            token(profile["profile_ref"])
            token(profile["profile_version"])
            token(profile["profile_digest"], DIGEST)
        result.append(freeze(item))
    ordered([thaw(item)["key"].encode() for item in result])
    if len(canonical(value)) > MAX_EXTENSION:
        fail("v2 registrations exceed bound")
    return tuple(result)


def parse_v2_table(raw) -> AwareModuleSpecV2:
    value = _parse_version_table(raw, version=2)
    if not isinstance(value, AwareModuleSpecV2):
        fail("exact version-2 module result required")
    return value


def _parse_version_table(raw, *, version):
    from .parser import _parse_module_table
    from .v3_models import AwareModuleSpecV3

    if type(version) is not int or version not in (2, 3):
        fail("unsupported module extension version")
    if type(raw.get("aware")) is not int or raw["aware"] != version:
        fail(f"v{version} aware must be exact integer {version}")
    legacy = dict(raw)
    legacy["aware"] = 1
    packages = raw.get("packages")
    if type(packages) is not list:
        fail("v2 packages must be array")
    stripped = []
    extensions = []
    for package in packages:
        if type(package) is not dict:
            fail("v2 package must be table")
        copy = dict(package)
        extension = copy.pop("semantic_admission", None)
        registration = []
        if "semantic_contract" in copy:
            if type(copy["semantic_contract"]) is not dict:
                fail("semantic_contract must be table")
            parent = dict(copy["semantic_contract"])
            registration = parent.pop("registrations", [])
            copy["semantic_contract"] = parent
        stripped.append(copy)
        extensions.append((extension, registration, "semantic_admission" in package))
    legacy["packages"] = stripped
    base = _parse_module_table(legacy)
    declarations = tuple(
        PackageDeclarationV2(
            package.id,
            registrations(reg, package.semantic_contract, package.kind, base.plugins),
            occurrence(ext, _version=version),
            declared,
        )
        for package, (ext, reg, declared) in zip(base.packages, extensions, strict=True)
    )
    values: dict[str, Any] = {f.name: getattr(base, f.name) for f in fields(base)}
    values["aware"] = version
    model = AwareModuleSpecV2 if version == 2 else AwareModuleSpecV3
    return model(**values, package_declarations=declarations)
