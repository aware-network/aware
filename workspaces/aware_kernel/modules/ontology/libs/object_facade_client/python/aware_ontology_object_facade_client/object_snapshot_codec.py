"""Complete detached snapshot grammar. Decoding never reconstructs host authority."""
from __future__ import annotations
from typing import Any
from . import owner_values as _owner
from . import object_value_codec as _values
from .owner_values import OntologyObjectProviderAuthorityClaim, OntologyObjectSnapshotAuthorityData, OntologyObjectSnapshotData, OntologyObjectSourceAuthorityEvidence, OBJECT_SOURCE_AUTHORITY_CONTRACT, OBJECT_SNAPSHOT_AUTHORITY_CONTRACT, OBJECT_SNAPSHOT_CONTRACT, digest_payload

def _canonical(wire):
    return _call(_values._canonical, wire)

def _parse(body):
    return _call(_values._parse, body)

def _provider(wire):
    item = _call(_values._keys, wire, 'grade provider_key authority_ref provider_generation canonical_branch_ref canonical_commit_ref')
    return _call(OntologyObjectProviderAuthorityClaim, **item)

def _source(wire):
    if wire is None:
        return None
    item = _call(_values._keys, wire, 'contract source_coordinate_ref source_observation_ref source_mapping_digest source_authority_digest')
    if item['contract'] != OBJECT_SOURCE_AUTHORITY_CONTRACT:
        raise _call(ValueError, 'source authority contract mismatched')
    _call(_values._check_digest, item, 'source_authority_digest')
    return _call(OntologyObjectSourceAuthorityEvidence, **{k: v for k, v in _call(item.items) if k != 'contract'})

def _authority(wire):
    item = _call(_values._keys, wire, 'contract value_digest provider_authority class_binding_digest topology_digest branch_ref revision_ref projection_ref view_digest source_authority authority_digest')
    if item['contract'] != OBJECT_SNAPSHOT_AUTHORITY_CONTRACT:
        raise _call(ValueError, 'snapshot authority contract mismatched')
    provider = _call(_provider, item['provider_authority'])
    source = _call(_source, item['source_authority'])
    _call(_values._check_digest, item, 'authority_digest')
    payload = {k: v for k, v in _call(item.items) if k not in ('contract', 'provider_authority', 'source_authority')}
    return _call(OntologyObjectSnapshotAuthorityData, provider_authority=provider, source_authority=source, **payload)

def _reconstruct(wire):
    item = _call(_values._keys, wire, 'contract value authority snapshot_digest')
    if item['contract'] != OBJECT_SNAPSHOT_CONTRACT:
        raise _call(ValueError, 'snapshot contract mismatched')
    value = _call(_values._reconstruct, item['value'])
    authority = _call(_authority, item['authority'])
    _call(_values._check_digest, item, 'snapshot_digest')
    return _call(OntologyObjectSnapshotData, value, authority, item['snapshot_digest'])

def encode_object_snapshot_data(data: OntologyObjectSnapshotData) -> bytes:
    if _call(type, data) is not OntologyObjectSnapshotData:
        raise _call(TypeError, 'snapshot must be exact detached data')
    return _call(_canonical, _call(_owner._value_snapshot_wire, data))

def decode_object_snapshot_data(body: bytes) -> OntologyObjectSnapshotData:
    return _call(_reconstruct, _call(_parse, body))

_codec_guard = None

def _call(operation: Any, /, *args: Any, **kwargs: Any) -> Any:
    return operation(*args, **kwargs)

__all__ = ["encode_object_snapshot_data", "decode_object_snapshot_data"]
