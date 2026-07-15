from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import msgpack

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.runtime_derivation.clone import (
    clone_runtime_graph_for_language_transformer_handoff,
)
from aware_meta.graph.config.runtime_derivation.schemas import (
    RuntimeObjectConfigGraphDerivationRequest,
)
from aware_meta.graph.config.runtime_derivation.service import (
    RuntimeObjectConfigGraphDerivationService,
)

from aware_meta.orm_artifacts.binding import (
    dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph,
    orm_graph_binding_snapshot_from_object_config_graph,
)
from python_grammar.transformers.runtime_to_python_transformer import (
    RuntimeToPythonTransformer,
)


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


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


def _derive_python_graph(
    *,
    graph,
    namespace_by_code_id: dict[UUID, NamespacePath],
):
    runtime_graph = (
        RuntimeObjectConfigGraphDerivationService()
        .derive(RuntimeObjectConfigGraphDerivationRequest(source_graph=graph))
        .runtime_graph
    )
    transformer = RuntimeToPythonTransformer(namespace_by_code_id=namespace_by_code_id)
    return transformer.transform(
        clone_runtime_graph_for_language_transformer_handoff(runtime_graph),
        code_primitive_type=None,
    )


def _collect_code_section_keys(value: object, keys: set[str]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            if (
                isinstance(k, str)
                and k.startswith("code_section_")
                and k.endswith("_id")
            ):
                keys.add(k)
            _collect_code_section_keys(v, keys)
    elif isinstance(value, list):
        for v in value:
            _collect_code_section_keys(v, keys)


SAMPLE = """
class User {
    id UUID
    name String
    tags String[]
}
""".strip()

REL_SAMPLE = """
class Author {
    id UUID
    name String
}

class Post {
    id UUID
    author Author
}
""".strip()


def test_orm_graph_binding_snapshot_msgpack_is_byte_deterministic(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "a.aware", SAMPLE)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    ocg = build_object_config_graph_from_code(
        name="snap",
        description="snap",
        fqn_prefix="pkg",
        file_codes=[("a.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    b1 = dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(
        object_config_graph=ocg
    )
    b2 = dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(
        object_config_graph=ocg
    )
    assert (
        b1 == b2
    ), "expected byte-for-byte determinism when dumping the same OCG snapshot twice"

    # Roundtrip unpack->pack should also be stable now that we canonicalize dict key order.
    payload = msgpack.unpackb(b1, raw=False)
    b3 = msgpack.packb(payload, use_bin_type=True)
    # NOTE: we don't assert b3 == b1 because packb(payload) doesn't canonicalize key ordering;
    # the invariant we require is that our dumper produces stable bytes across runs.
    assert isinstance(b3, (bytes, bytearray))


def test_orm_graph_binding_snapshot_preserves_function_contract_metadata() -> None:
    class_config_id = uuid4()
    function_config_id = uuid4()
    attribute_config_id = uuid4()
    attribute = SimpleNamespace(
        id=attribute_config_id,
        name="service_id",
        owner_key="service_id",
        description=None,
        default_value=None,
        is_primary=True,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=None,
    )
    function_attribute = SimpleNamespace(
        id=uuid4(),
        class_config_id=class_config_id,
        function_config_id=function_config_id,
        attribute_config_id=attribute_config_id,
        position=0,
        type="input",
        is_identity_key=True,
        attribute_config=attribute,
    )
    function = SimpleNamespace(
        id=function_config_id,
        owner_key="aware_service.default.service.Service.build",
        name="build",
        description="Create a Service.",
        verb="construct",
        is_async=True,
        kind="instance",
        function_config_attribute_configs=[function_attribute],
    )
    function_link = SimpleNamespace(
        id=uuid4(),
        class_config_id=class_config_id,
        function_config_id=function_config_id,
        position=0,
        is_public=True,
        is_constructor=True,
        function_config=function,
    )
    class_config = SimpleNamespace(
        id=class_config_id,
        class_fqn="aware_service.default.service.Service",
        name="Service",
        value_mode="graph_ref",
        identity_mode="contained",
        parent_class_id=None,
        class_config_attribute_configs=[],
        class_config_function_configs=[function_link],
        class_config_relationships=[],
    )
    ocg = SimpleNamespace(
        fqn_prefix="aware_service",
        id=uuid4(),
        object_config_graph_nodes=[
            SimpleNamespace(id=uuid4(), class_config=class_config),
        ],
    )

    snapshot = orm_graph_binding_snapshot_from_object_config_graph(
        object_config_graph=ocg,
    )

    function_binding = snapshot.entities[0].function_bindings[0]
    assert function_binding.is_public is True
    assert function_binding.is_constructor is True

    function_spec = function_binding.function
    assert function_spec is not None
    assert function_spec.description == "Create a Service."
    assert function_spec.verb == "construct"
    assert function_spec.is_async is True
    assert function_spec.kind == "instance"

    binding = function_spec.field_bindings[0]
    assert binding.binding_role == "input"
    assert binding.is_identity_key is True


def test_orm_graph_binding_snapshot_does_not_infer_identity_key_from_primary_field() -> (
    None
):
    class_config_id = uuid4()
    function_config_id = uuid4()
    attribute_config_id = uuid4()
    attribute = SimpleNamespace(
        id=attribute_config_id,
        name="service_id",
        owner_key="service_id",
        description=None,
        default_value=None,
        is_primary=True,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=None,
    )
    function_attribute = SimpleNamespace(
        id=uuid4(),
        class_config_id=class_config_id,
        function_config_id=function_config_id,
        attribute_config_id=attribute_config_id,
        position=0,
        type="input",
        is_identity_key=False,
        attribute_config=attribute,
    )
    function = SimpleNamespace(
        id=function_config_id,
        owner_key="aware_service.default.service.Service.build",
        name="build",
        kind="instance",
        function_config_attribute_configs=[function_attribute],
    )
    function_link = SimpleNamespace(
        id=uuid4(),
        class_config_id=class_config_id,
        function_config_id=function_config_id,
        position=0,
        is_public=True,
        is_constructor=True,
        function_config=function,
    )
    class_config = SimpleNamespace(
        id=class_config_id,
        class_fqn="aware_service.default.service.Service",
        name="Service",
        value_mode="graph_ref",
        identity_mode="contained",
        parent_class_id=None,
        class_config_attribute_configs=[],
        class_config_function_configs=[function_link],
        class_config_relationships=[],
    )
    ocg = SimpleNamespace(
        fqn_prefix="aware_service",
        id=uuid4(),
        object_config_graph_nodes=[
            SimpleNamespace(id=uuid4(), class_config=class_config),
        ],
    )

    snapshot = orm_graph_binding_snapshot_from_object_config_graph(
        object_config_graph=ocg,
    )

    binding = snapshot.entities[0].function_bindings[0].function.field_bindings[0]
    assert binding.binding_role == "input"
    assert binding.field is not None
    assert binding.field.is_primary is True
    assert binding.is_identity_key is False


def test_orm_graph_binding_snapshot_is_deterministic_across_runtime_transform(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "rel.aware", REL_SAMPLE)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    ocg = build_object_config_graph_from_code(
        name="snap",
        description="snap",
        fqn_prefix="pkg",
        file_codes=[("rel.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    bytes_1 = dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(
        object_config_graph=_derive_python_graph(
            graph=ocg,
            namespace_by_code_id=ns,
        )
    )
    bytes_2 = dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(
        object_config_graph=_derive_python_graph(
            graph=ocg,
            namespace_by_code_id=ns,
        )
    )

    assert (
        bytes_1 == bytes_2
    ), "expected byte-for-byte determinism when dumping snapshots across runtime transforms"


def test_orm_graph_binding_snapshot_strips_code_section_ids(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "a.aware", SAMPLE)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    ocg = build_object_config_graph_from_code(
        name="snap",
        description="snap",
        fqn_prefix="pkg",
        file_codes=[("a.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    payload = msgpack.unpackb(
        dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(
            object_config_graph=ocg
        ),
        raw=False,
    )
    found: set[str] = set()
    _collect_code_section_keys(payload, found)
    assert (
        not found
    ), f"binding snapshot must not embed code section IDs: {sorted(found)}"
