from __future__ import annotations

import hashlib
from pathlib import Path

_DAEMON_FINGERPRINT_PATHS = (
    Path("workspaces/aware_network/modules/interface/services/interface/aware_interface_service"),
    Path("workspaces/aware_network/modules/interface/services/interface/pyproject.toml"),
    Path("workspaces/aware_network/modules/interface/apis/interface/python/aware_interface_service_api/aware_interface_service_api"),
    Path("workspaces/aware_network/modules/interface/apis/interface/python/aware_interface_service_protocol/aware_interface_service_protocol"),
    Path("workspaces/aware_network/modules/interface/apis/interface/python/aware_interface_service_dto/aware_interface_service_dto"),
    Path("workspaces/aware_network/modules/interface/apis/interface/python/aware_interface_service_dto/pyproject.toml"),
)


def _iter_daemon_fingerprint_files(*, repository_root: Path) -> list[Path]:
    files: list[Path] = []
    for relative_path in _DAEMON_FINGERPRINT_PATHS:
        path = (repository_root / relative_path).resolve()
        if path.is_dir():
            files.extend(
                child
                for child in sorted(path.rglob("*.py"))
                if "__pycache__" not in child.parts
            )
            continue
        if path.is_file():
            files.append(path)
    return files


def compute_daemon_source_fingerprint(*, repository_root: Path) -> str:
    resolved_root = repository_root.resolve()
    digest = hashlib.sha256()
    for file_path in _iter_daemon_fingerprint_files(repository_root=resolved_root):
        relative_path = file_path.relative_to(resolved_root)
        digest.update(str(relative_path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
