from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
from pathlib import Path
import tomllib
from typing import cast

from aware_experience.profile.api_models import (
    ExperienceGraphIdentityProfile,
    ExperienceGraphIdentityProfileExemplar,
)


@dataclass(frozen=True, slots=True)
class ExperienceProfileCatalogSource:
    path: Path
    experience_name: str
    projection_key: str
    graph_name: str
    catalog_revision: str
    profiles: tuple[ExperienceGraphIdentityProfile, ...]


def _require_mapping(value: object, *, label: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise ValueError(f"{label} must be a mapping")


def _require_list(value: object, *, label: str) -> list[object]:
    if isinstance(value, list):
        return cast(list[object], value)
    raise ValueError(f"{label} must be a list")


def _normalize_required_token(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    token = value.strip()
    if not token:
        raise ValueError(f"{label} must be non-empty")
    return token


def _normalize_optional_token(value: object, *, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string or null")
    token = value.strip()
    return token or None


def _normalize_required_token_list(value: object, *, label: str) -> list[str]:
    rows = _require_list(value, label=label)
    normalized: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        token = _normalize_required_token(row, label=f"{label}[{index}]")
        if token in seen:
            continue
        seen.add(token)
        normalized.append(token)
    if not normalized:
        raise ValueError(f"{label} requires at least one entry")
    return normalized


def _normalize_optional_token_list(value: object, *, label: str) -> list[str]:
    if value is None:
        return []
    rows = _require_list(value, label=label)
    normalized: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        token = _normalize_required_token(row, label=f"{label}[{index}]")
        if token in seen:
            continue
        seen.add(token)
        normalized.append(token)
    return normalized


def _catalog_revision_for_text(document_text: str) -> str:
    return hashlib.sha256(document_text.encode("utf-8")).hexdigest()


def load_profile_catalog_source(*, path: Path) -> ExperienceProfileCatalogSource:
    document_text = path.read_text(encoding="utf-8")
    document = tomllib.loads(document_text)
    sample = _require_mapping(document.get("sample"), label="sample")
    experience_name = _normalize_required_token(sample.get("experience_name"), label="sample.experience_name")
    projection_key = _normalize_required_token(sample.get("projection_key"), label="sample.projection_key")
    graph_name = _normalize_required_token(sample.get("graph_name"), label="sample.graph_name")

    profile_rows = _require_list(document.get("graph_identity_profiles"), label="graph_identity_profiles")
    profiles: list[ExperienceGraphIdentityProfile] = []
    seen_graph_identity_refs: set[str] = set()

    for profile_index, row in enumerate(profile_rows):
        profile_map = _require_mapping(row, label=f"graph_identity_profiles[{profile_index}]")
        graph_identity_ref = _normalize_required_token(
            profile_map.get("graph_identity_ref"),
            label=f"graph_identity_profiles[{profile_index}].graph_identity_ref",
        )
        if graph_identity_ref in seen_graph_identity_refs:
            raise ValueError(
                f"graph_identity_profiles[{profile_index}] duplicates graph_identity_ref {graph_identity_ref!r}"
            )
        seen_graph_identity_refs.add(graph_identity_ref)

        exemplar_rows = _require_list(
            profile_map.get("exemplars", []),
            label=f"graph_identity_profiles[{profile_index}].exemplars",
        )
        exemplars: list[ExperienceGraphIdentityProfileExemplar] = []
        seen_exemplar_keys: set[str] = set()
        for exemplar_index, exemplar_row in enumerate(exemplar_rows):
            exemplar_map = _require_mapping(
                exemplar_row,
                label=f"graph_identity_profiles[{profile_index}].exemplars[{exemplar_index}]",
            )
            exemplar_key = _normalize_required_token(
                exemplar_map.get("key"),
                label=f"graph_identity_profiles[{profile_index}].exemplars[{exemplar_index}].key",
            )
            if exemplar_key in seen_exemplar_keys:
                raise ValueError(
                    "graph_identity_profiles"
                    f"[{profile_index}].exemplars duplicates key {exemplar_key!r}"
                )
            seen_exemplar_keys.add(exemplar_key)
            exemplars.append(
                ExperienceGraphIdentityProfileExemplar(
                    key=exemplar_key,
                    label=_normalize_optional_token(
                        exemplar_map.get("label"),
                        label=f"graph_identity_profiles[{profile_index}].exemplars[{exemplar_index}].label",
                    ),
                    prompt_hint=_normalize_optional_token(
                        exemplar_map.get("prompt_hint"),
                        label=f"graph_identity_profiles[{profile_index}].exemplars[{exemplar_index}].prompt_hint",
                    ),
                    note=_normalize_optional_token(
                        exemplar_map.get("note"),
                        label=f"graph_identity_profiles[{profile_index}].exemplars[{exemplar_index}].note",
                    ),
                    is_primary=bool(exemplar_map.get("is_primary", False)),
                )
            )

        profiles.append(
            ExperienceGraphIdentityProfile(
                graph_identity_ref=graph_identity_ref,
                review_label=_normalize_required_token(
                    profile_map.get("review_label"),
                    label=f"graph_identity_profiles[{profile_index}].review_label",
                ),
                resolution_prompts=_normalize_required_token_list(
                    profile_map.get("resolution_prompts"),
                    label=f"graph_identity_profiles[{profile_index}].resolution_prompts",
                ),
                aliases=_normalize_optional_token_list(
                    profile_map.get("aliases"),
                    label=f"graph_identity_profiles[{profile_index}].aliases",
                ),
                summary=_normalize_optional_token(
                    profile_map.get("summary"),
                    label=f"graph_identity_profiles[{profile_index}].summary",
                ),
                notes=_normalize_optional_token(
                    profile_map.get("notes"),
                    label=f"graph_identity_profiles[{profile_index}].notes",
                ),
                exemplars=exemplars,
            )
        )

    if not profiles:
        raise ValueError("graph_identity_profiles requires at least one entry")

    return ExperienceProfileCatalogSource(
        path=path,
        experience_name=experience_name,
        projection_key=projection_key,
        graph_name=graph_name,
        catalog_revision=_catalog_revision_for_text(document_text),
        profiles=tuple(profiles),
    )


def discover_profile_catalog_sources(*, catalog_root: Path) -> tuple[ExperienceProfileCatalogSource, ...]:
    root = catalog_root.expanduser().resolve()
    sources: list[ExperienceProfileCatalogSource] = []
    for path in sorted(root.rglob("*.instance-profiles.toml")):
        if path.parent.name != "profiles":
            continue
        sources.append(load_profile_catalog_source(path=path))
    return tuple(sources)


def resolve_profile_catalog_source(
    *,
    experience_name: str,
    graph_name: str,
    catalog_root: Path,
) -> ExperienceProfileCatalogSource:
    matched_sources = [
        source
        for source in discover_profile_catalog_sources(catalog_root=catalog_root)
        if source.experience_name == experience_name and source.graph_name == graph_name
    ]
    if not matched_sources:
        raise FileNotFoundError(
            "No Experience graph-identity profile catalog matches "
            + f"experience_name={experience_name!r} graph_name={graph_name!r}"
        )
    if len(matched_sources) > 1:
        matched_paths = ", ".join(str(source.path) for source in matched_sources)
        raise ValueError(
            "Ambiguous Experience graph-identity profile catalogs for "
            + f"experience_name={experience_name!r} graph_name={graph_name!r}: {matched_paths}"
        )
    return matched_sources[0]
