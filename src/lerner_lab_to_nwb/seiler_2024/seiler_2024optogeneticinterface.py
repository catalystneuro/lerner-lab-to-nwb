"""Primary class for converting experiment-specific optogenetic stimulation."""
import numpy as np
from pynwb.file import NWBFile
from pynwb.ogen import OptogeneticSeries
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from neuroconv.tools.optogenetics import create_optogenetic_stimulation_timeseries
from typing import Literal
from hdmf.backends.hdf5.h5_utils import H5DataIO
from datetime import datetime, time
from pathlib import Path
import pandas as pd

from neuroconv.datainterfaces.behavior.medpc.medpc_helpers import read_medpc_file


class Seiler2024OptogeneticInterface(BaseDataInterface):
    """Optogenetic interface for seiler_2024 conversion."""

    keywords = ["optogenetics"]

    def __init__(
        self,
        file_path: str,
        session_conditions: dict,
        start_variable: str,
        experimental_group: Literal["DMS-Inhibitory", "DMS-Excitatory", "DLS-Excitatory"],
        optogenetic_treatment: Literal["ChR2", "EYFP", "ChR2Scrambled", "NpHR", "NpHRScrambled", "Unknown"],
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
        from_csv = file_path.endswith(".csv")
        super().__init__(
            file_path=file_path,
            session_conditions=session_conditions,
            start_variable=start_variable,
            experimental_group=experimental_group,
            optogenetic_treatment=optogenetic_treatment,
            from_csv=from_csv,
            verbose=verbose,
        )

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()

        if self.source_data["optogenetic_treatment"] == "ChR2":
            metadata["NWBFile"]["stimulus_notes"] = "Excitatory stimulation on rewarded nosepokes"
        elif self.source_data["optogenetic_treatment"] == "NpHR":
            metadata["NWBFile"]["stimulus_notes"] = "Inhibitory stimulation on rewarded nosepokes"
        elif self.source_data["optogenetic_treatment"] == "ChR2Scrambled":
            metadata["NWBFile"]["stimulus_notes"] = "Excitatory stimulation on random nosepokes"
        elif self.source_data["optogenetic_treatment"] == "NpHRScrambled":
            metadata["NWBFile"]["stimulus_notes"] = "Inhibitory stimulation on random nosepokes"
        elif self.source_data["optogenetic_treatment"] == "EYFP":
            metadata["NWBFile"]["stimulus_notes"] = "Control"
        elif self.source_data["optogenetic_treatment"] == "Unknown":
            return metadata
        else:
            raise ValueError(
                f"Optogenetic treatment must be one of 'ChR2', 'EYFP', 'ChR2Scrambled', 'NpHR', 'NpHRScrambled', or 'Unknown' but got {self.source_data['optogenetic_treatment']}"
            )
        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # Read stim times from medpc file or csv
        if self.source_data["from_csv"]:
            csv_name_to_dict_name = {
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
            }
            session_df = pd.read_csv(self.source_data["file_path"], dtype=session_dtypes)
            session_dict = {}
            for csv_name, dict_name in csv_name_to_dict_name.items():
                session_dict[dict_name] = np.trim_zeros(session_df[csv_name].dropna().values, trim="b")
            if "Z" in session_df.columns:
                session_dict["optogenetic_stimulation_times"] = np.trim_zeros(session_df["Z"].dropna().values, trim="b")
        else:
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
            if not stim_times:  # sessions without reward/stim times are skipped with a warning
                if self.verbose:
                    print(f"No optogenetic stimulation times found for {metadata['NWBFile']['session_id']}")
                return
            session_dict["stim_times"] = np.sort(stim_times)
        stim_times = session_dict["stim_times"]

        # Create optogenetic series and add to nwbfile
        opto_metadata = metadata["Optogenetics"]["experimental_group_to_metadata"][
            self.source_data["experimental_group"]
        ]
        device = nwbfile.create_device(
            name="Optogenetics_LED_Dual",
            description=(
                "Optogenetic stimulus pulses were generated from the Optogenetics-LED-Dual (Prizmatix) driven by the "
                "Optogenetics PulserPlus (Prizmatix). Engineered for scaling Optogenetics experiments, the "
                "Optogenetics-LED-Dual light source features two independent fiber-coupled LED channels each equipped "
                "with independent power and switching control. Optogenetics Pulser / PulserPlus are programmable "
                "TTL pulse train generators for pulsing LEDs, lasers and shutters used in Optogenetics activation "
                "in neurophysiology and behavioral research."
            ),
            manufacturer="Prizmatix",
        )
        ogen_site = nwbfile.create_ogen_site(
            name="OptogeneticStimulusSite",
            device=device,
            description=opto_metadata["ogen_site_description"],
            location=f"Injection location: {opto_metadata['injection_location']} \n Stimulation location: {opto_metadata['stimulation_location']}",
            excitation_lambda=opto_metadata["excitation_lambda"],
        )
        timestamps, data = create_optogenetic_stimulation_timeseries(
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
        )
        nwbfile.add_stimulus(ogen_series)
