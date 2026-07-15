from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from aware_skill_sdk import (
    SkillSdkError,
    SkillSdkOperationRunRequest,
    SkillSdkOperationRunner,
    SkillSdkOperationTarget,
)


_TEST_PROVIDER_REF = f"{__name__}:get_test_sdk_operation_catalog"
_MUTATING_PROVIDER_REF = f"{__name__}:get_mutating_sdk_operation_catalog"


def get_test_sdk_operation_catalog() -> dict[str, object]:
    return {
        "catalog_contract": "aware.sdk_operation_catalog.v0",
        "sdk_name": "test_sdk",
        "package_name": "aware-test-sdk",
        "version_number": 1,
        "operations": [
            {
                "operation_ref": "test_sdk.echo",
                "title": "Echo",
                "description": "Echo one request payload through a test SDK handler.",
                "endpoint_refs": ["test.echo.echo"],
                "input_schema": {"type": "object", "additionalProperties": True},
                "context_schema": {"type": "object", "additionalProperties": True},
                "effect": "read",
                "stability": "test",
                "handler_ref": f"{__name__}:dispatch_test_sdk_operation",
                "requires_confirmation": False,
            }
        ],
    }


def get_mutating_sdk_operation_catalog() -> dict[str, object]:
    return {
        "catalog_contract": "aware.sdk_operation_catalog.v0",
        "sdk_name": "mutating_sdk",
        "package_name": "aware-mutating-test-sdk",
        "version_number": 1,
        "operations": [
            {
                "operation_ref": "mutating_sdk.write",
                "title": "Write",
                "description": "Mutation guard canary.",
                "endpoint_refs": ["mutating.write.write"],
                "input_schema": {"type": "object", "additionalProperties": True},
                "context_schema": {"type": "object", "additionalProperties": True},
                "effect": "write",
                "stability": "test",
                "handler_ref": f"{__name__}:dispatch_test_sdk_operation",
                "requires_confirmation": True,
            }
        ],
    }


async def dispatch_test_sdk_operation(
    *,
    operation_ref: str,
    request_payload: dict[str, Any],
    context: dict[str, object],
    timeout_s: float | None = None,
) -> dict[str, object]:
    return {
        "operation_ref": operation_ref,
        "request_payload": dict(request_payload),
        "context": dict(context),
        "timeout_s": timeout_s,
    }


@pytest.mark.asyncio
async def test_skill_sdk_operation_runner_dispatches_declared_sdk_operation() -> None:
    runner = SkillSdkOperationRunner(
        extra_provider_refs=(_TEST_PROVIDER_REF,),
        include_builtin_providers=False,
    )

    receipt = await runner.run(
        SkillSdkOperationRunRequest(
            operation_ref="test_sdk.echo",
            request_payload={"message": "hello"},
            context={"workspace_root": "/tmp/workspace"},
            timeout_s=3.0,
        )
    )

    assert receipt.succeeded is True
    assert receipt.catalog_contract == "aware.sdk_operation_catalog.v0"
    assert receipt.operation_ref == "test_sdk.echo"
    assert receipt.sdk_name == "test_sdk"
    assert receipt.operation_name == "echo"
    assert receipt.effect == "read"
    assert receipt.result == {
        "operation_ref": "test_sdk.echo",
        "request_payload": {"message": "hello"},
        "context": {"workspace_root": "/tmp/workspace"},
        "timeout_s": 3.0,
    }
    assert receipt.evidence["boundary"] == "aware_skill_sdk.sdk_operation_runner"
    assert receipt.evidence["endpoint_refs"] == ["test.echo.echo"]


@pytest.mark.asyncio
async def test_skill_sdk_operation_runner_accepts_materialized_sdk_target() -> None:
    runner = SkillSdkOperationRunner(
        extra_provider_refs=(_TEST_PROVIDER_REF,),
        include_builtin_providers=False,
    )

    receipt = await runner.run(
        SkillSdkOperationRunRequest(
            target=SkillSdkOperationTarget(
                operation_ref="test_sdk.echo",
                sdk_package_name="aware-test-sdk",
                sdk_name="test_sdk",
                sdk_package_revision_id="revision-001",
                catalog_hash_sha256="a" * 64,
                catalog_schema_version=1,
            ),
            request_payload={"message": "hello"},
        )
    )

    assert receipt.succeeded is True
    assert receipt.target is not None
    assert receipt.target.sdk_package_name == "aware-test-sdk"
    assert receipt.catalog_package_name == "aware-test-sdk"
    assert receipt.catalog_provider_ref == _TEST_PROVIDER_REF
    assert receipt.catalog_hash_sha256 == "a" * 64
    assert receipt.result_hash_sha256 is not None
    assert receipt.evidence["catalog_package_name"] == "aware-test-sdk"
    assert receipt.evidence["catalog_hash_sha256"] == "a" * 64
    assert receipt.evidence["effect_policy"] == {
        "effect": "read",
        "requires_confirmation": False,
        "allow_mutation": False,
    }
    assert receipt.evidence["target"] == {
        "operation_ref": "test_sdk.echo",
        "sdk_package_name": "aware-test-sdk",
        "sdk_name": "test_sdk",
        "sdk_package_revision_id": "revision-001",
        "catalog_hash_sha256": "a" * 64,
        "catalog_schema_version": 1,
        "runtime": "python",
    }


@pytest.mark.asyncio
async def test_skill_sdk_operation_runner_rejects_target_package_mismatch() -> None:
    runner = SkillSdkOperationRunner(
        extra_provider_refs=(_TEST_PROVIDER_REF,),
        include_builtin_providers=False,
    )

    with pytest.raises(SkillSdkError, match="sdk_package_name"):
        await runner.run(
            SkillSdkOperationRunRequest(
                target=SkillSdkOperationTarget(
                    operation_ref="test_sdk.echo",
                    sdk_package_name="wrong-sdk",
                ),
            )
        )


@pytest.mark.asyncio
async def test_skill_sdk_operation_runner_rejects_target_ref_mismatch() -> None:
    runner = SkillSdkOperationRunner(
        extra_provider_refs=(_TEST_PROVIDER_REF,),
        include_builtin_providers=False,
    )

    with pytest.raises(SkillSdkError, match="operation_ref must match"):
        await runner.run(
            SkillSdkOperationRunRequest(
                operation_ref="test_sdk.other",
                target=SkillSdkOperationTarget(
                    operation_ref="test_sdk.echo",
                    sdk_package_name="aware-test-sdk",
                ),
            )
        )


@pytest.mark.asyncio
async def test_skill_sdk_operation_runner_requires_target_package_name() -> None:
    runner = SkillSdkOperationRunner(
        extra_provider_refs=(_TEST_PROVIDER_REF,),
        include_builtin_providers=False,
    )

    with pytest.raises(SkillSdkError, match="target.sdk_package_name"):
        await runner.run(
            SkillSdkOperationRunRequest(
                target=SkillSdkOperationTarget(operation_ref="test_sdk.echo"),
            )
        )


@pytest.mark.asyncio
async def test_skill_sdk_operation_runner_preserves_catalog_mutation_guard() -> None:
    runner = SkillSdkOperationRunner(
        extra_provider_refs=(_MUTATING_PROVIDER_REF,),
        include_builtin_providers=False,
    )

    with pytest.raises(SkillSdkError, match="may mutate state"):
        await runner.run(
            SkillSdkOperationRunRequest(
                operation_ref="mutating_sdk.write",
                request_payload={"value": 1},
            )
        )


def test_skill_sdk_operation_runner_does_not_import_skill_runtime_or_service() -> None:
    source = sys.modules[SkillSdkOperationRunner.__module__].__file__
    assert source is not None
    text = Path(source).read_text(encoding="utf-8")

    forbidden_imports = (
        "from aware_skill ",
        "from aware_skill.",
        "import aware_skill\n",
        "from aware_skill_service ",
        "from aware_skill_service.",
        "import aware_skill_service\n",
        "aware_skill_service_protocol",
    )
    offenders = [item for item in forbidden_imports if item in text]
    assert offenders == []
