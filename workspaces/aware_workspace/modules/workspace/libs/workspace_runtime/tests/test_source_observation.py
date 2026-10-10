
import copy
import os
import pickle
from contextlib import asynccontextmanager

import pytest
from aware_workspace_runtime import (
    FileSystemIndexObservationProvider,
    SourceObservationLimits,
    SourceObservationUnavailable,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryObservationSession,
    WorkspaceRetainedRootObservation,
    WorkspaceSourceObservationRuntime,
)
from test_repository_delta_retention_client import retained


@asynccontextmanager
async def runtime(tmp_path, *, capacity=16, limits=SourceObservationLimits()):
    root = tmp_path / "repository"
    root.mkdir()
    package = root / "package"
    package.mkdir()
    (package / "manifest.toml").write_bytes(b"meaning = 1")
    (package / "plain.bin").write_bytes(b"initial")
    binding = WorkspaceRepositoryBinding(root)
    session = WorkspaceRepositoryObservationSession(
        binding=binding, provider=FileSystemIndexObservationProvider(binding=binding)
    )
    await session.start(background=False)
    store = retained(
        repository_binding_ref=binding.binding_key,
        state_root=tmp_path / "state",
        body_capacity=capacity,
    )
    observer = WorkspaceSourceObservationRuntime(
        session=session, store=store, limits=limits
    )
    try:
        yield observer, session, store, package
    finally:
        observer.close()
        await session.stop()


async def test_retained_reader_is_exact_and_revalidation_has_later_interval(tmp_path):
    async with runtime(tmp_path) as (observer, _, _, package):
        (package / ".hidden").write_bytes(b"hidden")
        handle = observer.observe(root_relative_path="package")
        evidence = observer.evidence(handle)
        assert [b.relative_path for b in evidence.bodies] == [
            ".hidden",
            "manifest.toml",
            "plain.bin",
        ]
        assert observer.read(handle, relative_path="plain.bin") == b"initial"
        result = observer.revalidate(handle)
        assert (
            evidence.started_ns
            <= evidence.completed_ns
            <= result.started_ns
            <= result.completed_ns
        )
        assert result.observation_digest == evidence.observation_digest
        (package / "plain.bin").write_bytes(b"changed")
        assert observer.read(handle, relative_path="plain.bin") == b"initial"
        with pytest.raises(SourceObservationUnavailable, match="changed"):
            observer.revalidate(handle)


@pytest.mark.parametrize(
    "change", ["add", "delete", "manifest", "same_metadata", "root"]
)
async def test_complete_set_revalidation_rejects_changes(tmp_path, change):
    async with runtime(tmp_path) as (observer, _, _, package):
        handle = observer.observe(root_relative_path="package")
        if change == "add":
            (package / "unselected.txt").write_bytes(b"new")
        elif change == "delete":
            (package / "plain.bin").unlink()
        elif change == "manifest":
            (package / "manifest.toml").write_bytes(b"meaning = 2")
        elif change == "same_metadata":
            path = package / "plain.bin"
            old = path.stat()
            path.write_bytes(b"altered")
            os.utime(path, ns=(old.st_atime_ns, old.st_mtime_ns))
        else:
            package.rename(package.with_name("old"))
            package.mkdir()
            (package / "manifest.toml").write_bytes(b"meaning = 1")
            (package / "plain.bin").write_bytes(b"initial")
        with pytest.raises(SourceObservationUnavailable):
            observer.revalidate(handle)


async def test_eviction_and_restart_do_not_revive_reader(tmp_path):
    async with runtime(tmp_path, capacity=2) as (observer, session, store, _):
        handle = observer.observe(root_relative_path="package")
        store.record_bodies((b"evict-one", b"evict-two"))
        with pytest.raises(SourceObservationUnavailable, match="retained"):
            observer.read(handle, relative_path="plain.bin")
        fresh = observer.observe(root_relative_path="package")
        await session.stop()
        await session.start(background=False)
        with pytest.raises(SourceObservationUnavailable, match="lifetime"):
            observer.read(fresh, relative_path="plain.bin")
        other = WorkspaceSourceObservationRuntime(session=session, store=store)
        try:
            with pytest.raises(SourceObservationUnavailable, match="foreign"):
                other.read(fresh, relative_path="plain.bin")
            assert (
                other.read(
                    other.observe(root_relative_path="package"),
                    relative_path="plain.bin",
                )
                == b"initial"
            )
        finally:
            other.close()


async def test_wrong_issuer_forgery_release_and_inspection_mutation(tmp_path):
    async with runtime(tmp_path) as (observer, session, store, _):
        handle = observer.observe(root_relative_path="package")
        forged = object.__new__(WorkspaceRetainedRootObservation)
        with pytest.raises(SourceObservationUnavailable, match="foreign"):
            observer.evidence(forged)
        with pytest.raises(TypeError):
            pickle.dumps(handle)
        with pytest.raises(TypeError):
            copy.copy(handle)
        detached = observer.evidence(handle)
        object.__setattr__(detached.bodies[0], "body_ref", "foreign")
        assert observer.read(handle, relative_path="manifest.toml") == b"meaning = 1"
        other = WorkspaceSourceObservationRuntime(session=session, store=store)
        try:
            with pytest.raises(SourceObservationUnavailable, match="foreign"):
                other.evidence(handle)
        finally:
            other.close()
        observer.release(handle)
        with pytest.raises(SourceObservationUnavailable, match="foreign"):
            observer.evidence(handle)


@pytest.mark.parametrize(
    "change", ["file_symlink", "directory_symlink", "fifo", "limit", "traversal"]
)
async def test_no_partial_or_unconfined_capture(tmp_path, change):
    limits = (
        SourceObservationLimits(maximum_files=1)
        if change == "limit"
        else SourceObservationLimits()
    )
    async with runtime(tmp_path, limits=limits) as (observer, _, _, package):
        if change == "file_symlink":
            (package / "link").symlink_to(package / "plain.bin")
        elif change == "directory_symlink":
            (package / "link").symlink_to(tmp_path, target_is_directory=True)
        elif change == "fifo":
            os.mkfifo(package / "pipe")
        with pytest.raises(SourceObservationUnavailable):
            observer.observe(
                root_relative_path="../outside" if change == "traversal" else "package"
            )


async def test_retained_corruption_refuses(tmp_path):
    async with runtime(tmp_path) as (observer, _, _store, _):
        handle = observer.observe(root_relative_path="package")
        # Exercise the real durable store corruption boundary, not replacement IO.
        files = tuple((tmp_path / "state" / "repository_delta").glob("*/bodies/**/*"))
        path = next(p for p in files if p.is_file())
        path.write_bytes(b"corrupt")
        with pytest.raises(RuntimeError):
            observer.evidence(handle)


async def test_sequential_capture_does_not_claim_atomic_snapshot(tmp_path, monkeypatch):
    import aware_workspace_runtime.source_observation_io as io

    async with runtime(tmp_path) as (observer, _, _, package):
        original = io.os.read
        bodies_read = 0

        def read(fd, count):
            nonlocal bodies_read
            body = original(fd, count)
            if body:
                bodies_read += 1
                if bodies_read == 2:
                    (package / "manifest.toml").write_bytes(b"meaning = 2")
            return body

        with monkeypatch.context() as patch:
            patch.setattr(io.os, "read", read)
            handle = observer.observe(root_relative_path="package")
        # The first file was observed before that concurrent write. The reader
        # preserves this honest interval; later complete revalidation rejects.
        assert observer.read(handle, relative_path="manifest.toml") == b"meaning = 1"
        with pytest.raises(SourceObservationUnavailable, match="changed"):
            observer.revalidate(handle)


async def test_parent_process_capability_cannot_be_used_after_fork(
    tmp_path, monkeypatch
):
    import aware_workspace_runtime.source_observation as implementation

    async with runtime(tmp_path) as (observer, _, _, _):
        handle = observer.observe(root_relative_path="package")
        pid = os.getpid()
        with monkeypatch.context() as patch:
            patch.setattr(implementation.os, "getpid", lambda: pid + 1)
            with pytest.raises(SourceObservationUnavailable, match="lifetime"):
                observer.evidence(handle)


async def test_store_capacity_never_issues_partial_reader(tmp_path):
    async with runtime(tmp_path, capacity=1) as (observer, _, _, _):
        with pytest.raises(RuntimeError, match="capacity"):
            observer.observe(root_relative_path="package")


async def test_repository_root_package_retention_and_revalidation(tmp_path):
    async with runtime(tmp_path) as (observer, session, _, package):
        manifest = package.parent / "aware.environment.toml"
        manifest.write_bytes(b"root manifest")
        handle = observer.observe(root_relative_path=".")
        assert observer.evidence(handle).root_relative_path == "."
        assert (
            observer.read(handle, relative_path="aware.environment.toml")
            == b"root manifest"
        )
        observer.revalidate(handle)
        # Closing each duplicate must leave the admitted repository descriptor usable.
        observer.observe(root_relative_path=".")
        assert session.authority_admitted
        manifest.write_bytes(b"changed root manifest")
        with pytest.raises(SourceObservationUnavailable, match="changed"):
            observer.revalidate(handle)


@pytest.mark.parametrize(
    "root", ["", "..", "../outside", "./package", "package/..", "/"]
)
async def test_root_dot_exception_does_not_allow_traversal(tmp_path, root):
    async with runtime(tmp_path) as (observer, _, _, _):
        with pytest.raises(SourceObservationUnavailable):
            observer.observe(root_relative_path=root)


def test_dot_is_still_invalid_as_a_member_path():
    from aware_workspace_runtime.source_observation_io import validate_relative_path

    with pytest.raises(SourceObservationUnavailable):
        validate_relative_path(".")


async def test_declaration_observation_retains_only_authored_structure(tmp_path):
    async with runtime(tmp_path) as (observer, _, _, package):
        root = package.parent
        (root / "aware.workspace.toml").write_text(
            'aware = 1\n[workspace]\nhandle="demo"'
            '\n[[workspace.modules]]\nid="main"\npath="."\n'
        )
        (root / "aware.module.toml").write_text(
            'aware = 1\n[module]\n[[packages]]\nid="demo"\nkind="example"'
            '\nmanifest="package/manifest.toml"\nvisibility="module"\n'
        )
        handle = observer.observe_declarations()
        evidence = observer.declaration_evidence(handle)
        assert [body.relative_path for body in evidence.bodies] == [
            "aware.module.toml",
            "aware.workspace.toml",
            "package/manifest.toml",
        ]
        assert observer.read_declaration(
            handle, relative_path="package/manifest.toml"
        ) == b"meaning = 1"
        with pytest.raises(SourceObservationUnavailable, match="foreign"):
            observer.evidence(handle)
        with pytest.raises(SourceObservationUnavailable, match="foreign"):
            observer.declaration_evidence(object.__new__(WorkspaceRetainedRootObservation))
        assert observer.revalidate_declarations(handle).observation_digest == (
            evidence.observation_digest
        )
        (package / "plain.bin").write_bytes(b"unrelated")
        observer.revalidate_declarations(handle)
        (root / "aware.module.toml").write_text(
            (root / "aware.module.toml").read_text()
            + '\n[[packages]]\nid="extra"\nkind="example"'
            '\nmanifest="other/manifest.toml"\n'
        )
        (root / "other").mkdir()
        (root / "other/manifest.toml").write_bytes(b"other")
        with pytest.raises(SourceObservationUnavailable, match="changed"):
            observer.revalidate_declarations(handle)
        observer.release_declarations(handle)
        with pytest.raises(SourceObservationUnavailable, match="foreign"):
            observer.declaration_evidence(handle)


async def test_declaration_observation_refuses_symlink_and_eviction(tmp_path):
    async with runtime(tmp_path, capacity=2) as (observer, _, store, package):
        root = package.parent
        (root / "aware.workspace.toml").write_text(
            'aware = 1\n[workspace]\nhandle="demo"'
            '\n[[workspace.modules]]\nid="main"\npath="."\n'
        )
        (root / "aware.module.toml").write_text(
            'aware = 1\n[module]\n[[packages]]\nid="demo"\nkind="example"'
            '\nmanifest="package/manifest.toml"\nvisibility="module"\n'
        )
        # Capacity refusal does not issue a partial nominal handle.
        with pytest.raises(RuntimeError, match="capacity"):
            observer.observe_declarations()
    (tmp_path / "other").mkdir()
    async with runtime(tmp_path / "other", capacity=3) as (observer, _, store, package):
        root = package.parent
        (root / "aware.workspace.toml").write_text(
            'aware = 1\n[workspace]\nhandle="demo"'
            '\n[[workspace.modules]]\nid="main"\npath="."\n'
        )
        (root / "aware.module.toml").write_text(
            'aware = 1\n[module]\n[[packages]]\nid="demo"\nkind="example"'
            '\nmanifest="package/manifest.toml"\nvisibility="module"\n'
        )
        handle = observer.observe_declarations()
        store.record_bodies((b"a", b"b", b"c"))
        with pytest.raises(SourceObservationUnavailable, match="retained"):
            observer.declaration_evidence(handle)
        observer.release_declarations(handle)
        (package / "manifest.toml").unlink()
        (package / "manifest.toml").symlink_to(root / "aware.module.toml")
        with pytest.raises(SourceObservationUnavailable):
            observer.observe_declarations()


async def test_selected_package_excludes_only_declared_nested_root(tmp_path):
    async with runtime(tmp_path) as (observer, _, _, package):
        root = package.parent
        (root / "aware.workspace.toml").write_text(
            'aware = 1\n[workspace]\nhandle="demo"'
            '\n[[workspace.modules]]\nid="main"\npath="."\n'
        )
        (root / "aware.module.toml").write_text(
            'aware = 1\n[module]\n[[packages]]\nid="parent"\nkind="example"'
            '\nmanifest="package/manifest.toml"\nvisibility="module"\n'
            '[[packages]]\nid="child"\nkind="example"'
            '\nmanifest="package/child/manifest.toml"\nvisibility="module"\n'
        )
        child = package / "child"
        child.mkdir()
        (child / "manifest.toml").write_bytes(b"child")
        (child / "body.bin").write_bytes(b"child body")
        (package / ".hidden").write_bytes(b"parent hidden")
        declaration = observer.observe_declarations()
        parent = observer.observe_selected_package(
            declaration=declaration,
            workspace_manifest_path="aware.workspace.toml",
            module_id="main",
            package_id="parent",
        )
        evidence = observer.selected_package_evidence(parent)
        assert evidence.excluded_nested_roots == ("child",)
        assert [body.relative_path for body in evidence.bodies] == [
            ".hidden", "manifest.toml", "plain.bin"
        ]
        child_handle = observer.observe_selected_package(
            declaration=declaration,
            workspace_manifest_path="aware.workspace.toml",
            module_id="main",
            package_id="child",
        )
        assert [body.relative_path for body in observer.selected_package_evidence(child_handle).bodies] == [
            "body.bin", "manifest.toml"
        ]
        with pytest.raises(SourceObservationUnavailable, match="still_live"):
            observer.release_declarations(declaration)
        (child / "body.bin").write_bytes(b"changed child")
        observer.revalidate_selected_package(parent)
        with pytest.raises(SourceObservationUnavailable, match="changed"):
            observer.revalidate_selected_package(child_handle)
        observer.release_selected_package(child_handle)
        observer.release_selected_package(parent)
        observer.release_declarations(declaration)


async def test_selected_package_refuses_undeclared_child_and_changed_declaration(tmp_path):
    async with runtime(tmp_path) as (observer, _, _, package):
        root = package.parent
        (root / "aware.workspace.toml").write_text(
            'aware = 1\n[workspace]\nhandle="demo"'
            '\n[[workspace.modules]]\nid="main"\npath="."\n'
        )
        (root / "aware.module.toml").write_text(
            'aware = 1\n[module]\n[[packages]]\nid="demo"\nkind="example"'
            '\nmanifest="package/manifest.toml"\nvisibility="module"\n'
        )
        (package / "undeclared").mkdir()
        (package / "undeclared/body.bin").write_bytes(b"included")
        declaration = observer.observe_declarations()
        selected = observer.observe_selected_package(
            declaration=declaration,
            workspace_manifest_path="aware.workspace.toml",
            module_id="main",
            package_id="demo",
        )
        assert "undeclared/body.bin" in [
            body.relative_path for body in observer.selected_package_evidence(selected).bodies
        ]
        (root / "aware.module.toml").write_text(
            (root / "aware.module.toml").read_text() + "\n# changed\n"
        )
        with pytest.raises(SourceObservationUnavailable, match="changed"):
            observer.revalidate_selected_package(selected)


async def test_nested_workspace_profile_keeps_repository_relative_origin(tmp_path):
    async with runtime(tmp_path) as (observer, _, _, package):
        root = package.parent
        (root / "aware.repo.toml").write_text(
            'aware_repo = 1\n[repo]\nhandle="demo"\nworkspaces_dir="workspaces"'
            '\n[[workspaces]]\nhandle="kernel"\npath="kernel"\n'
        )
        workspace = root / "workspaces/kernel"
        workspace.mkdir(parents=True)
        (workspace / "aware.workspace.toml").write_text(
            'aware = 2\n[workspace]\nhandle="kernel"'
            '\n[[workspace.modules]]\nid="main"\npath="modules/main"\n'
            '[[workspace.code_semantic_contract_profile_packages]]'
            '\nprofile_key="kernel.default"'
            '\nprofile_package_ref="workspace://kernel#kernel.default"\n'
        )
        module = workspace / "modules/main"
        module.mkdir(parents=True)
        (module / "aware.module.toml").write_text(
            'aware = 1\n[module]\n[[packages]]\nid="demo"\nkind="example"'
            '\nmanifest="package/manifest.toml"\nvisibility="module"\n'
        )
        (module / "package").mkdir()
        (module / "package/manifest.toml").write_bytes(b"owner")
        profile = workspace / "semantic_contract/profiles/kernel.default"
        profile.mkdir(parents=True)
        (profile / "aware.semantic_contract_profile.toml").write_bytes(b"profile")
        declaration = observer.observe_declarations()
        paths = [
            body.relative_path for body in observer.declaration_evidence(declaration).bodies
        ]
        assert "workspaces/kernel/semantic_contract/profiles/kernel.default/aware.semantic_contract_profile.toml" in paths
        assert "workspaces/kernel/modules/main/package/manifest.toml" in paths
        observer.revalidate_declarations(declaration)


async def test_selected_repository_root_package_excludes_declared_child(tmp_path):
    async with runtime(tmp_path) as (observer, _, _, package):
        root = package.parent
        (root / "aware.workspace.toml").write_text(
            'aware = 1\n[workspace]\nhandle="demo"'
            '\n[[workspace.modules]]\nid="main"\npath="."\n'
        )
        (root / "aware.module.toml").write_text(
            'aware = 1\n[module]\n[[packages]]\nid="root"\nkind="example"'
            '\nmanifest="aware.example.toml"\nvisibility="module"\n'
            '[[packages]]\nid="child"\nkind="example"'
            '\nmanifest="package/manifest.toml"\nvisibility="module"\n'
        )
        (root / "aware.example.toml").write_bytes(b"root")
        declaration = observer.observe_declarations()
        selected = observer.observe_selected_package(
            declaration=declaration,
            workspace_manifest_path="aware.workspace.toml",
            module_id="main",
            package_id="root",
        )
        evidence = observer.selected_package_evidence(selected)
        assert evidence.package_root == "."
        assert evidence.excluded_nested_roots == ("package",)
        assert "package/manifest.toml" not in [
            body.relative_path for body in evidence.bodies
        ]
        assert observer.read_selected_package(
            selected, relative_path="aware.example.toml"
        ) == b"root"
        assert observer.read_selected_package_location(selected) == str(root)

@asynccontextmanager
async def selected_location(tmp_path):
    from test_declaration_scope_admission import fixture

    async with fixture(tmp_path) as (root, _, observer, _, observed, _):
        handle = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            module_id="main", package_id="example",
        )
        yield root, observer, handle


async def test_selected_location_failure_retires_under_parent_after_releasing_source_lock(tmp_path, monkeypatch):
    from contextlib import contextmanager

    async with selected_location(tmp_path) as (root, observer, handle):
        original = type(observer._exclusion).mutation
        calls = []

        @contextmanager
        def mutation(exclusion, *, retiring=False):
            assert not observer._lock._is_owned()
            with original(exclusion, retiring=retiring) as guard:
                calls.append(retiring)
                yield guard

        with monkeypatch.context() as patch:
            patch.setattr(type(observer._exclusion), "mutation", mutation)
            (root / "workspaces/network/modules/main/package/body.bin").write_bytes(b"changed")
            with pytest.raises(SourceObservationUnavailable):
                observer.read_selected_package_location(handle)
        assert calls == [True]


async def test_selected_location_registered_restamp_retires_without_foreign_dispatch(tmp_path):
    calls = []

    class Hostile:
        __slots__ = ("__weakref__",)

        def __getattribute__(self, name):
            calls.append("get")
            raise AssertionError(name)

        def __hash__(self):
            calls.append("hash")
            raise AssertionError("foreign hash")

        def __eq__(self, other):
            calls.append("eq")
            raise AssertionError("foreign equality")

    async with selected_location(tmp_path) as (_, observer, handle):
        original = type(handle)
        object.__setattr__(handle, "__class__", Hostile)
        try:
            with pytest.raises(SourceObservationUnavailable, match="expired_selected"):
                observer.read_selected_package_location(handle)
        finally:
            object.__setattr__(handle, "__class__", original)
        with pytest.raises(SourceObservationUnavailable, match="expired_selected"):
            observer.read_selected_package_location(handle)
        assert calls == []


async def test_selected_location_is_original_outer_root_and_unknown_use_is_isolated(tmp_path):
    async with selected_location(tmp_path) as (root, observer, handle):
        with pytest.raises(SourceObservationUnavailable):
            observer.read_selected_package_location(object())
        assert observer.read_selected_package_location(handle) == (
            str(root) + "/workspaces/network/modules/main/package"
        )
        assert observer._session.authority_admitted


@pytest.mark.parametrize("change", ["body", "package_symlink", "repository", "descriptor"])
async def test_selected_location_change_is_terminal_after_restoration(tmp_path, change):
    import shutil

    async with selected_location(tmp_path) as (root, observer, handle):
        package = root / "workspaces/network/modules/main/package"
        if change == "body":
            body = package / "body.bin"
            original = body.read_bytes()
            body.write_bytes(b"changed")

            def restore():
                body.write_bytes(original)
        elif change == "package_symlink":
            saved = package.with_name("saved")
            package.rename(saved)
            package.symlink_to(saved, target_is_directory=True)

            def restore():
                package.unlink()
                saved.rename(package)
        elif change == "repository":
            saved = root.with_name("original")
            root.rename(saved)
            shutil.copytree(saved, root)

            def restore():
                shutil.rmtree(root)
                saved.rename(root)
        else:
            original = observer._root_fd
            alias = os.dup(original)
            observer._root_fd = alias

            def restore():
                observer._root_fd = original
                os.close(alias)
        try:
            with pytest.raises(SourceObservationUnavailable):
                observer.read_selected_package_location(handle)
        finally:
            restore()
        with pytest.raises(SourceObservationUnavailable, match="expired_selected"):
            observer.read_selected_package_location(handle)


@pytest.mark.parametrize("change", ["session", "binding", "path", "binding_key", "binding_type", "descriptor"])
async def test_selected_location_rejects_foreign_binding_without_behavior(tmp_path, change):
    from dataclasses import replace

    calls = []

    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign behavior")

        def __eq__(self, other):
            calls.append("equal")
            raise AssertionError("foreign comparison")

    class RestampedBinding:
        __slots__ = ("binding_key", "filter_version", "root_path")

        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("restamped binding")

    async with selected_location(tmp_path) as (_, observer, handle):
        session = observer._session
        binding = session.binding
        if change == "session":
            observer._session = Foreign()

            def restore():
                observer._session = session
        elif change == "binding":
            session.binding = replace(binding)

            def restore():
                session.binding = binding
        elif change == "path":
            original = binding.root_path
            object.__setattr__(binding, "root_path", Foreign())

            def restore():
                object.__setattr__(binding, "root_path", original)
        elif change == "binding_key":
            original = binding.binding_key
            object.__setattr__(binding, "binding_key", Foreign())

            def restore():
                object.__setattr__(binding, "binding_key", original)
        elif change == "binding_type":
            object.__setattr__(binding, "__class__", RestampedBinding)

            def restore():
                object.__setattr__(binding, "__class__", WorkspaceRepositoryBinding)
        else:
            original = WorkspaceRepositoryBinding.root_path

            class HostileDescriptor:
                def __get__(self, instance, owner):
                    calls.append("descriptor")
                    raise AssertionError("foreign descriptor")

            WorkspaceRepositoryBinding.root_path = HostileDescriptor()

            def restore():
                WorkspaceRepositoryBinding.root_path = original
        try:
            with pytest.raises(SourceObservationUnavailable, match="binding_origin"):
                observer.read_selected_package_location(handle)
        finally:
            restore()
        assert calls == []
        with pytest.raises(SourceObservationUnavailable, match="expired_selected"):
            observer.read_selected_package_location(handle)
