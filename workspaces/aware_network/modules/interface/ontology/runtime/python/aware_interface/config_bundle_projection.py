from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

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
from aware_interface_ontology.interface.interface_config_pane_config import (
    InterfaceConfigPaneConfig,
)
from aware_interface_ontology.interface.interface_config_window_config import (
    InterfaceConfigWindowConfig,
)
from aware_interface_ontology.interface.interface_package import InterfacePackage
from aware_interface_ontology.interface.pane_package import PanePackage
from aware_interface_ontology.interface.window_config import WindowConfig
from aware_interface_ontology.interface.window_config_layout_config import (
    WindowConfigLayoutConfig,
)
from aware_attention_ontology.layout.layout_config import LayoutConfig
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)

from .package_ref_resolution import ResolvedInterfaceRuntimePackageRef


@dataclass(frozen=True, slots=True)
class InterfaceConfigBundleProjectionError(RuntimeError):
    message: str

    def __str__(self) -> str:
        return self.message


def project_interface_config_bundle_from_committed_package(
    resolved: ResolvedInterfaceRuntimePackageRef,
) -> InterfaceConfigBundle:
    """Project the host-facing bundle from committed Interface ontology truth."""

    interface_package = resolved.interface_package
    interface_config = resolved.interface_config
    pane_packages_by_config_id = _pane_packages_by_config_id(interface_package)

    window_configs = [
        InterfaceWindowConfigBundle(
            interface_config_window_config_id=window_binding.id,
            window_config_id=_require_uuid(
                window_binding.window_config_id,
                "InterfaceConfigWindowConfig.window_config_id",
            ),
            key=window_config.key,
            description=window_config.description,
            layout_configs=[
                InterfaceWindowConfigLayoutBundle(
                    window_config_layout_config_id=layout_binding.id,
                    layout_config_id=_require_uuid(
                        layout_binding.layout_config_id,
                        "WindowConfigLayoutConfig.layout_config_id",
                    ),
                    key=layout_config.key,
                    is_default=bool(layout_binding.is_default),
                    sections=[
                        InterfaceWindowLayoutSectionBundle(
                            layout_config_section_config_id=section.id,
                            key=section.section_key,
                        )
                        for section in sorted(
                            layout_config.section_configs,
                            key=lambda item: (
                                item.order,
                                item.section_key,
                                str(item.id),
                            ),
                        )
                    ],
                )
                for layout_binding, layout_config in _window_layout_bindings(
                    window_config=window_config,
                    context=f"WindowConfig[{window_config.key}]",
                )
            ],
        )
        for window_binding, window_config in _interface_window_bindings(
            interface_package_name=interface_package.name,
            interface_config_window_configs=interface_config.interface_config_window_configs,
        )
    ]

    pane_configs = [
        _project_pane_config_bundle(
            interface_config_pane_config=pane_binding,
            pane_package=(
                pane_packages_by_config_id.get(pane_binding.pane_config_id)
                if pane_binding.pane_config_id is not None
                else None
            ),
        )
        for pane_binding in sorted(
            interface_config.interface_config_pane_configs,
            key=lambda item: (
                item.pane_config.name if item.pane_config is not None else "",
                str(item.id),
            ),
        )
    ]

    return InterfaceConfigBundle(
        interface_package_id=interface_package.id,
        interface_package_name=interface_package.name,
        interface_config_id=interface_config.id,
        name=interface_config.name,
        description=interface_config.description,
        window_configs=window_configs,
        pane_configs=pane_configs,
    )


def _project_pane_config_bundle(
    *,
    interface_config_pane_config: InterfaceConfigPaneConfig,
    pane_package: PanePackage | None,
) -> InterfacePaneConfigBundle:
    pane_config = interface_config_pane_config.pane_config
    if pane_config is None:
        raise InterfaceConfigBundleProjectionError(
            "InterfaceConfigPaneConfig is missing hydrated pane_config: "
            f"interface_config_pane_config_id={interface_config_pane_config.id}"
        )

    section_mounts_by_view_binding_id: dict[
        UUID, list[InterfacePaneSectionMountBundle]
    ] = {}
    for mount in sorted(
        interface_config_pane_config.section_mounts,
        key=lambda item: (str(item.layout_config_section_config_id), str(item.id)),
    ):
        section_mounts_by_view_binding_id.setdefault(
            pane_config.id,
            [],
        ).append(
            InterfacePaneSectionMountBundle(
                mount_id=mount.id,
                layout_config_section_config_id=mount.layout_config_section_config_id,
            )
        )

    projection_views = []
    projection_view = pane_config.projection_experience_view
    if projection_view is None:
        raise InterfaceConfigBundleProjectionError(
            "PaneConfig is missing hydrated projection_experience_view; "
            f"pane_config_id={pane_config.id}"
        )
    api_view = _projection_view_api_view(
        projection_experience_view=projection_view,
        context=f"PaneConfig[{pane_config.id}]",
    )
    observable_id = _require_uuid(
        getattr(api_view, "object_projection_graph_observable_id", None),
        "ProjectionExperienceView.api_view.object_projection_graph_observable_id",
    )
    projection_view_key = _projection_view_key_from_hydrated_view(
        projection_experience_view=projection_view,
        api_view=api_view,
        context=f"PaneConfig[{pane_config.id}]",
    )
    projection_views.append(
        InterfacePaneProjectionExperienceViewBundle(
            binding_id=pane_config.id,
            projection_experience_view_id=pane_config.projection_experience_view_id,
            object_projection_graph_observable_id=observable_id,
            state_model_id=_require_uuid(
                getattr(api_view, "state_model_id", None),
                "ProjectionExperienceView.api_view.state_model_id",
            ),
            view_ref=_require_text(
                pane_config.view_ref,
                f"PaneConfig[{pane_config.id}].view_ref",
            ),
            projection_view_key=projection_view_key,
            is_default=True,
            invocation_actions=[
                _project_projection_view_invocation_action_bundle(action_config)
                for action_config in sorted(
                    projection_view.invocation_action_configs,
                    key=lambda item: (
                        getattr(item, "action_key", None) or "",
                        str(item.id),
                    ),
                )
            ],
            section_mounts=section_mounts_by_view_binding_id.get(pane_config.id, []),
        )
    )

    return InterfacePaneConfigBundle(
        pane_config_id=pane_config.id,
        pane_package_id=pane_package.id if pane_package is not None else None,
        pane_package_name=pane_package.name if pane_package is not None else None,
        name=pane_config.name,
        pane_kind=pane_config.pane_kind,
        description=pane_config.description,
        narrative_key=interface_config_pane_config.narrative_key,
        projection_experience_views=projection_views,
    )


def _interface_window_bindings(
    *,
    interface_package_name: str,
    interface_config_window_configs: list[InterfaceConfigWindowConfig],
) -> list[tuple[InterfaceConfigWindowConfig, WindowConfig]]:
    bindings: list[tuple[InterfaceConfigWindowConfig, WindowConfig]] = []
    for window_binding in sorted(
        interface_config_window_configs,
        key=lambda item: (
            item.window_config.key if item.window_config is not None else "",
            str(item.id),
        ),
    ):
        window_config = window_binding.window_config
        if window_config is None:
            raise InterfaceConfigBundleProjectionError(
                "InterfaceConfigWindowConfig is missing hydrated window_config: "
                f"interface_package={interface_package_name!r} "
                f"interface_config_window_config_id={window_binding.id}"
            )
        bindings.append((window_binding, window_config))
    return bindings


def _window_layout_bindings(
    *,
    window_config: WindowConfig,
    context: str,
) -> list[tuple[WindowConfigLayoutConfig, LayoutConfig]]:
    bindings: list[tuple[WindowConfigLayoutConfig, LayoutConfig]] = []
    for layout_binding in sorted(
        window_config.layout_configs,
        key=lambda item: (
            item.layout_config.key if item.layout_config is not None else "",
            str(item.id),
        ),
    ):
        layout_config = layout_binding.layout_config
        if layout_config is None:
            raise InterfaceConfigBundleProjectionError(
                f"{context} layout binding is missing hydrated layout_config: "
                f"window_config_layout_config_id={layout_binding.id}"
            )
        bindings.append((layout_binding, layout_config))
    return bindings


def _pane_packages_by_config_id(
    interface_package: InterfacePackage,
) -> dict[UUID, PanePackage]:
    pane_packages: dict[UUID, PanePackage] = {}
    for package_binding in interface_package.pane_packages:
        pane_package = package_binding.pane_package
        if pane_package is None:
            raise InterfaceConfigBundleProjectionError(
                "InterfacePackagePanePackage is missing hydrated pane_package: "
                f"interface_package_pane_package_id={package_binding.id}"
            )
        pane_packages[pane_package.pane_config_id] = pane_package
    return pane_packages


def _projection_view_key_from_hydrated_view(
    *,
    projection_experience_view: ProjectionExperienceView,
    api_view: object,
    context: str,
) -> str:
    observable = getattr(api_view, "object_projection_graph_observable", None)
    if observable is None:
        raise InterfaceConfigBundleProjectionError(
            f"{context} is missing hydrated api_view.object_projection_graph_observable; "
            "cannot derive projection_view_key"
        )
    observable_key = _require_text(
        observable.observable_key,
        f"{context}.object_projection_graph_observable.observable_key",
    )
    view_name = _require_text(
        projection_experience_view.name,
        f"{context}.projection_experience_view.name",
    )
    return f"{observable_key}.{view_name}"


def _projection_view_api_view(
    *,
    projection_experience_view: ProjectionExperienceView,
    context: str,
) -> object:
    api_view = projection_experience_view.api_view
    if api_view is None:
        raise InterfaceConfigBundleProjectionError(
            f"{context} is missing hydrated api_view; cannot derive lower view contract"
        )
    return api_view


def _project_projection_view_invocation_action_bundle(
    action_config: object,
) -> InterfacePaneViewInvocationActionBundle:
    action = getattr(action_config, "experience_invocation_action_config", None)
    if action is None:
        raise InterfaceConfigBundleProjectionError(
            "ProjectionExperienceViewInvocationActionConfig is missing hydrated "
            "experience_invocation_action_config: "
            f"projection_experience_view_invocation_action_config_id={getattr(action_config, 'id', None)}"
        )
    api_view_action = getattr(action_config, "api_view_capability_endpoint", None)
    target_kind = _require_text(
        str(
            getattr(
                getattr(action, "target_kind", None),
                "value",
                getattr(action, "target_kind", ""),
            )
        ),
        "ExperienceInvocationActionConfig.target_kind",
    )
    target_ref = _projection_view_invocation_action_target_ref(
        action=action,
        api_view_action=api_view_action,
        action_config=action_config,
        target_kind=target_kind,
    )
    return InterfacePaneViewInvocationActionBundle(
        projection_experience_view_invocation_action_id=_require_uuid(
            getattr(action_config, "id", None),
            "ProjectionExperienceViewInvocationActionConfig.id",
        ),
        action_key=_require_text(
            getattr(action_config, "action_key", None),
            "ProjectionExperienceViewInvocationActionConfig.action_key",
        ),
        action_kind=target_kind,
        target_ref=target_ref,
        api_capability_endpoint_id=getattr(action, "api_capability_endpoint_id", None),
        sdk_operation_id=getattr(action, "sdk_operation_id", None),
        label=getattr(action_config, "label", None),
        receipt_policy=getattr(action_config, "receipt_policy", None),
        confirmation_policy=getattr(action_config, "confirmation_policy", None),
        optimistic_policy=getattr(action_config, "optimistic_policy", None),
    )


def _projection_view_invocation_action_target_ref(
    *,
    action: object,
    api_view_action: object | None,
    action_config: object,
    target_kind: str,
) -> str:
    if target_kind == "api":
        endpoint_ref = (
            getattr(api_view_action, "endpoint_ref", None)
            if api_view_action is not None
            else None
        )
        if endpoint_ref:
            return _require_text(
                endpoint_ref,
                "ProjectionExperienceViewInvocationActionConfig.api_view_capability_endpoint.endpoint_ref",
            )
        return str(
            _require_uuid(
                getattr(action, "api_capability_endpoint_id", None),
                "ExperienceInvocationActionConfig.api_capability_endpoint_id",
            )
        )
    if target_kind == "sdk":
        return str(
            _require_uuid(
                getattr(action, "sdk_operation_id", None),
                "ExperienceInvocationActionConfig.sdk_operation_id",
            )
        )
    raise InterfaceConfigBundleProjectionError(
        "ProjectionExperienceViewInvocationActionConfig has unsupported target kind: "
        + f"{target_kind!r} "
        + f"projection_experience_view_invocation_action_config_id={getattr(action_config, 'id', None)}"
    )


def _require_text(value: str | None, context: str) -> str:
    if value is None or not value.strip():
        raise InterfaceConfigBundleProjectionError(
            f"Missing required committed Interface bundle field: {context}"
        )
    return value.strip()


def _require_uuid(value: UUID | None, context: str) -> UUID:
    if value is None:
        raise InterfaceConfigBundleProjectionError(
            f"Missing required committed Interface bundle UUID: {context}"
        )
    return value


__all__ = [
    "InterfaceConfigBundleProjectionError",
    "project_interface_config_bundle_from_committed_package",
]
