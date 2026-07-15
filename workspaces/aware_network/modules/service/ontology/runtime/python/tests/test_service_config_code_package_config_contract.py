from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

import pytest

from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphRuntimeIndex,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    MetaOIGAssertions,
    materialize_meta_runtime_lane_head,
)
from aware_service_runtime.handlers._generated import (
    meta_handlers as service_meta_handlers,
)
from _service_runtime_test_paths import REPO_ROOT

_SERVICE_META_HANDLERS_ANY: Any = service_meta_handlers
_SERVICE_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _SERVICE_META_HANDLERS_ANY,
)
_SERVICE_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _SERVICE_META_HANDLERS_ANY,
)


@dataclass(frozen=True, slots=True)
class IsolatedMetaAwareRoot:
    root: Path
    persistence_backend: str = "fs"
    _env_overrides: dict[str, str | None] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def __enter__(self) -> Path:
        root = self.root.expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        (root / ".aware").mkdir(parents=True, exist_ok=True)
        env_overrides = {
            "AWARE_ROOT": os.environ.get("AWARE_ROOT"),
            "AWARE_PERSISTENCE_BACKEND": os.environ.get("AWARE_PERSISTENCE_BACKEND"),
            "DATABASE_URL": os.environ.get("DATABASE_URL"),
        }
        object.__setattr__(self, "_env_overrides", env_overrides)
        os.environ["AWARE_ROOT"] = str(root)
        os.environ["AWARE_PERSISTENCE_BACKEND"] = self.persistence_backend
        os.environ.pop("DATABASE_URL", None)
        return root

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = exc_type, exc, tb
        for key, previous in self._env_overrides.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous


def _service_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/economy/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/service/ontology/structure/aware.toml",
    )


def _build_service_meta_runtime(repo_root: Path, *, workspace_root: Path):
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_service_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=workspace_root,
        handler_modules=(_SERVICE_META_HANDLER_MODULE,),
        bootstrap_modules=(_SERVICE_META_BOOTSTRAP_MODULE,),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    assert runtime.context is not None
    return runtime


def _has_meta_handler(*, owner_key: str, function_name: str) -> bool:
    return any(
        key.owner_key == owner_key and key.function_name == function_name
        for key in service_meta_handlers.AWARE_META_GRAPH_HANDLERS
    )


def _has_empty_lane_bootstrap(*, owner_key: str, function_name: str) -> bool:
    return any(
        key.owner_key == owner_key and key.function_name == function_name
        for key in service_meta_handlers.AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS
    )


@pytest.mark.asyncio
async def test_service_config_code_package_config_meta_runtime_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    from aware_code_ontology.stable_ids import stable_code_package_config_id
    from aware_service_ontology.service.service_config import ServiceConfig
    from aware_service_ontology.service.service_enums import (
        ServiceConfigCodePackageConfigCardinality,
    )
    from aware_service_ontology.stable_ids import (
        stable_service_config_code_package_config_id,
        stable_service_config_id,
    )

    service_config_name = "aware-experience-service"
    slot_key = "experience"
    code_package_config_id = stable_code_package_config_id(
        config_key="aware_experience_package",
    )
    expected_service_config_id = stable_service_config_id(name=service_config_name)
    expected_slot_id = stable_service_config_code_package_config_id(
        service_config_id=expected_service_config_id,
        code_package_config_id=code_package_config_id,
        slot_key=slot_key,
    )

    assert _has_meta_handler(
        owner_key="aware_service.service.ServiceConfig",
        function_name="declare_code_package_config",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_service.service.ServiceConfigCodePackageConfig",
        function_name="build_via_service_config",
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_service_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        lane = runtime.bind(
            projection="ServiceConfig",
            branch_id=uuid5(
                NAMESPACE_URL,
                "service://tests/code-package-config/branch",
            ),
        )
        with lane.activate(commit=True, publish=False):
            service_config = await ServiceConfig.build(
                name=service_config_name,
                description="Experience service capability catalog.",
            )

        with lane.activate(commit=True, publish=False):
            slot = await service_config.declare_code_package_config(
                slot_key=slot_key,
                code_package_config_id=code_package_config_id,
                cardinality=ServiceConfigCodePackageConfigCardinality.many,
                required=True,
                description="Experience packages hosted by this service.",
            )

        assert service_config.id == expected_service_config_id
        assert slot.id == expected_slot_id
        assert slot.service_config_id == expected_service_config_id
        assert slot.code_package_config_id == code_package_config_id
        assert slot.slot_key == slot_key
        assert slot.required is True
        assert slot.cardinality is ServiceConfigCodePackageConfigCardinality.many
        oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=lane,
        )

    assertions = MetaOIGAssertions(
        oig=oig,
        index=cast(MetaGraphRuntimeIndex, cast(object, context.index)),
    )
    assertions.expect_root(expected_service_config_id)
    assertions.expect_instance(expected_service_config_id)
    assertions.expect_instance(expected_slot_id)
    assertions.expect_edge(
        source_id=expected_service_config_id,
        target_id=expected_slot_id,
        relationship_name="code_package_configs",
    )
    assertions.expect_primitive(
        instance_id=expected_slot_id,
        field_name="slot_key",
        expected=slot_key,
    )
    code_package_config_primitive = assertions.primitive(
        instance_id=expected_slot_id,
        field_name="code_package_config_id",
    )
    assert code_package_config_primitive in {
        code_package_config_id,
        str(code_package_config_id),
    }
    assertions.expect_primitive(
        instance_id=expected_slot_id,
        field_name="cardinality",
        expected=ServiceConfigCodePackageConfigCardinality.many.value,
    )
    assertions.expect_primitive(
        instance_id=expected_slot_id,
        field_name="required",
        expected=True,
    )
