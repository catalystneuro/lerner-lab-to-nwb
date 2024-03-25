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
        """Align the FiberPhotometry and Behavior data interfaces in time.

        This method uses TTLs from the FiberPhotometry data that correspond to behavior events to generate aligned
        timestamps for the photometry data. Then, all timestamps are shifted such that the fiber photometry starts at 0s.
        """
        if not "FiberPhotometry" in self.data_interface_objects.keys():
            self.data_interface_objects["Behavior"].source_data["start_time_offset"] = 0
            return  # No need to align if there is no fiber photometry data

        # Read Behavior Data
        medpc_name_to_dict_name = {
            "G": "port_entry_times",
            "A": "left_nose_poke_times",
            "C": "right_nose_poke_times",
            "D": "right_reward_times",
            "B": "left_reward_times",
        }
        dict_name_to_type = {
            "port_entry_times": np.ndarray,
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
        metadata = self.data_interface_objects["Behavior"].get_metadata(session_dict)

        # Read Fiber Photometry Data
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
        all_ttl_timestamps, all_behavior_timestamps = [], []
        for ttl_name, behavior_name in ttl_names_to_behavior_names.items():
            if ttl_name == "PrtN":
                ttl_timestamps = np.sort(
                    np.concatenate((tdt_photometry.epocs["PrtN"].onset, tdt_photometry.epocs["PrtR"].onset))
                )
            elif ttl_name == "Sock" and "ShockProbe" not in metadata["NWBFile"]["session_id"]:
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
        commanded_len = tdt_photometry.streams["Fi1d"].data.shape[1]
        commanded_fs = tdt_photometry.streams["Fi1d"].fs
        unaligned_commanded_timestamps = np.linspace(0, commanded_len / commanded_fs, commanded_len)
        aligned_commanded_timestamps = self.align_timestamps(
            unaligned_commanded_timestamps, all_ttl_timestamps, all_behavior_timestamps
        )

        response_len = tdt_photometry.streams["Dv1A"].data.shape[0]
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
        """
        Interpolate the timestamps of this interface using a mapping from some unaligned time basis to its aligned one.
        Then, using a linear model, extrapolate the timestamps that could not be interpolated.

        Use this method if the unaligned timestamps of the data in this interface are not directly tracked by a primary
        system, but are known to occur between timestamps that are tracked, then align the timestamps of this interface
        by interpolating between the two.

        An example could be a metronomic TTL pulse (e.g., every second) from a secondary data stream to the primary
        timing system; if the time references of this interface are recorded within the relative time of the secondary
        data stream, then their exact time in the primary system is inferred given the pulse times.

        Must be in units seconds relative to the common 'session_start_time'.

        Parameters
        ----------
        unaligned_dense_timestamps : numpy.ndarray
            The dense timestamps of the unaligned secondary time basis.
        unaligned_timestamps : numpy.ndarray
            The sparse timestamps of the unaligned secondary time basis.
        aligned_timestamps : numpy.ndarray
            The sparse timestamps aligned to the primary time basis.

        Returns
        -------
        numpy.ndarray
            The dense timestamps aligned to the primary time basis.
        """
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
