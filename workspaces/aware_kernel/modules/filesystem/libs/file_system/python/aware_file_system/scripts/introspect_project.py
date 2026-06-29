#!/usr/bin/env python3
"""
Script to introspect a project and generate a comprehensive report.
"""

import argparse
import logging
import os
import json
import time

from aware_file_system.introspection import FileSystemIntrospector
from aware_file_system.config import Config
from aware_file_system.utils import script as script_utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main function to run the introspection script."""
    parser = argparse.ArgumentParser(description="Introspect project files and generate comprehensive report")
    parser.add_argument("--root_path", help="Path to the root directory to introspect")
    parser.add_argument(
        "--config_file_name",
        default="default.yaml",
        help="Path to the configuration file",
    )
    parser.add_argument(
        "--output_dir",
        help="Directory to output results (defaults to timestamp in tmp dir)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    config = Config.load_from_file_name(args.config_file_name)

    # Get root path from arguments or user input
    if not args.root_path:
        config.file_system.root_path = script_utils.get_user_input(
            "Enter the project root directory path", config.file_system.root_path
        )
    else:
        config.file_system.root_path = args.root_path

    # Validate root path
    if not os.path.isdir(config.file_system.root_path):
        logger.error(f"Error: {config.file_system.root_path} is not a valid directory")
        return 1

    # Create output directory
    output_dir = args.output_dir
    if not output_dir:
        timestamp = int(time.time())
        output_dir = os.path.join(script_utils.get_tmp_dir(), str(timestamp))

    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Results will be saved to: {output_dir}")

    # Perform introspection
    logger.info(f"Introspecting project at: {config.file_system.root_path}")
    introspector = FileSystemIntrospector(config)
    project_structure = introspector.introspect()

    # Save the tree representation
    tree_path = os.path.join(output_dir, "project_tree.txt")
    with open(tree_path, "w") as f:
        f.write(project_structure.tree)
    logger.info(f"Project tree saved to: {tree_path}")

    # Save project summary
    summary = {
        "root_path": project_structure.root_path,
        "file_count": project_structure.file_count,
        "total_size_bytes": project_structure.total_size,
        "max_directory_depth": project_structure.max_depth,
        "analysis_timestamp": project_structure.last_updated.isoformat(),
    }

    summary_path = os.path.join(output_dir, "project_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Project summary saved to: {summary_path}")

    # Create file listing with metadata
    file_listing = {}
    for path, metadata in project_structure.files_metadata.items():
        # Skip binary content for readability
        metadata_dict = metadata.model_dump(mode="json", exclude={"content"})
        file_listing[path] = metadata_dict

    listing_path = os.path.join(output_dir, "file_listing.json")
    with open(listing_path, "w") as f:
        json.dump(file_listing, f, indent=2)
    logger.info(f"File listing saved to: {listing_path}")

    # Success message
    logger.info(
        f"Introspection complete. Found {project_structure.file_count} files with a total size of {project_structure.total_size} bytes."
    )
    return 0


if __name__ == "__main__":
    exit(main())
