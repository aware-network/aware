"""Private native profile proofs; run against an admitted compiled source cut."""

import gc
import sys
from pathlib import Path
from types import CodeType, FunctionType

import pytest
from aware_ontology_object_facade_client import codec
from aware_ontology_object_facade_client import preparation as p


@pytest.fixture
def native():
    assert p._native_scan_module is not None, (
        "native proof requires its compiled artifact"
    )
    return p._native_scan_module


def _entry_arguments():
    check = p._preparation_check
    cells = dict(zip(check.__code__.co_freevars, check.__closure__, strict=True))
    retained = {name: cell.cell_contents for name, cell in cells.items()}
    return (
        check,
        check.__code__,
        retained["native_map"],
        retained["native_zip"],
        retained["native_type"],
        retained["length"],
        retained["get"],
        retained["get_dict"],
        retained["class_get"],
        retained["native_id"],
        retained["native_tuple"],
        retained["native_any"],
        retained["dict_keys"],
        retained["dict_items"],
    ), retained


def _unbound_installer():
    source = Path(p.__file__)
    module_code = compile(source.read_bytes(), str(source), "exec")
    installer_code = next(
        item
        for item in module_code.co_consts
        if type(item) is CodeType and item.co_name == "_install_preparation_dispatch"
    )
    return FunctionType(installer_code, p.__dict__)


def _checker(code):
    return next(
        item
        for item in code.co_consts
        if type(item) is CodeType and item.co_name == "check"
    )


def test_installed_native_entry_is_retained_in_authenticated_code(native):
    check = p._preparation_check
    assert any(item is native.scan for item in check.__code__.co_consts)
    assert any(item is native.fingerprint for item in check.__code__.co_consts)
    assert "__aware_native_preparation_scan_anchor_v1__" not in check.__code__.co_consts
    assert check() is None


def test_repeated_native_checks_release_type_dictionary_references(native):
    del native
    arguments, retained = _entry_arguments()
    classes = [type, object, dict, *(row[0] for row in retained["class_rows"])]
    dictionaries = [gc.get_referents(cls.__dict__)[0] for cls in classes]
    check = arguments[0]
    check()
    before = [sys.getrefcount(dictionary) for dictionary in dictionaries]
    for _ in range(100):
        check()
    assert [sys.getrefcount(dictionary) for dictionary in dictionaries] == before


def test_complete_native_scan_preserves_declared_field_observations(native):
    arguments, retained = _entry_arguments()
    assert native.scan(*arguments) is True
    report = native.observe(*arguments, True)
    assert report["accepted"] is True
    function_groups = (retained["function_rows"], retained["receiver_function_rows"])
    functions = [row for group in function_groups for row in group]
    assert report["function_rows"] == len(functions)
    assert report["function_fixed_reads"] == 4 * len(functions)
    assert report["function_metadata_reads"] == sum(len(row[5]) for row in functions)
    assert report["cell_contents_reads"] == sum(len(row[6]) for row in functions)
    assert report["data_rows"] == len(retained["data_rows"]) + len(
        retained["receiver_data_rows"]
    )
    expected = []
    for group_index, group in enumerate(function_groups):
        for row_index, row in enumerate(group):
            target, code, defaults, kwdefaults, _attributes, metadata, cells = row
            for position, (label, value) in enumerate(
                (
                    ("function.code", code),
                    ("function.defaults", defaults),
                    ("function.kwdefaults", kwdefaults),
                    ("function.dict", target.__dict__),
                )
            ):
                expected.append((label, group_index, row_index, position, id(value)))
            expected.extend(
                ("function.metadata", group_index, row_index, position, id(value))
                for position, (_, value) in enumerate(metadata)
            )
            expected.extend(
                ("cell.contents", group_index, row_index, position, id(value))
                for position, (_, value) in enumerate(cells)
            )
    actual = [
        tuple(event)
        for event in report["trace"]
        if event[0].startswith("function.") or event[0] == "cell.contents"
    ]
    assert actual == expected


@pytest.mark.parametrize("value", ({"key": "value"}, [None, True, 1, "text"], {}))
def test_native_profile_preserves_public_canonical_roundtrip(native, value):
    del native
    body = codec.canonical_bytes(value)
    assert codec.decode_canonical(body) == value


def test_binding_changes_constants_only_and_repeated_binding_refuses(native):
    installer = _unbound_installer()
    before = installer.__code__
    before_check = _checker(before)
    native.bind_installer(installer)
    after = installer.__code__
    after_check = _checker(after)
    fields = (
        "co_argcount",
        "co_posonlyargcount",
        "co_kwonlyargcount",
        "co_nlocals",
        "co_stacksize",
        "co_flags",
        "co_code",
        "co_names",
        "co_varnames",
        "co_filename",
        "co_name",
        "co_qualname",
        "co_firstlineno",
        "co_linetable",
        "co_exceptiontable",
        "co_freevars",
        "co_cellvars",
    )
    for original, bound in ((before, after), (before_check, after_check)):
        for field in fields:
            assert getattr(original, field) == getattr(bound, field), field
    for original, bound in zip(before.co_consts, after.co_consts, strict=True):
        if original is before_check:
            assert bound is after_check
        elif (
            type(original) is str
            and original == "__aware_native_preparation_plan_ports_v1__"
        ):
            assert type(bound) is tuple and len(bound) == 2
            assert bound[0] is native.core_plan_create
            assert bound[1] is native.core_plan_finalize
        else:
            assert bound is original
    anchors = {
        "__aware_native_preparation_scan_anchor_v1__": native.scan,
        "__aware_native_preparation_state_anchor_v1__": native.fingerprint,
    }
    for original, bound in zip(
        before_check.co_consts, after_check.co_consts, strict=True
    ):
        expected = (
            anchors.get(original, original) if type(original) is str else original
        )
        assert bound is expected
    with pytest.raises(RuntimeError):
        native.bind_installer(installer)
    assert installer.__code__ is after


@pytest.mark.parametrize(
    "shape",
    (
        "missing_check",
        "duplicate_check",
        "missing_anchor",
        "duplicate_anchor",
        "missing_state_anchor",
        "duplicate_state_anchor",
    ),
)
def test_ambiguous_binding_refuses_without_changing_installer(native, shape):
    installer = _unbound_installer()
    outer = installer.__code__
    check = _checker(outer)
    constants = outer.co_consts
    if shape == "missing_check":
        constants = tuple(item for item in constants if item is not check)
    elif shape == "duplicate_check":
        constants += (check,)
    else:
        anchor = (
            "__aware_native_preparation_state_anchor_v1__"
            if "state" in shape
            else "__aware_native_preparation_scan_anchor_v1__"
        )
        changed = (
            tuple(item for item in check.co_consts if item != anchor)
            if shape.startswith("missing")
            else (*check.co_consts, anchor)
        )
        replacement = check.replace(co_consts=changed)
        constants = tuple(replacement if item is check else item for item in constants)
    installer.__code__ = outer.replace(co_consts=constants)
    supplied_code = installer.__code__
    with pytest.raises(RuntimeError):
        native.bind_installer(installer)
    assert installer.__code__ is supplied_code


"""Additional actual native observation controls; no inherited pass transfer."""

_SHAPES = tuple((kind, size) for kind in (tuple, list, dict, set, frozenset)
                for size in (0, 1, 3, 8))


@pytest.mark.parametrize("kind,size,mismatch", tuple(
    (kind, size, mismatch) for kind, size in _SHAPES
    for mismatch in ("none", "first", "last", "cardinality")
    if size or mismatch in ("none", "cardinality")))
def test_native_data_row_fresh_identity_order_and_first_refusal(native, kind, size, mismatch):
    arguments, _retained = _entry_arguments()
    objects = tuple(object() for _ in range(size))
    value = dict(zip(objects, objects, strict=True)) if kind is dict else kind(objects)
    expected = native.fingerprint(value)
    identities = list(expected[1])
    if mismatch == "cardinality":
        identities.append((0, 0) if kind is dict else 0)
    elif mismatch != "none":
        index = 0 if mismatch == "first" else size - 1
        identities[index] = (0, identities[index][1]) if kind is dict else 0
    altered_expectation = (expected[0], tuple(identities))
    cells = dict(zip(arguments[0].__code__.co_freevars, arguments[0].__closure__, strict=True))
    cell = cells["data_rows"]
    original = cell.cell_contents
    try:
        cell.cell_contents = (*original, (value, altered_expectation))
        report = native.observe(*arguments, True)
    finally:
        cell.cell_contents = original
    assert native.scan(*arguments) is True
    assert report["accepted"] is (mismatch == "none")
    actual = [tuple(event) for event in report["trace"]
              if event[0].startswith("data.") and event[1:3] == (0, len(original))]
    observed = []
    if mismatch != "cardinality":
        for index, item in enumerate(value):
            if kind is dict:
                observed.extend((("data.key", 0, len(original), index, id(item)),
                                 ("data.value", 0, len(original), index, id(value[item]))))
            else:
                observed.append(("data.item", 0, len(original), index, id(item)))
            if mismatch == "first" or (mismatch == "last" and index == size - 1):
                break
    assert actual == observed


@pytest.mark.parametrize("kind,size", _SHAPES)
def test_native_scan_does_not_call_python_element_primitives(native, kind, size):
    arguments, _retained = _entry_arguments()
    values = tuple(object() for _ in range(size))
    value = dict(zip(values, values, strict=True)) if kind is dict else kind(values)
    expected = native.fingerprint(value)
    cells = dict(zip(arguments[0].__code__.co_freevars, arguments[0].__closure__, strict=True))
    cell = cells["data_rows"]
    original = cell.cell_contents
    events = []
    scan = native.scan
    def observe(frame, event, target):
        events.append((event, target is scan))
    previous = sys.getprofile()
    try:
        cell.cell_contents = (*original, (value, expected))
        sys.setprofile(observe)
        accepted = scan(*arguments)
        sys.setprofile(previous)
    finally:
        sys.setprofile(previous)
        cell.cell_contents = original
    assert accepted is True
    assert events[:2] == [("c_call", True), ("c_return", True)]
    assert events[2:] == [("c_call", False)]  # Restoring the original profiler.
    assert native.scan(*arguments) is True
