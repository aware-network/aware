# @code-under-test: ../aware_meta/function/impl/builder.py
# @code-under-test: ../aware_meta/graph/config/builder.py

from pathlib import Path
from uuid import UUID

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_storage.bucket_handlers import create_blob_store
from aware_storage_ontology.bucket.storage_bucket import StorageBucket
from aware_storage_ontology.bucket.storage_bucket_enums import StorageBackend

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_grammar.transformers.aware_to_runtime_transformer import (
    AwareToRuntimeTransformer,
)

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.function.impl import builder as impl_builder
from aware_meta.function.impl.builder import (
    build_function_impl_from_body,
    build_function_invocation_plan_from_body,
    build_function_invocation_plan_from_impl,
)
from aware_meta.graph.config import builder as ocg_builder
from aware_meta.graph.config.builder import build_object_config_graph_from_code

from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionKind
from aware_meta_ontology.function.function_config_invocation_enums import (
    FunctionInvocationKind,
    FunctionInvocationRootKind,
)
from aware_meta_ontology.function.function_impl import FunctionImpl
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplDeleteTargetKind,
    FunctionImplInstructionType,
    FunctionImplRequireCompareOperator,
    FunctionImplRequireKind,
    FunctionImplValueSourceReadPathRootKind,
    FunctionImplValueSourceKind,
    FunctionImplValueTransformKind,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.stable_ids import (
    stable_class_config_attribute_config_id,
    stable_function_impl_id,
)


def _function_impl_kind_token(function_impl: object) -> str | None:
    raw = getattr(function_impl, "kind", None)
    if raw is None:
        return None
    return str(getattr(raw, "value", raw))


def _build_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content)
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(p),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _build_blob_backed_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content)
    sections_index = CodeSectionBuilderIndex()
    bucket = StorageBucket(
        name="invocation-plan-test",
        backend=StorageBackend.local,
        config={"path_local": str(tmp_path / "blobs")},
    )
    blob_store = create_blob_store(bucket)
    sections_index.set_blob_store(blob_store)
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(p),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
        bucket=bucket,
        blob_store=blob_store,
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


def test_ocg_builder_normalizes_aware_language_value_before_strict_impl_lowering(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "aware_language_value.aware",
        """
class Owner {
    fn attach () -> Owner {
        let value = construct missing_relationship.create()
    }
}
""".strip(),
    )
    code.language = CodeLanguage.aware.value
    ns, domains = _ns(
        fqn_prefix="pkg",
        namespace="default",
        code_ids=[code.id],
    )

    res = build_object_config_graph_from_code(
        name="aware_language_value",
        description="aware_language_value",
        fqn_prefix="pkg",
        file_codes=[("aware_language_value.aware", code)],
        namespace_by_code_id=ns,
    )

    owner = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Owner"
    )
    attach_fn = next(
        edge.function_config
        for edge in owner.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "attach"
    )
    assert attach_fn.function_impl is None
    assert attach_fn.invocations == []


def test_function_invocation_plan_lowering_from_body(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "invocation_plan.aware",
        """
class Child {
    fn step () -> String {}
    fn make construct () -> Child {}
}

class Parent {
    child Child

    fn run () -> String {
        call child.step()
        let built = construct child.make()
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="invocation_plan",
        description="invocation_plan",
        fqn_prefix="pkg",
        file_codes=[("invocation_plan.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )
    invocations = sorted(run_fn.invocations, key=lambda i: i.position)

    assert len(invocations) == 2
    assert [inv.kind for inv in invocations] == [
        FunctionInvocationKind.call,
        FunctionInvocationKind.construct,
    ]
    assert [inv.root_kind for inv in invocations] == [
        FunctionInvocationRootKind.owner,
        FunctionInvocationRootKind.owner,
    ]
    assert [inv.capture_name for inv in invocations] == [None, "built"]
    assert [inv.target_function_config.name for inv in invocations] == ["step", "make"]
    assert [inv.class_config_relationship is not None for inv in invocations] == [
        True,
        True,
    ]

    rel = invocations[0].class_config_relationship
    assert rel is not None
    member_names = [
        rel_attr.attribute_config.name
        for rel_attr in rel.class_config_relationship_attributes
        if rel_attr.attribute_config is not None
    ]
    assert "child" in member_names

    function_impl = build_function_impl_from_body(
        function_config=run_fn,
        owner_class_config=parent,
    )
    assert function_impl is not None
    assert function_impl.id == stable_function_impl_id(function_config_id=run_fn.id)
    assert len(function_impl.instructions) == len(invocations)
    assert [ins.sequence for ins in function_impl.instructions] == [0, 1]

    capture_by_sequence = {inv.position: inv.capture_name for inv in invocations}
    invocations_from_impl = build_function_invocation_plan_from_impl(
        function_config=run_fn,
        function_impl=function_impl,
        capture_name_by_sequence=capture_by_sequence,
    )
    invocations_from_impl = sorted(invocations_from_impl, key=lambda i: i.position)
    assert [inv.kind for inv in invocations_from_impl] == [
        inv.kind for inv in invocations
    ]
    assert [inv.target_function_config_id for inv in invocations_from_impl] == [
        inv.target_function_config_id for inv in invocations
    ]
    assert [inv.class_config_relationship_id for inv in invocations_from_impl] == [
        inv.class_config_relationship_id for inv in invocations
    ]
    assert [inv.capture_name for inv in invocations_from_impl] == [
        inv.capture_name for inv in invocations
    ]


def test_function_invocation_plan_lowering_from_blob_backed_body(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_blob_backed_code(
        tmp_path,
        "invocation_plan_blob.aware",
        """
class Child {
    fn step () -> String {}
}

class Parent {
    child Child

    fn run () -> String {
        call child.step()
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="invocation_plan_blob",
        description="invocation_plan_blob",
        fqn_prefix="pkg",
        file_codes=[("invocation_plan_blob.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )
    invocations = sorted(run_fn.invocations, key=lambda i: i.position)

    assert len(invocations) == 1
    assert invocations[0].kind == FunctionInvocationKind.call
    assert invocations[0].target_function_config is not None
    assert invocations[0].target_function_config.name == "step"


def test_function_invocation_plan_allows_owner_local_call(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "invocation_plan_owner_local.aware",
        """
class Parent {
    fn helper () -> String {}

    fn run () -> String {
        call helper()
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="invocation_plan_owner_local",
        description="invocation_plan_owner_local",
        fqn_prefix="pkg",
        file_codes=[("invocation_plan_owner_local.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )
    invocations = sorted(run_fn.invocations, key=lambda i: i.position)

    assert len(invocations) == 1
    assert invocations[0].kind == FunctionInvocationKind.call
    assert invocations[0].class_config_relationship is None
    assert invocations[0].target_function_config is not None
    assert invocations[0].target_function_config.name == "helper"


def test_function_invocation_plan_mixes_tree_sitter_and_owner_local_fallback(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "invocation_plan_mixed.aware",
        """
class Child {
    fn step () -> String {}
    fn make construct () -> Child {}
}

class Parent {
    child Child

    fn helper () -> String {}

    fn run () -> String {
        call child.step()
        call helper()
        let built = construct child.make()
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="invocation_plan_mixed",
        description="invocation_plan_mixed",
        fqn_prefix="pkg",
        file_codes=[("invocation_plan_mixed.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )
    invocations = sorted(run_fn.invocations, key=lambda i: i.position)

    assert len(invocations) == 3
    assert [inv.kind for inv in invocations] == [
        FunctionInvocationKind.call,
        FunctionInvocationKind.call,
        FunctionInvocationKind.construct,
    ]
    assert [inv.target_function_config.name for inv in invocations] == [
        "step",
        "helper",
        "make",
    ]
    assert [inv.class_config_relationship is not None for inv in invocations] == [
        True,
        False,
        True,
    ]
    assert [inv.capture_name for inv in invocations] == [None, None, "built"]


def test_function_invocation_plan_can_source_from_function_impl_when_enabled(
    tmp_path: Path, monkeypatch
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "invocation_plan_impl_gate.aware",
        """
class Child {
    fn step () -> String {}
    fn make construct () -> Child {}
}

class Parent {
    child Child

    fn run () -> String {
        call child.step()
        let built = construct child.make()
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    monkeypatch.setattr(ocg_builder, "_ENABLE_FUNCTION_IMPL_SHADOW", True)
    monkeypatch.setattr(ocg_builder, "_ENABLE_FUNCTION_IMPL_INVOCATION_SOURCE", True)

    res = build_object_config_graph_from_code(
        name="invocation_plan_impl_gate",
        description="invocation_plan_impl_gate",
        fqn_prefix="pkg",
        file_codes=[("invocation_plan_impl_gate.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )
    invocations = sorted(run_fn.invocations, key=lambda i: i.position)
    assert len(invocations) == 2
    assert [inv.capture_name for inv in invocations] == [None, "built"]
    assert run_fn.function_impl is not None
    assert len(run_fn.function_impl.instructions) == 2


def test_function_invocation_plan_fails_on_unresolved_receiver_path(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "invocation_plan_invalid_receiver.aware",
        """
class Child {
    fn step () -> String {}
}

class Parent {
    child Child

    fn run () -> String {
        call Child.step()
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="invocation_plan_invalid_receiver",
        description="invocation_plan_invalid_receiver",
        fqn_prefix="pkg",
        file_codes=[("invocation_plan_invalid_receiver.aware", code)],
        namespace_by_code_id=ns,
    )
    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    with pytest.raises(
        ValueError, match=r"Unresolved function invocation\(s\) in Parent.run"
    ):
        build_function_invocation_plan_from_body(
            function_config=run_fn,
            owner_class_config=parent,
        )


def test_function_invocation_plan_fails_on_multi_hop_receiver_path(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "invocation_plan_invalid_multihop.aware",
        """
class Leaf {
    fn step () -> String {}
}

class Child {
    leaf Leaf
}

class Parent {
    child Child

    fn run () -> String {
        call child.leaf.step()
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="invocation_plan_invalid_multihop",
        description="invocation_plan_invalid_multihop",
        fqn_prefix="pkg",
        file_codes=[("invocation_plan_invalid_multihop.aware", code)],
        namespace_by_code_id=ns,
    )
    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    with pytest.raises(
        ValueError, match=r"Unresolved function invocation\(s\) in Parent.run"
    ):
        build_function_invocation_plan_from_body(
            function_config=run_fn,
            owner_class_config=parent,
        )


def test_function_invocation_plan_fails_closed_on_function_body_parse_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "invocation_plan_parse_error_gate.aware",
        """
class Child {
    fn step () -> String {}
}

class Parent {
    child Child

    fn run () -> String {
        call child.step()
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    original_parse = impl_builder.parse_function_invocations_from_block

    def _raise_parse_error(body_text: str):
        if "call child.step()" in (body_text or ""):
            raise impl_builder.FunctionParseError(
                "Aware function body source contains parse errors"
            )
        if original_parse is None:
            return ()
        return original_parse(body_text)

    monkeypatch.setattr(
        impl_builder,
        "parse_function_invocations_from_block",
        _raise_parse_error,
    )

    res = build_object_config_graph_from_code(
        name="invocation_plan_parse_error_gate",
        description="invocation_plan_parse_error_gate",
        fqn_prefix="pkg",
        file_codes=[("invocation_plan_parse_error_gate.aware", code)],
        namespace_by_code_id=ns,
    )
    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    with pytest.raises(
        ValueError, match=r"Unresolved function invocation\(s\) in Parent.run"
    ):
        build_function_invocation_plan_from_body(
            function_config=run_fn,
            owner_class_config=parent,
        )


def test_function_invocation_plan_fails_closed_when_parser_unavailable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "invocation_plan_parser_unavailable.aware",
        """
class Child {
    fn step () -> String {}
}

class Parent {
    child Child

    fn run () -> String {
        call child.step()
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    monkeypatch.setattr(
        impl_builder,
        "parse_function_invocations_from_block",
        None,
    )

    res = build_object_config_graph_from_code(
        name="invocation_plan_parser_unavailable",
        description="invocation_plan_parser_unavailable",
        fqn_prefix="pkg",
        file_codes=[("invocation_plan_parser_unavailable.aware", code)],
        namespace_by_code_id=ns,
    )
    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    with pytest.raises(ValueError, match=r"function invocation parser is unavailable"):
        build_function_invocation_plan_from_body(
            function_config=run_fn,
            owner_class_config=parent,
        )


def test_function_invocation_plan_construct_prefers_association_edge_constructor(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "invocation_plan_assoc.aware",
        """
class Child {
    fn make construct () -> Child {}
    fn step () -> String {}
}

edge Link {
    fn make construct () -> Link {}
}

class Parent {
    children Child[] @Link

    fn run () -> String {
        let built = construct children.make()
        call children.step()
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="invocation_plan_assoc",
        description="invocation_plan_assoc",
        fqn_prefix="pkg",
        file_codes=[("invocation_plan_assoc.aware", code)],
        namespace_by_code_id=ns,
    )

    class_by_name = {
        n.class_config.name: n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_ and n.class_config is not None
    }
    parent = class_by_name["Parent"]
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )
    invocations = sorted(run_fn.invocations, key=lambda i: i.position)
    assert len(invocations) == 2

    fn_owner_by_id: dict[UUID, str] = {}
    for cls in class_by_name.values():
        for link in cls.class_config_function_configs:
            fn = link.function_config
            if fn is None:
                continue
            fn_owner_by_id[fn.id] = cls.name

    construct_inv = next(
        inv for inv in invocations if inv.kind == FunctionInvocationKind.construct
    )
    call_inv = next(
        inv for inv in invocations if inv.kind == FunctionInvocationKind.call
    )

    assert construct_inv.target_function_config is not None
    assert construct_inv.target_function_config.name == "make"
    assert fn_owner_by_id[construct_inv.target_function_config.id] == "Link"

    assert call_inv.target_function_config is not None
    assert call_inv.target_function_config.name == "step"


def test_runtime_transform_completes_edge_endpoint_invocation_resolution(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "runtime_edge_endpoint_resolution.aware",
        """
class Code {
    fn create construct(relative_path String key) -> Code {}
}

class CodePackage {
    codes Code[] @CodePackageCode

    fn create_code(relative_path String key) -> CodePackageCode {
        let created = construct codes.create(relative_path = relative_path)
    }
}

edge CodePackageCode {
    fn create construct(relative_path String key) -> CodePackageCode {
        let created_code = construct code.create(relative_path = relative_path)
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    built = build_object_config_graph_from_code(
        name="runtime_edge_endpoint_resolution",
        description="runtime_edge_endpoint_resolution",
        fqn_prefix="pkg",
        file_codes=[("runtime_edge_endpoint_resolution.aware", code)],
        namespace_by_code_id=ns,
    )

    canonical_class_by_name = {
        n.class_config.name: n.class_config
        for n in built.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_ and n.class_config is not None
    }
    canonical_edge = canonical_class_by_name["CodePackageCode"]
    canonical_create = next(
        edge.function_config
        for edge in canonical_edge.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "create"
    )
    assert canonical_create.invocations == []
    assert canonical_create.function_impl is None

    runtime = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)
    runtime_class_by_name = {
        n.class_config.name: n.class_config
        for n in runtime.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_ and n.class_config is not None
    }

    code_package = runtime_class_by_name["CodePackage"]
    code_package_create = next(
        edge.function_config
        for edge in code_package.class_config_function_configs
        if edge.function_config is not None
        and edge.function_config.name == "create_code"
    )
    assert len(code_package_create.invocations) == 1
    assert code_package_create.invocations[0].target_function_config is not None
    assert (
        code_package_create.invocations[0].target_function_config.name
        == "create_via_code_package"
    )

    runtime_edge = runtime_class_by_name["CodePackageCode"]
    runtime_fn_by_name = {
        edge.function_config.name: edge.function_config
        for edge in runtime_edge.class_config_function_configs
        if edge.function_config is not None
    }
    assert "create" not in runtime_fn_by_name
    path_create = runtime_fn_by_name["create_via_code_package"]
    assert path_create.function_impl is not None
    assert _function_impl_kind_token(path_create.function_impl) == "instruction_body"
    assert len(path_create.invocations) == 1

    runtime_code = runtime_class_by_name["Code"]
    runtime_code_fn_by_name = {
        edge.function_config.name: edge.function_config
        for edge in runtime_code.class_config_function_configs
        if edge.function_config is not None
    }
    runtime_code_attr_by_name = {
        edge.attribute_config.name: edge
        for edge in runtime_code.class_config_attribute_configs
        if edge.attribute_config is not None
    }
    assert "create" not in runtime_code_fn_by_name
    assert "create_via_code_package_code" in runtime_code_fn_by_name
    runtime_code_path_create = runtime_code_fn_by_name["create_via_code_package_code"]
    assert runtime_code_path_create.function_impl is not None
    assert (
        _function_impl_kind_token(runtime_code_path_create.function_impl)
        == "auto_constructor"
    )
    assert "code_package_code_id" in runtime_code_attr_by_name
    assert runtime_code_attr_by_name["code_package_code_id"].is_identity_key is True

    invocation = path_create.invocations[0]
    assert invocation.target_function_config is not None
    assert invocation.target_function_config.name == "create_via_code_package_code"
    assert (
        invocation.target_function_config_id
        == runtime_code_fn_by_name["create_via_code_package_code"].id
    )
    assert invocation.class_config_relationship is not None
    assert invocation.class_config_relationship.target_class_config is not None
    assert invocation.class_config_relationship.target_class_config.name == "Code"

    runtime_code_path_inputs = [
        edge
        for edge in sorted(
            runtime_code_fn_by_name[
                "create_via_code_package_code"
            ].function_config_attribute_configs,
            key=lambda edge: edge.position,
        )
        if edge.attribute_config is not None and edge.type.value == "input"
    ]
    assert runtime_code_path_inputs[0].attribute_config.name == "code_package_code_id"
    assert runtime_code_path_inputs[0].is_identity_key is True


def test_function_impl_lowering_emits_set_and_require_with_typed_sources(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_set_require.aware",
        """
class Parent {
    display_name String

    fn run(name String) -> String {
        let alias = name
        set display_name = alias
        require exists(alias) message "alias is required"
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_set_require",
        description="function_impl_set_require",
        fqn_prefix="pkg",
        file_codes=[("function_impl_set_require.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    function_impl = build_function_impl_from_body(
        function_config=run_fn,
        owner_class_config=parent,
    )
    assert function_impl is not None

    instructions = sorted(
        function_impl.instructions, key=lambda ins: (ins.sequence, ins.type.value)
    )
    assert [ins.type for ins in instructions] == [
        FunctionImplInstructionType.let,
        FunctionImplInstructionType.set,
        FunctionImplInstructionType.require,
    ]

    let_instruction = instructions[0]
    assert let_instruction.instruction_let is not None
    assert let_instruction.instruction_let.name == "alias"

    set_instruction = instructions[1]
    assert set_instruction.instruction_set is not None
    assert (
        set_instruction.instruction_set.target_class_config_attribute_config is not None
    )
    assert (
        set_instruction.instruction_set.target_class_config_attribute_config.attribute_config.name
        == "display_name"
    )
    assert set_instruction.instruction_set.value_source is not None
    assert (
        set_instruction.instruction_set.value_source.kind
        == FunctionImplValueSourceKind.let_ref
    )

    require_instruction = instructions[2]
    assert require_instruction.instruction_require is not None
    assert (
        require_instruction.instruction_require.kind == FunctionImplRequireKind.exists
    )
    assert require_instruction.instruction_require.message == "alias is required"
    assert len(require_instruction.instruction_require.operands) == 1
    assert (
        require_instruction.instruction_require.operands[0].value_source.kind
        == FunctionImplValueSourceKind.let_ref
    )


def test_function_impl_lowering_emits_delete_self_instruction(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_delete_self.aware",
        """
class Parent {
    fn delete_me() -> Parent {
        delete self
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_delete_self",
        description="function_impl_delete_self",
        fqn_prefix="pkg",
        file_codes=[("function_impl_delete_self.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    delete_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "delete_me"
    )

    function_impl = build_function_impl_from_body(
        function_config=delete_fn,
        owner_class_config=parent,
    )
    assert function_impl is not None

    instructions = sorted(
        function_impl.instructions, key=lambda ins: (ins.sequence, ins.type.value)
    )
    assert [ins.type for ins in instructions] == [FunctionImplInstructionType.delete]
    delete_instruction = instructions[0]
    assert delete_instruction.instruction_delete is not None
    assert (
        delete_instruction.instruction_delete.target_kind
        == FunctionImplDeleteTargetKind.self
    )
    assert delete_instruction.value_sources == []


def test_function_impl_lowering_rejects_non_self_delete_target(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_delete_other.aware",
        """
class Child {}

class Parent {
    child Child

    fn delete_child() -> Parent {
        delete child
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_delete_other",
        description="function_impl_delete_other",
        fqn_prefix="pkg",
        file_codes=[("function_impl_delete_other.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    delete_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None
        and edge.function_config.name == "delete_child"
    )

    with pytest.raises(
        ValueError,
        match=(
            r"(delete target must be `self`|statement could not be parsed|"
            r"function body parse error)"
        ),
    ):
        build_function_impl_from_body(
            function_config=delete_fn,
            owner_class_config=parent,
        )


def test_function_impl_lowering_accepts_enum_set_token(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_enum_set.aware",
        """
enum GoalStatus {
    active
    blocked
}

class Goal {
    status GoalStatus = active

    fn block() -> Goal {
        set status = blocked
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_enum_set",
        description="function_impl_enum_set",
        fqn_prefix="pkg",
        file_codes=[("function_impl_enum_set.aware", code)],
        namespace_by_code_id=ns,
    )

    goal = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Goal"
    )
    block_fn = next(
        edge.function_config
        for edge in goal.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "block"
    )

    function_impl = build_function_impl_from_body(
        function_config=block_fn,
        owner_class_config=goal,
    )
    assert function_impl is not None

    [instruction] = function_impl.instructions
    assert instruction.type == FunctionImplInstructionType.set
    assert instruction.instruction_set is not None
    value_source = instruction.instruction_set.value_source
    assert value_source is not None
    assert value_source.kind == FunctionImplValueSourceKind.literal
    assert value_source.source_literal_primitive is not None
    assert value_source.source_literal_primitive.value == {"value": "blocked"}


def test_function_impl_lowering_accepts_enum_lifecycle_guard(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_enum_lifecycle_guard.aware",
        """
enum GoalStatus {
    proposed
    active
    blocked
    parked
    achieved
}

class Goal {
    status GoalStatus = proposed

    fn activate() -> Goal {
        let current_status = status
        require member(current_status, list.of(proposed, parked, blocked)) message "goal status cannot activate"
        set status = active
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_enum_lifecycle_guard",
        description="function_impl_enum_lifecycle_guard",
        fqn_prefix="pkg",
        file_codes=[("function_impl_enum_lifecycle_guard.aware", code)],
        namespace_by_code_id=ns,
    )

    goal = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Goal"
    )
    activate_fn = next(
        edge.function_config
        for edge in goal.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "activate"
    )

    function_impl = build_function_impl_from_body(
        function_config=activate_fn,
        owner_class_config=goal,
    )
    assert function_impl is not None

    instructions = sorted(function_impl.instructions, key=lambda item: item.sequence)
    assert [instruction.type for instruction in instructions] == [
        FunctionImplInstructionType.let,
        FunctionImplInstructionType.require,
        FunctionImplInstructionType.set,
    ]
    assert instructions[0].instruction_let is not None
    assert instructions[0].instruction_let.value_expr == {
        "kind": "reference",
        "name": "status",
    }

    require = instructions[1].instruction_require
    assert require is not None
    assert require.kind == FunctionImplRequireKind.member
    assert require.message == "goal status cannot activate"
    assert [operand.value_source.kind for operand in require.operands] == [
        FunctionImplValueSourceKind.let_ref,
        FunctionImplValueSourceKind.literal,
    ]
    accepted_values = require.operands[1].value_source.source_literal_primitive
    assert accepted_values is not None
    assert accepted_values.value == {"value": ["proposed", "parked", "blocked"]}

    set_payload = instructions[2].instruction_set
    assert set_payload is not None
    assert set_payload.value_source.kind == FunctionImplValueSourceKind.literal
    assert set_payload.value_source.source_literal_primitive is not None
    assert set_payload.value_source.source_literal_primitive.value == {
        "value": "active"
    }


def test_function_impl_lowering_emits_transform_value_source_for_let(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_transform_value_source.aware",
        """
class Parent {
    display_name String

    fn run(name String) -> String {
        let normalized = text.casefold(text.strip(name))
        set display_name = normalized
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_transform_value_source",
        description="function_impl_transform_value_source",
        fqn_prefix="pkg",
        file_codes=[("function_impl_transform_value_source.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    function_impl = build_function_impl_from_body(
        function_config=run_fn,
        owner_class_config=parent,
    )
    assert function_impl is not None

    instructions = sorted(
        function_impl.instructions, key=lambda ins: (ins.sequence, ins.type.value)
    )
    assert [ins.type for ins in instructions] == [
        FunctionImplInstructionType.let,
        FunctionImplInstructionType.set,
    ]

    let_instruction = instructions[0]
    assert let_instruction.instruction_let is not None
    assert let_instruction.instruction_let.value_expr["kind"] == "value_source"
    assert len(let_instruction.value_sources) == 1
    root_source = let_instruction.value_sources[0]
    assert root_source.key == "value"
    assert root_source.kind == FunctionImplValueSourceKind.transform
    assert root_source.source_transform is not None
    assert (
        root_source.source_transform.operation
        == FunctionImplValueTransformKind.text_casefold
    )
    assert len(root_source.source_transform.operands) == 1

    strip_source = root_source.source_transform.operands[0].value_source
    assert strip_source.kind == FunctionImplValueSourceKind.transform
    assert strip_source.source_transform is not None
    assert (
        strip_source.source_transform.operation
        == FunctionImplValueTransformKind.text_strip
    )
    assert len(strip_source.source_transform.operands) == 1

    input_source = strip_source.source_transform.operands[0].value_source
    assert input_source.kind == FunctionImplValueSourceKind.function_input_ref
    set_instruction = instructions[1]
    assert set_instruction.instruction_set is not None
    assert (
        set_instruction.instruction_set.value_source.kind
        == FunctionImplValueSourceKind.let_ref
    )


def test_function_impl_lowering_resolves_relationship_reference_set_target(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_relationship_set.aware",
        """
class TvChannel {
    name String key
}

class Tv {
    active_channel TvChannel?

    fn set_active_channel(active_channel_id UUID) -> Tv {
        set active_channel = active_channel_id
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_relationship_set",
        description="function_impl_relationship_set",
        fqn_prefix="pkg",
        file_codes=[("function_impl_relationship_set.aware", code)],
        namespace_by_code_id=ns,
    )

    tv = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Tv"
    )
    run_fn = next(
        edge.function_config
        for edge in tv.class_config_function_configs
        if edge.function_config is not None
        and edge.function_config.name == "set_active_channel"
    )

    function_impl = build_function_impl_from_body(
        function_config=run_fn,
        owner_class_config=tv,
    )
    assert function_impl is not None

    instructions = sorted(
        function_impl.instructions, key=lambda ins: (ins.sequence, ins.type.value)
    )
    assert [ins.type for ins in instructions] == [FunctionImplInstructionType.set]

    set_instruction = instructions[0]
    assert set_instruction.instruction_set is not None
    target_link = set_instruction.instruction_set.target_class_config_attribute_config
    assert target_link is not None
    assert target_link.class_config_id == tv.id
    assert target_link.attribute_config is not None
    assert target_link.attribute_config.name == "active_channel"
    assert target_link.attribute_config_id is not None
    assert target_link.id == stable_class_config_attribute_config_id(
        class_config_id=tv.id,
        attribute_config_id=target_link.attribute_config_id,
    )
    value_source = set_instruction.instruction_set.value_source
    assert value_source is not None
    assert value_source.kind == FunctionImplValueSourceKind.function_input_ref


def test_function_impl_lowering_emits_explicit_construct_instruction_and_skips_invocation_plan(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_explicit_construct.aware",
        """
class Home {
    name String
    is_on Bool = false

    fn ping () -> String {}

    fn run(label String) -> Home {
        let created = construct Home(name = label, is_on = true)
        call ping()
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_explicit_construct",
        description="function_impl_explicit_construct",
        fqn_prefix="pkg",
        file_codes=[("function_impl_explicit_construct.aware", code)],
        namespace_by_code_id=ns,
    )

    home = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Home"
    )
    run_fn = next(
        edge.function_config
        for edge in home.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    invocations = sorted(run_fn.invocations, key=lambda i: i.position)
    assert len(invocations) == 1
    assert invocations[0].kind == FunctionInvocationKind.call
    assert invocations[0].target_function_config is not None
    assert invocations[0].target_function_config.name == "ping"

    function_impl = build_function_impl_from_body(
        function_config=run_fn,
        owner_class_config=home,
    )
    assert function_impl is not None
    instructions = sorted(
        function_impl.instructions, key=lambda ins: (ins.sequence, ins.type.value)
    )
    assert [ins.type for ins in instructions] == [
        FunctionImplInstructionType.construct,
        FunctionImplInstructionType.invoke,
    ]

    construct_instruction = instructions[0]
    assert construct_instruction.instruction_construct is not None
    assert construct_instruction.instruction_construct.target_class_config is not None
    assert (
        construct_instruction.instruction_construct.target_class_config.name == "Home"
    )
    assignment_by_name = {
        assignment.target_class_config_attribute_config.attribute_config.name: assignment
        for assignment in construct_instruction.instruction_construct.assignments
        if assignment.target_class_config_attribute_config is not None
        and assignment.target_class_config_attribute_config.attribute_config is not None
    }
    assert set(assignment_by_name) == {"name", "is_on"}
    assert (
        assignment_by_name["name"].value_source.kind
        == FunctionImplValueSourceKind.function_input_ref
    )
    assert (
        assignment_by_name["is_on"].value_source.kind
        == FunctionImplValueSourceKind.literal
    )


def test_constructor_function_impl_shadow_is_materialized_without_gate(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_constructor_shadow.aware",
        """
class Home {
    name String

    fn build construct(label String) -> Home {
        let created = construct Home(name = label)
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_constructor_shadow",
        description="function_impl_constructor_shadow",
        fqn_prefix="pkg",
        file_codes=[("function_impl_constructor_shadow.aware", code)],
        namespace_by_code_id=ns,
    )

    home = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Home"
    )
    build_fn = next(
        edge.function_config
        for edge in home.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "build"
    )

    assert build_fn.function_impl is not None
    assert _function_impl_kind_token(build_fn.function_impl) == "instruction_body"
    instructions = sorted(
        build_fn.function_impl.instructions,
        key=lambda ins: (ins.sequence, ins.type.value),
    )
    assert [ins.type for ins in instructions] == [FunctionImplInstructionType.construct]
    assert instructions[0].instruction_construct is not None
    assert instructions[0].instruction_construct.target_class_config is not None
    assert instructions[0].instruction_construct.target_class_config.name == "Home"


def test_bodyless_constructor_function_impl_kind_is_auto_constructor(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_bodyless_constructor_kind.aware",
        '''
class Home {
    name String key

    fn build construct(name String key) -> Home {
        """
        Build a Home through constructor identity rails.
        """
    }
}
'''.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_bodyless_constructor_kind",
        description="function_impl_bodyless_constructor_kind",
        fqn_prefix="pkg",
        file_codes=[("function_impl_bodyless_constructor_kind.aware", code)],
        namespace_by_code_id=ns,
    )

    home = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Home"
    )
    build_fn = next(
        edge.function_config
        for edge in home.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "build"
    )

    assert build_fn.function_impl is not None
    assert build_fn.function_impl.instructions == []
    assert _function_impl_kind_token(build_fn.function_impl) == "auto_constructor"


def test_existing_bodyless_constructor_shell_kind_normalizes_at_edge() -> None:
    function_config = FunctionConfig(
        id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        owner_key="pkg.dom.default.Home",
        name="build",
        verb="construct",
        kind=FunctionKind.instance,
    )
    function_impl = FunctionImpl(
        id=stable_function_impl_id(function_config_id=function_config.id),
        key="default",
        function_config_id=function_config.id,
    )

    assert _function_impl_kind_token(function_impl) == "instruction_body"

    impl_builder.apply_function_impl_kind(
        function_config=function_config,
        function_impl=function_impl,
        is_constructor=True,
    )

    assert function_impl.instructions == []
    assert _function_impl_kind_token(function_impl) == "auto_constructor"


def test_instruction_body_function_impl_kind_is_instruction_body(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_instruction_body_kind.aware",
        """
class Home {
    display_name String

    fn rename(label String) -> Home {
        set display_name = label
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_instruction_body_kind",
        description="function_impl_instruction_body_kind",
        fqn_prefix="pkg",
        file_codes=[("function_impl_instruction_body_kind.aware", code)],
        namespace_by_code_id=ns,
    )

    home = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Home"
    )
    rename_fn = next(
        edge.function_config
        for edge in home.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "rename"
    )

    function_impl = build_function_impl_from_body(
        function_config=rename_fn,
        owner_class_config=home,
    )
    assert function_impl is not None
    assert len(function_impl.instructions) == 1
    assert _function_impl_kind_token(function_impl) == "instruction_body"


def test_function_impl_lowering_rejects_ambiguous_construct_class_vs_owner_function(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_explicit_construct_ambiguous.aware",
        """
class Home {
    name String

    fn Home construct(name String) -> Home {}

    fn run(label String) -> Home {
        let created = construct Home(name = label)
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="function_impl_explicit_construct_ambiguous",
        description="function_impl_explicit_construct_ambiguous",
        fqn_prefix="pkg",
        file_codes=[("function_impl_explicit_construct_ambiguous.aware", code)],
        namespace_by_code_id=ns,
    )
    home = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Home"
    )
    run_fn = next(
        edge.function_config
        for edge in home.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    with pytest.raises(
        ValueError,
        match=r"construct target 'Home' is ambiguous between class construction and owner-local function invocation",
    ):
        build_function_invocation_plan_from_body(
            function_config=run_fn,
            owner_class_config=home,
        )


def test_function_impl_lowering_emits_invoke_attribute_bindings(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_invoke_args.aware",
        """
class Child {
    fn make construct(name String, score Int, is_ready Bool) -> Child {}
}

class Parent {
    child Child

    fn run(alias String) -> Child {
        let created = construct child.make(name = alias, score = 1, true)
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_invoke_args",
        description="function_impl_invoke_args",
        fqn_prefix="pkg",
        file_codes=[("function_impl_invoke_args.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    function_impl = build_function_impl_from_body(
        function_config=run_fn,
        owner_class_config=parent,
    )
    assert function_impl is not None

    invoke_instruction = next(
        ins
        for ins in function_impl.instructions
        if ins.type == FunctionImplInstructionType.invoke
    )
    invoke_payload = invoke_instruction.instruction_invoke
    assert invoke_payload is not None
    assert len(invoke_payload.attribute_configs) == 3

    by_attr_name = {
        binding.attribute_config.name: binding
        for binding in invoke_payload.attribute_configs
        if binding.attribute_config is not None
    }
    assert set(by_attr_name) == {"name", "score", "is_ready"}
    assert by_attr_name["name"].value_expr == {"kind": "reference", "name": "alias"}
    assert by_attr_name["score"].value_expr == {"kind": "literal", "value": 1}
    assert by_attr_name["is_ready"].value_expr == {"kind": "literal", "value": True}


def test_function_impl_lowering_accepts_construct_capture_identity_reference(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_construct_capture_id.aware",
        """
class Child {
    fn make construct() -> Child {}
}

edge Link {
    fn make construct() -> Link {}
}

class Parent {
    children Child[] @Link

    fn consume(content_id UUID) -> UUID {}

    fn append() -> UUID {
        let content = construct children.make()
        call consume(content_id = content.id)
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_construct_capture_id",
        description="function_impl_construct_capture_id",
        fqn_prefix="pkg",
        file_codes=[("function_impl_construct_capture_id.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    append_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "append"
    )

    function_impl = build_function_impl_from_body(
        function_config=append_fn,
        owner_class_config=parent,
    )
    assert function_impl is not None
    invoke_payloads = [
        instruction.instruction_invoke
        for instruction in sorted(function_impl.instructions, key=lambda item: item.sequence)
        if instruction.type == FunctionImplInstructionType.invoke
        and instruction.instruction_invoke is not None
    ]
    assert [payload.target_function_config.name for payload in invoke_payloads] == [
        "make",
        "consume",
    ]
    consume_payload = invoke_payloads[1]
    content_id_binding = next(
        binding
        for binding in consume_payload.attribute_configs
        if binding.attribute_config is not None
        and binding.attribute_config.name == "content_id"
    )
    assert content_id_binding.value_expr == {
        "kind": "reference",
        "name": "content.id",
    }


def test_function_impl_lowering_accepts_owner_attribute_and_dotted_input_references(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_invoke_owner_and_input_path.aware",
        """
class Result : inline_value {
    lane String
    semantics String?
}

class Child {
    fn make construct(compile_index Int, lane String, semantics String? = null) -> Child {}
}

class Parent {
    child Child
    next_compile_index Int = 1

    fn run(result Result) -> Child {
        let created = construct child.make(
            compile_index = next_compile_index,
            lane = result.lane,
            semantics = result.semantics,
        )
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_invoke_owner_and_input_path",
        description="function_impl_invoke_owner_and_input_path",
        fqn_prefix="pkg",
        file_codes=[("function_impl_invoke_owner_and_input_path.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    function_impl = build_function_impl_from_body(
        function_config=run_fn,
        owner_class_config=parent,
    )
    assert function_impl is not None

    invoke_instruction = next(
        ins
        for ins in function_impl.instructions
        if ins.type == FunctionImplInstructionType.invoke
    )
    invoke_payload = invoke_instruction.instruction_invoke
    assert invoke_payload is not None
    assert len(invoke_payload.attribute_configs) == 3

    by_attr_name = {
        binding.attribute_config.name: binding
        for binding in invoke_payload.attribute_configs
        if binding.attribute_config is not None
    }
    assert set(by_attr_name) == {"compile_index", "lane", "semantics"}
    assert by_attr_name["compile_index"].value_expr == {
        "kind": "reference",
        "name": "next_compile_index",
    }
    assert by_attr_name["lane"].value_expr == {
        "kind": "reference",
        "name": "result.lane",
    }
    assert by_attr_name["semantics"].value_expr == {
        "kind": "reference",
        "name": "result.semantics",
    }


def test_function_impl_lowering_accepts_relationship_object_id_argument_source(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_relationship_object_id_argument_source.aware",
        """
class Child {
    name String key
}

class Request {
    child Child key
}

class Receipt {
    child_id UUID key

    fn create construct(child_id UUID key) -> Receipt {}
}

class Parent {
    request Request unique
    receipts Receipt[]

    fn create_receipt() -> Receipt {
        let created = construct receipts.create(
            child_id = request.child.id,
        )
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_relationship_object_id_argument_source",
        description="function_impl_relationship_object_id_argument_source",
        fqn_prefix="pkg",
        file_codes=[
            ("function_impl_relationship_object_id_argument_source.aware", code)
        ],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    create_receipt_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None
        and edge.function_config.name == "create_receipt"
    )

    function_impl = build_function_impl_from_body(
        function_config=create_receipt_fn,
        owner_class_config=parent,
    )
    assert function_impl is not None

    invoke_instruction = next(
        ins
        for ins in function_impl.instructions
        if ins.type == FunctionImplInstructionType.invoke
    )
    invoke_payload = invoke_instruction.instruction_invoke
    assert invoke_payload is not None
    by_attr_name = {
        binding.attribute_config.name: binding
        for binding in invoke_payload.attribute_configs
        if binding.attribute_config is not None
    }
    assert by_attr_name["child_id"].value_expr == {
        "kind": "reference",
        "name": "request.child.id",
    }


def test_function_impl_lowering_emits_read_path_value_sources(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_read_path_value_sources.aware",
        """
class Patch : inline_value {
    text_after String
}

class Child {
    label String
}

class Parent {
    child Child
    display_name String

    fn apply(patch Patch) -> Parent {
        let local_patch = patch
        set display_name = local_patch.text_after
        require equals(patch.text_after, child.label) message "patch must match child label"
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_read_path_value_sources",
        description="function_impl_read_path_value_sources",
        fqn_prefix="pkg",
        file_codes=[("function_impl_read_path_value_sources.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    apply_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "apply"
    )

    function_impl = build_function_impl_from_body(
        function_config=apply_fn,
        owner_class_config=parent,
    )
    assert function_impl is not None

    instructions = sorted(function_impl.instructions, key=lambda item: item.sequence)
    assert [instruction.type for instruction in instructions] == [
        FunctionImplInstructionType.let,
        FunctionImplInstructionType.set,
        FunctionImplInstructionType.require,
    ]

    set_payload = instructions[1].instruction_set
    assert set_payload is not None
    set_source = set_payload.value_source
    assert set_source.kind == FunctionImplValueSourceKind.read_path
    assert set_source.source_read_path is not None
    assert (
        set_source.source_read_path.root_kind
        == FunctionImplValueSourceReadPathRootKind.let_binding
    )
    assert set_source.source_read_path.root_instruction_let is not None
    assert set_source.source_read_path.root_instruction_let.name == "local_patch"
    assert [
        segment.attribute_config.name
        for segment in set_source.source_read_path.segments
    ] == ["text_after"]

    require_payload = instructions[2].instruction_require
    assert require_payload is not None
    operand_sources = [
        operand.value_source
        for operand in sorted(require_payload.operands, key=lambda item: item.position)
    ]
    assert [source.kind for source in operand_sources] == [
        FunctionImplValueSourceKind.read_path,
        FunctionImplValueSourceKind.read_path,
    ]
    assert operand_sources[0].source_read_path is not None
    assert (
        operand_sources[0].source_read_path.root_kind
        == FunctionImplValueSourceReadPathRootKind.function_input
    )
    assert [
        segment.attribute_config.name
        for segment in operand_sources[0].source_read_path.segments
    ] == ["text_after"]
    assert operand_sources[1].source_read_path is not None
    assert (
        operand_sources[1].source_read_path.root_kind
        == FunctionImplValueSourceReadPathRootKind.target_attribute
    )
    assert [
        segment.attribute_config.name
        for segment in operand_sources[1].source_read_path.segments
    ] == ["label"]


def test_function_impl_lowering_allows_invoke_capture_reference_in_later_construct(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_invoke_capture.aware",
        """
class Child {
    fn make_id(name String) -> UUID {}
}

class Entry {
    foreign_id UUID

    fn create construct(foreign_id UUID) -> Entry {}
}

class Parent {
    child Child
    entries Entry[]

    fn run(alias String) -> Entry {
        let generated_id = call child.make_id(name = alias)
        let created = construct entries.create(foreign_id = generated_id)
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_invoke_capture",
        description="function_impl_invoke_capture",
        fqn_prefix="pkg",
        file_codes=[("function_impl_invoke_capture.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    function_impl = build_function_impl_from_body(
        function_config=run_fn,
        owner_class_config=parent,
    )
    assert function_impl is not None

    invoke_instructions = [
        ins
        for ins in function_impl.instructions
        if ins.type == FunctionImplInstructionType.invoke
    ]
    assert len(invoke_instructions) == 2
    second_invoke = invoke_instructions[1].instruction_invoke
    assert second_invoke is not None

    by_attr_name = {
        binding.attribute_config.name: binding
        for binding in second_invoke.attribute_configs
        if binding.attribute_config is not None
    }
    assert by_attr_name["foreign_id"].value_expr == {
        "kind": "reference",
        "name": "generated_id",
    }


def test_function_impl_lowering_injects_parent_self_id_for_relationship_construct(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_invoke_self_id.aware",
        """
class Child {
    fn create construct(label String key) -> Child {}
}

class Parent {
    children Child[]

    fn run(label String) -> Child {
        let created = construct children.create(label = label)
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_invoke_self_id",
        description="function_impl_invoke_self_id",
        fqn_prefix="pkg",
        file_codes=[("function_impl_invoke_self_id.aware", code)],
        namespace_by_code_id=ns,
    )

    runtime_graph = AwareToRuntimeTransformer(
        namespace_by_code_id=ns,
        relationship_loading_config=None,
    ).transform(res.graph)

    parent = next(
        n.class_config
        for n in runtime_graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    function_impl = run_fn.function_impl
    assert function_impl is not None
    invoke_instruction = next(
        ins
        for ins in function_impl.instructions
        if ins.type == FunctionImplInstructionType.invoke
    )
    invoke_payload = invoke_instruction.instruction_invoke
    assert invoke_payload is not None

    by_attr_name = {
        binding.attribute_config.name: binding
        for binding in invoke_payload.attribute_configs
        if binding.attribute_config is not None
    }
    assert by_attr_name["label"].value_expr == {"kind": "reference", "name": "label"}
    parent_id_bindings = [
        binding
        for name, binding in by_attr_name.items()
        if name.endswith("_id")
        and isinstance(binding.value_expr, dict)
        and binding.value_expr.get("kind") == "self_id"
    ]
    assert len(parent_id_bindings) == 1


def test_function_impl_lowering_allows_explicit_owner_id_in_invoke_argument(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_explicit_owner_id.aware",
        """
class Child {
    parent_id UUID key
    label String key

    fn create construct(parent_id UUID key, label String key) -> Child {
        construct Child(parent_id = parent_id, label = label)
    }
}

class Parent {
    children Child[]

    fn capture(child_id UUID) -> UUID {
    }

    fn run(label String) -> Child {
        let child = construct Child.create(parent_id = id, label = label)
        call capture(child_id = child.id)
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_explicit_owner_id",
        description="function_impl_explicit_owner_id",
        fqn_prefix="pkg",
        file_codes=[("function_impl_explicit_owner_id.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    function_impl = build_function_impl_from_body(
        function_config=run_fn,
        owner_class_config=parent,
    )
    assert function_impl is not None

    invoke_instructions = [
        ins
        for ins in function_impl.instructions
        if ins.type == FunctionImplInstructionType.invoke
    ]
    assert len(invoke_instructions) == 2

    invoke_payload = invoke_instructions[0].instruction_invoke
    assert invoke_payload is not None
    assert invoke_payload.class_config_relationship_id is None
    by_attr_name = {
        binding.attribute_config.name: binding
        for binding in invoke_payload.attribute_configs
        if binding.attribute_config is not None
    }
    assert by_attr_name["parent_id"].value_expr == {"kind": "self_id"}
    assert by_attr_name["label"].value_expr == {"kind": "reference", "name": "label"}

    capture_payload = invoke_instructions[1].instruction_invoke
    assert capture_payload is not None
    capture_by_attr_name = {
        binding.attribute_config.name: binding
        for binding in capture_payload.attribute_configs
        if binding.attribute_config is not None
    }
    assert capture_by_attr_name["child_id"].value_expr == {
        "kind": "reference",
        "name": "child.id",
    }


def test_function_impl_lowering_requires_owner_local_set_target(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_set_cross_target.aware",
        """
class Child {
    display_name String
}

class Parent {
    child Child

    fn run(name String) -> String {
        set child.display_name = name
    }
}
    """.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_set_cross_target",
        description="function_impl_set_cross_target",
        fqn_prefix="pkg",
        file_codes=[("function_impl_set_cross_target.aware", code)],
        namespace_by_code_id=ns,
    )
    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    with pytest.raises(ValueError, match=r"parse errors"):
        build_function_impl_from_body(
            function_config=run_fn,
            owner_class_config=parent,
        )


def test_function_impl_lowering_supports_require_compare_with_literal(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_require_compare.aware",
        """
class Parent {
    score Int

    fn run(input_score Int) -> String {
        set score = input_score
        require compare(gte, input_score, 0)
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_require_compare",
        description="function_impl_require_compare",
        fqn_prefix="pkg",
        file_codes=[("function_impl_require_compare.aware", code)],
        namespace_by_code_id=ns,
    )

    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    function_impl = build_function_impl_from_body(
        function_config=run_fn,
        owner_class_config=parent,
    )
    assert function_impl is not None

    require_instruction = next(
        ins
        for ins in function_impl.instructions
        if ins.type == FunctionImplInstructionType.require
    )
    assert require_instruction.instruction_require is not None
    assert (
        require_instruction.instruction_require.kind == FunctionImplRequireKind.compare
    )
    assert (
        require_instruction.instruction_require.compare_operator
        == FunctionImplRequireCompareOperator.gte
    )
    assert len(require_instruction.instruction_require.operands) == 2


def test_function_impl_lowering_supports_text_matches_regex_require(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_require_regex.aware",
        """
class Blob {
    sha String

    fn create construct(sha String key) -> Blob {
        require text_matches_regex(sha, "[0-9a-f]{64}") message "sha must be valid"
        construct Blob(sha = sha)
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="function_impl_require_regex",
        description="function_impl_require_regex",
        fqn_prefix="pkg",
        file_codes=[("function_impl_require_regex.aware", code)],
        namespace_by_code_id=ns,
    )

    blob = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Blob"
    )
    create_fn = next(
        edge.function_config
        for edge in blob.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "create"
    )

    function_impl = build_function_impl_from_body(
        function_config=create_fn,
        owner_class_config=blob,
    )
    assert function_impl is not None
    require_instruction = next(
        ins
        for ins in function_impl.instructions
        if ins.type == FunctionImplInstructionType.require
    )
    assert require_instruction.instruction_require is not None
    assert (
        require_instruction.instruction_require.kind
        == FunctionImplRequireKind.text_matches_regex
    )
    assert require_instruction.instruction_require.message == "sha must be valid"
    assert len(require_instruction.instruction_require.operands) == 2


def test_function_impl_shadow_strict_gate_rejects_unsupported_body_statement(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_strict_gate_unsupported.aware",
        """
class Parent {
    fn run(name String) -> String {
        let alias = name
        return alias
    }
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="function_impl_strict_gate_unsupported",
        description="function_impl_strict_gate_unsupported",
        fqn_prefix="pkg",
        file_codes=[("function_impl_strict_gate_unsupported.aware", code)],
        namespace_by_code_id=ns,
    )
    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )

    with pytest.raises(
        ValueError, match=r"unsupported function body statement for FunctionImpl v0"
    ):
        build_function_impl_from_body(
            function_config=run_fn,
            owner_class_config=parent,
        )


def test_function_impl_shadow_strict_gate_allows_docstring_only_body(
    tmp_path: Path,
    monkeypatch,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "function_impl_strict_gate_docstring.aware",
        '''
class Parent {
    fn run() -> String {
        """
        Keep this behavior documented.
        """
    }
}
'''.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    monkeypatch.setattr(ocg_builder, "_ENABLE_FUNCTION_IMPL_SHADOW", True)
    monkeypatch.setattr(ocg_builder, "_ENABLE_FUNCTION_IMPL_INVOCATION_SOURCE", False)

    res = build_object_config_graph_from_code(
        name="function_impl_strict_gate_docstring",
        description="function_impl_strict_gate_docstring",
        fqn_prefix="pkg",
        file_codes=[("function_impl_strict_gate_docstring.aware", code)],
        namespace_by_code_id=ns,
    )
    parent = next(
        n.class_config
        for n in res.graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    run_fn = next(
        edge.function_config
        for edge in parent.class_config_function_configs
        if edge.function_config is not None and edge.function_config.name == "run"
    )
    assert run_fn.function_impl is not None
    assert run_fn.function_impl.instructions == []
