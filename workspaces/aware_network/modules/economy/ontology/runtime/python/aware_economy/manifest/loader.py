from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import cast

import tomllib

from aware_economy.manifest.spec import (
    AwareEconomyTomlBuildSpec,
    AwareEconomyTomlPackageSpec,
    AwareEconomyTomlPriceScheduleSpec,
    AwareEconomyTomlPriceSpec,
    AwareEconomyTomlPricingPolicySpec,
    AwareEconomyTomlSpec,
    AwareEconomyPriceType,
)


class AwareEconomyTomlError(ValueError):
    """Raised when `aware.economy.toml` fails strict validation."""


def load_aware_economy_toml_spec_from_text(
    *,
    toml_text: str,
    toml_path: str | Path | None = None,
) -> AwareEconomyTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.economy.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareEconomyTomlError(
            f"Failed to parse TOML at {path_label}: {exc}"
        ) from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_economy_toml_raw(raw)


def load_aware_economy_toml_spec(
    *,
    toml_path: str | Path,
) -> AwareEconomyTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareEconomyTomlError(f"aware.economy.toml not found: {p}")
    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:
        raise AwareEconomyTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")
    return _parse_aware_economy_toml_raw(raw)


def _parse_aware_economy_toml_raw(
    raw: dict[str, object],
) -> AwareEconomyTomlSpec:
    _expect_keys(
        raw,
        required={"aware_economy", "economy", "build"},
        optional={"prices"},
        ctx="root",
    )
    spec_version = _expect_int(raw, "aware_economy", ctx="root")
    if spec_version != 1:
        raise AwareEconomyTomlError(
            f"Unsupported aware.economy.toml version {spec_version}; expected 1"
        )

    economy_tbl = _expect_table(raw, "economy", ctx="root")
    _expect_keys(
        economy_tbl,
        required={"package_name", "fqn_prefix"},
        optional={"version_number", "title", "description"},
        ctx="[economy]",
    )
    package_name = _expect_str(economy_tbl, "package_name", ctx="[economy]")
    fqn_prefix = _expect_str(economy_tbl, "fqn_prefix", ctx="[economy]")
    version_number = (
        _expect_opt_int(economy_tbl, "version_number", ctx="[economy]") or 1
    )
    title = _expect_opt_str(economy_tbl, "title", ctx="[economy]")
    description = _expect_opt_str(economy_tbl, "description", ctx="[economy]")

    _validate_package_name(package_name, ctx="[economy].package_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[economy].fqn_prefix")

    build_tbl = _expect_table(raw, "build", ctx="root")
    _expect_keys(
        build_tbl,
        required=set(),
        optional={"sources_dir", "include_paths", "exclude_paths", "force_fresh_scan"},
        ctx="[build]",
    )
    sources_dir = _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "economy"
    include_paths = _expect_opt_str_list(build_tbl, "include_paths", ctx="[build]") or [
        "**/*.aware"
    ]
    exclude_paths = (
        _expect_opt_str_list(build_tbl, "exclude_paths", ctx="[build]") or []
    )
    force_fresh_scan = _expect_opt_bool(
        build_tbl,
        "force_fresh_scan",
        ctx="[build]",
    )
    if force_fresh_scan is None:
        force_fresh_scan = True

    _validate_rel_path(sources_dir, ctx="[build].sources_dir")
    for index, include_path in enumerate(include_paths):
        _validate_rel_path(include_path, ctx=f"[build].include_paths[{index}]")
    for index, exclude_path in enumerate(exclude_paths):
        _validate_rel_path(exclude_path, ctx=f"[build].exclude_paths[{index}]")

    prices = _parse_price_specs(raw.get("prices", []))

    return AwareEconomyTomlSpec(
        aware_economy=spec_version,
        economy=AwareEconomyTomlPackageSpec(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            version_number=version_number,
            title=title,
            description=description,
        ),
        build=AwareEconomyTomlBuildSpec(
            sources_dir=sources_dir,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            force_fresh_scan=force_fresh_scan,
        ),
        prices=prices,
    )


def _parse_price_specs(value: object) -> tuple[AwareEconomyTomlPriceSpec, ...]:
    tables = _as_table_list(value, ctx="[[prices]]")
    prices: list[AwareEconomyTomlPriceSpec] = []
    seen_price_names: set[str] = set()
    seen_policy_keys: set[tuple[str, int]] = set()
    for index, table in enumerate(tables):
        ctx = f"[[prices]] (index={index})"
        _expect_keys(
            table,
            required={"name", "coin", "type", "pricing_policy", "schedules"},
            optional=set(),
            ctx=ctx,
        )
        name = _expect_str(table, "name", ctx=ctx).strip()
        name_key = name.casefold()
        if name_key in seen_price_names:
            raise AwareEconomyTomlError(f"Duplicate Economy price name: {name!r}")
        seen_price_names.add(name_key)

        coin = _expect_str(table, "coin", ctx=ctx).strip().upper()
        _validate_coin_symbol(coin, ctx=f"{ctx}.coin")
        price_type = _expect_price_type(table, "type", ctx=ctx)
        policy = _parse_pricing_policy_spec(
            _expect_table(table, "pricing_policy", ctx=ctx),
            ctx=f"{ctx}.pricing_policy",
        )
        policy_key = (policy.name.casefold(), policy.version)
        if policy_key in seen_policy_keys:
            raise AwareEconomyTomlError(
                "Duplicate Economy pricing policy authority: "
                f"name={policy.name!r} version={policy.version}"
            )
        seen_policy_keys.add(policy_key)
        schedules = _parse_price_schedule_specs(
            table.get("schedules", []),
            price_name=name,
            price_type=price_type,
            ctx=f"{ctx}.schedules",
        )
        if not schedules:
            raise AwareEconomyTomlError(
                f"Economy price {name!r} requires at least one schedule"
            )
        prices.append(
            AwareEconomyTomlPriceSpec(
                name=name,
                coin=coin,
                type=price_type,
                pricing_policy=policy,
                schedules=schedules,
            )
        )
    return tuple(prices)


def _parse_pricing_policy_spec(
    table: dict[str, object],
    *,
    ctx: str,
) -> AwareEconomyTomlPricingPolicySpec:
    _expect_keys(
        table,
        required={"name"},
        optional={"version", "description", "policy_json", "fail_closed"},
        ctx=ctx,
    )
    name = _expect_str(table, "name", ctx=ctx).strip()
    version = _expect_opt_int(table, "version", ctx=ctx) or 1
    if version < 1:
        raise AwareEconomyTomlError(f"{ctx}.version must be >= 1")
    policy_json_value = table.get("policy_json", {})
    policy_json = _as_table(policy_json_value, ctx=f"{ctx}.policy_json")
    fail_closed = _expect_opt_bool(table, "fail_closed", ctx=ctx)
    return AwareEconomyTomlPricingPolicySpec(
        name=name,
        version=version,
        description=_expect_opt_str(table, "description", ctx=ctx),
        policy_json=policy_json,
        fail_closed=True if fail_closed is None else fail_closed,
    )


def _parse_price_schedule_specs(
    value: object,
    *,
    price_name: str,
    price_type: AwareEconomyPriceType,
    ctx: str,
) -> tuple[AwareEconomyTomlPriceScheduleSpec, ...]:
    schedules: list[AwareEconomyTomlPriceScheduleSpec] = []
    seen: set[tuple[str, int]] = set()
    for index, table in enumerate(_as_table_list(value, ctx=ctx)):
        item_ctx = f"{ctx}[{index}]"
        _expect_keys(
            table,
            required={"name", "effective_from"},
            optional={
                "version",
                "effective_until",
                "fixed_amount",
                "markup_percentage",
            },
            ctx=item_ctx,
        )
        name = _expect_str(table, "name", ctx=item_ctx).strip()
        version = _expect_opt_int(table, "version", ctx=item_ctx) or 1
        if version < 1:
            raise AwareEconomyTomlError(f"{item_ctx}.version must be >= 1")
        key = (name.casefold(), version)
        if key in seen:
            raise AwareEconomyTomlError(
                f"Duplicate schedule for Economy price {price_name!r}: {key!r}"
            )
        seen.add(key)
        effective_from = _expect_datetime(table, "effective_from", ctx=item_ctx)
        effective_until = _expect_opt_datetime(
            table,
            "effective_until",
            ctx=item_ctx,
        )
        if effective_until is not None and effective_until < effective_from:
            raise AwareEconomyTomlError(
                f"{item_ctx}.effective_until must be >= effective_from"
            )
        fixed_amount = _expect_opt_decimal_text(
            table,
            "fixed_amount",
            ctx=item_ctx,
        )
        markup_percentage = _expect_opt_decimal_text(
            table,
            "markup_percentage",
            ctx=item_ctx,
        )
        if price_type is AwareEconomyPriceType.fixed:
            if fixed_amount is None or markup_percentage is not None:
                raise AwareEconomyTomlError(
                    f"{item_ctx} fixed price requires fixed_amount only"
                )
        elif markup_percentage is None or fixed_amount is not None:
            raise AwareEconomyTomlError(
                f"{item_ctx} dynamic price requires markup_percentage only"
            )
        schedules.append(
            AwareEconomyTomlPriceScheduleSpec(
                name=name,
                version=version,
                effective_from=effective_from,
                effective_until=effective_until,
                fixed_amount=fixed_amount,
                markup_percentage=markup_percentage,
            )
        )
    return tuple(schedules)


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareEconomyTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def _expect_keys(
    table: dict[str, object],
    *,
    required: set[str],
    optional: set[str],
    ctx: str,
) -> None:
    allowed = required | optional
    extra = set(table.keys()) - allowed
    missing = required - set(table.keys())
    if extra:
        raise AwareEconomyTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareEconomyTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareEconomyTomlError(
            f"Expected {ctx}.{key} to be a table; got {type(val)}"
        )
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareEconomyTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareEconomyTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareEconomyTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: dict[str, object], key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareEconomyTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareEconomyTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return val


def _expect_opt_str_list(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareEconomyTomlError(f"Expected {ctx}.{key} to be a list[str] or null")
    out: list[str] = []
    items = cast(list[object], val)
    for i, item in enumerate(items):
        if not isinstance(item, str):
            raise AwareEconomyTomlError(f"Expected {ctx}.{key}[{i}] to be a string")
        out.append(item)
    return out


def _as_table_list(value: object, *, ctx: str) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise AwareEconomyTomlError(f"Expected {ctx} to be an array of tables")
    return [_as_table(item, ctx=f"{ctx}[{index}]") for index, item in enumerate(value)]


def _expect_price_type(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> AwareEconomyPriceType:
    value = _expect_str(root, key, ctx=ctx).strip().casefold()
    try:
        return AwareEconomyPriceType(value)
    except ValueError as exc:
        raise AwareEconomyTomlError(
            f"{ctx}.{key} must be one of {[item.value for item in AwareEconomyPriceType]}"
        ) from exc


def _expect_datetime(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> datetime:
    value = root.get(key)
    parsed: datetime
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise AwareEconomyTomlError(
                f"{ctx}.{key} must be an ISO-8601 datetime"
            ) from exc
    else:
        raise AwareEconomyTomlError(f"{ctx}.{key} must be an ISO-8601 datetime")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AwareEconomyTomlError(f"{ctx}.{key} must include a timezone")
    return parsed.astimezone(UTC)


def _expect_opt_datetime(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> datetime | None:
    if root.get(key) is None:
        return None
    return _expect_datetime(root, key, ctx=ctx)


def _expect_opt_decimal_text(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> Decimal | None:
    value = root.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise AwareEconomyTomlError(f"{ctx}.{key} must be canonical decimal text")
    try:
        parsed = Decimal(value.strip())
    except InvalidOperation as exc:
        raise AwareEconomyTomlError(
            f"{ctx}.{key} must be canonical decimal text"
        ) from exc
    if not parsed.is_finite() or parsed < 0:
        raise AwareEconomyTomlError(
            f"{ctx}.{key} must be a finite non-negative decimal"
        )
    return parsed


def _validate_package_name(value: str, *, ctx: str) -> None:
    if not value.strip():
        raise AwareEconomyTomlError(f"{ctx} must be non-empty")
    for char in value:
        if not (char.islower() or char.isdigit() or char in {"-", "_"}):
            raise AwareEconomyTomlError(
                f"{ctx} must contain only lowercase letters, digits, '-' or '_'"
            )


def _validate_coin_symbol(value: str, *, ctx: str) -> None:
    if not value or any(not (char.isupper() or char.isdigit()) for char in value):
        raise AwareEconomyTomlError(
            f"{ctx} must contain only uppercase letters and digits"
        )


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    _validate_symbol_ref(value, ctx=ctx)


def _validate_rel_path(value: str, *, ctx: str) -> None:
    normalized = value.strip()
    if not normalized:
        raise AwareEconomyTomlError(f"{ctx} must be a non-empty relative path")
    token = Path(normalized)
    if token.is_absolute():
        raise AwareEconomyTomlError(f"{ctx} must be relative, not absolute")
    if ".." in token.parts:
        raise AwareEconomyTomlError(f"{ctx} must not contain '..'")


def _validate_symbol_ref(value: str, *, ctx: str) -> None:
    if not value or any(char.isspace() for char in value):
        raise AwareEconomyTomlError(
            f"{ctx} must be a non-empty token without whitespace"
        )
    for char in value:
        if not (char.isalnum() or char in {"_", "-", "."}):
            raise AwareEconomyTomlError(
                f"{ctx} must contain only letters, digits, '_', '-', or '.'"
            )


__all__ = [
    "AwareEconomyTomlError",
    "load_aware_economy_toml_spec",
    "load_aware_economy_toml_spec_from_text",
]
