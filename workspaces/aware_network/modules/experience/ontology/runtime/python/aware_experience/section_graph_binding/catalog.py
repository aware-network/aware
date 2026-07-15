from __future__ import annotations

# pyright: reportAttributeAccessIssue=false

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable, Protocol
from uuid import UUID

from aware_api_ontology.api.api_view_capability_endpoint import (
    ApiViewCapabilityEndpoint,
)
from aware_api_ontology.api.api_view import ApiView
from aware_experience.section_graph_binding.api_models import (
    ExperienceLayoutGraphBindingDescriptor,
    ExperienceSectionGraphBindingDescriptor,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_graph_identity import (
    ProjectionExperienceGraphIdentity,
)
from aware_experience_ontology.projection.projection_experience_layout_graph_binding import (
    ProjectionExperienceLayoutGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_layout_section_graph_binding import (
    ProjectionExperienceLayoutSectionGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
    ProjectionExperienceSectionGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_section import (
    ProjectionExperienceSection,
)
from aware_experience_ontology.projection.projection_experience_section_view import (
    ProjectionExperienceSectionView,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_experience_ontology.projection.projection_experience_view_instance import (
    ProjectionExperienceViewInstance,
)
from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
    ProjectionExperienceViewInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)


class _SessionLike(Protocol):
    def imap_all_objects(self) -> Iterable[object]: ...


@dataclass(frozen=True, slots=True)
class ExperienceSectionGraphBindingCatalogEntry:
    descriptor: ExperienceSectionGraphBindingDescriptor
    projection_observable_id: UUID
    graph_identity_object_id: UUID
    object_projection_graph_identity_id: UUID
    projection_experience_id: UUID | None = None
    projection_experience_view_id: UUID | None = None
    section_graph_binding_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ExperienceLayoutGraphBindingCatalogEntry:
    descriptor: ExperienceLayoutGraphBindingDescriptor
    section_entries: tuple[ExperienceSectionGraphBindingCatalogEntry, ...]
    layout_graph_binding_id: UUID
    projection_experience_id: UUID
    layout_config_id: UUID


@dataclass(frozen=True, slots=True)
class ExperienceSectionObservableViewResolution:
    projection_experience_id: UUID
    section_id: UUID
    object_projection_graph_observable_id: UUID
    projection_experience_section_id: UUID
    projection_experience_section_view_id: UUID
    projection_experience_view_instance_id: UUID
    projection_experience_view_id: UUID
    section_graph_binding_id: UUID
    view_ref: str
    view_instance_key: str
    section_key: str | None
    status: str


@dataclass(frozen=True, slots=True)
class ExperienceSectionObservableInvocationActionResolution:
    projection_experience_view_id: UUID
    view_invocation_action_config_id: UUID
    experience_invocation_action_config_id: UUID
    api_view_capability_endpoint_id: UUID
    action_key: str
    target_kind: str
    endpoint_ref: str
    label: str | None = None
    receipt_policy: str | None = None
    confirmation_policy: str | None = None
    optimistic_policy: str | None = None
    sdk_operation_api_view_capability_endpoint_id: UUID | None = None
    api_capability_endpoint_id: UUID | None = None
    sdk_operation_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ExperienceSectionGraphBindingCatalog:
    experience_name: str
    catalog_revision: str
    entries: tuple[ExperienceSectionGraphBindingCatalogEntry, ...]

    def entry_for_binding_key(
        self,
        *,
        binding_key: str,
    ) -> ExperienceSectionGraphBindingCatalogEntry | None:
        normalized_binding_key = (binding_key or "").strip().casefold()
        if not normalized_binding_key:
            return None
        for entry in self.entries:
            if (
                entry.descriptor.binding_key.strip().casefold()
                == normalized_binding_key
            ):
                return entry
        return None

    def filter_entries(
        self,
        *,
        section_keys: list[str],
        binding_keys: list[str],
    ) -> tuple[ExperienceSectionGraphBindingCatalogEntry, ...]:
        normalized_section_keys = _normalize_filter_tokens(section_keys)
        normalized_binding_keys = _normalize_filter_tokens(binding_keys)
        filtered: list[ExperienceSectionGraphBindingCatalogEntry] = []
        for entry in self.entries:
            section_key = entry.descriptor.section_key.strip().casefold()
            binding_key = entry.descriptor.binding_key.strip().casefold()
            if normalized_section_keys and section_key not in normalized_section_keys:
                continue
            if normalized_binding_keys and binding_key not in normalized_binding_keys:
                continue
            filtered.append(entry)
        return tuple(filtered)


@dataclass(frozen=True, slots=True)
class ExperienceLayoutGraphBindingCatalog:
    experience_name: str
    catalog_revision: str
    entries: tuple[ExperienceLayoutGraphBindingCatalogEntry, ...]

    def entry_for_binding_key(
        self,
        *,
        binding_key: str,
    ) -> ExperienceLayoutGraphBindingCatalogEntry | None:
        normalized_binding_key = (binding_key or "").strip().casefold()
        if not normalized_binding_key:
            return None
        for entry in self.entries:
            if (
                entry.descriptor.binding_key.strip().casefold()
                == normalized_binding_key
            ):
                return entry
        return None

    def filter_entries(
        self,
        *,
        layout_binding_keys: list[str],
    ) -> tuple[ExperienceLayoutGraphBindingCatalogEntry, ...]:
        normalized_binding_keys = _normalize_filter_tokens(layout_binding_keys)
        filtered: list[ExperienceLayoutGraphBindingCatalogEntry] = []
        for entry in self.entries:
            binding_key = entry.descriptor.binding_key.strip().casefold()
            if normalized_binding_keys and binding_key not in normalized_binding_keys:
                continue
            filtered.append(entry)
        return tuple(filtered)


def resolve_section_graph_binding_catalog(
    *,
    session: _SessionLike,
    experience_name: str,
) -> ExperienceSectionGraphBindingCatalog:
    normalized_experience_name = (experience_name or "").strip()
    if not normalized_experience_name:
        raise ValueError("experience_name is required")

    experiences_by_name: dict[str, list[ProjectionExperience]] = {}
    views_by_id: dict[UUID, ProjectionExperienceView] = {}
    api_views_by_id: dict[UUID, ApiView] = {}
    graph_identities_by_id: dict[UUID, ProjectionExperienceGraphIdentity] = {}
    bindings_by_id: dict[UUID, ProjectionExperienceSectionGraphBinding] = {}

    for obj in session.imap_all_objects():
        if isinstance(obj, ApiView) and obj.id is not None:
            api_views_by_id[obj.id] = obj
            continue
        if isinstance(obj, ProjectionExperience) and obj.id is not None:
            experiences_by_name.setdefault(obj.name.strip().casefold(), []).append(obj)
            continue
        if isinstance(obj, ProjectionExperienceView) and obj.id is not None:
            views_by_id[obj.id] = obj
            continue
        if isinstance(obj, ProjectionExperienceGraphIdentity) and obj.id is not None:
            graph_identities_by_id[obj.id] = obj
            continue
        if (
            isinstance(obj, ProjectionExperienceSectionGraphBinding)
            and obj.id is not None
        ):
            bindings_by_id[obj.id] = obj

    matched_experiences = experiences_by_name.get(
        normalized_experience_name.casefold(), []
    )
    if not matched_experiences:
        raise ValueError(
            "Unknown ProjectionExperience for section graph bindings: "
            + f"experience_name={normalized_experience_name!r}"
        )
    if len(matched_experiences) != 1:
        raise ValueError(
            "Ambiguous ProjectionExperience for section graph bindings: "
            + f"experience_name={normalized_experience_name!r}"
        )
    experience = matched_experiences[0]
    experience_id = experience.id
    if experience_id is None:
        raise ValueError("ProjectionExperience.id is required")
    object_projection_graph_identity_id = experience.object_projection_graph_identity_id
    if object_projection_graph_identity_id is None:
        raise ValueError(
            "ProjectionExperience.object_projection_graph_identity_id is required "
            + "for section graph binding catalog."
        )

    bindings_by_key: dict[str, ProjectionExperienceSectionGraphBinding] = {}
    for candidate in bindings_by_id.values():
        if candidate.projection_experience_id != experience_id:
            continue
        binding_key = (candidate.binding_key or "").strip()
        if not binding_key:
            raise ValueError(
                "ProjectionExperienceSectionGraphBinding.binding_key is required"
            )
        normalized_binding_key = binding_key.casefold()
        existing = bindings_by_key.get(normalized_binding_key)
        if existing is not None and existing.id != candidate.id:
            raise ValueError(
                "Duplicate ProjectionExperienceSectionGraphBinding.binding_key under one ProjectionExperience: "
                + f"experience_name={normalized_experience_name!r} binding_key={binding_key!r}"
            )
        bindings_by_key[normalized_binding_key] = candidate

    entries: list[ExperienceSectionGraphBindingCatalogEntry] = []
    for binding in sorted(
        bindings_by_key.values(),
        key=lambda item: (
            item.section_key.strip().casefold(),
            item.binding_key.strip().casefold(),
            str(item.id),
        ),
    ):
        view = views_by_id.get(binding.projection_experience_view_id)
        if view is None:
            raise ValueError(
                "ProjectionExperienceSectionGraphBinding references missing ProjectionExperienceView: "
                + f"binding_key={binding.binding_key!r} "
                + f"projection_experience_view_id={binding.projection_experience_view_id}"
            )
        projection_observable_id = _projection_view_observable_id(
            view=view,
            api_views_by_id=api_views_by_id,
            context=(
                "section graph binding catalog: "
                + f"binding_key={binding.binding_key!r} "
                + f"projection_experience_view_id={binding.projection_experience_view_id}"
            ),
        )

        graph_identity = graph_identities_by_id.get(
            binding.projection_experience_graph_identity_id
        )
        if graph_identity is None or graph_identity.id is None:
            raise ValueError(
                "ProjectionExperienceSectionGraphBinding references missing ProjectionExperienceGraphIdentity: "
                + f"binding_key={binding.binding_key!r} "
                + "projection_experience_graph_identity_id="
                + f"{binding.projection_experience_graph_identity_id}"
            )

        entries.append(
            ExperienceSectionGraphBindingCatalogEntry(
                descriptor=ExperienceSectionGraphBindingDescriptor(
                    binding_key=binding.binding_key,
                    section_key=binding.section_key,
                    projection_observable_id=projection_observable_id,
                    projection_experience_graph_identity_id=graph_identity.id,
                    object_projection_graph_identity_id=object_projection_graph_identity_id,
                    view_ref=f"{experience.name}.{view.name}",
                    graph_identity_ref=graph_identity.key,
                ),
                projection_observable_id=projection_observable_id,
                graph_identity_object_id=graph_identity.id,
                object_projection_graph_identity_id=object_projection_graph_identity_id,
                projection_experience_id=experience_id,
                projection_experience_view_id=view.id,
                section_graph_binding_id=binding.id,
            )
        )

    return ExperienceSectionGraphBindingCatalog(
        experience_name=experience.name,
        catalog_revision=_catalog_revision(entries),
        entries=tuple(entries),
    )


def resolve_layout_graph_binding_catalog(
    *,
    session: _SessionLike,
    experience_name: str,
) -> ExperienceLayoutGraphBindingCatalog:
    section_catalog = resolve_section_graph_binding_catalog(
        session=session,
        experience_name=experience_name,
    )
    if not section_catalog.entries:
        return ExperienceLayoutGraphBindingCatalog(
            experience_name=section_catalog.experience_name,
            catalog_revision=_layout_catalog_revision(()),
            entries=(),
        )
    projection_experience_id = section_catalog.entries[0].projection_experience_id
    if projection_experience_id is None:
        raise ValueError("ProjectionExperience.id is required")

    layout_bindings: dict[UUID, ProjectionExperienceLayoutGraphBinding] = {}
    layout_section_rows_by_layout_id: dict[
        UUID, list[ProjectionExperienceLayoutSectionGraphBinding]
    ] = {}
    section_entries_by_id = {
        entry.section_graph_binding_id: entry
        for entry in section_catalog.entries
        if entry.section_graph_binding_id is not None
    }

    for obj in session.imap_all_objects():
        if (
            isinstance(obj, ProjectionExperienceLayoutGraphBinding)
            and obj.id is not None
            and obj.projection_experience_id == projection_experience_id
        ):
            layout_bindings[obj.id] = obj
            continue
        if (
            isinstance(obj, ProjectionExperienceLayoutSectionGraphBinding)
            and obj.projection_experience_layout_graph_binding_id is not None
        ):
            layout_section_rows_by_layout_id.setdefault(
                obj.projection_experience_layout_graph_binding_id,
                [],
            ).append(obj)

    entries: list[ExperienceLayoutGraphBindingCatalogEntry] = []
    for layout_binding in sorted(
        layout_bindings.values(),
        key=lambda item: (
            item.binding_key.strip().casefold(),
            str(item.layout_config_id),
            str(item.id),
        ),
    ):
        binding_key = (layout_binding.binding_key or "").strip()
        if not binding_key:
            raise ValueError(
                "ProjectionExperienceLayoutGraphBinding.binding_key is required"
            )
        section_entries: list[ExperienceSectionGraphBindingCatalogEntry] = []
        seen_section_binding_ids: set[UUID] = set()
        for row in sorted(
            layout_section_rows_by_layout_id.get(layout_binding.id, []),
            key=lambda item: str(item.section_graph_binding_id),
        ):
            section_binding_id = row.section_graph_binding_id
            section_entry = section_entries_by_id.get(section_binding_id)
            if section_entry is None:
                raise ValueError(
                    "ProjectionExperienceLayoutGraphBinding references missing "
                    + "ProjectionExperienceSectionGraphBinding: "
                    + f"layout_binding_key={binding_key!r} "
                    + f"section_graph_binding_id={section_binding_id}"
                )
            if section_binding_id in seen_section_binding_ids:
                raise ValueError(
                    "Duplicate section graph binding row under layout graph binding: "
                    + f"layout_binding_key={binding_key!r} "
                    + f"section_graph_binding_id={section_binding_id}"
                )
            seen_section_binding_ids.add(section_binding_id)
            section_entries.append(section_entry)
        section_entries_tuple = tuple(
            sorted(
                section_entries,
                key=lambda item: (
                    item.descriptor.section_key.strip().casefold(),
                    item.descriptor.binding_key.strip().casefold(),
                ),
            )
        )
        entries.append(
            ExperienceLayoutGraphBindingCatalogEntry(
                descriptor=ExperienceLayoutGraphBindingDescriptor(
                    binding_key=binding_key,
                    projection_experience_layout_graph_binding_id=layout_binding.id,
                    projection_experience_id=projection_experience_id,
                    layout_config_id=layout_binding.layout_config_id,
                    section_bindings=tuple(
                        entry.descriptor for entry in section_entries_tuple
                    ),
                ),
                section_entries=section_entries_tuple,
                layout_graph_binding_id=layout_binding.id,
                projection_experience_id=projection_experience_id,
                layout_config_id=layout_binding.layout_config_id,
            )
        )

    return ExperienceLayoutGraphBindingCatalog(
        experience_name=section_catalog.experience_name,
        catalog_revision=_layout_catalog_revision(entries),
        entries=tuple(entries),
    )


def resolve_section_observable_view_instance(
    *,
    session: _SessionLike,
    experience_name: str,
    section_id: UUID,
    object_projection_graph_observable_id: UUID,
    require_active: bool = True,
) -> ExperienceSectionObservableViewResolution:
    """
    Resolve the concrete view instance for one Experience + Attention Section + Observable.

    This is the runtime read side of the ontology bridge:
    ProjectionExperience + Section + Observable -> ProjectionExperienceSectionView
    -> ProjectionExperienceViewInstance -> ProjectionExperienceView.
    """

    normalized_experience_name = (experience_name or "").strip()
    if not normalized_experience_name:
        raise ValueError("experience_name is required")

    objects = _collect_section_view_objects(session=session)
    matched_experiences = [
        experience
        for experience in objects.experiences
        if experience.name.strip().casefold() == normalized_experience_name.casefold()
    ]
    if not matched_experiences:
        raise ValueError(
            "Unknown ProjectionExperience for section observable view resolution: "
            + f"experience_name={normalized_experience_name!r}"
        )
    if len(matched_experiences) != 1:
        raise ValueError(
            "Ambiguous ProjectionExperience for section observable view resolution: "
            + f"experience_name={normalized_experience_name!r}"
        )
    experience = matched_experiences[0]
    if experience.id is None:
        raise ValueError("ProjectionExperience.id is required")

    section_matches = [
        section
        for section in objects.sections
        if section.projection_experience_id == experience.id
        and section.section_id == section_id
    ]
    if not section_matches:
        raise ValueError(
            "No ProjectionExperienceSection matches section observable view lookup: "
            + f"experience_name={normalized_experience_name!r} "
            + f"section_id={section_id}"
        )
    if len(section_matches) != 1:
        raise ValueError(
            "Ambiguous ProjectionExperienceSection for section observable view lookup: "
            + f"experience_name={normalized_experience_name!r} "
            + f"section_id={section_id} matches={len(section_matches)}"
        )
    section = section_matches[0]
    if section.id is None:
        raise ValueError("ProjectionExperienceSection.id is required")

    section_view_matches = [
        section_view
        for section_view in objects.section_views
        if section_view.projection_experience_section_id == section.id
        and (
            not require_active
            or (section_view.status or "").strip().casefold() == "active"
        )
        and _section_view_observable_id(
            section_view=section_view,
            objects=objects,
            context=(
                "section observable view lookup: "
                + f"experience_name={normalized_experience_name!r} "
                + f"section_id={section_id}"
            ),
        )
        == object_projection_graph_observable_id
    ]
    if not section_view_matches:
        raise ValueError(
            "No ProjectionExperienceSectionView resolves the selected section observable: "
            + f"experience_name={normalized_experience_name!r} "
            + f"section_id={section_id} "
            + f"object_projection_graph_observable_id={object_projection_graph_observable_id}"
        )
    if len(section_view_matches) != 1:
        raise ValueError(
            "Ambiguous ProjectionExperienceSectionView resolves the selected section observable: "
            + f"experience_name={normalized_experience_name!r} "
            + f"section_id={section_id} "
            + f"object_projection_graph_observable_id={object_projection_graph_observable_id} "
            + f"matches={len(section_view_matches)}"
        )
    section_view = section_view_matches[0]
    if section_view.id is None:
        raise ValueError("ProjectionExperienceSectionView.id is required")

    view_instance = objects.view_instances_by_id.get(
        section_view.projection_experience_view_instance_id
    )
    if view_instance is None:
        raise ValueError(
            "ProjectionExperienceSectionView references missing view instance: "
            + f"projection_experience_section_view_id={section_view.id} "
            + "projection_experience_view_instance_id="
            + f"{section_view.projection_experience_view_instance_id}"
        )

    view = objects.views_by_id.get(view_instance.projection_experience_view_id)
    if view is None:
        raise ValueError(
            "ProjectionExperienceViewInstance references missing view config: "
            + f"projection_experience_view_instance_id={view_instance.id} "
            + f"projection_experience_view_id={view_instance.projection_experience_view_id}"
        )
    if view.projection_experience_id != experience.id:
        raise ValueError(
            "ProjectionExperienceSectionView resolved a view from a different ProjectionExperience: "
            + f"experience_name={normalized_experience_name!r} "
            + f"projection_experience_view_id={view.id}"
        )
    resolved_observable_id = _projection_view_observable_id(
        view=view,
        api_views_by_id=objects.api_views_by_id,
        context=(
            "section observable view resolved view config: "
            + f"projection_experience_section_view_id={section_view.id} "
            + f"projection_experience_view_id={view.id}"
        ),
    )
    if resolved_observable_id != object_projection_graph_observable_id:
        raise ValueError(
            "ProjectionExperienceSectionView ApiView observable does not match selected observable: "
            + f"projection_experience_section_view_id={section_view.id} "
            + f"projection_experience_view_id={view.id}"
        )
    if view_instance.section_graph_binding_id is None:
        raise ValueError(
            "ProjectionExperienceViewInstance.section_graph_binding_id is required: "
            + f"projection_experience_view_instance_id={view_instance.id}"
        )

    return ExperienceSectionObservableViewResolution(
        projection_experience_id=experience.id,
        section_id=section_id,
        object_projection_graph_observable_id=object_projection_graph_observable_id,
        projection_experience_section_id=section.id,
        projection_experience_section_view_id=section_view.id,
        projection_experience_view_instance_id=section_view.projection_experience_view_instance_id,
        projection_experience_view_id=view_instance.projection_experience_view_id,
        section_graph_binding_id=view_instance.section_graph_binding_id,
        view_ref=f"{experience.name}.{view.name}",
        view_instance_key=view_instance.view_instance_key,
        section_key=section.section_key,
        status=section_view.status,
    )


def resolve_section_observable_invocation_actions(
    *,
    session: _SessionLike,
    experience_name: str,
    section_id: UUID,
    object_projection_graph_observable_id: UUID,
    require_active: bool = True,
) -> tuple[ExperienceSectionObservableInvocationActionResolution, ...]:
    resolution = resolve_section_observable_view_instance(
        session=session,
        experience_name=experience_name,
        section_id=section_id,
        object_projection_graph_observable_id=object_projection_graph_observable_id,
        require_active=require_active,
    )
    action_configs: list[ProjectionExperienceViewInvocationActionConfig] = []
    experience_action_configs_by_id: dict[UUID, ExperienceInvocationActionConfig] = {}
    api_view_capability_endpoints_by_id: dict[UUID, ApiViewCapabilityEndpoint] = {}
    for obj in session.imap_all_objects():
        if (
            isinstance(obj, ProjectionExperienceViewInvocationActionConfig)
            and obj.id is not None
            and obj.projection_experience_view_id
            == resolution.projection_experience_view_id
        ):
            action_configs.append(obj)
            continue
        if isinstance(obj, ExperienceInvocationActionConfig) and obj.id is not None:
            experience_action_configs_by_id[obj.id] = obj
            continue
        if isinstance(obj, ApiViewCapabilityEndpoint) and obj.id is not None:
            api_view_capability_endpoints_by_id[obj.id] = obj

    actions: list[ExperienceSectionObservableInvocationActionResolution] = []
    for action_config in action_configs:
        generic_config_id = action_config.experience_invocation_action_config_id
        if generic_config_id is None:
            raise ValueError(
                "ProjectionExperienceViewInvocationActionConfig.experience_invocation_action_config_id "
                + "is required: "
                + f"view_invocation_action_config_id={action_config.id}"
            )
        generic_config = experience_action_configs_by_id.get(generic_config_id)
        if generic_config is None:
            generic_config = action_config.experience_invocation_action_config
        if generic_config is None or generic_config.id is None:
            raise ValueError(
                "ProjectionExperienceViewInvocationActionConfig references missing "
                + "ExperienceInvocationActionConfig: "
                + f"view_invocation_action_config_id={action_config.id} "
                + f"experience_invocation_action_config_id={generic_config_id}"
            )
        if generic_config.id != generic_config_id:
            raise ValueError(
                "ProjectionExperienceViewInvocationActionConfig references mismatched "
                + "ExperienceInvocationActionConfig: "
                + f"view_invocation_action_config_id={action_config.id} "
                + f"expected={generic_config_id} actual={generic_config.id}"
            )
        if (
            generic_config.projection_experience_id
            != resolution.projection_experience_id
        ):
            raise ValueError(
                "ExperienceInvocationActionConfig belongs to a different ProjectionExperience: "
                + f"view_invocation_action_config_id={action_config.id} "
                + f"experience_invocation_action_config_id={generic_config.id}"
            )
        api_view_capability_endpoint_id = action_config.api_view_capability_endpoint_id
        if api_view_capability_endpoint_id is None:
            raise ValueError(
                "ProjectionExperienceViewInvocationActionConfig.api_view_capability_endpoint_id "
                + "is required: "
                + f"view_invocation_action_config_id={action_config.id}"
            )
        api_view_capability_endpoint = api_view_capability_endpoints_by_id.get(
            api_view_capability_endpoint_id
        )
        if api_view_capability_endpoint is None:
            api_view_capability_endpoint = action_config.api_view_capability_endpoint
        if (
            api_view_capability_endpoint is None
            or api_view_capability_endpoint.id is None
        ):
            raise ValueError(
                "ProjectionExperienceViewInvocationActionConfig references missing "
                + "ApiViewCapabilityEndpoint: "
                + f"view_invocation_action_config_id={action_config.id} "
                + f"api_view_capability_endpoint_id={api_view_capability_endpoint_id}"
            )
        if api_view_capability_endpoint.id != api_view_capability_endpoint_id:
            raise ValueError(
                "ProjectionExperienceViewInvocationActionConfig references mismatched "
                + "ApiViewCapabilityEndpoint: "
                + f"view_invocation_action_config_id={action_config.id} "
                + f"expected={api_view_capability_endpoint_id} "
                + f"actual={api_view_capability_endpoint.id}"
            )
        if (
            generic_config.api_capability_endpoint_id is not None
            and generic_config.api_capability_endpoint_id
            != api_view_capability_endpoint.api_capability_endpoint_id
        ):
            raise ValueError(
                "ExperienceInvocationActionConfig API endpoint target does not match "
                + "ApiViewCapabilityEndpoint: "
                + f"view_invocation_action_config_id={action_config.id}"
            )
        actions.append(
            ExperienceSectionObservableInvocationActionResolution(
                projection_experience_view_id=resolution.projection_experience_view_id,
                view_invocation_action_config_id=action_config.id,
                experience_invocation_action_config_id=generic_config.id,
                api_view_capability_endpoint_id=api_view_capability_endpoint_id,
                action_key=action_config.action_key,
                target_kind=generic_config.target_kind.value,
                endpoint_ref=api_view_capability_endpoint.endpoint_ref,
                label=action_config.label,
                receipt_policy=action_config.receipt_policy,
                confirmation_policy=action_config.confirmation_policy,
                optimistic_policy=action_config.optimistic_policy,
                sdk_operation_api_view_capability_endpoint_id=(
                    action_config.sdk_operation_api_view_capability_endpoint_id
                ),
                api_capability_endpoint_id=(
                    api_view_capability_endpoint.api_capability_endpoint_id
                ),
                sdk_operation_id=generic_config.sdk_operation_id,
            )
        )
    return tuple(
        sorted(
            actions,
            key=lambda item: (
                (item.action_key or "").strip().casefold(),
                str(item.view_invocation_action_config_id),
            ),
        )
    )


@dataclass(frozen=True, slots=True)
class _SectionViewObjects:
    experiences: tuple[ProjectionExperience, ...]
    sections: tuple[ProjectionExperienceSection, ...]
    section_views: tuple[ProjectionExperienceSectionView, ...]
    views_by_id: dict[UUID, ProjectionExperienceView]
    view_instances_by_id: dict[UUID, ProjectionExperienceViewInstance]
    api_views_by_id: dict[UUID, ApiView]


def _collect_section_view_objects(*, session: _SessionLike) -> _SectionViewObjects:
    experiences: list[ProjectionExperience] = []
    sections: list[ProjectionExperienceSection] = []
    section_views: list[ProjectionExperienceSectionView] = []
    views_by_id: dict[UUID, ProjectionExperienceView] = {}
    view_instances_by_id: dict[UUID, ProjectionExperienceViewInstance] = {}
    api_views_by_id: dict[UUID, ApiView] = {}

    for obj in session.imap_all_objects():
        if isinstance(obj, ApiView) and obj.id is not None:
            api_views_by_id[obj.id] = obj
        elif isinstance(obj, ProjectionExperience) and obj.id is not None:
            experiences.append(obj)
        elif isinstance(obj, ProjectionExperienceSection) and obj.id is not None:
            sections.append(obj)
        elif isinstance(obj, ProjectionExperienceSectionView) and obj.id is not None:
            section_views.append(obj)
        elif isinstance(obj, ProjectionExperienceView) and obj.id is not None:
            views_by_id[obj.id] = obj
        elif isinstance(obj, ProjectionExperienceViewInstance) and obj.id is not None:
            view_instances_by_id[obj.id] = obj

    return _SectionViewObjects(
        experiences=tuple(experiences),
        sections=tuple(sections),
        section_views=tuple(section_views),
        views_by_id=views_by_id,
        view_instances_by_id=view_instances_by_id,
        api_views_by_id=api_views_by_id,
    )


def _section_view_observable_id(
    *,
    section_view: ProjectionExperienceSectionView,
    objects: _SectionViewObjects,
    context: str,
) -> UUID:
    view_instance = objects.view_instances_by_id.get(
        section_view.projection_experience_view_instance_id
    )
    if view_instance is None:
        raise ValueError(
            "ProjectionExperienceSectionView references missing view instance: "
            + context
            + " projection_experience_section_view_id="
            + f"{section_view.id}"
        )
    view = objects.views_by_id.get(view_instance.projection_experience_view_id)
    if view is None:
        raise ValueError(
            "ProjectionExperienceViewInstance references missing view config: "
            + context
            + " projection_experience_view_instance_id="
            + f"{view_instance.id}"
        )
    return _projection_view_observable_id(
        view=view,
        api_views_by_id=objects.api_views_by_id,
        context=context,
    )


def _projection_view_observable_id(
    *,
    view: ProjectionExperienceView,
    api_views_by_id: dict[UUID, ApiView],
    context: str,
) -> UUID:
    api_view = view.api_view
    if not isinstance(api_view, ApiView):
        api_view = api_views_by_id.get(view.api_view_id)
    if api_view is None:
        raise ValueError(
            "ProjectionExperienceView references missing ApiView: "
            + context
            + f" api_view_id={view.api_view_id}"
        )
    observable_id = api_view.object_projection_graph_observable_id
    if observable_id is None:
        raise ValueError(
            "ApiView.object_projection_graph_observable_id is required: "
            + context
            + f" api_view_id={api_view.id}"
        )
    return observable_id


def _catalog_revision(entries: list[ExperienceSectionGraphBindingCatalogEntry]) -> str:
    payload = [
        entry.descriptor.model_dump(mode="json", exclude_none=True) for entry in entries
    ]
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _layout_catalog_revision(
    entries: tuple[ExperienceLayoutGraphBindingCatalogEntry, ...],
) -> str:
    payload = [
        entry.descriptor.model_dump(mode="json", exclude_none=True) for entry in entries
    ]
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_filter_tokens(values: list[str]) -> set[str]:
    normalized: set[str] = set()
    for value in values:
        token = (value or "").strip().casefold()
        if token:
            normalized.add(token)
    return normalized


__all__ = [
    "ExperienceLayoutGraphBindingCatalog",
    "ExperienceLayoutGraphBindingCatalogEntry",
    "ExperienceSectionGraphBindingCatalog",
    "ExperienceSectionGraphBindingCatalogEntry",
    "ExperienceSectionObservableInvocationActionResolution",
    "ExperienceSectionObservableViewResolution",
    "resolve_layout_graph_binding_catalog",
    "resolve_section_graph_binding_catalog",
    "resolve_section_observable_invocation_actions",
    "resolve_section_observable_view_instance",
]
