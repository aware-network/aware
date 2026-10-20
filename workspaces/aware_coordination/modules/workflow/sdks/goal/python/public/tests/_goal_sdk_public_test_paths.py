from __future__ import annotations

from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent
PUBLIC_SDK_ROOT = TESTS_ROOT.parent
GOAL_SDK_ROOT = PUBLIC_SDK_ROOT.parents[1]
WORKFLOW_MODULE_ROOT = PUBLIC_SDK_ROOT.parents[3]
AWARE_COORDINATION_WORKSPACE_ROOT = WORKFLOW_MODULE_ROOT.parent.parent
REPO_ROOT = AWARE_COORDINATION_WORKSPACE_ROOT.parent.parent
KERNEL_WORKSPACE_ROOT = REPO_ROOT / "workspaces" / "aware_kernel"
SDK_RUNTIME_ROOT = (
    KERNEL_WORKSPACE_ROOT / "modules" / "sdk" / "ontology" / "runtime" / "python"
)

GOAL_SERVICE_API_ROOT = (
    WORKFLOW_MODULE_ROOT / "apis" / "goal" / "python" / "aware_goal_service_api"
)
GOAL_SERVICE_DTO_ROOT = (
    WORKFLOW_MODULE_ROOT / "apis" / "goal" / "python" / "aware_goal_service_dto"
)
CONTENT_SERVICE_DTO_ROOT = (
    KERNEL_WORKSPACE_ROOT
    / "modules"
    / "content"
    / "apis"
    / "content"
    / "python"
    / "aware_content_service_dto"
)
AWARE_GOALS_LANGUAGE_ROOT = (
    WORKFLOW_MODULE_ROOT
    / "experiences"
    / "aware-goals"
    / "languages"
    / "python"
    / "aware_goals"
)
GOAL_SDK_TOML = GOAL_SDK_ROOT / "aware" / "aware.sdk.toml"
