from __future__ import annotations

from dataclasses import dataclass, field

AWARE_MODULE_CODE_PACKAGE_MATERIALIZATION_CONTRACT_EXPORT_NAME = (
    "AWARE_MODULE_CODE_PACKAGE_MATERIALIZATION_CONTRACT"
)


@dataclass(frozen=True, slots=True)
class ModuleCodePackageMaterializationDescriptor:
    """Module-owned code-package materialization truth for create/bootstrap consumers."""

    surface: str
    language: str
    manager: str
    distribution_name: str
    import_root: str
    package_root_relpath: str
    manifest_relpath: str
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ModuleCodePackageMaterializationContract:
    """Shared module-owned code-package materialization contract."""

    provider_key: str
    package_materializations: tuple[ModuleCodePackageMaterializationDescriptor, ...] = ()

    def package_materializations_for(
        self,
        *,
        surface: str,
    ) -> tuple[ModuleCodePackageMaterializationDescriptor, ...]:
        return tuple(
            item
            for item in self.package_materializations
            if item.surface == surface
        )


__all__ = [
    "AWARE_MODULE_CODE_PACKAGE_MATERIALIZATION_CONTRACT_EXPORT_NAME",
    "ModuleCodePackageMaterializationContract",
    "ModuleCodePackageMaterializationDescriptor",
]
