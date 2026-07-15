from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from aware_service_runtime.compiler import load_service_ownership_from_sources

from _service_runtime_test_paths import REPO_ROOT

_REPO_ROOT = REPO_ROOT


def _write_service_source(root: Path, *, relpath: str, source: str) -> Path:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(source, encoding="utf-8")
    return Path(relpath)


def test_load_service_ownership_from_sources_parses_service_definition(
    tmp_path: Path,
) -> None:
    relpath = _write_service_source(
        tmp_path,
        relpath="services/bindings/home.services.aware",
        source="""\
service home_story {
    api home_story_api {
        projection aware_home.home_projection
    }
    api audit_api
    experience home_story

    operation open_door {
        endpoint home_story_api.door.open
        price {
            coin USD
            type fixed
            fixed_amount 2.50
            effective_from "2026-04-21T00:00:00Z"

            policy {
                fail_closed true
            }
        }
    }

    operation inspect_audit {
        endpoint audit_api.history.inspect
        admission public_read
        receipt read_model
    }
}
""",
    )

    ownership = load_service_ownership_from_sources(
        package_root=tmp_path,
        source_files=(relpath,),
    )

    assert len(ownership) == 1
    service = ownership[0]
    assert service.name == "home_story"
    assert tuple(api.api_ref for api in service.apis) == ("audit_api", "home_story_api")
    assert tuple(experience.experience_ref for experience in service.experiences) == (
        "home_story",
    )
    home_api = next(api for api in service.apis if api.api_ref == "home_story_api")
    assert tuple(
        projection.projection_ref for projection in home_api.api_projections
    ) == ("aware_home.home_projection",)
    assert tuple(operation.name for operation in service.operations) == (
        "inspect_audit",
        "open_door",
    )
    assert service.operations[0].admission_mode == "public_read"
    assert service.operations[0].fulfillment_kind == "view"
    assert service.operations[0].receipt_policy == "read_model"
    assert service.operations[1].admission_mode == "contract_required"
    assert service.operations[1].fulfillment_kind == "coordination"
    assert service.operations[1].price is not None
    assert service.operations[1].price.coin_symbol == "USD"
    assert service.operations[1].price.price_type == "fixed"
    assert service.operations[1].price.fixed_amount == Decimal("2.50")
    assert service.operations[1].price.effective_from == "2026-04-21T00:00:00Z"


def test_network_service_topology_surface_is_identity_gated() -> None:
    ownership = load_service_ownership_from_sources(
        package_root=_REPO_ROOT,
        source_files=(
            Path(
                "workspaces/aware_network/modules/network/services/network/bindings/network.services.aware"
            ),
        ),
    )

    assert len(ownership) == 1
    service = ownership[0]
    assert service.name == "aware_network"
    operations = {operation.name: operation for operation in service.operations}

    committed_writes = {
        "publish_environment",
        "publish_hosted_service",
        "register_node",
        "upsert_peer",
    }
    read_model_ops = {
        "discover_experience_territory",
        "discover_territory",
        "list_environments",
        "list_hosted_services",
        "list_peers",
        "resolve_hosted_service_routes",
    }

    assert set(operations) == committed_writes | read_model_ops
    for operation_name in committed_writes:
        operation = operations[operation_name]
        assert operation.receipt_policy == "committed"
        assert operation.fulfillment_kind == "coordination"
        assert operation.admission_mode == "identity_required"
    for operation_name in read_model_ops:
        operation = operations[operation_name]
        assert operation.receipt_policy == "read_model"
        assert operation.fulfillment_kind == "view"
        assert operation.admission_mode == "identity_required"
    assert all(operation.price is None for operation in operations.values())


def test_workspace_delta_preview_read_model_operation_compiles_as_view() -> None:
    ownership = load_service_ownership_from_sources(
        package_root=_REPO_ROOT,
        source_files=(
            Path(
                "workspaces/aware_workspace/modules/workspace/services/workspace/bindings/workspace.services.aware"
            ),
        ),
    )

    assert len(ownership) == 1
    service = ownership[0]
    operations = {operation.name: operation for operation in service.operations}
    delta_preview = operations["delta_preview"]

    assert delta_preview.receipt_policy == "read_model"
    assert delta_preview.fulfillment_kind == "view"


def test_load_service_ownership_from_sources_parses_contract_view_and_role_config(
    tmp_path: Path,
) -> None:
    relpath = _write_service_source(
        tmp_path,
        relpath="services/bindings/identity.services.aware",
        source="""\
service identity {
    api identity_api
    experience actor_identity

    operation actor_roles {
        endpoint identity_api.actor.roles
        view identity.roles
        role identity.actor_reader {
            access operation
            scope operation actor_roles
            class_instance_identity_required true
            role_assignment_binding_required true
        }
    }

    contract actor_subscription {
        kind subscription
        projection_experience actor_identity
        grant operation actor_roles {
            access operation
        }
        grant actor_role identity.actor_reader {
            access service
            scope service default
            class_instance_identity_required false
            role_assignment_binding_required true
        }
    }
}
""",
    )

    ownership = load_service_ownership_from_sources(
        package_root=tmp_path,
        source_files=(relpath,),
    )

    assert len(ownership) == 1
    service = ownership[0]
    assert service.name == "identity"
    assert tuple(experience.experience_ref for experience in service.experiences) == (
        "actor_identity",
    )
    assert tuple(operation.name for operation in service.operations) == ("actor_roles",)

    operation = service.operations[0]
    assert tuple(view.view_ref for view in operation.api_views) == ("identity.roles",)
    assert tuple(
        requirement.role_ref for requirement in operation.role_requirements
    ) == ("identity.actor_reader",)
    assert operation.role_requirements[0].access_scope == "operation"
    assert operation.role_requirements[0].scope_kind == "operation"
    assert operation.role_requirements[0].scope_ref == "actor_roles"
    assert operation.role_requirements[0].class_instance_identity_required is True
    assert operation.role_requirements[0].role_assignment_binding_required is True

    assert tuple(contract.name for contract in service.contract_configs) == (
        "actor_subscription",
    )
    contract = service.contract_configs[0]
    assert contract.default_kind == "subscription"
    assert contract.projection_experience_ref == "actor_identity"
    assert tuple(grant.operation_ref for grant in contract.operation_grants) == (
        "actor_roles",
    )
    assert contract.operation_grants[0].access_scope == "operation"
    assert tuple(grant.role_ref for grant in contract.actor_role_grants) == (
        "identity.actor_reader",
    )
    assert contract.actor_role_grants[0].access_scope == "service"
    assert contract.actor_role_grants[0].scope_kind == "service"
    assert contract.actor_role_grants[0].scope_ref == "default"
    assert contract.actor_role_grants[0].class_instance_identity_required is False
    assert contract.actor_role_grants[0].role_assignment_binding_required is True


def test_load_service_ownership_from_sources_rejects_retired_view_provider_block(
    tmp_path: Path,
) -> None:
    relpath = _write_service_source(
        tmp_path,
        relpath="services/bindings/identity.services.aware",
        source="""\
service identity {
    api identity

    operation actor_roles {
        endpoint identity.actor.roles
        view identity.roles {
            provider service_operation
        }
    }
}
""",
    )

    with pytest.raises(ValueError, match="retired nested view provider syntax"):
        load_service_ownership_from_sources(
            package_root=tmp_path,
            source_files=(relpath,),
        )


def test_load_service_ownership_from_sources_rejects_undeclared_api_binding(
    tmp_path: Path,
) -> None:
    relpath = _write_service_source(
        tmp_path,
        relpath="services/bindings/home.services.aware",
        source="""\
service home_story {
    api home_story_api

    operation open_door {
        endpoint other_api.door.open
    }
}
""",
    )

    with pytest.raises(ValueError, match="undeclared api"):
        _ = load_service_ownership_from_sources(
            package_root=tmp_path,
            source_files=(relpath,),
        )


def test_load_service_ownership_from_sources_rejects_public_read_committed_operation(
    tmp_path: Path,
) -> None:
    relpath = _write_service_source(
        tmp_path,
        relpath="services/bindings/home.services.aware",
        source="""\
service home_story {
    api home_story_api

    operation open_door {
        endpoint home_story_api.door.open
        admission public_read
    }
}
""",
    )

    with pytest.raises(ValueError, match="public_read admission"):
        _ = load_service_ownership_from_sources(
            package_root=tmp_path,
            source_files=(relpath,),
        )


def test_load_service_ownership_from_sources_rejects_duplicate_operation_name(
    tmp_path: Path,
) -> None:
    relpath = _write_service_source(
        tmp_path,
        relpath="services/bindings/home.services.aware",
        source="""\
service home_story {
    api home_story_api

    operation open_door {
        endpoint home_story_api.door.open
    }

    operation open_door {
        endpoint home_story_api.door.reopen
    }
}
""",
    )

    with pytest.raises(ValueError, match="duplicate operation"):
        _ = load_service_ownership_from_sources(
            package_root=tmp_path,
            source_files=(relpath,),
        )


def test_load_service_ownership_from_sources_rejects_duplicate_experience_binding(
    tmp_path: Path,
) -> None:
    relpath = _write_service_source(
        tmp_path,
        relpath="services/bindings/home.services.aware",
        source="""\
service home_story {
    api home_story_api
    experience home_story
    experience home_story

    operation open_door {
        endpoint home_story_api.door.open
    }
}
""",
    )

    with pytest.raises(ValueError, match="duplicate experience"):
        _ = load_service_ownership_from_sources(
            package_root=tmp_path,
            source_files=(relpath,),
        )


def test_load_service_ownership_from_sources_rejects_duplicate_api_projection(
    tmp_path: Path,
) -> None:
    relpath = _write_service_source(
        tmp_path,
        relpath="services/bindings/home.services.aware",
        source="""\
service home_story {
    api home_story_api {
        projection aware_home.home_projection
        projection aware_home.home_projection
    }

    operation open_door {
        endpoint home_story_api.door.open
    }
}
""",
    )

    with pytest.raises(ValueError, match="duplicate projection"):
        _ = load_service_ownership_from_sources(
            package_root=tmp_path,
            source_files=(relpath,),
        )


def test_load_service_ownership_from_sources_rejects_duplicate_operation_price(
    tmp_path: Path,
) -> None:
    relpath = _write_service_source(
        tmp_path,
        relpath="services/bindings/home.services.aware",
        source="""\
service home_story {
    api home_story_api

    operation open_door {
        endpoint home_story_api.door.open
        price {
            coin USD
            type fixed
            fixed_amount 2.50
            effective_from "2026-04-21T00:00:00Z"
        }
        price {
            coin USD
            type fixed
            fixed_amount 3.50
            effective_from "2026-04-22T00:00:00Z"
        }
    }
}
""",
    )

    with pytest.raises(ValueError, match="duplicate price binding"):
        _ = load_service_ownership_from_sources(
            package_root=tmp_path,
            source_files=(relpath,),
        )


def test_load_service_ownership_from_sources_rejects_fixed_price_without_amount(
    tmp_path: Path,
) -> None:
    relpath = _write_service_source(
        tmp_path,
        relpath="services/bindings/home.services.aware",
        source="""\
service home_story {
    api home_story_api

    operation open_door {
        endpoint home_story_api.door.open
        price {
            coin USD
            type fixed
            effective_from "2026-04-21T00:00:00Z"
        }
    }
}
""",
    )

    with pytest.raises(ValueError, match="fixed price requires fixed_amount"):
        _ = load_service_ownership_from_sources(
            package_root=tmp_path,
            source_files=(relpath,),
        )
