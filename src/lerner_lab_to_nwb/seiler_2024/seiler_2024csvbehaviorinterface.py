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


class Seiler2024CSVBehaviorInterface(BaseDataInterface):
    """Behavior interface for seiler_2024 conversion"""

    keywords = ["behavior"]

    def __init__(self, file_path: str, has_port_entry_durations: bool = True, verbose: bool = True):
        """Initialize Seiler2024BehaviorInterface.

        Parameters
        ----------
        file_path : str
            Path to the CSV file.
        verbose : bool, optional
            Whether to print verbose output, by default True
        """
        super().__init__(
            file_path=file_path,
            has_port_entry_durations=has_port_entry_durations,
            verbose=verbose,
        )

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
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
        start_time = session_df["Start Time"][0] if "Start Time" in session_df.columns else "00:00:00"
        msn = session_df["MSN"][0] if "MSN" in session_df.columns else "Unknown"
        box = session_df["Box"][0] if "Box" in session_df.columns else "Unknown"

        metadata["Behavior"] = {
            "Box": box,
            "MSN": msn,
            "start_date": start_date,
            "start_time": start_time,
        }

        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["Behavior"] = {
            "type": "object",
            "properties": {
                "Box": {"type": "string"},
                "MSN": {"type": "string"},
            },
        }
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict) -> None:
        if self.source_data["session_dict"] is None:
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
        if not self.source_data[
            "has_port_entry_durations"
        ]:  # some sessions are missing port entry durations ex. FP Experiments/Behavior/PR/028.392/07-09-20
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
