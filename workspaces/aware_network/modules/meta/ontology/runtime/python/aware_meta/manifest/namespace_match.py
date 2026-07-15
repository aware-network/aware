from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path

from aware_meta.manifest.spec import AwareTomlNamespaceMappingSpec


def namespace_for_source_path(
    *,
    source_path: str,
    namespace_mappings: tuple[AwareTomlNamespaceMappingSpec, ...] = (),
) -> str:
    matches = tuple(
        mapping
        for mapping in namespace_mappings
        if namespace_path_matches(path_pattern=mapping.path, source_path=source_path)
    )
    if not matches:
        return layout_namespace_for_source_path(source_path)

    matches_by_specificity = sorted(
        matches,
        key=lambda mapping: (-len(_normalize_path_text(mapping.path)), mapping.path),
    )
    winner = matches_by_specificity[0]
    same_specificity = tuple(
        mapping
        for mapping in matches_by_specificity
        if len(_normalize_path_text(mapping.path))
        == len(_normalize_path_text(winner.path))
    )
    namespaces = {mapping.namespace for mapping in same_specificity}
    if len(namespaces) > 1:
        rendered = ", ".join(
            f"{mapping.path}={mapping.namespace}"
            for mapping in sorted(same_specificity, key=lambda item: item.path)
        )
        raise ValueError(
            "Ambiguous [build.namespace] mappings matched source "
            + f"{source_path!r}: {rendered}"
        )
    return winner.namespace


def layout_namespace_for_source_path(source_path: str) -> str:
    parts = list(Path(_normalize_path_text(source_path)).parts)
    if not parts:
        raise ValueError(f"Cannot derive layout namespace from empty path {source_path!r}")

    namespace_parts = tuple(_clean_namespace_segment(part) for part in parts[:-1])
    return ".".join(part for part in namespace_parts if part)


def namespace_path_matches(*, path_pattern: str, source_path: str) -> bool:
    """Match namespace mapping globs against source paths with segment semantics."""

    pattern_parts = _normalize_path_text(path_pattern).split("/")
    source_parts = _normalize_path_text(source_path).split("/")
    return _match_parts(pattern_parts=pattern_parts, source_parts=source_parts)


def _match_parts(*, pattern_parts: list[str], source_parts: list[str]) -> bool:
    if not pattern_parts:
        return not source_parts

    current_pattern = pattern_parts[0]
    if current_pattern == "**":
        if _match_parts(
            pattern_parts=pattern_parts[1:],
            source_parts=source_parts,
        ):
            return True
        return bool(source_parts) and _match_parts(
            pattern_parts=pattern_parts,
            source_parts=source_parts[1:],
        )

    if not source_parts:
        return False
    if not fnmatchcase(source_parts[0], current_pattern):
        return False
    return _match_parts(
        pattern_parts=pattern_parts[1:],
        source_parts=source_parts[1:],
    )


def _normalize_path_text(value: str) -> str:
    return Path(value).as_posix().strip().strip("/")


def _clean_namespace_segment(value: str) -> str:
    return value.rstrip("_")


__all__ = [
    "layout_namespace_for_source_path",
    "namespace_for_source_path",
    "namespace_path_matches",
]
