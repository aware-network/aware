from __future__ import annotations
import json
from collections.abc import Mapping, Sequence
from aware_meta_type_schema import ScalarKind, ShapeKind, ValueShape
from typing import Any, Callable
from types import FunctionType
import sys
from . import owner_values as _owner
from .owner_values import canonical_json, Cardinality, MutationScope, TraversalPolicy, OBJECT_ABI_CONTRACT, OBJECT_ACTION_ROLES_CONTRACT, OntologyObjectAbi, OntologyObjectActionBinding, OntologyObjectActionParameterBinding, OntologyObjectActionRole, OntologyObjectActionRoleDeclaration, OntologyObjectActionRoleManifest, OntologyObjectClassBinding, OntologyObjectFieldBinding, OntologyObjectRelationshipBinding, OntologyObjectRelationshipConstructorPath, OntologyObjectRelationshipDirection, ActionValueMode, RelationshipEndpointResidence, SchemaActionDefinition, SchemaActionParameterDefinition
SUPPORTED_OBJECT_ABI_CONTRACTS = (OBJECT_ABI_CONTRACT,)

class OntologyObjectAbiDecodeError(ValueError):
    pass

def negotiate_object_abi_contract(offered_contracts: Sequence[str], *, supported_contracts: Sequence[str]=SUPPORTED_OBJECT_ABI_CONTRACTS) -> str:
    offered = _call(_tokens, offered_contracts, 'offered_contracts')
    supported = _call(_tokens, supported_contracts, 'supported_contracts')
    for contract in supported:
        if contract in offered:
            return contract
    raise _call(OntologyObjectAbiDecodeError, f'no supported object ABI contract; offered={_call(list, offered)!r}, supported={_call(list, supported)!r}')

def encode_object_abi(abi: OntologyObjectAbi) -> bytes:
    if _call(type, abi) is not OntologyObjectAbi:
        raise _call(TypeError, 'abi must be OntologyObjectAbi')
    _call(_owner._abi_native, abi, OntologyObjectAbi)
    return _call(_call(canonical_json, _call(abi.to_wire)).encode)

def decode_object_abi(payload: bytes | str, *, expected_topology_digest: str | None=None, expected_schema_digest: str | None=None, expected_schema_slice_digest: str | None=None, expected_abi_digest: str | None=None, supported_contracts: Sequence[str]=SUPPORTED_OBJECT_ABI_CONTRACTS, allow_external_dependency_bindings: bool=False) -> OntologyObjectAbi:
    """Decode bindings; external metadata requires explicit profile selection.

    This option preserves declared external relationship metadata. It supplies
    no external Object state, read authorization or navigation capability. The
    default retains the historical closed class-closure profile.
    """
    if _call(type, allow_external_dependency_bindings) is not bool:
        raise _call(TypeError, 'external dependency profile must be exact bool')
    for authority in (expected_topology_digest, expected_schema_digest, expected_schema_slice_digest, expected_abi_digest):
        if authority is not None and _call(type, authority) is not str:
            raise _call(TypeError, 'expected digests must be exact str or None')
    _call(_tokens, supported_contracts, 'supported_contracts')
    root = _call(_root, payload)
    _call(_exact, root, {'contract', 'topology_digest', 'schema_digest', 'schema_slice_digest', 'action_roles', 'classes', 'abi_digest'}, '$')
    contract = _call(_text, root, 'contract', '$')
    _call(negotiate_object_abi_contract, (contract,), supported_contracts=supported_contracts)
    if contract != OBJECT_ABI_CONTRACT:
        raise _call(OntologyObjectAbiDecodeError, f'decoder does not implement {contract!r}')
    try:
        roles = _call(_decode_roles, root['action_roles'], '$.action_roles')
        abi = _call(OntologyObjectAbi, topology_digest=_call(_text, root, 'topology_digest', '$'), schema_digest=_call(_text, root, 'schema_digest', '$'), schema_slice_digest=_call(_text, root, 'schema_slice_digest', '$'), action_roles=roles, classes=_call(tuple, (_call(_decode_class, item, f'$.classes[{index}]') for index, item in _call(enumerate, _call(_array, root, 'classes', '$')))), abi_digest=_call(_text, root, 'abi_digest', '$'), contract=contract)
    except (TypeError, ValueError) as error:
        if _call(isinstance, error, OntologyObjectAbiDecodeError):
            raise
        raise _call(OntologyObjectAbiDecodeError, f'object ABI violates {contract}: {error}') from error
    expected = (('topology_digest', expected_topology_digest, abi.topology_digest), ('schema_digest', expected_schema_digest, abi.schema_digest), ('schema_slice_digest', expected_schema_slice_digest, abi.schema_slice_digest), ('abi_digest', expected_abi_digest, abi.abi_digest))
    for field, authority, actual in expected:
        if authority is not None and authority != actual:
            raise _call(OntologyObjectAbiDecodeError, f'object ABI {field} authority mismatched')
    _call(_validate_portable_abi_closure, abi, allow_external_dependency_bindings)
    return abi

def _validate_portable_abi_closure(abi: OntologyObjectAbi, allow_external_dependency_bindings: bool=False) -> None:
    roles = {item.action_ref: item for item in abi.action_roles.actions}
    classes = {item.type_ref: item for item in abi.classes}
    bound_actions: set[str] = _call(set)
    for class_binding in abi.classes:
        for action in class_binding.actions:
            declaration = _call(roles.get, action.action_ref)
            if declaration is None or (declaration.definition.target_type_ref != class_binding.type_ref or declaration.role is not action.role or _call(_owner._abi_paths, declaration.relationship_constructor_paths) != _call(_owner._abi_paths, action.relationship_constructor_paths)):
                raise _call(OntologyObjectAbiDecodeError, 'object ABI Action binding escaped authored role authority')
            expected_parameters = _call(_owner._abi_parameters, declaration.definition.parameters)
            actual_parameters = _call(_owner._abi_parameters, action.parameters)
            if actual_parameters != expected_parameters:
                raise _call(OntologyObjectAbiDecodeError, 'object ABI Action signature escaped authored role authority')
            _call(bound_actions.add, action.action_ref)
        for relationship in class_binding.relationships:
            outgoing = relationship.direction is OntologyObjectRelationshipDirection.OUTGOING
            owner_type_ref = relationship.source_type_ref if outgoing else relationship.target_type_ref
            peer_type_ref = relationship.target_type_ref if outgoing else relationship.source_type_ref
            if owner_type_ref != class_binding.type_ref or (peer_type_ref not in classes and not (
                allow_external_dependency_bindings and relationship.endpoint_residence is RelationshipEndpointResidence.EXTERNAL_DEPENDENCY
            )):
                raise _call(OntologyObjectAbiDecodeError, 'object ABI relationship binding escaped class closure')
    if bound_actions != _call(set, roles):
        raise _call(OntologyObjectAbiDecodeError, 'object ABI class bindings do not exactly cover authored Action roles')

def _decode_roles(value: object, path: str) -> OntologyObjectActionRoleManifest:
    item = _call(_object, value, path)
    _call(_exact, item, {'contract', 'topology_digest', 'actions', 'manifest_digest'}, path)
    contract = _call(_text, item, 'contract', path)
    if contract != OBJECT_ACTION_ROLES_CONTRACT:
        raise _call(OntologyObjectAbiDecodeError, 'nested Action-role contract is unsupported')
    return _call(OntologyObjectActionRoleManifest, topology_digest=_call(_text, item, 'topology_digest', path), actions=_call(tuple, (_call(_decode_role, entry, f'{path}.actions[{index}]') for index, entry in _call(enumerate, _call(_array, item, 'actions', path)))), manifest_digest=_call(_text, item, 'manifest_digest', path), contract=contract)

def _decode_role(value: object, path: str) -> OntologyObjectActionRoleDeclaration:
    item = _call(_object, value, path)
    _call(_exact, item, {'definition', 'role', 'relationship_constructor_paths'}, path)
    return _call(OntologyObjectActionRoleDeclaration, _call(_decode_action, item['definition'], f'{path}.definition'), _call(OntologyObjectActionRole, _call(_text, item, 'role', path)), _call(tuple, (_call(_decode_path, entry, f'{path}.relationship_constructor_paths[{index}]') for index, entry in _call(enumerate, _call(_array, item, 'relationship_constructor_paths', path)))))

def _decode_path(value: object, path: str) -> OntologyObjectRelationshipConstructorPath:
    item = _call(_object, value, path)
    _call(_exact, item, {'relationship_refs', 'constructor_action_ref'}, path)
    return _call(OntologyObjectRelationshipConstructorPath, _call(_text_array, item, 'relationship_refs', path), _call(_text, item, 'constructor_action_ref', path))

def _decode_action(value: object, path: str) -> SchemaActionDefinition:
    item = _call(_object, value, path)
    _call(_exact, item, {'action_ref', 'target_type_ref', 'parameters', 'result_shape', 'result_value_mode', 'mutation_scope', 'mutation_type_refs'}, path)
    result_shape = item['result_shape']
    return _call(SchemaActionDefinition, _call(_text, item, 'action_ref', path), _call(_text, item, 'target_type_ref', path), _call(tuple, (_call(_decode_parameter, entry, f'{path}.parameters[{index}]') for index, entry in _call(enumerate, _call(_array, item, 'parameters', path)))), None if result_shape is None else _call(_decode_shape, result_shape, f'{path}.result_shape'), _call(ActionValueMode, _call(_text, item, 'result_value_mode', path)), _call(MutationScope, _call(_text, item, 'mutation_scope', path)), _call(_text_array, item, 'mutation_type_refs', path))

def _decode_parameter(value: object, path: str) -> SchemaActionParameterDefinition:
    item = _call(_object, value, path)
    _call(_exact, item, {'parameter_ref', 'position', 'shape', 'required', 'nullable', 'value_mode'}, path)
    return _call(SchemaActionParameterDefinition, _call(_text, item, 'parameter_ref', path), _call(_integer, item, 'position', path), _call(_decode_shape, item['shape'], f'{path}.shape'), _call(_boolean, item, 'required', path), _call(_boolean, item, 'nullable', path), _call(ActionValueMode, _call(_text, item, 'value_mode', path)))

def _decode_class(value: object, path: str) -> OntologyObjectClassBinding:
    item = _call(_object, value, path)
    _call(_exact, item, {'type_ref', 'class_name', 'fields', 'actions', 'relationships', 'binding_digest'}, path)
    return _call(OntologyObjectClassBinding, _call(_text, item, 'type_ref', path), _call(_text, item, 'class_name', path), _call(tuple, (_call(_decode_field, entry, f'{path}.fields[{index}]') for index, entry in _call(enumerate, _call(_array, item, 'fields', path)))), _call(tuple, (_call(_decode_action_binding, entry, f'{path}.actions[{index}]') for index, entry in _call(enumerate, _call(_array, item, 'actions', path)))), _call(tuple, (_call(_decode_relationship, entry, f'{path}.relationships[{index}]') for index, entry in _call(enumerate, _call(_array, item, 'relationships', path)))), _call(_text, item, 'binding_digest', path))

def _decode_field(value: object, path: str) -> OntologyObjectFieldBinding:
    item = _call(_object, value, path)
    _call(_exact, item, {'field_ref', 'attribute_name', 'shape', 'required', 'nullable'}, path)
    return _call(OntologyObjectFieldBinding, _call(_text, item, 'field_ref', path), _call(_text, item, 'attribute_name', path), _call(_decode_shape, item['shape'], f'{path}.shape'), _call(_boolean, item, 'required', path), _call(_boolean, item, 'nullable', path))

def _decode_action_binding(value: object, path: str) -> OntologyObjectActionBinding:
    item = _call(_object, value, path)
    _call(_exact, item, {'action_ref', 'method_name', 'parameters', 'role', 'relationship_constructor_paths'}, path)
    return _call(OntologyObjectActionBinding, _call(_text, item, 'action_ref', path), _call(_text, item, 'method_name', path), _call(tuple, (_call(_decode_parameter_binding, entry, f'{path}.parameters[{index}]') for index, entry in _call(enumerate, _call(_array, item, 'parameters', path)))), _call(OntologyObjectActionRole, _call(_text, item, 'role', path)), _call(tuple, (_call(_decode_path, entry, f'{path}.relationship_constructor_paths[{index}]') for index, entry in _call(enumerate, _call(_array, item, 'relationship_constructor_paths', path)))))

def _decode_parameter_binding(value: object, path: str) -> OntologyObjectActionParameterBinding:
    item = _call(_object, value, path)
    _call(_exact, item, {'parameter_ref', 'position', 'shape', 'required', 'nullable', 'value_mode'}, path)
    return _call(OntologyObjectActionParameterBinding, _call(_text, item, 'parameter_ref', path), _call(_integer, item, 'position', path), _call(_decode_shape, item['shape'], f'{path}.shape'), _call(_boolean, item, 'required', path), _call(_boolean, item, 'nullable', path), _call(ActionValueMode, _call(_text, item, 'value_mode', path)))

def _decode_relationship(value: object, path: str) -> OntologyObjectRelationshipBinding:
    item = _call(_object, value, path)
    _call(_exact, item, {'relationship_ref', 'method_name', 'source_type_ref', 'target_type_ref', 'direction', 'cardinality', 'traversal', 'endpoint_residence'}, path)
    return _call(OntologyObjectRelationshipBinding, _call(_text, item, 'relationship_ref', path), _call(_text, item, 'method_name', path), _call(_text, item, 'source_type_ref', path), _call(_text, item, 'target_type_ref', path), _call(OntologyObjectRelationshipDirection, _call(_text, item, 'direction', path)), _call(Cardinality, _call(_text, item, 'cardinality', path)), _call(TraversalPolicy, _call(_text, item, 'traversal', path)), None if item['endpoint_residence'] is None else _call(RelationshipEndpointResidence, _call(_text, item, 'endpoint_residence', path)))

def _decode_shape(value: object, path: str) -> ValueShape:
    item = _call(_object, value, path)
    _call(_exact, item, {'kind', 'scalar_kind', 'type_ref', 'element', 'map_value', 'variants'}, path)
    scalar = item['scalar_kind']
    type_ref = item['type_ref']
    if scalar is not None and _call(type, scalar) is not str:
        raise _call(OntologyObjectAbiDecodeError, f'{path}.scalar_kind must be text or null')
    if type_ref is not None and _call(type, type_ref) is not str:
        raise _call(OntologyObjectAbiDecodeError, f'{path}.type_ref must be text or null')
    return _call(ValueShape, _call(ShapeKind, _call(_text, item, 'kind', path)), scalar_kind=None if scalar is None else _call(ScalarKind, scalar), type_ref=type_ref, element=None if item['element'] is None else _call(_decode_shape, item['element'], f'{path}.element'), map_value=None if item['map_value'] is None else _call(_decode_shape, item['map_value'], f'{path}.map_value'), variants=_call(tuple, (_call(_decode_shape, entry, f'{path}.variants[{index}]') for index, entry in _call(enumerate, _call(_array, item, 'variants', path)))))

def _root(payload: Any) -> Mapping[str, object]:
    if _call(type, payload) is bytes:
        try:
            payload = _call(payload.decode)
        except UnicodeDecodeError as error:
            raise _call(OntologyObjectAbiDecodeError, 'payload is not UTF-8') from error
    if _call(type, payload) is not str:
        raise _call(TypeError, 'payload must be bytes or str')
    try:
        return _call(_object, _call(json.loads, payload, object_pairs_hook=_without_duplicates), '$')
    except json.JSONDecodeError as error:
        raise _call(OntologyObjectAbiDecodeError, 'payload is not JSON') from error

def _without_duplicates(values: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in values:
        if key in result:
            raise _call(OntologyObjectAbiDecodeError, f'duplicate JSON key {key!r}')
        result[key] = value
    return result

def _object(value: Any, path: str) -> Mapping[str, Any]:
    if _call(type, value) is not dict or _call(any, (_call(type, key) is not str for key in value)):
        raise _call(OntologyObjectAbiDecodeError, f'{path} must be object')
    return value

def _exact(value: Mapping[str, Any], keys: set[str], path: str) -> None:
    if _call(set, value) != keys:
        raise _call(OntologyObjectAbiDecodeError, f'{path} keys are not exact; missing={_call(sorted, keys - _call(set, value))!r}, unknown={_call(sorted, _call(set, value) - keys)!r}')

def _array(value: Mapping[str, Any], field: str, path: str) -> list[object]:
    result = value[field]
    if _call(type, result) is not list:
        raise _call(OntologyObjectAbiDecodeError, f'{path}.{field} must be array')
    return result

def _text(value: Mapping[str, Any], field: str, path: str) -> str:
    result = value[field]
    if _call(type, result) is not str:
        raise _call(OntologyObjectAbiDecodeError, f'{path}.{field} must be text')
    return result

def _text_array(value: Mapping[str, Any], field: str, path: str) -> tuple[str, ...]:
    result = _call(_array, value, field, path)
    if _call(any, (_call(type, item) is not str for item in result)):
        raise _call(OntologyObjectAbiDecodeError, f'{path}.{field} must contain text')
    return _call(tuple, (item for item in result if _call(type, item) is str))

def _boolean(value: Mapping[str, Any], field: str, path: str) -> bool:
    result = value[field]
    if _call(type, result) is not bool:
        raise _call(OntologyObjectAbiDecodeError, f'{path}.{field} must be bool')
    return result

def _integer(value: Mapping[str, Any], field: str, path: str) -> int:
    result = value[field]
    if _call(type, result) is not int:
        raise _call(OntologyObjectAbiDecodeError, f'{path}.{field} must be integer')
    return result

def _tokens(values: Sequence[str], path: str) -> tuple[str, ...]:
    if _call(type, values) is not tuple and _call(type, values) is not list:
        raise _call(TypeError, f'{path} must be exact tuple or list')
    result = _call(tuple, values)
    if not result or _call(any, (_call(type, item) is not str or not _call(item.strip) for item in result)):
        raise _call(OntologyObjectAbiDecodeError, f'{path} must contain non-empty text')
    if _call(len, result) != _call(len, _call(set, result)):
        raise _call(OntologyObjectAbiDecodeError, f'{path} contains duplicates')
    return result
__all__ = ['SUPPORTED_OBJECT_ABI_CONTRACTS', 'OntologyObjectAbiDecodeError', 'decode_object_abi', 'encode_object_abi', 'negotiate_object_abi_contract']


# A private fence is built once from the actual owning closure, never supplied by callers.
def _call(operation: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Any:
    return operation(*args, **kwargs)


_codec_guard: Any = None
def _install_codec_dispatch() -> Any:
    """Retain the genuine verifier in every codec entrance and return fence."""
    guard: Any = None
    unwind = BaseException
    namespace = globals()
    originals = []
    wrappers = []

    def protect(operation):
        originals.append(operation)

        def protected(*args, **kwargs):
            check = guard
            check()
            try:
                result = operation(*args, **kwargs)
            except unwind:
                check()
                raise
            check()
            return result

        protected.__name__ = operation.__name__
        protected.__qualname__ = operation.__qualname__
        protected.__module__ = operation.__module__
        protected.__annotations__ = operation.__annotations__
        protected.__kwdefaults__ = operation.__kwdefaults__
        protected.__dict__["__wrapped__"] = operation
        wrappers.append(protected)
        return protected

    for name, operation in tuple(namespace.items()):
        if type(operation) is FunctionType and operation.__module__ == __name__ and name != "_install_codec_dispatch":
            namespace[name] = protect(operation)
    guard_cell = next(cell for cell, name in zip(wrappers[0].__closure__, wrappers[0].__code__.co_freevars)
                      if name == "guard")

    guard = _owner._protect_shape_dispatch((
        OntologyObjectAbiDecodeError,
        _owner.OntologyObjectAbi, _owner.OntologyObjectActionRoleManifest,
        _owner.OntologyObjectActionRoleDeclaration, _owner.SchemaActionDefinition,
        _owner.SchemaActionParameterDefinition, _owner.OntologyObjectClassBinding,
        _owner.OntologyObjectActionBinding, _owner.OntologyObjectActionParameterBinding,
        _owner.OntologyObjectFieldBinding, _owner.OntologyObjectRelationshipBinding,
        _owner.OntologyObjectRelationshipConstructorPath,
        _owner.Cardinality, _owner.TraversalPolicy, _owner.ActionValueMode,
        _owner.RelationshipEndpointResidence, _owner.OntologyObjectActionRole,
        _owner.OntologyObjectRelationshipDirection, _owner.MutationScope,
        json.JSONEncoder, json.JSONDecoder, json.JSONDecodeError,
    ), guard_name="_codec_guard", guard_namespace=globals(),
    helpers=(*tuple(value for value in tuple(globals().values()) if type(value) is FunctionType), *originals),
    retained_guard_cell=guard_cell,
    extra_modules=tuple(sys.modules[name] for name in (
        __name__, "json", "json.encoder", "json.decoder", "json.scanner", "hashlib",
    )))
    return guard


_codec_guard = _install_codec_dispatch()
