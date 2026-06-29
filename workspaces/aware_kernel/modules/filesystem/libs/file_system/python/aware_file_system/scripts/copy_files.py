#!/usr/bin/env python3
import argparse
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, List

from aware_file_system.utils import script as script_utils
from aware_file_system.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collect_content(start_dir: str, file_extension: str) -> str:
    """
    Recursively collect all files from the given directory and subdirectories
    and concatenate their contents into a single string.

    Args:
        start_dir (str): Starting directory path
        file_extension (str): File extension to filter by

    Returns:
        str: Concatenated contents of all files found
    """
    start_path = Path(start_dir)
    if not start_path.is_dir():
        logger.error(f"Error: {start_dir} is not a valid directory")
        return ""

    all_content = []
    all_content.append(f"-- Files collected from: {start_path.resolve()}\n")
    all_content.append(f"-- Collection timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    # Find and process all files
    files = sorted(list(start_path.glob(f"**/*{file_extension}")))

    if not files:
        logger.warning(f"No {file_extension} files found in {start_dir}")
        return f"-- No {file_extension} files found in {start_dir}"

    logger.info(f"Found {len(files)} {file_extension} files")

    # Process each file
    for file in files:
        # Add file path as a comment/header
        relative_path = file.relative_to(start_path)
        all_content.append(f"\n-- FILE: {relative_path}\n")

        try:
            if file.is_dir():
                logger.debug("Skipping directory match: %s", file)
                continue
            # Read and append file content
            content = file.read_text(encoding="utf-8")
            all_content.append(content)

            # Add a separator between files
            all_content.append("\n\n-- =============================================\n")
        except Exception as e:
            logger.error(f"Error reading {file}: {e}")
            all_content.append(f"-- ERROR reading file: {str(e)}\n")

    # Combine all content
    return "".join(all_content)


def copy_to_clipboard(payload: str) -> bool:
    """
    Attempt to copy the provided payload to the system clipboard using common utilities.
    Returns True when the copy succeeds, otherwise False.
    """
    commands = [
        ("wl-copy",),
        ("xclip", "-selection", "clipboard"),
        ("pbcopy",),
    ]

    for command in commands:
        executable = command[0]
        if shutil.which(executable) is None:
            continue

        try:
            subprocess.run(
                command,
                input=payload.encode("utf-8"),
                check=True,
            )
            return True
        except subprocess.CalledProcessError as exc:
            logger.debug("Clipboard command %s failed: %s", executable, exc)

    return False


def main() -> str:
    """Main function to run the file collector script."""
    parser = argparse.ArgumentParser(description="Copy files from a folder into a single file")
    parser.add_argument("--root_path", help="Path to the root directory containing files")
    parser.add_argument(
        "--output_path",
        "-o",
        help="Output file path (if not specified, prints to stdout)",
    )
    parser.add_argument(
        "--extension",
        "-e",
        default=".sql",
        help="File extension to filter (default: .sql)",
    )
    parser.add_argument(
        "--copy-path",
        action="store_true",
        help="Copy the generated output path to the clipboard when supported",
    )
    parser.add_argument(
        "--copy-content",
        action="store_true",
        help="Copy the generated output file contents to the clipboard when supported",
    )

    args = parser.parse_args()

    # Get root path from arguments or user input
    root_path = args.root_path
    if not root_path:
        root_path = input("Enter the root directory path: ").strip()

    # Collect content
    content = collect_content(root_path, args.extension)

    latest_path = Path(root_path).resolve().parts[-1]

    # Create output directory
    output_path = args.output_path
    if not output_path:
        output_path = os.path.join(script_utils.get_tmp_dir(), f"{latest_path}.txt")

    with open(output_path, "w") as f:
        f.write(content)

    logger.info("Output written to: %s", output_path)
    # Print plain path to make it easy to copy from the terminal output.
    print(output_path)

    if args.copy_path:
        if copy_to_clipboard(output_path):
            logger.info("Output path copied to clipboard.")
        else:
            logger.warning("Unable to copy output path automatically. Install wl-clipboard, xclip, or pbcopy.")

    if args.copy_content:
        if copy_to_clipboard(content):
            logger.info("Output file contents copied to clipboard.")
        else:
            logger.warning("Unable to copy output contents automatically. Install wl-clipboard, xclip, or pbcopy.")

    return output_path


if __name__ == "__main__":
    main()
