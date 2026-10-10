"""Explicit v2 wire; reuses canonical v1 body/scope grammar, never v1 admission."""

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
    DependencyScopeDeclaration,
    DependencyScopeEdge,
    DependencyScopeEntry,
)
from .dependency_scope_closure_codec import (
    _array,
    _body,
    _digest,
    _exact,
    _pairs,
    _scope,
    _tag,
    _wire,
)
from .dependency_scope_closure_v2 import (
    CONTRACT_V2,
    CodeRetainedDependencyScopeClosureV2,
    DependencyScopeProfileAssociation,
)
from .retained_scope_interfaces import MAX_SCOPE_BODY_BYTES


def closure_payload_bytes_v2(value):
    if type(value) is not CodeRetainedDependencyScopeClosureV2:
        raise ContractViolation("exact v2 dependency closure required")
    value.__post_init__()
    payload = {
        "contract": CONTRACT_V2,
        "consumer_scope_key": value.consumer_scope_key,
        "scopes": _wire(value.scopes),
        "edges": _wire(value.edges),
        "profile_associations": [
            {
                "declaring_scope_key": a.declaring_scope_key,
                "declaration": _wire(a.declaration),
                "target_scope_key": a.target_scope_key,
                "manifest": a.manifest.to_wire(),
            }
            for a in value.profile_associations
        ],
    }
    body = canonical_json_bytes(payload)
    if len(body) > MAX_CANONICAL_BYTES:
        raise ContractViolation("v2 closure encoded bound")
    return body


def encode_dependency_scope_closure_v2(value):
    payload = closure_payload_bytes_v2(value)
    wire = json.loads(payload)
    wire["closure_digest"] = ContentDigest.of_bytes(payload).to_wire()
    result = canonical_json_bytes(wire)
    if len(result) > MAX_CANONICAL_BYTES:
        raise ContractViolation("v2 closure encoded bound")
    return result


def _declaration(value):
    args = dict(_exact(value, (f.name for f in fields(DependencyScopeDeclaration))))
    args["manifest_content_digest"] = _digest(args["manifest_content_digest"])
    return DependencyScopeDeclaration(**args)


def _preflight(wire):
    """Count repeated wire occurrences before allocating decoded raw bodies."""
    bodies = []
    modules = packages = 0
    for row in _array(wire["scopes"], MAX_SCOPES):
        _exact(row, ("scope_key", "workspace_handle", "projection"))
        p = row["projection"]
        _exact(
            p,
            (
                "contract",
                "repository_binding_ref",
                "observation_digest",
                "workspace_manifest",
                "modules",
                "packages",
            ),
        )
        ms = _array(p["modules"], MAX_MODULES)
        ps = _array(p["packages"], MAX_PACKAGES)
        modules += len(ms)
        packages += len(ps)
        if modules > MAX_MODULES or packages > MAX_PACKAGES:
            raise ContractViolation("v2 aggregate member count bound")
        bodies.append(p["workspace_manifest"])
        for m in ms:
            _exact(m, ("module_id", "manifest"))
            bodies.append(m["manifest"])
        for p in ps:
            if type(p) is not dict or "manifest" not in p:
                raise ContractViolation("package body required")
            bodies.append(p["manifest"])
    edges = _array(wire["edges"], MAX_EDGES)
    associations = _array(wire["profile_associations"], MAX_EDGES)
    if len(edges) != len(associations):
        raise ContractViolation("profile association count differs")
    for row in associations:
        _exact(
            row, ("declaring_scope_key", "declaration", "target_scope_key", "manifest")
        )
        bodies.append(row["manifest"])
    if len(bodies) > MAX_PATHS:
        raise ContractViolation("v2 aggregate path count bound")
    size = 0
    for body in bodies:
        _exact(
            body,
            ("relative_path", "body_ref", "content_digest", "size_bytes", "body_hex"),
        )
        n = body["size_bytes"]
        if type(n) is not int or not 0 <= n <= MAX_SCOPE_BODY_BYTES:
            raise ContractViolation("v2 individual body bound")
        if type(body["body_hex"]) is not str or len(body["body_hex"]) != n * 2:
            raise ContractViolation("v2 body hex length differs")
        size += n
        if size > MAX_BODY_BYTES:
            raise ContractViolation("v2 aggregate raw body bound")


def decode_dependency_scope_closure_v2(body):
    if type(body) is not bytes or len(body) > MAX_CANONICAL_BYTES:
        raise ContractViolation("bounded exact v2 closure bytes required")
    try:
        wire = json.loads(body.decode("utf-8"), object_pairs_hook=_pairs)
        _exact(
            wire,
            (
                "contract",
                "consumer_scope_key",
                "scopes",
                "edges",
                "profile_associations",
                "closure_digest",
            ),
        )
        if wire["contract"] != CONTRACT_V2:
            raise ContractViolation("v2 closure contract differs")
        _preflight(wire)
        scopes = tuple(
            DependencyScopeEntry(
                r["scope_key"], r["workspace_handle"], _scope(r["projection"])
            )
            for r in wire["scopes"]
        )
        edges = []
        for row in wire["edges"]:
            args = dict(_exact(row, (f.name for f in fields(DependencyScopeEdge))))
            args["declaration"] = _declaration(args["declaration"])
            for key in (
                "channel",
                "revision",
                "profile_key",
                "semantic_contract_provider_keys",
            ):
                args[key] = _tag(
                    args[key], providers=key == "semantic_contract_provider_keys"
                )
            edges.append(DependencyScopeEdge(**args))
        associations = tuple(
            DependencyScopeProfileAssociation(
                r["declaring_scope_key"],
                _declaration(r["declaration"]),
                r["target_scope_key"],
                _body(r["manifest"]),
            )
            for r in wire["profile_associations"]
        )
        result = CodeRetainedDependencyScopeClosureV2(
            wire["consumer_scope_key"], scopes, tuple(edges), associations
        )
        if (
            _digest(wire["closure_digest"]) != result.closure_digest
            or encode_dependency_scope_closure_v2(result) != body
        ):
            raise ContractViolation("v2 closure digest or canonical bytes differ")
        return result
    except (ValueError, TypeError, KeyError, RecursionError) as error:
        raise ContractViolation("invalid v2 dependency closure encoding") from error
