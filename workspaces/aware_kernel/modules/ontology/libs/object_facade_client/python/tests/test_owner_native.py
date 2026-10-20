"""Original owner-state native profile: fresh reads, parity and lifetime."""

import gc
from pathlib import Path
from types import CodeType, FunctionType

import pytest
from aware_ontology_object_facade_client import owner_values as owner
from test_owner_body_parity import _legacy_scan, _scan_cells


@pytest.fixture
def native():
    if owner._owner_native_scan_module is None:
        pytest.skip("requires the separately locked native artifact")
    return owner._owner_native_scan_module


@pytest.mark.parametrize(
    "name",
    ("_shape_guard", "_binding_guard", "_record_guard", "_abi_guard", "_attempt_guard"),
)
def test_original_owner_code_and_allocation_currentness(native, name):
    check = getattr(owner, name)
    assert native.scan_owner in check.__code__.co_consts
    assert native.scan_owner(check, check.__code__) is True
    clone = FunctionType(check.__code__, check.__globals__, closure=check.__closure__)
    assert native.scan_owner(clone, clone.__code__) is False
    assert native.scan_owner(check, check.__code__.replace(co_firstlineno=1)) is False
    oracle = _legacy_scan(check, owner, 2194)
    oracle()
    check()
    gc.collect()
    assert native.scan_owner(check, check.__code__) is True


def test_owner_installer_binding_is_one_use_and_executable_fields_unchanged(native):
    code = compile(Path(owner.__file__).read_bytes(), owner.__file__, "exec")
    outer = next(
        c
        for c in code.co_consts
        if type(c) is CodeType and c.co_name == "_protect_shape_dispatch"
    )
    installer = FunctionType(outer, owner.__dict__)
    before = installer.__code__
    check = next(
        c for c in before.co_consts if type(c) is CodeType and c.co_name == "check"
    )
    native.bind_owner_installer(installer)
    after = installer.__code__
    replacement = next(
        c for c in after.co_consts if type(c) is CodeType and c.co_name == "check"
    )
    for field in (
        "co_code",
        "co_freevars",
        "co_cellvars",
        "co_names",
        "co_varnames",
        "co_linetable",
        "co_exceptiontable",
    ):
        assert getattr(before, field) == getattr(after, field)
        assert getattr(check, field) == getattr(replacement, field)
    for old, new in zip(check.co_consts, replacement.co_consts, strict=True):
        assert new is (
            native.scan_owner
            if type(old) is str and old == "__aware_native_owner_scan_anchor_v1__"
            else old
        )
    with pytest.raises(RuntimeError):
        native.bind_owner_installer(installer)
    assert installer.__code__ is after


@pytest.mark.parametrize(
    "name",
    ("_shape_guard", "_binding_guard", "_record_guard", "_abi_guard", "_attempt_guard"),
)
def test_each_physical_closure_slot_is_freshly_read_after_every_return(
    native, monkeypatch, name
):
    check = getattr(owner, name)
    rows = _scan_cells(check)["cell_plan"][0]
    assert len(rows) == len({id(cell) for cell, _ in rows})
    check()
    cell, expected = rows[0]
    foreign = object()
    with monkeypatch.context() as patch:
        patch.setattr(cell, "cell_contents", foreign)
        assert native.scan_owner(check, check.__code__) is False
        with pytest.raises(TypeError):
            check()
    assert cell.cell_contents is expected
    check()


def test_scanner_retains_no_positive_admission_or_class_dictionary_reference(native):
    import sys

    check = owner._abi_guard
    target = owner.ValueShape
    dictionary = gc.get_referents(vars(target))[0]
    assert type(dictionary) is dict
    before = sys.getrefcount(dictionary)
    for _ in range(200):
        assert native.scan_owner(check, check.__code__) is True
    assert sys.getrefcount(dictionary) == before
    assert native.scan_owner(None, None) is False


def test_substituted_descriptor_class_refuses_before_foreign_access(native):
    check = owner._abi_guard
    target = next(
        target
        for target, _ in _scan_cells(check)["descriptors"]
        if type(target) is not property
    )
    original = type(target)
    calls = []

    class Foreign:
        @property
        def fget(self):
            calls.append("foreign")
            raise AssertionError("foreign descriptor executed")

    target.__class__ = Foreign
    try:
        assert native.scan_owner(check, check.__code__) is False
        with pytest.raises(TypeError):
            check()
        assert calls == []
    finally:
        target.__class__ = original
    check()


@pytest.mark.parametrize("representation", ("holes", "general", "same_text", "foreign_key", "changed_value"))
def test_combined_namespace_and_general_fallback_preserve_original_admission(native, representation):
    check = owner._attempt_guard
    code = check.__code__
    scan = native.scan_owner
    namespace = vars(owner)
    original = tuple(namespace.items())
    key, value = original[-1]
    changed = object()

    class ForeignKey(str):
        pass

    # These mutations are setup, not operations performed by the scanner.
    if representation == "holes":
        namespace["_temporary_native_hole_"] = None
        del namespace["_temporary_native_hole_"]
    elif representation == "general":
        namespace[changed] = None
        del namespace[changed]
    elif representation in {"same_text", "foreign_key"}:
        del namespace[key]
        replacement = (" " + key)[1:] if representation == "same_text" else ForeignKey(key)
        assert replacement == key and replacement is not key
        namespace[replacement] = value
    else:
        namespace[key] = changed
    try:
        assert scan(check, code) is (representation not in {"foreign_key", "changed_value"})
    finally:
        namespace.clear()
        namespace.update(original)
    assert scan(check, code) is True
