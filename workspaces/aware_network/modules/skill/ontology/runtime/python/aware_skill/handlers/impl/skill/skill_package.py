from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Skill Ontology
from aware_skill_ontology.skill.skill_package import SkillPackage
from aware_skill_ontology.skill.skill_package_api_package import SkillPackageApiPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code_ontology.package.code_package import CodePackage
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta.runtime.handler_context import current_handler_session
from aware_skill_ontology.skill.skill_config import SkillConfig
from aware_skill_ontology.stable_ids import (
    stable_skill_package_api_package_id,
    stable_skill_package_id,
)

# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    skill_config_id: UUID,
    skill_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
) -> SkillPackage:
    """
    Create the canonical Skill-owned package root over an existing `SkillConfig`.

    Contract:
    - Identity is keyed by Skill package `name`.
    - `SkillPackage` is the package/public root over an existing canonical `SkillConfig`.
    - `skill_config_id` must point at the canonical SkillConfig stable id for this package root.
    - `skill_config_object_instance_graph_commit_id` pins the historical ObjectInstanceGraphCommit
      for the semantic SkillConfig root so package consumers can replay exact skill truth without
      resolving branch head or reopening authoring TOML.
    - `source_code_package_id` is explicit raw-source provenance for this semantic leaf package.
    - Workspace will later mount `SkillPackage`, not raw `SkillConfig`.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("SkillPackage.build requires non-empty name")

    skill_package_id = stable_skill_package_id(name=normalized_name)
    session = current_handler_session()
    resolved_skill_config_oig_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            skill_config_object_instance_graph_commit_id,
        )
        if skill_config_object_instance_graph_commit_id is not None
        else None
    )
    existing = session.imap_get(SkillPackage, skill_package_id)
    if existing is not None:
        if (existing.name or "").strip() != normalized_name:
            raise RuntimeError(
                "SkillPackage.build payload mismatch for existing package: " + f"skill_package_id={skill_package_id}"
            )
        if existing.skill_config_id != skill_config_id:
            raise RuntimeError(
                "SkillPackage.build skill_config_id mismatch for existing package: "
                f"skill_package_id={skill_package_id} existing={existing.skill_config_id} provided={skill_config_id}"
            )
        if source_code_package_id is not None:
            if existing.source_code_package_id is None:
                existing.source_code_package_id = source_code_package_id
                existing.source_code_package = session.imap_get(CodePackage, source_code_package_id)
            elif existing.source_code_package_id != source_code_package_id:
                raise RuntimeError(
                    "SkillPackage.build source_code_package_id mismatch for existing package: "
                    f"skill_package_id={skill_package_id} "
                    f"existing={existing.source_code_package_id} provided={source_code_package_id}"
                )
        if skill_config_object_instance_graph_commit_id is not None:
            existing_oig_commit_id = existing.skill_config_object_instance_graph_commit_id
            if existing_oig_commit_id is None:
                existing.skill_config_object_instance_graph_commit_id = skill_config_object_instance_graph_commit_id
                existing.skill_config_object_instance_graph_commit = resolved_skill_config_oig_commit
            elif existing_oig_commit_id != skill_config_object_instance_graph_commit_id:
                raise RuntimeError(
                    "SkillPackage.build skill_config_object_instance_graph_commit_id mismatch "
                    "for existing package: "
                    f"skill_package_id={skill_package_id} "
                    f"existing={existing_oig_commit_id} "
                    f"provided={skill_config_object_instance_graph_commit_id}"
                )
        return existing

    return SkillPackage.model_construct(
        id=skill_package_id,
        name=normalized_name,
        skill_config=session.imap_get(SkillConfig, skill_config_id),
        skill_config_id=skill_config_id,
        skill_config_object_instance_graph_commit=resolved_skill_config_oig_commit,
        skill_config_object_instance_graph_commit_id=skill_config_object_instance_graph_commit_id,
        source_code_package=(
            session.imap_get(CodePackage, source_code_package_id) if source_code_package_id is not None else None
        ),
        source_code_package_id=source_code_package_id,
    )
    # --- AWARE: LOGIC END build


async def attach_api_package(
    skill_package: SkillPackage, api_package_id: UUID, description: str | None = None
) -> SkillPackageApiPackage:
    """
    Attach one API package to this SkillPackage.

    Contract:
    - This is the package/import rail for authored Skill source.
    - It declares which API packages are available to this Skill package.
    - Config/runtime semantic API use remains a separate `SkillConfig -> Api` and
      `SkillConfigApiEndpoint -> ApiCapabilityEndpoint` bridge.
    """

    # --- AWARE: LOGIC START attach_api_package
    if skill_package.id is None:
        raise RuntimeError("SkillPackage.attach_api_package requires SkillPackage.id")

    skill_package_api_package_id = stable_skill_package_api_package_id(
        skill_package_id=skill_package.id,
        api_package_id=api_package_id,
    )

    for existing in skill_package.api_packages:
        if existing.id == skill_package_api_package_id or existing.api_package_id == api_package_id:
            return existing

    created = await SkillPackageApiPackage.build_via_skill_package(
        skill_package_id=skill_package.id,
        api_package_id=api_package_id,
        description=description,
    )
    skill_package.api_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_api_package
