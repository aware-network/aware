from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class CodeSourceOwnershipClassification(str, Enum):
    source_owned = "source_owned"
    generated_fallout = "generated_fallout"
    unmapped = "unmapped"


@dataclass(frozen=True, slots=True)
class CodeSourceOwnershipPackageBinding:
    package_name: str
    package_root: str
    sources_root: str | None = None
    manifest_relative_path: str | None = None
    language: str | None = None
    surface: str | None = None
    manifest_kind: str | None = None
    generated_roots: tuple[str, ...] = ()
    owned_file_paths: frozenset[str] = frozenset()
    metadata: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CodeSourceOwnershipObservedPath:
    path: str
    language: str | None = None
    is_structural: bool | None = None
    metadata: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CodeSourceOwnershipPathMatch:
    path: str
    classification: CodeSourceOwnershipClassification
    package_name: str | None = None
    manifest_relative_path: str | None = None
    package_root: str | None = None
    sources_root: str | None = None
    package_relative_path: str | None = None
    binding_index: int | None = None
    language: str | None = None
    is_structural: bool | None = None


@dataclass(frozen=True, slots=True)
class CodeSourceOwnershipResult:
    matches: tuple[CodeSourceOwnershipPathMatch, ...]
    diagnostics: tuple[str, ...] = ()
    package_count: int = 0
    path_count: int = 0
    source_owned_path_count: int = 0
    generated_fallout_path_count: int = 0
    unmapped_path_count: int = 0


@dataclass(frozen=True, slots=True)
class _Candidate:
    binding: CodeSourceOwnershipPackageBinding
    binding_index: int
    classification: CodeSourceOwnershipClassification
    package_relative_path: str
    score: tuple[int, int]


def classify_source_ownership(
    *,
    package_bindings: tuple[CodeSourceOwnershipPackageBinding, ...],
    observed_paths: tuple[CodeSourceOwnershipObservedPath, ...],
    strict: bool = True,
) -> CodeSourceOwnershipResult:
    normalized_bindings, binding_diagnostics = _normalize_bindings(
        bindings=package_bindings,
        strict=strict,
    )
    matches = tuple(
        _match_observed_path(
            bindings=normalized_bindings,
            observed_path=observed_path,
        )
        for observed_path in observed_paths
    )
    return CodeSourceOwnershipResult(
        matches=matches,
        diagnostics=binding_diagnostics,
        package_count=len(normalized_bindings),
        path_count=len(matches),
        source_owned_path_count=sum(
            1
            for match in matches
            if match.classification is CodeSourceOwnershipClassification.source_owned
        ),
        generated_fallout_path_count=sum(
            1
            for match in matches
            if match.classification
            is CodeSourceOwnershipClassification.generated_fallout
        ),
        unmapped_path_count=sum(
            1
            for match in matches
            if match.classification is CodeSourceOwnershipClassification.unmapped
        ),
    )


def _normalize_bindings(
    *,
    bindings: tuple[CodeSourceOwnershipPackageBinding, ...],
    strict: bool,
) -> tuple[tuple[CodeSourceOwnershipPackageBinding, ...], tuple[str, ...]]:
    normalized: list[CodeSourceOwnershipPackageBinding] = []
    diagnostics: list[str] = []
    for index, binding in enumerate(bindings):
        package_root = _normalized_repo_path(binding.package_root)
        sources_root = _normalized_repo_path(binding.sources_root) or package_root
        if package_root is None:
            diagnostics.append(f"package_bindings[{index}].package_root is required.")
            if strict:
                continue
            package_root = "."
            sources_root = sources_root or "."
        normalized.append(
            CodeSourceOwnershipPackageBinding(
                package_name=binding.package_name,
                package_root=package_root,
                sources_root=sources_root,
                manifest_relative_path=_normalized_repo_path(
                    binding.manifest_relative_path
                ),
                language=binding.language,
                surface=binding.surface,
                manifest_kind=binding.manifest_kind,
                generated_roots=tuple(
                    sorted(
                        _normalized_repo_path(root) or "."
                        for root in binding.generated_roots
                    )
                ),
                owned_file_paths=frozenset(
                    normalized_path
                    for path in binding.owned_file_paths
                    for normalized_path in (_normalized_repo_path(path),)
                    if normalized_path is not None
                ),
                metadata=binding.metadata,
            )
        )
    return tuple(normalized), tuple(diagnostics)


def _match_observed_path(
    *,
    bindings: tuple[CodeSourceOwnershipPackageBinding, ...],
    observed_path: CodeSourceOwnershipObservedPath,
) -> CodeSourceOwnershipPathMatch:
    path = _normalized_repo_path(observed_path.path)
    if path is None:
        return CodeSourceOwnershipPathMatch(
            path=observed_path.path,
            classification=CodeSourceOwnershipClassification.unmapped,
            language=observed_path.language,
            is_structural=observed_path.is_structural,
        )

    best: _Candidate | None = None
    for index, binding in enumerate(bindings):
        candidate = _candidate_for_binding(
            binding=binding,
            binding_index=index,
            path=path,
        )
        if candidate is not None and (best is None or candidate.score > best.score):
            best = candidate

    if best is None:
        return CodeSourceOwnershipPathMatch(
            path=path,
            classification=CodeSourceOwnershipClassification.unmapped,
            language=observed_path.language,
            is_structural=observed_path.is_structural,
        )

    binding = best.binding
    return CodeSourceOwnershipPathMatch(
        path=path,
        classification=best.classification,
        package_name=binding.package_name,
        manifest_relative_path=binding.manifest_relative_path,
        package_root=binding.package_root,
        sources_root=binding.sources_root,
        package_relative_path=best.package_relative_path,
        binding_index=best.binding_index,
        language=observed_path.language or binding.language,
        is_structural=observed_path.is_structural,
    )


def _candidate_for_binding(
    *,
    binding: CodeSourceOwnershipPackageBinding,
    binding_index: int,
    path: str,
) -> _Candidate | None:
    package_relative_from_owned_path = (
        _package_relative_path(binding=binding, path=path)
        if path in binding.owned_file_paths
        else None
    )
    if package_relative_from_owned_path is not None:
        return _Candidate(
            binding=binding,
            binding_index=binding_index,
            classification=CodeSourceOwnershipClassification.source_owned,
            package_relative_path=package_relative_from_owned_path,
            score=(4, _path_depth(binding.package_root)),
        )
    if binding.package_root == "." and binding.owned_file_paths:
        return None

    package_relative_from_root = _relative_path_under_root(
        path=path,
        root=binding.package_root,
    )
    if package_relative_from_root is None:
        return None
    package_relative_from_sources = _relative_path_under_root(
        path=path,
        root=binding.sources_root or binding.package_root,
    )
    if package_relative_from_sources is not None and not _is_generated_fallout_path(
        path=path,
        relative_path=package_relative_from_root,
        binding=binding,
    ):
        return _Candidate(
            binding=binding,
            binding_index=binding_index,
            classification=CodeSourceOwnershipClassification.source_owned,
            package_relative_path=package_relative_from_sources,
            score=(3, _path_depth(binding.sources_root or binding.package_root)),
        )
    if (
        (binding.sources_root or binding.package_root) != binding.package_root
        or _is_generated_fallout_path(
            path=path,
            relative_path=package_relative_from_root,
            binding=binding,
        )
    ):
        return _Candidate(
            binding=binding,
            binding_index=binding_index,
            classification=CodeSourceOwnershipClassification.generated_fallout,
            package_relative_path=package_relative_from_root,
            score=(1, _path_depth(binding.package_root)),
        )
    return _Candidate(
        binding=binding,
        binding_index=binding_index,
        classification=CodeSourceOwnershipClassification.source_owned,
        package_relative_path=package_relative_from_root,
        score=(2, _path_depth(binding.package_root)),
    )


def _package_relative_path(
    *,
    binding: CodeSourceOwnershipPackageBinding,
    path: str,
) -> str | None:
    package_relative_from_sources = _relative_path_under_root(
        path=path,
        root=binding.sources_root or binding.package_root,
    )
    if package_relative_from_sources is not None:
        return package_relative_from_sources
    return _relative_path_under_root(path=path, root=binding.package_root)


def _is_generated_fallout_path(
    *,
    path: str,
    relative_path: str,
    binding: CodeSourceOwnershipPackageBinding,
) -> bool:
    for generated_root in binding.generated_roots:
        if _relative_path_under_root(path=path, root=generated_root) is not None:
            return True
    parts = [part for part in Path(relative_path).parts if part not in {"", "."}]
    if not parts:
        return False
    for part in parts:
        if part in {
            ".aware",
            ".dart_tool",
            "__pycache__",
            "_aware",
            "_generated",
            "build",
        }:
            return True
        if part.endswith(".egg-info"):
            return True
    return False


def _relative_path_under_root(*, path: str, root: str | None) -> str | None:
    normalized_path = _normalized_repo_path(path)
    normalized_root = _normalized_repo_path(root) or "."
    if normalized_path is None:
        return None
    if normalized_root == ".":
        return normalized_path
    if normalized_path == normalized_root:
        return "."
    prefix = f"{normalized_root}/"
    if normalized_path.startswith(prefix):
        return normalized_path[len(prefix) :]
    return None


def _normalized_repo_path(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = Path(value.strip()).as_posix().strip("/")
    if normalized in {"", "."}:
        return "."
    if normalized.startswith("../") or normalized == "..":
        return None
    return normalized


def _path_depth(path: str) -> int:
    return len([part for part in Path(path).parts if part not in {"", "."}])


__all__ = [
    "CodeSourceOwnershipClassification",
    "CodeSourceOwnershipObservedPath",
    "CodeSourceOwnershipPackageBinding",
    "CodeSourceOwnershipPathMatch",
    "CodeSourceOwnershipResult",
    "classify_source_ownership",
]
