from aware_meta_ontology.graph.config.object_config_graph_package import (
    ObjectConfigGraphPackage,
)
from aware_meta_ontology.graph.config.object_config_graph_package_build import (
    ObjectConfigGraphPackageBuild,
)
from aware_meta_ontology.graph.config.object_config_graph_package_dependency import (
    ObjectConfigGraphPackageDependency,
)
from aware_history_ontology.version.version import Version

from aware_meta.graph.config.package.constants import (
    package_build_uuid,
    package_dependency_uuid,
    package_uuid,
    package_version_uuid,
)
from aware_meta.manifest.spec import AwareTomlSpec


class AwareTomlBuildError(RuntimeError):
    """Raised when building ORM package objects from specs fails."""


def build_packages_from_specs(
    *,
    specs_by_package_name: dict[str, AwareTomlSpec],
) -> tuple[
    dict[str, ObjectConfigGraphPackage],
    dict[str, ObjectConfigGraphPackageBuild],
    dict[str, Version],
]:
    """
    Build deterministic ORM package objects for a set of already-discovered specs.

    This function:
    - creates *all* packages first (identity-map), with deterministic UUIDs
    - creates builds with deterministic UUIDs
    - creates dependency edges (package -> package) by linking to the target package object

    No stubs are created; target packages must exist in `specs_by_package_name`.
    """
    # 1) Create all packages (identity map) up-front.
    packages: dict[str, ObjectConfigGraphPackage] = {}
    for pkg_name, spec in specs_by_package_name.items():
        if pkg_name != spec.package.package_name:
            raise AwareTomlBuildError(
                f"Spec map key mismatch: key={pkg_name!r} but spec.package.package_name={spec.package.package_name!r}"
            )
        pkg_id = package_uuid(package_name=spec.package.package_name)
        packages[pkg_name] = ObjectConfigGraphPackage(
            id=pkg_id,
            package_name=spec.package.package_name,
            fqn_prefix=spec.package.fqn_prefix,
            title=spec.package.title,
            description=spec.package.description,
            object_config_graph=None,
            object_config_graph_id=None,
            dependencies=[],
        )

    # 2) Create builds.
    builds: dict[str, ObjectConfigGraphPackageBuild] = {}
    for pkg_name, spec in specs_by_package_name.items():
        build_id = package_build_uuid(
            package_name=spec.package.package_name,
            environment_slug=spec.build.environment_slug,
        )
        pkg = packages[pkg_name]
        builds[pkg_name] = ObjectConfigGraphPackageBuild(
            id=build_id,
            object_config_graph_package=pkg,
            object_config_graph_package_id=pkg.id,
            environment_slug=spec.build.environment_slug,
            sources_dir=spec.build.sources_dir,
            include_paths=spec.build.include_paths,
        )

    # 3) Create dependency edges.
    # Also mint deterministic Version objects (even if head_commit is not set yet).
    versions: dict[str, Version] = {}
    for pkg_name, spec in specs_by_package_name.items():
        ver_id = package_version_uuid(
            package_name=spec.package.package_name,
            version_number=spec.package.version_number,
        )
        versions[pkg_name] = Version(
            id=ver_id,
            version_number=spec.package.version_number,
            head_commit=None,
            head_commit_id=None,
        )

    for pkg_name, spec in specs_by_package_name.items():
        src_pkg = packages[pkg_name]
        deps: list[ObjectConfigGraphPackageDependency] = []
        for dep in spec.dependencies:
            tgt_pkg = packages.get(dep.package_name)
            if tgt_pkg is None:
                raise AwareTomlBuildError(
                    f"Dependency target package not found in workspace: {pkg_name!r} depends on {dep.package_name!r}"
                )
            dep_id = package_dependency_uuid(
                source_package_name=src_pkg.package_name,
                target_package_name=tgt_pkg.package_name,
            )
            target_version_id = None
            if dep.version_number is not None:
                target_version_id = package_version_uuid(
                    package_name=tgt_pkg.package_name,
                    version_number=int(dep.version_number),
                )
            deps.append(
                ObjectConfigGraphPackageDependency(
                    id=dep_id,
                    object_config_graph_package=src_pkg,
                    object_config_graph_package_id=src_pkg.id,
                    target_object_config_graph_package=tgt_pkg,
                    target_object_config_graph_package_id=tgt_pkg.id,
                    target_version=None,
                    target_version_id=target_version_id,
                )
            )
        src_pkg.dependencies.extend(deps)

    return packages, builds, versions


__all__ = [
    "AwareTomlBuildError",
    "build_packages_from_specs",
]
