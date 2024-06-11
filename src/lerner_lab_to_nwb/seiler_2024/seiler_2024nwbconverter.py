"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from typing import Optional
from pynwb import NWBFile
from neuroconv.tools.nwb_helpers import make_or_load_nwbfile

from lerner_lab_to_nwb.seiler_2024 import (
    Seiler2024FiberPhotometryInterface,
    Seiler2024OptogeneticInterface,
    Seiler2024ExcelMetadataInterface,
    Seiler2024CSVBehaviorInterface,
    Seiler2024WesternBlotInterface,
)
from .medpcdatainterface import MedPCInterface
from .medpc_helpers import read_medpc_file
import numpy as np
import pandas as pd
from tdt import read_block
import os
from contextlib import redirect_stdout
from pathlib import Path


class Seiler2024NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        FiberPhotometry=Seiler2024FiberPhotometryInterface,
        Optogenetic=Seiler2024OptogeneticInterface,
        Metadata=Seiler2024ExcelMetadataInterface,
        MedPC=MedPCInterface,
        Behavior=Seiler2024CSVBehaviorInterface,
    )

    def temporally_align_data_interfaces(self, metadata: dict, conversion_options: dict):
        """Align the FiberPhotometry and Behavior data interfaces in time.

        This method uses TTLs from the FiberPhotometry data that correspond to behavior events to generate aligned
        timestamps for the behavior data in the fiber photometry time basis.

        Parameters
        ----------
        metadata : dict
            The metadata for the session.
        conversion_options : dict
            The conversion options for the session.
        """
        if not "FiberPhotometry" in self.data_interface_objects.keys():
            return  # No need to align if there is no fiber photometry data

        # Read Behavior Data
        if "MedPC" in self.data_interface_objects.keys():
            msn = metadata["MedPC"]["MSN"]
            medpc_name_to_output_name = metadata["MedPC"]["msn_to_medpc_name_to_output_name"][msn]
            medpc_name_to_info_dict = {
                medpc_name: {"name": output_name, "is_array": True}
                for medpc_name, output_name in medpc_name_to_output_name.items()
            }
            session_dict = read_medpc_file(
                file_path=self.data_interface_objects["MedPC"].source_data["file_path"],
                medpc_name_to_info_dict=medpc_name_to_info_dict,
                session_conditions=self.data_interface_objects["MedPC"].source_data["session_conditions"],
                start_variable=self.data_interface_objects["MedPC"].source_data["start_variable"],
            )
        elif "Behavior" in self.data_interface_objects.keys():
            csv_name_to_dict_name = {
                "portEntryTs": "port_entry_times",
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

        # Read Fiber Photometry Data
        t2 = conversion_options["FiberPhotometry"].get("t2", None)
        folder_path = Path(self.data_interface_objects["FiberPhotometry"].source_data["folder_path"])
        second_folder_path = conversion_options["FiberPhotometry"].get("second_folder_path", None)
        with open(os.devnull, "w") as f, redirect_stdout(f):
            if t2 is None:
                tdt_photometry = read_block(folder_path)
            else:
                tdt_photometry = read_block(folder_path, t2=t2)
            if second_folder_path is not None:
                tdt_photometry2 = read_block(second_folder_path)

        # Aggregate TTLs and Behavior Timestamps
        right_ttl_names_to_behavior_names = {
            "LNPS": "left_nose_poke_times",
            "RNRW": "right_reward_times",
            "RNnR": "right_nose_poke_times",
            "PrtN": "reward_port_entry_times",
            "Sock": "footshock_times",
        }
        left_ttl_names_to_behavior_names = {
            "RNPS": "right_nose_poke_times",
            "LNRW": "left_reward_times",
            "LNnR": "left_nose_poke_times",
            "PrtN": "reward_port_entry_times",
            "Sock": "footshock_times",
        }
        msn_is_right = "RIGHT" in msn or "Right" in msn or "right" in msn
        msn_is_left = "LEFT" in msn or "Left" in msn or "left" in msn or msn == "Probe Test Habit Training TTL"
        if not conversion_options["FiberPhotometry"]["flip_ttls_lr"] and msn_is_right:
            ttl_names_to_behavior_names = right_ttl_names_to_behavior_names
        elif not conversion_options["FiberPhotometry"]["flip_ttls_lr"] and msn_is_left:
            ttl_names_to_behavior_names = left_ttl_names_to_behavior_names
        elif conversion_options["FiberPhotometry"]["flip_ttls_lr"] and msn_is_right:
            ttl_names_to_behavior_names = left_ttl_names_to_behavior_names
        elif conversion_options["FiberPhotometry"]["flip_ttls_lr"] and msn_is_left:
            ttl_names_to_behavior_names = right_ttl_names_to_behavior_names
        else:
            raise ValueError(f"MSN ({msn}) does not indicate appropriate TTLs for alignment.")
        if folder_path.name == "Photo_332_393-200728-122403":
            ttl_names_to_behavior_names = {  # This special session only has 2 TTLs bc it is split into 2 folders
                "RNnR": "right_nose_poke_times",
                "PrtN": "reward_port_entry_times",
            }
        for ttl_name, behavior_name in ttl_names_to_behavior_names.items():
            if ttl_name == "Sock" and "ShockProbe" not in metadata["NWBFile"]["session_id"]:
                continue  # If the session is not a shock probe session the tdt file will not have the appropriate TTL
            if len(session_dict[behavior_name]) == 0:
                continue  # If behavior is not present the tdt file will not have the appropriate TTL
            len_behavior = len(session_dict[behavior_name])

            ttl_timestamps = self.get_ttl_timestamps(ttl_name, tdt_photometry, len_behavior)
            if second_folder_path is not None:
                ttl_timestamps2 = self.get_ttl_timestamps(ttl_name, tdt_photometry2, len_behavior)
                ttl_timestamps = np.concatenate((ttl_timestamps, ttl_timestamps2))
            session_dict[behavior_name] = ttl_timestamps
        if "MedPC" in self.data_interface_objects.keys():
            behavioral_interface = "MedPC"
        elif "Behavior" in self.data_interface_objects.keys():
            behavioral_interface = "Behavior"
        self.data_interface_objects[behavioral_interface].set_aligned_timestamps(session_dict)
        self.data_interface_objects[behavioral_interface].source_data["aligned_timestamp_names"] = list(
            session_dict.keys()
        )

    def get_ttl_timestamps(self, ttl_name, tdt_photometry, len_behavior):
        if ttl_name == "PrtN":
            ttl_timestamps = []
            if "PrtN" in tdt_photometry.epocs.keys():
                for timestamp in tdt_photometry.epocs["PrtN"].onset:
                    ttl_timestamps.append(timestamp)
            if "PrtR" in tdt_photometry.epocs.keys():
                for timestamp in tdt_photometry.epocs["PrtR"].onset:
                    ttl_timestamps.append(timestamp)
            ttl_timestamps = np.sort(ttl_timestamps)
        elif ttl_name == "RNnR" or ttl_name == "LNnR" and len(tdt_photometry.epocs[ttl_name].onset) != len_behavior:
            rewarded_ttl_name = ttl_name[:2] + "RW"  # RNRW or LNRW
            if (
                len(tdt_photometry.epocs[ttl_name].onset) + len(tdt_photometry.epocs[rewarded_ttl_name].onset)
                == len_behavior
            ):
                ttl_timestamps = []
                for timestamp in tdt_photometry.epocs[ttl_name].onset:
                    ttl_timestamps.append(timestamp)
                for timestamp in tdt_photometry.epocs[rewarded_ttl_name].onset:
                    ttl_timestamps.append(timestamp)
                ttl_timestamps = np.sort(ttl_timestamps)
            else:  # TTLs and behavior do not match
                NnR_has_all_nose_pokes = all_close_contains(
                    query_array=tdt_photometry.epocs[rewarded_ttl_name].onset,
                    target_array=tdt_photometry.epocs[ttl_name].onset,
                    tolerance=0.1,
                )
                if NnR_has_all_nose_pokes:
                    ttl_timestamps = tdt_photometry.epocs[ttl_name].onset
                else:
                    ttl_timestamps = []
                    for timestamp in tdt_photometry.epocs[ttl_name].onset:
                        ttl_timestamps.append(timestamp)
                    for timestamp in tdt_photometry.epocs[rewarded_ttl_name].onset:
                        ttl_timestamps.append(timestamp)
                    ttl_timestamps = np.sort(ttl_timestamps)
        else:
            ttl_timestamps = tdt_photometry.epocs[ttl_name].onset
        return ttl_timestamps

    def run_conversion(
        self,
        nwbfile_path: Optional[str] = None,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        overwrite: bool = False,
        conversion_options: Optional[dict] = None,
    ) -> None:
        if metadata is None:
            metadata = self.get_metadata()

        self.validate_metadata(metadata=metadata)

        self.validate_conversion_options(conversion_options=conversion_options)

        self.temporally_align_data_interfaces(metadata=metadata, conversion_options=conversion_options)

        with make_or_load_nwbfile(
            nwbfile_path=nwbfile_path,
            nwbfile=nwbfile,
            metadata=metadata,
            overwrite=overwrite,
            verbose=self.verbose,
        ) as nwbfile_out:
            self.add_to_nwbfile(nwbfile_out, metadata, conversion_options)


class Seiler2024WesternBlotNWBConverter(NWBConverter):
    """Western Blot conversion class."""

    data_interface_classes = dict(
        WesternBlot=Seiler2024WesternBlotInterface,
    )


def all_close_contains(*, query_array: np.ndarray, target_array: np.ndarray, tolerance: float) -> bool:
    """Check if all elements in query_array are present (up to some tolerance) in target_array.

    Parameters
    ----------
    query_array : np.ndarray
        The array to check.
    target_array : np.ndarray
        The array to check against.
    tolerance : float
        The tolerance for closeness.

    Returns
    -------
    bool
        Whether all elements in query_array are within tolerance of any element in target_array.
    """
    for query_element in query_array:
        if np.min(np.abs(target_array - query_element)) > tolerance:
            assert (
                np.min(np.abs(target_array - query_element)) > 10 * tolerance
            ), f"Edge case TTLs need investigation (<tolerance but >10 x tolerance)."
            return False
    return True
