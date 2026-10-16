"""Native C shape/guard correspondence, never live authority or installed proof."""

from __future__ import annotations

import ast
import dataclasses
import json
import subprocess
from pathlib import Path

import pytest
from aware_file_system import confined_mutation as values

ROOT = next(
    parent
    for parent in Path(__file__).parents
    if (parent / "aware.repo.toml").is_file()
)
NAMES = (
    "ConfinedTreeEntryPin",
    "ConfinedTreeFileTransition",
    "ConfinedTreeAncestorTransition",
    "ConfinedTreeLimits",
    "ConfinedTreeProjectionRequest",
    "ConfinedTreePreparationObservation",
    "ConfinedTreePhysicalEffect",
    "ConfinedTreeTransitionResult",
    "ConfinedTreeEffectObservation",
    "ConfinedTreeCleanupObservation",
    "ConfinedTreeResourceCleanup",
)


def create(path="file", body=b"body", mode=0o644):
    return values.ConfinedTreeFileTransition(
        path,
        values.ConfinedMutationKind.CREATE,
        values.ConfinedTreeEntryPin(False),
        body,
        values._content_digest(body),
        len(body),
        mode,
    )


@pytest.mark.parametrize("name", NAMES)
def test_all_physical_root_fields_match_accepted_c_and_are_immutable(name):
    packet = json.loads(
        (
            ROOT
            / "docs/reports/workspace-repository-tree-projection-inputs-20261011.json"
        ).read_text()
    )
    cls = getattr(values, name)
    fields = tuple(field.name for field in dataclasses.fields(cls))
    assert fields == tuple(
        packet["joined_freeze_candidate"]["supplier_schemas"][name]["fields"]
    )
    assert cls.__dataclass_params__.frozen
    assert "__dict__" not in cls.__slots__


@pytest.mark.parametrize("kind", tuple(values.ConfinedMutationKind))
def test_native_content_keeps_exact_kind_and_delete_has_no_successor(kind):
    before = values.ConfinedTreeEntryPin(
        True, 1, 2, 3, 4, 5, 0o640, 1, values._content_digest(b"old")
    )
    if kind is values.ConfinedMutationKind.CREATE:
        row = create()
    elif kind is values.ConfinedMutationKind.DELETE:
        row = values.ConfinedTreeFileTransition(
            "file", kind, before, None, None, None, None
        )
    else:
        row = values.ConfinedTreeFileTransition(
            "file", kind, before, b"new", values._content_digest(b"new"), 3, 0o755
        )
    assert type(row.kind) is values.ConfinedMutationKind
    if row.content is not None:
        assert row.content_digest == values._content_digest(row.content)
        with pytest.raises(TypeError):
            json.dumps(dataclasses.asdict(row))


@pytest.mark.parametrize("bad", (True, 0o600, 0o777, 0o1644, None, "0644"))
def test_successor_modes_are_exact_c_modes_not_coerced(bad):
    with pytest.raises(ValueError):
        create(mode=bad)


@pytest.mark.parametrize("bad", (True, 1, None, "false"))
def test_absence_is_exact_and_carries_no_invented_preimage(bad):
    with pytest.raises(ValueError):
        values.ConfinedTreeEntryPin(bad)
    with pytest.raises(ValueError):
        values.ConfinedTreeEntryPin(False, device=1)


@pytest.mark.parametrize(
    "field",
    tuple(field.name for field in dataclasses.fields(values.ConfinedTreeLimits)),
)
def test_conjunctive_limits_reject_zero_boolean_and_beyond_each_ceiling(field):
    original = values.ConfinedTreeLimits()
    for bad in (0, True, -1, getattr(original, field) + 1):
        with pytest.raises(ValueError):
            dataclasses.replace(original, **{field: bad})


@pytest.mark.parametrize(
    "path",
    (
        "/file",
        "a//file",
        "../file",
        "a/../file",
        "a\\file",
        "e\u0301/file",
        "a\u0080file",
        "a" * 1025,
    ),
)
def test_invalid_paths_refuse_before_any_factory_or_io(path):
    with pytest.raises(ValueError):
        create(path)


@pytest.mark.parametrize("components", (64, 65, 128, 512))
def test_native_c_paths_do_not_derive_depth_from_descriptor_budget(components):
    path = "/".join(["a"] * components)
    assert len(path.encode("utf-8")) <= 1024
    assert create(path).path == path


def test_preserve_ancestor_never_requests_chmod_or_relabels_file_pin():
    before = values.ConfinedTreeEntryPin(True, 1, 2, 3, 4, 5, 0o700, 2)
    assert (
        values.ConfinedTreeAncestorTransition(
            "a", "preserve", before, None
        ).requested_mode
        is None
    )
    with pytest.raises(ValueError):
        values.ConfinedTreeAncestorTransition("a", "preserve", before, 0o755)
    with pytest.raises(ValueError):
        values.ConfinedTreeAncestorTransition("a", "create", before, 0o755)


def test_sequence_canonical_order_and_explicit_ancestor_guards_are_not_scope_permission():
    ancestor = values.ConfinedTreeAncestorTransition(
        "a", "create", values.ConfinedTreeEntryPin(False), 0o755
    )
    row = create("a/file")
    assert values.ConfinedTreeProjectionRequest(
        "request", (1, 2), (row,), (ancestor,)
    ).files == (row,)
    for files, ancestors in (
        ((row,), ()),
        ((row, row), (ancestor,)),
        ((create("a"),), (ancestor,)),
    ):
        with pytest.raises(ValueError):
            values.ConfinedTreeProjectionRequest("request", (1, 2), files, ancestors)


def test_requested_body_and_preimage_combined_quota_is_not_per_side():
    limits = dataclasses.replace(
        values.ConfinedTreeLimits(), maximum_combined_body_bytes=3
    )
    with pytest.raises(ValueError):
        values.ConfinedTreeProjectionRequest(
            "request", (1, 2), (create(body=b"four"),), (), limits
        )
    limits = dataclasses.replace(limits, maximum_combined_body_bytes=5)
    before = values.ConfinedTreeEntryPin(
        True, 1, 2, 3, 4, 5, 0o644, 1, values._content_digest(b"old")
    )
    row = values.ConfinedTreeFileTransition(
        "file",
        values.ConfinedMutationKind.UPDATE,
        before,
        b"new",
        values._content_digest(b"new"),
        3,
        0o644,
    )
    with pytest.raises(ValueError):
        values.ConfinedTreeProjectionRequest("request", (1, 2), (row,), (), limits)


def test_original_reader_writer_and_read_disposal_algorithms_are_preserved():
    path = "workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/confined_mutation.py"
    original = subprocess.check_output(
        ["git", "show", "cadb609524b16f8f4371dbabf4532b257aa70429:" + path],
        cwd=ROOT,
        text=True,
    )
    old = {
        node.name: node
        for node in ast.parse(original).body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    current = {
        node.name: node
        for node in ast.parse((ROOT / path).read_text()).body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }

    class DefaultIO(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if node.name == "_write_temporary":
                assert node.args.kwonlyargs[-1].arg == "_io"
                assert ast.dump(node.args.kw_defaults[-1]) == ast.dump(
                    ast.Name(id="os", ctx=ast.Load())
                )
                node.args.kwonlyargs.pop()
                node.args.kw_defaults.pop()
            if node.name == "open":
                assert node.args.kwonlyargs[-1].arg == "mode"
                node.args.kwonlyargs.pop()
                node.args.kw_defaults.pop()
            return self.generic_visit(node)

        def visit_Name(self, node):
            if node.id == "_io":
                node.id = "os"
            return node

        def visit_If(self, node):
            if (
                isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "mode"
            ):
                assert ast.unparse(node.test) == "mode is None"
                return node.body
            return self.generic_visit(node)

    # C records the original IO through private optional inputs. Removing only
    # those inputs leaves the original default algorithms exactly unchanged.
    for name in ("_write_temporary", "_ReadLedger"):
        current[name] = DefaultIO().visit(current[name])
    for name in (
        "mutate_confined_file",
        "_read_current",
        "_write_temporary",
        "_ReadLedger",
        "observe_confined_file_with_cleanup",
    ):
        assert ast.dump(old[name], include_attributes=False) == ast.dump(
            current[name], include_attributes=False
        )


def test_physical_modules_have_no_upward_issue_workspace_protocol_imports():
    folder = Path(values.__file__).parent
    for name in ("confined_mutation.py", "retained_tree_projection.py"):
        parsed = ast.parse((folder / name).read_text())
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                roots = [(node.module or "").split(".")[0]]
            else:
                continue
            assert not any(
                root.startswith(("aware_issue", "aware_workspace", "aware_protocol"))
                for root in roots
            )
