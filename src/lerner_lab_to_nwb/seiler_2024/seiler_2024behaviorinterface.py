"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from datetime import datetime, date, time, timezone
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
import numpy as np
from pprint import pprint
from .medpc import read_medpc_file


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
