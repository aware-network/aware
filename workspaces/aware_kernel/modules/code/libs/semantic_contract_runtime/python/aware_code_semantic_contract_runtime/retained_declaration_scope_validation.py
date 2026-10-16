"""Original V3 value integrity, not source, membership or lifetime authority.

A private owner may retain this complete coordinate after portable validation.
Detached values still require the ordinary V3 codec. No cache, addresses, weak
aliases or Workspace semantics enter this interface.
"""

from __future__ import annotations

import json
from types import MemberDescriptorType
from typing import NamedTuple

from .contracts import ContentDigest, ContractViolation, canonical_json_bytes
from .dependency_scope_closure import (
    MAX_CANONICAL_BYTES,
    MAX_PATHS,
    DependencyScopeDeclaration,
    DependencyScopeEdge,
    DependencyScopeRestriction,
)
from .dependency_scope_closure_v2 import DependencyScopeProfileAssociation
from .retained_declaration_scope import (
    DECLARATION_SCOPE_CONTRACT,
    DEPENDENCY_CLOSURE_CONTRACT_V3,
    CodeRetainedDeclarationPackage,
    CodeRetainedDeclarationScopeEntry,
    CodeRetainedDeclarationScopeProjection,
    CodeRetainedDependencyScopeClosureV3,
    CodeRetainedLocalProfilePublication,
)
from .retained_declaration_scope_codec import decode_retained_declaration_scope
from .retained_scope_interfaces import CodeRetainedScopeBody, CodeRetainedScopeModule


class _FieldRecord(NamedTuple):
    kind: type
    original: object
    fields: tuple[tuple[str, MemberDescriptorType, object], ...]


class RetainedDeclarationScopeCoordinate(NamedTuple):
    """Strong immutable field custody only; possession grants no authority."""

    original: CodeRetainedDependencyScopeClosureV3
    digest: str
    records: tuple[_FieldRecord, ...]


def _entrances():
    # Closed schema, captured original slot descriptors. No dataclass reflection
    # or nominal lookup on a foreign class/metaclass is performed at runtime.
    schema = tuple(
        (kind, tuple((name, vars(kind)[name]) for name in names))
        for kind, names in (
            (ContentDigest, ("value",)),
            (CodeRetainedScopeBody, ("relative_path", "body_ref", "content_digest", "body")),
            (CodeRetainedScopeModule, ("module_id", "manifest")),
            (CodeRetainedDeclarationPackage, ("module_id", "package_id", "package_kind", "module_manifest_path", "package_root", "manifest_relative_path", "manifest")),
            (CodeRetainedDeclarationScopeProjection, ("repository_binding_ref", "observation_digest", "workspace_manifest", "modules", "packages")),
            (CodeRetainedDeclarationScopeEntry, ("scope_key", "workspace_handle", "projection")),
            (CodeRetainedLocalProfilePublication, ("owning_scope_key", "profile_key", "manifest")),
            (CodeRetainedDependencyScopeClosureV3, ("consumer_scope_key", "repository_binding_ref", "repository_manifest", "scopes", "edges", "local_profiles", "profile_associations")),
            (DependencyScopeDeclaration, ("manifest_relative_path", "manifest_content_digest", "dependency_index", "profile_package_index")),
            (DependencyScopeRestriction, ("state", "value")),
            (DependencyScopeEdge, ("declaring_scope_key", "target_scope_key", "declaration", "dependency_id", "dependency_kind", "dependency_source", "channel", "revision", "profile_package_ref", "profile_key", "semantic_contract_provider_keys")),
            (DependencyScopeProfileAssociation, ("declaring_scope_key", "declaration", "target_scope_key", "manifest")),
        )
    )
    coordinate_type, record_type = RetainedDeclarationScopeCoordinate, _FieldRecord
    root_type, digest_type = CodeRetainedDependencyScopeClosureV3, ContentDigest
    body_type, restriction_type = CodeRetainedScopeBody, DependencyScopeRestriction
    projection_type = CodeRetainedDeclarationScopeProjection
    encode, decode = canonical_json_bytes, decode_retained_declaration_scope
    fail = ContractViolation

    def compare(coordinate, value):
        if (type(coordinate) is not coordinate_type or type(value) is not root_type
            or value is not tuple.__getitem__(coordinate, 0)):
            raise fail("original declaration coordinate required")
        for record in tuple.__getitem__(coordinate, 2):
            kind = tuple.__getitem__(record, 0)
            original = tuple.__getitem__(record, 1)
            fields = tuple.__getitem__(record, 2)
            if type(original) is not kind:
                raise fail("original declaration class changed")
            # Read the original slots directly only after descriptor identity.
            namespace = type.__getattribute__(kind, "__dict__")
            for name, slot, member in fields:
                if namespace.get(name) is not slot:
                    raise fail("original declaration slot changed")
                if slot.__get__(original, kind) is not member:
                    raise fail("original declaration field changed")

    def compare_detached(coordinate, value):
        if type(coordinate) is not coordinate_type or type(value) is not root_type:
            raise fail("exact declaration coordinate and value required")
        # Temporary traversal index only. Every original is strongly retained;
        # no numeric addresses or detached aliases enter the coordinate.
        index = {
            id(tuple.__getitem__(record, 1)): record
            for record in tuple.__getitem__(coordinate, 2)
        }

        def check(expected, actual):
            record = index.get(id(expected))
            if record is not None:
                kind = tuple.__getitem__(record, 0)
                if type(actual) is not kind:
                    raise fail("detached declaration class changed")
                namespace = type.__getattribute__(kind, "__dict__")
                for name, slot, member in tuple.__getitem__(record, 2):
                    if namespace.get(name) is not slot:
                        raise fail("original declaration slot changed")
                    check(member, slot.__get__(actual, kind))
            elif type(expected) is tuple:
                if type(actual) is not tuple or len(actual) != len(expected):
                    raise fail("detached declaration tuple changed")
                for left, right in zip(expected, actual, strict=True):
                    check(left, right)
            elif (type(actual) is not type(expected)
                  or not (type(expected) is str or type(expected) is int
                          or type(expected) is bytes or expected is None)
                  or actual != expected):
                raise fail("detached declaration field changed")

        check(tuple.__getitem__(coordinate, 0), value)

    def capture(value):
        if type(value) is not root_type:
            raise fail("exact declaration closure required")
        records = []
        seen = {}  # Temporary traversal only; coordinates retain no addresses.

        def visit(item):
            kind = type(item)
            if kind is str or kind is int or kind is bytes or kind is type(None):
                return
            if kind is tuple:
                for member in item:
                    visit(member)
                return
            fields = next((slots for expected, slots in schema if kind is expected), None)
            if fields is None:
                raise fail("foreign declaration field")
            if id(item) in seen:
                return
            seen[id(item)] = item
            if len(records) >= MAX_PATHS * 16:
                raise fail("declaration coordinate bound")
            namespace = type.__getattribute__(kind, "__dict__")
            values = []
            for name, slot in fields:
                if type(slot) is not MemberDescriptorType or namespace.get(name) is not slot:
                    raise fail("original declaration slot changed")
                values.append((name, slot, slot.__get__(item, kind)))
            record = tuple.__new__(record_type, (kind, item, tuple(values)))
            records.append(record)
            for _, _, member in record.fields:
                visit(member)

        visit(value)
        index = {id(record.original): record for record in records}

        def wire(item):
            kind = type(item)
            if kind is str or kind is int or kind is type(None):
                return item
            if kind is tuple:
                return [wire(member) for member in item]
            record = index[id(item)]
            fields = {name: member for name, _, member in record.fields}
            if record.kind is digest_type:
                return fields["value"]
            if record.kind is body_type:
                raw = fields.pop("body")
                return {**{name: wire(member) for name, member in fields.items()},
                        "size_bytes": len(raw), "body_hex": raw.hex()}
            if record.kind is restriction_type and fields["state"] != "present":
                fields.pop("value")
            result = {name: wire(member) for name, member in fields.items()}
            if record.kind is root_type:
                result["contract"] = DEPENDENCY_CLOSURE_CONTRACT_V3
            elif record.kind is projection_type:
                result["contract"] = DECLARATION_SCOPE_CONTRACT
            return result

        # Build only from captured immutable fields, never live DTO methods.
        payload = encode(wire(value))
        if len(payload) > MAX_CANONICAL_BYTES:
            raise fail("declaration coordinate canonical bound")
        digest = digest_type.of_bytes(payload).value
        detached = json.loads(payload)
        detached["closure_digest"] = digest
        # Complete original codec laws apply once to independently detached
        # bytes. This call grants no owner/source admission.
        decode(encode(detached))
        coordinate = tuple.__new__(coordinate_type, (value, digest, tuple(records)))
        compare(coordinate, value)
        return coordinate

    return capture, compare, compare_detached


(capture_retained_declaration_scope,
 validate_retained_declaration_scope_coordinate,
 validate_detached_declaration_scope_coordinate) = _entrances()
