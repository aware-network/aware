from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest
from aware_code_service_dto.code.features.package_delta import CodePackageDelta
from aware_code_service_dto.code.features.package_delta import CodePackageDeltaKind
from aware_code_service_dto.code.features.package_delta import CodePackageDeltaPath
from aware_code_service_dto.code.features.package_common import CodePackagePathRole
from aware_file_system_service_dto.file_system.service_operation import (
    ApplyFileSystemDeltaRequest,
)
from aware_file_system_service_dto.file_system.service_operation import (
    ApplyFileSystemDeltaResponse,
)
from aware_file_system_service_dto.file_system.service_operation import (
    CollectFileSystemDeltaRequest,
)
from aware_file_system_service_dto.file_system.service_operation import (
    CollectFileSystemDeltaResponse,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemApplyReceipt,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemBackendKind,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemDeltaOperation,
)
from aware_file_system_service_dto.file_system.service_operation import (
    ScanFileSystemSnapshotRequest,
)
from aware_file_system_service_dto.file_system.service_operation import (
    ScanFileSystemSnapshotResponse,
)
from aware_file_system_service_dto.file_system.service_operation import (
    VerifyFileSystemRootRequest,
)
from aware_file_system_service_dto.file_system.service_operation import (
    VerifyFileSystemRootResponse,
)
from aware_file_system_sdk import (
    AwareFileSystemSdk,
    FileSystemCodePackageDeltaClient,
    FileSystemSdkError,
)


class _FakeDeltaClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.apply_requests: list[ApplyFileSystemDeltaRequest] = []
        self.collect_requests: list[CollectFileSystemDeltaRequest] = []

    async def apply(
        self,
        request: ApplyFileSystemDeltaRequest,
    ) -> ApplyFileSystemDeltaResponse:
        self.apply_requests.append(request)
        if self.fail:
            return ApplyFileSystemDeltaResponse(
                success=False,
                error="apply failed",
                receipt=None,
            )
        created_count = 0
        updated_count = 0
        deleted_count = 0
        bytes_written = 0
        root = Path(request.root.root_path)
        if not request.dry_run:
            for entry in request.delta_set.entries:
                target = root / entry.path.relative_path
                if entry.operation == FileSystemDeltaOperation.delete:
                    if target.exists():
                        target.unlink()
                        deleted_count += 1
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                existed = target.exists()
                content = entry.content_text or ""
                target.write_text(content, encoding="utf-8")
                bytes_written += len(content.encode("utf-8"))
                if existed:
                    updated_count += 1
                else:
                    created_count += 1
        receipt = FileSystemApplyReceipt(
            root=request.root,
            success=True,
            created_count=created_count,
            updated_count=updated_count,
            deleted_count=deleted_count,
            bytes_written=bytes_written,
            digest_verified_count=request.delta_set.totals.digest_count
            if request.delta_set.totals is not None
            else 0,
        )
        return ApplyFileSystemDeltaResponse(success=True, receipt=receipt)

    async def collect(
        self,
        request: CollectFileSystemDeltaRequest,
    ) -> CollectFileSystemDeltaResponse:
        self.collect_requests.append(request)
        return CollectFileSystemDeltaResponse(success=True)


class _FakeRootClient:
    def __init__(self) -> None:
        self.requests: list[VerifyFileSystemRootRequest] = []

    async def verify(
        self,
        request: VerifyFileSystemRootRequest,
    ) -> VerifyFileSystemRootResponse:
        self.requests.append(request)
        return VerifyFileSystemRootResponse(success=True, root_ok=True)


class _FakeSnapshotClient:
    def __init__(self) -> None:
        self.requests: list[ScanFileSystemSnapshotRequest] = []

    async def scan(
        self,
        request: ScanFileSystemSnapshotRequest,
    ) -> ScanFileSystemSnapshotResponse:
        self.requests.append(request)
        return ScanFileSystemSnapshotResponse(success=True)


class _FakeFileSystemNamespace:
    def __init__(self, *, fail_apply: bool = False) -> None:
        self.delta = _FakeDeltaClient(fail=fail_apply)
        self.root = _FakeRootClient()
        self.snapshot = _FakeSnapshotClient()


class _FakeApiClient:
    def __init__(self, *, fail_apply: bool = False) -> None:
        self.filesystem = _FakeFileSystemNamespace(fail_apply=fail_apply)


@pytest.mark.asyncio
async def test_verify_root_forwards_root_and_paths(tmp_path: Path) -> None:
    api_client = _FakeApiClient()
    sdk = AwareFileSystemSdk(api_client=api_client)

    response = await sdk.verify_root(
        root_path=tmp_path,
        relative_paths=("pkg/src/main.py",),
        display_name="test-root",
    )

    assert response.root_ok is True
    request = api_client.filesystem.root.requests[0]
    assert request.root.root_path == tmp_path.resolve().as_posix()
    assert request.root.display_name == "test-root"
    assert [path.relative_path for path in request.relative_paths] == [
        "pkg/src/main.py"
    ]


@pytest.mark.asyncio
async def test_apply_code_package_delta_uses_code_api_dto_and_writes(tmp_path: Path) -> None:
    api_client = _FakeApiClient()
    sdk = AwareFileSystemSdk(api_client=api_client)
    client = FileSystemCodePackageDeltaClient(file_system_sdk=sdk)
    content = "print('ok')\n"
    expected_sha256 = sha256(content.encode("utf-8")).hexdigest()
    delta = CodePackageDelta(
        package_name="demo",
        package_root="packages/demo",
        sources_root="packages/demo/src",
        paths=[
            CodePackageDeltaPath(
                relative_path="src/main.py",
                kind=CodePackageDeltaKind.create,
                path_role=CodePackagePathRole.generated_code,
                content_text=content,
                after_hash=f"sha256:{expected_sha256}",
            )
        ],
    )

    result = await client.apply(
        root_path=tmp_path,
        code_package_deltas=(delta,),
        backend_kind=FileSystemBackendKind.rust,
    )

    target = tmp_path / "packages/demo/src/main.py"
    assert target.read_text(encoding="utf-8") == content
    assert result.applied_files[0].root_relative_path == "packages/demo/src/main.py"
    assert result.applied_files[0].after_sha256 == expected_sha256
    request = api_client.filesystem.delta.apply_requests[0]
    assert request.backend_kind is FileSystemBackendKind.rust
    assert request.delta_set.entries[0].path.relative_path == "packages/demo/src/main.py"
    assert request.delta_set.totals.create_count == 1
    assert request.delta_set.totals.digest_count == 1
    assert result.evidence["code_api_dto_package"] == "aware_code_service_api"


@pytest.mark.asyncio
async def test_empty_code_package_delta_apply_sends_empty_delta_set(
    tmp_path: Path,
) -> None:
    api_client = _FakeApiClient()
    sdk = AwareFileSystemSdk(api_client=api_client)
    client = FileSystemCodePackageDeltaClient(file_system_sdk=sdk)

    result = await client.apply(root_path=tmp_path, code_package_deltas=())

    assert result.applied_files == ()
    request = api_client.filesystem.delta.apply_requests[0]
    assert request.delta_set.entries == []
    assert request.delta_set.totals.create_count == 0
    assert request.delta_set.totals.byte_count == 0


def test_code_package_delta_plan_uses_package_root_relative_paths(
    tmp_path: Path,
) -> None:
    api_client = _FakeApiClient()
    sdk = AwareFileSystemSdk(api_client=api_client)
    client = FileSystemCodePackageDeltaClient(file_system_sdk=sdk)
    delta = CodePackageDelta(
        package_name="demo",
        package_root="packages/demo",
        sources_root="src",
        paths=[
            CodePackageDeltaPath(
                relative_path="src/main.py",
                kind=CodePackageDeltaKind.create,
                path_role=CodePackagePathRole.authored_source,
                content_text="print('ok')\n",
            )
        ],
    )

    plan = client.plan(root_path=tmp_path, code_package_deltas=(delta,))

    assert plan.planned_entries[0].root_relative_path == "packages/demo/src/main.py"
    assert plan.delta_set.entries[0].path.relative_path == "packages/demo/src/main.py"


def test_code_package_delta_plan_uses_sources_root_for_source_relative_paths(
    tmp_path: Path,
) -> None:
    api_client = _FakeApiClient()
    sdk = AwareFileSystemSdk(api_client=api_client)
    client = FileSystemCodePackageDeltaClient(file_system_sdk=sdk)
    delta = CodePackageDelta(
        package_name="demo",
        package_root="packages/demo",
        sources_root="packages/demo/src",
        paths=[
            CodePackageDeltaPath(
                relative_path="main.py",
                kind=CodePackageDeltaKind.create,
                path_role=CodePackagePathRole.generated_code,
                content_text="print('ok')\n",
            )
        ],
    )

    plan = client.plan(root_path=tmp_path, code_package_deltas=(delta,))

    assert plan.planned_entries[0].root_relative_path == "packages/demo/src/main.py"
    assert plan.delta_set.entries[0].path.relative_path == "packages/demo/src/main.py"


@pytest.mark.asyncio
async def test_digest_mismatch_fails_before_apply(tmp_path: Path) -> None:
    api_client = _FakeApiClient()
    sdk = AwareFileSystemSdk(api_client=api_client)
    client = FileSystemCodePackageDeltaClient(file_system_sdk=sdk)
    delta = CodePackageDelta(
        package_name="demo",
        package_root="packages/demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="main.py",
                kind=CodePackageDeltaKind.create,
                content_text="different",
                after_hash="0" * 64,
            )
        ],
    )

    with pytest.raises(FileSystemSdkError, match="digest mismatch"):
        await client.apply(root_path=tmp_path, code_package_deltas=(delta,))

    assert api_client.filesystem.delta.apply_requests == []


@pytest.mark.asyncio
async def test_path_escape_fails_before_apply(tmp_path: Path) -> None:
    api_client = _FakeApiClient()
    sdk = AwareFileSystemSdk(api_client=api_client)
    client = FileSystemCodePackageDeltaClient(file_system_sdk=sdk)
    delta = CodePackageDelta(
        package_name="demo",
        package_root="packages/demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="../outside.py",
                kind=CodePackageDeltaKind.create,
                content_text="x",
            )
        ],
    )

    with pytest.raises(FileSystemSdkError, match="escapes"):
        await client.apply(root_path=tmp_path, code_package_deltas=(delta,))

    assert api_client.filesystem.delta.apply_requests == []


@pytest.mark.asyncio
async def test_apply_failure_is_reported(tmp_path: Path) -> None:
    api_client = _FakeApiClient(fail_apply=True)
    sdk = AwareFileSystemSdk(api_client=api_client)
    client = FileSystemCodePackageDeltaClient(file_system_sdk=sdk)
    delta = CodePackageDelta(
        package_name="demo",
        package_root="packages/demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="main.py",
                kind=CodePackageDeltaKind.create,
                content_text="x",
            )
        ],
    )

    with pytest.raises(FileSystemSdkError, match="apply failed"):
        await client.apply(root_path=tmp_path, code_package_deltas=(delta,))

    assert len(api_client.filesystem.delta.apply_requests) == 1
