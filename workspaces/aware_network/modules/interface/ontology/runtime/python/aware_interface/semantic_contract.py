from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticContract,
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticPackageRoleDescriptor,
    ModuleSemanticRuntimeProjectionPackageDescriptor,
    ModuleSemanticSyntaxLaneDescriptor,
)
from aware_code.semantic_materialization import SEMANTIC_MATERIALIZATION_CAPABILITY
from aware_code.semantic_currentness import (
    SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_ENTRYPOINT,
    SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_METADATA_KEY,
    SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_CONTRACT_VERSION,
)
from aware_code.semantic_package.schemas import (
    CapabilityBundleDescriptor,
    CapabilityParticipationDescriptor,
    CapabilityProfileDescriptor,
)
from aware_interface.semantic_scope import INTERFACE_SEMANTIC_SCOPE_KEY


INTERFACE_PROVIDER_OWNER = "aware_interface.provider"
INTERFACE_ROOT_OWNER = "aware_interface.interface"
INTERFACE_API_OWNER = "aware_interface.api"
INTERFACE_WINDOW_OWNER = "aware_interface.window"
INTERFACE_LAYOUT_OWNER = "aware_interface.layout"
INTERFACE_SECTION_OWNER = "aware_interface.section"
INTERFACE_PANE_COMPOSITION_OWNER = "aware_interface.pane_composition"
INTERFACE_MOUNT_OWNER = "aware_interface.mount"
INTERFACE_NARRATIVE_OWNER = "aware_interface.narrative"
INTERFACE_PANE_OWNER = "aware_interface.pane"
INTERFACE_VIEW_OWNER = "aware_interface.view"
INTERFACE_ENDPOINT_OWNER = "aware_interface.endpoint"
INTERFACE_RENDER_COMPONENT_OWNER = "aware_interface.render_component"
INTERFACE_RENDER_COMPONENT_PORT_OWNER = "aware_interface.render_component_port"
INTERFACE_RENDER_COMPONENT_CAPABILITY_OWNER = "aware_interface.render_component_capability"

INTERFACE_SEMANTIC_SCOPE_KEYS = (INTERFACE_SEMANTIC_SCOPE_KEY,)

INTERFACE_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE = (
    INTERFACE_ROOT_OWNER,
    INTERFACE_API_OWNER,
    INTERFACE_WINDOW_OWNER,
    INTERFACE_LAYOUT_OWNER,
    INTERFACE_SECTION_OWNER,
    INTERFACE_PANE_COMPOSITION_OWNER,
    INTERFACE_MOUNT_OWNER,
    INTERFACE_NARRATIVE_OWNER,
)

INTERFACE_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE = (
    INTERFACE_ROOT_OWNER,
    INTERFACE_API_OWNER,
    INTERFACE_WINDOW_OWNER,
    INTERFACE_LAYOUT_OWNER,
    INTERFACE_SECTION_OWNER,
    INTERFACE_PANE_COMPOSITION_OWNER,
    INTERFACE_MOUNT_OWNER,
    INTERFACE_NARRATIVE_OWNER,
)

PANE_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE = (
    INTERFACE_PANE_OWNER,
    INTERFACE_VIEW_OWNER,
    INTERFACE_ENDPOINT_OWNER,
)

PANE_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE = (
    INTERFACE_PANE_OWNER,
    INTERFACE_VIEW_OWNER,
    INTERFACE_ENDPOINT_OWNER,
)

RENDER_COMPONENT_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE = (
    INTERFACE_RENDER_COMPONENT_OWNER,
    INTERFACE_RENDER_COMPONENT_PORT_OWNER,
    INTERFACE_RENDER_COMPONENT_CAPABILITY_OWNER,
)

RENDER_COMPONENT_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE = (
    INTERFACE_RENDER_COMPONENT_OWNER,
    INTERFACE_RENDER_COMPONENT_PORT_OWNER,
    INTERFACE_RENDER_COMPONENT_CAPABILITY_OWNER,
)

INTERFACE_DIAGNOSTICS_OWNER_SEQUENCE = (
    *INTERFACE_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE,
    *PANE_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE,
    *RENDER_COMPONENT_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE,
)

INTERFACE_SEMANTIC_TOKENS_OWNER_SEQUENCE = (
    *INTERFACE_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE,
    *PANE_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE,
    *RENDER_COMPONENT_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE,
)

INTERFACE_MATERIALIZATION_OWNER_SEQUENCE = (INTERFACE_PROVIDER_OWNER,)
INTERFACE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES = ("interface-ontology",)
INTERFACE_MATERIALIZATION_REQUIRED_PROJECTIONS = (
    "AppConfig",
    "AppPackage",
    "InterfaceConfig",
    "InterfacePackage",
    "PanePackage",
    "PaneRenderSpec",
    "ApiPackage",
    "ExperiencePackage",
    "SdkPackage",
    "CodePackage",
)
INTERFACE_MATERIALIZATION_CAPABILITY_METADATA: dict[str, object] = {
    SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_METADATA_KEY: {
        "callable_module": "aware_interface.materialization.currentness_replay",
        "callable_name": (SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_ENTRYPOINT),
        "contract_version": (SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_CONTRACT_VERSION),
    },
}

INTERFACE_MATERIALIZATION_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        metadata=INTERFACE_MATERIALIZATION_CAPABILITY_METADATA,
    )
    for semantic_owner in INTERFACE_MATERIALIZATION_OWNER_SEQUENCE
)

INTERFACE_PACKAGE_CAPABILITY_PARTICIPATION = (
    *tuple(
        CapabilityParticipationDescriptor(
            capability="diagnostics",
            semantic_owner=semantic_owner,
        )
        for semantic_owner in INTERFACE_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE
    ),
    *tuple(
        CapabilityParticipationDescriptor(
            capability="semantic_tokens",
            semantic_owner=semantic_owner,
        )
        for semantic_owner in INTERFACE_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE
    ),
)

PANE_PACKAGE_CAPABILITY_PARTICIPATION = (
    *tuple(
        CapabilityParticipationDescriptor(
            capability="diagnostics",
            semantic_owner=semantic_owner,
        )
        for semantic_owner in PANE_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE
    ),
    *tuple(
        CapabilityParticipationDescriptor(
            capability="semantic_tokens",
            semantic_owner=semantic_owner,
        )
        for semantic_owner in PANE_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE
    ),
)

RENDER_COMPONENT_PACKAGE_CAPABILITY_PARTICIPATION = (
    *tuple(
        CapabilityParticipationDescriptor(
            capability="diagnostics",
            semantic_owner=semantic_owner,
        )
        for semantic_owner in RENDER_COMPONENT_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE
    ),
    *tuple(
        CapabilityParticipationDescriptor(
            capability="semantic_tokens",
            semantic_owner=semantic_owner,
        )
        for semantic_owner in RENDER_COMPONENT_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE
    ),
)

INTERFACE_DIAGNOSTICS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability="diagnostics",
        semantic_owner=semantic_owner,
    )
    for semantic_owner in INTERFACE_DIAGNOSTICS_OWNER_SEQUENCE
)

INTERFACE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability="semantic_tokens",
        semantic_owner=semantic_owner,
    )
    for semantic_owner in INTERFACE_SEMANTIC_TOKENS_OWNER_SEQUENCE
)

INTERFACE_CAPABILITY_PARTICIPATION = (
    *INTERFACE_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    *INTERFACE_DIAGNOSTICS_CAPABILITY_PARTICIPATION,
    *INTERFACE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION,
)

_INTERFACE_DIAGNOSTICS_PRIORITY_BY_OWNER = {
    INTERFACE_ROOT_OWNER: 130,
    INTERFACE_API_OWNER: 131,
    INTERFACE_WINDOW_OWNER: 132,
    INTERFACE_LAYOUT_OWNER: 133,
    INTERFACE_SECTION_OWNER: 134,
    INTERFACE_PANE_COMPOSITION_OWNER: 135,
    INTERFACE_MOUNT_OWNER: 136,
    INTERFACE_NARRATIVE_OWNER: 137,
    INTERFACE_PANE_OWNER: 138,
    INTERFACE_VIEW_OWNER: 139,
    INTERFACE_ENDPOINT_OWNER: 140,
    INTERFACE_RENDER_COMPONENT_OWNER: 141,
    INTERFACE_RENDER_COMPONENT_PORT_OWNER: 142,
    INTERFACE_RENDER_COMPONENT_CAPABILITY_OWNER: 143,
}

_INTERFACE_DIAGNOSTICS_CALLABLE_NAME_BY_OWNER = {
    INTERFACE_ROOT_OWNER: "_interface_root_diagnostics_provider",
    INTERFACE_API_OWNER: "_interface_api_diagnostics_provider",
    INTERFACE_WINDOW_OWNER: "_interface_window_diagnostics_provider",
    INTERFACE_LAYOUT_OWNER: "_interface_layout_diagnostics_provider",
    INTERFACE_SECTION_OWNER: "_interface_section_diagnostics_provider",
    INTERFACE_PANE_COMPOSITION_OWNER: "_interface_pane_composition_diagnostics_provider",
    INTERFACE_MOUNT_OWNER: "_interface_mount_diagnostics_provider",
    INTERFACE_NARRATIVE_OWNER: "_interface_narrative_diagnostics_provider",
    INTERFACE_PANE_OWNER: "_pane_diagnostics_provider",
    INTERFACE_VIEW_OWNER: "_view_diagnostics_provider",
    INTERFACE_ENDPOINT_OWNER: "_endpoint_diagnostics_provider",
    INTERFACE_RENDER_COMPONENT_OWNER: "_render_component_diagnostics_provider",
    INTERFACE_RENDER_COMPONENT_PORT_OWNER: "_render_component_port_diagnostics_provider",
    INTERFACE_RENDER_COMPONENT_CAPABILITY_OWNER: ("_render_component_capability_diagnostics_provider"),
}

_INTERFACE_SEMANTIC_TOKENS_PRIORITY_BY_OWNER = {
    INTERFACE_ROOT_OWNER: 160,
    INTERFACE_API_OWNER: 161,
    INTERFACE_WINDOW_OWNER: 162,
    INTERFACE_LAYOUT_OWNER: 163,
    INTERFACE_SECTION_OWNER: 164,
    INTERFACE_PANE_COMPOSITION_OWNER: 165,
    INTERFACE_MOUNT_OWNER: 166,
    INTERFACE_NARRATIVE_OWNER: 167,
    INTERFACE_PANE_OWNER: 168,
    INTERFACE_VIEW_OWNER: 169,
    INTERFACE_ENDPOINT_OWNER: 170,
    INTERFACE_RENDER_COMPONENT_OWNER: 171,
    INTERFACE_RENDER_COMPONENT_PORT_OWNER: 172,
    INTERFACE_RENDER_COMPONENT_CAPABILITY_OWNER: 173,
}

_INTERFACE_SEMANTIC_TOKENS_CALLABLE_NAME_BY_OWNER = {
    INTERFACE_ROOT_OWNER: "_interface_root_tokens_provider",
    INTERFACE_API_OWNER: "_interface_api_tokens_provider",
    INTERFACE_WINDOW_OWNER: "_interface_window_tokens_provider",
    INTERFACE_LAYOUT_OWNER: "_interface_layout_tokens_provider",
    INTERFACE_SECTION_OWNER: "_interface_section_tokens_provider",
    INTERFACE_PANE_COMPOSITION_OWNER: "_interface_pane_composition_tokens_provider",
    INTERFACE_MOUNT_OWNER: "_interface_mount_tokens_provider",
    INTERFACE_NARRATIVE_OWNER: "_interface_narrative_tokens_provider",
    INTERFACE_PANE_OWNER: "_pane_tokens_provider",
    INTERFACE_VIEW_OWNER: "_view_tokens_provider",
    INTERFACE_ENDPOINT_OWNER: "_endpoint_tokens_provider",
    INTERFACE_RENDER_COMPONENT_OWNER: "_render_component_tokens_provider",
    INTERFACE_RENDER_COMPONENT_PORT_OWNER: "_render_component_port_tokens_provider",
    INTERFACE_RENDER_COMPONENT_CAPABILITY_OWNER: ("_render_component_capability_tokens_provider"),
}

INTERFACE_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="diagnostics",
        semantic_owner=semantic_owner,
        callable_name=_INTERFACE_DIAGNOSTICS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        required_semantic_scope_keys=INTERFACE_SEMANTIC_SCOPE_KEYS,
        priority=_INTERFACE_DIAGNOSTICS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in INTERFACE_DIAGNOSTICS_OWNER_SEQUENCE
)

INTERFACE_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="semantic_tokens",
        semantic_owner=semantic_owner,
        callable_name=_INTERFACE_SEMANTIC_TOKENS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        priority=_INTERFACE_SEMANTIC_TOKENS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in INTERFACE_SEMANTIC_TOKENS_OWNER_SEQUENCE
)

INTERFACE_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_module="aware_interface.materialization.workspace_provider",
        callable_name="materialize",
        priority=600,
    )
    for semantic_owner in INTERFACE_MATERIALIZATION_OWNER_SEQUENCE
)

INTERFACE_CAPABILITY_EXECUTION_POLICY = (
    *INTERFACE_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY,
    *INTERFACE_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY,
    *INTERFACE_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY,
)

_INTERFACE_OWNER_PROFILES = (
    ("module.aware_interface.interface", (INTERFACE_ROOT_OWNER,)),
    ("module.aware_interface.api", (INTERFACE_API_OWNER,)),
    ("module.aware_interface.window", (INTERFACE_WINDOW_OWNER,)),
    ("module.aware_interface.layout", (INTERFACE_LAYOUT_OWNER,)),
    ("module.aware_interface.section", (INTERFACE_SECTION_OWNER,)),
    ("module.aware_interface.pane_composition", (INTERFACE_PANE_COMPOSITION_OWNER,)),
    ("module.aware_interface.mount", (INTERFACE_MOUNT_OWNER,)),
    ("module.aware_interface.narrative", (INTERFACE_NARRATIVE_OWNER,)),
)

_PANE_OWNER_PROFILES = (
    ("module.aware_interface.pane", (INTERFACE_PANE_OWNER,)),
    ("module.aware_interface.view", (INTERFACE_VIEW_OWNER,)),
    ("module.aware_interface.endpoint", (INTERFACE_ENDPOINT_OWNER,)),
)

_RENDER_COMPONENT_OWNER_PROFILES = (
    ("module.aware_interface.render_component", (INTERFACE_RENDER_COMPONENT_OWNER,)),
    (
        "module.aware_interface.render_component_port",
        (INTERFACE_RENDER_COMPONENT_PORT_OWNER,),
    ),
    (
        "module.aware_interface.render_component_capability",
        (INTERFACE_RENDER_COMPONENT_CAPABILITY_OWNER,),
    ),
)

INTERFACE_DIAGNOSTICS_CAPABILITY_PROFILES = tuple(
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name=name,
        semantic_owners=semantic_owners,
    )
    for name, semantic_owners in _INTERFACE_OWNER_PROFILES
)

INTERFACE_SEMANTIC_TOKENS_CAPABILITY_PROFILES = tuple(
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name=name,
        semantic_owners=semantic_owners,
    )
    for name, semantic_owners in _INTERFACE_OWNER_PROFILES
)

PANE_DIAGNOSTICS_CAPABILITY_PROFILES = tuple(
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name=name,
        semantic_owners=semantic_owners,
    )
    for name, semantic_owners in _PANE_OWNER_PROFILES
)

PANE_SEMANTIC_TOKENS_CAPABILITY_PROFILES = tuple(
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name=name,
        semantic_owners=semantic_owners,
    )
    for name, semantic_owners in _PANE_OWNER_PROFILES
)

RENDER_COMPONENT_DIAGNOSTICS_CAPABILITY_PROFILES = tuple(
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name=name,
        semantic_owners=semantic_owners,
    )
    for name, semantic_owners in _RENDER_COMPONENT_OWNER_PROFILES
)

RENDER_COMPONENT_SEMANTIC_TOKENS_CAPABILITY_PROFILES = tuple(
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name=name,
        semantic_owners=semantic_owners,
    )
    for name, semantic_owners in _RENDER_COMPONENT_OWNER_PROFILES
)

INTERFACE_CAPABILITY_PROFILES = (
    *INTERFACE_DIAGNOSTICS_CAPABILITY_PROFILES,
    *INTERFACE_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
    *PANE_DIAGNOSTICS_CAPABILITY_PROFILES,
    *PANE_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
    *RENDER_COMPONENT_DIAGNOSTICS_CAPABILITY_PROFILES,
    *RENDER_COMPONENT_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
)

INTERFACE_PACKAGE_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name="module.aware_interface",
        semantic_owners=INTERFACE_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE,
        default_selected=True,
    ),
    *INTERFACE_DIAGNOSTICS_CAPABILITY_PROFILES,
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name="module.aware_interface",
        semantic_owners=INTERFACE_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE,
        default_selected=True,
    ),
    *INTERFACE_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
)

PANE_PACKAGE_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name="module.aware_interface",
        semantic_owners=PANE_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE,
        default_selected=True,
    ),
    *PANE_DIAGNOSTICS_CAPABILITY_PROFILES,
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name="module.aware_interface",
        semantic_owners=PANE_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE,
        default_selected=True,
    ),
    *PANE_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
)

RENDER_COMPONENT_PACKAGE_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name="module.aware_interface.render_component",
        semantic_owners=RENDER_COMPONENT_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE,
        default_selected=True,
    ),
    *RENDER_COMPONENT_DIAGNOSTICS_CAPABILITY_PROFILES,
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name="module.aware_interface.render_component",
        semantic_owners=RENDER_COMPONENT_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE,
        default_selected=True,
    ),
    *RENDER_COMPONENT_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
)

INTERFACE_CAPABILITY_BUNDLES = (
    CapabilityBundleDescriptor(
        capability="diagnostics",
        name="bundle.authoring",
        profile_names=("module.aware_interface",),
    ),
    CapabilityBundleDescriptor(
        capability="semantic_tokens",
        name="bundle.authoring",
        profile_names=("module.aware_interface",),
    ),
)

INTERFACE_SYNTAX_LANES = (
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.interface",
        semantic_owner=INTERFACE_ROOT_OWNER,
        compiler_owner=INTERFACE_ROOT_OWNER,
        grammar_rules=("interface_def",),
        semantic_token_types=("keyword", "namespace"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.api",
        semantic_owner=INTERFACE_API_OWNER,
        compiler_owner=INTERFACE_API_OWNER,
        grammar_rules=("interface_api_decl",),
        semantic_token_types=("keyword", "type"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.window",
        semantic_owner=INTERFACE_WINDOW_OWNER,
        compiler_owner=INTERFACE_WINDOW_OWNER,
        grammar_rules=("interface_window_def",),
        semantic_token_types=("keyword", "namespace"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.layout",
        semantic_owner=INTERFACE_LAYOUT_OWNER,
        compiler_owner=INTERFACE_LAYOUT_OWNER,
        grammar_rules=("interface_layout_def",),
        semantic_token_types=("keyword", "class"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.section",
        semantic_owner=INTERFACE_SECTION_OWNER,
        compiler_owner=INTERFACE_SECTION_OWNER,
        grammar_rules=("interface_layout_section_def",),
        semantic_token_types=("keyword", "property"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.pane_composition",
        semantic_owner=INTERFACE_PANE_COMPOSITION_OWNER,
        compiler_owner=INTERFACE_PANE_COMPOSITION_OWNER,
        grammar_rules=("interface_pane_def",),
        semantic_token_types=("keyword", "class"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.mount",
        semantic_owner=INTERFACE_MOUNT_OWNER,
        compiler_owner=INTERFACE_MOUNT_OWNER,
        grammar_rules=("interface_pane_mount_def",),
        semantic_token_types=("keyword", "type", "property"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.narrative",
        semantic_owner=INTERFACE_NARRATIVE_OWNER,
        compiler_owner=INTERFACE_NARRATIVE_OWNER,
        grammar_rules=("interface_pane_narrative_def",),
        semantic_token_types=("keyword", "type", "property"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.pane",
        semantic_owner=INTERFACE_PANE_OWNER,
        compiler_owner=INTERFACE_PANE_OWNER,
        grammar_rules=("pane_def", "pane_kind_decl"),
        semantic_token_types=("keyword", "class", "enumMember"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.view",
        semantic_owner=INTERFACE_VIEW_OWNER,
        compiler_owner=INTERFACE_VIEW_OWNER,
        grammar_rules=("pane_view_def",),
        semantic_token_types=("keyword", "type", "property"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.endpoint",
        semantic_owner=INTERFACE_ENDPOINT_OWNER,
        compiler_owner=INTERFACE_ENDPOINT_OWNER,
        grammar_rules=("pane_endpoint_def",),
        semantic_token_types=("keyword", "type", "function"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.render_component",
        semantic_owner=INTERFACE_RENDER_COMPONENT_OWNER,
        compiler_owner=INTERFACE_RENDER_COMPONENT_OWNER,
        grammar_rules=("pane_render_component_stmt",),
        semantic_token_types=("keyword", "class", "enumMember"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.render_component_port",
        semantic_owner=INTERFACE_RENDER_COMPONENT_PORT_OWNER,
        compiler_owner=INTERFACE_RENDER_COMPONENT_PORT_OWNER,
        grammar_rules=(
            "pane_render_state_binding_stmt",
            "pane_render_action_binding_def",
            "pane_render_input_binding_stmt",
        ),
        semantic_token_types=("keyword", "type", "property"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_interface.render_component_capability",
        semantic_owner=INTERFACE_RENDER_COMPONENT_CAPABILITY_OWNER,
        compiler_owner=INTERFACE_RENDER_COMPONENT_CAPABILITY_OWNER,
        grammar_rules=(
            "pane_render_require_decl",
            "pane_render_fallback_stmt",
        ),
        semantic_token_types=("keyword", "type", "property"),
    ),
)

INTERFACE_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role="aware_interface.provider",
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=(
            "diagnostics",
            "semantic_tokens",
            SEMANTIC_MATERIALIZATION_CAPABILITY,
        ),
        owns_manifest_kinds=(
            "aware_interface_toml",
            "aware_pane_toml",
            "aware_render_component_toml",
            "aware_app_toml",
        ),
    ),
)

INTERFACE_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=INTERFACE_PROVIDER_OWNER,
        manifest_kind="aware_interface_toml",
        filename="aware.interface.toml",
        contract="aware.interface",
        loader_module="aware_interface.manifest.loader",
        loader_name="load_aware_interface_toml_spec",
        workspace_manifest_kind="interface",
        package_role=INTERFACE_PROVIDER_OWNER,
        semantic_package_family="interface",
        semantic_package_kind="interface_package",
        semantic_projection_name="InterfacePackage",
        semantic_root_kind="interface_config",
        code_package_surface="representation",
        workspace_materialization_order=600,
        workspace_materialization_branch="semantic",
        workspace_materialization_commit=True,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=(
            "fqn_prefix",
            "package_kind",
            "config_bundle_path",
        ),
        semantic_package_metadata={
            "workspace_materialization_runtime_index": "workspace_experience",
        },
        priority=600,
    ),
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=INTERFACE_PROVIDER_OWNER,
        manifest_kind="aware_pane_toml",
        filename="aware.pane.toml",
        contract="aware.pane",
        loader_module="aware_interface.manifest.loader",
        loader_name="load_aware_pane_toml_spec",
        workspace_manifest_kind="pane",
        package_role=INTERFACE_PROVIDER_OWNER,
        semantic_package_family="interface",
        semantic_package_kind="pane_package",
        semantic_projection_name="PanePackage",
        semantic_root_kind="pane_package",
        code_package_surface="representation",
        workspace_materialization_order=500,
        workspace_materialization_branch="none",
        workspace_materialization_commit=False,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=(
            "fqn_prefix",
            "package_kind",
            "pane_name",
        ),
        priority=500,
    ),
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=INTERFACE_PROVIDER_OWNER,
        manifest_kind="aware_render_component_toml",
        filename="aware.render_component.toml",
        contract="aware.render_component",
        loader_module="aware_interface.manifest.loader",
        loader_name="load_aware_render_component_toml_spec",
        workspace_manifest_kind="render_component",
        package_role=INTERFACE_PROVIDER_OWNER,
        semantic_package_family="interface",
        semantic_package_kind="render_component_package",
        semantic_projection_name="RenderComponentPackage",
        semantic_root_kind="render_component_package",
        code_package_surface="representation",
        workspace_materialization_order=550,
        workspace_materialization_branch="none",
        workspace_materialization_commit=False,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=("fqn_prefix", "package_kind"),
        semantic_package_metadata={
            "package_section_name": "render_component",
        },
        priority=550,
    ),
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=INTERFACE_PROVIDER_OWNER,
        manifest_kind="aware_app_toml",
        filename="aware.app.toml",
        contract="aware.app",
        loader_module="aware_interface.manifest.loader",
        loader_name="load_aware_app_toml_spec",
        workspace_manifest_kind="app",
        package_role=INTERFACE_PROVIDER_OWNER,
        semantic_package_family="interface",
        semantic_package_kind="app_package",
        semantic_projection_name="AppPackage",
        semantic_root_kind="app_package",
        code_package_surface="app",
        workspace_materialization_order=700,
        workspace_materialization_branch="semantic",
        workspace_materialization_commit=True,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=(
            "fqn_prefix",
            "package_kind",
            "app_name",
        ),
        semantic_package_metadata={
            "package_section_name": "app",
            "dependency_attribute_name": "dependencies",
            "metadata_resolver_module": "aware_interface.manifest.app_metadata",
            "metadata_resolver_name": "resolve_aware_app_manifest_metadata",
            "workspace_materialization_runtime_index": "workspace_experience",
        },
        priority=700,
    ),
)

INTERFACE_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=INTERFACE_PROVIDER_OWNER,
        runtime_ontology_package_names=(INTERFACE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES),
        lane_projection_name="InterfacePackage",
        required_projection_names=INTERFACE_MATERIALIZATION_REQUIRED_PROJECTIONS,
        runtime_projection_packages=(
            ModuleSemanticRuntimeProjectionPackageDescriptor(
                package_name="interface-ontology",
                projection_names=(
                    "AppConfig",
                    "AppPackage",
                    "InterfaceConfig",
                    "InterfacePackage",
                    "PanePackage",
                    "PaneRenderSpec",
                ),
            ),
        ),
        environment_handle="workspace-semantic-materialization",
        include_package_dependency_closure=True,
        priority=500,
    ),
)

_INTERFACE_MATERIALIZATION_RUNTIME_CONTEXT_CONTRACT = (
    "Interface-owned Workspace semantic materialization runtime context"
)

INTERFACE_MATERIALIZATION_RUNTIME_CONTEXT = (
    ModuleSemanticMaterializationRuntimeContextDescriptor(
        semantic_owner=INTERFACE_PROVIDER_OWNER,
        callable_module="aware_interface.materialization.runtime_context",
        callable_name="build_interface_workspace_materialization_runtime_context",
        required=True,
        priority=500,
        provider_payload={
            "contract": _INTERFACE_MATERIALIZATION_RUNTIME_CONTEXT_CONTRACT,
            "runtime_ontology_package_names": (INTERFACE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES),
        },
    ),
)

AWARE_INTERFACE_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_interface",
    semantic_scope_keys=INTERFACE_SEMANTIC_SCOPE_KEYS,
    capability_participation=INTERFACE_CAPABILITY_PARTICIPATION,
    capability_execution_policy=INTERFACE_CAPABILITY_EXECUTION_POLICY,
    capability_profiles=INTERFACE_CAPABILITY_PROFILES,
    capability_bundles=(),
    syntax_lanes=INTERFACE_SYNTAX_LANES,
    package_roles=INTERFACE_PACKAGE_ROLES,
    manifest_resolution=INTERFACE_MANIFEST_RESOLUTION,
    materialization_runtime=INTERFACE_MATERIALIZATION_RUNTIME,
    materialization_runtime_context=INTERFACE_MATERIALIZATION_RUNTIME_CONTEXT,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_INTERFACE_SEMANTIC_CONTRACT


__all__ = [
    "AWARE_INTERFACE_SEMANTIC_CONTRACT",
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "INTERFACE_API_OWNER",
    "INTERFACE_CAPABILITY_BUNDLES",
    "INTERFACE_CAPABILITY_EXECUTION_POLICY",
    "INTERFACE_CAPABILITY_PARTICIPATION",
    "INTERFACE_CAPABILITY_PROFILES",
    "INTERFACE_DIAGNOSTICS_CAPABILITY_PARTICIPATION",
    "INTERFACE_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY",
    "INTERFACE_DIAGNOSTICS_CAPABILITY_PROFILES",
    "INTERFACE_DIAGNOSTICS_OWNER_SEQUENCE",
    "INTERFACE_ENDPOINT_OWNER",
    "INTERFACE_LAYOUT_OWNER",
    "INTERFACE_MANIFEST_RESOLUTION",
    "INTERFACE_MOUNT_OWNER",
    "INTERFACE_MATERIALIZATION_CAPABILITY_PARTICIPATION",
    "INTERFACE_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY",
    "INTERFACE_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "INTERFACE_MATERIALIZATION_RUNTIME",
    "INTERFACE_MATERIALIZATION_RUNTIME_CONTEXT",
    "INTERFACE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "INTERFACE_MATERIALIZATION_OWNER_SEQUENCE",
    "INTERFACE_NARRATIVE_OWNER",
    "INTERFACE_PACKAGE_ROLES",
    "INTERFACE_PACKAGE_CAPABILITY_PARTICIPATION",
    "INTERFACE_PACKAGE_CAPABILITY_PROFILES",
    "INTERFACE_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE",
    "INTERFACE_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE",
    "INTERFACE_PANE_COMPOSITION_OWNER",
    "INTERFACE_PANE_OWNER",
    "INTERFACE_PROVIDER_OWNER",
    "INTERFACE_RENDER_COMPONENT_CAPABILITY_OWNER",
    "INTERFACE_RENDER_COMPONENT_OWNER",
    "INTERFACE_RENDER_COMPONENT_PORT_OWNER",
    "INTERFACE_ROOT_OWNER",
    "INTERFACE_SECTION_OWNER",
    "INTERFACE_SEMANTIC_SCOPE_KEYS",
    "INTERFACE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION",
    "INTERFACE_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY",
    "INTERFACE_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
    "INTERFACE_SEMANTIC_TOKENS_OWNER_SEQUENCE",
    "INTERFACE_SYNTAX_LANES",
    "INTERFACE_VIEW_OWNER",
    "INTERFACE_WINDOW_OWNER",
    "PANE_DIAGNOSTICS_CAPABILITY_PROFILES",
    "PANE_PACKAGE_CAPABILITY_PARTICIPATION",
    "PANE_PACKAGE_CAPABILITY_PROFILES",
    "PANE_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE",
    "PANE_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE",
    "PANE_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
    "RENDER_COMPONENT_DIAGNOSTICS_CAPABILITY_PROFILES",
    "RENDER_COMPONENT_PACKAGE_CAPABILITY_PARTICIPATION",
    "RENDER_COMPONENT_PACKAGE_CAPABILITY_PROFILES",
    "RENDER_COMPONENT_PACKAGE_DIAGNOSTICS_OWNER_SEQUENCE",
    "RENDER_COMPONENT_PACKAGE_SEMANTIC_TOKENS_OWNER_SEQUENCE",
    "RENDER_COMPONENT_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
]
