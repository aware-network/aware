from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import importlib
import json
from pathlib import Path, PurePosixPath
import sys
import tomllib
from uuid import UUID

from aware_attention.manifest import load_aware_attention_toml_spec
from aware_experience.manifest import (
    AwareExperienceTomlSpec,
    load_aware_experience_toml_spec,
)
from aware_interface.manifest import (
    AwareInterfaceDependencyKind,
    AwarePaneDependencyKind,
    AwareInterfaceTomlSpec,
    AwarePaneTomlSpec,
    AwareRenderComponentTomlSpec,
    load_aware_interface_toml_spec,
    load_aware_pane_toml_spec,
    load_aware_render_component_toml_spec,
)


_LOCAL_WORKSPACE_PACKAGE_DIRS = frozenset(
    (
        "attentions",
        "experiences",
        "interfaces",
        "panes",
        "render_components",
    )
)


@dataclass(frozen=True, slots=True)
class InterfacePanePackageSnapshot:
    spec_path: Path
    package_root: Path
    spec: AwarePaneTomlSpec
    source_files: tuple[Path, ...]
    experience_packages: tuple[InterfaceExperiencePackageSnapshot, ...] = ()
    render_spec_files: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceAttentionLayoutSectionSnapshot:
    layout_config_section_config_id: UUID
    section_config_id: UUID
    section_key: str
    title: str
    description: str | None
    order: int
    flex: float
    is_visible: bool


@dataclass(frozen=True, slots=True)
class InterfaceAttentionLayoutSnapshot:
    layout_config_id: UUID
    layout_key: str
    title: str
    description: str | None
    frame_mode: str
    sections: tuple[InterfaceAttentionLayoutSectionSnapshot, ...]


@dataclass(frozen=True, slots=True)
class InterfaceAttentionPackageSnapshot:
    package_name: str
    runtime_artifact_path: Path
    layouts: tuple[InterfaceAttentionLayoutSnapshot, ...]


@dataclass(frozen=True, slots=True)
class InterfaceExperiencePackageSnapshot:
    spec_path: Path
    package_root: Path
    spec: AwareExperienceTomlSpec
    source_files: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class InterfaceRenderComponentPackageSnapshot:
    spec_path: Path
    package_root: Path
    spec: AwareRenderComponentTomlSpec
    source_files: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class InterfaceDependencyCatalogRootSnapshot:
    root: Path
    source_kind: str


@dataclass(frozen=True, slots=True)
class InterfaceWorkspaceSnapshot:
    repo_root: Path
    workspace_root: Path
    package_root: Path
    spec_path: Path
    spec: AwareInterfaceTomlSpec
    source_files: tuple[Path, ...]
    pane_packages: tuple[InterfacePanePackageSnapshot, ...]
    attention_packages: tuple[InterfaceAttentionPackageSnapshot, ...]
    experience_packages: tuple[InterfaceExperiencePackageSnapshot, ...]
    render_component_packages: tuple[InterfaceRenderComponentPackageSnapshot, ...]
    dependency_catalog_roots: tuple[InterfaceDependencyCatalogRootSnapshot, ...]
    config_bundle_path: Path

    @property
    def pane_source_files(self) -> tuple[Path, ...]:
        return tuple(
            path for package in self.pane_packages for path in package.source_files
        )

    @property
    def pane_render_spec_files(self) -> tuple[Path, ...]:
        return tuple(
            path for package in self.pane_packages for path in package.render_spec_files
        )


class InterfaceWorkspace:
    _spec_path: Path
    _package_root: Path
    _repo_root: Path

    def __init__(self, *, spec_path: str | Path, repo_root: str | Path | None = None):
        resolved_spec_path = Path(spec_path).resolve()
        if not resolved_spec_path.exists():
            raise FileNotFoundError(
                f"aware.interface.toml not found: {resolved_spec_path}"
            )
        self._spec_path = resolved_spec_path
        self._package_root = resolved_spec_path.parent
        if repo_root is None:
            self._repo_root = _resolve_repo_root(start=self._package_root)
        else:
            self._repo_root = Path(repo_root).resolve()

    @classmethod
    def from_toml(
        cls,
        *,
        toml_path: str | Path,
        repo_root: str | Path | None = None,
    ) -> InterfaceWorkspace:
        return cls(spec_path=toml_path, repo_root=repo_root)

    @property
    def spec_path(self) -> Path:
        return self._spec_path

    @property
    def package_root(self) -> Path:
        return self._package_root

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    def build_snapshot(self) -> InterfaceWorkspaceSnapshot:
        spec = load_aware_interface_toml_spec(toml_path=self._spec_path)
        workspace_root = _resolve_workspace_root(
            start=self._package_root, fallback=self._repo_root
        )

        ordered_source_files = _collect_authored_source_files(
            package_root=self._package_root,
            sources_dir=spec.build.sources_dir,
            include_paths=spec.build.include_paths,
            exclude_paths=spec.build.exclude_paths,
            rel_base=self._package_root,
            label="[build].sources_dir",
        )
        pane_packages = _merge_pane_package_snapshots(
            _discover_workspace_pane_packages(
                repo_root=self._repo_root,
                workspace_root=workspace_root,
            ),
            _load_declared_pane_packages(
                repo_root=self._repo_root,
                workspace_root=workspace_root,
                dependencies=spec.dependencies,
            ),
        )
        attention_packages = _load_declared_attention_packages(
            repo_root=self._repo_root,
            workspace_root=workspace_root,
            dependencies=spec.dependencies,
        )
        if not attention_packages:
            attention_packages = _load_workspace_attention_packages(
                repo_root=self._repo_root,
                workspace_root=workspace_root,
            )
        experience_packages = _load_declared_experience_packages(
            repo_root=self._repo_root,
            workspace_root=workspace_root,
            dependencies=spec.dependencies,
        )
        render_component_packages = _load_declared_render_component_packages(
            repo_root=self._repo_root,
            workspace_root=workspace_root,
            dependencies=spec.dependencies,
        )
        dependency_catalog_roots = _resolve_compile_time_dependency_catalog_roots(
            repo_root=self._repo_root,
            workspace_root=workspace_root,
        )

        config_bundle_path = (
            self._package_root / spec.build.config_bundle_path
        ).resolve()
        _assert_within(
            base=self._package_root,
            candidate=config_bundle_path,
            label="[build].config_bundle_path",
        )

        return InterfaceWorkspaceSnapshot(
            repo_root=self._repo_root,
            workspace_root=workspace_root,
            package_root=self._package_root,
            spec_path=self._spec_path,
            spec=spec,
            source_files=ordered_source_files,
            pane_packages=pane_packages,
            attention_packages=attention_packages,
            experience_packages=experience_packages,
            render_component_packages=render_component_packages,
            dependency_catalog_roots=dependency_catalog_roots,
            config_bundle_path=config_bundle_path,
        )


def _load_declared_attention_packages(
    *,
    repo_root: Path,
    workspace_root: Path,
    dependencies,
) -> tuple[InterfaceAttentionPackageSnapshot, ...]:
    attention_package_names = tuple(
        dependency.package_name.strip()
        for dependency in dependencies
        if dependency.kind == AwareInterfaceDependencyKind.attention_package
        and dependency.package_name.strip()
    )
    if not attention_package_names:
        return ()

    package_snapshots: list[InterfaceAttentionPackageSnapshot] = []
    for package_name in attention_package_names:
        runtime_artifact_path = (
            repo_root
            / ".aware"
            / "attention"
            / "runtime"
            / package_name
            / "attention.compile_plan.json"
        ).resolve()
        _assert_within(
            base=repo_root,
            candidate=runtime_artifact_path,
            label="attention runtime artifact",
        )
        if not runtime_artifact_path.exists():
            attention_toml_path = _resolve_attention_toml_path(
                repo_root=repo_root,
                workspace_root=workspace_root,
                package_name=package_name,
            )
            _compile_attention_workspace(
                toml_path=attention_toml_path,
                repo_root=repo_root,
                emit_compile_plan=True,
            )
        if not runtime_artifact_path.exists():
            raise FileNotFoundError(
                "Declared attention_package dependency is missing compiled runtime artifact: "
                + f"{runtime_artifact_path}"
            )
        if not runtime_artifact_path.is_file():
            raise IsADirectoryError(
                f"Declared attention_package runtime artifact must be a file: {runtime_artifact_path}"
            )
        package_snapshots.append(
            _load_attention_package_snapshot(
                package_name=package_name,
                runtime_artifact_path=runtime_artifact_path,
            )
        )
    return tuple(
        sorted(package_snapshots, key=lambda item: item.package_name.casefold())
    )


def _load_workspace_attention_packages(
    *,
    repo_root: Path,
    workspace_root: Path,
) -> tuple[InterfaceAttentionPackageSnapshot, ...]:
    attention_manifest_paths = _local_package_manifest_paths(
        root=workspace_root,
        directory_name="attentions",
        filename="aware.attention.toml",
    )
    package_snapshots: list[InterfaceAttentionPackageSnapshot] = []
    for resolved_path in attention_manifest_paths:
        _assert_within(
            base=workspace_root,
            candidate=resolved_path,
            label="workspace attention manifest",
        )
        manifest = load_aware_attention_toml_spec(toml_path=resolved_path)
        package_name = (manifest.attention.package_name or "").strip()
        if not package_name:
            raise ValueError(
                "Workspace attention manifest requires non-empty [attention].package_name: "
                + str(resolved_path)
            )
        runtime_artifact_path = (
            repo_root
            / ".aware"
            / "attention"
            / "runtime"
            / package_name
            / "attention.compile_plan.json"
        ).resolve()
        _assert_within(
            base=repo_root,
            candidate=runtime_artifact_path,
            label="workspace attention runtime artifact",
        )
        if not runtime_artifact_path.exists():
            _compile_attention_workspace(
                toml_path=resolved_path,
                repo_root=repo_root,
                emit_compile_plan=True,
            )
        if not runtime_artifact_path.exists():
            raise FileNotFoundError(
                "Workspace attention entry is missing compiled runtime artifact: "
                + f"{runtime_artifact_path}"
            )
        package_snapshots.append(
            _load_attention_package_snapshot(
                package_name=package_name,
                runtime_artifact_path=runtime_artifact_path,
            )
        )
    return tuple(
        sorted(package_snapshots, key=lambda item: item.package_name.casefold())
    )


def _load_declared_pane_packages(
    *,
    repo_root: Path,
    workspace_root: Path,
    dependencies,
) -> tuple[InterfacePanePackageSnapshot, ...]:
    pane_package_names = tuple(
        dependency.package_name.strip()
        for dependency in dependencies
        if dependency.kind == AwareInterfaceDependencyKind.pane_package
        and dependency.package_name.strip()
    )
    if not pane_package_names:
        return ()

    package_snapshots: list[InterfacePanePackageSnapshot] = []
    for package_name in pane_package_names:
        spec_path = _resolve_pane_toml_path(
            repo_root=repo_root,
            workspace_root=workspace_root,
            package_name=package_name,
        )
        package_root = spec_path.parent.resolve()
        spec = load_aware_pane_toml_spec(toml_path=spec_path)
        if (spec.pane.package_name or "").strip() != package_name:
            raise ValueError(
                "Declared pane_package dependency package_name mismatch: "
                + f"declared={package_name!r} manifest={spec.pane.package_name!r} "
                + f"path={spec_path}"
            )
        source_files = _collect_authored_source_files(
            package_root=package_root,
            sources_dir=spec.build.sources_dir,
            include_paths=spec.build.include_paths,
            exclude_paths=spec.build.exclude_paths,
            rel_base=repo_root,
            label="pane [build].sources_dir",
        )
        experience_packages = _load_pane_package_experience_packages(
            repo_root=repo_root,
            workspace_root=workspace_root,
            spec=spec,
        )
        render_spec_files = _collect_pane_render_spec_files(
            package_root=package_root,
            rel_base=repo_root,
        )
        package_snapshots.append(
            InterfacePanePackageSnapshot(
                spec_path=spec_path,
                package_root=package_root,
                spec=spec,
                source_files=source_files,
                experience_packages=experience_packages,
                render_spec_files=render_spec_files,
            )
        )
    return tuple(
        sorted(
            package_snapshots,
            key=lambda item: item.spec.pane.package_name.casefold(),
        )
    )


def _load_declared_experience_packages(
    *,
    repo_root: Path,
    workspace_root: Path,
    dependencies,
) -> tuple[InterfaceExperiencePackageSnapshot, ...]:
    experience_package_names = tuple(
        dependency.package_name.strip()
        for dependency in dependencies
        if dependency.kind == AwareInterfaceDependencyKind.experience_package
        and dependency.package_name.strip()
    )
    if not experience_package_names:
        return ()

    package_snapshots: list[InterfaceExperiencePackageSnapshot] = []
    package_snapshots.extend(
        _load_experience_package_snapshots_by_name(
            repo_root=repo_root,
            workspace_root=workspace_root,
            package_names=experience_package_names,
            label="Declared experience_package dependency",
        )
    )
    return tuple(
        sorted(
            package_snapshots,
            key=lambda item: item.spec.experience.package_name.casefold(),
        )
    )


def _load_pane_package_experience_packages(
    *,
    repo_root: Path,
    workspace_root: Path,
    spec: AwarePaneTomlSpec,
) -> tuple[InterfaceExperiencePackageSnapshot, ...]:
    package_names = tuple(
        dependency.package_name.strip()
        for dependency in spec.dependencies
        if dependency.kind == AwarePaneDependencyKind.experience_package
        and dependency.package_name.strip()
    )
    return _load_experience_package_snapshots_by_name(
        repo_root=repo_root,
        workspace_root=workspace_root,
        package_names=package_names,
        label="Declared pane experience_package dependency",
    )


def _load_experience_package_snapshots_by_name(
    *,
    repo_root: Path,
    workspace_root: Path,
    package_names: tuple[str, ...],
    label: str,
) -> tuple[InterfaceExperiencePackageSnapshot, ...]:
    if not package_names:
        return ()

    package_snapshots: list[InterfaceExperiencePackageSnapshot] = []
    seen: set[str] = set()
    for package_name in package_names:
        package_key = package_name.casefold()
        if package_key in seen:
            raise ValueError(
                f"{label} declared duplicate package_name={package_name!r}"
            )
        seen.add(package_key)
        spec_path = _resolve_experience_toml_path(
            repo_root=repo_root,
            workspace_root=workspace_root,
            package_name=package_name,
        )
        package_root = spec_path.parent.resolve()
        spec = load_aware_experience_toml_spec(toml_path=spec_path)
        if (spec.experience.package_name or "").strip() != package_name:
            raise ValueError(
                f"{label} package_name mismatch: "
                + f"declared={package_name!r} manifest={spec.experience.package_name!r} path={spec_path}"
            )
        source_files = _collect_authored_source_files(
            package_root=package_root,
            sources_dir=spec.build.sources_dir,
            include_paths=spec.build.include_paths,
            exclude_paths=spec.build.exclude_paths,
            rel_base=package_root,
            label="experience [build].sources_dir",
        )
        package_snapshots.append(
            InterfaceExperiencePackageSnapshot(
                spec_path=spec_path,
                package_root=package_root,
                spec=spec,
                source_files=source_files,
            )
        )
    return tuple(
        sorted(
            package_snapshots,
            key=lambda item: item.spec.experience.package_name.casefold(),
        )
    )


def _load_declared_render_component_packages(
    *,
    repo_root: Path,
    workspace_root: Path,
    dependencies,
) -> tuple[InterfaceRenderComponentPackageSnapshot, ...]:
    render_component_package_names = tuple(
        dependency.package_name.strip()
        for dependency in dependencies
        if dependency.kind == AwareInterfaceDependencyKind.render_component_package
        and dependency.package_name.strip()
    )
    if not render_component_package_names:
        return ()

    package_snapshots: list[InterfaceRenderComponentPackageSnapshot] = []
    for package_name in render_component_package_names:
        spec_path = _resolve_render_component_toml_path(
            repo_root=repo_root,
            workspace_root=workspace_root,
            package_name=package_name,
        )
        package_root = spec_path.parent.resolve()
        spec = load_aware_render_component_toml_spec(toml_path=spec_path)
        if (spec.render_component.package_name or "").strip() != package_name:
            raise ValueError(
                "Declared render_component_package dependency package_name mismatch: "
                + f"declared={package_name!r} manifest={spec.render_component.package_name!r} path={spec_path}"
            )
        source_files = _collect_authored_source_files(
            package_root=package_root,
            sources_dir=spec.build.sources_dir,
            include_paths=spec.build.include_paths,
            exclude_paths=spec.build.exclude_paths,
            rel_base=package_root,
            label="render component [build].sources_dir",
        )
        package_snapshots.append(
            InterfaceRenderComponentPackageSnapshot(
                spec_path=spec_path,
                package_root=package_root,
                spec=spec,
                source_files=source_files,
            )
        )
    return tuple(
        sorted(
            package_snapshots,
            key=lambda item: item.spec.render_component.package_name.casefold(),
        )
    )


def _load_attention_package_snapshot(
    *,
    package_name: str,
    runtime_artifact_path: Path,
) -> InterfaceAttentionPackageSnapshot:
    try:
        raw_payload = json.loads(
            runtime_artifact_path.read_text(encoding="utf-8") or "{}"
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse attention compile artifact at {runtime_artifact_path}: {exc}"
        ) from exc
    if not isinstance(raw_payload, dict):
        raise ValueError(
            f"Attention compile artifact must be a JSON object: {runtime_artifact_path}"
        )

    payload_package_name = str(raw_payload.get("package_name") or "").strip()
    if payload_package_name != package_name:
        raise ValueError(
            "Attention compile artifact package_name mismatch: "
            + f"declared={package_name!r} artifact={payload_package_name!r} path={runtime_artifact_path}"
        )

    layout_rows = raw_payload.get("layout_ontology")
    if not isinstance(layout_rows, list):
        raise ValueError(
            f"Attention compile artifact is missing layout_ontology list: {runtime_artifact_path}"
        )

    layouts: list[InterfaceAttentionLayoutSnapshot] = []
    for index, layout_row in enumerate(layout_rows):
        if not isinstance(layout_row, dict):
            raise ValueError(
                f"Attention compile artifact layout_ontology[{index}] must be an object: {runtime_artifact_path}"
            )
        layout_key = str(layout_row.get("layout_key") or "").strip()
        layout_config_id = str(layout_row.get("layout_config_id") or "").strip()
        title = str(layout_row.get("title") or "").strip()
        if not layout_key or not layout_config_id or not title:
            raise ValueError(
                "Attention compile artifact layout rows must declare layout_key, layout_config_id, and title: "
                + f"{runtime_artifact_path}#{index}"
            )
        sections_payload = layout_row.get("sections")
        if not isinstance(sections_payload, list):
            raise ValueError(
                f"Attention compile artifact layout_ontology[{index}].sections must be a list: {runtime_artifact_path}"
            )
        sections: list[InterfaceAttentionLayoutSectionSnapshot] = []
        for section_index, section_row in enumerate(sections_payload):
            if not isinstance(section_row, dict):
                raise ValueError(
                    "Attention compile artifact section rows must be objects: "
                    + f"{runtime_artifact_path}#{index}:{section_index}"
                )
            section_key = str(section_row.get("section_key") or "").strip()
            layout_section_config_id = str(
                section_row.get("layout_config_section_config_id") or ""
            ).strip()
            section_config_id = str(section_row.get("section_config_id") or "").strip()
            section_title = str(section_row.get("title") or "").strip()
            if (
                not section_key
                or not layout_section_config_id
                or not section_config_id
                or not section_title
            ):
                raise ValueError(
                    "Attention compile artifact section rows must declare section_key, "
                    + "layout_config_section_config_id, section_config_id, and title: "
                    + f"{runtime_artifact_path}#{index}:{section_index}"
                )
            order = section_row.get("order")
            flex = section_row.get("flex")
            is_visible = section_row.get("is_visible")
            if not isinstance(order, int):
                raise ValueError(
                    "Attention compile artifact section order must be an int: "
                    + f"{runtime_artifact_path}#{index}:{section_index}"
                )
            if not isinstance(flex, (int, float)):
                raise ValueError(
                    "Attention compile artifact section flex must be numeric: "
                    + f"{runtime_artifact_path}#{index}:{section_index}"
                )
            if not isinstance(is_visible, bool):
                raise ValueError(
                    "Attention compile artifact section is_visible must be a bool: "
                    + f"{runtime_artifact_path}#{index}:{section_index}"
                )
            description_raw = section_row.get("description")
            section_description = (
                description_raw.strip()
                if isinstance(description_raw, str) and description_raw.strip()
                else None
            )
            sections.append(
                InterfaceAttentionLayoutSectionSnapshot(
                    layout_config_section_config_id=UUID(layout_section_config_id),
                    section_config_id=UUID(section_config_id),
                    section_key=section_key,
                    title=section_title,
                    description=section_description,
                    order=order,
                    flex=float(flex),
                    is_visible=is_visible,
                )
            )
        if "territories" in layout_row:
            raise ValueError(
                "Attention compile artifact territories are no longer supported: "
                + f"{runtime_artifact_path}#{index}"
            )
        description_raw = layout_row.get("description")
        layout_description = (
            description_raw.strip()
            if isinstance(description_raw, str) and description_raw.strip()
            else None
        )
        frame_mode = str(layout_row.get("frame_mode") or "").strip()
        if not frame_mode:
            raise ValueError(
                f"Attention compile artifact layout rows must declare frame_mode: {runtime_artifact_path}#{index}"
            )
        layouts.append(
            InterfaceAttentionLayoutSnapshot(
                layout_config_id=UUID(layout_config_id),
                layout_key=layout_key,
                title=title,
                description=layout_description,
                frame_mode=frame_mode,
                sections=tuple(
                    sorted(
                        sections,
                        key=lambda item: (item.order, item.section_key.casefold()),
                    )
                ),
            )
        )

    return InterfaceAttentionPackageSnapshot(
        package_name=package_name,
        runtime_artifact_path=runtime_artifact_path,
        layouts=tuple(sorted(layouts, key=lambda item: item.layout_key.casefold())),
    )


def _resolve_attention_toml_path(
    *, repo_root: Path, workspace_root: Path, package_name: str
) -> Path:
    workspace_direct_path = (
        workspace_root / "attentions" / package_name / "aware.attention.toml"
    ).resolve()
    if workspace_direct_path.exists():
        return workspace_direct_path
    matches: list[Path] = []
    for path in _declared_workspace_package_manifest_paths(
        repo_root=repo_root,
        workspace_root=workspace_root,
        directory_name="attentions",
        filename="aware.attention.toml",
    ):
        if not path.is_file():
            continue
        try:
            spec = load_aware_attention_toml_spec(toml_path=path)
        except Exception:
            continue
        manifest_package_name = (spec.attention.package_name or "").strip()
        if manifest_package_name.casefold() == package_name.casefold():
            matches.append(path.resolve())
    workspace_local_matches = _select_workspace_local_matches(
        workspace_root=workspace_root,
        matches=matches,
    )
    if len(workspace_local_matches) == 1:
        return workspace_local_matches[0]
    if len(workspace_local_matches) > 1:
        raise ValueError(
            "Multiple workspace-local aware.attention.toml packages matched the declared "
            + f"attention_package {package_name!r} under {workspace_root}: "
            + ", ".join(path.as_posix() for path in workspace_local_matches)
        )
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(
            "Multiple aware.attention.toml packages matched the declared attention_package "
            + f"{package_name!r}: {', '.join(path.as_posix() for path in matches)}"
        )
    raise FileNotFoundError(
        "Declared attention_package "
        + f"{package_name!r} does not resolve under the consumer Workspace or its declared Workspace dependencies"
    )


def _resolve_experience_toml_path(
    *,
    repo_root: Path,
    workspace_root: Path,
    package_name: str,
) -> Path:
    workspace_direct_path = (
        workspace_root / "experiences" / package_name / "aware.experience.toml"
    ).resolve()
    if workspace_direct_path.exists():
        return workspace_direct_path
    matches = sorted(
        path.resolve()
        for path in _declared_workspace_package_manifest_paths(
            repo_root=repo_root,
            workspace_root=workspace_root,
            directory_name="experiences",
            filename="aware.experience.toml",
        )
        if path.is_file()
        and (
            load_aware_experience_toml_spec(toml_path=path).experience.package_name
            or ""
        )
        .strip()
        .casefold()
        == package_name.casefold()
    )
    workspace_local_matches = _select_workspace_local_matches(
        workspace_root=workspace_root,
        matches=matches,
    )
    if len(workspace_local_matches) == 1:
        return workspace_local_matches[0]
    if len(workspace_local_matches) > 1:
        raise ValueError(
            "Multiple workspace-local aware.experience.toml packages matched the declared "
            + f"experience_package {package_name!r} under {workspace_root}: "
            + ", ".join(path.as_posix() for path in workspace_local_matches)
        )
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(
            "Multiple aware.experience.toml packages matched the declared experience_package "
            + f"{package_name!r}: {', '.join(path.as_posix() for path in matches)}"
        )
    raise FileNotFoundError(
        "Declared experience_package "
        + f"{package_name!r} does not resolve under the consumer Workspace or its declared Workspace dependencies"
    )


def _resolve_pane_toml_path(
    *,
    repo_root: Path,
    workspace_root: Path,
    package_name: str,
) -> Path:
    workspace_direct_path = (
        workspace_root / "panes" / package_name / "aware.pane.toml"
    ).resolve()
    if workspace_direct_path.exists():
        return workspace_direct_path
    matches_by_path: dict[Path, Path] = {}
    for path in _declared_workspace_package_manifest_paths(
        repo_root=repo_root,
        workspace_root=workspace_root,
        directory_name="panes",
        filename="aware.pane.toml",
    ):
        if (
            load_aware_pane_toml_spec(toml_path=path).pane.package_name or ""
        ).strip().casefold() != package_name.casefold():
            continue
        resolved_path = path.resolve()
        matches_by_path[resolved_path] = resolved_path
    matches = sorted(matches_by_path.values())
    workspace_local_matches = _select_workspace_local_matches(
        workspace_root=workspace_root,
        matches=matches,
    )
    if len(workspace_local_matches) == 1:
        return workspace_local_matches[0]
    if len(workspace_local_matches) > 1:
        raise ValueError(
            "Multiple workspace-local aware.pane.toml packages matched the declared "
            + f"pane_package {package_name!r} under {workspace_root}: "
            + ", ".join(path.as_posix() for path in workspace_local_matches)
        )
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(
            "Multiple aware.pane.toml packages matched the declared pane_package "
            + f"{package_name!r}: {', '.join(path.as_posix() for path in matches)}"
        )
    raise FileNotFoundError(
        "Declared pane_package "
        + f"{package_name!r} does not resolve to an aware.pane.toml package under the consumer Workspace "
        + f"or its declared Workspace dependencies: consumer={workspace_root}"
    )


def _resolve_render_component_toml_path(
    *,
    repo_root: Path,
    workspace_root: Path,
    package_name: str,
) -> Path:
    workspace_direct_path = (
        workspace_root
        / "render_components"
        / package_name
        / "aware.render_component.toml"
    ).resolve()
    if workspace_direct_path.exists():
        return workspace_direct_path
    matches = sorted(
        path.resolve()
        for path in _declared_workspace_package_manifest_paths(
            repo_root=repo_root,
            workspace_root=workspace_root,
            directory_name="render_components",
            filename="aware.render_component.toml",
        )
        if path.is_file()
        and (
            load_aware_render_component_toml_spec(
                toml_path=path
            ).render_component.package_name
            or ""
        )
        .strip()
        .casefold()
        == package_name.casefold()
    )
    workspace_local_matches = _select_workspace_local_matches(
        workspace_root=workspace_root,
        matches=matches,
    )
    if len(workspace_local_matches) == 1:
        return workspace_local_matches[0]
    if len(workspace_local_matches) > 1:
        raise ValueError(
            "Multiple workspace-local aware.render_component.toml packages matched the declared "
            + f"render_component_package {package_name!r} under {workspace_root}: "
            + ", ".join(path.as_posix() for path in workspace_local_matches)
        )
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(
            "Multiple aware.render_component.toml packages matched the declared "
            + f"render_component_package {package_name!r}: "
            + ", ".join(path.as_posix() for path in matches)
        )
    raise FileNotFoundError(
        "Declared render_component_package "
        + f"{package_name!r} does not resolve under the consumer Workspace or its declared Workspace dependencies"
    )


def _compile_attention_workspace(
    *, toml_path: Path, repo_root: Path, emit_compile_plan: bool
) -> None:
    attention_runtime_root = (repo_root / "modules" / "attention" / "runtime").resolve()
    if str(attention_runtime_root) not in sys.path:
        sys.path.insert(0, str(attention_runtime_root))
    compile_module = importlib.import_module("aware_attention.compile")
    compile_module.compile_attention_workspace(
        toml_path=toml_path,
        repo_root=repo_root,
        emit_compile_plan=emit_compile_plan,
    )


def _discover_workspace_pane_packages(
    *,
    repo_root: Path,
    workspace_root: Path,
) -> tuple[InterfacePanePackageSnapshot, ...]:
    spec_paths = _workspace_pane_package_spec_paths(
        repo_root=repo_root,
        workspace_root=workspace_root,
    )

    pane_packages: list[InterfacePanePackageSnapshot] = []
    for spec_path in spec_paths:
        package_root = spec_path.parent.resolve()
        _assert_within(
            base=repo_root, candidate=package_root, label="workspace pane package"
        )
        spec = load_aware_pane_toml_spec(toml_path=spec_path)
        source_files = _collect_authored_source_files(
            package_root=package_root,
            sources_dir=spec.build.sources_dir,
            include_paths=spec.build.include_paths,
            exclude_paths=spec.build.exclude_paths,
            rel_base=repo_root,
            label="pane [build].sources_dir",
        )
        experience_packages = _load_pane_package_experience_packages(
            repo_root=repo_root,
            workspace_root=workspace_root,
            spec=spec,
        )
        render_spec_files = _collect_pane_render_spec_files(
            package_root=package_root,
            rel_base=repo_root,
        )
        pane_packages.append(
            InterfacePanePackageSnapshot(
                spec_path=spec_path,
                package_root=package_root,
                spec=spec,
                source_files=source_files,
                experience_packages=experience_packages,
                render_spec_files=render_spec_files,
            )
        )
    return tuple(
        sorted(
            pane_packages,
            key=lambda item: (
                item.spec.pane.pane_name.casefold(),
                item.spec_path.relative_to(repo_root).as_posix(),
            ),
        )
    )


def _merge_pane_package_snapshots(
    *groups: tuple[InterfacePanePackageSnapshot, ...],
) -> tuple[InterfacePanePackageSnapshot, ...]:
    merged_by_path: dict[Path, InterfacePanePackageSnapshot] = {}
    for group in groups:
        for package in group:
            merged_by_path.setdefault(package.spec_path.resolve(), package)
    return tuple(
        sorted(
            merged_by_path.values(),
            key=lambda item: (
                item.spec.pane.pane_name.casefold(),
                item.spec_path.as_posix(),
            ),
        )
    )


def _workspace_pane_package_spec_paths(
    *,
    repo_root: Path,
    workspace_root: Path,
) -> tuple[Path, ...]:
    spec_paths: set[Path] = set(
        _local_package_manifest_paths(
            root=workspace_root,
            directory_name="panes",
            filename="aware.pane.toml",
        )
    )
    for module_root in _workspace_module_roots(workspace_root=workspace_root):
        spec_paths.update(
            _local_package_manifest_paths(
                root=module_root,
                directory_name="panes",
                filename="aware.pane.toml",
            )
        )
    for dependency_workspace_root in _local_dependency_workspace_roots(
        repo_root=repo_root,
        workspace_root=workspace_root,
    ):
        spec_paths.update(
            _selected_workspace_pane_package_spec_paths(
                workspace_root=dependency_workspace_root,
            )
        )
    return tuple(sorted(spec_paths))


def _local_dependency_workspace_roots(
    *,
    repo_root: Path,
    workspace_root: Path,
) -> tuple[Path, ...]:
    declaring_workspace_root = _nearest_workspace_manifest_root(start=workspace_root)
    if declaring_workspace_root is None:
        return ()
    workspace_toml_path = declaring_workspace_root / "aware.workspace.toml"
    try:
        payload = tomllib.loads(workspace_toml_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return ()

    dependencies = payload.get("workspace", {}).get("dependencies", ())
    if not isinstance(dependencies, list):
        return ()

    roots: list[Path] = []
    seen: set[Path] = set()
    for dependency in dependencies:
        if not isinstance(dependency, Mapping):
            continue
        if str(dependency.get("kind") or "").strip() != "workspace":
            continue
        workspace_id = _local_workspace_dependency_id(dependency=dependency)
        if not workspace_id:
            continue
        for candidate in _local_workspace_dependency_candidates(
            repo_root=repo_root,
            declaring_workspace_root=declaring_workspace_root,
            workspace_id=workspace_id,
        ):
            if candidate == declaring_workspace_root.resolve():
                continue
            if candidate in seen or not (candidate / "aware.workspace.toml").is_file():
                continue
            seen.add(candidate)
            roots.append(candidate)
            break
    return tuple(roots)


def _local_workspace_dependency_id(*, dependency: Mapping[str, object]) -> str | None:
    source = str(dependency.get("source") or "").strip()
    prefix = "workspace://"
    if source.startswith(prefix):
        workspace_id = source.removeprefix(prefix).strip()
        return workspace_id or None
    workspace_id = str(dependency.get("id") or "").strip()
    return workspace_id or None


def _local_workspace_dependency_candidates(
    *,
    repo_root: Path,
    declaring_workspace_root: Path,
    workspace_id: str,
) -> tuple[Path, ...]:
    candidates: list[Path] = []

    def add(candidate: Path) -> None:
        resolved = candidate.resolve()
        if resolved not in candidates:
            candidates.append(resolved)

    resolved_repo_root = repo_root.resolve()
    add(resolved_repo_root / "workspaces" / workspace_id)
    if resolved_repo_root.name == "workspaces":
        add(resolved_repo_root / workspace_id)
    if resolved_repo_root.parent.name == "workspaces":
        add(resolved_repo_root.parent / workspace_id)

    resolved_declaring_workspace_root = declaring_workspace_root.resolve()
    if resolved_declaring_workspace_root.parent.name == "workspaces":
        add(resolved_declaring_workspace_root.parent / workspace_id)

    return tuple(candidates)


def _selected_workspace_pane_package_spec_paths(
    *,
    workspace_root: Path,
) -> tuple[Path, ...]:
    return _selected_workspace_manifest_paths(
        workspace_root=workspace_root,
        field_name="panes",
        filename="aware.pane.toml",
        label="dependency workspace pane manifest",
    )


def _selected_workspace_manifest_paths(
    *,
    workspace_root: Path,
    field_name: str,
    filename: str,
    label: str,
) -> tuple[Path, ...]:
    workspace_toml_path = workspace_root / "aware.workspace.toml"
    try:
        payload = tomllib.loads(workspace_toml_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return ()

    manifest_paths = payload.get("workspace", {}).get(field_name, ())
    if not isinstance(manifest_paths, list):
        return ()

    spec_paths: list[Path] = []
    for raw_path in manifest_paths:
        if not isinstance(raw_path, str) or not raw_path.strip():
            continue
        candidate = (workspace_root / raw_path).resolve()
        if candidate.name != filename or not candidate.is_file():
            continue
        _assert_within(
            base=workspace_root,
            candidate=candidate,
            label=label,
        )
        spec_paths.append(candidate)
    return tuple(sorted(spec_paths))


def _workspace_module_roots(*, workspace_root: Path) -> tuple[Path, ...]:
    modules_workspace_root = _containing_modules_workspace_root(
        workspace_root=workspace_root
    )
    if modules_workspace_root is None:
        return ()
    modules_root = modules_workspace_root / "modules"
    return tuple(
        sorted(child.resolve() for child in modules_root.iterdir() if child.is_dir())
    )


def _containing_modules_workspace_root(*, workspace_root: Path) -> Path | None:
    resolved_workspace_root = workspace_root.resolve()
    for candidate in (resolved_workspace_root, *resolved_workspace_root.parents):
        if (candidate / "modules").is_dir():
            return candidate
    return None


def _nearest_workspace_manifest_root(*, start: Path) -> Path | None:
    resolved_start = start.resolve()
    for candidate in (resolved_start, *resolved_start.parents):
        if (candidate / "aware.workspace.toml").is_file():
            return candidate
    return None


def _resolve_compile_time_dependency_catalog_roots(
    *,
    repo_root: Path,
    workspace_root: Path,
) -> tuple[InterfaceDependencyCatalogRootSnapshot, ...]:
    roots: list[InterfaceDependencyCatalogRootSnapshot] = []

    def add(root: Path, source_kind: str) -> None:
        resolved = root.resolve()
        if any(existing.root == resolved for existing in roots):
            return
        roots.append(
            InterfaceDependencyCatalogRootSnapshot(
                root=resolved,
                source_kind=source_kind,
            )
        )

    add(repo_root, "kernel_dependency_artifact_root")
    for dependency_workspace_root in _local_dependency_workspace_roots(
        repo_root=repo_root,
        workspace_root=workspace_root,
    ):
        add(
            dependency_workspace_root,
            "declared_workspace_dependency_artifact_root",
        )
    add(workspace_root, "workspace_authoring_artifact_root")
    modules_workspace_root = _containing_modules_workspace_root(
        workspace_root=workspace_root
    )
    if modules_workspace_root is not None:
        add(modules_workspace_root, "workspace_module_dependency_artifact_root")
    return tuple(roots)


def _local_package_manifest_paths(
    *,
    root: Path,
    directory_name: str,
    filename: str,
) -> tuple[Path, ...]:
    search_root = (root / directory_name).resolve()
    if not search_root.exists():
        return ()
    if not search_root.is_dir():
        raise NotADirectoryError(
            f"Local package root must be a directory: {search_root}"
        )
    return tuple(
        sorted(path.resolve() for path in search_root.rglob(filename) if path.is_file())
    )


def _declared_workspace_package_manifest_paths(
    *,
    repo_root: Path,
    workspace_root: Path,
    directory_name: str,
    filename: str,
) -> tuple[Path, ...]:
    declared_workspace_roots = (
        workspace_root.resolve(),
        *_local_dependency_workspace_roots(
            repo_root=repo_root,
            workspace_root=workspace_root,
        ),
    )
    manifests: set[Path] = set()
    for declared_workspace_root in declared_workspace_roots:
        manifests.update(
            _local_package_manifest_paths(
                root=declared_workspace_root,
                directory_name=directory_name,
                filename=filename,
            )
        )
        manifests.update(
            _workspace_module_package_manifest_paths(
                workspace_root=declared_workspace_root,
                filename=filename,
            )
        )
    return tuple(sorted(manifests))


def _workspace_module_package_manifest_paths(
    *,
    workspace_root: Path,
    filename: str,
) -> tuple[Path, ...]:
    manifests: set[Path] = set()
    for module_root in _workspace_module_roots(workspace_root=workspace_root):
        module_toml_path = module_root / "aware.module.toml"
        if not module_toml_path.is_file():
            continue
        try:
            payload = tomllib.loads(module_toml_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ValueError(
                f"Failed to load module package registry {module_toml_path}: {exc}"
            ) from exc
        packages = payload.get("packages", ())
        if not isinstance(packages, list):
            raise ValueError(
                f"Module package registry must declare [[packages]] rows: {module_toml_path}"
            )
        for package in packages:
            if not isinstance(package, Mapping):
                raise ValueError(
                    f"Module package registry row must be a table: {module_toml_path}"
                )
            manifest = str(package.get("manifest") or "").strip()
            if not manifest:
                continue
            candidate = (module_root / manifest).resolve()
            _assert_within(
                base=module_root,
                candidate=candidate,
                label="module package manifest",
            )
            if candidate.name != filename:
                continue
            if not candidate.is_file():
                raise FileNotFoundError(
                    "Module package manifest declared by aware.module.toml was not found: "
                    + f"module={module_root.name!r} manifest={manifest!r}"
                )
            manifests.add(candidate)
    return tuple(sorted(manifests))


def _collect_authored_source_files(
    *,
    package_root: Path,
    sources_dir: str,
    include_paths: list[str],
    exclude_paths: list[str],
    rel_base: Path,
    label: str,
) -> tuple[Path, ...]:
    sources_root = (package_root / sources_dir).resolve()
    _assert_within(base=package_root, candidate=sources_root, label=label)
    if not sources_root.exists():
        raise FileNotFoundError(f"Authored sources_dir does not exist: {sources_root}")
    if not sources_root.is_dir():
        raise NotADirectoryError(
            f"Authored sources_dir must be a directory: {sources_root}"
        )

    files_by_rel: dict[str, Path] = {}
    for include in include_paths:
        pattern = (include or "").strip()
        if not pattern:
            continue
        for candidate in sources_root.glob(pattern):
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            _assert_within(base=sources_root, candidate=resolved, label="include_paths")
            _assert_within(base=rel_base, candidate=resolved, label="authored source")
            rel_from_sources = resolved.relative_to(sources_root).as_posix()
            if _is_excluded(rel_path=rel_from_sources, exclude_patterns=exclude_paths):
                continue
            rel_from_base = resolved.relative_to(rel_base).as_posix()
            files_by_rel[rel_from_base] = Path(rel_from_base)
    return tuple(files_by_rel[key] for key in sorted(files_by_rel))


def _collect_pane_render_spec_files(
    *,
    package_root: Path,
    rel_base: Path,
) -> tuple[Path, ...]:
    patterns = (
        "*.render_spec.json",
        "render_specs/*.render_spec.json",
    )
    files_by_rel: dict[str, Path] = {}
    for pattern in patterns:
        for candidate in package_root.glob(pattern):
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            _assert_within(
                base=package_root, candidate=resolved, label="pane render_spec"
            )
            _assert_within(base=rel_base, candidate=resolved, label="pane render_spec")
            rel_from_base = resolved.relative_to(rel_base).as_posix()
            files_by_rel[rel_from_base] = Path(rel_from_base)
    return tuple(files_by_rel[key] for key in sorted(files_by_rel))


def _resolve_repo_root(*, start: Path) -> Path:
    cursor = start.resolve()
    for candidate in [cursor, *cursor.parents]:
        if (candidate / "aware.environment.toml").exists():
            return candidate
    return cursor


def _resolve_workspace_root(*, start: Path, fallback: Path) -> Path:
    cursor = start.resolve()
    for candidate in [cursor, *cursor.parents]:
        if any(
            (candidate / directory_name).is_dir()
            for directory_name in _LOCAL_WORKSPACE_PACKAGE_DIRS
        ):
            return candidate
    return fallback.resolve()


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}"
    )


def _select_workspace_local_matches(
    *, workspace_root: Path, matches: list[Path]
) -> tuple[Path, ...]:
    resolved_workspace_root = workspace_root.resolve()
    return tuple(
        path
        for path in matches
        if resolved_workspace_root == path.parent
        or resolved_workspace_root in path.parents
    )


def _is_excluded(*, rel_path: str, exclude_patterns: list[str]) -> bool:
    token = PurePosixPath(rel_path)
    for raw_pattern in exclude_patterns:
        pattern = (raw_pattern or "").strip()
        if pattern and token.match(pattern):
            return True
    return False


__all__ = [
    "InterfaceAttentionLayoutSectionSnapshot",
    "InterfaceAttentionLayoutSnapshot",
    "InterfaceAttentionPackageSnapshot",
    "InterfacePanePackageSnapshot",
    "InterfaceWorkspace",
    "InterfaceWorkspaceSnapshot",
]
