"""`aware_orm.runtime` public API.

Generated Python packages embed `_aware/*` resources and install through
`bootstrap_orm_package` + `install_package_runtime_artifacts`. Environment
bundle install is retired; executable runtime truth comes from ontology-owned
package artifacts, not Structure-composed manifests.
"""

from __future__ import annotations

from typing import Any

# IMPORTANT:
# This package must be safe to import in *all* contexts (including during generated package import).
# Therefore: do not import bundle rail modules eagerly here, because they can transitively import
# kernel structure/environment objects which may import the generated ontology package and trigger
# early binding side effects.


__all__ = [
    # Errors
    "install_bindings_from_bundle",
    "install_bindings_from_payload",
    "BindingInstallResult",
    "BundleInstallError",
    "PackageInstallError",
    "SQLRuntimeMetadata",
    # Package rail (canonical)
    "bootstrap_orm_package",
    "install_package_runtime_artifacts",
    "ORMClassConfigReference",
    "ORMClassResolutionIndex",
    "resolve_orm_class",
    "install_sql_metadata_from_bundle",
    "install_sql_metadata_from_bindings_payload",
    "SQLMetadataInstallResult",
    # Bundle rail optional artifacts
    "install_relationship_strategies",
    "install_relationship_metadata_from_payload",
    "RelationshipStrategiesInstallResult",
    "get_relationship_metadata",
]


def __getattr__(name: str) -> Any:  # pragma: no cover
    """
    Lazily resolve runtime public API symbols.

    This avoids import-time side effects while keeping a convenient top-level API.
    """
    if name in {"BundleInstallError", "PackageInstallError"}:
        from .errors import BundleInstallError, PackageInstallError

        return {
            "BundleInstallError": BundleInstallError,
            "PackageInstallError": PackageInstallError,
        }[name]

    if name in {"SQLRuntimeMetadata"}:
        from .sql_metadata import SQLRuntimeMetadata

        return SQLRuntimeMetadata

    if name in {"bootstrap_orm_package"}:
        from .package_bootstrap import bootstrap_orm_package

        return bootstrap_orm_package

    if name in {"install_package_runtime_artifacts"}:
        from .package_install import install_package_runtime_artifacts

        return install_package_runtime_artifacts

    if name in {
        "ORMClassConfigReference",
        "ORMClassResolutionIndex",
        "resolve_orm_class",
    }:
        from .class_resolver import (
            ORMClassConfigReference,
            ORMClassResolutionIndex,
            resolve_orm_class,
        )

        return {
            "ORMClassConfigReference": ORMClassConfigReference,
            "ORMClassResolutionIndex": ORMClassResolutionIndex,
            "resolve_orm_class": resolve_orm_class,
        }[name]

    if name in {
        "install_bindings_from_bundle",
        "install_bindings_from_payload",
        "BindingInstallResult",
    }:
        from .bundle_binding import (
            install_bindings_from_bundle,
            install_bindings_from_payload,
            BindingInstallResult,
        )

        return {
            "install_bindings_from_bundle": install_bindings_from_bundle,
            "install_bindings_from_payload": install_bindings_from_payload,
            "BindingInstallResult": BindingInstallResult,
        }[name]

    if name in {
        "install_sql_metadata_from_bundle",
        "install_sql_metadata_from_bindings_payload",
        "SQLMetadataInstallResult",
    }:
        from .bundle_sql_metadata import (
            install_sql_metadata_from_bundle,
            install_sql_metadata_from_bindings_payload,
            SQLMetadataInstallResult,
        )

        return {
            "install_sql_metadata_from_bundle": install_sql_metadata_from_bundle,
            "install_sql_metadata_from_bindings_payload": install_sql_metadata_from_bindings_payload,
            "SQLMetadataInstallResult": SQLMetadataInstallResult,
        }[name]

    if name in {
        "install_relationship_strategies",
        "install_relationship_metadata_from_payload",
        "RelationshipStrategiesInstallResult",
        "get_relationship_metadata",
    }:
        from .relationship_strategies import (
            install_relationship_strategies,
            install_relationship_metadata_from_payload,
            RelationshipStrategiesInstallResult,
            get_relationship_metadata,
        )

        return {
            "install_relationship_strategies": install_relationship_strategies,
            "install_relationship_metadata_from_payload": install_relationship_metadata_from_payload,
            "RelationshipStrategiesInstallResult": RelationshipStrategiesInstallResult,
            "get_relationship_metadata": get_relationship_metadata,
        }[name]

    raise AttributeError(name)
