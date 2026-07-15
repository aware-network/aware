from __future__ import annotations

# Standard
from enum import Enum


class CredentialGrantEffect(Enum):
    allow = "allow"
    deny = "deny"


class CredentialKind(Enum):
    api_key = "api_key"
    bearer_token = "bearer_token"
    oauth2_access_token = "oauth2_access_token"
    oidc_trusted_publisher = "oidc_trusted_publisher"
    ssh_key = "ssh_key"
    certificate = "certificate"
    password = "password"
    generic_secret = "generic_secret"


class CredentialProfileStatus(Enum):
    planned = "planned"
    ready = "ready"
    blocked = "blocked"
    revoked = "revoked"
    expired = "expired"


class CredentialReadinessStatus(Enum):
    unknown = "unknown"
    ready = "ready"
    missing = "missing"
    invalid = "invalid"
    unauthorized = "unauthorized"
    blocked = "blocked"


class CredentialSecretResolverKind(Enum):
    env_var = "env_var"
    pypirc = "pypirc"
    local_file = "local_file"
    aware_secrets_dir = "aware_secrets_dir"
    ci_secret = "ci_secret"
    external_vault = "external_vault"
    trusted_publisher_oidc = "trusted_publisher_oidc"
    no_secret = "no_secret"


class CredentialTargetKind(Enum):
    aware_api = "aware_api"
    aware_service = "aware_service"
    test_pypi = "test_pypi"
    pypi = "pypi"
    github = "github"
    oci = "oci"
    hub = "hub"
    generic = "generic"


class CredentialUsageStatus(Enum):
    planned = "planned"
    succeeded = "succeeded"
    failed = "failed"
    blocked = "blocked"
    skipped = "skipped"
