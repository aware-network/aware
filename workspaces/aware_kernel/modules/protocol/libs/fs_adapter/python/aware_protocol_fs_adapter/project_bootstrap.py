"""Protocol-owned, read-only fs_v3 and explicit fs_v4 configuration preparation.

This prepares one exact manifest, not an admission to publish or install it.
Workspace owns initial publication permission. Existing fs_v1 init is unchanged.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from weakref import WeakKeyDictionary

from aware_protocol_runtime import ProtocolAdmissionOutcomeKind

from .goal_templates import canonical_relative_path
from .manifest import (
    COLLABORATION_PLANNING_FS_PROFILE,
    COLLABORATION_PROJECT_FS_PROFILE,
    NATIVE_GOAL_RECORD_PROFILE,
    PLANNING_GOAL_RECORD_PROFILE,
    validate_protocol_manifest_content,
)


@dataclass(frozen=True, slots=True)
class ProjectConfiguration:
    repository_root: str
    issue_root: str
    goal_root: str
    project_root: str
    content: bytes
    source_sha256: str

    def to_wire(self):
        return {
            "repository_root": self.repository_root,
            "issue_root": self.issue_root,
            "goal_root": self.goal_root,
            "project_root": self.project_root,
            "content_utf8": self.content.decode("utf-8"),
            "source_sha256": self.source_sha256,
        }


_PLANS = WeakKeyDictionary()


class ProjectConfigurationPlan:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable] -- Python owns the weakref slot

    def __new__(cls):
        raise TypeError("use prepare_project_configuration")

    def __copy__(self):
        raise TypeError("configuration_plan_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("configuration_plan_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("configuration_plan_not_serializable")


def _render(
    repository_root, issue_root, goal_root, project_root,
    *, profile=COLLABORATION_PROJECT_FS_PROFILE,
):
    if type(profile) is not str or profile not in {
        COLLABORATION_PROJECT_FS_PROFILE, COLLABORATION_PLANNING_FS_PROFILE,
    }:
        raise ValueError("project_bootstrap_profile_invalid")
    planning = profile == COLLABORATION_PLANNING_FS_PROFILE
    version = 4 if planning else 3
    goal_profile = PLANNING_GOAL_RECORD_PROFILE if planning else NATIVE_GOAL_RECORD_PROFILE
    root = Path(repository_root)
    if (
        not root.is_absolute()
        or str(root) != repository_root
        or root.resolve() != root
        or root == Path("/")
    ):
        raise ValueError("project_bootstrap_canonical_root_required")
    roots = (issue_root, goal_root, project_root)
    if any(
        not canonical_relative_path(value) or ".git" in PurePosixPath(value).parts
        for value in roots
    ):
        raise ValueError("project_bootstrap_record_root_invalid")
    if any(
        a == b or a.startswith(b + "/") or b.startswith(a + "/")
        for i, a in enumerate(roots)
        for b in roots[i + 1 :]
    ):
        raise ValueError("project_bootstrap_record_roots_overlap")
    if any(
        value == "aware.protocol.toml" or value.startswith("aware.protocol.toml/")
        for value in roots
    ):
        raise ValueError("project_bootstrap_manifest_collision")
    quote = json.dumps
    text = (
        'aware = 1\n\n[protocol]\nname = "aware.collaboration"\n'
        f'profile = "{profile}"\nsemantic_version = {version}\n\n'
        '[target]\nkind = "repository"\nauthority_mode = "filesystem"\n\n'
        '[bootstrap]\nagent_contract = "AGENTS.md"\n\n'
        '[records.issue]\nprofile = "aware.issue.markdown.v1"\nrole = "authority"\n'
        f'root = {quote(issue_root)}\npath_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"\n\n'
        f'[records.goal]\nprofile = "{goal_profile}"\nrole = "authority"\n'
        f'root = {quote(goal_root)}\npath_template = "YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md"\n\n'
        '[records.project]\nprofile = "aware.project.context.toml.v1"\nrole = "authority"\n'
        f'root = {quote(project_root)}\npath_template = "project-<slug>.toml"\n\n'
        '[records.feed]\nprofile = "aware.feed.projection.v1"\nrole = "unavailable"\n\n'
        '[records.specification]\nprofile = "specification_fs_v1"\nrole = "unavailable"\n\n'
        '[records.evidence]\nprofile = "aware.protocol.evidence.v1"\nrole = "unavailable"\n'
    ).encode()
    admitted = validate_protocol_manifest_content(source=text)
    if admitted.outcome is not ProtocolAdmissionOutcomeKind.CANONICAL_V1:
        raise ValueError(
            "project_bootstrap_manifest_invalid:" + ":".join(admitted.diagnostics)
        )
    return ProjectConfiguration(
        repository_root,
        issue_root,
        goal_root,
        project_root,
        text,
        "sha256:" + hashlib.sha256(text).hexdigest(),
    )


def prepare_project_configuration(
    *, repository_root, issue_root, goal_root, project_root
):
    """Original fs_v3 preparation; existing default bytes remain exact."""
    return _prepare(repository_root, issue_root, goal_root, project_root, COLLABORATION_PROJECT_FS_PROFILE)


def prepare_planning_project_configuration(
    *, repository_root, issue_root="docs/issues", goal_root="docs/goals", project_root="docs/projects"
):
    """Explicit fs_v4 opt-in with Protocol-owned roots; no publication/upgrade."""
    return _prepare(repository_root, issue_root, goal_root, project_root, COLLABORATION_PLANNING_FS_PROFILE)


def _prepare(repository_root, issue_root, goal_root, project_root, profile):
    config = _render(repository_root, issue_root, goal_root, project_root, profile=profile)
    plan = object.__new__(ProjectConfigurationPlan)
    _PLANS[plan] = (os.getpid(), config, json.dumps(config.to_wire(), sort_keys=True), profile)
    return plan


def require_project_configuration(plan):
    state = _PLANS.get(plan) if type(plan) is ProjectConfigurationPlan else None
    if state is None or state[0] != os.getpid():
        raise ValueError("original_project_configuration_plan_required")
    config = state[1]
    if json.dumps(config.to_wire(), sort_keys=True) != state[2] or config != _render(
        config.repository_root, config.issue_root, config.goal_root, config.project_root,
        profile=state[3],
    ):
        raise ValueError("project_configuration_changed")
    # The consumer gets detached data, never the registry's retained object.
    return ProjectConfiguration(
        config.repository_root,
        config.issue_root,
        config.goal_root,
        config.project_root,
        config.content,
        config.source_sha256,
    )
