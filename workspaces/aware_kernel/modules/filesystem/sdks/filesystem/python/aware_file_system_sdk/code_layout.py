from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from typing import Literal, cast

from aware_code_service_dto.code.features.package_layout import (
    CodePackageLayoutContract,
)
from aware_code_service_dto.code.features.package_layout import (
    CodePackageLayoutPathRole,
)
from aware_code_service_dto.code.features.package_common import CodePackagePathRole
from aware_code_service_dto.code.features.semantic_contract import CodeSemanticContract

from aware_file_system_sdk.client import FileSystemSdkError, normalize_relative_path

FileSystemCodeLayoutPathScope = Literal["root_relative", "package_relative"]


@dataclass(frozen=True, slots=True)
class FileSystemCodeLayoutPathClassification:
    input_path: str
    root_relative_path: str
    package_relative_path: str | None
    package_name: str | None
    package_root: str
    sources_root: str | None
    role: CodePackagePathRole | None
    source: str
    semantic_owner_hints: tuple[str, ...] = ()
    provider_key: str | None = None
    matched_include_pattern: str | None = None
    matched_exclude_pattern: str | None = None
    generated_root: str | None = None
    manifest_relative_path: str | None = None

    @property
    def role_value(self) -> str | None:
        if self.role is None:
            return None
        return self.role.value


@dataclass(frozen=True, slots=True)
class FileSystemCodeLayoutClassificationResult:
    classifications: tuple[FileSystemCodeLayoutPathClassification, ...]
    evidence: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FileSystemCodeLayoutClassifier:
    layout_contract: CodePackageLayoutContract
    semantic_contract: CodeSemanticContract | None = None

    def classify_path(
        self,
        path: str,
        *,
        path_scope: FileSystemCodeLayoutPathScope = "root_relative",
    ) -> FileSystemCodeLayoutPathClassification:
        layout = _normalized_layout(self.layout_contract)
        input_path = normalize_relative_path(path)
        root_relative_path = _root_relative_path(
            path=input_path,
            package_root=layout.package_root,
            path_scope=path_scope,
        )
        package_relative_path = _package_relative_path(
            root_relative_path=root_relative_path,
            package_root=layout.package_root,
        )
        provider_key = _provider_key(
            layout_contract=self.layout_contract,
            semantic_contract=self.semantic_contract,
        )
        if package_relative_path is None:
            return FileSystemCodeLayoutPathClassification(
                input_path=input_path,
                root_relative_path=root_relative_path,
                package_relative_path=None,
                package_name=layout.package_name,
                package_root=layout.package_root,
                sources_root=layout.sources_root,
                role=None,
                source="outside_package",
                semantic_owner_hints=_semantic_owner_hints(
                    provider_key=provider_key,
                    explicit_hints=(),
                ),
                provider_key=provider_key,
                manifest_relative_path=layout.manifest_relative_path,
            )

        path_role_match = _match_path_role(
            package_relative_path=package_relative_path,
            path_roles=tuple(self.layout_contract.path_roles),
        )
        if path_role_match is not None:
            return FileSystemCodeLayoutPathClassification(
                input_path=input_path,
                root_relative_path=root_relative_path,
                package_relative_path=package_relative_path,
                package_name=layout.package_name,
                package_root=layout.package_root,
                sources_root=layout.sources_root,
                role=path_role_match.path_role.role,
                source="path_role",
                semantic_owner_hints=_semantic_owner_hints(
                    provider_key=provider_key,
                    explicit_hints=path_role_match.path_role.semantic_owner_hints,
                ),
                provider_key=provider_key,
                matched_include_pattern=path_role_match.include_pattern,
                manifest_relative_path=layout.manifest_relative_path,
            )

        manifest_relative_path = layout.manifest_relative_path
        if (
            manifest_relative_path is not None
            and package_relative_path == manifest_relative_path
        ):
            return _fallback_classification(
                input_path=input_path,
                root_relative_path=root_relative_path,
                package_relative_path=package_relative_path,
                layout=layout,
                role=CodePackagePathRole.generated_manifest,
                source="manifest_relative_path",
                provider_key=provider_key,
            )

        for generated_root in layout.generated_roots:
            if _is_relative_path_under(
                child=root_relative_path,
                parent=generated_root,
            ):
                return _fallback_classification(
                    input_path=input_path,
                    root_relative_path=root_relative_path,
                    package_relative_path=package_relative_path,
                    layout=layout,
                    role=CodePackagePathRole.generated_metadata,
                    source="generated_root",
                    provider_key=provider_key,
                    generated_root=generated_root,
                )

        if layout.sources_root is not None and _is_relative_path_under(
            child=root_relative_path,
            parent=layout.sources_root,
        ):
            return _fallback_classification(
                input_path=input_path,
                root_relative_path=root_relative_path,
                package_relative_path=package_relative_path,
                layout=layout,
                role=CodePackagePathRole.authored_source,
                source="sources_root",
                provider_key=provider_key,
            )

        return _fallback_classification(
            input_path=input_path,
            root_relative_path=root_relative_path,
            package_relative_path=package_relative_path,
            layout=layout,
            role=None,
            source="unclassified",
            provider_key=provider_key,
        )

    def classify_paths(
        self,
        paths: Iterable[str],
        *,
        path_scope: FileSystemCodeLayoutPathScope = "root_relative",
    ) -> FileSystemCodeLayoutClassificationResult:
        path_tuple = tuple(paths)
        classifications = tuple(
            self.classify_path(path, path_scope=path_scope)
            for path in path_tuple
        )
        return FileSystemCodeLayoutClassificationResult(
            classifications=classifications,
            evidence={
                "boundary": "filesystem.sdk.code_layout",
                "operation": "classify_paths",
                "code_api_dto_package": "aware_code_service_api",
                "package_name": self.layout_contract.package_name,
                "package_root": _normalized_layout(
                    self.layout_contract
                ).package_root,
                "semantic_contract_provider_key": _provider_key(
                    layout_contract=self.layout_contract,
                    semantic_contract=self.semantic_contract,
                ),
                "path_count": len(path_tuple),
                "classified_count": sum(
                    1 for item in classifications if item.role is not None
                ),
                "role_counts": _role_counts(classifications),
            },
        )


def build_code_layout_classifier(
    *,
    layout_contract: CodePackageLayoutContract,
    semantic_contract: CodeSemanticContract | None = None,
) -> FileSystemCodeLayoutClassifier:
    return FileSystemCodeLayoutClassifier(
        layout_contract=layout_contract,
        semantic_contract=semantic_contract,
    )


def classify_code_layout_paths(
    *,
    layout_contract: CodePackageLayoutContract,
    paths: Iterable[str],
    semantic_contract: CodeSemanticContract | None = None,
    path_scope: FileSystemCodeLayoutPathScope = "root_relative",
) -> FileSystemCodeLayoutClassificationResult:
    return build_code_layout_classifier(
        layout_contract=layout_contract,
        semantic_contract=semantic_contract,
    ).classify_paths(paths, path_scope=path_scope)


@dataclass(frozen=True, slots=True)
class _NormalizedLayout:
    package_name: str | None
    package_root: str
    sources_root: str | None
    generated_roots: tuple[str, ...]
    manifest_relative_path: str | None


@dataclass(frozen=True, slots=True)
class _PathRoleMatch:
    path_role: CodePackageLayoutPathRole
    include_pattern: str


def _normalized_layout(layout_contract: CodePackageLayoutContract) -> _NormalizedLayout:
    package_root = _required_relative_path(
        getattr(layout_contract, "package_root", None),
        "CodePackageLayoutContract.package_root",
    )
    sources_root = _optional_layout_root(
        package_root=package_root,
        value=getattr(layout_contract, "sources_root", None),
    )
    generated_roots = tuple(
        _optional_layout_root(package_root=package_root, value=value)
        for value in tuple(getattr(layout_contract, "generated_roots", ()) or ())
    )
    manifest_relative_path = _optional_relative_path(
        getattr(layout_contract, "manifest_relative_path", None)
    )
    return _NormalizedLayout(
        package_name=_optional_str(getattr(layout_contract, "package_name", None)),
        package_root=package_root,
        sources_root=sources_root,
        generated_roots=tuple(
            root for root in generated_roots if root is not None
        ),
        manifest_relative_path=manifest_relative_path,
    )


def _match_path_role(
    *,
    package_relative_path: str,
    path_roles: tuple[CodePackageLayoutPathRole, ...],
) -> _PathRoleMatch | None:
    for path_role in path_roles:
        include_pattern = _first_matching_pattern(
            path=package_relative_path,
            patterns=tuple(path_role.include_patterns),
        )
        if include_pattern is None:
            continue
        exclude_pattern = _first_matching_pattern(
            path=package_relative_path,
            patterns=tuple(path_role.exclude_patterns),
        )
        if exclude_pattern is not None:
            continue
        return _PathRoleMatch(
            path_role=path_role,
            include_pattern=include_pattern,
        )
    return None


def _first_matching_pattern(
    *,
    path: str,
    patterns: tuple[str, ...],
) -> str | None:
    for pattern in patterns:
        normalized = _normalize_pattern(pattern)
        if _pattern_matches(path=path, pattern=normalized):
            return normalized
    return None


def _pattern_matches(*, path: str, pattern: str) -> bool:
    if pattern in {"", "."}:
        return path == "."
    if fnmatchcase(path, pattern):
        return True
    if pattern.startswith("**/") and fnmatchcase(path, pattern[3:]):
        return True
    if pattern.endswith("/**"):
        root = pattern.removesuffix("/**")
        return path == root or path.startswith(root + "/")
    return False


def _fallback_classification(
    *,
    input_path: str,
    root_relative_path: str,
    package_relative_path: str,
    layout: _NormalizedLayout,
    role: CodePackagePathRole | None,
    source: str,
    provider_key: str | None,
    generated_root: str | None = None,
) -> FileSystemCodeLayoutPathClassification:
    return FileSystemCodeLayoutPathClassification(
        input_path=input_path,
        root_relative_path=root_relative_path,
        package_relative_path=package_relative_path,
        package_name=layout.package_name,
        package_root=layout.package_root,
        sources_root=layout.sources_root,
        role=role,
        source=source,
        semantic_owner_hints=_semantic_owner_hints(
            provider_key=provider_key,
            explicit_hints=(),
        ),
        provider_key=provider_key,
        generated_root=generated_root,
        manifest_relative_path=layout.manifest_relative_path,
    )


def _root_relative_path(
    *,
    path: str,
    package_root: str,
    path_scope: str,
) -> str:
    if path_scope == "root_relative":
        return path
    if path_scope == "package_relative":
        return _join_relative_paths(package_root, path)
    raise FileSystemSdkError(f"Unsupported FileSystem SDK path scope: {path_scope}")


def _package_relative_path(
    *,
    root_relative_path: str,
    package_root: str,
) -> str | None:
    if package_root == ".":
        return root_relative_path
    if root_relative_path == package_root:
        return "."
    prefix = package_root.rstrip("/") + "/"
    if root_relative_path.startswith(prefix):
        return root_relative_path.removeprefix(prefix)
    return None


def _optional_layout_root(*, package_root: str, value: object) -> str | None:
    root = _optional_relative_path(value)
    if root is None:
        return None
    if package_root == ".":
        return root
    if root == package_root or root.startswith(package_root.rstrip("/") + "/"):
        return root
    return _join_relative_paths(package_root, root)


def _optional_relative_path(value: object) -> str | None:
    text = _optional_str(value)
    if text is None:
        return None
    return normalize_relative_path(text)


def _required_relative_path(value: object, context: str) -> str:
    path = _optional_relative_path(value)
    if path is None:
        raise FileSystemSdkError(f"{context} requires a relative path.")
    return path


def _join_relative_paths(base: str, relative: str) -> str:
    if base == ".":
        return relative
    if relative == ".":
        return base
    return f"{base.rstrip('/')}/{relative.lstrip('/')}"


def _is_relative_path_under(*, child: str, parent: str) -> bool:
    if parent == ".":
        return True
    return child == parent or child.startswith(parent.rstrip("/") + "/")


def _semantic_owner_hints(
    *,
    provider_key: str | None,
    explicit_hints: Iterable[str],
) -> tuple[str, ...]:
    hints: list[str] = []
    for hint in explicit_hints:
        _append_unique(hints, hint)
    if provider_key is not None:
        _append_unique(hints, provider_key)
    return tuple(hints)


def _provider_key(
    *,
    layout_contract: CodePackageLayoutContract,
    semantic_contract: CodeSemanticContract | None,
) -> str | None:
    if semantic_contract is not None:
        provider_key = _optional_str(getattr(semantic_contract, "provider_key", None))
        if provider_key is not None:
            return provider_key
    metadata = _model_mapping(getattr(layout_contract, "metadata", None))
    if metadata is None:
        return None
    return _optional_str(metadata.get("provider_key"))


def _role_counts(
    classifications: tuple[FileSystemCodeLayoutPathClassification, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in classifications:
        key = item.role_value or "unclassified"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _normalize_pattern(pattern: str) -> str:
    return pattern.strip().replace("\\", "/").strip("/")


def _optional_str(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _append_unique(items: list[str], value: str) -> None:
    text = value.strip()
    if text and text not in items:
        items.append(text)


def _model_mapping(value: object) -> Mapping[str, object] | None:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return cast(Mapping[str, object], model_dump(mode="json"))
    return None


__all__ = [
    "FileSystemCodeLayoutClassificationResult",
    "FileSystemCodeLayoutClassifier",
    "FileSystemCodeLayoutPathClassification",
    "FileSystemCodeLayoutPathScope",
    "build_code_layout_classifier",
    "classify_code_layout_paths",
]
