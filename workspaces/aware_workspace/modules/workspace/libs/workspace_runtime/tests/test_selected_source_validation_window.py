"""Post-Code source windows preserve terminal checks and original dispatch."""

import sys

import pytest
from aware_code_semantic_contract_runtime import ContractViolation
from aware_workspace_runtime import SourceObservationUnavailable
from test_grouped_selected_source_input import _original_selection, scope


@pytest.mark.parametrize("checkpoint", [1, 2])
@pytest.mark.parametrize("change", ["source", "input", "interrupt"])
async def test_member_capture_terminal_checks(tmp_path, checkpoint, change):
    fired = []
    error = (
        KeyboardInterrupt
        if change == "interrupt"
        else (SourceObservationUnavailable, ContractViolation)
    )
    try:
        async with _original_selection(tmp_path) as original:
            path = original.root / "workspaces/network/modules/main/package/a.bin"
            saved = path.read_bytes()
            with (
                pytest.raises((SourceObservationUnavailable, ContractViolation)),
                scope(original) as expected,
            ):
                contexts = expected.context_bodies
                calls = []
                previous = sys.getprofile()

                def mutate(frame, event, value):
                    if (
                        fired
                        or event != "return"
                        or frame.f_code.co_name != "_selected_input_values"
                    ):
                        return
                    ancestors = []
                    parent = frame.f_back
                    for _ in range(3):
                        if parent is None:
                            break
                        ancestors.append(parent.f_code.co_name)
                        parent = parent.f_back
                    if "_grouped_selected_values" not in ancestors:
                        return
                    calls.append(1)
                    if len(calls) != checkpoint:
                        return
                    fired.append(change)
                    if change == "source":
                        path.write_bytes(b"changed after genuine Code validation")
                    elif change == "input":
                        object.__setattr__(expected, "context_bodies", ())
                    else:
                        raise KeyboardInterrupt("capture interrupted")

                sys.setprofile(mutate)
                try:
                    with pytest.raises(error):
                        original.issuer.validate_semantic_input_source(
                            original.selected, expected=expected
                        )
                finally:
                    sys.setprofile(previous)
                    path.write_bytes(saved)
                    object.__setattr__(expected, "context_bodies", contexts)
                assert fired == [change]
                assert original.issuer._semantic_source_window is None
                with pytest.raises(SourceObservationUnavailable):
                    original.issuer.validate_semantic_input_source(
                        original.selected, expected=expected
                    )
    except (SourceObservationUnavailable, ContractViolation):
        pass
    assert fired == [change]
    assert original.issuer._semantic_source_window is None


@pytest.mark.parametrize("change", ["selection", "original_input"])
async def test_identity_window_teardown_precedes_terminal_comparison(tmp_path, change):
    from aware_code_semantic_contract_runtime import ContentDigest

    fired = []
    restore = []
    try:
        async with _original_selection(tmp_path) as original:
            with (
                pytest.raises((SourceObservationUnavailable, ContractViolation)),
                scope(original) as expected,
            ):
                previous = sys.getprofile()

                def mutate(frame, event, value):
                    if (
                        fired
                        or event != "return"
                        or frame.f_code.co_name != "_read_source_projection_pair"
                        or frame.f_locals.get("closing") is None
                    ):
                        return
                    parent = frame.f_back
                    for _ in range(5):
                        if parent is None:
                            return
                        if parent.f_code.co_name == "_selected_input_values":
                            break
                        parent = parent.f_back
                    else:
                        return
                    if "coordinates" not in parent.f_locals:
                        return
                    if change == "selection":
                        target = parent.f_locals["selection"]
                        field = "source_identity_digest"
                        replacement = ContentDigest.of_bytes(b"late detached selection")
                    else:
                        target = parent.f_locals["origin"].expected
                        field = "use_ref"
                        replacement = "late-original-input"
                    restore.append((target, field, getattr(target, field)))
                    fired.append(change)
                    object.__setattr__(target, field, replacement)

                sys.setprofile(mutate)
                try:
                    with pytest.raises(
                        (SourceObservationUnavailable, ContractViolation)
                    ):
                        original.issuer.validate_semantic_input_source(
                            original.selected, expected=expected
                        )
                finally:
                    sys.setprofile(previous)
                    for target, field, value in restore:
                        object.__setattr__(target, field, value)
                assert fired == [change]
                assert original.issuer._semantic_source_window is None
                with pytest.raises(SourceObservationUnavailable):
                    original.issuer.validate_semantic_input_source(
                        original.selected, expected=expected
                    )
    except (SourceObservationUnavailable, ContractViolation):
        pass
    assert fired == [change]
    assert original.issuer._semantic_source_window is None


@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
async def test_source_window_substitution_after_code_read_is_zero_call_terminal(
    tmp_path, behavior
):
    fired = []
    hostile_calls = []
    try:
        async with _original_selection(tmp_path) as original:
            issuer_type = type(original.issuer)
            genuine = vars(issuer_type)["_original_semantic_source_window"]

            def hostile(*args, **kwargs):
                hostile_calls.append(behavior)
                if behavior == "restore":
                    issuer_type._original_semantic_source_window = genuine
                if behavior == "raise":
                    raise RuntimeError("substituted window executed")

            with (
                pytest.raises((SourceObservationUnavailable, ContractViolation)),
                scope(original) as expected,
            ):
                previous = sys.getprofile()

                def substitute(frame, event, value):
                    if (
                        fired
                        or event != "return"
                        or frame.f_code.co_name
                        != "read_registered_semantic_input_source_selection"
                        or frame.f_back.f_code.co_name != "_selected_input_values"
                    ):
                        return
                    fired.append(behavior)
                    issuer_type._original_semantic_source_window = hostile

                sys.setprofile(substitute)
                try:
                    with pytest.raises(
                        (SourceObservationUnavailable, ContractViolation)
                    ):
                        original.issuer.validate_semantic_input_source(
                            original.selected, expected=expected
                        )
                finally:
                    sys.setprofile(previous)
                    issuer_type._original_semantic_source_window = genuine
                assert fired == [behavior]
                assert not hostile_calls
                assert original.issuer._semantic_source_window is None
                with pytest.raises(SourceObservationUnavailable):
                    original.issuer.validate_semantic_input_source(
                        original.selected, expected=expected
                    )
    except (SourceObservationUnavailable, ContractViolation):
        pass
    assert fired == [behavior]
    assert not hostile_calls
    assert original.issuer._semantic_source_window is None
