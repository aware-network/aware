from __future__ import annotations

import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest
from aware_code_service_dto.code.features.package_common import CodePackagePathRole
from aware_code_service_dto.code.features.package_delta import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_file_system_service_dto.file_system.service_operation import (
    ResolveFileSystemBackendCapabilitiesRequest,
)
from aware_file_system_service_dto.file_system.service_operation import (
    ScanFileSystemSnapshotRequest,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemBackendKind,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemFilterProfile,
)
from aware_file_system_service_dto.file_system.types import FileSystemRootRef
from aware_file_system_sdk import (
    AwareFileSystemSdk,
    FileSystemCodePackageDeltaClient,
    build_direct_file_system_runtime_api_client,
)


@pytest.mark.asyncio
async def test_direct_filesystem_runtime_applies_code_package_delta(
    tmp_path: Path,
) -> None:
    api_client = build_direct_file_system_runtime_api_client()
    sdk = AwareFileSystemSdk(
        api_client=api_client,
        backend_kind=FileSystemBackendKind.python,
    )
    client = FileSystemCodePackageDeltaClient(file_system_sdk=sdk)
    content = "print('direct-runtime')\n"
    expected_sha256 = sha256(content.encode("utf-8")).hexdigest()

    result = await client.apply(
        root_path=tmp_path,
        code_package_deltas=(
            CodePackageDelta(
                package_name="demo",
                package_root="packages/demo",
                sources_root="src",
                paths=[
                    CodePackageDeltaPath(
                        relative_path="src/main.py",
                        kind=CodePackageDeltaKind.create,
                        path_role=CodePackagePathRole.generated_code,
                        content_text=content,
                        after_hash=f"sha256:{expected_sha256}",
                    )
                ],
            ),
        ),
    )

    target = tmp_path / "packages" / "demo" / "src" / "main.py"
    assert target.read_text(encoding="utf-8") == content
    assert result.applied_files[0].root_relative_path == "packages/demo/src/main.py"
    assert result.file_system_apply_receipt is not None
    assert result.file_system_apply_receipt["digest_verified_count"] == 1
    assert result.evidence["backend_kind_requested"] == "python"
    assert result.evidence["backend_receipt"]["backend_kind"] == "python"


@pytest.mark.asyncio
async def test_direct_filesystem_runtime_scans_and_reports_capabilities(
    tmp_path: Path,
) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
    api_client = build_direct_file_system_runtime_api_client()

    scan = await api_client.filesystem.snapshot.scan(
        ScanFileSystemSnapshotRequest(
            root=FileSystemRootRef(root_path=tmp_path.as_posix()),
            filter_profile=FileSystemFilterProfile.canonical_source,
            include_hashes=True,
            force_refresh=True,
        )
    )
    capabilities = await api_client.filesystem.backend.capabilities(
        ResolveFileSystemBackendCapabilitiesRequest(
            requested_backend_kind=FileSystemBackendKind.python,
        )
    )

    assert scan.success is True
    assert scan.snapshot is not None
    assert [entry.path.relative_path for entry in scan.snapshot.entries] == [
        "src/main.py"
    ]
    assert scan.snapshot.entries[0].digest is not None
    assert capabilities.success is True
    assert capabilities.capabilities is not None
    assert capabilities.capabilities.selected_backend is not None
    assert (
        capabilities.capabilities.selected_backend.backend_kind
        is FileSystemBackendKind.python
    )


def test_direct_filesystem_runtime_import_boundary_excludes_service_modules() -> None:
    script = (
        "import json\n"
        "import sys\n"
        "from aware_file_system_sdk import build_direct_file_system_runtime_api_client\n"
        "build_direct_file_system_runtime_api_client()\n"
        "print(json.dumps(sorted(sys.modules)))\n"
    )
    process = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
    loaded = set(json.loads(process.stdout))
    forbidden = sorted(
        module
        for module in loaded
        if module == "aware_file_system_service"
        or module.startswith("aware_file_system_service.")
        or module == "aware_service_runtime"
        or module.startswith("aware_service_runtime.")
        or module == "aware_service_service"
        or module.startswith("aware_service_service.")
    )

    assert forbidden == []
