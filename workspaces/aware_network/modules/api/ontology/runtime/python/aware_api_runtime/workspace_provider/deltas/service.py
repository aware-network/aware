from __future__ import annotations


async def materialize_delta(request: object) -> dict[str, object]:
    from aware_api_runtime.workspace_provider import provider  # noqa: WPS433

    return await provider._materialize_delta_impl(
        request=request,
    )


__all__ = [
    "materialize_delta",
]
