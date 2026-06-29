from __future__ import annotations

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


def _text(source_bytes: bytes, node: Node | None) -> str:
    assert node is not None
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8")


def _find_nodes(node: Node, node_type: str) -> list[Node]:
    matches: list[Node] = []
    if node.type == node_type:
        matches.append(node)
    for child in node.named_children:
        matches.extend(_find_nodes(child, node_type))
    return matches


def test_tree_sitter_parses_service_blocks() -> None:
    source = """\
service workspace {
    api workspace_api {
        projection aware_workspace.workspace_graph;
    }
    experience workspace_coordination;

    operation compile {
        endpoint workspace_api.compilation.compile;
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    service_defs = _find_nodes(root, "service_def")
    assert len(service_defs) == 1

    service_def = service_defs[0]
    assert _text(source_bytes, service_def.child_by_field_name("name")) == "workspace"

    api_decls = _find_nodes(service_def, "service_api_decl")
    assert len(api_decls) == 1
    assert (
        _text(source_bytes, api_decls[0].child_by_field_name("api")) == "workspace_api"
    )
    api_projection_decls = _find_nodes(service_def, "service_api_projection_decl")
    assert len(api_projection_decls) == 1
    assert _text(
        source_bytes, api_projection_decls[0].child_by_field_name("projection")
    ) == ("aware_workspace.workspace_graph")
    experience_decls = _find_nodes(service_def, "service_experience_decl")
    assert len(experience_decls) == 1
    assert _text(
        source_bytes, experience_decls[0].child_by_field_name("experience")
    ) == ("workspace_coordination")

    operation_defs = _find_nodes(service_def, "service_operation_def")
    assert len(operation_defs) == 1
    operation_def = operation_defs[0]
    assert (
        _text(source_bytes, operation_def.child_by_field_name("operation_name"))
        == "compile"
    )

    endpoint_defs = _find_nodes(operation_def, "service_operation_endpoint_def")
    assert len(endpoint_defs) == 1
    assert _text(source_bytes, endpoint_defs[0].child_by_field_name("endpoint")) == (
        "workspace_api.compilation.compile"
    )


def test_tree_sitter_parses_service_operation_price_declaration() -> None:
    source = """\
service workspace {
    api workspace_api;

    operation diagnose {
        endpoint workspace_api.diagnostics.run;
        admission metered_settlement_required;
        receipt committed;
        settlement reserve_and_finalize;
        price {
            coin USD;
            type fixed;
            fixed_amount 2.50;
            effective_from "2026-04-21T00:00:00Z";

            policy {
                fail_closed true;
            }
        }
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    price_defs = _find_nodes(root, "service_operation_price_def")
    assert len(price_defs) == 1
    settlement_defs = _find_nodes(root, "service_operation_settlement_decl")
    assert len(settlement_defs) == 1
    assert _text(
        source_bytes, settlement_defs[0].child_by_field_name("settlement_policy")
    ) == ("reserve_and_finalize")
    admission_defs = _find_nodes(root, "service_operation_admission_policy_decl")
    assert len(admission_defs) == 1
    assert _text(
        source_bytes, admission_defs[0].child_by_field_name("admission_mode")
    ) == ("metered_settlement_required")
    receipt_defs = _find_nodes(root, "service_operation_receipt_policy_decl")
    assert len(receipt_defs) == 1
    assert (
        _text(source_bytes, receipt_defs[0].child_by_field_name("receipt_policy"))
        == "committed"
    )
    price_def = price_defs[0]
    coin_defs = _find_nodes(price_def, "service_operation_price_coin_decl")
    assert len(coin_defs) == 1
    assert _text(source_bytes, coin_defs[0].child_by_field_name("coin_symbol")) == "USD"

    type_defs = _find_nodes(price_def, "service_operation_price_type_decl")
    assert len(type_defs) == 1
    assert (
        _text(source_bytes, type_defs[0].child_by_field_name("price_type")) == "fixed"
    )

    fixed_amount_defs = _find_nodes(
        price_def, "service_operation_price_fixed_amount_decl"
    )
    assert len(fixed_amount_defs) == 1
    assert (
        _text(source_bytes, fixed_amount_defs[0].child_by_field_name("fixed_amount"))
        == "2.50"
    )

    effective_from_defs = _find_nodes(
        price_def, "service_operation_price_effective_from_decl"
    )
    assert len(effective_from_defs) == 1
    assert _text(
        source_bytes, effective_from_defs[0].child_by_field_name("effective_from")
    ) == ('"2026-04-21T00:00:00Z"')

    fail_closed_defs = _find_nodes(
        price_def, "service_operation_price_policy_fail_closed_decl"
    )
    assert len(fail_closed_defs) == 1
    assert (
        _text(source_bytes, fail_closed_defs[0].child_by_field_name("fail_closed"))
        == "true"
    )


def test_tree_sitter_parses_service_code_package_config_declaration() -> None:
    source = """\
service aware_experience {
    api experience;

    package experience {
        manifest aware_experience_toml;
        surface experience;
        cardinality many;
        required false;
    }

    operation resolve_package {
        endpoint experience.package_materialization.resolve_experience_package_projection_ownership;
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    package_decls = _find_nodes(root, "service_code_package_config_decl")
    assert len(package_decls) == 1
    package_decl = package_decls[0]
    assert _text(source_bytes, package_decl.child_by_field_name("slot")) == "experience"

    manifest_decls = _find_nodes(
        package_decl, "service_code_package_config_manifest_decl"
    )
    assert len(manifest_decls) == 1
    assert (
        _text(source_bytes, manifest_decls[0].child_by_field_name("manifest_kind"))
        == "aware_experience_toml"
    )
    surface_decls = _find_nodes(
        package_decl, "service_code_package_config_surface_decl"
    )
    assert len(surface_decls) == 1
    assert (
        _text(source_bytes, surface_decls[0].child_by_field_name("surface"))
        == "experience"
    )
    cardinality_decls = _find_nodes(
        package_decl, "service_code_package_config_cardinality_decl"
    )
    assert len(cardinality_decls) == 1
    assert (
        _text(source_bytes, cardinality_decls[0].child_by_field_name("cardinality"))
        == "many"
    )
    required_decls = _find_nodes(
        package_decl, "service_code_package_config_required_decl"
    )
    assert len(required_decls) == 1
    assert (
        _text(source_bytes, required_decls[0].child_by_field_name("required"))
        == "false"
    )


def test_tree_sitter_parses_service_contract_operation_view_and_role_declarations() -> (
    None
):
    source = """\
service identity {
    api identity_api;
    experience actor_identity;

    operation actor_roles {
        endpoint identity_api.actor.roles;
        view actor_identity.roles {
            provider service_operation;
        }
        role identity.actor_reader {
            access operation;
            scope operation actor_roles;
            class_instance_identity_required true;
            role_assignment_binding_required true;
        }
    }

    contract actor_subscription {
        kind subscription;
        projection_experience actor_identity;
        grant operation actor_roles {
            access operation;
        }
        grant actor_role identity.actor_reader {
            access service;
            scope service default;
            class_instance_identity_required false;
            role_assignment_binding_required true;
        }
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    view_defs = _find_nodes(root, "service_operation_view_def")
    assert len(view_defs) == 1
    assert (
        _text(source_bytes, view_defs[0].child_by_field_name("view"))
        == "actor_identity.roles"
    )

    provider_decls = _find_nodes(root, "service_operation_view_provider_decl")
    assert len(provider_decls) == 1
    assert _text(
        source_bytes, provider_decls[0].child_by_field_name("provider_kind")
    ) == ("service_operation")

    role_requirement_defs = _find_nodes(root, "service_operation_role_requirement_def")
    assert len(role_requirement_defs) == 1
    assert _text(
        source_bytes, role_requirement_defs[0].child_by_field_name("role")
    ) == ("identity.actor_reader")

    contract_defs = _find_nodes(root, "service_contract_config_def")
    assert len(contract_defs) == 1
    assert _text(source_bytes, contract_defs[0].child_by_field_name("name")) == (
        "actor_subscription"
    )

    contract_kind_decls = _find_nodes(root, "service_contract_kind_decl")
    assert len(contract_kind_decls) == 1
    assert _text(
        source_bytes, contract_kind_decls[0].child_by_field_name("contract_kind")
    ) == ("subscription")

    projection_experience_decls = _find_nodes(
        root, "service_contract_projection_experience_decl"
    )
    assert len(projection_experience_decls) == 1
    assert (
        _text(
            source_bytes,
            projection_experience_decls[0].child_by_field_name("projection_experience"),
        )
        == "actor_identity"
    )

    operation_grant_defs = _find_nodes(root, "service_contract_operation_grant_def")
    assert len(operation_grant_defs) == 1
    assert _text(
        source_bytes, operation_grant_defs[0].child_by_field_name("operation")
    ) == ("actor_roles")

    actor_role_grant_defs = _find_nodes(root, "service_contract_actor_role_grant_def")
    assert len(actor_role_grant_defs) == 1
    assert _text(
        source_bytes, actor_role_grant_defs[0].child_by_field_name("role")
    ) == ("identity.actor_reader")

    access_decls = _find_nodes(root, "service_role_access_decl")
    assert len(access_decls) == 3
    assert [
        _text(source_bytes, node.child_by_field_name("access_scope"))
        for node in access_decls
    ] == [
        "operation",
        "operation",
        "service",
    ]

    scope_decls = _find_nodes(root, "service_role_scope_decl")
    assert len(scope_decls) == 2
    assert (
        _text(source_bytes, scope_decls[0].child_by_field_name("scope_kind"))
        == "operation"
    )
    assert (
        _text(source_bytes, scope_decls[0].child_by_field_name("scope_ref"))
        == "actor_roles"
    )
    assert (
        _text(source_bytes, scope_decls[1].child_by_field_name("scope_kind"))
        == "service"
    )
    assert (
        _text(source_bytes, scope_decls[1].child_by_field_name("scope_ref"))
        == "default"
    )
