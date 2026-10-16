"""Genuine setup derivation custody; no fake Issue or FileSystem execution port."""

import ast
import copy
import gc
import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path
from threading import Thread

import pytest
from aware_workspace_runtime import architecture_setup as runtime
from aware_workspace_sdk.architecture_setup import (
    ArchitectureSetupError,
    ArchitectureSetupRequest,
    WorkspaceSetupClient,
)


def capture(client, request):
    preview = client.preview(request)
    return runtime._capture_setup_derivation(
        client._runtime, request, expected_plan_sha256=preview.plan_sha256
    )


def files(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_original_plan_derived_once_then_verified_without_reconstruction(tmp_path):
    with WorkspaceSetupClient.filesystem(repository_root=tmp_path) as client:
        request = ArchitectureSetupRequest(
            "repository", name="example", license_expression="MIT"
        )
        preview = client.preview(request)
        before = files(tmp_path)
        calls = []
        original_code = runtime.ArchitectureSetupRuntime._plan.__code__

        def observe(frame, event, _):
            if event == "call" and frame.f_code is original_code:
                calls.append("derive")

        prior = sys.getprofile()
        try:
            sys.setprofile(observe)
            handle = runtime._capture_setup_derivation(
                client._runtime, request, expected_plan_sha256=preview.plan_sha256
            )
            state = runtime._verify_setup_derivation(client._runtime, handle)
            runtime._verify_setup_derivation(client._runtime, handle)

        finally:
            sys.setprofile(prior)
        assert calls == ["derive"]
        assert state.request is not request
        assert state.plan_sha256 == preview.plan_sha256
        assert state.inputs == (("aware.repo.toml", None),)
        assert dict(state.outputs)["aware.repo.toml"].startswith(b"aware_repo = 1")
        assert files(tmp_path) == before == {}
        runtime._release_setup_derivation(client._runtime, handle)
        assert state.request is None and state.inputs == state.outputs == ()
        with pytest.raises(ArchitectureSetupError, match="retired"):
            runtime._verify_setup_derivation(client._runtime, handle)


def test_original_deriver_matches_frozen_source_and_preview_algorithm():
    root = next(
        p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
    )
    freeze = json.loads(
        (
            root / "docs/reports/workspace-setup-a1-supplier-inputs-20261012.json"
        ).read_text()
    )["joined_freeze"]
    path = Path(runtime.__file__).relative_to(root).as_posix()
    pin = next(row for row in freeze["candidate_path_preimages"] if row["path"] == path)
    before = subprocess.check_output(
        ["git", "show", freeze["captured_revision"] + ":" + path], cwd=root
    )
    assert hashlib.sha256(before).hexdigest() == pin["sha256"]

    def derivation(body):
        cls = next(
            node
            for node in ast.parse(body).body
            if isinstance(node, ast.ClassDef)
            and node.name == "ArchitectureSetupRuntime"
        )
        return {
            node.name: ast.dump(node, include_attributes=False)
            for node in cls.body
            if isinstance(node, ast.FunctionDef)
            and node.name in ("_plan", "preview", "apply")
        }

    assert derivation(before) == derivation(Path(runtime.__file__).read_bytes())


def test_retained_inputs_terminally_reject_drift_and_restoration(tmp_path):
    with WorkspaceSetupClient.filesystem(repository_root=tmp_path) as client:
        client.create_repository("example", license_expression="MIT")
        request = ArchitectureSetupRequest(
            "workspace", name="application", path="application"
        )
        handle = capture(client, request)
        state = runtime._verify_setup_derivation(client._runtime, handle)
        manifest = tmp_path / "aware.repo.toml"
        before = manifest.read_bytes()
        manifest.write_bytes(before + b"\n# changed\n")
        with pytest.raises(ArchitectureSetupError, match="input_drift"):
            runtime._verify_setup_derivation(client._runtime, handle)
        manifest.write_bytes(before)
        with pytest.raises(ArchitectureSetupError, match="retired"):
            runtime._verify_setup_derivation(client._runtime, handle)
        assert state.inputs == state.outputs == ()


def test_foreign_owner_thread_and_forged_handle_do_not_consume_original_custody(
    tmp_path,
):
    with (
        WorkspaceSetupClient.filesystem(repository_root=tmp_path) as first,
        WorkspaceSetupClient.filesystem(repository_root=tmp_path) as second,
    ):
        request = ArchitectureSetupRequest(
            "repository", name="example", license_expression="MIT"
        )
        handle = capture(first, request)
        with pytest.raises(ArchitectureSetupError, match="owner_mismatch"):
            runtime._verify_setup_derivation(second._runtime, handle)
        with pytest.raises(ArchitectureSetupError, match="original_setup_derivation"):
            runtime._verify_setup_derivation(
                first._runtime, object.__new__(runtime._RetainedSetupDerivation)
            )
        errors = []

        def foreign_thread():
            try:
                runtime._release_setup_derivation(first._runtime, handle)
            except ArchitectureSetupError as error:
                errors.append(str(error))

        thread = Thread(target=foreign_thread)
        thread.start()
        thread.join()
        assert errors == ["setup_derivation_execution_mismatch"]
        assert (
            runtime._verify_setup_derivation(first._runtime, handle).phase == "retained"
        )
        runtime._release_setup_derivation(first._runtime, handle)


@pytest.mark.parametrize("operation", (copy.copy, copy.deepcopy, pickle.dumps))
def test_retained_derivation_is_not_copyable_or_serializable(tmp_path, operation):
    with WorkspaceSetupClient.filesystem(repository_root=tmp_path) as client:
        request = ArchitectureSetupRequest(
            "repository", name="example", license_expression="MIT"
        )
        handle = capture(client, request)
        with pytest.raises(TypeError):
            operation(handle)
        assert (
            runtime._verify_setup_derivation(client._runtime, handle).phase
            == "retained"
        )
        runtime._release_setup_derivation(client._runtime, handle)


def test_request_mutation_does_not_change_original_retained_request(tmp_path):
    with WorkspaceSetupClient.filesystem(repository_root=tmp_path) as client:
        request = ArchitectureSetupRequest(
            "repository", name="example", license_expression="MIT"
        )
        handle = capture(client, request)
        object.__setattr__(request, "name", "replacement")
        state = runtime._verify_setup_derivation(client._runtime, handle)
        assert state.request.name == "example"
        assert b'"example"' in dict(state.outputs)["aware.repo.toml"]
        runtime._release_setup_derivation(client._runtime, handle)


@pytest.mark.parametrize("bad", (None, True, "", "sha256:" + "0" * 64))
def test_unreviewed_or_changed_digest_refuses_without_writes(tmp_path, bad):
    with WorkspaceSetupClient.filesystem(repository_root=tmp_path) as client:
        request = ArchitectureSetupRequest(
            "repository", name="example", license_expression="MIT"
        )
        with pytest.raises(ArchitectureSetupError):
            runtime._capture_setup_derivation(
                client._runtime, request, expected_plan_sha256=bad
            )
        assert files(tmp_path) == {}


def test_changed_deriver_refuses_before_foreign_call(tmp_path, monkeypatch):
    with WorkspaceSetupClient.filesystem(repository_root=tmp_path) as client:
        request = ArchitectureSetupRequest(
            "repository", name="example", license_expression="MIT"
        )
        preview = client.preview(request)
        calls = []
        monkeypatch.setattr(
            runtime.ArchitectureSetupRuntime,
            "_plan",
            lambda *_: calls.append("foreign"),
        )
        with pytest.raises(
            ArchitectureSetupError, match="original_setup_deriver_changed"
        ):
            runtime._capture_setup_derivation(
                client._runtime, request, expected_plan_sha256=preview.plan_sha256
            )
        assert calls == [] and files(tmp_path) == {}


def test_client_closure_or_handle_collection_releases_private_bytes_only(tmp_path):
    client = WorkspaceSetupClient.filesystem(repository_root=tmp_path)
    request = ArchitectureSetupRequest(
        "repository", name="example", license_expression="MIT"
    )
    handle = capture(client, request)
    state = runtime._verify_setup_derivation(client._runtime, handle)
    key = id(handle)
    del handle
    gc.collect()
    assert key not in runtime._SETUP_DERIVATIONS
    assert state.phase == "released" and state.retained_bytes == 0
    handle = capture(client, request)
    state = runtime._verify_setup_derivation(client._runtime, handle)
    client.close()
    assert state.phase == "released" and state.retained_bytes == 0
    with pytest.raises(ArchitectureSetupError, match="retired"):
        runtime._verify_setup_derivation(client._runtime, handle)
    assert state.phase == "released" and state.retained_bytes == 0
    assert files(tmp_path) == {}


def test_owner_collection_expires_bytes_without_closing_a_borrowed_physical_owner(
    tmp_path,
):
    client = WorkspaceSetupClient.filesystem(repository_root=tmp_path)
    physical = client._runtime.physical
    request = ArchitectureSetupRequest(
        "repository", name="example", license_expression="MIT"
    )
    handle = capture(client, request)
    state = runtime._verify_setup_derivation(client._runtime, handle)
    try:
        del client
        gc.collect()
        assert state.phase == "released" and state.request is None
        assert state.inputs == state.outputs == ()
        assert physical.fd >= 0
    finally:
        physical.close()


def test_genuine_package_derivation_preserves_original_code_renderer(tmp_path):
    with WorkspaceSetupClient.filesystem(repository_root=tmp_path) as client:
        client.create_repository("example", license_expression="MIT")
        request = ArchitectureSetupRequest(
            "python_package",
            name="consumer",
            owner="repository",
            path="libs/consumer/python",
            distribution="example-consumer",
            import_root="example_consumer",
        )
        before = files(tmp_path)
        handle = capture(client, request)
        state = runtime._verify_setup_derivation(client._runtime, handle)
        outputs = dict(state.outputs)
        assert set(outputs) == {
            "aware.repo.toml",
            "libs/consumer/python/pyproject.toml",
            "libs/consumer/python/src/example_consumer/__init__.py",
        }
        assert files(tmp_path) == before
        assert state.outputs[-1][0] == "aware.repo.toml"
        runtime._release_setup_derivation(client._runtime, handle)
