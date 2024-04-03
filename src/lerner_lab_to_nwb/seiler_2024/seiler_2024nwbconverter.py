"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter

from lerner_lab_to_nwb.seiler_2024 import Seiler2024BehaviorInterface
from lerner_lab_to_nwb.seiler_2024 import Seiler2024FiberPhotometryInterface
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
    )

    def temporally_align_data_interfaces(self):
        """Align the FiberPhotometry and Behavior data interfaces in time.

        This method uses TTLs from the FiberPhotometry data that correspond to behavior events to generate aligned
        timestamps for the behavior data in the fiber photometry time basis.
        """
        if not "FiberPhotometry" in self.data_interface_objects.keys():
            self.data_interface_objects["Behavior"].source_data["session_dict"] = None
            return  # No need to align if there is no fiber photometry data

        # Read Behavior Data
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
        metadata = self.data_interface_objects["Behavior"].get_metadata()
        if "ShockProbe" in metadata["NWBFile"]["session_id"]:
            medpc_name_to_dict_name["H"] = "footshock_times"
            dict_name_to_type["footshock_times"] = np.ndarray
        session_dict = read_medpc_file(
            file_path=self.data_interface_objects["Behavior"].source_data["file_path"],
            medpc_name_to_dict_name=medpc_name_to_dict_name,
            dict_name_to_type=dict_name_to_type,
            session_conditions=self.data_interface_objects["Behavior"].source_data["session_conditions"],
            start_variable=self.data_interface_objects["Behavior"].source_data["start_variable"],
        )

        # Read Fiber Photometry Data
        with open(os.devnull, "w") as f, redirect_stdout(f):
            tdt_photometry = read_block(self.data_interface_objects["FiberPhotometry"].source_data["folder_path"])

        # Aggregate TTLs and Behavior Timestamps
        msn = metadata["NWBFile"]["session_description"]
        if "RIGHT" in msn or "Right" in msn or "right" in msn:
            ttl_names_to_behavior_names = {
                "LNPS": "left_nose_poke_times",
                "RNRW": "right_reward_times",
                "RNnR": "right_nose_poke_times",
                "PrtN": "port_entry_times",
                "Sock": "footshock_times",
            }
        elif "LEFT" in msn or "Left" in msn or "left" in msn:
            ttl_names_to_behavior_names = {
                "RNPS": "right_nose_poke_times",
                "LNRW": "left_reward_times",
                "LNnR": "left_nose_poke_times",
                "PrtN": "port_entry_times",
                "Sock": "footshock_times",
            }
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
