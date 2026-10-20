"""Strict structural Object-value reconstruction. No provider authority."""
from __future__ import annotations

from . import owner_values as _owner
from .owner_values import (
    OntologyObjectValue, RelationshipEndpointPortableInputError,
    ExternalAssociationEndpointReference, ExternalSchemaFieldEndpointReference,
    ExternalRelationshipEndpointReference, ExternalRelationshipEndpointEvidenceClaim,
    ExternalRelationshipEndpointEvidenceProfile, SchemaTopologyInputGrade,
    RelationshipEndpointResidence, EXTERNAL_SCHEMA_FIELD_ENDPOINT_REFERENCE_CONTRACT,
    EXTERNAL_ASSOCIATION_ENDPOINT_REFERENCE_CONTRACT,
    EXTERNAL_RELATIONSHIP_ENDPOINT_EVIDENCE_CLAIM_CONTRACT,
)
import json
from types import ModuleType, BuiltinMethodType
from contextvars import ContextVar
from typing import Any, cast
from .owner_values import _reject_number, _unique_pairs, canonical_json, digest_payload
_metrics: ContextVar[dict[str, int] | None] = ContextVar('object_value_codec_metrics', default=None)

def _track(name: str, count: int) -> None:
    if _call(type, _metrics) is not ContextVar:
        raise _call(TypeError, 'codec metrics context changed')
    metrics = _call(_metrics.get)
    if metrics is not None:
        if _call(type, metrics) is not dict or _call(type, _call(metrics.get, name, 0)) is not int:
            raise _call(TypeError, 'codec metrics must be exact counters')
        metrics[name] = _call(metrics.get, name, 0) + count

def _preflight(value: object) -> None:
    native_type, failure = type, TypeError
    visited = 0
    def visit(item):
        nonlocal visited
        visited += 1
        kind = native_type(item)
        if item is None or kind is bool or kind is int:
            return
        if kind is str:
            item.encode('utf-8', 'strict')
            return
        if kind is list:
            for child in item:
                visit(child)
            return
        if kind is dict:
            for key in item:
                if native_type(key) is not str or not key:
                    raise failure('keys must be exact nonempty strings')
                key.encode('utf-8', 'strict')
            for child in dict.values(item):
                visit(child)
            return
        raise failure('non-structural wire value')
    visit(value)
    _call(_track, 'members_visited', visited)


def _make_native_json():
    # The native C string primitives have no replaceable Python body. Keep
    # their original references through the entire native-only traversal.
    if type(json) is not ModuleType:
        raise TypeError("JSON module must be native")
    namespace = object.__getattribute__(json, "__dict__")
    encoder, decoder = namespace["encoder"], namespace["decoder"]
    if type(encoder) is not ModuleType or type(decoder) is not ModuleType:
        raise TypeError("JSON helper modules must be native")
    quote = object.__getattribute__(encoder, "__dict__")["encode_basestring"]
    scan = object.__getattribute__(decoder, "__dict__")["scanstring"]
    if type(quote) is not BuiltinMethodType or type(scan) is not BuiltinMethodType:
        raise TypeError("JSON string primitives must be native")
    native_type, integer, length = type, int, len
    failure = ValueError

    def encode(value):
        def render(item):
            kind = native_type(item)
            if item is None: return 'null'
            if kind is bool: return 'true' if item else 'false'
            if kind is int: return str(item)
            if kind is str: return quote(item)
            if kind is list: return '[' + ','.join(render(child) for child in item) + ']'
            if kind is dict:
                return '{' + ','.join(quote(key) + ':' + render(item[key]) for key in sorted(item)) + '}'
            raise failure('non-structural wire value')
        return render(value).encode('utf-8', 'strict')

    def decode(body):
        text = body.decode('utf-8', 'strict')
        end = length(text)
        def parse(index):
            if index >= end: raise failure('incomplete JSON')
            marker = text[index]
            if marker == '"': return scan(text, index + 1, True)
            if marker == '[':
                items = []
                index += 1
                if index < end and text[index] == ']': return items, index + 1
                while True:
                    item, index = parse(index)
                    items.append(item)
                    if index >= end: raise failure('incomplete array')
                    if text[index] == ']': return items, index + 1
                    if text[index] != ',': raise failure('array delimiter')
                    index += 1
            if marker == '{':
                items = {}
                index += 1
                if index < end and text[index] == '}': return items, index + 1
                while True:
                    if index >= end or text[index] != '"': raise failure('object key')
                    key, index = scan(text, index + 1, True)
                    if key in items: raise failure('duplicate JSON key')
                    if index >= end or text[index] != ':': raise failure('object delimiter')
                    item, index = parse(index + 1)
                    items[key] = item
                    if index >= end: raise failure('incomplete object')
                    if text[index] == '}': return items, index + 1
                    if text[index] != ',': raise failure('object delimiter')
                    index += 1
            for literal, value in (('null', None), ('true', True), ('false', False)):
                if text.startswith(literal, index): return value, index + length(literal)
            start = index
            if marker == '-': index += 1
            while index < end and '0' <= text[index] <= '9': index += 1
            if index == start or (marker == '-' and index == start + 1): raise failure('invalid JSON scalar')
            return integer(text[start:index]), index
        value, consumed = parse(0)
        if consumed != end: raise failure('trailing JSON')
        return value
    return encode, decode


_native_encode, _native_decode = _make_native_json()

def _canonical(wire: object) -> bytes:
    _call(_preflight, wire)
    body = _call(_native_encode, wire)
    _call(_track, 'bytes_encoded', len(body))
    return body

def _parse(body: bytes) -> dict[str, Any]:
    if type(body) is not bytes:
        raise TypeError('body must be exact bytes')
    _call(_track, 'bytes_decoded', len(body))
    wire = _call(_native_decode, body)
    if type(wire) is not dict or _call(_canonical, wire) != body:
        raise ValueError('noncanonical body')
    return wire

def _keys(value: object, names: str) -> dict[str, Any]:
    _preflight(value)
    if _call(type, value) is not dict or _call(set, value) != _call(set, _call(names.split)):
        raise _call(ValueError, 'wire fields mismatched')
    return _call(cast, dict[str, Any], value)

def _token(value: object) -> str:
    if _call(type, value) is not str or not value or _call(any, (_call(c.isspace) for c in _call(cast, str, value))):
        raise _call(ValueError, 'invalid exact token')
    _call(_call(cast, str, value).encode, 'utf-8', 'strict')
    return _call(cast, str, value)

def _ordered(values: object, coordinates: tuple[str, ...]) -> list[dict[str, Any]]:
    if _call(type, values) is not list:
        raise _call(TypeError, 'collection must be exact list')
    previous = None
    for value in _call(cast, list[dict[str, Any]], values):
        if _call(type, value) is not dict:
            raise _call(TypeError, 'member must be exact dictionary')
        current = _call(tuple, (_call(_call(_token, value[k]).encode) for k in coordinates))
        if previous is not None and current <= previous:
            raise _call(ValueError, 'unordered or duplicate coordinates')
        previous = current
    return _call(cast, list[dict[str, Any]], values)

def _check_digest(wire: dict[str, Any], name: str) -> None:
    payload = {k: v for k, v in _call(wire.items) if k not in ('contract', name)}
    if wire[name] != _call(_owner._value_digest, wire['contract'], payload):
        raise _call(ValueError, 'semantic digest mismatched')

def _field(wire: object):
    _call(_track, 'reconstruction_calls', 1)
    from .owner_values import FieldValue, RuntimeValue, ValueKind
    item = _call(_keys, wire, 'field_ref value')
    raw = _call(_keys, item['value'], 'value_kind value')
    return _call(FieldValue, _call(_token, item['field_ref']), _call(RuntimeValue.of, _call(ValueKind, raw['value_kind']), raw['value']))

def _slice(wire: object):
    _call(_track, 'reconstruction_calls', 1)
    from .owner_values import Cardinality, CoverageGrade, ProjectionCoverage, TraversalPolicy
    from .owner_values import OntologyObjectRelationshipDirection, OntologyObjectRelationshipEdgeValue, OntologyObjectRelationshipSlice
    item = _call(_keys, wire, 'contract relationship_ref direction owner_instance_ref owner_type_ref peer_type_ref cardinality traversal coverage edges relationship_value_digest')
    if item['contract'] != 'aware.ontology.object-relationship-slice.v1':
        raise _call(ValueError, 'slice contract mismatched')
    coverage = _call(_keys, item['coverage'], 'grade missing_refs')
    missing = coverage['missing_refs']
    if _call(type, missing) is not list:
        raise _call(TypeError, 'missing refs must be exact list')
    tokens = [_call(_call(_token, x).encode) for x in missing]
    if tokens != _call(sorted, _call(set, tokens)):
        raise _call(ValueError, 'missing refs unordered or duplicated')
    edges = []
    refs = _call(set)
    for edge in _call(_ordered, item['edges'], ('relationship_instance_ref', 'source_instance_ref', 'target_instance_ref', 'peer_instance_ref')):
        _call(_keys, edge, 'relationship_instance_ref source_instance_ref target_instance_ref peer_instance_ref')
        if edge['relationship_instance_ref'] in refs:
            raise _call(ValueError, 'duplicate edge identity')
        _call(refs.add, edge['relationship_instance_ref'])
        _call(edges.append, _call(OntologyObjectRelationshipEdgeValue, **edge))
    _call(_check_digest, item, 'relationship_value_digest')
    return _call(OntologyObjectRelationshipSlice, _call(_token, item['relationship_ref']), _call(OntologyObjectRelationshipDirection, item['direction']), _call(_token, item['owner_instance_ref']), _call(_token, item['owner_type_ref']), _call(_token, item['peer_type_ref']), _call(Cardinality, item['cardinality']), _call(TraversalPolicy, item['traversal']), _call(ProjectionCoverage, _call(CoverageGrade, coverage['grade']), _call(tuple, missing)), _call(tuple, edges), item['relationship_value_digest'])

def _reconstruct(wire: dict[str, object]):
    _call(_track, 'reconstruction_calls', 1)
    from .owner_values import external_relationship_endpoint_sort_key
    from .owner_values import OntologyObjectValue
    _call(_preflight, wire)
    item = _call(_keys, wire, 'contract instance_ref type_ref fields relationships external_endpoint_references value_digest')
    if item['contract'] != 'aware.ontology.object-value.v3':
        raise _call(ValueError, 'Object-value contract mismatched')
    fields = _call(tuple, (_call(_field, x) for x in _call(_ordered, item['fields'], ('field_ref',))))
    relationships = _call(tuple, (_call(_slice, x) for x in _call(_ordered, item['relationships'], ('relationship_ref', 'direction'))))
    if _call(type, item['external_endpoint_references']) is not list:
        raise _call(TypeError, 'endpoints must be exact list')
    endpoints = _call(tuple, (_call(_decode_endpoint_reference, x, 'endpoint') for x in item['external_endpoint_references']))
    keys = [_call(tuple, (_call(v.encode) for v in _call(external_relationship_endpoint_sort_key, x))) for x in endpoints]
    if keys != _call(sorted, _call(set, keys)):
        raise _call(ValueError, 'endpoint order or duplication')
    _call(_check_digest, item, 'value_digest')
    return _call(OntologyObjectValue, _call(_token, item['instance_ref']), _call(_token, item['type_ref']), fields, relationships, endpoints, item['value_digest'])

def _check_record(value: object) -> None:
    if not any(type(value) is kind for kind in _owner._value_records):
        raise TypeError('foreign Object-value object')
    _call(_owner._value_native, value)


def _decode_endpoint_reference(value: object, path: str) -> ExternalRelationshipEndpointReference:
    item = _call(_object, value, path)
    contract = _call(item.get, 'contract')
    if contract == EXTERNAL_SCHEMA_FIELD_ENDPOINT_REFERENCE_CONTRACT:
        _call(_exact, item, {'contract', 'relationship_ref', 'source_instance_ref', 'source_type_ref', 'package_ref', 'type_ref', 'instance_ref', 'schema_evidence_ref', 'endpoint_residence', 'evidence_claim', 'reference_digest'}, path)
        return _call(ExternalSchemaFieldEndpointReference, _call(_text, item, 'relationship_ref', path), _call(_text, item, 'source_instance_ref', path), _call(_text, item, 'source_type_ref', path), _call(_text, item, 'package_ref', path), _call(_text, item, 'type_ref', path), _call(_text, item, 'instance_ref', path), _call(_text, item, 'schema_evidence_ref', path), _call(RelationshipEndpointResidence, _call(_text, item, 'endpoint_residence', path)), _call(_decode_endpoint_claim, item['evidence_claim'], f'{path}.evidence_claim'), _call(_text, item, 'reference_digest', path))
    _call(_exact, item, {'contract', 'role_ref', 'association_instance_ref', 'association_type_ref', 'package_ref', 'type_ref', 'instance_ref', 'schema_evidence_ref', 'endpoint_residence', 'evidence_claim', 'reference_digest'}, path)
    if contract != EXTERNAL_ASSOCIATION_ENDPOINT_REFERENCE_CONTRACT:
        raise _call(RelationshipEndpointPortableInputError, 'unsupported endpoint reference')
    return _call(ExternalAssociationEndpointReference, _call(_text, item, 'role_ref', path), _call(_text, item, 'association_instance_ref', path), _call(_text, item, 'association_type_ref', path), _call(_text, item, 'package_ref', path), _call(_text, item, 'type_ref', path), _call(_text, item, 'instance_ref', path), _call(_text, item, 'schema_evidence_ref', path), _call(RelationshipEndpointResidence, _call(_text, item, 'endpoint_residence', path)), _call(_decode_endpoint_claim, item['evidence_claim'], f'{path}.evidence_claim'), _call(_text, item, 'reference_digest', path))

def _decode_endpoint_claim(value: object, path: str) -> ExternalRelationshipEndpointEvidenceClaim:
    item = _call(_object, value, path)
    _call(_exact, item, {'contract', 'provider_key', 'provider_generation', 'profile', 'evidence_ref', 'input_grade', 'claim_digest'}, path)
    if item['contract'] != EXTERNAL_RELATIONSHIP_ENDPOINT_EVIDENCE_CLAIM_CONTRACT:
        raise _call(RelationshipEndpointPortableInputError, 'unsupported endpoint claim')
    return _call(ExternalRelationshipEndpointEvidenceClaim, _call(_text, item, 'provider_key', path), _call(_text, item, 'provider_generation', path), _call(ExternalRelationshipEndpointEvidenceProfile, _call(_text, item, 'profile', path)), _call(_text, item, 'evidence_ref', path), _call(SchemaTopologyInputGrade, _call(_text, item, 'input_grade', path)), _call(_text, item, 'claim_digest', path))

def _kind_is(kind, kinds):
    return any(kind is expected for expected in kinds)


def _object(value: object, path: str) -> dict[str, Any]:
    _call(_preflight, value)
    if _call(type, value) is not dict:
        raise _call(RelationshipEndpointPortableInputError, 'endpoint must be exact dictionary')
    return _call(cast, dict[str, Any], value)

def _exact(value, expected, path):
    if _call(set, value) != expected:
        raise _call(RelationshipEndpointPortableInputError, 'endpoint keys are not exact')

def _text(value, field, path):
    if _call(type, value[field]) is not str:
        raise _call(RelationshipEndpointPortableInputError, 'endpoint field must be exact text')
    return value[field]

def encode_object_value(value: OntologyObjectValue) -> bytes:
    if _call(type, value) is not OntologyObjectValue:
        raise _call(TypeError, 'value must be exact OntologyObjectValue')
    return _call(value.canonical_bytes)

def decode_object_value(body: bytes) -> OntologyObjectValue:
    return _call(_reconstruct, _call(_parse, body))

_codec_guard = None

def _call(operation: Any, /, *args: Any, **kwargs: Any) -> Any:
    return operation(*args, **kwargs)

__all__ = ["encode_object_value", "decode_object_value"]
