"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from datetime import datetime, date, time
from pytz import timezone
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from neuroconv.tools import nwb_helpers
import numpy as np
from ndx_events import Events
from pynwb.behavior import BehavioralEpochs, IntervalSeries
from hdmf.backends.hdf5.h5_utils import H5DataIO

from .medpc import read_medpc_file


class Seiler2024BehaviorInterface(BaseDataInterface):
    """Behavior interface for seiler_2024 conversion"""

    keywords = ["behavior"]

    def __init__(self, file_path: str, session_conditions: dict, start_variable: str, verbose: bool = True):
        """Initialize Seiler2024BehaviorInterface.

        Parameters
        ----------
        file_path : str
            Path to the MedPC file.
        session_conditions : dict
            The conditions that define the session. The keys are the names of the single-line variables (ex. 'Start Date')
            and the values are the values of those variables for the desired session (ex. '11/09/18').
        start_variable : str
            The name of the variable that starts the session (ex. 'Start Date').
        verbose : bool, optional
            Whether to print verbose output, by default True
        """
        super().__init__(
            file_path=file_path,
            session_conditions=session_conditions,
            start_variable=start_variable,
            verbose=verbose,
        )

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        medpc_name_to_dict_name = {
            "Start Date": "start_date",
            "Subject": "subject",
            "Box": "box",
            "Start Time": "start_time",
            "MSN": "MSN",
        }
        dict_name_to_type = {
            "start_date": date,
            "subject": str,
            "box": str,
            "start_time": time,
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
            "FOOD_FR1 Habit Training TTL": "FR1",
            "20sOmissions_TTL": "OmissionProbe",
            "20sOmissions": "OmissionProbe",
            "RR5_Left_CVC": "?",
            "RR20Right": "RR20",
            "FOOD_FR1 Habit Training TTL": "FR1",
            "FOOD_Magazine Training 1 hr": "MagazineTraining",
            "Probe Test Habit Training TTL": "OmissionProbe",
            "RI 30 RIGHT_STIM": "RI30",
            "RI 60 RIGHT STIM": "RI60",
        }
        session_dict = read_medpc_file(
            file_path=self.source_data["file_path"],
            medpc_name_to_dict_name=medpc_name_to_dict_name,
            dict_name_to_type=dict_name_to_type,
            session_conditions=self.source_data["session_conditions"],
            start_variable=self.source_data["start_variable"],
        )
        session_start_time = datetime.combine(
            session_dict["start_date"], session_dict["start_time"], tzinfo=timezone("US/Central")
        )
        training_stage = msn_to_training_stage[session_dict["MSN"]]
        session_id = session_start_time.isoformat() + "-" + training_stage

        metadata["NWBFile"]["session_description"] = session_dict["MSN"]
        metadata["NWBFile"]["session_start_time"] = session_start_time
        metadata["NWBFile"]["identifier"] = session_dict["subject"] + "-" + session_id
        metadata["NWBFile"]["session_id"] = session_id

        metadata["Subject"] = {}
        metadata["Subject"]["subject_id"] = session_dict["subject"]
        metadata["Subject"]["sex"] = "U"  # TODO: Grab sex info from sheets

        metadata["Behavior"] = {}
        metadata["Behavior"]["box"] = session_dict["box"]

        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["Behavior"] = {
            "type": "object",
            "properties": {
                "box": {"type": "string"},
            },
        }
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        if self.source_data["session_dict"] is None:
            medpc_name_to_dict_name = {
                "G": "port_entry_times",
                "E": "duration_of_port_entry",
                "A": "left_nose_poke_times",
                "C": "right_nose_poke_times",
                "D": "right_reward_times",
                "B": "left_reward_times",
            }
            dict_name_to_type = {
                "port_entry_times": np.ndarray,
                "duration_of_port_entry": np.ndarray,
                "left_nose_poke_times": np.ndarray,
                "right_nose_poke_times": np.ndarray,
                "right_reward_times": np.ndarray,
                "left_reward_times": np.ndarray,
            }
            if "ShockProbe" in metadata["NWBFile"]["session_id"]:
                medpc_name_to_dict_name["H"] = "footshock_times"
                dict_name_to_type["footshock_times"] = np.ndarray
            session_dict = read_medpc_file(
                file_path=self.source_data["file_path"],
                medpc_name_to_dict_name=medpc_name_to_dict_name,
                dict_name_to_type=dict_name_to_type,
                session_conditions=self.source_data["session_conditions"],
                start_variable=self.source_data["start_variable"],
            )
        else:
            session_dict = self.source_data["session_dict"]

        # Add behavior data to nwbfile
        behavior_module = nwb_helpers.get_module(
            nwbfile=nwbfile,
            name="behavior",
            description=f"Operant behavioral data from MedPC. Box = {metadata['Behavior']['box']}",
        )

        # Port Entry
        if (
            len(session_dict["duration_of_port_entry"]) == 0
        ):  # some sessions are missing port entry durations ex. FP Experiments/Behavior/PR/028.392/07-09-20
            if self.verbose:
                print(f"No port entry durations found for {metadata['NWBFile']['session_id']}")
            reward_port_entry_times = Events(
                name="reward_port_entry_times",
                description="Reward port entry times",
                timestamps=H5DataIO(session_dict["port_entry_times"], compression=True),
            )
            behavior_module.add(reward_port_entry_times)
        else:
            port_times, data = [], []
            for port_entry_time, duration in zip(
                session_dict["port_entry_times"], session_dict["duration_of_port_entry"]
            ):
                port_times.append(port_entry_time)
                data.append(1)
                port_times.append(port_entry_time + duration)
                data.append(-1)
            reward_port_intervals = IntervalSeries(
                name="reward_port_intervals",
                description="Interval of time spent in reward port (1 is entry, -1 is exit)",
                timestamps=H5DataIO(port_times, compression=True),
                data=data,
            )
            behavioral_epochs = BehavioralEpochs(name="behavioral_epochs")
            behavioral_epochs.add_interval_series(reward_port_intervals)
            behavior_module.add(behavioral_epochs)

        # Left/Right Nose pokes
        left_nose_poke_times = Events(
            name="left_nose_poke_times",
            description="Left nose poke times",
            timestamps=H5DataIO(session_dict["left_nose_poke_times"], compression=True),
        )
        right_nose_poke_times = Events(
            name="right_nose_poke_times",
            description="Right nose poke times",
            timestamps=H5DataIO(session_dict["right_nose_poke_times"], compression=True),
        )
        behavior_module.add(left_nose_poke_times)
        behavior_module.add(right_nose_poke_times)

        # Left/Right Rewards -- Interleaved for most sessions
        if len(session_dict["left_reward_times"]) > 0:
            left_reward_times = Events(
                name="left_reward_times",
                description="Left Reward times",
                timestamps=H5DataIO(session_dict["left_reward_times"], compression=True),
            )
            behavior_module.add(left_reward_times)
        if len(session_dict["right_reward_times"]) > 0:
            right_reward_times = Events(
                name="right_reward_times",
                description="Right Reward times",
                timestamps=H5DataIO(session_dict["right_reward_times"], compression=True),
            )
            behavior_module.add(right_reward_times)

        # Footshock
        if "ShockProbe" in metadata["NWBFile"]["session_id"]:
            footshock_times = Events(
                name="footshock_times",
                description="Footshock times",
                timestamps=session_dict["footshock_times"],
            )
            behavior_module.add(footshock_times)
