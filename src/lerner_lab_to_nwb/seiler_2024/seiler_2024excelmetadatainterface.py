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

    def __init__(self, file_path: str, verbose: bool = True):
        """Initialize Seiler2024BehaviorInterface.

        Parameters
        ----------
        file_path : str
            Path to the excel metadata file.
        verbose : bool, optional
            Whether to print verbose output, by default True
        """
        super().__init__(
            file_path=file_path,
            verbose=verbose,
        )

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        return metadata_schema

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict) -> None:
        pass
