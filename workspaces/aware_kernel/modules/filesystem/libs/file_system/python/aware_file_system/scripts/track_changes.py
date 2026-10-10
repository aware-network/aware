import asyncio
import os

from aware_file_system import change_tracking
from aware_file_system.utils import script as script_utils


async def main():
    config = script_utils.setup("Track changes in a project")

    change_manager = change_tracking.Manager(config)

    # Initial update
    initial_update = await change_manager.process_update()
    print(f"Initial analysis complete. Total files: {initial_update.project_structure.file_count}")

    # Simulate some changes to the project...
    print("Simulating changes...")
    # Create a new file with dummy content
    new_file_path = os.path.join(config.file_system.root_path, "new_file.txt")
    with open(new_file_path, "w") as f:
        f.write("Hello, world!")

    # Process another update
    new_update = await change_manager.process_update(previous_update=initial_update)
    print(f"Update processed. Changes detected: {len(new_update.changes.changes)}\n")
    print(f"Report summary: {new_update.report.summary}\n")
    print(f"Report diffs: {new_update.report.diffs}")

    # Remove the new file
    os.remove(new_file_path)


if __name__ == "__main__":
    asyncio.run(main())
