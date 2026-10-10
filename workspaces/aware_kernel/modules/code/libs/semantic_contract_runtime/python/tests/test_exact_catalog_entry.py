"""Exact binding reads preserve admission, full integrity and detached values."""

from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import materialization_catalog as catalogs
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from test_materialization_catalog import _binding, _catalog, _resolver


def test_exact_entry_read_is_detached_without_full_catalog_export(monkeypatch):
    binding = _binding()
    resolver = _resolver(_catalog(binding))

    def forbidden(*args):
        raise AssertionError("full catalog export is unnecessary")

    monkeypatch.setattr(catalogs, "_detached_catalog_snapshot", forbidden)
    value = resolver.read_profile_binding(
        profile=binding.profile_declaration,
        semantic_provider_key=binding.semantic_provider_key,
    )
    assert value == binding and value is not binding
    object.__setattr__(value.profile_declaration, "version", "foreign")
    assert (
        resolver.read_profile_binding(
            profile=binding.profile_declaration,
            semantic_provider_key=binding.semantic_provider_key,
        )
        == binding
    )


@pytest.mark.parametrize("change", ["provider", "profile", "revoked", "unselected"])
def test_missing_or_invalid_original_entry_rejects(change):
    binding, other = _binding(), _binding(provider_key="other")
    resolver = _resolver(_catalog(binding, other))
    profile, provider = binding.profile_declaration, binding.semantic_provider_key
    if change == "provider":
        provider = "foreign"
    elif change == "profile":
        profile = replace(profile, version="foreign")
    elif change == "revoked":
        catalogs._revoke_code_semantic_contract_catalog(resolver._admission)
    else:
        entry = next(
            e for e in resolver._catalog.entries if e.semantic_provider_key == "other"
        )
        object.__setattr__(entry.profile_declaration, "version", "foreign")
    with pytest.raises(ContractViolation):
        resolver.read_profile_binding(profile=profile, semantic_provider_key=provider)


@pytest.mark.parametrize("change", ["snapshot", "revocation"])
def test_changes_during_copy_reject(change, monkeypatch):
    binding = _binding()
    resolver = _resolver(_catalog(binding))
    original = catalogs.deepcopy

    def changed(value):
        result = original(value)
        if change == "snapshot":
            object.__setattr__(result.profile_declaration, "version", "foreign")
        else:
            catalogs._revoke_code_semantic_contract_catalog(resolver._admission)
        return result

    monkeypatch.setattr(catalogs, "deepcopy", changed)
    with pytest.raises(ContractViolation):
        resolver.read_profile_binding(
            profile=binding.profile_declaration,
            semantic_provider_key=binding.semantic_provider_key,
        )
