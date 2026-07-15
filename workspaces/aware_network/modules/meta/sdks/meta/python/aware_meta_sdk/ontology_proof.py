from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_meta_sdk.client import MetaSdkClient
from aware_meta_service_dto.diagnostics.completeness import (
    MetaCompletenessAnalyzeResponse,
)
from aware_meta_service_dto.graph.config.package_compile import (
    MetaObjectConfigGraphPackageDependencyRef,
)


@dataclass(frozen=True, slots=True)
class OigCommitExpectation:
    label: str = "oig commit"
    require_domain_commit_id: bool = True
    require_object_instance_graph_commit_id: bool = True
    require_graph_hash_post: bool = True
    require_root_object_id: bool = True
    expected_domain_branch_id: UUID | None = None
    expected_domain_projection_hash: str | None = None
    expected_root_object_id: UUID | None = None

    def assert_matches(self, response: object) -> None:
        errors: list[str] = []
        if self.require_domain_commit_id and _field(response, "domain_commit_id") is None:
            errors.append("missing domain_commit_id")
        if (
            self.require_object_instance_graph_commit_id
            and _field(response, "object_instance_graph_commit_id") is None
        ):
            errors.append("missing object_instance_graph_commit_id")
        if self.require_graph_hash_post and not _field(response, "graph_hash_post"):
            errors.append("missing graph_hash_post")
        if self.require_root_object_id and _field(response, "root_object_id") is None:
            errors.append("missing root_object_id")
        if (
            self.expected_domain_branch_id is not None
            and _field(response, "domain_branch_id") != self.expected_domain_branch_id
        ):
            errors.append(
                "domain_branch_id mismatch: "
                + f"expected={self.expected_domain_branch_id} "
                + f"actual={_field(response, 'domain_branch_id')}"
            )
        if (
            self.expected_domain_projection_hash is not None
            and _field(response, "domain_projection_hash")
            != self.expected_domain_projection_hash
        ):
            errors.append(
                "domain_projection_hash mismatch: "
                + f"expected={self.expected_domain_projection_hash!r} "
                + f"actual={_field(response, 'domain_projection_hash')!r}"
            )
        if (
            self.expected_root_object_id is not None
            and _field(response, "root_object_id") != self.expected_root_object_id
        ):
            errors.append(
                "root_object_id mismatch: "
                + f"expected={self.expected_root_object_id} "
                + f"actual={_field(response, 'root_object_id')}"
            )
        if errors:
            raise AssertionError(f"{self.label} expectation failed: " + "; ".join(errors))


@dataclass(frozen=True, slots=True)
class ProjectionProof:
    projection_name: str
    commit_expectations: tuple[OigCommitExpectation, ...] = ()


@dataclass(frozen=True, slots=True)
class FunctionCallProof:
    function_key: str
    commit_expectation: OigCommitExpectation = OigCommitExpectation()

    def assert_matches(self, response: object) -> None:
        self.commit_expectation.assert_matches(response)


@dataclass(frozen=True, slots=True)
class FunctionCoverageSkip:
    function_key: str
    reason: str


@dataclass(frozen=True, slots=True)
class ProjectionBehaviorProof:
    projection_name: str
    covered_functions: tuple[str | FunctionCallProof, ...] = ()
    expected_skips: tuple[FunctionCoverageSkip, ...] = ()


@dataclass(frozen=True, slots=True)
class ProjectionProofResult:
    proof: ProjectionProof
    exists: bool

    @property
    def projection_name(self) -> str:
        return self.proof.projection_name

    @property
    def commit_expectation_count(self) -> int:
        return len(self.proof.commit_expectations)

    def assert_satisfied(self) -> None:
        if not self.exists:
            raise AssertionError(f"Missing projection proof: {self.projection_name}")


@dataclass(frozen=True, slots=True)
class ProjectionFunctionProofResult:
    function_key: str
    status: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectionBehaviorProofResult:
    proof: ProjectionBehaviorProof
    exists: bool
    required_function_keys: tuple[str, ...]
    function_results: tuple[ProjectionFunctionProofResult, ...]
    covered_function_proofs: tuple[FunctionCallProof, ...]
    covered_function_keys: tuple[str, ...]
    skipped_function_keys: tuple[str, ...]
    missing_function_keys: tuple[str, ...]
    unknown_function_keys: tuple[str, ...]
    invalid_skip_function_keys: tuple[str, ...]

    @property
    def projection_name(self) -> str:
        return self.proof.projection_name

    def assert_satisfied(self) -> None:
        errors: list[str] = []
        if not self.exists:
            errors.append("projection not found")
        if self.invalid_skip_function_keys:
            errors.append(
                "skip reason missing for: "
                + ", ".join(self.invalid_skip_function_keys)
            )
        if self.unknown_function_keys:
            errors.append(
                "unknown function keys: " + ", ".join(self.unknown_function_keys)
            )
        if self.missing_function_keys:
            errors.append(
                "missing function coverage: "
                + ", ".join(self.missing_function_keys)
            )
        if errors:
            raise AssertionError(
                "Projection behavior proof failed for "
                + f"{self.projection_name}: "
                + "; ".join(errors)
            )

    @property
    def passed_function_keys(self) -> tuple[str, ...]:
        return tuple(
            result.function_key
            for result in self.function_results
            if result.status == "passed"
        )

    @property
    def report(self) -> ProjectionBehaviorProofReport:
        return ProjectionBehaviorProofReport(
            projection_name=self.projection_name,
            status=(
                "passed"
                if self.exists
                and not self.missing_function_keys
                and not self.unknown_function_keys
                and not self.invalid_skip_function_keys
                else "failed"
            ),
            exists=self.exists,
            required_function_keys=self.required_function_keys,
            passed_function_keys=self.passed_function_keys,
            skipped_function_keys=self.skipped_function_keys,
            missing_function_keys=self.missing_function_keys,
            unknown_function_keys=self.unknown_function_keys,
            invalid_skip_function_keys=self.invalid_skip_function_keys,
        )


@dataclass(frozen=True, slots=True)
class ProjectionBehaviorProofReport:
    projection_name: str
    status: str
    exists: bool
    required_function_keys: tuple[str, ...]
    passed_function_keys: tuple[str, ...]
    skipped_function_keys: tuple[str, ...]
    missing_function_keys: tuple[str, ...]
    unknown_function_keys: tuple[str, ...]
    invalid_skip_function_keys: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "projection_name": self.projection_name,
            "status": self.status,
            "exists": self.exists,
            "required_functions": list(self.required_function_keys),
            "passed_functions": list(self.passed_function_keys),
            "skipped_functions": list(self.skipped_function_keys),
            "missing_functions": list(self.missing_function_keys),
            "unknown_functions": list(self.unknown_function_keys),
            "invalid_skip_functions": list(self.invalid_skip_function_keys),
        }


@dataclass(frozen=True, slots=True)
class OntologyProofReport:
    status: str
    response_status: str
    package_name: str | None
    fqn_prefix: str | None
    diagnostic_count: int
    diagnostic_codes: tuple[str, ...]
    projection_names: tuple[str, ...]
    missing_projection_names: tuple[str, ...]
    behavior_reports: tuple[ProjectionBehaviorProofReport, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "response_status": self.response_status,
            "package_name": self.package_name,
            "fqn_prefix": self.fqn_prefix,
            "diagnostic_count": self.diagnostic_count,
            "diagnostic_codes": list(self.diagnostic_codes),
            "projection_names": list(self.projection_names),
            "missing_projection_names": list(self.missing_projection_names),
            "behavior_proofs": [
                report.as_dict() for report in self.behavior_reports
            ],
        }


@dataclass(frozen=True, slots=True)
class OntologyProofResult:
    response: MetaCompletenessAnalyzeResponse
    object_config_graph: Mapping[str, Any]
    projection_results: tuple[ProjectionProofResult, ...]
    behavior_results: tuple[ProjectionBehaviorProofResult, ...] = ()

    @property
    def package_name(self) -> str | None:
        return self.response.package_name

    @property
    def fqn_prefix(self) -> str | None:
        return self.response.fqn_prefix

    @property
    def projection_names(self) -> frozenset[str]:
        return frozenset(_projection_names(self.object_config_graph))

    @property
    def missing_projection_names(self) -> tuple[str, ...]:
        return tuple(
            result.projection_name
            for result in self.projection_results
            if not result.exists
        )

    @property
    def report(self) -> OntologyProofReport:
        behavior_reports = tuple(result.report for result in self.behavior_results)
        return OntologyProofReport(
            status=(
                "passed"
                if self.response.status == "succeeded"
                and not self.response.diagnostics
                and not self.missing_projection_names
                and all(report.status == "passed" for report in behavior_reports)
                else "failed"
            ),
            response_status=self.response.status,
            package_name=self.package_name,
            fqn_prefix=self.fqn_prefix,
            diagnostic_count=len(self.response.diagnostics),
            diagnostic_codes=tuple(
                str(getattr(diagnostic, "code", ""))
                for diagnostic in self.response.diagnostics
            ),
            projection_names=tuple(sorted(self.projection_names)),
            missing_projection_names=self.missing_projection_names,
            behavior_reports=behavior_reports,
        )

    def assert_succeeded(self) -> None:
        if self.response.status != "succeeded":
            raise AssertionError(
                "Ontology proof failed: "
                + f"status={self.response.status!r} error={self.response.error!r}"
            )
        self.assert_projection_proofs()
        self.assert_behavior_proofs()

    def assert_zero_diagnostics(self) -> None:
        if self.response.diagnostics:
            raise AssertionError(
                "Ontology proof produced diagnostics: "
                + repr(self.response.diagnostics)
            )

    def assert_projection_proofs(self) -> None:
        missing = self.missing_projection_names
        if missing:
            raise AssertionError(
                "Missing projection proofs: "
                + ", ".join(missing)
                + f"; available={sorted(self.projection_names)!r}"
            )

    def assert_behavior_proofs(self) -> None:
        for result in self.behavior_results:
            result.assert_satisfied()

    def assert_complete(self) -> None:
        self.assert_succeeded()
        self.assert_zero_diagnostics()


async def prove_ontology_package(
    sdk: MetaSdkClient,
    *,
    package_root: str | Path,
    actor_id: UUID | None = None,
    workspace_root: str | Path | None = None,
    aware_toml_path: str | None = "aware.toml",
    source_files: Sequence[str] = (),
    dependency_refs: Sequence[MetaObjectConfigGraphPackageDependencyRef] = (),
    projection_proofs: Sequence[ProjectionProof | str] = (),
    behavior_proofs: Sequence[ProjectionBehaviorProof] = (),
    completeness_diagnostics: bool = True,
    diagnostic_severity: str = "warning",
) -> OntologyProofResult:
    response = await sdk.analyze_object_config_graph_completeness(
        package_root=_path_string(package_root),
        actor_id=actor_id,
        workspace_root=(
            None if workspace_root is None else _path_string(workspace_root)
        ),
        aware_toml_path=aware_toml_path,
        source_files=source_files,
        dependency_refs=dependency_refs,
        completeness_diagnostics=completeness_diagnostics,
        diagnostic_severity=diagnostic_severity,
        include_object_config_graph=True,
    )
    object_config_graph = _object_config_graph(response.object_config_graph)
    projection_names = _projection_names(object_config_graph)
    normalized_proofs = tuple(_projection_proof(proof) for proof in projection_proofs)
    normalized_behavior_proofs = tuple(behavior_proofs)
    return OntologyProofResult(
        response=response,
        object_config_graph=object_config_graph,
        projection_results=tuple(
            ProjectionProofResult(
                proof=proof,
                exists=proof.projection_name in projection_names,
            )
            for proof in normalized_proofs
        ),
        behavior_results=tuple(
            _projection_behavior_result(
                object_config_graph=object_config_graph,
                proof=proof,
                projection_names=projection_names,
            )
            for proof in normalized_behavior_proofs
        ),
    )


def assert_oig_commit_matches(
    response: object,
    expectation: OigCommitExpectation | None = None,
) -> None:
    (expectation or OigCommitExpectation()).assert_matches(response)


def _projection_proof(value: ProjectionProof | str) -> ProjectionProof:
    if isinstance(value, ProjectionProof):
        return value
    return ProjectionProof(projection_name=value)


def _function_call_proof(value: str | FunctionCallProof) -> FunctionCallProof:
    if isinstance(value, FunctionCallProof):
        return value
    return FunctionCallProof(function_key=value)


def _projection_behavior_result(
    *,
    object_config_graph: Mapping[str, Any],
    proof: ProjectionBehaviorProof,
    projection_names: set[str],
) -> ProjectionBehaviorProofResult:
    requirements = _projection_function_requirements(
        object_config_graph,
        proof.projection_name,
    )
    required_keys = tuple(requirement.key for requirement in requirements)
    covered_function_proofs = tuple(
        _function_call_proof(value) for value in proof.covered_functions
    )
    covered_keys, unknown_covered = _match_function_keys(
        requirements,
        tuple(value.function_key for value in covered_function_proofs),
    )
    skip_keys = tuple(skip.function_key for skip in proof.expected_skips)
    skipped_keys, unknown_skips = _match_function_keys(requirements, skip_keys)
    skip_reason_by_key = _skip_reason_by_required_key(
        requirements=requirements,
        expected_skips=proof.expected_skips,
        skipped_keys=skipped_keys,
    )
    invalid_skip_keys = tuple(
        key for key in skipped_keys if not skip_reason_by_key.get(key, "").strip()
    )
    covered_set = frozenset(covered_keys)
    skipped_set = frozenset(skipped_keys)
    missing_keys = tuple(
        key for key in required_keys if key not in covered_set and key not in skipped_set
    )
    function_results = tuple(
        ProjectionFunctionProofResult(
            function_key=key,
            status=(
                "passed"
                if key in covered_set
                else "skipped"
                if key in skipped_set
                else "missing"
            ),
            reason=skip_reason_by_key.get(key),
        )
        for key in required_keys
    )
    return ProjectionBehaviorProofResult(
        proof=proof,
        exists=proof.projection_name in projection_names,
        required_function_keys=required_keys,
        function_results=function_results,
        covered_function_proofs=covered_function_proofs,
        covered_function_keys=covered_keys,
        skipped_function_keys=skipped_keys,
        missing_function_keys=missing_keys,
        unknown_function_keys=tuple(sorted((*unknown_covered, *unknown_skips))),
        invalid_skip_function_keys=invalid_skip_keys,
    )


@dataclass(frozen=True, slots=True)
class _FunctionRequirement:
    key: str
    aliases: frozenset[str]


def _projection_function_requirements(
    object_config_graph: Mapping[str, Any],
    projection_name: str,
) -> tuple[_FunctionRequirement, ...]:
    class_names = _projection_class_names(object_config_graph, projection_name)
    class_configs = _class_configs_by_name(object_config_graph)
    requirements: list[_FunctionRequirement] = []
    seen: set[str] = set()
    for class_name in sorted(class_names):
        class_config = class_configs.get(class_name)
        if class_config is None:
            continue
        for requirement in _class_function_requirements(class_config):
            if requirement.key in seen:
                continue
            seen.add(requirement.key)
            requirements.append(requirement)
    return tuple(requirements)


def _projection_class_names(
    object_config_graph: Mapping[str, Any],
    projection_name: str,
) -> frozenset[str]:
    names: set[str] = set()
    for declaration in _mapping_items(
        object_config_graph.get("object_projection_graph_declarations")
    ):
        if declaration.get("projection_name") != projection_name:
            continue
        for binding in _mapping_items(
            declaration.get("object_projection_graph_bindings")
        ):
            _add_string(names, binding.get("class_name"))
            _add_string(names, binding.get("class_fqn"))
            _add_string(names, binding.get("object_fqn"))
    return frozenset(names)


def _class_configs_by_name(
    object_config_graph: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    configs: dict[str, Mapping[str, Any]] = {}
    for node in _mapping_items(object_config_graph.get("object_config_graph_nodes")):
        class_config = node.get("class_config")
        if not isinstance(class_config, Mapping):
            continue
        for key in (
            class_config.get("name"),
            class_config.get("class_fqn"),
            class_config.get("owner_key"),
        ):
            if isinstance(key, str) and key:
                configs[key] = class_config
    return configs


def _class_function_requirements(
    class_config: Mapping[str, Any],
) -> tuple[_FunctionRequirement, ...]:
    class_name = str(class_config.get("name") or class_config.get("class_fqn"))
    class_fqn = class_config.get("class_fqn")
    requirements: list[_FunctionRequirement] = []
    for link in _mapping_items(class_config.get("class_config_function_configs")):
        function_config = link.get("function_config")
        if not isinstance(function_config, Mapping):
            continue
        function_name = function_config.get("name")
        if not isinstance(function_name, str) or not function_name:
            continue
        canonical_key = f"{class_name}.{function_name}"
        aliases = {canonical_key}
        for owner_key in (class_fqn, function_config.get("owner_key")):
            if isinstance(owner_key, str) and owner_key:
                aliases.add(f"{owner_key}.{function_name}")
        requirements.append(
            _FunctionRequirement(
                key=canonical_key,
                aliases=frozenset(aliases),
            )
        )
    return tuple(requirements)


def _match_function_keys(
    requirements: tuple[_FunctionRequirement, ...],
    declared_keys: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    matched: list[str] = []
    unknown: list[str] = []
    for declared_key in declared_keys:
        requirement = _requirement_for_declared_key(requirements, declared_key)
        if requirement is None:
            unknown.append(declared_key)
            continue
        if requirement.key not in matched:
            matched.append(requirement.key)
    return tuple(matched), tuple(unknown)


def _requirement_for_declared_key(
    requirements: tuple[_FunctionRequirement, ...],
    declared_key: str,
) -> _FunctionRequirement | None:
    normalized = str(declared_key).strip()
    for requirement in requirements:
        if normalized in requirement.aliases:
            return requirement
    return None


def _skip_reason_by_required_key(
    *,
    requirements: tuple[_FunctionRequirement, ...],
    expected_skips: tuple[FunctionCoverageSkip, ...],
    skipped_keys: tuple[str, ...],
) -> dict[str, str]:
    skipped = frozenset(skipped_keys)
    reasons: dict[str, str] = {}
    for skip in expected_skips:
        requirement = _requirement_for_declared_key(
            requirements,
            skip.function_key,
        )
        if requirement is None or requirement.key not in skipped:
            continue
        reasons[requirement.key] = skip.reason
    return reasons


def _add_string(target: set[str], value: object) -> None:
    if isinstance(value, str) and value:
        target.add(value)


def _object_config_graph(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AssertionError("Ontology proof response did not include an OCG payload")
    return value


def _projection_names(object_config_graph: Mapping[str, Any]) -> set[str]:
    names: set[str] = set()
    for declaration in _mapping_items(
        object_config_graph.get("object_projection_graph_declarations")
    ):
        projection_name = declaration.get("projection_name")
        if isinstance(projection_name, str):
            names.add(projection_name)
    return names


def _mapping_items(value: object) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise AssertionError(f"Expected list payload, got {type(value).__name__}")
    items: list[Mapping[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise AssertionError(
                f"Expected mapping payload item, got {type(item).__name__}"
            )
        items.append(item)
    return tuple(items)


def _field(response: object, name: str) -> object:
    if isinstance(response, Mapping):
        return response.get(name)
    return getattr(response, name, None)


def _path_string(path: str | Path) -> str:
    return path.as_posix() if isinstance(path, Path) else path
