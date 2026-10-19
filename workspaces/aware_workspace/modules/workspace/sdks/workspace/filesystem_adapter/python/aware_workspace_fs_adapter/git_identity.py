"""Read-only prospective commit metadata, never identity or write authority.

Use Git's logical variables at the exact future metadata path, not a parent
repository's local config. The original preparation provider retains topology.
This advisory observation cannot freeze all later Git configuration changes.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from aware_workspace_sdk.repository_preparation import RepositoryPrepareRequest

from .repository_preparation import FilesystemRepositoryPreparationPort

_SELECTION_OVERRIDES = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_SHALLOW_FILE",
    "GIT_CONFIG",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
}


def _ident(value: str) -> dict[str, str] | None:
    match = re.fullmatch(
        r"([^<>\r\n]+) <([^<>\r\n]+)> -?\d+ [+-]\d{4}", value.rstrip("\r\n")
    )
    if match is None or not all(part.strip() for part in match.groups()):
        return None
    return {"name": match[1].strip(), "email": match[2].strip()}


def observe_initial_git_identity(*, repository_root: str) -> dict[str, Any]:
    port = FilesystemRepositoryPreparationPort(repository_root=repository_root)
    result: dict[str, Any] = {
        "schema_id": "aware.workspace.git-commit-identity-observation.v1",
        "repository_root": repository_root,
        "status": "unavailable",
        "author": None,
        "committer": None,
        "diagnostics": [],
        "authorizes_publication": False,
        "authorizes_retry": False,
        "authorizes_redispatch": False,
    }
    if any(key in os.environ for key in _SELECTION_OVERRIDES):
        result["diagnostics"] = ["git_repository_selection_override_refused"]
    else:
        retained = port.retain(RepositoryPrepareRequest(repository_root, True))
        try:
            retained.validate_current()
            if retained.snapshot is None or retained.snapshot["outcome"] == "refused":
                raise ValueError("git_identity_repository_source_refused")
            root = Path(repository_root)
            # Same ambient identity/configuration environment as the original
            # publisher. Explicit coordinates prevent parent-repo discovery.
            for role, variable in (
                ("author", "GIT_AUTHOR_IDENT"),
                ("committer", "GIT_COMMITTER_IDENT"),
            ):
                try:
                    observed = subprocess.run(
                        [
                            "git",
                            f"--git-dir={root / '.git'}",
                            f"--work-tree={root}",
                            "var",
                            variable,
                        ],
                        cwd=root if retained.root_fd is not None else root.parent,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=10,
                    )
                except (OSError, subprocess.TimeoutExpired):
                    result["diagnostics"].append(f"git_{role}_observation_unavailable")
                    continue
                identity = (
                    _ident(observed.stdout)
                    if observed.returncode == 0 and len(observed.stdout) <= 8192
                    else None
                )
                result[role] = identity
                if identity is None:
                    result["diagnostics"].append(f"git_{role}_identity_unavailable")
            retained.validate_current()
            if result["author"] is not None and result["committer"] is not None:
                result["status"] = "available"
        finally:
            retained.release()
    # No time coordinate or caller boolean: a content reference for an
    # observation only. It is neither sealed execution authority nor a grant.
    result["observation_ref"] = (
        "workspace-git-identity:sha256:"
        + hashlib.sha256(
            json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    return result
