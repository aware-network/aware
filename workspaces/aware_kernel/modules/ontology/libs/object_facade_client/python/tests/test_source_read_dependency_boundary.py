"""The explicit read import adds data modules, with no host or provider edges."""

import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "aware_ontology_object_facade_client"
META_ROOT = ROOT.parents[3] / "meta/libs/type_schema/python"
META_PACKAGE = META_ROOT / "aware_meta_type_schema"
MODULES = ("__init__", "wire", "codec", "transport", "owner_values", "object_abi_codec",
           "source_read_wire", "source_read_codec", "object_value_codec", "object_snapshot_codec", "subject_identity_codec", "preparation", "client", "topology_values", "topology_codec", "topology_validation")
META_MODULES = (
    "__init__", "_origin_profile", "codec", "compatibility",
    "composed_slice_advancement", "composition", "composition_codec",
    "composition_transition", "definition_fragment", "diagnostics", "encoding",
    "migration", "model", "persistent_index", "positive_reader",
    "type_schema_operation", "validation",
)


def test_complete_public_source_closure_and_single_canonical_owner() -> None:
    assert {p.stem for p in PACKAGE.glob("*.py")} == set(MODULES)
    for name in MODULES:
        tree = ast.parse(PACKAGE.joinpath(name + ".py").read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert {n.name.split(".")[0] for n in node.names} <= sys.stdlib_module_names
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    assert node.level == 1 and node.module in (None, *MODULES)
                else:
                    assert (node.module or "").split(".")[0] in sys.stdlib_module_names | {"aware_meta_type_schema"}
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in {"eval", "exec", "compile", "__import__"}
                elif isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in {"import_module", "module_from_spec", "exec_module"}
        if name.startswith(("source_read", "subject_identity")):
            # Source reading, schema/provider construction and a second JSON
            # implementation cannot be smuggled into portable framing.
            assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) and
                any(x in ast.unparse(n) for x in ("json", "pathlib", "os", "subprocess", "runtime", "transport"))
                for n in ast.walk(tree))


def test_isolated_loaded_read_closure_preserves_origins_and_has_no_execution_packages() -> None:
    script = """
import json
import sys
from pathlib import Path
sys.path[:0] = sys.argv[1:3]
from aware_ontology_object_facade_client import source_read_codec as read
from aware_ontology_object_facade_client import source_read_wire as w
from aware_ontology_object_facade_client import subject_identity_codec as subject
assert subject.EPOCH in subject.SUPPORTED_CONTRACTS
value = dict(contract=w.REJECTION_CONTRACT, profile_ref=w.PROFILE, tag='unavailable', code='owner_unavailable')
assert read.decode_rejection(read.encode_rejection(value)) == value
import aware_ontology_object_facade_client as public
from aware_meta_type_schema import ValueShape
assert public.ValueShape is ValueShape
assert public.RuntimeValue.of(public.ValueKind.INTEGER, 1).to_wire()['value'] == 1
names = sorted(n for n in sys.modules if n.startswith('aware_'))
print(json.dumps({n: str(Path(sys.modules[n].__file__).resolve()) for n in names}, sort_keys=True))
"""
    proc = subprocess.run([sys.executable, "-I", "-B", "-c", script, str(ROOT), str(META_ROOT)],
                          capture_output=True, text=True, check=True, timeout=10)
    assert proc.stderr == ""
    origins = json.loads(proc.stdout)
    expected_public = {PACKAGE.name: PACKAGE / "__init__.py", **{
        PACKAGE.name + "." + n: PACKAGE / (n + ".py") for n in MODULES if n != "__init__"}}
    assert {p.stem for p in META_PACKAGE.glob("*.py")} == set(META_MODULES)
    expected_meta = {"aware_meta_type_schema" + ("." + name if name != "__init__" else ""):
        META_PACKAGE / (name + ".py")
        for name in META_MODULES if name != "type_schema_operation"}
    assert len(expected_public) == 16 and len(expected_meta) == 16
    assert origins == {n: str(p.resolve()) for n, p in (expected_public | expected_meta).items()}
