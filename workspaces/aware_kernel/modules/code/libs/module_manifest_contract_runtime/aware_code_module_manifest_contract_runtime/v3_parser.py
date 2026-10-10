"""Qualified v3 addresses and full module parsing through the shared grammar."""

import re

from .v2_parser import address, fail, rows, table
from .v3_models import AwareModuleSpecV3, QualifiedModuleAddress

_HANDLE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,127}", flags=re.ASCII)


def parse_qualified_address(value, *, registration=False) -> QualifiedModuleAddress:
    if type(registration) is not bool:
        fail("exact registration mode required")
    keys = ("scope", "module_id", "package_id")
    if registration:
        keys += ("registration_key",)
    table(value, keys)
    scope = value["scope"]
    if type(scope) is not dict or type(scope.get("kind")) is not str:
        fail("exact tagged qualified scope required")
    kind = scope["kind"]
    handle = None
    if kind == "local":
        table(scope, ("kind",))
    elif kind == "dependency":
        table(scope, ("kind", "workspace_handle"))
        handle = scope["workspace_handle"]
        if type(handle) is not str or _HANDLE.fullmatch(handle) is None:
            fail("canonical qualified Workspace handle required")
    else:
        fail("unknown qualified scope kind")
    # Reuse exact existing local identifier rules, without changing v2 addresses.
    address({k: v for k, v in value.items() if k != "scope"}, registration)
    return QualifiedModuleAddress(
        kind, handle, value["module_id"], value["package_id"],
        value.get("registration_key"),
    )


def qualified_address_wire(value: QualifiedModuleAddress, *, registration=False):
    if type(value) is not QualifiedModuleAddress:
        fail("exact qualified address required")
    scope = {"kind": value.scope_kind}
    if value.scope_kind == "dependency":
        if type(value.workspace_handle) is not str:
            fail("dependency address requires exact handle")
        scope["workspace_handle"] = value.workspace_handle
    elif value.workspace_handle is not None:
        fail("local address cannot retain dependency handle")
    result = {"scope": scope, "module_id": value.module_id, "package_id": value.package_id}
    if registration:
        result["registration_key"] = value.registration_key
    elif value.registration_key is not None:
        fail("target address cannot retain registration key")
    if parse_qualified_address(result, registration=registration) != value:
        fail("qualified address meaning differs")
    return result


def parse_qualified_targets(value) -> tuple[QualifiedModuleAddress, ...]:
    values = rows(value)
    if not values:
        fail("qualified dependency mapping requires targets")
    targets = tuple(parse_qualified_address(v) for v in values)
    keys = [t.ordering_key for t in targets]
    if keys != sorted(set(keys)):
        fail("qualified targets must be unique and scope ordered")
    return targets


def parse_v3_table(raw) -> AwareModuleSpecV3:
    from .v2_parser import _parse_version_table
    value = _parse_version_table(raw, version=3)
    if not isinstance(value, AwareModuleSpecV3):
        fail("exact version-3 module result required")
    return value
