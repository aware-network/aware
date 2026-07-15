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

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package import CodePackage
    from aware_experience_ontology.environment.environment_experience import EnvironmentExperience
    from aware_experience_ontology.environment.experience_package_api_package import ExperiencePackageApiPackage
    from aware_experience_ontology.environment.experience_package_attention_package import (
        ExperiencePackageAttentionPackage,
    )
    from aware_experience_ontology.environment.experience_package_dependency import ExperiencePackageDependency
    from aware_experience_ontology.environment.experience_package_language_package import (
        ExperiencePackageLanguagePackage,
    )
    from aware_experience_ontology.environment.experience_package_sdk_package import ExperiencePackageSdkPackage


class ExperiencePackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    attention_packages: list[ExperiencePackageAttentionPackage] = Field(default_factory=list)
    api_packages: list[ExperiencePackageApiPackage] = Field(default_factory=list)
    environment_experience: EnvironmentExperience | None = Field(default=None)
    experience_package_dependencies: list[ExperiencePackageDependency] = Field(default_factory=list)
    language_packages: list[ExperiencePackageLanguagePackage] = Field(default_factory=list)
    sdk_packages: list[ExperiencePackageSdkPackage] = Field(default_factory=list)

    # Attributes
    name: str

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for ExperiencePackage.source_code_package"
    )
    environment_experience_id: UUID = Field(description="Foreign key for ExperiencePackage.environment_experience")

    @classmethod
    async def build(
        cls, name: str, environment_experience_id: UUID, source_code_package_id: UUID | None = None
    ) -> ExperiencePackage:
        """
        Create the canonical Experience-owned package root over an existing `EnvironmentExperience`.

        Contract:
        - Identity is keyed by Experience package `name`.
        - `ExperiencePackage` is the package/public root over an existing canonical
          `EnvironmentExperience`.
        - `environment_experience_id` must point at the canonical EnvironmentExperience stable id
          for this package root.
        - `source_code_package_id` is the explicit raw-source provenance link for this semantic
          leaf package.
        - Workspace will later mount `ExperiencePackage`, not raw `EnvironmentExperience`.
        """

        payload = {
            "name": name,
            "environment_experience_id": environment_experience_id,
            "source_code_package_id": source_code_package_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperiencePackage):
            return value
        return ExperiencePackage.validate_invocation_value(value)

    async def attach_attention_package(
        self, attention_package_id: UUID, description: str | None = None
    ) -> ExperiencePackageAttentionPackage:
        """
        Attach one Attention package dependency to this ExperiencePackage.

        Contract:
        - This is package-level dependency truth for Experience-authored layout/section bindings.
        - ProjectionExperienceSectionGraphBinding may target Attention layout sections only through
          committed package dependency truth, not through runtime guesses.
        - The dependency is relational truth; runtime mutation still goes through Attention services.
        """

        payload = {"attention_package_id": attention_package_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="attach_attention_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.experience_package_attention_package import (
            ExperiencePackageAttentionPackage,
        )

        if isinstance(value, ExperiencePackageAttentionPackage):
            return value
        return ExperiencePackageAttentionPackage.validate_invocation_value(value)

    async def attach_api_package(
        self, api_package_id: UUID, description: str | None = None
    ) -> ExperiencePackageApiPackage:
        """
        Attach one API package dependency to this ExperiencePackage.

        Contract:
        - Experience owns ProjectionExperienceView action capability truth.
        - API package dependencies declare which API packages those view actions may target.
        - Pane/interface packages must not become the product owner of API capability truth.
        """

        payload = {"api_package_id": api_package_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="attach_api_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.experience_package_api_package import ExperiencePackageApiPackage

        if isinstance(value, ExperiencePackageApiPackage):
            return value
        return ExperiencePackageApiPackage.validate_invocation_value(value)

    async def attach_experience_package_dependency(
        self,
        target_experience_package_id: UUID,
        target_package_name: str,
        target_experience_package_object_instance_graph_commit_id: UUID | None = None,
        target_version_number: int | None = None,
        expected_hash_sha256: str | None = None,
        description: str | None = None,
    ) -> ExperiencePackageDependency:
        """
        Attach one Experience package dependency to this ExperiencePackage.

        Contract:
        - This is package-level dependency truth for cross-Experience profile composition.
        - View/event transitions may reference source views or target bindings from another
          Experience package only when backed by this dependency closure.
        - `target_version_number` is selector/compatibility metadata.
        - `target_experience_package_object_instance_graph_commit_id`, when present, pins
          exact semantic package truth resolved through WorkspaceRevision/Hub evidence.
        """

        payload = {
            "target_experience_package_id": target_experience_package_id,
            "target_package_name": target_package_name,
            "target_experience_package_object_instance_graph_commit_id": target_experience_package_object_instance_graph_commit_id,
            "target_version_number": target_version_number,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_instance(
            orm_model=self, function_name="attach_experience_package_dependency", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.experience_package_dependency import ExperiencePackageDependency

        if isinstance(value, ExperiencePackageDependency):
            return value
        return ExperiencePackageDependency.validate_invocation_value(value)

    async def attach_language_package(
        self,
        code_package_id: UUID,
        package_name: str,
        language: CodeLanguage,
        import_root: str,
        manifest_relative_path: str,
        package_root: str = ".",
        sources_root: str | None = None,
        role: str = "view_model_package",
        output_key: str = "experience.language_contract.generated_code_packages",
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
    ) -> ExperiencePackageLanguagePackage:
        """
        Attach one Experience-owned generated language package.

        Contract:
        - Experience packages own their generated view-model/runtime language package truth.
        - Identity is keyed by the attached generated CodePackage.
        - Consumers must not infer Experience language packages from local targets or filesystem
          layout; they must read this package relationship.
        - The CodePackage remains the code-content owner. This edge is semantic package
          ownership/provenance, not a parallel artifact rail.
        """

        payload = {
            "code_package_id": code_package_id,
            "package_name": package_name,
            "language": language,
            "import_root": import_root,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "role": role,
            "output_key": output_key,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_language_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.experience_package_language_package import (
            ExperiencePackageLanguagePackage,
        )

        if isinstance(value, ExperiencePackageLanguagePackage):
            return value
        return ExperiencePackageLanguagePackage.validate_invocation_value(value)

    async def attach_sdk_package(
        self, sdk_package_id: UUID, description: str | None = None
    ) -> ExperiencePackageSdkPackage:
        """
        Attach one SDK package dependency to this ExperiencePackage.

        Contract:
        - Experience owns ProjectionExperienceView action capability truth.
        - SDK package dependencies declare which SDK packages those view actions may target.
        - SDK invocation remains a boundary adapter, not pane-owned product semantics.
        """

        payload = {"sdk_package_id": sdk_package_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="attach_sdk_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.experience_package_sdk_package import ExperiencePackageSdkPackage

        if isinstance(value, ExperiencePackageSdkPackage):
            return value
        return ExperiencePackageSdkPackage.validate_invocation_value(value)


class ExperiencePackageBuildInput(BaseModel):
    name: str
    environment_experience_id: UUID
    source_code_package_id: UUID | None = Field(default=None)


class ExperiencePackageBuildOutput(BaseModel):
    value: ExperiencePackage


class ExperiencePackageAttachAttentionPackageInput(BaseModel):
    attention_package_id: UUID
    description: str | None = Field(default=None)


class ExperiencePackageAttachAttentionPackageOutput(BaseModel):
    value: ExperiencePackageAttentionPackage


class ExperiencePackageAttachApiPackageInput(BaseModel):
    api_package_id: UUID
    description: str | None = Field(default=None)


class ExperiencePackageAttachApiPackageOutput(BaseModel):
    value: ExperiencePackageApiPackage


class ExperiencePackageAttachExperiencePackageDependencyInput(BaseModel):
    target_experience_package_id: UUID
    target_package_name: str
    target_experience_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class ExperiencePackageAttachExperiencePackageDependencyOutput(BaseModel):
    value: ExperiencePackageDependency


class ExperiencePackageAttachLanguagePackageInput(BaseModel):
    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    import_root: str
    manifest_relative_path: str
    package_root: str = Field(default=".")
    sources_root: str | None = Field(default=None)
    role: str = Field(default="view_model_package")
    output_key: str = Field(default="experience.language_contract.generated_code_packages")
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)


class ExperiencePackageAttachLanguagePackageOutput(BaseModel):
    value: ExperiencePackageLanguagePackage


class ExperiencePackageAttachSdkPackageInput(BaseModel):
    sdk_package_id: UUID
    description: str | None = Field(default=None)


class ExperiencePackageAttachSdkPackageOutput(BaseModel):
    value: ExperiencePackageSdkPackage


FUNCTIONS = {
    "ExperiencePackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Experience-owned package root over an existing `EnvironmentExperience`.\n\nContract:\n- Identity is keyed by Experience package `name`.\n- `ExperiencePackage` is the package/public root over an existing canonical\n  `EnvironmentExperience`.\n- `environment_experience_id` must point at the canonical EnvironmentExperience stable id\n  for this package root.\n- `source_code_package_id` is the explicit raw-source provenance link for this semantic\n  leaf package.\n- Workspace will later mount `ExperiencePackage`, not raw `EnvironmentExperience`.",
                "is_constructor": True,
            },
            "input": ExperiencePackageBuildInput,
            "output": ExperiencePackageBuildOutput,
        },
        "attach_attention_package": {
            "canonical": {
                "name": "attach_attention_package",
                "description": "Attach one Attention package dependency to this ExperiencePackage.\n\nContract:\n- This is package-level dependency truth for Experience-authored layout/section bindings.\n- ProjectionExperienceSectionGraphBinding may target Attention layout sections only through\n  committed package dependency truth, not through runtime guesses.\n- The dependency is relational truth; runtime mutation still goes through Attention services.",
                "is_constructor": False,
            },
            "input": ExperiencePackageAttachAttentionPackageInput,
            "output": ExperiencePackageAttachAttentionPackageOutput,
        },
        "attach_api_package": {
            "canonical": {
                "name": "attach_api_package",
                "description": "Attach one API package dependency to this ExperiencePackage.\n\nContract:\n- Experience owns ProjectionExperienceView action capability truth.\n- API package dependencies declare which API packages those view actions may target.\n- Pane/interface packages must not become the product owner of API capability truth.",
                "is_constructor": False,
            },
            "input": ExperiencePackageAttachApiPackageInput,
            "output": ExperiencePackageAttachApiPackageOutput,
        },
        "attach_experience_package_dependency": {
            "canonical": {
                "name": "attach_experience_package_dependency",
                "description": "Attach one Experience package dependency to this ExperiencePackage.\n\nContract:\n- This is package-level dependency truth for cross-Experience profile composition.\n- View/event transitions may reference source views or target bindings from another\n  Experience package only when backed by this dependency closure.\n- `target_version_number` is selector/compatibility metadata.\n- `target_experience_package_object_instance_graph_commit_id`, when present, pins\n  exact semantic package truth resolved through WorkspaceRevision/Hub evidence.",
                "is_constructor": False,
            },
            "input": ExperiencePackageAttachExperiencePackageDependencyInput,
            "output": ExperiencePackageAttachExperiencePackageDependencyOutput,
        },
        "attach_language_package": {
            "canonical": {
                "name": "attach_language_package",
                "description": "Attach one Experience-owned generated language package.\n\nContract:\n- Experience packages own their generated view-model/runtime language package truth.\n- Identity is keyed by the attached generated CodePackage.\n- Consumers must not infer Experience language packages from local targets or filesystem\n  layout; they must read this package relationship.\n- The CodePackage remains the code-content owner. This edge is semantic package\n  ownership/provenance, not a parallel artifact rail.",
                "is_constructor": False,
            },
            "input": ExperiencePackageAttachLanguagePackageInput,
            "output": ExperiencePackageAttachLanguagePackageOutput,
        },
        "attach_sdk_package": {
            "canonical": {
                "name": "attach_sdk_package",
                "description": "Attach one SDK package dependency to this ExperiencePackage.\n\nContract:\n- Experience owns ProjectionExperienceView action capability truth.\n- SDK package dependencies declare which SDK packages those view actions may target.\n- SDK invocation remains a boundary adapter, not pane-owned product semantics.",
                "is_constructor": False,
            },
            "input": ExperiencePackageAttachSdkPackageInput,
            "output": ExperiencePackageAttachSdkPackageOutput,
        },
    },
}

__all__ = [
    "ExperiencePackage",
    "ExperiencePackageBuildInput",
    "ExperiencePackageBuildOutput",
    "ExperiencePackageAttachAttentionPackageInput",
    "ExperiencePackageAttachAttentionPackageOutput",
    "ExperiencePackageAttachApiPackageInput",
    "ExperiencePackageAttachApiPackageOutput",
    "ExperiencePackageAttachExperiencePackageDependencyInput",
    "ExperiencePackageAttachExperiencePackageDependencyOutput",
    "ExperiencePackageAttachLanguagePackageInput",
    "ExperiencePackageAttachLanguagePackageOutput",
    "ExperiencePackageAttachSdkPackageInput",
    "ExperiencePackageAttachSdkPackageOutput",
    "FUNCTIONS",
]
