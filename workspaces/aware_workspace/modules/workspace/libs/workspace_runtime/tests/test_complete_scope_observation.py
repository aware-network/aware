"""Complete source enumeration proofs; not policy participant classification."""

import copy
import os
from pathlib import Path

import pytest
import aware_workspace_runtime.complete_scope_observation as scope_module
from aware_workspace_runtime import (
    SourceObservationUnavailable,
    WorkspaceCompleteScopeObservationRuntime,
    WorkspaceCompleteScopeSnapshot,
)
from test_observed_semantic_issuers import setup


def owner(observation, membership):
    return WorkspaceCompleteScopeObservationRuntime(
        observation_runtime=observation,
        membership_runtime=membership,
    )


def capture(runtime, retained):
    return runtime.capture_complete_scope(
        observation=retained,
        workspace_manifest_path="aware.workspace.toml",
    )


async def test_complete_scope_includes_every_package_and_retained_body(
    tmp_path, monkeypatch
):
    async with setup(tmp_path) as (root, _, observation, membership, retained, _, _):
        runtime = owner(observation, membership)
        try:
            snapshot = capture(runtime, retained)
            original_read = Path.read_bytes

            def forbid_checkout(path):
                if path.is_relative_to(root):
                    raise AssertionError("checkout read outside original observer")
                return original_read(path)

            monkeypatch.setattr(Path, "read_bytes", forbid_checkout)
            runtime.validate_complete_scope(snapshot)  # before policy producer
            source = runtime.read_complete_scope(snapshot)
            runtime.validate_complete_scope(snapshot)  # after policy producer
            assert [m.module_id for m in source.modules] == ["main"]
            assert [p.membership.package_id for p in source.packages] == [
                "demo",
                "provider",
                "target",
            ]
            coordinates = {b.relative_path: b for b in source.observation.bodies}
            for package in source.packages:
                assert (
                    package.manifest_coordinate
                    == coordinates[package.manifest_coordinate.relative_path]
                )
                assert (
                    len(package.manifest_body) == package.manifest_coordinate.size_bytes
                )
            assert len(source.modules[0].meaning.package_declarations) == 3
            # Mutating detached inspection cannot filter the original nominal scope.
            object.__setattr__(source, "packages", ())
            assert len(runtime.read_complete_scope(snapshot).packages) == 3
        finally:
            runtime.close()


async def test_capture_complete_scope_batches_membership_admission(
    tmp_path, monkeypatch
):
    async with setup(tmp_path) as (
        _,
        _,
        observation,
        membership,
        retained,
        _,
        _,
    ):
        runtime = owner(observation, membership)
        try:
            calls = []
            original = membership.admit_many

            def admit_many(**kwargs):
                calls.append(kwargs["selections"])
                return original(**kwargs)

            monkeypatch.setattr(membership, "admit_many", admit_many)
            snapshot = capture(runtime, retained)
            assert len(calls) == 1
            assert len(calls[0]) == 3
            runtime.release(snapshot)
        finally:
            runtime.close()


async def test_scope_read_reuses_identical_module_meaning_only_within_read(
    tmp_path, monkeypatch
):
    async with setup(tmp_path) as (
        root,
        _,
        observation,
        membership,
        retained,
        _,
        _,
    ):
        workspace = root / "aware.workspace.toml"
        workspace.write_text(
            workspace.read_text()
            + '\n[[workspace.modules]]\nid="copy"\npath="copy"\n'
        )
        copy_root = root / "copy"
        (copy_root / "provider").mkdir(parents=True)
        (copy_root / "target").mkdir()
        (copy_root / "package").mkdir()
        (copy_root / "aware.module.toml").write_bytes(
            (root / "aware.module.toml").read_bytes()
        )
        (copy_root / "provider/pyproject.toml").write_bytes(b"copy provider")
        (copy_root / "target/aware.example.toml").write_bytes(b"copy target")
        (copy_root / "package/aware.example.toml").write_bytes(b"copy demo")
        retained = observation.observe(root_relative_path=".")
        runtime = owner(observation, membership)
        try:
            calls = []
            original = scope_module.parse_module_manifest

            def parse(body):
                calls.append(body)
                return original(body)

            monkeypatch.setattr(scope_module, "parse_module_manifest", parse)
            snapshot = capture(runtime, retained)
            assert len(calls) == 1
            calls.clear()
            source = runtime.read_complete_scope(snapshot)
            assert [module.module_id for module in source.modules] == [
                "copy",
                "main",
            ]
            assert len(calls) == 1
            runtime.read_complete_scope(snapshot)
            assert len(calls) == 2
        finally:
            runtime.close()


async def test_scope_membership_validation_reuses_shared_root_currentness(tmp_path):
    async with setup(tmp_path) as (
        _,
        _,
        observation,
        membership,
        retained,
        _,
        _,
    ):
        runtime = owner(observation, membership)
        try:
            snapshot = capture(runtime, retained)
            observed = observation._evidence(retained)
            before = observation._store.snapshot().metrics.body_read_count
            runtime.validate_complete_scope(snapshot)
            after = observation._store.snapshot().metrics.body_read_count
            assert after - before == 2 * len(observed.bodies)
        finally:
            runtime.close()


async def test_scope_read_reuses_shared_body_refs_only_within_operation(tmp_path):
    async with setup(tmp_path) as (
        _,
        _,
        observation,
        membership,
        retained,
        _,
        _,
    ):
        runtime = owner(observation, membership)
        try:
            snapshot = capture(runtime, retained)
            observed = observation._evidence(retained)
            unique_refs = len({body.body_ref for body in observed.bodies})
            assert unique_refs < len(observed.bodies)
            before = observation._store.snapshot().metrics.body_read_count
            runtime.read_complete_scope(snapshot)
            first_after = observation._store.snapshot().metrics.body_read_count
            # The operation keeps its required two-sided root rereads in both
            # validators. Only the retained-body batch read reuses shared refs.
            expected_reads = 4 * len(observed.bodies) + unique_refs
            assert first_after - before == expected_reads
            runtime.read_complete_scope(snapshot)
            second_after = observation._store.snapshot().metrics.body_read_count
            assert second_after - first_after == expected_reads
        finally:
            runtime.close()


@pytest.mark.parametrize("version", [1, 2])
async def test_scope_includes_other_modules_and_requires_v2(tmp_path, version):
    async with setup(tmp_path) as (root, _, observation, membership, _, _, _):
        workspace = root / "aware.workspace.toml"
        workspace.write_text(
            workspace.read_text()
            + '\n[[workspace.modules]]\nid="empty"\npath="empty"\n'
        )
        (root / "empty").mkdir()
        (root / "empty/aware.module.toml").write_text(
            f'aware={version}\n[[packages]]\nid="extra"\nkind="code"\n'
            'manifest="package/pyproject.toml"\n'
        )
        (root / "empty/package").mkdir()
        (root / "empty/package/pyproject.toml").write_bytes(b"opaque extra package")
        retained = observation.observe(root_relative_path=".")
        runtime = owner(observation, membership)
        try:
            if version == 1:
                with pytest.raises(SourceObservationUnavailable, match="requires_v2"):
                    capture(runtime, retained)
            else:
                source = runtime.read_complete_scope(capture(runtime, retained))
                assert [m.module_id for m in source.modules] == ["empty", "main"]
                assert len(source.packages) == 4
        finally:
            runtime.close()


@pytest.mark.parametrize(
    "change",
    [
        "workspace",
        "module",
        "package",
        "addition",
        "eviction",
        "restart",
        "fork",
        "membership_closed",
        "scope_released",
        "runtime_closed",
    ],
)
async def test_scope_invalidates_before_after_producer(tmp_path, change, monkeypatch):
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
        snapshot = capture(runtime, retained)
        runtime.validate_complete_scope(snapshot)
        if change in ("workspace", "module", "package"):
            path = {
                "workspace": "aware.workspace.toml",
                "module": "aware.module.toml",
                "package": "provider/pyproject.toml",
            }[change]
            (root / path).write_bytes(b"changed")
        elif change == "addition":
            (root / "new_source").write_bytes(b"added")
        elif change == "eviction":
            for path in (tmp_path / "state").rglob("*"):
                if path.is_file():
                    path.unlink()
        elif change == "restart":
            await session.stop()
            await session.start(background=False)
        elif change == "fork":
            monkeypatch.setattr(os, "getpid", lambda: -1)
        elif change == "membership_closed":
            membership.close()
        elif change == "scope_released":
            runtime.release(snapshot)
        else:
            runtime.close()
        try:
            with pytest.raises(SourceObservationUnavailable):
                runtime.validate_complete_scope(snapshot)
            with pytest.raises(SourceObservationUnavailable):
                runtime.read_complete_scope(snapshot)
        finally:
            runtime.close()


async def test_scope_revalidates_after_batched_read(tmp_path, monkeypatch):
    async with setup(tmp_path) as (
        root,
        _,
        observation,
        membership,
        retained,
        _,
        _,
    ):
        runtime = owner(observation, membership)
        snapshot = capture(runtime, retained)
        original_batch = runtime._read_retained_body_set

        def read_batch(observed):
            result = original_batch(observed)
            (root / "provider/pyproject.toml").write_bytes(
                b"changed during complete-scope read"
            )
            return result

        monkeypatch.setattr(runtime, "_read_retained_body_set", read_batch)
        try:
            with pytest.raises(SourceObservationUnavailable):
                runtime.read_complete_scope(snapshot)
        finally:
            runtime.close()


async def test_scope_nominality_and_exact_selection(tmp_path):
    async with setup(tmp_path) as (_, _, observation, membership, retained, _, _):
        runtime, other = owner(observation, membership), owner(observation, membership)
        try:
            snapshot = capture(runtime, retained)
            with pytest.raises(TypeError):
                copy.copy(snapshot)
            for validator, handle in [
                (other, snapshot),
                (runtime, object.__new__(WorkspaceCompleteScopeSnapshot)),
            ]:
                with pytest.raises(SourceObservationUnavailable):
                    validator.validate_complete_scope(handle)
            with pytest.raises(SourceObservationUnavailable):
                runtime.capture_complete_scope(
                    observation=retained,
                    workspace_manifest_path="foreign/aware.workspace.toml",
                )
            with pytest.raises(TypeError):
                runtime.capture_complete_scope(
                    observation=retained,
                    workspace_manifest_path="aware.workspace.toml",
                    packages=["demo"],
                )
        finally:
            runtime.close()
            other.close()


async def test_inaccessible_required_package_is_not_silently_omitted(tmp_path):
    async with setup(tmp_path) as (root, _, observation, membership, _, _, _):
        (root / "provider/pyproject.toml").unlink()
        retained = observation.observe(root_relative_path=".")
        runtime = owner(observation, membership)
        from aware_workspace_runtime.composition import WorkspaceCompositionFailure

        try:
            with pytest.raises(WorkspaceCompositionFailure):
                capture(runtime, retained)
        finally:
            runtime.close()


async def test_omitted_occurrence_stays_in_complete_scope(tmp_path):
    async with setup(tmp_path) as (_, _, observation, membership, retained, _, _):
        runtime = owner(observation, membership)
        try:
            source = runtime.read_complete_scope(capture(runtime, retained))
            declarations = {
                d.package_id: d for d in source.modules[0].meaning.package_declarations
            }
            assert declarations["provider"].occurrence_declared is False
            assert declarations["demo"].occurrence_declared is True
            assert declarations["target"].occurrence_declared is True
            assert any(p.membership.package_id == "provider" for p in source.packages)
        finally:
            runtime.close()


@pytest.mark.parametrize(
    "field",
    [
        "registration",
        "semantic_package_name",
        "semantic_version",
        "code_package_name",
        "source_code_package_id",
        "configuration",
        "namespace",
        "owned_roots",
        "dependency_targets",
    ],
)
async def test_incomplete_authored_participant_refuses_entire_scope(tmp_path, field):
    import re

    async with setup(
        tmp_path,
        lambda b: re.sub(
            "^" + field + "=.*$",
            field + '={state="unavailable"}',
            b,
            count=1,
            flags=re.MULTILINE,
        ),
    ) as (_, _, observation, membership, retained, _, _):
        runtime = owner(observation, membership)
        try:
            with pytest.raises(
                SourceObservationUnavailable, match="incomplete_authored"
            ):
                capture(runtime, retained)
        finally:
            runtime.close()


async def test_explicit_all_unavailable_cannot_disappear_as_nonparticipant(tmp_path):
    fields = (
        "registration",
        "semantic_version",
        "semantic_package_name",
        "code_package_name",
        "source_code_package_id",
        "configuration",
        "namespace",
        "owned_roots",
        "dependency_targets",
    )
    incomplete = "\n[packages.semantic_admission]\n" + "".join(
        f'{field}={{state="unavailable"}}\n' for field in fields
    )

    def authored_provider(body):
        return body.replace(
            '\n[[packages]]\nid="target"', incomplete + '\n[[packages]]\nid="target"'
        )

    async with setup(tmp_path, authored_provider) as (
        _,
        _,
        observation,
        membership,
        retained,
        _,
        _,
    ):
        runtime = owner(observation, membership)
        try:
            with pytest.raises(
                SourceObservationUnavailable, match="incomplete_authored"
            ):
                capture(runtime, retained)
        finally:
            runtime.close()
