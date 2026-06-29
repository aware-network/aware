"""Strict loader for `aware.module.toml` -> AwareModuleSpec."""

from __future__ import annotations

from pathlib import Path
import re
from typing import cast

import tomllib

from aware_code.module_manifest.spec import (
    AwareModulePackageSpec,
    AwareModulePackageSemanticBindingSpec,
    AwareModulePackageSemanticContractBindingSpec,
    AwareModulePackageSemanticContractSpec,
    AwareModulePluginCapabilityPolicySpec,
    AwareModulePluginSpec,
    AwareModuleServiceSpec,
    AwareModuleRuntimeSpec,
    AwareModuleSpec,
)


class AwareModuleTomlError(ValueError):
    """Raised when `aware.module.toml` fails strict validation."""


_PACKAGE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_IMPORT_ROOT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_PYTHON_MODULE_RE = re.compile(r"^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$")
_MODULE_PROVIDER_KEY_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_CAPABILITY_NAME_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_PYTHON_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_PACKAGE_ID_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_PACKAGE_KIND_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_SEMANTIC_BINDING_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
_SERVICE_SURFACES: tuple[str, ...] = ("environment", "api", "node", "service")
_WORKSPACE_ACTIVATIONS: tuple[str, ...] = ("always", "owner")
_PACKAGE_VISIBILITIES: tuple[str, ...] = (
    "module",
    "public",
    "internal",
    "private",
)
_CODE_MODULE_PLUGIN_KIND = "code.module_plugin"


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareModuleTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def _as_table_list(value: object, *, ctx: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise AwareModuleTomlError(f"Expected {ctx} to be an array of tables")
    tables: list[dict[str, object]] = []
    items = cast(list[object], value)
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise AwareModuleTomlError(f"Expected {ctx}[{i}] to be a table/object")
        payload = cast(dict[object, object], item)
        tables.append({str(k): v for k, v in payload.items()})
    return tables


def load_aware_module_spec(*, toml_path: str | Path) -> AwareModuleSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareModuleTomlError(f"aware.module.toml not found: {p}")
    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover
        raise AwareModuleTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")

    _expect_keys(
        raw,
        required={"aware", "packages"},
        optional={"module", "runtime", "services", "plugins"},
        ctx="root",
    )
    aware_version = _expect_int(raw, "aware", ctx="root")
    if aware_version != 1:
        raise AwareModuleTomlError(
            f"Unsupported aware.module.toml version {aware_version}; expected 1"
        )

    module_tbl = raw.get("module", None)
    structure_root = "structure"
    runtime_root = "runtime"
    representation_root = "representation"
    stable_ids_ownership = "authored"
    stable_ids_parity_policy = "warn"
    stable_ids_resolution_policy = "class_strict"
    function_impl_ownership = "authored"
    function_impl_parity_policy = "off"
    if module_tbl is not None:
        module_tbl = _as_table(module_tbl, ctx="[module]")
        _expect_keys(
            module_tbl,
            required=set(),
            optional={
                "structure_root",
                "runtime_root",
                "representation_root",
                "stable_ids_ownership",
                "stable_ids_parity_policy",
                "stable_ids_resolution_policy",
                "function_impl_ownership",
                "function_impl_parity_policy",
            },
            ctx="[module]",
        )
        structure_root = (
            _expect_opt_str(module_tbl, "structure_root", ctx="[module]")
            or structure_root
        )
        runtime_root = (
            _expect_opt_str(module_tbl, "runtime_root", ctx="[module]") or runtime_root
        )
        representation_root = (
            _expect_opt_str(module_tbl, "representation_root", ctx="[module]")
            or representation_root
        )
        ownership_raw = _expect_opt_str(
            module_tbl, "stable_ids_ownership", ctx="[module]"
        )
        if ownership_raw is not None:
            stable_ids_ownership = ownership_raw.strip().lower()
            if stable_ids_ownership not in {"authored", "compiler"}:
                raise AwareModuleTomlError(
                    "[module].stable_ids_ownership must be one of: authored, compiler"
                )
        policy_raw = _expect_opt_str(
            module_tbl, "stable_ids_parity_policy", ctx="[module]"
        )
        if policy_raw is not None:
            stable_ids_parity_policy = policy_raw.strip().lower()
            if stable_ids_parity_policy not in {"off", "warn", "error"}:
                raise AwareModuleTomlError(
                    "[module].stable_ids_parity_policy must be one of: off, warn, error"
                )
        resolution_raw = _expect_opt_str(
            module_tbl, "stable_ids_resolution_policy", ctx="[module]"
        )
        if resolution_raw is not None:
            stable_ids_resolution_policy = resolution_raw.strip().lower()
            if stable_ids_resolution_policy != "class_strict":
                raise AwareModuleTomlError(
                    "[module].stable_ids_resolution_policy must be class_strict"
                )
        function_impl_ownership_raw = _expect_opt_str(
            module_tbl, "function_impl_ownership", ctx="[module]"
        )
        if function_impl_ownership_raw is not None:
            function_impl_ownership = function_impl_ownership_raw.strip().lower()
            if function_impl_ownership not in {"authored", "compiler"}:
                raise AwareModuleTomlError(
                    "[module].function_impl_ownership must be one of: authored, compiler"
                )
        function_impl_policy_raw = _expect_opt_str(
            module_tbl, "function_impl_parity_policy", ctx="[module]"
        )
        if function_impl_policy_raw is not None:
            function_impl_parity_policy = function_impl_policy_raw.strip().lower()
            if function_impl_parity_policy not in {"off", "warn", "error"}:
                raise AwareModuleTomlError(
                    "[module].function_impl_parity_policy must be one of: off, warn, error"
                )
        _validate_rel_path(structure_root, ctx="[module].structure_root")
        _validate_rel_path(runtime_root, ctx="[module].runtime_root")
        _validate_rel_path(representation_root, ctx="[module].representation_root")

    runtime_spec: AwareModuleRuntimeSpec | None = None
    runtime_tbl = raw.get("runtime", None)
    if runtime_tbl is not None:
        runtime_tbl = _as_table(runtime_tbl, ctx="[runtime]")
        _expect_keys(
            runtime_tbl,
            required=set(),
            optional={"handler_modules", "project_name", "import_root"},
            ctx="[runtime]",
        )
        handler_modules = (
            _expect_opt_str_list(runtime_tbl, "handler_modules", ctx="[runtime]") or []
        )
        handler_modules = [m.strip() for m in handler_modules if m.strip()]
        project_name = _expect_opt_str(runtime_tbl, "project_name", ctx="[runtime]")
        import_root = _expect_opt_str(runtime_tbl, "import_root", ctx="[runtime]")
        if project_name is not None:
            project_name = project_name.strip()
            if not _PACKAGE_NAME_RE.fullmatch(project_name):
                raise AwareModuleTomlError(
                    "[runtime].project_name must match ^[a-z0-9][a-z0-9_-]*$"
                )
        if import_root is not None:
            import_root = import_root.strip()
            if not _IMPORT_ROOT_RE.fullmatch(import_root):
                raise AwareModuleTomlError(
                    "[runtime].import_root must match ^[a-z_][a-z0-9_]*$"
                )
        runtime_spec = AwareModuleRuntimeSpec(
            handler_modules=tuple(handler_modules),
            project_name=project_name,
            import_root=import_root,
        )

    services_tbl = _as_table_list(raw.get("services", []), ctx="[[services]]")
    services: list[AwareModuleServiceSpec] = []
    seen_surfaces: set[str] = set()
    for i, service_tbl in enumerate(services_tbl):
        _expect_keys(
            service_tbl,
            required={"surface", "provider_modules"},
            optional={"required"},
            ctx=f"[[services]] (index={i})",
        )
        surface = (
            _expect_str(service_tbl, "surface", ctx=f"services[{i}]").strip().lower()
        )
        if surface not in _SERVICE_SURFACES:
            raise AwareModuleTomlError(
                f"services[{i}].surface must be one of: {', '.join(_SERVICE_SURFACES)}"
            )
        if surface in seen_surfaces:
            raise AwareModuleTomlError(
                f"Duplicate [[services]] entry for surface={surface!r}; declare one entry per surface"
            )
        seen_surfaces.add(surface)
        provider_modules = _expect_opt_str_list(
            service_tbl,
            "provider_modules",
            ctx=f"services[{i}]",
        )
        provider_tokens = [
            token.strip()
            for token in (provider_modules or [])
            if token and token.strip()
        ]
        if not provider_tokens:
            raise AwareModuleTomlError(
                f"services[{i}].provider_modules must include at least one module import"
            )
        deduped_provider_modules: list[str] = []
        seen_provider_modules: set[str] = set()
        for provider_module in provider_tokens:
            if not _PYTHON_MODULE_RE.fullmatch(provider_module):
                raise AwareModuleTomlError(
                    f"services[{i}].provider_modules entries must match "
                    "^([a-z_][a-z0-9_]*)(\\.[a-z_][a-z0-9_]*)*$: "
                    f"{provider_module!r}"
                )
            if provider_module in seen_provider_modules:
                continue
            seen_provider_modules.add(provider_module)
            deduped_provider_modules.append(provider_module)
        required = _expect_opt_bool(service_tbl, "required", ctx=f"services[{i}]")
        if required is None:
            required = True
        services.append(
            AwareModuleServiceSpec(
                surface=surface,
                provider_modules=tuple(deduped_provider_modules),
                required=required,
            )
        )

    plugins_tbl = _as_table_list(raw.get("plugins", []), ctx="[[plugins]]")
    plugins: list[AwareModulePluginSpec] = []
    for i, plugin_tbl in enumerate(plugins_tbl):
        _expect_keys(
            plugin_tbl,
            required={"kind"},
            optional={
                "name",
                "module",
                "provider_key",
                "capability_contract_module",
                "capability_execution_module",
                "semantic_contract_module",
                "code_package_materialization_contract_module",
                "capability_policy",
                "required",
            },
            ctx=f"[[plugins]] (index={i})",
        )
        kind = _expect_str(plugin_tbl, "kind", ctx=f"plugins[{i}]").strip()
        name = _expect_opt_str(plugin_tbl, "name", ctx=f"plugins[{i}]")
        module = _expect_opt_str(plugin_tbl, "module", ctx=f"plugins[{i}]")
        provider_key = _expect_opt_str(plugin_tbl, "provider_key", ctx=f"plugins[{i}]")
        capability_contract_module = _expect_opt_str(
            plugin_tbl,
            "capability_contract_module",
            ctx=f"plugins[{i}]",
        )
        capability_execution_module = _expect_opt_str(
            plugin_tbl,
            "capability_execution_module",
            ctx=f"plugins[{i}]",
        )
        semantic_contract_module = _expect_opt_str(
            plugin_tbl,
            "semantic_contract_module",
            ctx=f"plugins[{i}]",
        )
        code_package_materialization_contract_module = _expect_opt_str(
            plugin_tbl,
            "code_package_materialization_contract_module",
            ctx=f"plugins[{i}]",
        )
        capability_policy_tbl = _as_table_list(
            plugin_tbl.get("capability_policy"),
            ctx=f"plugins[{i}].capability_policy",
        )
        capability_policy: list[AwareModulePluginCapabilityPolicySpec] = []
        seen_policy_capabilities: set[str] = set()
        for policy_index, policy_tbl in enumerate(capability_policy_tbl):
            _expect_keys(
                policy_tbl,
                required={"capability"},
                optional={"workspace_activation", "workspace_fallback"},
                ctx=f"plugins[{i}].capability_policy[{policy_index}]",
            )
            capability = _expect_str(
                policy_tbl,
                "capability",
                ctx=f"plugins[{i}].capability_policy[{policy_index}]",
            ).strip()
            if not _CAPABILITY_NAME_RE.fullmatch(capability):
                raise AwareModuleTomlError(
                    f"plugins[{i}].capability_policy[{policy_index}].capability must match "
                    "^[a-z_][a-z0-9_]*$"
                )
            if capability in seen_policy_capabilities:
                raise AwareModuleTomlError(
                    f"plugins[{i}].capability_policy declares duplicate capability {capability!r}"
                )
            seen_policy_capabilities.add(capability)
            workspace_activation = (
                (
                    _expect_opt_str(
                        policy_tbl,
                        "workspace_activation",
                        ctx=f"plugins[{i}].capability_policy[{policy_index}]",
                    )
                    or "owner"
                )
                .strip()
                .lower()
            )
            if workspace_activation not in _WORKSPACE_ACTIVATIONS:
                raise AwareModuleTomlError(
                    f"plugins[{i}].capability_policy[{policy_index}].workspace_activation "
                    f"must be one of: {', '.join(_WORKSPACE_ACTIVATIONS)}"
                )
            workspace_fallback = _expect_opt_bool(
                policy_tbl,
                "workspace_fallback",
                ctx=f"plugins[{i}].capability_policy[{policy_index}]",
            )
            capability_policy.append(
                AwareModulePluginCapabilityPolicySpec(
                    capability=capability,
                    workspace_activation=workspace_activation,
                    workspace_fallback=bool(workspace_fallback),
                )
            )
        required = _expect_opt_bool(plugin_tbl, "required", ctx=f"plugins[{i}]")

        name = name.strip() if name is not None else None
        module = module.strip() if module is not None else None
        provider_key = provider_key.strip() if provider_key is not None else None
        capability_contract_module = (
            capability_contract_module.strip()
            if capability_contract_module is not None
            else None
        )
        capability_execution_module = (
            capability_execution_module.strip()
            if capability_execution_module is not None
            else None
        )
        semantic_contract_module = (
            semantic_contract_module.strip()
            if semantic_contract_module is not None
            else None
        )
        code_package_materialization_contract_module = (
            code_package_materialization_contract_module.strip()
            if code_package_materialization_contract_module is not None
            else None
        )
        if required is None:
            required = True

        if kind == "db.postgres.extension":
            if not name:
                raise AwareModuleTomlError(
                    f"plugins[{i}].name is required when kind='db.postgres.extension'"
                )
            if module:
                raise AwareModuleTomlError(
                    f"plugins[{i}].module is not allowed when kind='db.postgres.extension'"
                )
            if capability_contract_module:
                raise AwareModuleTomlError(
                    f"plugins[{i}].capability_contract_module is not allowed when kind='db.postgres.extension'"
                )
            if provider_key:
                raise AwareModuleTomlError(
                    f"plugins[{i}].provider_key is not allowed when kind='db.postgres.extension'"
                )
            if capability_execution_module:
                raise AwareModuleTomlError(
                    f"plugins[{i}].capability_execution_module is not allowed when kind='db.postgres.extension'"
                )
            if semantic_contract_module:
                raise AwareModuleTomlError(
                    f"plugins[{i}].semantic_contract_module is not allowed when kind='db.postgres.extension'"
                )
            if code_package_materialization_contract_module:
                raise AwareModuleTomlError(
                    "plugins["
                    f"{i}"
                    "].code_package_materialization_contract_module is not allowed "
                    "when kind='db.postgres.extension'"
                )
            if capability_policy:
                raise AwareModuleTomlError(
                    f"plugins[{i}].capability_policy is not allowed when kind='db.postgres.extension'"
                )
        elif kind == _CODE_MODULE_PLUGIN_KIND:
            if name:
                raise AwareModuleTomlError(
                    f"plugins[{i}].name is not allowed when kind='{_CODE_MODULE_PLUGIN_KIND}'"
                )
            if module and provider_key:
                raise AwareModuleTomlError(
                    f"plugins[{i}] cannot set both module and provider_key when kind='{_CODE_MODULE_PLUGIN_KIND}'"
                )
            if not module and not provider_key:
                raise AwareModuleTomlError(
                    f"plugins[{i}] must set either module or provider_key when kind='{_CODE_MODULE_PLUGIN_KIND}'"
                )
            if module and not _PYTHON_MODULE_RE.fullmatch(module):
                raise AwareModuleTomlError(
                    f"plugins[{i}].module must match "
                    "^([a-z_][a-z0-9_]*)(\\.[a-z_][a-z0-9_]*)*$ "
                    f"when kind='{_CODE_MODULE_PLUGIN_KIND}': {module!r}"
                )
            if provider_key is not None and not _MODULE_PROVIDER_KEY_RE.fullmatch(
                provider_key
            ):
                raise AwareModuleTomlError(
                    f"plugins[{i}].provider_key must match "
                    "^[a-z_][a-z0-9_]*$ "
                    f"when kind='{_CODE_MODULE_PLUGIN_KIND}': {provider_key!r}"
                )
            if (
                capability_contract_module is not None
                and not _PYTHON_MODULE_RE.fullmatch(capability_contract_module)
            ):
                raise AwareModuleTomlError(
                    f"plugins[{i}].capability_contract_module must match "
                    "^([a-z_][a-z0-9_]*)(\\.[a-z_][a-z0-9_]*)*$ "
                    f"when kind='{_CODE_MODULE_PLUGIN_KIND}': {capability_contract_module!r}"
                )
            if (
                capability_execution_module is not None
                and not _PYTHON_MODULE_RE.fullmatch(capability_execution_module)
            ):
                raise AwareModuleTomlError(
                    f"plugins[{i}].capability_execution_module must match "
                    "^([a-z_][a-z0-9_]*)(\\.[a-z_][a-z0-9_]*)*$ "
                    f"when kind='{_CODE_MODULE_PLUGIN_KIND}': {capability_execution_module!r}"
                )
            if (
                semantic_contract_module is not None
                and not _PYTHON_MODULE_RE.fullmatch(semantic_contract_module)
            ):
                raise AwareModuleTomlError(
                    f"plugins[{i}].semantic_contract_module must match "
                    "^([a-z_][a-z0-9_]*)(\\.[a-z_][a-z0-9_]*)*$ "
                    f"when kind='{_CODE_MODULE_PLUGIN_KIND}': {semantic_contract_module!r}"
                )
            if (
                code_package_materialization_contract_module is not None
                and not _PYTHON_MODULE_RE.fullmatch(
                    code_package_materialization_contract_module
                )
            ):
                raise AwareModuleTomlError(
                    f"plugins[{i}].code_package_materialization_contract_module must match "
                    "^([a-z_][a-z0-9_]*)(\\.[a-z_][a-z0-9_]*)*$ "
                    f"when kind='{_CODE_MODULE_PLUGIN_KIND}': {code_package_materialization_contract_module!r}"
                )
            if module and (
                capability_execution_module
                or code_package_materialization_contract_module
            ):
                raise AwareModuleTomlError(
                    f"plugins[{i}] cannot mix legacy module wrapper mode with "
                    f"capability_execution_module/code_package_materialization_contract_module/"
                    f"when kind='{_CODE_MODULE_PLUGIN_KIND}'"
                )
            if module and capability_policy:
                raise AwareModuleTomlError(
                    f"plugins[{i}] cannot declare capability_policy in legacy module wrapper mode "
                    f"when kind='{_CODE_MODULE_PLUGIN_KIND}'"
                )
            if provider_key is None and capability_policy:
                raise AwareModuleTomlError(
                    f"plugins[{i}] must set provider_key when capability_policy is declared "
                    f"for kind='{_CODE_MODULE_PLUGIN_KIND}'"
                )
        else:
            if not name and not module:
                raise AwareModuleTomlError(
                    f"plugins[{i}] must set at least one of name/module (kind={kind!r})"
                )

        if name is not None:
            _validate_rel_path(name, ctx=f"plugins[{i}].name")
        if module is not None:
            _validate_rel_path(module, ctx=f"plugins[{i}].module")
        if provider_key is not None:
            _validate_rel_path(provider_key, ctx=f"plugins[{i}].provider_key")
        if capability_contract_module is not None:
            _validate_rel_path(
                capability_contract_module,
                ctx=f"plugins[{i}].capability_contract_module",
            )
        if capability_execution_module is not None:
            _validate_rel_path(
                capability_execution_module,
                ctx=f"plugins[{i}].capability_execution_module",
            )
        if semantic_contract_module is not None:
            _validate_rel_path(
                semantic_contract_module,
                ctx=f"plugins[{i}].semantic_contract_module",
            )
        if code_package_materialization_contract_module is not None:
            _validate_rel_path(
                code_package_materialization_contract_module,
                ctx=f"plugins[{i}].code_package_materialization_contract_module",
            )
        plugins.append(
            AwareModulePluginSpec(
                kind=kind,
                name=name or None,
                module=module or None,
                provider_key=provider_key or None,
                capability_contract_module=capability_contract_module or None,
                capability_execution_module=capability_execution_module or None,
                semantic_contract_module=semantic_contract_module or None,
                code_package_materialization_contract_module=(
                    code_package_materialization_contract_module or None
                ),
                capability_policy=tuple(capability_policy),
                required=required,
            )
        )

    packages_tbl = _as_table_list(raw.get("packages", []), ctx="[[packages]]")
    packages: list[AwareModulePackageSpec] = []
    seen_package_ids: set[str] = set()
    for i, p_tbl in enumerate(packages_tbl):
        _expect_keys(
            p_tbl,
            required=set(),
            optional={
                "id",
                "kind",
                "manifest",
                "aware_toml_path",
                "visibility",
                "semantic_contract",
                "semantic_bindings",
                "mirrors_ontology",
            },
            ctx=f"[[packages]] (index={i})",
        )
        legacy_aware_toml_path = _expect_opt_str(
            p_tbl, "aware_toml_path", ctx=f"packages[{i}]"
        )
        package_id = _expect_opt_str(p_tbl, "id", ctx=f"packages[{i}]")
        package_kind = _expect_opt_str(p_tbl, "kind", ctx=f"packages[{i}]")
        manifest = _expect_opt_str(p_tbl, "manifest", ctx=f"packages[{i}]")
        visibility = (
            (_expect_opt_str(p_tbl, "visibility", ctx=f"packages[{i}]") or "module")
            .strip()
            .lower()
        )
        if visibility not in _PACKAGE_VISIBILITIES:
            raise AwareModuleTomlError(
                f"packages[{i}].visibility must be one of: {', '.join(_PACKAGE_VISIBILITIES)}"
            )

        if legacy_aware_toml_path is not None:
            if (
                package_id is not None
                or package_kind is not None
                or manifest is not None
            ):
                raise AwareModuleTomlError(
                    f"packages[{i}] cannot mix legacy aware_toml_path with id/kind/manifest"
                )
            manifest = legacy_aware_toml_path.strip()
            package_id = _legacy_package_id_for_manifest(manifest)
            package_kind = _legacy_package_kind_for_manifest(manifest)
        else:
            missing = [
                field
                for field, value in (
                    ("id", package_id),
                    ("kind", package_kind),
                    ("manifest", manifest),
                )
                if value is None
            ]
            if missing:
                raise AwareModuleTomlError(
                    f"packages[{i}] must set either aware_toml_path or all of id/kind/manifest; "
                    f"missing: {missing}"
                )
            if package_id is None or package_kind is None or manifest is None:
                raise AwareModuleTomlError(
                    f"packages[{i}] must set either aware_toml_path or all of id/kind/manifest"
                )
            package_id = package_id.strip()
            package_kind = package_kind.strip().lower()
            manifest = manifest.strip()

        assert package_id is not None
        assert package_kind is not None
        assert manifest is not None
        if not _PACKAGE_ID_RE.fullmatch(package_id):
            raise AwareModuleTomlError(
                f"packages[{i}].id must match ^[a-z_][a-z0-9_]*$"
            )
        if not _PACKAGE_KIND_RE.fullmatch(package_kind):
            raise AwareModuleTomlError(
                f"packages[{i}].kind must match ^[a-z_][a-z0-9_]*$"
            )
        if package_id in seen_package_ids:
            raise AwareModuleTomlError(
                f"packages[{i}] declares duplicate package id {package_id!r}"
            )
        seen_package_ids.add(package_id)
        _validate_rel_path(manifest, ctx=f"packages[{i}].manifest")
        semantic_contract = _parse_package_semantic_contract(
            p_tbl.get("semantic_contract"),
            ctx=f"packages[{i}].semantic_contract",
        )
        semantic_bindings = _parse_package_semantic_bindings(
            p_tbl.get("semantic_bindings"),
            ctx=f"packages[{i}].semantic_bindings",
        )
        if semantic_contract is not None and semantic_bindings:
            raise AwareModuleTomlError(
                f"packages[{i}] cannot mix semantic_contract with legacy semantic_bindings"
            )
        mirrors_ontology = (
            _expect_opt_bool(p_tbl, "mirrors_ontology", ctx=f"packages[{i}]") or False
        )
        packages.append(
            AwareModulePackageSpec(
                id=package_id,
                kind=package_kind,
                manifest=manifest,
                aware_toml_path=manifest,
                visibility=visibility,
                semantic_contract=semantic_contract,
                semantic_bindings=semantic_bindings,
                mirrors_ontology=mirrors_ontology,
            )
        )

    if not packages:
        raise AwareModuleTomlError(
            "aware.module.toml requires at least one [[packages]] entry"
        )
    _validate_package_semantic_contracts_have_registered_plugins(
        packages=packages,
        plugins=plugins,
    )

    return AwareModuleSpec(
        aware=aware_version,
        structure_root=structure_root,
        runtime_root=runtime_root,
        representation_root=representation_root,
        stable_ids_ownership=stable_ids_ownership,
        stable_ids_parity_policy=stable_ids_parity_policy,
        stable_ids_resolution_policy=stable_ids_resolution_policy,
        function_impl_ownership=function_impl_ownership,
        function_impl_parity_policy=function_impl_parity_policy,
        runtime=runtime_spec,
        services=tuple(services),
        plugins=tuple(plugins),
        packages=tuple(packages),
    )


def _legacy_package_id_for_manifest(manifest: str) -> str:
    path = Path(manifest)
    if path.name == "aware.toml" and path.parent.name:
        raw = path.parent.name
    else:
        raw = path.stem
    normalized = re.sub(r"[^a-z0-9_]+", "_", raw.strip().lower()).strip("_")
    if normalized and normalized[0].isdigit():
        normalized = f"package_{normalized}"
    return normalized or "package"


def _legacy_package_kind_for_manifest(manifest: str) -> str:
    path = Path(manifest)
    if path.name == "aware.toml" and path.parent.name:
        raw = path.parent.name
    else:
        raw = path.stem
    normalized = re.sub(r"[^a-z0-9_]+", "_", raw.strip().lower()).strip("_")
    if normalized and normalized[0].isdigit():
        normalized = f"package_{normalized}"
    return normalized or "package"


def _expect_keys(
    tbl: dict[str, object], *, required: set[str], optional: set[str], ctx: str
) -> None:
    allowed = required | optional
    extra = set(tbl.keys()) - allowed
    missing = required - set(tbl.keys())
    if extra:
        raise AwareModuleTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareModuleTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareModuleTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareModuleTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareModuleTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareModuleTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return val


def _expect_opt_str_list(
    root: dict[str, object], key: str, *, ctx: str
) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareModuleTomlError(f"Expected {ctx}.{key} to be a list[str] or null")
    out: list[str] = []
    items = cast(list[object], val)
    for i, item in enumerate(items):
        if not isinstance(item, str):
            raise AwareModuleTomlError(f"Expected {ctx}.{key}[{i}] to be a string")
        out.append(item)
    return out


def _normalize_capability_names(
    values: list[str] | None,
    *,
    ctx: str,
) -> tuple[str, ...] | None:
    if values is None:
        return None

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        value = raw_value.strip().lower()
        if not value:
            raise AwareModuleTomlError(f"{ctx} entries must be non-empty strings")
        if not _CAPABILITY_NAME_RE.fullmatch(value):
            raise AwareModuleTomlError(
                f"{ctx} entries must match ^[a-z_][a-z0-9_]*$: {raw_value!r}"
            )
        if value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _normalize_manifest_kinds(
    values: list[str] | None,
    *,
    ctx: str,
) -> tuple[str, ...] | None:
    if values is None:
        return None

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        value = raw_value.strip().lower()
        if not value:
            raise AwareModuleTomlError(f"{ctx} entries must be non-empty strings")
        if not _PACKAGE_KIND_RE.fullmatch(value):
            raise AwareModuleTomlError(
                f"{ctx} entries must match ^[a-z_][a-z0-9_]*$: {raw_value!r}"
            )
        if value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _parse_package_semantic_bindings(
    value: object,
    *,
    ctx: str,
) -> tuple[AwareModulePackageSemanticBindingSpec, ...]:
    binding_tables = _as_table_list(value, ctx=ctx)
    bindings: list[AwareModulePackageSemanticBindingSpec] = []
    seen_roles: set[str] = set()
    for i, binding_tbl in enumerate(binding_tables):
        binding_ctx = f"{ctx}[{i}]"
        _expect_keys(
            binding_tbl,
            required={"role", "contract"},
            optional={"binding_module", "capabilities", "callable"},
            ctx=binding_ctx,
        )
        role = _expect_str(binding_tbl, "role", ctx=binding_ctx).strip().lower()
        contract = _expect_str(binding_tbl, "contract", ctx=binding_ctx).strip().lower()
        if not _SEMANTIC_BINDING_KEY_RE.fullmatch(role):
            raise AwareModuleTomlError(
                f"{binding_ctx}.role must match ^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)*$"
            )
        if role in seen_roles:
            raise AwareModuleTomlError(
                f"{binding_ctx} declares duplicate semantic binding role {role!r}"
            )
        seen_roles.add(role)
        if not _SEMANTIC_BINDING_KEY_RE.fullmatch(contract):
            raise AwareModuleTomlError(
                f"{binding_ctx}.contract must match ^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)*$"
            )

        binding_module = _expect_opt_str(
            binding_tbl,
            "binding_module",
            ctx=binding_ctx,
        )
        if binding_module is not None:
            binding_module = binding_module.strip() or None
        if binding_module is not None and not _PYTHON_MODULE_RE.fullmatch(
            binding_module
        ):
            raise AwareModuleTomlError(
                f"{binding_ctx}.binding_module must match "
                f"^[a-z_][a-z0-9_]*(\\.[a-z_][a-z0-9_]*)*$"
            )

        capabilities = _normalize_capability_names(
            _expect_opt_str_list(binding_tbl, "capabilities", ctx=binding_ctx),
            ctx=f"{binding_ctx}.capabilities",
        )
        callable_name = _expect_opt_str(binding_tbl, "callable", ctx=binding_ctx)
        if callable_name is not None:
            callable_name = callable_name.strip() or None
        if callable_name is not None and not _PYTHON_IDENTIFIER_RE.fullmatch(
            callable_name
        ):
            raise AwareModuleTomlError(
                f"{binding_ctx}.callable must match ^[a-z_][a-z0-9_]*$"
            )
        bindings.append(
            AwareModulePackageSemanticBindingSpec(
                role=role,
                contract=contract,
                binding_module=binding_module,
                capabilities=capabilities or (),
                callable_name=callable_name,
            )
        )
    return tuple(bindings)


def _parse_package_semantic_contract(
    value: object,
    *,
    ctx: str,
) -> AwareModulePackageSemanticContractSpec | None:
    if value is None:
        return None
    contract_tbl = _as_table(value, ctx=ctx)
    _expect_keys(
        contract_tbl,
        required={"role", "contract", "provider_key", "module"},
        optional={
            "bindings",
            "owns_manifest_kinds",
            "capabilities",
        },
        ctx=ctx,
    )
    role = _expect_str(contract_tbl, "role", ctx=ctx).strip().lower()
    contract = _expect_str(contract_tbl, "contract", ctx=ctx).strip().lower()
    provider_key = _expect_str(contract_tbl, "provider_key", ctx=ctx).strip()
    module = _expect_str(contract_tbl, "module", ctx=ctx).strip()
    if not _SEMANTIC_BINDING_KEY_RE.fullmatch(role):
        raise AwareModuleTomlError(
            f"{ctx}.role must match ^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)*$"
        )
    if not _SEMANTIC_BINDING_KEY_RE.fullmatch(contract):
        raise AwareModuleTomlError(
            f"{ctx}.contract must match ^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)*$"
        )
    if not _MODULE_PROVIDER_KEY_RE.fullmatch(provider_key):
        raise AwareModuleTomlError(f"{ctx}.provider_key must match ^[a-z_][a-z0-9_]*$")
    if not _PYTHON_MODULE_RE.fullmatch(module):
        raise AwareModuleTomlError(
            f"{ctx}.module must match ^[a-z_][a-z0-9_]*(\\.[a-z_][a-z0-9_]*)*$"
        )
    owns_manifest_kinds = _normalize_manifest_kinds(
        _expect_opt_str_list(contract_tbl, "owns_manifest_kinds", ctx=ctx),
        ctx=f"{ctx}.owns_manifest_kinds",
    )
    capabilities = _normalize_capability_names(
        _expect_opt_str_list(contract_tbl, "capabilities", ctx=ctx),
        ctx=f"{ctx}.capabilities",
    )
    if contract == "aware.semantic_provider":
        if not owns_manifest_kinds:
            raise AwareModuleTomlError(
                f"{ctx}.owns_manifest_kinds is required when contract='aware.semantic_provider'"
            )
        if not capabilities:
            raise AwareModuleTomlError(
                f"{ctx}.capabilities is required when contract='aware.semantic_provider'"
            )

    binding_tables = _as_table_list(
        contract_tbl.get("bindings"),
        ctx=f"{ctx}.bindings",
    )
    bindings: list[AwareModulePackageSemanticContractBindingSpec] = []
    seen_capabilities: set[str] = set()
    for i, binding_tbl in enumerate(binding_tables):
        binding_ctx = f"{ctx}.bindings[{i}]"
        _expect_keys(
            binding_tbl,
            required={"capability", "module", "callable"},
            optional=set(),
            ctx=binding_ctx,
        )
        capability = (
            _expect_str(binding_tbl, "capability", ctx=binding_ctx).strip().lower()
        )
        binding_module = _expect_str(binding_tbl, "module", ctx=binding_ctx).strip()
        callable_name = _expect_str(binding_tbl, "callable", ctx=binding_ctx).strip()
        if not _CAPABILITY_NAME_RE.fullmatch(capability):
            raise AwareModuleTomlError(
                f"{binding_ctx}.capability must match ^[a-z_][a-z0-9_]*$"
            )
        if capability in seen_capabilities:
            raise AwareModuleTomlError(
                f"{binding_ctx} declares duplicate capability {capability!r}"
            )
        seen_capabilities.add(capability)
        if not _PYTHON_MODULE_RE.fullmatch(binding_module):
            raise AwareModuleTomlError(
                f"{binding_ctx}.module must match "
                "^[a-z_][a-z0-9_]*(\\.[a-z_][a-z0-9_]*)*$"
            )
        if not _PYTHON_IDENTIFIER_RE.fullmatch(callable_name):
            raise AwareModuleTomlError(
                f"{binding_ctx}.callable must match ^[a-z_][a-z0-9_]*$"
            )
        bindings.append(
            AwareModulePackageSemanticContractBindingSpec(
                capability=capability,
                module=binding_module,
                callable=callable_name,
            )
        )

    return AwareModulePackageSemanticContractSpec(
        role=role,
        contract=contract,
        provider_key=provider_key,
        module=module,
        owns_manifest_kinds=owns_manifest_kinds or (),
        capabilities=capabilities or (),
        bindings=tuple(bindings),
    )


def _validate_package_semantic_contracts_have_registered_plugins(
    *,
    packages: list[AwareModulePackageSpec],
    plugins: list[AwareModulePluginSpec],
) -> None:
    plugins_by_provider = {
        plugin.provider_key: plugin
        for plugin in plugins
        if plugin.kind == _CODE_MODULE_PLUGIN_KIND and plugin.provider_key is not None
    }
    for package in packages:
        semantic_contract = package.semantic_contract
        if semantic_contract is None:
            continue
        plugin = plugins_by_provider.get(semantic_contract.provider_key)
        if plugin is None:
            raise AwareModuleTomlError(
                f"packages[{package.id}].semantic_contract.provider_key "
                f"{semantic_contract.provider_key!r} must reference a "
                "registered code.module_plugin"
            )
        registered_module = plugin.semantic_contract_module
        if (
            registered_module is not None
            and registered_module != semantic_contract.module
        ):
            raise AwareModuleTomlError(
                f"packages[{package.id}].semantic_contract.module "
                f"{semantic_contract.module!r} must match registered plugin "
                f"semantic_contract_module {registered_module!r}"
            )


def _validate_rel_path(value: str, *, ctx: str) -> None:
    p = Path(value)
    if p.is_absolute():
        raise AwareModuleTomlError(
            f"{ctx} must be repo-relative (not absolute): {value!r}"
        )
    if ".." in p.parts:
        raise AwareModuleTomlError(f"{ctx} must not contain '..': {value!r}")


__all__ = [
    "AwareModuleTomlError",
    "load_aware_module_spec",
]
