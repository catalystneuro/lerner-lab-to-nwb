"""Primary class for converting experiment-specific optogenetic stimulation."""
import numpy as np
from pynwb.file import NWBFile
from pynwb.ogen import OptogeneticSeries
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from typing import Literal
from hdmf.backends.hdf5.h5_utils import H5DataIO

from .medpc import read_medpc_file


class Seiler2024OptogeneticInterface(BaseDataInterface):
    """Optogenetic interface for seiler_2024 conversion."""

    keywords = ["optogenetics"]

    def __init__(
        self,
        file_path: str,
        session_conditions: dict,
        start_variable: str,
        experimental_group: Literal["DMS-Inhibitory", "DMS-Excitatory", "DLS-Excitatory"],
        optogenetic_treatment: Literal["ChR2", "EYFP", "ChR2Scrambled", "NpHR", "NpHRScrambled"],
        verbose: bool = True,
    ):
        """Initialize Seiler2024OptogeneticInterface.

        Parameters
        ----------
        file_path : str
            Path to the MedPC file. Or path to the CSV file.
        session_conditions : dict
            The conditions that define the session. The keys are the names of the single-line variables (ex. 'Start Date')
            and the values are the values of those variables for the desired session (ex. '11/09/18').
        start_variable : str
            The name of the variable that starts the session (ex. 'Start Date').
        experimental_group : Literal["DMS-Inhibitory", "DMS-Excitatory", "DLS-Excitatory"]
            The experimental group.
        optogenetic_treatment : Literal["ChR2", "EYFP", "ChR2Scrambled", "NpHR", "NpHRScrambled"]
            The optogenetic treatment.
        verbose : bool, optional
            Whether to print verbose output, by default True
        """
        super().__init__(
            file_path=file_path,
            session_conditions=session_conditions,
            start_variable=start_variable,
            experimental_group=experimental_group,
            optogenetic_treatment=optogenetic_treatment,
            verbose=verbose,
        )

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # Read stim times from medpc file
        msn = metadata["Behavior"]["msn"]
        medpc_name_to_dict_name = metadata["Behavior"]["msn_to_medpc_name_to_dict_name"][msn]
        opto_dict_names = {"left_reward_times", "right_reward_times", "optogenetic_stimulation_times"}
        medpc_name_to_dict_name = {
            medpc_name: dict_name
            for medpc_name, dict_name in medpc_name_to_dict_name.items()
            if dict_name in opto_dict_names
        }
        dict_name_to_type = {dict_name: np.ndarray for dict_name in medpc_name_to_dict_name.values()}
        session_dict = read_medpc_file(
            file_path=self.source_data["file_path"],
            medpc_name_to_dict_name=medpc_name_to_dict_name,
            dict_name_to_type=dict_name_to_type,
            session_conditions=self.source_data["session_conditions"],
            start_variable=self.source_data["start_variable"],
        )
        if "optogenetic_stimulation_times" in session_dict:  # stim times are recorded for scrambled trials
            session_dict["stim_times"] = session_dict.pop("optogenetic_stimulation_times")
        else:  # otherwise, stim is delivered on either left or right reward -- usually interleaved
            stim_times = []
            if len(session_dict["left_reward_times"]) > 0:
                stim_times.extend(session_dict.pop("left_reward_times"))
            if len(session_dict["right_reward_times"]) > 0:
                stim_times.extend(session_dict.pop("right_reward_times"))
            if not stim_times:
                raise ValueError("No stim times found in medpc file.")
            session_dict["stim_times"] = np.sort(stim_times)
        stim_times = session_dict["stim_times"]

        # Create optogenetic series and add to nwbfile
        opto_metadata = metadata["Optogenetics"]["experimental_group_to_metadata"][
            self.source_data["experimental_group"]
        ]
        device = nwbfile.create_device(  # TODO: Ask Lerner Lab for data sheet
            name="LED_and_pulse_generator",
            description="LED and pulse generator used for optogenetic stimulation.",
            manufacturer="Prizmatix",
        )
        ogen_site = nwbfile.create_ogen_site(
            name="OptogeneticStimulusSite",
            device=device,
            description=opto_metadata["ogen_site_description"],
            location=f"Injection location: {opto_metadata['injection_location']} \n Stimulation location: {opto_metadata['stimulation_location']}",
            excitation_lambda=opto_metadata["excitation_lambda"],
        )
        timestamps, data = self.create_stimulation_timeseries(
            stimulation_onset_times=stim_times,
            duration=opto_metadata["duration"],
            frequency=opto_metadata["frequency"],
            pulse_width=opto_metadata["pulse_width"],
            power=opto_metadata["power"],
        )
        ogen_series = OptogeneticSeries(
            name="OptogeneticSeries",
            site=ogen_site,
            data=H5DataIO(data, compression=True),
            timestamps=H5DataIO(timestamps, compression=True),
            description=opto_metadata["ogen_series_description"],
            comments=f"Optogenetic Treatment: {self.source_data['optogenetic_treatment']}",
        )
        nwbfile.add_stimulus(ogen_series)

    def create_stimulation_timeseries(  # TODO: Move to neuroconv
        self, stimulation_onset_times: np.ndarray, duration: float, frequency: float, pulse_width: float, power: float
    ) -> tuple[np.ndarray, np.ndarray]:
        """Create a continuous stimulation time series from stimulation onset times and parameters.

        In the resulting data array, the offset time of each pulse is represented by a 0 power value.

        Parameters
        ----------
        stimulation_onset_times : np.ndarray
            Array of stimulation onset times.
        duration : float
            Duration of stimulation in seconds.
        frequency : float
            Frequency of stimulation in Hz.
        pulse_width : float
            Pulse width of stimulation in seconds.
        power : float
            Power of stimulation in W.

        Returns
        -------
        np.ndarray
            Stimulation timestamps.
        np.ndarray
            Instantaneous stimulation power.

        Notes
        -----
        For continuous stimulation of a desired duration, simply set
        ```
        pulse_width = duration
        frequency = 1 / duration
        ```
        """
        num_pulses = int(duration * frequency)
        inter_pulse_interval = 1 / frequency
        timestamps, data = [0], [0]
        for onset_time in stimulation_onset_times:
            for i in range(num_pulses):
                pulse_onset_time = onset_time + i * inter_pulse_interval
                timestamps.append(pulse_onset_time)
                data.append(power)
                pulse_offset_time = pulse_onset_time + pulse_width
                timestamps.append(pulse_offset_time)
                data.append(0)
        return np.array(timestamps), np.array(data)
