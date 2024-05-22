"""Primary class for converting experiment-specific western blot data."""
from pynwb.file import NWBFile
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from datetime import datetime
from pathlib import Path


class Seiler2024WesternBlotInterface(BaseDataInterface):
    """Western Blot interface for seiler_2024 conversion"""

    keywords = ["western blot"]

    def __init__(self, file_path: str, verbose: bool = True):
        """Initialize Seiler2024BehaviorInterface.

        Parameters
        ----------
        file_path : str
            Path to the .tif file.
        verbose : bool, optional
            Whether to print verbose output, by default True
        """
        super().__init__(
            file_path=file_path,
            verbose=verbose,
        )

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()

        # Western Blot does not have a start datetime --> using publication date of the paper: 2022-02-07
        metadata["NWBFile"]["session_start_time"] = datetime(2022, 2, 7, 0, 0, 0)
        file_path = Path(self.source_data["file_path"])
        metadata["Subject"]["subject_id"] = file_path.stem
        if "Female" in file_path.stem:
            metadata["Subject"]["sex"] = "F"
        elif "Male" in file_path.stem:
            metadata["Subject"]["sex"] = "M"
        else:
            metadata["Subject"]["sex"] = "U"
        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict) -> None:
        pass
