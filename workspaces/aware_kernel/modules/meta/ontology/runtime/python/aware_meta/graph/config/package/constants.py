from uuid import UUID, uuid5

# Deterministic UUID namespace for `aware.toml` package spine objects.
# This UUID is intentionally constant across all workspaces and time.
#
# If we ever need to rotate it, that should be an explicit schema/version migration.
AWARE_TOML_UUID_NAMESPACE = UUID("f9b1d8b4-8b9d-4f6f-9c7d-5d2e2baf4e55")


def deterministic_uuid(key: str) -> UUID:
    """Deterministically derive a UUID from a stable key string."""
    return uuid5(AWARE_TOML_UUID_NAMESPACE, key)


def package_uuid(*, package_name: str) -> UUID:
    return deterministic_uuid(f"package:{package_name}")


def package_build_uuid(*, package_name: str, environment_slug: str) -> UUID:
    return deterministic_uuid(f"package_build:{package_name}:{environment_slug}")


def package_dependency_uuid(*, source_package_name: str, target_package_name: str) -> UUID:
    return deterministic_uuid(f"package_dep:{source_package_name}->{target_package_name}")


def package_version_uuid(*, package_name: str, version_number: int) -> UUID:
    return deterministic_uuid(f"package_version:{package_name}:{version_number}")


__all__ = [
    "AWARE_TOML_UUID_NAMESPACE",
    "deterministic_uuid",
    "package_uuid",
    "package_build_uuid",
    "package_dependency_uuid",
    "package_version_uuid",
]
