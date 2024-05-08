"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile
from datetime import datetime, date, time
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
        msn_to_session_description = {
            "20sOmissions_TTL": "Omission Probe with concurrent fiber photometry",
            "20sOmissions": "Omission Probe",
            "FOOD_FR1 Habit Training TTL": "FR1 Habit Training with concurrent fiber photometry",
            "FOOD_FR1 HT TTL (Both)": "FR1 Habit Training with concurrent fiber photometry, rewards delivered on both left and right nose pokes",
            "FOOD_FR1 TTL Left": "FR1 Training with concurrent fiber photometry, rewards delivered on left nose pokes",
            "FOOD_FR1 TTL Right": "FR1 Training with concurrent fiber photometry, rewards delivered on right nose pokes",
            "FOOD_RI 30 LEFT": "RI30 Training, rewards delivered on left nose pokes",
            "FOOD_RI 30 RIGHT TTL": "RI30 Training with concurrent fiber photometry, rewards delivered on right nose pokes",
            "FOOD_RI 60 LEFT TTL": "RI60 Training with concurrent fiber photometry, rewards delivered on left nose pokes",
            "FOOD_RI 60 RIGHT TTL": "RI60 Training with concurrent fiber photometry, rewards delivered on right nose pokes",
            "Footshock Degradation Left": "Footshock Probe, shocks delivered on left nose pokes",
            "Footshock Degradation right": "Footshock Probe, shocks delivered on right nose pokes",
            "FR1_BOTH_SCRAMBLED": "FR1 Training with optogenetic stimulation, rewards delivered on both left and right nose pokes, optogenetic stimulation delivered on random nose pokes",
            "FR1_BOTH_WStim": "FR1 Training with optogenetic stimulation, rewards delivered on both left and right nose pokes, optogenetic stimulation delivered on all nose pokes",
            "FR1_LEFT_SCRAM": "FR1 Training with optogenetic stimulation, rewards delivered on left nose pokes, optogenetic stimulation delivered on random nose pokes",
            "FR1_LEFT_STIM": "FR1 Training with optogenetic stimulation, rewards delivered on left nose pokes, optogenetic stimulation delivered on left nose pokes",
            "FR1_RIGHT_SCRAMBLED": "FR1 Training with optogenetic stimulation, rewards delivered on right nose pokes, optogenetic stimulation delivered on random nose pokes",
            "FR1_RIGHT_STIM": "FR1 Training with optogenetic stimulation, rewards delivered on right nose pokes, optogenetic stimulation delivered on right nose pokes",
            "Probe Test Habit Training TTL": "Probe Test",
            "RI 30 RIGHT_STIM": "RI30 Training with optogenetic stimulation, rewards delivered on right nose pokes, optogenetic stimulation delivered on right nose pokes",
            "RI 60 RIGHT STIM": "RI60 Training with optogenetic stimulation, rewards delivered on right nose pokes, optogenetic stimulation delivered on right nose pokes",
            "RI 60 LEFT_STIM": "RI60 Training with optogenetic stimulation, rewards delivered on left nose pokes, optogenetic stimulation delivered on left nose pokes",
            "RI 30 LEFT_STIM": "RI30 Training with optogenetic stimulation, rewards delivered on left nose pokes, optogenetic stimulation delivered on left nose pokes",
            "RI30 Left Scrambled": "RI30 Training with optogenetic stimulation, rewards delivered on left nose pokes, optogenetic stimulation delivered on random nose pokes",
            "RI30 Right SCRAMBLED": "RI30 Training with optogenetic stimulation, rewards delivered on right nose pokes, optogenetic stimulation delivered on random nose pokes",
            "RI60_LEFT_SCRAM": "RI60 Training with optogenetic stimulation, rewards delivered on left nose pokes, optogenetic stimulation delivered on random nose pokes",
            "RI60_RIGHT_SCRAM": "RI60 Training with optogenetic stimulation, rewards delivered on right nose pokes, optogenetic stimulation delivered on random nose pokes",
            "RR5_Left_CVC": "RR5 Training",
            "RR20Left": "RR20 Training, rewards delivered on left nose pokes",
            "RR20_Left": "RR20 Training, rewards delivered on left nose pokes",
            "RR20Right": "RR20 Training, rewards delivered on right nose pokes",
            "RR20_Right_AHJS": "RR20 Training, rewards delivered on right nose pokes",
            "Unknown": "Unknown",
        }
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
        if self.source_data["from_csv"]:
            session_dtypes = {
                "Start Date": str,
                "End Date": str,
                "Start Time": str,
                "End Time": str,
                "MSN": str,
                "Experiment": str,
                "Subject": str,
                "Box": str,
            }
            session_df = pd.read_csv(self.source_data["file_path"], dtype=session_dtypes)
            start_date = (
                session_df["Start Date"][0]
                if "Start Date" in session_df.columns
                else Path(self.source_data["file_path"]).stem.split("_")[1].replace("-", "/")
            )
            start_date = datetime.strptime(start_date, "%m/%d/%y").date()
            start_time = session_df["Start Time"][0] if "Start Time" in session_df.columns else "00:00:00"
            start_time = datetime.strptime(start_time, "%H:%M:%S").time()
            msn = session_df["MSN"][0] if "MSN" in session_df.columns else "Unknown"
            box = session_df["Box"][0] if "Box" in session_df.columns else "Unknown"
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
            msn = session_dict["MSN"]
            box = session_dict["box"]

        session_start_time = datetime.combine(start_date, start_time)
        metadata["NWBFile"]["session_start_time"] = session_start_time

        metadata["Behavior"] = {}
        metadata["Behavior"]["box"] = box
        metadata["Behavior"]["msn"] = msn
        metadata["Behavior"]["session_description"] = msn_to_session_description[msn]

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
            session_dtypes = {
                "Start Date": str,
                "End Date": str,
                "Start Time": str,
                "End Time": str,
                "MSN": str,
                "Experiment": str,
                "Subject": str,
                "Box": str,
            }
            session_df = pd.read_csv(self.source_data["file_path"], dtype=session_dtypes)
            session_dict = {}
            for csv_name, dict_name in csv_name_to_dict_name.items():
                session_dict[dict_name] = np.trim_zeros(session_df[csv_name].dropna().values, trim="b")
        else:
            session_dict = self.source_data["session_dict"]

        # Add behavior data to nwbfile
        behavior_module = nwb_helpers.get_module(
            nwbfile=nwbfile,
            name="behavior",
            description=(
                f"Operant behavioral data from MedPC.\n"
                f"Box = {metadata['Behavior']['box']}\n"
                f"MSN = {metadata['Behavior']['msn']}"
            ),
        )

        # Port Entry
        if (
            len(session_dict["duration_of_port_entry"]) == 0
        ):  # some sessions are missing port entry durations ex. FP Experiments/Behavior/PR/028.392/07-09-20
            if self.verbose:
                print(f"No port entry durations found for {metadata['NWBFile']['session_id']}")
            if len(session_dict["port_entry_times"]) > 0:
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
        if len(session_dict["left_nose_poke_times"]) > 0:
            left_nose_poke_times = Events(
                name="left_nose_poke_times",
                description="Left nose poke times",
                timestamps=H5DataIO(session_dict["left_nose_poke_times"], compression=True),
            )
            behavior_module.add(left_nose_poke_times)
        if len(session_dict["right_nose_poke_times"]) > 0:
            right_nose_poke_times = Events(
                name="right_nose_poke_times",
                description="Right nose poke times",
                timestamps=H5DataIO(session_dict["right_nose_poke_times"], compression=True),
            )
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
        if "footshock_times" in session_dict and len(session_dict["footshock_times"]) > 0:
            footshock_times = Events(
                name="footshock_times",
                description="Footshock times",
                timestamps=session_dict["footshock_times"],
            )
            behavior_module.add(footshock_times)
