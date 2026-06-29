from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_history.handlers._generated import meta_handlers as history_meta_handlers
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    ProofCall,
    run_meta_runtime_proof,
)

_TESTS_ROOT = Path(__file__).resolve().parent
KERNEL_WORKSPACE_ROOT = _TESTS_ROOT.parents[5]
HISTORY_PACKAGE_MANIFEST_PATHS = (
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/aware.toml",
)


_HISTORY_META_HANDLERS_ANY: Any = history_meta_handlers
_HISTORY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _HISTORY_META_HANDLERS_ANY,
)
_HISTORY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _HISTORY_META_HANDLERS_ANY,
)


def _build_history_meta_runtime(*, aware_root: Path):
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=HISTORY_PACKAGE_MANIFEST_PATHS,
        workspace_root=KERNEL_WORKSPACE_ROOT,
        aware_root=aware_root,
        handler_modules=(_HISTORY_META_HANDLER_MODULE,),
        bootstrap_modules=(_HISTORY_META_BOOTSTRAP_MODULE,),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
    )
    assert runtime.context is not None
    return runtime


@pytest.mark.asyncio
async def test_history_branch_constructor_module_proof(tmp_path: Path) -> None:
    import aware_history_ontology  # noqa: F401
    from aware_history_ontology.stable_ids import stable_branch_id

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_history_meta_runtime(
            aware_root=aware_root,
        )
        env_id = uuid5(NAMESPACE_URL, "aware://tests/history/module-proof")
        process_id = uuid5(NAMESPACE_URL, "aware://tests/process/history")
        thread_id = uuid5(NAMESPACE_URL, "aware://tests/thread/history")
        branch_key = "history-main"
        branch_id = stable_branch_id(key=branch_key)
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(
                environment_id=env_id,
                process_id=process_id,
                thread_id=thread_id,
                branch_id=branch_id,
            ),
            opg_name="Branch",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_history.default.branch.Branch",
                    function_name="create",
                    args=[
                        str(branch_id),
                        "lane-hash-v1",
                    ],
                    kwargs={
                        "key": branch_key,
                        "is_main": True,
                        "name": "History Main",
                    },
                    expected_root_object_id=branch_id,
                )
            ],
        )

        assert result.root_object_id == branch_id == UUID(str(result.root_object_id))
        root_ci_id = UUID(str(assertions.oig.root_class_instance_id))
        assertions.expect_root(root_ci_id)
        assertions.expect_instance(root_ci_id)
        assertions.expect_primitive(
            instance_id=root_ci_id, field_name="name", expected="History Main"
        )
        assertions.expect_primitive(
            instance_id=root_ci_id, field_name="is_main", expected=True
        )
