from __future__ import annotations

import hashlib
import json
import tomllib
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Literal, cast

from aware_code_module_manifest_contract_runtime import (
    AwareModuleTomlError,
    parse_module_manifest,
)

from .workspace_profile_declarations import (
    WorkspaceProfileDeclarationError,
    local_profile_paths,
)

WORKSPACE_COMPOSITION_CONTRACT_REF = "aware.workspace.composition.v1"

_LOCAL_PROVIDER_KIND = "local_checkout_manifest"
_MAXIMUM_MANIFEST_BYTES = 1024 * 1024
_MAXIMUM_WORKSPACES = 100
_MAXIMUM_MODULES = 500
_MAXIMUM_PACKAGES = 2500


class WorkspaceCompositionFailure(Exception):
    def __init__(self, code: str, message: str, recovery: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.recovery = recovery


class LocalCheckoutWorkspaceCompositionProvider:
    """Workspace-owned observation of authored composition without revision claims."""

    def describe(self, root_path: str | Path) -> dict[str, object]:
        root = Path(root_path).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise _failure(
                "workspace_composition_root_invalid",
                "The granted composition root is not a directory.",
                "Choose an authored Aware repository or Workspace directory.",
            )
        self._root = root
        self._manifest_digests: dict[str, str] = {}
        if (root / "aware.repo.toml").is_file():
            root_kind: Literal["repository", "workspace"] = "repository"
            repository = self._repository()
        elif (root / "aware.workspace.toml").is_file():
            root_kind = "workspace"
            repository = self._standalone_workspace()
        else:
            raise _failure(
                "workspace_composition_manifest_required",
                "The granted directory has no aware.repo.toml or aware.workspace.toml.",
                "Choose an authored Aware repository or Workspace directory.",
            )
        return self._result(root_kind, repository)

    def _result(
        self, root_kind: str, repository: dict[str, object]
    ) -> dict[str, object]:
        digest_payload = json.dumps(
            sorted(self._manifest_digests.items()), separators=(",", ":")
        ).encode("utf-8")
        return {
            "contract_ref": WORKSPACE_COMPOSITION_CONTRACT_REF,
            "provider_kind": _LOCAL_PROVIDER_KIND,
            "resolution_state": "authored_declaration",
            "observation_digest": (
                f"sha256:{hashlib.sha256(digest_payload).hexdigest()}"
            ),
            "authority_ref": None,
            "root_kind": root_kind,
            "repository": repository,
        }

    def declaration_body_paths(self, description: dict[str, object]) -> tuple[str, ...]:
        """Return the complete structural body set selected by this interpreter."""
        paths = set(self._manifest_digests)
        repository = cast(dict[str, object], description["repository"])
        for workspace in cast(list[dict[str, object]], repository["workspaces"]):
            for module in cast(list[dict[str, object]], workspace["modules"]):
                for package in cast(list[dict[str, object]], module["packages"]):
                    paths.add(cast(str, package["manifest_path"]))
        return tuple(sorted(paths, key=str.encode))

    def python_package_memberships(
        self, description: dict[str, object]
    ) -> tuple[dict[str, str], ...]:
        """Project declared Python leaves from the existing composition traversal.

        Direct repo/workspace ``codes`` and module package slots are alternative
        declarations of the same physical leaf, never directory discovery.
        This descriptive entrance does not issue semantic execution authority.
        """
        repository = cast(dict[str, object], description["repository"])
        rows: list[dict[str, str]] = []

        def codes(table: Mapping[str, object], root: str, origin: str) -> None:
            values = table.get("codes", [])
            if type(values) is not list or any(type(v) is not str for v in values):
                raise _shape_failure("codes must be an array of manifest paths")
            if len(values) != len(set(values)):
                raise _duplicate("direct code manifest", origin)
            for value in values:
                path = _join_relative(root, _relative_path(value, "codes"))
                if PurePosixPath(path).name == "pyproject.toml":
                    rows.append({"manifest_path": path, "declaration_path": origin})

        if description["root_kind"] == "repository":
            raw = self._manifest("aware.repo.toml")
            if type(raw.get("aware_repo")) is not int or raw["aware_repo"] != 1:
                raise _shape_failure("repository requires schema version 1")
            codes(_mapping(raw["repo"], "repo"), ".", "aware.repo.toml")
        for workspace in cast(list[dict[str, object]], repository["workspaces"]):
            handle = cast(str, workspace["workspace_handle"])
            membership = workspace["repository_membership_handle"]
            if membership is not None and membership != handle:
                raise _shape_failure("repository/Workspace handle mismatch")
            origin = cast(str, workspace["manifest_path"])
            raw = self._manifest(origin)
            if type(raw.get("aware")) is not int or raw["aware"] not in (1, 2):
                raise _shape_failure("Workspace requires schema version 1 or 2")
            codes(
                _mapping(raw["workspace"], "workspace"),
                cast(str, workspace["relative_path"]), origin,
            )
            for module in cast(list[dict[str, object]], workspace["modules"]):
                for package in cast(list[dict[str, object]], module["packages"]):
                    path = cast(str, package["manifest_path"])
                    if PurePosixPath(path).name == "pyproject.toml":
                        rows.append({
                            "manifest_path": path,
                            "declaration_path": cast(str, module["manifest_path"]),
                            "workspace": handle,
                            "module": cast(str, module["module_id"]),
                            "package": cast(str, package["package_id"]),
                            "kind": cast(str, package["package_kind"]),
                        })
        if len(rows) > _MAXIMUM_PACKAGES:
            raise _budget_failure("Python package membership")
        return tuple(sorted(rows, key=lambda row: (row["manifest_path"], row["declaration_path"])))

    def _repository(self) -> dict[str, object]:
        payload = self._manifest("aware.repo.toml")
        repository = _mapping(payload.get("repo"), "repo")
        handle = _text(repository.get("handle"), "repo.handle")
        title = _optional_text(repository.get("title")) or handle
        workspaces_dir = _relative_path(
            _optional_text(repository.get("workspaces_dir")) or ".",
            "repo.workspaces_dir",
        )
        declarations = _mapping_list(payload.get("workspaces"), "workspaces")
        if not declarations:
            raise _failure(
                "workspace_composition_empty",
                "The repository declares no Workspace memberships.",
                "Declare at least one [[workspaces]] entry in aware.repo.toml.",
            )
        if len(declarations) > _MAXIMUM_WORKSPACES:
            raise _budget_failure("Workspace membership")
        seen: set[str] = set()
        workspaces: list[dict[str, object]] = []
        for declaration in declarations:
            membership_handle = _text(declaration.get("handle"), "workspaces.handle")
            if membership_handle in seen:
                raise _duplicate("repository Workspace membership", membership_handle)
            seen.add(membership_handle)
            declared_path = _relative_path(
                _text(declaration.get("path"), "workspaces.path"),
                "workspaces.path",
            )
            workspaces.append(
                self._workspace(
                    _join_relative(workspaces_dir, declared_path),
                    repository_membership_handle=membership_handle,
                )
            )
        return {
            "repository_ref": f"repository:{handle}",
            "repository_handle": handle,
            "title": title,
            "manifest_path": "aware.repo.toml",
            "workspaces": workspaces,
        }

    def _standalone_workspace(self) -> dict[str, object]:
        workspace = self._workspace(".", repository_membership_handle=None)
        handle = cast(str, workspace["workspace_handle"])
        return {
            "repository_ref": f"standalone-workspace:{handle}",
            "repository_handle": handle,
            "title": workspace["title"],
            "manifest_path": "aware.workspace.toml",
            "workspaces": [workspace],
        }

    def _workspace(
        self,
        relative_path: str,
        *,
        repository_membership_handle: str | None,
    ) -> dict[str, object]:
        manifest_path = _join_relative(relative_path, "aware.workspace.toml")
        payload = self._manifest(manifest_path)
        workspace = _mapping(payload.get("workspace"), "workspace")
        handle = _text(workspace.get("handle"), "workspace.handle")
        try:
            local_profiles = local_profile_paths(payload, workspace_handle=handle)
        except WorkspaceProfileDeclarationError as error:
            raise _shape_failure(str(error)) from error
        for _, profile_path in local_profiles:
            self._manifest_bytes(_join_relative(relative_path, profile_path))
        title = _optional_text(workspace.get("title")) or handle
        declarations = _mapping_list(
            workspace.get("modules"), "workspace.modules", optional=True
        )
        if len(declarations) > _MAXIMUM_MODULES:
            raise _budget_failure("Module declaration")
        seen: set[str] = set()
        modules: list[dict[str, object]] = []
        for declaration in declarations:
            module_id = _text(declaration.get("id"), "workspace.modules.id")
            if module_id in seen:
                raise _duplicate(f"Workspace {handle} module", module_id)
            seen.add(module_id)
            module_path = _join_relative(
                relative_path,
                _relative_path(
                    _text(declaration.get("path"), "workspace.modules.path"),
                    "workspace.modules.path",
                ),
            )
            modules.append(self._module(module_path, module_id=module_id))
        return {
            "workspace_ref": f"workspace:{handle}:{manifest_path}",
            "repository_membership_handle": repository_membership_handle,
            "workspace_handle": handle,
            "title": title,
            "relative_path": relative_path,
            "manifest_path": manifest_path,
            "modules": modules,
        }

    def _module(self, relative_path: str, *, module_id: str) -> dict[str, object]:
        manifest_path = _join_relative(relative_path, "aware.module.toml")
        content = self._manifest_bytes(manifest_path)
        try:
            module = parse_module_manifest(content, source_label=manifest_path)
        except AwareModuleTomlError as error:
            raise _failure(
                "workspace_composition_manifest_invalid",
                f"Authored module is invalid: {manifest_path} ({error}).",
                "Correct the Code module declaration and refresh the repository.",
            ) from error
        # Code preserves v1 grammar quirks; Workspace admission requires an
        # exact integer for each supported module version, including live views.
        if type(module.aware) is not int or module.aware not in (1, 2, 3):
            raise _shape_failure(
                "module declaration requires exact integer schema version 1, 2 or 3"
            )
        declarations = module.packages
        if len(declarations) > _MAXIMUM_PACKAGES:
            raise _budget_failure("Semantic package declaration")
        packages: list[dict[str, object]] = []
        for declaration in declarations:
            package_id = declaration.id
            package_kind = declaration.kind
            declared_manifest = _relative_path(
                declaration.manifest, "packages.manifest"
            )
            package_manifest = _join_relative(relative_path, declared_manifest)
            self._require_file(package_manifest)
            packages.append(
                {
                    "package_ref": (
                        f"semantic-package:{module_id}:{package_id}:{package_manifest}"
                    ),
                    "package_id": package_id,
                    "package_kind": package_kind,
                    "package_root": str(PurePosixPath(package_manifest).parent),
                    "manifest_path": package_manifest,
                    "visibility": declaration.visibility,
                    "provider_key": None,
                    "capabilities": [],
                }
            )
        return {
            "module_ref": f"module:{module_id}:{manifest_path}",
            "module_id": module_id,
            "relative_path": relative_path,
            "manifest_path": manifest_path,
            "packages": packages,
        }

    def _manifest(self, relative_path: str) -> Mapping[str, object]:
        return self._parse_manifest(relative_path, self._manifest_bytes(relative_path))

    def _manifest_bytes(self, relative_path: str) -> bytes:
        return self._record_manifest_bytes(
            relative_path, self._require_file(relative_path).read_bytes()
        )

    def _record_manifest_bytes(self, relative_path: str, content: bytes) -> bytes:
        if len(content) > _MAXIMUM_MANIFEST_BYTES:
            raise _failure(
                "workspace_composition_manifest_too_large",
                f"Authored manifest exceeds the bounded size: {relative_path}.",
                "Reduce the manifest below 1 MiB before opening it.",
            )
        self._manifest_digests[relative_path] = hashlib.sha256(content).hexdigest()
        return content

    def _parse_manifest(
        self, relative_path: str, content: bytes
    ) -> Mapping[str, object]:
        try:
            return tomllib.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
            raise _failure(
                "workspace_composition_manifest_invalid",
                f"Authored manifest is invalid: {relative_path} ({error}).",
                "Correct the authored TOML and refresh the repository.",
            ) from error

    def _require_file(self, relative_path: str) -> Path:
        normalized = _relative_path(relative_path, "manifest path")
        unresolved = self._root / normalized
        if unresolved.is_symlink() or not unresolved.is_file():
            raise _failure(
                "workspace_composition_manifest_missing",
                f"Declared manifest is missing: {relative_path}.",
                "Restore the declared manifest or correct its authored path.",
            )
        resolved = unresolved.resolve(strict=True)
        if resolved != self._root and self._root not in resolved.parents:
            raise _failure(
                "workspace_composition_path_escape",
                "Declared manifest resolves outside the granted root: "
                f"{relative_path}.",
                "Remove the escaping link or choose the containing repository.",
            )
        return resolved


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise _shape_failure(f"{label} must be a TOML table")
    return cast(Mapping[str, object], value)


def _mapping_list(
    value: object, label: str, *, optional: bool = False
) -> tuple[Mapping[str, object], ...]:
    if value is None and optional:
        return ()
    if not isinstance(value, list):
        raise _shape_failure(f"{label} must be an array of tables")
    return tuple(_mapping(item, label) for item in value)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _shape_failure(f"{label} must be non-empty text")
    return value.strip()


def _optional_text(value: object) -> str | None:
    return None if value is None else _text(value, "optional value")


def _relative_path(value: str, label: str) -> str:
    normalized = str(PurePosixPath(value.replace("\\", "/")))
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise _failure(
            "workspace_composition_path_escape",
            f"{label} must remain under the granted root: {value}.",
            "Use a confined root-relative path.",
        )
    return normalized


def _join_relative(left: str, right: str) -> str:
    result = str(PurePosixPath(left) / PurePosixPath(right))
    return "." if result == "." else _relative_path(result, "declared path")


def _shape_failure(detail: str) -> WorkspaceCompositionFailure:
    return _failure(
        "workspace_composition_manifest_shape_invalid",
        f"Authored composition is incomplete: {detail}.",
        "Correct the named declaration and refresh the repository.",
    )


def _duplicate(kind: str, identifier: str) -> WorkspaceCompositionFailure:
    return _failure(
        "workspace_composition_duplicate",
        f"Duplicate {kind} identity: {identifier}.",
        "Give each declaration a unique identity in its containing manifest.",
    )


def _budget_failure(kind: str) -> WorkspaceCompositionFailure:
    return _failure(
        "workspace_composition_budget_exceeded",
        f"{kind} count exceeds the local observation budget.",
        "Open a smaller repository or use the Workspace Service provider.",
    )


def _failure(code: str, message: str, recovery: str) -> WorkspaceCompositionFailure:
    return WorkspaceCompositionFailure(code, message, recovery)


class RetainedWorkspaceCompositionProvider(LocalCheckoutWorkspaceCompositionProvider):
    """Reuse owner declaration rules over exact nominal retained reads only.

    The result remains descriptive. Observed membership is issued separately
    after this interpreter and the observation runtime both validate inputs.
    """

    def describe_retained(
        self, *, observation_runtime, observation
    ) -> dict[str, object]:
        from .source_observation import WorkspaceSourceObservationRuntime

        if type(observation_runtime) is not WorkspaceSourceObservationRuntime:
            raise TypeError("exact Workspace observation runtime required")
        self._read_retained = lambda path: observation_runtime.read(
            observation, relative_path=path
        )
        self._retained_paths = frozenset(
            body.relative_path
            for body in observation_runtime.evidence(observation).bodies
        )
        return self._describe_selected_bodies()

    def describe_captured_bodies(
        self, bodies: tuple[tuple[str, bytes], ...]
    ) -> dict[str, object]:
        """Interpret exact captured declaration bytes before nominal issuance."""
        if type(bodies) is not tuple or not bodies:
            raise _shape_failure("captured declaration bodies required")
        by_path = dict(bodies)
        if len(by_path) != len(bodies):
            raise _shape_failure("captured declaration paths duplicate")
        self._read_retained = by_path.__getitem__
        self._retained_paths = frozenset(by_path)
        return self._describe_selected_bodies()

    def _describe_selected_bodies(self) -> dict[str, object]:
        self._manifest_digests = {}
        if "aware.repo.toml" in self._retained_paths:
            return self._result("repository", self._repository())
        if "aware.workspace.toml" in self._retained_paths:
            return self._result("workspace", self._standalone_workspace())
        raise _shape_failure("retained repository/workspace declaration required")

    def qualified_repository_membership(self) -> dict[str, str]:
        """Descriptive original-field mapping; caller must retain/revalidate source."""
        from .dependency_scope_declarations import canonical_handle, refuse

        raw = self._manifest("aware.repo.toml")
        declared = _mapping_list(raw.get("workspaces"), "workspaces")
        described = _mapping_list(self._repository()["workspaces"], "workspaces")
        result: dict[str, str] = {}
        paths: set[str] = set()
        for declaration, workspace in zip(declared, described, strict=True):
            handle = canonical_handle(declaration.get("handle"))
            path = _text(workspace["manifest_path"], "manifest_path")
            target = _mapping(self._manifest(path).get("workspace"), "workspace")
            if canonical_handle(target.get("handle")) != handle:
                refuse("dependency_workspace_handle_mismatch")
            if handle in result or path in paths:
                refuse("dependency_workspace_alias")
            result[handle] = path
            paths.add(path)
        return result

    def qualified_dependency_selections(self, path, *, targets):
        from .dependency_scope_declarations import selections

        workspace = _mapping(self._manifest(path).get("workspace"), "workspace")
        return selections(
            workspace, path=path, digest="sha256:" + self._manifest_digests[path], targets=targets
        )

    def _manifest(self, relative_path: str) -> Mapping[str, object]:
        value = self._parse_manifest(relative_path, self._manifest_bytes(relative_path))
        if relative_path == "aware.repo.toml":
            if type(value.get("aware_repo")) is not int or value["aware_repo"] != 1:
                raise _shape_failure("retained repository requires exact schema version 1")
        elif (
            type(value.get("aware")) is not int
            or value["aware"] not in (1, 2)
        ):
            raise _shape_failure("retained Workspace requires schema version 1 or 2")
        return value

    def _manifest_bytes(self, relative_path: str) -> bytes:
        self._require_file(relative_path)
        return self._record_manifest_bytes(
            relative_path,
            self._read_retained(relative_path),
        )

    def _require_file(self, relative_path: str) -> Path:
        from .source_observation_io import validate_relative_path

        validate_relative_path(relative_path)
        if relative_path not in self._retained_paths:
            raise _shape_failure(f"declared manifest not retained: {relative_path}")
        # The shared interpreter needs only existence. This lexical Path is never
        # opened: _manifest above delegates exclusively to the nominal reader.
        return Path(relative_path)
