"""Primary NWBConverter class for this dataset."""
from pathlib import Path

import numpy as np
from neuroconv.converters import WaveSurferIntracellularConverter
from neuroconv.utils import load_dict_from_file
from pynwb import NWBFile

from .external_resources import add_external_resources


class Nadel2026NWBConverter(WaveSurferIntracellularConverter):
    """Combine the WaveSurfer runs of one recording day into one NWB file, with the lab's log sheet columns.

    Each data interface is one run of one protocol on one cell. The WaveSurfer converter places the runs on one
    timeline by their start times and builds the icephys tables; this converter adds the columns from the lab's log
    sheets and cell tables, the digitizer, and the external resources.
    """

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict, conversion_options: dict | None = None):
        super().add_to_nwbfile(nwbfile=nwbfile, metadata=metadata, conversion_options=conversion_options)
        nwbfile.create_device(**metadata["Devices"]["digitizer"])

        # Each sequential recording is one run, built in the order its `sequence` label (the file stem) first
        # appears in the intracellular recordings table.
        file_names = {
            Path(interface.source_data["file_path"]).stem: Path(interface.source_data["file_path"]).name
            for interface in self.data_interface_objects.values()
        }
        intracellular_recordings = nwbfile.get_intracellular_recordings()
        run_labels = list(dict.fromkeys(intracellular_recordings["sequence"].data))
        run_file_names = [file_names[run_label] for run_label in run_labels]
        sequential_recordings = nwbfile.get_icephys_sequential_recordings()
        sequential_recordings.add_column(
            name="source_file",
            description="WaveSurfer file that holds the run.",
            data=run_file_names,
        )
        access_resistances = metadata["Icephys"]["TestPulseAccessResistances"]
        sequential_recordings.add_column(
            name="access_resistance",
            description=(
                "Access resistance in MOhm noted in the lab log sheet after this VC test pulse run; NaN for other "
                "runs and where none was noted."
            ),
            data=[access_resistances.get(file_name, np.nan) for file_name in run_file_names],
        )
        held_runs = set(metadata["Icephys"]["HeldRuns"])
        sequential_recordings.add_column(
            name="held_near_minus_60_mV",
            description=(
                "Whether the cell was held near -60 mV with DC current during this current clamp run, as noted in the "
                "lab log sheet. The logged holding current, where there is one, is the bias_current of the run's "
                "response series."
            ),
            data=[file_name in held_runs for file_name in run_file_names],
        )

        cells_metadata = metadata["Icephys"]["Cells"]
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
