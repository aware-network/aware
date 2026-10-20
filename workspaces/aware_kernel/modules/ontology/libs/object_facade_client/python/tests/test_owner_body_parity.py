"""Portable owning bodies retain their wire laws without host dependencies."""

import dataclasses
import hashlib
import json
import subprocess
from operator import itemgetter
from pathlib import Path
from types import CellType, CodeType, FunctionType, ModuleType
from typing import Any, cast

import pytest
from aware_ontology_object_facade_client import (
    ActionArgument,
    FrozenJson,
    OntologyRuntimeActionArgumentValue,
    OntologyRuntimeActionInstanceRefTarget,
    OntologyRuntimeActionOperationLocalResultTarget,
    OntologyRuntimeActionSchemaFieldsTarget,
    RuntimeValue,
    ValueKind,
)
from aware_ontology_object_facade_client import owner_values as owner


def _scan_cells(function):
    return dict(zip(function.__code__.co_freevars,
                    (cell.cell_contents for cell in function.__closure__ or ()), strict=True))


def _legacy_scan(current, module, line):
    """Original comparator over the *same* retained expectations; never installed.

    No bootstrap recapture, runtime alias replacement or cached admission. Both
    checkers freshly inspect the genuine live graph; only comparator code differs.
    """
    root = Path(__file__).resolve().parents[8]
    # The comparator is an explicitly historical authored source, not the
    # current candidate's executable coordinate (which may be privately staged).
    # Never ask the historical commit for a newly generated artifact path.
    member = "owner_values.py" if module is owner else "topology_values.py"
    relative = "workspaces/aware_kernel/modules/ontology/libs/object_facade_client/python/aware_ontology_object_facade_client/" + member
    body = subprocess.check_output([
        "git", "show", f"2bebf3d433b1467de0c28c1beab12d45e16aa253:{relative}",
    ], cwd=root)
    def find(code):
        if code.co_name == "check" and code.co_firstlineno == line:
            return code
        for value in code.co_consts:
            if type(value) is CodeType:
                match = find(value)
                if match is not None:
                    return match
        return None
    code = find(compile(body, str(root / relative), "exec", dont_inherit=True))
    assert code is not None
    bindings = _scan_cells(current)
    # The batched successor no longer needs these per-container comparison
    # ports in its runtime closure. The original oracle still uses the exact
    # compiled builtins, never substituted graph data or a fresh capture.
    bindings.setdefault("dict_items", dict.items)
    bindings.setdefault("dict_type", dict)
    bindings.setdefault("first_item", itemgetter(0))
    bindings.setdefault("second_item", itemgetter(1))
    bindings.setdefault("class_get", type.__getattribute__)
    if module is owner:
        bindings.update(
            primitive_bindings=bindings["owner_plan"][0][0],
            aliases=bindings["owner_plan"][0][1],
            builtin_bindings=bindings["builtin_plan"][0],
            checked_namespaces=tuple(row[:3] for row in bindings["namespace_plans"]),
            class_members=tuple(row[:3] for row in bindings["class_plans"]),
            member_namespaces=tuple(row[:3] for row in bindings["member_plans"]),
            containers=tuple(row[:2] for row in bindings["container_plans"]),
            dictionary_contains=dict.__contains__, pair_items=zip, any_item=any,
            attempt_guard_cell=owner._attempt_guard_cell,
        )
    else:
        expected_cells = {id(cell): expected for cell, expected in bindings["cell_plan"][0]}
        checked = _scan_cells(module._call)["checked"]
        checked_cells = dict(zip(checked.__code__.co_freevars, checked.__closure__, strict=True))
        bindings.update(
            builtin_rows=bindings["builtin_plan"][0],
            module_rows=tuple(row[:3] for row in bindings["module_plans"]),
            class_rows=tuple(row[:4] for row in bindings["class_plans"]),
            containers=tuple(row[:2] for row in bindings["container_plans"]),
            lower_rows=tuple(row[:2] for row in bindings["lower_plans"]),
            native_zip=zip,
            dict_get=dict.get, native_any=any,
            function_rows=bindings["function_plan"][0],
            cell_rows=tuple((cell, expected_cells.get(id(cell)))
                            for row in bindings["function_plan"][0]
                            for cell in row[0].__closure__ or ()),
            own_guard_cell=checked_cells["guard"], own_code_cell=checked_cells["guard_code"],
        )
    return FunctionType(code, current.__globals__, "original_scan_oracle",
                        closure=tuple(CellType(bindings[name]) for name in code.co_freevars))


SCALARS = [
    (ValueKind.STRING, "é"),
    (ValueKind.INTEGER, -7),
    (ValueKind.BOOLEAN, False),
    (ValueKind.DECIMAL, "1.50"),
    (ValueKind.DATETIME, "2026-10-02T00:00:00Z"),
    (ValueKind.REFERENCE, "ref:opaque"),
]
DIGEST = "sha256:" + "a" * 64


@pytest.mark.parametrize("kind,scalar", SCALARS)
@pytest.mark.parametrize("shape", ["scalar", "empty", "repeated"])
def test_all_scalar_kinds_preserve_tags_and_repeated_scalar_representation(kind, scalar, shape):
    raw = scalar if shape == "scalar" else [] if shape == "empty" else [scalar, scalar]
    value = RuntimeValue.of(kind, raw)
    expected = {"value_kind": kind.value, "value": raw}
    assert value.to_wire() == expected
    argument = ActionArgument.runtime("parameter:1", value)
    wire = {"parameter_ref": "parameter:1", "value": {"tag": "runtime_value", "runtime_value": expected}}
    assert argument.to_wire() == wire
    assert ActionArgument.from_wire(wire, "argument") == argument
    assert owner.canonical_json(wire) == json.dumps(wire, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(value, "value_kind", ValueKind.JSON)


def test_literal_json_body_and_digest_domain_are_unchanged():
    raw = {"z": [None, True, 1], "a": {"é": "δ"}}
    frozen = FrozenJson.from_value(raw)
    assert frozen.canonical.encode() == b'{"a":{"\xc3\xa9":"\xce\xb4"},"z":[null,true,1]}'
    assert frozen.to_wire() == raw
    assert RuntimeValue.of(ValueKind.JSON, raw).to_wire() == {"value_kind": "json", "value": raw}
    # Independent literal preimage: domain + LF, canonical UTF-8, no terminal LF.
    preimage = b'aware.test.owner.v1\n{"a":{"\xc3\xa9":"\xce\xb4"},"z":[null,true,1]}'
    assert owner.digest_payload("aware.test.owner.v1", raw) == "sha256:" + hashlib.sha256(preimage).hexdigest()
    assert owner.digest_payload("aware.test.owner.v2", raw) != owner.digest_payload("aware.test.owner.v1", raw)


@pytest.mark.parametrize("target,wire", [
    (OntologyRuntimeActionSchemaFieldsTarget.create(
        type_ref="T", identity_field_refs=("T.b", "T.a"),
        identity_contract_digest=DIGEST, normalized_semantic_key={"T.a": "x", "T.b": 1}),
     {"tag": "schema_fields", "type_ref": "T", "identity_field_refs": ["T.a", "T.b"],
      "identity_contract_digest": DIGEST, "normalized_semantic_key": {"T.a": "x", "T.b": 1}}),
    (OntologyRuntimeActionInstanceRefTarget("T", "provider", "generation", "o:1"),
     {"tag": "instance_ref", "type_ref": "T", "provider_key": "provider",
      "provider_generation": "generation", "instance_ref": "o:1"}),
    (OntologyRuntimeActionOperationLocalResultTarget("T", "operation", DIGEST, "result", 0),
     {"tag": "operation_local_result", "type_ref": "T", "operation_ref": "operation",
      "producer_action_digest": DIGEST, "result_symbol": "result", "ordinal": 0}),
])
def test_three_target_forms_preserve_complete_wire_and_argument_order(target, wire):
    assert target.to_wire() == wire
    value = OntologyRuntimeActionArgumentValue.target(target)
    assert value.tag == "object_target"
    argument = ActionArgument.target("second", target)
    expected = {"parameter_ref": "second", "value": {"tag": "object_target", "object_target": wire}}
    assert argument.to_wire() == expected
    assert ActionArgument.from_wire(expected, "argument") == argument
    first = ActionArgument.runtime("first", RuntimeValue.of(ValueKind.INTEGER, 2))
    assert [item["parameter_ref"] for item in [first.to_wire(), argument.to_wire()]] == ["first", "second"]


@pytest.mark.parametrize("kind,raw", [
    (ValueKind.INTEGER, True), (ValueKind.INTEGER, [1, False]),
    (ValueKind.STRING, ["x", 2]), (ValueKind.STRING, [["x"]]),
    (ValueKind.BOOLEAN, [True, 1]), (ValueKind.DECIMAL, 1),
    (ValueKind.DATETIME, None), (ValueKind.REFERENCE, [None]),
    (ValueKind.JSON, 1.2),
])
def test_invalid_tagged_content_rejects_without_coercion(kind, raw):
    with pytest.raises((TypeError, ValueError)):
        RuntimeValue.of(kind, raw)


@pytest.mark.parametrize("canonical", [
    '{"a":1,"a":2}', '{ "a":1}', '{"z":1,"a":2}',
    '1.5', 'NaN', 'Infinity', '"\\u00e9"',
])
def test_frozen_json_refuses_duplicates_noncanonical_and_noninteger_numbers(canonical):
    with pytest.raises((TypeError, ValueError)):
        FrozenJson(canonical)


@pytest.mark.parametrize("field", ["extra", "missing", "tag", "parameter", "bool_ordinal"])
def test_argument_and_target_wire_remain_strict(field):
    wire: Any = ActionArgument.target("p", OntologyRuntimeActionOperationLocalResultTarget(
        "T", "operation", DIGEST, "result", 0)).to_wire()
    if field == "extra":
        wire["extra"] = None
    elif field == "missing":
        del wire["value"]
    elif field == "tag":
        wire["value"]["tag"] = "other"
    elif field == "parameter":
        wire["parameter_ref"] = " leading"
    else:
        wire["value"]["object_target"]["ordinal"] = True
    with pytest.raises((TypeError, ValueError)):
        ActionArgument.from_wire(wire, "argument")


@pytest.mark.parametrize("entrance", ["normalize", "nested_list", "nested_dict", "kind", "argument_value", "argument_wire", "target", "path", "field", "digest"])
def test_native_admission_never_calls_foreign_metaclass_or_value_behavior(entrance):
    calls = []

    class ForeignMeta(type):
        def __eq__(cls, other):
            calls.append("class_eq")
            return False

    class Foreign(metaclass=ForeignMeta):
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign attribute")

        def __str__(self):
            calls.append("str")
            return "foreign"

    value = cast(Any, Foreign())
    with pytest.raises((TypeError, ValueError)):
        if entrance == "normalize":
            owner.normalize_json(value)
        elif entrance == "nested_list":
            RuntimeValue.of(ValueKind.JSON, [value])
        elif entrance == "nested_dict":
            FrozenJson.from_value({"nested": {"bad": value}})
        elif entrance == "kind":
            RuntimeValue(value, FrozenJson("1"))
        elif entrance == "argument_value":
            OntologyRuntimeActionArgumentValue.runtime(value)
        elif entrance == "argument_wire":
            ActionArgument.from_wire({"parameter_ref": "p", "value": value}, "argument")
        elif entrance == "target":
            OntologyRuntimeActionArgumentValue.target(value)
        elif entrance == "path":
            owner.normalize_json([], path=value)
        elif entrance == "field":
            ActionArgument.from_wire({}, value)
        else:
            owner.digest_payload(value, {})
    assert calls == []


@pytest.mark.parametrize("base", [str, int, list, dict])
def test_nested_native_subclasses_reject_without_callbacks(base):
    calls = []

    class Subclass(base):
        def __iter__(self):
            calls.append("iter")
            raise AssertionError("foreign iteration")

        def encode(self, *args):
            calls.append("encode")
            raise AssertionError("foreign encoding")

    with pytest.raises((TypeError, ValueError)):
        FrozenJson.from_value({"nested": [Subclass()]})
    assert calls == []


@pytest.mark.parametrize("entrance", ["frozen", "runtime", "schema", "instance", "result", "argument_value", "argument"])
def test_forged_exact_record_fields_refuse_before_foreign_attribute_dispatch(entrance):
    calls = []

    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign field")

    bad = Foreign()
    if entrance == "frozen":
        item = FrozenJson("1"); field = "canonical"
    elif entrance == "runtime":
        item = RuntimeValue.of(ValueKind.INTEGER, 1); field = "value_kind"
    elif entrance == "schema":
        item = OntologyRuntimeActionSchemaFieldsTarget.create(
            type_ref="T", identity_field_refs=("T.id",), identity_contract_digest=DIGEST,
            normalized_semantic_key={"T.id": "x"}); field = "normalized_semantic_key"
    elif entrance == "instance":
        item = OntologyRuntimeActionInstanceRefTarget("T", "p", "g", "o:1"); field = "instance_ref"
    elif entrance == "result":
        item = OntologyRuntimeActionOperationLocalResultTarget("T", "op", DIGEST, "r", 0); field = "ordinal"
    elif entrance == "argument_value":
        item = OntologyRuntimeActionArgumentValue.runtime(RuntimeValue.of(ValueKind.INTEGER, 1)); field = "runtime_value"
    else:
        item = ActionArgument.runtime("p", RuntimeValue.of(ValueKind.INTEGER, 1)); field = "value"
    object.__setattr__(item, field, bad)
    with pytest.raises((TypeError, ValueError)):
        item.to_wire()
    assert calls == []


def test_portable_factories_do_not_dispatch_subclass_constructors():
    calls = []

    class ForeignFrozen(FrozenJson):
        def __init__(self, *args):
            calls.append("init")

    class ForeignRuntime(RuntimeValue):
        def __init__(self, *args):
            calls.append("init")

    for invoke in (
        lambda: ForeignFrozen.from_value(1),
        lambda: ForeignRuntime.of(ValueKind.INTEGER, 1),
    ):
        with pytest.raises(TypeError):
            invoke()
    assert calls == []


SHAPES = [
    owner.ValueShape.scalar(kind) for kind in owner.ScalarKind
] + [
    owner.ValueShape.named("T"),
    owner.ValueShape.list_of(owner.ValueShape.scalar(owner.ScalarKind.STRING)),
    owner.ValueShape.map_of(owner.ValueShape.named("T")),
    owner.ValueShape.union_of(owner.ValueShape.named("T"), owner.ValueShape.scalar(owner.ScalarKind.INTEGER)),
]


@pytest.mark.parametrize("shape", SHAPES)
def test_abi_shape_wire_is_the_original_meta_wire(shape):
    field = owner.OntologyObjectFieldBinding("T.count", "count", shape, True, False)
    assert field.to_wire() == {"field_ref": "T.count", "attribute_name": "count",
                              "shape": shape.to_wire(), "required": True, "nullable": False}
    from aware_meta_type_schema import ScalarKind, ShapeKind, ValueShape
    assert owner.ValueShape is ValueShape and owner.ShapeKind is ShapeKind and owner.ScalarKind is ScalarKind


def _abi_class():
    shape = owner.ValueShape.scalar(owner.ScalarKind.INTEGER)
    field = owner.OntologyObjectFieldBinding("T.count", "count", shape, True, False)
    first = owner.OntologyObjectActionParameterBinding("T.increase.number", 0, shape, True, False, cast(Any, "value"))
    second = owner.OntologyObjectActionParameterBinding("T.increase.extra", 1, shape, False, True, cast(Any, "instance_ref"))
    path = owner.OntologyObjectRelationshipConstructorPath(("T.children",), "T.create")
    action = owner.OntologyObjectActionBinding("T.increase", "increase", (second, first), relationship_constructor_paths=(path,))
    relationship = owner.OntologyObjectRelationshipBinding("T.children", "children", "T", "T", cast(Any, "outgoing"), cast(Any, "many"), cast(Any, "source_to_target"), cast(Any, "resident_target"))
    return owner.OntologyObjectClassBinding.create(type_ref="T", class_name="Counter", fields=[field], actions=[action], relationships=[relationship])


def test_class_member_order_digest_and_declared_lookup_laws():
    binding = _abi_class()
    wire = binding.to_wire()
    payload = {name: value for name, value in wire.items() if name != "binding_digest"}
    preimage = b"aware.ontology.object-abi.v1.class\n" + json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert wire["binding_digest"] == "sha256:" + hashlib.sha256(preimage).hexdigest()
    assert binding.field("count") is binding.fields[0]
    action = binding.action("increase")
    assert action is not None and action is binding.actions[0]
    assert [item.position for item in action.parameters] == [0, 1]
    assert action.relationship_constructor_action_ref("create") == "T.create"
    assert binding.relationship("children", owner.OntologyObjectRelationshipDirection.OUTGOING) is binding.relationships[0]
    assert binding.action("missing") is None
    assert json.loads(owner.canonical_json(wire)) == wire


@pytest.mark.parametrize("position", ["field_ref", "shape", "flag", "enum", "parameters", "nested_parameter", "constructor_refs", "class_fields", "lookup", "shape_variants", "shape_ref"])
def test_abi_foreign_native_inputs_reject_without_behavior(position):
    calls = []
    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign attribute")
        def __iter__(self):
            calls.append("iter")
            raise AssertionError("foreign iteration")
        def __eq__(self, other):
            calls.append("eq")
            raise AssertionError("foreign equality")
        def __hash__(self):
            calls.append("hash")
            raise AssertionError("foreign hash")
        def __str__(self):
            calls.append("str")
            raise AssertionError("foreign str")
    foreign = cast(Any, Foreign())
    shape = owner.ValueShape.named("T")
    with pytest.raises((TypeError, ValueError)):
        if position == "field_ref":
            owner.OntologyObjectFieldBinding(foreign, "count", shape, True, False)
        elif position == "shape":
            owner.OntologyObjectFieldBinding("T.count", "count", foreign, True, False)
        elif position == "flag":
            owner.OntologyObjectFieldBinding("T.count", "count", shape, foreign, False)
        elif position == "enum":
            owner.OntologyObjectActionParameterBinding("T.act.x", 0, shape, True, False, foreign)
        elif position == "parameters":
            owner.OntologyObjectActionBinding("T.act", "act", foreign)
        elif position == "nested_parameter":
            owner.OntologyObjectActionBinding("T.act", "act", (foreign,))
        elif position == "constructor_refs":
            owner.OntologyObjectRelationshipConstructorPath((foreign,), "T.create")
        elif position == "class_fields":
            owner.OntologyObjectClassBinding.create(type_ref="T", class_name="T", fields=[foreign], actions=(), relationships=())
        elif position == "lookup":
            _abi_class().action(foreign)
        else:
            object.__setattr__(shape, "variants" if position == "shape_variants" else "type_ref", (foreign,) if position == "shape_variants" else foreign)
            owner.OntologyObjectFieldBinding("T.count", "count", shape, True, False)
    assert calls == []


def test_abi_metaclass_equality_and_forged_nested_fields_never_dispatch():
    calls = []
    class ForeignMeta(type):
        def __eq__(cls, other):
            calls.append("metaclass equality")
            raise AssertionError("foreign metaclass")
    class Foreign(metaclass=ForeignMeta):
        pass
    with pytest.raises(TypeError):
        owner.OntologyObjectActionBinding("T.act", "act", (cast(Any, Foreign()),))
    field = owner.OntologyObjectFieldBinding("T.count", "count", SHAPES[0], True, False)
    object.__setattr__(field, "required", Foreign())
    with pytest.raises(TypeError):
        field.to_wire()
    with pytest.raises(TypeError):
        owner.OntologyObjectClassBinding.create(type_ref="T", class_name="T", fields=(field,), actions=(), relationships=())
    assert calls == []


def test_cyclic_shape_refuses_without_alternate_shape_semantics():
    shape = owner.ValueShape.list_of(owner.ValueShape.named("T"))
    object.__setattr__(shape, "element", shape)
    with pytest.raises(ValueError, match="cyclic"):
        owner.OntologyObjectFieldBinding("T.count", "count", shape, True, False)


@pytest.mark.parametrize("method", ["__init__", "to_wire", "__post_init__"])
@pytest.mark.parametrize("depth", [0, 1, 2])
def test_meta_constructor_and_wire_checks_follow_nested_token_returns(monkeypatch, method, depth):
    shape = owner.ValueShape.named("T")
    for _ in range(depth):
        shape = owner.ValueShape.list_of(shape)
    original = owner._strict_token
    injected = []
    calls = []
    def foreign(*args, **kwargs):
        calls.append(method)
        raise AssertionError("foreign Meta behavior")
    def token(value, field):
        result = original(value, field)
        if field == "type_ref" and not injected:
            monkeypatch.setattr(owner.ValueShape, method, foreign)
            injected.append(True)
        return result
    monkeypatch.setattr(owner, "_strict_token", token)
    with pytest.raises(TypeError, match="shape operation identity"):
        owner.OntologyObjectFieldBinding("T.count", "count", shape, True, False)
    assert injected == [True] and calls == []



def test_abi_class_projection_matches_frozen_host_canonical_bytes():
    # Captured independently from the frozen pre-extraction host, including
    # class digests. Covers twelve shapes, four direction/traversal pairs and
    # every cardinality without installing either runtime.
    shapes = [owner.ValueShape.scalar(kind) for kind in owner.ScalarKind] + [
        owner.ValueShape.named("T"), owner.ValueShape.list_of(owner.ValueShape.named("T")),
        owner.ValueShape.map_of(owner.ValueShape.named("T")),
        owner.ValueShape.union_of(owner.ValueShape.named("T"), owner.ValueShape.scalar(owner.ScalarKind.INTEGER)),
    ]
    results = []
    for shape in shapes:
        for direction, traversal in (("outgoing", "source_to_target"), ("incoming", "target_to_source"), ("outgoing", "bidirectional"), ("incoming", "bidirectional")):
            for cardinality in ("one", "optional_one", "many"):
                fields = (owner.OntologyObjectFieldBinding("T.z", "z", shape, True, False), owner.OntologyObjectFieldBinding("T.a", "a", shape, False, True))
                parameters = (owner.OntologyObjectActionParameterBinding("T.inc.z", 1, shape, False, True, owner.ActionValueMode.INSTANCE_REF), owner.OntologyObjectActionParameterBinding("T.inc.a", 0, shape, True, False, owner.ActionValueMode.VALUE))
                path = owner.OntologyObjectRelationshipConstructorPath(("T.rel",), "T.new")
                action = owner.OntologyObjectActionBinding("T.inc", "inc", parameters, relationship_constructor_paths=(path,))
                relationship = owner.OntologyObjectRelationshipBinding("T.rel", "rel", "T", "T", owner.OntologyObjectRelationshipDirection(direction), owner.Cardinality(cardinality), owner.TraversalPolicy(traversal), None)
                value = owner.OntologyObjectClassBinding.create(type_ref="T", class_name="T", fields=fields, actions=(action,), relationships=(relationship,))
                results.append(value.to_wire())
    projection = owner.canonical_json(results).encode() + b"\n"
    assert len(results) == 144
    assert len(projection) == 208202
    assert hashlib.sha256(projection).hexdigest() == "574dd4cecacc63f5635dd4967436e01d20fd4f59acccc2da888b57ecb7398ce7"



@pytest.mark.parametrize("method", ["__init__", "__post_init__"])
def test_abi_factory_checks_constructor_after_digest_return(monkeypatch, method):
    original = owner.digest_payload
    injected = []
    calls = []
    def foreign(*args, **kwargs):
        calls.append(method)
        raise AssertionError("foreign ABI constructor")
    def digest(domain, value):
        result = original(domain, value)
        if domain == owner.OBJECT_ABI_CONTRACT + ".class":
            monkeypatch.setattr(owner.OntologyObjectClassBinding, method, foreign)
            injected.append(True)
        return result
    monkeypatch.setattr(owner, "digest_payload", digest)
    _p1_seal_observed_owner_dependencies(monkeypatch)
    with pytest.raises(TypeError, match="shape operation identity"):
        owner.OntologyObjectClassBinding.create(type_ref="T", class_name="T", fields=(), actions=(), relationships=())
    assert injected == [True] and calls == []



@pytest.mark.parametrize("boundary", ["lookup_token", "class_digest"])
def test_abi_record_access_after_helper_return_stays_protected(monkeypatch, boundary):
    binding = _abi_class()
    injected = []
    calls = []
    def foreign(self, name):
        calls.append(name)
        raise AssertionError("foreign record getter")
    if boundary == "lookup_token":
        original = owner._strict_token
        def token(value, field):
            result = original(value, field)
            if field == "member_name":
                monkeypatch.setattr(owner.OntologyObjectClassBinding, "__getattribute__", foreign)
                injected.append(True)
            return result
        monkeypatch.setattr(owner, "_strict_token", token)
        with pytest.raises(TypeError, match="shape operation identity"):
            binding.field("count")
    else:
        original_digest = owner.digest_payload
        def digest(domain, payload):
            result = original_digest(domain, payload)
            if domain == owner.OBJECT_ABI_CONTRACT + ".class":
                monkeypatch.setattr(owner.OntologyObjectClassBinding, "__getattribute__", foreign)
                injected.append(True)
            return result
        monkeypatch.setattr(owner, "digest_payload", digest)
        _p1_seal_observed_owner_dependencies(monkeypatch)
        with pytest.raises(TypeError, match="shape operation identity"):
            owner.OntologyObjectClassBinding.__post_init__(binding)
    assert injected == [True] and calls == []



def test_abi_token_return_rejects_an_absent_primitive_shadow(monkeypatch):
    binding = _abi_class()
    original = owner._strict_token
    calls = []
    injected = []
    def foreign(*args, **kwargs):
        calls.append("type")
        raise AssertionError("foreign primitive")
    def token(value, field):
        result = original(value, field)
        if field == "member_name":
            monkeypatch.setattr(owner, "type", foreign, raising=False)
            injected.append(True)
        return result
    monkeypatch.setattr(owner, "_strict_token", token)
    with pytest.raises(TypeError, match="shape operation identity"):
        binding.field("count")
    assert injected == [True] and calls == []


def _a3_parameter():
    return cast(Any, owner.SchemaActionParameterDefinition)("T.fn.p", 0, owner.ValueShape.scalar(owner.ScalarKind.INTEGER))


def _a3_action():
    return cast(Any, owner.SchemaActionDefinition)("T.fn", "T", (_a3_parameter(),))


@pytest.mark.parametrize("case", [
    "field_ref", "field_value", "object_ref", "object_type", "fields", "nested_field",
    "relationship_ref", "relationship_source", "coverage_grade", "coverage_refs", "nested_ref",
    "parameter_ref", "position", "shape", "required", "nullable", "parameter_mode",
    "action_ref", "target_type", "parameters", "nested_parameter", "result_shape", "result_mode",
    "scope", "mutation_refs", "nested_mutation_ref",
])
@pytest.mark.parametrize("payload_kind", ["object", "str_subclass"])
def test_a3_constructor_native_admission_rejects_without_foreign_behavior(case, payload_kind):
    calls = []

    class ForeignMeta(type):
        def __eq__(cls, other):
            calls.append("metaclass equality")
            raise AssertionError("foreign type equality")

    class Foreign(metaclass=ForeignMeta):
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign attribute")

        def __iter__(self):
            calls.append("iteration")
            raise AssertionError("foreign iteration")

        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("foreign equality")

    class ForeignString(str):
        def strip(self, *args):
            calls.append("strip")
            raise AssertionError("foreign string behavior")

    foreign = Foreign() if payload_kind == "object" else ForeignString("x")
    value = owner.RuntimeValue.of(owner.ValueKind.INTEGER, 1)
    field = cast(Any, owner.FieldValue)("T.a", value)
    parameter = _a3_parameter()
    factories = {
        "field_ref": lambda: cast(Any, owner.FieldValue)(foreign, value),
        "field_value": lambda: cast(Any, owner.FieldValue)("T.a", foreign),
        "object_ref": lambda: cast(Any, owner.ObjectInstance)(foreign, "T", (field,)),
        "object_type": lambda: cast(Any, owner.ObjectInstance)("o:1", foreign, (field,)),
        "fields": lambda: cast(Any, owner.ObjectInstance)("o:1", "T", foreign),
        "nested_field": lambda: cast(Any, owner.ObjectInstance)("o:1", "T", (foreign,)),
        "relationship_ref": lambda: cast(Any, owner.RelationshipInstance)("r:1", foreign, "o:1", "o:2"),
        "relationship_source": lambda: cast(Any, owner.RelationshipInstance)("r:1", "T.rel", foreign, "o:2"),
        "coverage_grade": lambda: cast(Any, owner.ProjectionCoverage)(foreign),
        "coverage_refs": lambda: cast(Any, owner.ProjectionCoverage)("partial", foreign),
        "nested_ref": lambda: cast(Any, owner.ProjectionCoverage)("partial", (foreign,)),
        "parameter_ref": lambda: cast(Any, owner.SchemaActionParameterDefinition)(foreign, 0, parameter.shape),
        "position": lambda: cast(Any, owner.SchemaActionParameterDefinition)("p", foreign, parameter.shape),
        "shape": lambda: cast(Any, owner.SchemaActionParameterDefinition)("p", 0, foreign),
        "required": lambda: cast(Any, owner.SchemaActionParameterDefinition)("p", 0, parameter.shape, foreign),
        "nullable": lambda: cast(Any, owner.SchemaActionParameterDefinition)("p", 0, parameter.shape, nullable=foreign),
        "parameter_mode": lambda: cast(Any, owner.SchemaActionParameterDefinition)("p", 0, parameter.shape, value_mode=foreign),
        "action_ref": lambda: cast(Any, owner.SchemaActionDefinition)(foreign, "T"),
        "target_type": lambda: cast(Any, owner.SchemaActionDefinition)("T.fn", foreign),
        "parameters": lambda: cast(Any, owner.SchemaActionDefinition)("T.fn", "T", foreign),
        "nested_parameter": lambda: cast(Any, owner.SchemaActionDefinition)("T.fn", "T", (foreign,)),
        "result_shape": lambda: cast(Any, owner.SchemaActionDefinition)("T.fn", "T", result_shape=foreign),
        "result_mode": lambda: cast(Any, owner.SchemaActionDefinition)("T.fn", "T", result_value_mode=foreign),
        "scope": lambda: cast(Any, owner.SchemaActionDefinition)("T.fn", "T", mutation_scope=foreign),
        "mutation_refs": lambda: cast(Any, owner.SchemaActionDefinition)("T.fn", "T", mutation_scope="declared_types", mutation_type_refs=foreign),
        "nested_mutation_ref": lambda: cast(Any, owner.SchemaActionDefinition)("T.fn", "T", mutation_scope="declared_types", mutation_type_refs=(foreign,)),
    }
    with pytest.raises((TypeError, ValueError)):
        factories[case]()
    assert calls == []


@pytest.mark.parametrize("kind", [
    "FieldValue", "ObjectInstance", "RelationshipInstance", "ProjectionCoverage",
    "SchemaActionParameterDefinition", "SchemaActionDefinition",
])
def test_a3_unbound_serialization_refuses_foreign_receivers_before_attributes(kind):
    calls = []

    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign receiver")

    with pytest.raises(TypeError):
        getattr(owner, kind).to_wire(Foreign())
    assert calls == []


@pytest.mark.parametrize("case", ["field_value", "object_fields", "relationship_target", "coverage_refs", "parameter_shape", "action_parameters"])
def test_a3_serialization_rechecks_tampered_slot_data_without_foreign_behavior(case):
    calls = []

    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign nested record")

        def __iter__(self):
            calls.append("iterate")
            raise AssertionError("foreign nested iteration")

    value = owner.RuntimeValue.of(owner.ValueKind.INTEGER, 1)
    choices = {
        "field_value": (cast(Any, owner.FieldValue)("T.a", value), "value", Foreign()),
        "object_fields": (cast(Any, owner.ObjectInstance)("o:1", "T", ()), "fields", (Foreign(),)),
        "relationship_target": (cast(Any, owner.RelationshipInstance)("r:1", "T.rel", "o:1", "o:2"), "target_instance_ref", Foreign()),
        "coverage_refs": (cast(Any, owner.ProjectionCoverage)("complete"), "missing_refs", (Foreign(),)),
        "parameter_shape": (_a3_parameter(), "shape", Foreign()),
        "action_parameters": (_a3_action(), "parameters", (Foreign(),)),
    }
    record, slot, foreign = choices[case]
    object.__setattr__(record, slot, foreign)
    with pytest.raises(TypeError):
        record.to_wire()
    assert calls == []


@pytest.mark.parametrize("case", ["bool_position", "negative_position", "complete_missing", "partial_empty", "duplicate_missing", "scope_empty", "unexpected_scope_refs"])
def test_a3_native_invalid_data_and_existing_semantic_rules_refuse(case):
    shape = owner.ValueShape.scalar(owner.ScalarKind.INTEGER)
    factories = {
        "bool_position": lambda: cast(Any, owner.SchemaActionParameterDefinition)("p", True, shape),
        "negative_position": lambda: cast(Any, owner.SchemaActionParameterDefinition)("p", -1, shape),
        "complete_missing": lambda: cast(Any, owner.ProjectionCoverage)("complete", ("x",)),
        "partial_empty": lambda: cast(Any, owner.ProjectionCoverage)("partial"),
        "duplicate_missing": lambda: cast(Any, owner.ProjectionCoverage)("partial", ("x", "x")),
        "scope_empty": lambda: cast(Any, owner.SchemaActionDefinition)("T.fn", "T", mutation_scope="declared_types"),
        "unexpected_scope_refs": lambda: cast(Any, owner.SchemaActionDefinition)("T.fn", "T", mutation_type_refs=("T",)),
    }
    with pytest.raises(ValueError):
        factories[case]()


def test_a3_literal_record_wires_keep_order_defaults_and_do_not_invent_joins():
    value = owner.RuntimeValue.of(owner.ValueKind.DECIMAL, "1.50")
    a, z = cast(Any, owner.FieldValue)("T.a", value), cast(Any, owner.FieldValue)("T.z", value)
    instance = cast(Any, owner.ObjectInstance)("o:1", "T", [z, a, a])
    assert instance.to_wire() == {"instance_ref": "o:1", "type_ref": "T", "fields": [a.to_wire(), a.to_wire(), z.to_wire()]}
    assert cast(Any, owner.ProjectionCoverage)("partial", ["z", "a"]).to_wire() == {"grade": "partial", "missing_refs": ["a", "z"]}
    shape = owner.ValueShape.named("Other")
    p = cast(Any, owner.SchemaActionParameterDefinition)("T.fn.z", 1, shape)
    q = cast(Any, owner.SchemaActionParameterDefinition)("T.fn.a", 1, p.shape)
    action = cast(Any, owner.SchemaActionDefinition)("T.fn", "T", [p, q], mutation_scope="declared_types", mutation_type_refs=["Z", "A"])
    wire = action.to_wire()
    assert wire["parameters"] == [q.to_wire(), p.to_wire()]
    assert wire["result_shape"] is None and wire["result_value_mode"] == "value"
    assert wire["mutation_type_refs"] == ["A", "Z"]
    assert p.shape is not q.shape and p.shape == q.shape
    assert p.shape is not shape
    assert list(owner.MutationScope) == [owner.MutationScope.TARGET, owner.MutationScope.CONTAINED, owner.MutationScope.DECLARED_TYPES]
    assert list(owner.CoverageGrade) == [owner.CoverageGrade.COMPLETE, owner.CoverageGrade.PARTIAL]


def test_a3_clean_parent_379_record_vector_projection_is_exact():
    values = []
    scalars = [(owner.ValueKind.STRING, "é"), (owner.ValueKind.INTEGER, -3), (owner.ValueKind.BOOLEAN, False),
               (owner.ValueKind.DECIMAL, "1.50"), (owner.ValueKind.DATETIME, "2026-10-03T00:00:00Z"),
               (owner.ValueKind.REFERENCE, "opaque:1")]
    for kind, raw in scalars:
        for payload in (raw, [], [raw, raw]):
            field = cast(Any, owner.FieldValue)("T.a", owner.RuntimeValue.of(kind, payload))
            values.append(field.to_wire())
            obj = cast(Any, owner.ObjectInstance)("o:1", "T", [cast(Any, owner.FieldValue)("T.z", owner.RuntimeValue.of(kind, payload)), field, field])
            values.append(obj.to_wire())
    for raw in (None, {"b": True, "a": [1, "δ", None]}, ["é", False]):
        values.append(cast(Any, owner.FieldValue)("T.json", owner.RuntimeValue.of(owner.ValueKind.JSON, raw)).to_wire())
    for source, target in (("o:1", "o:2"), ("o:2", "o:1")):
        values.append(cast(Any, owner.RelationshipInstance)("r:1", "T.rel", source, target).to_wire())
    values.extend([cast(Any, owner.ProjectionCoverage)("complete").to_wire(), cast(Any, owner.ProjectionCoverage)("partial", ["z", "a"]).to_wire()])
    shapes = [owner.ValueShape.scalar(kind) for kind in owner.ScalarKind] + [
        owner.ValueShape.named("T"), owner.ValueShape.list_of(owner.ValueShape.named("T")),
        owner.ValueShape.map_of(owner.ValueShape.named("T")),
        owner.ValueShape.union_of(owner.ValueShape.named("T"), owner.ValueShape.scalar(owner.ScalarKind.INTEGER)),
    ]
    for shape in shapes:
        for mode in owner.ActionValueMode:
            for required, nullable in ((True, False), (False, True)):
                a = cast(Any, owner.SchemaActionParameterDefinition)("T.fn.z", 1, shape, required, nullable, mode)
                b = cast(Any, owner.SchemaActionParameterDefinition)("T.fn.a", 1, shape, nullable, required, mode)
                values.append(a.to_wire())
                for scope in owner.MutationScope:
                    refs = ("Z", "A") if scope is owner.MutationScope.DECLARED_TYPES else ()
                    for result_shape in (None, shape):
                        values.append(cast(Any, owner.SchemaActionDefinition)("T.fn", "T", [a, b], result_shape, mode, scope, refs).to_wire())
    projection = {"mutation_scope": [x.value for x in owner.MutationScope], "coverage_grade": [x.value for x in owner.CoverageGrade],
                  "values": values, "digest": owner.digest_payload("aware.ontology.a3.parity.v1", values)}
    assert len(values) == 379
    encoded = owner.canonical_json(projection).encode() + b"\n"
    assert len(encoded) == 222005
    assert hashlib.sha256(encoded).hexdigest() == "5a1e430b0650aac360510594dee4c6219ecba8543b27b001ca353afb6936f3a5"


def _a3_seal_observed_record_closure(monkeypatch):
    from types import FunctionType

    classes = (owner.MutationScope, owner.CoverageGrade, owner.FieldValue, owner.ObjectInstance,
               owner.RelationshipInstance, owner.ProjectionCoverage, owner.SchemaActionParameterDefinition,
               owner.SchemaActionDefinition, owner.RuntimeValue, owner.FrozenJson, owner.ValueKind, owner.ActionValueMode)
    helpers = tuple(value for name, value in tuple(vars(owner).items())
                    if type(value) is FunctionType and name != "_record_guard") + owner._record_originals
    # This instruments a trusted data helper before the tested invocation. It is
    # not an API argument, caller verifier or source/installed authority proof.
    monkeypatch.setattr(owner, "_record_guard", owner._protect_shape_dispatch(
        classes, guard_name="_record_guard", helpers=helpers))


@pytest.mark.parametrize("case", ["field_getter", "action_getter", "original_wire", "items_helper", "parameter_post", "scope_member"])
def test_a3_nested_token_return_authenticates_getter_original_helper_and_constructor(monkeypatch, capsys, case):
    from types import SimpleNamespace

    value = owner.RuntimeValue.of(owner.ValueKind.INTEGER, 1)
    records = {
        "field_getter": owner.FieldValue("T.a", value),
        "action_getter": _a3_action(),
        "original_wire": owner.RelationshipInstance("r:1", "T.rel", "o:1", "o:2"),
        "items_helper": owner.ObjectInstance("o:1", "T", ()),
        "parameter_post": _a3_parameter(),
        "scope_member": _a3_action(),
    }
    record = records[case]
    original = owner._strict_token
    probe = SimpleNamespace(injected=[], calls=[])
    trigger = {"field_getter": "field_ref", "action_getter": "action_ref", "original_wire": "instance_ref",
               "items_helper": "instance_ref", "parameter_post": "parameter_ref", "scope_member": "action_ref"}[case]

    def foreign(*args, **kwargs):
        probe.calls.append(case)
        raise AssertionError("foreign nested record dispatch")

    def code_stub(*args, **kwargs):
        print("FOREIGN_RECORD_CODE_EXECUTED")
        raise AssertionError("foreign source-pinned original")

    def token_return(value, field):
        result = original(value, field)
        if field == trigger and not probe.injected:
            if case in ("field_getter", "action_getter"):
                monkeypatch.setattr(type(record), "__getattribute__", foreign, raising=False)
            elif case == "original_wire":
                monkeypatch.setattr(owner._record_originals[1], "__code__", code_stub.__code__)
            elif case == "items_helper":
                monkeypatch.setattr(owner, "_record_items", foreign)
            elif case == "parameter_post":
                monkeypatch.setattr(owner.SchemaActionParameterDefinition, "__post_init__", foreign)
            else:
                monkeypatch.setattr(owner.MutationScope.TARGET, "_value_", foreign)
            probe.injected.append(True)
        return result

    monkeypatch.setattr(owner, "_strict_token", token_return)
    _a3_seal_observed_record_closure(monkeypatch)
    with pytest.raises(TypeError, match="operation identity"):
        record.to_wire()
    assert probe.injected == [True] and probe.calls == []
    assert "FOREIGN_RECORD_CODE_EXECUTED" not in capsys.readouterr().out


# Captured before extraction from the accepted host parent. Complete bodies,
# not implementation-derived expected hashes: seven historical selected records.
P1_PARENT_WIRES = {'OntologyObjectExecutableSelectionAdmission': {'activation_request_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                'admission_digest': 'sha256:a4040034c6e30b24d0a4b561a2ad6a8bdc572a6c4422a71eb1af586d492e9953',
                                                'codec_version': 1,
                                                'current_base_operational_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                'executable_authority_body': {'admission_provider_generation': 'value:provider_generation',
                                                                              'admission_provider_key': 'value:provider_key',
                                                                              'authority_digest': 'sha256:dbe8523df202913623ecc6e54b6cc9d90d0f6596cff09920fa6713bc5f343bb6',
                                                                              'authority_ref': 'value:authority_ref',
                                                                              'base_operational_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                              'capability_catalog_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                              'executable_root_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                              'vm_implementation_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'},
                                                'executable_authority_digest': 'sha256:dbe8523df202913623ecc6e54b6cc9d90d0f6596cff09920fa6713bc5f343bb6',
                                                'execution_admission_request_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                'retained_revision_ref': 'value:retained_revision_ref',
                                                'schema': 'aware.ontology.object-executable-selection-admission.v1',
                                                'selection_disposition': 'selected',
                                                'selection_profile_body': {'application_authority_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                           'branch_ref': 'value:branch_ref',
                                                                           'codec_version': 1,
                                                                           'object_abi_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                           'profile_digest': 'sha256:675e004cd377c52edc27b25e90c7e257790d70eb13137b61bc89badec7511ef3',
                                                                           'schema': 'aware.ontology.object-executable-selection-profile.v1',
                                                                           'schema_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                           'schema_slice_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                           'selection_facts_body': {'actor_rule_body': {'codec_version': 1,
                                                                                                                        'kind': 'any_exact_text',
                                                                                                                        'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                                                                                                        'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                                                                                                        'values': []},
                                                                                                    'authority_ref': 'value:authority_ref',
                                                                                                    'capability_catalog_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                                                    'codec_version': 1,
                                                                                                    'executable_root_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                                                    'facts_digest': 'sha256:5c089a9560dfa64d78213ddbc0098b0162226ad9eb7f9c0aa7e1f2c02214c944',
                                                                                                    'idempotency_rule_body': {'codec_version': 1,
                                                                                                                              'kind': 'any_exact_text',
                                                                                                                              'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                                                                                                              'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                                                                                                              'values': []},
                                                                                                    'operation_rule_body': {'codec_version': 1,
                                                                                                                            'kind': 'any_exact_text',
                                                                                                                            'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                                                                                                            'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                                                                                                            'values': []},
                                                                                                    'projection_rule_body': {'codec_version': 1,
                                                                                                                             'kind': 'any_exact_text',
                                                                                                                             'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                                                                                                             'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                                                                                                             'values': []},
                                                                                                    'provider_generation': 'value:provider_generation',
                                                                                                    'provider_key': 'value:provider_key',
                                                                                                    'schema': 'aware.ontology.object-executable-selection-facts.v1',
                                                                                                    'vm_implementation_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'},
                                                                           'selection_facts_digest': 'sha256:5c089a9560dfa64d78213ddbc0098b0162226ad9eb7f9c0aa7e1f2c02214c944',
                                                                           'topology_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'},
                                                'selection_profile_digest': 'sha256:675e004cd377c52edc27b25e90c7e257790d70eb13137b61bc89badec7511ef3'},
 'OntologyObjectExecutableSelectionFacts': {'actor_rule_body': {'codec_version': 1,
                                                                'kind': 'any_exact_text',
                                                                'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                                                'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                                                'values': []},
                                            'authority_ref': 'value:authority_ref',
                                            'capability_catalog_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                            'codec_version': 1,
                                            'executable_root_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                            'facts_digest': 'sha256:5c089a9560dfa64d78213ddbc0098b0162226ad9eb7f9c0aa7e1f2c02214c944',
                                            'idempotency_rule_body': {'codec_version': 1,
                                                                      'kind': 'any_exact_text',
                                                                      'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                                                      'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                                                      'values': []},
                                            'operation_rule_body': {'codec_version': 1,
                                                                    'kind': 'any_exact_text',
                                                                    'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                                                    'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                                                    'values': []},
                                            'projection_rule_body': {'codec_version': 1,
                                                                     'kind': 'any_exact_text',
                                                                     'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                                                     'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                                                     'values': []},
                                            'provider_generation': 'value:provider_generation',
                                            'provider_key': 'value:provider_key',
                                            'schema': 'aware.ontology.object-executable-selection-facts.v1',
                                            'vm_implementation_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'},
 'OntologyObjectExecutableSelectionProfile': {'application_authority_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                              'branch_ref': 'value:branch_ref',
                                              'codec_version': 1,
                                              'object_abi_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                              'profile_digest': 'sha256:675e004cd377c52edc27b25e90c7e257790d70eb13137b61bc89badec7511ef3',
                                              'schema': 'aware.ontology.object-executable-selection-profile.v1',
                                              'schema_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                              'schema_slice_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                              'selection_facts_body': {'actor_rule_body': {'codec_version': 1,
                                                                                           'kind': 'any_exact_text',
                                                                                           'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                                                                           'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                                                                           'values': []},
                                                                       'authority_ref': 'value:authority_ref',
                                                                       'capability_catalog_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                       'codec_version': 1,
                                                                       'executable_root_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                       'facts_digest': 'sha256:5c089a9560dfa64d78213ddbc0098b0162226ad9eb7f9c0aa7e1f2c02214c944',
                                                                       'idempotency_rule_body': {'codec_version': 1,
                                                                                                 'kind': 'any_exact_text',
                                                                                                 'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                                                                                 'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                                                                                 'values': []},
                                                                       'operation_rule_body': {'codec_version': 1,
                                                                                               'kind': 'any_exact_text',
                                                                                               'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                                                                               'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                                                                               'values': []},
                                                                       'projection_rule_body': {'codec_version': 1,
                                                                                                'kind': 'any_exact_text',
                                                                                                'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                                                                                'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                                                                                'values': []},
                                                                       'provider_generation': 'value:provider_generation',
                                                                       'provider_key': 'value:provider_key',
                                                                       'schema': 'aware.ontology.object-executable-selection-facts.v1',
                                                                       'vm_implementation_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'},
                                              'selection_facts_digest': 'sha256:5c089a9560dfa64d78213ddbc0098b0162226ad9eb7f9c0aa7e1f2c02214c944',
                                              'topology_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'},
 'OntologyObjectExecutableSelectionTextRule': {'codec_version': 1,
                                               'kind': 'any_exact_text',
                                               'rule_digest': 'sha256:2660f329baad3aa44d0662a69c5c3fa4425a5cb253bba7c0a4f743629f415681',
                                               'schema': 'aware.ontology.object-executable-selection-text-rule.v1',
                                               'values': []},
 'OntologyObjectOperationAttempt': {'activation_request_digest': 'sha256:6cd48783d6e3dbca2135721fb643553d26d10921394f1563b11c1668bea0bf86',
                                    'actor_ref': 'value:actor_ref',
                                    'application_authority_body': {'application_ref': 'application:test',
                                                                   'authority_digest': 'sha256:b4b8b6c9c7446effbd933c706a9c07b6bd0763fd1819533fdc7302fc6eb5b3d8',
                                                                   'implementation_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'},
                                    'application_authority_digest': 'sha256:b4b8b6c9c7446effbd933c706a9c07b6bd0763fd1819533fdc7302fc6eb5b3d8',
                                    'attempt_digest': 'sha256:00186e0a0961a228b58e037f9495c16f89ddab9d94ee924991b5f6e8b8c1ece5',
                                    'attempt_ref': 'ontology-object-attempt:sha256:2621f63cb7b391244304015c0cc3d25f62705b137b76b8f6cabb1c7c6466fde0',
                                    'base_operational_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                    'branch_ref': 'value:branch_ref',
                                    'codec_version': 1,
                                    'executable_authority_body': {'admission_provider_generation': 'value:provider_generation',
                                                                  'admission_provider_key': 'value:provider_key',
                                                                  'authority_digest': 'sha256:9481b6ca2fa7d845cd68936f9da431fbcb20a3e1526c1c07ee5980560e052a13',
                                                                  'authority_ref': 'executable:test',
                                                                  'base_operational_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                  'capability_catalog_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                  'executable_root_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                  'vm_implementation_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'},
                                    'executable_authority_digest': 'sha256:9481b6ca2fa7d845cd68936f9da431fbcb20a3e1526c1c07ee5980560e052a13',
                                    'execution_admission_request_digest': 'sha256:0f3725c5b53541f49b0474c4385eb469ae45bef79d11c7e0d4accd0d019c95ae',
                                    'expected_revision_ref': None,
                                    'idempotency_key': 'value:idempotency_key',
                                    'object_abi_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                    'operation_ref': 'value:operation_ref',
                                    'projection_ref': 'value:projection_ref',
                                    'provider_generation': 'value:provider_generation',
                                    'provider_key': 'value:provider_key',
                                    'provider_profile_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                    'recovery_ref': 'ontology-object-recovery:sha256:857c1cfb64f9706a459c30220b0f9696dbd281b8049721cfffb5b16178105271',
                                    'schema': 'aware.ontology.object-operation-attempt.v1',
                                    'schema_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                    'schema_slice_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                    'topology_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'},
 'OntologyObjectOperationAttemptAdmission': {'admission_digest': 'sha256:8f53cff1a2a36b4818a565afa6763a359019fb1df1f3ab42d7133a2a6dc1b73b',
                                             'application_authority_digest': 'sha256:b4b8b6c9c7446effbd933c706a9c07b6bd0763fd1819533fdc7302fc6eb5b3d8',
                                             'attempt_body': {'activation_request_digest': 'sha256:6cd48783d6e3dbca2135721fb643553d26d10921394f1563b11c1668bea0bf86',
                                                              'actor_ref': 'value:actor_ref',
                                                              'application_authority_body': {'application_ref': 'application:test',
                                                                                             'authority_digest': 'sha256:b4b8b6c9c7446effbd933c706a9c07b6bd0763fd1819533fdc7302fc6eb5b3d8',
                                                                                             'implementation_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'},
                                                              'application_authority_digest': 'sha256:b4b8b6c9c7446effbd933c706a9c07b6bd0763fd1819533fdc7302fc6eb5b3d8',
                                                              'attempt_digest': 'sha256:00186e0a0961a228b58e037f9495c16f89ddab9d94ee924991b5f6e8b8c1ece5',
                                                              'attempt_ref': 'ontology-object-attempt:sha256:2621f63cb7b391244304015c0cc3d25f62705b137b76b8f6cabb1c7c6466fde0',
                                                              'base_operational_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                              'branch_ref': 'value:branch_ref',
                                                              'codec_version': 1,
                                                              'executable_authority_body': {'admission_provider_generation': 'value:provider_generation',
                                                                                            'admission_provider_key': 'value:provider_key',
                                                                                            'authority_digest': 'sha256:9481b6ca2fa7d845cd68936f9da431fbcb20a3e1526c1c07ee5980560e052a13',
                                                                                            'authority_ref': 'executable:test',
                                                                                            'base_operational_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                                            'capability_catalog_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                                            'executable_root_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                                                            'vm_implementation_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'},
                                                              'executable_authority_digest': 'sha256:9481b6ca2fa7d845cd68936f9da431fbcb20a3e1526c1c07ee5980560e052a13',
                                                              'execution_admission_request_digest': 'sha256:0f3725c5b53541f49b0474c4385eb469ae45bef79d11c7e0d4accd0d019c95ae',
                                                              'expected_revision_ref': None,
                                                              'idempotency_key': 'value:idempotency_key',
                                                              'object_abi_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                              'operation_ref': 'value:operation_ref',
                                                              'projection_ref': 'value:projection_ref',
                                                              'provider_generation': 'value:provider_generation',
                                                              'provider_key': 'value:provider_key',
                                                              'provider_profile_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                              'recovery_ref': 'ontology-object-recovery:sha256:857c1cfb64f9706a459c30220b0f9696dbd281b8049721cfffb5b16178105271',
                                                              'schema': 'aware.ontology.object-operation-attempt.v1',
                                                              'schema_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                              'schema_slice_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                                              'topology_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'},
                                             'attempt_digest': 'sha256:00186e0a0961a228b58e037f9495c16f89ddab9d94ee924991b5f6e8b8c1ece5',
                                             'codec_version': 1,
                                             'executable_authority_digest': 'sha256:9481b6ca2fa7d845cd68936f9da431fbcb20a3e1526c1c07ee5980560e052a13',
                                             'execution_admission_request_digest': 'sha256:0f3725c5b53541f49b0474c4385eb469ae45bef79d11c7e0d4accd0d019c95ae',
                                             'object_abi_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                             'preparation_disposition': 'prepared_without_provider_contact',
                                             'provider_action_count': 0,
                                             'provider_begin_count': 0,
                                             'provider_profile_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                             'provider_read_count': 0,
                                             'provider_recovery_count': 0,
                                             'provider_seal_count': 0,
                                             'provider_write_count': 0,
                                             'schema': 'aware.ontology.object-operation-attempt-admission.v1'},
 'OntologyObjectPrecontactRecoveryProfile': {'action_epoch_check_kind': 'durable_head_reread',
                                             'attempt_head_namespace_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                             'attempt_ref_scheme': 'ontology-object-attempt-sha256-v1',
                                             'codec_version': 1,
                                             'epoch_check_support': 'durable_head_reread_only',
                                             'executable_authority_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                             'native_fencing_implementation_contract_digest': None,
                                             'owner_write_epoch_check_kind': 'durable_head_reread',
                                             'profile_contract_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                             'profile_digest': 'sha256:6a50c22442d1ad2b2542294567dae61ae493fec0802c15c529605ebe04545f22',
                                             'provider_distribution_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
                                             'provider_generation': 'value:provider_generation',
                                             'provider_key': 'value:provider_key',
                                             'recovery_ref_scheme': 'ontology-object-recovery-sha256-v1',
                                             'restart_recovery_kind': 'durable_provider_journal',
                                             'schema': 'aware.ontology.object-precontact-recovery-profile.v1',
                                             'seal_epoch_check_kind': 'durable_head_reread',
                                             'supports_precontact_resolution': True,
                                             'supports_preseal_resolution': True,
                                             'supports_seal_intent_recovery': True,
                                             'trace_namespace_digest': 'sha256:1111111111111111111111111111111111111111111111111111111111111111'}}
P1_PARENT_COORDINATES = {'OntologyObjectExecutableSelectionAdmission': (3824,
                                                '662ad72dd4ddb1f692a73aba3d2cea5d535a41a8eb0624c777eea9fad5f44019'),
 'OntologyObjectExecutableSelectionFacts': (1528,
                                            '5a15dc9e35ae1e90f51293b5c59586960c06392574d438df1d3de902b88da333'),
 'OntologyObjectExecutableSelectionProfile': (2335,
                                              '1669bc05e8d76b131c113f00fea97a965facfaac862e3615ecf4d198ae8f846a'),
 'OntologyObjectExecutableSelectionTextRule': (210,
                                               'ec1d9a2ba64ffee132a0bd532f37cdba056564ae29517195c04ec95bdf589a81'),
 'OntologyObjectOperationAttempt': (2605,
                                    '2ef4d94f68960de9a0a7c7889cabeaff4f1b27855e1f4202e068381719377416'),
 'OntologyObjectOperationAttemptAdmission': (3616,
                                             '839a185047a97fa1b33927b473c7ae25d806a66ed8b18ed017ce45e9582ed1e5'),
 'OntologyObjectPrecontactRecoveryProfile': (1300,
                                             '6a261712dcf98b1af4a8e9e57e99a555c43b7f2a5eeb0a964ecd4f5af18c2f3c')}


@pytest.mark.parametrize("name", tuple(P1_PARENT_WIRES))
def test_p1_frozen_parent_complete_records_and_detached_reconstruction(name):
    import copy
    kind = getattr(owner, name)
    wire = P1_PARENT_WIRES[name]
    expected = json.dumps(wire, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    assert (len(expected), hashlib.sha256(expected).hexdigest()) == P1_PARENT_COORDINATES[name]
    for value in (kind.from_wire(wire), kind.from_canonical_bytes(expected), kind(**owner._attempt_convert_nested(name, wire)), kind.create(**wire)):
        assert type(value) is kind
        assert value.to_wire() == wire
        assert value.canonical_bytes() == expected
        with pytest.raises(TypeError):
            copy.copy(value)
        with pytest.raises(TypeError):
            copy.deepcopy(value)
        object.__setattr__(value, kind._digest_field, "sha256:" + "0" * 64)
        with pytest.raises((TypeError, ValueError)):
            value.canonical_bytes()


@pytest.mark.parametrize("name", tuple(P1_PARENT_WIRES))
@pytest.mark.parametrize("mode", ("foreign", "scalar_subclass", "native_restamp"))
def test_p1_recursive_operands_reject_before_foreign_dispatch(name, mode):
    calls = []
    class Meta(type):
        def __eq__(cls, other):
            calls.append("metaclass equality")
            return False
        def __hash__(cls):
            calls.append("metaclass hash")
            return 0
    class Foreign(metaclass=Meta):
        def __getattribute__(self, field):
            calls.append("attribute")
            raise AssertionError(field)
    class Scalar(str):
        def __eq__(self, other):
            calls.append("scalar equality")
            return False
        def strip(self, chars: str | None = None):
            calls.append("scalar strip")
            return self
    wire = json.loads(json.dumps(P1_PARENT_WIRES[name]))
    wire["schema"] = Foreign() if mode == "foreign" else Scalar(wire["schema"]) if mode == "scalar_subclass" else True
    with pytest.raises((TypeError, ValueError)):
        getattr(owner, name).from_wire(wire)
    assert calls == []


@pytest.mark.parametrize("name", tuple(P1_PARENT_WIRES))
@pytest.mark.parametrize("entrance", ("construct", "create", "wire", "bytes"))
def test_p1_guard_binding_is_checked_before_dispatch(monkeypatch, name, entrance):
    kind, wire = getattr(owner, name), P1_PARENT_WIRES[name]
    value = kind.from_wire(wire)
    body = value.canonical_bytes()
    calls = []
    def foreign():
        calls.append("guard")
    monkeypatch.setattr(owner, "_attempt_guard", foreign)
    with pytest.raises((TypeError, ValueError)):
        if entrance == "construct":
            kind(**wire)
        elif entrance == "create":
            kind.create(**{key: item for key, item in wire.items() if key not in ("schema", "codec_version", kind._digest_field)})
        elif entrance == "wire":
            value.to_wire()
        else:
            kind.from_canonical_bytes(body)
    assert calls == []


@pytest.mark.parametrize("helper", ("_attempt_normalize", "_attempt_wire_value", "_attempt_validate_wire", "_attempt_convert_nested", "attempt_digest_bytes"))
@pytest.mark.parametrize("entrance", ("encode", "decode", "create"))
def test_p1_helper_binding_and_original_code_are_protected(monkeypatch, helper, entrance):
    calls = []
    def foreign(*args, **kwargs):
        calls.append(helper)
        raise AssertionError("foreign portable helper")
    genuine = getattr(owner, helper)
    monkeypatch.setattr(owner, helper, foreign)
    with pytest.raises((TypeError, ValueError)):
        if entrance == "encode":
            owner.attempt_canonical_bytes({"key": [1]})
        elif entrance == "decode":
            owner.decode_attempt_canonical_bytes(b'{"key":1}')
        else:
            owner.OntologyObjectExecutableSelectionTextRule.create(kind="any_exact_text", values=())
    assert genuine is not foreign
    assert calls == []


@pytest.mark.parametrize("name", tuple(P1_PARENT_WIRES))
def test_p1_every_digest_and_correspondence_rejects_even_with_outer_rehash(name):
    kind = getattr(owner, name)
    for field in kind._field_names:
        if "digest" not in field:
            continue
        wire = json.loads(json.dumps(P1_PARENT_WIRES[name]))
        if wire[field] is None:
            continue
        wire[field] = "sha256:" + "0" * 64
        if field != kind._digest_field:
            wire[kind._digest_field] = owner.attempt_digest_wire(kind._schema, {key: item for key, item in wire.items() if key != kind._digest_field})
        # Independent source coordinates may be any valid digest. Only digests
        # with a derivation/correspondence or the owning digest must reject.
        derived = {
            "OntologyObjectExecutableSelectionProfile": ("selection_facts_digest",),
            "OntologyObjectExecutableSelectionAdmission": ("selection_profile_digest", "executable_authority_digest"),
            "OntologyObjectOperationAttempt": ("activation_request_digest", "execution_admission_request_digest", "application_authority_digest", "executable_authority_digest"),
            "OntologyObjectOperationAttemptAdmission": ("attempt_digest", "provider_profile_digest", "object_abi_digest", "application_authority_digest", "executable_authority_digest", "execution_admission_request_digest"),
        }
        must_reject = field == kind._digest_field or field in derived.get(name, ())
        if must_reject:
            with pytest.raises((TypeError, ValueError)):
                kind.from_wire(wire)


def test_p1_invalid_nested_record_under_recomputed_enclosing_hashes():
    name = "OntologyObjectExecutableSelectionProfile"
    kind = getattr(owner, name)
    wire = json.loads(json.dumps(P1_PARENT_WIRES[name]))
    facts = wire["selection_facts_body"]
    facts["actor_rule_body"]["rule_digest"] = "sha256:" + "0" * 64
    facts["facts_digest"] = owner.attempt_digest_wire(owner.OntologyObjectExecutableSelectionFacts._schema, {key: item for key, item in facts.items() if key != "facts_digest"})
    wire["selection_facts_digest"] = facts["facts_digest"]
    wire["profile_digest"] = owner.attempt_digest_wire(kind._schema, {key: item for key, item in wire.items() if key != "profile_digest"})
    with pytest.raises((TypeError, ValueError)):
        kind.from_wire(wire)
    with pytest.raises((TypeError, ValueError)):
        kind(**wire)


def _p1_vector_bytes(wire: dict[str, Any]) -> bytes:
    return json.dumps(wire, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def _p1_vector_digest(domain: str, wire: dict[str, Any], separator: bytes = b"\0") -> str:
    return "sha256:" + hashlib.sha256(domain.encode() + separator + _p1_vector_bytes(wire)).hexdigest()


def _p1_vector_own_digest(wire: dict[str, Any], field: str) -> None:
    wire[field] = _p1_vector_digest(wire["schema"], {key: item for key, item in wire.items() if key != field})


def _p1_rebuild_authority_chain(name: str, body_name: str, field: str, invalid: object) -> dict[str, Any]:
    """Independent wire oracle: rebuild all hashes/references, without owner helpers."""
    wire = json.loads(json.dumps(P1_PARENT_WIRES[name]))
    attempt = wire["attempt_body"] if name == "OntologyObjectOperationAttemptAdmission" else wire
    nested = attempt[body_name]
    nested[field] = invalid
    for nested_name, domain in (
        ("application_authority_body", "aware.ontology.object-application-authority.v1"),
        ("executable_authority_body", "aware.ontology.object-executable-authority.v1"),
    ):
        if nested_name not in attempt:
            continue
        authority = attempt[nested_name]
        digest = _p1_vector_digest(domain, {key: item for key, item in authority.items() if key != "authority_digest"}, b"\n")
        # An invalid owning digest is deliberately invalid. All its enclosing
        # hashes/joins are still rebuilt; it cannot also be its valid preimage.
        if nested_name != body_name or field != "authority_digest":
            authority["authority_digest"] = digest
        attempt[nested_name.removesuffix("_body") + "_digest"] = digest
    if name == "OntologyObjectExecutableSelectionAdmission":
        facts = wire["selection_profile_body"]["selection_facts_body"]
        for authority_field, facts_field in (
            ("admission_provider_key", "provider_key"),
            ("admission_provider_generation", "provider_generation"),
            ("authority_ref", "authority_ref"),
            ("executable_root_digest", "executable_root_digest"),
            ("vm_implementation_digest", "vm_implementation_digest"),
            ("capability_catalog_digest", "capability_catalog_digest"),
        ):
            # Keep the Facts valid: these joins can mismatch, but the asserted
            # owning-field error must precede comparison or authority hashing.
            if field != authority_field:
                assert nested[authority_field] == facts[facts_field]
        _p1_vector_own_digest(wire, "admission_digest")
        return wire
    executable = attempt["executable_authority_body"]
    # Keep outer native field laws valid, so shared provider/base mismatches
    # cannot be rejected there before the nested owning-field validator runs.
    for nested_field, outer_field in (
        ("admission_provider_key", "provider_key"),
        ("admission_provider_generation", "provider_generation"),
        ("base_operational_digest", "base_operational_digest"),
    ):
        if field != nested_field or body_name != "executable_authority_body":
            assert executable[nested_field] == attempt[outer_field]
    activation = {key: attempt[key] for key in (
        "branch_ref", "actor_ref", "projection_ref", "operation_ref", "idempotency_key",
        "object_abi_digest", "application_authority_body", "expected_revision_ref",
    )}
    attempt["activation_request_digest"] = _p1_vector_digest("aware.ontology.object-activation-request.v1", activation)
    execution = {key: attempt[key] for key in (
        "activation_request_digest", "provider_key", "provider_generation", "topology_digest",
        "schema_digest", "schema_slice_digest", "base_operational_digest",
    )}
    attempt["execution_admission_request_digest"] = _p1_vector_digest("aware.ontology.object-execution-admission-request.v1", execution)
    coordinates = {key: attempt[key] for key in (
        "activation_request_digest", "execution_admission_request_digest", "provider_profile_digest",
    )}
    attempt["attempt_ref"] = "ontology-object-attempt:" + _p1_vector_digest(
        "aware.ontology.object-operation-attempt-coordinate.v1.digest",
        {**coordinates, "schema": "aware.ontology.object-operation-attempt-coordinate.v1"},
    )
    attempt["recovery_ref"] = "ontology-object-recovery:" + _p1_vector_digest(
        "aware.ontology.object-operation-recovery-coordinate.v1.digest",
        {**coordinates, "attempt_ref": attempt["attempt_ref"], "schema": "aware.ontology.object-operation-recovery-coordinate.v1"},
    )
    _p1_vector_own_digest(attempt, "attempt_digest")
    if name == "OntologyObjectOperationAttemptAdmission":
        for key in ("attempt_digest", "provider_profile_digest", "object_abi_digest",
                    "application_authority_digest", "executable_authority_digest", "execution_admission_request_digest"):
            wire[key] = attempt[key]
        _p1_vector_own_digest(wire, "admission_digest")
    return wire


P1_AUTHORITY_INVALID_FIELDS = (
    ("application_authority_body", "application_ref", 17),
    ("application_authority_body", "implementation_digest", "not-a-digest"),
    ("application_authority_body", "authority_digest", "not-a-digest"),
    ("executable_authority_body", "admission_provider_key", 17),
    ("executable_authority_body", "admission_provider_generation", 17),
    ("executable_authority_body", "authority_ref", 17),
    ("executable_authority_body", "executable_root_digest", "not-a-digest"),
    ("executable_authority_body", "vm_implementation_digest", "sha256:" + "A" * 64),
    ("executable_authority_body", "capability_catalog_digest", "sha256:1"),
    ("executable_authority_body", "base_operational_digest", "not-a-digest"),
    ("executable_authority_body", "authority_digest", "not-a-digest"),
)


@pytest.mark.parametrize("name", ("OntologyObjectOperationAttempt", "OntologyObjectOperationAttemptAdmission", "OntologyObjectExecutableSelectionAdmission"))
def test_p1_independent_authority_chain_oracle_preserves_complete_parent_wire(name):
    original = P1_PARENT_WIRES[name]
    attempt = original["attempt_body"] if name == "OntologyObjectOperationAttemptAdmission" else original
    rebuilt = _p1_rebuild_authority_chain(name, "executable_authority_body", "authority_ref", attempt["executable_authority_body"]["authority_ref"])
    assert rebuilt == original
    assert (len(_p1_vector_bytes(rebuilt)), hashlib.sha256(_p1_vector_bytes(rebuilt)).hexdigest()) == P1_PARENT_COORDINATES[name]


@pytest.mark.parametrize("name", ("OntologyObjectOperationAttempt", "OntologyObjectOperationAttemptAdmission"))
@pytest.mark.parametrize("body_name,field,replacement", (
    ("application_authority_body", "application_ref", "application:detached-copy"),
    ("application_authority_body", "implementation_digest", "sha256:" + "b" * 64),
    ("executable_authority_body", "authority_ref", "executable:detached-copy"),
    ("executable_authority_body", "executable_root_digest", "sha256:" + "b" * 64),
    ("executable_authority_body", "vm_implementation_digest", "sha256:" + "c" * 64),
    ("executable_authority_body", "capability_catalog_digest", "sha256:" + "d" * 64),
))
def test_p1_rebuilt_valid_authorities_remain_detached_by_value(name, body_name, field, replacement):
    kind = getattr(owner, name)
    wire = _p1_rebuild_authority_chain(name, body_name, field, replacement)
    body = _p1_vector_bytes(wire)
    for value in (kind(**wire), kind.create(**wire), kind.from_wire(wire), kind.from_canonical_bytes(body)):
        assert value.to_wire() == wire and value.canonical_bytes() == body


def _p1_assert_invalid_authority_entrance(name: str, wire: dict[str, Any], field: str, entrance: str) -> None:
    kind = getattr(owner, name)
    original = kind.from_wire(P1_PARENT_WIRES[name]) if entrance in ("encode_wire", "encode_bytes") else None
    if original is not None:
        for key, item in wire.items():
            object.__setattr__(original, key, item)
    message = f"{field} must be " + (
        "a lowercase SHA-256 coordinate" if "digest" in field else "nonempty unpadded exact str"
    )
    # Exact field error proves semantic refusal occurs before hash, join or
    # weak construction-fingerprint rejection (including coherently restamped encodes).
    with pytest.raises(owner.OntologyObjectOperationAttemptCodecError, match="^" + message + "$"):
        if entrance == "construct":
            kind(**wire)
        elif entrance == "factory":
            kind.create(**wire)
        elif entrance == "decode_wire":
            kind.from_wire(wire)
        elif entrance == "decode_bytes":
            kind.from_canonical_bytes(_p1_vector_bytes(wire))
        elif entrance == "encode_wire":
            assert original is not None
            original.to_wire()
        else:
            assert entrance == "encode_bytes" and original is not None
            original.canonical_bytes()


@pytest.mark.parametrize("body_name,field,invalid", P1_AUTHORITY_INVALID_FIELDS)
@pytest.mark.parametrize("entrance", ("construct", "factory", "decode_wire", "decode_bytes", "encode_wire", "encode_bytes"))
def test_p1_authority_field_laws_precede_fully_rebuilt_attempt_coordinates(body_name, field, invalid, entrance):
    name = "OntologyObjectOperationAttempt"
    wire = _p1_rebuild_authority_chain(name, body_name, field, invalid)
    _p1_assert_invalid_authority_entrance(name, wire, field, entrance)


@pytest.mark.parametrize("body_name,field,invalid", P1_AUTHORITY_INVALID_FIELDS)
def test_p1_authority_field_laws_recurse_through_complete_attempt_admission(body_name, field, invalid):
    name = "OntologyObjectOperationAttemptAdmission"
    wire = _p1_rebuild_authority_chain(name, body_name, field, invalid)
    _p1_assert_invalid_authority_entrance(name, wire, field, "decode_bytes")


@pytest.mark.parametrize("body_name,field,invalid", [case for case in P1_AUTHORITY_INVALID_FIELDS if case[0] == "executable_authority_body"])
@pytest.mark.parametrize("entrance", ("construct", "factory", "decode_wire", "decode_bytes", "encode_wire", "encode_bytes"))
def test_p1_selection_admission_validates_owning_authority_fields_before_joins(body_name, field, invalid, entrance):
    name = "OntologyObjectExecutableSelectionAdmission"
    wire = _p1_rebuild_authority_chain(name, body_name, field, invalid)
    _p1_assert_invalid_authority_entrance(name, wire, field, entrance)


@pytest.mark.parametrize("name", ("OntologyObjectOperationAttempt", "OntologyObjectOperationAttemptAdmission", "OntologyObjectExecutableSelectionAdmission"))
@pytest.mark.parametrize("entrance", ("construct", "factory", "decode_bytes", "encode_bytes"))
def test_p1_authority_validator_binding_cannot_replace_retained_validation(monkeypatch, name, entrance):
    kind, wire = getattr(owner, name), P1_PARENT_WIRES[name]
    value = kind.from_wire(wire)
    body = value.canonical_bytes()
    calls = []
    def foreign(*args, **kwargs):
        calls.append("authority validator")
    monkeypatch.setattr(owner, "_attempt_validate_authority", foreign)
    with pytest.raises((TypeError, ValueError)):
        if entrance == "construct":
            kind(**wire)
        elif entrance == "factory":
            kind.create(**wire)
        elif entrance == "decode_bytes":
            kind.from_canonical_bytes(body)
        else:
            value.canonical_bytes()
    assert calls == []


@pytest.mark.parametrize("body_name,field", (("application_authority_body", "application_ref"), ("executable_authority_body", "authority_ref")))
@pytest.mark.parametrize("mode", ("foreign", "scalar_subclass"))
@pytest.mark.parametrize("entrance", ("construct", "factory", "decode_wire", "encode_wire", "encode_bytes"))
def test_p1_nested_authority_operands_reject_without_foreign_behavior(body_name, field, mode, entrance):
    calls = []
    class Foreign:
        def __getattribute__(self, name):
            calls.append("attribute")
            raise AssertionError(name)
        def __eq__(self, other):
            calls.append("equality")
            return False
    class Scalar(str):
        def strip(self, chars: str | None = None):
            calls.append("strip")
            return self
        def encode(self, encoding="utf-8", errors="strict"):
            calls.append("encode")
            return b"foreign"
    kind = owner.OntologyObjectOperationAttempt
    original = kind.from_wire(P1_PARENT_WIRES[kind.__name__])
    wire = json.loads(json.dumps(P1_PARENT_WIRES[kind.__name__]))
    wire[body_name][field] = Foreign() if mode == "foreign" else Scalar(wire[body_name][field])
    with pytest.raises(owner.OntologyObjectOperationAttemptCodecError):
        if entrance == "construct":
            kind(**wire)
        elif entrance == "factory":
            kind.create(**wire)
        elif entrance == "decode_wire":
            kind.from_wire(wire)
        else:
            object.__setattr__(original, body_name, wire[body_name])
            if entrance == "encode_wire":
                original.to_wire()
            else:
                original.canonical_bytes()
    assert calls == []


@pytest.mark.parametrize("name", ("OntologyObjectOperationAttempt", "OntologyObjectExecutableSelectionAdmission"))
def test_p1_authority_validation_return_authenticates_next_dispatch(monkeypatch, name):
    wrapper = cast(Any, owner._attempt_validate_authority)
    operation_cell = next(cell for key, cell in zip(wrapper.__code__.co_freevars, wrapper.__closure__ or ()) if key == "operation")
    original = operation_cell.cell_contents
    observed, calls = [], []
    def foreign(*args, **kwargs):
        calls.append("authority validator")
    def observed_authority(wire, *, application=False):
        result = original(wire, application=application)
        observed.append(True)
        monkeypatch.setattr(owner, "_attempt_validate_authority", foreign)
        return result
    monkeypatch.setattr(operation_cell, "cell_contents", observed_authority)
    _p1_seal_observed_owner_dependencies(monkeypatch)
    with pytest.raises((TypeError, ValueError)):
        getattr(owner, name).from_wire(P1_PARENT_WIRES[name])
    assert observed == [True] and calls == []


def test_p1_lower_grammar_domains_and_unbounded_historical_bytes():
    wire = {"é": (False, 1, None, {"key": "value"}), "long": "x" * 70000}
    expected = json.dumps(wire, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert owner.attempt_canonical_bytes(wire) == expected
    assert owner.decode_attempt_canonical_bytes(expected) == {"é": [False, 1, None, {"key": "value"}], "long": "x" * 70000}
    assert owner.attempt_digest_wire("aware.test.p1", wire) == "sha256:" + hashlib.sha256(b"aware.test.p1\0" + expected).hexdigest()
    assert owner.digest_payload("aware.test.p1", owner.decode_attempt_canonical_bytes(expected)) == "sha256:" + hashlib.sha256(b"aware.test.p1\n" + expected).hexdigest()
    assert owner.attempt_digest_wire("aware.test.p1", wire) != owner.digest_payload("aware.test.p1", owner.decode_attempt_canonical_bytes(expected))


@pytest.mark.parametrize("body", (b'{"x":1,"x":2}', b'{ "x":1}', b'{"x":1.0}', b'{"x":NaN}', b'{"x":" padded"}', b'[]', b'\xff'))
def test_p1_lower_decoder_preserves_strict_refusals(body):
    with pytest.raises(owner.OntologyObjectOperationAttemptCodecError):
        owner.decode_attempt_canonical_bytes(body)


@pytest.mark.parametrize("target", ("helper", "constructor", "defaults"))
def test_p1_protected_return_check_precedes_next_dispatch(monkeypatch, target):
    import sys
    from types import FunctionType
    wrapper = cast(Any, owner._attempt_text)
    operation_cell = next(cell for name, cell in zip(wrapper.__code__.co_freevars, wrapper.__closure__ or ()) if name == "operation")
    original = operation_cell.cell_contents
    observed, calls = [], []
    def foreign(*args, **kwargs):
        calls.append(target)
        raise AssertionError("foreign portable return dispatch")
    def observed_text(value, field):
        result = original(value, field)
        if not observed:
            observed.append(True)
            if target == "helper":
                monkeypatch.setattr(owner, "_attempt_normalize", foreign)
            elif target == "constructor":
                monkeypatch.setattr(owner.OntologyObjectExecutableSelectionTextRule, "__init__", foreign)
            else:
                monkeypatch.setitem(cast(Any, owner._attempt_normalize).__wrapped__.__kwdefaults__, "mapping_required", [foreign])
        return result
    monkeypatch.setattr(operation_cell, "cell_contents", observed_text)
    # Instrumentation is installed before this test's retained snapshot. The
    # actual compiled text helper still runs; subsequent changes occur only on
    # its observed return and are checked by the production entrance wrapper.
    _p1_seal_observed_owner_dependencies(monkeypatch)
    with pytest.raises((TypeError, ValueError)):
        owner.attempt_digest_bytes("aware.test.p1", b'{}')
    assert observed == [True] and calls == []


def test_p1_native_traversal_counter_scales_with_lower_input():
    import sys
    code = cast(Any, owner._attempt_normalize).__wrapped__.__code__
    counts = []
    for size in (16, 32):
        count = 0
        def observe(frame, event, arg):
            nonlocal count
            if event == "call" and frame.f_code is code:
                count += 1
        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            encoded = owner.attempt_canonical_bytes({"data": list(range(size))})
        finally:
            sys.setprofile(previous)
        assert json.loads(encoded) == {"data": list(range(size))}
        counts.append(count)
    assert counts == [18, 34]


def test_p1_dispatch_seal_cannot_refresh_changed_code(monkeypatch):
    calls = []
    def foreign(*args, **kwargs):
        calls.append("seal")
    monkeypatch.setattr(owner, "_attempt_normalize", foreign)
    with pytest.raises((TypeError, ValueError)):
        owner._attempt_seal()
    assert calls == []


def test_p1_reconstruction_checks_wire_names_before_hashing():
    calls = []
    class Key(str):
        def __hash__(self):
            calls.append("hash")
            return super().__hash__()
    arguments = dict(P1_PARENT_WIRES["OntologyObjectExecutableSelectionTextRule"])
    del arguments["kind"]
    arguments[Key("kind")] = "any_exact_text"
    calls.clear()
    with pytest.raises((TypeError, ValueError)):
        owner.OntologyObjectExecutableSelectionTextRule.from_wire(arguments)
    assert calls == []


def _p1_seal_observed_owner_dependencies(monkeypatch):
    """Retain a test-installed observer before exercising its return boundary."""
    import sys
    from types import FunctionType
    functions = [value for value in vars(owner).values() if type(value) is FunctionType]
    for kind in (*owner._attempt_classes, owner._AttemptPortableValue):
        for value in vars(kind).values():
            if type(value) is classmethod:
                value = value.__func__
            if type(value) is FunctionType:
                functions.append(value)
    seen = set()
    for function in functions:
        for cell in function.__closure__ or ():
            value = cell.cell_contents
            if type(value) is FunctionType and id(value) not in seen:
                seen.add(id(value))
                functions.append(value)
    check = owner._protect_shape_dispatch((*owner._attempt_classes, owner._AttemptPortableValue, owner.OntologyObjectOperationAttemptCodecError, owner.OntologyRuntimeEncodingError, owner.WeakKeyDictionary, json.JSONEncoder, json.JSONDecoder, json.JSONDecodeError),
        guard_name="_attempt_guard", helpers=tuple(functions), retained_guard_cell=owner._attempt_guard_cell,
        extra_modules=tuple(sys.modules[name] for name in ("json", "json.encoder", "json.decoder", "json.scanner", "hashlib", "weakref")))
    monkeypatch.setattr(owner._attempt_guard_cell, "cell_contents", check)
    monkeypatch.setattr(owner, "_attempt_guard", check)


def test_t1_projection_normalization_uses_single_shared_owner():
    value = owner.ProjectionDefinition("P", ("T",), ("T",), ("T.z", "T.a"), (), ())
    assert value.to_wire() == {"projection_ref": "P", "root_type_refs": ["T"], "type_refs": ["T"], "field_refs": ["T.a", "T.z"], "relationship_refs": [], "action_refs": []}
    assert type(value).__module__ == owner.__name__
    with pytest.raises(ValueError): owner.ProjectionDefinition("P", ("T",), ("T",), ("T.a", "T.a"))


@pytest.mark.parametrize("name", ("_shape_guard", "_binding_guard", "_record_guard", "_abi_guard", "_attempt_guard"))
@pytest.mark.parametrize("change", ("clean", "absent_none", "class_member", "code", "defaults", "kwdefaults", "cell", "container", "list", "primitive_port"))
def test_complete_scan_matches_original_comparator(monkeypatch, name, change):
    current = getattr(owner, name)
    original = _legacy_scan(current, owner, 2194)
    current()
    original()
    state = _scan_cells(current)
    calls = []
    list_target = None
    def foreign(*_args, **_kwargs):
        calls.append("foreign")
        raise AssertionError("scanner dispatched foreign behavior")
    with monkeypatch.context() as patch:
        if change == "absent_none":
            assert "abs" not in vars(owner)
            patch.setattr(owner, "abs", None, raising=False)
        elif change == "class_member":
            patch.setattr(owner.ValueShape, "_scan_extra", foreign, raising=False)
        elif change in ("code", "defaults", "kwdefaults"):
            patch.setattr(owner._shape_copy, "__" + change + "__",
                          foreign.__code__.replace(co_freevars=owner._shape_copy.__code__.co_freevars) if change == "code" else
                          (foreign,) if change == "defaults" else {"foreign": foreign})
        elif change == "cell":
            cell = state["cell_plan"][0][0][0]
            patch.setattr(cell, "cell_contents", foreign)
        elif change == "container":
            target = next(row[0] for row in state["container_plans"] if type(row[0]) is dict)
            patch.setitem(target, "_scan_extra", foreign)
        elif change == "list":
            target = next(row[0] for row in state["container_plans"] if type(row[0]) is list)
            list_target = target
            target.append(foreign)
        elif change == "primitive_port":
            import _operator
            patch.setattr(_operator, "is_", foreign)
        try:
            for checker in (original, current):
                if change == "clean":
                    checker()
                else:
                    with pytest.raises(TypeError):
                        checker()
            assert calls == []
        finally:
            if change == "list":
                assert list_target is not None
                assert list_target.pop() is foreign
    current()
    original()


@pytest.mark.parametrize("change", ("delete_none", "replace_value", "key_order", "foreign_key"))
def test_complete_namespace_scan_preserves_none_keys_and_identity(monkeypatch, change):
    extra = ModuleType("scan_parity_extra")
    vars(extra)["none"] = None
    vars(extra)["value"] = object()
    holder = {}
    current = owner._protect_shape_dispatch(guard_name="scan_parity", guard_namespace=holder, extra_modules=(extra,))
    holder["scan_parity"] = current
    original = _legacy_scan(current, owner, 2194)
    current()
    original()
    calls = []
    class Foreign:
        def __eq__(self, _other):
            calls.append("equality")
            raise AssertionError("foreign equality")
        def __hash__(self):
            return 77123456
    if change == "delete_none":
        del vars(extra)["none"]
    elif change == "replace_value":
        vars(extra)["value"] = Foreign()
    elif change == "key_order":
        value = extra.__dict__.pop("none")
        extra.__dict__["none"] = value
    else:
        cast(dict[Any, Any], vars(extra))[Foreign()] = object()
    for checker in (original, current):
        with pytest.raises(TypeError):
            checker()
    assert calls == []


@pytest.mark.parametrize("change", ("dictionary_shrink", "balanced_dictionaries", "sequence_shrink", "balanced_sequences", "same_length_substitution"))
def test_batched_scan_checks_each_original_extent_not_just_stream_prefix(change):
    first, second, third = object(), object(), object()
    left, right = {"a": first, "b": second}, {"c": third}
    one, two = [first, second], [third]

    extra = ModuleType("extent_parity_inputs")
    vars(extra).update(left=left, right=right, one=one, two=two)
    holder = {}
    current = owner._protect_shape_dispatch(
        guard_name="extent_parity", guard_namespace=holder, extra_modules=(extra,),
    )
    holder["extent_parity"] = current
    original = _legacy_scan(current, owner, 2194)
    current()
    original()
    try:
        if change == "dictionary_shrink":
            left.pop("b")
        elif change == "balanced_dictionaries":
            right["b"] = left.pop("b")
        elif change == "sequence_shrink":
            one.pop()
        elif change == "balanced_sequences":
            two.append(one.pop())
        else:
            one[1] = third
        for checker in (original, current):
            with pytest.raises(TypeError):
                checker()
    finally:
        left.clear()
        left.update(a=first, b=second)
        right.clear()
        right.update(c=third)
        one[:] = [first, second]
        two[:] = [third]
    # A refusal never turns into a cached denial or recaptured expectation.
    current()
    original()
