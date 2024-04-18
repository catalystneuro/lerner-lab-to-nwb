"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
from typing import Optional
from pynwb import NWBFile
from neuroconv.tools.nwb_helpers import make_or_load_nwbfile

from lerner_lab_to_nwb.seiler_2024 import (
    Seiler2024BehaviorInterface,
    Seiler2024FiberPhotometryInterface,
    Seiler2024OptogeneticInterface,
)
from .medpc import read_medpc_file
import numpy as np
from tdt import read_block
import os
from contextlib import redirect_stdout


class Seiler2024NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        Behavior=Seiler2024BehaviorInterface,
        FiberPhotometry=Seiler2024FiberPhotometryInterface,
        Optogenetic=Seiler2024OptogeneticInterface,
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
            self.data_interface_objects["Behavior"].source_data["session_dict"] = None
            return  # No need to align if there is no fiber photometry data

        # Read Behavior Data
        msn = metadata["Behavior"]["msn"]
        medpc_name_to_dict_name = metadata["Behavior"]["msn_to_medpc_name_to_dict_name"][msn]
        dict_name_to_type = {dict_name: np.ndarray for dict_name in medpc_name_to_dict_name.values()}
        session_dict = read_medpc_file(
            file_path=self.data_interface_objects["Behavior"].source_data["file_path"],
            medpc_name_to_dict_name=medpc_name_to_dict_name,
            dict_name_to_type=dict_name_to_type,
            session_conditions=self.data_interface_objects["Behavior"].source_data["session_conditions"],
            start_variable=self.data_interface_objects["Behavior"].source_data["start_variable"],
        )

        # Read Fiber Photometry Data
        t2 = conversion_options["FiberPhotometry"]["t2"] if "t2" in conversion_options["FiberPhotometry"] else None
        with open(os.devnull, "w") as f, redirect_stdout(f):
            if t2 is None:
                tdt_photometry = read_block(self.data_interface_objects["FiberPhotometry"].source_data["folder_path"])
            else:
                tdt_photometry = read_block(
                    self.data_interface_objects["FiberPhotometry"].source_data["folder_path"], t2=t2
                )

        # Aggregate TTLs and Behavior Timestamps
        right_ttl_names_to_behavior_names = {
            "LNPS": "left_nose_poke_times",
            "RNRW": "right_reward_times",
            "RNnR": "right_nose_poke_times",
            "PrtN": "port_entry_times",
            "Sock": "footshock_times",
        }
        left_ttl_names_to_behavior_names = {
            "RNPS": "right_nose_poke_times",
            "LNRW": "left_reward_times",
            "LNnR": "left_nose_poke_times",
            "PrtN": "port_entry_times",
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
        for ttl_name, behavior_name in ttl_names_to_behavior_names.items():
            if ttl_name == "PrtN":
                ttl_timestamps = []
                if "PrtN" in tdt_photometry.epocs:
                    for timestamp in tdt_photometry.epocs["PrtN"].onset:
                        ttl_timestamps.append(timestamp)
                if "PrtR" in tdt_photometry.epocs:
                    for timestamp in tdt_photometry.epocs["PrtR"].onset:
                        ttl_timestamps.append(timestamp)
                ttl_timestamps = np.sort(ttl_timestamps)
            elif ttl_name == "Sock" and "ShockProbe" not in metadata["NWBFile"]["session_id"]:
                continue
            else:
                if len(session_dict[behavior_name]) == 0:
                    continue  # If behavior is not present the tdt file will not have the appropriate TTL
                ttl_timestamps = tdt_photometry.epocs[ttl_name].onset
            session_dict[behavior_name] = ttl_timestamps
        self.data_interface_objects["Behavior"].source_data["session_dict"] = session_dict

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
