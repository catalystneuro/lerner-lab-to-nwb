"""Primary script to run to convert example sessions using the NWBConverter."""
import re
from pathlib import Path
from typing import Literal, Union
from zoneinfo import ZoneInfo

import pandas as pd
from neuroconv.utils import dict_deep_update, load_dict_from_file

from lerner_lab_to_nwb.nadel_2026 import Nadel2026NWBConverter, WaveSurferIntracellularInterface

SESSION_TIMEZONE = ZoneInfo("America/Chicago")
VOLTAGE_CLAMP_HOLDING_POTENTIAL = -70.0  # mV, set on the amplifier for every voltage clamp run
CELL_COLUMNS = {
    "cell_folder": "Name of the cell's folder in the lab's raw data, which carries bead status and MZ's cell number.",
    "experimenter": "Initials of the person who recorded the cell (JN, MZ, or ES).",
    "retrobead_positive": "Whether the cell contained retrobeads, from the cell folder name ('+' or '-'); "
    "'unknown' where the folder name does not say.",
    "in_paper": "Whether the cell is in the 160 cells analyzed in the preprint (metadata/used cells.csv).",
    "snl_cluster": "Electrophysiological cluster of the CeA-SNL cell in the preprint's clustering (1 regular "
    "spiking, 2 low-threshold bursting, 3 late firing); 0 for cells that were not clustered.",
}


def session_to_nwb(
    *,
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    tree: Literal["raw_data_organized", "timecourse_raw_data_organized"],
    mouse_folder: str,
    stub_test: bool = False,
    overwrite: bool = False,
):
    """Convert one recording day (one mouse) to NWB.

    Parameters
    ----------
    data_dir_path : Union[str, Path]
        Path to the aCUS_ephys_raw_for_NWB folder.
    output_dir_path : Union[str, Path]
        Path to the directory to save the NWB file.
    tree : Literal["raw_data_organized", "timecourse_raw_data_organized"]
        The data tree that holds the recording day.
    mouse_folder : str
        Name of the recording day folder, for example '20250213 756-0'.
    stub_test : bool, optional
        Whether to convert only the first cell of the day, by default False
    overwrite : bool, optional
        Whether to overwrite an existing NWB file, by default False
    """
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    cells = pd.read_csv(data_dir_path / "tables" / "cells_master.csv")
    cells = cells[(cells.tree == ("main" if tree == "raw_data_organized" else "timecourse"))]
    cells = cells[cells.mouse_folder == mouse_folder]
    if stub_test:
        cells = cells.iloc[:1]
    excluded_runs = pd.read_csv(Path(__file__).parent / "nadel_2026_excluded_runs.csv")
    excluded_runs = excluded_runs[(excluded_runs.tree == tree) & (excluded_runs.mouse_folder == mouse_folder)]
    misfiled_runs = pd.read_csv(Path(__file__).parent / "nadel_2026_misfiled_runs.csv")
    misfiled_runs = misfiled_runs[(misfiled_runs.tree == tree) & (misfiled_runs.mouse_folder == mouse_folder)]
    excluded_paths = {
        data_dir_path / tree / mouse_folder / cell_folder / filename
        for cell_folder, filename in zip(
            pd.concat([excluded_runs.cell_folder, misfiled_runs.found_in_cell_folder]),
            pd.concat([excluded_runs.filename, misfiled_runs.filename]),
        )
    }

    editable_metadata = load_dict_from_file(Path(__file__).parent / "nadel_2026_metadata.yaml")
    interfaces = {}
    electrodes_metadata = {}
    cells_metadata = {}
    for cell in cells.itertuples():
        electrode_name = f"electrode_{cell.cell_id.replace(' ', '_')}"
        experimenter = get_experimenter_initials(cell.cell_folder)
        cell_misfiled_runs = misfiled_runs[misfiled_runs.cell_folder == cell.cell_folder]
        file_paths = [
            file_path
            for file_path in (data_dir_path / tree / mouse_folder / cell.cell_folder).glob("*.h5")
            if file_path not in excluded_paths
        ] + [
            data_dir_path / tree / mouse_folder / found_in_cell_folder / filename
            for found_in_cell_folder, filename in zip(
                cell_misfiled_runs.found_in_cell_folder, cell_misfiled_runs.filename
            )
        ]
        for file_path in sorted(file_paths):
            interfaces[f"{cell.cell_folder}/{file_path.stem}"] = WaveSurferIntracellularInterface(
                file_path=file_path,
                electrode_name=electrode_name,
                voltage_clamp_holding_potential=VOLTAGE_CLAMP_HOLDING_POTENTIAL,
            )
        slice_number = re.fullmatch(r"m\d+ s(\d+)c\d+(ES)?", cell.cell_id).group(1)
        electrodes_metadata[electrode_name] = dict(
            device_name="MultiClamp700B",
            description=editable_metadata["Icephys"]["IntracellularElectrode"]["description"],
            location=editable_metadata["Icephys"]["IntracellularElectrode"]["location"],
            cell_id=cell.cell_id,
            slice=f"Slice {slice_number} of the recording day",
        )
        cells_metadata[electrode_name] = dict(
            cell_folder=cell.cell_folder,
            experimenter=experimenter,
            retrobead_positive={"+": "yes", "-": "no"}.get(cell.bead, "unknown"),
            in_paper=bool(cell.in_used_cells),
            snl_cluster=0 if pd.isna(cell.snl_cluster) else int(cell.snl_cluster),
        )

    converter = Nadel2026NWBConverter(data_interfaces=interfaces)
    metadata = converter.get_metadata()
    metadata["NWBFile"]["session_start_time"] = metadata["NWBFile"]["session_start_time"].replace(
        tzinfo=SESSION_TIMEZONE
    )

    date, animal_id = mouse_folder.split(" ")
    subjects = pd.read_csv(data_dir_path / "tables" / "subjects_from_makeMice.csv", dtype=str)
    subject = subjects[subjects.animal_id == animal_id].iloc[0]
    target = subject.projection_target
    stress_description = editable_metadata["stress_group_to_description"][subject.stress]
    session_metadata = dict(
        NWBFile=dict(
            session_id=mouse_folder.replace(" ", "_"),
            session_description=(
                f"Whole-cell recordings from central amygdala (CeA) neurons in acute coronal slices from mouse "
                f"{animal_id} ({subject.stress}; retrobeads in the {target}). Each cell was characterized with a "
                f"voltage clamp test pulse, a 30 s spontaneous recording at rest, current steps for the F-I curve "
                f"(500 ms, 0 to 200 pA), hyperpolarizing steps for sag (500 ms, 0 to -150 pA), short steps for "
                f"rheobase (50 ms, 5 pA increments), and a voltage clamp Ih protocol, most run three times."
            ),
            experimenter=sorted(
                {
                    editable_metadata["experimenter_initials_to_name"][cell_metadata["experimenter"]]
                    for cell_metadata in cells_metadata.values()
                }
            ),
            surgery=editable_metadata["projection_target_to_surgery"][target],
        ),
        Subject=dict(
            subject_id=animal_id,
            sex={"female": "F", "male": "M"}[subject.sex],
            description=f"{stress_description} Retrobeads injected into the {target}.",
        ),
        Icephys=dict(IntracellularElectrodes=electrodes_metadata, Cells=cells_metadata, CellColumns=CELL_COLUMNS),
    )
    if not pd.isna(subject.age_days):
        session_metadata["Subject"]["age"] = f"P{subject.age_days}D"
    metadata = dict_deep_update(metadata, editable_metadata)
    metadata = dict_deep_update(metadata, session_metadata)
    for lookup_name in ("stress_group_to_description", "experimenter_initials_to_name", "projection_target_to_surgery"):
        metadata.pop(lookup_name)
    metadata["Icephys"].pop("IntracellularElectrode")

    nwbfile_path = output_dir_path / f"sub-{animal_id}_ses-{date}.nwb"
    converter.run_conversion(nwbfile_path=nwbfile_path, metadata=metadata, overwrite=overwrite)


def get_experimenter_initials(cell_folder: str) -> str:
    """Return the initials of the person who recorded a cell, from the naming of its folder."""
    if "(mz_" in cell_folder:
        return "MZ"
    if cell_folder.endswith("ES"):
        return "ES"
    return "JN"


if __name__ == "__main__":
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/Lerner/aCUS_ephys_raw_for_NWB")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Lerner/conversion_nwb")
    stub_test = False

    example_sessions = [
        ("raw_data_organized", "20250213 756-0"),  # TS, 2025, recorded command matches the library stimulus
        ("raw_data_organized", "20230913 607-009"),  # Sept 2023, MZ cells and runs held at -60 mV
        ("timecourse_raw_data_organized", "20251016 855-L"),  # ES cells and the 20 kHz gap-free recording
    ]
    for tree, mouse_folder in example_sessions:
        session_to_nwb(
            data_dir_path=data_dir_path,
            output_dir_path=output_dir_path,
            tree=tree,
            mouse_folder=mouse_folder,
            stub_test=stub_test,
            overwrite=True,
        )
