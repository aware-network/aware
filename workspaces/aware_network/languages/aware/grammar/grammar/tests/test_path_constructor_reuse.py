from __future__ import annotations

from pathlib import Path
from uuid import UUID

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_grammar.transformers.aware_to_runtime_transformer import (
    AwareToRuntimeTransformer,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)


CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)


SOURCE = """
class Root {
    branches Branch[]

    fn create_root (
        branch_id UUID,
        lane_id UUID,
    ) -> Branch {
        let ensured_branch = construct branches.create_with_lane_and_branch(
            branch_id = branch_id,
            lane_id = lane_id,
        )
    }
}

class Branch {
    lanes Lane[]
    rels BranchRelationship[]

    branch_id UUID key

    fn create_with_lane_and_branch construct (
        branch_id UUID key,
        lane_id UUID,
    ) -> Branch {
        let created_lane = construct lanes.create(
            lane_id = lane_id,
        )
    }

    fn attach_lane (
        lane_id UUID,
    ) -> Lane {
        let attached_lane = construct lanes.create(
            lane_id = lane_id,
        )
    }

    fn attach_rel (
        target_branch_id UUID,
    ) -> BranchRelationship {
        let attached = construct rels.create(
            target_branch_id = target_branch_id,
        )
    }
}

class Lane {
    lane_id UUID key

    fn create construct (
        lane_id UUID key,
    ) -> Lane {
    }
}

class BranchRelationship {
    target_branch Branch key

    fn create construct (
        target_branch_id UUID key,
    ) -> BranchRelationship {
    }
}
""".strip()


def _build_graph(tmp_path: Path) -> tuple[ObjectConfigGraph, dict[UUID, NamespacePath]]:
    file_path = tmp_path / "path_constructor_reuse.aware"
    file_path.write_text(SOURCE, encoding="utf-8")
    code = build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=str(file_path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )
    namespace_by_code_id = {
        code.id: NamespacePath(package="pkg", namespace="dom.sch"),
    }
    result = build_object_config_graph_from_code(
        name="path_constructor_reuse",
        description="path_constructor_reuse",
        fqn_prefix="pkg",
        file_codes=[(str(file_path), code)],
        namespace_by_code_id=namespace_by_code_id,
    )
    return result.graph, namespace_by_code_id


def _class_by_name(graph: ObjectConfigGraph, name: str) -> ClassConfig:
    for node in graph.object_config_graph_nodes:
        if (
            node.type == ObjectConfigGraphNodeType.class_
            and node.class_config is not None
            and node.class_config.name == name
        ):
            return node.class_config
    raise AssertionError(f"class not found: {name}")


def _function_by_name(cls: ClassConfig, name: str):
    for link in cls.class_config_function_configs:
        if link.function_config.name == name:
            return link.function_config
    raise AssertionError(f"function not found: {cls.name}.{name}")


def test_path_constructor_reuses_existing_owner_scoped_constructor(
    tmp_path: Path,
) -> None:
    graph, namespace_by_code_id = _build_graph(tmp_path)

    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id,
        relationship_loading_config=None,
    ).transform(graph)

    branch = _class_by_name(runtime, "Branch")
    lane = _class_by_name(runtime, "Lane")

    attach_lane = _function_by_name(branch, "attach_lane")
    create_with_lane_and_branch_via_root = _function_by_name(
        branch, "create_with_lane_and_branch_via_root"
    )
    create_via_branch = _function_by_name(lane, "create_via_branch")

    lane_function_names = {
        link.function_config.name for link in lane.class_config_function_configs
    }
    assert lane_function_names == {"create_via_branch"}

    attach_lane_invocation = next(
        inv for inv in attach_lane.invocations if inv.kind.value == "construct"
    )
    assert attach_lane_invocation.target_function_config_id == create_via_branch.id

    nested_invocation = next(
        inv
        for inv in create_with_lane_and_branch_via_root.invocations
        if inv.kind.value == "construct"
    )
    assert nested_invocation.target_function_config_id == create_via_branch.id


def test_path_constructor_stays_scoped_when_target_has_child_mounts_and_runtime_helper(
    tmp_path: Path,
) -> None:
    source = """
class Config {
    targets Target[]

    fn attach_target (
        target_key String
    ) -> Target {
        let target = construct targets.build(
            target_key = target_key,
        )
    }

    fn attach_target_mount (
        target_key String,
        mount_key String
    ) -> Target {
    }
}

class Target {
    environment Environment?
    mounts Mount[]

    target_key String key

    fn build construct (
        target_key String key
    ) -> Target {
    }

    fn add_mount (
        mount_key String
    ) -> Mount {
        let mount = construct mounts.build(
            mount_key = mount_key,
        )
    }
}

class Mount {
    mount_key String key

    fn build construct (
        mount_key String key
    ) -> Mount {
    }
}

class Environment {
    key String key
}
""".strip()
    file_path = tmp_path / "path_constructor_mounts.aware"
    file_path.write_text(source, encoding="utf-8")
    code = build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=str(file_path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )
    namespace_by_code_id = {
        code.id: NamespacePath(package="pkg", namespace="dom.sch"),
    }
    result = build_object_config_graph_from_code(
        name="path_constructor_mounts",
        description="path_constructor_mounts",
        fqn_prefix="pkg",
        file_codes=[(str(file_path), code)],
        namespace_by_code_id=namespace_by_code_id,
    )

    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id,
        relationship_loading_config=None,
    ).transform(result.graph)

    target = _class_by_name(runtime, "Target")
    mount = _class_by_name(runtime, "Mount")

    target_function_names = {
        link.function_config.name for link in target.class_config_function_configs
    }
    assert "build_via_config" in target_function_names
    assert "build" not in target_function_names

    target_ctor = _function_by_name(target, "build_via_config")
    target_inputs = [
        edge.attribute_config.name
        for edge in sorted(
            target_ctor.function_config_attribute_configs,
            key=lambda edge: edge.position,
        )
        if edge.type.value == "input"
    ]
    assert target_inputs == ["config_id", "target_key"]

    mount_function_names = {
        link.function_config.name for link in mount.class_config_function_configs
    }
    assert "build_via_target" in mount_function_names


def test_edge_backed_target_constructor_lowers_to_edge_scoped_via_constructor(
    tmp_path: Path,
) -> None:
    package_source = """
class CodePackage {
    codes aware_code.code.Code[] @CodePackageCode

    fn create_code(
        relative_path String key,
        content String
    ) -> CodePackageCode {
        let created = construct codes.create(
            relative_path = relative_path,
            content = content,
        )
    }
}

edge CodePackageCode {
    relative_path String key

    fn create construct(
        relative_path String key,
        content String
    ) -> CodePackageCode {
        let created_code = construct code.create(
            relative_path = relative_path,
            content = content,
        )
    }
}
""".strip()
    code_source = """
class Code {
    relative_path String key
    content String

    fn create construct(
        relative_path String key,
        content String
    ) -> Code {
    }
}
""".strip()

    package_file = tmp_path / "package.aware"
    code_file = tmp_path / "code.aware"
    package_file.write_text(package_source, encoding="utf-8")
    code_file.write_text(code_source, encoding="utf-8")
    package_code = build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=str(package_file),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )
    code_code = build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=str(code_file),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )
    namespace_by_code_id = {
        package_code.id: NamespacePath(
            package="aware_code", namespace="package"
        ),
        code_code.id: NamespacePath(
            package="aware_code", namespace="code"
        ),
    }
    result = build_object_config_graph_from_code(
        name="edge_target_path_constructor",
        description="edge_target_path_constructor",
        fqn_prefix="aware_code",
        file_codes=[(str(package_file), package_code), (str(code_file), code_code)],
        namespace_by_code_id=namespace_by_code_id,
    )

    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id
    ).transform(result.graph)

    code_package_code = _class_by_name(runtime, "CodePackageCode")
    code = _class_by_name(runtime, "Code")

    edge_function_names = {
        link.function_config.name
        for link in code_package_code.class_config_function_configs
    }
    assert "create_via_code_package" in edge_function_names
    assert "create" not in edge_function_names

    code_function_names = {
        link.function_config.name for link in code.class_config_function_configs
    }
    assert "create_via_code_package_code" in code_function_names
    assert "create" not in code_function_names

    edge_ctor = _function_by_name(code_package_code, "create_via_code_package")
    code_ctor = _function_by_name(code, "create_via_code_package_code")
    invocation = next(
        inv for inv in edge_ctor.invocations if inv.kind.value == "construct"
    )
    assert invocation.target_function_config_id == code_ctor.id
    assert invocation.target_function_config is not None
    assert invocation.target_function_config.name == "create_via_code_package_code"

    code_ctor_inputs = [
        edge.attribute_config.name
        for edge in sorted(
            code_ctor.function_config_attribute_configs, key=lambda edge: edge.position
        )
        if edge.type.value == "input"
    ]
    assert code_ctor_inputs == ["code_package_code_id", "relative_path", "content"]
