"""API/neutrality proofs only. No test here supplies an original Subject issuer."""

import ast
import inspect
from pathlib import Path
from typing import get_type_hints

import pytest
from aware_ontology_object_facade_client import subject_read as owner
from aware_ontology_object_facade_client.subject_reference import SubjectReference

PROPERTIES = {
    "SubjectTarget": {
        "reference": SubjectReference,
        "root_identity_ref": str,
        "root_object_ref": str,
        "root_type_ref": str,
        "projection_ref": str,
        "observable_ref": str,
        "observable_branch_ref": str,
        "configuration_ref": str,
        "source_association_ref": str,
        "node_refs": tuple[str, ...],
    },
    "SubjectInput": {
        "owner_ref": str,
        "owner_generation": str,
        "profile_ref": str,
        "input_ref": str,
        "revision_ref": str,
    },
    "SubjectObservation": {
        "target": owner.SubjectTarget,
        "revision_ref": str,
        "inputs": tuple[owner.SubjectInput, ...],
    },
    "SubjectPublicationReservation": {"observation": owner.SubjectObservation},
    "SubjectPublicationContext": {},
    "SubjectRead": {"reference": SubjectReference},
    "SubjectReader": {},
}
METHODS = {
    "SubjectTarget": set(),
    "SubjectInput": set(),
    "SubjectObservation": set(),
    "SubjectPublicationReservation": {"require_current"},
    "SubjectPublicationContext": {"__enter__", "__exit__"},
    "SubjectRead": {"read", "require_current", "reserve_publication", "release"},
    "SubjectReader": {"acquire"},
}


@pytest.mark.parametrize("name", PROPERTIES)
def test_protocols_have_exact_abstract_consumer_members(name):
    interface = getattr(owner, name)
    assert interface.__abstractmethods__ == PROPERTIES[name].keys() | METHODS[name]
    public = {
        key
        for key in interface.__dict__
        if not key.startswith("_") or key in {"__enter__", "__exit__"}
    }
    assert public == PROPERTIES[name].keys() | METHODS[name]
    for key, result in PROPERTIES[name].items():
        member = getattr(interface, key)
        assert type(member) is property
        assert member.fset is None and member.fdel is None
        assert get_type_hints(member.fget) == {"return": result}


@pytest.mark.parametrize("name", PROPERTIES)
def test_interfaces_are_not_constructible_or_runtime_authority_checks(name):
    interface = getattr(owner, name)
    with pytest.raises(TypeError):
        interface()
    with pytest.raises(TypeError, match="runtime_checkable"):
        isinstance(object(), interface)
    with pytest.raises(TypeError, match="runtime_checkable"):
        issubclass(object, interface)


@pytest.mark.parametrize("name", PROPERTIES)
def test_nominal_subclass_cannot_inherit_successful_stub_methods(name):
    incomplete = type("Incomplete", (getattr(owner, name),), {})
    with pytest.raises(TypeError, match="abstract"):
        incomplete()


def test_acquisition_is_async_positional_request_with_no_caller_verifiers():
    method = owner.SubjectReader.acquire
    assert inspect.iscoroutinefunction(method)
    parameters = inspect.signature(method).parameters
    assert tuple(parameters) == ("self", "reference")
    assert parameters["reference"].kind is inspect.Parameter.POSITIONAL_ONLY
    assert get_type_hints(method) == {
        "reference": SubjectReference,
        "return": owner.SubjectRead,
    }


@pytest.mark.parametrize(
    ("interface", "method", "result"),
    [
        (owner.SubjectRead, "read", owner.SubjectObservation),
        (owner.SubjectRead, "require_current", type(None)),
        (owner.SubjectRead, "reserve_publication", owner.SubjectPublicationContext),
        (owner.SubjectRead, "release", type(None)),
        (owner.SubjectPublicationReservation, "require_current", type(None)),
        (
            owner.SubjectPublicationContext,
            "__enter__",
            owner.SubjectPublicationReservation,
        ),
    ],
)
def test_retained_use_and_reservation_have_no_await_or_retarget_arguments(
    interface, method, result
):
    member = getattr(interface, method)
    assert not inspect.iscoroutinefunction(member)
    assert tuple(inspect.signature(member).parameters) == ("self",)
    assert get_type_hints(member) == {"return": result}


def test_publication_exit_is_synchronous_and_cannot_suppress_errors():
    method = owner.SubjectPublicationContext.__exit__
    assert not inspect.iscoroutinefunction(method)
    assert tuple(inspect.signature(method).parameters) == (
        "self",
        "exc_type",
        "exc_value",
        "traceback",
    )
    assert str(get_type_hints(method)["return"]) == "typing.Literal[False]"


@pytest.mark.parametrize("failure", owner.SubjectReadFailure)
def test_closed_failures_preserve_owner_code_without_success_or_recovery(failure):
    error = owner.SubjectReadError(failure)
    assert type(error) is owner.SubjectReadError
    assert error.code is failure
    assert str(error) == failure.value
    assert not hasattr(error, "subject")
    assert not hasattr(error, "retry")
    assert not hasattr(error, "current")


@pytest.mark.parametrize("value", ["subject_read_stale", "current", True, None, 1])
def test_strings_or_flags_are_not_silently_adopted_as_failure_codes(value):
    with pytest.raises(TypeError, match="exact SubjectReadFailure"):
        owner.SubjectReadError(value)


def test_api_has_no_issuer_transport_wire_codec_or_identity_algorithm():
    tree = ast.parse(Path(owner.__file__).read_bytes())
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))
    imports = {
        (node.level, node.module)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imports == {
        (0, "__future__"),
        (0, "abc"),
        (0, "enum"),
        (0, "types"),
        (0, "typing"),
        (1, "subject_reference"),
    }
    assert not any(isinstance(node, ast.FunctionDef) for node in tree.body)
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    assert classes == set(PROPERTIES) | {"SubjectReadError", "SubjectReadFailure"}
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"runtime_checkable", "uuid5", "open"}
        for node in ast.walk(tree)
    )


def test_failure_vocabulary_is_exact_and_unique():
    assert tuple(member.value for member in owner.SubjectReadFailure) == (
        "subject_read_unavailable",
        "subject_not_found",
        "subject_ambiguous",
        "subject_profile_unsupported",
        "subject_read_denied",
        "subject_read_stale",
        "subject_read_invalidated",
        "subject_read_released",
        "subject_read_foreign_execution",
        "subject_publication_busy",
        "subject_cleanup_unresolved",
    )
    assert len(owner.SubjectReadFailure.__members__) == 11
