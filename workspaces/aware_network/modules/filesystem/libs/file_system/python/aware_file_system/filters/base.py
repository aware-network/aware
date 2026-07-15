from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict


class Filter(BaseModel, ABC):
    """
    Abstract base class for file filters.

    This class defines the interface for all file filters in the system.
    Concrete filter classes should inherit from this class and implement
    the `should_include` method.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)  # Allows any type to be passed as an argument

    def setup(self, root_path: str) -> None:
        """
        Perform any necessary setup for the filter.

        This method is called before the filter is used to include or exclude
        files. It can be used to initialize the filter with any required data
        or perform any other setup operations.

        Args:
            root_path (str): The root path of the project being analyzed.
        """
        pass

    @abstractmethod
    def should_include(self, file_path: str) -> bool:
        """
        Determine whether a file should be included based on the filter criteria.

        Args:
            file_path (str): The path of the file to be checked.

        Returns:
            bool: True if the file should be included, False otherwise.
        """
        pass
