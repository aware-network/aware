"""Strict portable closure codec; decoding never authenticates original evidence."""
from __future__ import annotations

import json
from dataclasses import fields

from .contracts import ContentDigest, ContractViolation, canonical_json_bytes
from .dependency_scope_closure import (
    CONTRACT,
    MAX_CANONICAL_BYTES,
    MAX_EDGES,
    MAX_SCOPES,
    CodeRetainedDependencyScopeClosure,
    DependencyScopeDeclaration,
    DependencyScopeEdge,
    DependencyScopeEntry,
    DependencyScopeRestriction,
)
from .retained_scope_interfaces import (
    RETAINED_SCOPE_CONTRACT,
    CodeRetainedScopeBody,
    CodeRetainedScopeModule,
    CodeRetainedScopePackage,
    CodeRetainedScopeProjection,
)


def _exact(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ContractViolation("exact closure wire fields required")
    return value


def _array(value, limit):
    if type(value) is not list or len(value) > limit:
        raise ContractViolation("closure array bound/type differs")
    return value


def _wire(value):
    if type(value) is ContentDigest:
        return value.to_wire()
    if type(value) is CodeRetainedScopeProjection:
        return value.to_wire()
    if type(value) is DependencyScopeRestriction:
        return {"state": value.state, **({"value": _wire(value.value)} if value.state == "present" else {})}
    if type(value) is tuple:
        return [_wire(v) for v in value]
    if type(value) in (CodeRetainedDependencyScopeClosure, DependencyScopeDeclaration, DependencyScopeEdge, DependencyScopeEntry):
        return {f.name: _wire(getattr(value, f.name)) for f in fields(value)}
    return value


def closure_payload_bytes(value):
    if type(value) is not CodeRetainedDependencyScopeClosure:
        raise ContractViolation("exact dependency closure required")
    value.__post_init__()
    projected = _wire(value)
    if not isinstance(projected, dict):
        raise ContractViolation("closure object required")
    body = canonical_json_bytes({"contract": CONTRACT, **projected})
    if len(body) > MAX_CANONICAL_BYTES:
        raise ContractViolation("closure encoded bound")
    return body


def encode_dependency_scope_closure(value):
    payload = closure_payload_bytes(value)
    wire = json.loads(payload)
    wire["closure_digest"] = ContentDigest.of_bytes(payload).to_wire()
    result = canonical_json_bytes(wire)
    if len(result) > MAX_CANONICAL_BYTES:
        raise ContractViolation("closure encoded bound")
    return result


def _digest(value):
    return ContentDigest(value)


def _body(value):
    _exact(value, ("relative_path", "body_ref", "content_digest", "size_bytes", "body_hex"))
    size = value["size_bytes"]
    if type(size) is not int or not 0 <= size <= 16_777_216:
        raise ContractViolation("retained body bound")
    text = value["body_hex"]
    if type(text) is not str or len(text) != size * 2:
        raise ContractViolation("retained body hex length")
    raw = bytes.fromhex(text)
    if raw.hex() != text:
        raise ContractViolation("noncanonical body hex")
    return CodeRetainedScopeBody(value["relative_path"], value["body_ref"], _digest(value["content_digest"]), raw)


def _scope(value):
    _exact(value, ("contract", "repository_binding_ref", "observation_digest", "workspace_manifest", "modules", "packages"))
    if value["contract"] != RETAINED_SCOPE_CONTRACT:
        raise ContractViolation("scope contract differs")
    modules = []
    for row in _array(value["modules"], 4096):
        _exact(row, ("module_id", "manifest"))
        modules.append(CodeRetainedScopeModule(row["module_id"], _body(row["manifest"])))
    packages = []
    for row in _array(value["packages"], 16384):
        _exact(row, (f.name for f in fields(CodeRetainedScopePackage)))
        args = dict(row)
        args["manifest"] = _body(args["manifest"])
        args["source_identity_digest"] = _digest(args["source_identity_digest"])
        packages.append(CodeRetainedScopePackage(**args))
    return CodeRetainedScopeProjection(value["repository_binding_ref"], _digest(value["observation_digest"]),
                                      _body(value["workspace_manifest"]), tuple(modules), tuple(packages))


def _tag(value, providers=False):
    if type(value) is not dict:
        raise ContractViolation("restriction object required")
    present = value.get("state") == "present"
    _exact(value, ("state", "value") if present else ("state",))
    item = value.get("value")
    if present and providers:
        item = tuple(_array(item, 256))
    return DependencyScopeRestriction(value["state"], item)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractViolation("duplicate closure JSON key")
        result[key] = value
    return result


def decode_dependency_scope_closure(body):
    if type(body) is not bytes or len(body) > MAX_CANONICAL_BYTES:
        raise ContractViolation("bounded exact closure bytes required")
    try:
        wire = json.loads(body.decode("utf-8"), object_pairs_hook=_pairs)
        _exact(wire, ("contract", "consumer_scope_key", "scopes", "edges", "closure_digest"))
        if wire["contract"] != CONTRACT:
            raise ContractViolation("closure contract differs")
        scopes = []
        for row in _array(wire["scopes"], MAX_SCOPES):
            _exact(row, ("scope_key", "workspace_handle", "projection"))
            scopes.append(DependencyScopeEntry(row["scope_key"], row["workspace_handle"], _scope(row["projection"])))
        edges = []
        for row in _array(wire["edges"], MAX_EDGES):
            _exact(row, (f.name for f in fields(DependencyScopeEdge)))
            args = dict(row)
            declaration = dict(_exact(args["declaration"], (f.name for f in fields(DependencyScopeDeclaration))))
            declaration["manifest_content_digest"] = _digest(declaration["manifest_content_digest"])
            args["declaration"] = DependencyScopeDeclaration(**declaration)
            for key in ("channel", "revision", "profile_key", "semantic_contract_provider_keys"):
                args[key] = _tag(args[key], providers=key == "semantic_contract_provider_keys")
            edges.append(DependencyScopeEdge(**args))
        result = CodeRetainedDependencyScopeClosure(wire["consumer_scope_key"], tuple(scopes), tuple(edges))
        if _digest(wire["closure_digest"]) != result.closure_digest or encode_dependency_scope_closure(result) != body:
            raise ContractViolation("closure digest or canonical bytes differ")
        return result
    except (ValueError, TypeError, KeyError, RecursionError) as error:
        raise ContractViolation("invalid dependency closure encoding") from error
