from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package_enums import CodePackageArtifactStatus
from aware_code_ontology.code.code_plan import CodePackagePathRole

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology.code.code import Code
    from aware_code_ontology.code.code_plan import CodeContentPlan
    from aware_code_ontology.code.code_plan import CodePackageDelta
    from aware_code_ontology.code.code_plan import CodePackageDeltaApplyResult
    from aware_code_ontology.code.code_plan import CodePackageDeltaProduction
    from aware_code_ontology.code.code_test_framework import CodeTestFramework
    from aware_code_ontology.package.code_package_artifact import CodePackageArtifact
    from aware_code_ontology.package.code_package_code import CodePackageCode
    from aware_code_ontology.package.code_package_delta_producer import CodePackageDeltaProducer
    from aware_code_ontology.package.code_package_test import CodePackageTest
    from aware_code_ontology.package.code_package_test_framework import CodePackageTestFramework


class CodePackage(ORMModel):
    # Relationships
    delta_producers: list[CodePackageDeltaProducer] = Field(default_factory=list)
    artifacts: list[CodePackageArtifact] = Field(default_factory=list)
    tests: list[CodePackageTest] = Field(default_factory=list)

    # Attributes
    manifest_relative_path: str
    package_name: str
    package_root: str
    sources_root: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    language: CodeLanguage
    surface: str | None = Field(default=None)

    # Foreign Keys
    code_package_config_id: UUID = Field(description="Foreign key for CodePackageConfig.packages")

    # Edges
    code_package_codes: list[CodePackageCode] = Field(
        default_factory=list, description="Edge association helper for codes"
    )
    code_package_test_frameworks: list[CodePackageTestFramework] = Field(
        default_factory=list, description="Edge association helper for test_frameworks"
    )

    @property
    def codes(self) -> list[Code]:
        return [edge.code for edge in self.code_package_codes if edge.code is not None]

    @property
    def test_frameworks(self) -> list[CodeTestFramework]:
        return [
            edge.code_test_framework
            for edge in self.code_package_test_frameworks
            if edge.code_test_framework is not None
        ]

    async def create_code(
        self,
        relative_path: str,
        plan: CodeContentPlan,
        path_role: CodePackagePathRole = CodePackagePathRole.authored_source,
        delta_production: CodePackageDeltaProduction | None = None,
    ) -> CodePackageCode:
        """Create package-owned Code under this CodePackage from a canonical content plan."""

        payload = {
            "relative_path": relative_path,
            "plan": plan,
            "path_role": path_role,
            "delta_production": delta_production,
        }
        result = await invoke_instance(orm_model=self, function_name="create_code", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_code import CodePackageCode

        if isinstance(value, CodePackageCode):
            return value
        return CodePackageCode.validate_invocation_value(value)

    async def upsert_delta_producer(
        self,
        provider_key: str,
        producer_key: str,
        producer_kind: str | None = None,
        provider_payload: JsonObject | None = None,
    ) -> CodePackageDeltaProducer:
        """
        Upsert one package-local raw delta producer identity.

        This stores generic producer identity for routing/blame only. Code does
        not interpret provider payloads or semantic materialization truth.
        """

        payload = {
            "provider_key": provider_key,
            "producer_key": producer_key,
            "producer_kind": producer_kind,
            "provider_payload": provider_payload,
        }
        result = await invoke_instance(orm_model=self, function_name="upsert_delta_producer", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_delta_producer import CodePackageDeltaProducer

        if isinstance(value, CodePackageDeltaProducer):
            return value
        return CodePackageDeltaProducer.validate_invocation_value(value)

    async def attach_artifact(
        self,
        output_key: str,
        artifact_key: str,
        status: CodePackageArtifactStatus = CodePackageArtifactStatus.available,
        artifact_family: str | None = None,
        artifact_role: str | None = None,
        required_for: list[str] = [],
        producer_key: str | None = None,
        producer_kind: str | None = None,
        materialization_index: int | None = None,
        source_code_package_id: UUID | None = None,
        source_object_instance_graph_commit_id: UUID | None = None,
        input_code_package_id: UUID | None = None,
        input_object_instance_graph_commit_id: UUID | None = None,
        digest: str | None = None,
        relative_path: str | None = None,
        uri: str | None = None,
        media_type: str | None = None,
        runtime_contract_version: str | None = None,
        provider_payload: JsonObject | None = None,
        receipt_payload: JsonObject | None = None,
        error: str | None = None,
    ) -> CodePackageArtifact:
        """
        Attach one package-owned artifact evidence row.

        Contract:
        - This is the package output evidence lane.
        - WorkspaceRevision should hydrate artifacts through the pinned
          WorkspaceRevisionCodePackage commit instead of owning per-artifact
          pointers.
        """

        payload = {
            "output_key": output_key,
            "artifact_key": artifact_key,
            "status": status,
            "artifact_family": artifact_family,
            "artifact_role": artifact_role,
            "required_for": required_for,
            "producer_key": producer_key,
            "producer_kind": producer_kind,
            "materialization_index": materialization_index,
            "source_code_package_id": source_code_package_id,
            "source_object_instance_graph_commit_id": source_object_instance_graph_commit_id,
            "input_code_package_id": input_code_package_id,
            "input_object_instance_graph_commit_id": input_object_instance_graph_commit_id,
            "digest": digest,
            "relative_path": relative_path,
            "uri": uri,
            "media_type": media_type,
            "runtime_contract_version": runtime_contract_version,
            "provider_payload": provider_payload,
            "receipt_payload": receipt_payload,
            "error": error,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_artifact", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_artifact import CodePackageArtifact

        if isinstance(value, CodePackageArtifact):
            return value
        return CodePackageArtifact.validate_invocation_value(value)

    async def delete_code(self, relative_path: str) -> bool:
        """Delete one package-owned code attachment by package-relative path."""

        payload = {"relative_path": relative_path}
        result = await invoke_instance(orm_model=self, function_name="delete_code", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value

    async def upsert_code(
        self,
        relative_path: str,
        plan: CodeContentPlan,
        path_role: CodePackagePathRole = CodePackagePathRole.authored_source,
        delta_production: CodePackageDeltaProduction | None = None,
    ) -> CodePackageCode:
        """Create or replace package-owned Code under this CodePackage from a canonical content plan."""

        payload = {
            "relative_path": relative_path,
            "plan": plan,
            "path_role": path_role,
            "delta_production": delta_production,
        }
        result = await invoke_instance(orm_model=self, function_name="upsert_code", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_code import CodePackageCode

        if isinstance(value, CodePackageCode):
            return value
        return CodePackageCode.validate_invocation_value(value)

    async def upsert_code_from_text(
        self, relative_path: str, content_text: str, language: CodeLanguage | None = None
    ) -> CodePackageCode:
        """Compatibility wrapper that parses raw text and delegates to `upsert_code(...)`."""

        payload = {"relative_path": relative_path, "content_text": content_text, "language": language}
        result = await invoke_instance(orm_model=self, function_name="upsert_code_from_text", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_code import CodePackageCode

        if isinstance(value, CodePackageCode):
            return value
        return CodePackageCode.validate_invocation_value(value)

    async def upsert_codes_from_text(
        self, relative_paths: list[str], content_texts: list[str], language: CodeLanguage | None = None
    ) -> None:
        """
        Batch compatibility wrapper that parses raw text and upserts package-owned Code entries in one
        invocation.

        Contract:
        - `relative_paths` and `content_texts` must have equal lengths.
        - Each `relative_path` must be unique within the request.
        - This preserves the public `CodePackage` mutation boundary while reducing repeated invocation
        overhead.
        """

        payload = {"relative_paths": relative_paths, "content_texts": content_texts, "language": language}
        await invoke_instance(orm_model=self, function_name="upsert_codes_from_text", payload=payload)
        return None

    async def apply_delta(self, delta: CodePackageDelta) -> CodePackageDeltaApplyResult:
        """
        Apply a canonical CodePackageDelta through the package-owned mutation boundary.

        Contract:
        - Create/update entries upsert package-owned Code.
        - Delete entries remove package-owned Code by package-relative path.
        - This is the shared Code-owned IR consumed by Workspace commit and semantic owners.
        """

        payload = {"delta": delta}
        result = await invoke_instance(orm_model=self, function_name="apply_delta", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.code.code_plan import CodePackageDeltaApplyResult

        if isinstance(value, CodePackageDeltaApplyResult):
            return value
        return CodePackageDeltaApplyResult.model_validate(value)

    async def sync_tests(self, manifest_text: str | None = None) -> None:
        """
        Discover and attach package-owned test framework/test inventory from language plugin truth.

        Contract:
        - Framework declarations are language-owned (for example pyproject.toml or pubspec.yaml).
        - Test units attach to existing Code/CodeSection truth already upserted under this CodePackage.
        - This is idempotent inventory sync only; execution receipts materialize later under
        CodePackageTest.runs.
        """

        payload = {"manifest_text": manifest_text}
        await invoke_instance(orm_model=self, function_name="sync_tests", payload=payload)
        return None

    async def attach_test_framework(
        self, framework_id: UUID, declaration_kind: str = "unknown", declaration_ref: str | None = None
    ) -> CodePackageTestFramework:
        """Attach an existing CodeTestFramework to this package with declaration provenance."""

        payload = {
            "framework_id": framework_id,
            "declaration_kind": declaration_kind,
            "declaration_ref": declaration_ref,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_test_framework", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_test_framework import CodePackageTestFramework

        if isinstance(value, CodePackageTestFramework):
            return value
        return CodePackageTestFramework.validate_invocation_value(value)

    async def attach_test(self, code_test_id: UUID, relative_path: str) -> CodePackageTest:
        """Attach an existing CodeTest to this package inventory."""

        payload = {"code_test_id": code_test_id, "relative_path": relative_path}
        result = await invoke_instance(orm_model=self, function_name="attach_test", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_test import CodePackageTest

        if isinstance(value, CodePackageTest):
            return value
        return CodePackageTest.validate_invocation_value(value)

    async def create_code_from_text(
        self, relative_path: str, content_text: str, language: CodeLanguage | None = None
    ) -> CodePackageCode:
        """Compatibility wrapper that parses raw text and delegates to `create_code(...)`."""

        payload = {"relative_path": relative_path, "content_text": content_text, "language": language}
        result = await invoke_instance(orm_model=self, function_name="create_code_from_text", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_code import CodePackageCode

        if isinstance(value, CodePackageCode):
            return value
        return CodePackageCode.validate_invocation_value(value)

    @classmethod
    async def build_via_code_package_config(
        cls,
        code_package_config_id: UUID,
        package_name: str,
        language: CodeLanguage,
        manifest_relative_path: str,
        package_root: str,
        sources_root: str | None = None,
        fqn_prefix: str | None = None,
        surface: str | None = None,
    ) -> CodePackage:
        """
        Create a deterministic CodePackage under a CodePackageConfig.

        Contract:
        - Parent CodePackageConfig context is propagated by constructor lowering.
        - Identity is config-scoped by `(code_package_config_id, package_name, language)`.
        - `manifest_relative_path`, `package_root`, and `sources_root` are package layout payload.
        - Semantic package kind and manifest-kind truth live on CodePackageConfig.
        """

        payload = {
            "code_package_config_id": code_package_config_id,
            "package_name": package_name,
            "language": language,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "fqn_prefix": fqn_prefix,
            "surface": surface,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_package_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackage):
            return value
        return CodePackage.validate_invocation_value(value)


class CodePackageCreateCodeInput(BaseModel):
    relative_path: str
    plan: CodeContentPlan
    path_role: CodePackagePathRole = Field(default=CodePackagePathRole.authored_source)
    delta_production: CodePackageDeltaProduction | None = Field(default=None)


class CodePackageCreateCodeOutput(BaseModel):
    value: CodePackageCode


class CodePackageUpsertDeltaProducerInput(BaseModel):
    provider_key: str
    producer_key: str
    producer_kind: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)


class CodePackageUpsertDeltaProducerOutput(BaseModel):
    value: CodePackageDeltaProducer


class CodePackageAttachArtifactInput(BaseModel):
    output_key: str
    artifact_key: str
    status: CodePackageArtifactStatus = Field(default=CodePackageArtifactStatus.available)
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    producer_key: str | None = Field(default=None)
    producer_kind: str | None = Field(default=None)
    materialization_index: int | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    source_object_instance_graph_commit_id: UUID | None = Field(default=None)
    input_code_package_id: UUID | None = Field(default=None)
    input_object_instance_graph_commit_id: UUID | None = Field(default=None)
    digest: str | None = Field(default=None)
    relative_path: str | None = Field(default=None)
    uri: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)
    receipt_payload: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)


class CodePackageAttachArtifactOutput(BaseModel):
    value: CodePackageArtifact


class CodePackageDeleteCodeInput(BaseModel):
    relative_path: str


class CodePackageDeleteCodeOutput(BaseModel):
    value: bool


class CodePackageUpsertCodeInput(BaseModel):
    relative_path: str
    plan: CodeContentPlan
    path_role: CodePackagePathRole = Field(default=CodePackagePathRole.authored_source)
    delta_production: CodePackageDeltaProduction | None = Field(default=None)


class CodePackageUpsertCodeOutput(BaseModel):
    value: CodePackageCode


class CodePackageUpsertCodeFromTextInput(BaseModel):
    relative_path: str
    content_text: str
    language: CodeLanguage | None = Field(default=None)


class CodePackageUpsertCodeFromTextOutput(BaseModel):
    value: CodePackageCode


class CodePackageUpsertCodesFromTextInput(BaseModel):
    relative_paths: list[str] = Field(default_factory=list)
    content_texts: list[str] = Field(default_factory=list)
    language: CodeLanguage | None = Field(default=None)


class CodePackageUpsertCodesFromTextOutput(BaseModel):
    pass


class CodePackageApplyDeltaInput(BaseModel):
    delta: CodePackageDelta


class CodePackageApplyDeltaOutput(BaseModel):
    value: CodePackageDeltaApplyResult


class CodePackageSyncTestsInput(BaseModel):
    manifest_text: str | None = Field(default=None)


class CodePackageSyncTestsOutput(BaseModel):
    pass


class CodePackageAttachTestFrameworkInput(BaseModel):
    framework_id: UUID
    declaration_kind: str = Field(default="unknown")
    declaration_ref: str | None = Field(default=None)


class CodePackageAttachTestFrameworkOutput(BaseModel):
    value: CodePackageTestFramework


class CodePackageAttachTestInput(BaseModel):
    code_test_id: UUID
    relative_path: str


class CodePackageAttachTestOutput(BaseModel):
    value: CodePackageTest


class CodePackageCreateCodeFromTextInput(BaseModel):
    relative_path: str
    content_text: str
    language: CodeLanguage | None = Field(default=None)


class CodePackageCreateCodeFromTextOutput(BaseModel):
    value: CodePackageCode


class CodePackageBuildViaCodePackageConfigInput(BaseModel):
    code_package_config_id: UUID = Field(description="Foreign key for CodePackageConfig.packages")
    package_name: str
    language: CodeLanguage
    manifest_relative_path: str
    package_root: str
    sources_root: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    surface: str | None = Field(default=None)


class CodePackageBuildViaCodePackageConfigOutput(BaseModel):
    value: CodePackage


FUNCTIONS = {
    "CodePackage": {
        "create_code": {
            "canonical": {
                "name": "create_code",
                "description": "Create package-owned Code under this CodePackage from a canonical content plan.",
                "is_constructor": False,
            },
            "input": CodePackageCreateCodeInput,
            "output": CodePackageCreateCodeOutput,
        },
        "upsert_delta_producer": {
            "canonical": {
                "name": "upsert_delta_producer",
                "description": "Upsert one package-local raw delta producer identity.\n\nThis stores generic producer identity for routing/blame only. Code does\nnot interpret provider payloads or semantic materialization truth.",
                "is_constructor": False,
            },
            "input": CodePackageUpsertDeltaProducerInput,
            "output": CodePackageUpsertDeltaProducerOutput,
        },
        "attach_artifact": {
            "canonical": {
                "name": "attach_artifact",
                "description": "Attach one package-owned artifact evidence row.\n\nContract:\n- This is the package output evidence lane.\n- WorkspaceRevision should hydrate artifacts through the pinned\n  WorkspaceRevisionCodePackage commit instead of owning per-artifact\n  pointers.",
                "is_constructor": False,
            },
            "input": CodePackageAttachArtifactInput,
            "output": CodePackageAttachArtifactOutput,
        },
        "delete_code": {
            "canonical": {
                "name": "delete_code",
                "description": "Delete one package-owned code attachment by package-relative path.",
                "is_constructor": False,
            },
            "input": CodePackageDeleteCodeInput,
            "output": CodePackageDeleteCodeOutput,
        },
        "upsert_code": {
            "canonical": {
                "name": "upsert_code",
                "description": "Create or replace package-owned Code under this CodePackage from a canonical content plan.",
                "is_constructor": False,
            },
            "input": CodePackageUpsertCodeInput,
            "output": CodePackageUpsertCodeOutput,
        },
        "upsert_code_from_text": {
            "canonical": {
                "name": "upsert_code_from_text",
                "description": "Compatibility wrapper that parses raw text and delegates to `upsert_code(...)`.",
                "is_constructor": False,
            },
            "input": CodePackageUpsertCodeFromTextInput,
            "output": CodePackageUpsertCodeFromTextOutput,
        },
        "upsert_codes_from_text": {
            "canonical": {
                "name": "upsert_codes_from_text",
                "description": "Batch compatibility wrapper that parses raw text and upserts package-owned Code entries in one invocation.\n\nContract:\n- `relative_paths` and `content_texts` must have equal lengths.\n- Each `relative_path` must be unique within the request.\n- This preserves the public `CodePackage` mutation boundary while reducing repeated invocation overhead.",
                "is_constructor": False,
            },
            "input": CodePackageUpsertCodesFromTextInput,
            "output": CodePackageUpsertCodesFromTextOutput,
        },
        "apply_delta": {
            "canonical": {
                "name": "apply_delta",
                "description": "Apply a canonical CodePackageDelta through the package-owned mutation boundary.\n\nContract:\n- Create/update entries upsert package-owned Code.\n- Delete entries remove package-owned Code by package-relative path.\n- This is the shared Code-owned IR consumed by Workspace commit and semantic owners.",
                "is_constructor": False,
            },
            "input": CodePackageApplyDeltaInput,
            "output": CodePackageApplyDeltaOutput,
        },
        "sync_tests": {
            "canonical": {
                "name": "sync_tests",
                "description": "Discover and attach package-owned test framework/test inventory from language plugin truth.\n\nContract:\n- Framework declarations are language-owned (for example pyproject.toml or pubspec.yaml).\n- Test units attach to existing Code/CodeSection truth already upserted under this CodePackage.\n- This is idempotent inventory sync only; execution receipts materialize later under CodePackageTest.runs.",
                "is_constructor": False,
            },
            "input": CodePackageSyncTestsInput,
            "output": CodePackageSyncTestsOutput,
        },
        "attach_test_framework": {
            "canonical": {
                "name": "attach_test_framework",
                "description": "Attach an existing CodeTestFramework to this package with declaration provenance.",
                "is_constructor": False,
            },
            "input": CodePackageAttachTestFrameworkInput,
            "output": CodePackageAttachTestFrameworkOutput,
        },
        "attach_test": {
            "canonical": {
                "name": "attach_test",
                "description": "Attach an existing CodeTest to this package inventory.",
                "is_constructor": False,
            },
            "input": CodePackageAttachTestInput,
            "output": CodePackageAttachTestOutput,
        },
        "create_code_from_text": {
            "canonical": {
                "name": "create_code_from_text",
                "description": "Compatibility wrapper that parses raw text and delegates to `create_code(...)`.",
                "is_constructor": False,
            },
            "input": CodePackageCreateCodeFromTextInput,
            "output": CodePackageCreateCodeFromTextOutput,
        },
        "build_via_code_package_config": {
            "canonical": {
                "name": "build_via_code_package_config",
                "description": "Create a deterministic CodePackage under a CodePackageConfig.\n\nContract:\n- Parent CodePackageConfig context is propagated by constructor lowering.\n- Identity is config-scoped by `(code_package_config_id, package_name, language)`.\n- `manifest_relative_path`, `package_root`, and `sources_root` are package layout payload.\n- Semantic package kind and manifest-kind truth live on CodePackageConfig.",
                "is_constructor": True,
            },
            "input": CodePackageBuildViaCodePackageConfigInput,
            "output": CodePackageBuildViaCodePackageConfigOutput,
        },
    },
}

__all__ = [
    "CodePackage",
    "CodePackageCreateCodeInput",
    "CodePackageCreateCodeOutput",
    "CodePackageUpsertDeltaProducerInput",
    "CodePackageUpsertDeltaProducerOutput",
    "CodePackageAttachArtifactInput",
    "CodePackageAttachArtifactOutput",
    "CodePackageDeleteCodeInput",
    "CodePackageDeleteCodeOutput",
    "CodePackageUpsertCodeInput",
    "CodePackageUpsertCodeOutput",
    "CodePackageUpsertCodeFromTextInput",
    "CodePackageUpsertCodeFromTextOutput",
    "CodePackageUpsertCodesFromTextInput",
    "CodePackageUpsertCodesFromTextOutput",
    "CodePackageApplyDeltaInput",
    "CodePackageApplyDeltaOutput",
    "CodePackageSyncTestsInput",
    "CodePackageSyncTestsOutput",
    "CodePackageAttachTestFrameworkInput",
    "CodePackageAttachTestFrameworkOutput",
    "CodePackageAttachTestInput",
    "CodePackageAttachTestOutput",
    "CodePackageCreateCodeFromTextInput",
    "CodePackageCreateCodeFromTextOutput",
    "CodePackageBuildViaCodePackageConfigInput",
    "CodePackageBuildViaCodePackageConfigOutput",
    "FUNCTIONS",
]
