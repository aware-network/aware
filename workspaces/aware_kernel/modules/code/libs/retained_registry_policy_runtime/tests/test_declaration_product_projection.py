"""Cross-owner source-grade conformance of the neutral pre-host Code projection.

Workspace fixtures only supply original observed declarations. Production Code
imports no Workspace or semantic-owner implementation.
"""

from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime.declaration_product_projection import (
    check_declared_product_origin,
    project_declared_inspect_product,
    project_declared_product,
)
from aware_code_semantic_contract_runtime import ContractViolation
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    RegistryPackageInputCodec,
    encode_registry_package_input,
)
from test_declaration_product_membership import prepared
from test_direct_cli_selected_host import factory as _factory

factory = _factory


async def test_original_projection_uses_existing_codec_before_host_policy(tmp_path, factory):
    async with prepared(tmp_path, factory) as (_, command, selected, product, _, _):
        issuer = command.sources.declaration_scope_runtime
        declaration = command.sources.declaration_scope
        closure = issuer.read_declaration_scope(declaration)
        view = issuer.read_selected_participant_view(declaration, selected)
        result = project_declared_product(closure, view, product)
        body = encode_registry_package_input(result.registry)
        assert RegistryPackageInputCodec().decode(body) == result.registry
        assert result.registry.semantic_provider_key == "attention-layout-definition"
        assert result.package.namespace == "sample_attention"
        assert result.terminal_roles == ("attention_definition_manifest",)
        assert command.catalog_host._phase == "new"
        check_declared_product_origin(product, result)
        with pytest.raises(ContractViolation):
            check_declared_product_origin(
                product, replace(result, registry=replace(result.registry, profile_ref="foreign"))
            )


async def test_foreign_product_and_incomplete_view_cannot_project_membership(tmp_path, factory):
    async with prepared(tmp_path, factory) as (_, command, selected, product, _, _):
        issuer = command.sources.declaration_scope_runtime
        declaration = command.sources.declaration_scope
        closure = issuer.read_declaration_scope(declaration)
        view = issuer.read_selected_participant_view(declaration, selected)
        with pytest.raises(TypeError):
            project_declared_product(closure, view, object())
        with pytest.raises(ContractViolation):
            project_declared_product(closure, replace(view, participants=(view.root,)), product)
        project_declared_product(closure, view, product)


async def test_inspect_projection_does_not_adopt_materialize_original(tmp_path, factory):
    async with prepared(tmp_path, factory) as (_, command, selected, product, _, _):
        issuer = command.sources.declaration_scope_runtime
        closure = issuer.read_declaration_scope(command.sources.declaration_scope)
        view = issuer.read_selected_participant_view(command.sources.declaration_scope, selected)
        with pytest.raises(ContractViolation, match="inspect-only"):
            project_declared_inspect_product(closure, view, product)
        # Refusal neither closes nor upgrades the original materialize product.
        project_declared_product(closure, view, product)
        with pytest.raises(TypeError):
            project_declared_inspect_product(closure, view, object())
