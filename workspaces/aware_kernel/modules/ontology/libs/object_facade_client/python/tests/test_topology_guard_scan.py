"""Fresh live-view scanning without re-expanding immutable tuple slots."""

import pytest
from aware_ontology_object_facade_client import topology_values as values
from test_owner_body_parity import _legacy_scan, _scan_cells


def _guard():
    return _scan_cells(_scan_cells(values._call)["checked"])["guard"]


def _nested_mutable(kind):
    plans = _scan_cells(_guard())["container_plans"]
    pending = [row[0] for row in plans if type(row[0]) is tuple]
    seen = set()
    while pending:
        item = pending.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        if type(item) is kind:
            return item
        if type(item) is tuple:
            pending.extend(item)
    raise AssertionError(f"missing retained tuple containing {kind}")


def test_immutable_tuple_discovery_keeps_all_mutable_descendants():
    state = _scan_cells(_guard())
    plans = state["container_plans"]
    mutable = {id(row[0]) for row in plans if type(row[0]) in (dict, list)}
    assert len(plans) == (len(state["dictionary_targets"])
                          + len(state["sequence_targets"])
                          + state["immutable_sequence_count"])
    assert all(type(item) is list for item in state["sequence_targets"])
    assert state["immutable_sequence_count"] > 0
    pending = [row[0] for row in plans if type(row[0]) is tuple]
    seen = set()
    found = set()
    while pending:
        item = pending.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        if type(item) in (dict, list):
            assert id(item) in mutable
            found.add(type(item))
            pending.extend(item.values() if type(item) is dict else item)
        elif type(item) is tuple:
            pending.extend(item)
    assert dict in found
    _guard()()


@pytest.mark.parametrize("kind", (dict, list))
@pytest.mark.parametrize("raising", (False, True))
def test_mutable_descendants_and_lists_still_refuse_without_foreign_behavior(kind, raising):
    guard = _guard()
    original = _legacy_scan(guard, values, 1219)
    item = (_nested_mutable(dict) if kind is dict else next(
        row[0] for row in _scan_cells(guard)["container_plans"] if type(row[0]) is list))
    calls = []

    class Foreign:
        def __eq__(self, _other):
            calls.append("eq")
            if raising:
                raise RuntimeError("foreign equality")
            return False

        def __bool__(self):
            calls.append("bool")
            raise RuntimeError("foreign truth test")

    guard()
    original()
    if kind is dict:
        item["_fresh_guard_scan_probe_"] = Foreign()
    else:
        item.append(Foreign())
    try:
        for check in (guard, original):
            with pytest.raises(TypeError):
                check()
        assert calls == []
    finally:
        if kind is dict:
            del item["_fresh_guard_scan_probe_"]
        else:
            item.pop()
    guard()
    original()


@pytest.mark.parametrize("owner", ("module", "class"))
def test_retained_namespace_views_observe_live_mutations(owner):
    guard = _guard()
    state = _scan_cells(guard)
    if owner == "module":
        target = values
        view = state["module_namespaces"][state["module_targets"].index(target)]
    else:
        target = values.GraphTypeBinding
        view = state["class_namespaces"][state["class_targets"].index(target)]
    key = "_fresh_guard_live_view_probe_"
    marker = object()
    guard()
    setattr(target, key, marker)
    try:
        assert view[key] is marker  # A live owner view, not a namespace copy.
        with pytest.raises(TypeError):
            guard()
    finally:
        delattr(target, key)
    guard()


def test_incoming_immutable_tuple_identity_is_still_freshly_checked():
    guard = _guard()
    cell, original = next((cell, expected)
                          for cell, expected in _scan_cells(guard)["cell_plan"][0]
                          if type(expected) is tuple and len(expected) > 0)
    replacement = (*original,)
    assert replacement is not original
    guard()
    try:
        cell.cell_contents = replacement
        with pytest.raises(TypeError):
            guard()
    finally:
        cell.cell_contents = original
    guard()
