from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from aware_experience.compiler.models import (
    ExperienceProjectionBranchOwnership,
    ExperienceProjectionExperienceOwnership,
    ExperienceProjectionNodeIdentityOwnership,
    ExperienceProjectionNodeKeyParamOwnership,
    ExperienceProjectionNodeOwnership,
    ExperienceProjectionObservableOwnership,
    ExperienceProjectionSectionSurfaceOwnership,
    ExperienceProjectionViewInvocationActionOwnership,
    ExperienceProjectionViewOwnership,
)


def decode_projection_experience_ownership_payload(
    *,
    payload: Sequence[object],
) -> tuple[ExperienceProjectionExperienceOwnership, ...]:
    ownerships: list[ExperienceProjectionExperienceOwnership] = []
    for index, ownership_obj in enumerate(payload):
        ownership_row = _expect_mapping(
            ownership_obj,
            field_name=f"projection_experience_ownership[{index}]",
        )
        ownerships.append(
            _decode_projection_experience_ownership_row(
                row=ownership_row, row_index=index
            )
        )
    return tuple(ownerships)


def _decode_projection_experience_ownership_row(
    *,
    row: Mapping[str, object],
    row_index: int,
) -> ExperienceProjectionExperienceOwnership:
    name = _required_str_token(
        row.get("name"),
        field_name=f"projection_experience_ownership[{row_index}].name",
    )
    projection = _required_str_token(
        row.get("projection"),
        field_name=f"projection_experience_ownership[{row_index}].projection",
    ).casefold()
    source_path = _required_str_token(
        row.get("source_path"),
        field_name=f"projection_experience_ownership[{row_index}].source_path",
    )

    branches = tuple(
        sorted(
            (
                _decode_projection_branch_ownership(
                    branch_obj=branch_obj,
                    row_index=row_index,
                    branch_index=branch_index,
                )
                for branch_index, branch_obj in enumerate(
                    _expect_list(
                        row.get("branches", []),
                        field_name=f"projection_experience_ownership[{row_index}].branches",
                    )
                )
            ),
            key=lambda item: (item.name, item.source_path),
        )
    )

    observables = tuple(
        sorted(
            (
                _decode_projection_observable_ownership(
                    observable_obj=observable_obj,
                    row_index=row_index,
                    observable_index=observable_index,
                )
                for observable_index, observable_obj in enumerate(
                    _expect_list(
                        row.get("observables", []),
                        field_name=f"projection_experience_ownership[{row_index}].observables",
                    )
                )
            ),
            key=lambda item: (item.key, item.source_path),
        )
    )

    nodes = tuple(
        sorted(
            (
                _decode_projection_node_ownership(
                    node_obj=node_obj,
                    row_index=row_index,
                    node_index=node_index,
                )
                for node_index, node_obj in enumerate(
                    _expect_list(
                        row.get("nodes", []),
                        field_name=f"projection_experience_ownership[{row_index}].nodes",
                    )
                )
            ),
            key=lambda item: (item.node_ref, item.source_path),
        )
    )
    section_surfaces = tuple(
        sorted(
            (
                _decode_projection_section_surface_ownership(
                    surface_obj=surface_obj,
                    row_index=row_index,
                    surface_index=surface_index,
                )
                for surface_index, surface_obj in enumerate(
                    _expect_list(
                        row.get("section_surfaces", []),
                        field_name=f"projection_experience_ownership[{row_index}].section_surfaces",
                    )
                )
            ),
            key=lambda item: (
                item.section_key.casefold(),
                item.surface_key.casefold(),
                item.source_path,
            ),
        )
    )

    branch_name_keys_seen: set[str] = set()
    default_branch_count = 0
    for branch in branches:
        branch_key = branch.name.casefold()
        if branch_key in branch_name_keys_seen:
            raise ValueError(
                "Invalid experience compile plan: duplicate projection branch declaration "
                + f"(experience={name!r}, branch={branch.name!r})"
            )
        branch_name_keys_seen.add(branch_key)
        if branch.is_default:
            default_branch_count += 1
    if default_branch_count > 1:
        raise ValueError(
            "Invalid experience compile plan: projection experience allows at most one default branch "
            + f"(experience={name!r}, defaults={default_branch_count})"
        )

    observable_keys_seen: set[str] = set()
    for observable in observables:
        observable_key_casefolded = observable.key.casefold()
        if observable_key_casefolded in observable_keys_seen:
            raise ValueError(
                "Invalid experience compile plan: duplicate observable declaration "
                + f"(experience={name!r}, observable={observable.key!r})"
            )
        observable_keys_seen.add(observable_key_casefolded)
        default_view_count = sum(1 for view in observable.views if view.is_default)
        if default_view_count != 1:
            raise ValueError(
                "Invalid experience compile plan: observable requires exactly one default view "
                + f"(experience={name!r}, observable={observable.key!r}, defaults={default_view_count})"
            )

        view_keys_seen: set[str] = set()
        for view in observable.views:
            view_key_casefolded = view.key.casefold()
            if view_key_casefolded in view_keys_seen:
                raise ValueError(
                    "Invalid experience compile plan: duplicate observable view declaration "
                    + (
                        f"(experience={name!r}, observable={observable.key!r}, "
                        f"view={view.key!r})"
                    )
                )
            view_keys_seen.add(view_key_casefolded)

    node_name_keys_seen: set[str] = set()
    node_ref_keys_seen: set[str] = set()
    identity_keys_seen: set[str] = set()
    for node in nodes:
        node_name_key = node.name.casefold()
        node_ref_key = node.node_ref.casefold()
        if node_name_key in node_name_keys_seen:
            raise ValueError(
                "Invalid experience compile plan: duplicate projection node name declaration "
                + f"(experience={name!r}, node={node.name!r})"
            )
        if node_ref_key in node_ref_keys_seen:
            raise ValueError(
                "Invalid experience compile plan: duplicate projection node_ref declaration "
                + f"(experience={name!r}, node_ref={node.node_ref!r})"
            )
        node_name_keys_seen.add(node_name_key)
        node_ref_keys_seen.add(node_ref_key)

        for identity in node.identities:
            identity_key = identity.key.casefold()
            if identity_key in identity_keys_seen:
                raise ValueError(
                    "Invalid experience compile plan: projection identity key duplicated across nodes "
                    + f"(experience={name!r}, identity={identity.key!r})"
                )
            identity_keys_seen.add(identity_key)

    observable_view_pairs = {
        (observable.key.casefold(), view.key.casefold())
        for observable in observables
        for view in observable.views
    }
    section_surface_keys_seen: set[str] = set()
    for surface in section_surfaces:
        surface_key = surface.surface_key.casefold()
        if surface_key in section_surface_keys_seen:
            raise ValueError(
                "Invalid experience compile plan: duplicate section surface declaration "
                + f"(experience={name!r}, surface={surface.surface_key!r})"
            )
        section_surface_keys_seen.add(surface_key)
        if not surface.section_key.strip():
            raise ValueError(
                "Invalid experience compile plan: section surface requires section key "
                + f"(experience={name!r}, surface={surface.surface_key!r})"
            )
        if (
            surface.observable_key.casefold(),
            surface.view_key.casefold(),
        ) not in observable_view_pairs:
            raise ValueError(
                "Invalid experience compile plan: section surface references unknown view "
                + f"(experience={name!r}, surface={surface.surface_key!r}, "
                + f"view={surface.observable_key}.{surface.view_key})"
            )
        if not surface.graph_identity_ref:
            raise ValueError(
                "Invalid experience compile plan: section surface requires graph identity anchor "
                + f"(experience={name!r}, surface={surface.surface_key!r})"
            )
        if surface.node_identity_ref is not None:
            raise ValueError(
                "Invalid experience compile plan: section surface must not declare node identity anchor "
                + f"(experience={name!r}, surface={surface.surface_key!r}, "
                + f"node_identity={surface.node_identity_ref!r})"
            )
        if surface.source_surface_key is not None:
            raise ValueError(
                "Invalid experience compile plan: section surface must not declare source surface linkage "
                + f"(experience={name!r}, surface={surface.surface_key!r}, "
                + f"source_surface={surface.source_surface_key!r})"
            )

    return ExperienceProjectionExperienceOwnership(
        name=name,
        projection=projection,
        source_path=source_path,
        branches=branches,
        observables=observables,
        nodes=nodes,
        section_surfaces=section_surfaces,
    )


def _decode_projection_branch_ownership(
    *,
    branch_obj: object,
    row_index: int,
    branch_index: int,
) -> ExperienceProjectionBranchOwnership:
    branch_row = _expect_mapping(
        branch_obj,
        field_name=f"projection_experience_ownership[{row_index}].branches[{branch_index}]",
    )
    return ExperienceProjectionBranchOwnership(
        name=_required_str_token(
            branch_row.get("name"),
            field_name=f"projection_experience_ownership[{row_index}].branches[{branch_index}].name",
        ),
        is_default=_expect_bool(
            branch_row.get("is_default"),
            field_name=f"projection_experience_ownership[{row_index}].branches[{branch_index}].is_default",
        ),
        source_path=_required_str_token(
            branch_row.get("source_path"),
            field_name=f"projection_experience_ownership[{row_index}].branches[{branch_index}].source_path",
        ),
    )


def _decode_projection_observable_ownership(
    *,
    observable_obj: object,
    row_index: int,
    observable_index: int,
) -> ExperienceProjectionObservableOwnership:
    observable_row = _expect_mapping(
        observable_obj,
        field_name=f"projection_experience_ownership[{row_index}].observables[{observable_index}]",
    )
    views = tuple(
        sorted(
            (
                _decode_projection_view_ownership(
                    view_obj=view_obj,
                    row_index=row_index,
                    observable_index=observable_index,
                    view_index=view_index,
                )
                for view_index, view_obj in enumerate(
                    _expect_list(
                        observable_row.get("views", []),
                        field_name=(
                            f"projection_experience_ownership[{row_index}]."
                            + f"observables[{observable_index}].views"
                        ),
                    )
                )
            ),
            key=lambda item: (item.key, item.source_path),
        )
    )
    return ExperienceProjectionObservableOwnership(
        key=_required_str_token(
            observable_row.get("key"),
            field_name=f"projection_experience_ownership[{row_index}].observables[{observable_index}].key",
        ),
        source_path=_required_str_token(
            observable_row.get("source_path"),
            field_name=f"projection_experience_ownership[{row_index}].observables[{observable_index}].source_path",
        ),
        views=views,
    )


def _decode_projection_view_ownership(
    *,
    view_obj: object,
    row_index: int,
    observable_index: int,
    view_index: int,
) -> ExperienceProjectionViewOwnership:
    view_row = _expect_mapping(
        view_obj,
        field_name=(
            f"projection_experience_ownership[{row_index}]."
            + f"observables[{observable_index}].views[{view_index}]"
        ),
    )
    action_field_name = (
        f"projection_experience_ownership[{row_index}]."
        + f"observables[{observable_index}].views[{view_index}].invocation_actions"
    )
    invocation_actions = tuple(
        sorted(
            (
                _decode_projection_view_invocation_action_ownership(
                    action_obj=action_obj,
                    row_index=row_index,
                    observable_index=observable_index,
                    view_index=view_index,
                    action_index=action_index,
                )
                for action_index, action_obj in enumerate(
                    _expect_list(
                        view_row.get("invocation_actions", []),
                        field_name=action_field_name,
                    )
                )
            ),
            key=lambda item: (
                item.key.casefold(),
                item.source_path,
            ),
        )
    )
    action_keys_seen: set[str] = set()
    for action in invocation_actions:
        action_key = action.key.casefold()
        if action_key in action_keys_seen:
            raise ValueError(
                "Invalid experience compile plan: duplicate view invocation action declaration "
                + (
                    f"(observable_index={observable_index}, view_index={view_index}, "
                    f"action={action.key!r})"
                )
            )
        action_keys_seen.add(action_key)

    state_model_ref = _optional_str_token(
        view_row.get("state_model_ref"),
        field_name=(
            f"projection_experience_ownership[{row_index}]."
            + f"observables[{observable_index}].views[{view_index}].state_model_ref"
        ),
    )
    api_view_ref = _optional_str_token(
        view_row.get("api_view_ref"),
        field_name=(
            f"projection_experience_ownership[{row_index}]."
            + f"observables[{observable_index}].views[{view_index}].api_view_ref"
        ),
    )
    if bool(state_model_ref) == bool(api_view_ref):
        raise ValueError(
            "Invalid experience compile plan: view must declare exactly one lower view contract "
            + (
                f"(observable_index={observable_index}, view_index={view_index}, "
                f"state_model_ref={state_model_ref!r}, api_view_ref={api_view_ref!r})"
            )
        )

    return ExperienceProjectionViewOwnership(
        key=_required_str_token(
            view_row.get("key"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"observables[{observable_index}].views[{view_index}].key"
            ),
        ),
        is_default=_expect_bool(
            view_row.get("is_default"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"observables[{observable_index}].views[{view_index}].is_default"
            ),
        ),
        state_model_ref=state_model_ref,
        api_view_ref=api_view_ref,
        state_provider_ref=_optional_str_token(
            view_row.get("state_provider_ref"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"observables[{observable_index}].views[{view_index}].state_provider_ref"
            ),
        ),
        source_path=_required_str_token(
            view_row.get("source_path"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"observables[{observable_index}].views[{view_index}].source_path"
            ),
        ),
        invocation_actions=invocation_actions,
    )


def _decode_projection_view_invocation_action_ownership(
    *,
    action_obj: object,
    row_index: int,
    observable_index: int,
    view_index: int,
    action_index: int,
) -> ExperienceProjectionViewInvocationActionOwnership:
    action_field = (
        f"projection_experience_ownership[{row_index}]."
        + f"observables[{observable_index}].views[{view_index}]."
        + f"invocation_actions[{action_index}]"
    )
    action_row = _expect_mapping(
        action_obj,
        field_name=action_field,
    )
    return ExperienceProjectionViewInvocationActionOwnership(
        key=_required_str_token(
            action_row.get("key"),
            field_name=f"{action_field}.key",
        ),
        label=_optional_str_token(
            action_row.get("label"),
            field_name=f"{action_field}.label",
        ),
        receipt_policy=_optional_str_token(
            action_row.get("receipt_policy"),
            field_name=f"{action_field}.receipt_policy",
        ),
        confirmation_policy=_optional_str_token(
            action_row.get("confirmation_policy"),
            field_name=f"{action_field}.confirmation_policy",
        ),
        optimistic_policy=_optional_str_token(
            action_row.get("optimistic_policy"),
            field_name=f"{action_field}.optimistic_policy",
        ),
        source_path=_required_str_token(
            action_row.get("source_path"),
            field_name=f"{action_field}.source_path",
        ),
    )


def _decode_projection_section_surface_ownership(
    *,
    surface_obj: object,
    row_index: int,
    surface_index: int,
) -> ExperienceProjectionSectionSurfaceOwnership:
    surface_row = _expect_mapping(
        surface_obj,
        field_name=f"projection_experience_ownership[{row_index}].section_surfaces[{surface_index}]",
    )
    return ExperienceProjectionSectionSurfaceOwnership(
        surface_key=_required_str_token(
            surface_row.get("surface_key"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"section_surfaces[{surface_index}].surface_key"
            ),
        ),
        section_key=_required_str_token(
            surface_row.get("section_key"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"section_surfaces[{surface_index}].section_key"
            ),
        ),
        observable_key=_required_str_token(
            surface_row.get("observable_key"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"section_surfaces[{surface_index}].observable_key"
            ),
        ),
        view_key=_required_str_token(
            surface_row.get("view_key"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"section_surfaces[{surface_index}].view_key"
            ),
        ),
        source_path=_required_str_token(
            surface_row.get("source_path"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"section_surfaces[{surface_index}].source_path"
            ),
        ),
        source_surface_key=_optional_str_token(
            surface_row.get("source_surface_key"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"section_surfaces[{surface_index}].source_surface_key"
            ),
        ),
        graph_identity_ref=_optional_str_token(
            surface_row.get("graph_identity_ref"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"section_surfaces[{surface_index}].graph_identity_ref"
            ),
        ),
        node_identity_ref=_optional_str_token(
            surface_row.get("node_identity_ref"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"section_surfaces[{surface_index}].node_identity_ref"
            ),
        ),
    )


def _decode_projection_node_ownership(
    *,
    node_obj: object,
    row_index: int,
    node_index: int,
) -> ExperienceProjectionNodeOwnership:
    node_row = _expect_mapping(
        node_obj,
        field_name=f"projection_experience_ownership[{row_index}].nodes[{node_index}]",
    )
    params = tuple(
        sorted(
            (
                _decode_projection_node_param_ownership(
                    param_obj=param_obj,
                    row_index=row_index,
                    node_index=node_index,
                    param_index=param_index,
                )
                for param_index, param_obj in enumerate(
                    _expect_list(
                        node_row.get("params", []),
                        field_name=f"projection_experience_ownership[{row_index}].nodes[{node_index}].params",
                    )
                )
            ),
            key=lambda item: item.name.casefold(),
        )
    )
    identities = tuple(
        sorted(
            (
                _decode_projection_node_identity_ownership(
                    identity_obj=identity_obj,
                    row_index=row_index,
                    node_index=node_index,
                    identity_index=identity_index,
                )
                for identity_index, identity_obj in enumerate(
                    _expect_list(
                        node_row.get("identities", []),
                        field_name=f"projection_experience_ownership[{row_index}].nodes[{node_index}].identities",
                    )
                )
            ),
            key=lambda item: item.key.casefold(),
        )
    )

    param_keys_seen: set[str] = set()
    for param in params:
        param_key = param.name.casefold()
        if param_key in param_keys_seen:
            raise ValueError(
                "Invalid experience compile plan: duplicate projection node param declaration "
                + f"(node_index={node_index}, param={param.name!r})"
            )
        param_keys_seen.add(param_key)

    if not identities:
        raise ValueError(
            "Invalid experience compile plan: projection node requires at least one identity "
            + f"(node_index={node_index})"
        )

    identity_keys_seen: set[str] = set()
    for identity in identities:
        identity_key = identity.key.casefold()
        if identity_key in identity_keys_seen:
            raise ValueError(
                "Invalid experience compile plan: duplicate projection node identity declaration "
                + f"(node_index={node_index}, identity={identity.key!r})"
            )
        identity_keys_seen.add(identity_key)

    return ExperienceProjectionNodeOwnership(
        name=_required_str_token(
            node_row.get("name"),
            field_name=f"projection_experience_ownership[{row_index}].nodes[{node_index}].name",
        ),
        node_ref=_required_str_token(
            node_row.get("node_ref"),
            field_name=f"projection_experience_ownership[{row_index}].nodes[{node_index}].node_ref",
        ),
        source_path=_required_str_token(
            node_row.get("source_path"),
            field_name=f"projection_experience_ownership[{row_index}].nodes[{node_index}].source_path",
        ),
        params=params,
        identities=identities,
    )


def _decode_projection_node_param_ownership(
    *,
    param_obj: object,
    row_index: int,
    node_index: int,
    param_index: int,
) -> ExperienceProjectionNodeKeyParamOwnership:
    param_row = _expect_mapping(
        param_obj,
        field_name=f"projection_experience_ownership[{row_index}].nodes[{node_index}].params[{param_index}]",
    )
    return ExperienceProjectionNodeKeyParamOwnership(
        name=_required_str_token(
            param_row.get("name"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"nodes[{node_index}].params[{param_index}].name"
            ),
        ),
        type_ref=_required_str_token(
            param_row.get("type_ref"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"nodes[{node_index}].params[{param_index}].type_ref"
            ),
        ),
    )


def _decode_projection_node_identity_ownership(
    *,
    identity_obj: object,
    row_index: int,
    node_index: int,
    identity_index: int,
) -> ExperienceProjectionNodeIdentityOwnership:
    identity_row = _expect_mapping(
        identity_obj,
        field_name=(
            f"projection_experience_ownership[{row_index}]."
            + f"nodes[{node_index}].identities[{identity_index}]"
        ),
    )
    return ExperienceProjectionNodeIdentityOwnership(
        key=_required_str_token(
            identity_row.get("key"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"nodes[{node_index}].identities[{identity_index}].key"
            ),
        ),
        source_path=_required_str_token(
            identity_row.get("source_path"),
            field_name=(
                f"projection_experience_ownership[{row_index}]."
                + f"nodes[{node_index}].identities[{identity_index}].source_path"
            ),
        ),
    )


def _expect_list(value: object, *, field_name: str) -> list[object]:
    if isinstance(value, list):
        return cast(list[object], value)
    raise ValueError(f"Invalid experience compile plan: {field_name} must be a list")


def _expect_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise ValueError(f"Invalid experience compile plan: {field_name} must be an object")


def _required_str_token(value: object, *, field_name: str) -> str:
    if isinstance(value, str):
        token = value.strip()
        if token:
            return token
    raise ValueError(f"Invalid experience compile plan: {field_name} is required")


def _optional_str_token(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        token = value.strip()
        return token or None
    raise ValueError(
        f"Invalid experience compile plan: {field_name} must be a string or null"
    )


def _expect_bool(value: object, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"Invalid experience compile plan: {field_name} must be a boolean")


__all__ = ["decode_projection_experience_ownership_payload"]
