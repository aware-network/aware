from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from aware_meta.materialization.deltas.code_dto import (
    CodeGeneratedMaterializationDeltaResult,
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
    CodePackagePathRole,
)


GENERATED_MATERIALIZATION_EVIDENCE_MANIFEST_CONTRACT_VERSION = (
    "aware.meta.generated-materialization-evidence-manifest.v1"
)


@dataclass(frozen=True, slots=True)
class GeneratedMaterializationPathContentMap:
    """Language-neutral path/content evidence extracted from Code package deltas."""

    content_text_by_path: dict[str, str]
    duplicate_paths: tuple[str, ...] = ()
    missing_content_text_paths: tuple[str, ...] = ()
    unsupported_path_kind_paths: tuple[str, ...] = ()
    deleted_paths: tuple[str, ...] = ()
    package_delta_entry_count: int = 0
    package_delta_path_count: int = 0

    @property
    def clean(self) -> bool:
        return not (
            self.duplicate_paths
            or self.missing_content_text_paths
            or self.unsupported_path_kind_paths
        )


@dataclass(frozen=True, slots=True)
class GeneratedMaterializationPathContentComparison:
    """Byte-level comparison between full render output and delta output."""

    expected_by_path: dict[str, str]
    actual_by_path: dict[str, str]
    duplicate_paths: tuple[str, ...] = ()
    missing_content_text_paths: tuple[str, ...] = ()
    missing_paths: tuple[str, ...] = ()
    unexpected_paths: tuple[str, ...] = ()
    mismatched_paths: tuple[str, ...] = ()
    unsupported_path_kind_paths: tuple[str, ...] = ()

    @property
    def equivalent(self) -> bool:
        return not (
            self.duplicate_paths
            or self.missing_content_text_paths
            or self.unsupported_path_kind_paths
            or self.missing_paths
            or self.unexpected_paths
            or self.mismatched_paths
        )

    @property
    def diagnostics(self) -> tuple[str, ...]:
        diagnostics: list[str] = []
        if self.duplicate_paths:
            diagnostics.append("duplicate_paths:" + ",".join(self.duplicate_paths))
        if self.missing_content_text_paths:
            diagnostics.append(
                "missing_content_text_paths:"
                + ",".join(self.missing_content_text_paths)
            )
        if self.unsupported_path_kind_paths:
            diagnostics.append(
                "unsupported_path_kind_paths:"
                + ",".join(self.unsupported_path_kind_paths)
            )
        if self.missing_paths:
            diagnostics.append("missing_paths:" + ",".join(self.missing_paths))
        if self.unexpected_paths:
            diagnostics.append("unexpected_paths:" + ",".join(self.unexpected_paths))
        if self.mismatched_paths:
            diagnostics.append("mismatched_paths:" + ",".join(self.mismatched_paths))
        return tuple(diagnostics)

    def summary(self) -> str:
        if self.equivalent:
            return "generated materialization path/content maps are equivalent"
        return "; ".join(self.diagnostics)


@dataclass(frozen=True, slots=True)
class GeneratedMaterializationArtifactPathEvidence:
    """One language-neutral package-delta artifact path emission."""

    provider_key: str
    semantic_owner: str | None
    result_mode: str | None
    entry_mode: str | None
    package_name: str | None
    target_language: str | None
    renderer_profile: str | None
    materialization_source: str | None
    artifact_family: str | None
    artifact_role: str | None
    artifact_key: str | None
    relative_path: str
    path_kind: str
    path_role: str | None
    delta_form: str | None
    has_content_text: bool

    def evidence_payload(self) -> dict[str, object]:
        return {
            "provider_key": self.provider_key,
            "semantic_owner": self.semantic_owner,
            "result_mode": self.result_mode,
            "entry_mode": self.entry_mode,
            "package_name": self.package_name,
            "target_language": self.target_language,
            "renderer_profile": self.renderer_profile,
            "materialization_source": self.materialization_source,
            "artifact_family": self.artifact_family,
            "artifact_role": self.artifact_role,
            "artifact_key": self.artifact_key,
            "relative_path": self.relative_path,
            "path_kind": self.path_kind,
            "path_role": self.path_role,
            "delta_form": self.delta_form,
            "has_content_text": self.has_content_text,
        }


@dataclass(frozen=True, slots=True)
class GeneratedMaterializationEvidenceManifest:
    """Neutral manifest over generated-materialization package-delta evidence."""

    result_count: int
    entry_count: int
    package_delta_entry_count: int
    package_delta_path_count: int
    non_package_delta_entry_count: int
    artifact_paths: tuple[GeneratedMaterializationArtifactPathEvidence, ...]
    contract_version: str = GENERATED_MATERIALIZATION_EVIDENCE_MANIFEST_CONTRACT_VERSION

    @property
    def artifact_path_count(self) -> int:
        return len(self.artifact_paths)

    @property
    def missing_content_text_path_count(self) -> int:
        return sum(1 for path in self.artifact_paths if not path.has_content_text)

    @property
    def missing_artifact_family_count(self) -> int:
        return sum(1 for path in self.artifact_paths if path.artifact_family is None)

    @property
    def missing_artifact_role_count(self) -> int:
        return sum(1 for path in self.artifact_paths if path.artifact_role is None)

    @property
    def artifact_family_counts(self) -> dict[str, int]:
        return _counts_by_optional_text(
            path.artifact_family for path in self.artifact_paths
        )

    @property
    def artifact_role_counts(self) -> dict[str, int]:
        return _counts_by_optional_text(
            path.artifact_role for path in self.artifact_paths
        )

    @property
    def delta_form_counts(self) -> dict[str, int]:
        return _counts_by_optional_text(path.delta_form for path in self.artifact_paths)

    @property
    def path_kind_counts(self) -> dict[str, int]:
        return _counts_by_optional_text(path.path_kind for path in self.artifact_paths)

    @property
    def path_role_counts(self) -> dict[str, int]:
        return _counts_by_optional_text(path.path_role for path in self.artifact_paths)

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "result_count": self.result_count,
            "entry_count": self.entry_count,
            "package_delta_entry_count": self.package_delta_entry_count,
            "package_delta_path_count": self.package_delta_path_count,
            "non_package_delta_entry_count": self.non_package_delta_entry_count,
            "artifact_path_count": self.artifact_path_count,
            "missing_content_text_path_count": self.missing_content_text_path_count,
            "missing_artifact_family_count": self.missing_artifact_family_count,
            "missing_artifact_role_count": self.missing_artifact_role_count,
            "artifact_family_counts": self.artifact_family_counts,
            "artifact_role_counts": self.artifact_role_counts,
            "delta_form_counts": self.delta_form_counts,
            "path_kind_counts": self.path_kind_counts,
            "path_role_counts": self.path_role_counts,
            "artifact_paths": tuple(
                path.evidence_payload() for path in self.artifact_paths
            ),
        }


def generated_materialization_path_content_map_from_results(
    delta_results: Iterable[CodeGeneratedMaterializationDeltaResult],
) -> GeneratedMaterializationPathContentMap:
    """Extract a language-neutral generated package path/content map.

    Meta owns this evidence shape because it only depends on the generated
    materialization result envelope and CodePackageDelta DTO. Language renderers
    still own how each package delta path is produced.
    """

    content_text_by_path: dict[str, str] = {}
    duplicate_paths: list[str] = []
    missing_content_text_paths: list[str] = []
    package_delta_entry_count = 0
    package_delta_path_count = 0

    for result in delta_results:
        for entry in result.entries:
            if entry.package_delta is None:
                continue
            package_delta_entry_count += 1
            for path in entry.package_delta.paths:
                package_delta_path_count += 1
                relative_path = path.relative_path.strip()
                if path.content_text is None:
                    _append_once(missing_content_text_paths, relative_path)
                    continue
                if relative_path in content_text_by_path:
                    _append_once(duplicate_paths, relative_path)
                content_text_by_path[relative_path] = path.content_text

    return GeneratedMaterializationPathContentMap(
        content_text_by_path=content_text_by_path,
        duplicate_paths=tuple(sorted(duplicate_paths)),
        missing_content_text_paths=tuple(sorted(missing_content_text_paths)),
        package_delta_entry_count=package_delta_entry_count,
        package_delta_path_count=package_delta_path_count,
    )


def generated_materialization_evidence_manifest_from_results(
    delta_results: Iterable[CodeGeneratedMaterializationDeltaResult],
) -> GeneratedMaterializationEvidenceManifest:
    """Build a neutral manifest from generated-materialization package evidence.

    The manifest intentionally reads only public Code DTO envelopes. It may
    expose target language/profile values present in evidence, but it does not
    import renderer modules or interpret renderer-specific artifact semantics.
    """

    result_count = 0
    entry_count = 0
    package_delta_entry_count = 0
    package_delta_path_count = 0
    non_package_delta_entry_count = 0
    artifact_paths: list[GeneratedMaterializationArtifactPathEvidence] = []

    for result in delta_results:
        result_count += 1
        result_mode = _object_text(result.mode)
        for entry in result.entries:
            entry_count += 1
            if entry.package_delta is None:
                non_package_delta_entry_count += 1
                continue
            package_delta_entry_count += 1
            package_delta = entry.package_delta
            target = entry.target
            for path in package_delta.paths:
                package_delta_path_count += 1
                relative_path = path.relative_path.strip()
                artifact_paths.append(
                    GeneratedMaterializationArtifactPathEvidence(
                        provider_key=result.provider_key,
                        semantic_owner=_object_text(result.semantic_owner),
                        result_mode=result_mode,
                        entry_mode=_object_text(entry.mode),
                        package_name=_first_text(
                            package_delta.package_name,
                            target.package_name,
                        ),
                        target_language=_object_text(target.target_language),
                        renderer_profile=_object_text(target.renderer_profile),
                        materialization_source=_object_text(
                            target.materialization_source
                        ),
                        artifact_family=_first_text(
                            entry.artifact_family,
                            target.artifact_family,
                            _metadata_text(path.metadata, "artifact_family"),
                            _metadata_text(package_delta.metadata, "artifact_family"),
                        ),
                        artifact_role=_first_text(
                            entry.artifact_role,
                            target.artifact_role,
                            _metadata_text(path.metadata, "artifact_role"),
                            _metadata_text(package_delta.metadata, "artifact_role"),
                        ),
                        artifact_key=_first_text(
                            entry.artifact_key,
                            target.output_key,
                            relative_path,
                        ),
                        relative_path=relative_path,
                        path_kind=_object_text(path.kind) or "",
                        path_role=_object_text(path.path_role),
                        delta_form=_first_text(
                            _metadata_text(path.metadata, "delta_form"),
                            _metadata_text(package_delta.metadata, "delta_form"),
                            _metadata_text(entry.metadata, "delta_form"),
                        ),
                        has_content_text=path.content_text is not None,
                    )
                )

    return GeneratedMaterializationEvidenceManifest(
        result_count=result_count,
        entry_count=entry_count,
        package_delta_entry_count=package_delta_entry_count,
        package_delta_path_count=package_delta_path_count,
        non_package_delta_entry_count=non_package_delta_entry_count,
        artifact_paths=tuple(artifact_paths),
    )


def generated_materialization_path_content_map_from_package_deltas(
    package_deltas: Iterable[CodePackageDelta],
) -> GeneratedMaterializationPathContentMap:
    """Extract path/content evidence from resolved CodePackageDelta DTOs."""

    return _path_content_map_from_package_deltas(package_deltas)


def generated_materialization_package_delta_from_path_content_map(
    *,
    package_name: str,
    content_text_by_path: Mapping[str, str],
    path_role: CodePackagePathRole = CodePackagePathRole.generated_code,
    path_kind: CodePackageDeltaKind = CodePackageDeltaKind.update,
) -> CodePackageDelta:
    """Build generated package-delta evidence from authoritative path bytes.

    This is for package-derived genesis/materialization receipts where the
    renderer can emit complete generated path content for the selected package.
    It does not infer semantic meaning from filenames and does not import a
    language renderer; callers provide the already-authoritative path/content
    map for the generated package surface.
    """

    return CodePackageDelta(
        package_name=package_name,
        paths=[
            CodePackageDeltaPath(
                relative_path=relative_path,
                kind=path_kind,
                content_text=content_text,
                path_role=path_role,
            )
            for relative_path, content_text in sorted(
                _normalized_expected_path_map(content_text_by_path).items(),
            )
        ],
    )


def compare_generated_materialization_path_content_map(
    *,
    expected_by_path: Mapping[str, str],
    delta_results: Iterable[CodeGeneratedMaterializationDeltaResult],
) -> GeneratedMaterializationPathContentComparison:
    """Compare full-render path bytes with aggregated generated-delta bytes."""

    expected = _normalized_expected_path_map(expected_by_path)
    actual = generated_materialization_path_content_map_from_results(delta_results)
    return _compare_expected_actual_path_content_maps(expected=expected, actual=actual)


def compare_generated_materialization_package_delta_path_content_map(
    *,
    expected_by_path: Mapping[str, str],
    package_deltas: Iterable[CodePackageDelta],
) -> GeneratedMaterializationPathContentComparison:
    """Compare full-render bytes with resolved generated package-delta bytes."""

    expected = _normalized_expected_path_map(expected_by_path)
    actual = _path_content_map_from_package_deltas(package_deltas)
    return _compare_expected_actual_path_content_maps(expected=expected, actual=actual)


def generated_materialization_final_path_content_map_from_package_deltas(
    *,
    baseline_by_path: Mapping[str, str],
    package_deltas: Iterable[CodePackageDelta],
) -> GeneratedMaterializationPathContentMap:
    """Apply ordered CodePackageDelta evidence to a baseline path/content map."""

    content_text_by_path = _normalized_expected_path_map(baseline_by_path)
    missing_content_text_paths: list[str] = []
    unsupported_path_kind_paths: list[str] = []
    deleted_paths: list[str] = []
    package_delta_path_count = 0

    for package_delta in package_deltas:
        for path in package_delta.paths:
            package_delta_path_count += 1
            relative_path = path.relative_path.strip()
            path_kind = _path_kind_value(path.kind)
            if path_kind == CodePackageDeltaKind.delete.value:
                content_text_by_path.pop(relative_path, None)
                _append_once(deleted_paths, relative_path)
                continue
            if path_kind not in {
                CodePackageDeltaKind.create.value,
                CodePackageDeltaKind.update.value,
            }:
                _append_once(unsupported_path_kind_paths, relative_path)
                continue
            if path.content_text is None:
                _append_once(missing_content_text_paths, relative_path)
                continue
            content_text_by_path[relative_path] = path.content_text

    return GeneratedMaterializationPathContentMap(
        content_text_by_path=content_text_by_path,
        missing_content_text_paths=tuple(sorted(missing_content_text_paths)),
        unsupported_path_kind_paths=tuple(sorted(unsupported_path_kind_paths)),
        deleted_paths=tuple(sorted(deleted_paths)),
        package_delta_path_count=package_delta_path_count,
    )


def compare_generated_materialization_package_delta_final_state(
    *,
    expected_by_path: Mapping[str, str],
    baseline_by_path: Mapping[str, str],
    package_deltas: Iterable[CodePackageDelta],
) -> GeneratedMaterializationPathContentComparison:
    """Compare full-render bytes with final state after ordered package deltas."""

    expected = _normalized_expected_path_map(expected_by_path)
    actual = generated_materialization_final_path_content_map_from_package_deltas(
        baseline_by_path=baseline_by_path,
        package_deltas=package_deltas,
    )
    return _compare_expected_actual_path_content_maps(expected=expected, actual=actual)


def _path_content_map_from_package_deltas(
    package_deltas: Iterable[CodePackageDelta],
) -> GeneratedMaterializationPathContentMap:
    content_text_by_path: dict[str, str] = {}
    duplicate_paths: list[str] = []
    missing_content_text_paths: list[str] = []
    package_delta_path_count = 0

    for package_delta in package_deltas:
        for path in package_delta.paths:
            package_delta_path_count += 1
            relative_path = path.relative_path.strip()
            if path.content_text is None:
                _append_once(missing_content_text_paths, relative_path)
                continue
            if relative_path in content_text_by_path:
                _append_once(duplicate_paths, relative_path)
            content_text_by_path[relative_path] = path.content_text

    return GeneratedMaterializationPathContentMap(
        content_text_by_path=content_text_by_path,
        duplicate_paths=tuple(sorted(duplicate_paths)),
        missing_content_text_paths=tuple(sorted(missing_content_text_paths)),
        package_delta_entry_count=0,
        package_delta_path_count=package_delta_path_count,
    )


def _compare_expected_actual_path_content_maps(
    *,
    expected: Mapping[str, str],
    actual: GeneratedMaterializationPathContentMap,
) -> GeneratedMaterializationPathContentComparison:
    expected_paths = set(expected)
    actual_paths = set(actual.content_text_by_path)
    shared_paths = expected_paths.intersection(actual_paths)

    return GeneratedMaterializationPathContentComparison(
        expected_by_path=dict(expected),
        actual_by_path=dict(actual.content_text_by_path),
        duplicate_paths=actual.duplicate_paths,
        missing_content_text_paths=actual.missing_content_text_paths,
        unsupported_path_kind_paths=actual.unsupported_path_kind_paths,
        missing_paths=tuple(sorted(expected_paths - actual_paths)),
        unexpected_paths=tuple(sorted(actual_paths - expected_paths)),
        mismatched_paths=tuple(
            sorted(
                relative_path
                for relative_path in shared_paths
                if expected[relative_path] != actual.content_text_by_path[relative_path]
            )
        ),
    )


def _normalized_expected_path_map(
    expected_by_path: Mapping[str, str],
) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for relative_path, content_text in expected_by_path.items():
        clean_relative_path = relative_path.strip()
        if not clean_relative_path:
            raise ValueError("expected path map contains an empty relative path")
        normalized[clean_relative_path] = content_text
    return normalized


def _path_kind_value(value: object) -> str:
    if isinstance(value, CodePackageDeltaKind):
        return value.value
    if isinstance(value, str):
        return value
    raw_value = getattr(value, "value", None)
    if isinstance(raw_value, str):
        return raw_value
    return str(value)


def _object_text(value: object) -> str | None:
    if value is None:
        return None
    raw_value = getattr(value, "value", None)
    if isinstance(raw_value, str):
        return raw_value.strip() or None
    if isinstance(value, str):
        return value.strip() or None
    return str(value).strip() or None


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _object_text(value)
        if text is not None:
            return text
    return None


def _metadata_text(metadata: object, key: str) -> str | None:
    if not isinstance(metadata, Mapping):
        return None
    return _object_text(metadata.get(key))


def _counts_by_optional_text(values: Iterable[str | None]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        if value is None:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _append_once(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


__all__ = [
    "GENERATED_MATERIALIZATION_EVIDENCE_MANIFEST_CONTRACT_VERSION",
    "GeneratedMaterializationArtifactPathEvidence",
    "GeneratedMaterializationEvidenceManifest",
    "GeneratedMaterializationPathContentComparison",
    "GeneratedMaterializationPathContentMap",
    "compare_generated_materialization_package_delta_final_state",
    "compare_generated_materialization_package_delta_path_content_map",
    "compare_generated_materialization_path_content_map",
    "generated_materialization_evidence_manifest_from_results",
    "generated_materialization_final_path_content_map_from_package_deltas",
    "generated_materialization_package_delta_from_path_content_map",
    "generated_materialization_path_content_map_from_package_deltas",
    "generated_materialization_path_content_map_from_results",
]
