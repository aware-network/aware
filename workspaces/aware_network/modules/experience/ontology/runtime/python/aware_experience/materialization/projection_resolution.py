from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from uuid import UUID

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.projection_support import build_meta_graph_opgi_index


@dataclass(frozen=True, slots=True)
class ProjectionRuntimeResolution:
    projection_key: str
    opgi_id: UUID
    opgi_entry: tuple[UUID, frozenset[str]]


class ProjectionRuntimeResolver:
    def __init__(self, *, index: MetaGraphRuntimeIndex) -> None:
        self._opgi_by_key = _build_opgi_by_key(index=index)
        self._class_ref_index = _build_class_ref_index(
            index=index,
            opgi_by_key=self._opgi_by_key,
        )

    @property
    def opgi_by_key_casefolded(self) -> Mapping[str, tuple[UUID, frozenset[str]]]:
        return {
            key: resolution.opgi_entry for key, resolution in self._opgi_by_key.items()
        }

    def resolve(
        self,
        *,
        projection_key: str,
        node_refs: Iterable[str] = (),
        experience_name: str,
        context: str,
    ) -> ProjectionRuntimeResolution:
        normalized_projection_key = _normalize_lookup_key(projection_key)
        if not normalized_projection_key:
            raise RuntimeError(
                f"{context} requires projection key "
                + f"(experience={experience_name!r})"
            )

        exact = self._opgi_by_key.get(normalized_projection_key)
        if exact is not None:
            return exact

        suffix_matches = [
            resolution
            for key, resolution in self._opgi_by_key.items()
            if key.rsplit(":", 1)[-1] == normalized_projection_key
        ]
        if len(suffix_matches) == 1:
            return suffix_matches[0]
        if len(suffix_matches) > 1:
            raise RuntimeError(
                f"{context} projection key resolved ambiguously across OPGI keys "
                + f"(experience={experience_name!r}, projection={projection_key!r})"
            )

        node_ref_resolutions: list[ProjectionRuntimeResolution] = []
        for node_ref in node_refs:
            resolved = self._resolve_class_ref(
                class_ref=node_ref,
                projection_key=projection_key,
                experience_name=experience_name,
                context=context,
            )
            if resolved is not None:
                node_ref_resolutions.append(resolved)
        unique_node_ref_resolutions = _unique_resolutions(node_ref_resolutions)
        if len(unique_node_ref_resolutions) == 1:
            return unique_node_ref_resolutions[0]
        if len(unique_node_ref_resolutions) > 1:
            projection_names = sorted(
                resolution.projection_key for resolution in unique_node_ref_resolutions
            )
            raise RuntimeError(
                f"{context} resolved node refs across multiple owning projections "
                + f"(experience={experience_name!r}, projection={projection_key!r}, "
                + f"owning_projections={projection_names!r})"
            )

        class_ref_resolution = self._resolve_class_ref(
            class_ref=projection_key,
            projection_key=projection_key,
            experience_name=experience_name,
            context=context,
        )
        if class_ref_resolution is not None:
            return class_ref_resolution

        candidate_projection_keys = sorted(
            resolution.projection_key for resolution in self._opgi_by_key.values()
        )
        raise RuntimeError(
            f"{context} projection key was not found in OPGI catalog or owning "
            + "class-node catalog "
            + f"(experience={experience_name!r}, projection={projection_key!r}, "
            + f"candidates={candidate_projection_keys!r})"
        )

    def _resolve_class_ref(
        self,
        *,
        class_ref: str,
        projection_key: str,
        experience_name: str,
        context: str,
    ) -> ProjectionRuntimeResolution | None:
        normalized = _normalize_lookup_key(class_ref)
        if not normalized:
            return None
        matches = _unique_resolutions(self._class_ref_index.get(normalized, ()))
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        projection_names = sorted(resolution.projection_key for resolution in matches)
        raise RuntimeError(
            f"{context} class target resolved ambiguously across owning projections "
            + f"(experience={experience_name!r}, projection={projection_key!r}, "
            + f"class_ref={class_ref!r}, owning_projections={projection_names!r})"
        )


def build_projection_runtime_resolver(
    *, index: MetaGraphRuntimeIndex
) -> ProjectionRuntimeResolver:
    return ProjectionRuntimeResolver(index=index)


def _build_opgi_by_key(
    *, index: MetaGraphRuntimeIndex
) -> dict[str, ProjectionRuntimeResolution]:
    opgi_entries = build_meta_graph_opgi_index(index=index)
    by_key: dict[str, ProjectionRuntimeResolution] = {}
    for projection_key, opgi_entry in opgi_entries.items():
        normalized_key = _normalize_lookup_key(projection_key)
        if not normalized_key:
            continue
        opgi_id, view_keys = opgi_entry
        by_key[normalized_key] = ProjectionRuntimeResolution(
            projection_key=projection_key,
            opgi_id=opgi_id,
            opgi_entry=(opgi_id, frozenset(view_keys)),
        )
    return by_key


def _build_class_ref_index(
    *,
    index: MetaGraphRuntimeIndex,
    opgi_by_key: Mapping[str, ProjectionRuntimeResolution],
) -> dict[str, tuple[ProjectionRuntimeResolution, ...]]:
    mutable: dict[str, dict[UUID, ProjectionRuntimeResolution]] = defaultdict(dict)
    resolution_by_opgi_id = {
        resolution.opgi_id: resolution for resolution in opgi_by_key.values()
    }

    for opg in index.ocg.object_projection_graphs:
        _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
            index=index,
            projection_hash=opg.projection_hash,
        )
        if opgi is None:
            continue
        resolution = resolution_by_opgi_id.get(opgi.id)
        if resolution is None:
            continue
        for node in opg.object_projection_graph_nodes or ():
            class_config = node.class_config
            if class_config is None and node.class_config_id is not None:
                class_config = index.class_configs_by_id.get(node.class_config_id)
            for key in _class_ref_lookup_keys(class_config=class_config):
                mutable[key][resolution.opgi_id] = resolution

    return {
        key: tuple(sorted(values.values(), key=lambda item: item.projection_key))
        for key, values in mutable.items()
    }


def _class_ref_lookup_keys(*, class_config: ClassConfig | None) -> frozenset[str]:
    if class_config is None:
        return frozenset()
    raw_values = {
        class_config.name,
        class_config.class_fqn,
    }
    raw_values.update(_suffixes(class_config.class_fqn))
    if ".default." in class_config.class_fqn:
        without_default = class_config.class_fqn.replace(".default.", ".")
        raw_values.add(without_default)
        raw_values.update(_suffixes(without_default))
    return frozenset(
        key
        for raw_value in raw_values
        for key in (_normalize_lookup_key(raw_value),)
        if key
    )


def _suffixes(value: str) -> tuple[str, ...]:
    parts = [part.strip() for part in (value or "").split(".") if part.strip()]
    return tuple(".".join(parts[index:]) for index in range(len(parts)))


def _unique_resolutions(
    resolutions: Iterable[ProjectionRuntimeResolution],
) -> tuple[ProjectionRuntimeResolution, ...]:
    by_opgi_id: dict[UUID, ProjectionRuntimeResolution] = {}
    for resolution in resolutions:
        by_opgi_id[resolution.opgi_id] = resolution
    return tuple(sorted(by_opgi_id.values(), key=lambda item: item.projection_key))


def _normalize_lookup_key(value: str) -> str:
    return (value or "").strip().casefold()


__all__ = [
    "ProjectionRuntimeResolution",
    "ProjectionRuntimeResolver",
    "build_projection_runtime_resolver",
]
