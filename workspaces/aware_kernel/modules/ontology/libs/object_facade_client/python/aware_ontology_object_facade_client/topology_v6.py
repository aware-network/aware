"""Closed portable-input portal topology v6; never producer/issuance authority.

Explicit successor profile, not V5 negotiation or a fallback decoder. Complete
original evidence remains out-of-band and mandatory for the bounded consumer.
No Meta/runtime/Workspace import or semantic reconstruction belongs here.
"""

from __future__ import annotations

import hashlib
import json
from types import FrameType
from typing import cast
from uuid import UUID

CONTRACT = "aware.ontology.runtime-schema-topology.v6"
PROFILE = "meta-inspect-forward-portals.v1"
MAX_BYTES = 1_048_576
MAX_ITEMS = 16_384
MAX_DEPTH = 64
_FIELDS = frozenset(("contract", "profile", "namespace", "semantic_version", "schema_digest",
    "schema_slice_digest", "input_grade", "evidence_digest", "projections", "relationships", "portals"))
_PROJECTION_FIELDS = frozenset(("projection_ref", "graph_ref", "identity_ref", "is_branchable",
    "root_node_refs", "nodes", "observables"))


class PortalTopologyError(ValueError):
    """Invalid detached content, not an authorization decision."""


def _plain(value: object) -> None:
    pending = [(value, 0)]
    count = size = 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if count > MAX_ITEMS or depth > MAX_DEPTH:
            raise PortalTopologyError("v6 intrinsic work/depth bound")
        kind = type(item)
        if item is None or kind is bool:
            continue
        if kind is int:
            if not 0 <= cast(int, item) <= MAX_ITEMS:
                raise PortalTopologyError("v6 integer bound")
        elif kind is str:
            try:
                size += len(cast(str, item).encode("utf-8"))
            except UnicodeError as error:
                raise PortalTopologyError("v6 invalid UTF-8") from error
            if size > MAX_BYTES:
                raise PortalTopologyError("v6 scalar byte bound")
        elif kind is list or kind is tuple:
            values = cast(list[object], item)
            if count + len(pending) + len(values) > MAX_ITEMS:
                raise PortalTopologyError("v6 intrinsic work bound")
            pending.extend((child, depth + 1) for child in values)
        elif kind is dict:
            members = cast(dict[object, object], item)
            if count + len(pending) + 2 * len(members) > MAX_ITEMS:
                raise PortalTopologyError("v6 intrinsic work bound")
            for key, child in members.items():
                if type(key) is not str:
                    raise PortalTopologyError("v6 foreign key")
                pending.extend(((key, depth + 1), (child, depth + 1)))
        else:
            raise PortalTopologyError("v6 foreign/non-integral value")


def _canonical(value: object) -> bytes:
    _plain(value)
    body = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False).encode("utf-8")
    if len(body) > MAX_BYTES:
        raise PortalTopologyError("v6 encoded byte bound")
    return body


def content_digest(domain: str, body: bytes) -> str:
    try:
        if (type(domain) is not str or domain not in (CONTRACT, CONTRACT + ".input-evidence")
                or type(body) is not bytes or len(body) > MAX_BYTES):
            raise PortalTopologyError("v6 digest operands")
        return "sha256:" + hashlib.sha256(domain.encode("utf-8") + b"\n" + body).hexdigest()
    finally:
        domain, body = cast(str, None), cast(bytes, None)


def _evidence_in_read(bundle: bytes, slice_: bytes, records: tuple[bytes, ...], facts: tuple[object, ...]) -> str:
    if type(bundle) is not bytes or type(slice_) is not bytes or type(records) is not tuple or type(facts) is not tuple:
        raise PortalTopologyError("v6 exact evidence operands required")
    total = len(bundle) + len(slice_)
    if total > MAX_BYTES or len(records) > MAX_ITEMS:
        raise PortalTopologyError("v6 evidence item bound")
    hashes: list[str] = []
    for body in records:
        if type(body) is not bytes:
            raise PortalTopologyError("v6 foreign evidence body")
        total += len(body)
        if total > MAX_BYTES:
            raise PortalTopologyError("v6 evidence byte bound")
        hashes.append("sha256:" + hashlib.sha256(body).hexdigest())
    facts_body = _canonical(facts)
    if total + len(facts_body) > MAX_BYTES:
        raise PortalTopologyError("v6 evidence byte bound")
    payload: list[object] = ["sha256:" + hashlib.sha256(bundle).hexdigest(),
        "sha256:" + hashlib.sha256(slice_).hexdigest(), hashes,
        "sha256:" + hashlib.sha256(facts_body).hexdigest()]
    return content_digest(CONTRACT + ".input-evidence", _canonical(payload))


def _text(value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise PortalTopologyError("v6 nonempty token required")
    return value


def _digest(value: object) -> None:
    text = _text(value)
    if len(text) != 71 or not text.startswith("sha256:") or any(c not in "0123456789abcdef" for c in text[7:]):
        raise PortalTopologyError("v6 digest shape")


def _uuid(value: object) -> str:
    text = _text(value)
    try:
        if str(UUID(text)) == text:
            return text
    except ValueError:
        pass
    raise PortalTopologyError("v6 canonical UUID required")


def _ref(value: object, prefix: str) -> str:
    text = _text(value)
    if not text.startswith(prefix):
        raise PortalTopologyError("v6 record reference family")
    _uuid(text[len(prefix):])
    return text


def _array(value: object, length: int | None = None) -> list[object]:
    if type(value) is not list and type(value) is not tuple:
        raise PortalTopologyError("v6 intrinsic array required")
    values = cast(list[object], value)
    if length is not None and len(values) != length:
        raise PortalTopologyError("v6 row arity")
    return values


def _bool(value: object) -> None:
    if type(value) is not bool:
        raise PortalTopologyError("v6 intrinsic boolean required")


def _ordered_unique(values: list[str]) -> None:
    if len(set(values)) != len(values):
        raise PortalTopologyError("v6 repeated member")


def _keyed(values: list[str]) -> None:
    if values != sorted(set(values)):
        raise PortalTopologyError("v6 keyed table order/uniqueness")


def _validate(root: object) -> dict[str, object]:
    _plain(root)  # BEFORE hashing, equality or conversion of supplied values.
    if type(root) is not dict:
        raise PortalTopologyError("v6 closed root fields")
    data = cast(dict[str, object], root)
    if frozenset(data) != _FIELDS:
        raise PortalTopologyError("v6 closed root fields")
    if data["contract"] != CONTRACT or data["profile"] != PROFILE or data["input_grade"] != "portable_input":
        raise PortalTopologyError("v6 explicit contract/profile/grade required")
    for name in ("namespace", "semantic_version"):
        _text(data[name])
    for name in ("schema_digest", "schema_slice_digest", "evidence_digest"):
        _digest(data[name])
    projections: dict[str, dict[str, object]] = {}
    nodes: dict[str, tuple[str, str]] = {}
    graph_refs: list[str] = []
    identity_refs: list[str] = []
    all_observables: list[str] = []
    for raw in _array(data["projections"]):
        if type(raw) is not dict:
            raise PortalTopologyError("v6 closed projection fields")
        projection = cast(dict[str, object], raw)
        if frozenset(projection) != _PROJECTION_FIELDS:
            raise PortalTopologyError("v6 closed projection fields")
        ref = _text(projection["projection_ref"])
        graph_refs.append(_ref(projection["graph_ref"], "opg:"))
        identity_refs.append(_ref(projection["identity_ref"], "opg-identity:"))
        _bool(projection["is_branchable"])
        roots: list[str] = []
        node_keys: list[str] = []
        for raw_node in _array(projection["nodes"]):
            node = _array(raw_node, 6)
            key, type_ref = _ref(node[0], "opg-node:"), _text(node[1])
            _bool(node[2])
            _bool(node[3])
            if node[4] not in ("one", "all", "top_n"):
                raise PortalTopologyError("v6 node selection")
            if node[4] == "top_n":
                if type(node[5]) is not int or node[5] <= 0:
                    raise PortalTopologyError("v6 positive top-n required")
            elif node[5] is not None:
                raise PortalTopologyError("v6 unexpected selection limit")
            if key in nodes:
                raise PortalTopologyError("v6 multiply owned node")
            nodes[key] = ref, type_ref
            node_keys.append(key)
            if node[2]:
                roots.append(key)
        if not roots or list(_array(projection["root_node_refs"])) != roots:
            raise PortalTopologyError("v6 exact root membership required")
        _ordered_unique(node_keys)
        observables = [_ref(value, "observable:") for value in _array(projection["observables"])]
        _ordered_unique(observables)
        all_observables.extend(observables)
        if ref in projections:
            raise PortalTopologyError("v6 repeated projection")
        projections[ref] = projection
    if not projections:
        raise PortalTopologyError("v6 projection inventory required")
    _keyed(list(projections))
    for values in (graph_refs, identity_refs, all_observables):
        _ordered_unique(values)
    relationships: dict[str, list[object]] = {}
    for raw in _array(data["relationships"]):
        row = _array(raw, 14)
        key = _ref(row[0], "relationship:")
        for value in row[1:4]:
            _text(value)
        for slot in (row[4], row[5]):
            slots = _array(slot, 1)
            if type(slots[0]) is not int or slots[0] != 0:
                raise PortalTopologyError("v6 unsupported nonlocal relationship")
        if row[6] is not None or row[7] is not None:
            raise PortalTopologyError("v6 association unavailable")
        for value in row[8:13]:
            _bool(value)
        if row[8] or row[9] or row[12]:
            raise PortalTopologyError("v6 unsupported transformed/collection relationship")
        policy = _array(row[13], 25)
        if (policy[0] not in ("one_to_one", "many_to_one")
                or tuple(policy[1:5]) != ("reference", "forward", False, "forward")):
            raise PortalTopologyError("v6 unsupported relationship policy")
        _text(policy[5])
        for position in (3, 6, 7, 8, 9, 10, 13, 14, 21, 22):
            _bool(policy[position])
        if any(policy[position] is not None for position in (11, 12, 15, 16, 17, 18, 19, 20, 23, 24)) or any(
            policy[position] for position in (13, 14, 21, 22)):
            raise PortalTopologyError("v6 unsupported reverse/association/parent policy")
        if row[10] is not policy[8] or row[10] is not (policy[0] == "one_to_one"):
            raise PortalTopologyError("v6 uniqueness/policy mismatch")
        if key in relationships:
            raise PortalTopologyError("v6 repeated relationship")
        relationships[key] = row
    _keyed(list(relationships))
    portal_keys: list[str] = []
    binding_ids: list[str] = []
    consumed: set[str] = set()
    for raw in _array(data["portals"]):
        row = _array(raw, 10)
        portal_keys.append(_ref(row[0], "opg-portal:"))
        source, target = _text(row[1]), _text(row[2])
        relation = relationships.get(_ref(row[3], "relationship:"))
        field, source_node, target_node = _text(row[4]), _ref(row[5], "opg-node:"), _ref(row[6], "opg-node:")
        source_type, target_type = _text(row[7]), _text(row[8])
        binding_ids.append(_uuid(row[9]))
        if (source == target or source not in projections or target not in projections
                or nodes.get(source_node) != (source, source_type) or nodes.get(target_node) != (target, target_type)
                or relation is None or list(relation[1:4]) != [source_type, field, target_type]):
            raise PortalTopologyError("v6 portal endpoint/relationship/membership mismatch")
        consumed.add(cast(str, row[3]))
    _keyed(portal_keys)
    _ordered_unique(binding_ids)
    if consumed != set(relationships):
        raise PortalTopologyError("v6 incomplete relationship portal coverage")
    return data


def _encode_in_read(payload: object) -> bytes:
    """Canonical portable value only; input must omit topology_digest."""
    data = _validate(payload)
    body = _canonical(data)
    root = {**data, "topology_digest": content_digest(CONTRACT, body)}
    return _canonical(root)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PortalTopologyError("v6 duplicate JSON key")
        result[key] = value
    return result


def _constant(_value: str) -> object:
    raise PortalTopologyError("v6 nonfinite JSON value")


def _decode_in_read(body: object) -> dict[str, object]:
    """Bounded framing/content verification; neither origin nor freshness."""
    if type(body) is not bytes or len(body) > MAX_BYTES:
        raise PortalTopologyError("v6 intrinsic body/byte bound")
    quoted = escaped = token = False
    depth = count = 0
    for byte in body:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
            token = False
            count += 1
        elif byte in (91, 123):
            token = False
            depth += 1
            count += 1
        elif byte in (93, 125):
            token = False
            depth -= 1
            if depth < 0:
                raise PortalTopologyError("v6 container balance")
        elif byte in (9, 10, 13, 32, 44, 58):
            token = False
        elif not token:
            token = True
            count += 1
        if depth > MAX_DEPTH or count > MAX_ITEMS:
            raise PortalTopologyError("v6 preparse depth/item bound")
    try:
        root: object = json.loads(body, object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise PortalTopologyError("v6 invalid JSON") from error
    _plain(root)
    if type(root) is not dict:
        raise PortalTopologyError("v6 closed encoded root")
    data = cast(dict[str, object], root)
    if frozenset(data) != _FIELDS | {"topology_digest"}:
        raise PortalTopologyError("v6 closed encoded root")
    digest = data.pop("topology_digest")
    _digest(digest)
    if encode_portal_topology_v6(data) != body:
        raise PortalTopologyError("v6 canonical bytes/digest mismatch")
    return data


def _release_failure(failure: BaseException) -> None:
    trace = failure.__traceback__
    # The public wrapper is active. Only completed owner/codec frames clear.
    trace = trace.tb_next if trace is not None else None
    frame = None
    try:
        while trace is not None:
            frame = trace.tb_frame
            FrameType.clear(frame)
            trace = trace.tb_next
        if type(failure) is PortalTopologyError:
            # JSONDecodeError.doc / UnicodeError.object can retain full input
            # even after frames clear. Keep our bounded reason, not that body.
            failure.__cause__ = failure.__context__ = None
    finally:
        trace = frame = None
        failure = cast(BaseException, None)


def encode_portal_topology_v6(payload: object) -> bytes:
    """Encode a detached value; a held refusal retains no caller payload."""
    try:
        return _encode_in_read(payload)
    except BaseException as failure:
        _release_failure(failure)
        raise
    finally:
        payload = None


def decode_portal_topology_v6(body: object) -> dict[str, object]:
    """Decode bounded portable content, never original authority/currentness."""
    try:
        return _decode_in_read(body)
    except BaseException as failure:
        _release_failure(failure)
        raise
    finally:
        body = None


def evidence_digest(bundle: bytes, slice_: bytes, records: tuple[bytes, ...], facts: tuple[object, ...]) -> str:
    """Exact evidence address; not a capability or a retained source record."""
    try:
        return _evidence_in_read(bundle, slice_, records, facts)
    except BaseException as failure:
        _release_failure(failure)
        raise
    finally:
        bundle = slice_ = cast(bytes, None)
        records = cast(tuple[bytes, ...], None)
        facts = cast(tuple[object, ...], None)
