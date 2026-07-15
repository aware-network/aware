"""Runtime registry for running service apps.

Used by tests and in-process integration harnesses.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from aware_comms.app.app import App

logger = logging.getLogger(__name__)


class AppRegistry(BaseModel):
    """Registry of running app instances (in-process)."""

    running_apps: dict[str, App] = Field(default_factory=dict)

    def get_app(self, app_type: str) -> App:
        app = self.running_apps.get(app_type)
        if not app:
            raise ValueError(
                f"App {app_type} not found. Available apps: {self.running_apps.keys()}"
            )
        return app

    def register_app(self, app: App) -> None:
        logger.info("Registering app %s", app.app_type)
        if app.app_type in self.running_apps:
            raise ValueError(f"App {app.app_type} already registered")
        self.running_apps[app.app_type] = app


app_registry = AppRegistry()

__all__ = ["AppRegistry", "app_registry"]
