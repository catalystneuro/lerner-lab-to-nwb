"""Primary NWBConverter class for this dataset."""
from pathlib import Path

import numpy as np
from neuroconv import ConverterPipe
from neuroconv.utils import DeepDict, load_dict_from_file
from pynwb import NWBFile
from pynwb.base import TimeSeriesReferenceVectorData

from .external_resources import add_external_resources


class Nadel2026NWBConverter(ConverterPipe):
    """Combine the WaveSurfer runs of one recording day into one NWB file.

    Each data interface is one run of one protocol on one cell. Runs are placed on one timeline by their start times,
    and the runs of a cell that repeat a protocol are grouped into one icephys repetition.
    """

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        metadata["NWBFile"]["session_start_time"] = min(
            interface.run_start_time for interface in self.data_interface_objects.values()
        )
        return metadata

    def temporally_align_data_interfaces(self, metadata: dict, conversion_options: dict | None = None):
        session_start_time = metadata["NWBFile"]["session_start_time"].replace(tzinfo=None)
        for interface in self.data_interface_objects.values():
            interface.set_aligned_starting_time((interface.run_start_time - session_start_time).total_seconds())

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict, conversion_options: dict | None = None):
        interfaces = sorted(self.data_interface_objects.values(), key=lambda interface: interface.run_start_time)
        # The optional stimulus_template column can only be added while the table is empty, and the first run of a day
        # may have no template (an I=0 recording).
        nwbfile.get_intracellular_recordings().category_tables["stimuli"].add_column(
            name="stimulus_template",
            description="Command built from the WaveSurfer stimulus library for the recording (rows).",
            col_cls=TimeSeriesReferenceVectorData,
        )
        for interface in interfaces:
            interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

        sequential_recordings = nwbfile.get_icephys_sequential_recordings()
        sequential_recordings.add_column(
            name="source_file",
            description="WaveSurfer file that holds the run.",
            data=[interface.source_data["file_path"].name for interface in interfaces],
        )
        access_resistances = metadata["Icephys"]["TestPulseAccessResistances"]
        sequential_recordings.add_column(
            name="access_resistance",
            description=(
                "Access resistance in MOhm noted in the lab log sheet after this VC test pulse run; NaN for other "
                "runs and where none was noted."
            ),
            data=[access_resistances.get(interface.source_data["file_path"].name, np.nan) for interface in interfaces],
        )
        sequential_recording_indices = {}
        for interface in interfaces:
            key = (interface.source_data["electrode_name"], interface.protocol_name)
            sequential_recording_indices.setdefault(key, []).append(interface.sequential_recording_index)
        for indices in sequential_recording_indices.values():
            nwbfile.add_icephys_repetition(sequential_recordings=indices)

        cells_metadata = metadata["Icephys"]["Cells"]
        intracellular_recordings = nwbfile.get_intracellular_recordings()
        electrodes = intracellular_recordings.category_tables["electrodes"]["electrode"].data
        electrode_names = [electrode.name for electrode in electrodes]
        for column_name, column_description in metadata["Icephys"]["CellColumns"].items():
            intracellular_recordings.add_column(
                name=column_name,
                description=column_description,
                data=[cells_metadata[electrode_name][column_name] for electrode_name in electrode_names],
                category="electrodes",
            )

        terms = load_dict_from_file(Path(__file__).parent / "nadel_2026_external_resources.yaml")
        add_external_resources(nwbfile=nwbfile, terms=terms)
