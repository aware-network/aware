"""Closed source metadata codecs; native body and holder values stay native."""

from __future__ import annotations

import copy
from dataclasses import replace

import pytest
from aware_workspace_sdk.repository_workflow import WorkspaceRepositoryWorkflowSource
from aware_workspace_sdk.repository_workflow_source_codec import (
    WorkspaceWorkflowSourceValueError,
    repository_workflow_source_value_from_json,
    repository_workflow_source_value_from_payload,
    repository_workflow_source_value_to_json,
    repository_workflow_source_value_to_payload,
)
from aware_workspace_sdk.repository_workflow_source_values import (
    MAX_WORKFLOW_SOURCE_BYTES,
    MAX_WORKFLOW_SOURCE_FILES,
    WorkspaceWorkflowSourceBinding,
    WorkspaceWorkflowSourceBody,
    WorkspaceWorkflowSourceFile,
    WorkspaceWorkflowSourceObservation,
    WorkspaceWorkflowSourceRead,
)
from aware_workspace_sdk.repository_workflow_values import WorkspaceWorkflowMarker


@pytest.fixture
def observation():
    digest = "sha256:" + "0" * 64
    binding = WorkspaceWorkflowSourceBinding(
        digest,
        "workflow:1",
        "attempt:1",
        digest,
        "generation:1",
        "codex-fixture",
        1,
        2,
        digest,
        digest,
        "/source",
        "/target",
        (1, 2),
        (3, 4),
        "a" * 40,
        "portable",
        digest,
        (WorkspaceWorkflowMarker("python_version", "3.12"),),
        digest,
        "aware.workspace.package-source-checkout.v2",
        digest,
        1,
        1,
        4,
        MAX_WORKFLOW_SOURCE_FILES,
        MAX_WORKFLOW_SOURCE_BYTES,
        "refs/heads/main",
        None,
    )
    return WorkspaceWorkflowSourceObservation(
        binding,
        (
            WorkspaceWorkflowSourceFile(
                "package/source.py", "public/source.py", digest, 4, "100644", 0o644
            ),
        ),
        "retained",
        "not_attempted",
    )


def test_source_codec_round_trip_and_native_values_excluded(observation):
    text = repository_workflow_source_value_to_json(observation)
    assert (
        repository_workflow_source_value_from_json(type(observation), text)
        == observation
    )
    for value in (
        WorkspaceWorkflowSourceRead(observation.binding, ()),
        WorkspaceWorkflowSourceBody(observation.files[0], b"data"),
        object.__new__(WorkspaceRepositoryWorkflowSource),
        b"raw",
    ):
        with pytest.raises(WorkspaceWorkflowSourceValueError):
            repository_workflow_source_value_to_payload(value)
    with pytest.raises(TypeError):
        WorkspaceRepositoryWorkflowSource()
    with pytest.raises(TypeError):
        copy.copy(object.__new__(WorkspaceRepositoryWorkflowSource))


@pytest.mark.parametrize(
    "poison",
    (
        "unknown",
        "missing",
        "null",
        "bool",
        "float",
        "parent",
        "mode",
        "digest",
        "root_identity",
        "duplicate_path",
        "ordering",
    ),
)
def test_source_metadata_rejections(observation, poison):
    payload = repository_workflow_source_value_to_payload(observation)
    if poison == "unknown":
        payload["foreign"] = None
    elif poison == "missing":
        del payload["binding"]["expected_target_head"]
    elif poison == "null":
        payload["files"] = None
    elif poison == "bool":
        payload["binding"]["process_id"] = True
    elif poison == "float":
        payload["binding"]["captured_bytes"] = 1.0
    elif poison == "parent":
        payload["files"][0]["source_path"] = "../source.py"
    elif poison == "mode":
        payload["files"][0]["projected_mode"] = 0o755
    elif poison == "digest":
        payload["files"][0]["content_digest"] = "same-bytes"
    elif poison == "root_identity":
        payload["binding"]["source_root_identity"] = [1]
    elif poison == "duplicate_path":
        payload["files"].append(dict(payload["files"][0]))
        payload["binding"]["projected_count"] = 2
    else:
        payload["files"].append({**payload["files"][0], "output_path": "a.py"})
        payload["binding"]["projected_count"] = 2
    with pytest.raises(WorkspaceWorkflowSourceValueError):
        repository_workflow_source_value_from_payload(type(observation), payload)


@pytest.mark.parametrize(
    "text", ('{"phase":1,"phase":2}', "{malformed", "[" * 1000, '{"number":NaN}')
)
def test_source_json_refusal(observation, text):
    with pytest.raises(WorkspaceWorkflowSourceValueError):
        repository_workflow_source_value_from_json(type(observation), text)


def test_source_file_count_bound_is_separate_from_journal(observation):
    from aware_workspace_sdk.repository_workflow_codec import (
        WorkspaceWorkflowValueError,
        repository_workflow_value_to_payload,
    )

    files = tuple(
        replace(observation.files[0], output_path=f"files/{i:05}.py")
        for i in range(MAX_WORKFLOW_SOURCE_FILES)
    )
    value = replace(
        observation,
        binding=replace(observation.binding, projected_count=len(files)),
        files=files,
    )
    assert (
        len(repository_workflow_source_value_to_payload(value)["files"])
        == MAX_WORKFLOW_SOURCE_FILES
    )
    with pytest.raises(WorkspaceWorkflowSourceValueError):
        repository_workflow_source_value_to_payload(
            replace(value, files=(*files, files[0]))
        )
    with pytest.raises(WorkspaceWorkflowValueError):
        repository_workflow_value_to_payload(value)


def test_source_hostile_fields_and_descriptors_are_behavior_free(
    observation, monkeypatch
):
    calls = []

    class Hostile:
        def __str__(self):
            calls.append("str")
            return "foreign"

        def __eq__(self, other):
            calls.append("eq")
            return True

        def __get__(self, instance, owner):
            calls.append("descriptor")
            return 1

    poison = Hostile()
    with pytest.raises(WorkspaceWorkflowSourceValueError):
        repository_workflow_source_value_to_payload(
            replace(observation.binding, process_id=poison)
        )
    monkeypatch.setattr(WorkspaceWorkflowSourceBinding, "process_id", poison)
    with pytest.raises(WorkspaceWorkflowSourceValueError):
        repository_workflow_source_value_to_payload(observation)
    assert calls == []


def test_original_source_paths_export_keeps_typed_contract_and_no_new_handle():
    import inspect
    from typing import get_type_hints

    from aware_workspace_sdk import repository_workflow as sdk

    method = sdk.verify_original_repository_workflow_source_paths
    assert "verify_original_repository_workflow_source_paths" in sdk.__all__
    assert list(inspect.signature(method).parameters) == [
        "source",
        "expected_binding",
        "output_paths",
    ]
    assert get_type_hints(method) == {
        "source": WorkspaceRepositoryWorkflowSource,
        "expected_binding": WorkspaceWorkflowSourceBinding,
        "output_paths": tuple[str, ...],
        "return": type(None),
    }
