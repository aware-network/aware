from __future__ import annotations

from dataclasses import dataclass

from aware_code.module_semantic_contract import (
    WorkspaceSemanticArtifactBinding,
    WorkspaceSemanticArtifactLeafOwnershipClaim,
    WorkspaceSemanticArtifactLeafOwnershipRequest,
    WorkspaceSemanticArtifactProduction,
)
from aware_api_runtime.manifest.loader import load_aware_api_toml_spec
from aware_api_runtime.manifest.spec import (
    AwareApiTomlDartTargetSpec,
    AwareApiTomlPythonTargetSpec,
    AwareApiTomlSpec,
)


_PYTHON_ARTIFACT_MANIFEST_KINDS = frozenset({"pyproject_toml", "setup_py"})
_DART_ARTIFACT_MANIFEST_KINDS = frozenset({"pubspec_yaml"})


@dataclass(frozen=True, slots=True)
class _ApiArtifactOutput:
    package_root: str
    output_key: str
    output_kind: str


def resolve_workspace_semantic_artifact_leaf_ownership(
    *,
    request: WorkspaceSemanticArtifactLeafOwnershipRequest,
) -> WorkspaceSemanticArtifactLeafOwnershipClaim | None:
    """Resolve API-owned generated language package leaves for Workspace."""

    owner = request.owner
    leaf = request.leaf

    if owner.semantic_contract_provider_key != "aware_api":
        return None
    if owner.manifest_kind != "aware_api_toml":
        return None

    leaf_manifest_kind = leaf.manifest_kind
    if leaf_manifest_kind not in (
        *_PYTHON_ARTIFACT_MANIFEST_KINDS,
        *_DART_ARTIFACT_MANIFEST_KINDS,
    ):
        return None

    owner_manifest_relative_path = owner.manifest_relative_path
    owner_package_root = _normalize_repo_path(owner.package_root)
    leaf_package_root = _normalize_repo_path(leaf.package_root)
    if owner_package_root is None or leaf_package_root is None:
        return None

    spec = load_aware_api_toml_spec(
        toml_path=(request.workspace_root / owner_manifest_relative_path).resolve()
    )
    claimed_outputs = _claimed_api_artifact_outputs(
        spec=spec,
        package_root=owner_package_root,
        leaf_manifest_kind=leaf_manifest_kind,
    )
    claimed_output = next(
        (
            output
            for output in claimed_outputs
            if output.package_root == leaf_package_root
        ),
        None,
    )
    if claimed_output is None:
        return None

    return WorkspaceSemanticArtifactLeafOwnershipClaim(
        owned=True,
        owner_semantic_package_manifest=owner_manifest_relative_path,
        ownership_role="semantic_generated_artifact",
        artifact_manifest_kind=leaf_manifest_kind,
        artifact_package_root=leaf_package_root,
        production=_api_artifact_production(
            owner=request.owner,
            leaf=request.leaf,
            owner_manifest_relative_path=owner_manifest_relative_path,
            leaf_manifest_kind=leaf_manifest_kind,
            leaf_package_root=leaf_package_root,
            artifact_output=claimed_output,
        ),
    )


def _claimed_api_artifact_outputs(
    *,
    spec: AwareApiTomlSpec,
    package_root: str,
    leaf_manifest_kind: str,
) -> tuple[_ApiArtifactOutput, ...]:
    outputs: list[_ApiArtifactOutput] = []
    if leaf_manifest_kind in _PYTHON_ARTIFACT_MANIFEST_KINDS:
        python = spec.targets.python
        python_import_root = _derive_python_import_root(spec=spec)
        outputs.append(
            _ApiArtifactOutput(
                package_root=_python_product_package_root(
                    package_root=package_root,
                    targets=python,
                    legacy_root_dir=(
                        None if python is None else python.public_package.root_dir
                    ),
                    package_dir=(
                        None if python is None else python.public_package.package_dir
                    ),
                    import_root=python_import_root,
                ),
                output_key="python.public_package",
                output_kind="python_package_output",
            )
        )
        outputs.append(
            _ApiArtifactOutput(
                package_root=_python_product_package_root(
                    package_root=package_root,
                    targets=python,
                    legacy_root_dir=(
                        None if python is None else python.service_protocol.root_dir
                    ),
                    package_dir=(
                        None if python is None else python.service_protocol.package_dir
                    ),
                    import_root=_derive_python_service_protocol_import_root(
                        public_import_root=python_import_root
                    ),
                ),
                output_key="python.service_protocol_package",
                output_kind="python_package_output",
            )
        )
    if leaf_manifest_kind in _DART_ARTIFACT_MANIFEST_KINDS:
        dart = spec.targets.dart
        outputs.append(
            _ApiArtifactOutput(
                package_root=_dart_product_package_root(
                    package_root=package_root,
                    targets=dart,
                    package_name=_derive_dart_public_package_name(spec=spec),
                ),
                output_key="dart.public_package",
                output_kind="dart_package_output",
            )
        )
    return tuple(output for output in outputs if output.package_root)


def _api_artifact_production(
    *,
    owner: WorkspaceSemanticArtifactBinding,
    leaf: WorkspaceSemanticArtifactBinding,
    owner_manifest_relative_path: str,
    leaf_manifest_kind: str,
    leaf_package_root: str,
    artifact_output: _ApiArtifactOutput,
) -> WorkspaceSemanticArtifactProduction:
    provider_payload = {
        "semantic_contract_provider_key": (
            owner.semantic_contract_provider_key or "aware_api"
        ),
        "semantic_contract_role": (
            owner.semantic_contract_role or "aware_api.provider"
        ),
        "semantic_contract_name": (
            owner.semantic_contract_name or "aware.semantic_provider"
        ),
        "owner_manifest_relative_path": owner_manifest_relative_path,
        "owner_package_name": owner.package_name,
        "artifact_manifest_kind": leaf_manifest_kind,
        "artifact_package_name": leaf.package_name,
        "artifact_package_root": leaf_package_root,
        "package_output_key": artifact_output.output_key,
        "package_output_kind": artifact_output.output_kind,
    }
    return WorkspaceSemanticArtifactProduction(
        provider_key="aware_api",
        producer_key=f"aware_api.{artifact_output.output_key}",
        producer_kind="semantic_materialization.package_output",
        provider_payload=provider_payload,
        emission_payload={
            "owner_semantic_package_manifest": owner_manifest_relative_path,
            "ownership_role": "semantic_generated_artifact",
            "artifact_manifest_kind": leaf_manifest_kind,
            "artifact_package_root": leaf_package_root,
            "package_output_key": artifact_output.output_key,
        },
    )


def _python_product_package_root(
    *,
    package_root: str,
    targets: AwareApiTomlPythonTargetSpec | None,
    legacy_root_dir: str | None,
    package_dir: str | None,
    import_root: str,
) -> str:
    if _text(legacy_root_dir) is not None:
        return _join_repo_path(package_root, _text(legacy_root_dir) or "")
    language_root = "python" if targets is None or not targets.root_dir else targets.root_dir
    product_dir = _text(package_dir) or import_root
    return _join_repo_path(package_root, language_root, product_dir)


def _dart_product_package_root(
    *,
    package_root: str,
    targets: AwareApiTomlDartTargetSpec | None,
    package_name: str,
) -> str:
    if targets is not None and _text(targets.public_package.root_dir) is not None:
        return _join_repo_path(package_root, _text(targets.public_package.root_dir) or "")
    language_root = "dart" if targets is None or not targets.root_dir else targets.root_dir
    package_dir = (
        package_name
        if targets is None
        else (_text(targets.public_package.package_dir) or package_name)
    )
    return _join_repo_path(package_root, language_root, package_dir)


def _derive_python_import_root(*, spec: AwareApiTomlSpec) -> str:
    token = (spec.api.fqn_prefix or spec.api.package_name).strip()
    token = token.replace("-", "_").strip("_")
    return token or "aware_api_public_package"


def _derive_python_service_protocol_import_root(*, public_import_root: str) -> str:
    token = public_import_root
    if token.endswith("_api"):
        token = token[: -len("_api")]
    token = token.strip("_")
    return f"{token}_protocol" if token else "aware_api_protocol"


def _derive_dart_public_package_name(*, spec: AwareApiTomlSpec) -> str:
    token = (spec.api.fqn_prefix or spec.api.package_name).strip()
    token = token.replace("-", "_").strip("_")
    return token or "aware_api_public_package"


def _join_repo_path(*parts: str) -> str:
    normalized_parts = [
        part.strip().strip("/")
        for part in parts
        if part.strip().strip("/")
    ]
    return "/".join(normalized_parts) or "."


def _normalize_repo_path(value: str | None) -> str | None:
    if value is None:
        return None
    return _join_repo_path(value)


def _text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = ["resolve_workspace_semantic_artifact_leaf_ownership"]
