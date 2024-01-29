"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict


class Seiler2024BehaviorInterface(BaseDataInterface):
    """Behavior interface for seiler_2024 conversion"""

    keywords = ["behavior"]

    def __init__(self, file_path: str, session_id: str):
        super().__init__(file_path=file_path, session_id=session_id)

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible from the source files available
        metadata = super().get_metadata()

        return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        print(f'{self.source_data["file_path"] = }')
        print(f'{self.source_data["session_id"] = }')
