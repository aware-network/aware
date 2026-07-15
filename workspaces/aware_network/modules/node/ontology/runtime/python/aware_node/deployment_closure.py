from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from aware_code.semantic_materialization import (
    SEMANTIC_PACKAGE_SELECTION_INTENTS_CONTEXT_KEY,
)
from aware_environment_ontology.stable_ids import stable_environment_config_id
from aware_interface_ontology.stable_ids import stable_interface_config_id
from aware_service_ontology.stable_ids import stable_service_config_id

NODE_RUNTIME_CLOSURE_SCHEMA = "aware.node.runtime_closure.v1"
NODE_RUNTIME_CLOSURE_CONTEXT_KEY = SEMANTIC_PACKAGE_SELECTION_INTENTS_CONTEXT_KEY
NODE_RUNTIME_CLOSURE_REQUIRED_PYTHON_PACKAGES_BY_KIND = {
    "node": "aware-node-service",
    "environment": "aware-environment-service",
    "service": "aware-service-service",
    "interface": "aware-interface-service",
}
PACKAGE_SELECTION_BINDING_KEYS = (
    "code_semantic_provider_registration_id",
    "code_semantic_package_binding_id",
    "semantic_binding_module_package_id",
    "semantic_binding_module_package_kind",
    "semantic_binding_module_relative_package_root",
    "semantic_binding_manifest_relative_path",
    "semantic_binding_contract_module",
    "semantic_binding_contract_name",
    "semantic_binding_contract_role",
    "semantic_binding_owned_manifest_kinds",
    "semantic_binding_capabilities",
    "semantic_binding_status",
)


def build_node_runtime_closure_payload(
    *,
    result: object,
    workspace_semantic_package_selection_intents: Sequence[Mapping[str, object]] = (),
) -> dict[str, object]:
    """Build the deployable runtime closure owned by Node materialization."""

    package_entries = _effective_bundle_entries(
        tuple(
            entry
            for entry in workspace_semantic_package_selection_intents
            if isinstance(entry, Mapping)
        )
    )
    node_package = getattr(result, "node_package")
    node_config = getattr(result, "node_config")
    node_package_name = _required_attr_text(node_package, "name")
    node_config_name = _required_attr_text(node_config, "name")
    node_package_selection = {
        "family_key": "node",
        "package_kind": "node",
        "package_name": node_package_name,
        "manifest_path": _relative_manifest_path(result),
        "semantic_package_id": _optional_attr_text(node_package, "id"),
        "semantic_root_kind": "node_config",
        "semantic_root_id": _optional_attr_text(node_config, "id"),
        "semantic_branch_id": _optional_text(
            getattr(result, "semantic_branch_id", None)
        ),
        "semantic_head_commit_id": _optional_attr_text(
            result, "package_head_commit_id"
        ),
        "semantic_object_instance_graph_commit_id": _optional_attr_text(
            result, "package_object_instance_graph_commit_id"
        ),
        "semantic_root_object_instance_graph_commit_id": _optional_attr_text(
            result, "node_config_object_instance_graph_commit_id"
        ),
        "source_code_package_id": _optional_attr_text(result, "source_code_package_id"),
    }
    node_bundle_selection = _optional_bundle_selection(
        entries=package_entries,
        package_kind="node",
        package_name=node_package_name,
        semantic_root_id=_optional_attr_text(node_config, "id"),
        target_name=node_package_name,
    )
    if node_bundle_selection is not None:
        node_package_selection.update(
            {
                key: node_bundle_selection[key]
                for key in PACKAGE_SELECTION_BINDING_KEYS
                if key in node_bundle_selection
            }
        )
    runtime_inputs: list[dict[str, object]] = []
    package_selections: list[dict[str, object]] = [node_package_selection]
    runtime_kinds: set[str] = {"node"}

    for target in getattr(result, "node_config_environment_targets", ()) or ():
        environment_handle = _required_attr_text(target, "environment_handle")
        environment_selection = _require_bundle_selection(
            entries=package_entries,
            package_kind="environment",
            semantic_root_id=str(
                stable_environment_config_id(handle=environment_handle)
            ),
            target_name=environment_handle,
        )
        package_selections.append(environment_selection)
        runtime_kinds.add("environment")
        for mount in getattr(target, "profile_mounts", ()) or ():
            profile_key = _required_attr_text(mount, "profile_key")
            package_name = _required_attr_text(mount, "package_name")
            profile_selection = _require_bundle_selection(
                entries=package_entries,
                package_kind="environment_profile",
                package_name=package_name,
                target_name=package_name,
            )
            package_selections.append(profile_selection)
            runtime_inputs.append(
                {
                    "runtime_kind": "environment",
                    "target_name": environment_handle,
                    "package_selection": environment_selection,
                    "environment_profile_package_selection": profile_selection,
                    "environment_handle": environment_handle,
                    "profile_key": profile_key,
                    "manifest_path": environment_selection.get("manifest_path"),
                }
            )

    for target in getattr(result, "node_config_ontology_targets", ()) or ():
        package_name = _required_attr_text(target, "package_name")
        selection = _require_bundle_selection(
            entries=package_entries,
            package_kind="ontology",
            package_name=package_name,
            semantic_root_kind="OntologyPackage",
            target_name=package_name,
        )
        package_selections.append(selection)
        runtime_inputs.append(
            {
                "runtime_kind": "ontology",
                "target_name": package_name,
                "package_selection": selection,
                "manifest_path": selection.get("manifest_path"),
            }
        )

    for target in getattr(result, "node_config_service_targets", ()) or ():
        service_name = _required_attr_text(target, "service_name")
        selection = _require_bundle_selection(
            entries=package_entries,
            package_kind="service",
            semantic_root_kind="service_config",
            semantic_root_id=str(stable_service_config_id(name=service_name)),
            target_name=service_name,
        )
        package_selections.append(selection)
        runtime_kinds.add("service")
        runtime_inputs.append(
            {
                "runtime_kind": "service",
                "target_name": service_name,
                "package_selection": selection,
                "manifest_path": selection.get("manifest_path"),
                "code_packages": [
                    {
                        "slot_key": _required_attr_text(package, "slot_key"),
                        "package_name": _required_attr_text(package, "package_name"),
                        "language": _optional_attr_text(package, "language") or "aware",
                    }
                    for package in getattr(target, "code_packages", ()) or ()
                ],
            }
        )

    for target in getattr(result, "node_config_interface_targets", ()) or ():
        interface_name = _required_attr_text(target, "interface_name")
        selection = _require_bundle_selection(
            entries=package_entries,
            package_kind="interface",
            semantic_root_id=str(stable_interface_config_id(name=interface_name)),
            target_name=interface_name,
        )
        package_selections.append(selection)
        runtime_kinds.add("interface")
        runtime_inputs.append(
            {
                "runtime_kind": "interface",
                "target_name": interface_name,
                "package_selection": selection,
                "manifest_path": selection.get("manifest_path"),
            }
        )

    return {
        "schema": NODE_RUNTIME_CLOSURE_SCHEMA,
        "node_selection": {
            "selector_key": node_config_name,
            "target_ref": node_config_name,
            "package_selection": _compact_payload(node_package_selection),
            "node_config_id": _optional_attr_text(node_config, "id"),
            "node_package_head_commit_id": _optional_attr_text(
                result, "package_head_commit_id"
            ),
        },
        "package_selections": _dedupe_package_selections(package_selections),
        "runtime_inputs": [_compact_payload(item) for item in runtime_inputs],
        "runtime_kinds": tuple(sorted(runtime_kinds)),
        "required_python_packages": tuple(
            package_name
            for kind, package_name in sorted(
                NODE_RUNTIME_CLOSURE_REQUIRED_PYTHON_PACKAGES_BY_KIND.items()
            )
            if kind in runtime_kinds
        ),
    }


def _require_bundle_selection(
    *,
    entries: Sequence[Mapping[str, object]],
    package_kind: str,
    target_name: str,
    package_name: str | None = None,
    semantic_root_kind: str | None = None,
    semantic_root_id: str | None = None,
) -> dict[str, object]:
    matches = _dedupe_bundle_entries(
        entry
        for entry in entries
        if _optional_text(entry.get("package_kind")) == package_kind
        and (package_name is None or _package_entry_name(entry) == package_name)
        and (
            semantic_root_kind is None
            or _optional_text(entry.get("semantic_root_kind")) == semantic_root_kind
        )
        and (
            semantic_root_id is None
            or _optional_text(entry.get("semantic_root_id")) == semantic_root_id
        )
    )
    if len(matches) != 1:
        criteria = {
            "package_kind": package_kind,
            "target_name": target_name,
            "package_name": package_name,
            "semantic_root_kind": semantic_root_kind,
            "semantic_root_id": semantic_root_id,
            "matches": len(matches),
        }
        raise RuntimeError(
            "Node runtime closure could not resolve declared target from "
            "Workspace semantic package selection intents: "
            + ", ".join(
                f"{key}={value!r}"
                for key, value in criteria.items()
                if value is not None
            )
        )
    return _package_selection_from_bundle(matches[0])


def _optional_bundle_selection(
    *,
    entries: Sequence[Mapping[str, object]],
    package_kind: str,
    target_name: str,
    package_name: str | None = None,
    semantic_root_kind: str | None = None,
    semantic_root_id: str | None = None,
) -> dict[str, object] | None:
    matches = _dedupe_bundle_entries(
        entry
        for entry in entries
        if _optional_text(entry.get("package_kind")) == package_kind
        and (package_name is None or _package_entry_name(entry) == package_name)
        and (
            semantic_root_kind is None
            or _optional_text(entry.get("semantic_root_kind")) == semantic_root_kind
        )
        and (
            semantic_root_id is None
            or _optional_text(entry.get("semantic_root_id")) == semantic_root_id
        )
    )
    if not matches:
        return None
    if len(matches) > 1:
        criteria = {
            "package_kind": package_kind,
            "target_name": target_name,
            "package_name": package_name,
            "semantic_root_kind": semantic_root_kind,
            "semantic_root_id": semantic_root_id,
            "matches": len(matches),
        }
        raise RuntimeError(
            "Node runtime closure matched multiple optional self package "
            "selection intents: "
            + ", ".join(
                f"{key}={value!r}"
                for key, value in criteria.items()
                if value is not None
            )
        )
    return _package_selection_from_bundle(matches[0])


def _package_selection_from_bundle(entry: Mapping[str, object]) -> dict[str, object]:
    package_kind = _optional_text(entry.get("package_kind")) or ""
    package_name = _package_entry_name(entry) or ""
    return _compact_payload(
        {
            "family_key": _optional_text(entry.get("semantic_package_family"))
            or package_kind,
            "package_kind": package_kind,
            "package_name": package_name,
            "label": _optional_text(entry.get("label")),
            "manifest_path": _optional_text(entry.get("manifest_path")),
            "experience_handle": _optional_text(entry.get("experience_handle")),
            "profiles": (
                entry.get("profiles") if isinstance(entry.get("profiles"), list) else ()
            ),
            "workspace_package_id": _optional_text(entry.get("workspace_package_id")),
            "source": _optional_text(entry.get("source")),
            "dependency_id": _optional_text(entry.get("dependency_id")),
            "workspace_dependency_revision_id": _optional_text(
                entry.get("workspace_dependency_revision_id")
            ),
            "export_ref": _optional_text(entry.get("export_ref")),
            "semantic_branch_id": _optional_text(entry.get("semantic_branch_id")),
            "semantic_head_commit_id": _optional_text(
                entry.get("semantic_head_commit_id")
            ),
            "semantic_package_id": _optional_text(entry.get("semantic_package_id")),
            "semantic_projection_hash": _optional_text(
                entry.get("semantic_projection_hash")
            ),
            "semantic_object_instance_graph_commit_id": _optional_text(
                entry.get("semantic_object_instance_graph_commit_id")
            ),
            "semantic_root_kind": _optional_text(entry.get("semantic_root_kind")),
            "semantic_root_id": _optional_text(entry.get("semantic_root_id")),
            "semantic_root_object_instance_graph_commit_id": _optional_text(
                entry.get("semantic_root_object_instance_graph_commit_id")
            ),
            "source_code_package_id": _optional_text(
                entry.get("source_code_package_id")
            ),
            "code_semantic_provider_registration_id": _optional_text(
                entry.get("code_semantic_provider_registration_id")
            ),
            "code_semantic_package_binding_id": _optional_text(
                entry.get("code_semantic_package_binding_id")
            ),
            "semantic_binding_module_package_id": _optional_text(
                entry.get("semantic_binding_module_package_id")
            ),
            "semantic_binding_module_package_kind": _optional_text(
                entry.get("semantic_binding_module_package_kind")
            ),
            "semantic_binding_module_relative_package_root": _optional_text(
                entry.get("semantic_binding_module_relative_package_root")
            ),
            "semantic_binding_manifest_relative_path": _optional_text(
                entry.get("semantic_binding_manifest_relative_path")
            ),
            "semantic_binding_contract_module": _optional_text(
                entry.get("semantic_binding_contract_module")
            ),
            "semantic_binding_contract_name": _optional_text(
                entry.get("semantic_binding_contract_name")
            ),
            "semantic_binding_contract_role": _optional_text(
                entry.get("semantic_binding_contract_role")
            ),
            "semantic_binding_owned_manifest_kinds": (
                entry.get("semantic_binding_owned_manifest_kinds")
                if isinstance(
                    entry.get("semantic_binding_owned_manifest_kinds"),
                    (list, tuple),
                )
                else ()
            ),
            "semantic_binding_capabilities": (
                entry.get("semantic_binding_capabilities")
                if isinstance(entry.get("semantic_binding_capabilities"), (list, tuple))
                else ()
            ),
            "semantic_binding_status": _optional_text(
                entry.get("semantic_binding_status")
            ),
        }
    )


def _effective_bundle_entries(
    entries: Sequence[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    materialized_package_keys = {
        key
        for entry in entries
        if _optional_text(entry.get("source"))
        != "workspace_local_semantic_package_registry"
        for key in (_bundle_package_key(entry),)
        if key is not None
    }
    return tuple(
        entry
        for entry in entries
        if not (
            _optional_text(entry.get("source"))
            == "workspace_local_semantic_package_registry"
            and _bundle_package_key(entry) in materialized_package_keys
        )
    )


def _dedupe_bundle_entries(
    entries: Iterable[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    deduped: dict[tuple[str | None, ...], Mapping[str, object]] = {}
    for entry in entries:
        key = _bundle_target_key(entry)
        if key not in deduped or _entry_specificity(entry) > _entry_specificity(
            deduped[key]
        ):
            deduped[key] = entry
    return tuple(deduped.values())


def _bundle_package_key(entry: Mapping[str, object]) -> tuple[str, str] | None:
    package_kind = _optional_text(entry.get("package_kind"))
    package_name = _package_entry_name(entry)
    if package_kind is None or package_name is None:
        return None
    return (package_kind, package_name)


def _bundle_target_key(entry: Mapping[str, object]) -> tuple[str | None, ...]:
    return (
        _optional_text(entry.get("package_kind")),
        _package_entry_name(entry),
        _optional_text(entry.get("semantic_package_id")),
        _optional_text(entry.get("semantic_root_kind")),
        _optional_text(entry.get("semantic_root_id")),
        _optional_text(entry.get("source_code_package_id")),
        _optional_text(entry.get("manifest_path")),
    )


def _entry_specificity(entry: Mapping[str, object]) -> int:
    return sum(1 for value in _bundle_target_key(entry) if value is not None)


def _dedupe_package_selections(
    selections: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    seen: set[tuple[str, str, str | None]] = set()
    result: list[dict[str, object]] = []
    for selection in selections:
        key = (
            str(selection.get("package_kind") or ""),
            str(selection.get("package_name") or ""),
            _optional_text(selection.get("semantic_package_id")),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(dict(selection))
    return tuple(result)


def _package_entry_name(entry: Mapping[str, object]) -> str | None:
    return _optional_text(entry.get("package_name")) or _optional_text(
        entry.get("package_key")
    )


def _relative_manifest_path(result: object) -> str | None:
    node_toml_path = getattr(result, "node_toml_path", None)
    workspace_root = getattr(result, "workspace_root", None)
    if node_toml_path is None:
        return None
    try:
        path = node_toml_path
        if workspace_root is not None:
            return path.relative_to(workspace_root).as_posix()
        return path.as_posix()
    except Exception:
        return str(node_toml_path)


def _required_attr_text(obj: object, attr: str) -> str:
    value = _optional_attr_text(obj, attr)
    if value is None:
        raise RuntimeError(f"Node runtime closure requires {attr}.")
    return value


def _optional_attr_text(obj: object, attr: str) -> str | None:
    return _optional_text(getattr(obj, attr, None))


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "value"):
        value = getattr(value, "value")
    text = str(value).strip()
    return text or None


def _compact_payload(payload: Mapping[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if value == ():
            continue
        if isinstance(value, list) and not value:
            continue
        result[key] = value
    return result


__all__ = [
    "NODE_RUNTIME_CLOSURE_CONTEXT_KEY",
    "NODE_RUNTIME_CLOSURE_REQUIRED_PYTHON_PACKAGES_BY_KIND",
    "NODE_RUNTIME_CLOSURE_SCHEMA",
    "build_node_runtime_closure_payload",
]
