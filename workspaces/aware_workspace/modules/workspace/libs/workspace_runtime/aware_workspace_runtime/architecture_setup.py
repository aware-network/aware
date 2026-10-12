"""Aware manifest creation and bounded authored-Python package alignment."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import overload

from aware_code_module_manifest_contract_runtime import parse_module_manifest
from aware_code_module_manifest_contract_runtime.python_package_setup import (
    PythonCodePackageSetup,
    render_python_code_package,
)
from aware_workspace_sdk.architecture_setup import (
    ArchitectureSetupChange,
    ArchitectureSetupError,
    ArchitectureSetupPreview,
    ArchitectureSetupRequest,
)
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name

from .package_manager_toml import (
    _merge_uv_workspace,
    _merge_uv_workspace_sources,
    _minimal_package_manager_pyproject_content,
    _toml_key_range,
    _toml_table_range,
    _WorkspacePackageManagerSourceSpec,
)


@overload
def digest(body: bytes) -> str: ...


@overload
def digest(body: None) -> None: ...


def digest(body: bytes | None) -> str | None:
    return None if body is None else "sha256:" + hashlib.sha256(body).hexdigest()


def relative(path):
    if (
        type(path) is not str
        or not path
        or "\\" in path
        or any(c in path for c in "*?[]\x00\n\r")
        or PurePosixPath(path).is_absolute()
        or any(part in ("", ".", "..") for part in path.split("/"))
    ):
        raise ArchitectureSetupError("invalid_relative_path")
    return path


def name(value, *, package=False):
    pattern = r"[a-z_][a-z0-9_]*" if package else r"[a-z][a-z0-9_-]*"
    if type(value) is not str or len(value) > 128 or not re.fullmatch(pattern, value):
        raise ArchitectureSetupError("invalid_architecture_name")
    return value


def table(body):
    if body is None:
        raise ArchitectureSetupError("manifest_missing")
    try:
        return tomllib.loads(body.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ArchitectureSetupError("manifest_invalid") from error


def _overlaps(left, right):
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def _code_manifests(owner, child_roots):
    """Exact support registrations, separate from registered child ownership."""
    rows = owner.get("codes", [])
    if type(rows) is not list:
        raise ArchitectureSetupError("invalid_code_registrations")
    roots = []
    for path in rows:
        relative(path)
        if not path.endswith("/pyproject.toml"):
            raise ArchitectureSetupError("support_profile_requires_python_manifest")
        root = str(PurePosixPath(path).parent)
        if any(_overlaps(root, child) for child in child_roots):
            raise ArchitectureSetupError("support_package_crosses_child_ownership")
        if any(_overlaps(root, old) for old in roots):
            raise ArchitectureSetupError("duplicate_or_overlapping_code_registration")
        roots.append(root)
    return rows


@dataclass
class _Plan:
    request: ArchitectureSetupRequest
    inputs: dict[str, bytes | None]
    outputs: dict[str, bytes]
    preview: ArchitectureSetupPreview


class ArchitectureSetupRuntime:
    def __init__(self, physical):
        if type(physical) not in _PHYSICAL_TYPES:
            raise TypeError("original_setup_physical_owner_required")
        self.physical = physical
        self.pid = os.getpid()
        self.closed = False

    def close(self):
        self.closed = True
        self.physical.close()

    def _current(self):
        if self.closed or self.pid != os.getpid():
            raise ArchitectureSetupError("setup_client_not_current")
        self.physical.current()

    def _read(self, path, inputs):
        path = relative(path)
        body = self.physical.read(path)
        if path in inputs and inputs[path] != body:
            raise ArchitectureSetupError("setup_input_drift")
        inputs[path] = body
        return body

    def _required(self, path, inputs):
        body = self._read(path, inputs)
        if body is None:
            raise ArchitectureSetupError("manifest_missing:" + path)
        return body

    def _repo(self, inputs):
        body = self._required("aware.repo.toml", inputs)
        data = table(body)
        if data.get("aware_repo") != 1 or type(data.get("repo")) is not dict:
            raise ArchitectureSetupError("unsupported_repository_manifest")
        name(data["repo"].get("handle"))
        relative(data["repo"].get("workspaces_dir"))
        self._registrations(data.get("workspaces", []), "handle")
        _code_manifests(data["repo"], self._workspace_roots(data))
        return data

    def _workspace_roots(self, repo):
        return [
            relative(repo["repo"]["workspaces_dir"] + "/" + row["path"])
            for row in repo.get("workspaces", [])
        ]

    def _registrations(self, rows, key):
        if type(rows) is not list:
            raise ArchitectureSetupError("invalid_registrations")
        names, paths = set(), []
        for row in rows:
            if type(row) is not dict:
                raise ArchitectureSetupError("invalid_registration")
            label, path = name(row.get(key)), relative(row.get("path"))
            if label in names or any(
                path == old or path.startswith(old + "/") or old.startswith(path + "/")
                for old in paths
            ):
                raise ArchitectureSetupError("duplicate_or_overlapping_registration")
            names.add(label)
            paths.append(path)

    def _workspace(self, label, inputs):
        name(label)
        repo = self._repo(inputs)
        rows = [row for row in repo.get("workspaces", []) if row["handle"] == label]
        if len(rows) != 1:
            raise ArchitectureSetupError("workspace_not_registered")
        path = relative(repo["repo"]["workspaces_dir"] + "/" + rows[0]["path"])
        body = self._required(path + "/aware.workspace.toml", inputs)
        data = table(body)
        if data.get("aware") != 2 or type(data.get("workspace")) is not dict:
            raise ArchitectureSetupError("setup_requires_workspace_v2")
        if data["workspace"].get("handle") != label:
            raise ArchitectureSetupError("workspace_identity_mismatch")
        self._registrations(data["workspace"].get("modules", []), "id")
        _code_manifests(
            data["workspace"],
            [row["path"] for row in data["workspace"].get("modules", [])],
        )
        return path, data, body

    def _module(self, workspace, label, inputs):
        name(label)
        wp, data, _ = self._workspace(workspace, inputs)
        rows = [
            row for row in data["workspace"].get("modules", []) if row["id"] == label
        ]
        if len(rows) != 1:
            raise ArchitectureSetupError("module_not_registered")
        path = relative(wp + "/" + rows[0]["path"])
        body = self._required(path + "/aware.module.toml", inputs)
        parsed = parse_module_manifest(body)
        if parsed.aware != 1:
            raise ArchitectureSetupError("authored_setup_requires_module_v1")
        return path, parsed, body

    def repository(self):
        self._current()
        return self._repo({})

    def workspace(self, label):
        self._current()
        return self._workspace(label, {})[0]

    def module(self, workspace, label):
        self._current()
        return self._module(workspace, label, {})[0]

    def _plan(self, request):
        self._current()
        if type(request) is not ArchitectureSetupRequest:
            raise TypeError("original_setup_request_required")
        if request.operation not in (
            "repository",
            "workspace",
            "module",
            "python_package",
            "package_manager",
        ):
            raise ArchitectureSetupError("unsupported_setup_operation")
        inputs, outputs = {}, {}
        q = json.dumps

        def create(path, body):
            prior = self._read(path, inputs)
            if prior is not None:
                raise ArchitectureSetupError("creation_target_already_exists:" + path)
            outputs[path] = body

        if request.operation == "repository":
            name(request.name)
            if (
                type(request.license_expression) is not str
                or not request.license_expression.strip()
            ):
                raise ArchitectureSetupError("explicit_license_expression_required")
            prior = self._read("aware.repo.toml", inputs)
            if prior is not None:
                repo = self._repo(inputs)
                if (
                    repo["repo"]["handle"] != request.name
                    or repo.get("licensing", {}).get("default_spdx_expression")
                    != request.license_expression
                ):
                    raise ArchitectureSetupError("existing_repository_conflicts")
            else:
                policies = {
                    "license_path": "LICENSE",
                    "notice_path": "NOTICE",
                    "third_party_notices_path": "THIRD_PARTY_NOTICES.md",
                    "generated_output_policy_path": "docs/legal/GENERATED_OUTPUT_POLICY.md",
                    "artifact_provenance_path": "docs/legal/ARTIFACT_PROVENANCE.toml",
                    "contribution_policy_path": "CONTRIBUTING.md",
                    "security_policy_path": "SECURITY.md",
                }
                text = "aware_repo = 1\nworkspaces = []\n\n[repo]\n"
                text += f'handle = {q(request.name)}\nworkspaces_dir = "workspaces"\ncodes = []\n\n[licensing]\n'
                text += f"default_spdx_expression = {q(request.license_expression)}\n"
                text += "".join(
                    f"{key} = {q(path)}\n" for key, path in policies.items()
                )
                for key, path in policies.items():
                    text += f"\n[[repository_files]]\nrole = {q(key.removesuffix('_path'))}\nsource_path = {q(path)}\ntarget_path = {q(path)}\n"
                outputs["aware.repo.toml"] = text.encode()
        elif request.operation == "workspace":
            name(request.name)
            path = relative(request.path)
            repo = self._repo(inputs)
            rows = repo.get("workspaces", [])
            prior = [row for row in rows if row["handle"] == request.name]
            if prior:
                if prior[0]["path"] != path:
                    raise ArchitectureSetupError("existing_workspace_conflicts")
                self._workspace(request.name, inputs)
            else:
                self._registrations(
                    [*rows, {"handle": request.name, "path": path}], "handle"
                )
                _code_manifests(
                    repo["repo"],
                    [
                        *self._workspace_roots(repo),
                        repo["repo"]["workspaces_dir"] + "/" + path,
                    ],
                )
                target = (
                    repo["repo"]["workspaces_dir"]
                    + "/"
                    + path
                    + "/aware.workspace.toml"
                )
                create(
                    target,
                    f"aware = 2\n\n[workspace]\nhandle = {q(request.name)}\nmodules = []\ncodes = []\n".encode(),
                )
                # Initial empty arrays must be removed before appending TOML array tables.
                text = inputs["aware.repo.toml"].decode()
                if not rows:
                    text = _remove_empty_array(text, "workspaces")
                outputs["aware.repo.toml"] = (
                    text.rstrip()
                    + f"\n\n[[workspaces]]\nhandle = {q(request.name)}\npath = {q(path)}\n"
                ).encode()
        elif request.operation == "module":
            name(request.name)
            path = relative(request.path)
            wp, data, body = self._workspace(request.workspace, inputs)
            rows = data["workspace"].get("modules", [])
            prior = [row for row in rows if row["id"] == request.name]
            if prior:
                if prior[0]["path"] != path:
                    raise ArchitectureSetupError("existing_module_conflicts")
                self._module(request.workspace, request.name, inputs)
            else:
                self._registrations([*rows, {"id": request.name, "path": path}], "id")
                _code_manifests(
                    data["workspace"], [row["path"] for row in rows] + [path]
                )
                create(
                    wp + "/" + path + "/aware.module.toml",
                    b"aware = 1\npackages = []\n",
                )
                text = body.decode()
                if not rows:
                    text = _remove_empty_array(text, "modules", section="workspace")
                outputs[wp + "/aware.workspace.toml"] = (
                    text.rstrip()
                    + f"\n\n[[workspace.modules]]\nid = {q(request.name)}\npath = {q(path)}\n"
                ).encode()
        elif request.operation == "python_package":
            name(request.name, package=True)
            path = relative(request.path)
            if not path.startswith(("libs/", "sdks/", "apps/", "services/", "apis/")):
                raise ArchitectureSetupError(
                    "package_requires_explicit_module_surface"
                    if request.owner == "module"
                    else "package_requires_explicit_owner_surface"
                )
            if (
                type(request.dependencies) is not tuple
                or len(request.dependencies) > 256
            ):
                raise ArchitectureSetupError("invalid_package_dependencies")
            for requirement in request.dependencies:
                Requirement(requirement)
            SpecifierSet(request.requires_python)
            spec = PythonCodePackageSetup(
                request.distribution,
                request.import_root,
                request.version,
                request.requires_python,
                request.dependencies,
            )
            owner_root, owner_manifest, body, registrations = self._package_owner(
                request, inputs
            )
            prefix = owner_root + "/" if owner_root else ""
            manifest = path + "/pyproject.toml"
            section = "repo" if request.owner == "repository" else "workspace"
            target = prefix + manifest
            catalog, _ = self._catalog(inputs)
            existing = catalog.get(canonicalize_name(request.distribution))
            if existing is not None and existing[0] != target:
                raise ArchitectureSetupError("duplicate_distribution_or_manifest")
            prior = [
                row
                for row in registrations
                if row[0] == (request.name if request.owner == "module" else manifest)
            ]
            if prior:
                if prior[0][1] != "code" or prior[0][2] != manifest:
                    raise ArchitectureSetupError("existing_package_conflicts")
                project = table(self._required(target, inputs)).get("project")
                expected = table(render_python_code_package(spec)[0][1])["project"]
                if project != expected:
                    raise ArchitectureSetupError(
                        "existing_package_configuration_differs"
                    )
                self._required(
                    prefix + path + f"/src/{request.import_root}/__init__.py", inputs
                )
            else:
                for _, _, registered in registrations:
                    other = PurePosixPath(relative(registered)).parent.as_posix()
                    if _overlaps(path, other):
                        raise ArchitectureSetupError("package_path_overlaps")
                if request.owner != "module":
                    owner_data = table(body)
                    child_roots = (
                        self._workspace_roots(owner_data)
                        if section == "repo"
                        else [
                            row["path"]
                            for row in owner_data[section].get("modules", [])
                        ]
                    )
                    _code_manifests(
                        {"codes": [row[2] for row in registrations] + [manifest]},
                        child_roots,
                    )
                for filename, data in render_python_code_package(spec):
                    create(prefix + path + "/" + filename, data)
                if request.owner == "module":
                    text = body.decode()
                    if not registrations:
                        text = _remove_empty_array(text, "packages")
                    outputs[owner_manifest] = (
                        text.rstrip()
                        + f'\n\n[[packages]]\nid = {q(request.name)}\nkind = "code"\nmanifest = {q(manifest)}\nvisibility = "module"\n'
                    ).encode()
                    parse_module_manifest(outputs[owner_manifest])
                else:
                    outputs[owner_manifest] = _append_code_manifest(
                        body.decode(),
                        section,
                        [row[2] for row in registrations] + [manifest],
                    ).encode()
        else:
            if request.module or request.path:
                raise ArchitectureSetupError("resolution_context_selection_conflicts")
            outputs.update(self._package_manager(inputs, workspace=request.workspace))

        outputs = {
            path: body for path, body in outputs.items() if inputs.get(path) != body
        }
        for path, body in outputs.items():
            if path.endswith(".toml"):
                table(body)
        identity = {
            "profile": "aware.workspace.architecture-setup.v1",
            "root": str(self.physical.root),
            "request": {
                field: getattr(request, field) for field in request.__dataclass_fields__
            },
            "inputs": {path: digest(body) for path, body in sorted(inputs.items())},
            "outputs": {path: digest(body) for path, body in sorted(outputs.items())},
        }
        preview = ArchitectureSetupPreview(
            request.operation,
            digest(json.dumps(identity, sort_keys=True).encode()),
            tuple(
                ArchitectureSetupChange(path, digest(inputs.get(path)), digest(body))
                for path, body in sorted(outputs.items())
            ),
            tuple(sorted(inputs)),
        )
        return _Plan(request, inputs, outputs, preview)

    def preview(self, request):
        return self._plan(request).preview

    def _package_owner(self, request, inputs):
        """Resolve original owner coordinates; rendering stays with Code's profile."""
        if request.owner == "repository":
            if request.workspace or request.module:
                raise ArchitectureSetupError("package_owner_selection_conflicts")
            data = self._repo(inputs)
            return (
                "",
                "aware.repo.toml",
                inputs["aware.repo.toml"],
                [(path, "code", path) for path in data["repo"].get("codes", [])],
            )
        if request.owner == "workspace":
            if not request.workspace or request.module:
                raise ArchitectureSetupError("package_owner_selection_conflicts")
            root, data, body = self._workspace(request.workspace, inputs)
            return (
                root,
                root + "/aware.workspace.toml",
                body,
                [(path, "code", path) for path in data["workspace"].get("codes", [])],
            )
        if request.owner == "module":
            if not request.workspace or not request.module:
                raise ArchitectureSetupError("package_owner_selection_conflicts")
            root, data, body = self._module(request.workspace, request.module, inputs)
            return (
                root,
                root + "/aware.module.toml",
                body,
                [(row.id, row.kind, row.manifest) for row in data.packages],
            )
        raise ArchitectureSetupError("unsupported_package_owner")

    def apply(self, request, *, expected_plan_sha256=None):
        self._current()
        with self.physical.lease():
            plan = self._plan(request)
            if (
                expected_plan_sha256 is not None
                and expected_plan_sha256 != plan.preview.plan_sha256
            ):
                raise ArchitectureSetupError("setup_plan_changed")
            return self.physical.apply(plan)

    def _catalog(self, inputs):
        repo = self._repo(inputs)
        packages = {}
        paths = set()

        def add(path):
            path = relative(path)
            payload = table(self._required(path, inputs))
            project = payload.get("project", {})
            distribution = project.get("name")
            if type(distribution) is not str or not distribution:
                raise ArchitectureSetupError("static_python_project_name_required")
            key = canonicalize_name(distribution)
            if key in packages or path in paths:
                raise ArchitectureSetupError("duplicate_distribution_or_manifest")
            packages[key] = (path, payload)
            paths.add(path)

        for path in repo["repo"].get("codes", []):
            add(path)
        workspace_roots = []
        for ws in repo.get("workspaces", []):
            wp, data, _ = self._workspace(ws["handle"], inputs)
            workspace_roots.append(wp)
            for path in data["workspace"].get("codes", []):
                add(wp + "/" + relative(path))
            for row in data["workspace"].get("modules", []):
                mp, module, _ = self._module(ws["handle"], row["id"], inputs)
                for package in module.packages:
                    if package.kind != "code" or not package.manifest.endswith(
                        "/pyproject.toml"
                    ):
                        raise ArchitectureSetupError(
                            "package_manager_profile_requires_authored_python_code"
                        )
                    add(mp + "/" + relative(package.manifest))
        return packages, workspace_roots

    def _context_catalog(self, inputs, *, workspace=""):
        packages, roots = self._catalog(inputs)
        selected = self._workspace(workspace, inputs)[0] if workspace else ""
        boundaries = {"": self._read("pyproject.toml", inputs)}
        for root in roots:
            body = self._read(root + "/pyproject.toml", inputs)
            payload = table(body) if body is not None else {}
            uv = payload.get("tool", {}).get("uv", {})
            if root == selected or "workspace" in uv:
                boundaries[root] = body
            elif "project" in payload:
                raise ArchitectureSetupError(
                    "plain_workspace_project_requires_explicit_alignment"
                )
        contexts = {}
        for key, (path, payload) in packages.items():
            if "workspace" in payload.get("tool", {}).get("uv", {}):
                raise ArchitectureSetupError(
                    "leaf_uv_workspace_requires_separate_profile"
                )
            context = ""
            parent = PurePosixPath(path).parent
            while str(parent) != ".":
                cursor = str(parent)
                if self._read(cursor + "/uv.toml", inputs) is not None:
                    raise ArchitectureSetupError("uv_config_requires_separate_profile")
                if cursor in boundaries:
                    if not context:
                        context = cursor
                elif cursor + "/pyproject.toml" != path:
                    body = self._read(cursor + "/pyproject.toml", inputs)
                    if body is not None:
                        data = table(body)
                        if "project" in data or "workspace" in data.get("tool", {}).get(
                            "uv", {}
                        ):
                            raise ArchitectureSetupError(
                                "unregistered_resolution_boundary"
                            )
                parent = parent.parent
            contexts[key] = context
        if self._read("uv.toml", inputs) is not None:
            raise ArchitectureSetupError("uv_config_requires_separate_profile")
        for root, body in boundaries.items():
            if self._read(root + "/uv.toml" if root else "uv.toml", inputs) is not None:
                raise ArchitectureSetupError("uv_config_requires_separate_profile")
            uv = table(body).get("tool", {}).get("uv", {}) if body is not None else {}
            if uv.get("managed") is False:
                raise ArchitectureSetupError("unmanaged_uv_context")
            boundary = uv.get("workspace", {})
            if type(boundary) is not dict or boundary.get("exclude", []):
                raise ArchitectureSetupError(
                    "workspace_membership_policy_requires_review"
                )
            members = boundary.get("members", [])
            allowed = {
                os.path.relpath(str(PurePosixPath(path).parent), root or ".")
                for path, _ in packages.values()
                if not root or path.startswith(root + "/")
            }
            if type(members) is not list or any(
                type(member) is not str or member not in allowed for member in members
            ):
                raise ArchitectureSetupError(
                    "workspace_membership_policy_requires_review"
                )
        return packages, boundaries, contexts, selected

    def _package_manager(self, inputs, *, workspace=""):
        packages, boundaries, contexts, selected = self._context_catalog(
            inputs, workspace=workspace
        )
        root_path = selected + "/pyproject.toml" if selected else "pyproject.toml"
        root_body = boundaries[selected]
        members_packages = {
            key: row for key, row in packages.items() if contexts[key] == selected
        }
        members = tuple(
            sorted(
                os.path.relpath(str(PurePosixPath(path).parent), selected or ".")
                for path, _ in members_packages.values()
            )
        )

        def bindings(origin, context, keys):
            desired = {}
            for key in keys:
                desired[key] = (
                    {"workspace": True}
                    if contexts[key] == context
                    else {
                        "path": os.path.relpath(
                            str(PurePosixPath(packages[key][0]).parent), origin or "."
                        ),
                        "editable": True,
                    }
                )
            return desired

        desired_root = bindings(selected, selected, packages)
        if root_body is not None:
            _local_dependencies(table(root_body), packages)
        _check_source_policies(
            table(root_body) if root_body is not None else {}, packages, desired_root
        )
        sources = tuple(
            _WorkspacePackageManagerSourceSpec(key, desired_root[key])
            for key in sorted(desired_root)
        )
        root = (
            _merge_uv_workspace(
                existing_text=root_body.decode(),
                workspace_members=members,
                workspace_source_specs=sources,
            )
            if root_body is not None
            else _minimal_package_manager_pyproject_content(
                workspace_members=members,
                workspace_sources=(),
                workspace_source_specs=sources,
            )
        )
        outputs = {root_path: root.encode()}
        for path, payload in members_packages.values():
            keys = _local_dependencies(payload, packages)
            keys.update(
                canonicalize_name(key)
                for key in payload.get("tool", {}).get("uv", {}).get("sources", {})
                if canonicalize_name(key) in packages
            )
            desired = bindings(str(PurePosixPath(path).parent), selected, keys)
            _check_source_policies(payload, packages, desired)
            outputs[path] = _merge_uv_workspace_sources(
                existing_text=inputs[path].decode(),
                workspace_source_specs=tuple(
                    _WorkspacePackageManagerSourceSpec(key, desired[key])
                    for key in sorted(desired)
                ),
            ).encode()
        return outputs

    def locks(self, *, check, workspace=""):
        self._current()
        with self.physical.lease():
            request = ArchitectureSetupRequest("package_manager", workspace=workspace)
            plan = self._plan(request)
            if plan.outputs:
                raise ArchitectureSetupError("package_metadata_alignment_required")
            packages, boundaries, contexts, selected = self._context_catalog(
                plan.inputs, workspace=workspace
            )
            # Path dependencies still consume their original context's sources.
            needed = {key for key in packages if contexts[key] == selected}
            root_path = selected + "/pyproject.toml" if selected else "pyproject.toml"
            needed.update(_local_dependencies(table(plan.inputs[root_path]), packages))
            pending = list(needed)
            while pending:
                key = pending.pop()
                for text in _requirements(packages[key][1]):
                    target = canonicalize_name(Requirement(text).name)
                    if target in packages and target not in needed:
                        needed.add(target)
                        pending.append(target)
            repo = self._repo(plan.inputs)
            handles = {
                self._workspace(row["handle"], plan.inputs)[0]: row["handle"]
                for row in repo.get("workspaces", [])
            }
            for context in {contexts[key] for key in needed} - {selected}:
                outputs = self._package_manager(
                    plan.inputs, workspace=handles.get(context, "")
                )
                if any(plan.inputs.get(path) != body for path, body in outputs.items()):
                    raise ArchitectureSetupError(
                        "dependency_context_alignment_required"
                    )
            for key in needed:
                path = packages[key][0]
                leaf = str(PurePosixPath(path).parent / "uv.lock")
                if self._read(leaf, plan.inputs) is not None:
                    raise ArchitectureSetupError(
                        "shadowed_leaf_lock_requires_consumer_disposition"
                    )
            # Refuse redirected locks anywhere between an original member and its owner.
            for path in tuple(plan.inputs):
                if path.endswith("/pyproject.toml"):
                    parent = str(PurePosixPath(path).parent)
                    if parent not in boundaries:
                        lock = parent + "/uv.lock"
                        if self._read(lock, plan.inputs) is not None:
                            raise ArchitectureSetupError(
                                "shadowed_leaf_lock_requires_consumer_disposition"
                            )
            return (
                self.physical.run_uv(
                    check=check, resolution_root=selected, inputs=plan.inputs
                ),
            )


_PHYSICAL_TYPES = set()


def _append_code_manifest(text, section, paths):
    """Replace only the owning codes key, retaining other authored sections."""
    lines = text.splitlines(keepends=True)
    start, end = _toml_table_range(lines=lines, table_name=section)
    if start is None or end is None:
        raise ArchitectureSetupError("registration_section_missing")
    first, last = _toml_key_range(
        lines=lines, section_start=start, section_end=end, key="codes"
    )
    if first is None:
        first = last = end
    rendered = "codes = " + json.dumps(paths) + "\n"
    if first and not lines[first - 1].endswith("\n"):
        rendered = "\n" + rendered
    return "".join(lines[:first]) + rendered + "".join(lines[last:])


def _check_source_policies(payload, packages, desired):
    sources = payload.get("tool", {}).get("uv", {}).get("sources", {})
    for source, value in sources.items():
        name = canonicalize_name(source)
        if (
            type(value) is dict
            and value.get("workspace") is True
            and name not in packages
        ):
            raise ArchitectureSetupError("unregistered_workspace_dependency")
        if name in desired and value != desired[name]:
            raise ArchitectureSetupError("explicit_source_policy_requires_review")


def _requirements(payload):
    project = payload.get("project", {})
    requirements = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        requirements.extend(group)
    for group in payload.get("dependency-groups", {}).values():
        requirements.extend(item for item in group if type(item) is str)
    return requirements


def _local_dependencies(payload, packages):
    keys = set()
    for text in _requirements(payload):
        req = Requirement(text)
        target = canonicalize_name(req.name)
        if target in packages:
            version = packages[target][1]["project"].get("version")
            if (
                req.url is not None
                or version is None
                or not req.specifier.contains(version)
            ):
                raise ArchitectureSetupError("local_dependency_configuration_conflicts")
            keys.add(target)
    return keys


def _register_physical_type(physical_type):
    _PHYSICAL_TYPES.add(physical_type)


def _remove_empty_array(text, key, *, section=None):
    lines = text.splitlines(keepends=True)
    if section is None:
        start = -1
        end = next(
            (i for i, line in enumerate(lines) if line.strip().startswith("[")),
            len(lines),
        )
    else:
        start, end = _toml_table_range(lines=lines, table_name=section)
    if start is None or end is None:
        raise ArchitectureSetupError("registration_section_missing")
    first, last = _toml_key_range(
        lines=lines, section_start=start, section_end=end, key=key
    )
    if first is None:
        return text
    # The parsed owner already proved this is an empty array. Preserve every other section.
    return "".join(lines[:first] + lines[last:])
