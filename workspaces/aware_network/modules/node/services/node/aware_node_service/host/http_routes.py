from __future__ import annotations


def register_node_http_routes(app) -> None:
    from aware_node_service.http_api.pairing import pairing_router

    app.include_router(pairing_router)


__all__ = ["register_node_http_routes"]
