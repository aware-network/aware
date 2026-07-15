from __future__ import annotations

from aware_code.module_code_package_materialization_contract import (
    ModuleCodePackageMaterializationContract,
    ModuleCodePackageMaterializationDescriptor,
)


AWARE_GRAMMAR_CODE_PACKAGE_MATERIALIZATION_CONTRACT = (
    ModuleCodePackageMaterializationContract(
        provider_key="aware_grammar",
        package_materializations=(
            ModuleCodePackageMaterializationDescriptor(
                surface="runtime",
                language="python",
                manager="uv",
                distribution_name="{runtime_project_name}",
                import_root="{runtime_import_root}",
                package_root_relpath="modules/{module_id}/runtime",
                manifest_relpath="modules/{module_id}/runtime/pyproject.toml",
            ),
            ModuleCodePackageMaterializationDescriptor(
                surface="environment_service",
                language="python",
                manager="uv",
                distribution_name="{environment_service_project_name}",
                import_root="{environment_service_import_root}",
                package_root_relpath="modules/{module_id}/services/environment",
                manifest_relpath="modules/{module_id}/services/environment/pyproject.toml",
            ),
        ),
    )
)

AWARE_MODULE_CODE_PACKAGE_MATERIALIZATION_CONTRACT = (
    AWARE_GRAMMAR_CODE_PACKAGE_MATERIALIZATION_CONTRACT
)


__all__ = [
    "AWARE_GRAMMAR_CODE_PACKAGE_MATERIALIZATION_CONTRACT",
    "AWARE_MODULE_CODE_PACKAGE_MATERIALIZATION_CONTRACT",
]
