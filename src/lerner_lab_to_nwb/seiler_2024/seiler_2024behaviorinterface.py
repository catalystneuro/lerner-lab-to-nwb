"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
import pandas as pd

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
        start_date = self.source_data["session_id"].split("_")[1].replace("-", "/")
        read_medpc_file(file_path=self.source_data["file_path"], start_date=start_date)


def read_medpc_file(file_path: str, start_date: str) -> pd.DataFrame:
    """Read a raw MedPC text file into a pandas DataFrame."""
    # Read the file
    with open(file_path, "r") as f:
        lines = f.readlines()

    # Find the start and end lines for the given session
    start_line, end_line = None, None
    for i, line in enumerate(lines):
        if line == f"Start Date: {start_date}\n":
            start_line = i
        elif start_line is not None and line == "\n":
            end_line = i
            break
    if start_line is None:
        raise ValueError(f"Could not find start date {start_date} in file {file_path}")
    if end_line is None:
        raise ValueError(f"Could not find end of session ('\\n') in file {file_path}")
    session_lines = lines[start_line:end_line]
    print(start_line, end_line)

    with open("temp.txt", "w") as f:
        f.writelines(session_lines)
