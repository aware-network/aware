"""Real Protocol issuer -> SPEC factory; fault injection never copies refusal law."""

import copy
import importlib.util
import os
import pickle
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from aware_protocol_fs_adapter import (
    SpecificationSourceSelection,
    admit_specification_selection,
    release_specification_selection,
    require_specification_selection,
)
from aware_protocol_fs_adapter import specification_selection as protocol_owner
from aware_specification_fs_sdk_adapter import (
    SpecificationFsSdkProvider,
    revalidate_specification_iteration_source_evidence,
)
from aware_specification_fs_sdk_adapter import protocol_selection as composition
from aware_specification_fs_sdk_adapter import provider as spec_owner
from aware_specification_sdk import (
    SpecificationDraftRequest,
    SpecificationObserveRequest,
    SpecificationOperationError,
    SpecificationSdkClient,
)

_spec = importlib.util.spec_from_file_location(
    "spec_protocol_fixture", Path(__file__).with_name("test_provider.py")
)
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
canonical_tree = _fixtures.canonical_tree
ROOT = "customer/contracts/location-not-semantic-key"
ITERATION = "specification:example.spec/phase:foundation/iteration:proof"


def protocol_bytes(role="authority"):
    location = (
        'root = "customer/contracts"\npath_template = "<spec-key>/aware.spec.toml"\n'
        if role != "unavailable"
        else ""
    )
    return f'''aware = 1
[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v1"
semantic_version = 1
[target]
kind = "repository"
authority_mode = "filesystem"
[bootstrap]
agent_contract = "AGENTS.md"
[records.goal]
profile = "aware.goal.markdown.v1"
role = "unavailable"
[records.issue]
profile = "aware.issue.markdown.v1"
role = "authority"
root = "issues"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"
[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"
[records.specification]
profile = "specification_fs_v1"
role = "{role}"
{location}[records.evidence]
profile = "aware.protocol.evidence.v1"
role = "unavailable"
'''.encode()


@pytest.fixture
def selected(canonical_tree):
    base, old_root = canonical_tree
    (base / ROOT).parent.mkdir(parents=True)
    (base / old_root).rename(base / ROOT)
    (base / "aware.protocol.toml").write_bytes(protocol_bytes())
    (base / "AGENTS.md").write_text("Fixture bootstrap\n")
    (base / "foreign.txt").write_text("Unrelated dirty work\n")
    admission = admit_specification_selection(
        repository_root=base,
        manifest_path=base / "aware.protocol.toml",
        selected_manifest_paths=(ROOT + "/aware.spec.toml",),
    )
    assert admission.selection is not None
    selection = admission.selection
    yield base, selection
    try:
        release_specification_selection(selection)
    except protocol_owner.SpecificationSelectionError:
        pass  # Tests intentionally exercise explicit lifetime retirement.


def bodies(base):
    return {
        p.relative_to(base).as_posix(): p.read_bytes()
        for p in base.rglob("*")
        if p.is_file()
    }


def descriptors():
    return set(os.listdir("/proc/self/fd"))


def test_real_factory_reads_custom_root_and_preserves_owner_meaning(selected):
    base, selection = selected
    before = bodies(base)
    provider = SpecificationFsSdkProvider.from_protocol_selection(selection)
    compatibility = _fixtures.open_provider(base, (ROOT,))
    try:
        observation = SpecificationSdkClient(provider).observe(
            SpecificationObserveRequest()
        )
        assert observation == compatibility.observe(SpecificationObserveRequest())
        capability = provider.admit_iteration(SpecificationObserveRequest(), ITERATION)
        evidence = revalidate_specification_iteration_source_evidence(capability)
        assert evidence.identity.iteration_ref == ITERATION
        assert evidence.observation == observation
        assert evidence.source_base_identity == provider._base_identity
        assert bodies(base) == before
    finally:
        compatibility.close()
        provider.close()


def test_protocol_selected_draft_refuses_before_render_or_stage(selected, monkeypatch):
    base, selection = selected
    before = bodies(base)
    provider = SpecificationFsSdkProvider.from_protocol_selection(selection)

    def prohibited(*args):
        pytest.fail("read-only factory reached writer implementation")

    monkeypatch.setattr(spec_owner, "render_draft", prohibited)
    monkeypatch.setattr(spec_owner, "stage_files", prohibited)
    try:
        with pytest.raises(
            SpecificationOperationError, match="protocol_selected_writer_unavailable"
        ) as caught:
            SpecificationSdkClient(provider).create_draft(
                SpecificationDraftRequest(
                    _fixtures.definition(), "declared-author", "intent"
                )
            )
        assert caught.value.effect == "none"
        assert bodies(base) == before
    finally:
        provider.close()


@pytest.mark.parametrize(
    "value", [None, {}, "customer/contracts", {"manifest_sha256": "sha256:" + "a" * 64}]
)
def test_caller_data_does_not_construct_provider(value):
    with pytest.raises(
        SpecificationOperationError, match="protocol_selection_refused:"
    ):
        SpecificationFsSdkProvider.from_protocol_selection(value)


def test_nominal_forgery_is_refused_by_real_issuer():
    forged = object.__new__(SpecificationSourceSelection)
    with pytest.raises(
        SpecificationOperationError, match="protocol_selection_refused:"
    ):
        SpecificationFsSdkProvider.from_protocol_selection(forged)


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_selection_cannot_be_copied_or_serialized(selected, operation):
    _, selection = selected
    with pytest.raises(TypeError):
        operation(selection)


def test_released_selection_refuses_before_spec_read(selected, monkeypatch):
    _, selection = selected
    provider = SpecificationFsSdkProvider.from_protocol_selection(selection)
    capability = provider.admit_iteration(SpecificationObserveRequest(), ITERATION)
    release_specification_selection(selection)

    def prohibited(*args):
        pytest.fail("released selection reached SPEC source reader")

    monkeypatch.setattr(spec_owner, "adapt_specification_fs_roots", prohibited)
    try:
        with pytest.raises(
            SpecificationOperationError, match="protocol_selection_refused:"
        ):
            provider.observe(SpecificationObserveRequest())
        assert provider._records == {}
        with pytest.raises(SpecificationOperationError):
            revalidate_specification_iteration_source_evidence(capability)
    finally:
        provider.close()


@pytest.mark.parametrize(
    "change",
    ["bytes", "same-byte-replacement", "root-symlink", "repository-replacement"],
)
def test_source_selection_changes_refuse_before_read(selected, monkeypatch, change):
    base, selection = selected
    provider = SpecificationFsSdkProvider.from_protocol_selection(selection)
    if change == "bytes":
        with (base / "aware.protocol.toml").open("ab") as stream:
            stream.write(b"# administrative change\n")
    elif change == "same-byte-replacement":
        replacement = base / "replacement.toml"
        replacement.write_bytes((base / "aware.protocol.toml").read_bytes())
        replacement.replace(base / "aware.protocol.toml")
    elif change == "root-symlink":
        original = base / "preserved-original"
        (base / ROOT).rename(original)
        (base / ROOT).symlink_to(original, target_is_directory=True)
    else:
        original = base.with_name(base.name + "-original")
        base.rename(original)
        shutil.copytree(original, base)

    def prohibited(*args):
        pytest.fail("changed Protocol selection reached SPEC parsing")

    monkeypatch.setattr(spec_owner, "adapt_specification_fs_roots", prohibited)
    try:
        with pytest.raises(
            SpecificationOperationError, match="protocol_selection_refused:"
        ):
            provider.observe(SpecificationObserveRequest())
    finally:
        provider.close()


def test_shared_selection_survives_one_provider_close(selected):
    _, selection = selected
    first = SpecificationFsSdkProvider.from_protocol_selection(selection)
    second = SpecificationFsSdkProvider.from_protocol_selection(selection)
    first.close()
    try:
        assert require_specification_selection(selection) is selection
        assert second.observe(SpecificationObserveRequest()).iterations
        release_specification_selection(selection)
        with pytest.raises(
            SpecificationOperationError, match="protocol_selection_refused:"
        ):
            second.observe(SpecificationObserveRequest())
    finally:
        first.close()
        second.close()


def test_factory_and_explicit_lifetimes_leave_no_descriptors(selected, monkeypatch):
    _, selection = selected
    before = descriptors()
    original_consume = protocol_owner.consume_specification_selection
    borrowed = []

    def consume(value, receiver):
        def capture(fd, roots, guard):
            borrowed.append(fd)
            return receiver(fd, roots, guard)

        return original_consume(value, capture)

    import aware_protocol_fs_adapter

    monkeypatch.setattr(
        aware_protocol_fs_adapter, "consume_specification_selection", consume
    )
    provider = SpecificationFsSdkProvider.from_protocol_selection(selection)
    with pytest.raises(OSError):
        os.fstat(borrowed[0])
    provider.close()
    assert descriptors() == before
    assert require_specification_selection(selection) is selection


def test_post_construction_protocol_refusal_closes_provider_and_admissions(
    selected, monkeypatch
):
    base, selection = selected
    original_consume = protocol_owner.consume_specification_selection
    captured = []
    before = descriptors()

    def consume(value, receiver):
        def after_construction(fd, roots, guard):
            provider = receiver(fd, roots, guard)
            capability = provider.admit_iteration(
                SpecificationObserveRequest(), ITERATION
            )
            captured.append((provider, capability))
            with (base / "aware.protocol.toml").open("ab") as stream:
                stream.write(b"# changed after real construction\n")
            return provider

        return original_consume(value, after_construction)

    import aware_protocol_fs_adapter

    monkeypatch.setattr(
        aware_protocol_fs_adapter, "consume_specification_selection", consume
    )
    with pytest.raises(
        SpecificationOperationError, match="protocol_selection_refused:"
    ):
        SpecificationFsSdkProvider.from_protocol_selection(selection)
    provider, capability = captured[0]
    assert provider._closed and not provider._records
    with pytest.raises(OSError):
        os.fstat(provider._base_fd)
    with pytest.raises(SpecificationOperationError, match="source_provider_closed"):
        revalidate_specification_iteration_source_evidence(capability)
    assert descriptors() == before


def test_receiver_failure_closes_partial_provider(selected, monkeypatch):
    base, selection = selected
    original_check = SpecificationFsSdkProvider._check_protocol_selection
    captured = []
    before = descriptors()

    def change_during_construction(provider):
        if provider._protocol_read_only and not captured:
            captured.append(provider)
            with (base / "aware.protocol.toml").open("ab") as stream:
                stream.write(b"# changed in receiver\n")
        return original_check(provider)

    monkeypatch.setattr(
        SpecificationFsSdkProvider,
        "_check_protocol_selection",
        change_during_construction,
    )
    with pytest.raises(
        SpecificationOperationError, match="protocol_selection_refused:"
    ):
        SpecificationFsSdkProvider.from_protocol_selection(selection)
    assert captured[0]._closed
    assert descriptors() == before


@pytest.mark.parametrize("seam", ["adaptation", "observation", "admission", "evidence"])
def test_guard_rechecks_through_return_horizon(selected, monkeypatch, seam):
    base, selection = selected
    provider = SpecificationFsSdkProvider.from_protocol_selection(selection)
    capability = provider.admit_iteration(SpecificationObserveRequest(), ITERATION)

    def change():
        with (base / "aware.protocol.toml").open("ab") as stream:
            stream.write(b"# changed at return horizon\n")

    if seam == "adaptation":
        original = spec_owner.adapt_specification_fs_roots

        def adapt(*args):
            result = original(*args)
            change()
            return result

        monkeypatch.setattr(spec_owner, "adapt_specification_fs_roots", adapt)
    elif seam == "observation":
        original = provider._observation

        def observation(*args):
            result = original(*args)
            change()
            return result

        monkeypatch.setattr(provider, "_observation", observation)
    elif seam == "admission":
        original = spec_owner.SpecificationIterationAdmission

        def admission(*args):
            result = original(*args)
            change()
            return result

        monkeypatch.setattr(spec_owner, "SpecificationIterationAdmission", admission)
    else:
        original = spec_owner.SpecificationIterationSourceEvidence

        def evidence(*args):
            result = original(*args)
            change()
            return result

        monkeypatch.setattr(
            spec_owner, "SpecificationIterationSourceEvidence", evidence
        )
    try:
        with pytest.raises(
            SpecificationOperationError, match="protocol_selection_refused:"
        ):
            if seam == "admission":
                provider.admit_iteration(SpecificationObserveRequest(), ITERATION)
            elif seam == "evidence":
                provider.revalidate_iteration_source_evidence(capability)
            else:
                provider.observe(SpecificationObserveRequest())
        assert provider._records == {}
    finally:
        provider.close()


def test_spec_source_drift_is_still_decided_by_spec_owner(selected):
    base, selection = selected
    provider = SpecificationFsSdkProvider.from_protocol_selection(selection)
    capability = provider.admit_iteration(SpecificationObserveRequest(), ITERATION)
    with (base / ROOT / "SPEC.md").open("ab") as stream:
        stream.write(b"\nAdministrative evidence.\n")
    try:
        assert require_specification_selection(selection) is selection
        with pytest.raises(SpecificationOperationError, match="source_changed"):
            revalidate_specification_iteration_source_evidence(capability)
        assert provider._records == {}
    finally:
        provider.close()


def test_missing_extra_refuses_without_constructing_raw_provider(monkeypatch):
    def absent(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(composition, "import_module", absent)
    with pytest.raises(
        SpecificationOperationError, match="protocol_integration_unavailable"
    ):
        SpecificationFsSdkProvider.from_protocol_selection({})


def test_absent_issuer_api_refuses_without_raw_fallback(monkeypatch):
    monkeypatch.setattr(composition, "import_module", lambda name: object())
    with pytest.raises(
        SpecificationOperationError, match="protocol_integration_unavailable"
    ):
        SpecificationFsSdkProvider.from_protocol_selection({})


def test_cleanup_failure_preserves_original_selection_refusal(selected, monkeypatch):
    base, selection = selected
    original_consume = protocol_owner.consume_specification_selection
    original_close = SpecificationFsSdkProvider.close

    def close(provider):
        original_close(provider)
        raise OSError("injected cleanup reporting failure")

    def consume(value, receiver):
        def after_construction(fd, roots, guard):
            provider = receiver(fd, roots, guard)
            with (base / "aware.protocol.toml").open("ab") as stream:
                stream.write(b"# original failure\n")
            return provider

        return original_consume(value, after_construction)

    import aware_protocol_fs_adapter

    monkeypatch.setattr(
        aware_protocol_fs_adapter, "consume_specification_selection", consume
    )
    monkeypatch.setattr(SpecificationFsSdkProvider, "close", close)
    before = descriptors()
    with pytest.raises(
        SpecificationOperationError, match="protocol_selection_refused:"
    ) as caught:
        SpecificationFsSdkProvider.from_protocol_selection(selection)
    assert caught.value.effect == "none"
    assert any(
        "cleanup_failed:OSError" in note for note in caught.value.__cause__.__notes__
    )
    assert descriptors() == before


def test_default_import_does_not_require_protocol():
    repository = next(
        p for p in Path(__file__).resolve().parents if (p / ".git").exists()
    )
    source_roots = [
        "workspaces/aware_kernel/modules/specification/libs/runtime/python",
        "workspaces/aware_kernel/modules/specification/libs/fs_source_contract/python",
        "workspaces/aware_kernel/modules/specification/libs/fs_adapter/python",
        "workspaces/aware_kernel/modules/specification/sdks/specification/python/public",
        "workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter",
    ]
    code = f"""
import sys
sys.path[:0] = {[str(repository / path) for path in source_roots]!r}
class NoProtocol:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("aware_protocol"):
            raise ModuleNotFoundError(fullname)
sys.meta_path.insert(0, NoProtocol())
import aware_specification_fs_sdk_adapter
import aware_specification_sdk
assert not any(n.startswith("aware_protocol") for n in sys.modules)
"""
    subprocess.run([sys.executable, "-I", "-B", "-c", code], check=True)


def test_fork_inherited_selection_cannot_make_spec_provider(selected):
    _, selection = selected
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        try:
            SpecificationFsSdkProvider.from_protocol_selection(selection)
        except SpecificationOperationError as error:
            os.write(write_fd, error.code.encode())
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    try:
        body = os.read(read_fd, 4096).decode()
    finally:
        os.close(read_fd)
        os.waitpid(child, 0)
    assert body == "protocol_selection_refused:specification_selection_foreign_process"
    assert require_specification_selection(selection) is selection
