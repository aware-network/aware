from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


@dataclass(frozen=True, slots=True)
class NodePackageIncludeOwnership:
    included_package_name: str
    include_key: str
    source_path: str


@dataclass(frozen=True, slots=True)
class NodeEnvironmentProfileMountOwnership:
    profile_key: str
    package_name: str
    mount_key: str
    mode: str
    position: int | None
    source_path: str


@dataclass(frozen=True, slots=True)
class NodeEnvironmentTargetOwnership:
    environment_handle: str
    profile_mounts: tuple[NodeEnvironmentProfileMountOwnership, ...]
    source_path: str


@dataclass(frozen=True, slots=True)
class NodeServiceCodePackageOwnership:
    slot_key: str
    package_name: str
    language: str
    source_path: str


@dataclass(frozen=True, slots=True)
class NodeServiceTargetOwnership:
    service_name: str
    source_path: str
    code_packages: tuple[NodeServiceCodePackageOwnership, ...] = ()


@dataclass(frozen=True, slots=True)
class NodeOntologyTargetOwnership:
    package_name: str
    source_path: str


@dataclass(frozen=True, slots=True)
class NodeInterfaceTargetOwnership:
    interface_name: str
    source_path: str


@dataclass(frozen=True, slots=True)
class NodeOwnership:
    name: str
    source_path: str
    included_node_packages: tuple[NodePackageIncludeOwnership, ...]
    environment_targets: tuple[NodeEnvironmentTargetOwnership, ...]
    ontology_targets: tuple[NodeOntologyTargetOwnership, ...]
    service_targets: tuple[NodeServiceTargetOwnership, ...]
    interface_targets: tuple[NodeInterfaceTargetOwnership, ...]


def load_node_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
) -> NodeOwnership:
    parser = Parser(language=AWARE_LANGUAGE)
    declared_node: NodeOwnership | None = None

    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="node source")
        source_text = source_path.read_text(encoding="utf-8")
        source_rel = relpath.as_posix()
        tree = parser.parse(source_text.encode("utf-8"))

        if tree.root_node.has_error:
            raise ValueError(f"Node source {source_path} has parse errors")

        for node in tree.root_node.named_children:
            if node.type != "node_def":
                continue
            if declared_node is not None:
                raise ValueError(
                    "Node package must declare exactly one node across authored sources; "
                    + f"already saw {declared_node.name!r}, found another in {source_path}"
                )
            declared_node = _load_node_definition(
                node=node,
                source_path=source_path,
                source_rel=source_rel,
            )

    if declared_node is None:
        raise ValueError(
            "Node package must declare exactly one node across authored sources"
        )

    return declared_node


def _load_node_definition(
    *,
    node: Node,
    source_path: Path,
    source_rel: str,
) -> NodeOwnership:
    node_name = _symbol_key(_field_text(node, "name"))
    if not node_name:
        raise ValueError(f"Node declaration has empty name in {source_path}")

    body = node.child_by_field_name("body")
    if body is None:
        raise ValueError(
            f"Node declaration {node_name!r} is missing a body in {source_path}"
        )

    environment_targets: dict[str, NodeEnvironmentTargetOwnership] = {}
    ontology_targets: dict[str, NodeOntologyTargetOwnership] = {}
    service_targets: dict[str, NodeServiceTargetOwnership] = {}
    interface_targets: dict[str, NodeInterfaceTargetOwnership] = {}
    included_node_packages: dict[str, NodePackageIncludeOwnership] = {}

    for child in _iter_node_children(node=body):
        if child.type == "node_include_decl":
            included_package_name = _qualified_text(child.child_by_field_name("target"))
            if not included_package_name:
                raise ValueError(
                    f"Node declaration {node_name!r} has include target with empty package name in {source_path}"
                )
            include_key = included_package_name
            include_dedupe_key = included_package_name.casefold()
            if include_dedupe_key in included_node_packages:
                raise ValueError(
                    f"Node declaration {node_name!r} duplicates included Node package "
                    + f"{included_package_name!r} in {source_path}"
                )
            included_node_packages[include_dedupe_key] = NodePackageIncludeOwnership(
                included_package_name=included_package_name,
                include_key=include_key,
                source_path=source_rel,
            )
            continue
        if child.type == "node_environment_decl":
            environment_target = _load_environment_target(
                node=child,
                node_name=node_name,
                source_path=source_path,
                source_rel=source_rel,
            )
            environment_key = environment_target.environment_handle.casefold()
            if environment_key in environment_targets:
                raise ValueError(
                    f"Node declaration {node_name!r} duplicates environment target "
                    + f"{environment_target.environment_handle!r} in {source_path}"
                )
            environment_targets[environment_key] = environment_target
            continue
        if child.type == "node_ontology_decl":
            package_name = _qualified_text(child.child_by_field_name("target"))
            if not package_name:
                raise ValueError(
                    f"Node declaration {node_name!r} has ontology target with empty package name in {source_path}"
                )
            ontology_key = package_name.casefold()
            if ontology_key in ontology_targets:
                raise ValueError(
                    f"Node declaration {node_name!r} duplicates ontology target "
                    + f"{package_name!r} in {source_path}"
                )
            ontology_targets[ontology_key] = NodeOntologyTargetOwnership(
                package_name=package_name,
                source_path=source_rel,
            )
            continue
        if child.type == "node_service_decl":
            service_target = _load_service_target(
                node=child,
                node_name=node_name,
                source_path=source_path,
                source_rel=source_rel,
            )
            service_name = service_target.service_name
            service_key = service_name.casefold()
            if service_key in service_targets:
                raise ValueError(
                    f"Node declaration {node_name!r} duplicates service target "
                    + f"{service_name!r} in {source_path}"
                )
            service_targets[service_key] = service_target
            continue
        if child.type == "node_interface_decl":
            interface_name = _qualified_text(child.child_by_field_name("target"))
            if not interface_name:
                raise ValueError(
                    f"Node declaration {node_name!r} has interface target with empty name in {source_path}"
                )
            interface_key = interface_name.casefold()
            if interface_key in interface_targets:
                raise ValueError(
                    f"Node declaration {node_name!r} duplicates interface target "
                    + f"{interface_name!r} in {source_path}"
                )
            interface_targets[interface_key] = NodeInterfaceTargetOwnership(
                interface_name=interface_name,
                source_path=source_rel,
            )

    if not (
        included_node_packages
        or environment_targets
        or ontology_targets
        or service_targets
        or interface_targets
    ):
        raise ValueError(
            f"Node declaration {node_name!r} must declare at least one runtime target in {source_path}"
        )

    return NodeOwnership(
        name=node_name,
        source_path=source_rel,
        included_node_packages=tuple(
            sorted(
                included_node_packages.values(),
                key=lambda item: (item.included_package_name, item.source_path),
            )
        ),
        environment_targets=tuple(
            sorted(
                environment_targets.values(),
                key=lambda item: (item.environment_handle, item.source_path),
            )
        ),
        ontology_targets=tuple(
            sorted(
                ontology_targets.values(),
                key=lambda item: (item.package_name, item.source_path),
            )
        ),
        service_targets=tuple(
            sorted(
                service_targets.values(),
                key=lambda item: (item.service_name, item.source_path),
            )
        ),
        interface_targets=tuple(
            sorted(
                interface_targets.values(),
                key=lambda item: (item.interface_name, item.source_path),
            )
        ),
    )


def _iter_node_children(*, node: Node) -> tuple[Node, ...]:
    return _iter_children(
        node=node,
        wrappers={"node_item"},
        allowed={
            "node_include_decl",
            "node_environment_decl",
            "node_ontology_decl",
            "node_service_decl",
            "node_interface_decl",
        },
    )


def _load_environment_target(
    *,
    node: Node,
    node_name: str,
    source_path: Path,
    source_rel: str,
) -> NodeEnvironmentTargetOwnership:
    environment_handle = _qualified_text(node.child_by_field_name("target"))
    if not environment_handle:
        raise ValueError(
            f"Node declaration {node_name!r} has environment target with empty handle in {source_path}"
        )

    body = node.child_by_field_name("body")
    if body is None:
        raise ValueError(
            f"Node declaration {node_name!r} environment target {environment_handle!r} is missing a body "
            + f"in {source_path}"
        )

    profile_decls = _iter_children(
        node=body,
        wrappers={"node_environment_item"},
        allowed={"node_environment_profile_decl"},
    )
    if not profile_decls:
        return NodeEnvironmentTargetOwnership(
            environment_handle=environment_handle,
            profile_mounts=(),
            source_path=source_rel,
        )

    profile_mounts: list[NodeEnvironmentProfileMountOwnership] = []
    seen_mount_keys: set[str] = set()
    for index, profile_decl in enumerate(profile_decls):
        mount = _load_environment_profile_mount(
            profile_decl=profile_decl,
            environment_handle=environment_handle,
            node_name=node_name,
            source_path=source_path,
            source_rel=source_rel,
            position=index,
        )
        mount_dedupe_key = mount.mount_key.casefold()
        if mount_dedupe_key in seen_mount_keys:
            raise ValueError(
                f"Node declaration {node_name!r} environment target {environment_handle!r} duplicates "
                + f"environment profile mount {mount.mount_key!r} in {source_path}"
            )
        seen_mount_keys.add(mount_dedupe_key)
        profile_mounts.append(mount)

    return NodeEnvironmentTargetOwnership(
        environment_handle=environment_handle,
        profile_mounts=tuple(profile_mounts),
        source_path=source_rel,
    )


def _load_environment_profile_mount(
    *,
    profile_decl: Node,
    environment_handle: str,
    node_name: str,
    source_path: Path,
    source_rel: str,
    position: int,
) -> NodeEnvironmentProfileMountOwnership:
    profile_key = _qualified_text(profile_decl.child_by_field_name("profile"))
    if not profile_key:
        raise ValueError(
            f"Node declaration {node_name!r} environment target {environment_handle!r} "
            + f"has empty profile key in {source_path}"
        )
    package_name = _qualified_text(profile_decl.child_by_field_name("package"))
    if not package_name:
        raise ValueError(
            f"Node declaration {node_name!r} environment target {environment_handle!r} "
            + f"profile {profile_key!r} is missing package selector in {source_path}"
        )

    return NodeEnvironmentProfileMountOwnership(
        profile_key=profile_key,
        package_name=package_name,
        mount_key=f"{package_name}:{profile_key}",
        mode="mounted",
        position=position,
        source_path=source_rel,
    )


def _load_service_target(
    *,
    node: Node,
    node_name: str,
    source_path: Path,
    source_rel: str,
) -> NodeServiceTargetOwnership:
    service_name = _qualified_text(node.child_by_field_name("target"))
    if not service_name:
        raise ValueError(
            f"Node declaration {node_name!r} has service target with empty name in {source_path}"
        )

    body = node.child_by_field_name("body")
    if body is None:
        return NodeServiceTargetOwnership(
            service_name=service_name,
            source_path=source_rel,
            code_packages=(),
        )

    package_decls = _iter_children(
        node=body,
        wrappers={"node_service_item"},
        allowed={"node_service_code_package_decl"},
    )
    code_packages: list[NodeServiceCodePackageOwnership] = []
    seen_packages: set[tuple[str, str, str]] = set()
    for package_decl in package_decls:
        slot_key = _symbol_key(_field_text(package_decl, "slot")).casefold()
        package_name = _qualified_text(package_decl.child_by_field_name("package"))
        if not slot_key:
            raise ValueError(
                f"Node declaration {node_name!r} service target {service_name!r} has package "
                + f"activation with empty slot in {source_path}"
            )
        if not package_name:
            raise ValueError(
                f"Node declaration {node_name!r} service target {service_name!r} has package "
                + f"activation with empty package name in {source_path}"
            )
        language = "aware"
        dedupe_key = (slot_key.casefold(), package_name.casefold(), language)
        if dedupe_key in seen_packages:
            raise ValueError(
                f"Node declaration {node_name!r} service target {service_name!r} duplicates "
                + f"package activation {slot_key!r}/{package_name!r} in {source_path}"
            )
        seen_packages.add(dedupe_key)
        code_packages.append(
            NodeServiceCodePackageOwnership(
                slot_key=slot_key,
                package_name=package_name,
                language=language,
                source_path=source_rel,
            )
        )

    return NodeServiceTargetOwnership(
        service_name=service_name,
        source_path=source_rel,
        code_packages=tuple(
            sorted(
                code_packages,
                key=lambda item: (item.slot_key, item.package_name, item.language),
            )
        ),
    )


def _iter_children(
    *, node: Node, wrappers: set[str], allowed: set[str]
) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type in allowed:
            children.append(child)
            continue
        if child.type in wrappers:
            children.extend(
                grandchild
                for grandchild in child.named_children
                if grandchild.is_named and grandchild.type in allowed
            )
    return tuple(children)


def _field_text(node: Node, field: str) -> str:
    target = node.child_by_field_name(field)
    return _qualified_text(target)


def _qualified_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8").strip()


def _symbol_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}"
    )


__all__ = [
    "NodeEnvironmentProfileMountOwnership",
    "NodeEnvironmentTargetOwnership",
    "NodeInterfaceTargetOwnership",
    "NodeOwnership",
    "NodeOntologyTargetOwnership",
    "NodeServiceTargetOwnership",
    "NodeServiceCodePackageOwnership",
    "load_node_ownership_from_sources",
]
