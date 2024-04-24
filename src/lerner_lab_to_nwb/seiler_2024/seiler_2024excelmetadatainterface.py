"""Primary class for converting excel-based metadata."""
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


class Seiler2024ExcelMetadataInterface(BaseDataInterface):
    """Excel Metadata interface for seiler_2024 conversion"""

    def __init__(self, file_path: str, subject_id: str, verbose: bool = True):
        """Initialize Seiler2024ExcelMetadataInterface.

        Parameters
        ----------
        file_path : str
            Path to the excel metadata file.
        subject_id : str
            Subject ID.
        verbose : bool, optional
            Whether to print verbose output, by default True
        """
        super().__init__(
            file_path=file_path,
            subject_id=subject_id,
            verbose=verbose,
        )

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()

        # Read metadata from excel file
        metadata_path = Path(self.source_data["file_path"])
        df = pd.read_excel(
            metadata_path,
            sheet_name="Mouse Demographics",
            dtype={"Mouse ID": str},
        )
        df.set_index("Mouse ID", inplace=True)
        try:
            subject_df = df.loc[self.source_data["subject_id"]]

            # Add metadata to metadata dict
            excel_sex_to_nwb_sex = {"Male": "M", "Female": "F"}
            metadata["Subject"]["sex"] = excel_sex_to_nwb_sex[subject_df["Sex"]]
            metadata["NWBFile"]["surgery"] = subject_df["Surgical Manipulation"]
            if not pd.isna(subject_df["Treatment"]):
                metadata["NWBFile"]["stimulus_notes"] = subject_df["Treatment"]
            if subject_df["Experiment"] == "Fiber Photometry":
                metadata["NWBFile"]["virus"] = "AAV5-CAG-FLEX-jGCaMP7b-WPRE"
            elif subject_df["Experiment"] == "DLS-Excitatory" or subject_df["Experiment"] == "DMS-Excitatory":
                metadata["NWBFile"]["virus"] = "AAV5-EF1a-DIO-hChR2(H134R)-EYFP"
            elif subject_df["Experiment"] == "DMS-Inhibitory" or subject_df["Experiment"] == "DMS-Inhibitory Group 2":
                metadata["NWBFile"]["virus"] = "AAV5-EF1a-DIO-eNpHR3.0-EYFP"
            if subject_df["Treatment"] == "Control":
                metadata["NWBFile"]["virus"] = "AAV5-EF1a-DIO-EYFP"
            metadata["NWBFile"]["notes"] = (
                f'Hemisphere with DMS: {subject_df["Hemisphere with DMS"]}\n'
                f'Experiment: {subject_df["Experiment"]}\n'
                f'Behavior: {subject_df["Behavior"]}\n'
                f'Punishment Group: {str(subject_df["Punishment Group"]).replace("Resitant", "Resistant")}\n'
            )
        except KeyError:  # TODO: Ask Lerner lab about missing subjects
            print(f"Subject ID {self.source_data['subject_id']} not found in metadata file.")
            metadata["Subject"]["sex"] = "U"

        metadata["Subject"]["subject_id"] = self.source_data["subject_id"]

        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict) -> None:
        pass
