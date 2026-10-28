"""Primary script to run to convert all sessions in a dataset using session_to_nwb."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Union

import pandas as pd
from tqdm import tqdm

from lerner_lab_to_nwb.nadel_2026.nadel_2026_convert_session import session_to_nwb


def dataset_to_nwb(
    *,
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    max_workers: int = 1,
    overwrite: bool = False,
):
    """Convert every recording day in both data trees to NWB, one file per day.

    Parameters
    ----------
    data_dir_path : Union[str, Path]
        Path to the aCUS_ephys_raw_for_NWB folder.
    output_dir_path : Union[str, Path]
        Path to the directory to save the NWB files.
    max_workers : int, optional
        Number of sessions to convert in parallel, by default 1
    overwrite : bool, optional
        Whether to overwrite existing NWB files, by default False
    """
    data_dir_path = Path(data_dir_path)
    cells = pd.read_csv(data_dir_path / "tables" / "cells_master.csv")
    tree_names = {"main": "raw_data_organized", "timecourse": "timecourse_raw_data_organized"}
    sessions = cells[["tree", "mouse_folder"]].drop_duplicates()
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                session_to_nwb,
                data_dir_path=data_dir_path,
                output_dir_path=output_dir_path,
                tree=tree_names[tree],
                mouse_folder=mouse_folder,
                overwrite=overwrite,
            )
            for tree, mouse_folder in zip(sessions.tree, sessions.mouse_folder)
        ]
        for future in tqdm(as_completed(futures), total=len(futures)):
            future.result()


if __name__ == "__main__":
    dataset_to_nwb(
        data_dir_path=Path("/Volumes/T7/CatalystNeuro/Lerner/aCUS_ephys_raw_for_NWB"),
        output_dir_path=Path("/Volumes/T7/CatalystNeuro/Lerner/conversion_nwb"),
        max_workers=4,
        overwrite=True,
    )
