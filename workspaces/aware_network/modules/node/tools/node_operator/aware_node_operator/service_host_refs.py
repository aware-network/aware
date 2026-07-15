from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ServiceHostImplementationPackageRefInput:
    """Committed ServicePackage ref rendered into ServiceHost bootstrap config."""

    family_key: str
    package_kind: str
    package_name: str
    manifest_path: Path | None = None
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    source_code_package_id: str | None = None

    def to_payload(self) -> dict[str, str]:
        payload = {
            "family_key": self.family_key,
            "package_kind": self.package_kind,
            "package_name": self.package_name,
            "manifest_path": (
                self.manifest_path.as_posix()
                if self.manifest_path is not None
                else None
            ),
            "workspace_package_id": self.workspace_package_id,
            "semantic_package_id": self.semantic_package_id,
            "semantic_object_instance_graph_commit_id": (
                self.semantic_object_instance_graph_commit_id
            ),
            "semantic_head_commit_id": self.semantic_head_commit_id,
            "semantic_branch_id": self.semantic_branch_id,
            "semantic_root_kind": self.semantic_root_kind,
            "semantic_root_id": self.semantic_root_id,
            "semantic_root_object_instance_graph_commit_id": (
                self.semantic_root_object_instance_graph_commit_id
            ),
            "source_code_package_id": self.source_code_package_id,
        }
        return {
            key: value
            for key, value in payload.items()
            if value is not None and str(value).strip()
        }
