"""File system analyzer implementation."""

import logging

from aware_file_system.models import ProjectStructure
from aware_file_system.config import Config
from aware_file_system.introspection.introspector import FileSystemIntrospector

logger = logging.getLogger(__name__)


class Analyzer:
    """
    Analyzer for file system introspection.
    This class serves as a bridge to maintain backward compatibility
    with the old API while using the new introspector internally.
    """

    def __init__(self, config: Config):
        """
        Initialize the analyzer with configuration.

        Args:
            config: Configuration for analysis
        """
        self.config = config
        self.introspector = FileSystemIntrospector(config)
        logger.debug(f"Initialized analyzer with config: {config}")

    def analyze(self) -> ProjectStructure:
        """
        Analyze the file system using the introspector.

        Returns:
            ProjectStructure containing the analysis results
        """
        return self.introspector.introspect()
