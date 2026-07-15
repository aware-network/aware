-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE credential_grant_effect AS ENUM ('allow', 'deny');

CREATE TYPE credential_kind AS ENUM ('api_key', 'bearer_token', 'certificate', 'generic_secret', 'oauth2_access_token', 'oidc_trusted_publisher', 'password', 'ssh_key');

CREATE TYPE credential_profile_status AS ENUM ('blocked', 'expired', 'planned', 'ready', 'revoked');

CREATE TYPE credential_readiness_status AS ENUM ('blocked', 'invalid', 'missing', 'ready', 'unauthorized', 'unknown');

CREATE TYPE credential_secret_resolver_kind AS ENUM ('aware_secrets_dir', 'ci_secret', 'env_var', 'external_vault', 'local_file', 'no_secret', 'pypirc', 'trusted_publisher_oidc');

CREATE TYPE credential_target_kind AS ENUM ('aware_api', 'aware_service', 'generic', 'github', 'hub', 'oci', 'pypi', 'test_pypi');

CREATE TYPE credential_usage_status AS ENUM ('blocked', 'failed', 'planned', 'skipped', 'succeeded');
