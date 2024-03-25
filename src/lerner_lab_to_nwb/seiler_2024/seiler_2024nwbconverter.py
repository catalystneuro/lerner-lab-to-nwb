"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter

from lerner_lab_to_nwb.seiler_2024 import Seiler2024BehaviorInterface
from lerner_lab_to_nwb.seiler_2024 import Seiler2024FiberPhotometryInterface
from .medpc import read_medpc_file
import numpy as np
from tdt import read_block
from sklearn.linear_model import LinearRegression


class Seiler2024NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        Behavior=Seiler2024BehaviorInterface,
        FiberPhotometry=Seiler2024FiberPhotometryInterface,
    )

    def temporally_align_data_interfaces(self):
        if not "FiberPhotometry" in self.data_interface_objects.keys():
            self.data_interface_objects["Behavior"].source_data["start_time_offset"] = 0
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
            "MSN": str,
            "port_entry_times": np.ndarray,
            "duration_of_port_entry": np.ndarray,
            "left_nose_poke_times": np.ndarray,
            "right_nose_poke_times": np.ndarray,
            "right_reward_times": np.ndarray,
            "left_reward_times": np.ndarray,
        }
        session_dict = read_medpc_file(
            file_path=self.data_interface_objects["Behavior"].source_data["file_path"],
            medpc_name_to_dict_name=medpc_name_to_dict_name,
            dict_name_to_type=dict_name_to_type,
            session_conditions=self.data_interface_objects["Behavior"].source_data["session_conditions"],
            start_variable=self.data_interface_objects["Behavior"].source_data["start_variable"],
        )

        # Read Fiber Photometry Data
        tdt_photometry = read_block(self.data_interface_objects["FiberPhotometry"].source_data["folder_path"])

        # Aggregate TTLs and Behavior Timestamps
        ttl_names_to_behavior_names = {
            "LNPS": "left_nose_poke_times",
            "RNRW": "right_reward_times",
            "RNnR": "right_nose_poke_times",
            "PrtN": "port_entry_times",
            "Sock": "footshock_times",
        }
        all_ttl_timestamps, all_behavior_timestamps = [], []
        for ttl_name, behavior_name in ttl_names_to_behavior_names.items():
            if ttl_name == "PrtN":
                ttl_timestamps = np.sort(
                    np.concatenate((tdt_photometry.epocs["PrtN"].onset, tdt_photometry.epocs["PrtR"].onset))
                )
            elif ttl_name == "Sock":
                continue
            else:
                ttl_timestamps = tdt_photometry.epocs[ttl_name].onset
            behavior_timestamps = session_dict[behavior_name]
            for ttl_timestamp, behavior_timestamp in zip(ttl_timestamps, behavior_timestamps):
                all_ttl_timestamps.append(ttl_timestamp)
                all_behavior_timestamps.append(behavior_timestamp)
        sort_indices = np.argsort(all_ttl_timestamps)
        all_ttl_timestamps = np.array(all_ttl_timestamps)[sort_indices]
        all_behavior_timestamps = np.array(all_behavior_timestamps)[sort_indices]

        # Align Timestamps
        commanded_len = len(tdt_photometry.streams["Fi1d"].data[0, :])
        commanded_fs = tdt_photometry.streams["Fi1d"].fs
        unaligned_commanded_timestamps = np.linspace(0, commanded_len / commanded_fs, commanded_len)
        aligned_commanded_timestamps = self.align_timestamps(
            unaligned_commanded_timestamps, all_ttl_timestamps, all_behavior_timestamps
        )

        response_len = len(tdt_photometry.streams["Dv1A"].data)
        response_fs = tdt_photometry.streams["Dv1A"].fs
        unaligned_response_timestamps = np.linspace(0, response_len / response_fs, response_len)
        aligned_response_timestamps = self.align_timestamps(
            unaligned_response_timestamps, all_ttl_timestamps, all_behavior_timestamps
        )

        start_time_offset = np.minimum(aligned_commanded_timestamps[0], aligned_response_timestamps[0])
        aligned_commanded_timestamps -= start_time_offset
        aligned_response_timestamps -= start_time_offset

        self.data_interface_objects["FiberPhotometry"].source_data[
            "aligned_commanded_timestamps"
        ] = aligned_commanded_timestamps
        self.data_interface_objects["FiberPhotometry"].source_data[
            "aligned_response_timestamps"
        ] = aligned_response_timestamps
        self.data_interface_objects["Behavior"].source_data["start_time_offset"] = start_time_offset

    def align_timestamps(self, unaligned_dense_timestamps, unaligned_sparse_timestamps, aligned_sparse_timestamps):
        aligned_dense_timestamps = np.interp(
            unaligned_dense_timestamps,
            unaligned_sparse_timestamps,
            aligned_sparse_timestamps,
            left=np.nan,
            right=np.nan,
        )
        extrapolated_timestamp_mask = np.isnan(aligned_dense_timestamps)
        linear_model = LinearRegression().fit(unaligned_sparse_timestamps.reshape(-1, 1), aligned_sparse_timestamps)
        extrapolated_timestamps = linear_model.predict(
            unaligned_dense_timestamps[extrapolated_timestamp_mask].reshape(-1, 1)
        )
        aligned_dense_timestamps[extrapolated_timestamp_mask] = extrapolated_timestamps
        return aligned_dense_timestamps
