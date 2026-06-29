from __future__ import annotations

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.package_strategy import ObjectConfigGraphPackageSpec

from aware_meta.materialization.schemas import (
    API_PUBLIC_PACKAGE_KIND,
    API_SERVICE_PROTOCOL_KIND,
    MaterializationConfig,
)

from .models import (
    ApiPublicPackageLoweringHandoff,
    ApiPublicPackageRenderJob,
    ApiPublicPackageRenderTarget,
    ApiServiceProtocolLoweringHandoff,
    ApiServiceProtocolRenderJob,
    ApiServiceProtocolRenderTarget,
)

_API_PUBLIC_PACKAGE_RENDER_JOB_SCHEMA_VERSION = 1
_API_SERVICE_PROTOCOL_RENDER_JOB_SCHEMA_VERSION = 1


def build_api_public_package_render_job(
    *,
    handoff: ApiPublicPackageLoweringHandoff,
    target: ApiPublicPackageRenderTarget,
    dependency_import_roots: tuple[str, ...] = (),
) -> ApiPublicPackageRenderJob:
    root_client_class_name = _build_root_client_class_name(
        import_root=target.import_root,
        package_name=target.package_name,
    )
    dependencies: list[str]
    metadata: dict[str, object] = {
        "aware_package_kind": handoff.backend_handoff.aware_package_kind,
    }
    if target.target_language == CodeLanguage.python:
        dependencies = [
            *dependency_import_roots,
            "aware-api-client",
            "aware-types",
            "aware-utils",
            "pydantic>=2.8.0,<3.0.0",
        ]
        metadata["root_export_refs"] = [f"client.{root_client_class_name}"]
        if dependency_import_roots:
            metadata["dependency_import_roots"] = list(dependency_import_roots)
            metadata["uses_external_api_dto_types"] = True
    elif target.target_language == CodeLanguage.dart:
        dependencies = []
        if target.repo_root is not None:
            metadata["repo_root"] = target.repo_root.resolve().as_posix()
        if target.dependency_repo_roots:
            metadata["dependency_repo_roots"] = [
                root.resolve().as_posix() for root in target.dependency_repo_roots
            ]
        if target.path_dependencies:
            metadata["path_dependencies"] = {
                name.replace("-", "_"): _path_dependency_metadata_value(
                    path=path,
                    repo_root=target.repo_root,
                )
                for name, path in target.path_dependencies
            }
    else:
        raise ValueError(
            "Unsupported public API package render job target language: "
            + f"{target.target_language.value}"
        )
    package_spec = ObjectConfigGraphPackageSpec(
        name=target.import_root or target.package_name,
        package_name=target.package_name,
        package_root=target.package_root,
        import_root=target.import_root,
        version=target.version,
        description=target.description,
        dependencies=dependencies,
        metadata=metadata,
    )

    materialization_config = MaterializationConfig(
        name=_build_materialization_name(target=target),
        source_aware_toml_path=target.source_aware_toml_path,
        source_package_name=handoff.package_name,
        target_language=target.target_language,
        renderer_kind=target.renderer_kind,
        target_output_dir=target.target_output_dir,
        manifest_path=target.manifest_path,
        import_root=target.import_root,
        packages=[package_spec],
        source=handoff.backend_handoff.materialization_source,
    )
    if handoff.backend_handoff.aware_package_kind != API_PUBLIC_PACKAGE_KIND:
        raise ValueError(
            "Invalid public API package render job input: expected aware_package_kind='api_public_package' "
            + f"but got {handoff.backend_handoff.aware_package_kind!r}"
        )

    return ApiPublicPackageRenderJob(
        schema_version=_API_PUBLIC_PACKAGE_RENDER_JOB_SCHEMA_VERSION,
        package_name=handoff.package_name,
        fqn_prefix=handoff.fqn_prefix,
        backend_handoff=handoff.backend_handoff,
        target=target,
        runtime_artifacts=handoff.runtime_artifacts,
        materialization_config=materialization_config,
    )


def build_api_service_protocol_render_job(
    *,
    handoff: ApiServiceProtocolLoweringHandoff,
    target: ApiServiceProtocolRenderTarget,
    dependency_import_roots: tuple[str, ...] = (),
    include_public_package_dependency: bool = True,
) -> ApiServiceProtocolRenderJob:
    public_package_import_root = _build_public_package_import_root(
        fqn_prefix=handoff.fqn_prefix,
        package_name=handoff.package_name,
    )
    root_protocol_name = _build_root_service_protocol_name(
        import_root=target.import_root,
        package_name=target.package_name,
    )
    dependency_roots = [
        *([public_package_import_root] if include_public_package_dependency else []),
        *[
            import_root
            for import_root in dependency_import_roots
            if import_root != public_package_import_root
        ],
    ]
    package_spec = ObjectConfigGraphPackageSpec(
        name=target.import_root or target.package_name,
        package_name=target.package_name,
        package_root=target.package_root,
        import_root=target.import_root,
        version=target.version,
        description=target.description,
        dependencies=[
            *dependency_roots,
            "aware-utils",
            "pydantic>=2.8.0,<3.0.0",
        ],
        metadata={
            "aware_package_kind": handoff.backend_handoff.aware_package_kind,
            "api_public_package_import_root": public_package_import_root,
            "dependency_import_roots": dependency_roots,
            "root_export_refs": [f"protocols.{root_protocol_name}"],
        },
    )

    materialization_config = MaterializationConfig(
        name=_build_service_protocol_materialization_name(target=target),
        source_aware_toml_path=target.source_aware_toml_path,
        source_package_name=handoff.package_name,
        target_language=target.target_language,
        renderer_kind=target.renderer_kind,
        target_output_dir=target.target_output_dir,
        manifest_path=target.manifest_path,
        import_root=target.import_root,
        packages=[package_spec],
        source=handoff.backend_handoff.materialization_source,
    )
    if handoff.backend_handoff.aware_package_kind != API_SERVICE_PROTOCOL_KIND:
        raise ValueError(
            "Invalid service protocol package render job input: expected aware_package_kind='api_service_protocol' "
            + f"but got {handoff.backend_handoff.aware_package_kind!r}"
        )

    return ApiServiceProtocolRenderJob(
        schema_version=_API_SERVICE_PROTOCOL_RENDER_JOB_SCHEMA_VERSION,
        package_name=handoff.package_name,
        fqn_prefix=handoff.fqn_prefix,
        backend_handoff=handoff.backend_handoff,
        target=target,
        runtime_artifacts=handoff.runtime_artifacts,
        materialization_config=materialization_config,
    )


def _build_materialization_name(*, target: ApiPublicPackageRenderTarget) -> str:
    return f"api-public-package-{target.target_language.value}"


def _build_root_client_class_name(*, import_root: str | None, package_name: str) -> str:
    token = import_root or package_name
    parts = [part for part in token.replace("-", "_").split("_") if part]
    base_name = (
        "".join(part[:1].upper() + part[1:] for part in parts)
        or "AwareApiPublicPackage"
    )
    return f"{base_name}Client"


def _build_service_protocol_materialization_name(
    *, target: ApiServiceProtocolRenderTarget
) -> str:
    return f"api-service-protocol-{target.target_language.value}"


def _build_root_service_protocol_name(
    *, import_root: str | None, package_name: str
) -> str:
    token = (import_root or package_name).replace("-", "_")
    for suffix in ("_service_protocol", "_protocol"):
        if token.endswith(suffix):
            token = token[: -len(suffix)]
            break
    parts = [part for part in token.split("_") if part]
    base_name = "".join(part[:1].upper() + part[1:] for part in parts) or "AwareApi"
    return f"{base_name}ServiceProtocol"


def _build_public_package_import_root(*, fqn_prefix: str, package_name: str) -> str:
    token = (fqn_prefix or package_name).strip()
    token = token.replace("-", "_")
    return token or "aware_api_public_package"


def _path_dependency_metadata_value(*, path, repo_root) -> str:
    resolved_path = path.resolve()
    if repo_root is not None:
        resolved_repo_root = repo_root.resolve()
        try:
            return resolved_path.relative_to(resolved_repo_root).as_posix()
        except ValueError:
            pass
    return resolved_path.as_posix()


__all__ = [
    "build_api_public_package_render_job",
    "build_api_service_protocol_render_job",
]
