from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from ._economy_runtime_test_paths import REPO_ROOT, economy_package_manifest_paths
from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    MetaOIGAssertions,
    ProofCall,
    run_meta_runtime_proof,
)


ECONOMY_PACKAGE_CLASS_FQN = "aware_economy.economy.EconomyPackage"

_ECONOMY_META_HANDLERS_ANY: Any = economy_meta_handlers
_ECONOMY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ECONOMY_META_HANDLERS_ANY,
)
_ECONOMY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ECONOMY_META_HANDLERS_ANY,
)


def _build_economy_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=economy_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_ECONOMY_META_HANDLER_MODULE,),
        bootstrap_modules=(_ECONOMY_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


def _expect_uuid_primitive(
    assertions: MetaOIGAssertions,
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


def _ids_by_class_name(assertions) -> dict[str, list[UUID]]:  # noqa: ANN001
    class_name_by_id = {
        cc_id: cc.name for cc_id, cc in assertions._class_configs_by_id.items()
    }  # noqa: SLF001
    ids_by_class_name: dict[str, list[UUID]] = {}
    for ci in assertions.oig.class_instances:
        if ci.id is None:
            continue
        class_name = class_name_by_id.get(ci.class_config_id)
        if class_name is None:
            continue
        ids_by_class_name.setdefault(class_name, []).append(UUID(str(ci.id)))
    return ids_by_class_name


@pytest.mark.asyncio
async def test_economy_package_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_code_ontology  # noqa: F401
    import aware_economy_ontology  # noqa: F401
    from aware_code_ontology.stable_ids import (
        stable_code_package_config_id,
        stable_code_package_id,
    )
    from aware_economy_ontology.economy.economy_package import EconomyPackage
    from aware_economy_ontology.stable_ids import stable_economy_package_id

    source_package_name = "aware_economy_test_source_package"
    source_package_config_key = "economy-test-source"
    economy_package_name = "aware-economy-test-package"

    source_code_package_config_id = stable_code_package_config_id(
        config_key=source_package_config_key,
    )
    source_code_package_id = stable_code_package_id(
        code_package_config_id=source_code_package_config_id,
        package_name=source_package_name,
        language="aware",
    )
    economy_package_id = stable_economy_package_id(name=economy_package_name)

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_economy_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        lane = LaneIds(
            branch_id=uuid4(),
            actor_id=uuid4(),
        )
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="EconomyPackage",
            root_class_fqn=ECONOMY_PACKAGE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_PACKAGE_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": economy_package_name,
                        "source_code_package_id": source_code_package_id,
                    },
                    expected_root_object_id=economy_package_id,
                ),
            ],
        )

        assert result.root_object_id == economy_package_id
        assertions.expect_root(economy_package_id)
        assertions.expect_instance(economy_package_id)
        assertions.expect_primitive(
            instance_id=economy_package_id,
            field_name="name",
            expected=economy_package_name,
        )

        _expect_uuid_primitive(
            assertions,
            instance_id=economy_package_id,
            field_name="source_code_package_id",
            expected=source_code_package_id,
        )

        ids_by_class = _ids_by_class_name(assertions)
        assert ids_by_class.get("EconomyPackage", [])

        payload = result.responses[-1].payload
        assert isinstance(payload, dict)
        created_payload = payload.get("value", payload)
        created = EconomyPackage.model_validate(created_payload)
        assert created.id == economy_package_id
        assert created.name == economy_package_name
        assert created.source_code_package_id == source_code_package_id
