from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID

import tomllib

from aware_service_runtime.manifest.spec import (
    AwareServiceCompilationMode,
    AwareServiceDependencyKind,
    AwareServiceHostActivationMode,
    AwareServiceImplementationLanguage,
    AwareServiceImplementationRole,
    AwareServiceRuntimeRequirementKind,
    AwareServiceRuntimeToolchainKind,
    AwareServiceTomlApiProviderSetSpec,
    AwareServiceTomlBuildSpec,
    AwareServiceTomlDependencySpec,
    AwareServiceTomlHostContractSpec,
    AwareServiceTomlHostSpec,
    AwareServiceTomlImplementationPackageSpec,
    AwareServiceTomlImplementationSpec,
    AwareServiceTomlObjectConfigGraphPackageSpec,
    AwareServiceTomlOntologyPackageSpec,
    AwareServiceTomlPackageSpec,
    AwareServiceTomlRuntimeRequirementSpec,
    AwareServiceTomlRuntimeSpec,
    AwareServiceTomlSpec,
    AwareServiceTomlRuntimeToolchainSpec,
    AwareServiceTomlRouteAuthoritySelectorSpec,
)


_ALLOWED_SERVICE_SURFACES = frozenset(("service", "node_host"))


class AwareServiceTomlError(ValueError):
    """Raised when `aware.service.toml` fails strict validation."""


_RUNTIME_REQUIREMENT_VALUE_KEYS = frozenset(
    {"value", "secret", "secret_value", "default", "example_value", "plaintext"}
)


def load_aware_service_toml_spec_from_text(
    *,
    toml_text: str,
    toml_path: str | Path | None = None,
) -> AwareServiceTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.service.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareServiceTomlError(
            f"Failed to parse TOML at {path_label}: {exc}"
        ) from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_service_toml_raw(raw, path_label=path_label)


def load_aware_service_toml_spec(*, toml_path: str | Path) -> AwareServiceTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareServiceTomlError(f"aware.service.toml not found: {p}")
    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:
        raise AwareServiceTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")
    return _parse_aware_service_toml_raw(raw, path_label=str(p))


def _parse_aware_service_toml_raw(
    raw: dict[str, object], *, path_label: str
) -> AwareServiceTomlSpec:
    _expect_keys(
        raw,
        required={"aware_service", "service", "build"},
        optional={
            "api_provider_sets",
            "dependencies",
            "host",
            "implementation",
            "object_config_graph_packages",
            "ontology_packages",
            "runtime",
        },
        ctx="root",
    )
    spec_version = _expect_int(raw, "aware_service", ctx="root")
    if spec_version != 1:
        raise AwareServiceTomlError(
            f"Unsupported aware.service.toml version {spec_version}; expected 1"
        )

    service_tbl = _expect_table(raw, "service", ctx="root")
    _expect_keys(
        service_tbl,
        required={"package_name", "fqn_prefix"},
        optional={"version_number", "title", "description"},
        ctx="[service]",
    )
    package_name = _expect_str(service_tbl, "package_name", ctx="[service]")
    fqn_prefix = _expect_str(service_tbl, "fqn_prefix", ctx="[service]")
    version_number = (
        _expect_opt_int(service_tbl, "version_number", ctx="[service]") or 1
    )
    title = _expect_opt_str(service_tbl, "title", ctx="[service]")
    description = _expect_opt_str(service_tbl, "description", ctx="[service]")

    _validate_package_name(package_name, ctx="[service].package_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[service].fqn_prefix")

    build_tbl = _expect_table(raw, "build", ctx="root")
    _expect_keys(
        build_tbl,
        required=set(),
        optional={
            "sources_dir",
            "include_paths",
            "exclude_paths",
            "force_fresh_scan",
            "compilation_mode",
        },
        ctx="[build]",
    )
    sources_dir = _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "services"
    include_paths = _expect_opt_str_list(build_tbl, "include_paths", ctx="[build]") or [
        "**/*.aware"
    ]
    exclude_paths = (
        _expect_opt_str_list(build_tbl, "exclude_paths", ctx="[build]") or []
    )
    force_fresh_scan = _expect_opt_bool(build_tbl, "force_fresh_scan", ctx="[build]")
    if force_fresh_scan is None:
        force_fresh_scan = True
    compilation_mode = _expect_opt_compilation_mode(
        build_tbl, "compilation_mode", ctx="[build]"
    )
    if compilation_mode is None:
        compilation_mode = AwareServiceCompilationMode.raw_xor

    _validate_rel_path(sources_dir, ctx="[build].sources_dir")
    for i, path in enumerate(include_paths):
        _validate_rel_path(path, ctx=f"[build].include_paths[{i}]")
    for i, path in enumerate(exclude_paths):
        _validate_rel_path(path, ctx=f"[build].exclude_paths[{i}]")

    host_tbl = _expect_opt_table(raw, "host", ctx="root")
    host_spec = AwareServiceTomlHostSpec()
    if host_tbl is not None:
        _expect_keys(
            host_tbl,
            required=set(),
            optional={
                "service_surface",
                "activation_mode",
                "materialize_on_start",
                "contract",
            },
            ctx="[host]",
        )
        service_surface = (
            _expect_opt_str(host_tbl, "service_surface", ctx="[host]") or "service"
        ).strip() or "service"
        activation_mode = _expect_opt_host_activation_mode(
            host_tbl, "activation_mode", ctx="[host]"
        )
        if activation_mode is None:
            activation_mode = (
                AwareServiceHostActivationMode.materialize_and_load_committed
            )
        materialize_on_start = _expect_opt_bool(
            host_tbl, "materialize_on_start", ctx="[host]"
        )
        if materialize_on_start is None:
            materialize_on_start = True
        contract_tbl = _expect_opt_table(host_tbl, "contract", ctx="[host]")
        host_contract = AwareServiceTomlHostContractSpec()
        if contract_tbl is not None:
            _expect_keys(
                contract_tbl,
                required=set(),
                optional={"entrypoint"},
                ctx="[host.contract]",
            )
            host_contract = AwareServiceTomlHostContractSpec(
                entrypoint=_expect_opt_str(
                    contract_tbl,
                    "entrypoint",
                    ctx="[host.contract]",
                )
            )

        _validate_service_surface(service_surface, ctx="[host].service_surface")
        host_spec = AwareServiceTomlHostSpec(
            service_surface=service_surface,
            activation_mode=activation_mode,
            materialize_on_start=materialize_on_start,
            contract=host_contract,
        )

    runtime_tbl = _expect_opt_table(raw, "runtime", ctx="root")
    runtime_spec = AwareServiceTomlRuntimeSpec()
    if runtime_tbl is not None:
        _expect_keys(
            runtime_tbl,
            required=set(),
            optional={
                "secrets_dir_env",
                "canonical_secrets_dir",
                "requirements",
                "toolchains",
            },
            ctx="[runtime]",
        )
        runtime_spec = AwareServiceTomlRuntimeSpec(
            secrets_dir_env=_expect_opt_str(
                runtime_tbl, "secrets_dir_env", ctx="[runtime]"
            ),
            canonical_secrets_dir=_expect_opt_str(
                runtime_tbl, "canonical_secrets_dir", ctx="[runtime]"
            ),
            requirements=_parse_runtime_requirements(
                runtime_tbl.get("requirements", []),
                path_label=path_label,
            ),
            toolchains=_parse_runtime_toolchains(
                runtime_tbl.get("toolchains", []),
                path_label=path_label,
            ),
        )

    implementation_tbl = _expect_opt_table(raw, "implementation", ctx="root")
    implementation_spec = AwareServiceTomlImplementationSpec()
    if implementation_tbl is not None:
        _expect_keys(
            implementation_tbl,
            required=set(),
            optional={"packages"},
            ctx="[implementation]",
        )
        implementation_spec = AwareServiceTomlImplementationSpec(
            packages=_parse_implementation_packages(
                implementation_tbl.get("packages", []),
                path_label=path_label,
            )
        )

    api_provider_sets = _parse_api_provider_sets(
        raw.get("api_provider_sets", []),
        path_label=path_label,
    )

    deps_tbl = _as_table_list(raw.get("dependencies", []), ctx="[[dependencies]]")
    dependencies: list[AwareServiceTomlDependencySpec] = []
    seen_deps: set[str] = set()
    for i, dep_tbl in enumerate(deps_tbl):
        _expect_keys(
            dep_tbl,
            required={"package_name"},
            optional={
                "version_number",
                "kind",
                "expected_hash_sha256",
                "route_authority_selector",
            },
            ctx=f"[[dependencies]] (index={i})",
        )
        dep_package_name = _expect_str(
            dep_tbl, "package_name", ctx=f"dependencies[{i}]"
        )
        dep_version_number = _expect_opt_int(
            dep_tbl, "version_number", ctx=f"dependencies[{i}]"
        )
        dep_kind = _expect_opt_dependency_kind(
            dep_tbl, "kind", ctx=f"dependencies[{i}]"
        )
        if dep_kind is None:
            dep_kind = AwareServiceDependencyKind.package
        dep_expected_hash = _expect_opt_str(
            dep_tbl, "expected_hash_sha256", ctx=f"dependencies[{i}]"
        )

        _validate_package_name(dep_package_name, ctx=f"dependencies[{i}].package_name")
        if dep_expected_hash is not None:
            dep_expected_hash = dep_expected_hash.strip().lower()
            _validate_sha256(
                dep_expected_hash, ctx=f"dependencies[{i}].expected_hash_sha256"
            )
        if (
            dep_kind == AwareServiceDependencyKind.api_service_protocol
            and dep_expected_hash is not None
        ):
            raise AwareServiceTomlError(
                "dependencies[{i}].expected_hash_sha256 is derived lock truth and is not allowed for api_service_protocol dependencies".replace(
                    "{i}", str(i)
                )
            )
        route_authority_selector = _parse_route_authority_selector(
            dep_tbl.get("route_authority_selector"),
            ctx=f"dependencies[{i}].route_authority_selector",
        )
        if (
            route_authority_selector is not None
            and dep_kind != AwareServiceDependencyKind.api_invocation
        ):
            raise AwareServiceTomlError(
                "dependencies[{i}].route_authority_selector is only supported "
                "for api_invocation dependencies".replace("{i}", str(i))
            )
        if dep_package_name in seen_deps:
            raise AwareServiceTomlError(
                f"Duplicate dependency package_name={dep_package_name!r} at dependencies[{i}] in {path_label}"
            )
        seen_deps.add(dep_package_name)
        dependencies.append(
            AwareServiceTomlDependencySpec(
                package_name=dep_package_name,
                version_number=dep_version_number,
                kind=dep_kind,
                expected_hash_sha256=dep_expected_hash,
                route_authority_selector=route_authority_selector,
            )
        )

    object_config_graph_packages = _parse_object_config_graph_packages(
        raw.get("object_config_graph_packages", []),
        path_label=path_label,
    )
    ontology_packages = _parse_ontology_packages(
        raw.get("ontology_packages", []),
        path_label=path_label,
    )

    return AwareServiceTomlSpec(
        aware_service=spec_version,
        service=AwareServiceTomlPackageSpec(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            version_number=version_number,
            title=title,
            description=description,
        ),
        build=AwareServiceTomlBuildSpec(
            sources_dir=sources_dir,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            force_fresh_scan=force_fresh_scan,
            compilation_mode=compilation_mode,
        ),
        host=host_spec,
        dependencies=dependencies,
        object_config_graph_packages=object_config_graph_packages,
        ontology_packages=ontology_packages,
        implementation=implementation_spec,
        api_provider_sets=api_provider_sets,
        runtime=runtime_spec,
    )


def _parse_object_config_graph_packages(
    value: object,
    *,
    path_label: str,
) -> list[AwareServiceTomlObjectConfigGraphPackageSpec]:
    package_tbls = _as_table_list(
        value,
        ctx="[[object_config_graph_packages]]",
    )
    packages: list[AwareServiceTomlObjectConfigGraphPackageSpec] = []
    seen_manifests: set[str] = set()
    for i, package_tbl in enumerate(package_tbls):
        ctx = f"[[object_config_graph_packages]] (index={i})"
        _expect_keys(
            package_tbl,
            required={"manifest"},
            optional={
                "role",
                "description",
                "expected_hash_sha256",
                "object_instance_graph_commit_id",
            },
            ctx=ctx,
        )
        entry_ctx = f"object_config_graph_packages[{i}]"
        manifest = _expect_str(package_tbl, "manifest", ctx=entry_ctx)
        role = _expect_opt_str(package_tbl, "role", ctx=entry_ctx) or "local_state"
        description = _expect_opt_str(package_tbl, "description", ctx=entry_ctx)
        expected_hash = _expect_opt_str(
            package_tbl,
            "expected_hash_sha256",
            ctx=entry_ctx,
        )
        oig_commit_id = _expect_opt_str(
            package_tbl,
            "object_instance_graph_commit_id",
            ctx=entry_ctx,
        )

        _validate_rel_path(manifest, ctx=f"{entry_ctx}.manifest")
        if Path(manifest).name != "aware.toml":
            raise AwareServiceTomlError(
                "object_config_graph_packages entries must point at an "
                f"aware.toml manifest; got {manifest!r}"
            )
        if manifest in seen_manifests:
            raise AwareServiceTomlError(
                "Duplicate object_config_graph_packages manifest="
                f"{manifest!r} at index={i} in {path_label}"
            )
        seen_manifests.add(manifest)

        if expected_hash is not None:
            expected_hash = expected_hash.strip().lower()
            _validate_sha256(
                expected_hash,
                ctx=f"{entry_ctx}.expected_hash_sha256",
            )
        oig_commit_id = _clean_optional_uuid_str(
            oig_commit_id,
            ctx=f"{entry_ctx}.object_instance_graph_commit_id",
        )
        packages.append(
            AwareServiceTomlObjectConfigGraphPackageSpec(
                manifest=manifest,
                role=role,
                description=description,
                expected_hash_sha256=expected_hash,
                object_instance_graph_commit_id=oig_commit_id,
            )
        )
    return packages


def _parse_ontology_packages(
    value: object,
    *,
    path_label: str,
) -> list[AwareServiceTomlOntologyPackageSpec]:
    package_tbls = _as_table_list(value, ctx="[[ontology_packages]]")
    packages: list[AwareServiceTomlOntologyPackageSpec] = []
    seen_keys: set[tuple[str, str]] = set()
    for i, package_tbl in enumerate(package_tbls):
        ctx = f"[[ontology_packages]] (index={i})"
        _expect_keys(
            package_tbl,
            required={"package_name", "fqn_prefix"},
            optional={
                "role",
                "requirement_mode",
                "description",
                "expected_hash_sha256",
                "object_instance_graph_commit_id",
            },
            ctx=ctx,
        )
        entry_ctx = f"ontology_packages[{i}]"
        package_name = _expect_str(package_tbl, "package_name", ctx=entry_ctx)
        fqn_prefix = _expect_str(package_tbl, "fqn_prefix", ctx=entry_ctx)
        role = _expect_opt_str(package_tbl, "role", ctx=entry_ctx) or "replica"
        requirement_mode = (
            _expect_opt_str(package_tbl, "requirement_mode", ctx=entry_ctx)
            or "required"
        )
        description = _expect_opt_str(package_tbl, "description", ctx=entry_ctx)
        expected_hash = _expect_opt_str(
            package_tbl,
            "expected_hash_sha256",
            ctx=entry_ctx,
        )
        oig_commit_id = _expect_opt_str(
            package_tbl,
            "object_instance_graph_commit_id",
            ctx=entry_ctx,
        )

        _validate_package_name(package_name, ctx=f"{entry_ctx}.package_name")
        _validate_fqn_prefix(fqn_prefix, ctx=f"{entry_ctx}.fqn_prefix")
        role = role.strip()
        if role != "replica":
            raise AwareServiceTomlError(
                f"{entry_ctx}.role only supports 'replica' in this contract; got {role!r}"
            )
        requirement_mode = requirement_mode.strip()
        if requirement_mode != "required":
            raise AwareServiceTomlError(
                f"{entry_ctx}.requirement_mode only supports 'required' in this contract; "
                f"got {requirement_mode!r}"
            )
        if expected_hash is not None:
            expected_hash = expected_hash.strip().lower()
            _validate_sha256(
                expected_hash,
                ctx=f"{entry_ctx}.expected_hash_sha256",
            )
        oig_commit_id = _clean_optional_uuid_str(
            oig_commit_id,
            ctx=f"{entry_ctx}.object_instance_graph_commit_id",
        )
        seen_key = (package_name.strip().casefold(), fqn_prefix.strip())
        if seen_key in seen_keys:
            raise AwareServiceTomlError(
                "Duplicate ontology_packages package_name/fqn_prefix="
                f"{package_name!r}/{fqn_prefix!r} at index={i} in {path_label}"
            )
        seen_keys.add(seen_key)
        packages.append(
            AwareServiceTomlOntologyPackageSpec(
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                role=role,
                requirement_mode=requirement_mode,
                description=description,
                expected_hash_sha256=expected_hash,
                object_instance_graph_commit_id=oig_commit_id,
            )
        )
    return packages


def _parse_api_provider_sets(
    value: object,
    *,
    path_label: str,
) -> list[AwareServiceTomlApiProviderSetSpec]:
    provider_set_tbls = _as_table_list(value, ctx="[[api_provider_sets]]")
    provider_sets: list[AwareServiceTomlApiProviderSetSpec] = []
    seen_keys: set[str] = set()
    for i, provider_set_tbl in enumerate(provider_set_tbls):
        ctx = f"[[api_provider_sets]] (index={i})"
        _expect_keys(
            provider_set_tbl,
            required={"key"},
            optional={"title", "description", "membership_key"},
            ctx=ctx,
        )
        key = _expect_str(provider_set_tbl, "key", ctx=f"api_provider_sets[{i}]")
        title = _expect_opt_str(
            provider_set_tbl,
            "title",
            ctx=f"api_provider_sets[{i}]",
        )
        description = _expect_opt_str(
            provider_set_tbl,
            "description",
            ctx=f"api_provider_sets[{i}]",
        )
        membership_key = _expect_opt_str(
            provider_set_tbl,
            "membership_key",
            ctx=f"api_provider_sets[{i}]",
        )
        _validate_provider_set_key(key, ctx=f"api_provider_sets[{i}].key")
        if membership_key is not None:
            _validate_provider_set_key(
                membership_key,
                ctx=f"api_provider_sets[{i}].membership_key",
            )
        normalized_key = key.strip()
        if normalized_key in seen_keys:
            raise AwareServiceTomlError(
                f"Duplicate api_provider_sets key={normalized_key!r} in {path_label}"
            )
        seen_keys.add(normalized_key)
        provider_sets.append(
            AwareServiceTomlApiProviderSetSpec(
                key=normalized_key,
                title=(title.strip() or None) if title is not None else None,
                description=(
                    description.strip() or None if description is not None else None
                ),
                membership_key=(
                    membership_key.strip() or None
                    if membership_key is not None
                    else None
                ),
            )
        )
    return provider_sets


def _parse_route_authority_selector(
    value: object,
    *,
    ctx: str,
) -> AwareServiceTomlRouteAuthoritySelectorSpec | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise AwareServiceTomlError(f"Expected {ctx} to be an inline table")
    payload = {
        str(key): item for key, item in cast(dict[object, object], value).items()
    }
    _expect_keys(
        payload,
        required=set(),
        optional={
            "provider_set_id",
            "workspace_revision_id",
            "workspace_deployment_revision_id",
            "workspace_deployment_channel",
            "workspace_deployment_artifact_key",
        },
        ctx=ctx,
    )
    selector = AwareServiceTomlRouteAuthoritySelectorSpec(
        provider_set_id=_clean_optional_selector_str(
            _expect_opt_str(payload, "provider_set_id", ctx=ctx),
            ctx=f"{ctx}.provider_set_id",
        ),
        workspace_revision_id=_clean_optional_uuid_str(
            _expect_opt_str(payload, "workspace_revision_id", ctx=ctx),
            ctx=f"{ctx}.workspace_revision_id",
        ),
        workspace_deployment_revision_id=_clean_optional_selector_str(
            _expect_opt_str(payload, "workspace_deployment_revision_id", ctx=ctx),
            ctx=f"{ctx}.workspace_deployment_revision_id",
        ),
        workspace_deployment_channel=_clean_optional_selector_str(
            _expect_opt_str(payload, "workspace_deployment_channel", ctx=ctx),
            ctx=f"{ctx}.workspace_deployment_channel",
        ),
        workspace_deployment_artifact_key=_clean_optional_selector_str(
            _expect_opt_str(payload, "workspace_deployment_artifact_key", ctx=ctx),
            ctx=f"{ctx}.workspace_deployment_artifact_key",
        ),
    )
    if selector.is_empty:
        raise AwareServiceTomlError(f"{ctx} must select at least one authority field")
    return selector


def _clean_optional_selector_str(value: str | None, *, ctx: str) -> str | None:
    if value is None:
        return None
    token = value.strip()
    if not token:
        raise AwareServiceTomlError(f"{ctx} must be non-empty when present")
    return token


def _clean_optional_uuid_str(value: str | None, *, ctx: str) -> str | None:
    token = _clean_optional_selector_str(value, ctx=ctx)
    if token is None:
        return None
    try:
        return str(UUID(token))
    except ValueError as exc:
        raise AwareServiceTomlError(f"{ctx} must be a valid UUID") from exc


def _parse_implementation_packages(
    value: object,
    *,
    path_label: str,
) -> list[AwareServiceTomlImplementationPackageSpec]:
    package_tbls = _as_table_list(value, ctx="[[implementation.packages]]")
    packages: list[AwareServiceTomlImplementationPackageSpec] = []
    seen: set[tuple[AwareServiceImplementationLanguage, str, str]] = set()
    for i, package_tbl in enumerate(package_tbls):
        ctx = f"[[implementation.packages]] (index={i})"
        _expect_keys(
            package_tbl,
            required={"language", "package_name", "import_root", "manifest_path"},
            optional={
                "package_root",
                "entrypoint",
                "role",
                "include_paths",
                "exclude_paths",
            },
            ctx=ctx,
        )
        language = _expect_opt_implementation_language(
            package_tbl,
            "language",
            ctx=f"implementation.packages[{i}]",
        )
        if language is None:
            raise AwareServiceTomlError(
                f"Expected implementation.packages[{i}].language to be non-empty"
            )
        package_name = _expect_str(
            package_tbl,
            "package_name",
            ctx=f"implementation.packages[{i}]",
        )
        import_root = _expect_str(
            package_tbl,
            "import_root",
            ctx=f"implementation.packages[{i}]",
        )
        manifest_path = _expect_str(
            package_tbl,
            "manifest_path",
            ctx=f"implementation.packages[{i}]",
        )
        package_root = (
            _expect_opt_str(
                package_tbl,
                "package_root",
                ctx=f"implementation.packages[{i}]",
            )
            or "."
        )
        entrypoint = _expect_opt_str(
            package_tbl,
            "entrypoint",
            ctx=f"implementation.packages[{i}]",
        )
        role = _expect_opt_implementation_role(
            package_tbl,
            "role",
            ctx=f"implementation.packages[{i}]",
        )
        if role is None:
            role = AwareServiceImplementationRole.service_bindings
        include_paths = (
            _expect_opt_str_list(
                package_tbl,
                "include_paths",
                ctx=f"implementation.packages[{i}]",
            )
            or []
        )
        exclude_paths = (
            _expect_opt_str_list(
                package_tbl,
                "exclude_paths",
                ctx=f"implementation.packages[{i}]",
            )
            or []
        )

        _validate_package_name(
            package_name,
            ctx=f"implementation.packages[{i}].package_name",
        )
        _validate_fqn_prefix(
            import_root,
            ctx=f"implementation.packages[{i}].import_root",
        )
        _validate_rel_path(
            package_root,
            ctx=f"implementation.packages[{i}].package_root",
        )
        _validate_rel_path(
            manifest_path,
            ctx=f"implementation.packages[{i}].manifest_path",
        )
        if entrypoint is not None:
            _validate_entrypoint(
                entrypoint,
                ctx=f"implementation.packages[{i}].entrypoint",
            )
        for path_index, path in enumerate(include_paths):
            _validate_rel_path(
                path,
                ctx=f"implementation.packages[{i}].include_paths[{path_index}]",
            )
        for path_index, path in enumerate(exclude_paths):
            _validate_rel_path(
                path,
                ctx=f"implementation.packages[{i}].exclude_paths[{path_index}]",
            )

        dedupe_key = (language, package_name, role.value)
        if dedupe_key in seen:
            raise AwareServiceTomlError(
                "Duplicate implementation package declaration in "
                f"{path_label}: language={language.value!r} package_name={package_name!r} "
                f"role={role.value!r}"
            )
        seen.add(dedupe_key)
        packages.append(
            AwareServiceTomlImplementationPackageSpec(
                package_name=package_name,
                language=language,
                import_root=import_root,
                manifest_path=manifest_path,
                package_root=package_root,
                entrypoint=entrypoint,
                role=role,
                include_paths=include_paths,
                exclude_paths=exclude_paths,
            )
        )
    return packages


def _parse_runtime_requirements(
    value: object,
    *,
    path_label: str,
) -> list[AwareServiceTomlRuntimeRequirementSpec]:
    req_tbls = _as_table_list(value, ctx="[[runtime.requirements]]")
    requirements: list[AwareServiceTomlRuntimeRequirementSpec] = []
    seen_names: set[str] = set()
    for i, req_tbl in enumerate(req_tbls):
        leaked_keys = sorted(
            key for key in req_tbl if key in _RUNTIME_REQUIREMENT_VALUE_KEYS
        )
        if leaked_keys:
            raise AwareServiceTomlError(
                "Runtime requirements declare names only, not values: "
                f"index={i} keys={leaked_keys} path={path_label}"
            )
        _expect_keys(
            req_tbl,
            required={"name", "kind"},
            optional={
                "required",
                "sensitive",
                "runtime_env",
                "resolver",
                "description",
                "allowed_values",
            },
            ctx=f"[[runtime.requirements]] (index={i})",
        )
        name = _expect_str(req_tbl, "name", ctx=f"runtime.requirements[{i}]")
        kind = _expect_opt_runtime_requirement_kind(
            req_tbl,
            "kind",
            ctx=f"runtime.requirements[{i}]",
        )
        if kind is None:
            raise AwareServiceTomlError(
                f"Expected runtime.requirements[{i}].kind to be non-empty"
            )
        required = _expect_opt_bool(
            req_tbl, "required", ctx=f"runtime.requirements[{i}]"
        )
        sensitive = _expect_opt_bool(
            req_tbl, "sensitive", ctx=f"runtime.requirements[{i}]"
        )
        if name in seen_names:
            raise AwareServiceTomlError(
                f"Duplicate runtime requirement name={name!r} in {path_label}"
            )
        seen_names.add(name)
        requirements.append(
            AwareServiceTomlRuntimeRequirementSpec(
                name=name,
                kind=kind,
                required=True if required is None else required,
                sensitive=(
                    (kind == AwareServiceRuntimeRequirementKind.secret)
                    if sensitive is None
                    else sensitive
                ),
                runtime_env=(
                    _expect_opt_str(
                        req_tbl, "runtime_env", ctx=f"runtime.requirements[{i}]"
                    )
                    or name
                ),
                resolver=_expect_opt_str(
                    req_tbl, "resolver", ctx=f"runtime.requirements[{i}]"
                ),
                description=_expect_opt_str(
                    req_tbl, "description", ctx=f"runtime.requirements[{i}]"
                ),
                allowed_values=_expect_opt_str_list(
                    req_tbl, "allowed_values", ctx=f"runtime.requirements[{i}]"
                )
                or [],
            )
        )
    return requirements


def _parse_runtime_toolchains(
    value: object,
    *,
    path_label: str,
) -> list[AwareServiceTomlRuntimeToolchainSpec]:
    toolchain_tbls = _as_table_list(value, ctx="[[runtime.toolchains]]")
    toolchains: list[AwareServiceTomlRuntimeToolchainSpec] = []
    seen_names: set[str] = set()
    for i, toolchain_tbl in enumerate(toolchain_tbls):
        leaked_keys = sorted(
            key for key in toolchain_tbl if key in _RUNTIME_REQUIREMENT_VALUE_KEYS
        )
        if leaked_keys:
            raise AwareServiceTomlError(
                "Runtime toolchains declare metadata only, not values: "
                f"index={i} keys={leaked_keys} path={path_label}"
            )
        _expect_keys(
            toolchain_tbl,
            required={"name", "kind"},
            optional={
                "required",
                "package",
                "version",
                "channel",
                "executable",
                "runtime_env",
                "description",
                "verify_commands",
                "features",
            },
            ctx=f"[[runtime.toolchains]] (index={i})",
        )
        name = _expect_str(toolchain_tbl, "name", ctx=f"runtime.toolchains[{i}]")
        kind = _expect_opt_runtime_toolchain_kind(
            toolchain_tbl,
            "kind",
            ctx=f"runtime.toolchains[{i}]",
        )
        if kind is None:
            raise AwareServiceTomlError(
                f"Expected runtime.toolchains[{i}].kind to be non-empty"
            )
        required = _expect_opt_bool(
            toolchain_tbl, "required", ctx=f"runtime.toolchains[{i}]"
        )
        if name in seen_names:
            raise AwareServiceTomlError(
                f"Duplicate runtime toolchain name={name!r} in {path_label}"
            )
        seen_names.add(name)
        toolchains.append(
            AwareServiceTomlRuntimeToolchainSpec(
                name=name,
                kind=kind,
                required=True if required is None else required,
                package=_expect_opt_str(
                    toolchain_tbl, "package", ctx=f"runtime.toolchains[{i}]"
                ),
                version=_expect_opt_str(
                    toolchain_tbl, "version", ctx=f"runtime.toolchains[{i}]"
                ),
                channel=_expect_opt_str(
                    toolchain_tbl, "channel", ctx=f"runtime.toolchains[{i}]"
                ),
                executable=_expect_opt_str(
                    toolchain_tbl, "executable", ctx=f"runtime.toolchains[{i}]"
                ),
                runtime_env=_expect_opt_str(
                    toolchain_tbl, "runtime_env", ctx=f"runtime.toolchains[{i}]"
                ),
                description=_expect_opt_str(
                    toolchain_tbl, "description", ctx=f"runtime.toolchains[{i}]"
                ),
                verify_commands=_expect_opt_str_list(
                    toolchain_tbl, "verify_commands", ctx=f"runtime.toolchains[{i}]"
                )
                or [],
                features=_expect_opt_str_list(
                    toolchain_tbl, "features", ctx=f"runtime.toolchains[{i}]"
                )
                or [],
            )
        )
    return toolchains


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareServiceTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def _as_table_list(value: object, *, ctx: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise AwareServiceTomlError(f"Expected {ctx} to be an array of tables")
    tables: list[dict[str, object]] = []
    items = cast(list[object], value)
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise AwareServiceTomlError(f"Expected {ctx}[{i}] to be a table/object")
        payload = cast(dict[object, object], item)
        tables.append({str(k): v for k, v in payload.items()})
    return tables


def _expect_keys(
    table: dict[str, object], *, required: set[str], optional: set[str], ctx: str
) -> None:
    allowed = required | optional
    extra = set(table.keys()) - allowed
    missing = required - set(table.keys())
    if extra:
        raise AwareServiceTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareServiceTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareServiceTomlError(
            f"Expected {ctx}.{key} to be a table; got {type(val)}"
        )
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_opt_table(
    root: dict[str, object], key: str, *, ctx: str
) -> dict[str, object] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, dict):
        raise AwareServiceTomlError(
            f"Expected {ctx}.{key} to be a table or null; got {type(val)}"
        )
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareServiceTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareServiceTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareServiceTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: dict[str, object], key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareServiceTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareServiceTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return val


def _expect_opt_str_list(
    root: dict[str, object], key: str, *, ctx: str
) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareServiceTomlError(f"Expected {ctx}.{key} to be a list[str] or null")
    out: list[str] = []
    items = cast(list[object], val)
    for i, item in enumerate(items):
        if not isinstance(item, str):
            raise AwareServiceTomlError(f"Expected {ctx}.{key}[{i}] to be a string")
        out.append(item)
    return out


def _expect_opt_compilation_mode(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> AwareServiceCompilationMode | None:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is None:
        return None
    try:
        return AwareServiceCompilationMode(value)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in AwareServiceCompilationMode)
        raise AwareServiceTomlError(
            f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}"
        ) from exc


def _expect_opt_dependency_kind(
    root: dict[str, object], key: str, *, ctx: str
) -> AwareServiceDependencyKind | None:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is None:
        return None
    try:
        return AwareServiceDependencyKind(value)
    except ValueError as exc:
        allowed = ", ".join(kind.value for kind in AwareServiceDependencyKind)
        raise AwareServiceTomlError(
            f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}"
        ) from exc


def _expect_opt_host_activation_mode(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> AwareServiceHostActivationMode | None:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is None:
        return None
    try:
        return AwareServiceHostActivationMode(value)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in AwareServiceHostActivationMode)
        raise AwareServiceTomlError(
            f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}"
        ) from exc


def _expect_opt_implementation_language(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> AwareServiceImplementationLanguage | None:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is None:
        return None
    try:
        return AwareServiceImplementationLanguage(value)
    except ValueError as exc:
        allowed = ", ".join(
            language.value for language in AwareServiceImplementationLanguage
        )
        raise AwareServiceTomlError(
            f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}"
        ) from exc


def _expect_opt_implementation_role(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> AwareServiceImplementationRole | None:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is None:
        return None
    try:
        return AwareServiceImplementationRole(value)
    except ValueError as exc:
        allowed = ", ".join(role.value for role in AwareServiceImplementationRole)
        raise AwareServiceTomlError(
            f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}"
        ) from exc


def _expect_opt_runtime_requirement_kind(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> AwareServiceRuntimeRequirementKind | None:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is None:
        return None
    try:
        return AwareServiceRuntimeRequirementKind(value)
    except ValueError as exc:
        allowed = ", ".join(kind.value for kind in AwareServiceRuntimeRequirementKind)
        raise AwareServiceTomlError(
            f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}"
        ) from exc


def _expect_opt_runtime_toolchain_kind(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> AwareServiceRuntimeToolchainKind | None:
    value = _expect_opt_str(root, key, ctx=ctx)
    if value is None:
        return None
    try:
        return AwareServiceRuntimeToolchainKind(value)
    except ValueError as exc:
        allowed = ", ".join(kind.value for kind in AwareServiceRuntimeToolchainKind)
        raise AwareServiceTomlError(
            f"Expected {ctx}.{key} to be one of [{allowed}]; got {value!r}"
        ) from exc


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    if "." in value:
        raise AwareServiceTomlError(
            f"{ctx} must not contain '.' (single-segment namespace); got {value!r}"
        )
    if any(ch.isspace() for ch in value):
        raise AwareServiceTomlError(f"{ctx} must not contain whitespace; got {value!r}")
    if "-" in value:
        raise AwareServiceTomlError(
            f"{ctx} must not contain '-' (use package_name for hyphens); got {value!r}"
        )


def _validate_package_name(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareServiceTomlError(f"{ctx} must not contain whitespace; got {value!r}")


def _validate_rel_path(value: str, *, ctx: str) -> None:
    p = Path(value)
    if p.is_absolute():
        raise AwareServiceTomlError(
            f"{ctx} must be repo-relative (not absolute): {value!r}"
        )
    if ".." in p.parts:
        raise AwareServiceTomlError(f"{ctx} must not contain '..': {value!r}")


def _validate_service_surface(value: str, *, ctx: str) -> None:
    if value not in _ALLOWED_SERVICE_SURFACES:
        allowed = ", ".join(
            repr(surface) for surface in sorted(_ALLOWED_SERVICE_SURFACES)
        )
        raise AwareServiceTomlError(f"{ctx} must be one of {allowed}; got {value!r}")


def _validate_provider_set_key(value: str, *, ctx: str) -> None:
    token = value.strip()
    if not token:
        raise AwareServiceTomlError(f"{ctx} must be non-empty")
    if any(ch.isspace() for ch in token):
        raise AwareServiceTomlError(f"{ctx} must not contain whitespace; got {value!r}")
    if any(ch in token for ch in "/\\"):
        raise AwareServiceTomlError(
            f"{ctx} must not contain path separators; got {value!r}"
        )


def _validate_entrypoint(value: str, *, ctx: str) -> None:
    token = value.strip()
    if not token:
        raise AwareServiceTomlError(f"{ctx} must be non-empty")
    if ":" not in token:
        raise AwareServiceTomlError(
            f"{ctx} must use 'module:function' format; got {value!r}"
        )
    module_name, function_name = token.split(":", 1)
    module_segments = module_name.split(".")
    if not module_segments or any(not segment.strip() for segment in module_segments):
        raise AwareServiceTomlError(
            f"{ctx} module segment must be non-empty; got {value!r}"
        )
    for index, segment in enumerate(module_segments):
        _validate_fqn_prefix(segment, ctx=f"{ctx}.module[{index}]")
    if not function_name.strip() or any(ch.isspace() for ch in function_name):
        raise AwareServiceTomlError(
            f"{ctx} function segment must be non-empty and contain no whitespace; got {value!r}"
        )


def _validate_sha256(value: str, *, ctx: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise AwareServiceTomlError(
            f"{ctx} must be a lowercase 64-character sha256 hex string; got {value!r}"
        )


__all__ = [
    "AwareServiceTomlError",
    "load_aware_service_toml_spec",
    "load_aware_service_toml_spec_from_text",
]
