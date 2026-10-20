"""Complete detached ABI, canonical parity and behavior-free native refusal."""

import hashlib
import json
from typing import Any, cast

import pytest

import aware_ontology_object_facade_client as facade
from aware_ontology_object_facade_client import object_abi_codec as codec
from aware_ontology_object_facade_client import owner_values as owner


def _fixture(shape=None, *, result=False):
    shape = shape or owner.ValueShape.scalar(owner.ScalarKind.INTEGER)
    parameter = owner.SchemaActionParameterDefinition('T.fn.number', 0, shape, False, True)
    action = owner.SchemaActionDefinition('T.fn', 'T', (parameter,), shape if result else None)
    declaration = owner.OntologyObjectActionRoleDeclaration(action, owner.OntologyObjectActionRole.INSTANCE)
    role_payload = {'contract': owner.OBJECT_ACTION_ROLES_CONTRACT,
                    'topology_digest': 'topology:1', 'actions': [declaration.to_wire()]}
    roles = owner.OntologyObjectActionRoleManifest('topology:1', (declaration,), owner.digest_payload(owner.OBJECT_ACTION_ROLES_CONTRACT, role_payload))
    field = owner.OntologyObjectFieldBinding('T.number', 'number', shape, False, True)
    binding = owner.OntologyObjectActionBinding('T.fn', 'fn', (
        owner.OntologyObjectActionParameterBinding('T.fn.number', 0, shape, False, True, owner.ActionValueMode.VALUE),
    ))
    cls = owner.OntologyObjectClassBinding.create(type_ref='T', class_name='T', fields=(field,), actions=(binding,), relationships=())
    payload = {'contract': owner.OBJECT_ABI_CONTRACT, 'topology_digest': 'topology:1',
               'schema_digest': 'schema:1', 'schema_slice_digest': 'slice:1',
               'action_roles': roles.to_wire(), 'classes': [cls.to_wire()]}
    return owner.OntologyObjectAbi('topology:1', 'schema:1', 'slice:1', roles, (cls,), owner.digest_payload(owner.OBJECT_ABI_CONTRACT, payload))


def test_single_public_owner_and_no_attached_host_factories():
    for name in ('OntologyObjectAbi', 'OntologyObjectActionRoleDeclaration', 'OntologyObjectActionRoleManifest'):
        assert getattr(facade, name) is getattr(owner, name)
        assert getattr(owner, name).__module__ == owner.__name__
    assert not hasattr(facade.OntologyObjectAbi, 'derive')
    assert not hasattr(facade.OntologyObjectActionRoleManifest, 'create')
    for name in ('derive_object_abi', 'create_object_action_role_manifest', 'runtime_action_argument',
                 'OntologyRuntime', 'AuthorityEvidence', 'OntologyObjectSnapshot'):
        assert not hasattr(facade, name) and not hasattr(owner, name)


@pytest.mark.parametrize('scalar', list(owner.ScalarKind))
@pytest.mark.parametrize('result', [False, True])
def test_complete_scalar_shape_bytes_and_expected_consistency(scalar, result):
    value = _fixture(owner.ValueShape.scalar(scalar), result=result)
    encoded = facade.encode_object_abi(value)
    assert encoded == owner.canonical_json(value.to_wire()).encode()
    decoded = facade.decode_object_abi(encoded, expected_topology_digest=value.topology_digest,
                                      expected_schema_digest=value.schema_digest,
                                      expected_schema_slice_digest=value.schema_slice_digest,
                                      expected_abi_digest=value.abi_digest)
    assert type(decoded) is owner.OntologyObjectAbi
    assert facade.encode_object_abi(decoded) == encoded
    assert decoded.action_roles.action('T.fn') is decoded.action_roles.actions[0]
    assert decoded.class_binding('T') is decoded.classes[0]


@pytest.mark.parametrize('shape', [
    owner.ValueShape.named('Other'),
    owner.ValueShape.list_of(owner.ValueShape.scalar(owner.ScalarKind.INTEGER)),
    owner.ValueShape.map_of(owner.ValueShape.named('Other')),
    owner.ValueShape.union_of(owner.ValueShape.named('Other'), owner.ValueShape.scalar(owner.ScalarKind.STRING)),
])
def test_recursive_shape_roundtrip_and_whole_join(shape):
    encoded = facade.encode_object_abi(_fixture(shape))
    assert facade.encode_object_abi(facade.decode_object_abi(encoded)) == encoded


@pytest.mark.parametrize('slot', ['topology_digest', 'schema_digest', 'schema_slice_digest', 'abi_digest'])
def test_expected_digests_remain_consistency_checks(slot):
    with pytest.raises(facade.OntologyObjectAbiDecodeError, match='authority mismatched'):
        facade.decode_object_abi(facade.encode_object_abi(_fixture()), **{'expected_'+slot: 'different'})


@pytest.mark.parametrize('case', ['payload', 'nested_payload', 'expected', 'supported', 'supported_item', 'encode',
                                 'abi_contract', 'abi_roles', 'abi_classes', 'abi_class', 'manifest_actions',
                                 'manifest_action', 'role_definition', 'role_enum', 'role_paths', 'lookup'])
def test_foreign_inputs_refuse_with_zero_calls(case):
    calls = []

    class ForeignMeta(type):
        def __eq__(cls, other):
            calls.append('metaclass equality')
            raise AssertionError('foreign metaclass')

    class Foreign(metaclass=ForeignMeta):
        def __getattribute__(self, name):
            calls.append('attribute')
            raise AssertionError('foreign attribute')

        def __iter__(self):
            calls.append('iterator')
            raise AssertionError('foreign iterator')

        def __eq__(self, other):
            calls.append('equality')
            raise AssertionError('foreign equality')

        def __str__(self):
            calls.append('string')
            raise AssertionError('foreign string')

    value = _fixture();foreign = Foreign();encoded = facade.encode_object_abi(value)
    def tampered(slot, data):
        object.__setattr__(value, slot, data)
        return facade.encode_object_abi(value)
    choices = {
        'payload': lambda: facade.decode_object_abi(cast(Any, foreign)),
        'nested_payload': lambda: codec._decode_class({'type_ref': foreign}, '$'),
        'expected': lambda: facade.decode_object_abi(encoded, expected_abi_digest=cast(Any, foreign)),
        'supported': lambda: facade.decode_object_abi(encoded, supported_contracts=cast(Any, foreign)),
        'supported_item': lambda: facade.negotiate_object_abi_contract(cast(Any, [foreign])),
        'encode': lambda: facade.encode_object_abi(cast(Any, foreign)),
        'abi_contract': lambda: tampered('contract', foreign),
        'abi_roles': lambda: tampered('action_roles', foreign),
        'abi_classes': lambda: tampered('classes', foreign),
        'abi_class': lambda: tampered('classes', (foreign,)),
        'manifest_actions': lambda: cast(Any, owner.OntologyObjectActionRoleManifest)('topology:1', foreign, 'digest'),
        'manifest_action': lambda: cast(Any, owner.OntologyObjectActionRoleManifest)('topology:1', (foreign,), 'digest'),
        'role_definition': lambda: cast(Any, owner.OntologyObjectActionRoleDeclaration)(foreign, 'instance'),
        'role_enum': lambda: cast(Any, owner.OntologyObjectActionRoleDeclaration)(value.action_roles.actions[0].definition, foreign),
        'role_paths': lambda: cast(Any, owner.OntologyObjectActionRoleDeclaration)(value.action_roles.actions[0].definition, 'instance', (foreign,)),
        'lookup': lambda: value.class_binding(cast(Any, foreign)),
    }
    with pytest.raises((TypeError, ValueError)):
        choices[case]()
    assert calls == []


@pytest.mark.parametrize('payload', [b'{', b'\xff', b'{}', b'{"contract":"a","contract":"b"}',
                                   b'{"contract":"unknown","topology_digest":"t","schema_digest":"s","schema_slice_digest":"x","action_roles":{},"classes":[],"abi_digest":"d"}'])
def test_malformed_framing_is_typed(payload):
    with pytest.raises(codec.OntologyObjectAbiDecodeError):
        facade.decode_object_abi(payload)


def test_external_dependency_constructor_and_restricted_decoder_profile():
    roles_payload = {'contract': owner.OBJECT_ACTION_ROLES_CONTRACT, 'topology_digest': 't', 'actions': []}
    roles = owner.OntologyObjectActionRoleManifest('t', (), owner.digest_payload(owner.OBJECT_ACTION_ROLES_CONTRACT, roles_payload))
    relationship = owner.OntologyObjectRelationshipBinding('T.other', 'other', 'T', 'Other',
        owner.OntologyObjectRelationshipDirection.OUTGOING, owner.Cardinality.ONE,
        owner.TraversalPolicy.SOURCE_TO_TARGET, owner.RelationshipEndpointResidence.EXTERNAL_DEPENDENCY)
    cls = owner.OntologyObjectClassBinding.create(type_ref='T', class_name='T', fields=(), actions=(), relationships=(relationship,))
    payload = {'contract': owner.OBJECT_ABI_CONTRACT, 'topology_digest': 't', 'schema_digest': 's',
               'schema_slice_digest': 'x', 'action_roles': roles.to_wire(), 'classes': [cls.to_wire()]}
    value = owner.OntologyObjectAbi('t', 's', 'x', roles, (cls,), owner.digest_payload(owner.OBJECT_ABI_CONTRACT, payload))
    with pytest.raises(codec.OntologyObjectAbiDecodeError, match='relationship binding escaped class closure'):
        facade.decode_object_abi(facade.encode_object_abi(value))


@pytest.mark.parametrize('name', ['type', '__name__', 'canonical_json', '_decode_class', '_tokens'])
def test_codec_lookup_substitution_refuses_before_foreign_dispatch(monkeypatch, name):
    value = _fixture();encoded = facade.encode_object_abi(value);calls=[]
    def foreign(*args, **kwargs):
        calls.append(name)
        raise AssertionError('foreign codec lookup')
    monkeypatch.setattr(codec, name, foreign, raising=False)
    with pytest.raises(TypeError, match='operation identity'):
        facade.decode_object_abi(encoded)
    assert calls == []


def _seal_codec(monkeypatch):
    # Trusted test instrumentation seals the original observed closure before the
    # invocation. It is not a caller guard, decoder option or installed authority.
    from types import FunctionType
    import sys
    classes = (owner.OntologyObjectAbi, owner.OntologyObjectActionRoleManifest, owner.OntologyObjectActionRoleDeclaration,
               owner.SchemaActionDefinition, owner.SchemaActionParameterDefinition, owner.OntologyObjectClassBinding,
               owner.OntologyObjectActionBinding, owner.OntologyObjectActionParameterBinding,
               owner.OntologyObjectFieldBinding, owner.OntologyObjectRelationshipBinding,
               owner.OntologyObjectRelationshipConstructorPath, owner.OntologyObjectActionRole,
               owner.ActionValueMode, owner.MutationScope, codec.OntologyObjectAbiDecodeError)
    guard_cell = next(cell for name, cell in zip(codec._call.__code__.co_freevars, (codec._call.__closure__ or ()))
                      if name == 'guard')
    functions = tuple(v for k,v in tuple(vars(codec).items()) if type(v) is FunctionType and k!='_codec_guard')
    originals = tuple(v.__dict__['__wrapped__'] for v in functions if hasattr(v, '__wrapped__'))
    check = owner._protect_shape_dispatch(classes, guard_name='_codec_guard', guard_namespace=cast(dict[str, Any], vars(codec)),
        helpers=(*functions, *originals), retained_guard_cell=guard_cell,
        extra_modules=tuple(sys.modules[n] for n in (codec.__name__, 'json', 'json.encoder', 'json.decoder', 'json.scanner', 'hashlib')))
    monkeypatch.setattr(guard_cell, 'cell_contents', check)
    monkeypatch.setattr(codec, '_codec_guard', check)


@pytest.mark.parametrize('target', ['abi_init', 'manifest_post', 'class_init', 'shape_init', 'next_parser', 'encoder'])
def test_nested_parser_returns_recheck_complete_constructor_arguments(monkeypatch, target):
    value=_fixture();encoded=facade.encode_object_abi(value);calls=[];injected=[]
    original=codec._text
    def foreign(*args, **kwargs):
        calls.append(target)
        raise AssertionError('foreign nested dispatch')
    def text_return(mapping, field, path):
        result=original(mapping, field, path)
        if not injected and ((target=='abi_init' and field=='abi_digest') or
                             (target in ('manifest_post','class_init','shape_init','next_parser','encoder') and field=='contract')):
            destination = {'abi_init': (owner.OntologyObjectAbi, '__init__'),
                           'manifest_post': (owner.OntologyObjectActionRoleManifest, '__post_init__'),
                           'class_init': (owner.OntologyObjectClassBinding, '__init__'),
                           'shape_init': (owner.ValueShape, '__init__'),
                           'next_parser': (codec, '_decode_roles'),
                           'encoder': (codec, 'canonical_json')}[target]
            monkeypatch.setattr(*destination, foreign)
            injected.append(True)
        return result
    monkeypatch.setattr(codec, '_text', text_return)
    _seal_codec(monkeypatch)
    with pytest.raises(TypeError, match='operation identity'):
        facade.decode_object_abi(encoded)
    assert injected == [True] and calls == []


def test_frozen_parent_complete_abi_and_manifest_vector_projection():
    shapes = [owner.ValueShape.scalar(kind) for kind in owner.ScalarKind] + [
        owner.ValueShape.named('Other'), owner.ValueShape.list_of(owner.ValueShape.scalar(owner.ScalarKind.INTEGER)),
        owner.ValueShape.map_of(owner.ValueShape.named('Other')),
        owner.ValueShape.union_of(owner.ValueShape.named('Other'), owner.ValueShape.scalar(owner.ScalarKind.STRING)),
    ]
    values = []
    for shape in shapes:
        for result in (False, True):
            value = _fixture(shape, result=result)
            values.append({'abi': json.loads(facade.encode_object_abi(value)),
                           'manifest': value.action_roles.to_wire(),
                           'abi_digest': value.abi_digest, 'manifest_digest': value.action_roles.manifest_digest})
    encoded = owner.canonical_json(values).encode() + b'\n'
    assert len(values) == 24 and len(encoded) == 63158
    assert hashlib.sha256(encoded).hexdigest() == '786d400fa87512b09e53c0538fb8a594301892782d4f8c5c65ab20b07fa69a21'


def test_tampered_signature_mode_is_typed_refusal_before_digest_comparison():
    value = _fixture()
    object.__setattr__(value.classes[0].actions[0].parameters[0], 'value_mode', 'value')
    with pytest.raises(TypeError, match='normalized enum'):
        value.__post_init__()


@pytest.mark.parametrize(('guard_name', 'entrance'), [
    *[('_abi_guard', entry) for entry in (
        'declaration_construct', 'manifest_construct', 'abi_construct', 'action_property',
        'manifest_lookup', 'abi_lookup', 'declaration_wire', 'manifest_payload',
        'manifest_wire', 'abi_payload', 'abi_wire', 'negotiate', 'encode', 'decode')],
    *[('_codec_guard', entry) for entry in ('negotiate', 'encode', 'decode')],
])
def test_guard_binding_substitution_rejects_before_foreign_dispatch(monkeypatch, guard_name, entrance):
    value = _fixture()
    encoded = facade.encode_object_abi(value)
    declaration = value.action_roles.actions[0]
    calls = []
    def foreign(*args, **kwargs):
        calls.append(guard_name)
        raise AssertionError('foreign guard binding')
    operations = {
        'declaration_construct': lambda: owner.OntologyObjectActionRoleDeclaration(declaration.definition, declaration.role),
        'manifest_construct': lambda: owner.OntologyObjectActionRoleManifest(value.topology_digest, value.action_roles.actions, value.action_roles.manifest_digest),
        'abi_construct': lambda: owner.OntologyObjectAbi(value.topology_digest, value.schema_digest, value.schema_slice_digest, value.action_roles, value.classes, value.abi_digest),
        'action_property': lambda: declaration.action_ref,
        'manifest_lookup': lambda: value.action_roles.action('T.fn'),
        'abi_lookup': lambda: value.class_binding('T'),
        'declaration_wire': declaration.to_wire,
        'manifest_payload': value.action_roles._wire_payload,
        'manifest_wire': value.action_roles.to_wire,
        'abi_payload': value._wire_payload,
        'abi_wire': value.to_wire,
        'negotiate': lambda: facade.negotiate_object_abi_contract((owner.OBJECT_ABI_CONTRACT,)),
        'encode': lambda: facade.encode_object_abi(value),
        'decode': lambda: facade.decode_object_abi(encoded),
    }
    monkeypatch.setattr(owner if guard_name == '_abi_guard' else codec, guard_name, foreign)
    with pytest.raises(TypeError, match='operation identity'):
        operations[entrance]()
    assert calls == []


@pytest.mark.parametrize('guard_name', ['_abi_guard', '_codec_guard'])
@pytest.mark.parametrize('entrance', ['negotiate', 'encode', 'decode'])
def test_guard_binding_changed_at_codec_nested_return_is_never_dispatched(monkeypatch, guard_name, entrance):
    value = _fixture()
    encoded = facade.encode_object_abi(value)
    calls = []
    injected = []
    helper = {'negotiate': '_tokens', 'encode': 'canonical_json', 'decode': '_text'}[entrance]
    original = getattr(codec, helper)
    def foreign(*args, **kwargs):
        calls.append(guard_name)
        raise AssertionError('foreign guard at nested return')
    def returning(*args, **kwargs):
        result = original(*args, **kwargs)
        if not injected:
            monkeypatch.setattr(owner if guard_name == '_abi_guard' else codec, guard_name, foreign)
            injected.append(True)
        return result
    monkeypatch.setattr(codec, helper, returning)
    _seal_codec(monkeypatch)
    operations = {
        'negotiate': lambda: facade.negotiate_object_abi_contract((owner.OBJECT_ABI_CONTRACT,)),
        'encode': lambda: facade.encode_object_abi(value),
        'decode': lambda: facade.decode_object_abi(encoded),
    }
    with pytest.raises(TypeError, match='operation identity'):
        operations[entrance]()
    assert injected == [True] and calls == []



def _seal_abi(monkeypatch):
    # Trusted instrumentation reseals the actual original method/helper closure;
    # no guard is an input to public construction, methods or codec functions.
    from types import FunctionType
    import sys
    kinds = (owner.OntologyObjectActionRoleDeclaration, owner.OntologyObjectActionRoleManifest,
             owner.OntologyObjectAbi, owner.SchemaActionDefinition, owner.SchemaActionParameterDefinition,
             owner.OntologyObjectClassBinding, owner.OntologyObjectActionBinding,
             owner.OntologyObjectActionParameterBinding, owner.OntologyObjectFieldBinding,
             owner.OntologyObjectRelationshipBinding, owner.OntologyObjectRelationshipConstructorPath,
             owner.OntologyObjectContractError, owner.OntologyObjectActionRole,
             owner.OntologyObjectRelationshipDirection, owner.Cardinality, owner.TraversalPolicy,
             owner.RelationshipEndpointResidence, owner.ActionValueMode, owner.MutationScope,
             json.JSONEncoder, json.JSONDecoder, json.JSONDecodeError)
    functions = [v for k,v in tuple(vars(owner).items()) if type(v) is FunctionType and k != '_abi_guard']
    for kind in kinds:
        for value in vars(kind).values():
            if type(value) is FunctionType:
                functions.append(value)
            elif type(value) is property and value.fget is not None:
                functions.append(value.fget)
    originals = tuple(v.__dict__['__wrapped__'] for v in functions if hasattr(v, '__wrapped__'))
    guard_cell = next(cell for name, cell in zip(owner._abi_slot.__code__.co_freevars, (owner._abi_slot.__closure__ or ()))
                      if name == 'guard')
    check = owner._protect_shape_dispatch(kinds, guard_name='_abi_guard',
        helpers=(*functions, *originals), retained_guard_cell=guard_cell,
        extra_modules=tuple(sys.modules[n] for n in ('json', 'json.encoder', 'json.decoder', 'json.scanner', 'hashlib')))
    monkeypatch.setattr(guard_cell, 'cell_contents', check)
    monkeypatch.setattr(owner, '_abi_guard', check)


@pytest.mark.parametrize('entrance', [
    'declaration_construct', 'manifest_construct', 'abi_construct', 'action_property',
    'manifest_lookup', 'abi_lookup', 'declaration_wire', 'manifest_wire', 'abi_wire',
])
def test_abi_guard_binding_changed_at_native_slot_return_rejects_without_dispatch(monkeypatch, entrance):
    from types import FunctionType, SimpleNamespace
    value = _fixture()
    declaration = value.action_roles.actions[0]
    operation = owner._abi_slot.__dict__['__wrapped__']
    original = FunctionType(operation.__code__, operation.__globals__, operation.__name__, operation.__defaults__)
    probe = SimpleNamespace(calls=[], injected=[])
    def foreign(*args, **kwargs):
        probe.calls.append('guard')
        raise AssertionError('foreign ABI guard')
    def slot_return(receiver, field, _original=original, _probe=probe, _foreign=foreign, _patch=monkeypatch, _owner=owner):
        result = _original(receiver, field)
        if not _probe.injected:
            _patch.setattr(_owner, '_abi_guard', _foreign)
            _probe.injected.append(True)
        return result
    monkeypatch.setattr(operation, '__code__', slot_return.__code__)
    monkeypatch.setattr(operation, '__defaults__', slot_return.__defaults__)
    _seal_abi(monkeypatch)
    operations = {
        'declaration_construct': lambda: owner.OntologyObjectActionRoleDeclaration(declaration.definition, declaration.role),
        'manifest_construct': lambda: owner.OntologyObjectActionRoleManifest(value.topology_digest, value.action_roles.actions, value.action_roles.manifest_digest),
        'abi_construct': lambda: owner.OntologyObjectAbi(value.topology_digest, value.schema_digest, value.schema_slice_digest, value.action_roles, value.classes, value.abi_digest),
        'action_property': lambda: declaration.action_ref,
        'manifest_lookup': lambda: value.action_roles.action('T.fn'),
        'abi_lookup': lambda: value.class_binding('T'),
        'declaration_wire': declaration.to_wire,
        'manifest_wire': value.action_roles.to_wire,
        'abi_wire': value.to_wire,
    }
    with pytest.raises(TypeError, match='operation identity'):
        operations[entrance]()
    assert probe.injected == [True] and probe.calls == []
