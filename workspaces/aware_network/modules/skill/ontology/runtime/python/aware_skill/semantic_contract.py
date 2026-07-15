from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticContract,
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticPackageRoleDescriptor,
    ModuleSemanticSyntaxLaneDescriptor,
)
from aware_code.semantic_capability import SEMANTIC_ANALYSIS_CAPABILITY
from aware_code.semantic_materialization import SEMANTIC_MATERIALIZATION_CAPABILITY
from aware_code.semantic_package.schemas import (
    CapabilityBundleDescriptor,
    CapabilityParticipationDescriptor,
    CapabilityProfileDescriptor,
)
from aware_skill.semantic_scope import SKILL_SEMANTIC_SCOPE_KEY


SKILL_PROVIDER_OWNER = "aware_skill.provider"
SKILL_CONFIG_OWNER = "aware_skill.skill_config"
SKILL_API_OWNER = "aware_skill.api"
SKILL_ENDPOINT_OWNER = "aware_skill.endpoint"
SKILL_STEP_OWNER = "aware_skill.step"

SKILL_SEMANTIC_SCOPE_KEYS = (SKILL_SEMANTIC_SCOPE_KEY,)

SKILL_DIAGNOSTICS_OWNER_SEQUENCE = (
    SKILL_CONFIG_OWNER,
    SKILL_API_OWNER,
    SKILL_ENDPOINT_OWNER,
    SKILL_STEP_OWNER,
)
SKILL_SEMANTIC_TOKENS_OWNER_SEQUENCE = SKILL_DIAGNOSTICS_OWNER_SEQUENCE
SKILL_SEMANTIC_ANALYSIS_OWNER_SEQUENCE = (SKILL_CONFIG_OWNER,)
SKILL_MATERIALIZATION_OWNER_SEQUENCE = (SKILL_PROVIDER_OWNER,)
SKILL_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES = ("skill-ontology",)
SKILL_MATERIALIZATION_REQUIRED_PROJECTIONS = (
    "SkillPackage",
    "ApiPackage",
    "CodePackage",
)

SKILL_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
    )
    for semantic_owner in SKILL_SEMANTIC_ANALYSIS_OWNER_SEQUENCE
)

SKILL_MATERIALIZATION_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
    )
    for semantic_owner in SKILL_MATERIALIZATION_OWNER_SEQUENCE
)

SKILL_DIAGNOSTICS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability="diagnostics",
        semantic_owner=semantic_owner,
    )
    for semantic_owner in SKILL_DIAGNOSTICS_OWNER_SEQUENCE
)

SKILL_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability="semantic_tokens",
        semantic_owner=semantic_owner,
    )
    for semantic_owner in SKILL_SEMANTIC_TOKENS_OWNER_SEQUENCE
)

SKILL_CAPABILITY_PARTICIPATION = (
    *SKILL_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION,
    *SKILL_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    *SKILL_DIAGNOSTICS_CAPABILITY_PARTICIPATION,
    *SKILL_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION,
)

_SKILL_SEMANTIC_ANALYSIS_PRIORITY_BY_OWNER = {
    SKILL_CONFIG_OWNER: 410,
}
_SKILL_SEMANTIC_ANALYSIS_CALLABLE_NAME_BY_OWNER = {
    SKILL_CONFIG_OWNER: "_skill_semantic_analysis_provider",
}

_SKILL_DIAGNOSTICS_PRIORITY_BY_OWNER = {
    SKILL_CONFIG_OWNER: 420,
    SKILL_API_OWNER: 421,
    SKILL_ENDPOINT_OWNER: 422,
    SKILL_STEP_OWNER: 423,
}
_SKILL_DIAGNOSTICS_CALLABLE_NAME_BY_OWNER = {
    SKILL_CONFIG_OWNER: "_skill_config_diagnostics_provider",
    SKILL_API_OWNER: "_skill_api_diagnostics_provider",
    SKILL_ENDPOINT_OWNER: "_skill_endpoint_diagnostics_provider",
    SKILL_STEP_OWNER: "_skill_step_diagnostics_provider",
}

_SKILL_SEMANTIC_TOKENS_PRIORITY_BY_OWNER = {
    SKILL_CONFIG_OWNER: 450,
    SKILL_API_OWNER: 451,
    SKILL_ENDPOINT_OWNER: 452,
    SKILL_STEP_OWNER: 453,
}
_SKILL_SEMANTIC_TOKENS_CALLABLE_NAME_BY_OWNER = {
    SKILL_CONFIG_OWNER: "_skill_config_tokens_provider",
    SKILL_API_OWNER: "_skill_api_tokens_provider",
    SKILL_ENDPOINT_OWNER: "_skill_endpoint_tokens_provider",
    SKILL_STEP_OWNER: "_skill_step_tokens_provider",
}

SKILL_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_name=_SKILL_SEMANTIC_ANALYSIS_CALLABLE_NAME_BY_OWNER[
            semantic_owner
        ],
        required_semantic_scope_keys=SKILL_SEMANTIC_SCOPE_KEYS,
        priority=_SKILL_SEMANTIC_ANALYSIS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in SKILL_SEMANTIC_ANALYSIS_OWNER_SEQUENCE
)

SKILL_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_module="aware_skill.materialization.workspace_provider",
        callable_name="materialize",
        priority=500,
    )
    for semantic_owner in SKILL_MATERIALIZATION_OWNER_SEQUENCE
)

SKILL_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="diagnostics",
        semantic_owner=semantic_owner,
        callable_name=_SKILL_DIAGNOSTICS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        required_semantic_scope_keys=SKILL_SEMANTIC_SCOPE_KEYS,
        priority=_SKILL_DIAGNOSTICS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in SKILL_DIAGNOSTICS_OWNER_SEQUENCE
)

SKILL_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="semantic_tokens",
        semantic_owner=semantic_owner,
        callable_name=_SKILL_SEMANTIC_TOKENS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        priority=_SKILL_SEMANTIC_TOKENS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in SKILL_SEMANTIC_TOKENS_OWNER_SEQUENCE
)

SKILL_CAPABILITY_EXECUTION_POLICY = (
    *SKILL_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY,
    *SKILL_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY,
    *SKILL_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY,
    *SKILL_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY,
)

_SKILL_PROFILE_OWNERS = (
    ("module.aware_skill.skill_config", (SKILL_CONFIG_OWNER,)),
    ("module.aware_skill.api", (SKILL_API_OWNER,)),
    ("module.aware_skill.endpoint", (SKILL_ENDPOINT_OWNER,)),
    ("module.aware_skill.step", (SKILL_STEP_OWNER,)),
)

SKILL_SEMANTIC_ANALYSIS_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        name="module.aware_skill",
        semantic_owners=SKILL_SEMANTIC_ANALYSIS_OWNER_SEQUENCE,
        default_selected=True,
    ),
)

SKILL_DIAGNOSTICS_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name="module.aware_skill",
        semantic_owners=SKILL_DIAGNOSTICS_OWNER_SEQUENCE,
        default_selected=True,
    ),
    *(
        CapabilityProfileDescriptor(
            capability="diagnostics",
            name=name,
            semantic_owners=semantic_owners,
        )
        for name, semantic_owners in _SKILL_PROFILE_OWNERS
    ),
)

SKILL_SEMANTIC_TOKENS_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name="module.aware_skill",
        semantic_owners=SKILL_SEMANTIC_TOKENS_OWNER_SEQUENCE,
        default_selected=True,
    ),
    *(
        CapabilityProfileDescriptor(
            capability="semantic_tokens",
            name=name,
            semantic_owners=semantic_owners,
        )
        for name, semantic_owners in _SKILL_PROFILE_OWNERS
    ),
)

SKILL_CAPABILITY_PROFILES = (
    *SKILL_SEMANTIC_ANALYSIS_CAPABILITY_PROFILES,
    *SKILL_DIAGNOSTICS_CAPABILITY_PROFILES,
    *SKILL_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
)

SKILL_CAPABILITY_BUNDLES = (
    CapabilityBundleDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        name="bundle.authoring",
        profile_names=("module.aware_skill",),
    ),
    CapabilityBundleDescriptor(
        capability="diagnostics",
        name="bundle.authoring",
        profile_names=("module.aware_skill",),
    ),
    CapabilityBundleDescriptor(
        capability="semantic_tokens",
        name="bundle.authoring",
        profile_names=("module.aware_skill",),
    ),
)

SKILL_SYNTAX_LANES = (
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_skill.skill_config",
        semantic_owner=SKILL_CONFIG_OWNER,
        compiler_owner=SKILL_CONFIG_OWNER,
        grammar_rules=("skill_def",),
        semantic_token_types=("keyword", "class"),
        semantic_token_modifiers=("skill",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_skill.api",
        semantic_owner=SKILL_API_OWNER,
        compiler_owner=SKILL_API_OWNER,
        grammar_rules=("skill_api_decl",),
        semantic_token_types=("keyword", "namespace"),
        semantic_token_modifiers=("skill",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_skill.endpoint",
        semantic_owner=SKILL_ENDPOINT_OWNER,
        compiler_owner=SKILL_ENDPOINT_OWNER,
        grammar_rules=("skill_endpoint_def",),
        semantic_token_types=("keyword", "function"),
        semantic_token_modifiers=("skill",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_skill.step",
        semantic_owner=SKILL_STEP_OWNER,
        compiler_owner=SKILL_STEP_OWNER,
        grammar_rules=("skill_step_def",),
        semantic_token_types=("keyword", "number", "function"),
        semantic_token_modifiers=("skill",),
    ),
)

SKILL_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role=SKILL_PROVIDER_OWNER,
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=(
            SEMANTIC_ANALYSIS_CAPABILITY,
            "diagnostics",
            "semantic_tokens",
            SEMANTIC_MATERIALIZATION_CAPABILITY,
        ),
        owns_manifest_kinds=("aware_skill_toml",),
    ),
)

SKILL_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=SKILL_PROVIDER_OWNER,
        manifest_kind="aware_skill_toml",
        filename="aware.skill.toml",
        contract="aware.skill",
        loader_module="aware_skill.manifest.loader",
        loader_name="load_aware_skill_toml_spec",
        package_role=SKILL_PROVIDER_OWNER,
        semantic_package_family="skill",
        semantic_package_kind="skill_package",
        semantic_projection_name="SkillPackage",
        semantic_root_kind="skill_config",
        code_package_surface="runtime",
        workspace_materialization_order=400,
        workspace_materialization_branch="semantic",
        workspace_materialization_commit=True,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=("fqn_prefix", "package_kind"),
        priority=400,
    ),
)

SKILL_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=SKILL_PROVIDER_OWNER,
        runtime_ontology_package_names=(
            SKILL_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        lane_projection_name="SkillPackage",
        required_projection_names=SKILL_MATERIALIZATION_REQUIRED_PROJECTIONS,
        environment_handle="workspace-semantic-materialization",
        include_package_dependency_closure=True,
        priority=400,
    ),
)

AWARE_SKILL_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_skill",
    semantic_scope_keys=SKILL_SEMANTIC_SCOPE_KEYS,
    capability_participation=SKILL_CAPABILITY_PARTICIPATION,
    capability_execution_policy=SKILL_CAPABILITY_EXECUTION_POLICY,
    capability_profiles=SKILL_CAPABILITY_PROFILES,
    capability_bundles=SKILL_CAPABILITY_BUNDLES,
    syntax_lanes=SKILL_SYNTAX_LANES,
    package_roles=SKILL_PACKAGE_ROLES,
    manifest_resolution=SKILL_MANIFEST_RESOLUTION,
    materialization_runtime=SKILL_MATERIALIZATION_RUNTIME,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_SKILL_SEMANTIC_CONTRACT


__all__ = [
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "AWARE_SKILL_SEMANTIC_CONTRACT",
    "SKILL_API_OWNER",
    "SKILL_CAPABILITY_BUNDLES",
    "SKILL_CAPABILITY_EXECUTION_POLICY",
    "SKILL_CAPABILITY_PARTICIPATION",
    "SKILL_CAPABILITY_PROFILES",
    "SKILL_CONFIG_OWNER",
    "SKILL_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY",
    "SKILL_DIAGNOSTICS_CAPABILITY_PARTICIPATION",
    "SKILL_DIAGNOSTICS_CAPABILITY_PROFILES",
    "SKILL_DIAGNOSTICS_OWNER_SEQUENCE",
    "SKILL_ENDPOINT_OWNER",
    "SKILL_MANIFEST_RESOLUTION",
    "SKILL_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY",
    "SKILL_MATERIALIZATION_CAPABILITY_PARTICIPATION",
    "SKILL_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "SKILL_MATERIALIZATION_RUNTIME",
    "SKILL_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "SKILL_MATERIALIZATION_OWNER_SEQUENCE",
    "SKILL_PACKAGE_ROLES",
    "SKILL_PROVIDER_OWNER",
    "SKILL_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY",
    "SKILL_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION",
    "SKILL_SEMANTIC_ANALYSIS_CAPABILITY_PROFILES",
    "SKILL_SEMANTIC_ANALYSIS_OWNER_SEQUENCE",
    "SKILL_SEMANTIC_SCOPE_KEYS",
    "SKILL_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY",
    "SKILL_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION",
    "SKILL_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
    "SKILL_SEMANTIC_TOKENS_OWNER_SEQUENCE",
    "SKILL_STEP_OWNER",
    "SKILL_SYNTAX_LANES",
]
