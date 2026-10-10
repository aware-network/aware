"""Strict portable codecs for the declaration-only closure and selected source.

Decoding reconstructs values only. It cannot authenticate Workspace handles,
complete enumeration, a selected source, or an execution lifetime.
"""

from __future__ import annotations

import json
from dataclasses import fields

from .contracts import ContentDigest, ContractViolation, canonical_json_bytes
from .dependency_scope_closure import (
    MAX_BODY_BYTES,
    MAX_CANONICAL_BYTES,
    MAX_EDGES,
    MAX_MODULES,
    MAX_PACKAGES,
    MAX_PATHS,
    MAX_SCOPES,
    DependencyScopeEdge,
)
from .dependency_scope_closure_codec import (
    _array,
    _body,
    _digest,
    _exact,
    _pairs,
    _tag,
)
from .dependency_scope_closure_codec_v2 import _declaration
from .dependency_scope_closure_v2 import DependencyScopeProfileAssociation
from .retained_declaration_scope import (
    DECLARATION_SCOPE_CONTRACT,
    DEPENDENCY_CLOSURE_CONTRACT_V3,
    SELECTED_SOURCE_BINDING_CONTRACT,
    CodeDeclarationScopeExpectation,
    CodeRetainedDeclarationPackage,
    CodeRetainedDeclarationScopeEntry,
    CodeRetainedDeclarationScopeProjection,
    CodeRetainedDependencyScopeClosureV3,
    CodeRetainedLocalProfilePublication,
    CodeSelectedPackageSourceBinding,
    CodeSelectedPackageSourceExpectation,
)
from .retained_scope_interfaces import CodeRetainedScopeModule, MAX_SCOPE_BODY_BYTES
from .semantic_candidates import decode_semantic_candidate_listing


def declaration_closure_payload_bytes(value: CodeRetainedDependencyScopeClosureV3) -> bytes:
    if type(value) is not CodeRetainedDependencyScopeClosureV3:
        raise ContractViolation("exact declaration closure required")
    value.__post_init__()
    body = canonical_json_bytes(value.to_wire())
    if len(body) > MAX_CANONICAL_BYTES:
        raise ContractViolation("declaration closure canonical body bound")
    return body


def encode_retained_declaration_scope(value: CodeRetainedDependencyScopeClosureV3) -> bytes:
    payload = declaration_closure_payload_bytes(value)
    wire = json.loads(payload)
    wire["closure_digest"] = ContentDigest.of_bytes(payload).to_wire()
    body = canonical_json_bytes(wire)
    if len(body) > MAX_CANONICAL_BYTES:
        raise ContractViolation("declaration closure encoded body bound")
    return body


def _preflight(wire: dict[str, object]) -> None:
    bodies = [wire["repository_manifest"]]
    modules = packages = 0
    for scope in _array(wire["scopes"], MAX_SCOPES):
        _exact(scope, ("scope_key", "workspace_handle", "projection"))
        projection = _exact(
            scope["projection"],
            (
                "contract", "repository_binding_ref", "observation_digest",
                "workspace_manifest", "modules", "packages",
            ),
        )
        if projection["contract"] != DECLARATION_SCOPE_CONTRACT:
            raise ContractViolation("declaration projection contract differs")
        rows_m = _array(projection["modules"], MAX_MODULES)
        rows_p = _array(projection["packages"], MAX_PACKAGES)
        modules += len(rows_m)
        packages += len(rows_p)
        bodies.append(projection["workspace_manifest"])
        for row in rows_m:
            bodies.append(_exact(row, ("module_id", "manifest"))["manifest"])
        for row in rows_p:
            bodies.append(
                _exact(row, (f.name for f in fields(CodeRetainedDeclarationPackage)))["manifest"]
            )
    if modules > MAX_MODULES or packages > MAX_PACKAGES:
        raise ContractViolation("declaration aggregate member bound")
    _array(wire["edges"], MAX_EDGES)
    for profile in _array(wire["local_profiles"], MAX_PACKAGES):
        bodies.append(
            _exact(profile, ("owning_scope_key", "profile_key", "manifest"))["manifest"]
        )
    for association in _array(wire["profile_associations"], MAX_EDGES):
        bodies.append(
            _exact(
                association,
                ("declaring_scope_key", "declaration", "target_scope_key", "manifest"),
            )["manifest"]
        )
    if len(bodies) > MAX_PATHS:
        raise ContractViolation("declaration aggregate body count")
    size = 0
    for body in bodies:
        row = _exact(
            body,
            ("relative_path", "body_ref", "content_digest", "size_bytes", "body_hex"),
        )
        count = row["size_bytes"]
        if type(count) is not int or not 0 <= count <= MAX_SCOPE_BODY_BYTES:
            raise ContractViolation("declaration individual body bound")
        if type(row["body_hex"]) is not str or len(row["body_hex"]) != count * 2:
            raise ContractViolation("declaration body hex size differs")
        size += count
        if size > MAX_BODY_BYTES:
            raise ContractViolation("declaration aggregate raw body bound")


def decode_retained_declaration_scope(body: bytes) -> CodeRetainedDependencyScopeClosureV3:
    if type(body) is not bytes or len(body) > MAX_CANONICAL_BYTES:
        raise ContractViolation("bounded exact declaration closure bytes required")
    try:
        wire = _exact(
            json.loads(body.decode("utf-8"), object_pairs_hook=_pairs),
            (
                "contract", "consumer_scope_key", "repository_binding_ref",
                "repository_manifest", "scopes", "edges", "local_profiles",
                "profile_associations", "closure_digest",
            ),
        )
        if wire["contract"] != DEPENDENCY_CLOSURE_CONTRACT_V3:
            raise ContractViolation("declaration closure contract differs")
        _preflight(wire)
        scopes = []
        for row in wire["scopes"]:
            projection = row["projection"]
            modules = tuple(
                CodeRetainedScopeModule(m["module_id"], _body(m["manifest"]))
                for m in projection["modules"]
            )
            packages = []
            for package in projection["packages"]:
                args = dict(package)
                args["manifest"] = _body(args["manifest"])
                packages.append(CodeRetainedDeclarationPackage(**args))
            scopes.append(
                CodeRetainedDeclarationScopeEntry(
                    row["scope_key"], row["workspace_handle"],
                    CodeRetainedDeclarationScopeProjection(
                        projection["repository_binding_ref"],
                        _digest(projection["observation_digest"]),
                        _body(projection["workspace_manifest"]),
                        modules, tuple(packages),
                    ),
                )
            )
        edges = []
        for row in wire["edges"]:
            args = dict(_exact(row, (f.name for f in fields(DependencyScopeEdge))))
            args["declaration"] = _declaration(args["declaration"])
            for key in ("channel", "revision", "profile_key", "semantic_contract_provider_keys"):
                args[key] = _tag(args[key], providers=key == "semantic_contract_provider_keys")
            edges.append(DependencyScopeEdge(**args))
        local_profiles = tuple(
            CodeRetainedLocalProfilePublication(
                row["owning_scope_key"], row["profile_key"], _body(row["manifest"])
            )
            for row in wire["local_profiles"]
        )
        associations = tuple(
            DependencyScopeProfileAssociation(
                row["declaring_scope_key"], _declaration(row["declaration"]),
                row["target_scope_key"], _body(row["manifest"]),
            )
            for row in wire["profile_associations"]
        )
        result = CodeRetainedDependencyScopeClosureV3(
            wire["consumer_scope_key"], wire["repository_binding_ref"],
            _body(wire["repository_manifest"]), tuple(scopes), tuple(edges),
            local_profiles, associations,
        )
        if (
            _digest(wire["closure_digest"]) != result.closure_digest
            or encode_retained_declaration_scope(result) != body
        ):
            raise ContractViolation("declaration closure digest or canonical bytes differ")
        return result
    except (ValueError, TypeError, KeyError, RecursionError) as error:
        raise ContractViolation("invalid declaration closure encoding") from error


def encode_selected_package_source_binding(value: CodeSelectedPackageSourceBinding) -> bytes:
    if type(value) is not CodeSelectedPackageSourceBinding:
        raise ContractViolation("exact selected source binding required")
    value.__post_init__()
    body = canonical_json_bytes(value.to_wire())
    if len(body) > MAX_CANONICAL_BYTES:
        raise ContractViolation("selected binding body bound")
    return body


def decode_selected_package_source_binding(body: bytes) -> CodeSelectedPackageSourceBinding:
    if type(body) is not bytes or len(body) > MAX_CANONICAL_BYTES:
        raise ContractViolation("bounded selected binding bytes required")
    try:
        wire = _exact(
            json.loads(body.decode("utf-8"), object_pairs_hook=_pairs),
            ("contract", "expectation", "candidates"),
        )
        if wire["contract"] != SELECTED_SOURCE_BINDING_CONTRACT:
            raise ContractViolation("selected binding contract differs")
        expected = _exact(
            wire["expectation"],
            (
                "declaration", "closure_digest", "scope_key", "module_id",
                "package_id", "manifest_relative_path", "manifest_content_digest",
                "source_identity_digest",
            ),
        )
        declaration = CodeDeclarationScopeExpectation(
            **_exact(
                expected["declaration"],
                (
                    "repository_binding_ref", "parent_identity", "process_id",
                    "operation_identity", "epoch_identity",
                ),
            )
        )
        expectation = CodeSelectedPackageSourceExpectation(
            declaration, _digest(expected["closure_digest"]),
            expected["scope_key"], expected["module_id"], expected["package_id"],
            expected["manifest_relative_path"],
            _digest(expected["manifest_content_digest"]),
            _digest(expected["source_identity_digest"]),
        )
        candidates = decode_semantic_candidate_listing(
            canonical_json_bytes(wire["candidates"])
        )
        result = CodeSelectedPackageSourceBinding(expectation, candidates)
        if encode_selected_package_source_binding(result) != body:
            raise ContractViolation("selected binding bytes are not canonical")
        return result
    except (ValueError, TypeError, KeyError, RecursionError) as error:
        raise ContractViolation("invalid selected binding encoding") from error


__all__ = [
    "decode_retained_declaration_scope",
    "decode_selected_package_source_binding",
    "encode_retained_declaration_scope",
    "encode_selected_package_source_binding",
]
