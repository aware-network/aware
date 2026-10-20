from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, replace

import pytest
from aware_goal_operational_runtime.contracts import (
    AppendGoalLaneIssueIntent,
    EnsureGoalIntent,
    EnsureGoalLaneIntent,
    GoalLaneStatus,
)
from aware_goal_operational_runtime.host import GoalOperationalRuntimeHost
from aware_goal_operational_runtime.host_handoff import (
    HmacSha256GoalRuntimeHostHandoffAuthenticator,
    decode_goal_runtime_host_handoff,
    encode_goal_runtime_host_handoff,
    issue_goal_runtime_host_handoff,
    restore_goal_runtime_host_handoff,
)
from aware_goal_operational_runtime.observation import (
    GoalObservationQuery,
    ObservationDepth,
)
from aware_goal_operational_runtime.persistence import InMemoryGoalStateStore
from conftest import context

_RESTORE_SCRIPT = r"""
import json
import sys
from dataclasses import asdict

from aware_goal_operational_runtime.host_handoff import (
    HmacSha256GoalRuntimeHostHandoffAuthenticator,
    decode_goal_runtime_host_handoff,
    restore_goal_runtime_host_handoff,
)

request = json.load(sys.stdin)
authenticator = HmacSha256GoalRuntimeHostHandoffAuthenticator(
    issuer_ref=request["issuer_ref"],
    secret=bytes.fromhex(request["secret_hex"]),
)
restored = restore_goal_runtime_host_handoff(
    handoff=decode_goal_runtime_host_handoff(request["handoff"]),
    authenticator=authenticator,
    expected_authority_ref=request["authority_ref"],
    expected_provider_runtime_ref=request["provider_runtime_ref"],
    expected_source_revision=request["source_revision"],
    expected_currentness_receipt_ref=request["currentness_receipt_ref"],
    expected_replay_context=request["replay_context"],
)
print(json.dumps(asdict(restored.observation), sort_keys=True, separators=(",", ":")))
"""


def _admitted_host(actor, state):
    store = InMemoryGoalStateStore()
    host = GoalOperationalRuntimeHost(store)
    authority_ref = state.authority.authority_ref
    assert host.admit_authority(authority_ref, state, epoch="actorworld-goal-1")
    goal = host.submit(
        authority_ref,
        EnsureGoalIntent(
            context(actor, "host-goal"),
            tag="goal/2026-09-10/actorworld-ux-ax-runtime-convergence-v0",
            title="ActorWorld",
        ),
    )
    assert goal.transition is not None and goal.transition.goal_ref is not None
    lane = host.submit(
        authority_ref,
        EnsureGoalLaneIntent(
            context(actor, "host-lane"),
            goal_ref=goal.transition.goal_ref,
            expected_goal_revision=0,
            lane_key="goal-ontology-object-runtime",
            status=GoalLaneStatus.ACTIVE,
        ),
    )
    assert lane.transition is not None and lane.transition.lane_ref is not None
    row = host.submit(
        authority_ref,
        AppendGoalLaneIssueIntent(
            context(actor, "host-row"),
            goal_ref=goal.transition.goal_ref,
            lane_ref=lane.transition.lane_ref,
            expected_lane_revision=0,
            expected_head_row_ref=None,
            row_key="g2-goal-operational-ontology-object-host",
            gate="Resolve the exact G2 Goal observation.",
        ),
    )
    assert row.transition is not None and row.transition.row_ref is not None
    query = GoalObservationQuery(
        ObservationDepth.ROW,
        goal_ref=goal.transition.goal_ref,
        lane_ref=lane.transition.lane_ref,
        row_ref=row.transition.row_ref,
    )
    return host, authority_ref, query


def test_authenticated_handoff_restores_exact_host_observation(actor, state) -> None:
    host, authority_ref, query = _admitted_host(actor, state)
    authenticator = HmacSha256GoalRuntimeHostHandoffAuthenticator(
        issuer_ref="goal-runtime-issuer:actorworld",
        secret=b"a" * 32,
    )
    handoff = issue_goal_runtime_host_handoff(
        host=host,
        authority_ref=authority_ref,
        query=query,
        provider_runtime_ref="goal-runtime:actorworld:1",
        source_revision="commit:actorworld-goal-authority",
        currentness_receipt_ref="goal-currentness:actorworld-g2",
        replay_context="g2-canary:attempt-1",
        authenticator=authenticator,
    )

    decoded = decode_goal_runtime_host_handoff(
        encode_goal_runtime_host_handoff(handoff)
    )
    restored = restore_goal_runtime_host_handoff(
        handoff=decoded,
        authenticator=authenticator,
        expected_authority_ref=authority_ref,
        expected_provider_runtime_ref="goal-runtime:actorworld:1",
        expected_source_revision="commit:actorworld-goal-authority",
        expected_currentness_receipt_ref="goal-currentness:actorworld-g2",
        expected_replay_context="g2-canary:attempt-1",
    )

    assert restored.observation == host.observe(authority_ref, query)
    assert restored.host.read(authority_ref) == host.read(authority_ref)


def test_conformance_authenticator_emits_standard_hmac_sha256() -> None:
    authenticator = HmacSha256GoalRuntimeHostHandoffAuthenticator(
        issuer_ref="goal-runtime-issuer:conformance",
        secret=b"a" * 32,
    )

    authentication_ref = authenticator.authenticate(b"goal-runtime-handoff")

    assert authentication_ref == (
        "hmac-sha256:"
        "993b27d261d11d2c7c3da91a0849319e5ad38c77f3a44da4910a98c9f2c2b994"
    )
    assert authenticator.verify(b"goal-runtime-handoff", authentication_ref)
    assert not authenticator.verify(b"other", authentication_ref)


def test_authenticated_handoff_restores_in_three_fresh_processes(actor, state) -> None:
    host, authority_ref, query = _admitted_host(actor, state)
    secret = b"fresh-process-goal-host-secret!!!"
    authenticator = HmacSha256GoalRuntimeHostHandoffAuthenticator(
        issuer_ref="goal-runtime-issuer:actorworld",
        secret=secret,
    )
    encoded = encode_goal_runtime_host_handoff(
        issue_goal_runtime_host_handoff(
            host=host,
            authority_ref=authority_ref,
            query=query,
            provider_runtime_ref="goal-runtime:actorworld:1",
            source_revision="commit:actorworld-goal-authority",
            currentness_receipt_ref="goal-currentness:actorworld-g2",
            replay_context="g2-canary:attempt-1",
            authenticator=authenticator,
        )
    )
    request = json.dumps(
        {
            "handoff": encoded,
            "issuer_ref": authenticator.issuer_ref,
            "secret_hex": secret.hex(),
            "authority_ref": authority_ref,
            "provider_runtime_ref": "goal-runtime:actorworld:1",
            "source_revision": "commit:actorworld-goal-authority",
            "currentness_receipt_ref": "goal-currentness:actorworld-g2",
            "replay_context": "g2-canary:attempt-1",
        }
    )
    expected = json.dumps(
        asdict(host.observe(authority_ref, query)),
        sort_keys=True,
        separators=(",", ":"),
    )
    clean_environment = os.environ.copy()
    clean_environment.pop("PYTHONPATH", None)

    results = [
        subprocess.run(
            [sys.executable, "-c", _RESTORE_SCRIPT],
            input=request,
            text=True,
            capture_output=True,
            check=True,
            env=clean_environment,
        ).stdout.strip()
        for _ in range(3)
    ]

    assert results == [expected, expected, expected]


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("authority_ref", "goal-authority:other", "authority does not match"),
        ("source_revision", "commit:other", "source revision is stale"),
        (
            "currentness_receipt_ref",
            "goal-currentness:other",
            "currentness receipt is stale",
        ),
        ("replay_context", "g2-canary:attempt-2", "replay context is stale"),
        ("payload_digest", "sha256:wrong", "payload digest is invalid"),
        ("authentication_ref", "hmac-sha256:wrong", "authentication is invalid"),
    ],
)
def test_restore_rejects_stale_or_altered_handoff(
    actor, state, field: str, value: str, match: str
) -> None:
    host, authority_ref, query = _admitted_host(actor, state)
    authenticator = HmacSha256GoalRuntimeHostHandoffAuthenticator(
        issuer_ref="goal-runtime-issuer:actorworld",
        secret=b"a" * 32,
    )
    handoff = issue_goal_runtime_host_handoff(
        host=host,
        authority_ref=authority_ref,
        query=query,
        provider_runtime_ref="goal-runtime:actorworld:1",
        source_revision="commit:actorworld-goal-authority",
        currentness_receipt_ref="goal-currentness:actorworld-g2",
        replay_context="g2-canary:attempt-1",
        authenticator=authenticator,
    )
    altered = replace(handoff, **{field: value})

    with pytest.raises(ValueError, match=match):
        restore_goal_runtime_host_handoff(
            handoff=altered,
            authenticator=authenticator,
            expected_authority_ref=authority_ref,
            expected_provider_runtime_ref="goal-runtime:actorworld:1",
            expected_source_revision="commit:actorworld-goal-authority",
            expected_currentness_receipt_ref="goal-currentness:actorworld-g2",
            expected_replay_context="g2-canary:attempt-1",
        )


def test_restore_rejects_authenticated_observation_tampering(actor, state) -> None:
    host, authority_ref, query = _admitted_host(actor, state)
    authenticator = HmacSha256GoalRuntimeHostHandoffAuthenticator(
        issuer_ref="goal-runtime-issuer:actorworld",
        secret=b"a" * 32,
    )
    handoff = issue_goal_runtime_host_handoff(
        host=host,
        authority_ref=authority_ref,
        query=query,
        provider_runtime_ref="goal-runtime:actorworld:1",
        source_revision="commit:actorworld-goal-authority",
        currentness_receipt_ref="goal-currentness:actorworld-g2",
        replay_context="g2-canary:attempt-1",
        authenticator=authenticator,
    )
    altered_observation = {**handoff.observation, "state_digest": "sha256:wrong"}
    unsigned = asdict(replace(handoff, observation=altered_observation))
    unsigned.pop("payload_digest")
    unsigned.pop("authentication_ref")
    payload_digest = "sha256:" + hashlib.sha256(_canonical(unsigned)).hexdigest()
    altered = replace(
        handoff,
        observation=altered_observation,
        payload_digest=payload_digest,
        authentication_ref=authenticator.authenticate(
            _canonical({**unsigned, "payload_digest": payload_digest})
        ),
    )

    with pytest.raises(ValueError, match="observation differs"):
        restore_goal_runtime_host_handoff(
            handoff=altered,
            authenticator=authenticator,
            expected_authority_ref=authority_ref,
            expected_provider_runtime_ref="goal-runtime:actorworld:1",
            expected_source_revision="commit:actorworld-goal-authority",
            expected_currentness_receipt_ref="goal-currentness:actorworld-g2",
            expected_replay_context="g2-canary:attempt-1",
        )


def test_decode_rejects_non_exact_envelope_fields(actor, state) -> None:
    host, authority_ref, query = _admitted_host(actor, state)
    authenticator = HmacSha256GoalRuntimeHostHandoffAuthenticator(
        issuer_ref="goal-runtime-issuer:actorworld",
        secret=b"a" * 32,
    )
    payload = json.loads(
        encode_goal_runtime_host_handoff(
            issue_goal_runtime_host_handoff(
                host=host,
                authority_ref=authority_ref,
                query=query,
                provider_runtime_ref="goal-runtime:actorworld:1",
                source_revision="commit:actorworld-goal-authority",
                currentness_receipt_ref="goal-currentness:actorworld-g2",
                replay_context="g2-canary:attempt-1",
                authenticator=authenticator,
            )
        )
    )
    payload["unexpected"] = True

    with pytest.raises(ValueError, match="fields are not exact"):
        decode_goal_runtime_host_handoff(json.dumps(payload))


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
