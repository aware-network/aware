from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

import pytest

from aware_meta.runtime import (
    MetaGraphCommitIndex,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationKind,
    MetaGraphRuntimeContext,
    MetaGraphRuntimeIndexView,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    ProofCall,
    run_meta_runtime_proof,
)
from aware_storage.handlers._generated import meta_handlers as storage_meta_handlers

_TESTS_ROOT = Path(__file__).resolve().parent
KERNEL_WORKSPACE_ROOT = _TESTS_ROOT.parents[5]
STORAGE_PACKAGE_MANIFEST_PATHS = (
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/aware.toml",
)


_STORAGE_META_HANDLERS_ANY: Any = storage_meta_handlers
_STORAGE_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _STORAGE_META_HANDLERS_ANY,
)
_STORAGE_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _STORAGE_META_HANDLERS_ANY,
)


def _build_storage_meta_runtime(*, aware_root: Path):
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=STORAGE_PACKAGE_MANIFEST_PATHS,
        workspace_root=KERNEL_WORKSPACE_ROOT,
        aware_root=aware_root,
        handler_modules=(_STORAGE_META_HANDLER_MODULE,),
        bootstrap_modules=(_STORAGE_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


def _implementation_kind(
    context: MetaGraphRuntimeContext,
    *,
    owner_key: str,
    function_name: str,
) -> MetaGraphImplementationKind:
    view = MetaGraphRuntimeIndexView(
        index=cast(MetaGraphCommitIndex, cast(object, context.index)),
        implementation_policy=context.implementation_policy,
    )
    for descriptor in view.implementation_descriptors_by_id.values():
        function_config = descriptor.function_config
        if (
            function_config.owner_key == owner_key
            and function_config.name == function_name
        ):
            return descriptor.kind
    raise AssertionError(f"Function descriptor not found: {owner_key}.{function_name}")


@pytest.mark.asyncio
async def test_storage_module_proof_constructor_projected_to_storage_blob_opg(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_storage_ontology  # noqa: F401
    from aware_storage.handlers.impl.blob import storage_blob as storage_blob_handler
    from aware_storage.stable_ids import stable_storage_blob_id

    async def _forbidden_python_create(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise AssertionError(
            "StorageBlob.create parity proof must use native FunctionImpl"
        )

    monkeypatch.setenv("AWARE_RUNTIME_FUNCTION_IMPL_MODE", "interpreter_primary")
    monkeypatch.setattr(storage_blob_handler, "create", _forbidden_python_create)

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_storage_meta_runtime(
            aware_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        idx = context.index

        # Storage module has constructor metadata in ontology.
        storage_blob_cc = next(
            cc for cc in idx.class_configs_by_id.values() if cc.name == "StorageBlob"
        )
        storage_bucket_cc = next(
            cc for cc in idx.class_configs_by_id.values() if cc.name == "StorageBucket"
        )
        assert storage_blob_cc is not None
        assert storage_bucket_cc is not None

        create_fn = next(
            fn_conf
            for fn_conf in storage_blob_cc.class_config_function_configs
            if fn_conf.is_constructor and fn_conf.function_config.name == "create"
        )
        # StorageBlob.create must be a constructor in ontology.
        assert create_fn.function_config.name == "create"
        assert (
            _implementation_kind(
                context,
                owner_key="aware_storage.default.blob.StorageBlob",
                function_name="create",
            )
            is MetaGraphImplementationKind.aware_function_impl
        )

        opg_by_name = {str(opg.name): opg for opg in idx.ocg.object_projection_graphs}
        assert "StorageBlob" in opg_by_name
        assert "StorageBucket" in opg_by_name

        storage_blob_constructor_ids = {
            c.function_constructor_id
            for c in opg_by_name["StorageBlob"].object_projection_graph_constructors
        }
        assert create_fn.id in storage_blob_constructor_ids

        sha = "A" * 64
        normalized_sha = sha.lower()
        expected_blob_id = stable_storage_blob_id(sha=normalized_sha)
        lane = LaneIds(
            environment_id=uuid5(NAMESPACE_URL, "aware://tests/storage/env"),
            process_id=uuid5(NAMESPACE_URL, "aware://tests/storage/process"),
            thread_id=uuid5(NAMESPACE_URL, "aware://tests/storage/thread"),
        )
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="StorageBlob",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_storage.default.blob.StorageBlob",
                    function_name="create",
                    args=[sha, " ", 12],
                    expected_root_object_id=expected_blob_id,
                )
            ],
        )
        assert result.root_object_id == expected_blob_id
        assertions.expect_root(expected_blob_id)
        assertions.expect_instance(expected_blob_id)
        assertions.expect_primitive(
            instance_id=expected_blob_id, field_name="sha", expected=normalized_sha
        )
        assertions.expect_primitive(
            instance_id=expected_blob_id,
            field_name="mime_type",
            expected="application/octet-stream",
        )
        assertions.expect_primitive(
            instance_id=expected_blob_id, field_name="size_bytes", expected=12
        )
        assertions.expect_primitive(
            instance_id=expected_blob_id,
            field_name="object_key",
            expected=f"{normalized_sha[:2]}/{normalized_sha[2:]}",
        )
