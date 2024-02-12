"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from datetime import datetime, date, time
from pytz import timezone
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

    def __init__(self, file_path: str, start_date: str):
        start_date = start_date.replace("_", "/")
        super().__init__(file_path=file_path, start_date=start_date)

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
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
        }
        msn_to_training_stage = {
            "RR20Left": "RR20",
            "RI60_RIGHT_SCRAM": "RI60",
            "RI60_LEFT_SCRAM": "RI60",
            "RI30 Right SCRAMBLED": "RI30",
            "RI30 Left Scrambled": "RI30",
            "FR1_RIGHT_STIM": "FR1",
            "FR1_RIGHT_SCRAMBLED": "FR1",
            "FR1_LEFT_STIM": "FR1",
            "FR1_LEFT_SCRAM": "FR1",
            "FR1_BOTH_WStim": "FR1",
            "FR1_BOTH_SCRAMBLED": "FR1",
            "Footshock Degradation right": "ShockProbe",
            "Footshock Degradation Left": "ShockProbe",
            "FOOD_RI 60 RIGHT TTL": "RI60",
            "FOOD_RI 60 LEFT TTL": "RI60",
            "FOOD_RI 30 RIGHT TTL": "RI60",
            "FOOD_RI 30 LEFT": "RI60",
            "FOOD_FR1 TTL Right": "FR1",
            "FOOD_FR1 TTL Left": "FR1",
            "FOOD_FR1 HT TTL (Both)": "FR1",
            "20sOmissions_TTL": "OmissionProbe",
        }
        session_dict = read_medpc_file(
            file_path=self.source_data["file_path"],
            start_date=self.source_data["start_date"],
            medpc_name_to_dict_name=medpc_name_to_dict_name,
            medpc_name_to_type=dict_name_to_type,
        )
        session_start_time = datetime.combine(
            session_dict["start_date"], session_dict["start_time"], tzinfo=timezone("US/Central")
        )
        training_stage = msn_to_training_stage[session_dict["MSN"]]
        session_id = self.source_data["start_date"].replace("/", "-") + "-" + training_stage

        metadata["NWBFile"]["session_description"] = session_dict["MSN"]
        metadata["NWBFile"]["session_start_time"] = session_start_time
        metadata["NWBFile"]["identifier"] = session_id
        metadata["NWBFile"]["session_id"] = session_id

        metadata["Subject"] = {}
        metadata["Subject"]["subject_id"] = session_dict["subject"]
        metadata["Subject"]["sex"] = "U"  # TODO: Grab sex info from sheets

        return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        medpc_name_to_dict_name = {
            "MSN": "MSN",
            "G": "port_entry_times",
            "E": "duration_of_port_entry",
            "A": "left_nose_poke_times",
            "C": "right_nose_poke_times",
            "D": "right_reward_times",
            "B": "left_reward_times",
            "H": "footshock_times",
        }
        dict_name_to_type = {
            "MSN": str,
            "port_entry_times": np.ndarray,
            "duration_of_port_entry": np.ndarray,
            "left_nose_poke_times": np.ndarray,
            "right_nose_poke_times": np.ndarray,
            "right_reward_times": np.ndarray,
            "left_reward_times": np.ndarray,
            "footshock_times": np.ndarray,
        }
        session_dict = read_medpc_file(
            file_path=self.source_data["file_path"],
            start_date=self.source_data["start_date"],
            medpc_name_to_dict_name=medpc_name_to_dict_name,
            medpc_name_to_type=dict_name_to_type,
        )

        # Add behavior data to nwbfile
        behavior_module = nwb_helpers.get_module(
            nwbfile=nwbfile, name="behavior", description="Operant behavioral data from MedPC"
        )

        # Port Entry
        port_times, data = [], []
        for port_entry_time, duration in zip(session_dict["port_entry_times"], session_dict["duration_of_port_entry"]):
            port_times.append(port_entry_time)
            data.append(1)
            port_times.append(port_entry_time + duration)
            data.append(-1)
        reward_port_intervals = IntervalSeries(
            name="reward_port_intervals",
            description="Interval of time spent in reward port (1 is entry, -1 is exit)",
            timestamps=port_times,
            data=data,
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

        # Footshock
        if "Footshock" in session_dict["MSN"]:
            footshock_times = Events(
                name="footshock_times",
                description="Footshock times",
                timestamps=session_dict["footshock_times"],
            )
            behavior_module.add(footshock_times)
