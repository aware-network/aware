"""Explicit Aware architecture setup, separate from physical repository init."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True, slots=True)
class ArchitectureSetupRequest:
    operation: Literal[
        "repository", "workspace", "module", "python_package", "package_manager"
    ]
    name: str = ""
    workspace: str = ""
    module: str = ""
    path: str = ""
    distribution: str = ""
    import_root: str = ""
    version: str = "0.1.0"
    requires_python: str = ">=3.12"
    dependencies: tuple[str, ...] = ()
    license_expression: str = ""
    owner: Literal["repository", "workspace", "module"] = "module"


@dataclass(frozen=True, slots=True)
class ArchitectureSetupChange:
    path: str
    before_sha256: str | None
    after_sha256: str


@dataclass(frozen=True, slots=True)
class ArchitectureSetupPreview:
    operation: str
    plan_sha256: str
    changes: tuple[ArchitectureSetupChange, ...]
    input_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ArchitectureSetupReceipt:
    operation: str
    plan_sha256: str
    status: str
    written_paths: tuple[str, ...]
    remaining_paths: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


class ArchitectureSetupError(RuntimeError):
    def __init__(
        self,
        code: str,
        *,
        receipt: ArchitectureSetupReceipt | PackageManagerReceipt | None = None,
    ):
        self.receipt = receipt
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class PackageManagerReceipt:
    operation: str
    resolution_root: str
    command: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str
    before_lock_sha256: str | None
    after_lock_sha256: str | None
    status: Literal["completed", "uncertain"] = "completed"
    before_lock_observation: Literal["present", "absent"] = "absent"
    after_lock_observation: Literal["present", "absent", "unavailable"] = "unavailable"
    diagnostics: tuple[str, ...] = ()


class WorkspaceSetupClient:
    """One explicitly selected local provider. Use as a context manager."""

    def __init__(self, runtime, token):
        if token is not _TOKEN:
            raise TypeError("select_setup_provider_explicitly")
        self._runtime = runtime

    @classmethod
    def filesystem(
        cls, *, repository_root: Path, uv_executable: Path | None = None
    ) -> WorkspaceSetupClient:
        fs = importlib.import_module("aware_workspace_fs_adapter.architecture_setup")
        runtime = importlib.import_module("aware_workspace_runtime.architecture_setup")
        return cls(
            runtime.ArchitectureSetupRuntime(
                fs.FilesystemArchitectureSetup(
                    repository_root=repository_root,
                    uv_executable=uv_executable,
                )
            ),
            _TOKEN,
        )

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        self._runtime.close()

    def preview(self, request: ArchitectureSetupRequest) -> ArchitectureSetupPreview:
        return self._runtime.preview(request)

    def apply(
        self,
        request: ArchitectureSetupRequest,
        *,
        expected_plan_sha256: str | None = None,
    ) -> ArchitectureSetupReceipt:
        return self._runtime.apply(request, expected_plan_sha256=expected_plan_sha256)

    def create_repository(self, name: str, *, license_expression: str) -> Repository:
        receipt = self.apply(
            ArchitectureSetupRequest(
                "repository",
                name=name,
                license_expression=license_expression,
            )
        )
        return Repository(self, receipt, _TOKEN)

    def repository(self) -> Repository:
        self._runtime.repository()
        return Repository(self, None, _TOKEN)


_TOKEN = object()


class Repository:
    def __init__(self, client, receipt, token):
        if token is not _TOKEN:
            raise TypeError("use_setup_client")
        self._client, self.receipt = client, receipt

    def create_workspace(self, name: str, *, path: str | None = None) -> Workspace:
        receipt = self._client.apply(
            ArchitectureSetupRequest("workspace", name=name, path=path or name)
        )
        return Workspace(self._client, name, receipt, _TOKEN)

    def workspace(self, name: str) -> Workspace:
        self._client._runtime.workspace(name)
        return Workspace(self._client, name, None, _TOKEN)

    def create_python_package(
        self,
        name: str,
        *,
        distribution: str,
        import_root: str,
        path: str | None = None,
        version: str = "0.1.0",
        requires_python: str = ">=3.12",
        dependencies: tuple[str, ...] = (),
    ) -> PythonPackage:
        return _create_python_package(
            self._client,
            "repository",
            name,
            distribution=distribution,
            import_root=import_root,
            path=path,
            version=version,
            requires_python=requires_python,
            dependencies=dependencies,
        )

    def align_package_manager(self) -> ArchitectureSetupReceipt:
        return self._client.apply(ArchitectureSetupRequest("package_manager"))

    def check_locks(self) -> tuple[PackageManagerReceipt, ...]:
        return self._client._runtime.locks(check=True)

    def update_locks(self) -> tuple[PackageManagerReceipt, ...]:
        return self._client._runtime.locks(check=False)


class Workspace:
    def __init__(self, client, name, receipt, token):
        if token is not _TOKEN:
            raise TypeError("use_repository")
        self._client, self.name, self.receipt = client, name, receipt

    def align_package_manager(self) -> ArchitectureSetupReceipt:
        return self._client.apply(
            ArchitectureSetupRequest("package_manager", workspace=self.name)
        )

    def check_locks(self) -> tuple[PackageManagerReceipt, ...]:
        return self._client._runtime.locks(check=True, workspace=self.name)

    def update_locks(self) -> tuple[PackageManagerReceipt, ...]:
        return self._client._runtime.locks(check=False, workspace=self.name)

    def create_module(self, name: str, *, path: str | None = None) -> Module:
        receipt = self._client.apply(
            ArchitectureSetupRequest(
                "module",
                name=name,
                workspace=self.name,
                path=path or f"modules/{name}",
            )
        )
        return Module(self._client, self.name, name, receipt, _TOKEN)

    def module(self, name: str) -> Module:
        self._client._runtime.module(self.name, name)
        return Module(self._client, self.name, name, None, _TOKEN)

    def create_python_package(
        self,
        name: str,
        *,
        distribution: str,
        import_root: str,
        path: str | None = None,
        version: str = "0.1.0",
        requires_python: str = ">=3.12",
        dependencies: tuple[str, ...] = (),
    ) -> PythonPackage:
        return _create_python_package(
            self._client,
            "workspace",
            name,
            workspace=self.name,
            distribution=distribution,
            import_root=import_root,
            path=path,
            version=version,
            requires_python=requires_python,
            dependencies=dependencies,
        )


class Module:
    def __init__(self, client, workspace, name, receipt, token):
        if token is not _TOKEN:
            raise TypeError("use_workspace")
        self._client, self.workspace, self.name, self.receipt = (
            client,
            workspace,
            name,
            receipt,
        )

    def create_python_package(
        self,
        name: str,
        *,
        distribution: str,
        import_root: str,
        path: str | None = None,
        version: str = "0.1.0",
        requires_python: str = ">=3.12",
        dependencies: tuple[str, ...] = (),
    ) -> PythonPackage:
        return _create_python_package(
            self._client,
            "module",
            name,
            workspace=self.workspace,
            module=self.name,
            distribution=distribution,
            import_root=import_root,
            path=path,
            version=version,
            requires_python=requires_python,
            dependencies=dependencies,
        )


def _create_python_package(
    client,
    owner,
    name,
    *,
    distribution,
    import_root,
    path,
    version,
    requires_python,
    dependencies,
    workspace="",
    module="",
):
    receipt = client.apply(
        ArchitectureSetupRequest(
            "python_package",
            name=name,
            owner=owner,
            workspace=workspace,
            module=module,
            path=path or f"libs/{name}/python",
            distribution=distribution,
            import_root=import_root,
            version=version,
            requires_python=requires_python,
            dependencies=dependencies,
        )
    )
    return PythonPackage(distribution, import_root, receipt)


@dataclass(frozen=True, slots=True)
class PythonPackage:
    distribution: str
    import_root: str
    receipt: ArchitectureSetupReceipt
