"""Manifest-derived source checkout; no execution, installation or publication.

Membership uses Workspace composition and Code's module parser. Files are the
complete Git-tracked physical package roots, never a caller-authored file list.
Registry requirements remain requirements for the qualified packaging resolver.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import tomllib
import weakref
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any, Self, cast

from packaging.markers import default_environment
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

from .checkout_profiles import (
    checkout_repository_files,
    expand_checkout_profiles,
    parse_checkout_profiles,
)
from .composition import LocalCheckoutWorkspaceCompositionProvider
from .source_observation_io import (
    SourceObservationLimits,
    capture_exact_paths,
    validate_relative_path,
)

CONTRACT = "aware.workspace.package-source-checkout.v1"
PROFILE_CONTRACT = "aware.workspace.package-source-checkout.v2"
_LIMITS = SourceObservationLimits(
    maximum_files=16384, maximum_total_bytes=512 * 1024 * 1024
)
_MAX_PACKAGES = 2500


class PackageCheckoutError(ValueError):
    """No complete source checkout satisfying the request can be issued."""


def _wire(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def _sha(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


_GIT_RUN = subprocess.run
_TRACKED_STAT = os.stat


def _git(root: Path, *args: str, _retained: bool = False) -> bytes:
    result = (_GIT_RUN if _retained else subprocess.run)(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_LITERAL_PATHSPECS": "1"},
    )
    if result.returncode:
        raise PackageCheckoutError("Git source inventory unavailable")
    return result.stdout


def _requirement(value: str) -> Requirement:
    try:
        requirement = Requirement(value)
    except InvalidRequirement as error:
        raise PackageCheckoutError(f"invalid requirement: {value}") from error
    if requirement.url is not None:
        raise PackageCheckoutError(
            f"direct URL requires qualified artifact resolution: {value}"
        )
    return requirement


_COMPOSITION_READER_ENTRIES = tuple(
    (name, value)
    for name, value in vars(LocalCheckoutWorkspaceCompositionProvider).items()
    if callable(value)
)


def _retain_composition_readers(
    provider: LocalCheckoutWorkspaceCompositionProvider, guard: Callable[[], None]
) -> None:
    """Retain this same original interpreter's helpers; never clone its resolver."""
    reference = weakref.ref(provider)
    installed: dict[str, Any] = {}

    def invoke(original: Any, *args: Any, **kwargs: Any) -> Any:
        receiver = reference()
        try:
            guard()
            if (
                receiver is None
                or type(receiver) is not LocalCheckoutWorkspaceCompositionProvider
                or any(
                    vars(receiver).get(name) is not entrance
                    for name, entrance in installed.items()
                )
            ):
                raise PackageCheckoutError("composition reader substituted")
            result = original(receiver, *args, **kwargs)
            guard()
            return result
        finally:
            receiver = result = original = None
            args = ()
            kwargs.clear()

    def entrance(original: Any) -> Any:
        def dispatch(*args: Any, **kwargs: Any) -> Any:
            try:
                return invoke(original, *args, **kwargs)
            finally:
                args = ()
                kwargs.clear()

        return dispatch

    for name, original in _COMPOSITION_READER_ENTRIES:
        installed[name] = entrance(original)
        setattr(provider, name, installed[name])


_RETAINED_READER_GUARDS: weakref.WeakKeyDictionary[
    PackageSourceCheckout, Callable[[], None]
] = weakref.WeakKeyDictionary()


def _retain_reader_registry_ports(
    registry: weakref.WeakKeyDictionary[PackageSourceCheckout, Callable[[], None]],
) -> tuple[
    Callable[[PackageSourceCheckout, Callable[[], None]], None], Callable[..., None]
]:
    """Bind enrollment and checking to the same definition-time owner registry."""

    def _bind_retained_reader(
        reader: PackageSourceCheckout, guard: Callable[[], None]
    ) -> None:
        object.__setattr__(reader, "_reader_guard", guard)
        registry[reader] = guard

    def _check_retained_reader(
        reader: PackageSourceCheckout, _registry: Any = registry
    ) -> None:
        original = guard = None
        try:
            # Do not derive scan authority from the mutable module reference,
            # even when it and the callable default are substituted together.
            if _registry is not registry:
                raise PackageCheckoutError("retained read registry substituted")
            for original, guard in registry.items():
                if original is reader:
                    guard()
                    allowed = {
                        "root",
                        "_fd",
                        "_identity",
                        "_revision",
                        "_inventory",
                        "_bodies",
                        "_source_rows",
                        "_package_roots",
                        "_repository_rows",
                        "_output_rows",
                        "_written",
                        "_reader_guard",
                    }
                    if object.__getattribute__(
                        reader, "_reader_guard"
                    ) is not guard or any(
                        name not in allowed
                        for name in object.__getattribute__(reader, "__dict__")
                    ):
                        raise PackageCheckoutError("retained read guard substituted")
                    return
            if object.__getattribute__(reader, "_reader_guard") is not None:
                raise PackageCheckoutError("retained read guard unregistered")
        finally:
            del reader, _registry, original, guard

    return _bind_retained_reader, _check_retained_reader


_bind_retained_reader, _check_retained_reader = _retain_reader_registry_ports(
    _RETAINED_READER_GUARDS
)


def _read_git(
    reader: PackageSourceCheckout,
    *args: str,
    _guard: Callable[..., None] = _check_retained_reader,
) -> bytes:
    _guard(reader)
    return _git(
        reader.root,
        *args,
        _retained=object.__getattribute__(reader, "_reader_guard") is not None,
    )


class PackageSourceCheckout:
    """One confined working-tree capture, usable only while this reader is live.

    Before/after rereads detect drift. They do not claim an external-writer
    exclusion fence or authenticate an OSS publication. Inventory is evidence,
    not a portable authority handle.
    """

    def __init__(
        self,
        repository_root: str | Path,
        *,
        _workflow_guard: Callable[[], None] | None = None,
    ) -> None:
        self._reader_guard: Callable[[], None] | None = None
        if _workflow_guard is not None:
            _bind_retained_reader(self, _workflow_guard)
            _workflow_guard()
        self.root = Path(repository_root).resolve(strict=True)
        if (
            Path(_git(self.root, "rev-parse", "--show-toplevel").decode().strip())
            != self.root
        ):
            raise PackageCheckoutError("select the canonical repository root")
        if _workflow_guard is not None:
            _workflow_guard()
        self._revision = _git(self.root, "rev-parse", "HEAD").decode().strip()
        if _workflow_guard is not None:
            _workflow_guard()
        descriptor = -1
        release_root = os.close
        self._fd = -1
        try:
            descriptor = os.open(
                self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            )
            self._fd = descriptor
            if _workflow_guard is not None:
                _workflow_guard()
            self._identity = os.fstat(self._fd).st_dev, os.fstat(self._fd).st_ino
            self._inventory: dict[str, Any] | None = None
            self._bodies: tuple[tuple[str, bytes], ...] = ()
            self._source_rows: tuple[tuple[str, str], ...] = ()
            self._package_roots: tuple[str, ...] = ()
            self._repository_rows: tuple[tuple[str, str], ...] = ()
            self._output_rows: tuple[tuple[str, str, str], ...] = ()
            self._written = False
        except BaseException as acquisition_error:
            # Revoke local custody before a once-only physical release. Neither
            # the caller nor a retained traceback may retry an uncertain close.
            self._fd = -1
            cleanup_state = "completed"
            cleanup_error = None
            try:
                if descriptor >= 0:
                    release_root(descriptor)
            except BaseException as error:  # noqa: BLE001 -- preserve original acquisition interruption/cause
                cleanup_state = "unknown"
                cleanup_error = error
            vars(acquisition_error)["workspace_source_acquisition_cleanup"] = (
                cleanup_state
            )
            if cleanup_error is not None:
                vars(acquisition_error)[
                    "workspace_source_acquisition_cleanup_error"
                ] = cleanup_error
            self._reader_guard = None
            raise
        finally:
            # A held acquisition error must not retain this failed reader/guard.
            del self, _workflow_guard, release_root

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self, *, _close: Callable[[int], None] = os.close) -> None:
        if self._reader_guard is not None:
            descriptor, self._fd = self._fd, -1
            self._bodies = ()
            self._inventory = None
            self._reader_guard = None
            if descriptor >= 0:
                _close(descriptor)
        else:
            if self._fd >= 0:
                os.close(self._fd)
                self._fd = -1
            self._bodies = ()
            self._inventory = None

    def _check(self, *, _guard: Callable[..., None] = _check_retained_reader) -> None:
        _guard(self)
        if self._fd < 0:
            raise PackageCheckoutError("checkout reader closed")
        current = self.root.stat()
        _guard(self)
        if self.root.is_symlink() or (current.st_dev, current.st_ino) != self._identity:
            raise PackageCheckoutError("repository root replaced")
        _guard(self)
        if _read_git(self, "rev-parse", "HEAD").decode().strip() != self._revision:
            raise PackageCheckoutError("repository revision changed")

    def resolve(
        self,
        packages: Sequence[str] = (),
        *,
        profiles: Sequence[str] = (),
        overlays: Sequence[str] = (),
        marker_environment: Mapping[str, str] | None = None,
        forbidden_packages: Sequence[str] = (),
        _guard: Callable[..., None] = _check_retained_reader,
    ) -> dict[str, Any]:
        """Resolve explicit PEP 508 selections against canonical declared leaves.

        Local edges preserve constraints, markers and accumulated extras. Unknown
        ``aware-`` names are not treated specially: undeclared names remain
        external requirements, without inventing local membership.
        """
        self._check()
        if self._inventory is not None:
            raise PackageCheckoutError("checkout selection already resolved")
        if (not packages and not profiles) or len(packages) > _MAX_PACKAGES:
            raise PackageCheckoutError("package selection empty or exceeds bound")
        environment: dict[str, str] = {
            key: str(value) for key, value in default_environment().items()
        }
        if marker_environment is not None:
            if set(marker_environment) != set(environment) or any(
                type(v) is not str or not v for v in marker_environment.values()
            ):
                raise PackageCheckoutError(
                    "target requires a complete PEP 508 marker environment"
                )
            environment = dict(marker_environment)
        try:
            python_version = Version(environment["python_full_version"])
        except InvalidVersion as error:
            raise PackageCheckoutError("target Python version invalid") from error
        if (
            ".".join(str(part) for part in python_version.release[:2])
            != environment["python_version"]
        ):
            raise PackageCheckoutError("target Python marker fields disagree")
        forbidden = {
            canonicalize_name(value, validate=True) for value in forbidden_packages
        }
        _guard(self)
        provider = LocalCheckoutWorkspaceCompositionProvider()
        if self._reader_guard is not None:
            _retain_composition_readers(provider, self._reader_guard)
        description = provider.describe(self.root)
        memberships = provider.python_package_memberships(description)
        paths = tuple(sorted({r["manifest_path"] for r in memberships}))
        structural = provider.declaration_body_paths(description)
        # Capture through the shared descriptor-confined reader, then rederive
        # the hierarchy. Local file parsing alone does not establish membership.
        captured = dict(
            capture_exact_paths(
                self._fd,
                tuple(sorted(set(structural) | set(paths))),
                _LIMITS,
                _verify=self._reader_guard,
            )
        )
        if any(
            row.get("kind") == "sdk_python_target"
            and _sha(captured[row["semantic_manifest_path"]])
            != row["semantic_manifest_digest"]
            for row in memberships
        ):
            raise PackageCheckoutError("SDK declaration changed before capture")
        _guard(self)
        repeated = LocalCheckoutWorkspaceCompositionProvider()
        if self._reader_guard is not None:
            _retain_composition_readers(repeated, self._reader_guard)
        repeated_description = repeated.describe(self.root)
        if (
            repeated_description != description
            or repeated.python_package_memberships(repeated_description) != memberships
        ):
            raise PackageCheckoutError("declaration membership changed")
        indexed: dict[str, list[str]] = {}
        projects: dict[str, dict[str, Any]] = {}
        metadata: dict[str, dict[str, Any]] = {}
        for path in paths:
            metadata[path] = tomllib.loads(captured[path].decode())
            project = metadata[path].get("project")
            if type(project) is not dict:
                raise PackageCheckoutError(
                    f"static PEP 621 project unavailable: {path}"
                )
            name = project.get("name")
            if type(name) is not str or not name:
                raise PackageCheckoutError(f"package name unavailable: {path}")
            name = canonicalize_name(name, validate=True)
            projects[path] = project
            indexed.setdefault(name, []).append(path)
        profile_keys: tuple[str, ...] = ()
        profile_leaves: tuple[tuple[str, tuple[str, ...]], ...] = ()
        selected_overlays = tuple(sorted(set(overlays)))
        repository_files: tuple[dict[str, str], ...] = ()
        selected_packages = list(packages)
        if profiles or overlays:
            payload = tomllib.loads(captured["aware.repo.toml"].decode())
            profile_values = parse_checkout_profiles(
                payload,
                frozenset(
                    w["workspace_handle"]
                    for w in cast(dict[str, Any], description["repository"])[
                        "workspaces"
                    ]
                ),
            )
            profile_leaves, profile_keys, profile_overlays = expand_checkout_profiles(
                profile_values,
                profiles,
                memberships,
                description,
            )
            selected_overlays = tuple(sorted(set(overlays) | set(profile_overlays)))
            repository_files = checkout_repository_files(payload, selected_overlays)
            for path, extras in profile_leaves:
                name = projects[path]["name"]
                selected_packages.append(
                    name + ("[" + ",".join(extras) + "]" if extras else "")
                )
        if len(selected_packages) > _MAX_PACKAGES:
            raise PackageCheckoutError("composed package selection exceeds bound")
        roots: dict[str, str] = {}
        requested_extras: dict[str, set[str]] = {}
        requirements: dict[str, list[Requirement]] = {}
        queue: deque[str] = deque()
        root_requests: set[str] = set()
        edges: set[tuple[str, str]] = set()

        def enqueue(requirement: Requirement, parent: str | None) -> None:
            name = canonicalize_name(requirement.name)
            if name in forbidden:
                raise PackageCheckoutError(
                    f"forbidden dependency {name} from {parent or 'selection'}"
                )
            if parent is not None:
                edges.add((parent, str(requirement)))
            candidates = indexed.get(name, [])
            sources = (
                {}
                if parent is None
                else metadata[roots[parent]]
                .get("tool", {})
                .get("uv", {})
                .get("sources", {})
            )
            source = next(
                (v for k, v in sources.items() if canonicalize_name(k) == name), None
            )
            if type(source) is dict and (
                ("workspace" in source and source["workspace"] is not True)
                or ("path" in source and type(source["path"]) is not str)
                or ("editable" in source and type(source["editable"]) is not bool)
            ):
                raise PackageCheckoutError(f"invalid owner source declaration: {name}")
            if source is not None and (
                type(source) is not dict
                or set(source) - {"workspace", "path", "editable"}
            ):
                raise PackageCheckoutError(
                    f"owner-selected artifact source requires qualified resolution: {name}"
                )
            if not candidates:
                if parent is None:
                    raise PackageCheckoutError(
                        f"selected package is not declared: {name}"
                    )
                if source is not None:
                    raise PackageCheckoutError(
                        f"owner-selected source requires canonical local/artifact admission: {name} from {parent}"
                    )
                requirements.setdefault(name, []).append(requirement)
                return
            if len(candidates) != 1:
                raise PackageCheckoutError(
                    f"ambiguous package name {name}: {candidates}"
                )
            path = candidates[0]
            if any(
                row.get("kind", "code") not in {"code", "sdk_python_target"}
                for row in memberships
                if row["manifest_path"] == path
            ):
                raise PackageCheckoutError(
                    f"Python checkout requires an owner-declared Code leaf or SDK Python target: {path}"
                )
            if source is not None and "path" in source:
                assert parent is not None
                expected_root = (self.root / roots[parent]).parent / source["path"]
                if expected_root.resolve() != (self.root / path).parent.resolve():
                    raise PackageCheckoutError(
                        f"owner source path and canonical membership disagree: {name}"
                    )
            project = projects[path]
            dynamic = project.get("dynamic", [])
            if type(dynamic) is not list or any(
                type(field) is not str for field in dynamic
            ):
                raise PackageCheckoutError(f"invalid dynamic metadata: {name}")
            if set(dynamic) & {
                "version",
                "dependencies",
                "optional-dependencies",
            }:
                raise PackageCheckoutError(
                    f"dynamic metadata requires an owner build: {name}"
                )
            try:
                version = Version(project["version"])
            except (KeyError, TypeError, InvalidVersion) as error:
                raise PackageCheckoutError(
                    f"static version unavailable: {name}"
                ) from error
            if not requirement.specifier.contains(version, prereleases=True):
                raise PackageCheckoutError(
                    f"local version conflict: {requirement} versus {version} at {path}"
                )
            python = project.get("requires-python")
            if python is not None and not _requirement(
                f"python{python}"
            ).specifier.contains(environment["python_full_version"], prereleases=True):
                raise PackageCheckoutError(
                    f"target Python incompatible with {name}: {python}"
                )
            optional = project.get("optional-dependencies", {})
            if type(optional) is not dict:
                raise PackageCheckoutError(f"optional dependencies unavailable: {name}")
            available = {canonicalize_name(key): key for key in optional}
            if len(available) != len(optional):
                raise PackageCheckoutError(f"ambiguous extras: {name}")
            extra_names = {canonicalize_name(extra) for extra in requirement.extras}
            if extra_names - set(available):
                raise PackageCheckoutError(
                    f"unknown extras on {name}: {sorted(extra_names - set(available))}"
                )
            extras = requested_extras.setdefault(name, set())
            previous = set(extras)
            extras.update(extra_names)
            if name not in roots or extras != previous:
                queue.append(name)
            roots[name] = path
            if len(roots) > _MAX_PACKAGES:
                raise PackageCheckoutError("dependency closure exceeds bound")

        for raw in selected_packages:
            req = _requirement(raw)
            if req.marker is not None:
                raise PackageCheckoutError(
                    "root selection must be unconditional; supply the target separately"
                )
            root_requests.add(str(req))
            enqueue(req, None)
        while queue:
            name = queue.popleft()
            project = projects[roots[name]]
            values = project.get("dependencies", [])
            if type(values) is not list or any(type(v) is not str for v in values):
                raise PackageCheckoutError(f"invalid dependencies: {name}")
            groups = [(values, ("", *sorted(requested_extras[name])))]
            optional = project.get("optional-dependencies", {})
            for extra in sorted(requested_extras[name]):
                key = next(k for k in optional if canonicalize_name(k) == extra)
                extra_values = optional[key]
                if type(extra_values) is not list or any(
                    type(v) is not str for v in extra_values
                ):
                    raise PackageCheckoutError(
                        f"invalid extra dependencies: {name}[{extra}]"
                    )
                groups.append((extra_values, (extra,)))
            for values, marker_extras in groups:
                for raw in values:
                    req = _requirement(raw)
                    if req.marker is None or any(
                        req.marker.evaluate({**environment, "extra": extra})
                        for extra in marker_extras
                    ):
                        enqueue(req, name)
        self._package_roots = tuple(
            sorted({str(PurePosixPath(path).parent) for path in roots.values()})
        )
        if "." in self._package_roots:
            raise PackageCheckoutError(
                "repository-root package requires its owner-defined physical boundary"
            )
        for left in self._package_roots:
            if any(
                right != left and right.startswith(left + "/")
                for right in self._package_roots
            ):
                raise PackageCheckoutError(
                    "nested package roots require an owner-defined packaging boundary"
                )
        _guard(self)
        self._source_rows = self._tracked_sources()
        source_paths = {path for _, path in self._source_rows}
        if not set(roots.values()) <= source_paths:
            raise PackageCheckoutError("selected package manifest is not Git-tracked")
        _guard(self)
        self._repository_rows = self._tracked_exact_sources(
            tuple(sorted({row["source_path"] for row in repository_files}))
        )
        modes = {path: mode for mode, path in self._repository_rows}
        outputs = [(mode, path, path) for mode, path in self._source_rows]
        outputs.extend(
            (modes[row["source_path"]], row["target_path"], row["source_path"])
            for row in repository_files
        )
        targets = [target for _, target, _ in outputs] + ["checkout-inventory.json"]
        target_set = set(targets)
        if len(target_set) != len(targets) or any(
            str(parent) in target_set
            for target in targets
            for parent in PurePosixPath(target).parents
            if str(parent) != "."
        ):
            raise PackageCheckoutError("checkout output target collision")
        self._output_rows = tuple(sorted(outputs, key=lambda row: row[1]))
        self._bodies = capture_exact_paths(
            self._fd,
            tuple(sorted(source_paths | set(captured) | set(modes))),
            _LIMITS,
            _verify=self._reader_guard,
        )
        fresh = dict(self._bodies)
        if any(fresh[path] != body for path, body in captured.items()):
            raise PackageCheckoutError("captured declaration changed during resolution")
        inventory = {
            "contract": PROFILE_CONTRACT if profiles or overlays else CONTRACT,
            "state": "source_closure_resolved",
            "revision_basis": self._revision,
            "source_mode": "captured_working_tree",
            "repository": cast(dict[str, object], description["repository"])[
                "repository_ref"
            ],
            "selection": sorted(root_requests),
            "marker_environment": environment,
            "forbidden_packages": sorted(forbidden),
            "packages": [
                {
                    "name": name,
                    "version": projects[path]["version"],
                    "extras": sorted(requested_extras[name]),
                    "manifest_path": path,
                    "root": str(PurePosixPath(path).parent),
                    "build_system": metadata[path].get("build-system", {}),
                    "memberships": [
                        r for r in memberships if r["manifest_path"] == path
                    ],
                }
                for name, path in sorted(roots.items())
            ],
            "dependency_edges": [list(edge) for edge in sorted(edges)],
            "registry_requirements": sorted(
                {str(req) for reqs in requirements.values() for req in reqs}
            ),
            "registry_resolver_requests": sorted(
                {
                    str(req).split(";")[0].strip()
                    for reqs in requirements.values()
                    for req in reqs
                }
            ),
            "manifests": [
                {"path": path, "digest": _sha(body)}
                for path, body in sorted(captured.items())
            ],
            "files": [
                {"path": target, "digest": _sha(fresh[source]), "mode": mode}
                for mode, target, source in self._output_rows
            ],
            "claims": {
                "materialized": False,
                "installed": False,
                "registry_locked": False,
                "publication_authorized": False,
            },
        }
        if profiles or overlays:
            inventory["profiles"] = {
                "requested": sorted(set(profiles)),
                "expanded": list(profile_keys),
            }
            inventory["profile_members"] = [
                {"manifest_path": path, "extras": list(extras)}
                for path, extras in profile_leaves
            ]
            inventory["overlays"] = list(selected_overlays)
            inventory["repository_files"] = [
                {**row, "source_digest": _sha(fresh[row["source_path"]])}
                for row in repository_files
            ]
        inventory["inventory_digest"] = _sha(_wire(inventory))
        self._inventory = inventory
        _guard(self)
        self.revalidate()
        return copy.deepcopy(inventory)

    def _tracked_sources(
        self, *, _guard: Callable[..., None] = _check_retained_reader
    ) -> tuple[tuple[str, str], ...]:
        _guard(self)
        untracked = _read_git(
            self,
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            *self._package_roots,
        )
        if untracked:
            raise PackageCheckoutError(
                "untracked package sources require repository admission"
            )
        rows: list[tuple[str, str]] = []
        retained = self._reader_guard is not None
        root_text = str(self.root)
        for raw in _read_git(
            self, "ls-files", "--stage", "-z", "--", *self._package_roots
        ).split(b"\0"):
            if not raw:
                continue
            metadata, path_wire = raw.split(b"\t", 1)
            mode, _, stage = metadata.decode().split()
            path = path_wire.decode("utf-8")
            validate_relative_path(path)
            if stage != "0" or mode not in {"100644", "100755"}:
                raise PackageCheckoutError(
                    f"unsupported tracked package member: {path}"
                )
            if retained:
                if os.stat is not _TRACKED_STAT:
                    raise PackageCheckoutError("retained stat reader substituted")
                executable = bool(_TRACKED_STAT(root_text + "/" + path).st_mode & 0o111)
            else:
                executable = bool((self.root / path).stat().st_mode & 0o111)
            if executable != (mode == "100755"):
                raise PackageCheckoutError(f"source mode changed: {path}")
            rows.append((mode, path))
        return tuple(sorted(rows, key=lambda row: row[1]))

    def _tracked_exact_sources(
        self,
        paths: tuple[str, ...],
        *,
        _guard: Callable[..., None] = _check_retained_reader,
    ) -> tuple[tuple[str, str], ...]:
        _guard(self)
        if not paths:
            return ()
        # Only immutable exact source names use operation-local hashing. Other
        # inputs preserve the original sequence membership and its behavior.
        membership = (
            frozenset(paths)
            if type(paths) is tuple and all(type(path) is str for path in paths)
            else paths
        )
        rows = []
        for raw in _read_git(self, "ls-files", "--stage", "-z", "--", *paths).split(
            b"\0"
        ):
            if not raw:
                continue
            metadata, path_wire = raw.split(b"\t", 1)
            mode, _, stage = metadata.decode().split()
            path = path_wire.decode("utf-8")
            if (
                path not in membership
                or stage != "0"
                or mode not in {"100644", "100755"}
            ):
                raise PackageCheckoutError(
                    "repository file is not one tracked regular file"
                )
            _guard(self)
            if bool((self.root / path).stat().st_mode & 0o111) != (mode == "100755"):
                raise PackageCheckoutError("repository file mode changed")
            rows.append((mode, path))
        if {path for _, path in rows} != set(paths):
            raise PackageCheckoutError("repository file is not Git-tracked")
        return tuple(sorted(rows, key=lambda row: row[1]))

    def revalidate(
        self, *, _guard: Callable[..., None] = _check_retained_reader
    ) -> None:
        _guard(self)
        self._check()
        if self._inventory is None:
            raise PackageCheckoutError("checkout is not resolved")
        _guard(self)
        if (
            self._tracked_exact_sources(
                tuple(path for _, path in self._repository_rows)
            )
            != self._repository_rows
        ):
            raise PackageCheckoutError("repository-file membership changed")
        _guard(self)
        if self._tracked_sources() != self._source_rows:
            raise PackageCheckoutError("tracked source membership changed")
        _guard(self)
        if (
            capture_exact_paths(
                self._fd,
                tuple(path for path, _ in self._bodies),
                _LIMITS,
                _verify=self._reader_guard,
            )
            != self._bodies
        ):
            raise PackageCheckoutError("checkout sources changed")
        _guard(self)
        self._check()

    def revalidate_paths(
        self,
        output_paths: tuple[str, ...],
        *,
        _guard: Callable[..., None] = _check_retained_reader,
        _original_capture: tuple[tuple[Any, ...], tuple[Any, ...]] | None = None,
    ) -> None:
        """Recheck original selected leaves; full membership is a separate boundary."""
        originals: tuple[Any, ...] = ()
        original_bodies: tuple[Any, ...] = ()
        captured: Any = None
        outputs = modes = actual = expected = None
        source_paths = row = None
        try:
            _guard(self)
            self._check()
            if self._inventory is None:
                raise PackageCheckoutError("checkout is not resolved")
            if (
                type(output_paths) is not tuple
                or len(output_paths) > _LIMITS.maximum_files
                or any(type(path) is not str for path in output_paths)
            ):
                raise PackageCheckoutError("invalid selected output paths")
            if tuple(sorted(set(output_paths))) != output_paths:
                raise PackageCheckoutError(
                    "selected outputs are duplicated or reordered"
                )
            if _original_capture is not None:
                # The original Workflow owner supplies its retained immutable
                # tuples. Recheck after Git/guard callbacks, before any lookup;
                # identity checks never iterate a substituted live container.
                if (
                    type(_original_capture) is not tuple
                    or len(_original_capture) != 2
                    or type(_original_capture[0]) is not tuple
                    or type(_original_capture[1]) is not tuple
                    or self._output_rows is not _original_capture[0]
                    or self._bodies is not _original_capture[1]
                ):
                    raise PackageCheckoutError("retained capture substituted")
                originals, original_bodies = _original_capture
                outputs = {}
                for path in output_paths:
                    lower, upper = 0, len(originals)
                    while lower < upper:
                        middle = (lower + upper) // 2
                        if originals[middle][1] < path:
                            lower = middle + 1
                        else:
                            upper = middle
                    if lower == len(originals) or originals[lower][1] != path:
                        raise PackageCheckoutError(
                            "selected output is outside the original capture"
                        )
                    row = originals[lower]
                    outputs[path] = (row[0], row[2])
            else:
                # Standalone/unretained callers retain their original behavior.
                outputs = {
                    target: (mode, source) for mode, target, source in self._output_rows
                }
                if any(path not in outputs for path in output_paths):
                    raise PackageCheckoutError(
                        "selected output is outside the original capture"
                    )
            modes = {outputs[path][1]: outputs[path][0] for path in output_paths}
            source_paths = tuple(sorted(modes))
            if source_paths:
                _guard(self)
                if self._tracked_exact_sources(source_paths) != tuple(
                    (modes[path], path) for path in source_paths
                ):
                    raise PackageCheckoutError(
                        "selected source membership or mode changed"
                    )
                _guard(self)
                if _original_capture is None:
                    captured = dict(self._bodies)
                elif (
                    self._output_rows is not originals
                    or self._bodies is not original_bodies
                ):
                    raise PackageCheckoutError("retained capture substituted")
                actual = capture_exact_paths(
                    self._fd, source_paths, _LIMITS, _verify=self._reader_guard
                )
                if _original_capture is None:
                    expected = tuple((path, captured[path]) for path in source_paths)
                else:
                    if (
                        self._output_rows is not originals
                        or self._bodies is not original_bodies
                    ):
                        raise PackageCheckoutError("retained capture substituted")
                    expected = []
                    for path in source_paths:
                        lower, upper = 0, len(original_bodies)
                        while lower < upper:
                            middle = (lower + upper) // 2
                            if original_bodies[middle][0] < path:
                                lower = middle + 1
                            else:
                                upper = middle
                        if (
                            lower == len(original_bodies)
                            or original_bodies[lower][0] != path
                        ):
                            raise KeyError(path)
                        expected.append(original_bodies[lower])
                    expected = tuple(expected)
                if actual != expected:
                    raise PackageCheckoutError("selected checkout sources changed")
            _guard(self)
            self._check()
            if _original_capture is not None and (
                self._output_rows is not originals
                or self._bodies is not original_bodies
            ):
                raise PackageCheckoutError("retained capture substituted")
        finally:
            # Held errors may retain frames, never this borrowed body inventory.
            del (
                self,
                output_paths,
                _guard,
                _original_capture,
                originals,
                original_bodies,
                outputs,
                modes,
                captured,
                actual,
                expected,
                source_paths,
                row,
            )

    def write(self, destination: str | Path) -> dict[str, Any]:
        """Copy exact captured package roots; refuse existing/inside-repo targets."""
        self.revalidate()
        if self._written:
            raise PackageCheckoutError("checkout already written")
        target = Path(destination).absolute()
        parent = target.parent.resolve(strict=True)
        target = parent / target.name
        if target == self.root or self.root in target.parents:
            raise PackageCheckoutError(
                "checkout destination must be outside the source repository"
            )
        target.mkdir()  # Exclusive destination; no pre-existing files are touched.
        try:
            bodies = dict(self._bodies)
            for mode, path, source in self._output_rows:
                output = target / path
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("xb") as stream:
                    stream.write(bodies[source])
                output.chmod(0o755 if mode == "100755" else 0o644)
            assert self._inventory is not None
            wire = _wire(self._inventory) + b"\n"
            with (target / "checkout-inventory.json").open("xb") as stream:
                stream.write(wire)
            self.revalidate()
            verify_package_checkout(target)
        except BaseException:
            shutil.rmtree(target)
            raise
        self._written = True
        return {
            "state": "source_checkout_written",
            "destination": str(target),
            "inventory_digest": self._inventory["inventory_digest"],
        }


def verify_package_checkout(destination: str | Path) -> dict[str, Any]:
    """Verify generated evidence and the complete checkout file set, not custody."""
    root = Path(destination).resolve(strict=True)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        wire = capture_exact_paths(fd, ("checkout-inventory.json",), _LIMITS)[0][1]
    finally:
        os.close(fd)
    inventory = json.loads(wire)
    if type(inventory) is not dict or inventory.get("contract") not in {
        CONTRACT,
        PROFILE_CONTRACT,
    }:
        raise PackageCheckoutError("inventory contract differs")
    if _wire(inventory) + b"\n" != wire:
        raise PackageCheckoutError("inventory bytes are not canonical")
    digest = inventory.pop("inventory_digest", None)
    if _sha(_wire(inventory)) != digest:
        raise PackageCheckoutError("inventory digest differs")
    expected: set[str] = {"checkout-inventory.json"}
    rows = inventory.get("files")
    if type(rows) is not list or len(rows) > _LIMITS.maximum_files:
        raise PackageCheckoutError("inventory file set invalid")
    for row in rows:
        if (
            type(row) is not dict
            or set(row) != {"path", "digest", "mode"}
            or type(row["path"]) is not str
            or type(row["digest"]) is not str
            or type(row["mode"]) is not str
        ):
            raise PackageCheckoutError("inventory file row invalid")
        path = row["path"]
        validate_relative_path(path)
        if path in expected or row["mode"] not in {"100644", "100755"}:
            raise PackageCheckoutError("inventory member invalid")
        expected.add(path)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        actual_bodies = dict(capture_exact_paths(fd, tuple(sorted(expected)), _LIMITS))
    finally:
        os.close(fd)
    actual = set()
    for directory, dirs, names in os.walk(root, followlinks=False):
        if any((Path(directory) / name).is_symlink() for name in dirs):
            raise PackageCheckoutError("checkout contains a linked directory")
        actual.update(str((Path(directory) / name).relative_to(root)) for name in names)
    if actual != expected:
        raise PackageCheckoutError("checkout file coverage differs")
    for row in rows:
        if _sha(actual_bodies[row["path"]]) != row["digest"] or bool(
            (root / row["path"]).stat().st_mode & 0o111
        ) != (row["mode"] == "100755"):
            raise PackageCheckoutError(f"checkout member changed: {row['path']}")
    inventory["inventory_digest"] = digest
    return inventory
