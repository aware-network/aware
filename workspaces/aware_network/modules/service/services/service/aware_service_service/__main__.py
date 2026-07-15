from __future__ import annotations

import asyncio
import os
import signal
from contextlib import suppress

from aware_utils.logging import logger

from aware_service_runtime.local_authority import (
    ServiceHostStartupPhase,
    write_service_host_startup_failure_from_environment,
)

from aware_service_service import (
    ServiceHostApp,
    ServiceHostBootstrapConfig,
    ServiceHostIpcServer,
    build_service_host_app_from_bootstrap_config,
)


async def _serve(
    *,
    config: ServiceHostBootstrapConfig,
    app: ServiceHostApp,
) -> None:
    await _serve_app(config=config, app=app)


async def _serve_app(
    *,
    config: ServiceHostBootstrapConfig,
    app: ServiceHostApp,
) -> None:
    server = ServiceHostIpcServer(
        app=app,
        endpoint=config.ipc.endpoint,
        managed_startup=(
            os.environ.get("AWARE_SERVICE_HOST_NODE_MANAGED_STARTUP", "").strip() == "1"
        ),
    )
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)
    loaded = await server.start()
    logger.info(
        "aware_service_service listening on %s services=%s bootstrap_config=%s",
        config.ipc.socket_path.as_posix(),
        list(loaded),
        config.source_path.as_posix() if config.source_path is not None else None,
    )
    try:
        await stop_event.wait()
    finally:
        await server.close()


def main() -> None:
    phase = ServiceHostStartupPhase.bootstrap_config
    try:
        config = ServiceHostBootstrapConfig.from_env()
        phase = ServiceHostStartupPhase.app_construction
        app = build_service_host_app_from_bootstrap_config(config=config)
        phase = ServiceHostStartupPhase.activation
        asyncio.run(_serve(config=config, app=app))
    except KeyboardInterrupt:
        return
    except Exception as exc:
        write_service_host_startup_failure_from_environment(
            phase=phase,
            error=exc,
        )
        raise


if __name__ == "__main__":
    main()
