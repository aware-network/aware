"""Workspace-owned local profile declarations; profile meaning belongs to Code."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping
from pathlib import PurePosixPath


class WorkspaceProfileDeclarationError(ValueError):
    pass


_KEY = re.compile(r"[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*", re.ASCII)
_HANDLE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,127}", re.ASCII)
_MAX_PROFILES = 256


def local_profile_paths_from_bytes(
    body: bytes, *, workspace_handle: str
) -> tuple[tuple[str, str], ...]:
    try:
        manifest = tomllib.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise WorkspaceProfileDeclarationError(
            "workspace_profile_manifest_invalid"
        ) from error
    return local_profile_paths(manifest, workspace_handle=workspace_handle)


def local_profile_paths(
    manifest: Mapping[str, object], *, workspace_handle: str
) -> tuple[tuple[str, str], ...]:
    """Read only explicitly published v2 profiles at their fixed local paths."""

    version = manifest.get("aware")
    if type(version) is not int or version not in (1, 2):
        raise WorkspaceProfileDeclarationError("workspace_manifest_version_unavailable")
    if version == 1:
        return ()
    workspace = manifest.get("workspace")
    if type(workspace) is not dict or workspace.get("handle") != workspace_handle:
        raise WorkspaceProfileDeclarationError("workspace_profile_owner_mismatch")
    if _HANDLE.fullmatch(workspace_handle) is None:
        raise WorkspaceProfileDeclarationError("workspace_profile_owner_noncanonical")
    declarations = workspace.get("code_semantic_contract_profile_packages", [])
    if type(declarations) is not list or len(declarations) > _MAX_PROFILES:
        raise WorkspaceProfileDeclarationError("workspace_profile_declarations_invalid")
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for declaration in declarations:
        if type(declaration) is not dict or set(declaration) != {
            "profile_key",
            "profile_package_ref",
        }:
            raise WorkspaceProfileDeclarationError("workspace_profile_declaration_shape")
        key = declaration["profile_key"]
        ref = declaration["profile_package_ref"]
        if (
            type(key) is not str
            or len(key.encode("utf-8")) > 192
            or _KEY.fullmatch(key) is None
            or key in seen
            or ref != f"workspace://{workspace_handle}#{key}"
        ):
            raise WorkspaceProfileDeclarationError(
                "workspace_profile_declaration_correspondence"
            )
        seen.add(key)
        result.append(
            (
                key,
                str(
                    PurePosixPath("semantic_contract")
                    / "profiles"
                    / key
                    / "aware.semantic_contract_profile.toml"
                ),
            )
        )
    return tuple(result)
