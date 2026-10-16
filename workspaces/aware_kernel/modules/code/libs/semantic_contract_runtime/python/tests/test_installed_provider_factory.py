"""Original factory intake and fixed metadata; no genuine grammar execution."""

from __future__ import annotations

import ast
import json
import os
import select
import signal
import subprocess
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import Distribution, EntryPoint
from pathlib import Path
from threading import Event, Thread
from uuid import uuid4

import pytest
from aware_code_semantic_contract_runtime import installed_provider_factory as installer
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.selected_provider import _factory_state


def _fixture_factory():
    raise AssertionError("intake must not execute a factory")


def _foreign_factory():
    raise AssertionError("foreign factory must not execute")


def _argument_factory(value):
    raise AssertionError("argument factory must not execute")


class FixtureDistribution(Distribution):
    def __init__(self, name="Fixture_Package"):
        self.name_header = name

    def read_text(self, filename):
        if filename == "METADATA":
            return f"Name: {self.name_header}\nVersion: 0.2.0\n"
        return None

    def locate_file(self, path):
        return Path(path)


def fixture_entry(
    key=None, *, distribution="Fixture_Package", factory="_fixture_factory", target=None
):
    key = key or "fixture-" + uuid4().hex
    entry = EntryPoint(
        name=key, value=target or f"{__name__}:{factory}", group=installer._GROUP
    )
    return entry._for(FixtureDistribution(distribution))


def product(entry, *, distribution="fixture-package", target=None):
    return installer.admit_installed_semantic_product_factory(
        entry.name,
        expected_distribution=distribution,
        expected_entrypoint=entry.value if target is None else target,
    )


def test_original_root_admitted_once_and_metadata_revalidated(monkeypatch):
    entry = fixture_entry()
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))
    first = installer.admit_installed_semantic_stage_factory(entry.name)
    assert first is installer.admit_installed_semantic_stage_factory(entry.name)
    assert _factory_state(first).selection_factory is _fixture_factory
    changed = fixture_entry(entry.name, factory="_foreign_factory")
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (changed,))
    with pytest.raises(ContractViolation, match="selection changed"):
        installer.admit_installed_semantic_stage_factory(entry.name)


def test_original_missing_duplicate_and_exact_key_refusal(monkeypatch):
    entry = fixture_entry()
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: ())
    with pytest.raises(ContractViolation, match="unique installed"):
        installer.admit_installed_semantic_stage_factory(entry.name)
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry, entry))
    with pytest.raises(ContractViolation, match="unique installed"):
        installer.admit_installed_semantic_stage_factory(entry.name)
    for bad in (None, 0, ""):
        with pytest.raises(TypeError, match="exact selected"):
            installer.admit_installed_semantic_stage_factory(bad)


def test_root_legacy_has_no_new_product_token_or_distribution_law(monkeypatch):
    # Historical root admission accepted any nonempty exact key, without a bound.
    entry = fixture_entry(" legacy root key " + "x" * 513)
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))
    first = installer.admit_installed_semantic_stage_factory(entry.name)
    assert _factory_state(first).provider_key == entry.name
    with pytest.raises(ContractViolation, match="bounded nonblank"):
        product(entry)


@pytest.mark.parametrize("first", ("root", "product"))
def test_root_and_product_share_original_cache_and_load_once(monkeypatch, first):
    entry = fixture_entry()
    loads = []
    original = EntryPoint.load

    def load(value):
        loads.append(value)
        return original(value)

    monkeypatch.setattr(EntryPoint, "load", load)
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))
    root = installer.admit_installed_semantic_stage_factory
    initial = root(entry.name) if first == "root" else product(entry)
    assert initial is root(entry.name) is product(entry)
    assert loads == [entry]
    assert _factory_state(initial).selection_factory is _fixture_factory


def test_parallel_root_and_product_intake_has_one_admission(monkeypatch):
    entry = fixture_entry()
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))

    def intake(i):
        return (
            product(entry)
            if i % 2
            else installer.admit_installed_semantic_stage_factory(entry.name)
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(intake, range(32)))
    assert all(value is results[0] for value in results)


@pytest.mark.parametrize(
    "name",
    ("Fixture_Package", "FIXTURE.PACKAGE", "fixture---package", "fixture_package"),
)
def test_distribution_normalization_preserves_original_entry_target(monkeypatch, name):
    entry = fixture_entry(distribution=name)
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))
    assert _factory_state(product(entry)).selection_factory is _fixture_factory


@pytest.mark.parametrize(
    "mode",
    (
        "missing_dist",
        "wrong_dist",
        "wrong_target",
        "duplicate",
        "missing",
        "wrong_group",
    ),
)
def test_metadata_refusals_precede_load_and_owner_admission(monkeypatch, mode):
    entry = fixture_entry()
    selected = (entry,)
    if mode == "missing_dist":
        selected = (EntryPoint(name=entry.name, value=entry.value, group=entry.group),)
    elif mode == "wrong_dist":
        selected = (fixture_entry(entry.name, distribution="foreign-package"),)
    elif mode == "wrong_target":
        selected = (fixture_entry(entry.name, factory="_foreign_factory"),)
    elif mode == "duplicate":
        selected = (entry, fixture_entry(entry.name, distribution="foreign-package"))
    elif mode == "missing":
        selected = ()
    elif mode == "wrong_group":
        selected = (EntryPoint(name=entry.name, value=entry.value, group="foreign"),)
    loads = []
    monkeypatch.setattr(EntryPoint, "load", lambda value: loads.append(value))
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: selected)
    with pytest.raises(ContractViolation):
        product(entry)
    assert loads == []
    assert entry.name not in installer._ADMISSIONS


@pytest.mark.parametrize(
    "field", ("provider_key", "expected_distribution", "expected_entrypoint")
)
@pytest.mark.parametrize(
    "bad", (None, 1, "", " spaced", "white\nspace", "x" * 4097, "\ud800")
)
def test_product_argument_refusal_before_metadata_lookup(monkeypatch, field, bad):
    calls = []
    monkeypatch.setattr(
        installer, "entry_points", lambda **_kwargs: calls.append("lookup")
    )
    kwargs = dict(
        provider_key="key",
        expected_distribution="fixture-package",
        expected_entrypoint=f"{__name__}:_fixture_factory",
    )
    kwargs[field] = bad
    with pytest.raises((TypeError, ContractViolation)):
        installer.admit_installed_semantic_product_factory(**kwargs)
    assert calls == []


@pytest.mark.parametrize(
    "bad",
    (
        "module",
        "module:",
        ":function",
        "module::function",
        "module:function[extra]",
        "module:function [extra]",
        "a..b:function",
        "module:0function",
        "a-b:function",
        "module:.function",
    ),
)
def test_target_syntax_refuses_before_loading(monkeypatch, bad):
    calls = []
    monkeypatch.setattr(
        installer, "entry_points", lambda **_kwargs: calls.append("lookup")
    )
    with pytest.raises(ContractViolation):
        installer.admit_installed_semantic_product_factory(
            "key", expected_distribution="fixture-package", expected_entrypoint=bad
        )
    assert calls == []


def test_product_inclusive_utf8_bounds_and_no_implicit_trim(monkeypatch):
    entry = fixture_entry("k" * 512, distribution="d" * 512)
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))
    assert product(entry, distribution="d" * 512)
    for field in ("provider_key", "expected_distribution"):
        kwargs = dict(
            provider_key=entry.name,
            expected_distribution="d" * 512,
            expected_entrypoint=entry.value,
        )
        kwargs[field] += "x"
        with pytest.raises(ContractViolation):
            installer.admit_installed_semantic_product_factory(**kwargs)
    calls = []
    target = "m" * 4094 + ":f"
    monkeypatch.setattr(
        installer, "entry_points", lambda **_kwargs: calls.append("lookup") or ()
    )
    with pytest.raises(ContractViolation, match="unique installed"):
        installer.admit_installed_semantic_product_factory(
            "key", expected_distribution="fixture", expected_entrypoint=target
        )
    assert calls == ["lookup"]
    with pytest.raises(ContractViolation, match="bounded"):
        installer.admit_installed_semantic_product_factory(
            "key", expected_distribution="fixture", expected_entrypoint=target + "f"
        )


def test_changed_distribution_and_function_refuse_on_cache_hit(monkeypatch):
    entry = fixture_entry()
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))
    first = product(entry)
    changed = fixture_entry(entry.name, distribution="foreign")
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (changed,))
    with pytest.raises(ContractViolation, match="distribution differs"):
        product(entry)
    assert installer.admit_installed_semantic_stage_factory(entry.name) is first
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))
    monkeypatch.setattr(_fixture_factory, "__module__", "foreign.module")
    with pytest.raises(ContractViolation, match="function differs"):
        product(entry)
    assert installer._ADMISSIONS[entry.name][2] is first


@pytest.mark.parametrize("returned", (_foreign_factory, len, object(), lambda: None))
def test_wrong_loaded_function_cannot_be_admitted(monkeypatch, returned):
    entry = fixture_entry()
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))
    monkeypatch.setattr(EntryPoint, "load", lambda value: returned)
    with pytest.raises(ContractViolation, match="function differs"):
        product(entry)
    assert entry.name not in installer._ADMISSIONS


def test_original_zero_argument_admission_refuses_signature(monkeypatch):
    entry = fixture_entry(factory="_argument_factory")
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))
    with pytest.raises(TypeError, match="zero-argument"):
        product(entry)
    assert entry.name not in installer._ADMISSIONS


def test_loaded_foreign_module_label_has_no_equality_callback(monkeypatch):
    calls = []

    class ForeignLabel:
        def __eq__(self, other):
            calls.append("eq")
            raise AssertionError("foreign label callback")

    entry = fixture_entry()
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))
    monkeypatch.setattr(_fixture_factory, "__module__", ForeignLabel())
    with pytest.raises(ContractViolation, match="function differs"):
        product(entry)
    assert calls == []
    assert entry.name not in installer._ADMISSIONS


def test_product_unicode_bounds_measure_utf8_not_character_count(monkeypatch):
    entry = fixture_entry("é" * 256, distribution="é" * 256)
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))
    assert product(entry, distribution="é" * 256)
    for field in ("provider_key", "expected_distribution"):
        kwargs = dict(
            provider_key=entry.name,
            expected_distribution="é" * 256,
            expected_entrypoint=entry.value,
        )
        kwargs[field] += "é"
        with pytest.raises(ContractViolation, match="bounded"):
            installer.admit_installed_semantic_product_factory(**kwargs)


@pytest.mark.parametrize(
    "error", (RuntimeError("import changed state"), KeyboardInterrupt())
)
def test_loading_error_identity_survives_without_retry_or_cache(monkeypatch, error):
    entry = fixture_entry()
    calls = []
    monkeypatch.setattr(installer, "entry_points", lambda **_kwargs: (entry,))

    def load(value):
        calls.append(value)
        raise error

    monkeypatch.setattr(EntryPoint, "load", load)
    with pytest.raises(type(error)) as caught:
        product(entry)
    assert caught.value is error
    assert calls == [entry]
    assert entry.name not in installer._ADMISSIONS


def test_process_refusal_precedes_lock_metadata_and_even_argument_inspection(
    monkeypatch,
):
    class PoisonLock:
        def __enter__(self):
            raise AssertionError("inherited lock touched")

    monkeypatch.setattr(installer, "_LOCK", PoisonLock())
    monkeypatch.setattr(installer, "_CREATOR_PID", -1)
    with pytest.raises(ContractViolation, match="another process"):
        installer.admit_installed_semantic_product_factory(
            object(), expected_distribution=object(), expected_entrypoint=object()
        )


def test_real_fork_does_not_touch_parent_thread_lock():
    locked, release = Event(), Event()

    def hold():
        with installer._LOCK:
            locked.set()
            release.wait(5)

    thread = Thread(target=hold)
    thread.start()
    assert locked.wait(2)
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            installer.admit_installed_semantic_product_factory(
                "forked",
                expected_distribution="fixture",
                expected_entrypoint="fixture:factory",
            )
        except ContractViolation:
            os.write(write_fd, b"refused")
            os._exit(0)
        except BaseException:
            os._exit(2)
        os._exit(3)
    os.close(write_fd)
    try:
        ready, _, _ = select.select([read_fd], [], [], 3)
        if not ready:
            os.kill(pid, signal.SIGTERM)
            pytest.fail("child blocked on inherited lock")
        assert os.read(read_fd, 7) == b"refused"
        assert os.waitpid(pid, 0)[1] == 0
    finally:
        os.close(read_fd)
        release.set()
        thread.join(2)


def test_neutral_site_free_import_and_no_factory_or_transport_start(tmp_path):
    source = Path(installer.__file__).resolve().parent.parent
    script = (
        "import json,sys; from aware_code_semantic_contract_runtime import installed_provider_factory as i; "
        "assert i._ADMISSIONS == {}; "
        "assert not any(n.startswith(('aware_dev','aware_workspace','aware_language','aware_meta','aware_ontology','aware_service')) for n in sys.modules); "
        "print(json.dumps(i.__all__))"
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-S", "-c", script],
        cwd=tmp_path,
        env={"PYTHONPATH": str(source), "PATH": os.defpath},
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(completed.stdout) == installer.__all__
    tree = ast.parse(Path(installer.__file__).read_text())
    names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "_admit_installed" in names
    assert "admit_installed_semantic_product_factory" in names


@pytest.mark.parametrize(
    ("relative", "version", "dependency"),
    (
        (
            "workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/pyproject.toml",
            "0.2.0",
            None,
        ),
        (
            "workspaces/aware_dev/modules/dev/sdks/aware_dev/python/pyproject.toml",
            "0.1.2",
            "aware-code-semantic-contract-runtime>=0.2.0,<0.3.0",
        ),
    ),
)
def test_successor_metadata_changes_only_frozen_version_and_dependency(
    relative, version, dependency
):
    root = Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=Path(installer.__file__).parent,
            text=True,
        ).strip()
    )
    predecessor = tomllib.loads(
        subprocess.check_output(
            ["git", "show", f"faf17a478574ed5c7aa8894f0808185cc693d5f9:{relative}"],
            cwd=root,
            text=True,
        )
    )
    current = tomllib.loads((root / relative).read_text())
    predecessor["project"]["version"] = version
    if dependency is not None:
        dependencies = predecessor["project"]["dependencies"]
        dependencies.insert(dependencies.index("aware-code-sdk") + 1, dependency)
    assert current == predecessor
