"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from datetime import datetime, date, time, timezone
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
import numpy as np
from pprint import pprint


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
        medpc_name_to_dict_name = {
            "Start Date": "start_date",
            "End Date": "end_date",
            "Subject": "subject",
            "Experiment": "experiment",
            "Group": "group",
            "Box": "box",
            "Start Time": "start_time",
            "End Time": "end_time",
            "MSN": "MSN",
            "G": "port_entry_times",
            "E": "duration_of_port_entry",
            "A": "left_nose_poke_times",
            "C": "right_nose_poke_times",
            "D": "right_reward_times",
            "B": "left_reward_times",
        }
        dict_name_to_type = {
            "start_date": date,
            "end_date": date,
            "subject": str,
            "experiment": str,
            "group": str,
            "box": str,
            "start_time": time,
            "end_time": time,
            "MSN": str,
            "port_entry_times": np.ndarray,
            "duration_of_port_entry": np.ndarray,
            "left_nose_poke_times": np.ndarray,
            "right_nose_poke_times": np.ndarray,
            "right_reward_times": np.ndarray,
            "left_reward_times": np.ndarray,
        }
        session_dict = read_medpc_file(
            file_path=self.source_data["file_path"],
            start_date=start_date,
            medpc_name_to_dict_name=medpc_name_to_dict_name,
            medpc_name_to_type=dict_name_to_type,
        )
        pprint(session_dict)


def read_medpc_file(file_path: str, start_date: str, medpc_name_to_dict_name: dict, medpc_name_to_type: dict) -> dict:
    """Read a raw MedPC text file into a dictionary."""
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

    # Parse the session lines into a dictionary
    session_dict = {}
    for i, line in enumerate(session_lines):
        line = line.strip("\\n")
        split_line = line.split(":", maxsplit=1)
        medpc_name, data = split_line
        data = data.strip()
        if medpc_name.startswith("     "):  # multiline variable
            if medpc_name == "     0":
                multiline_variable_name = session_lines[i - 1].split(":")[0]
                if multiline_variable_name not in medpc_name_to_dict_name:
                    continue
                session_dict[medpc_name_to_dict_name[multiline_variable_name]] = []
            if multiline_variable_name not in medpc_name_to_dict_name:
                continue
            data = data.split(" ")
            for datum in data:
                datum = datum.strip()
                if datum == "":
                    continue
                session_dict[medpc_name_to_dict_name[multiline_variable_name]].append(datum)
        elif medpc_name in medpc_name_to_dict_name:
            dict_name = medpc_name_to_dict_name[medpc_name]
            session_dict[dict_name] = data

    # Convert the data types
    for medpc_name, data_type in medpc_name_to_type.items():
        if medpc_name in session_dict:
            if data_type == date:
                session_dict[medpc_name] = datetime.strptime(session_dict[medpc_name], "%m/%d/%y").date()
            elif data_type == time:
                session_dict[medpc_name] = datetime.strptime(session_dict[medpc_name], "%H:%M:%S").time()
            elif data_type == np.ndarray:
                if session_dict[medpc_name] == "":
                    session_dict[medpc_name] = np.array([], dtype=float)
                else:
                    session_dict[medpc_name] = np.array(session_dict[medpc_name], dtype=float)
    return session_dict
