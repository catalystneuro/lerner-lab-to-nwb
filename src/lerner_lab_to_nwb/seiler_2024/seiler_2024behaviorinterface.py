"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from datetime import datetime, date, time
from pytz import timezone
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from neuroconv.tools import nwb_helpers
import numpy as np
import pandas as pd
from ndx_events import Events
from pynwb.behavior import BehavioralEpochs, IntervalSeries
from hdmf.backends.hdf5.h5_utils import H5DataIO
from pathlib import Path

from .medpc import read_medpc_file


class Seiler2024BehaviorInterface(BaseDataInterface):
    """Behavior interface for seiler_2024 conversion"""

    keywords = ["behavior"]

    def __init__(self, file_path: str, session_conditions: dict, start_variable: str, verbose: bool = True):
        """Initialize Seiler2024BehaviorInterface.

        Parameters
        ----------
        file_path : str
            Path to the MedPC file. Or path to the CSV file.
        session_conditions : dict
            The conditions that define the session. The keys are the names of the single-line variables (ex. 'Start Date')
            and the values are the values of those variables for the desired session (ex. '11/09/18').
        start_variable : str
            The name of the variable that starts the session (ex. 'Start Date').
        verbose : bool, optional
            Whether to print verbose output, by default True
        """
        from_csv = file_path.endswith(".csv")
        super().__init__(
            file_path=file_path,
            session_conditions=session_conditions,
            start_variable=start_variable,
            from_csv=from_csv,
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
            "RR5_Left_CVC": "RR5",
            "RR20Right": "RR20",
            "FOOD_FR1 Habit Training TTL": "FR1",
            "Probe Test Habit Training TTL": "OmissionProbe",  # TODO: Confirm with Lerner Lab
            "RI 30 RIGHT_STIM": "RI30",
            "RI 60 RIGHT STIM": "RI60",
            "RI 60 LEFT_STIM": "RI60",
        }
        if self.source_data["from_csv"]:
            start_date = datetime.strptime(Path(self.source_data["file_path"]).stem.split("_")[1], "%m-%d-%y")
            start_time = time(0, 0, 0)
            training_stage = "Unknown"
            subject = Path(self.source_data["file_path"]).stem.split("_")[0]
            msn = "Unknown"
            box = "Unknown"
        else:
            session_dict = read_medpc_file(
                file_path=self.source_data["file_path"],
                medpc_name_to_dict_name=medpc_name_to_dict_name,
                dict_name_to_type=dict_name_to_type,
                session_conditions=self.source_data["session_conditions"],
                start_variable=self.source_data["start_variable"],
            )
            start_date = session_dict["start_date"]
            start_time = session_dict["start_time"]
            training_stage = msn_to_training_stage[session_dict["MSN"]]
            subject = session_dict["subject"]
            msn = session_dict["MSN"]
            box = session_dict["box"]

        session_start_time = datetime.combine(start_date, start_time, tzinfo=timezone("US/Central"))
        session_id = session_start_time.isoformat() + "-" + training_stage

        metadata["NWBFile"]["session_start_time"] = session_start_time
        metadata["NWBFile"]["identifier"] = subject + "-" + session_id
        metadata["NWBFile"]["session_id"] = session_id

        metadata["Subject"] = {}
        metadata["Subject"]["subject_id"] = subject
        metadata["Subject"]["sex"] = "U"  # TODO: Grab sex info from sheets

        metadata["Behavior"] = {}
        metadata["Behavior"]["box"] = box
        metadata["Behavior"]["msn"] = msn

        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["Behavior"] = {
            "type": "object",
            "properties": {
                "box": {"type": "string"},
                "msn": {"type": "string"},
            },
        }
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict) -> None:
        from_csv = self.source_data["from_csv"]
        if self.source_data["session_dict"] is None and not from_csv:
            msn = metadata["Behavior"]["msn"]
            medpc_name_to_dict_name = metadata["Behavior"]["msn_to_medpc_name_to_dict_name"][msn]
            dict_name_to_type = {dict_name: np.ndarray for dict_name in medpc_name_to_dict_name.values()}
            session_dict = read_medpc_file(
                file_path=self.source_data["file_path"],
                medpc_name_to_dict_name=medpc_name_to_dict_name,
                dict_name_to_type=dict_name_to_type,
                session_conditions=self.source_data["session_conditions"],
                start_variable=self.source_data["start_variable"],
            )
        elif self.source_data["session_dict"] is None and from_csv:
            csv_name_to_dict_name = {
                "portEntryTs": "port_entry_times",
                "DurationOfPE": "duration_of_port_entry",
                "LeftNoseTs": "left_nose_poke_times",
                "RightNoseTs": "right_nose_poke_times",
                "RightRewardTs": "right_reward_times",
                "LeftRewardTs": "left_reward_times",
            }
            session_df = pd.read_csv(self.source_data["file_path"])
            session_dict = {}
            for csv_name, dict_name in csv_name_to_dict_name.items():
                session_dict[dict_name] = np.trim_zeros(session_df[csv_name].dropna().values, trim="b")
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
        if "footshock_times" in session_dict:
            footshock_times = Events(
                name="footshock_times",
                description="Footshock times",
                timestamps=session_dict["footshock_times"],
            )
            behavior_module.add(footshock_times)
