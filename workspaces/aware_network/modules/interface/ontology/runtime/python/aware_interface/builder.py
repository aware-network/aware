from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, replace
from hashlib import sha256
import json
from pathlib import Path
import tomllib
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid5
import warnings

import msgpack
from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_interface.pane_render import (
    lower_pane_render_spec_to_payload,
    parse_pane_render_specs,
)
from aware_attention_ontology.stable_ids import (
    stable_layout_config_id,
    stable_layout_config_section_config_id,
)
from aware_experience.compiler.models import (
    ExperienceProjectionExperienceOwnership,
    ExperienceProjectionViewOwnership,
    ExperienceProjectionViewInvocationActionOwnership,
)
from aware_experience.projection.compiler import (
    load_projection_experience_ownership_from_sources,
)
from aware_experience.view_contracts import load_view_state_model_contracts_from_sources
from aware_experience.stable_ids import (
    stable_projection_experience_id,
    stable_projection_experience_view_id,
    stable_projection_experience_view_invocation_action_config_id,
)
from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_id,
    stable_api_capability_id,
    stable_api_id,
    stable_api_view_capability_endpoint_id,
    stable_api_view_id,
)
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
    InterfacePaneConfigBundle,
    InterfacePaneProjectionExperienceViewBundle,
    InterfacePaneSectionMountBundle,
    InterfacePaneViewInvocationActionBundle,
    InterfaceWindowConfigBundle,
    InterfaceWindowConfigLayoutBundle,
    InterfaceWindowLayoutSectionBundle,
)
from aware_interface_ontology.stable_ids import (
    stable_interface_config_id,
    stable_interface_config_pane_config_id,
    stable_interface_config_pane_config_section_config_id,
    stable_interface_package_id,
    stable_interface_config_window_config_id,
    stable_pane_config_id,
    stable_pane_package_id,
    stable_pane_action_binding_id,
    stable_pane_input_binding_id,
    stable_pane_render_node_id,
    stable_pane_render_spec_id,
    stable_pane_renderer_capability_requirement_id,
    stable_pane_state_binding_id,
    stable_pane_style_token_ref_id,
    stable_window_config_id,
    stable_window_config_layout_config_id,
)
from aware_interface_ontology.render.pane_render_enums import (
    PaneActionEvent,
    PaneRenderNodeKind,
    PaneRenderSemanticRole,
    PaneStateBindingTargetProperty,
    PaneStateBindingTransform,
)
from aware_interface.manifest import AwareInterfaceDependencyKind
from aware_meta.fqn_resolver import authored_ref_from_fqn
from aware_meta.runtime.package_index import load_meta_runtime_package_projection_index
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_id,
    stable_object_config_graph_identity_id,
    stable_object_projection_graph_id,
    stable_object_projection_graph_identity_id,
    stable_object_projection_graph_observable_id,
)
from .compiler import (
    InterfaceOwnership,
    InterfacePaneMountOwnership,
    InterfacePaneOwnership,
    InterfaceSourceOwnership,
    InterfaceWindowLayoutOwnership,
    load_interface_ownership_from_sources,
)
from .workspace import (
    InterfaceAttentionLayoutSnapshot,
    InterfaceExperiencePackageSnapshot,
    InterfacePanePackageSnapshot,
    InterfaceWorkspaceSnapshot,
)


@dataclass(frozen=True, slots=True)
class InterfaceDependencyOwnership:
    package_name: str
    version_number: int | None
    kind: str


@dataclass(frozen=True, slots=True)
class InterfaceCompilePlan:
    schema_version: int
    package_name: str
    fqn_prefix: str
    source_files: tuple[str, ...]
    dependencies: tuple[InterfaceDependencyOwnership, ...]
    pane_ownership: tuple[InterfacePaneOwnership, ...]
    interface_ownership: tuple[InterfaceOwnership, ...]


@dataclass(frozen=True, slots=True)
class InterfaceCompilePlanArtifact:
    path: Path
    relpath: str
    hash_sha256: str


@dataclass(frozen=True, slots=True)
class InterfaceConfigBundleArtifact:
    path: Path
    relpath: str
    hash_sha256: str


@dataclass(frozen=True, slots=True)
class InterfaceDartPaneRegistrarBundleArtifact:
    path: Path
    relpath: str
    hash_sha256: str


@dataclass(frozen=True, slots=True)
class InterfacePaneRenderSpecMaterializationArtifact:
    path: Path
    relpath: str
    hash_sha256: str


class PaneRenderSpecCompatibilityWarning(UserWarning):
    """Warns when pane render specs are loaded from JSON compatibility sources."""


_PANE_RENDER_SPEC_MATERIALIZATION_SCHEMA_VERSION = 2
_PANE_RENDER_SPEC_MATERIALIZATION_KIND = (
    "aware.interface.pane-render-spec.materialization.v1"
)


def build_interface_compile_plan(
    *, snapshot: InterfaceWorkspaceSnapshot
) -> InterfaceCompilePlan:
    package_name = (snapshot.spec.interface.package_name or "").strip()
    if not package_name:
        raise ValueError(
            "Interface package_name must be non-empty for compile planning"
        )
    fqn_prefix = (snapshot.spec.interface.fqn_prefix or "").strip()
    if not fqn_prefix:
        raise ValueError("Interface fqn_prefix must be non-empty for compile planning")

    interface_ownership = load_interface_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
    )
    external_pane_ownership = _load_workspace_pane_ownership(snapshot=snapshot)
    ownership = _merge_interface_source_ownership(
        interface_ownership=interface_ownership,
        external_pane_ownership=external_pane_ownership,
    )
    pane_experience_catalogs = _load_pane_experience_catalogs(snapshot=snapshot)
    _validate_interface_ownership(
        ownership=ownership,
        attention_layout_catalog=_load_attention_layout_catalog(snapshot=snapshot),
        pane_experience_catalogs=pane_experience_catalogs,
    )

    dependencies = tuple(
        InterfaceDependencyOwnership(
            package_name=item.package_name,
            version_number=item.version_number,
            kind=(
                item.kind.value
                if isinstance(item.kind, AwareInterfaceDependencyKind)
                else str(item.kind)
            ),
        )
        for item in snapshot.spec.dependencies
    )

    return InterfaceCompilePlan(
        schema_version=1,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        source_files=tuple(
            sorted(
                path.as_posix()
                for path in (
                    *snapshot.source_files,
                    *snapshot.pane_source_files,
                    *snapshot.pane_render_spec_files,
                )
            )
        ),
        dependencies=dependencies,
        pane_ownership=ownership.pane_ownership,
        interface_ownership=ownership.interface_ownership,
    )


def _load_workspace_pane_ownership(
    *, snapshot: InterfaceWorkspaceSnapshot
) -> tuple[InterfacePaneOwnership, ...]:
    pane_ownership: list[InterfacePaneOwnership] = []
    for pane_package in snapshot.pane_packages:
        package_ownership = load_interface_ownership_from_sources(
            package_root=snapshot.repo_root,
            source_files=pane_package.source_files,
        )
        if package_ownership.interface_ownership:
            raise ValueError(
                "Workspace pane packages must not declare interface definitions; "
                + f"found in {pane_package.spec_path}"
            )
        pane_ownership.extend(package_ownership.pane_ownership)
    return tuple(pane_ownership)


def _merge_interface_source_ownership(
    *,
    interface_ownership: InterfaceSourceOwnership,
    external_pane_ownership: tuple[InterfacePaneOwnership, ...],
) -> InterfaceSourceOwnership:
    pane_by_name: dict[str, InterfacePaneOwnership] = {}
    for pane in (*interface_ownership.pane_ownership, *external_pane_ownership):
        pane_key = pane.name.casefold()
        if pane_key in pane_by_name:
            existing = pane_by_name[pane_key]
            raise ValueError(
                "Duplicate pane declaration "
                + f"{pane.name!r} across authored Interface and pane package sources: "
                + f"{existing.source_path} vs {pane.source_path}"
            )
        pane_by_name[pane_key] = pane
    return InterfaceSourceOwnership(
        pane_ownership=tuple(
            sorted(
                pane_by_name.values(), key=lambda item: (item.name, item.source_path)
            )
        ),
        interface_ownership=interface_ownership.interface_ownership,
    )


def emit_interface_compile_plan_artifact(
    *,
    plan: InterfaceCompilePlan,
    runtime_package_dir: Path,
    repo_root: Path,
) -> InterfaceCompilePlanArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = _encode_plan(plan=plan)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (runtime_package_dir / "interface.compile_plan.json").resolve()
    _ = artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return InterfaceCompilePlanArtifact(
        path=artifact_path, relpath=relpath, hash_sha256=digest
    )


@dataclass(frozen=True, slots=True)
class ProjectionIdentityTruth:
    object_projection_graph_identity_id: UUID
    projection_name: str


@dataclass(frozen=True, slots=True)
class ApiViewActionTruth:
    action_key: str
    endpoint_ref: str
    api_view_capability_endpoint_id: UUID | None = None
    api_capability_endpoint_id: UUID | None = None
    sdk_operation_api_view_capability_endpoint_id: UUID | None = None
    sdk_operation_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ApiViewStateTruth:
    view_ref: str
    state_model_ref: str
    state_model_id: UUID
    action_endpoints_by_key: Mapping[str, ApiViewActionTruth] = field(
        default_factory=dict
    )


@dataclass(frozen=True, slots=True)
class _ApiCompilePlanViewTruth:
    view_ref: str
    view_name: str
    observable_ref: str | None = None


@dataclass(frozen=True, slots=True)
class _ProjectionExperienceViewTruth:
    projection_experience_id: UUID
    projection_experience_view_id: UUID
    object_projection_graph_observable_id: UUID
    object_projection_graph_identity_id: UUID
    projection_view_key: str
    state_model_id: UUID
    state_model_ref: str
    state_attribute_ids_by_ref: Mapping[str, UUID]
    api_view_ref: str | None = None
    api_view_truth: ApiViewStateTruth | None = None
    invocation_actions: tuple[
        ExperienceProjectionViewInvocationActionOwnership, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class _ProjectionExperienceOwnershipTruth:
    package_name: str
    source_path: str
    ownership: ExperienceProjectionExperienceOwnership
    view_state_model_ids_by_ref: Mapping[str, UUID]
    view_state_attribute_ids_by_ref: Mapping[str, Mapping[str, UUID]]
    api_view_state_by_ref: Mapping[str, ApiViewStateTruth]


@dataclass(frozen=True, slots=True)
class _PanePackageIdentityTruth:
    pane_package_id: UUID
    pane_package_name: str


@dataclass(frozen=True, slots=True)
class _InterfaceRuntimeLayoutTruth:
    layout_config_id: UUID
    layout_key: str
    label: str
    is_default: bool


@dataclass(frozen=True, slots=True)
class _InterfaceRuntimeSectionRepresentationTruth:
    representation_id: UUID
    window_key: str
    layout_key: str
    section_key: str
    pane_name: str
    pane_kind: str
    label: str
    observable_id: UUID
    view_ref: str
    projection_view_key: str
    api_view_ref: str | None = None
    api_view_state_model_ref: str | None = None


@dataclass(frozen=True, slots=True)
class _DartPaneRegistrarTruth:
    pane_name: str
    pane_package_name: str
    library: str
    symbol: str


@dataclass(frozen=True, slots=True)
class _DartRenderComponentRegistrarTruth:
    render_component_package_name: str
    library: str
    symbol: str


@dataclass(frozen=True, slots=True)
class _DartViewModelRegistryTruth:
    package_name: str
    library: str
    decoders_symbol: str


@dataclass(frozen=True, slots=True)
class _DartApiViewStateDecoderTruth:
    package_name: str
    library: str
    class_name: str
    decoder_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _DartPaneRenderSpecTruth:
    source_path: str
    source_kind: str
    pane_name: str
    pane_kind: str
    view_ref: str
    projection_view_key: str
    payload: Mapping[str, object]


def build_interface_config_bundle(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    plan: InterfaceCompilePlan,
    projection_catalog: Mapping[str, ProjectionIdentityTruth] | None = None,
    state_model_catalog: Mapping[str, UUID] | None = None,
    state_attribute_catalog: Mapping[str, Mapping[str, UUID]] | None = None,
    api_view_catalog: Mapping[str, ApiViewStateTruth] | None = None,
) -> InterfaceConfigBundle:
    if len(plan.interface_ownership) != 1:
        raise ValueError(
            "Interface bundle emission currently requires exactly one interface declaration per package; "
            + f"got {len(plan.interface_ownership)} in {snapshot.spec_path}"
        )

    interface = plan.interface_ownership[0]
    interface_config_id = stable_interface_config_id(name=interface.name)
    pane_experience_catalogs = _load_pane_experience_catalogs(
        snapshot=snapshot,
        state_model_catalog=state_model_catalog,
        state_attribute_catalog=state_attribute_catalog,
        api_view_catalog=api_view_catalog,
    )
    projection_catalog = _resolve_projection_identity_catalog(
        snapshot=snapshot,
        projection_catalog=projection_catalog,
    )
    pane_package_catalog = _load_pane_package_catalog(snapshot=snapshot)
    attention_layout_catalog = _load_attention_layout_catalog(snapshot=snapshot)

    window_configs: list[InterfaceWindowConfigBundle] = []
    section_config_ids: dict[tuple[str, str, str], UUID] = {}
    for window in interface.windows:
        window_config_id = stable_window_config_id(key=window.key)
        layout_bundles: list[InterfaceWindowConfigLayoutBundle] = []
        for layout in window.layouts:
            attention_layout = attention_layout_catalog.get(layout.key.casefold())
            if snapshot.attention_packages and attention_layout is None:
                raise ValueError(
                    "Interface layout key is missing Attention-backed layout truth: "
                    + f"{layout.key!r} in {snapshot.spec_path}"
                )
            layout_config_id = (
                attention_layout.layout_config_id
                if attention_layout is not None
                else stable_layout_config_id(key=layout.key)
            )
            sections: list[InterfaceWindowLayoutSectionBundle] = []
            if attention_layout is not None:
                for section in attention_layout.sections:
                    section_key = section.section_key
                    section_config_id = section.layout_config_section_config_id
                    section_config_ids[
                        (
                            window.key.casefold(),
                            layout.key.casefold(),
                            section_key.casefold(),
                        )
                    ] = section_config_id
                    sections.append(
                        InterfaceWindowLayoutSectionBundle(
                            layout_config_section_config_id=section_config_id,
                            key=section_key,
                        )
                    )
            else:
                for section in layout.sections:
                    section_key = section.key
                    section_config_id = stable_layout_config_section_config_id(
                        layout_config_id=layout_config_id,
                        section_key=section_key,
                    )
                    section_config_ids[
                        (
                            window.key.casefold(),
                            layout.key.casefold(),
                            section_key.casefold(),
                        )
                    ] = section_config_id
                    sections.append(
                        InterfaceWindowLayoutSectionBundle(
                            layout_config_section_config_id=section_config_id,
                            key=section_key,
                        )
                    )

            layout_bundles.append(
                InterfaceWindowConfigLayoutBundle(
                    window_config_layout_config_id=stable_window_config_layout_config_id(
                        window_config_id=window_config_id,
                        layout_config_id=layout_config_id,
                    ),
                    layout_config_id=layout_config_id,
                    key=layout.key,
                    is_default=layout.is_default,
                    sections=sections,
                )
            )

        window_configs.append(
            InterfaceWindowConfigBundle(
                interface_config_window_config_id=stable_interface_config_window_config_id(
                    interface_config_id=interface_config_id,
                    window_config_id=window_config_id,
                ),
                window_config_id=window_config_id,
                key=window.key,
                description=None,
                layout_configs=layout_bundles,
            )
        )

    pane_by_name = {pane.name.casefold(): pane for pane in plan.pane_ownership}
    pane_configs: list[InterfacePaneConfigBundle] = []
    for pane_mounts in interface.panes:
        pane = pane_by_name.get(pane_mounts.pane_name.casefold())
        if pane is None:
            raise ValueError(
                f"Interface {interface.name!r} references pane {pane_mounts.pane_name!r} that was not declared"
            )
        pane_package = pane_package_catalog.get(pane.name.casefold())
        pane_experience_catalog = _pane_experience_catalog_for_name(
            pane_name=pane.name,
            pane_experience_catalogs=pane_experience_catalogs,
        )
        pane_view = pane.views[0]
        pane_projection_view_truth = _resolve_projection_experience_view_truth(
            workspace_root=snapshot.workspace_root,
            view_ref=pane_view.ref,
            experience_catalog=pane_experience_catalog,
            projection_catalog=projection_catalog,
            dependency_scope_label="declared pane experience_package dependency scope",
        )
        pane_config_id = stable_pane_config_id(
            name=pane.name,
            projection_experience_view_id=pane_projection_view_truth.projection_experience_view_id,
        )
        interface_config_pane_config_id = stable_interface_config_pane_config_id(
            interface_config_id=interface_config_id,
            pane_config_id=pane_config_id,
        )

        section_mounts: list[InterfacePaneSectionMountBundle] = []
        for mount in pane_mounts.mounts:
            target = (
                mount.window_key.casefold(),
                mount.layout_key.casefold(),
                mount.section_key.casefold(),
            )
            section_config_id = section_config_ids.get(target)
            if section_config_id is None:
                raise ValueError(
                    "Interface pane mount target was not found in compiled window/layout sections: "
                    + f"{mount.window_key}.{mount.layout_key}.{mount.section_key}"
                )
            section_mounts.append(
                InterfacePaneSectionMountBundle(
                    mount_id=stable_interface_config_pane_config_section_config_id(
                        interface_config_pane_config_id=interface_config_pane_config_id,
                        layout_config_section_config_id=section_config_id,
                    ),
                    layout_config_section_config_id=section_config_id,
                )
            )

        projection_view_bundles = [
            InterfacePaneProjectionExperienceViewBundle(
                binding_id=pane_config_id,
                projection_experience_view_id=(
                    pane_projection_view_truth.projection_experience_view_id
                ),
                object_projection_graph_observable_id=(
                    pane_projection_view_truth.object_projection_graph_observable_id
                ),
                object_projection_graph_identity_id=(
                    pane_projection_view_truth.object_projection_graph_identity_id
                ),
                state_model_id=pane_projection_view_truth.state_model_id,
                view_ref=pane_view.ref,
                projection_view_key=pane_projection_view_truth.projection_view_key,
                is_default=pane_view.is_default,
                invocation_actions=list(
                    _projection_view_invocation_action_bundles(
                        projection_experience_id=(
                            pane_projection_view_truth.projection_experience_id
                        ),
                        projection_experience_view_id=(
                            pane_projection_view_truth.projection_experience_view_id
                        ),
                        invocation_actions=pane_projection_view_truth.invocation_actions,
                    )
                ),
                section_mounts=section_mounts,
            )
        ]

        pane_configs.append(
            InterfacePaneConfigBundle(
                pane_config_id=pane_config_id,
                pane_package_id=(
                    pane_package.pane_package_id if pane_package is not None else None
                ),
                pane_package_name=(
                    pane_package.pane_package_name if pane_package is not None else None
                ),
                name=pane.name,
                pane_kind=pane.pane_kind,
                description=pane.description,
                narrative_key=pane_mounts.narrative_key,
                projection_experience_views=projection_view_bundles,
            )
        )

    bundle = InterfaceConfigBundle(
        interface_package_id=stable_interface_package_id(
            name=snapshot.spec.interface.package_name,
        ),
        interface_package_name=snapshot.spec.interface.package_name,
        interface_config_id=interface_config_id,
        name=interface.name,
        description=None,
        window_configs=window_configs,
        pane_configs=pane_configs,
    )
    _validate_section_resolution_defaults(bundle=bundle)
    return bundle


def _validate_section_resolution_defaults(*, bundle: InterfaceConfigBundle) -> None:
    @dataclass(frozen=True, slots=True)
    class _SectionBinding:
        pane_name: str
        pane_kind: str
        observable_id: UUID | None
        projection_experience_view_id: UUID
        view_ref: str

    section_mounts: dict[UUID, list[_SectionBinding]] = {}
    for pane_config in bundle.pane_configs:
        for projection_view in pane_config.projection_experience_views:
            for mount in projection_view.section_mounts:
                section_mounts.setdefault(
                    mount.layout_config_section_config_id,
                    [],
                ).append(
                    _SectionBinding(
                        pane_name=pane_config.name,
                        pane_kind=pane_config.pane_kind,
                        observable_id=projection_view.object_projection_graph_observable_id,
                        projection_experience_view_id=projection_view.projection_experience_view_id,
                        view_ref=projection_view.view_ref,
                    )
                )
    for section_config_id, bindings in section_mounts.items():
        for binding in bindings:
            if binding.observable_id is None:
                raise ValueError(
                    "Interface sections must resolve canonical `observable -> experience view -> pane` bindings. "
                    + f"Section {section_config_id} has view {binding.view_ref!r} on pane {binding.pane_name!r} "
                    + "without an observable id."
                )

        if len(bindings) <= 1:
            continue

        seen_projection_views: dict[UUID, _SectionBinding] = {}
        seen_observables: dict[UUID, _SectionBinding] = {}
        for binding in bindings:
            existing_view = seen_projection_views.get(
                binding.projection_experience_view_id
            )
            if existing_view is not None:
                raise ValueError(
                    "Interface sections must not duplicate the same experience view binding. "
                    + f"Section {section_config_id} repeats view {binding.view_ref!r} "
                    + f"on panes {existing_view.pane_name!r} and {binding.pane_name!r}."
                )
            seen_projection_views[binding.projection_experience_view_id] = binding

            observable_id = binding.observable_id
            if observable_id is None:
                continue
            existing = seen_observables.get(observable_id)
            if existing is not None:
                raise ValueError(
                    "Interface sections must resolve one `observable -> experience view -> pane` chain "
                    + "per observable. "
                    + f"Section {section_config_id} duplicates observable {observable_id} on "
                    + f"{existing.view_ref!r} -> {existing.pane_name!r} and "
                    + f"{binding.view_ref!r} -> {binding.pane_name!r}."
                )
            seen_observables[observable_id] = binding


def _load_attention_layout_catalog(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
) -> dict[str, InterfaceAttentionLayoutSnapshot]:
    catalog: dict[str, InterfaceAttentionLayoutSnapshot] = {}
    for attention_package in snapshot.attention_packages:
        for layout in attention_package.layouts:
            layout_key = layout.layout_key.casefold()
            if layout_key in catalog:
                existing = catalog[layout_key]
                raise ValueError(
                    "Duplicate Attention-backed layout ownership for layout key "
                    + f"{layout.layout_key!r}: {existing.layout_key!r} vs {layout.layout_key!r}"
                )
            catalog[layout_key] = layout
    return catalog


def _load_pane_package_catalog(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
) -> dict[str, _PanePackageIdentityTruth]:
    catalog: dict[str, _PanePackageIdentityTruth] = {}
    for pane_package in snapshot.pane_packages:
        pane_name = (pane_package.spec.pane.pane_name or "").strip()
        if not pane_name:
            raise ValueError(
                f"Pane package must declare a non-empty pane_name: {pane_package.spec_path}"
            )
        package_name = (pane_package.spec.pane.package_name or "").strip()
        if not package_name:
            raise ValueError(
                f"Pane package must declare a non-empty package_name: {pane_package.spec_path}"
            )
        pane_key = pane_name.casefold()
        if pane_key in catalog:
            existing = catalog[pane_key]
            raise ValueError(
                "Duplicate pane package ownership for pane "
                + f"{pane_name!r}: {existing.pane_package_name!r} vs {package_name!r}"
            )
        catalog[pane_key] = _PanePackageIdentityTruth(
            pane_package_id=stable_pane_package_id(name=package_name),
            pane_package_name=package_name,
        )
    return catalog


def _load_pane_package_snapshot_catalog(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
) -> dict[str, InterfacePanePackageSnapshot]:
    catalog: dict[str, InterfacePanePackageSnapshot] = {}
    for pane_package in snapshot.pane_packages:
        pane_name = (pane_package.spec.pane.pane_name or "").strip()
        if not pane_name:
            raise ValueError(
                f"Pane package must declare a non-empty pane_name: {pane_package.spec_path}"
            )
        pane_key = pane_name.casefold()
        if pane_key in catalog:
            existing = catalog[pane_key]
            raise ValueError(
                "Duplicate pane package ownership for pane "
                + f"{pane_name!r}: {existing.spec.pane.package_name!r} vs "
                + f"{pane_package.spec.pane.package_name!r}"
            )
        catalog[pane_key] = pane_package
    return catalog


def _load_pane_experience_catalogs(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    state_model_catalog: Mapping[str, UUID] | None = None,
    state_attribute_catalog: Mapping[str, Mapping[str, UUID]] | None = None,
    api_view_catalog: Mapping[str, ApiViewStateTruth] | None = None,
) -> dict[str, dict[str, _ProjectionExperienceOwnershipTruth]]:
    catalogs: dict[str, dict[str, _ProjectionExperienceOwnershipTruth]] = {}
    for pane_name, pane_package in _load_pane_package_snapshot_catalog(
        snapshot=snapshot
    ).items():
        catalogs[pane_name] = _load_projection_experience_catalog(
            snapshot=snapshot,
            experience_packages=pane_package.experience_packages,
            state_model_catalog=state_model_catalog,
            state_attribute_catalog=state_attribute_catalog,
            api_view_catalog=api_view_catalog,
            dependency_scope_label="declared pane experience_package dependency scope",
        )
    return catalogs


def _pane_experience_catalog_for_name(
    *,
    pane_name: str,
    pane_experience_catalogs: Mapping[
        str, dict[str, _ProjectionExperienceOwnershipTruth]
    ],
) -> dict[str, _ProjectionExperienceOwnershipTruth]:
    catalog = pane_experience_catalogs.get(pane_name.casefold())
    if catalog is None:
        raise ValueError(
            "Interface pane "
            + f"{pane_name!r} is not backed by a PanePackage with declared experience_package dependencies"
        )
    return catalog


def emit_interface_config_bundle_artifact(
    *,
    bundle: InterfaceConfigBundle,
    config_bundle_path: Path,
    repo_root: Path,
) -> InterfaceConfigBundleArtifact:
    artifact_path = config_bundle_path.resolve()
    repo_root = repo_root.resolve()
    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    payload = bundle.model_dump(mode="json")
    payload.pop("apis", None)
    for pane_payload in payload.get("pane_configs", []):
        if isinstance(pane_payload, dict):
            pane_payload.pop("api_capability_endpoints", None)
            pane_payload.pop("sdk_operations", None)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return InterfaceConfigBundleArtifact(
        path=artifact_path, relpath=relpath, hash_sha256=digest
    )


def emit_interface_pane_render_spec_materialization_artifact(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    plan: InterfaceCompilePlan,
    runtime_package_dir: Path,
    repo_root: Path,
    projection_catalog: Mapping[str, ProjectionIdentityTruth] | None = None,
    state_model_catalog: Mapping[str, UUID] | None = None,
    state_attribute_catalog: Mapping[str, Mapping[str, UUID]] | None = None,
    api_view_catalog: Mapping[str, ApiViewStateTruth] | None = None,
) -> InterfacePaneRenderSpecMaterializationArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    render_spec_truths = _load_dart_pane_render_spec_truths(
        snapshot=snapshot,
        plan=plan,
        projection_catalog=projection_catalog,
        state_model_catalog=state_model_catalog,
        state_attribute_catalog=state_attribute_catalog,
        api_view_catalog=api_view_catalog,
    )
    payload = _encode_pane_render_spec_materialization(
        plan=plan,
        render_spec_truths=render_spec_truths,
    )
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (
        runtime_package_dir / "pane_render_specs.materialization.json"
    ).resolve()
    artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return InterfacePaneRenderSpecMaterializationArtifact(
        path=artifact_path, relpath=relpath, hash_sha256=digest
    )


def emit_interface_dart_pane_registrar_bundle_artifact(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    plan: InterfaceCompilePlan,
    dart_package_dir: Path,
    repo_root: Path,
    projection_catalog: Mapping[str, ProjectionIdentityTruth] | None = None,
    state_model_catalog: Mapping[str, UUID] | None = None,
    state_attribute_catalog: Mapping[str, Mapping[str, UUID]] | None = None,
    api_view_catalog: Mapping[str, ApiViewStateTruth] | None = None,
    render_spec_materialization_path: Path | None = None,
) -> InterfaceDartPaneRegistrarBundleArtifact:
    dart_package_dir = dart_package_dir.resolve()
    repo_root = repo_root.resolve()
    artifact_path = (
        dart_package_dir
        / "lib"
        / "_aware"
        / "interface"
        / "pane_package_registrars.dart"
    ).resolve()
    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    registrar_truths = _load_dart_pane_registrar_truths(snapshot=snapshot, plan=plan)
    payload = _render_dart_pane_registrar_bundle(
        snapshot=snapshot,
        plan=plan,
        registrar_truths=registrar_truths,
        projection_catalog=projection_catalog,
        state_model_catalog=state_model_catalog,
        state_attribute_catalog=state_attribute_catalog,
        api_view_catalog=api_view_catalog,
        render_spec_materialization_path=render_spec_materialization_path,
    )
    canonical = payload.encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path.write_text(payload, encoding="utf-8")
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return InterfaceDartPaneRegistrarBundleArtifact(
        path=artifact_path, relpath=relpath, hash_sha256=digest
    )


def _load_projection_experience_catalog(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    experience_packages: tuple[InterfaceExperiencePackageSnapshot, ...] | None = None,
    state_model_catalog: Mapping[str, UUID] | None = None,
    state_attribute_catalog: Mapping[str, Mapping[str, UUID]] | None = None,
    api_view_catalog: Mapping[str, ApiViewStateTruth] | None = None,
    dependency_scope_label: str = "declared interface experience_package dependency scope",
) -> dict[str, _ProjectionExperienceOwnershipTruth]:
    catalog: dict[str, _ProjectionExperienceOwnershipTruth] = {}
    fallback_state_model_ids_by_ref: dict[str, UUID] = {}
    fallback_state_attribute_ids_by_ref: dict[str, Mapping[str, UUID]] = {}
    api_view_state_by_ref: dict[str, ApiViewStateTruth] = {}
    for catalog_root in _catalog_roots_for_snapshot(snapshot=snapshot):
        fallback_state_model_ids_by_ref.update(
            _load_workspace_state_model_catalog(workspace_root=catalog_root)
        )
        fallback_state_attribute_ids_by_ref.update(
            _load_workspace_state_attribute_catalog(workspace_root=catalog_root)
        )
        for view_key, truth in _load_workspace_api_view_state_catalog(
            workspace_root=catalog_root
        ).items():
            api_view_state_by_ref[view_key] = _merge_api_view_state_truth(
                existing=api_view_state_by_ref.get(view_key),
                incoming=truth,
            )
    for ref, class_config_id in (state_model_catalog or {}).items():
        normalized_ref = (ref or "").strip()
        if normalized_ref:
            fallback_state_model_ids_by_ref[normalized_ref.casefold()] = class_config_id
    for ref, attribute_ids in (state_attribute_catalog or {}).items():
        normalized_ref = (ref or "").strip()
        if normalized_ref:
            fallback_state_attribute_ids_by_ref[normalized_ref.casefold()] = (
                attribute_ids
            )
    for ref, truth in (api_view_catalog or {}).items():
        normalized_ref = (ref or "").strip()
        if normalized_ref:
            normalized_key = normalized_ref.casefold()
            api_view_state_by_ref[normalized_key] = _merge_api_view_state_truth(
                existing=api_view_state_by_ref.get(normalized_key),
                incoming=truth,
            )
    for truth in api_view_state_by_ref.values():
        fallback_state_model_ids_by_ref.setdefault(
            truth.state_model_ref.casefold(),
            truth.state_model_id,
        )
    for experience_package in (
        experience_packages
        if experience_packages is not None
        else snapshot.experience_packages
    ):
        ownership = load_projection_experience_ownership_from_sources(
            package_root=experience_package.package_root,
            source_files=experience_package.source_files,
        )
        view_state_contracts = load_view_state_model_contracts_from_sources(
            package_root=experience_package.package_root,
            source_files=experience_package.source_files,
            fqn_prefix=(experience_package.spec.experience.fqn_prefix or "").strip(),
            package_name=(
                experience_package.spec.experience.package_name or ""
            ).strip(),
        )
        view_state_model_ids_by_ref = {
            **fallback_state_model_ids_by_ref,
            **{
                contract.state_model_ref.casefold(): contract.class_config_id
                for contract in view_state_contracts
            },
        }
        view_state_attribute_ids_by_ref: dict[str, Mapping[str, UUID]] = {
            **fallback_state_attribute_ids_by_ref,
        }
        for contract in view_state_contracts:
            attribute_ids = _state_attribute_ids_from_class_config(
                class_config=contract.class_config
            )
            for state_model_ref in _state_model_catalog_refs(
                class_fqn=contract.state_model_ref,
                fqn_prefix=(
                    experience_package.spec.experience.fqn_prefix or ""
                ).strip(),
            ):
                view_state_attribute_ids_by_ref[state_model_ref.casefold()] = (
                    attribute_ids
                )
        for experience in ownership:
            experience_key = experience.name.casefold()
            if experience_key in catalog:
                existing = catalog[experience_key]
                raise ValueError(
                    f"{dependency_scope_label} exposes duplicate experience "
                    + f"{experience.name!r}: package {existing.package_name!r} "
                    + f"({existing.source_path}) vs {experience_package.spec.experience.package_name!r} "
                    + f"({experience.source_path})"
                )
            catalog[experience_key] = _ProjectionExperienceOwnershipTruth(
                package_name=experience_package.spec.experience.package_name,
                source_path=experience.source_path,
                ownership=experience,
                view_state_model_ids_by_ref=view_state_model_ids_by_ref,
                view_state_attribute_ids_by_ref=view_state_attribute_ids_by_ref,
                api_view_state_by_ref=api_view_state_by_ref,
            )
    return catalog


def build_projection_identity_catalog_from_ocg(
    *,
    ocg: ObjectConfigGraph,
) -> dict[str, ProjectionIdentityTruth]:
    catalog: dict[str, ProjectionIdentityTruth] = {}
    object_config_graph_identity = ocg.object_config_graph_identity
    if object_config_graph_identity is None:
        return catalog

    object_projection_graphs_by_id = {
        object_projection_graph.id: object_projection_graph
        for object_projection_graph in ocg.object_projection_graphs
    }
    for (
        projection_identity
    ) in object_config_graph_identity.object_projection_graph_identities:
        projection_name = (projection_identity.projection_name or "").strip()
        normalized_projection_name = _normalize_projection_name(projection_name)
        if not normalized_projection_name:
            continue
        truth = ProjectionIdentityTruth(
            object_projection_graph_identity_id=projection_identity.id,
            projection_name=projection_name,
        )
        catalog[normalized_projection_name] = truth

        object_projection_graph = object_projection_graphs_by_id.get(
            projection_identity.object_projection_graph_id
        )
        if object_projection_graph is None:
            continue
        root_tokens = {
            _normalize_projection_name(node.class_config.class_fqn)
            for node in object_projection_graph.object_projection_graph_nodes
            if node.is_root and node.class_config is not None
        }
        root_tokens.discard("")
        if len(root_tokens) != 1:
            continue
        catalog.setdefault(next(iter(root_tokens)), truth)
    return catalog


def build_state_model_catalog_from_ocg(
    *,
    ocg: ObjectConfigGraph,
) -> dict[str, UUID]:
    catalog: dict[str, UUID] = {}
    for node in ocg.object_config_graph_nodes:
        _add_state_model_catalog_entry(
            catalog=catalog,
            class_config=node.class_config,
            fqn_prefix=ocg.fqn_prefix,
        )
    for object_projection_graph in ocg.object_projection_graphs:
        for node in object_projection_graph.object_projection_graph_nodes:
            _add_state_model_catalog_entry(
                catalog=catalog,
                class_config=node.class_config,
                fqn_prefix=ocg.fqn_prefix,
            )
    return catalog


def build_state_attribute_catalog_from_ocg(
    *,
    ocg: ObjectConfigGraph,
) -> dict[str, Mapping[str, UUID]]:
    catalog: dict[str, Mapping[str, UUID]] = {}
    for node in ocg.object_config_graph_nodes:
        _add_state_attribute_catalog_entry(
            catalog=catalog,
            class_config=node.class_config,
            fqn_prefix=ocg.fqn_prefix,
        )
    for object_projection_graph in ocg.object_projection_graphs:
        for node in object_projection_graph.object_projection_graph_nodes:
            _add_state_attribute_catalog_entry(
                catalog=catalog,
                class_config=node.class_config,
                fqn_prefix=ocg.fqn_prefix,
            )
    return catalog


def _load_workspace_state_model_catalog(*, workspace_root: Path) -> dict[str, UUID]:
    catalog: dict[str, UUID] = {}
    for ocg_payload in _iter_workspace_ocg_payloads(workspace_root=workspace_root):
        fqn_prefix = str(ocg_payload.get("fqn_prefix") or "").strip()
        for class_config in _iter_ocg_class_config_payloads(ocg_payload=ocg_payload):
            _add_state_model_catalog_payload_entry(
                catalog=catalog,
                class_config=class_config,
                fqn_prefix=fqn_prefix,
            )
    return catalog


def _load_workspace_state_attribute_catalog(
    *, workspace_root: Path
) -> dict[str, Mapping[str, UUID]]:
    catalog: dict[str, Mapping[str, UUID]] = {}
    for ocg_payload in _iter_workspace_ocg_payloads(workspace_root=workspace_root):
        fqn_prefix = str(ocg_payload.get("fqn_prefix") or "").strip()
        for class_config in _iter_ocg_class_config_payloads(ocg_payload=ocg_payload):
            _add_state_attribute_catalog_payload_entry(
                catalog=catalog,
                class_config=class_config,
                fqn_prefix=fqn_prefix,
            )
    return catalog


def _iter_workspace_ocg_payloads(
    *, workspace_root: Path
) -> tuple[Mapping[str, object], ...]:
    payloads: list[Mapping[str, object]] = []
    for module_manifest_path in _resolve_workspace_module_manifest_paths(
        workspace_root=workspace_root,
    ):
        if not module_manifest_path.exists():
            continue
        module_manifest = cast(
            dict[str, object],
            json.loads(module_manifest_path.read_text(encoding="utf-8") or "{}"),
        )
        ocg_payload = _load_module_ocg_snapshot(
            module_manifest_path=module_manifest_path,
            module_manifest=module_manifest,
        )
        payloads.append(ocg_payload)
    payloads.extend(
        _load_workspace_api_accessible_dependency_graphs(workspace_root=workspace_root)
    )
    return tuple(payloads)


def _load_workspace_api_accessible_dependency_graphs(
    *, workspace_root: Path
) -> tuple[Mapping[str, object], ...]:
    runtime_root = workspace_root / ".aware" / "api" / "runtime"
    if not runtime_root.is_dir():
        return ()
    graphs: list[Mapping[str, object]] = []
    for graph_index_path in sorted(
        runtime_root.glob("*/api.accessible_dependency_graphs.json")
    ):
        try:
            payload = cast(
                Mapping[str, object],
                json.loads(graph_index_path.read_text(encoding="utf-8") or "{}"),
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Failed to parse API accessible dependency graph index at "
                + f"{graph_index_path}: {exc}"
            ) from exc
        raw_graphs = payload.get("graphs")
        if not isinstance(raw_graphs, list):
            continue
        for graph_payload in raw_graphs:
            if isinstance(graph_payload, dict):
                graphs.append(cast(Mapping[str, object], graph_payload))
    return tuple(graphs)


def _iter_ocg_class_config_payloads(
    *, ocg_payload: Mapping[str, object]
) -> tuple[object, ...]:
    class_configs: list[object] = []
    graph_nodes = ocg_payload.get("object_config_graph_nodes", [])
    if isinstance(graph_nodes, list):
        for node in graph_nodes:
            if isinstance(node, dict):
                class_configs.append(node.get("class_config"))
    projection_graphs = ocg_payload.get("object_projection_graphs", [])
    if isinstance(projection_graphs, list):
        for projection_graph in projection_graphs:
            if not isinstance(projection_graph, dict):
                continue
            projection_nodes = projection_graph.get("object_projection_graph_nodes", [])
            if not isinstance(projection_nodes, list):
                continue
            for node in projection_nodes:
                if isinstance(node, dict):
                    class_configs.append(node.get("class_config"))
    return tuple(class_configs)


def _add_state_model_catalog_entry(
    *,
    catalog: dict[str, UUID],
    class_config: object,
    fqn_prefix: str,
) -> None:
    class_fqn = (getattr(class_config, "class_fqn", "") or "").strip()
    class_config_id = getattr(class_config, "id", None)
    if not class_fqn or not isinstance(class_config_id, UUID):
        return
    for ref in _state_model_catalog_refs(
        class_fqn=class_fqn,
        fqn_prefix=fqn_prefix,
    ):
        catalog.setdefault(ref.casefold(), class_config_id)


def _add_state_attribute_catalog_entry(
    *,
    catalog: dict[str, Mapping[str, UUID]],
    class_config: object,
    fqn_prefix: str,
) -> None:
    class_fqn = (getattr(class_config, "class_fqn", "") or "").strip()
    if not class_fqn:
        return
    attribute_ids = _state_attribute_ids_from_class_config(class_config=class_config)
    if not attribute_ids:
        return
    for ref in _state_model_catalog_refs(
        class_fqn=class_fqn,
        fqn_prefix=fqn_prefix,
    ):
        catalog.setdefault(ref.casefold(), attribute_ids)


def _add_state_model_catalog_payload_entry(
    *,
    catalog: dict[str, UUID],
    class_config: object,
    fqn_prefix: str,
) -> None:
    if not isinstance(class_config, dict):
        return
    class_fqn = str(class_config.get("class_fqn") or "").strip()
    class_config_id_raw = str(class_config.get("id") or "").strip()
    if not class_fqn or not class_config_id_raw:
        return
    class_config_id = UUID(class_config_id_raw)
    for ref in _state_model_catalog_refs(
        class_fqn=class_fqn,
        fqn_prefix=fqn_prefix,
    ):
        catalog.setdefault(ref.casefold(), class_config_id)


def _add_state_attribute_catalog_payload_entry(
    *,
    catalog: dict[str, Mapping[str, UUID]],
    class_config: object,
    fqn_prefix: str,
) -> None:
    if not isinstance(class_config, dict):
        return
    class_fqn = str(class_config.get("class_fqn") or "").strip()
    if not class_fqn:
        return
    attribute_ids = _state_attribute_ids_from_class_config_payload(
        class_config=class_config,
    )
    if not attribute_ids:
        return
    for ref in _state_model_catalog_refs(
        class_fqn=class_fqn,
        fqn_prefix=fqn_prefix,
    ):
        catalog.setdefault(ref.casefold(), attribute_ids)


def _state_model_catalog_refs(*, class_fqn: str, fqn_prefix: str) -> tuple[str, ...]:
    refs: list[str] = []
    seen_refs: set[str] = set()

    def add(ref: str) -> None:
        normalized = ref.strip()
        key = normalized.casefold()
        if normalized and key not in seen_refs:
            seen_refs.add(key)
            refs.append(normalized)

    add(class_fqn)
    normalized_fqn_prefix = (fqn_prefix or "").strip()
    if normalized_fqn_prefix and not class_fqn.casefold().startswith(
        f"{normalized_fqn_prefix}.".casefold()
    ):
        add(f"{normalized_fqn_prefix}.{class_fqn}")
    for ref in tuple(refs):
        add(authored_ref_from_fqn(ref))

    return tuple(refs)


def _state_attribute_ids_from_class_config(
    *, class_config: object
) -> Mapping[str, UUID]:
    attribute_ids: dict[str, UUID] = {}
    class_attribute_edges = getattr(class_config, "class_config_attribute_configs", ())
    for edge in class_attribute_edges:
        attribute_config = getattr(edge, "attribute_config", None)
        attribute_name = (getattr(attribute_config, "name", "") or "").strip()
        attribute_config_id = getattr(attribute_config, "id", None)
        if not attribute_name or not isinstance(attribute_config_id, UUID):
            continue
        attribute_ids[attribute_name.casefold()] = attribute_config_id
        owner_key = (getattr(attribute_config, "owner_key", "") or "").strip()
        if owner_key:
            attribute_ids[f"{owner_key}.{attribute_name}".casefold()] = (
                attribute_config_id
            )
    return attribute_ids


def _state_attribute_ids_from_class_config_payload(
    *, class_config: Mapping[str, object]
) -> Mapping[str, UUID]:
    attribute_ids: dict[str, UUID] = {}
    edge_rows = class_config.get("class_config_attribute_configs")
    if not isinstance(edge_rows, list):
        return attribute_ids
    for edge_row in edge_rows:
        if not isinstance(edge_row, dict):
            continue
        attribute_config = edge_row.get("attribute_config")
        if not isinstance(attribute_config, dict):
            continue
        attribute_name = str(attribute_config.get("name") or "").strip()
        attribute_config_id_raw = str(attribute_config.get("id") or "").strip()
        if not attribute_name or not attribute_config_id_raw:
            continue
        attribute_config_id = UUID(attribute_config_id_raw)
        attribute_ids[attribute_name.casefold()] = attribute_config_id
        owner_key = str(attribute_config.get("owner_key") or "").strip()
        if owner_key:
            attribute_ids[f"{owner_key}.{attribute_name}".casefold()] = (
                attribute_config_id
            )
    return attribute_ids


def _load_workspace_api_view_state_catalog(
    *, workspace_root: Path
) -> dict[str, ApiViewStateTruth]:
    catalog: dict[str, ApiViewStateTruth] = {}
    runtime_root = workspace_root / ".aware" / "api" / "runtime"
    if not runtime_root.is_dir():
        return catalog
    projection_identity_catalog = _load_projection_identity_catalog(
        workspace_root=workspace_root,
    )
    for compile_plan_path in sorted(runtime_root.glob("*/api.compile_plan.json")):
        try:
            payload = cast(
                Mapping[str, object],
                json.loads(compile_plan_path.read_text(encoding="utf-8") or "{}"),
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Failed to parse API compile plan at {compile_plan_path}: {exc}"
            ) from exc
        for raw_api in (
            *_mapping_items(payload.get("api_ownership")),
            *_mapping_items(payload.get("api_ontology")),
        ):
            action_endpoints_by_view_ref = _api_view_action_truths_by_view_ref(
                raw_api=raw_api,
                projection_identity_catalog=projection_identity_catalog,
            )
            for raw_view in _mapping_items(raw_api.get("views")):
                view_ref = str(raw_view.get("view_ref") or "").strip()
                state_model_ref = str(raw_view.get("state_model_ref") or "").strip()
                state_model_id_raw = str(raw_view.get("state_model_id") or "").strip()
                if not view_ref or not state_model_ref or not state_model_id_raw:
                    continue
                view_key = view_ref.casefold()
                truth = ApiViewStateTruth(
                    view_ref=view_ref,
                    state_model_ref=state_model_ref,
                    state_model_id=UUID(state_model_id_raw),
                    action_endpoints_by_key=action_endpoints_by_view_ref.get(
                        view_key,
                        {},
                    ),
                )
                catalog[view_key] = _merge_api_view_state_truth(
                    existing=catalog.get(view_key),
                    incoming=truth,
                )
    return catalog


def _api_view_action_truths_by_view_ref(
    *,
    raw_api: Mapping[str, object],
    projection_identity_catalog: Mapping[str, ProjectionIdentityTruth],
) -> dict[str, Mapping[str, ApiViewActionTruth]]:
    view_truths_by_name = _api_view_truths_by_name(raw_api=raw_api)
    api_name = _api_compile_plan_name(raw_api=raw_api)
    actions_by_view_ref: dict[str, dict[str, ApiViewActionTruth]] = {}
    for raw_view in _mapping_items(raw_api.get("views")):
        view_ref = str(raw_view.get("view_ref") or "").strip()
        if not view_ref:
            continue
        _add_api_view_action_truths(
            actions_by_key=actions_by_view_ref.setdefault(view_ref.casefold(), {}),
            raw_endpoints=_mapping_items(raw_view.get("capability_endpoints")),
            api_name=api_name,
            view_truth=view_truths_by_name.get(
                str(raw_view.get("name") or raw_view.get("view_key") or "")
                .strip()
                .casefold()
            ),
            projection_identity_catalog=projection_identity_catalog,
        )
    for raw_endpoint in _mapping_items(raw_api.get("view_capability_endpoints")):
        view_name = str(raw_endpoint.get("view_name") or "").strip()
        if not view_name:
            continue
        view_truth = view_truths_by_name.get(view_name.casefold())
        view_ref = view_truth.view_ref if view_truth is not None else None
        if view_ref is None:
            view_ref = f"{api_name}.{view_name}" if api_name else view_name
        _add_api_view_action_truths(
            actions_by_key=actions_by_view_ref.setdefault(view_ref.casefold(), {}),
            raw_endpoints=(raw_endpoint,),
            api_name=api_name,
            view_truth=view_truth,
            projection_identity_catalog=projection_identity_catalog,
        )
    return {
        view_ref: dict(actions_by_key)
        for view_ref, actions_by_key in actions_by_view_ref.items()
    }


def _api_view_truths_by_name(
    *, raw_api: Mapping[str, object]
) -> dict[str, _ApiCompilePlanViewTruth]:
    views_by_name: dict[str, _ApiCompilePlanViewTruth] = {}
    for raw_view in _mapping_items(raw_api.get("views")):
        view_ref = str(raw_view.get("view_ref") or "").strip()
        view_name = str(raw_view.get("name") or raw_view.get("view_key") or "").strip()
        if view_ref and view_name:
            views_by_name[view_name.casefold()] = _ApiCompilePlanViewTruth(
                view_ref=view_ref,
                view_name=view_name,
                observable_ref=str(raw_view.get("observable_ref") or "").strip()
                or None,
            )
    return views_by_name


def _api_compile_plan_name(*, raw_api: Mapping[str, object]) -> str:
    api_name = str(raw_api.get("name") or "").strip()
    if api_name:
        return api_name
    api_row = raw_api.get("api")
    if isinstance(api_row, Mapping):
        return str(api_row.get("name") or "").strip()
    return ""


def _add_api_view_action_truths(
    *,
    actions_by_key: dict[str, ApiViewActionTruth],
    raw_endpoints: tuple[Mapping[str, object], ...],
    api_name: str,
    view_truth: _ApiCompilePlanViewTruth | None,
    projection_identity_catalog: Mapping[str, ProjectionIdentityTruth],
) -> None:
    for raw_endpoint in raw_endpoints:
        action_key = str(raw_endpoint.get("action_key") or "").strip()
        endpoint_ref = str(raw_endpoint.get("endpoint_ref") or "").strip()
        if not action_key or not endpoint_ref:
            continue
        api_capability_endpoint_id = _uuid_or_none(
            raw_endpoint.get("api_capability_endpoint_id")
        ) or _stable_api_capability_endpoint_id_from_ref(
            api_name=api_name,
            endpoint_ref=endpoint_ref,
        )
        api_view_capability_endpoint_id = _uuid_or_none(
            raw_endpoint.get("api_view_capability_endpoint_id")
        )
        if api_view_capability_endpoint_id is None:
            api_view_id = _stable_api_view_id_from_compile_plan(
                api_name=api_name,
                view_truth=view_truth,
                projection_identity_catalog=projection_identity_catalog,
            )
            if api_view_id is not None and api_capability_endpoint_id is not None:
                api_view_capability_endpoint_id = (
                    stable_api_view_capability_endpoint_id(
                        api_view_id=api_view_id,
                        api_capability_endpoint_id=api_capability_endpoint_id,
                    )
                )
        actions_by_key[action_key.casefold()] = ApiViewActionTruth(
            action_key=action_key,
            endpoint_ref=endpoint_ref,
            api_view_capability_endpoint_id=api_view_capability_endpoint_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
            sdk_operation_api_view_capability_endpoint_id=_uuid_or_none(
                raw_endpoint.get("sdk_operation_api_view_capability_endpoint_id")
            ),
            sdk_operation_id=_uuid_or_none(raw_endpoint.get("sdk_operation_id")),
        )


def _stable_api_capability_endpoint_id_from_ref(
    *, api_name: str, endpoint_ref: str
) -> UUID | None:
    parts = tuple(part.strip() for part in endpoint_ref.split(".") if part.strip())
    if len(parts) != 3:
        return None
    endpoint_api_name, capability_name, endpoint_name = parts
    resolved_api_name = api_name or endpoint_api_name
    if resolved_api_name.casefold() != endpoint_api_name.casefold():
        return None
    api_id = stable_api_id(name=resolved_api_name)
    api_capability_id = stable_api_capability_id(
        api_id=api_id,
        name=capability_name,
    )
    return stable_api_capability_endpoint_id(
        api_capability_id=api_capability_id,
        name=endpoint_name,
    )


def _stable_api_view_id_from_compile_plan(
    *,
    api_name: str,
    view_truth: _ApiCompilePlanViewTruth | None,
    projection_identity_catalog: Mapping[str, ProjectionIdentityTruth],
) -> UUID | None:
    if view_truth is None or not api_name:
        return None
    observable_ref = (view_truth.observable_ref or "").strip()
    if not observable_ref:
        return None
    observable_parts = tuple(
        part.strip() for part in observable_ref.split(".") if part.strip()
    )
    if len(observable_parts) != 2:
        return None
    projection_name, observable_key = observable_parts
    projection_truth = projection_identity_catalog.get(
        _normalize_projection_name(projection_name)
    )
    if projection_truth is None:
        return None
    object_projection_graph_observable_id = (
        stable_object_projection_graph_observable_id(
            object_projection_graph_identity_id=(
                projection_truth.object_projection_graph_identity_id
            ),
            observable_key=observable_key,
        )
    )
    return stable_api_view_id(
        api_id=stable_api_id(name=api_name),
        object_projection_graph_observable_id=object_projection_graph_observable_id,
        name=view_truth.view_name,
    )


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value.strip())
    return None


def _merge_api_view_state_truth(
    *,
    existing: ApiViewStateTruth | None,
    incoming: ApiViewStateTruth,
) -> ApiViewStateTruth:
    if existing is None:
        return incoming
    action_endpoints_by_key = {
        **existing.action_endpoints_by_key,
        **incoming.action_endpoints_by_key,
    }
    return replace(
        incoming,
        action_endpoints_by_key=action_endpoints_by_key,
    )


def _mapping_items(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _load_projection_identity_catalog(
    *, workspace_root: Path
) -> dict[str, ProjectionIdentityTruth]:
    manifest_paths = _resolve_workspace_module_manifest_paths(
        workspace_root=workspace_root
    )
    catalog: dict[str, ProjectionIdentityTruth] = (
        _load_meta_runtime_projection_identity_catalog(
            workspace_root=workspace_root,
        )
    )
    projection_alias_candidates: dict[str, set[str]] = {}
    for module_manifest_path in manifest_paths:
        if not module_manifest_path.exists():
            continue
        module_manifest = cast(
            dict[str, object],
            json.loads(module_manifest_path.read_text(encoding="utf-8") or "{}"),
        )
        ocg_payload = _load_module_ocg_snapshot(
            module_manifest_path=module_manifest_path,
            module_manifest=module_manifest,
        )
        object_config_graph_identity = ocg_payload.get("object_config_graph_identity")
        if not isinstance(object_config_graph_identity, dict):
            continue
        projection_identities = object_config_graph_identity.get(
            "object_projection_graph_identities", []
        )
        if not isinstance(projection_identities, list):
            continue
        for projection_identity in projection_identities:
            if not isinstance(projection_identity, dict):
                continue
            projection_name = str(
                projection_identity.get("projection_name") or ""
            ).strip()
            identity_id = str(projection_identity.get("id") or "").strip()
            if not projection_name or not identity_id:
                continue
            normalized_projection_name = _normalize_projection_name(projection_name)
            if not normalized_projection_name:
                continue
            catalog.setdefault(
                normalized_projection_name,
                ProjectionIdentityTruth(
                    object_projection_graph_identity_id=UUID(identity_id),
                    projection_name=projection_name,
                ),
            )
        for projection_alias, projection_name in _load_projection_root_aliases(
            module_manifest_path=module_manifest_path,
            module_manifest=module_manifest,
        ).items():
            projection_alias_candidates.setdefault(projection_alias, set()).add(
                projection_name.casefold()
            )

    for projection_alias, projection_names in projection_alias_candidates.items():
        if projection_alias in catalog:
            continue
        if len(projection_names) != 1:
            continue
        projection_name = next(iter(projection_names))
        if projection_name not in catalog:
            continue
        catalog[projection_alias] = catalog[projection_name]
    for projection_key, truth in _load_source_projection_identity_catalog(
        workspace_root=workspace_root
    ).items():
        catalog.setdefault(projection_key, truth)
    return catalog


def _load_meta_runtime_projection_identity_catalog(
    *,
    workspace_root: Path,
) -> dict[str, ProjectionIdentityTruth]:
    package_index = load_meta_runtime_package_projection_index(
        aware_root=workspace_root,
    )
    if package_index is None:
        return {}
    catalog: dict[str, ProjectionIdentityTruth] = {}
    for projection_entry in package_index.projections_by_name.values():
        if projection_entry.object_projection_graph_identity_id is None:
            continue
        normalized_projection_name = _normalize_projection_name(
            projection_entry.projection_name
        )
        if not normalized_projection_name:
            continue
        catalog[normalized_projection_name] = ProjectionIdentityTruth(
            object_projection_graph_identity_id=(
                projection_entry.object_projection_graph_identity_id
            ),
            projection_name=projection_entry.projection_name,
        )
    return catalog


def _load_source_projection_identity_catalog(
    *, workspace_root: Path
) -> dict[str, ProjectionIdentityTruth]:
    catalog: dict[str, ProjectionIdentityTruth] = {}
    for ontology_toml_path in _local_ontology_toml_paths(workspace_root=workspace_root):
        try:
            with ontology_toml_path.open("rb") as handle:
                payload = cast(dict[str, object], tomllib.load(handle))
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(
                f"Failed to parse aware.ontology.toml at {ontology_toml_path}: {exc}"
            ) from exc
        ontology_row = payload.get("ontology")
        if not isinstance(ontology_row, dict):
            continue
        fqn_prefix = str(ontology_row.get("fqn_prefix") or "").strip()
        if not fqn_prefix:
            continue
        package_root_raw = str(ontology_row.get("package_root") or ".").strip() or "."
        sources_root_raw = str(
            ontology_row.get("sources_root") or "structure/aware"
        ).strip()
        package_root = (ontology_toml_path.parent / package_root_raw).resolve()
        sources_root = (package_root / sources_root_raw).resolve()
        if not sources_root.exists() or not sources_root.is_dir():
            continue
        object_config_graph_id = stable_object_config_graph_id(
            fqn_prefix=fqn_prefix,
            language="aware",
        )
        object_config_graph_identity_id = stable_object_config_graph_identity_id(
            key=fqn_prefix,
        )
        parser = Parser(language=AWARE_LANGUAGE)
        for source_path in sorted(sources_root.rglob("*.aware")):
            if not source_path.is_file():
                continue
            source_text = source_path.read_text(encoding="utf-8")
            tree = parser.parse(source_text.encode("utf-8"))
            if tree.root_node.has_error:
                continue
            for node in tree.root_node.named_children:
                if node.type != "projection_def":
                    continue
                projection_name = _aware_field_text(node, "name")
                normalized_projection_name = _normalize_projection_name(projection_name)
                if not normalized_projection_name:
                    continue
                object_projection_graph_id = stable_object_projection_graph_id(
                    object_config_graph_id=object_config_graph_id,
                    name=projection_name,
                )
                truth = ProjectionIdentityTruth(
                    object_projection_graph_identity_id=stable_object_projection_graph_identity_id(
                        object_config_graph_identity_id=object_config_graph_identity_id,
                        object_projection_graph_id=object_projection_graph_id,
                    ),
                    projection_name=projection_name,
                )
                catalog.setdefault(normalized_projection_name, truth)
                root_token = _projection_root_token(node=node)
                if root_token:
                    catalog.setdefault(root_token, truth)
    return catalog


def _local_ontology_toml_paths(*, workspace_root: Path) -> tuple[Path, ...]:
    resolved_workspace_root = workspace_root.resolve()
    candidate_paths: set[Path] = set()

    direct_path = resolved_workspace_root / "aware.ontology.toml"
    if direct_path.is_file():
        candidate_paths.add(direct_path.resolve())

    local_ontology_path = resolved_workspace_root / "ontology" / "aware.ontology.toml"
    if local_ontology_path.is_file():
        candidate_paths.add(local_ontology_path.resolve())

    modules_root = resolved_workspace_root / "modules"
    if modules_root.is_dir():
        for ontology_toml_path in modules_root.glob("*/ontology/aware.ontology.toml"):
            if ontology_toml_path.is_file():
                candidate_paths.add(ontology_toml_path.resolve())

    return tuple(sorted(candidate_paths))


def _projection_root_token(*, node: Node) -> str:
    for item in node.named_children:
        if item.type != "projection_item":
            continue
        for child in item.named_children:
            if child.type != "projection_root":
                continue
            return _normalize_projection_name(
                _aware_qualified_text(child.child_by_field_name("type"))
            )
    return ""


def _resolve_projection_identity_catalog(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    projection_catalog: Mapping[str, ProjectionIdentityTruth] | None = None,
) -> dict[str, ProjectionIdentityTruth]:
    resolved_catalog: dict[str, ProjectionIdentityTruth] = {}
    for catalog_root in _catalog_roots_for_snapshot(snapshot=snapshot):
        resolved_catalog.update(
            _load_projection_identity_catalog(workspace_root=catalog_root)
        )
    if projection_catalog is None:
        return resolved_catalog
    for projection_name, truth in projection_catalog.items():
        normalized_projection_name = _normalize_projection_name(projection_name)
        if not normalized_projection_name:
            continue
        resolved_catalog[normalized_projection_name] = truth
    return resolved_catalog


def _catalog_roots_for_snapshot(
    *, snapshot: InterfaceWorkspaceSnapshot
) -> tuple[Path, ...]:
    return tuple(root.root for root in snapshot.dependency_catalog_roots)


def _load_projection_root_aliases(
    *,
    module_manifest_path: Path,
    module_manifest: dict[str, object],
) -> dict[str, str]:
    runtime_dir = module_manifest_path.parent
    bindings_row = module_manifest.get("bindings")
    if not isinstance(bindings_row, dict):
        return {}
    bindings_relpath = str(bindings_row.get("file") or "").strip()
    if not bindings_relpath:
        return {}
    bindings_path = (runtime_dir / bindings_relpath).resolve()
    if not bindings_path.exists():
        return {}
    bindings_payload = cast(
        dict[str, object], json.loads(bindings_path.read_text(encoding="utf-8") or "{}")
    )
    bindings_rows = bindings_payload.get("bindings")
    if not isinstance(bindings_rows, list):
        return {}

    class_token_by_config_id: dict[str, str] = {}
    for binding_row in bindings_rows:
        if not isinstance(binding_row, dict):
            continue
        class_fqn = str(binding_row.get("class_fqn") or "").strip()
        canonical_class_config_id = str(
            binding_row.get("canonical_class_config_id") or ""
        ).strip()
        if not class_fqn or not canonical_class_config_id:
            continue
        class_token = _normalize_projection_name(class_fqn.rsplit(".", 1)[-1])
        if not class_token:
            continue
        class_token_by_config_id[canonical_class_config_id] = class_token

    opg_index_row = module_manifest.get("opg_index")
    if not isinstance(opg_index_row, dict):
        return {}
    opg_entries = opg_index_row.get("entries")
    if not isinstance(opg_entries, list):
        return {}

    aliases: dict[str, str] = {}
    for entry in opg_entries:
        if not isinstance(entry, dict):
            continue
        projection_name = _normalize_projection_name(
            str(entry.get("model") or "").strip()
        )
        file_relpath = str(entry.get("file") or "").strip()
        if not projection_name or not file_relpath:
            continue
        opg_path = (runtime_dir / file_relpath).resolve()
        if not opg_path.exists():
            continue
        opg_payload = cast(
            dict[str, object], json.loads(opg_path.read_text(encoding="utf-8") or "{}")
        )
        opg_nodes = opg_payload.get("object_projection_graph_nodes")
        if not isinstance(opg_nodes, list):
            continue
        root_tokens: set[str] = set()
        for opg_node in opg_nodes:
            if not isinstance(opg_node, dict):
                continue
            if not bool(opg_node.get("is_root")):
                continue
            class_config_id = str(opg_node.get("class_config_id") or "").strip()
            if not class_config_id:
                continue
            class_token = class_token_by_config_id.get(class_config_id)
            if class_token:
                root_tokens.add(class_token)
        if len(root_tokens) != 1:
            continue
        aliases[next(iter(root_tokens))] = projection_name

    return aliases


def _resolve_workspace_module_manifest_paths(
    *, workspace_root: Path
) -> tuple[Path, ...]:
    _ = workspace_root
    return ()


def _normalize_projection_name(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.casefold()


def _resolve_projection_experience_view_truth(
    *,
    workspace_root: Path,
    view_ref: str,
    experience_catalog: dict[str, _ProjectionExperienceOwnershipTruth],
    projection_catalog: Mapping[str, ProjectionIdentityTruth],
    dependency_scope_label: str = "declared interface experience_package dependency scope",
) -> _ProjectionExperienceViewTruth:
    _ = workspace_root
    parsed = _split_projection_experience_view_ref(view_ref=view_ref)
    if parsed is None:
        raise ValueError(
            f"Interface pane view ref must use `experience.observable.view`: {view_ref!r}"
        )
    experience_name, observable_key, view_key = parsed
    experience_truth = experience_catalog.get(experience_name.casefold())
    if experience_truth is None:
        raise ValueError(
            "Interface pane view "
            + f"{view_ref!r} references unknown experience {experience_name!r} "
            + f"outside the {dependency_scope_label}"
        )
    experience = experience_truth.ownership

    observable = next(
        (
            item
            for item in experience.observables
            if item.key.casefold() == observable_key.casefold()
        ),
        None,
    )
    if observable is None:
        raise ValueError(
            f"Interface pane view {view_ref!r} references unknown observable "
            + f"{observable_key!r} on experience {experience_name!r}"
        )
    view = next(
        (
            item
            for item in observable.views
            if item.key.casefold() == view_key.casefold()
        ),
        None,
    )
    if view is None:
        raise ValueError(
            f"Interface pane view {view_ref!r} references unknown view "
            + f"{view_key!r} on {experience_name!r}.{observable_key!r}"
        )
    projection_truth = projection_catalog.get(experience.projection.casefold())
    if projection_truth is None:
        raise ValueError(
            f"Interface pane view {view_ref!r} references projection "
            + f"{experience.projection!r} without workspace OPG identity truth"
        )

    api_view_truth = _resolve_projection_view_api_view_truth(
        view=view,
        api_view_state_by_ref=experience_truth.api_view_state_by_ref,
        view_ref=view_ref,
    )
    state_model_ref = _resolve_projection_view_state_model_ref(
        view=view,
        api_view_truth=api_view_truth,
        view_ref=view_ref,
    )
    state_model_id = experience_truth.view_state_model_ids_by_ref.get(
        state_model_ref.casefold()
    )
    if state_model_id is None:
        available_refs = tuple(
            sorted(experience_truth.view_state_model_ids_by_ref)[:10]
        )
        raise ValueError(
            f"Interface pane view {view_ref!r} references state model "
            + f"{state_model_ref!r} without generated view-state model truth; "
            + f"available_state_model_refs={available_refs!r}"
        )

    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=projection_truth.object_projection_graph_identity_id,
        name=experience.name,
    )
    observable_id = stable_object_projection_graph_observable_id(
        object_projection_graph_identity_id=projection_truth.object_projection_graph_identity_id,
        observable_key=observable.key,
    )
    return _ProjectionExperienceViewTruth(
        projection_experience_id=projection_experience_id,
        projection_experience_view_id=stable_projection_experience_view_id(
            projection_experience_id=projection_experience_id,
            name=view_key,
        ),
        object_projection_graph_observable_id=observable_id,
        object_projection_graph_identity_id=(
            projection_truth.object_projection_graph_identity_id
        ),
        projection_view_key=f"{observable.key}.{view_key}",
        state_model_id=state_model_id,
        state_model_ref=state_model_ref,
        state_attribute_ids_by_ref=experience_truth.view_state_attribute_ids_by_ref.get(
            state_model_ref.casefold(),
            {},
        ),
        api_view_ref=view.api_view_ref,
        api_view_truth=api_view_truth,
        invocation_actions=_hydrate_projection_view_invocation_actions(
            view=view,
            api_view_truth=api_view_truth,
            view_ref=view_ref,
        ),
    )


def _resolve_projection_view_api_view_truth(
    *,
    view: ExperienceProjectionViewOwnership,
    api_view_state_by_ref: Mapping[str, ApiViewStateTruth],
    view_ref: str,
) -> ApiViewStateTruth | None:
    if view.api_view_ref is None:
        return None
    api_view_truth = api_view_state_by_ref.get(view.api_view_ref.casefold())
    if api_view_truth is None:
        available_api_views = tuple(sorted(api_view_state_by_ref)[:12])
        raise ValueError(
            f"Interface pane view {view_ref!r} references ApiView "
            + f"{view.api_view_ref!r} without generated API view truth; "
            + f"available_api_views={available_api_views!r}"
        )
    return api_view_truth


def _resolve_projection_view_state_model_ref(
    *,
    view: ExperienceProjectionViewOwnership,
    api_view_truth: ApiViewStateTruth | None,
    view_ref: str,
) -> str:
    if view.state_model_ref is not None:
        return view.state_model_ref
    if api_view_truth is None:
        raise ValueError(
            f"Interface pane view {view_ref!r} has no Experience state model or ApiView reference"
        )
    return api_view_truth.state_model_ref


def _hydrate_projection_view_invocation_actions(
    *,
    view: ExperienceProjectionViewOwnership,
    api_view_truth: ApiViewStateTruth | None,
    view_ref: str,
) -> tuple[ExperienceProjectionViewInvocationActionOwnership, ...]:
    if not view.invocation_actions:
        if api_view_truth is None:
            return ()
        return tuple(
            _projection_view_invocation_action_from_api_truth(
                action_truth=action_truth,
                source_path=view.source_path,
            )
            for action_truth in sorted(
                api_view_truth.action_endpoints_by_key.values(),
                key=lambda item: (
                    item.action_key.casefold(),
                    item.endpoint_ref.casefold(),
                ),
            )
        )

    hydrated_actions: list[ExperienceProjectionViewInvocationActionOwnership] = []
    for action in view.invocation_actions:
        if _projection_view_invocation_action_has_target(action):
            hydrated_actions.append(action)
            continue
        if api_view_truth is None:
            hydrated_actions.append(action)
            continue
        action_truth = api_view_truth.action_endpoints_by_key.get(action.key.casefold())
        if action_truth is None:
            available_actions = tuple(
                sorted(api_view_truth.action_endpoints_by_key)[:12]
            )
            raise ValueError(
                f"Interface pane view {view_ref!r} action {action.key!r} "
                + f"references ApiView {api_view_truth.view_ref!r} without a matching "
                + "view capability endpoint; "
                + f"available_api_view_actions={available_actions!r}"
            )
        hydrated_actions.append(
            replace(
                action,
                endpoint_ref=action_truth.endpoint_ref,
                api_view_capability_endpoint_id=(
                    action_truth.api_view_capability_endpoint_id
                ),
                api_capability_endpoint_id=action_truth.api_capability_endpoint_id,
                sdk_operation_api_view_capability_endpoint_id=(
                    action_truth.sdk_operation_api_view_capability_endpoint_id
                ),
                sdk_operation_id=action_truth.sdk_operation_id,
            )
        )
    return tuple(hydrated_actions)


def _projection_view_invocation_action_from_api_truth(
    *,
    action_truth: ApiViewActionTruth,
    source_path: str,
) -> ExperienceProjectionViewInvocationActionOwnership:
    return ExperienceProjectionViewInvocationActionOwnership(
        key=action_truth.action_key,
        source_path=source_path,
        api_view_capability_endpoint_id=action_truth.api_view_capability_endpoint_id,
        endpoint_ref=action_truth.endpoint_ref,
        api_capability_endpoint_id=action_truth.api_capability_endpoint_id,
        sdk_operation_api_view_capability_endpoint_id=(
            action_truth.sdk_operation_api_view_capability_endpoint_id
        ),
        sdk_operation_id=action_truth.sdk_operation_id,
    )


def _projection_view_invocation_action_has_target(
    action: ExperienceProjectionViewInvocationActionOwnership,
) -> bool:
    action_kind = getattr(action, "action_kind", None)
    target_ref = getattr(action, "target_ref", None)
    if isinstance(action_kind, str) and isinstance(target_ref, str):
        return bool(action_kind.strip() and target_ref.strip())
    endpoint_ref = getattr(action, "endpoint_ref", None)
    if isinstance(endpoint_ref, str) and endpoint_ref.strip():
        return True
    return isinstance(getattr(action, "sdk_operation_id", None), UUID)


def _projection_view_invocation_action_config_id(
    *,
    projection_experience_view_id: UUID,
    action: ExperienceProjectionViewInvocationActionOwnership,
) -> UUID:
    api_view_capability_endpoint_id = getattr(
        action,
        "api_view_capability_endpoint_id",
        None,
    )
    if not isinstance(api_view_capability_endpoint_id, UUID):
        raise ValueError(
            "Experience view invocation action requires api_view_capability_endpoint_id "
            + "from ApiView action truth before Interface can derive its stable config id "
            + f"(action_key={action.key!r})"
        )
    return stable_projection_experience_view_invocation_action_config_id(
        projection_experience_view_id=projection_experience_view_id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
    )


def _projection_view_invocation_action_bundles(
    *,
    projection_experience_id: UUID,
    projection_experience_view_id: UUID,
    invocation_actions: tuple[ExperienceProjectionViewInvocationActionOwnership, ...],
) -> tuple[InterfacePaneViewInvocationActionBundle, ...]:
    bundles: list[InterfacePaneViewInvocationActionBundle] = []
    for action in invocation_actions:
        action_kind, target_ref = _projection_view_invocation_action_target(action)
        action_id = _projection_view_invocation_action_config_id(
            projection_experience_view_id=projection_experience_view_id,
            action=action,
        )

        bundles.append(
            InterfacePaneViewInvocationActionBundle(
                projection_experience_view_invocation_action_id=action_id,
                action_key=action.key,
                action_kind=action_kind,
                target_ref=target_ref,
                api_capability_endpoint_id=getattr(
                    action,
                    "api_capability_endpoint_id",
                    None,
                ),
                sdk_operation_id=getattr(action, "sdk_operation_id", None),
                label=action.label,
                receipt_policy=action.receipt_policy,
                confirmation_policy=action.confirmation_policy,
                optimistic_policy=action.optimistic_policy,
            )
        )
    return tuple(
        sorted(
            bundles,
            key=lambda item: (
                item.action_key.casefold(),
                str(item.projection_experience_view_invocation_action_id),
            ),
        )
    )


def _projection_view_invocation_action_target(
    action: ExperienceProjectionViewInvocationActionOwnership,
) -> tuple[str, str]:
    action_kind = getattr(action, "action_kind", None)
    target_ref = getattr(action, "target_ref", None)
    if isinstance(action_kind, str) and isinstance(target_ref, str):
        if action_kind not in {"view", "api", "sdk", "service"}:
            raise ValueError(
                "Experience view invocation action has unsupported action_kind: "
                + f"{action_kind!r}"
            )
        return action_kind, target_ref

    sdk_operation_id = getattr(action, "sdk_operation_id", None)
    if isinstance(sdk_operation_id, UUID):
        return "sdk", str(sdk_operation_id)

    endpoint_ref = getattr(action, "endpoint_ref", None)
    if isinstance(endpoint_ref, str) and endpoint_ref.strip():
        return "api", endpoint_ref.strip()

    if (
        getattr(action, "api_capability_endpoint_id", None) is not None
        or getattr(
            action,
            "api_view_capability_endpoint_id",
            None,
        )
        is not None
    ):
        raise ValueError(
            "Experience view invocation action resolved an API endpoint id without endpoint_ref "
            + f"(action_key={action.key!r})"
        )

    raise ValueError(
        "Experience view invocation action has no supported target metadata "
        + f"(action_key={action.key!r})"
    )


def _assert_workspace_file(
    *, workspace_root: Path, source_path: Path, label: str
) -> None:
    workspace_root = workspace_root.resolve()
    source_path = source_path.resolve()
    if workspace_root != source_path and workspace_root not in source_path.parents:
        raise ValueError(f"{label} resolved outside workspace root: {source_path}")
    if not source_path.is_file():
        raise FileNotFoundError(f"{label} not found: {source_path}")


def _aware_field_text(node: Node, field: str) -> str:
    return _aware_qualified_text(node.child_by_field_name(field))


def _aware_qualified_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8").strip()


def _load_module_ocg_snapshot(
    *,
    module_manifest_path: Path,
    module_manifest: dict[str, object],
) -> dict[str, object]:
    ocg = module_manifest.get("ocg")
    if not isinstance(ocg, dict):
        raise ValueError(
            f"Environment manifest {module_manifest_path} is missing `ocg` metadata"
        )
    snapshot_relpath = str(ocg.get("snapshot") or "").strip()
    if not snapshot_relpath:
        raise ValueError(
            f"Environment manifest {module_manifest_path} is missing `ocg.snapshot`"
        )
    snapshot_path = (module_manifest_path.parent / snapshot_relpath).resolve()
    if not snapshot_path.exists():
        raise FileNotFoundError(f"OCG snapshot not found: {snapshot_path}")
    payload = msgpack.unpackb(snapshot_path.read_bytes(), raw=False)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid OCG snapshot payload at {snapshot_path}")
    return cast(dict[str, object], payload)


def _validate_interface_ownership(
    *,
    ownership: InterfaceSourceOwnership,
    attention_layout_catalog: dict[str, InterfaceAttentionLayoutSnapshot],
    pane_experience_catalogs: Mapping[
        str, dict[str, _ProjectionExperienceOwnershipTruth]
    ],
) -> None:
    pane_by_name = {pane.name.casefold(): pane for pane in ownership.pane_ownership}

    for interface in ownership.interface_ownership:
        window_map = {
            window.key.casefold(): {
                layout.key.casefold(): _layout_mount_scope(
                    layout=layout,
                    attention_layout_catalog=attention_layout_catalog,
                )
                for layout in window.layouts
            }
            for window in interface.windows
        }

        for pane_mounts in interface.panes:
            pane = pane_by_name.get(pane_mounts.pane_name.casefold())
            if pane is None:
                raise ValueError(
                    f"Interface {interface.name!r} references unknown pane {pane_mounts.pane_name!r}"
                )
            pane_experience_catalog = _pane_experience_catalog_for_name(
                pane_name=pane.name,
                pane_experience_catalogs=pane_experience_catalogs,
            )
            for view in pane.views:
                _validate_projection_experience_view_ref(
                    view_ref=view.ref,
                    experience_catalog=pane_experience_catalog,
                    dependency_scope_label=(
                        "declared pane experience_package dependency scope"
                    ),
                )
            for mount in pane_mounts.mounts:
                layout_map = window_map.get(mount.window_key.casefold())
                if layout_map is None:
                    raise ValueError(
                        f"Interface {interface.name!r} pane {pane_mounts.pane_name!r} mounts unknown window "
                        + f"{mount.window_key!r}"
                    )
                mount_scope = layout_map.get(mount.layout_key.casefold())
                if mount_scope is None:
                    raise ValueError(
                        f"Interface {interface.name!r} pane {pane_mounts.pane_name!r} mounts unknown layout "
                        + f"{mount.layout_key!r} under window {mount.window_key!r}"
                    )
                if mount.section_key.casefold() not in mount_scope.section_keys:
                    raise ValueError(
                        f"Interface {interface.name!r} pane {pane_mounts.pane_name!r} mounts unknown section "
                        + f"{mount.section_key!r} under {mount.window_key!r}.{mount.layout_key!r}"
                    )


def _validate_projection_experience_view_ref(
    *,
    view_ref: str,
    experience_catalog: dict[str, _ProjectionExperienceOwnershipTruth],
    dependency_scope_label: str = "declared interface experience_package dependency scope",
) -> None:
    parsed = _split_projection_experience_view_ref(view_ref=view_ref)
    if parsed is None:
        raise ValueError(
            f"Interface pane view ref must use `experience.observable.view`: {view_ref!r}"
        )

    experience_name, observable_key, view_key = parsed
    experience_truth = experience_catalog.get(experience_name.casefold())
    if experience_truth is None:
        raise ValueError(
            "Interface pane view "
            + f"{view_ref!r} references unknown experience {experience_name!r} "
            + f"outside the {dependency_scope_label}"
        )

    observable = next(
        (
            item
            for item in experience_truth.ownership.observables
            if item.key.casefold() == observable_key.casefold()
        ),
        None,
    )
    if observable is None:
        raise ValueError(
            f"Interface pane view {view_ref!r} references unknown observable "
            + f"{observable_key!r} on experience {experience_truth.ownership.name!r}"
        )
    if not any(item.key.casefold() == view_key.casefold() for item in observable.views):
        raise ValueError(
            f"Interface pane view {view_ref!r} references unknown view "
            + f"{view_key!r} on {experience_truth.ownership.name!r}.{observable.key!r}"
        )


@dataclass(frozen=True, slots=True)
class _LayoutMountScope:
    section_keys: set[str]


def _layout_mount_scope(
    *,
    layout: InterfaceWindowLayoutOwnership,
    attention_layout_catalog: dict[str, InterfaceAttentionLayoutSnapshot],
) -> _LayoutMountScope:
    attention_layout = attention_layout_catalog.get(layout.key.casefold())
    if attention_layout is None:
        if attention_layout_catalog:
            raise ValueError(
                "Interface layout key is missing Attention-backed layout truth: "
                + f"{layout.key!r}"
            )
        if not layout.sections:
            raise ValueError(
                f"Interface layout {layout.key!r} must declare sections when no attention_package is linked"
            )
        return _LayoutMountScope(
            section_keys={section.key.casefold() for section in layout.sections},
        )
    if layout.sections:
        raise ValueError(
            "Attention-backed Interface layouts must not author structural topology. "
            + f"Layout {layout.key!r} still declares sections."
        )
    return _LayoutMountScope(
        section_keys={
            section.section_key.casefold() for section in attention_layout.sections
        },
    )


def _load_dart_pane_registrar_truths(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    plan: InterfaceCompilePlan,
) -> tuple[_DartPaneRegistrarTruth, ...]:
    in_scope_pane_names = {
        pane.pane_name.casefold()
        for interface in plan.interface_ownership
        for pane in interface.panes
    }
    registrar_truths: list[_DartPaneRegistrarTruth] = []
    for pane_package in snapshot.pane_packages:
        pane_name = (pane_package.spec.pane.pane_name or "").strip()
        if not pane_name or pane_name.casefold() not in in_scope_pane_names:
            continue
        dart_spec = pane_package.spec.dart
        if dart_spec is None or dart_spec.flutter is None:
            continue
        pane_package_name = (pane_package.spec.pane.package_name or "").strip()
        if not pane_package_name:
            raise ValueError(
                f"Pane package must declare a non-empty package_name: {pane_package.spec_path}"
            )
        registrar_truths.append(
            _DartPaneRegistrarTruth(
                pane_name=pane_name,
                pane_package_name=pane_package_name,
                library=dart_spec.flutter.library,
                symbol=dart_spec.flutter.symbol,
            )
        )
    return tuple(
        sorted(
            registrar_truths,
            key=lambda item: (
                item.pane_package_name.casefold(),
                item.library,
                item.symbol,
            ),
        )
    )


def _load_dart_render_component_registrar_truths(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
) -> tuple[_DartRenderComponentRegistrarTruth, ...]:
    registrar_truths: list[_DartRenderComponentRegistrarTruth] = []
    for render_component_package in snapshot.render_component_packages:
        dart_spec = render_component_package.spec.dart
        if dart_spec is None or dart_spec.flutter is None:
            continue
        package_name = (
            render_component_package.spec.render_component.package_name or ""
        ).strip()
        if not package_name:
            raise ValueError(
                "Render component package must declare a non-empty package_name: "
                + f"{render_component_package.spec_path}"
            )
        registrar_truths.append(
            _DartRenderComponentRegistrarTruth(
                render_component_package_name=package_name,
                library=dart_spec.flutter.library,
                symbol=dart_spec.flutter.symbol,
            )
        )
    return tuple(
        sorted(
            registrar_truths,
            key=lambda item: (
                item.render_component_package_name.casefold(),
                item.library,
                item.symbol,
            ),
        )
    )


def _resolve_dart_view_model_registry_truths(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    section_representations: tuple[_InterfaceRuntimeSectionRepresentationTruth, ...],
) -> tuple[_DartViewModelRegistryTruth, ...]:
    in_scope_experience_keys = {
        view_ref.split(".", 1)[0].casefold()
        for view_ref in (
            section.view_ref.strip() for section in section_representations
        )
        if view_ref
    }
    if not in_scope_experience_keys:
        return ()

    truths: dict[str, _DartViewModelRegistryTruth] = {}
    experience_packages_by_path: dict[Path, InterfaceExperiencePackageSnapshot] = {}
    for pane_package in snapshot.pane_packages:
        for experience_package in pane_package.experience_packages:
            experience_packages_by_path.setdefault(
                experience_package.spec_path.resolve(),
                experience_package,
            )
    for experience_package in experience_packages_by_path.values():
        ownership = load_projection_experience_ownership_from_sources(
            package_root=experience_package.package_root,
            source_files=experience_package.source_files,
        )
        if not any(
            experience.name.casefold() in in_scope_experience_keys
            for experience in ownership
        ):
            continue

        dart_target = experience_package.spec.targets.get("dart")
        root_dir = dart_target.root_dir if dart_target is not None else "languages/dart"
        package_dir = (
            dart_target.package_dir
            if dart_target is not None
            else (experience_package.spec.experience.fqn_prefix or "").strip()
        )
        if not package_dir:
            continue
        package_import_root = Path(package_dir).parts[-1]
        registry_path = (
            experience_package.package_root
            / root_dir
            / package_dir
            / "lib"
            / "view_model_registry.dart"
        )
        if not registry_path.exists():
            continue

        truths[package_import_root] = _DartViewModelRegistryTruth(
            package_name=package_import_root,
            library=f"package:{package_import_root}/{package_import_root}.dart",
            decoders_symbol=f"{_snake_to_camel(package_import_root)}ViewModelDecoders",
        )
    return tuple(sorted(truths.values(), key=lambda item: item.package_name.casefold()))


def _resolve_dart_api_view_state_decoder_truths(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    section_representations: tuple[_InterfaceRuntimeSectionRepresentationTruth, ...],
) -> tuple[_DartApiViewStateDecoderTruth, ...]:
    declared_dart_packages = _declared_api_dart_public_package_names(snapshot=snapshot)
    if not declared_dart_packages:
        return ()

    grouped_decoder_keys: dict[tuple[str, str], list[str]] = {}
    for section in section_representations:
        state_model_ref = (section.api_view_state_model_ref or "").strip()
        package_name = _dart_service_api_package_name_from_state_model_ref(
            state_model_ref
        )
        class_name = _dart_class_name_from_state_model_ref(state_model_ref)
        if package_name is None or class_name is None:
            continue
        if package_name not in declared_dart_packages:
            continue

        decoder_keys = grouped_decoder_keys.setdefault((package_name, class_name), [])
        for raw_key in (
            section.view_ref,
            section.projection_view_key,
            section.api_view_ref,
        ):
            key = (raw_key or "").strip()
            if key and key not in decoder_keys:
                decoder_keys.append(key)

    return tuple(
        _DartApiViewStateDecoderTruth(
            package_name=package_name,
            library=f"package:{package_name}/{package_name}.dart",
            class_name=class_name,
            decoder_keys=tuple(decoder_keys),
        )
        for (package_name, class_name), decoder_keys in sorted(
            grouped_decoder_keys.items(),
            key=lambda item: (item[0][0].casefold(), item[0][1].casefold()),
        )
        if decoder_keys
    )


def _declared_api_dart_public_package_names(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
) -> frozenset[str]:
    package_names: set[str] = set()
    for root in dict.fromkeys(
        (
            snapshot.workspace_root.resolve(),
            *_catalog_roots_for_snapshot(snapshot=snapshot),
        )
    ):
        if not root.is_dir():
            continue
        for toml_path in sorted(root.rglob("aware.api.toml")):
            if ".aware" in toml_path.parts:
                continue
            package_name = _declared_api_dart_public_package_name(toml_path=toml_path)
            if package_name is not None:
                package_names.add(package_name)
    return frozenset(package_names)


def _declared_api_dart_public_package_name(*, toml_path: Path) -> str | None:
    try:
        with toml_path.open("rb") as stream:
            raw = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError):
        return None

    targets = raw.get("targets")
    if not isinstance(targets, Mapping):
        return None
    dart = targets.get("dart")
    if not isinstance(dart, Mapping):
        return None
    public_package = dart.get("public_package")
    package_dir = (
        public_package.get("package_dir")
        if isinstance(public_package, Mapping)
        else None
    )
    if isinstance(package_dir, str) and package_dir.strip():
        return package_dir.strip()

    api = raw.get("api")
    fqn_prefix = api.get("fqn_prefix") if isinstance(api, Mapping) else None
    if isinstance(fqn_prefix, str) and fqn_prefix.strip():
        return fqn_prefix.strip()
    return None


def _dart_service_api_package_name_from_state_model_ref(
    state_model_ref: str,
) -> str | None:
    root = state_model_ref.split(".", 1)[0].strip()
    suffix = "_service_dto"
    if not root.endswith(suffix):
        return None
    return root[: -len(suffix)] + "_service_api"


def _dart_class_name_from_state_model_ref(state_model_ref: str) -> str | None:
    class_name = state_model_ref.rsplit(".", 1)[-1].strip()
    return class_name or None


_PANE_RENDER_NODE_KINDS = frozenset(item.value for item in PaneRenderNodeKind)
_PANE_RENDER_SEMANTIC_ROLES = frozenset(item.value for item in PaneRenderSemanticRole)
_PANE_RENDER_STATE_TARGETS = frozenset(
    item.value for item in PaneStateBindingTargetProperty
)
_PANE_RENDER_STATE_TRANSFORMS = frozenset(
    item.value for item in PaneStateBindingTransform
)
_PANE_RENDER_ACTION_EVENTS = frozenset(item.value for item in PaneActionEvent)


def _load_dart_pane_render_spec_truths(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    plan: InterfaceCompilePlan,
    projection_catalog: Mapping[str, ProjectionIdentityTruth] | None = None,
    state_model_catalog: Mapping[str, UUID] | None = None,
    state_attribute_catalog: Mapping[str, Mapping[str, UUID]] | None = None,
    api_view_catalog: Mapping[str, ApiViewStateTruth] | None = None,
) -> tuple[_DartPaneRenderSpecTruth, ...]:
    in_scope_pane_names = {
        pane.pane_name.casefold()
        for interface in plan.interface_ownership
        for pane in interface.panes
    }
    if not in_scope_pane_names:
        return ()

    pane_by_name = {pane.name.casefold(): pane for pane in plan.pane_ownership}
    pane_experience_catalogs = _load_pane_experience_catalogs(
        snapshot=snapshot,
        state_model_catalog=state_model_catalog,
        state_attribute_catalog=state_attribute_catalog,
        api_view_catalog=api_view_catalog,
    )
    resolved_projection_catalog = _resolve_projection_identity_catalog(
        snapshot=snapshot,
        projection_catalog=projection_catalog,
    )
    truths: list[_DartPaneRenderSpecTruth] = []
    for pane_package in snapshot.pane_packages:
        pane_name = (pane_package.spec.pane.pane_name or "").strip()
        if not pane_name or pane_name.casefold() not in in_scope_pane_names:
            continue
        pane = pane_by_name.get(pane_name.casefold())
        if pane is None:
            continue
        pane_experience_catalog = _pane_experience_catalog_for_name(
            pane_name=pane.name,
            pane_experience_catalogs=pane_experience_catalogs,
        )
        authored_truths = _load_authored_dart_pane_render_spec_truths(
            snapshot=snapshot,
            pane_package=pane_package,
            pane=pane,
            experience_catalog=pane_experience_catalog,
            projection_catalog=resolved_projection_catalog,
        )
        if authored_truths:
            truths.extend(authored_truths)
            continue
        if pane_package.render_spec_files:
            warnings.warn(
                "Pane package "
                + f"{pane_package.spec.pane.package_name!r} uses compatibility JSON render specs; "
                + "authored `.aware` render declarations are canonical.",
                PaneRenderSpecCompatibilityWarning,
                stacklevel=2,
            )
        for rel_path in pane_package.render_spec_files:
            source_path = (snapshot.repo_root / rel_path).resolve()
            payload = json.loads(source_path.read_text(encoding="utf-8") or "{}")
            if not isinstance(payload, dict):
                raise ValueError(
                    f"Pane render spec must be a JSON object: {source_path}"
                )
            truths.append(
                _build_dart_pane_render_spec_truth(
                    source_path=source_path,
                    source_relpath=rel_path.as_posix(),
                    source_kind="compatibility_json",
                    workspace_root=snapshot.repo_root,
                    pane=pane,
                    payload=cast(Mapping[str, object], payload),
                    experience_catalog=pane_experience_catalog,
                    projection_catalog=resolved_projection_catalog,
                )
            )
    return tuple(
        sorted(
            truths,
            key=lambda item: (
                item.pane_name.casefold(),
                item.view_ref.casefold(),
                str(item.payload.get("name") or "").casefold(),
                item.source_path,
            ),
        )
    )


def _load_authored_dart_pane_render_spec_truths(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    pane_package: InterfacePanePackageSnapshot,
    pane: InterfacePaneOwnership,
    experience_catalog: dict[str, _ProjectionExperienceOwnershipTruth],
    projection_catalog: Mapping[str, ProjectionIdentityTruth],
) -> tuple[_DartPaneRenderSpecTruth, ...]:
    truths: list[_DartPaneRenderSpecTruth] = []
    for rel_path in pane_package.source_files:
        source_path = (snapshot.repo_root / rel_path).resolve()
        _assert_workspace_file(
            workspace_root=snapshot.repo_root,
            source_path=source_path,
            label="pane source",
        )
        source_text = source_path.read_text(encoding="utf-8")
        for spec in parse_pane_render_specs(source_text):
            if spec.pane_name.casefold() != pane.name.casefold():
                continue
            payload = lower_pane_render_spec_to_payload(spec)
            truths.append(
                _build_dart_pane_render_spec_truth(
                    source_path=source_path,
                    source_relpath=f"{rel_path.as_posix()}#render:{spec.name}",
                    source_kind="authored_aware",
                    workspace_root=snapshot.repo_root,
                    pane=pane,
                    payload=payload,
                    experience_catalog=experience_catalog,
                    projection_catalog=projection_catalog,
                )
            )
    return tuple(truths)


def _encode_pane_render_spec_materialization(
    *,
    plan: InterfaceCompilePlan,
    render_spec_truths: tuple[_DartPaneRenderSpecTruth, ...],
) -> dict[str, object]:
    render_specs = [
        _encode_pane_render_spec_materialization_row(truth=truth)
        for truth in render_spec_truths
    ]
    commit_seed: dict[str, object] = {
        "schema_version": _PANE_RENDER_SPEC_MATERIALIZATION_SCHEMA_VERSION,
        "materialization_kind": _PANE_RENDER_SPEC_MATERIALIZATION_KIND,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "render_spec_count": len(render_specs),
        "render_specs": render_specs,
    }
    materialization_content_hash = _canonical_json_sha256(commit_seed)
    materialization_commit_id = _stable_pane_render_spec_materialization_commit_id(
        package_name=plan.package_name,
        fqn_prefix=plan.fqn_prefix,
        content_hash_sha256=materialization_content_hash,
    )
    return {
        "schema_version": _PANE_RENDER_SPEC_MATERIALIZATION_SCHEMA_VERSION,
        "materialization_kind": _PANE_RENDER_SPEC_MATERIALIZATION_KIND,
        "materialization_commit_id": str(materialization_commit_id),
        "materialization_content_hash_sha256": materialization_content_hash,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "render_spec_count": len(render_specs),
        "render_specs": render_specs,
    }


def _encode_pane_render_spec_materialization_row(
    *,
    truth: _DartPaneRenderSpecTruth,
) -> dict[str, object]:
    payload = dict(truth.payload)
    return {
        "source_path": truth.source_path,
        "source_kind": truth.source_kind,
        "pane_name": truth.pane_name,
        "pane_kind": truth.pane_kind,
        "view_ref": truth.view_ref,
        "projection_view_key": truth.projection_view_key,
        "render_spec_id": _require_materialized_string(payload, "payload", "spec_id"),
        "render_spec_content_hash_sha256": _canonical_json_sha256(payload),
        "semantic_object_ids": _pane_render_spec_semantic_object_ids(payload=payload),
        "payload": payload,
    }


def _stable_pane_render_spec_materialization_commit_id(
    *,
    package_name: str,
    fqn_prefix: str,
    content_hash_sha256: str,
) -> UUID:
    package_key = package_name.casefold().strip()
    fqn_key = fqn_prefix.casefold().strip()
    return uuid5(
        NAMESPACE_URL,
        "aware://interface/pane-render-spec-materialization/v1/"
        + f"{package_key}/{fqn_key}/{content_hash_sha256}",
    )


def _canonical_json_sha256(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def _pane_render_spec_semantic_object_ids(
    *, payload: Mapping[str, object]
) -> dict[str, object]:
    pane_render_spec_id = UUID(
        _require_materialized_string(payload, "payload", "spec_id")
    )
    node_ids: dict[str, str] = {}
    state_binding_ids: dict[str, str] = {}
    action_binding_ids: dict[str, str] = {}
    input_binding_ids: dict[str, str] = {}
    style_token_ids: dict[str, str] = {}
    renderer_requirement_ids: dict[str, str] = {}

    raw_nodes = payload.get("nodes")
    if not isinstance(raw_nodes, list):
        raise ValueError(
            "Pane render spec materialization payload.nodes must be a list"
        )
    for index, raw_node in enumerate(raw_nodes):
        if not isinstance(raw_node, dict):
            raise ValueError(
                f"Pane render spec materialization payload.nodes[{index}] must be an object"
            )
        node = cast(Mapping[str, object], raw_node)
        node_key = _require_materialized_string(
            node, f"payload.nodes[{index}]", "node_key"
        )
        pane_render_node_id = stable_pane_render_node_id(
            pane_render_spec_id=pane_render_spec_id,
            node_key=node_key,
        )
        node_ids[node_key] = str(pane_render_node_id)

        raw_state_bindings = node.get("state_bindings")
        if isinstance(raw_state_bindings, list):
            for binding_index, raw_binding in enumerate(raw_state_bindings):
                if not isinstance(raw_binding, dict):
                    raise ValueError(
                        "Pane render spec materialization "
                        + f"payload.nodes[{index}].state_bindings[{binding_index}] must be an object"
                    )
                binding = cast(Mapping[str, object], raw_binding)
                binding_key = _require_materialized_string(
                    binding,
                    f"payload.nodes[{index}].state_bindings[{binding_index}]",
                    "binding_key",
                )
                state_binding_ids[f"{node_key}.{binding_key}"] = str(
                    stable_pane_state_binding_id(
                        pane_render_node_id=pane_render_node_id,
                        binding_key=binding_key,
                    )
                )
        elif raw_state_bindings is not None:
            raise ValueError(
                f"Pane render spec materialization payload.nodes[{index}].state_bindings must be a list"
            )

        raw_action_bindings = node.get("action_bindings")
        if isinstance(raw_action_bindings, list):
            for binding_index, raw_binding in enumerate(raw_action_bindings):
                if not isinstance(raw_binding, dict):
                    raise ValueError(
                        "Pane render spec materialization "
                        + f"payload.nodes[{index}].action_bindings[{binding_index}] must be an object"
                    )
                binding = cast(Mapping[str, object], raw_binding)
                binding_key = _require_materialized_string(
                    binding,
                    f"payload.nodes[{index}].action_bindings[{binding_index}]",
                    "binding_key",
                )
                pane_action_binding_id = stable_pane_action_binding_id(
                    pane_render_node_id=pane_render_node_id,
                    binding_key=binding_key,
                )
                action_binding_ids[f"{node_key}.{binding_key}"] = str(
                    pane_action_binding_id
                )

                raw_input_bindings = binding.get("input_bindings")
                if isinstance(raw_input_bindings, list):
                    for input_index, raw_input in enumerate(raw_input_bindings):
                        if not isinstance(raw_input, dict):
                            raise ValueError(
                                "Pane render spec materialization "
                                + f"payload.nodes[{index}].action_bindings[{binding_index}]"
                                + f".input_bindings[{input_index}] must be an object"
                            )
                        input_binding = cast(Mapping[str, object], raw_input)
                        payload_path = _require_materialized_string(
                            input_binding,
                            (
                                f"payload.nodes[{index}].action_bindings[{binding_index}]"
                                + f".input_bindings[{input_index}]"
                            ),
                            "payload_path",
                        )
                        input_binding_ids[
                            f"{node_key}.{binding_key}.{payload_path}"
                        ] = str(
                            stable_pane_input_binding_id(
                                pane_action_binding_id=pane_action_binding_id,
                                payload_path=payload_path,
                            )
                        )
                elif raw_input_bindings is not None:
                    raise ValueError(
                        "Pane render spec materialization "
                        + f"payload.nodes[{index}].action_bindings[{binding_index}].input_bindings must be a list"
                    )
        elif raw_action_bindings is not None:
            raise ValueError(
                f"Pane render spec materialization payload.nodes[{index}].action_bindings must be a list"
            )

        raw_style_tokens = node.get("style_tokens")
        if isinstance(raw_style_tokens, list):
            for token_index, raw_token in enumerate(raw_style_tokens):
                if not isinstance(raw_token, dict):
                    raise ValueError(
                        "Pane render spec materialization "
                        + f"payload.nodes[{index}].style_tokens[{token_index}] must be an object"
                    )
                token = cast(Mapping[str, object], raw_token)
                token_key = _require_materialized_string(
                    token,
                    f"payload.nodes[{index}].style_tokens[{token_index}]",
                    "token_key",
                )
                style_token_ids[f"{node_key}.{token_key}"] = str(
                    stable_pane_style_token_ref_id(
                        pane_render_node_id=pane_render_node_id,
                        token_key=token_key,
                    )
                )
        elif raw_style_tokens is not None:
            raise ValueError(
                f"Pane render spec materialization payload.nodes[{index}].style_tokens must be a list"
            )

    raw_renderer_requirements = payload.get("renderer_requirements")
    if isinstance(raw_renderer_requirements, list):
        for index, raw_requirement in enumerate(raw_renderer_requirements):
            if not isinstance(raw_requirement, dict):
                raise ValueError(
                    f"Pane render spec materialization payload.renderer_requirements[{index}] must be an object"
                )
            requirement = cast(Mapping[str, object], raw_requirement)
            capability_kind = _require_materialized_string(
                requirement,
                f"payload.renderer_requirements[{index}]",
                "capability_kind",
            )
            capability_key = _require_materialized_string(
                requirement,
                f"payload.renderer_requirements[{index}]",
                "capability_key",
            )
            renderer_requirement_ids[f"{capability_kind}:{capability_key}"] = str(
                stable_pane_renderer_capability_requirement_id(
                    pane_render_spec_id=pane_render_spec_id,
                    capability_kind=capability_kind,
                    capability_key=capability_key,
                )
            )
    elif raw_renderer_requirements is not None:
        raise ValueError(
            "Pane render spec materialization payload.renderer_requirements must be a list"
        )

    return {
        "pane_render_spec_id": str(pane_render_spec_id),
        "pane_render_node_ids_by_key": node_ids,
        "pane_state_binding_ids_by_ref": state_binding_ids,
        "pane_action_binding_ids_by_ref": action_binding_ids,
        "pane_input_binding_ids_by_ref": input_binding_ids,
        "pane_style_token_ref_ids_by_ref": style_token_ids,
        "pane_renderer_capability_requirement_ids_by_ref": renderer_requirement_ids,
    }


def _require_materialized_string(
    payload: Mapping[str, object], context: str, key: str
) -> str:
    value = payload.get(key)
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            return normalized
    raise ValueError(
        f"Pane render spec materialization {context} must declare non-empty {key!r}"
    )


def _validate_pane_render_spec_materialization_commit(
    *,
    payload: Mapping[str, object],
    materialization_path: Path,
    rows: list[object],
) -> None:
    materialization_kind = _require_materialized_string(
        payload,
        str(materialization_path),
        "materialization_kind",
    )
    if materialization_kind != _PANE_RENDER_SPEC_MATERIALIZATION_KIND:
        raise ValueError(
            "Pane render spec materialization has unsupported materialization_kind "
            + f"{materialization_kind!r}: {materialization_path}"
        )
    package_name = _require_materialized_string(
        payload,
        str(materialization_path),
        "package_name",
    )
    fqn_prefix = _require_materialized_string(
        payload,
        str(materialization_path),
        "fqn_prefix",
    )
    expected_count = payload.get("render_spec_count")
    if not isinstance(expected_count, int) or isinstance(expected_count, bool):
        raise ValueError(
            "Pane render spec materialization must declare integer render_spec_count: "
            + str(materialization_path)
        )
    if expected_count != len(rows):
        raise ValueError(
            "Pane render spec materialization render_spec_count mismatch: "
            + f"expected={expected_count} actual={len(rows)} path={materialization_path}"
        )

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(
                f"Pane render spec materialization render_specs[{index}] must be an object: {materialization_path}"
            )
        raw = cast(Mapping[str, object], row)
        render_payload = raw.get("payload")
        if not isinstance(render_payload, dict):
            raise ValueError(
                f"Pane render spec materialization render_specs[{index}].payload must be an object: "
                + str(materialization_path)
            )
        render_spec_id = _require_materialized_string(
            raw,
            f"render_specs[{index}]",
            "render_spec_id",
        )
        payload_spec_id = _require_materialized_string(
            cast(Mapping[str, object], render_payload),
            f"render_specs[{index}].payload",
            "spec_id",
        )
        if render_spec_id != payload_spec_id:
            raise ValueError(
                "Pane render spec materialization render_spec_id mismatch: "
                + f"render_specs[{index}] expected={payload_spec_id} actual={render_spec_id} "
                + f"path={materialization_path}"
            )
        expected_render_hash = _require_materialized_string(
            raw,
            f"render_specs[{index}]",
            "render_spec_content_hash_sha256",
        )
        actual_render_hash = _canonical_json_sha256(
            cast(Mapping[str, object], render_payload)
        )
        if expected_render_hash != actual_render_hash:
            raise ValueError(
                "Pane render spec materialization render spec hash mismatch: "
                + f"render_specs[{index}] expected={expected_render_hash} actual={actual_render_hash} "
                + f"path={materialization_path}"
            )
        expected_object_ids = raw.get("semantic_object_ids")
        actual_object_ids = _pane_render_spec_semantic_object_ids(
            payload=cast(Mapping[str, object], render_payload),
        )
        if expected_object_ids != actual_object_ids:
            raise ValueError(
                "Pane render spec materialization semantic object ids mismatch: "
                + f"render_specs[{index}] path={materialization_path}"
            )

    commit_seed: dict[str, object] = {
        "schema_version": _PANE_RENDER_SPEC_MATERIALIZATION_SCHEMA_VERSION,
        "materialization_kind": materialization_kind,
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "render_spec_count": len(rows),
        "render_specs": rows,
    }
    expected_content_hash = _require_materialized_string(
        payload,
        str(materialization_path),
        "materialization_content_hash_sha256",
    )
    actual_content_hash = _canonical_json_sha256(commit_seed)
    if expected_content_hash != actual_content_hash:
        raise ValueError(
            "Pane render spec materialization content hash mismatch: "
            + f"expected={expected_content_hash} actual={actual_content_hash} path={materialization_path}"
        )
    expected_commit_id = str(
        _stable_pane_render_spec_materialization_commit_id(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            content_hash_sha256=expected_content_hash,
        )
    )
    actual_commit_id = _require_materialized_string(
        payload,
        str(materialization_path),
        "materialization_commit_id",
    )
    if actual_commit_id != expected_commit_id:
        raise ValueError(
            "Pane render spec materialization commit id mismatch: "
            + f"expected={expected_commit_id} actual={actual_commit_id} path={materialization_path}"
        )


def _load_dart_pane_render_spec_truths_from_materialization_artifact(
    *,
    materialization_path: Path,
) -> tuple[_DartPaneRenderSpecTruth, ...]:
    materialization_path = materialization_path.resolve()
    payload = json.loads(materialization_path.read_text(encoding="utf-8") or "{}")
    if not isinstance(payload, dict):
        raise ValueError(
            f"Pane render spec materialization must be a JSON object: {materialization_path}"
        )
    schema_version = payload.get("schema_version")
    if schema_version not in (1, _PANE_RENDER_SPEC_MATERIALIZATION_SCHEMA_VERSION):
        raise ValueError(
            "Pane render spec materialization has unsupported schema_version "
            + f"{schema_version!r}: {materialization_path}"
        )
    rows = payload.get("render_specs")
    if not isinstance(rows, list):
        raise ValueError(
            f"Pane render spec materialization must declare render_specs: {materialization_path}"
        )
    if schema_version == _PANE_RENDER_SPEC_MATERIALIZATION_SCHEMA_VERSION:
        _validate_pane_render_spec_materialization_commit(
            payload=cast(Mapping[str, object], payload),
            materialization_path=materialization_path,
            rows=rows,
        )

    truths: list[_DartPaneRenderSpecTruth] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(
                f"Pane render spec materialization render_specs[{index}] must be an object: {materialization_path}"
            )
        raw = cast(Mapping[str, object], row)
        render_payload = raw.get("payload")
        if not isinstance(render_payload, dict):
            raise ValueError(
                f"Pane render spec materialization render_specs[{index}].payload must be an object: "
                + str(materialization_path)
            )
        truths.append(
            _DartPaneRenderSpecTruth(
                source_path=_require_payload_string(
                    raw, materialization_path, f"render_specs[{index}]", "source_path"
                ),
                source_kind=_require_payload_string(
                    raw, materialization_path, f"render_specs[{index}]", "source_kind"
                ),
                pane_name=_require_payload_string(
                    raw, materialization_path, f"render_specs[{index}]", "pane_name"
                ),
                pane_kind=_require_payload_string(
                    raw, materialization_path, f"render_specs[{index}]", "pane_kind"
                ),
                view_ref=_require_payload_string(
                    raw, materialization_path, f"render_specs[{index}]", "view_ref"
                ),
                projection_view_key=_require_payload_string(
                    raw,
                    materialization_path,
                    f"render_specs[{index}]",
                    "projection_view_key",
                ),
                payload=cast(Mapping[str, object], render_payload),
            )
        )
    return tuple(
        sorted(
            truths,
            key=lambda item: (
                item.pane_name.casefold(),
                item.view_ref.casefold(),
                str(item.payload.get("name") or "").casefold(),
                item.source_path,
            ),
        )
    )


def _build_dart_pane_render_spec_truth(
    *,
    source_path: Path,
    source_relpath: str,
    source_kind: str,
    workspace_root: Path,
    pane: InterfacePaneOwnership,
    payload: Mapping[str, object],
    experience_catalog: dict[str, _ProjectionExperienceOwnershipTruth],
    projection_catalog: Mapping[str, ProjectionIdentityTruth],
) -> _DartPaneRenderSpecTruth:
    payload_pane_name = _payload_string(payload, "pane_name", "paneName")
    if (
        payload_pane_name is not None
        and payload_pane_name.casefold() != pane.name.casefold()
    ):
        raise ValueError(
            "Pane render spec pane_name does not match canonical pane declaration: "
            + f"{source_path} declares {payload_pane_name!r}, expected {pane.name!r}"
        )

    view_ref = _payload_string(
        payload, "view_ref", "viewRef"
    ) or _default_pane_view_ref(
        pane=pane,
        source_path=source_path,
    )
    if not any(view.ref.casefold() == view_ref.casefold() for view in pane.views):
        raise ValueError(
            f"Pane render spec {source_path} references view {view_ref!r} "
            + f"that pane {pane.name!r} does not declare"
        )

    projection_view_truth = _resolve_projection_experience_view_truth(
        workspace_root=workspace_root,
        view_ref=view_ref,
        experience_catalog=experience_catalog,
        projection_catalog=projection_catalog,
        dependency_scope_label="declared pane experience_package dependency scope",
    )
    pane_config_id = stable_pane_config_id(
        name=pane.name,
        projection_experience_view_id=projection_view_truth.projection_experience_view_id,
    )
    name = _payload_string(payload, "name") or f"{pane.name}_default"
    spec_version = (
        _payload_string(payload, "spec_version", "specVersion", "version") or "0.1.0"
    )
    spec_id = stable_pane_render_spec_id(
        pane_config_id=pane_config_id,
        name=name,
        spec_version=spec_version,
    )
    explicit_spec_id = _payload_string(payload, "spec_id", "specId")
    if explicit_spec_id is not None and explicit_spec_id != str(spec_id):
        raise ValueError(
            f"Pane render spec {source_path} declares spec_id {explicit_spec_id!r}; "
            + f"expected stable id {spec_id}"
        )

    root_node_key = _payload_string(payload, "root_node_key", "rootNodeKey") or "root"
    nodes = _normalize_dart_pane_render_nodes(
        raw_nodes=payload.get("nodes"),
        projection_experience_id=projection_view_truth.projection_experience_id,
        projection_experience_view_id=projection_view_truth.projection_experience_view_id,
        state_model_id=projection_view_truth.state_model_id,
        state_model_ref=projection_view_truth.state_model_ref,
        state_attribute_ids_by_ref=projection_view_truth.state_attribute_ids_by_ref,
        pane=pane,
        pane_config_id=pane_config_id,
        workspace_root=workspace_root,
        projection_view_actions={
            action.key.casefold(): action
            for action in projection_view_truth.invocation_actions
        },
        api_view_truth=projection_view_truth.api_view_truth,
        source_path=source_path,
    )
    if not any(node.get("node_key") == root_node_key for node in nodes):
        raise ValueError(
            f"Pane render spec {source_path} root_node_key {root_node_key!r} was not found in nodes"
        )

    spec_payload: dict[str, object] = {
        "spec_id": str(spec_id),
        "name": name,
        "spec_version": spec_version,
        "pane_name": pane.name,
        "pane_kind": pane.pane_kind,
        "view_ref": view_ref,
        "projection_view_key": projection_view_truth.projection_view_key,
        "pane_config_id": str(pane_config_id),
        "projection_experience_view_id": str(
            projection_view_truth.projection_experience_view_id
        ),
        "state_model_id": str(projection_view_truth.state_model_id),
        "root_node_key": root_node_key,
        "nodes": list(nodes),
        "renderer_requirements": list(
            _normalize_dart_pane_renderer_requirements(
                raw_requirements=payload.get("renderer_requirements")
                or payload.get("rendererRequirements"),
                source_path=source_path,
            )
        ),
    }
    description = _payload_string(payload, "description")
    if description is not None:
        spec_payload["description"] = description

    return _DartPaneRenderSpecTruth(
        source_path=source_relpath,
        source_kind=source_kind,
        pane_name=pane.name,
        pane_kind=pane.pane_kind,
        view_ref=view_ref,
        projection_view_key=projection_view_truth.projection_view_key,
        payload=spec_payload,
    )


def _default_pane_view_ref(*, pane: InterfacePaneOwnership, source_path: Path) -> str:
    default_views = tuple(view.ref for view in pane.views if view.is_default)
    if len(default_views) == 1:
        return default_views[0]
    if len(pane.views) == 1:
        return pane.views[0].ref
    raise ValueError(
        f"Pane render spec {source_path} must declare view_ref because pane {pane.name!r} "
        + f"has {len(pane.views)} declared views and {len(default_views)} defaults"
    )


def _normalize_dart_pane_render_nodes(
    *,
    raw_nodes: object,
    projection_experience_id: UUID,
    projection_experience_view_id: UUID,
    state_model_id: UUID,
    state_model_ref: str,
    state_attribute_ids_by_ref: Mapping[str, UUID],
    pane: InterfacePaneOwnership,
    pane_config_id: UUID,
    workspace_root: Path,
    projection_view_actions: Mapping[
        str, ExperienceProjectionViewInvocationActionOwnership
    ],
    api_view_truth: ApiViewStateTruth | None,
    source_path: Path,
) -> tuple[dict[str, object], ...]:
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ValueError(
            f"Pane render spec {source_path} must declare a non-empty nodes list"
        )

    nodes: list[dict[str, object]] = []
    node_keys: set[str] = set()
    parent_refs: list[tuple[str, str]] = []
    for index, raw_node in enumerate(raw_nodes):
        if not isinstance(raw_node, dict):
            raise ValueError(
                f"Pane render spec {source_path} node #{index} must be a JSON object"
            )
        raw = cast(Mapping[str, object], raw_node)
        node_key = _require_payload_string(
            raw, source_path, f"nodes[{index}]", "node_key", "nodeKey"
        )
        if node_key.casefold() in node_keys:
            raise ValueError(
                f"Pane render spec {source_path} duplicates node_key {node_key!r}"
            )
        node_keys.add(node_key.casefold())

        node_kind = _require_payload_string(
            raw, source_path, f"nodes[{index}]", "node_kind", "nodeKind"
        )
        if node_kind not in _PANE_RENDER_NODE_KINDS:
            raise ValueError(
                f"Pane render spec {source_path} node {node_key!r} uses unknown node_kind {node_kind!r}"
            )

        order = _payload_int(raw, "order")
        node: dict[str, object] = {
            "node_key": node_key,
            "node_kind": node_kind,
            "order": order if order is not None else index,
        }
        parent_node_key = _payload_string(raw, "parent_node_key", "parentNodeKey")
        if parent_node_key is not None:
            node["parent_node_key"] = parent_node_key
            parent_refs.append((node_key, parent_node_key))
        semantic_role = _payload_string(raw, "semantic_role", "semanticRole")
        if semantic_role is not None:
            if semantic_role not in _PANE_RENDER_SEMANTIC_ROLES:
                raise ValueError(
                    f"Pane render spec {source_path} node {node_key!r} "
                    + f"uses unknown semantic_role {semantic_role!r}"
                )
            node["semantic_role"] = semantic_role
        for key in ("slot_key", "label", "text", "placeholder"):
            value = _payload_string(raw, key, _snake_to_camel(key))
            if value is not None:
                node[key] = value
        for key in (
            "component_ref",
            "component_contract_id",
            "fallback_node_kind",
            "fallback_text",
        ):
            value = _payload_string(raw, key, _snake_to_camel(key))
            if value is not None:
                if key == "fallback_node_kind" and value not in _PANE_RENDER_NODE_KINDS:
                    raise ValueError(
                        f"Pane render spec {source_path} node {node_key!r} "
                        + f"uses unknown fallback_node_kind {value!r}"
                    )
                node[key] = value

        state_bindings = _normalize_dart_pane_state_bindings(
            raw_bindings=raw.get("state_bindings") or raw.get("stateBindings"),
            state_model_id=state_model_id,
            state_model_ref=state_model_ref,
            state_attribute_ids_by_ref=state_attribute_ids_by_ref,
            source_path=source_path,
            node_key=node_key,
        )
        if state_bindings:
            node["state_bindings"] = list(state_bindings)
        action_bindings = _normalize_dart_pane_action_bindings(
            raw_bindings=raw.get("action_bindings") or raw.get("actionBindings"),
            projection_experience_id=projection_experience_id,
            projection_experience_view_id=projection_experience_view_id,
            projection_view_actions=projection_view_actions,
            api_view_truth=api_view_truth,
            source_path=source_path,
            node_key=node_key,
        )
        if action_bindings:
            node["action_bindings"] = list(action_bindings)
        style_tokens = _normalize_dart_pane_style_tokens(
            raw_tokens=raw.get("style_tokens") or raw.get("styleTokens"),
            source_path=source_path,
            node_key=node_key,
        )
        if style_tokens:
            node["style_tokens"] = list(style_tokens)
        nodes.append(node)

    for node_key, parent_node_key in parent_refs:
        if parent_node_key.casefold() not in node_keys:
            raise ValueError(
                f"Pane render spec {source_path} node {node_key!r} references missing parent_node_key "
                + f"{parent_node_key!r}"
            )
    return tuple(nodes)


def _normalize_dart_pane_state_bindings(
    *,
    raw_bindings: object,
    state_model_id: UUID,
    state_model_ref: str,
    state_attribute_ids_by_ref: Mapping[str, UUID],
    source_path: Path,
    node_key: str,
) -> tuple[dict[str, object], ...]:
    if raw_bindings is None:
        return ()
    if not isinstance(raw_bindings, list):
        raise ValueError(
            f"Pane render spec {source_path} node {node_key!r} state_bindings must be a list"
        )
    bindings: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, raw_binding in enumerate(raw_bindings):
        if not isinstance(raw_binding, dict):
            raise ValueError(
                f"Pane render spec {source_path} node {node_key!r} state_bindings[{index}] must be a JSON object"
            )
        raw = cast(Mapping[str, object], raw_binding)
        binding_key = _require_payload_string(
            raw,
            source_path,
            f"{node_key}.state_bindings[{index}]",
            "binding_key",
            "bindingKey",
        )
        if binding_key.casefold() in seen:
            raise ValueError(
                f"Pane render spec {source_path} node {node_key!r} duplicates state binding {binding_key!r}"
            )
        seen.add(binding_key.casefold())
        target_property = _require_payload_string(
            raw,
            source_path,
            f"{node_key}.state_bindings[{index}]",
            "target_property",
            "targetProperty",
        )
        if target_property not in _PANE_RENDER_STATE_TARGETS:
            raise ValueError(
                f"Pane render spec {source_path} state binding {binding_key!r} "
                + f"uses unknown target_property {target_property!r}"
            )
        transform = _payload_string(raw, "transform") or "raw"
        if transform not in _PANE_RENDER_STATE_TRANSFORMS:
            raise ValueError(
                f"Pane render spec {source_path} state binding {binding_key!r} "
                + f"uses unknown transform {transform!r}"
            )
        binding: dict[str, object] = {
            "binding_key": binding_key,
            "target_property": target_property,
            "json_path": _require_payload_string(
                raw,
                source_path,
                f"{node_key}.state_bindings[{index}]",
                "json_path",
                "jsonPath",
            ),
            "state_model_id": _payload_string(raw, "state_model_id", "stateModelId")
            or str(state_model_id),
            "transform": transform,
        }
        state_attribute_config_id = _payload_string(
            raw, "state_attribute_config_id", "stateAttributeConfigId"
        )
        state_attribute_ref = _payload_string(
            raw,
            "state_attribute_ref",
            "stateAttributeRef",
            "attribute_ref",
            "attributeRef",
        )
        resolved_state_attribute_config_id = _resolve_state_attribute_config_id(
            source_path=source_path,
            binding_key=binding_key,
            state_model_ref=state_model_ref,
            state_attribute_ref=state_attribute_ref,
            state_attribute_config_id=state_attribute_config_id,
            state_attribute_ids_by_ref=state_attribute_ids_by_ref,
        )
        if resolved_state_attribute_config_id is not None:
            binding["state_attribute_ref"] = (
                state_attribute_ref
                or _attribute_ref_from_json_path(
                    _require_payload_string(
                        raw,
                        source_path,
                        f"{node_key}.state_bindings[{index}]",
                        "json_path",
                        "jsonPath",
                    )
                )
            )
            state_attribute_config_id = str(resolved_state_attribute_config_id)
            binding["state_attribute_config_id"] = state_attribute_config_id
        fallback_value = _payload_string(raw, "fallback_value", "fallbackValue")
        if fallback_value is not None:
            binding["fallback_value"] = fallback_value
        component_input_port_key = _payload_string(
            raw,
            "component_input_port_key",
            "componentInputPortKey",
        )
        if component_input_port_key is not None:
            binding["component_input_port_key"] = component_input_port_key
        bindings.append(binding)
    return tuple(bindings)


def _resolve_state_attribute_config_id(
    *,
    source_path: Path,
    binding_key: str,
    state_model_ref: str,
    state_attribute_ref: str | None,
    state_attribute_config_id: str | None,
    state_attribute_ids_by_ref: Mapping[str, UUID],
) -> UUID | None:
    if state_attribute_ref is None:
        if state_attribute_config_id is None:
            return None
        try:
            return UUID(state_attribute_config_id)
        except ValueError as exc:
            raise ValueError(
                f"Pane render spec {source_path} state binding {binding_key!r} "
                + f"declares invalid state_attribute_config_id {state_attribute_config_id!r}"
            ) from exc

    resolved = state_attribute_ids_by_ref.get(state_attribute_ref.casefold())
    if resolved is None:
        available_refs = tuple(sorted(state_attribute_ids_by_ref)[:12])
        raise ValueError(
            f"Pane render spec {source_path} state binding {binding_key!r} "
            + f"references unknown state attribute {state_attribute_ref!r} on {state_model_ref!r}; "
            + f"available_state_attribute_refs={available_refs!r}"
        )
    if state_attribute_config_id is not None and state_attribute_config_id != str(
        resolved
    ):
        raise ValueError(
            f"Pane render spec {source_path} state binding {binding_key!r} "
            + f"declares state_attribute_config_id {state_attribute_config_id!r} that does not match "
            + f"state_attribute_ref {state_attribute_ref!r} ({resolved})"
        )
    return resolved


def _attribute_ref_from_json_path(json_path: str) -> str:
    normalized = json_path.strip().replace("$.", "", 1).replace("$", "", 1)
    return normalized.split(".", 1)[0].strip()


def _normalize_dart_pane_action_bindings(
    *,
    raw_bindings: object,
    projection_experience_id: UUID,
    projection_experience_view_id: UUID,
    projection_view_actions: Mapping[
        str, ExperienceProjectionViewInvocationActionOwnership
    ],
    api_view_truth: ApiViewStateTruth | None,
    source_path: Path,
    node_key: str,
) -> tuple[dict[str, object], ...]:
    if raw_bindings is None:
        return ()
    if not isinstance(raw_bindings, list):
        raise ValueError(
            f"Pane render spec {source_path} node {node_key!r} action_bindings must be a list"
        )
    bindings: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, raw_binding in enumerate(raw_bindings):
        if not isinstance(raw_binding, dict):
            raise ValueError(
                f"Pane render spec {source_path} node {node_key!r} action_bindings[{index}] must be a JSON object"
            )
        raw = cast(Mapping[str, object], raw_binding)
        binding_key = _require_payload_string(
            raw,
            source_path,
            f"{node_key}.action_bindings[{index}]",
            "binding_key",
            "bindingKey",
        )
        if binding_key.casefold() in seen:
            raise ValueError(
                f"Pane render spec {source_path} node {node_key!r} duplicates action binding {binding_key!r}"
            )
        seen.add(binding_key.casefold())
        action_key = _payload_string(raw, "action_key", "actionKey")
        view_action_key = _payload_string(raw, "view_action_key", "viewActionKey")
        if (
            action_key is not None
            and view_action_key is not None
            and action_key.casefold() == view_action_key.casefold()
        ):
            action_key = None
        binding = _resolve_dart_pane_action_binding(
            action_key=action_key,
            view_action_key=view_action_key,
            sdk_operation_ref=_payload_string(
                raw,
                "sdk_operation_ref",
                "sdkOperationRef",
                "operation_ref",
                "operationRef",
            ),
            api_endpoint_ref=_payload_string(
                raw,
                "api_endpoint_ref",
                "apiEndpointRef",
                "endpoint_ref",
                "endpointRef",
            ),
            projection_view_actions=projection_view_actions,
            api_view_truth=api_view_truth,
            projection_experience_id=projection_experience_id,
            projection_experience_view_id=projection_experience_view_id,
            source_path=source_path,
            binding_key=binding_key,
        )
        event = _payload_string(raw, "event") or "activate"
        if event not in _PANE_RENDER_ACTION_EVENTS:
            raise ValueError(
                f"Pane render spec {source_path} action binding {binding_key!r} uses unknown event {event!r}"
            )
        binding["binding_key"] = binding_key
        binding["event"] = event
        for key in (
            "label",
            "confirmation_policy",
            "optimistic_policy",
            "receipt_policy",
        ):
            value = _payload_string(raw, key, _snake_to_camel(key))
            if value is not None:
                binding[key] = value
        input_bindings = _normalize_dart_pane_input_bindings(
            raw_bindings=raw.get("input_bindings") or raw.get("inputBindings"),
            source_path=source_path,
            binding_key=binding_key,
        )
        if input_bindings:
            binding["input_bindings"] = list(input_bindings)
        bindings.append(binding)
    return tuple(bindings)


def _resolve_dart_pane_action_binding(
    *,
    action_key: str | None,
    view_action_key: str | None,
    sdk_operation_ref: str | None,
    api_endpoint_ref: str | None,
    projection_view_actions: Mapping[
        str, ExperienceProjectionViewInvocationActionOwnership
    ],
    api_view_truth: ApiViewStateTruth | None,
    projection_experience_id: UUID,
    projection_experience_view_id: UUID,
    source_path: Path,
    binding_key: str,
) -> dict[str, object]:
    if sdk_operation_ref is not None or api_endpoint_ref is not None:
        raise ValueError(
            f"Pane render spec {source_path} action binding {binding_key!r} "
            + "must bind an Experience view action; direct API/SDK pane targets are not supported"
        )
    if view_action_key is None and action_key is not None:
        raise ValueError(
            f"Pane render spec {source_path} action binding {binding_key!r} "
            + "declares action_key without view_action_key"
        )
    if view_action_key is None:
        raise ValueError(
            f"Pane render spec {source_path} action binding {binding_key!r} "
            + "must declare view_action_key"
        )

    view_action = projection_view_actions.get(view_action_key.casefold())
    if view_action is None:
        available_actions = tuple(sorted(projection_view_actions)[:12])
        raise ValueError(
            f"Pane render spec {source_path} action binding {binding_key!r} "
            + f"references unknown Experience view action {view_action_key!r}; "
            + f"available_view_actions={available_actions!r}"
        )
    action_kind, target_ref = _projection_view_invocation_action_target(view_action)
    render_action_kind = "view_action" if action_kind == "view" else action_kind
    binding: dict[str, object] = {
        "action_key": view_action.key,
        "action_kind": render_action_kind,
        "view_action_key": view_action.key,
        "projection_experience_view_invocation_action_id": str(
            _projection_view_invocation_action_config_id(
                projection_experience_view_id=projection_experience_view_id,
                action=view_action,
            )
        ),
    }
    if action_kind != "view":
        binding["target_ref"] = target_ref
    if action_kind == "sdk":
        binding["operation_ref"] = target_ref
    elif action_kind == "api":
        binding["endpoint_ref"] = target_ref
    for policy_key, policy_value in (
        ("label", view_action.label),
        ("receipt_policy", view_action.receipt_policy),
        ("confirmation_policy", view_action.confirmation_policy),
        ("optimistic_policy", view_action.optimistic_policy),
    ):
        if policy_value is not None:
            binding[policy_key] = policy_value
    return binding


def _normalize_dart_pane_input_bindings(
    *,
    raw_bindings: object,
    source_path: Path,
    binding_key: str,
) -> tuple[dict[str, object], ...]:
    if raw_bindings is None:
        return ()
    if not isinstance(raw_bindings, list):
        raise ValueError(
            f"Pane render spec {source_path} action {binding_key!r} input_bindings must be a list"
        )
    bindings: list[dict[str, object]] = []
    for index, raw_binding in enumerate(raw_bindings):
        if not isinstance(raw_binding, dict):
            raise ValueError(
                f"Pane render spec {source_path} action {binding_key!r} input_bindings[{index}] must be a JSON object"
            )
        raw = cast(Mapping[str, object], raw_binding)
        binding: dict[str, object] = {
            "payload_path": _require_payload_string(
                raw,
                source_path,
                f"{binding_key}.input_bindings[{index}]",
                "payload_path",
                "payloadPath",
            )
        }
        source_node_key = _payload_string(raw, "source_node_key", "sourceNodeKey")
        source_json_path = _payload_string(raw, "source_json_path", "sourceJsonPath")
        literal_value = _payload_string(raw, "literal_value", "literalValue")
        if (
            source_node_key is None
            and source_json_path is None
            and literal_value is None
        ):
            raise ValueError(
                f"Pane render spec {source_path} action {binding_key!r} input binding "
                + f"{binding['payload_path']!r} must declare a source"
            )
        if source_node_key is not None:
            binding["source_node_key"] = source_node_key
        if source_json_path is not None:
            binding["source_json_path"] = source_json_path
        if literal_value is not None:
            binding["literal_value"] = literal_value
        bindings.append(binding)
    return tuple(bindings)


def _normalize_dart_pane_style_tokens(
    *,
    raw_tokens: object,
    source_path: Path,
    node_key: str,
) -> tuple[dict[str, object], ...]:
    if raw_tokens is None:
        return ()
    if not isinstance(raw_tokens, list):
        raise ValueError(
            f"Pane render spec {source_path} node {node_key!r} style_tokens must be a list"
        )
    tokens: list[dict[str, object]] = []
    for index, raw_token in enumerate(raw_tokens):
        if not isinstance(raw_token, dict):
            raise ValueError(
                f"Pane render spec {source_path} node {node_key!r} style_tokens[{index}] must be an object"
            )
        raw = cast(Mapping[str, object], raw_token)
        token: dict[str, object] = {
            "token_key": _require_payload_string(
                raw,
                source_path,
                f"{node_key}.style_tokens[{index}]",
                "token_key",
                "tokenKey",
            )
        }
        token_value = _payload_string(raw, "token_value", "tokenValue")
        if token_value is not None:
            token["token_value"] = token_value
        tokens.append(token)
    return tuple(tokens)


def _normalize_dart_pane_renderer_requirements(
    *,
    raw_requirements: object,
    source_path: Path,
) -> tuple[dict[str, object], ...]:
    if raw_requirements is None:
        return ()
    if not isinstance(raw_requirements, list):
        raise ValueError(
            f"Pane render spec {source_path} renderer_requirements must be a list"
        )
    requirements: list[dict[str, object]] = []
    for index, raw_requirement in enumerate(raw_requirements):
        if not isinstance(raw_requirement, dict):
            raise ValueError(
                f"Pane render spec {source_path} renderer_requirements[{index}] must be a JSON object"
            )
        raw = cast(Mapping[str, object], raw_requirement)
        is_required = _payload_bool(raw, "is_required", "isRequired")
        requirements.append(
            {
                "capability_kind": _require_payload_string(
                    raw,
                    source_path,
                    f"renderer_requirements[{index}]",
                    "capability_kind",
                    "capabilityKind",
                ),
                "capability_key": _require_payload_string(
                    raw,
                    source_path,
                    f"renderer_requirements[{index}]",
                    "capability_key",
                    "capabilityKey",
                ),
                "is_required": is_required if is_required is not None else True,
            }
        )
    return tuple(requirements)


def _payload_string(payload: Mapping[str, object], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            trimmed = value.strip()
            if trimmed:
                return trimmed
    return None


def _payload_int(payload: Mapping[str, object], *keys: str) -> int | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _payload_bool(payload: Mapping[str, object], *keys: str) -> bool | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, bool):
            return value
    return None


def _require_payload_string(
    payload: Mapping[str, object],
    source_path: Path,
    context: str,
    *keys: str,
) -> str:
    value = _payload_string(payload, *keys)
    if value is None:
        raise ValueError(
            f"Pane render spec {source_path} {context} must declare one of {keys!r}"
        )
    return value


def _dart_json_map_literal(
    payload: Mapping[str, object], *, indent: int
) -> tuple[str, ...]:
    literal = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).replace(
        "$", r"\$"
    )
    lines = literal.splitlines()
    if lines:
        lines[0] = "<String, dynamic>" + lines[0]
    padding = " " * indent
    return tuple(padding + line for line in lines)


def _render_dart_pane_registrar_bundle(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    plan: InterfaceCompilePlan,
    registrar_truths: tuple[_DartPaneRegistrarTruth, ...],
    projection_catalog: Mapping[str, ProjectionIdentityTruth] | None = None,
    state_model_catalog: Mapping[str, UUID] | None = None,
    state_attribute_catalog: Mapping[str, Mapping[str, UUID]] | None = None,
    api_view_catalog: Mapping[str, ApiViewStateTruth] | None = None,
    render_spec_materialization_path: Path | None = None,
) -> str:
    interface_package_name = (snapshot.spec.interface.package_name or "").strip()
    if not interface_package_name:
        raise ValueError(
            "Interface package_name must be non-empty for Dart runtime metadata"
        )
    interface_package_id = stable_interface_package_id(name=interface_package_name)
    interface_aliases = tuple(
        sorted(
            {
                interface.name
                for interface in plan.interface_ownership
                if interface.name.strip()
            }
        )
    )
    layout_options = _resolve_interface_runtime_layout_options(
        snapshot=snapshot,
        plan=plan,
    )
    section_representations = _resolve_interface_runtime_section_representations(
        snapshot=snapshot,
        plan=plan,
        projection_catalog=projection_catalog,
        state_model_catalog=state_model_catalog,
        state_attribute_catalog=state_attribute_catalog,
        api_view_catalog=api_view_catalog,
    )
    render_spec_truths = (
        _load_dart_pane_render_spec_truths_from_materialization_artifact(
            materialization_path=render_spec_materialization_path,
        )
        if render_spec_materialization_path is not None
        else _load_dart_pane_render_spec_truths(
            snapshot=snapshot,
            plan=plan,
            projection_catalog=projection_catalog,
            state_model_catalog=state_model_catalog,
            state_attribute_catalog=state_attribute_catalog,
            api_view_catalog=api_view_catalog,
        )
    )
    render_component_registrar_truths = _load_dart_render_component_registrar_truths(
        snapshot=snapshot,
    )
    api_view_state_decoder_truths = _resolve_dart_api_view_state_decoder_truths(
        snapshot=snapshot,
        section_representations=section_representations,
    )
    experience_keys = tuple(
        sorted(
            {
                *interface_aliases,
                *(
                    view_ref.split(".", 1)[0]
                    for view_ref in (
                        section.view_ref.strip() for section in section_representations
                    )
                    if view_ref
                ),
            }
        )
    )
    lines = [
        "// Generated by aware_interface compile. Do not edit manually.",
        "",
        "import 'package:aware_shell/aware_shell.dart';",
        "import 'package:aware_pane_runtime/aware_pane_runtime.dart';",
    ]
    used_aliases: set[str] = set()
    aliased_truths: list[tuple[str, _DartPaneRegistrarTruth]] = []
    for truth in registrar_truths:
        alias = _make_dart_import_alias(
            seed=truth.pane_package_name,
            used_aliases=used_aliases,
        )
        aliased_truths.append((alias, truth))
        lines.append(f"import '{truth.library}' as {alias};")
    aliased_render_component_truths: list[
        tuple[str, _DartRenderComponentRegistrarTruth]
    ] = []
    for truth in render_component_registrar_truths:
        alias = _make_dart_import_alias(
            seed=truth.render_component_package_name,
            used_aliases=used_aliases,
        )
        aliased_render_component_truths.append((alias, truth))
        lines.append(f"import '{truth.library}' as {alias};")
    aliased_api_view_state_decoder_truths: list[
        tuple[str, _DartApiViewStateDecoderTruth]
    ] = []
    for truth in api_view_state_decoder_truths:
        alias = _make_dart_import_alias(
            seed=truth.package_name,
            used_aliases=used_aliases,
        )
        aliased_api_view_state_decoder_truths.append((alias, truth))
        lines.append(f"import '{truth.library}' as {alias};")

    lines.extend(
        [
            "",
            "void registerPanePackages(PanePackageRegistry registry) {",
        ]
    )
    if aliased_truths:
        for alias, truth in aliased_truths:
            lines.append(f"  {alias}.{truth.symbol}(registry);")
    else:
        lines.append(
            "  // No pane-package Dart registrars declared for this interface package."
        )
    lines.extend(
        [
            "}",
            "",
            "void registerRenderComponents(RenderComponentRegistryBuilder registry) {",
        ]
    )
    if aliased_render_component_truths:
        for alias, truth in aliased_render_component_truths:
            lines.append(f"  {alias}.{truth.symbol}(registry);")
    else:
        lines.append(
            "  // No render-component Dart registrars declared for this interface package."
        )
    lines.extend(
        [
            "}",
            "",
            "InterfacePackageRuntime buildInterfacePackageRuntime() {",
            "  final panePackageRegistry = PanePackageRegistry();",
            "  final renderComponentRegistryBuilder = RenderComponentRegistryBuilder();",
            "  registerPanePackages(panePackageRegistry);",
            "  registerRenderComponents(renderComponentRegistryBuilder);",
            "  return InterfacePackageRuntime(",
            f"    interfacePackageId: '{interface_package_id}',",
            f"    interfacePackageName: '{interface_package_name}',",
        ]
    )
    if experience_keys:
        lines.append("    experienceKeys: const <String>[")
        for experience_key in experience_keys:
            lines.append(f"      '{experience_key}',")
        lines.append("    ],")
    if layout_options:
        lines.append("    layouts: const <InterfacePackageRuntimeLayout>[")
        for layout in layout_options:
            lines.append(
                "      InterfacePackageRuntimeLayout("
                + f"layoutConfigId: '{layout.layout_config_id}', "
                + f"layoutKey: '{layout.layout_key}', "
                + f"label: '{layout.label}', "
                + f"isDefault: {str(layout.is_default).lower()}),"
            )
        lines.append("    ],")
    if section_representations:
        lines.append(
            "    sectionRepresentations: const <InterfacePackageRuntimeSectionRepresentation>["
        )
        for representation in section_representations:
            lines.append(
                "      InterfacePackageRuntimeSectionRepresentation("
                + f"representationId: '{representation.representation_id}', "
                + f"windowKey: '{representation.window_key}', "
                + f"layoutKey: '{representation.layout_key}', "
                + f"sectionKey: '{representation.section_key}', "
                + f"paneName: '{representation.pane_name}', "
                + f"paneKind: '{representation.pane_kind}', "
                + f"label: '{representation.label}', "
                + f"observableId: '{representation.observable_id}', "
                + f"viewRef: '{representation.view_ref}', "
                + f"projectionViewKey: '{representation.projection_view_key}', "
                + "),"
            )
        lines.append("    ],")
    if render_spec_truths:
        lines.append("    renderSpecs: <PaneRenderSpec>[")
        for render_spec in render_spec_truths:
            lines.append("      PaneRenderSpec.fromJson(")
            lines.extend(_dart_json_map_literal(render_spec.payload, indent=8))
            lines.append("      ),")
        lines.append("    ],")
    else:
        lines.append("    renderSpecs: const <PaneRenderSpec>[],")
    if aliased_api_view_state_decoder_truths:
        lines.append(
            "    viewStateDecoderRegistry: InterfaceViewStateDecoderRegistry.fromDecoderMaps("
        )
        lines.append("      <Map<String, InterfaceViewStateDecoder>>[")
        lines.append("        <String, InterfaceViewStateDecoder>{")
        for alias, truth in aliased_api_view_state_decoder_truths:
            for decoder_key in truth.decoder_keys:
                lines.append(
                    f"          {json.dumps(decoder_key)}: "
                    + f"{alias}.{truth.class_name}.fromJson,"
                )
        lines.append("        },")
        lines.append("      ],")
        lines.append("    ),")
    lines.extend(
        [
            "    renderComponentRegistry: renderComponentRegistryBuilder.build(),",
            "    panePackageRegistry: panePackageRegistry,",
            "  );",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def _resolve_interface_runtime_layout_options(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    plan: InterfaceCompilePlan,
) -> tuple[_InterfaceRuntimeLayoutTruth, ...]:
    attention_layout_catalog = _load_attention_layout_catalog(snapshot=snapshot)
    options: list[_InterfaceRuntimeLayoutTruth] = []
    seen: set[UUID] = set()
    for interface in plan.interface_ownership:
        for window in interface.windows:
            for layout in window.layouts:
                layout_key = layout.key.strip()
                if not layout_key:
                    continue
                attention_layout = attention_layout_catalog.get(layout_key.casefold())
                layout_config_id = (
                    attention_layout.layout_config_id
                    if attention_layout is not None
                    else stable_layout_config_id(key=layout_key)
                )
                if layout_config_id in seen:
                    continue
                seen.add(layout_config_id)
                options.append(
                    _InterfaceRuntimeLayoutTruth(
                        layout_config_id=layout_config_id,
                        layout_key=layout_key,
                        label=_runtime_layout_label(layout_key),
                        is_default=layout.is_default,
                    )
                )
    return tuple(options)


def _resolve_interface_runtime_section_representations(
    *,
    snapshot: InterfaceWorkspaceSnapshot,
    plan: InterfaceCompilePlan,
    projection_catalog: Mapping[str, ProjectionIdentityTruth] | None = None,
    state_model_catalog: Mapping[str, UUID] | None = None,
    state_attribute_catalog: Mapping[str, Mapping[str, UUID]] | None = None,
    api_view_catalog: Mapping[str, ApiViewStateTruth] | None = None,
) -> tuple[_InterfaceRuntimeSectionRepresentationTruth, ...]:
    pane_by_name = {pane.name.casefold(): pane for pane in plan.pane_ownership}
    pane_experience_catalogs = _load_pane_experience_catalogs(
        snapshot=snapshot,
        state_model_catalog=state_model_catalog,
        state_attribute_catalog=state_attribute_catalog,
        api_view_catalog=api_view_catalog,
    )
    projection_catalog = _resolve_projection_identity_catalog(
        snapshot=snapshot,
        projection_catalog=projection_catalog,
    )
    ordered_representations: list[
        tuple[int, _InterfaceRuntimeSectionRepresentationTruth]
    ] = []
    order = 0
    for interface in plan.interface_ownership:
        for pane_mounts in interface.panes:
            pane = pane_by_name.get(pane_mounts.pane_name.casefold())
            if pane is None:
                continue
            pane_experience_catalog = _pane_experience_catalog_for_name(
                pane_name=pane.name,
                pane_experience_catalogs=pane_experience_catalogs,
            )
            pane_view = pane.views[0]
            projection_view_truth = _resolve_projection_experience_view_truth(
                workspace_root=snapshot.workspace_root,
                view_ref=pane_view.ref,
                experience_catalog=pane_experience_catalog,
                projection_catalog=projection_catalog,
                dependency_scope_label="declared pane experience_package dependency scope",
            )
            observable_key = _observable_key_from_view_ref(pane_view.ref)
            label = _humanize_runtime_label(observable_key)
            pane_config_id = stable_pane_config_id(
                name=pane.name,
                projection_experience_view_id=projection_view_truth.projection_experience_view_id,
            )
            for mount in pane_mounts.mounts:
                ordered_representations.append(
                    (
                        order,
                        _InterfaceRuntimeSectionRepresentationTruth(
                            representation_id=pane_config_id,
                            window_key=mount.window_key,
                            layout_key=mount.layout_key,
                            section_key=mount.section_key,
                            pane_name=pane.name,
                            pane_kind=pane.pane_kind,
                            label=label,
                            observable_id=projection_view_truth.object_projection_graph_observable_id,
                            view_ref=pane_view.ref,
                            projection_view_key=projection_view_truth.projection_view_key,
                            api_view_ref=projection_view_truth.api_view_ref,
                            api_view_state_model_ref=(
                                projection_view_truth.api_view_truth.state_model_ref
                                if projection_view_truth.api_view_truth is not None
                                else None
                            ),
                        ),
                    )
                )
                order += 1
    return tuple(
        item
        for _, item in sorted(
            ordered_representations,
            key=lambda entry: (
                entry[1].window_key.casefold(),
                entry[1].layout_key.casefold(),
                entry[1].section_key.casefold(),
                entry[0],
            ),
        )
    )


def _runtime_layout_label(layout_key: str) -> str:
    normalized = layout_key.strip().lower()
    if normalized == "workspace_control":
        return "Workspace"
    if normalized == "graph_view":
        return "Graph"
    if normalized == "code_view":
        return "Code"
    return " ".join(part.capitalize() for part in layout_key.split("_") if part.strip())


def _observable_key_from_view_ref(view_ref: str) -> str:
    parts = [segment.strip() for segment in view_ref.split(".") if segment.strip()]
    if len(parts) >= 2:
        return parts[1]
    if parts:
        return parts[-1]
    return view_ref


def _split_projection_experience_view_ref(view_ref: str) -> tuple[str, str, str] | None:
    parts = [segment.strip() for segment in view_ref.split(".") if segment.strip()]
    if len(parts) < 3:
        return None
    return parts[0], parts[1], ".".join(parts[2:])


def _humanize_runtime_label(value: str) -> str:
    return " ".join(
        part.capitalize() for part in value.replace("-", "_").split("_") if part.strip()
    )


def _make_dart_import_alias(*, seed: str, used_aliases: set[str]) -> str:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in seed.lower()).strip("_")
    alias = normalized or "pane_package"
    counter = 2
    while alias in used_aliases:
        alias = f"{normalized}_{counter}" if normalized else f"pane_package_{counter}"
        counter += 1
    used_aliases.add(alias)
    return alias


def _snake_to_camel(value: str) -> str:
    parts = [part for part in value.split("_") if part]
    if not parts:
        return value
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _encode_plan(*, plan: InterfaceCompilePlan) -> dict[str, object]:
    return {
        "schema_version": plan.schema_version,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "source_files": list(plan.source_files),
        "dependencies": [
            {
                "package_name": item.package_name,
                "version_number": item.version_number,
                "kind": item.kind,
            }
            for item in plan.dependencies
        ],
        "pane_ownership": [
            {
                "name": pane.name,
                "pane_kind": pane.pane_kind,
                "source_path": pane.source_path,
                "description": pane.description,
                "views": [
                    {
                        "ref": view.ref,
                        "is_default": view.is_default,
                        "source_path": view.source_path,
                        "description": view.description,
                    }
                    for view in pane.views
                ],
            }
            for pane in plan.pane_ownership
        ],
        "interface_ownership": [
            {
                "name": interface.name,
                "source_path": interface.source_path,
                "windows": [
                    {
                        "key": window.key,
                        "source_path": window.source_path,
                        "layouts": [
                            {
                                "key": layout.key,
                                "is_default": layout.is_default,
                                "source_path": layout.source_path,
                                "sections": [
                                    asdict(section) for section in layout.sections
                                ],
                            }
                            for layout in window.layouts
                        ],
                    }
                    for window in interface.windows
                ],
                "panes": [
                    {
                        "pane_name": pane.pane_name,
                        "source_path": pane.source_path,
                        "narrative_key": pane.narrative_key,
                        "mounts": [asdict(mount) for mount in pane.mounts],
                    }
                    for pane in interface.panes
                ],
            }
            for interface in plan.interface_ownership
        ],
    }


__all__ = [
    "ApiViewActionTruth",
    "ApiViewStateTruth",
    "InterfaceCompilePlan",
    "InterfaceCompilePlanArtifact",
    "InterfaceConfigBundleArtifact",
    "InterfaceDartPaneRegistrarBundleArtifact",
    "InterfaceDependencyOwnership",
    "InterfacePaneRenderSpecMaterializationArtifact",
    "PaneRenderSpecCompatibilityWarning",
    "build_interface_compile_plan",
    "build_interface_config_bundle",
    "build_projection_identity_catalog_from_ocg",
    "build_state_attribute_catalog_from_ocg",
    "build_state_model_catalog_from_ocg",
    "emit_interface_dart_pane_registrar_bundle_artifact",
    "emit_interface_compile_plan_artifact",
    "emit_interface_config_bundle_artifact",
    "emit_interface_pane_render_spec_materialization_artifact",
]
