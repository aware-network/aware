"""Locked native topology profile: original code, refusal and lifetime proofs."""

import gc
import subprocess
import sys
import weakref
from pathlib import Path
from types import CodeType, FunctionType

import pytest
from aware_ontology_object_facade_client import topology_values as values
from test_owner_body_parity import _legacy_scan, _scan_cells


@pytest.fixture
def native():
    if values._native_scan_module is None:
        pytest.skip("requires the locked native artifact")
    return values._native_scan_module


def _guard():
    return _scan_cells(_scan_cells(values._call)["checked"])["guard"]


@pytest.mark.parametrize("representation", ("holes", "general", "same_text", "foreign_key", "changed_value"))
def test_fresh_namespace_fast_path_and_iterator_fallback_match_oracle(native, representation):
    guard = _guard()
    code = guard.__code__
    scan = native.scan_topology
    oracle = _legacy_scan(guard, values, 1219)
    namespace = vars(values)
    original = tuple(namespace.items())
    key, value = original[-1]
    foreign = object()

    class ForeignKey(str):
        pass

    if representation == "holes":
        namespace["_temporary_native_hole_"] = None
        del namespace["_temporary_native_hole_"]
    elif representation == "general":
        namespace[foreign] = None
        del namespace[foreign]
    elif representation in {"same_text", "foreign_key"}:
        del namespace[key]
        replacement = (" " + key)[1:] if representation == "same_text" else ForeignKey(key)
        namespace[replacement] = value
    else:
        namespace[key] = foreign
    accepted = representation not in {"foreign_key", "changed_value"}
    try:
        assert scan(guard, code) is accepted
        if accepted:
            oracle()
        else:
            with pytest.raises(TypeError):
                oracle()
    finally:
        namespace.clear()
        namespace.update(original)
    assert scan(guard, code) is True


def _unbound():
    code = compile(Path(values.__file__).read_bytes(), values.__file__, "exec")
    outer = next(c for c in code.co_consts if type(c) is CodeType and c.co_name == "_install_dispatch")
    return FunctionType(outer, values.__dict__)


def _nested(code, name):
    return next(c for c in code.co_consts if type(c) is CodeType and c.co_name == name)


def test_native_topology_constant_binding_preserves_all_executable_fields(native):
    installer = _unbound()
    before = installer.__code__
    seal = _nested(before, "seal")
    checker = _nested(seal, "check")
    native.bind_topology_installer(installer)
    after = installer.__code__
    new_seal = _nested(after, "seal")
    new_checker = _nested(new_seal, "check")
    fields = ("co_argcount", "co_posonlyargcount", "co_kwonlyargcount", "co_nlocals",
              "co_stacksize", "co_flags", "co_code", "co_names", "co_varnames",
              "co_filename", "co_name", "co_qualname", "co_firstlineno",
              "co_linetable", "co_exceptiontable", "co_freevars", "co_cellvars")
    for old, new, child, replacement in ((before, after, seal, new_seal),
                                         (seal, new_seal, checker, new_checker)):
        for field in fields:
            assert getattr(old, field) == getattr(new, field), field
        for left, right in zip(old.co_consts, new.co_consts, strict=True):
            assert right is (replacement if left is child else left)
    for field in fields:
        assert getattr(checker, field) == getattr(new_checker, field), field
    for left, right in zip(checker.co_consts, new_checker.co_consts, strict=True):
        expected = (native.scan_topology if type(left) is str
                    and left == "__aware_native_topology_scan_anchor_v1__" else left)
        assert right is expected
    with pytest.raises(RuntimeError):
        native.bind_topology_installer(installer)
    assert installer.__code__ is after
    guard = _guard()
    assert any(c is native.scan_topology for c in guard.__code__.co_consts)
    assert native.scan_topology(guard, guard.__code__) is True
    guard()


@pytest.mark.parametrize("shape", ("no_seal", "duplicate_seal", "no_check", "duplicate_check", "no_anchor", "duplicate_anchor", "missing_field"))
def test_native_topology_binding_is_atomic_on_ambiguous_input(native, shape):
    installer = _unbound()
    outer = installer.__code__
    seal = _nested(outer, "seal")
    check = _nested(seal, "check")
    if shape == "no_seal":
        outer = outer.replace(co_consts=tuple(c for c in outer.co_consts if c is not seal))
    elif shape == "duplicate_seal":
        outer = outer.replace(co_consts=(*outer.co_consts, seal))
    else:
        if shape == "no_check":
            changed = tuple(c for c in seal.co_consts if c is not check)
        elif shape == "duplicate_check":
            changed = (*seal.co_consts, check)
        else:
            if shape == "missing_field":
                new_check = check.replace(co_freevars=tuple("missing_guard" if n == "guard" else n for n in check.co_freevars))
            else:
                marker = "__aware_native_topology_scan_anchor_v1__"
                if shape == "no_anchor":
                    constants = tuple(None if type(c) is str and c == marker else c for c in check.co_consts)
                else:
                    constants = (*check.co_consts, marker)
                new_check = check.replace(co_consts=constants)
            changed = tuple(new_check if c is check else c for c in seal.co_consts)
        new_seal = seal.replace(co_consts=changed)
        outer = outer.replace(co_consts=tuple(new_seal if c is seal else c for c in outer.co_consts))
    installer.__code__ = outer
    with pytest.raises(RuntimeError):
        native.bind_topology_installer(installer)
    assert installer.__code__ is outer
    _guard()()


def test_native_topology_rejects_copied_checker_and_unregistered_code(native):
    guard = _guard()
    clone = FunctionType(guard.__code__, guard.__globals__, closure=guard.__closure__)
    assert native.scan_topology(clone, clone.__code__) is False
    changed = guard.__code__.replace(co_firstlineno=1)
    assert native.scan_topology(guard, changed) is False
    assert native.scan_topology(None, None) is False
    guard()


@pytest.mark.parametrize("change", ("module", "class", "code", "defaults", "kwdefaults", "cell", "dict", "list"))
def test_native_topology_refusals_match_original_python_oracle(native, change):
    guard = _guard()
    state = _scan_cells(guard)
    oracle = _legacy_scan(guard, values, 1219)
    if change == "module":
        target, key, replacement = values, "SCHEMA_TOPOLOGY_CONTRACT", object()
    elif change == "class":
        target, key, replacement = values.GraphTypeBinding, "__qualname__", "changed"
    elif change in ("code", "defaults", "kwdefaults"):
        target = state["function_targets"][0]
        key = {"code": "__code__", "defaults": "__defaults__", "kwdefaults": "__kwdefaults__"}[change]
        replacement = target.__code__.replace(co_firstlineno=1) if change == "code" else (
            (1,) if change == "defaults" else {"changed": 1})
    elif change == "cell":
        closure = values._token.__closure__
        assert closure is not None
        target = next(c for n, c in zip(values._token.__code__.co_freevars, closure, strict=True) if n == "row")
        key, replacement = "cell_contents", object()
    elif change == "dict":
        target = state["dictionary_targets"][-1]
        guard(); oracle()
        target["_native_topology_probe_"] = object()
        try:
            assert native.scan_topology(guard, guard.__code__) is False
            with pytest.raises(TypeError):
                oracle()
        finally:
            del target["_native_topology_probe_"]
        guard(); oracle()
        return
    else:
        target = state["sequence_targets"][0]
        guard(); oracle()
        target.append(object())
        try:
            assert native.scan_topology(guard, guard.__code__) is False
            with pytest.raises(TypeError):
                oracle()
        finally:
            target.pop()
        guard(); oracle()
        return
    original = getattr(target, key)
    guard(); oracle()
    setattr(target, key, replacement)
    try:
        assert native.scan_topology(guard, guard.__code__) is False
        with pytest.raises(TypeError):
            guard()
        with pytest.raises(TypeError):
            oracle()
    finally:
        setattr(target, key, original)
    guard(); oracle()


@pytest.mark.parametrize("raising", (False, True))
def test_native_topology_never_calls_substituted_native_alias(native, raising):
    original = native.scan_topology
    calls = []

    def foreign(*_args):
        calls.append(True)
        if raising:
            raise RuntimeError("foreign scanner")
        return True

    native.scan_topology = foreign
    try:
        with pytest.raises(TypeError):
            _guard()()
        assert calls == []
    finally:
        native.scan_topology = original
    _guard()()


@pytest.mark.parametrize("field", ("module_plans", "class_plans", "container_plans", "cell_plan", "function_plan", "sys_get"))
@pytest.mark.parametrize("raising", (False, True))
def test_native_topology_admits_original_fields_before_foreign_behavior(native, field, raising):
    guard = _guard()
    cell = dict(zip(guard.__code__.co_freevars, guard.__closure__, strict=True))[field]
    original = cell.cell_contents
    calls = []

    class Foreign:
        def __iter__(self):
            calls.append("iter")
            if raising:
                raise RuntimeError("foreign iterator")
            return iter(())

        def __call__(self, *_args):
            calls.append("call")
            raise RuntimeError("foreign getter")

        def __eq__(self, _other):
            calls.append("eq")
            raise RuntimeError("foreign equality")

    cell.cell_contents = Foreign()
    try:
        assert native.scan_topology(guard, guard.__code__) is False
        with pytest.raises(TypeError):
            guard()
        assert calls == []
    finally:
        cell.cell_contents = original
    guard()


@pytest.mark.parametrize("raising", (False, True))
def test_native_topology_never_invokes_substituted_metaclass_descriptor(native, raising):
    calls = []
    meta = values._owner._TopologyEnumMeta
    original = meta.__dict__["__module__"]

    def foreign(_receiver):
        calls.append(True)
        if raising:
            raise RuntimeError("foreign class descriptor")
        return "enum"

    type.__setattr__(meta, "__module__", property(foreign))
    try:
        assert native.scan_topology(_guard(), _guard().__code__) is False
        with pytest.raises(TypeError):
            _guard()()
        assert calls == []
    finally:
        type.__setattr__(meta, "__module__", original)
    _guard()()


def test_native_topology_repeated_success_and_refusal_release_references(native):
    guard = _guard()
    state = _scan_cells(guard)
    dictionaries = [gc.get_referents(cls.__dict__)[0] for cls in state["class_targets"]]
    tracked = [guard, guard.__code__, *dictionaries, *state["function_targets"][:10]]
    before = tuple(sys.getrefcount(item) for item in tracked)
    for _ in range(100):
        assert native.scan_topology(guard, guard.__code__) is True
    assert tuple(sys.getrefcount(item) for item in tracked) == before
    original = values.SCHEMA_TOPOLOGY_CONTRACT
    values.SCHEMA_TOPOLOGY_CONTRACT = object()
    try:
        before = tuple(sys.getrefcount(item) for item in tracked)
        for _ in range(100):
            assert native.scan_topology(guard, guard.__code__) is False
        assert tuple(sys.getrefcount(item) for item in tracked) == before
    finally:
        values.SCHEMA_TOPOLOGY_CONTRACT = original
    guard()


def test_native_topology_layout_does_not_own_code_lifetime(native):
    def issue():
        installer = _unbound()
        native.bind_topology_installer(installer)
        return weakref.ref(installer.__code__), weakref.ref(_nested(_nested(installer.__code__, "seal"), "check"))

    refs = issue()
    gc.collect()
    assert all(ref() is None for ref in refs)
    _guard()()  # Prunes dead layouts without retaining any source owner.


def test_native_topology_hierarchy_substitution_cannot_resume_after_restoration(native):
    package = Path(values.__file__).parents[1]
    schema = Path(values.__file__).parents[5] / "meta" / "libs" / "type_schema" / "python"
    program = f'''
import importlib.abc, importlib.util, sys
from types import FunctionType
sys.path[:0] = [{str(package)!r}, {str(schema)!r}]
class Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name == "aware_ontology_object_facade_client._preparation_scan":
            return importlib.util.spec_from_file_location(name, {native.__file__!r})
sys.meta_path.insert(0, Finder())
from aware_ontology_object_facade_client import topology_values as v
def cells(fn): return dict(zip(fn.__code__.co_freevars, (c.cell_contents for c in fn.__closure__)))
guard = cells(cells(v._call)["checked"])["guard"]
n = v._native_scan_module
code = guard.__code__.replace(co_consts=tuple("__aware_native_topology_scan_anchor_v1__" if c is n.scan_topology else c for c in guard.__code__.co_consts))
oracle = FunctionType(code, guard.__globals__, closure=guard.__closure__)
guard(); oracle()
class Meta(type): __slots__ = ()
target = v._owner._TopologyMeta
old = target.__bases__
target.__bases__ = (Meta,)
for restored in (False, True):
    if restored: target.__bases__ = old
    assert n.scan_topology(guard, guard.__code__) is False
    try: oracle()
    except TypeError: pass
    else: raise AssertionError("MRO identity was silently renewed")
'''
    result = subprocess.run([sys.executable, "-I", "-c", program], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


def test_native_topology_trace_has_complete_functions_cells_and_live_reads(native):
    guard = _guard()
    state = _scan_cells(guard)
    report = native.observe_topology(guard, guard.__code__)
    assert report["accepted"] is True
    functions = [(label, group, row, position, identity) for label, group, row, position, identity in report["trace"]
                 if label == "topology.function"]
    expected = [("topology.function", 8, i, j, id(value))
                for i, row in enumerate(state["function_plan"][0])
                for j, value in enumerate(row[1:])]
    assert functions == expected
    cells = [event for event in report["trace"] if event[0] == "topology.cell"]
    assert [event[-1] for event in cells] == [id(expected) for _, expected in state["cell_plan"][0]]
    assert {event[0] for event in report["trace"]} >= {
        "topology.key.kind", "topology.key", "topology.value", "topology.class.bases",
        "topology.class.mro", "topology.class.label", "topology.list.item", "topology.lower.value"}


def test_native_topology_trace_serialization_cannot_hide_gc_mutation(native):
    guard = _guard()
    original = values.SCHEMA_TOPOLOGY_CONTRACT
    old_threshold, was_enabled = gc.get_threshold(), gc.isenabled()
    armed, changed = [False], []

    def callback(phase, _info):
        if phase == "start" and armed[0] and not changed:
            changed.append(True)
            values.SCHEMA_TOPOLOGY_CONTRACT = object()

    gc.callbacks.append(callback)
    try:
        # Explicit diagnostic collection runs INSIDE the native observer after
        # serialization, not a nondeterministic collection after C returns.
        gc.disable()
        armed[0] = True
        report = native.observe_topology(guard, guard.__code__, True)
        armed[0] = False
        assert changed and report["accepted"] is False
    finally:
        armed[0] = False
        gc.callbacks.remove(callback)
        gc.set_threshold(*old_threshold)
        if was_enabled:
            gc.enable()
        values.SCHEMA_TOPOLOGY_CONTRACT = original
    guard()


@pytest.mark.parametrize("module", ("preparation", "topology_values"))
@pytest.mark.parametrize("failure", ("missing_self", "missing_dependency", "import", "runtime"))
def test_present_native_loader_failure_never_selects_portable(module, failure):
    package = Path(values.__file__).parents[1]
    schema = Path(values.__file__).parents[5] / "meta" / "libs" / "type_schema" / "python"
    program = f'''
import importlib.abc, importlib.util, sys
sys.path[:0] = [{str(package)!r}, {str(schema)!r}]
name = "aware_ontology_object_facade_client._preparation_scan"
# Establish ordinary dependencies with the genuinely absent extension first.
# Execute each receiving module's actual bootstrap separately so the package's
# import order cannot hide preparation's own loader boundary behind topology's.
import aware_ontology_object_facade_client
class Loader(importlib.abc.Loader):
    def create_module(self, spec): return None
    def exec_module(self, module):
        failure = {failure!r}
        if failure.startswith("missing"):
            raise ModuleNotFoundError("native loader failed", name=name if failure == "missing_self" else "foreign_dependency")
        if failure == "import": raise ImportError("native loader failed")
        raise RuntimeError("native loader failed")
class Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == name: return importlib.util.spec_from_loader(name, Loader())
sys.meta_path.insert(0, Finder())
try:
    spec = importlib.util.spec_from_file_location("aware_ontology_object_facade_client.{module}", {str(package / 'aware_ontology_object_facade_client' / (module + '.py'))!r})
    candidate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(candidate)
except (ImportError, RuntimeError) as error:
    assert "native loader failed" in str(error), repr(error)
else:
    raise AssertionError("present native loader failure selected portable")
'''
    result = subprocess.run([sys.executable, "-I", "-c", program], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
