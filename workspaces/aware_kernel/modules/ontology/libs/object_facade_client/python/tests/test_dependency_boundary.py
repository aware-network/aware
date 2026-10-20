"""Source and isolated loaded-module proofs for the entire public import closure."""

import ast
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from types import CellType

import aware_ontology_object_facade_client as facade

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "aware_ontology_object_facade_client"
META_ROOT = ROOT.parents[3] / "meta/libs/type_schema/python"
META_PACKAGE = META_ROOT / "aware_meta_type_schema"
SOURCE_FILES = ("__init__.py", "wire.py", "codec.py", "transport.py", "owner_values.py", "object_abi_codec.py", "object_value_codec.py", "object_snapshot_codec.py", "preparation.py", "source_read_wire.py", "source_read_codec.py", "subject_identity_codec.py", "client.py", "topology_values.py", "topology_codec.py", "topology_validation.py", "local_scalar.py", "facade.py", "constructor.py")
SOURCE_FILES += ("subject_reference.py", "subject_read.py")
DEFAULT_SOURCE_FILES = tuple(name for name in SOURCE_FILES if name not in {"subject_identity_codec.py", "subject_reference.py", "subject_read.py"})
META_SOURCE_FILES = (
    "__init__.py", "_origin_profile.py", "codec.py", "compatibility.py",
    "composed_slice_advancement.py", "composition.py", "composition_codec.py",
    "composition_transition.py", "definition_fragment.py", "diagnostics.py",
    "encoding.py", "migration.py", "model.py", "persistent_index.py",
    "positive_reader.py", "type_schema_operation.py", "validation.py", "local_read_model.py",
)


def test_every_direct_import_uses_only_the_admitted_packages() -> None:
    # Inspect the complete source closure and all tests; Meta is the sole shape owner.
    assert {path.name for path in PACKAGE.glob("*.py")} == set(SOURCE_FILES)
    for path in [*(PACKAGE / name for name in SOURCE_FILES), *ROOT.joinpath("tests").glob("*.py")]:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [item.name.split(".")[0] for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    assert path.parent == PACKAGE
                    assert node.module in (None, *(name[:-3] for name in SOURCE_FILES))
                    continue
                modules = [(node.module or "").split(".")[0]]
            else:
                continue
            allowed = sys.stdlib_module_names | {"aware_ontology_object_facade_client", "aware_meta_type_schema"}
            if path.parent != PACKAGE:
                allowed |= {"pytest"}
                if path.name == "test_preparation.py":
                    # Its canonical vectors come from this audited local test.
                    assert ROOT.joinpath("tests/test_codec.py").is_file()
                    allowed |= {"test_codec"}
            assert set(modules) <= allowed
        # No dynamic module/code loading can evade the closure census.
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if path == ROOT / "tests/test_preparation_native.py" and node.func.id == "compile":
                    # Existing native-lock proof compiles the fixed authored
                    # module to inspect code constants; it does not execute it.
                    assert not node.keywords
                    assert ast.dump(node) == ast.dump(ast.parse(
                        'compile(source.read_bytes(), str(source), "exec")', mode="eval").body)
                    continue
                assert node.func.id not in {"eval", "exec", "__import__", "compile"}
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if (path == PACKAGE / "preparation.py" and node.func.attr == "import_module"):
                    # The existing admitted optional native scan is the only
                    # fixed loader entrance; it never chooses a runtime/host.
                    assert isinstance(node.func.value, ast.Name)
                    assert node.func.value.id == "_native_importlib"
                    assert not node.keywords and len(node.args) == 1
                    assert ast.dump(node.args[0]) == ast.dump(ast.parse(
                        '__package__ + "._preparation_scan"', mode="eval").body)
                    continue
                assert node.func.attr not in {"import_module", "exec_module", "module_from_spec"}


def test_package_metadata_has_no_runtime_edges_or_workspace_wiring() -> None:
    metadata = tomllib.loads(ROOT.joinpath("pyproject.toml").read_text())
    assert metadata["project"]["dependencies"] == ["aware-meta-type-schema>=0.1.0"]
    assert "sources" not in metadata.get("tool", {}).get("uv", {})
    assert metadata["project"]["optional-dependencies"] == {"test": ["pytest>=8.4.2,<10.0.0"]}
    assert metadata["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [PACKAGE.name]
    assert PACKAGE.joinpath("py.typed").read_bytes() == b""


def test_public_exports_do_not_reference_unimplemented_or_hosting_modules() -> None:
    assert len(facade.__all__) == len(set(facade.__all__))
    for name in facade.__all__:
        assert hasattr(facade, name)
    from aware_ontology_object_facade_client import client, source_read_codec
    assert facade.exchange_read is client.exchange_read
    assert client._admit_decoded_budget is source_read_codec._admitted_budget
    # Preparation wraps the codec after the read client retains its original
    # helper. Join that actual retained target, not the later wrapper identity.
    fail = facade.codec._fail
    closure = fail.__closure__
    assert closure is not None
    cells: dict[str, CellType] = dict(zip(fail.__code__.co_freevars, closure, strict=True))
    assert cells["target"].cell_contents is client._wire_fail
    assert facade.OntologyObjectFacade.__module__ == "aware_ontology_object_facade_client.facade"
    for absent in ("activate", "Object"):
        assert not hasattr(facade, absent)
        assert not PACKAGE.joinpath(absent + ".py").exists()
    tree = ast.parse(PACKAGE.joinpath("transport.py").read_text())
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    assert len(classes) == 1
    methods = [node for node in classes[0].body if isinstance(node, ast.AsyncFunctionDef)]
    assert [node.name for node in methods] == ["exchange"]
    assert isinstance(methods[0].body[-1], ast.Expr)
    assert isinstance(methods[0].body[-1].value, ast.Constant)
    assert methods[0].body[-1].value.value is Ellipsis


def test_isolated_import_enumerates_public_and_typeschema_origins() -> None:
    script = """
import json
import sys
from pathlib import Path
sys.path[:0] = sys.argv[1:3]
import aware_ontology_object_facade_client as facade
assert facade.decode_canonical(facade.canonical_bytes({'data': ['é', 1, True, None]})) == {'data': ['é', 1, True, None]}
value = facade.RuntimeValue.of(facade.ValueKind.INTEGER, 1)
field = facade.FieldValue('T.a', value)
assert facade.ObjectInstance('o:1', 'T', [field]).to_wire()['fields'] == [field.to_wire()]
assert facade.RelationshipInstance('r:1', 'T.rel', 'o:1', 'o:2').to_wire()['target_instance_ref'] == 'o:2'
assert facade.ProjectionCoverage(facade.CoverageGrade.COMPLETE).to_wire() == {'grade': 'complete', 'missing_refs': []}
shape = facade.ValueShape.named('T')
parameter = facade.SchemaActionParameterDefinition('T.fn.p', 0, shape)
action = facade.SchemaActionDefinition('T.fn', 'T', [parameter], mutation_scope=facade.MutationScope.TARGET)
assert action.to_wire()['parameters'] == [parameter.to_wire()]
assert parameter.shape is not shape
names = sorted(name for name in sys.modules if name.startswith('aware_'))
origins = {name: str(Path(sys.modules[name].__file__).resolve()) for name in names}
print(json.dumps(origins, sort_keys=True))
"""
    proc = subprocess.run([sys.executable, "-I", "-B", "-c", script, str(ROOT), str(META_ROOT)],
                          capture_output=True, text=True, timeout=10, check=True)
    assert proc.stderr == ""
    origins = json.loads(proc.stdout)
    public_origins = {name: origin for name, origin in origins.items() if name.startswith(PACKAGE.name)}
    meta_origins = {name: origin for name, origin in origins.items() if name.startswith("aware_meta_type_schema")}
    assert set(origins) == set(public_origins) | set(meta_origins)
    assert set(public_origins) == {PACKAGE.name, *(PACKAGE.name + "." + name[:-3] for name in DEFAULT_SOURCE_FILES[1:])}
    assert {Path(value) for value in public_origins.values()} == {PACKAGE / name for name in DEFAULT_SOURCE_FILES}
    # The real initializer also loads nominal definitions. None is a facade export.
    expected_meta = {
        "aware_meta_type_schema" + ("." + name[:-3] if name != "__init__.py" else ""):
        str(META_PACKAGE / name)
        for name in META_SOURCE_FILES if name not in {"type_schema_operation.py", "local_read_model.py"}
    }
    assert len(meta_origins) == 16
    assert meta_origins == expected_meta
    assert not any("ValueIndex" in name or "Issuer" in name or "Capability" in name for name in facade.__all__)



def test_typeschema_foundation_has_no_transitive_service_or_execution_edge():
    files = tuple(META_PACKAGE.glob("*.py"))
    assert {path.name for path in files} == set(META_SOURCE_FILES)
    assert len(files) == 18
    local_modules = {path.stem for path in files}
    for path in files:
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert {item.name.split(".")[0] for item in node.names} <= sys.stdlib_module_names
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    assert node.level == 1
                    if node.module is None:
                        assert {item.name for item in node.names} <= local_modules
                    else:
                        assert node.module in local_modules
                else:
                    assert (node.module or "").split(".")[0] in sys.stdlib_module_names


def test_p1_public_records_and_codecs_are_data_with_one_owner():
    from aware_ontology_object_facade_client import owner_values
    for name in owner_values._attempt_specs:
        assert getattr(facade, name) is getattr(owner_values, name)
        assert getattr(facade, name).__module__ == owner_values.__name__
    for name in ("attempt_canonical_bytes", "decode_attempt_canonical_bytes", "attempt_digest_bytes", "attempt_digest_wire", "attempt_require_sha256", "attempt_require_exact_keys", "OntologyObjectOperationAttemptCodecError"):
        assert getattr(facade, name) is getattr(owner_values, name)
    for name in ("_NominalCapability", "_CapabilityRegistry", "OntologyObjectOperationAttemptIssuer", "OntologyObjectPreparedOperation", "OntologyObjectOperationExecutionContinuationCapability", "OntologyObjectOperationProvider"):
        assert not hasattr(facade, name)
        assert not hasattr(owner_values, name)
