from __future__ import annotations

import argparse
from pathlib import Path

from aware_node_operator.kernel_ops.seed_plan import build_kernel_seed_plan
from aware_node_operator.kernel_ops.seed_spec import KernelSeedSpec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print the deterministic Aware kernel seed plan (dry-run)."
    )
    parser.add_argument("--spec", required=True, help="Path to a kernel seed TOML spec")
    args = parser.parse_args(argv)

    spec_path = Path(args.spec).expanduser().resolve()
    spec = KernelSeedSpec.load(spec_path)
    plan = build_kernel_seed_plan(spec)

    print(f"seed={plan.spec_id} version={plan.spec_version}")
    system = plan.system_identity
    print("system_identity:")
    print(f"  key_label={system.label}")
    print(f"  identity_id={system.identity_id}")
    print(f"  actor_id={system.actor_id}")
    provider = plan.provider_org.provider
    print("provider_organization:")
    print(f"  key_label={provider.label}")
    print(f"  identity_id={provider.identity_id}")
    print(f"  actor_id={provider.actor_id}")
    print(f"  organization_id={plan.provider_org.organization_id}")
    print("executors:")
    for ex in plan.executors:
        print(
            f"  - key_label={ex.label} identity_id={ex.identity_id} actor_id={ex.actor_id}"
        )
    print("organization_members:")
    for m in plan.members:
        print(
            f"  - member_id={m.member_id} role={m.role} identity_id={m.member_identity.identity_id} key_label={m.member_identity.label}"
        )
    print("service_catalog:")
    print(f"  service_config_id={plan.service.service_config_id}")
    print(f"  inference_service_id={plan.service.inference_service_id}")
    print("economy_primitives:")
    print(f"  provider_finance_entity_id={plan.economy.provider_finance_entity_id}")
    print(f"  smart_contract_config_id={plan.economy.smart_contract_config_id}")
    print(f"  smart_contract_id={plan.economy.smart_contract_id}")

    print("planned_commits:")
    print("  - identity.Identity.signup(type=system)")
    print("  - identity.Identity.signup(type=organization)")
    print("  - organization.Organization.create(actor_id=org_actor_id)")
    for ex in plan.executors:
        print(f"  - identity.Identity.signup(type=agent)  # {ex.label}")
    for m in plan.members:
        print(
            f"  - organization.Organization.create_member(identity_id={m.member_identity.identity_id}, role={m.role})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
