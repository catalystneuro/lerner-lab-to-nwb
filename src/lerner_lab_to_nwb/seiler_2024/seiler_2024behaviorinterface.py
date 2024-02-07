"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from datetime import datetime, date, time, timezone
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from neuroconv.tools import nwb_helpers
import numpy as np
from pprint import pprint
from ndx_events import Events
from pynwb.behavior import BehavioralEpochs, IntervalSeries

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

        # Add behavior data to nwbfile
        behavior_module = nwb_helpers.get_module(
            nwbfile=nwbfile, name="behavior", description="Operant behavioral data from MedPC"
        )

        # Port Entry
        port_times = []
        for port_entry_time, duration in zip(session_dict["port_entry_times"], session_dict["duration_of_port_entry"]):
            port_times.append(port_entry_time)
            port_times.append(port_entry_time + duration)
        reward_port_intervals = IntervalSeries(
            name="reward_port_intervals",
            description="Interval of time spent in reward port (1 is entry, -1 is exit)",
            timestamps=port_times,
            data=np.array([1, -1] * (len(port_times) // 2), dtype=int),
        )
        behavioral_epochs = BehavioralEpochs(name="behavioral_epochs")
        behavioral_epochs.add_interval_series(reward_port_intervals)
        behavior_module.add(behavioral_epochs)

        # Left/Right Nose pokes
        left_nose_poke_times = Events(
            name="left_nose_poke_times",
            description="Left nose poke times",
            timestamps=session_dict["left_nose_poke_times"],
        )
        right_nose_poke_times = Events(
            name="right_nose_poke_times",
            description="Right nose poke times",
            timestamps=session_dict["right_nose_poke_times"],
        )
        behavior_module.add(left_nose_poke_times)
        behavior_module.add(right_nose_poke_times)

        # Interleaved Left/Right Rewards
        assert not (
            len(session_dict["left_reward_times"]) > 0 and len(session_dict["right_reward_times"]) > 0
        ), "Both left and right reward times are present (not interleaved)"
        if len(session_dict["left_reward_times"]) > 0:
            reward_times = Events(
                name="reward_times",
                description="Reward times (left)",
                timestamps=session_dict["left_reward_times"],
            )
        else:
            reward_times = Events(
                name="reward_times",
                description="Reward times (right)",
                timestamps=session_dict["right_reward_times"],
            )
        behavior_module.add(reward_times)
