from __future__ import annotations

# pyright: reportImplicitStringConcatenation=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnusedCallResult=false

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field


ENVIRONMENT_META_PROJECTION_CATALOG_CONTEXT_KEY = "environment_meta_projection_catalog"
META_PROJECTION_HASH_BY_NAME_CONTEXT_KEY = "meta_projection_hash_by_name"


@dataclass(frozen=True, slots=True)
class EnvironmentMetaProjectionCatalog:
    """Meta-owned projection hash catalog consumed by Environment."""

    projection_hash_by_name: Mapping[str, str] = field(default_factory=dict)
    projection_hash_resolver: Callable[[str], object] | None = None
    source: str = "unknown"

    def projection_hash_for_name(self, projection_name: str) -> str:
        name = projection_name.strip()
        if not name:
            raise RuntimeError("Environment Meta projection catalog requires a name.")
        projection_hash = self.projection_hash_by_name.get(name)
        if projection_hash is None and self.projection_hash_resolver is not None:
            projection_hash = self.projection_hash_resolver(name)
        resolved = str(projection_hash or "").strip()
        if not resolved:
            raise RuntimeError(
                "Environment requires Meta projection catalog evidence for "
                f"{name!r}; direct runtime-index projection lookup is forbidden."
            )
        return resolved


def environment_meta_projection_catalog_from_context(
    context: Mapping[str, object] | None,
) -> EnvironmentMetaProjectionCatalog | None:
    if not isinstance(context, Mapping):
        return None
    direct = environment_meta_projection_catalog_from_value(
        context.get(ENVIRONMENT_META_PROJECTION_CATALOG_CONTEXT_KEY),
        source=ENVIRONMENT_META_PROJECTION_CATALOG_CONTEXT_KEY,
    )
    if direct is not None:
        return direct
    direct_mapping = environment_meta_projection_catalog_from_value(
        context.get(META_PROJECTION_HASH_BY_NAME_CONTEXT_KEY),
        source=META_PROJECTION_HASH_BY_NAME_CONTEXT_KEY,
    )
    if direct_mapping is not None:
        return direct_mapping
    for key in (
        "provider_runtime_context",
        "aware_meta.graph_runtime_context",
        "meta_context",
    ):
        candidate = context.get(key)
        catalog = environment_meta_projection_catalog_from_value(
            candidate,
            source=key,
        )
        if catalog is not None:
            return catalog
        nested = getattr(candidate, "meta_context", None)
        nested_catalog = environment_meta_projection_catalog_from_value(
            nested,
            source=f"{key}.meta_context",
        )
        if nested_catalog is not None:
            return nested_catalog
    return None


def require_environment_meta_projection_catalog(
    value: object,
    *,
    required_projection_names: tuple[str, ...] = (),
    source: str = "argument",
) -> EnvironmentMetaProjectionCatalog:
    catalog = environment_meta_projection_catalog_from_value(value, source=source)
    if catalog is None:
        raise RuntimeError(
            "Environment requires Meta projection catalog evidence; direct "
            "runtime-index projection lookup is forbidden."
        )
    for projection_name in required_projection_names:
        catalog.projection_hash_for_name(projection_name)
    return catalog


def environment_meta_projection_catalog_from_value(
    value: object,
    *,
    source: str,
) -> EnvironmentMetaProjectionCatalog | None:
    if value is None:
        return None
    if isinstance(value, EnvironmentMetaProjectionCatalog):
        return value
    if isinstance(value, Mapping):
        nested = value.get(ENVIRONMENT_META_PROJECTION_CATALOG_CONTEXT_KEY)
        if nested is not None:
            return environment_meta_projection_catalog_from_value(
                nested,
                source=ENVIRONMENT_META_PROJECTION_CATALOG_CONTEXT_KEY,
            )
        projection_hash_by_name = value.get("projection_hash_by_name", value)
        if isinstance(projection_hash_by_name, Mapping):
            normalized = _normalized_projection_hash_by_name(projection_hash_by_name)
            if normalized:
                return EnvironmentMetaProjectionCatalog(
                    projection_hash_by_name=normalized,
                    source=source,
                )
        return None
    projection_hash_by_name = getattr(value, "projection_hash_by_name", None)
    if isinstance(projection_hash_by_name, Mapping):
        normalized = _normalized_projection_hash_by_name(projection_hash_by_name)
        if normalized:
            return EnvironmentMetaProjectionCatalog(
                projection_hash_by_name=normalized,
                source=source,
            )
    opg_by_hash = getattr(value, "opg_by_hash", None)
    if isinstance(opg_by_hash, Mapping):
        normalized = _projection_hash_by_name_from_opg_by_hash(opg_by_hash)
        if normalized:
            return EnvironmentMetaProjectionCatalog(
                projection_hash_by_name=normalized,
                source=f"{source}.opg_by_hash",
            )
    resolver = getattr(value, "projection_hash_for_name", None)
    if callable(resolver):
        return EnvironmentMetaProjectionCatalog(
            projection_hash_resolver=resolver,
            source=source,
        )
    return None


def _normalized_projection_hash_by_name(
    value: Mapping[object, object]
) -> dict[str, str]:
    return {
        projection_name: projection_hash
        for raw_name, raw_hash in value.items()
        for projection_name in (str(raw_name or "").strip(),)
        for projection_hash in (str(raw_hash or "").strip(),)
        if projection_name and projection_hash
    }


def _projection_hash_by_name_from_opg_by_hash(
    value: Mapping[object, object],
) -> dict[str, str]:
    projection_hash_by_name: dict[str, str] = {}
    for raw_hash, opg in value.items():
        projection_name = str(getattr(opg, "name", "") or "").strip()
        projection_hash = str(
            getattr(opg, "projection_hash", None) or raw_hash or ""
        ).strip()
        if projection_name and projection_hash:
            projection_hash_by_name.setdefault(projection_name, projection_hash)
    return projection_hash_by_name
