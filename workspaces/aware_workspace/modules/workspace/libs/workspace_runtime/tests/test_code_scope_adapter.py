"""Real retained Workspace scope projected through Code's neutral boundary."""

from dataclasses import replace

import pytest
import aware_workspace_runtime.code_scope_adapter as scope_adapter_module
from aware_workspace_runtime import (
    SourceObservationUnavailable,
    WorkspaceCodeScopeAdapter,
    WorkspaceCompleteScopeSnapshot,
)
from test_complete_scope_observation import capture, owner
from test_observed_semantic_issuers import setup


async def test_exact_complete_projection_and_shared_refs(tmp_path):
    async with setup(tmp_path) as (_, _, observation, membership, retained, _, _):
        runtime = owner(observation, membership)
        try:
            snapshot = capture(runtime, retained)
            adapter = WorkspaceCodeScopeAdapter(scope_runtime=runtime)
            adapter.validate_complete_scope_projection(snapshot)
            source = runtime.read_complete_scope(snapshot)
            result = adapter.read_complete_scope_projection(snapshot)
            assert [p.package_id for p in result.packages] == [
                "demo",
                "provider",
                "target",
            ]
            assert result.workspace_manifest.body == source.workspace_body
            assert (
                result.workspace_manifest.body_ref
                == source.workspace_coordinate.body_ref
            )
            for actual, original in zip(result.modules, source.modules, strict=True):
                assert actual.module_id == original.module_id
                assert actual.manifest.body == original.body
                assert (
                    actual.manifest.relative_path == original.coordinate.relative_path
                )
            for actual, original in zip(result.packages, source.packages, strict=True):
                assert actual.manifest.body == original.manifest_body
                assert actual.manifest.body_ref == original.manifest_coordinate.body_ref
                assert (
                    actual.manifest.relative_path
                    == original.manifest_coordinate.relative_path
                )
                assert (
                    actual.source_identity_digest
                    == original.membership.source_identity_digest
                )
            provider, target = result.packages[1:]
            assert provider.manifest.body_ref == target.manifest.body_ref
            assert provider.manifest.relative_path != target.manifest.relative_path
            adapter.validate_complete_scope_projection(
                snapshot, projection_digest=result.projection_digest
            )
            filtered = replace(
                result, packages=(result.packages[0], result.packages[2])
            )
            with pytest.raises(SourceObservationUnavailable, match="digest_mismatch"):
                adapter.validate_complete_scope_projection(
                    snapshot, projection_digest=filtered.projection_digest
                )
            object.__setattr__(result, "packages", ())
            assert len(adapter.read_complete_scope_projection(snapshot).packages) == 3
        finally:
            runtime.close()


@pytest.mark.parametrize(
    "change",
    ["content", "addition", "eviction", "restart", "release", "close", "foreign"],
)
async def test_original_lifetime_and_observation_required(tmp_path, change):
    async with setup(tmp_path) as (
        root,
        session,
        observation,
        membership,
        retained,
        _,
        _,
    ):
        runtime = owner(observation, membership)
        try:
            snapshot = capture(runtime, retained)
            adapter = WorkspaceCodeScopeAdapter(scope_runtime=runtime)
            digest = adapter.read_complete_scope_projection(snapshot).projection_digest
            if change == "content":
                (root / "provider/pyproject.toml").write_bytes(b"changed")
            elif change == "addition":
                (root / "new").write_bytes(b"new")
            elif change == "eviction":
                for path in (tmp_path / "state").rglob("*"):
                    if path.is_file():
                        path.unlink()
            elif change == "restart":
                await session.stop()
                await session.start(background=False)
            elif change == "release":
                runtime.release(snapshot)
            elif change == "close":
                runtime.close()
            else:
                snapshot = object.__new__(WorkspaceCompleteScopeSnapshot)
            with pytest.raises(SourceObservationUnavailable):
                adapter.validate_complete_scope_projection(
                    snapshot, projection_digest=digest
                )
            with pytest.raises(SourceObservationUnavailable):
                adapter.read_complete_scope_projection(snapshot)
        finally:
            runtime.close()


async def test_projection_final_validation_catches_projection_time_mutation(
    tmp_path, monkeypatch
):
    async with setup(tmp_path) as (root, _, observation, membership, retained, _, _):
        runtime = owner(observation, membership)
        try:
            snapshot = capture(runtime, retained)
            adapter = WorkspaceCodeScopeAdapter(scope_runtime=runtime)
            original_body = scope_adapter_module._body
            mutated = False

            def mutate_during_projection(coordinate, body):
                nonlocal mutated
                result = original_body(coordinate, body)
                if not mutated:
                    mutated = True
                    (root / "provider/pyproject.toml").write_bytes(
                        b"changed during projection"
                    )
                return result

            monkeypatch.setattr(scope_adapter_module, "_body", mutate_during_projection)
            with pytest.raises(SourceObservationUnavailable):
                adapter.read_complete_scope_projection(snapshot)
        finally:
            runtime.close()


@pytest.mark.parametrize(
    "entrance",
    [
        "_begin_projection_read",
        "_begin_projection_batch_read",
        "validate_complete_scope",
        "validate_complete_scope_batch",
    ],
)
async def test_original_callable_cannot_be_replaced(tmp_path, monkeypatch, entrance):
    async with setup(tmp_path) as (_, _, observation, membership, retained, _, _):
        runtime = owner(observation, membership)
        try:
            snapshot = capture(runtime, retained)
            adapter = WorkspaceCodeScopeAdapter(scope_runtime=runtime)
            monkeypatch.setattr(runtime, entrance, lambda *a, **k: None)
            if entrance in ("_begin_projection_batch_read", "validate_complete_scope_batch"):
                with pytest.raises(SourceObservationUnavailable, match="origin_changed"):
                    adapter.read_complete_scope_projections((snapshot,))
            else:
                with pytest.raises(SourceObservationUnavailable, match="origin_changed"):
                    adapter.read_complete_scope_projection(snapshot)
                with pytest.raises(SourceObservationUnavailable, match="origin_changed"):
                    adapter.validate_complete_scope_projection(snapshot)
        finally:
            runtime.close()


def test_structural_runtime_is_not_an_owner():
    with pytest.raises(TypeError):
        WorkspaceCodeScopeAdapter(scope_runtime=object())
