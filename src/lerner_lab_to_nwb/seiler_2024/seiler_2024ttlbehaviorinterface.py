"""Behavior interface for sessions whose only behavior record is the TTLs of the fiber photometry system."""
import os
from contextlib import redirect_stdout
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import numpy as np
from ndx_events import Events
from neuroconv.basetemporalalignmentinterface import BaseTemporalAlignmentInterface
from neuroconv.tools import nwb_helpers
from neuroconv.utils import DeepDict
from pynwb.file import NWBFile
from tdt import read_block

TDT_TIMEZONE = ZoneInfo("America/Chicago")


class Seiler2024TTLBehaviorInterface(BaseTemporalAlignmentInterface):
    """Behavior interface for a fiber photometry session that has no MedPC record.

    The behavioral events are the TTLs that the MedPC program sent to the fiber photometry system. The converter maps
    them to behavior names from the MSN of the program and sets them with set_aligned_timestamps.
    """

    keywords = ["behavior"]

    def __init__(self, folder_path: str, msn: str, verbose: bool = True):
        """Initialize Seiler2024TTLBehaviorInterface.

        Parameters
        ----------
        folder_path : str
            Path to the folder of the TDT block that holds the TTLs.
        msn : str
            The MSN of the MedPC program that sent the TTLs, ex. 'Footshock Degradation Left'.
        verbose : bool, optional
            Whether to print verbose output, by default True
        """
        super().__init__(folder_path=folder_path, msn=msn, verbose=verbose)
        self.timestamps_dict = {}

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        with open(os.devnull, "w") as f, redirect_stdout(f):
            tdt_block = read_block(self.source_data["folder_path"], evtype=["epocs"])
        # tdt gives the block start in the local time of the computer running the conversion
        start_timestamp = round(tdt_block.info.start_date.timestamp())
        start_datetime = datetime.fromtimestamp(start_timestamp, tz=TDT_TIMEZONE)
        metadata["TTLBehavior"] = {
            "MSN": self.source_data["msn"],
            "start_date": start_datetime.strftime("%m/%d/%y"),
            "start_time": start_datetime.strftime("%H:%M:%S"),
        }
        return metadata

    def get_original_timestamps(self) -> dict[str, np.ndarray]:
        raise NotImplementedError("The TTL onsets are set by the converter with set_aligned_timestamps.")

    def get_timestamps(self) -> dict[str, np.ndarray]:
        return self.timestamps_dict

    def set_aligned_timestamps(self, aligned_timestamps_dict: dict[str, np.ndarray]) -> None:
        self.timestamps_dict = aligned_timestamps_dict

    def set_aligned_starting_time(self, aligned_starting_time: float) -> None:
        self.timestamps_dict = {
            name: timestamps + aligned_starting_time for name, timestamps in self.timestamps_dict.items()
        }

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict) -> None:
        name_to_description = {event["name"]: event["description"] for event in metadata["MedPC"]["Events"]}
        name_to_description["reward_port_entry_times"] = "Reward port entry times"
        behavior_module = nwb_helpers.get_module(
            nwbfile=nwbfile,
            name="behavior",
            description=(
                "Operant behavioral events from the TTLs that the MedPC program sent to the fiber photometry system. "
                "No MedPC record of this session exists.\n"
                f"MSN = {metadata['TTLBehavior']['MSN']}"
            ),
        )
        for name, timestamps in self.get_timestamps().items():
            if len(timestamps) == 0:
                continue
            behavior_module.add(Events(name=name, description=name_to_description[name], timestamps=timestamps))
        assert behavior_module.data_interfaces, "No behavior TTLs were found for this session."
