"""Workspace-owned qualified selection interpretation, never Code policy."""

import re
from typing import NoReturn

from aware_code_semantic_contract_runtime import ContentDigest
from aware_code_semantic_contract_runtime.dependency_scope_closure import (
    MAX_EDGES,
    DependencyScopeDeclaration,
    DependencyScopeEdge,
    DependencyScopeRestriction,
)

from .source_observation_io import SourceObservationUnavailable


def refuse(reason: str) -> NoReturn:
    raise SourceObservationUnavailable(reason)


def canonical_handle(value):
    if (
        type(value) is not str
        or re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,127}", value, re.ASCII) is None
    ):
        refuse("dependency_handle_noncanonical")
    return value


def text(value):
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or len(value.encode()) > 4096
    ):
        refuse("dependency_field_unavailable")
    return value


def selections(workspace, *, path, digest, targets):
    dependencies = workspace.get("dependencies", [])
    if type(dependencies) is not list or len(dependencies) > MAX_EDGES:
        refuse("dependency_declaration_bound")
    result, ids = [], set()
    for index, dependency in enumerate(dependencies):
        if type(dependency) is not dict:
            refuse("dependency_declaration_shape")
        identifier = text(dependency.get("id"))
        if identifier in ids:
            refuse("duplicate_dependency_id")
        ids.add(identifier)
        profiles = dependency.get("code_semantic_contract_profile_packages", [])
        if type(profiles) is not list or len(profiles) > MAX_EDGES:
            refuse("profile_selection_bound")
        if not profiles:
            continue
        source = text(dependency.get("source"))
        if dependency.get("kind") != "workspace" or not source.startswith(
            "workspace://"
        ):
            refuse("dependency_source_unsupported")
        target = canonical_handle(source[len("workspace://") :])
        if target not in targets:
            refuse("dependency_target_not_member")
        if (
            dependency.get("channel") != "local"
            or dependency.get("revision") != "workspace-revision:local"
        ):
            refuse("dependency_selection_not_local_observation")
        refs = set()
        for profile_index, profile in enumerate(profiles):
            if type(profile) is not dict or set(profile) - {
                "profile_package_ref",
                "profile_key",
                "semantic_contract_provider_keys",
                "status",
                "runtime_import_mode",
                "runtime_import_required",
            }:
                refuse("profile_selection_shape")
            if profile.get("status", "active") != "active":
                refuse("profile_selection_inactive")
            if "runtime_import_mode" in profile:
                text(profile["runtime_import_mode"])
            if (
                "runtime_import_required" in profile
                and type(profile["runtime_import_required"]) is not bool
            ):
                refuse("profile_import_hint_shape")
            key = text(profile.get("profile_key"))
            # Existing Workspace selector grammar; target profile parsing stays Code-owned.
            if (
                re.fullmatch(r"[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*", key, re.ASCII)
                is None
            ):
                refuse("profile_key_noncanonical")
            ref = text(profile.get("profile_package_ref"))
            if ref != f"workspace://{target}#{key}" or ref in refs:
                refuse("profile_selection_correspondence")
            refs.add(ref)
            providers = profile.get("semantic_contract_provider_keys")
            if type(providers) is not list or not providers or len(providers) > 256:
                refuse("profile_provider_restriction_unavailable")
            if any(type(k) is not str for k in providers) or len(set(providers)) != len(
                providers
            ):
                refuse("profile_provider_restriction_duplicate")
            keys = tuple(sorted((text(k) for k in providers), key=lambda k: k.encode()))
            result.append(
                DependencyScopeEdge(
                    path,
                    targets[target],
                    DependencyScopeDeclaration(
                        path, ContentDigest.of_wire(digest), index, profile_index
                    ),
                    identifier,
                    "workspace",
                    source,
                    DependencyScopeRestriction("present", "local"),
                    DependencyScopeRestriction("present", "workspace-revision:local"),
                    ref,
                    DependencyScopeRestriction("present", key),
                    DependencyScopeRestriction("present", keys),
                )
            )
            if len(result) > MAX_EDGES:
                refuse("profile_selection_bound")
    return tuple(result)
