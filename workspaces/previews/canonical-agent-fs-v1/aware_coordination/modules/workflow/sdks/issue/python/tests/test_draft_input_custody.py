"""Neutral custody observations validate spelling, domains and detached shape."""

import os
import subprocess
import sys
import tomllib
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest
from aware_issue_sdk import (
    IssueDraftInputBinding,
    IssueDraftInputCustodyObservation,
    IssueDraftInputCustodyRefusal,
    IssueDraftInputResourceObservation,
)


def resource():
    return IssueDraftInputResourceObservation(
        "acquired",
        "custody",
        "not_attempted",
        "not_invoked",
        False,
        "not_attempted",
        (),
    )


def binding():
    return IssueDraftInputBinding(
        "attempt",
        "intent",
        "codex-execution",
        "context",
        "/repository",
        "aware.protocol.toml",
        "sha256:" + "0" * 64,
        "specs/example",
        "specs/.aware-spec-draft-" + "a" * 32,
        (("README.md", b"real bytes"),),
    )


def observation():
    return IssueDraftInputCustodyObservation(
        "attempt",
        "intent",
        None,
        "reserved",
        "/repository",
        "aware.protocol.toml",
        "sha256:" + "0" * 64,
        "specs/example",
        "specs/.aware-spec-draft-" + "a" * 32,
        resource(),
        resource(),
        None,
        (),
        "context",
    )


def test_detached_values_are_immutable_and_exports_resolve():
    import aware_issue_sdk

    for name in (
        "IssueDraftInputResourceObservation",
        "IssueDraftInputCustodyObservation",
        "IssueDraftInputBinding",
        "IssueDraftInputCustodyRefusal",
    ):
        assert name in aware_issue_sdk.__all__
        assert getattr(aware_issue_sdk, name) is not None
    for value in (binding(), observation(), resource()):
        with pytest.raises((FrozenInstanceError, TypeError)):
            value.permission = True
    refusal = IssueDraftInputCustodyRefusal("unavailable", input_custody=None)
    assert refusal.input_custody is None


@pytest.mark.parametrize(
    "field", ["manifest_locator", "target_locator", "scratch_locator"]
)
@pytest.mark.parametrize(
    "bad", ["e\u0301/file", "a\u0080b/file", "/absolute", "../outside", "a//b"]
)
def test_binding_and_observation_refuse_noncanonical_coordinates(field, bad):
    for original in (binding(), observation()):
        with pytest.raises(ValueError):
            replace(original, **{field: bad})


@pytest.mark.parametrize(
    "field",
    [
        "acquisition",
        "responsibility",
        "transfer",
        "release_invocation",
        "owner_cleanup_outcome",
    ],
)
def test_resource_domains_are_exact(field):
    with pytest.raises(ValueError):
        replace(resource(), **{field: "invented"})


@pytest.mark.parametrize(
    "field", ["attempt_ref", "client_intent_id", "execution_ref", "context_ref"]
)
@pytest.mark.parametrize("bad", ["", "e\u0301", "a\u0080b", " x ", "\ud800"])
def test_exact_correlations_are_not_silently_normalized(field, bad):
    for original in (binding(), observation()):
        with pytest.raises(ValueError):
            replace(original, **{field: bad})


def test_unknown_resources_never_default_to_caller_ownership():
    unknown = IssueDraftInputResourceObservation(
        "unknown", "unknown", "unknown", "not_invoked", None, "unknown", ()
    )
    value = replace(
        observation(),
        physical=unknown,
        protocol=unknown,
        root_locator=None,
        manifest_locator=None,
        manifest_sha256=None,
        target_locator=None,
        scratch_locator=None,
        custody_state="unknown",
    )
    assert value.physical.responsibility == "unknown"
    assert value.protocol.owner_cleanup_attempted is None
    with pytest.raises(TypeError):
        replace(value, physical={"responsibility": "caller"})
    with pytest.raises(TypeError):
        replace(resource(), owner_cleanup_attempted=1)


@pytest.mark.parametrize("bad", ["relative", "/a/../b", "/a/./b", "/a//b"])
def test_absolute_roots_have_exact_non_normalized_spelling(bad):
    for original in (binding(), observation()):
        with pytest.raises(ValueError):
            replace(original, root_locator=bad)


def test_fresh_neutral_export_import_does_not_load_lower_or_service_owners():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
from aware_issue_sdk import (IssueDraftInputBinding, IssueDraftInputCustodyObservation,
    IssueDraftInputResourceObservation, IssueDraftInputCustodyRefusal)
assert not any(name.startswith(('aware_file_system', 'aware_protocol', 'aware_service',
    'aware_issue_fs_adapter', 'aware_issue_ontology')) for name in sys.modules)
""",
        ],
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_authored_sdk_successor_is_not_old_metadata_with_new_checkout_bytes():
    import aware_issue_sdk

    manifest = Path(aware_issue_sdk.__file__).parents[1] / "pyproject.toml"
    assert tomllib.loads(manifest.read_text())["project"]["version"] == "0.10.1"
