import pytest
from aware_issue_operational_runtime import (
    IssueSourceScopeRefusal,
    evaluate_issue_source_scope,
    issue_scope_covers_path,
)


@pytest.mark.parametrize(
    "status", ["In Progress", "in_progress", "IN-PROGRESS", "  in   progress  "]
)
def test_existing_in_progress_spellings(status):
    result = evaluate_issue_source_scope(
        issue_owner="codex-owner",
        issue_status=status,
        scope_paths=("owned",),
        actor_ref="codex-owner",
        effect_paths=("owned/a", "owned/b/c"),
    )
    assert result.allowed


@pytest.mark.parametrize("status", ["Open", "Blocked", "Closed", "", "inprogress"])
def test_other_lifecycles_refuse(status):
    result = evaluate_issue_source_scope(
        issue_owner="codex-owner",
        issue_status=status,
        scope_paths=("owned",),
        actor_ref="codex-owner",
        effect_paths=("owned/a",),
    )
    assert result.refusal is IssueSourceScopeRefusal.STATUS_INVALID


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("owned", True),
        ("owned/a", True),
        ("owned/a/b", True),
        ("ownedness/a", False),
        ("other/owned", False),
        ("own", False),
    ],
)
def test_scope_uses_component_delimited_prefix(path, expected):
    assert issue_scope_covers_path(path=path, scope_paths=("owned",)) is expected


def test_refusal_precedence_matches_existing_publication():
    assert (
        evaluate_issue_source_scope(
            issue_owner="foreign",
            issue_status="Closed",
            scope_paths=(),
            actor_ref="codex-owner",
            effect_paths=("foreign",),
        ).refusal
        is IssueSourceScopeRefusal.OWNER_MISMATCH
    )
    result = evaluate_issue_source_scope(
        issue_owner="codex-owner",
        issue_status="In Progress",
        scope_paths=("owned",),
        actor_ref="codex-owner",
        effect_paths=("owned/a", "first", "second"),
    )
    assert result.refusal is IssueSourceScopeRefusal.OUT_OF_SCOPE
    assert result.offending_path == "first"


def test_empty_effects_preserve_policy_but_do_not_admit_an_operation():
    assert evaluate_issue_source_scope(
        issue_owner="codex-owner",
        issue_status="In Progress",
        scope_paths=(),
        actor_ref="codex-owner",
        effect_paths=(),
    ).allowed


def _original_decision(owner, status, scopes, actor, effects):
    from aware_issue_operational_runtime.source_scope_policy import (
        IssueSourceScopeDecision,
    )

    if owner != actor:
        return IssueSourceScopeDecision(IssueSourceScopeRefusal.OWNER_MISMATCH)
    normalized = " ".join(
        status.strip().lower().replace("_", " ").replace("-", " ").split()
    )
    if normalized != "in progress":
        return IssueSourceScopeDecision(IssueSourceScopeRefusal.STATUS_INVALID)
    for path in effects:
        if not any(path == scope or path.startswith(scope + "/") for scope in scopes):
            return IssueSourceScopeDecision(IssueSourceScopeRefusal.OUT_OF_SCOPE, path)
    return IssueSourceScopeDecision()


def _decision(scopes, effects, *, owner="same", actor="same", status="In Progress"):
    return evaluate_issue_source_scope(
        issue_owner=owner,
        issue_status=status,
        scope_paths=scopes,
        actor_ref=actor,
        effect_paths=effects,
    )


def test_fresh_lookup_matches_original_complete_path_corpus():
    from itertools import product

    # Includes valid owner-normalized paths and pure-policy characterization
    # outside that contract. Parsing still belongs to the original source owner.
    components = ("a", "ab", "a-b", "é", "日本", "", ".", "..")
    paths = ("", "/", "a/", "a//b") + tuple(
        "/".join(parts)
        for depth in (1, 2, 3)
        for parts in product(components, repeat=depth)
    )
    scope_sets = (
        (),
        ("a",),
        ("a/b",),
        ("a/",),
        ("",),
        ("/",),
        ("é", "日本/a", "ab"),
        ("a/b", "a", "a", "ab/a"),
    )
    for scopes in scope_sets:
        for path in paths:
            assert _decision(scopes, (path,)) == _original_decision(
                "same", "In Progress", scopes, "same", (path,)
            ), (scopes, path)


def test_effect_order_not_scope_order_selects_first_refusal():
    effects = ("a/first", "foreign/first", "foreign/second")
    for scopes in (("a", "a/first"), ("a/first", "a"), ("a", "a", "a/first")):
        result = _decision(scopes, effects)
        assert result.refusal is IssueSourceScopeRefusal.OUT_OF_SCOPE
        assert result.offending_path == "foreign/first"


def test_each_decision_observes_scope_owner_status_and_effect_changes():
    assert _decision(("a",), ("a/child",)).allowed
    assert not _decision(("b",), ("a/child",)).allowed
    assert _decision(("a",), ("a/child",), owner="foreign").refusal is (
        IssueSourceScopeRefusal.OWNER_MISMATCH
    )
    assert _decision(("a",), ("a/child",), status="Closed").refusal is (
        IssueSourceScopeRefusal.STATUS_INVALID
    )
    assert not _decision(("a",), ("b/child",)).allowed
    assert _decision(("a",), ("a/child",)).allowed


def test_scope_not_traversed_before_owner_status_or_empty_effects():
    class UnreadableScope(tuple):
        def __iter__(self):
            raise AssertionError("scope must not be read")

    scopes = UnreadableScope(("a",))
    assert _decision(scopes, ("a",), owner="foreign").refusal is (
        IssueSourceScopeRefusal.OWNER_MISMATCH
    )
    assert _decision(scopes, ("a",), status="Closed").refusal is (
        IssueSourceScopeRefusal.STATUS_INVALID
    )
    assert _decision(scopes, ()).allowed


def test_nonexact_string_scope_and_path_preserve_original_unhashed_fallback():
    class UnhashableText(str):
        __hash__ = None

    scope = UnhashableText("a")
    path = UnhashableText("a/child")
    for scopes, effects in (
        ((scope,), ("a/child",)),
        (("a",), (path,)),
        ((scope,), (path,)),
        (["a"], ("a/child",)),
    ):
        assert _decision(scopes, effects) == _original_decision(
            "same", "In Progress", scopes, "same", effects
        )


def test_complete_policy_signature_and_standalone_lookup_remain_original():
    import inspect

    from aware_issue_operational_runtime.source_scope_policy import (
        evaluate_issue_source_scope as policy,
    )

    assert tuple(inspect.signature(policy).parameters) == (
        "issue_owner",
        "issue_status",
        "scope_paths",
        "actor_ref",
        "effect_paths",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in inspect.signature(policy).parameters.values()
    )
    for path in ("a", "a/child", "ab/child", "a/b/c", "é/a"):
        assert issue_scope_covers_path(path=path, scope_paths=("a", "é")) == any(
            path == scope or path.startswith(scope + "/") for scope in ("a", "é")
        )
