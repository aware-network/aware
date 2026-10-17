"""Real optional native builds; no installed image or operational authority."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SDK = Path(__file__).resolve().parents[1]
REPO = next(p for p in SDK.parents if (p / "aware.repo.toml").is_file())


def test_native_scope_preserves_all_other_original_definitions():
    relative = (
        SDK / "aware_workspace_sdk/repository_tree_projection_codec.py"
    ).relative_to(REPO)
    before = subprocess.run(
        [
            "git",
            "show",
            "13086d4cdde3cffe5b5457fc559fe1b3b5013d68:" + relative.as_posix(),
        ],
        cwd=REPO,
        capture_output=True,
        check=True,
    ).stdout
    assert hashlib.sha256(before).hexdigest() == (
        "9e5ccedfc5170f1547470244ebdb1f18a44f52dc690db6ec31f2049b7abb86f0"
    )
    after = (REPO / relative).read_bytes()

    def definitions(body):
        return {
            node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(body).body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        }

    old, new = definitions(before), definitions(after)
    assert old.keys() == new.keys()
    assert {name for name in old if old[name] != new[name]} == {
        "_compile_native_fields",
        "_wire",
        "_path",
    }
    for node in ast.walk(ast.parse(after)):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            assert not any(
                isinstance(target, ast.Attribute) and target.attr == "__code__"
                for target in targets
            )


@pytest.fixture(scope="module")
def native_sdk(tmp_path_factory):
    root = tmp_path_factory.mktemp("workspace-native-source")
    shutil.copytree(
        SDK / "aware_workspace_sdk",
        root / "aware_workspace_sdk",
        ignore=shutil.ignore_patterns("__pycache__", "*.so"),
    )
    shutil.copy2(SDK / "hatch_build.py", root / "hatch_build.py")
    build = subprocess.run(
        [
            sys.executable,
            str(root / "hatch_build.py"),
            "--output-directory",
            str(root / "aware_workspace_sdk"),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=130,
    )
    evidence = json.loads(build.stdout)
    (root / "build-evidence.json").write_text(build.stdout)
    if evidence["status"] != "compiled":
        pytest.skip(evidence["reason"])
    return root


def run_native(native_sdk: Path, body: str):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(native_sdk), environment.get("PYTHONPATH")))
    )
    prelude = f"""
from pathlib import Path
import sys, types, json, gc, weakref, importlib.util
from dataclasses import replace
from aware_workspace_sdk import repository_tree_projection_codec as codec
from aware_workspace_sdk import _tree_native as native
assert Path(codec.__file__).is_relative_to(Path({str(native_sdk)!r}))
assert Path(native.__file__).is_relative_to(Path({str(native_sdk)!r}))
assert codec._TREE_NATIVE_HANDOFF is not None
portable = types.ModuleType('aware_workspace_sdk._native_portable_control')
portable.__package__ = 'aware_workspace_sdk'
exec(compile(Path(codec.__file__).read_bytes(), '<portable-control>', 'exec'), vars(portable))
assert portable._TREE_NATIVE_HANDOFF is None
case_path = Path({str(SDK / "tests/test_repository_tree_projection_contract.py")!r})
spec = importlib.util.spec_from_file_location('native_original_contract_cases', case_path)
cases = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cases
spec.loader.exec_module(cases)
"""
    result = subprocess.run(
        [sys.executable, "-c", prelude + body],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def test_original_examples_have_exact_portable_wire(native_sdk):
    run_native(
        native_sdk,
        """
for value in cases.examples():
    actual = codec.repository_tree_projection_value_to_json(value)
    assert actual == portable.repository_tree_projection_value_to_json(value)
    assert codec.repository_tree_projection_value_from_json(type(value), actual) == value
""",
    )


def test_failed_rebuild_preserves_the_known_artifact(native_sdk, tmp_path):
    source = tmp_path / "source"
    shutil.copytree(native_sdk, source)
    artifact = next((source / "aware_workspace_sdk").glob("_tree_native*.so"))
    original = artifact.read_bytes()
    c_source = source / "aware_workspace_sdk/_tree_native.c"
    c_source.write_text(c_source.read_text() + "\nnot valid C;\n")
    result = subprocess.run(
        [
            sys.executable,
            str(source / "hatch_build.py"),
            "--output-directory",
            str(artifact.parent),
        ],
        capture_output=True,
        text=True,
        timeout=130,
        check=False,
    )
    assert result.returncode != 0
    assert "native metadata compilation failed" in result.stderr
    assert artifact.read_bytes() == original
    assert not list(artifact.parent.glob("workspace-tree-build-*"))


def test_identical_operands_execute_two_fresh_native_conversions(native_sdk):
    run_native(
        native_sdk,
        """
value = cases.binding()
original = native.convert_root
calls = []
def observe(frame, event, argument):
    if event == 'c_call' and argument is original:
        calls.append(True)
try:
    sys.setprofile(observe)
    codec.repository_tree_projection_value_validate_equal(value, expected_value=value)
finally:
    sys.setprofile(None)
assert len(calls) == 2, calls
""",
    )


@pytest.mark.parametrize("operand", ("actual", "expected"))
def test_each_operand_checks_fresh_fields(native_sdk, operand):
    run_native(
        native_sdk,
        f"""
left, right = cases.binding(), cases.binding()
selected = left if {operand!r} == 'actual' else right
before = replace(selected.files[0].before)
changed = replace(selected.files[0], before=before)
selected = replace(selected, files=(changed,))
left, right = (selected, right) if {operand!r} == 'actual' else (left, selected)
object.__setattr__(before, 'size_bytes', True)
try:
    codec.repository_tree_projection_value_validate_equal(left, expected_value=right)
except codec.WorkspaceTreeProjectionValueError as error:
    assert str(error) == 'tree primitive type differs'
else:
    raise AssertionError('fresh invalid operand accepted')
""",
    )


def test_outputs_are_detached_and_not_cached(native_sdk):
    run_native(
        native_sdk,
        """
value = cases.binding()
one = codec.repository_tree_projection_value_to_payload(value)
two = codec.repository_tree_projection_value_to_payload(value)
assert one == two and one is not two and one['files'] is not two['files']
one['files'][0]['path'] = 'changed/retained-output'
assert codec.repository_tree_projection_value_to_payload(value) == two
""",
    )


def test_original_unicode_error_context_is_preserved(native_sdk):
    run_native(
        native_sdk,
        """
value = replace(cases.binding(), plan_ref='invalid-\\ud800')
for implementation in (portable, codec):
    try:
        implementation.repository_tree_projection_value_to_payload(value)
    except implementation.WorkspaceTreeProjectionValueError as error:
        assert str(error) == 'tree text must be UTF-8'
        assert type(error.__context__) is UnicodeEncodeError
        assert error.__cause__ is None
    else:
        raise AssertionError('invalid UTF-8 accepted')
""",
    )


def test_context_is_nominal_and_sealing_is_once_only(native_sdk):
    run_native(
        native_sdk,
        """
context = native.new_context()
for create in (lambda: type(context)(), lambda: object.__new__(type(context))):
    try:
        create()
    except TypeError:
        pass
    else:
        raise AssertionError('private context constructed outside its factory')
try:
    native.seal(context, ())
except TypeError:
    pass
else:
    raise AssertionError('incomplete declaration accepted')
for call in (lambda: native.seal(context, ()), lambda: native.verify(context)):
    try:
        call()
    except RuntimeError:
        pass
    else:
        raise AssertionError('failed context resumed')
codec.repository_tree_projection_value_to_payload(cases.binding())
""",
    )


def test_changed_native_export_refuses_before_dispatch(native_sdk):
    run_native(
        native_sdk,
        """
original = native.convert_root
native.convert_root = object()
try:
    codec.repository_tree_projection_value_to_payload(cases.binding())
except codec.WorkspaceTreeProjectionValueError as error:
    assert 'native metadata export changed' in str(error)
else:
    raise AssertionError('changed component export accepted')
finally:
    native.convert_root = original
# The formatter carries no operation admission; a fresh valid value is usable.
codec.repository_tree_projection_value_to_payload(cases.binding())
""",
    )


def test_retained_code_does_not_retain_a_retired_module(native_sdk):
    run_native(
        native_sdk,
        """
name = 'aware_workspace_sdk._native_collection_control'
module = types.ModuleType(name)
module.__package__ = 'aware_workspace_sdk'
sys.modules[name] = module
exec(compile(Path(codec.__file__).read_bytes(), '<registered-native-clone>', 'exec'), vars(module))
assert module._TREE_NATIVE_HANDOFF is not None
context_ref = weakref.ref(module._TREE_NATIVE_HANDOFF[0])
module_ref = weakref.ref(module)
code = module._NATIVE_FIELDS_BY_ID[id(module.values.WorkspaceTreeProjectionBinding)][2][1]
del sys.modules[name]
del module
gc.collect()
assert module_ref() is None and context_ref() is None
assert code.co_name == 'convert'
""",
    )


def run_receipt_native(native_sdk: Path, body: str):
    runtime = (
        REPO / "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime"
    )
    prelude = f"""
import copy, dataclasses, subprocess
sys.path.insert(0, {str(runtime / "tests")!r})
from aware_workspace_runtime import change_evidence_codec as receipt
assert receipt._RECEIPT_NATIVE_HANDOFF is not None
receipt_path = 'workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/change_evidence_codec.py'
receipt_before = subprocess.run(['git', 'show', 'fbb8df6957a89a4b5b65db865910904e2cbdb96a:' + receipt_path], cwd={str(REPO)!r}, capture_output=True, check=True).stdout
baseline = types.ModuleType('aware_workspace_runtime._receipt_native_baseline')
baseline.__package__ = 'aware_workspace_runtime'
exec(compile(receipt_before, '<literal-receipt-native-predecessor>', 'exec'), vars(baseline))
import test_change_evidence_codec as receipt_cases

def outcome(module, value):
    try:
        return ('ok', json.dumps(module._encode(value, type(value)), sort_keys=True, separators=(',', ':'), ensure_ascii=False))
    except BaseException as error:
        return (type(error).__name__, str(error))
"""
    return run_native(native_sdk, prelude + body)


def test_native_receipt_complete_fields_preserve_portable_bytes_and_errors(native_sdk):
    run_receipt_native(
        native_sdk,
        """
items = [receipt_cases._evidence(receipt_cases.RepositoryEvidencePosture.PROVIDER_CORRELATED),
         receipt_cases._external(), receipt_cases._mutation_receipt(),
         *receipt_cases._diff_values(), receipt_cases._checkpoint(),
         receipt_cases.capture(), receipt_cases.content_delta(receipt_cases.capture())]
checks = 0
for value in items:
    assert outcome(receipt, value) == outcome(baseline, value)
    checks += 1
    for field in dataclasses.fields(value):
        for bad in (None, False, 0, '', (), object(), b'a'):
            changed = copy.copy(value)
            object.__setattr__(changed, field.name, bad)
            assert outcome(receipt, changed) == outcome(baseline, changed), field.name
            checks += 1
assert checks == 820, checks
""",
    )


def test_native_receipt_reads_changed_fields_after_prior_encoding(native_sdk):
    run_receipt_native(
        native_sdk,
        """
value = receipt_cases._mutation_receipt()
assert outcome(receipt, value) == outcome(baseline, value)
for field in dataclasses.fields(value):
    before = getattr(value, field.name)
    for successor in (None, 'changed', ('changed',)):
        object.__setattr__(value, field.name, successor)
        assert outcome(receipt, value) == outcome(baseline, value), field.name
    object.__setattr__(value, field.name, before)
""",
    )


def test_native_receipt_keeps_lazy_hints_and_schema_change_fallback(native_sdk):
    run_receipt_native(
        native_sdk,
        """
assert receipt._type_hints.cache_info().currsize == 0
assert receipt._encode.__annotations__ == baseline._encode.__annotations__
assert receipt._encode.__defaults__ == baseline._encode.__defaults__
assert receipt._encode.__kwdefaults__ == baseline._encode.__kwdefaults__
assert receipt._encode.__type_params__ == baseline._encode.__type_params__
value = receipt_cases._mutation_receipt()
cls = type(value)
original = cls.__dataclass_fields__
for mode in ('replace', 'reverse'):
    results = []
    for module in (baseline, receipt):
        module._type_hints.cache_clear()
        real = module._type_hints
        calls = []
        def hints(target):
            result = real(target)
            calls.append(target)
            if target is cls:
                cls.__dataclass_fields__ = dict(original) if mode == 'replace' else dict(reversed(tuple(original.items())))
            return result
        module._type_hints = hints
        try:
            results.append(outcome(module, value))
        finally:
            module._type_hints = real
            cls.__dataclass_fields__ = original
        assert calls.count(cls) == 1
    assert results[0] == results[1], mode
for module in (baseline, receipt):
    module._type_hints.cache_clear()
annotations = cls.__annotations__
previous = annotations['target_path']
try:
    annotations['target_path'] = tuple[str, ...]
    assert outcome(receipt, value) == outcome(baseline, value)
finally:
    annotations['target_path'] = previous
    baseline._type_hints.cache_clear()
    receipt._type_hints.cache_clear()
""",
    )


def test_native_receipt_context_is_collectable_with_code_retained(native_sdk):
    run_receipt_native(
        native_sdk,
        """
clone = types.ModuleType('aware_workspace_runtime._receipt_native_collection')
clone.__package__ = 'aware_workspace_runtime'
sys.modules[clone.__name__] = clone
exec(compile(Path(receipt.__file__).read_bytes(), '<original-receipt-clone>', 'exec'), vars(clone))
context = clone._RECEIPT_NATIVE_HANDOFF[0]
context_ref, module_ref = weakref.ref(context), weakref.ref(clone)
code = clone._encode.__code__
del sys.modules[clone.__name__]
del context, clone
for _ in range(3): gc.collect()
assert context_ref() is None
assert module_ref() is None
assert code.co_name == '_encode'
""",
    )


def test_native_receipt_export_refuses_before_changed_dispatch(native_sdk):
    run_receipt_native(
        native_sdk,
        """
value = receipt_cases._mutation_receipt()
original = native.convert_receipt
calls = []
def foreign(*args):
    calls.append(True)
    return {}
native.convert_receipt = foreign
try:
    try:
        receipt.repository_mutation_receipt_payload(value)
    except TypeError as error:
        assert 'original native receipt export' in str(error)
    else:
        raise AssertionError('changed native export accepted')
finally:
    native.convert_receipt = original
assert calls == []
assert outcome(receipt, value) == outcome(baseline, value)
""",
    )


def test_native_receipt_context_is_nominal_and_sealed_once(native_sdk):
    run_receipt_native(
        native_sdk,
        """
for context in (None, object(), native.new_context()):
    try: native.convert_receipt(context, None, (), {}, {})
    except TypeError: pass
    else: raise AssertionError('foreign receipt context accepted')
context = native.new_receipt_context()
try: type(context)()
except TypeError: pass
else: raise AssertionError('public receipt constructor')
try: native.seal_receipts(context, ())
except TypeError: pass
else: raise AssertionError('incomplete receipt declaration accepted')
try: native.seal_receipts(context, ())
except RuntimeError: pass
else: raise AssertionError('failed receipt seal resumed')
""",
    )


@pytest.mark.parametrize("missing", ["module", "helpers", "all", "partial"])
def test_native_receipt_supported_older_images_keep_portable_fallback(
    native_sdk, missing
):
    run_receipt_native(
        native_sdk,
        f"""
from aware_workspace_sdk import _tree_native_binding as binding
missing = {missing!r}
name = 'aware_workspace_runtime._receipt_older_image'
clone = types.ModuleType(name)
clone.__package__ = 'aware_workspace_runtime'
sys.modules[name] = clone
module_name = 'aware_workspace_sdk._tree_native_binding'
old_module = sys.modules[module_name]
old_prepare, old_seal = binding.prepare_receipts, binding.seal_receipts
native_names = ('new_receipt_context', 'convert_receipt', 'seal_receipts', 'receipt_prelude')
old_exports = {{key: vars(native)[key] for key in native_names}}
try:
    if missing == 'module':
        sys.modules[module_name] = None
    elif missing == 'helpers':
        del binding.prepare_receipts, binding.seal_receipts
    elif missing == 'all':
        for key in native_names: delattr(native, key)
    else:
        del native.receipt_prelude
    exec(compile(Path(receipt.__file__).read_bytes(), '<supported-older-image>', 'exec'), vars(clone))
    assert clone._RECEIPT_NATIVE_HANDOFF is None
    assert outcome(clone, receipt_cases._mutation_receipt()) == outcome(baseline, receipt_cases._mutation_receipt())
finally:
    sys.modules[module_name] = old_module
    binding.prepare_receipts, binding.seal_receipts = old_prepare, old_seal
    for key, value in old_exports.items(): setattr(native, key, value)
    del sys.modules[name]
""",
    )


def test_canonical_index_memo_preserves_every_fresh_record_and_exact_integers(
    native_sdk,
):
    run_receipt_native(
        native_sdk,
        """
from aware_workspace_sdk import _tree_native_binding as binding
context = binding._STORE_JSON_HANDOFF[0]
assert native.INDEX_FORMATTER_ABI == 1
row = receipt.repository_mutation_receipt_payload(receipt_cases._mutation_receipt())
def root(rows):
    return {'contract_ref':'c','contract_version':'1','repository_binding_ref':'r','records':rows}
values = [None, False, True, 0, -2**63, 2**64, 2**80, -2**80, 1.25,
          float('nan'), 'é', '😀', '\\ud800', 'x\\n"\\\\']
for value in values:
    payload = root([{'value': value}, row])
    assert native.call_index_formatter(context, json.dumps, payload, json) == json.dumps(payload, sort_keys=True, separators=(',', ':'))
for field in tuple(row['value']):
    original = row['value'][field]
    for changed in (None, 'changed', ['new'], 2**64):
        row['value'][field] = changed
        payload = root([row, row])
        assert native.call_index_formatter(context, json.dumps, payload, json) == json.dumps(payload, sort_keys=True, separators=(',', ':'))
    row['value'][field] = original
stats = native.index_formatter_stats(context)
assert stats['hits'] > 0
assert stats['charged_bytes'] <= 16 * 1024 * 1024
assert stats['entries'] <= 4096
""",
    )


def test_canonical_formatter_keeps_selected_callee_and_keyword_order(native_sdk):
    run_receipt_native(
        native_sdk,
        """
from aware_workspace_sdk import _tree_native_binding as binding
context = binding._STORE_JSON_HANDOFF[0]
calls = []
def selected(value, **kwargs):
    calls.append((value, tuple(kwargs.items())))
    return 'selected-original'
value = object()
assert native.call_index_formatter(context, selected, value, json) == 'selected-original'
assert calls == [(value, (('sort_keys', True), ('separators', (',', ':'))))]
class Stop(BaseException): pass
failure = Stop('original selected interruption')
def interrupted(value, **kwargs):
    raise failure
try: native.call_index_formatter(context, interrupted, value, json)
except Stop as error: assert error is failure
else: raise AssertionError('selected interruption lost')
""",
    )


def test_canonical_factory_declines_cold_custom_code_and_defaults(native_sdk):
    run_receipt_native(
        native_sdk,
        """
original = json.dumps
calls = []
def custom(value, **kwargs):
    calls.append(value)
    return original(value, **kwargs) + ' '
json.dumps = custom
try:
    assert native.make_index_formatter(json, json.encoder, 1, 1, 16777216) is None
finally:
    json.dumps = original
assert calls == []
original_defaults = json.dumps.__kwdefaults__
try:
    json.dumps.__kwdefaults__ = {**original_defaults, 'cls': object}
    assert native.make_index_formatter(json, json.encoder, 1, 1, 16777216) is None
finally:
    json.dumps.__kwdefaults__ = original_defaults
assert native.make_index_formatter(json, json.encoder, 1, 1, 16777216) is not None
""",
    )


def test_canonical_context_is_gc_visible_and_does_not_retain_dto_graphs(native_sdk):
    run_receipt_native(
        native_sdk,
        """
clone = types.ModuleType('json_profile_collection_clone')
vars(clone).update(vars(json))
clone.dumps = types.FunctionType(json.dumps.__code__, vars(clone), json.dumps.__name__, json.dumps.__defaults__)
clone.dumps.__kwdefaults__ = json.dumps.__kwdefaults__
context = native.make_index_formatter(clone, json.encoder, 1, 1, 16777216)
assert context is not None
context_ref, clone_ref = weakref.ref(context), weakref.ref(clone)
clone.retained_context_cycle = context
del context, clone
for _ in range(3): gc.collect()
assert context_ref() is None and clone_ref() is None
context = native.make_index_formatter(json, json.encoder, 1, 1, 0)
for i in range(10):
    value = {'contract_ref':'c','contract_version':'1','repository_binding_ref':'r','records':[{'ordinal': i}]}
    assert native.call_index_formatter(context, json.dumps, value, json) == json.dumps(value, sort_keys=True, separators=(',', ':'))
assert native.index_formatter_stats(context)['charged_bytes'] == 0
assert native.index_formatter_stats(context)['entries'] == 0
""",
    )


def test_store_methods_share_one_formatter_and_keep_portable_older_sdk(native_sdk):
    run_receipt_native(
        native_sdk,
        """
from aware_workspace_sdk import _tree_native_binding as binding
from aware_workspace_fs_adapter import repository_mutation_store as mutations
from aware_workspace_fs_adapter import repository_delta_store as deltas
assert mutations._STORE_NATIVE_HANDOFF is binding._STORE_JSON_HANDOFF
assert deltas._STORE_NATIVE_HANDOFF is binding._STORE_JSON_HANDOFF
assert mutations.WorkspaceRepositoryMutationStore._persist.__name__ == '_persist'
assert deltas.WorkspaceRepositoryDeltaStore._persist_index.__name__ == '_persist_index'
module_name = 'aware_workspace_sdk._tree_native_binding'
original_module = sys.modules[module_name]
try:
    sys.modules[module_name] = None
    for original in (mutations, deltas):
        clone = types.ModuleType(original.__name__ + '_older_sdk')
        clone.__package__ = original.__package__
        sys.modules[clone.__name__] = clone
        try:
            exec(compile(Path(original.__file__).read_bytes(), '<store-older-sdk>', 'exec'), vars(clone))
            assert clone._STORE_NATIVE_HANDOFF is None
        finally:
            del sys.modules[clone.__name__]
finally:
    sys.modules[module_name] = original_module
abi = native.INDEX_FORMATTER_ABI
try:
    native.INDEX_FORMATTER_ABI = 0
    assert binding._prepare_store_json_native() is None
finally:
    native.INDEX_FORMATTER_ABI = abi
""",
    )


@pytest.mark.parametrize(
    "change", ["class", "constructor", "lookup", "factory", "infinity"]
)
def test_canonical_factory_declines_custom_encoder_behavior_before_callbacks(
    native_sdk, change
):
    run_receipt_native(
        native_sdk,
        f"""
change = {change!r}
original_class = json.JSONEncoder
original_init = json.JSONEncoder.__init__
original_factory = json.encoder.c_make_encoder
original_infinity = json.encoder.INFINITY
calls = []
class Custom(original_class):
    def __init__(self, *args, **kwargs):
        calls.append('constructor')
        super().__init__(*args, **kwargs)
def constructor(self, *args, **kwargs):
    calls.append('constructor')
    return original_init(self, *args, **kwargs)
def lookup(self, name):
    calls.append('lookup')
    return object.__getattribute__(self, name)
class Factory:
    def __call__(self, *args, **kwargs):
        calls.append('factory')
        return []
class Infinity:
    def __neg__(self):
        calls.append('negative')
        return self
try:
    if change == 'class': json.JSONEncoder = Custom
    elif change == 'constructor': json.JSONEncoder.__init__ = constructor
    elif change == 'lookup': json.JSONEncoder.__getattribute__ = lookup
    elif change == 'factory': json.encoder.c_make_encoder = Factory
    else: json.encoder.INFINITY = Infinity()
    assert native.make_index_formatter(json, json.encoder, 1, 1, 16777216) is None
    assert calls == []
finally:
    json.JSONEncoder = original_class
    json.JSONEncoder.__init__ = original_init
    if '__getattribute__' in vars(original_class): del original_class.__getattribute__
    json.encoder.c_make_encoder = original_factory
    json.encoder.INFINITY = original_infinity
""",
    )


def test_canonical_memo_bounds_entries_and_reclaims_previous_formatting(native_sdk):
    run_receipt_native(
        native_sdk,
        """
context = native.make_index_formatter(json, json.encoder, 1, 1, 16777216)
for ordinal in range(4205):
    value = {'contract_ref':'c','contract_version':'1','repository_binding_ref':'r','records':[{'ordinal':ordinal}]}
    assert native.call_index_formatter(context, json.dumps, value, json) == json.dumps(value, sort_keys=True, separators=(',', ':'))
stats = native.index_formatter_stats(context)
assert stats['entries'] == 4096
assert stats['charged_bytes'] <= 16777216
context = native.make_index_formatter(json, json.encoder, 1, 1, 32768)
for ordinal in range(80):
    value = {'contract_ref':'c','contract_version':'1','repository_binding_ref':'r','records':[{'ordinal':ordinal, 'text':'x'*4096}]}
    assert native.call_index_formatter(context, json.dumps, value, json) == json.dumps(value, sort_keys=True, separators=(',', ':'))
stats = native.index_formatter_stats(context)
assert 0 < stats['entries'] < 80
assert stats['charged_bytes'] <= 32768
""",
    )


@pytest.mark.parametrize("change", ["cloned_globals", "builtin_shadow"])
def test_canonical_factory_declines_unqualified_function_resolution(native_sdk, change):
    run_receipt_native(
        native_sdk,
        f"""
change = {change!r}
original = json.dumps
calls = []
def alternate(*args):
    calls.append(True)
    return False
try:
    if change == 'cloned_globals':
        json.dumps = types.FunctionType(original.__code__, dict(original.__globals__), original.__name__, original.__defaults__)
        json.dumps.__kwdefaults__ = original.__kwdefaults__
    else:
        json.encoder.isinstance = alternate
    assert native.make_index_formatter(json, json.encoder, 1, 1, 16777216) is None
    assert calls == []
finally:
    json.dumps = original
    if 'isinstance' in vars(json.encoder): del json.encoder.isinstance
""",
    )


def test_original_delta_store_enters_native_composition_and_reopens(native_sdk):
    run_receipt_native(
        native_sdk,
        """
from tempfile import TemporaryDirectory
from aware_workspace_sdk import _tree_native_binding as binding
from aware_workspace_fs_adapter.repository_delta_store import WorkspaceRepositoryDeltaStore
context = binding._STORE_JSON_HANDOFF[0]
before = native.index_formatter_stats(context)
with TemporaryDirectory() as directory:
    root = Path(directory)
    store = WorkspaceRepositoryDeltaStore(repository_binding_ref='repository:native-delta-control', state_root=root)
    first = store.record_body(b'first exact body')
    second = store.record_body(b'second exact body')
    store._persist_index()
    path = store.store_root / 'index.json'
    raw = path.read_bytes()
    payload = json.loads(raw)
    assert tuple(payload) == ('bodies', 'captures', 'contract_ref', 'deltas', 'repository_binding_ref', 'sequence', 'version')
    assert raw == (json.dumps(payload, sort_keys=True, separators=(',', ':')) + '\\n').encode()
    reopened = WorkspaceRepositoryDeltaStore(repository_binding_ref='repository:native-delta-control', state_root=root)
    assert reopened.resolve_body(first) == b'first exact body'
    assert reopened.resolve_body(second) == b'second exact body'
after = native.index_formatter_stats(context)
assert after['misses'] > before['misses']
assert after['hits'] > before['hits']
assert after['fallbacks'] == before['fallbacks'], (before, after)
""",
    )


def test_original_mutation_resolves_stream_write_before_serializer(native_sdk):
    run_receipt_native(
        native_sdk,
        """
from tempfile import TemporaryDirectory
from aware_workspace_fs_adapter import repository_mutation_store as mutations
calls = []
error = OSError('original stream lookup failed')
class Stream:
    def __enter__(self): return self
    def __exit__(self, *args): return False
    @property
    def write(self):
        calls.append('write lookup')
        raise error
original_fdopen, original_dumps = mutations.os.fdopen, json.dumps
def fdopen(descriptor, *args, **kwargs):
    mutations.os.close(descriptor)
    return Stream()
def dumps(*args, **kwargs):
    calls.append('serializer')
    return original_dumps(*args, **kwargs)
with TemporaryDirectory() as directory:
    store = mutations.WorkspaceRepositoryMutationStore(repository_binding_ref='repository:write-order', state_root=Path(directory))
    mutations.os.fdopen = fdopen
    json.dumps = dumps
    try:
        try: store._persist()
        except OSError as actual: assert actual is error
        else: raise AssertionError('stream error lost')
    finally:
        mutations.os.fdopen, json.dumps = original_fdopen, original_dumps
assert calls == ['write lookup'], calls
""",
    )


def test_mutation_payload_failure_releases_uninvoked_selected_serializer(native_sdk):
    run_receipt_native(
        native_sdk,
        """
from tempfile import TemporaryDirectory
from aware_workspace_fs_adapter import repository_mutation_store as mutations
class Serializer:
    def __call__(self, *args, **kwargs):
        raise AssertionError('serializer must not run before failed receipt conversion')
original = json.dumps
selected = Serializer()
reference = weakref.ref(selected)
held = None
with TemporaryDirectory() as directory:
    store = mutations.WorkspaceRepositoryMutationStore(repository_binding_ref='repository:payload-failure', state_root=Path(directory))
    store._records['invalid-receipt'] = ('fingerprint', object())
    json.dumps = selected
    try:
        try: store._persist()
        except BaseException as error: held = error
        else: raise AssertionError('invalid receipt accepted')
    finally:
        json.dumps = original
    assert held is not None and not isinstance(held, AssertionError)
    del selected
    gc.collect()
    assert reference() is None
assert held is not None
""",
    )


def test_tree_wire_profile_matches_portable_bytes_and_refusals(native_sdk):
    run_native(
        native_sdk,
        """
assert codec._TREE_JSON_ACTIVE
assert native.TREE_FORMATTER_ABI == 1
samples = [None, False, True, 0, 2**64, 2**80, 1.25, float('nan'), 'é', '😀', '\\ud800', {'z':[None, {'é':'😀'}]}, object(), b'a']
cycle = []
cycle.append(cycle)
samples.append(cycle)
def result(function, value):
    try: return ('ok', function(value))
    except BaseException as error: return (type(error).__name__, str(error), type(error.__context__).__name__)
for value in samples:
    for _ in range(2): assert result(codec._wire, value) == result(portable._wire, value)
for value in cases.examples():
    assert codec.repository_tree_projection_value_to_json(value) == portable.repository_tree_projection_value_to_json(value)
""",
    )


def test_tree_and_store_profiles_share_budget_without_text_aliasing(native_sdk):
    run_receipt_native(
        native_sdk,
        """
from aware_workspace_sdk import _tree_native_binding as binding
context = binding._STORE_JSON_HANDOFF[0]
assert codec._TREE_JSON_HANDOFF is binding._STORE_JSON_HANDOFF
value = {'contract_ref':'c','contract_version':'1','repository_binding_ref':'r','records':[{'path':'é/😀'}]}
store_expected = json.dumps(value,sort_keys=True,separators=(',',':'))
tree_expected = json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':'))
assert store_expected != tree_expected
for _ in range(3):
    assert native.call_index_formatter(context,json.dumps,value,json) == store_expected
    assert native.call_tree_formatter(context,json.dumps,value,json) == tree_expected
value['records'][0]['path'] = 'changed fresh value'
assert native.call_tree_formatter(context,json.dumps,value,json) == json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':'))
stats = native.index_formatter_stats(context)
assert stats['hits'] > 0 and stats['charged_bytes'] <= 16777216 and stats['entries'] <= 4096
""",
    )


def test_tree_formatter_preserves_original_selected_keywords(native_sdk):
    run_native(
        native_sdk,
        """
from aware_workspace_sdk import _tree_native_binding as binding
context = binding._STORE_JSON_HANDOFF[0]
calls = []
value = object()
def selected(payload, **kwargs):
    calls.append((payload, tuple(kwargs.items())))
    return 'original selected text'
assert native.call_tree_formatter(context,selected,value,json) == 'original selected text'
assert calls == [(value,(('ensure_ascii',False),('allow_nan',False),('sort_keys',True),('separators',(',',':'))))]
""",
    )


@pytest.mark.parametrize("missing", ["export", "abi"])
def test_tree_formatter_older_image_keeps_original_wire_definition(native_sdk, missing):
    run_native(
        native_sdk,
        f"""
from aware_workspace_sdk import _tree_native_binding as binding
clone = types.ModuleType('aware_workspace_sdk._older_tree_profile')
clone._wire = portable._wire
clone._TREE_JSON_ACTIVE = False
sys.modules[clone.__name__] = clone
name = 'call_tree_formatter' if {missing!r} == 'export' else 'TREE_FORMATTER_ABI'
original = getattr(native, name)
try:
    delattr(native, name)
    assert binding.bind_tree_json(vars(clone)) is None
    assert clone._wire is portable._wire and clone._TREE_JSON_ACTIVE is False
finally:
    setattr(native, name, original)
    del sys.modules[clone.__name__]
""",
    )


def test_direct_key_renderer_preserves_unicode_sorting_and_complete_stock_text(
    native_sdk,
):
    run_native(
        native_sdk,
        """
import random
from aware_workspace_sdk import _tree_native_binding as binding
context = binding._STORE_JSON_HANDOFF[0]
rng = random.Random(20261015)
characters = ''.join(chr(i) for i in range(128)) + 'éÿĀǿ\\ud7ff\\ud800\\udfff\\ue000\\uffff𐀀😀\\U0010ffff'
values = [None, False, True, 0, -2**63, 2**63-1, 2**63, 2**64-1, 2**64]
for repeat in range(600):
    keys = [''.join(rng.choice(characters) for _ in range(rng.randrange(0,24))) for _ in range(8)]
    scalar = rng.choice(values)
    text = ''.join(rng.choice(characters) for _ in range(80))
    payload = {key:[text,scalar,{'z':None,'a':repeat}] for key in reversed(keys)}
    expected = json.dumps(payload,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':'))
    for _ in range(2): assert native.call_tree_formatter(context,json.dumps,payload,json) == expected
large = {str(i):i for i in range(8193)}
before = native.index_formatter_stats(context)
assert native.call_tree_formatter(context,json.dumps,large,json) == json.dumps(large,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':'))
after = native.index_formatter_stats(context)
assert after['tree_fallbacks'] == before['tree_fallbacks']+1
""",
    )


@pytest.fixture(scope="module")
def diagnostic_sdk(native_sdk, tmp_path_factory):
    root = tmp_path_factory.mktemp("workspace-native-clock-source")
    shutil.copytree(
        native_sdk,
        root,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.so"),
    )
    build = subprocess.run(
        [
            sys.executable,
            str(root / "hatch_build.py"),
            "--output-directory",
            str(root / "aware_workspace_sdk"),
            "--diagnostic-counters",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=130,
    )
    evidence = json.loads(build.stdout)
    (root / "diagnostic-build-evidence.json").write_text(build.stdout)
    assert evidence["status"] == "compiled" and evidence["diagnostic_counters"] is True
    assert "-DWORKSPACE_FORMATTER_COSTS=1" in evidence["command"]
    return root


def test_default_image_has_no_diagnostic_clock_methods(native_sdk):
    run_native(
        native_sdk,
        """
assert not hasattr(native, 'read_cost_counters')
assert not hasattr(native, 'reset_cost_counters')
""",
    )


def test_diagnostic_image_counts_both_original_operands_and_native_json(diagnostic_sdk):
    run_receipt_native(
        diagnostic_sdk,
        """
left, right = cases.binding(), cases.binding()
native.reset_cost_counters()
empty = native.read_cost_counters()
assert all(row['calls']==0 for name,row in empty.items() if name!='diagnostics')
codec.repository_tree_projection_value_validate_equal(left,expected_value=right)
context = codec._TREE_JSON_HANDOFF[0]
assert native.call_tree_formatter(context,json.dumps,{'positive':'é'},json) == '{"positive":"é"}'
rows = native.read_cost_counters()
assert rows['tree_fields_and_nested_semantics']['calls'] >= 2
assert rows['tree_canonical_formatting']['calls'] > 0
assert rows['diagnostics'] == {'clock_errors':0,'nesting_overflow':0}
for name,row in rows.items():
    if name != 'diagnostics': assert 0 <= row['exclusive_marked_thread_cpu_ns'] <= row['inclusive_thread_cpu_ns']
class OriginalFailure(BaseException): pass
error = OriginalFailure('same diagnostic failure')
def selected(*args,**kwargs): raise error
try: native.call_tree_formatter(context,selected,object(),json)
except OriginalFailure as caught: assert caught is error
else: raise AssertionError('original exception lost')
native.reset_cost_counters()
assert all(row['calls']==0 for name,row in native.read_cost_counters().items() if name!='diagnostics')
""",
    )


def test_native_graph_uses_original_lazy_hints_and_fresh_nested_records(native_sdk):
    run_receipt_native(
        native_sdk,
        """
assert native.RECEIPT_DIRECT_RECORD_ABI == 1
value = receipt_cases._mutation_receipt()
before = native.receipt_graph_stats()
assert outcome(receipt,value) == outcome(baseline,value)
after = native.receipt_graph_stats()
assert after['direct_records'] > before['direct_records'], (before,after)
changed = copy.copy(value.expected_coordinate)
object.__setattr__(changed, "state_digest", "changed-fresh-state")
changed_value = copy.copy(value)
object.__setattr__(changed_value, "expected_coordinate", changed)
assert outcome(receipt,changed_value) == outcome(baseline,changed_value)
assert receipt._type_hints.cache_info().currsize > 0
""",
    )


def test_graph_metadata_movement_after_hints_uses_original_continuation_once(
    native_sdk,
):
    run_receipt_native(
        native_sdk,
        """
value = receipt_cases._mutation_receipt()
cls = type(value.expected_coordinate)
original_fields = cls.__dataclass_fields__
outputs = []
counts = []
before = native.receipt_graph_stats()
for module in (receipt,baseline):
    if cls.__dataclass_fields__ is not original_fields:
        cls.__dataclass_fields__ = original_fields
    module._type_hints.cache_clear()
    original = module.get_type_hints
    calls = []
    def hints(target):
        calls.append(target)
        if target is cls:
            cls.__dataclass_fields__ = dict(reversed(tuple(original_fields.items())))
        return original(target)
    module.get_type_hints = hints
    try:
        outputs.append(module._encode(value,type(value)))
        counts.append(calls.count(cls))
    finally:
        module.get_type_hints = original
        cls.__dataclass_fields__ = original_fields
assert outputs[0] == outputs[1]
assert tuple(outputs[0]['expected_coordinate']) == tuple(outputs[1]['expected_coordinate'])
assert counts == [1,1], counts
# The byte/membership/order parity remains required even if metadata restoration
# conservatively disqualifies the positive path for the second observation.
assert native.receipt_graph_stats()['posthint_continuations'] > before['posthint_continuations']
""",
    )


def test_new_runtime_with_older_receipt_image_keeps_original_record_path(native_sdk):
    run_receipt_native(
        native_sdk,
        """
name = 'aware_workspace_runtime._supported_legacy_receipt_image'
clone = types.ModuleType(name)
clone.__package__ = 'aware_workspace_runtime'
sys.modules[name] = clone
abi = native.RECEIPT_DIRECT_RECORD_ABI
try:
    del native.RECEIPT_DIRECT_RECORD_ABI
    exec(compile(Path(receipt.__file__).read_bytes(),'<legacy-receipt-capability>','exec'),vars(clone))
    value = receipt_cases._mutation_receipt()
    before = native.receipt_graph_stats()
    assert outcome(clone,value) == outcome(baseline,value)
    assert native.receipt_graph_stats()['direct_records'] == before['direct_records']
finally:
    native.RECEIPT_DIRECT_RECORD_ABI = abi
    del sys.modules[name]
""",
    )


@pytest.mark.parametrize("change", ["defaults", "registry"])
def test_graph_revalidates_original_entry_after_lazy_hints(native_sdk, change):
    run_receipt_native(
        native_sdk,
        f"""
value = receipt_cases._mutation_receipt()
cls = type(value.expected_coordinate)
results = []
for module in (receipt,baseline):
    module._type_hints.cache_clear()
    entry = module._RECEIPT_FIELDS_BY_ID[id(cls)]
    converter = entry[2][0]
    defaults = converter.__defaults__
    original = module.get_type_hints
    calls = []
    def hints(target):
        result = original(target)
        if target is cls:
            calls.append(target)
            if {change!r} == 'defaults': converter.__defaults__ = ()
            else: module._RECEIPT_FIELDS_BY_ID[id(cls)] = tuple(list(entry))
        return result
    module.get_type_hints = hints
    try:
        results.append(outcome(module,value))
        assert calls == [cls], calls
    finally:
        module.get_type_hints = original
        module._RECEIPT_FIELDS_BY_ID[id(cls)] = entry
        converter.__defaults__ = defaults
assert results[0] == results[1], results
assert results[0][0] == 'TypeError', results
""",
    )


def test_graph_missing_optional_wrapper_metadata_uses_original_callable(native_sdk):
    run_receipt_native(
        native_sdk,
        """
value = receipt_cases._mutation_receipt()
wrapper = receipt._type_hints
inner = wrapper.__wrapped__
del wrapper.__wrapped__
try:
    assert outcome(receipt,value) == outcome(baseline,value)
finally:
    wrapper.__wrapped__ = inner
""",
    )


@pytest.mark.parametrize("when", ["before", "after"])
def test_graph_authenticates_continuation_at_its_actual_dispatch(native_sdk, when):
    run_receipt_native(
        native_sdk,
        f"""
value = receipt_cases._mutation_receipt()
cls = type(value.expected_coordinate)
metadata = cls.__dataclass_fields__
original_hints = receipt.get_type_hints
continuation = receipt._encode_record_after_hints
calls = []
def foreign(*args,**kwargs):
    calls.append('foreign')
    raise AssertionError('foreign continuation ran')
def hints(target):
    result = original_hints(target)
    if target is cls:
        cls.__dataclass_fields__ = dict(reversed(tuple(metadata.items())))
        if {when!r} == 'before': receipt._encode_record_after_hints = foreign
    return result
original_fields = receipt.fields
def fields(target):
    result = original_fields(target)
    if target is cls and {when!r} == 'after': receipt._encode_record_after_hints = foreign
    return result
receipt._type_hints.cache_clear()
receipt.get_type_hints = hints
receipt.fields = fields
try:
    result = outcome(receipt,value)
    assert result[0]=='TypeError',result
    assert calls==[],calls
finally:
    receipt.get_type_hints = original_hints
    receipt.fields = original_fields
    receipt._encode_record_after_hints = continuation
    cls.__dataclass_fields__ = metadata
""",
    )


@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
@pytest.mark.parametrize("key_kind", ["general", "string_subclass"])
def test_identifier_lookup_preserves_general_key_allocation_and_errors(
    diagnostic_sdk, mode, key_kind
):
    run_native(
        diagnostic_sdk,
        f"""
assert hasattr(native, 'literal_lookup_probe')
results = []
for original in (True, False):
    seen = []
    value = object()
    class Key(str if {key_kind!r} == 'string_subclass' else object):
        def __new__(cls):
            return str.__new__(cls,'values') if {key_kind!r} == 'string_subclass' else object.__new__(cls)
        def __hash__(self): return hash('values')
        def __eq__(self, other):
            seen.append(other)
            if {mode!r} == 'raise': raise OSError('same lookup failure')
            if {mode!r} == 'restore': mapping['after'] = value
            return other == 'values'
    mapping = {{Key(): value}}
    answers = [native.literal_lookup_probe(mapping,original) for _ in range(2)]
    assert len(seen) == 2,seen
    assert all(type(v) is str and v == 'values' for v in seen)
    assert seen[0] is not seen[1], 'general-key lookup must retain fresh original names'
    results.append([v is value for v in answers])
assert results[0] == results[1],results
assert results[0] == ([False,False] if {mode!r} == 'raise' else [True,True])
# Exact Unicode-only tables still observe replacement and deletion freshly.
mapping = {{'values': 1}}
assert native.literal_lookup_probe(mapping,False) == 1
mapping['values'] = 2
assert native.literal_lookup_probe(mapping,False) == 2
del mapping['values']
assert native.literal_lookup_probe(mapping,False) is None
""",
    )


def test_receipt_slot_reads_preserve_deleted_and_changed_values(native_sdk):
    run_receipt_native(
        native_sdk,
        """
value = receipt_cases._mutation_receipt()
for field in dataclasses.fields(value):
    changed = copy.copy(value)
    object.__delattr__(changed, field.name)
    assert outcome(receipt, changed) == outcome(baseline, changed), field.name
    if field.name != 'physical_effect':
        changed = copy.copy(value)
        object.__setattr__(changed, field.name, 'fresh-after-prior-read')
        assert outcome(receipt, changed) == outcome(baseline, changed), field.name
assert outcome(receipt, value) == outcome(baseline, value)
""",
    )


@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_receipt_slot_declaration_movement_during_flag_snapshot(native_sdk, mode):
    run_receipt_native(
        native_sdk,
        f"""
mode = {mode!r}
value = receipt_cases._mutation_receipt()
cls = type(value)
original_slot = vars(cls)['target_path']
original_flag = vars(dataclasses.Field)['_field_type']
first_field = dataclasses.fields(cls)[0]
outputs = []
for module in (receipt, baseline):
    armed = [True]
    calls = []
    def selected(instance):
        calls.append(mode)
        if mode == 'restore':
            setattr(cls, 'target_path', original_slot)
        if mode == 'raise':
            raise LookupError('same original slot failure')
        return original_slot.__get__(instance, cls) + '-fresh-projection'
    def flag(field):
        if field is first_field and armed[0]:
            armed[0] = False
            setattr(cls, 'target_path', property(selected))
        return original_flag.__get__(field, type(field))
    setattr(dataclasses.Field, '_field_type', property(flag))
    try:
        outputs.append((outcome(module, value), tuple(calls)))
    finally:
        setattr(cls, 'target_path', original_slot)
        setattr(dataclasses.Field, '_field_type', original_flag)
assert outputs[0] == outputs[1], outputs
assert outputs[0][1] == (mode,), outputs
""",
    )


def test_receipt_slot_reads_preserve_changed_getattribute(native_sdk):
    run_receipt_native(
        native_sdk,
        """
value = receipt_cases._mutation_receipt()
cls = type(value)
outputs = []
for module in (receipt, baseline):
    seen = []
    def access(instance, name):
        seen.append(name)
        result = object.__getattribute__(instance, name)
        return result + '-fresh-access' if name == 'target_path' else result
    cls.__getattribute__ = access
    try:
        outputs.append((outcome(module, value), tuple(seen)))
    finally:
        del cls.__getattribute__
assert outputs[0] == outputs[1], outputs
assert 'target_path' in outputs[0][1]
""",
    )


def test_native_preparation_copy_runs_original_parity_and_owner_controls(native_sdk):
    run_receipt_native(
        native_sdk,
        f"""
import inspect, os
from aware_workspace_runtime import repository_tree_preparation_copy as preparation
handoff = inspect.getclosurevars(preparation.copy_preparation_observation).nonlocals['native_handoff']
assert handoff is not None and handoff[1] is native.copy_preparation
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
import pytest
code = pytest.main(['-q', '-c', '/dev/null', '--import-mode=importlib',
                   '-p', 'pytest_asyncio.plugin', '-p', 'no:cacheprovider',
                   {str(REPO / "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_tree_preparation_copy_optimization.py")!r}])
assert code == 0, code
""",
    )


@pytest.mark.parametrize("entry", ("fields", "walk", "converter", "unknown"))
def test_native_preparation_dispatch_substitution_is_not_executed(native_sdk, entry):
    run_receipt_native(
        native_sdk,
        f"""
import inspect
from aware_workspace_runtime import repository_tree_preparation_copy as preparation
from aware_file_system.confined_mutation import ConfinedTreeEntryPin
copy_value = preparation.copy_preparation_observation
variables = inspect.getclosurevars(copy_value).nonlocals
context, original_native = variables['native_handoff']
walk = variables['walk']
walk_variables = inspect.getclosurevars(walk).nonlocals
entry = {entry!r}
if entry == 'fields': target = walk_variables['original_fields']
elif entry == 'walk': target = walk
elif entry == 'unknown': target = walk_variables['copy_unknown']
else: target = walk_variables['converters'][1][2]
original = target.__code__
# The finite fields/converter functions have no closure. Match walk's own
# closure arity when checking its genuine dispatch rather than replacing it.
text = 'def outer():\\n' + ''.join('    f'+str(i)+'=None\\n' for i in range(len(original.co_freevars)))
text += '    def foreign(*args,**kwargs):\\n        held=('
text += ''.join('f'+str(i)+',' for i in range(len(original.co_freevars)))
text += ')\\n        raise AssertionError("foreign preparation delegate executed")\\n    return foreign\\n'
namespace={{}}
exec(compile(text,'<preparation-delegate-control>','exec'),{{}},namespace)
target.__code__ = namespace['outer']().__code__
try:
    try: original_native(context, ConfinedTreeEntryPin(False))
    except TypeError as error: assert 'original preparation' in str(error)
    else: raise AssertionError('substituted original function accepted')
finally: target.__code__ = original
assert copy_value(ConfinedTreeEntryPin(False)) == dataclasses.asdict(ConfinedTreeEntryPin(False))
""",
    )


def test_native_preparation_context_does_not_retain_copied_values(native_sdk):
    run_receipt_native(
        native_sdk,
        """
from aware_workspace_runtime import repository_tree_preparation_copy as preparation
from aware_file_system.confined_mutation import ConfinedTreeEntryPin
class Leaf:
    def __deepcopy__(self,memo): return 'detached-original'
value = ConfinedTreeEntryPin(False)
leaf = Leaf()
weak = weakref.ref(leaf)
object.__setattr__(value, 'content_digest', leaf)
result = preparation.copy_preparation_observation(value)
assert result['content_digest'] == 'detached-original'
del leaf,value
gc.collect()
assert weak() is None
assert result['content_digest'] == 'detached-original'
""",
    )


@pytest.mark.parametrize("entry", ("make_preparation_copy", "copy_preparation"))
def test_preparation_binding_refuses_builtin_alias_before_dispatch(native_sdk, entry):
    run_native(
        native_sdk,
        f"""
import dataclasses
from aware_workspace_sdk import _tree_native_binding as binding
entry = {entry!r}
original = getattr(native, entry)
setattr(native, entry, native.new_context)
def walk(value): return value
try:
    assert binding.prepare_preparation_copy((), (), dataclasses._ATOMIC_TYPES,
                                            dataclasses.fields, walk, (), walk) is None
finally: setattr(native, entry, original)
""",
    )


@pytest.mark.parametrize("shape", ("list", "sequence", "filtered"))
def test_native_preparation_preserves_original_fields_collection_protocol(
    native_sdk, shape
):
    run_receipt_native(
        native_sdk,
        f"""
from aware_workspace_runtime import repository_tree_preparation_copy as preparation
from aware_file_system.confined_mutation import ConfinedTreeEntryPin
path='workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_tree_preparation_copy.py'
source=subprocess.run(['git','show','a7b94699311954f3248f71c9175373a17ff23d8c:'+path],cwd={str(REPO)!r},capture_output=True,check=True).stdout
prior=types.ModuleType('aware_workspace_runtime._literal_preparation_collection_control')
prior.__package__='aware_workspace_runtime'
exec(compile(source,'<original-preparation-collection>','exec'),vars(prior))
shape={shape!r}
value=ConfinedTreeEntryPin(False)
outputs=[]
for copier in (preparation.copy_preparation_observation,prior.copy_preparation_observation):
    calls=[]
    class Collection:
        def __init__(self,items): self.items=list(items)
        def __len__(self): calls.append('len');return len(self.items)
        def __getitem__(self,index): calls.append(('item',index));return self.items[index]
        def __iter__(self): calls.append('iter');return iter(self.items)
    def materialize(items):
        rows=list(items)
        if shape=='list':return rows
        if shape=='filtered':rows=rows[:-1]
        return Collection(rows)
    dataclasses.tuple=materialize
    try:outputs.append((copier(value),tuple(calls)))
    finally:del dataclasses.tuple
assert outputs[0]==outputs[1], outputs
""",
    )


@pytest.mark.parametrize("depth", (0, 20))
def test_native_preparation_conserves_unknown_atomic_membership_schedule(
    native_sdk, depth
):
    run_receipt_native(
        native_sdk,
        f"""
from aware_workspace_runtime import repository_tree_preparation_copy as preparation
from aware_file_system.confined_mutation import ConfinedTreeEntryPin
path='workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_tree_preparation_copy.py'
source=subprocess.run(['git','show','a7b94699311954f3248f71c9175373a17ff23d8c:'+path],cwd={str(REPO)!r},capture_output=True,check=True).stdout
prior=types.ModuleType('aware_workspace_runtime._literal_preparation_membership_control')
prior.__package__='aware_workspace_runtime'
exec(compile(source,'<original-preparation-membership>','exec'),vars(prior))
outputs=[]
for copier in (preparation.copy_preparation_observation,prior.copy_preparation_observation):
    calls=[]
    class Meta(type):
        def __hash__(cls): calls.append('hash');return 1234567
    class Leaf(metaclass=Meta):
        def __deepcopy__(self,memo): calls.append('copy');return 'detached'
    value=ConfinedTreeEntryPin(False)
    nested=Leaf()
    for i in range({depth}):nested=(nested,)
    object.__setattr__(value,'content_digest',nested)
    outputs.append((copier(value),tuple(calls)))
assert outputs[0]==outputs[1], outputs
assert outputs[0][1].count('copy')==1
""",
    )


def test_native_preparation_origin_lookup_refuses_foreign_keys_without_behavior(
    native_sdk,
):
    run_receipt_native(
        native_sdk,
        """
import inspect
from aware_workspace_runtime import repository_tree_preparation_copy as preparation
from aware_workspace_sdk import _tree_native_binding as binding
from aware_file_system.confined_mutation import ConfinedTreeEntryPin
copy_value = preparation.copy_preparation_observation
context, original_native = inspect.getclosurevars(copy_value).nonlocals['native_handoff']
calls=[]
class Key:
    def __hash__(self): return hash('copy_preparation')
    def __eq__(self, other): calls.append('foreign-key');return False
key=Key()
namespace=vars(native)
namespace[key]=None
calls.clear()
def walk(value):return value
try:
    assert binding.prepare_preparation_copy((),(),dataclasses._ATOMIC_TYPES,
                                             dataclasses.fields,walk,(),walk) is None
    try: original_native(context,ConfinedTreeEntryPin(False))
    except TypeError:pass
    else:raise AssertionError('foreign native namespace accepted')
    assert calls==[],calls
finally:del namespace[key]
assert copy_value(ConfinedTreeEntryPin(False))==dataclasses.asdict(ConfinedTreeEntryPin(False))
""",
    )


def test_tuple_formatting_is_exact_array_text_with_fresh_aliases(native_sdk):
    run_native(
        native_sdk,
        """
from aware_workspace_sdk import _tree_native_binding as binding
context = binding._STORE_JSON_HANDOFF[0]
assert native.OWNER_FORMATTER_ABI == 1
values = [(),(None,False,True,0,2**64,'é','😀'), {'a':(1,{'b':(2,3)})},
          (2**80,), (1.25,), (float('nan'),), (b'a',), (object(),), ('\\ud800',)]
cycle=[]
cycle.append((cycle,))
values.append((cycle,))
def render(value): return json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':'))
def outcome(function,value):
    try:return ('ok',function(value))
    except BaseException as error:return (type(error).__name__,str(error),type(error.__context__).__name__)
for value in values:
    for i in range(2):
        assert outcome(lambda v:native.call_tree_formatter(context,json.dumps,v,json),value)==outcome(render,value)
member={'value':1}
alias=((member,), (member,))
assert native.call_tree_formatter(context,json.dumps,alias,json)==render(alias)
member['value']=2
assert native.call_tree_formatter(context,json.dumps,alias,json)==render(alias)
assert native.call_tree_formatter(context,json.dumps,[1,2],json)==render((1,2))
assert native.call_tree_formatter(context,json.dumps,(1,2),json)==render([1,2])
""",
    )


def test_original_owner_canonical_bytes_and_fallback_errors(native_sdk):
    run_receipt_native(
        native_sdk,
        """
from aware_workspace_runtime import repository_tree_projection as runtime
from aware_workspace_sdk import _tree_native_binding as binding
assert runtime._owner_json_handoff is binding._STORE_JSON_HANDOFF

def original(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
def outcome(function,value):
    try:return ('ok',function(value))
    except BaseException as error:return (type(error).__name__,str(error),type(error.__context__).__name__)
for value in (None,False,2**64,2**80,(),(1,'é'),{'z':(1,2),'a':'😀'},1.25,float('nan'),b'a',object(),'\\ud800'):
    assert outcome(runtime._canonical,value)==outcome(original,value)
assert outcome(runtime._canonical,{'fresh':[1]})==outcome(original,{'fresh':[1]})
""",
    )


@pytest.mark.parametrize("behavior", ("return", "raise", "restore"))
def test_owner_formatter_preserves_selected_callee_and_keyword_order(
    native_sdk, behavior
):
    run_receipt_native(
        native_sdk,
        f"""
from aware_workspace_runtime import repository_tree_projection as runtime
behavior={behavior!r}
original=json.dumps
value=object()
calls=[]
error=BaseException('same selected canonical failure')
def selected(payload,**kwargs):
    calls.append((payload,tuple(kwargs.items())))
    if behavior=='restore':json.dumps=original
    if behavior=='raise':raise error
    return 'original selected text'
json.dumps=selected
try:
    try: result=runtime._canonical(value)
    except BaseException as caught:assert behavior=='raise' and caught is error
    else:assert result==b'original selected text' and behavior!='raise'
finally:json.dumps=original
assert calls==[(value,(('sort_keys',True),('ensure_ascii',False),('separators',(',',':')),('allow_nan',False)))],calls
""",
    )


@pytest.mark.parametrize("missing", ("owner_abi", "export"))
def test_owner_formatter_older_image_preserves_original_definition(native_sdk, missing):
    run_receipt_native(
        native_sdk,
        f"""
from aware_workspace_runtime import repository_tree_projection as runtime
from aware_workspace_sdk import _tree_native_binding as binding
path=Path(runtime.__file__)
node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_canonical')
clone=types.ModuleType('aware_workspace_runtime._older_owner_formatter_control')
clone.__dict__.update(json=json,_owner_json_handoff=None)
sys.modules[clone.__name__]=clone
exec(compile(ast.get_source_segment(path.read_text(),node),'<owner-original-canonical>','exec'),vars(clone))
original=clone._canonical
name='OWNER_FORMATTER_ABI' if {missing!r}=='owner_abi' else 'call_tree_formatter'
prior=getattr(native,name)
delattr(native,name)
try:
    assert binding.bind_owner_json(vars(clone),'_canonical') is None
    assert clone._canonical is original
    assert clone._canonical({{'a':(1,2)}})==b'{{"a":[1,2]}}'
finally:setattr(native,name,prior)
""".replace(
            "from aware_workspace_runtime import",
            "import ast\nfrom aware_workspace_runtime import",
            1,
        ),
    )


@pytest.mark.parametrize("name", ("_encode", "_timestamp"))
@pytest.mark.parametrize("behavior", ("return", "raise", "restore"))
def test_receipt_namespace_witness_rechecks_changed_binding(native_sdk, name, behavior):
    run_receipt_native(
        native_sdk,
        f"""
name={name!r}
behavior={behavior!r}
value=receipt_cases._mutation_receipt()
selected=receipt._encode
original=getattr(receipt,name)
calls=[]
def foreign(*args,**kwargs):
    calls.append('foreign')
    if behavior=='restore':setattr(receipt,name,original)
    if behavior=='raise':raise AssertionError('foreign delegate executed')
    return {{}}
setattr(receipt,name,foreign)
try:
    try:selected(value,type(value))
    except TypeError:pass
    else:raise AssertionError('changed original binding accepted')
    assert calls==[],calls
finally:setattr(receipt,name,original)
assert outcome(receipt,value)==outcome(baseline,value)
""",
    )


@pytest.mark.parametrize("change", ("code", "defaults", "kwdefaults"))
def test_receipt_namespace_witness_preserves_live_function_checks(native_sdk, change):
    run_receipt_native(
        native_sdk,
        f"""
change={change!r}
context=receipt._RECEIPT_NATIVE_HANDOFF[0]
value=receipt_cases._mutation_receipt()
function=receipt._timestamp
attribute={{'code':'__code__','defaults':'__defaults__','kwdefaults':'__kwdefaults__'}}[change]
original=getattr(function,attribute)
def foreign(*args,**kwargs):raise AssertionError('foreign receipt code executed')
replacement=foreign.__code__ if change=='code' else (() if change=='defaults' else {{}})
setattr(function,attribute,replacement)
try:
    try:native.receipt_prelude(context,type(value),receipt._RECEIPT_FIELDS_BY_ID,
                              receipt._RECEIPT_ORIGINAL_REGISTRY,receipt._RECEIPT_ORIGINAL_ENTRIES)
    except TypeError:pass
    else:raise AssertionError('unchanged namespace hid changed function')
finally:setattr(function,attribute,original)
assert outcome(receipt,value)==outcome(baseline,value)
""",
    )


@pytest.mark.parametrize("target", ("runtime", "native"))
def test_receipt_namespace_rechecks_allocation_gap_before_first_use(native_sdk, target):
    run_receipt_native(
        native_sdk,
        f"""
import ast
node=ast.parse(Path(receipt.__file__).read_bytes())
last=node.body[-1]
assert isinstance(last,ast.If) and '_receipt_native_seal' in ast.unparse(last)
node.body.pop()
clone=types.ModuleType('aware_workspace_runtime._allocation_seal_control')
clone.__package__='aware_workspace_runtime'
sys.modules[clone.__name__]=clone
exec(compile(node,'<original-unsealed-receipt-module>','exec'),vars(clone))
context=clone._RECEIPT_NATIVE_HANDOFF[0]
namespace=vars(clone) if {target!r}=='runtime' else vars(native)
name='_encode' if {target!r}=='runtime' else 'convert_receipt'
sealer=native.seal_receipts
state={{'armed':False,'poisoned':False,'prior':None}}
calls=[]
def foreign(*args,**kwargs):calls.append('foreign');return {{}}
def callback(phase,info):
    if phase=='start' and state['armed'] and not state['poisoned']:
        state['poisoned']=True
        state['prior']=namespace[name]
        namespace[name]=foreign

def profile(frame,event,function):
    if function is sealer:
        if event=='c_call':state['armed']=True
        # Keep the callback armed across the return to Python: CPython may
        # defer pending cyclic collection until after the C function returns.
previous_profile=sys.getprofile()
threshold=gc.get_threshold()
was_enabled=gc.isenabled()
gc.collect()
gc.callbacks.append(callback)
gc.set_threshold(1,1,1)
gc.enable()
sys.setprofile(profile)
seal_failed=False
try:
    try:clone._receipt_native_seal(vars(clone),clone._RECEIPT_NATIVE_HANDOFF)
    except TypeError:seal_failed=True
    if not state['poisoned']:gc.collect()
    if not seal_failed:
        try:native.receipt_prelude(context,receipt_cases.WorkspaceRepositoryMutationReceipt,
                                  clone._RECEIPT_FIELDS_BY_ID,clone._RECEIPT_ORIGINAL_REGISTRY,
                                  clone._RECEIPT_ORIGINAL_ENTRIES)
        except TypeError:pass
        else:raise AssertionError('issuance-to-use namespace movement accepted')
finally:
    sys.setprofile(previous_profile)
    state['armed']=False
    gc.callbacks.remove(callback)
    gc.set_threshold(*threshold)
    if not was_enabled:gc.disable()
    if state['poisoned']:namespace[name]=state['prior']
assert state['poisoned'] and calls==[],(state,calls)
value=receipt_cases._mutation_receipt()
if seal_failed:
    assert gc.get_referents(context)==[]
    try:native.receipt_prelude(context,type(value),clone._RECEIPT_FIELDS_BY_ID,
                             clone._RECEIPT_ORIGINAL_REGISTRY,clone._RECEIPT_ORIGINAL_ENTRIES)
    except RuntimeError:pass
    else:raise AssertionError('restored bindings resumed rejected seal')
# A descriptive codec is not an operation family. A post-seal namespace refusal
# cannot revoke unrelated codecs; original operation retirement stays outside.
assert outcome(receipt,value)==outcome(baseline,value)
""",
    )


def test_preparation_build_profile_includes_original_fields(native_sdk):
    evidence = json.loads((native_sdk / "build-evidence.json").read_bytes())
    pins = evidence["json_profile_pins"]
    assert len(pins) == 6
    assert pins[-1]["function"] == "fields"
    assert pins[-1]["size"] > 0
    header = evidence["json_profile_header"]
    assert "WORKSPACE_JSON_PROFILE_COUNT 6" in header
    assert "index_json_profile_5};" in header


@pytest.mark.parametrize("change", ("access", "metadata", "flag", "missing_flag"))
def test_native_fields_snapshot_preserves_original_dispatch(native_sdk, change):
    run_receipt_native(
        native_sdk,
        f"""
from aware_workspace_runtime import repository_tree_preparation_copy as preparation
from aware_file_system.confined_mutation import ConfinedTreeScratchEffect
cls=ConfinedTreeScratchEffect
value=cls('path','role',1,'create',0o600)
metadata=cls.__dataclass_fields__
flag_descriptor=vars(dataclasses.Field)['_field_type']
field=metadata['role']
flag=field._field_type
outcomes=[]
for copier in (dataclasses.asdict,preparation.copy_preparation_observation):
    calls=[]
    if {change!r}=='access':
        def access(instance,name):
            calls.append(('access',name))
            return object.__getattribute__(instance,name)
        cls.__getattribute__=access
    elif {change!r}=='metadata':
        class Metadata(dict):
            def values(self):
                calls.append(('values',))
                return super().values()
        cls.__dataclass_fields__=Metadata(metadata)
    elif {change!r}=='flag':
        def read_flag(instance):
            calls.append(('flag',object.__getattribute__(instance,'name')))
            return flag_descriptor.__get__(instance,type(instance))
        dataclasses.Field._field_type=property(read_flag)
    else:
        del field._field_type
    try:
        try:outcome=('return',copier(value))
        except BaseException as error:outcome=('error',type(error),str(error))
        outcomes.append((outcome,tuple(calls)))
    finally:
        if {change!r}=='access':del cls.__getattribute__
        cls.__dataclass_fields__=metadata
        dataclasses.Field._field_type=flag_descriptor
        field._field_type=flag
assert outcomes[0]==outcomes[1],outcomes
""",
    )


@pytest.mark.parametrize("name", ("getattr", "tuple"))
@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_native_fields_snapshot_preserves_original_namespace_fallback(
    native_sdk, name, mode
):
    run_receipt_native(
        native_sdk,
        f"""
import builtins
from aware_workspace_runtime import repository_tree_preparation_copy as preparation
from aware_file_system.confined_mutation import ConfinedTreeScratchEffect
value=ConfinedTreeScratchEffect('path','role',1,'create',0o600)
ns=vars(dataclasses)
name={name!r}
assert name not in ns
from aware_workspace_sdk import _tree_native_binding as binding
original_factory=binding.prepare_preparation_copy
binding.prepare_preparation_copy=lambda *args:None
try:prior_copy=preparation._bind_preparation_copy()
finally:binding.prepare_preparation_copy=original_factory
outcomes=[]
for copier in (prior_copy,preparation.copy_preparation_observation):
    calls=[]
    original=getattr(builtins,name)
    def selected(*args):
        calls.append(name)
        if {mode!r}=='restore':ns.pop(name,None)
        if {mode!r}=='raise':raise LookupError('literal fields namespace failure')
        return original(*args)
    ns[name]=selected
    try:
        try:outcome=('return',copier(value))
        except BaseException as error:outcome=('error',type(error),str(error))
        outcomes.append((outcome,tuple(calls)))
    finally:ns.pop(name,None)
assert outcomes[0]==outcomes[1],outcomes
assert outcomes[0][1],outcomes
""",
    )


@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_native_fields_snapshot_preserves_callback_before_later_fields(
    native_sdk, mode
):
    run_receipt_native(
        native_sdk,
        f"""
from aware_workspace_runtime import repository_tree_preparation_copy as preparation
from aware_file_system.confined_mutation import ConfinedTreeScratchEffect
cls=ConfinedTreeScratchEffect
metadata=cls.__dataclass_fields__
field=metadata['role']
old_name=field.name
outcomes=[]
for copier in (dataclasses.asdict,preparation.copy_preparation_observation):
    calls=[]
    class Leaf:
        def __deepcopy__(self,memo):
            calls.append('copy')
            field.name='path'
            if {mode!r}=='raise':raise LookupError('original nested callback')
            if {mode!r}=='restore':field.name=old_name
            return 'copied'
    value=cls(Leaf(),'role',1,'create',0o600)
    try:
        try:outcome=('return',copier(value))
        except BaseException as error:outcome=('error',type(error),str(error))
        outcomes.append((outcome,tuple(calls)))
    finally:field.name=old_name
assert outcomes[0]==outcomes[1],outcomes
""",
    )


def test_native_receipt_record_sequence_enters_original_child_recursion(native_sdk):
    run_receipt_native(
        native_sdk,
        """
value=receipt_cases.capture()
value=copy.copy(value)
object.__setattr__(value,'path_states',value.path_states*128)
before=native.receipt_graph_stats()['direct_records']
assert outcome(receipt,value)==outcome(baseline,value)
assert native.receipt_graph_stats()['direct_records']-before>=128
""",
    )


@pytest.mark.parametrize(
    "shape", ("empty", "list", "subclass", "iterator", "malformed")
)
def test_native_receipt_record_sequence_preserves_original_iteration(native_sdk, shape):
    run_receipt_native(
        native_sdk,
        f"""
value=receipt_cases.capture()
original=value.path_states
results=[]
for module in (receipt,baseline):
    calls=[]
    class Rows(tuple):
        def __iter__(self):
            calls.append('iteration')
            return super().__iter__()
    shape={shape!r}
    selected=()if shape=='empty'else(list(original)if shape=='list'else(Rows(original)if shape=='subclass'else(iter(original)if shape=='iterator'else (None,object()))))
    changed=copy.copy(value)
    object.__setattr__(changed,'path_states',selected)
    results.append((outcome(module,changed),tuple(calls)))
assert results[0]==results[1],results
""",
    )


@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_native_receipt_record_sequence_preserves_child_dispatch_movement(
    native_sdk, mode
):
    run_receipt_native(
        native_sdk,
        f"""
value=receipt_cases.capture()
value=copy.copy(value)
object.__setattr__(value,'path_states',value.path_states*2)
cls=type(value.path_states[0])
name='path'
original=vars(cls)[name]
results=[]
for module in (receipt,baseline):
    calls=[]
    def access(instance):
        calls.append({mode!r})
        if {mode!r}=='restore':setattr(cls,name,original)
        if {mode!r}=='raise':raise LookupError('original ordered child failure')
        return original.__get__(instance,cls)
    setattr(cls,name,property(access))
    try:results.append((outcome(module,value),tuple(calls)))
    finally:setattr(cls,name,original)
assert results[0]==results[1],results
assert results[0][1],results
""",
    )


def test_index_key_render_preserves_stock_ascii_unicode_and_integer_bytes(native_sdk):
    run_native(
        native_sdk,
        """
context=native.make_index_formatter(json,json.encoder,1,1,0)
assert context is not None
characters=[chr(i)for i in range(256)]+[chr(i)for i in (0x7ff,0x800,0xd7ff,0xd800,0xdbff,0xdc00,0xdfff,0xe000,0xffff,0x10000,0x10ffff)]
characters+= [chr((i*7919)%0x110000) for i in range(4096)]
for position in range(0,len(characters),37):
    strings=characters[position:position+37]
    value={'contract_ref':'r','contract_version':'1','repository_binding_ref':'r','records':[{'text':''.join(strings),'keys':{s:s for s in strings},'values':[None,True,False,-2**63,0,2**63,2**64]}]}
    actual=native.call_index_formatter(context,json.dumps,value,json)
    assert actual==json.dumps(value,sort_keys=True,separators=(',',':')),(position,actual)
    assert actual.isascii()
assert native.index_formatter_stats(context)['charged_bytes']==0
""",
    )


def test_index_key_render_keeps_large_object_and_unsupported_value_fallback(native_sdk):
    run_native(
        native_sdk,
        """
context=native.make_index_formatter(json,json.encoder,1,1,0)
for row in ({str(i):i for i in range(8193)}, {'float':1.5}, {'large':2**65}):
    value={'contract_ref':'r','contract_version':'1','repository_binding_ref':'r','records':[row]}
    assert native.call_index_formatter(context,json.dumps,value,json)==json.dumps(value,sort_keys=True,separators=(',',':'))
""",
    )


@pytest.mark.parametrize("attribute", ("name", "_field_type"))
@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_receipt_geometry_preserves_field_class_dispatch(native_sdk, attribute, mode):
    run_receipt_native(
        native_sdk,
        f"""
value=receipt_cases._mutation_receipt()
attribute={attribute!r}
mode={mode!r}
original=vars(dataclasses.Field)[attribute]
original_name=vars(dataclasses.Field)['name']
outputs=[]
for module in (receipt,baseline):
    calls=[]
    def read(field):
        calls.append(original_name.__get__(field,type(field)))
        if mode=='restore':setattr(dataclasses.Field,attribute,original)
        if mode=='raise':raise LookupError('original field descriptor failure')
        return original.__get__(field,type(field))
    setattr(dataclasses.Field,attribute,property(read))
    try:outputs.append((outcome(module,value),tuple(calls)))
    finally:setattr(dataclasses.Field,attribute,original)
assert outputs[0]==outputs[1],outputs
assert outputs[0][1],outputs
""",
    )


@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_receipt_geometry_foreign_hint_keys_keep_original_dispatch(native_sdk, mode):
    run_receipt_native(
        native_sdk,
        f"""
value=receipt_cases._mutation_receipt()
mode={mode!r}
outputs=[]
for module in (receipt,baseline):
    hints=module._type_hints(type(value))
    initial=dict(hints)
    selected=hints.pop('target_path')
    calls=[]
    class Key:
        def __hash__(self):return hash('target_path')
        def __eq__(self,other):
            calls.append(other)
            if mode=='raise':raise LookupError('original hint key failure')
            if mode=='restore':
                hints.clear()
                hints.update(initial)
            return other=='target_path'
    hints[Key()]=selected
    try:outputs.append((outcome(module,value),tuple(calls)))
    finally:
        hints.clear()
        hints.update(initial)
assert outputs[0]==outputs[1],outputs
assert outputs[0][1]==('target_path',),outputs
""",
    )


def test_receipt_geometry_still_looks_up_hint_before_none(native_sdk):
    run_receipt_native(
        native_sdk,
        """
value=receipt_cases._mutation_receipt()
assert value.expected_content_digest is None
outputs=[]
for module in (receipt,baseline):
    hints=module._type_hints(type(value))
    original=hints.pop('expected_content_digest')
    try:outputs.append(outcome(module,value))
    finally:hints['expected_content_digest']=original
assert outputs[0]==outputs[1],outputs
assert outputs[0]==('KeyError',"'expected_content_digest'"),outputs
""",
    )


@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_receipt_geometry_keeps_final_name_read_after_child(native_sdk, mode):
    run_receipt_native(
        native_sdk,
        f"""
from datetime import datetime
value=receipt_cases._checkpoint()
field=type(value).__dataclass_fields__['accepted_at']
original=field.name
mode={mode!r}
outputs=[]
for module in (receipt,baseline):
    calls=[]
    class SourceTime(datetime):
        def astimezone(self,tz):
            calls.append('timestamp')
            field.name='consumer_key'
            if mode=='raise':raise LookupError('original timestamp failure')
            if mode=='restore':field.name=original
            return super().astimezone(tz)
    changed=copy.copy(value)
    object.__setattr__(changed,'accepted_at',SourceTime.fromisoformat(value.accepted_at.isoformat()))
    try:outputs.append((outcome(module,changed),tuple(calls)))
    finally:field.name=original
assert outputs[0]==outputs[1],outputs
assert outputs[0][1]==('timestamp',),outputs
""",
    )


def test_ascii_intrinsic_matches_original_path_values_and_errors(native_sdk):
    run_native(
        native_sdk,
        """
import random
slot = next(item for item in codec._path.__code__.co_consts
    if type(item) is tuple and len(item) == 2
    and item[0] == '__workspace_ascii_path_slot_v2__')
assert slot[1] is native.ascii_path_positive
assert native.ASCII_PATH_POSITIVE_ABI == 2

def outcome(function, value, maximum):
    try:
        result = function(value, maximum=maximum)
    except BaseException as error:
        return type(error).__name__, error.args
    return 'returned', result

rng = random.Random(81028)
alphabet = 'abAZ09 /._-\\\\\\x00\\x1f\\x7f'
values = [b'a', bytearray(b'a'), None, 1, [], {}, object(), '', '.', '..',
    'a/b', 'a//b', '/a', 'a/', 'a'*255, 'a'*256,
    '/'.join(['a'*200]*6), 'é', 'e\\u0301', 'a/é', 'a\\u200d', '\\ud800']
values += [''.join(rng.choice(alphabet) for _ in range(rng.randrange(70)))
    for _ in range(20000)]
for value in values:
    for maximum in (0, 1, 256, 1024, 4096, 2**100, -(2**100), True, 1.5):
        assert outcome(codec._path, value, maximum) == outcome(portable._path, value, maximum), (repr(value), maximum)
for value in ('a', 'a/b', 'a'*255):
    assert native.ascii_path_positive(value, 1024) is True
for value in (b'a', '', '.', '..', 'a//b', 'é', 'a'*256):
    assert native.ascii_path_positive(value, 1024) is False
assert native.ascii_path_positive('a', 2**100) is False
assert native.ascii_path_positive('a', True) is False
""",
    )


def test_ascii_intrinsic_keeps_subclass_and_comparison_dispatch_order(native_sdk):
    run_native(
        native_sdk,
        """
def probe(function, mode):
    calls=[]
    class Text(str):
        def isascii(self):
            calls.append('isascii')
            if mode == 'raise':
                raise RuntimeError('original dispatch')
            return True
    class Maximum:
        def __lt__(self, other):
            calls.append(('compare', other))
            return False
    try:
        function(Text('a/b'), maximum=Maximum())
    except BaseException as error:
        result=type(error).__name__, error.args
    else:
        result=None
    return result, calls
for mode in ('return', 'raise'):
    assert probe(codec._path, mode) == probe(portable._path, mode)

def compare_probe(function):
    calls=[]
    class Maximum:
        def __lt__(self, other):
            calls.append(other)
            raise RuntimeError('maximum comparator')
    try:
        function('a/b', maximum=Maximum())
    except BaseException as error:
        result=type(error).__name__, error.args
    return result, calls
assert compare_probe(codec._path) == compare_probe(portable._path)
""",
    )


@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
def test_ascii_intrinsic_export_rebinding_cannot_replace_retained_dispatch(
    native_sdk, mode
):
    run_native(
        native_sdk,
        f"""
calls=[]
original=native.ascii_path_positive

def foreign(*args):
    calls.append(args)
    if {mode!r} == 'restore':
        native.ascii_path_positive=original
    if {mode!r} == 'raise':
        raise RuntimeError('foreign intrinsic')
    return True
native.ascii_path_positive=foreign
for value in ('a/b', 'a//b'):
    try:
        codec._path(value)
    except codec.WorkspaceTreeProjectionValueError:
        assert value == 'a//b'
assert calls == []
for value in cases.examples():
    assert codec.repository_tree_projection_value_to_json(value) == portable.repository_tree_projection_value_to_json(value)
""",
    )


@pytest.mark.parametrize("mode", ["missing", "foreign", "odd_abi"])
def test_ascii_intrinsic_optional_export_uses_original_portable_fallback(
    native_sdk, mode
):
    run_native(
        native_sdk,
        f"""
calls=[]
class OddABI:
    def __eq__(self, other):
        calls.append('eq')
        raise RuntimeError('foreign ABI')
def foreign(*args):
    calls.append('call')
    raise RuntimeError('foreign intrinsic')
if {mode!r} == 'missing':
    del native.ASCII_PATH_POSITIVE_ABI
elif {mode!r} == 'foreign':
    native.ascii_path_positive=foreign
else:
    native.ASCII_PATH_POSITIVE_ABI=OddABI()
module=types.ModuleType('aware_workspace_sdk._ascii_optional_case')
module.__package__='aware_workspace_sdk'
sys.modules[module.__name__]=module
exec(compile(Path(codec.__file__).read_bytes(), '<optional-case>', 'exec'), vars(module))
slot=next(item for item in module._path.__code__.co_consts
    if type(item) is tuple and len(item)==2
    and item[0]=='__workspace_ascii_path_slot_v2__')
assert slot[1] is None
for value in cases.examples():
    assert module.repository_tree_projection_value_to_json(value) == portable.repository_tree_projection_value_to_json(value)
assert calls == []
""",
    )


@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
def test_ascii_intrinsic_forged_code_constant_refuses_before_foreign_call(
    native_sdk, mode
):
    run_native(
        native_sdk,
        f"""
from aware_workspace_sdk import _tree_native_binding as binding
source=Path(codec.__file__).read_text()
assert source.count('_seal_native_tree_binding(globals(), _TREE_NATIVE_HANDOFF)') == 1
source=source.replace('_seal_native_tree_binding(globals(), _TREE_NATIVE_HANDOFF)', '')
module=types.ModuleType('aware_workspace_sdk._ascii_forged_case')
module.__package__='aware_workspace_sdk'
sys.modules[module.__name__]=module
exec(compile(source, '<forged-case>', 'exec'), vars(module))
original=module._path.__code__
calls=[]
def foreign(*args):
    calls.append(args)
    if {mode!r} == 'restore':
        module._path.__code__=original
    if {mode!r} == 'raise':
        raise RuntimeError('foreign intrinsic')
    return True
module._path.__code__=original.replace(co_consts=tuple(
    (item[0], foreign)
    if type(item) is tuple and len(item)==2 and item[0]=='__workspace_ascii_path_slot_v2__'
    else item for item in original.co_consts))
try:
    binding.seal(vars(module), module._TREE_NATIVE_HANDOFF)
except (TypeError, RuntimeError, ValueError):
    pass
else:
    raise AssertionError('forged slot accepted')
assert calls == []
module._path.__code__=original
try:
    binding.seal(vars(module), module._TREE_NATIVE_HANDOFF)
except (TypeError, RuntimeError, ValueError):
    pass
else:
    raise AssertionError('rejected context resumed')
assert calls == []
""",
    )


def test_invocation_hint_index_preserves_repeated_fresh_bindings(native_sdk):
    run_native(
        native_sdk,
        """
from dataclasses import asdict
import hashlib
bound = cases.binding()
files = tuple(replace(bound.files[0], path=f'pkg/output-{i:03}.py') for i in range(128))
bound = replace(bound, files=files, transition_count=129,
                effect_paths=('pkg', *(row.path for row in files)))
payload = asdict(bound)
del payload['binding_ref']
encoded = json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',', ':'))
bound = replace(bound, binding_ref='sha256:'+hashlib.sha256(encoded.encode()).hexdigest())
expected = portable.repository_tree_projection_value_to_json(bound)
for _ in range(3):
    assert codec.repository_tree_projection_value_to_json(bound) == expected
    codec.repository_tree_projection_value_validate_equal(bound,expected_value=bound)
row = bound.files[-1]
prior = row.requested_mode
try:
    object.__setattr__(row,'requested_mode',0o777)
    for module in (portable,codec):
        try:module.repository_tree_projection_value_to_json(bound)
        except module.WorkspaceTreeProjectionValueError:pass
        else:raise AssertionError('later fresh value was not checked')
finally:object.__setattr__(row,'requested_mode',prior)
assert codec.repository_tree_projection_value_to_json(bound) == expected
""",
    )


@pytest.mark.parametrize("registry_change", ["replace", "remove"])
def test_invocation_hint_index_authenticates_fresh_registry_entry(
    native_sdk, registry_change
):
    run_native(
        native_sdk,
        f"""
bound = cases.binding()
expected = codec.repository_tree_projection_value_to_json(bound)
definitions = next(definitions for cls,definitions in codec._DEFINITIONS
                   if cls is type(bound))
hint = next(hint for name,descriptor,hint in definitions if name == 'effect_paths')
shape_keys = (id(hint),)
original = dict(codec._HINT_SHAPES)
try:
    for key in shape_keys:
        codec._HINT_SHAPES.clear()
        codec._HINT_SHAPES.update(original)
        if {registry_change!r} == 'replace':codec._HINT_SHAPES[key] = (object(),None,())
        else:del codec._HINT_SHAPES[key]
        try:codec.repository_tree_projection_value_to_json(bound)
        except codec.WorkspaceTreeProjectionValueError:pass
        else:
            raise AssertionError('substituted used hint registry accepted')
finally:
    codec._HINT_SHAPES.clear()
    codec._HINT_SHAPES.update(original)
assert codec.repository_tree_projection_value_to_json(bound) == expected
""",
    )


@pytest.mark.parametrize("replacement", ["equal_tuple", "foreign", "missing"])
def test_invocation_hint_index_rechecks_after_prior_rows(native_sdk, replacement):
    run_native(
        native_sdk,
        f"""
bound = cases.binding()
# This calls only the descriptive converter; no valid plan or authority is
# issued from deliberately repeated metadata rows.
bound = replace(bound,files=(bound.files[0],)*8)
pin = codec.values.WorkspaceTreeEntryPin
definitions = codec._DEFINITIONS_BY_ID[id(pin)][1]
hint = next(hint for name,descriptor,hint in definitions if name == 'size_bytes')
key = id(hint)
original = codec._HINT_SHAPES[key]
maximum = codec._path.__kwdefaults__['maximum']
visits = []
calls = []
class Foreign:
    def __eq__(self,other):calls.append('equality');return True
    def __iter__(self):calls.append('iteration');return iter(())
def observe(frame,event,arg):
    if event == 'call' and frame.f_code is codec._validate.__code__ and frame.f_locals.get('cls') is pin:
        visits.append(True)
        if len(visits) == 3:
            if {replacement!r} == 'equal_tuple':codec._HINT_SHAPES[key] = tuple(list(original))
            elif {replacement!r} == 'foreign':codec._HINT_SHAPES[key] = Foreign()
            else:del codec._HINT_SHAPES[key]
prior_profile = sys.getprofile()
codec._path.__kwdefaults__['maximum'] = maximum+1
try:
    sys.setprofile(observe)
    try:native.convert_root(codec._TREE_NATIVE_HANDOFF[0],type(bound),bound,'',0)
    except codec.WorkspaceTreeProjectionValueError as error:
        assert 'native whole hint shape substituted' in str(error),error
    else:raise AssertionError('previous declaration lookup bypassed fresh registry check')
finally:
    sys.setprofile(prior_profile)
    codec._path.__kwdefaults__['maximum'] = maximum
    codec._HINT_SHAPES[key] = original
assert len(visits) == 3 and calls == [],(visits,calls)
""",
    )


def test_index_preflight_preserves_private_bounds_and_fresh_shared_lists(native_sdk):
    run_native(
        native_sdk,
        """
context=native.make_index_formatter(json,json.encoder,1,1,16*1024*1024)
for count in (0,1,4095,4096,4097):
    row={'value':'before','nested':[1,2,3]}
    shared=[row]*count
    value={'contract_ref':'r','version':'1','repository_binding_ref':'r','sequence':3,'bodies':shared,'captures':shared,'deltas':shared}
    for changed in ('before','after'):
        row['value']=changed
        assert native.call_index_formatter(context,json.dumps,value,json)==json.dumps(value,sort_keys=True,separators=(',',':'))
for size in (8*1024*1024-10,8*1024*1024-9,8*1024*1024-8):
    value={'contract_ref':'r','contract_version':'1','repository_binding_ref':'r','records':['x'*size,{'tail':'fresh'}]}
    assert native.call_index_formatter(context,json.dumps,value,json)==json.dumps(value,sort_keys=True,separators=(',',':'))
""",
    )


def test_index_preflight_invalidates_before_real_literal_serializer_callback(
    native_sdk,
):
    run_native(
        native_sdk,
        """
prior=gc.get_threshold()
was_enabled=gc.isenabled()
mid_region=0
try:
    gc.enable()
    for headroom in range(1,25):
        gc.set_threshold(1000000,1000000,1000000)
        gc.collect()
        context=native.make_index_formatter(json,json.encoder,1,1,16*1024*1024)
        assert context is not None
        value={'contract_ref':'r','contract_version':'1','repository_binding_ref':'r','records':[{str(j):j for j in range(8193)}]+[{'ordinal':j,'text':'original'}for j in range(20)]}
        events=[]
        during=[False]
        class Pending:
            def __del__(self):
                events.append((during[0],native.index_formatter_stats(context)['misses']))
                value['records'][-1]['text']='changed'
        pending=Pending()
        pending.loop=pending
        del pending
        gc.set_threshold(gc.get_count()[0]+headroom,1000000,1000000)
        during[0]=True
        try:
            text=native.call_index_formatter(context,json.dumps,value,json)
        finally:
            during[0]=False
            gc.set_threshold(1000000,1000000,1000000)
        earlier=[misses for active,misses in events if active and misses<25]
        if earlier:
            assert json.loads(text)['records'][-1]['text']=='changed',events
            mid_region+=1
        gc.collect()
        del context,value
    assert mid_region>0
finally:
    gc.set_threshold(*prior)
    if not was_enabled:gc.disable()
""",
    )


def test_index_prefetch_fifo_pressure_text_release(native_sdk):
    run_native(
        native_sdk,
        "\nroot=lambda records:{'contract_ref':'r','contract_version':'1','repository_binding_ref':'r','records':records}\nfor sample in ('x'*50,'雪😀\\ud800'):\n    context=native.make_index_formatter(json,json.encoder,1,1,1600)\n    future=[{'n':i,'s':sample}for i in(1,2)]\n    native.call_index_formatter(context,json.dumps,root(future),json)\n    cache=next(v for v in gc.get_referents(context)if type(v)is dict and v and all(type(k)is bytes for k in v))\n    texts=[entry[0]for entry in cache.values()]\n    refs=[sys.getrefcount(text)for text in texts]\n    del cache\n    payload=root([{'n':0,'s':'missing'},*future])\n    before=native.index_formatter_stats(context)\n    actual=native.call_index_formatter(context,json.dumps,payload,json)\n    after=native.index_formatter_stats(context)\n    assert actual==json.dumps(payload,sort_keys=True,separators=(',',':'))\n    assert after['hits']-before['hits']==0 and after['misses']-before['misses']==10\n    for _ in range(40):\n        assert native.call_index_formatter(context,json.dumps,payload,json)==actual\n    del context\n    gc.collect()\n    remaining=[sys.getrefcount(text)for text in texts]\n    assert all(a==b-1 for a,b in zip(remaining,refs)),(refs,remaining)\n    context=native.make_index_formatter(json,json.encoder,1,1,1600)\n    for changed in('first','second'):\n        future[-1]['s']=changed\n        assert native.call_index_formatter(context,json.dumps,payload,json)==json.dumps(payload,sort_keys=True,separators=(',',':'))\n",
    )


def test_index_prefetch_unsupported_future_literal_callback(native_sdk):
    run_native(
        native_sdk,
        "\nprior=gc.get_threshold()\nwas_enabled=gc.isenabled()\nmiddle=0\ntry:\n    gc.enable()\n    for headroom in range(1,17):\n        gc.set_threshold(1000000,1000000,1000000)\n        gc.collect()\n        root=lambda records:{'contract_ref':'r','contract_version':'1','repository_binding_ref':'r','records':records}\n        future={str(j):j for j in range(8193)}\n        last={'text':'original'}\n        context=native.make_index_formatter(json,json.encoder,1,1,400000)\n        native.call_index_formatter(context,json.dumps,root([future,last]),json)\n        initial=native.index_formatter_stats(context)\n        value=root([{str(j):j+1 for j in range(8192)},future,last])\n        events=[]\n        during=[False]\n        class Pending:\n            def __del__(self):\n                events.append((during[0],native.index_formatter_stats(context)['misses']-initial['misses']))\n                last['text']='changed'\n        pending=Pending()\n        pending.loop=pending\n        del pending\n        gc.set_threshold(gc.get_count()[0]+headroom,1000000,1000000)\n        during[0]=True\n        try:text=native.call_index_formatter(context,json.dumps,value,json)\n        finally:\n            during[0]=False\n            gc.set_threshold(1000000,1000000,1000000)\n        if any(active and 4<misses<10 for active,misses in events):\n            assert json.loads(text)['records'][-1]['text']=='changed',events\n            middle+=1\n        gc.collect()\n        del context,value\n    assert middle>0\nfinally:\n    gc.set_threshold(*prior)\n    if not was_enabled:gc.disable()\n",
    )


@pytest.mark.parametrize("kind", ["raising", "missing", "returning"])
def test_native_receipt_subclass_field_key_keeps_member_custody(native_sdk, kind):
    run_receipt_native(
        native_sdk,
        f"""
from aware_workspace_runtime.repository_access import RepositoryObservationCoordinate
cls=RepositoryObservationCoordinate
field=cls.__dataclass_fields__['repository_binding_ref']
original_name=field.name
results=[]
events=[]
armed=False
class Key(str):
    def __hash__(self):
        if armed:
            events.append('hash-start')
            object.__setattr__(value,'repository_binding_ref',None)
            events.append('hash-after-drop')
            if {kind!r}=='raising':raise ValueError('original hash interruption')
        return str.__hash__(self)
class Victim:
    def __del__(self):events.append('member-finalized')
try:
    field.name=Key(original_name)
    for tag,source in (('native',Path(receipt.__file__).read_bytes()),('literal',receipt_before)):
        module=types.ModuleType('aware_workspace_runtime._paired_prefix_'+tag)
        module.__package__='aware_workspace_runtime'
        sys.modules[module.__name__]=module
        exec(compile(source,'<paired-prefix-'+tag+'>','exec'),vars(module))
        if tag=='native':assert module._RECEIPT_NATIVE_HANDOFF is not None
        hints=module._type_hints(cls)
        if {kind!r}=='missing':del hints[original_name]
        value=cls('owner','epoch',0,'digest','policy','version')
        object.__setattr__(value,'repository_binding_ref',Victim())
        events=[]
        armed=True
        result=None
        try:
            result=module._encode(value,cls)
            observed=('ok',type(result).__name__)
        except BaseException as error:observed=(type(error).__name__,str(error))
        finally:
            result=None
            armed=False
        results.append((observed,tuple(events)))
    assert results[0]==results[1],results
    assert results[0][1].count('member-finalized')==1,results
    assert 'hash-start' in results[0][1],results
finally:
    armed=False
    field.name=original_name
""",
    )


@pytest.mark.parametrize(
    "alias",
    [
        "WorkspaceTreeLimits",
        "WorkspaceTreeFileIntent",
        "WorkspaceTreeFileTransition",
        "WorkspaceTreeAncestorIntent",
        "WorkspaceTreeAncestorTransition",
        "WorkspaceTreeProjectionRequest",
        "WorkspaceTreeProjectionBinding",
        "WorkspaceTreeProjectionObservation",
    ],
)
def test_nested_leaf_semantics_preserve_changed_class_aliases(native_sdk, alias):
    run_native(
        native_sdk,
        f"""
value = cases.binding()
original_wire = codec.repository_tree_projection_value_to_json(value)
values = codec.values
original = getattr(values, {alias!r})
def outcome(module):
    try:
        return ('accepted', module.repository_tree_projection_value_to_json(value))
    except BaseException as error:
        return (type(error).__name__, str(error))
try:
    setattr(values, {alias!r}, values.WorkspaceTreeEntryPin)
    assert outcome(codec) == outcome(portable)
finally:
    setattr(values, {alias!r}, original)
assert codec.repository_tree_projection_value_to_json(value) == original_wire
codec.repository_tree_projection_value_validate_equal(value, expected_value=value)
""",
    )


@pytest.mark.parametrize("collect", [False, True])
def test_nested_leaf_semantics_preserve_changed_source_class(native_sdk, collect):
    run_native(
        native_sdk,
        f"""
value = cases.binding()
original_wire = codec.repository_tree_projection_value_to_json(value)
original = codec.WorkspaceWorkflowSourceBinding
prior_threshold = gc.get_threshold()
def outcome(module):
    try:
        return ('accepted', module.repository_tree_projection_value_to_json(value))
    except BaseException as error:
        return (type(error).__name__, str(error))
try:
    codec.WorkspaceWorkflowSourceBinding = codec.values.WorkspaceTreeEntryPin
    portable.WorkspaceWorkflowSourceBinding = codec.values.WorkspaceTreeEntryPin
    if {collect!r}:
        gc.set_threshold(1, 1, 1)
        gc.collect()
    actual, expected = outcome(codec), outcome(portable)
    assert actual == expected
    assert actual[0] == 'WorkspaceTreeProjectionValueError'
finally:
    gc.set_threshold(*prior_threshold)
    codec.WorkspaceWorkflowSourceBinding = original
    portable.WorkspaceWorkflowSourceBinding = original
assert codec.repository_tree_projection_value_to_json(value) == original_wire
codec.repository_tree_projection_value_validate_equal(value, expected_value=value)
""",
    )


@pytest.mark.parametrize(
    "change",
    (
        "native_class",
        "native_export",
        "runtime_export",
        "runtime_code",
        "runtime_defaults",
        "runtime_kwdefaults",
    ),
)
def test_receipt_invocation_proof_rechecks_after_original_child(native_sdk, change):
    run_receipt_native(
        native_sdk,
        f"""
# The admitted coordinate runs before context_refs and initializes the local
# declaration proof. This exercises a proof hit, rather than only first entry.
value = receipt_cases.capture()
original_refs = value.context_refs
original_native_class = native.__class__
original_export = native.convert_receipt
original_encode = receipt._encode
original_timestamp = receipt._timestamp
original_code = original_timestamp.__code__
original_defaults = original_timestamp.__defaults__
original_kwdefaults = original_timestamp.__kwdefaults__
calls = []
class NativeSubclass(types.ModuleType):
    pass
def foreign(*args, **kwargs):
    calls.append('foreign')
    return None
class Trigger:
    def __iter__(self):
        calls.append('original-iterator')
        change = {change!r}
        if change == 'native_class':
            native.__class__ = NativeSubclass
        elif change == 'native_export':
            native.convert_receipt = foreign
        elif change == 'runtime_export':
            receipt._encode = foreign
        elif change == 'runtime_code':
            original_timestamp.__code__ = foreign.__code__
        elif change == 'runtime_defaults':
            original_timestamp.__defaults__ = (None,)
        elif change == 'runtime_kwdefaults':
            original_timestamp.__kwdefaults__ = {{'unexpected': None}}
        else:
            raise AssertionError(change)
        return iter(())
object.__setattr__(value, 'context_refs', Trigger())
try:
    result = outcome(receipt, value)
    assert result[0] == 'TypeError', result
    assert calls == ['original-iterator'], calls
finally:
    native.__class__ = original_native_class
    native.convert_receipt = original_export
    receipt._encode = original_encode
    original_timestamp.__code__ = original_code
    original_timestamp.__defaults__ = original_defaults
    original_timestamp.__kwdefaults__ = original_kwdefaults
    object.__setattr__(value, 'context_refs', original_refs)
assert outcome(receipt, value) == outcome(baseline, value)
""",
    )


@pytest.mark.parametrize("restore", (False, True))
def test_receipt_invocation_proof_preserves_fresh_helper_history(native_sdk, restore):
    run_receipt_native(
        native_sdk,
        f"""
value = receipt_cases.capture()
original_refs = value.context_refs
original_encode = receipt._encode
calls = []
def foreign(*args, **kwargs):
    calls.append('foreign')
    raise AssertionError('foreign encoder ran')
class Trigger:
    def __iter__(self):
        calls.append('original-iterator')
        # A namespace version may move while its exact original bindings stay
        # unchanged. Only current associations are proved; no history authority.
        receipt._workspace_test_marker = None
        del receipt._workspace_test_marker
        if {restore!r}:
            receipt._encode = foreign
            receipt._encode = original_encode
        return iter(original_refs)
object.__setattr__(value, 'context_refs', Trigger())
try:
    before = receipt._type_hints.cache_info()
    first = outcome(receipt, value)
    middle = receipt._type_hints.cache_info()
    second = outcome(receipt, value)
    after = receipt._type_hints.cache_info()
    assert first == second == outcome(baseline, value)
    assert calls == ['original-iterator'] * 3, calls
    assert middle.hits > before.hits
    assert after.hits > middle.hits
finally:
    receipt._encode = original_encode
    object.__setattr__(value, 'context_refs', original_refs)
""",
    )


def test_ascii_batch_scans_all_paths_and_keeps_unknown_objects_unobserved(native_sdk):
    run_native(
        native_sdk,
        """
context=codec._TREE_NATIVE_HANDOFF[0]
limits={'maximum_path_utf8_bytes':1024,'maximum_metadata_bytes':1000000}
payload={'effect_paths':['later'],'read_guard_paths':['last']}
last=payload['read_guard_paths'][-1]
assert native.ascii_paths_last(context,['first'],payload,limits) is last
for paths in ([],['é'],['a//b'],[b'a'],['a'*256],['a']*16385):
    assert native.ascii_paths_last(context,paths,{'effect_paths':[],'read_guard_paths':[]},limits) is None
calls=[]
class Foreign:
    def __getattribute__(self,name):calls.append(name);raise RuntimeError('foreign')
class Paths(list):
    def __iter__(self):calls.append('iter');raise RuntimeError('foreign')
for value in (Foreign(),Paths(['a'])):
    assert native.ascii_paths_last(context,value,payload,limits) is None
assert native.ascii_paths_last(context,[Foreign()],payload,limits) is None
assert native.ascii_paths_last(Foreign(),['a'],payload,limits) is None
assert calls==[]
""",
    )


@pytest.mark.parametrize("change", ("export", "abi", "large_abi"))
@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_ascii_batch_retained_dispatch_rejects_export_substitution(
    native_sdk, change, mode
):
    run_native(
        native_sdk,
        f"""
context=codec._TREE_NATIVE_HANDOFF[0]
retained=native.ascii_paths_last
original_abi=native.ASCII_PATH_BATCH_ABI
calls=[]
def foreign(*args):
    calls.append('foreign')
    if {mode!r}=='restore':native.ascii_paths_last=retained
    if {mode!r}=='raise':raise RuntimeError('foreign')
    return 'accepted'
class ABI:
    def __eq__(self,other):calls.append('eq');raise RuntimeError('foreign ABI')
if {change!r}=='export':native.ascii_paths_last=foreign
elif {change!r}=='abi':native.ASCII_PATH_BATCH_ABI=ABI()
else:native.ASCII_PATH_BATCH_ABI=2**100
try:
    try:retained(context,['a'],{{'effect_paths':[],'read_guard_paths':[]}},{{'maximum_path_utf8_bytes':1024,'maximum_metadata_bytes':1000000}})
    except TypeError:pass
    else:raise AssertionError('substitution accepted')
finally:native.ascii_paths_last=retained;native.ASCII_PATH_BATCH_ABI=original_abi
assert calls==[]
""",
    )


@pytest.mark.parametrize("scenario", ("empty", "iterable", "collision", "custody"))
def test_ascii_batch_post_wire_callback_keeps_literal_loop_order(native_sdk, scenario):
    run_native(
        native_sdk,
        f"""
outputs=[]
for module in (portable,codec):
    payload=module.repository_tree_projection_value_to_payload(cases.binding())
    payload['scratch_effects']=[];payload['effect_paths']=[];payload['read_guard_paths']=[]
    events=[];original=json.dumps
    def selected(value,**kwargs):
        text=original(value,**kwargs);json.dumps=original
        if {scenario!r}=='empty':payload['limits'].pop('maximum_path_utf8_bytes')
        elif {scenario!r}=='iterable':
            class Paths:
                def __len__(self):events.append('len');return 1
                def __iter__(self):events.append('iter');return iter(['later'])
                def __radd__(self,other):events.append('radd');return self
            payload['read_guard_paths']=Paths();payload['limits'].pop('maximum_path_utf8_bytes')
        elif {scenario!r}=='collision':
            class Key:
                def __hash__(self):return hash('maximum_path_utf8_bytes')
                def __eq__(self,other):events.append('eq');return other=='maximum_path_utf8_bytes'
            payload['effect_paths']=['first','second'];payload['limits'].pop('maximum_path_utf8_bytes');payload['limits'][Key()]=1024
        else:
            class Remaining:
                def __lt__(self,other):events.append(sys._getframe(1).f_locals.get('path'));return False
            payload['effect_paths']=['final'];payload['limits']['maximum_metadata_bytes']=Remaining()
        return text
    json.dumps=selected
    try:
        try:result=module._sequence(payload);outcome=('ok',result)
        except BaseException as error:outcome=(type(error).__name__,error.args)
    finally:json.dumps=original
    outputs.append((outcome,events))
assert outputs[0]==outputs[1],outputs
if {scenario!r}=='custody':assert outputs[1][1][-1]=='final'
if {scenario!r}=='collision':assert outputs[1][1]==['eq','eq']
if {scenario!r}=='iterable':assert outputs[1][1]==['len','iter','radd','iter']
""",
    )


@pytest.mark.parametrize("binding", ("builtin", "global"))
@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_ascii_batch_declines_changed_effective_type_without_dispatch(
    native_sdk, binding, mode
):
    run_native(
        native_sdk,
        f"""
import builtins
context=codec._TREE_NATIVE_HANDOFF[0];original=builtins.str;calls=[]
def foreign(*args):
    calls.append('foreign')
    if {mode!r}=='restore':builtins.str=original
    if {mode!r}=='raise':raise RuntimeError('foreign')
    return original(*args)
if {binding!r}=='builtin':builtins.str=foreign
else:codec.str=foreign
try:result=native.ascii_paths_last(context,['a'],{{'effect_paths':[],'read_guard_paths':[]}},{{'maximum_path_utf8_bytes':1024,'maximum_metadata_bytes':1000000}})
finally:
    builtins.str=original
    if {binding!r}=='global':del codec.str
assert result is None and calls==[]
""",
    )


@pytest.mark.parametrize("binding", ("shadow", "unbound"))
def test_ascii_batch_declines_incomplete_preseal_effective_path_proof(
    native_sdk, binding
):
    run_native(
        native_sdk,
        f"""
name=codec.__name__;module=types.ModuleType(name);module.__package__=codec.__package__
original=sys.modules[name];original_abi=native.ASCII_PATH_POSITIVE_ABI;sys.modules[name]=module
injection="str = lambda *args: (_ for _ in ()).throw(RuntimeError('foreign str'))\\n" if {binding!r}=='shadow' else "_TREE_NATIVE_HANDOFF[1].__self__.ASCII_PATH_POSITIVE_ABI = 0\\n"
body=Path(codec.__file__).read_text().replace('_seal_native_tree_binding(globals(), _TREE_NATIVE_HANDOFF)',injection+'_seal_native_tree_binding(globals(), _TREE_NATIVE_HANDOFF)')
try:
    exec(compile(body,codec.__file__,'exec'),vars(module))
    assert module._TREE_NATIVE_HANDOFF is not None
    context=module._TREE_NATIVE_HANDOFF[0];native.verify(context)
    slot=next(item for item in module._sequence.__code__.co_consts if type(item)is tuple and len(item)==3 and item[0]=='__workspace_ascii_paths_slot_v1__')
    assert slot[1] is native.ascii_paths_last
    assert native.ascii_paths_last(context,['a'],{{'effect_paths':[],'read_guard_paths':[]}},{{'maximum_path_utf8_bytes':1024,'maximum_metadata_bytes':1000000}})is None
finally:sys.modules[name]=original;native.ASCII_PATH_POSITIVE_ABI=original_abi
""",
    )


@pytest.mark.parametrize(
    "change",
    ("union_equal", "union_other", "scalar", "tuple_other", "missing", "cache_clear"),
)
def test_native_receipt_fresh_declaration_rechecks_fresh_hint_dictionary(
    native_sdk, change
):
    run_receipt_native(
        native_sdk,
        f"""
value=receipt_cases._mutation_receipt()
object.__setattr__(value,'expected_content_digest','digest:original')
results=[]
for module in (receipt,baseline):
    module._type_hints.cache_clear()
    hints=module._type_hints(type(value))
    name='expected_content_digest'
    prior=hints[name]
    rows=[outcome(module,value),outcome(module,value)]
    try:
        if {change!r}=='union_equal':hints[name]=type(None)|str
        elif {change!r}=='union_other':hints[name]=int|None
        elif {change!r}=='scalar':hints[name]=str
        elif {change!r}=='tuple_other':hints[name]=tuple[int,...]
        elif {change!r}=='missing':del hints[name]
        else:module._type_hints.cache_clear()
        rows.extend((outcome(module,value),outcome(module,value)))
    finally:hints[name]=prior
    rows.append(outcome(module,value))
    module._type_hints.cache_clear()
    rows.append(outcome(module,value))
    results.append(rows)
assert results[0]==results[1],results
""",
    )


@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_native_receipt_fresh_declaration_keeps_later_hint_drift(native_sdk, mode):
    run_receipt_native(
        native_sdk,
        f"""
value=receipt_cases._mutation_receipt()
object.__setattr__(value,'expected_content_digest','digest:original')
cls=type(value)
slot=vars(cls)['target_path']
results=[]
for module in (receipt,baseline):
    module._type_hints.cache_clear()
    hints=module._type_hints(cls)
    prior=hints['expected_content_digest']
    assert outcome(module,value)[0]=='ok'
    calls=[]
    def access(instance):
        calls.append('target_path')
        hints['expected_content_digest']=int|None
        if {mode!r}=='restore':hints['expected_content_digest']=prior
        if {mode!r}=='raise':raise LookupError('same ordered hint movement')
        return slot.__get__(instance,cls)
    setattr(cls,'target_path',property(access))
    try:results.append((outcome(module,value),tuple(calls)))
    finally:
        setattr(cls,'target_path',slot)
        hints['expected_content_digest']=prior
assert results[0]==results[1],results
assert results[0][1]
""",
    )


def test_native_receipt_fresh_declaration_does_not_retain_retired_hint_objects(
    native_sdk,
):
    run_receipt_native(
        native_sdk,
        """
value=receipt_cases._mutation_receipt()
cls=type(value)
for module in (receipt,baseline):
    module._type_hints.cache_clear()
    hints=module._type_hints(cls)
    prior=hints['context_refs']
    class Origin:pass
    alias=types.GenericAlias(Origin,(str,))
    handle=weakref.ref(alias)
    hints['context_refs']=alias
    outcome(module,value)
    hints['context_refs']=prior
    del alias
    gc.collect()
    assert handle() is None
""",
    )


def test_native_receipt_fresh_declaration_alternate_private_names_remain_literal(
    native_sdk,
):
    run_receipt_native(
        native_sdk,
        """
value=receipt_cases._mutation_receipt()
context=receipt._RECEIPT_NATIVE_HANDOFF[0]
config=next(v for v in gc.get_referents(context)if type(v)is tuple and len(v)==9)
fixed=list(config[3]);fixed[7]='fake_args';fixed[8]='fake_origin'
raw=(config[0],config[1],config[2],tuple(fixed),config[4],config[6],config[7])
new_context=native.new_receipt_context();native.seal_receipts(new_context,raw)
entry=receipt._RECEIPT_FIELDS_BY_ID[id(type(value))]
hints={row[1]:str for row in entry[1]}
class OriginMeta(type):
    @property
    def fake_origin(cls):calls.append('origin');return tuple
    @property
    def fake_args(cls):calls.append('args');return(str,Ellipsis)
class Origin(metaclass=OriginMeta):pass
hints['context_refs']=types.GenericAlias(Origin,(str,Ellipsis))
calls=[]
first=native.convert_receipt(new_context,value,entry,receipt._RECEIPT_FIELDS_BY_ID,hints)
second=native.convert_receipt(new_context,value,entry,receipt._RECEIPT_FIELDS_BY_ID,hints)
assert first==second
assert calls==['origin','args','origin','args'],calls
""",
    )


@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_native_receipt_fresh_declaration_same_record_reentry_keeps_outer_hints(
    native_sdk, mode
):
    run_receipt_native(
        native_sdk,
        f"""
value=receipt_cases._mutation_receipt()
cls=type(value)
old_refs=value.context_refs
results=[]
for module in (receipt,baseline):
    module._type_hints.cache_clear()
    hints_a=module._type_hints(cls)
    assert outcome(module,value)[0]=='ok'
    calls=[]
    class Rows:
        def __iter__(self):
            calls.append('outer-iterate')
            module._type_hints.cache_clear()
            hints_b=module._type_hints(cls)
            assert hints_b is not hints_a
            prior=hints_b['result_content_digest']
            hints_b['result_content_digest']=int|None
            inner=copy.copy(value)
            object.__setattr__(inner,'context_refs',old_refs)
            calls.append(('inner',outcome(module,inner)))
            if {mode!r}=='restore':hints_b['result_content_digest']=prior
            if {mode!r}=='raise':raise LookupError('same original reentry interruption')
            return iter(old_refs)
    object.__setattr__(value,'context_refs',Rows())
    try:
        outer=outcome(module,value)
        object.__setattr__(value,'context_refs',old_refs)
        later=outcome(module,value)
        module._type_hints.cache_clear()
        restored=outcome(module,value)
        results.append((outer,later,restored,tuple(calls)))
    finally:object.__setattr__(value,'context_refs',old_refs)
assert results[0]==results[1],results
assert results[0][3][0]=='outer-iterate'
""",
    )


def test_native_receipt_fresh_declaration_warm_field_name_movement_stays_fresh(
    native_sdk,
):
    run_receipt_native(
        native_sdk,
        """
value=receipt_cases._mutation_receipt()
object.__setattr__(value,'expected_content_digest','digest:original')
field=type(value).__dataclass_fields__['expected_content_digest']
prior=field.name
results=[]
for module in (receipt,baseline):
    module._type_hints.cache_clear()
    rows=[outcome(module,value),outcome(module,value)]
    try:
        field.name='result_content_digest'
        rows.extend((outcome(module,value),outcome(module,value)))
    finally:field.name=prior
    rows.append(outcome(module,value))
    results.append(rows)
assert results[0]==results[1],results
""",
    )


@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_native_receipt_fresh_declaration_nonbuiltin_alias_keeps_original_callbacks(
    native_sdk, mode
):
    run_receipt_native(
        native_sdk,
        f"""
value=receipt_cases._mutation_receipt()
results=[]
for module in (receipt,baseline):
    module._type_hints.cache_clear()
    hints=module._type_hints(type(value))
    prior=hints['context_refs']
    assert outcome(module,value)[0]=='ok'
    calls=[]
    class Alias(types.GenericAlias):
        def __getattribute__(self,name):
            calls.append(name)
            if {mode!r}=='restore':hints['context_refs']=prior
            if {mode!r}=='raise':raise LookupError('same original alias attribute')
            return super().__getattribute__(name)
    hints['context_refs']=Alias(tuple,(str,Ellipsis))
    try:results.append((outcome(module,value),tuple(calls)))
    finally:hints['context_refs']=prior
assert results[0]==results[1],results
assert results[0][1]
""",
    )


@pytest.mark.parametrize("mode", ("return", "raise", "restore"))
def test_native_receipt_fresh_declaration_custom_original_field_name_keeps_key_callbacks(
    native_sdk, mode
):
    run_receipt_native(
        native_sdk,
        f"""
value=receipt_cases._mutation_receipt()
object.__setattr__(value,'expected_content_digest','digest:original')
cls=type(value)
field=cls.__dataclass_fields__['expected_content_digest']
prior=field.name
calls=[]
armed=False
class Key(str):
    def __hash__(self):
        if armed:
            calls.append('hash')
            if {mode!r}=='restore':field.name=prior
            if {mode!r}=='raise':raise LookupError('same original key callback')
        return str.__hash__(self)
source=Path(receipt.__file__).read_bytes()
results=[]
try:
    field.name=Key(prior)
    clone=types.ModuleType('aware_workspace_runtime._receipt_shape_foreign_key')
    clone.__package__='aware_workspace_runtime'
    sys.modules[clone.__name__]=clone
    exec(compile(source,'<receipt-shape-foreign-key>', 'exec'),vars(clone))
    assert clone._RECEIPT_NATIVE_HANDOFF is not None
    key=field.name
    for module in (clone,baseline):
        field.name=key
        module._type_hints.cache_clear()
        assert outcome(module,value)[0]=='ok'
        calls=[]
        armed=True
        try:results.append((outcome(module,value),tuple(calls)))
        finally:armed=False
    assert results[0]==results[1],results
    assert results[0][1]
finally:field.name=prior
""",
    )


@pytest.mark.parametrize("replacement", ("missing", "none", "foreign"))
def test_native_receipt_fresh_declaration_deleted_warm_field_name_preserves_refusal(
    native_sdk, replacement
):
    run_receipt_native(
        native_sdk,
        f"""
from aware_workspace_runtime.repository_access import RepositoryObservationCoordinate
cls=RepositoryObservationCoordinate
value=cls('owner','epoch',0,'digest','policy','version')
field=cls.__dataclass_fields__['repository_binding_ref']
prior=field.name
results=[]
for module in (receipt,baseline):
    module._type_hints.cache_clear()
    rows=[outcome(module,value),outcome(module,value)]
    try:
        if {replacement!r}=='missing':del field.name
        elif {replacement!r}=='none':field.name=None
        else:field.name=object()
        rows.extend((outcome(module,value),outcome(module,value)))
    finally:field.name=prior
    rows.append(outcome(module,value))
    results.append(rows)
assert results[0]==results[1],results
assert results[0][2][0]!='ok',results
""",
    )
