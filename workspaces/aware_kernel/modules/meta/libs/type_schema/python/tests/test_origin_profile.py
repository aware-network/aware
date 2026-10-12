from __future__ import annotations

import dis
import random
import sys
from types import FrameType

import pytest
from aware_meta_type_schema import encoding
from aware_meta_type_schema._origin_profile import canonical_json_for_origin
from aware_meta_type_schema.encoding import TypeSchemaEncodingError


def _cell(name: str):
    encoder = encoding._canonical_json_native_for_origin
    for current_name, cell in zip(
        encoder.__code__.co_freevars, encoder.__closure__ or (), strict=True
    ):
        if current_name == name:
            return cell
    raise AssertionError(name)


def test_canonical_parity_and_input_isolation() -> None:
    randomizer = random.Random(4729)
    values: list[object] = [None, True, False, 0, -1, "", "雪\n", [], {}]
    values.extend(
        {"z": [randomizer.randrange(-(10**20), 10**20), None], "a": "☃"}
        for _ in range(256)
    )
    for value in values:
        assert canonical_json_for_origin(value) == encoding.canonical_json(value)
    original = {"x": [1, {"y": True}]}
    assert canonical_json_for_origin(original) == '{"x":[1,{"y":true}]}'
    assert original == {"x": [1, {"y": True}]}


@pytest.mark.parametrize(
    "slot", ["type", "dict", "str", "set", "_canonical_json_native_for_origin"]
)
def test_owner_binding_and_absent_builtin_shadow(
    slot: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def foreign(*_args: object, **_kwargs: object) -> object:
        calls.append(True)
        raise AssertionError("foreign binding executed")

    monkeypatch.setattr(encoding, slot, foreign, raising=False)
    with pytest.raises(ValueError, match="^origin_owner_changed$"):
        canonical_json_for_origin({"x": []})
    assert calls == []


@pytest.mark.parametrize(
    "slot",
    ["quote", "native_type", "native_dict", "native_join", "error_new", "error_init"],
)
def test_encoder_capability_cell_substitution(slot: str) -> None:
    cell = _cell(slot)
    original = cell.cell_contents
    calls = []

    def foreign(*_args: object, **_kwargs: object) -> object:
        calls.append(True)
        raise AssertionError("foreign capability executed")

    try:
        cell.cell_contents = foreign
        with pytest.raises(ValueError, match="^origin_owner_changed$"):
            canonical_json_for_origin({"x": []})
    finally:
        cell.cell_contents = original
    assert calls == []
    assert canonical_json_for_origin({"x": []}) == '{"x":[]}'


def test_code_and_closure_expectation_restamp_reject() -> None:
    encoder = encoding._canonical_json_native_for_origin
    original_code = encoder.__code__
    calls = []
    # Match the original closure arity; changing code plus a rewritten retained
    # cell table cannot change the literal executable signature in the entrance.
    names = original_code.co_freevars
    source = "def factory():\n"
    source += "".join(f"    {name} = None\n" for name in names)
    source += "    def foreign(value):\n"
    source += "        retained = (" + ",".join(names) + ")\n"
    source += "        retained[0](value)\n        return 'poison'\n"
    source += "    return foreign\n"
    namespace = {}
    exec(source, namespace)  # noqa: S102 -- deliberately compile a closure poison
    foreign_code = namespace["factory"]().__code__
    first_cell = encoder.__closure__[0]
    original_first = first_cell.cell_contents
    root_cells = dict(
        zip(
            canonical_json_for_origin.__code__.co_freevars,
            canonical_json_for_origin.__closure__,
            strict=True,
        )
    )
    expectation = root_cells["encoder_cells"]
    original_expectation = expectation.cell_contents

    def foreign(_value: object) -> None:
        calls.append(True)

    try:
        encoder.__code__ = foreign_code
        first_cell.cell_contents = foreign
        expectation.cell_contents = tuple(
            (cell, cell.cell_contents) for cell in encoder.__closure__
        )
        with pytest.raises(ValueError, match="^origin_owner_changed$"):
            canonical_json_for_origin({})
    finally:
        encoder.__code__ = original_code
        first_cell.cell_contents = original_first
        expectation.cell_contents = original_expectation
    assert calls == []


@pytest.mark.parametrize("container", ["root", "list", "dict", "key"])
def test_foreign_native_operand_rejection(container: str) -> None:
    calls = []

    class ForeignMeta(type):
        def __eq__(cls, _other: object) -> bool:
            calls.append("class equality")
            raise AssertionError

    class Foreign(metaclass=ForeignMeta):
        def __hash__(self) -> int:
            return 101

        def __eq__(self, _other: object) -> bool:
            calls.append("equality")
            raise AssertionError

        def __getattribute__(self, _name: str) -> object:
            calls.append("attribute")
            raise AssertionError

    foreign = Foreign()
    value = {
        "root": foreign,
        "list": [foreign],
        "dict": {"x": foreign},
        "key": {foreign: 1},
    }[container]
    with pytest.raises(ValueError, match="^origin_native_data_invalid$"):
        canonical_json_for_origin(value)
    assert calls == []


@pytest.mark.parametrize("namespace", ["owner", "registry"])
def test_foreign_namespace_key_rejects_without_lookup(namespace: str) -> None:
    calls = []

    class ForeignKey:
        def __hash__(self) -> int:
            return hash("_canonical_json_native_for_origin")

        def __eq__(self, _other: object) -> bool:
            calls.append(True)
            return False

    key = ForeignKey()
    target = vars(encoding) if namespace == "owner" else sys.modules
    # Establish the poisoned dictionary before observing the entrance. Inserting
    # it may itself compare an existing key; the port must make no such lookup.
    target[key] = None
    calls.clear()
    try:
        with pytest.raises(ValueError, match="^origin_owner_changed$"):
            canonical_json_for_origin({})
        assert calls == []
    finally:
        del target[key]


@pytest.mark.parametrize("mutation", ["binding", "code", "cell", "registry"])
def test_actual_encoder_return_boundary_rechecks(mutation: str) -> None:
    encoder = encoding._canonical_json_native_for_origin
    original_code = encoder.__code__
    original_binding = encoding._canonical_json_native_for_origin
    quote_cell = _cell("quote")
    original_quote = quote_cell.cell_contents
    original_module = sys.modules[encoding.__name__]
    injected = []
    calls = []

    def foreign(*_args: object, **_kwargs: object) -> object:
        calls.append(True)
        raise AssertionError("foreign return replacement executed")

    def trace(frame: FrameType, event: str, _arg: object):
        if frame.f_code is original_code and event == "return" and not injected:
            injected.append(True)
            if mutation == "binding":
                encoding._canonical_json_native_for_origin = foreign
            elif mutation == "cell":
                quote_cell.cell_contents = foreign
            elif mutation == "registry":
                sys.modules[encoding.__name__] = object()
            else:
                encoder.__code__ = original_code.replace(
                    co_consts=(*original_code.co_consts, "poison")
                )
        return trace

    old_trace = sys.gettrace()
    try:
        sys.settrace(trace)
        with pytest.raises(ValueError, match="^origin_owner_changed$"):
            canonical_json_for_origin({"x": 1})
    finally:
        sys.settrace(old_trace)
        encoding._canonical_json_native_for_origin = original_binding
        quote_cell.cell_contents = original_quote
        sys.modules[encoding.__name__] = original_module
        encoder.__code__ = original_code
    assert injected == [True]
    assert calls == []


def test_encoder_foreign_code_constant_is_not_compared() -> None:
    calls = []

    class ForeignConstant:
        def __eq__(self, _other: object) -> bool:
            calls.append(True)
            raise AssertionError

    encoder = encoding._canonical_json_native_for_origin
    original = encoder.__code__
    try:
        encoder.__code__ = original.replace(
            co_consts=(ForeignConstant(), *original.co_consts[1:])
        )
        with pytest.raises(ValueError, match="^origin_owner_changed$"):
            canonical_json_for_origin({})
    finally:
        encoder.__code__ = original
    assert calls == []


def test_no_global_or_python_verifier_dispatch() -> None:
    assert not any(
        instruction.opname == "LOAD_GLOBAL"
        for instruction in dis.get_instructions(canonical_json_for_origin)
    )
    assert "check" not in canonical_json_for_origin.__code__.co_varnames


@pytest.mark.parametrize("slot", ["encode_basestring", "make_encoder"])
def test_backend_binding_replacement(
    slot: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def foreign(*_args: object, **_kwargs: object) -> object:
        calls.append(True)
        raise AssertionError

    monkeypatch.setattr(encoding._json, slot, foreign)
    with pytest.raises(ValueError, match="^origin_owner_changed$"):
        canonical_json_for_origin({})
    assert calls == []


@pytest.mark.parametrize("slot", ["__new__", "__init__"])
@pytest.mark.parametrize("bad_input", ["native", "owner"])
def test_refusal_constructor_substitution(
    slot: str, bad_input: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def foreign(*_args: object, **_kwargs: object) -> object:
        calls.append(True)
        raise AssertionError

    monkeypatch.setattr(TypeSchemaEncodingError, slot, foreign)
    value = object() if bad_input == "native" else {}
    if bad_input == "owner":
        monkeypatch.setattr(encoding, "type", foreign, raising=False)
    reason = (
        "origin_native_data_invalid"
        if bad_input == "native"
        else "origin_owner_changed"
    )
    with pytest.raises(ValueError, match=f"^{reason}$"):
        canonical_json_for_origin(value)
    assert calls == []


@pytest.mark.parametrize("owner", ["encoding", "backend", "system"])
def test_module_receiver_substitution(owner: str) -> None:
    from types import ModuleType

    calls = []

    class HostileModule(ModuleType):
        def __getattribute__(self, _name: str) -> object:
            calls.append(True)
            raise AssertionError

    module = {"encoding": encoding, "backend": encoding._json, "system": sys}[owner]
    original = module.__class__
    try:
        module.__class__ = HostileModule
        with pytest.raises(ValueError, match="^origin_owner_changed$"):
            canonical_json_for_origin({})
    finally:
        ModuleType.__setattr__(module, "__class__", original)
    assert calls == []


@pytest.mark.parametrize("slot", ["__defaults__", "__kwdefaults__"])
def test_encoder_defaults_replacement(slot: str) -> None:
    encoder = encoding._canonical_json_native_for_origin
    original = getattr(encoder, slot)
    try:
        setattr(encoder, slot, (None,) if slot == "__defaults__" else {"x": None})
        with pytest.raises(ValueError, match="^origin_owner_changed$"):
            canonical_json_for_origin({})
    finally:
        setattr(encoder, slot, original)


def test_unrelated_native_registry_entry_is_preserved() -> None:
    name = "_origin_unrelated_native_module"
    marker = object()
    assert name not in sys.modules
    sys.modules[name] = marker
    try:
        assert canonical_json_for_origin({"x": 1}) == '{"x":1}'
        assert sys.modules[name] is marker
    finally:
        del sys.modules[name]


def test_missing_none_owner_binding_with_extra_key_is_not_accepted() -> None:
    namespace = vars(encoding)
    original = namespace.pop("__doc__")
    namespace["_origin_extra_key"] = None
    try:
        with pytest.raises(ValueError, match="^origin_owner_changed$"):
            canonical_json_for_origin({})
    finally:
        del namespace["_origin_extra_key"]
        namespace["__doc__"] = original


def test_captured_cell_table_admission_is_behavior_free() -> None:
    calls = []

    class ForeignTable:
        def __iter__(self):
            calls.append(True)
            raise AssertionError

    root_cells = dict(
        zip(
            canonical_json_for_origin.__code__.co_freevars,
            canonical_json_for_origin.__closure__,
            strict=True,
        )
    )
    cell = root_cells["encoder_cells"]
    original = cell.cell_contents
    try:
        cell.cell_contents = ForeignTable()
        with pytest.raises(ValueError, match="^origin_owner_changed$"):
            canonical_json_for_origin({})
    finally:
        cell.cell_contents = original
    assert calls == []


def test_public_root_is_the_exact_owner_alias() -> None:
    import aware_meta_type_schema

    assert aware_meta_type_schema.canonical_json_for_origin is canonical_json_for_origin
    assert "canonical_json_for_origin" in aware_meta_type_schema.__all__


@pytest.mark.parametrize(
    "slot", ["owner_bindings", "backend_bindings", "builtins_bindings"]
)
def test_snapshot_table_type_precedes_len_and_iteration(slot: str) -> None:
    calls = []

    class ForeignTable:
        def __len__(self):
            calls.append("len")
            raise AssertionError

        def __iter__(self):
            calls.append("iter")
            raise AssertionError

    root_cells = dict(
        zip(
            canonical_json_for_origin.__code__.co_freevars,
            canonical_json_for_origin.__closure__,
            strict=True,
        )
    )
    cell = root_cells[slot]
    original = cell.cell_contents
    try:
        cell.cell_contents = ForeignTable()
        with pytest.raises(ValueError, match="^origin_owner_changed$"):
            canonical_json_for_origin({})
    finally:
        cell.cell_contents = original
    assert calls == []


@pytest.mark.parametrize(
    "slot", ["quote", "native_type", "native_join", "encoder_call", "error_new"]
)
def test_native_capability_and_expected_row_restamp(slot: str) -> None:
    encoder = encoding._canonical_json_native_for_origin
    current = _cell(slot)
    original = current.cell_contents
    root_cells = dict(
        zip(
            canonical_json_for_origin.__code__.co_freevars,
            canonical_json_for_origin.__closure__,
            strict=True,
        )
    )
    expectations = root_cells["encoder_cells"]
    original_expectations = expectations.cell_contents
    calls = []

    def foreign(*_args: object, **_kwargs: object) -> object:
        calls.append(True)
        raise AssertionError("foreign native replacement")

    try:
        current.cell_contents = foreign
        expectations.cell_contents = tuple(
            (cell, cell.cell_contents) for cell in encoder.__closure__
        )
        with pytest.raises(ValueError, match="^origin_owner_changed$"):
            canonical_json_for_origin({"x": 1})
    finally:
        current.cell_contents = original
        expectations.cell_contents = original_expectations
    assert calls == []


def test_native_quote_alias_and_all_expectations_restamp_reject() -> None:
    import builtins

    calls = []
    namespace = vars(builtins)
    name = "_origin_native_quote_probe"
    assert name not in namespace
    namespace[name] = calls
    root_cells = dict(
        zip(
            canonical_json_for_origin.__code__.co_freevars,
            canonical_json_for_origin.__closure__,
            strict=True,
        )
    )
    original_tables = {
        name: root_cells[name].cell_contents
        for name in ("backend_bindings", "builtins_bindings", "encoder_cells")
    }
    quote_cell = _cell("quote")
    original_quote = quote_cell.cell_contents
    backend_quote = encoding._json.encode_basestring
    try:
        encoding._json.encode_basestring = eval
        quote_cell.cell_contents = eval
        root_cells["backend_bindings"].cell_contents = tuple(
            vars(encoding._json).items()
        )
        root_cells["builtins_bindings"].cell_contents = tuple(namespace.items())
        root_cells["encoder_cells"].cell_contents = tuple(
            (cell, cell.cell_contents)
            for cell in encoding._canonical_json_native_for_origin.__closure__
        )
        # This builtin is native but interprets supplied text. Authentic name and
        # receiver checks must reject it before any quote callback is dispatched.
        value = "__import__('builtins')._origin_native_quote_probe.append(1) or ''"
        with pytest.raises(ValueError, match="^origin_owner_changed$"):
            canonical_json_for_origin(value)
    finally:
        encoding._json.encode_basestring = backend_quote
        quote_cell.cell_contents = original_quote
        for key, original in original_tables.items():
            root_cells[key].cell_contents = original
        del namespace[name]
    assert calls == []


@pytest.mark.parametrize("entry", ["canonical", "private"])
@pytest.mark.parametrize("path", ["native", "owner", "limit", "backend"])
@pytest.mark.parametrize("stage", ["before", "after"])
def test_native_refusal_collection_survives_legacy_finalizer(
    entry: str,
    path: str,
    stage: str,
) -> None:
    _isolated_refusal_probe("collection", entry, path, stage)


@pytest.mark.parametrize("entry", ["canonical", "private"])
@pytest.mark.parametrize("slot", ["error_class", "error_new", "error_init"])
@pytest.mark.parametrize("restamp", ["single", "expectation"])
def test_refusal_capability_substitution_is_safe_through_collection(
    entry: str,
    slot: str,
    restamp: str,
) -> None:
    _isolated_refusal_probe("capability", entry, slot, restamp)


@pytest.mark.parametrize("entry", ["canonical", "private"])
def test_refusal_alias_cells_and_all_expectations_cannot_bless_heap_class(
    entry: str,
) -> None:
    _isolated_refusal_probe("coherent", entry, "", "")


@pytest.mark.parametrize("target", ["root_cell", "builtins_alias", "installer_alias"])
def test_canonical_refusal_type_alias_is_admitted_before_allocation(
    target: str,
) -> None:
    _isolated_refusal_probe("alias", "canonical", target, "")


def test_private_bootstrap_refusal_uses_native_class() -> None:
    _isolated_refusal_probe("bootstrap", "private", "", "")


def test_generic_valueerror_is_not_an_origin_reason() -> None:
    # A genuine C-backend integer-formatting failure is an ordinary ValueError,
    # not a qualified Origin refusal; the entrance must not relabel its reason.
    previous_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(4300)
        with pytest.raises(ValueError) as unexpected:
            canonical_json_for_origin(10**4300)
    finally:
        sys.set_int_max_str_digits(previous_limit)
    assert type(unexpected.value) is ValueError
    assert "Exceeds the limit" in unexpected.value.args[0]
    assert unexpected.value.args[0] not in {
        "origin_owner_changed",
        "origin_native_data_invalid",
        "origin_native_data_limit",
        "origin_native_backend_changed",
    }


def _isolated_refusal_probe(mode: str, entry: str, operand: str, variant: str) -> None:
    import subprocess
    from pathlib import Path

    source = r"""
import builtins
import gc
import sys
from aware_meta_type_schema import encoding
from aware_meta_type_schema._origin_profile import canonical_json_for_origin
native_error = ValueError
legacy_error = encoding.TypeSchemaEncodingError
calls = []
mode, entry, operand, variant = sys.argv[1:]
encoder = encoding._canonical_json_native_for_origin
root_cells = dict(zip(canonical_json_for_origin.__code__.co_freevars,
                      canonical_json_for_origin.__closure__, strict=True))
encoder_cells = dict(zip(encoder.__code__.co_freevars,
                         encoder.__closure__, strict=True))

def foreign(*args, **kwargs):
    calls.append('FOREIGN')
    raise RuntimeError('foreign capability ran')

class HeapRefusal(native_error):
    __del__ = foreign
    __init__ = foreign
    __new__ = staticmethod(foreign)

class ForeignMeta(type):
    def __eq__(self, other):
        calls.append('FOREIGN_META_EQUALITY')
        raise RuntimeError('foreign equality')
    def __getattribute__(self, name):
        calls.append('FOREIGN_META_ATTRIBUTE')
        raise RuntimeError('foreign class attribute')

# Raw native hierarchy iteration must also skip an untrusted metaclass.
class UntrustedRefusal(native_error, metaclass=ForeignMeta):
    pass

invoke = canonical_json_for_origin if entry == 'canonical' else encoder
expected_reason = 'origin_owner_changed'
value = object()
if mode == 'collection':
    expected_reason = 'origin_native_data_invalid' if operand == 'native' else 'origin_owner_changed'
    if operand == 'limit':
        value = []
        value.append(value)
        expected_reason = 'origin_native_data_limit'
    elif operand == 'backend':
        encoding._json.make_encoder.__call__ = foreign
        expected_reason = 'origin_owner_changed' if entry == 'canonical' else 'origin_native_backend_changed'
        value = {}
    if variant == 'before':
        legacy_error.__del__ = foreign
    if operand == 'owner':
        if entry == 'canonical':
            encoding.type = foreign
        else:
            encoder_cells['error_class'].cell_contents = HeapRefusal
        value = {}
elif mode == 'capability':
    encoder_cells[operand].cell_contents = HeapRefusal if operand == 'error_class' else foreign
    if variant == 'expectation':
        root_cells['encoder_cells'].cell_contents = tuple(
            (cell, cell.cell_contents) for cell in encoder.__closure__)
elif mode == 'coherent':
    # Rebaseline every mutable alias and expectation involved in refusal.
    builtins.ValueError = HeapRefusal
    encoding.TypeSchemaEncodingError = HeapRefusal
    root_cells['error_class'].cell_contents = HeapRefusal
    encoder_cells['error_class'].cell_contents = HeapRefusal
    encoder_cells['error_new'].cell_contents = foreign
    encoder_cells['error_init'].cell_contents = foreign
    root_cells['owner_bindings'].cell_contents = tuple(vars(encoding).items())
    root_cells['builtins_bindings'].cell_contents = tuple(vars(builtins).items())
    root_cells['encoder_cells'].cell_contents = tuple(
        (cell, cell.cell_contents) for cell in encoder.__closure__)
elif mode == 'alias':
    if operand == 'root_cell':
        root_cells['error_class'].cell_contents = HeapRefusal
    else:
        from aware_meta_type_schema import _origin_profile
        if operand == 'builtins_alias':
            builtins.ValueError = HeapRefusal
        else:
            _origin_profile.ValueError = HeapRefusal
        invoke = _origin_profile._install_canonical_entrance()
elif mode == 'bootstrap':
    legacy_error.__del__ = foreign
    # This guarded member has no inherited replacement, exercising the early
    # factory refusal rather than any created encoder's traversal.
    del encoding._json.make_encoder.__call__
    invoke = lambda value: encoding._make_origin_native_canonical_encoder()
    expected_reason = 'origin_native_backend_changed'
else:
    raise AssertionError(mode)

def refuse_and_drop():
    try:
        invoke(value)
    except native_error as error:
        assert type(error) is native_error
        assert error.args == (expected_reason,)
        if mode == 'collection' and variant == 'after':
            legacy_error.__del__ = foreign
        # Verify the minted class and instance cannot acquire heap finalizers.
        for slot in ('__del__', '__getattribute__', '__getattr__', '__str__',
                     '__repr__', '__setattr__', '__new__', '__init__',
                     '__reduce__', '__reduce_ex__'):
            try:
                setattr(type(error), slot, foreign)
            except TypeError:
                pass
            else:
                raise AssertionError('native class accepted lifecycle rewrite')
        try:
            error.__class__ = HeapRefusal
        except TypeError:
            pass
        else:
            raise AssertionError('native instance accepted class rewrite')
    else:
        raise AssertionError('substitution accepted')
refuse_and_drop()
for _ in range(3):
    gc.collect()
assert calls == [], calls
print('NATIVE_REFUSED_AND_COLLECTED')
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", source, mode, entry, operand, variant],
        cwd=str(Path(encoding.__file__).resolve().parents[1]),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "NATIVE_REFUSED_AND_COLLECTED\n"
    assert result.stderr == ""
