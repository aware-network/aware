"""Pure repository checkout-profile grammar shared by source and legacy loaders.

V1 retains broad revision-based Workspace selection. V2 selects exact declared
Code leaves and composes profiles; it does not select semantic providers.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from packaging.utils import canonicalize_name

from .source_observation_io import validate_relative_path

_MAX_PROFILES = 256
_MAX_ROWS = 2500


def _text(value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError("checkout profile requires nonblank text")
    return value.strip()


def _strings(value: object) -> tuple[str, ...]:
    if type(value) is not list or len(value) > _MAX_ROWS:
        raise ValueError("checkout profile requires a bounded string array")
    result = tuple(_text(item) for item in value)
    if len(set(result)) != len(result):
        raise ValueError("duplicate checkout profile selector")
    return result


def _identifier(value: object) -> str:
    text = _text(value)
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", text):
        raise ValueError("checkout profile identifier invalid")
    return text


@dataclass(frozen=True, slots=True)
class CheckoutPackageSelection:
    workspace: str = ""
    module: str = ""
    package: str = ""
    code_manifest: str = ""
    repo_code_manifest: str = ""
    extras: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CheckoutProfile:
    key: str
    workspace_handles: tuple[str, ...] = ()
    version: int = 1
    include_profiles: tuple[str, ...] = ()
    package_selections: tuple[CheckoutPackageSelection, ...] = ()
    overlays: tuple[str, ...] = ()


def parse_checkout_profiles(
    payload: Mapping[str, object], workspace_handles: frozenset[str]
) -> tuple[CheckoutProfile, ...]:
    raw = payload.get("checkout_profile_sets", [])
    if type(raw) is not list or len(raw) > _MAX_PROFILES:
        raise ValueError("checkout profiles require a bounded table array")
    result: list[CheckoutProfile] = []
    for row in raw:
        if type(row) is not dict:
            raise ValueError("checkout profile must be a table")
        key = _text(row.get("key"))
        version = row.get("version", 1)
        if type(version) is not int or version not in (1, 2):
            raise ValueError("checkout profile version unsupported")
        if version == 1:
            handles = _strings(row.get("workspace_handles"))
            if not handles or not set(handles) <= workspace_handles:
                raise ValueError("legacy checkout profile requires declared Workspaces")
            # V1's historically ignored fields remain ignored by its grammar.
            result.append(CheckoutProfile(key, handles))
            continue
        if set(row) - {
            "key",
            "version",
            "include_profiles",
            "package_selections",
            "overlays",
        }:
            raise ValueError("unknown v2 checkout profile field")
        includes = _strings(row.get("include_profiles", []))
        overlays = _strings(row.get("overlays", []))
        selections = row.get("package_selections", [])
        if type(selections) is not list or len(selections) > _MAX_ROWS:
            raise ValueError("checkout selections require a bounded table array")
        members: list[CheckoutPackageSelection] = []
        for member in selections:
            if type(member) is not dict:
                raise ValueError("checkout package selection must be a table")
            shape = set(member) - {"extras"}
            if shape not in (
                {"workspace", "module", "package"},
                {"workspace", "code_manifest"},
                {"repo_code_manifest"},
            ):
                raise ValueError(
                    "checkout selection requires one exact declared address"
                )
            extras = tuple(
                sorted(
                    canonicalize_name(v, validate=True)
                    for v in _strings(member.get("extras", []))
                )
            )
            if len(set(extras)) != len(extras):
                raise ValueError("duplicate canonical extras")
            values = {
                key: _identifier(member[key])
                for key in ("workspace", "module", "package")
                if key in member
            }
            if "workspace" in values and values["workspace"] not in workspace_handles:
                raise ValueError("checkout selection Workspace is not declared")
            for field in ("code_manifest", "repo_code_manifest"):
                if field in member:
                    path = _text(member[field])
                    validate_relative_path(path)
                    values[field] = path
            members.append(CheckoutPackageSelection(**values, extras=extras))
        if len(set(members)) != len(members):
            raise ValueError("duplicate checkout package selection")
        if not includes and not members:
            raise ValueError("v2 checkout profile has no package selection")
        result.append(
            CheckoutProfile(
                key,
                version=2,
                include_profiles=includes,
                package_selections=tuple(members),
                overlays=overlays,
            )
        )
    indexed = {profile.key: profile for profile in result}
    if len(indexed) != len(result):
        raise ValueError("duplicate checkout profile key")
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(key: str) -> None:
        if key in visiting:
            raise ValueError("checkout profile composition cycle")
        if key in done:
            return
        if key not in indexed:
            raise ValueError(f"unknown included checkout profile: {key}")
        visiting.add(key)
        for child in indexed[key].include_profiles:
            visit(child)
        visiting.remove(key)
        done.add(key)

    for key in indexed:
        visit(key)
    return tuple(result)


def expand_checkout_profiles(
    profiles: Sequence[CheckoutProfile],
    requested: Sequence[str],
    memberships: Sequence[Mapping[str, str]],
    description: Mapping[str, Any],
) -> tuple[tuple[tuple[str, tuple[str, ...]], ...], tuple[str, ...], tuple[str, ...]]:
    """Resolve exact profile leaves against the same retained composition."""
    if len(requested) > _MAX_PROFILES:
        raise ValueError("requested checkout profiles exceed bound")
    indexed = {profile.key: profile for profile in profiles}
    workspaces = {
        w["workspace_handle"]: w for w in description["repository"]["workspaces"]
    }
    visited: set[str] = set()
    leaves: set[tuple[str, tuple[str, ...]]] = set()
    overlays: set[str] = set()

    def visit(key: str) -> None:
        if key in visited:
            return
        if key not in indexed:
            raise ValueError(f"unknown checkout profile: {key}")
        profile = indexed[key]
        if profile.version != 2:
            raise ValueError(
                f"legacy profile {key} requires complete revision/generated coverage; use an explicit v2 source profile"
            )
        visited.add(key)
        for child in profile.include_profiles:
            visit(child)
        overlays.update(profile.overlays)
        for selection in profile.package_selections:
            if selection.repo_code_manifest:
                matches = [
                    r["manifest_path"]
                    for r in memberships
                    if r["declaration_path"] == "aware.repo.toml"
                    and r["manifest_path"] == selection.repo_code_manifest
                ]
            elif selection.code_manifest:
                workspace = workspaces[selection.workspace]
                path = str(
                    PurePosixPath(workspace["relative_path"]) / selection.code_manifest
                )
                matches = [
                    r["manifest_path"]
                    for r in memberships
                    if r["declaration_path"] == workspace["manifest_path"]
                    and r["manifest_path"] == path
                ]
            else:
                matches = [
                    r["manifest_path"]
                    for r in memberships
                    if r.get("workspace") == selection.workspace
                    and r.get("module") == selection.module
                    and r.get("package") == selection.package
                    and r.get("kind") == "code"
                ]
            if len(set(matches)) != 1:
                raise ValueError(
                    f"profile {key} member is not one declared Python Code leaf: {selection}"
                )
            leaves.add((matches[0], selection.extras))
            if len(leaves) > _MAX_ROWS:
                raise ValueError("composed checkout selection exceeds bound")

    for key in requested:
        visit(key)
    return tuple(sorted(leaves)), tuple(sorted(visited)), tuple(sorted(overlays))


def checkout_repository_files(
    payload: Mapping[str, object],
    overlays: Sequence[str],
) -> tuple[dict[str, str], ...]:
    raw = payload.get("repository_files", [])
    if type(raw) is not list or len(raw) > _MAX_ROWS:
        raise ValueError("repository files require a bounded table array")
    rows: list[dict[str, str]] = []
    targets: set[str] = set()
    available: set[str] = set()
    for row in raw:
        if type(row) is not dict or set(row) - {
            "role",
            "source_path",
            "target_path",
            "overlay",
        }:
            raise ValueError("invalid repository file declaration")
        item = {
            key: _text(row.get(key)) for key in ("role", "source_path", "target_path")
        }
        for field in ("source_path", "target_path"):
            validate_relative_path(item[field])
        overlay = _text(row["overlay"]) if row.get("overlay") is not None else ""
        if item["target_path"] in targets:
            raise ValueError("duplicate repository file target")
        targets.add(item["target_path"])
        if overlay:
            available.add(overlay)
        if not overlay or overlay in overlays:
            rows.append({**item, "overlay": overlay})
    if not set(overlays) <= available:
        raise ValueError("unknown repository-file overlay")
    return tuple(sorted(rows, key=lambda row: row["target_path"]))
