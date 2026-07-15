from typing import Optional
from pydantic import BaseModel, ConfigDict

from aware_file_system.models import ProjectUpdate, Report, Changes, ChangeType

from aware_file_system.config import Config
from aware_file_system.introspection.analyzer import Analyzer
from aware_file_system.change_tracking.detector import Detector
from aware_file_system.change_tracking.diff_calculator import DiffCalculator


class Manager(BaseModel):
    config: Config
    _project_analyzer: Analyzer
    _change_detector: Detector
    _diff_calculator: DiffCalculator

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, config: Config, **data):
        super().__init__(config=config, **data)
        self._project_analyzer = Analyzer(config)
        self._change_detector = Detector()
        self._diff_calculator = DiffCalculator()

    async def process_update(self, previous_update: Optional[ProjectUpdate] = None) -> ProjectUpdate:
        """
        Process an update to the project, detecting changes and generating a report.

        Args:
            previous_update (Optional[ProjectUpdate]): The previous state of the project, if any.

        Returns:
            ProjectUpdate: The new state of the project, including changes and a report.
        """
        current_structure = self._project_analyzer.analyze()

        if previous_update:
            changes = self._change_detector.detect_changes(
                previous_update.project_structure.files_metadata,
                current_structure.files_metadata,
            )
        else:
            changes = Changes()

        report = self._generate_report(changes, current_structure.files_metadata, previous_update)

        return ProjectUpdate(project_structure=current_structure, changes=changes, report=report)

    def _generate_report(
        self,
        changes: Changes,
        current_files: dict,
        previous_update: Optional[ProjectUpdate],
    ) -> Report:
        """
        Generate a report based on the detected changes.

        Args:
            changes (Changes): The detected changes.
            current_files (dict): The current state of the files.
            previous_update (Optional[ProjectUpdate]): The previous state of the project, if any.

        Returns:
            Report: A report summarizing the changes and including diffs.
        """
        summary = self._diff_calculator.summarize_changes(changes, current_files)
        diffs = []

        for change_type in [ChangeType.update, ChangeType.create]:
            for file_path in changes.changes[change_type]:
                previous_file = (
                    previous_update.project_structure.files_metadata.get(file_path) if previous_update else None
                )
                current_file = current_files.get(file_path)
                if current_file:
                    diff = self._diff_calculator.calculate_diff(previous_file, current_file)
                    diffs.append(diff)

        return Report(summary=summary, diffs=diffs)
