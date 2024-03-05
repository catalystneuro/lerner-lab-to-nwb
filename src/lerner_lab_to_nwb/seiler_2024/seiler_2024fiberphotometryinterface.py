"""Primary class for converting experiment-specific fiber photometry."""
from pynwb.file import NWBFile
from datetime import datetime, date, time
from pytz import timezone
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from neuroconv.tools import nwb_helpers
from pathlib import Path


class Seiler2024FiberPhotometryInterface(BaseDataInterface):
    """Fiber Photometry interface for seiler_2024 conversion."""

    keywords = ["fiber photometry"]

    def __init__(self, folder_path: str, verbose: bool = True):
        super().__init__(
            folder_path=folder_path,
            verbose=verbose,
        )

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()

        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        folder_path = Path(self.source_data["folder_path"])
        assert folder_path.is_dir(), f"Folder path {folder_path} does not exist."
        pass
