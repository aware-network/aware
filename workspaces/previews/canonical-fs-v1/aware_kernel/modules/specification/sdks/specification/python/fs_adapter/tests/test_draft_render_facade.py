"""Pure owner delegation and source facade, never installed authoring proof."""

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import aware_specification_fs_sdk_adapter as facade
import pytest
from aware_specification_fs_adapter import SpecificationFsSchemaResolutionContext
from aware_specification_fs_sdk_adapter import draft
from aware_specification_runtime import (
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationPhaseDefinition,
    SpecificationPhaseGateDefinition,
)
from aware_specification_sdk import (
    SpecificationDraftRequest,
    SpecificationOperationError,
)

ROOT = Path(__file__).resolve().parents[9]


@pytest.fixture
def request_value():
    gate = SpecificationPhaseGateDefinition(
        "reviewed", "The bounded contract is reviewed.", "contract", "evidence"
    )
    meaning = SpecificationDefinition(
        "example.renderer",
        "Renderer example",
        1,
        SpecificationFsSchemaResolutionContext().semantic_resolution_digest,
        (SpecificationInvariantDefinition("safe", "Preserve unrelated work."),),
        (
            SpecificationPhaseDefinition(
                "first", "First", 0, gate, description="Deliver a bounded increment."
            ),
        ),
        "Prepare exact draft bytes without publishing them.",
    )
    return SpecificationDraftRequest(meaning, "declared-author", "declared-intent")


def test_exact_original_rendered_bytes_and_deterministic_order(request_value):
    expected = tuple(sorted(draft.render_draft(request_value).items()))
    actual = facade.render_specification_draft(request_value)
    assert type(actual) is tuple and actual == expected
    assert len(actual) == 6
    assert facade.render_specification_draft(request_value) == actual
    assert tuple(p for p, _ in actual) == tuple(sorted(p for p, _ in actual))
    assert all(type(member) is tuple and type(member[1]) is bytes for member in actual)
    assert all(body.endswith(b"\n") and b"\r" not in body for _, body in actual)


def test_calls_original_renderer_once_and_detaches_its_mapping(
    request_value, monkeypatch
):
    bodies = draft.render_draft(request_value)
    calls = []

    def original(request):
        assert request is request_value
        calls.append(request)
        return bodies

    monkeypatch.setattr(draft, "render_draft", original)
    actual = facade.render_specification_draft(request_value)
    assert calls == [request_value]
    bodies.clear()
    assert len(actual) == 6
    with pytest.raises(TypeError):
        actual[0] = ("changed", b"changed")


def test_no_filesystem_or_compatibility_publication_entrance(
    request_value, monkeypatch
):
    def forbidden(*args, **kwargs):
        raise AssertionError("pure renderer performed IO or publication")

    before = set(os.listdir("/proc/self/fd"))
    for name in ("stage_files", "rename_no_replace", "cleanup_stage"):
        monkeypatch.setattr(draft, name, forbidden)
    for name in ("open", "mkdir", "write", "rename", "unlink", "rmdir", "chmod"):
        monkeypatch.setattr(draft.os, name, forbidden)
    assert len(facade.render_specification_draft(request_value)) == 6
    assert set(os.listdir("/proc/self/fd")) == before


@pytest.mark.parametrize("value", [None, object(), {}, [], "request"])
def test_wrong_request_type_is_typed_no_effect(value):
    with pytest.raises(SpecificationOperationError) as caught:
        facade.render_specification_draft(value)
    assert caught.value.code == "invalid_draft_request"
    assert caught.value.effect == "none" and caught.value.evidence is None


def test_incomplete_exact_request_is_typed_no_effect():
    value = object.__new__(SpecificationDraftRequest)
    with pytest.raises(SpecificationOperationError) as caught:
        facade.render_specification_draft(value)
    assert caught.value.code == "invalid_draft_request"
    assert caught.value.effect == "none"


@pytest.mark.parametrize(
    ("field", "value"),
    [("definition", None), ("author_ref", None), ("authoring_intent_ref", [])],
)
def test_malformed_nested_request_is_typed_no_effect(request_value, field, value):
    object.__setattr__(request_value, field, value)
    with pytest.raises(SpecificationOperationError) as caught:
        facade.render_specification_draft(request_value)
    assert caught.value.effect == "none" and caught.value.evidence is None


def test_subclass_request_cannot_run_foreign_validator():
    class Foreign(SpecificationDraftRequest):
        def __post_init__(self):
            raise AssertionError("foreign validator executed")

    value = object.__new__(Foreign)
    with pytest.raises(SpecificationOperationError, match="invalid_draft_request"):
        facade.render_specification_draft(value)


def test_original_size_refusal_is_preserved(request_value, monkeypatch):
    monkeypatch.setattr(draft, "MAX_TOTAL_BYTES", 0)
    with pytest.raises(SpecificationOperationError) as caught:
        facade.render_specification_draft(request_value)
    assert caught.value.code == "draft_size_exceeded"
    assert caught.value.effect == "none"


def test_facade_exports_no_compatibility_physical_helpers():
    assert "render_specification_draft" in facade.__all__
    for name in ("render_draft", "stage_files", "rename_no_replace", "cleanup_stage"):
        assert name not in facade.__all__ and not hasattr(facade, name)


def test_successor_keeps_all_dependency_edges_unchanged():
    metadata = tomllib.loads(
        Path(__file__).parents[1].joinpath("pyproject.toml").read_text()
    )
    assert metadata["project"]["version"] == "0.3.1"
    assert metadata["project"]["dependencies"] == [
        "aware-specification-sdk>=0.2.0,<0.3.0",
        "aware-specification-fs-adapter",
    ]
    assert metadata["project"]["optional-dependencies"] == {
        "protocol": ["aware-protocol-fs-adapter>=0.3.0,<0.6.0"],
        "governed": [
            "aware-protocol-fs-adapter[draft]>=0.5.0,<0.6.0",
            "aware-issue-sdk>=0.8.0,<0.9.0",
            "aware-issue-fs-adapter>=0.7.0,<0.8.0",
            "aware-file-system>=0.2.0,<0.3.0",
        ],
    }


def test_fresh_facade_import_requires_no_writer_or_service_suppliers():
    roots = [
        str(ROOT / p)
        for p in (
            "workspaces/aware_kernel/modules/specification/libs/runtime/python",
            "workspaces/aware_kernel/modules/specification/libs/fs_source_contract/python",
            "workspaces/aware_kernel/modules/specification/libs/fs_adapter/python",
            "workspaces/aware_kernel/modules/specification/sdks/specification/python/public",
            "workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter",
        )
    ]
    script = """
import importlib.abc, json, sys
sys.path[:0] = json.loads(sys.argv[1])
blocked = {'aware_issue_sdk', 'aware_issue_fs_adapter', 'aware_file_system',
           'aware_protocol_fs_adapter', 'aware_specification',
           'aware_workflow_ontology_dto', 'aware_issue_service_api',
           'aware_issue_service_dto'}
class Reject(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in blocked:
            raise ImportError('unexpected_supplier:' + fullname)
sys.meta_path.insert(0, Reject())
from aware_specification_fs_sdk_adapter import render_specification_draft
assert callable(render_specification_draft)
assert blocked.isdisjoint(sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script, json.dumps(roots)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
