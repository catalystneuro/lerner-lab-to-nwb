"""Convert the entire dataset to NWB."""
from pathlib import Path
from typing import Union
from tqdm import tqdm
from datetime import datetime
import shutil

from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_session import session_to_nwb
from lerner_lab_to_nwb.seiler_2024.medpc import get_start_dates, get_start_times, get_MSNs


def dataset_to_nwb(
    data_dir_path: Union[str, Path], output_dir_path: Union[str, Path], stub_test: bool = False, verbose: bool = True
):
    """Convert the entire dataset to NWB."""
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    experiment_type = "FP"
    experimental_groups = ["DPR", "PR", "PS", "RR20"]
    behavior_path = data_dir_path / f"{experiment_type} Experiments" / "Behavior"
    for experimental_group in experimental_groups:
        experimental_group_path = behavior_path / experimental_group
        subject_dirs = [subject_dir for subject_dir in experimental_group_path.iterdir() if subject_dir.is_dir()]
        for subject_dir in tqdm(subject_dirs):
            subject_id = subject_dir.name
            medpc_file_path = subject_dir / f"{subject_id}"
            try:
                start_dates = get_start_dates(medpc_file_path)
                start_times = get_start_times(medpc_file_path)
                msns = get_MSNs(medpc_file_path)
            except FileNotFoundError:  # TODO: Find the missing medpc files
                print(f"Could not find MedPC file for subject {subject_id}")
                continue
            for start_date, start_time, msn in zip(start_dates, start_times, msns):
                if msn in {
                    "FOOD_Magazine Training 1 hr",
                    "Probe Test Habit Training TTL",
                }:  # TODO: Find the missing msn files
                    continue  # magazine training does not yield useful data
                start_datetime = datetime.strptime(f"{start_date} {start_time}", "%m/%d/%y %H:%M:%S")
                session_to_nwb(
                    data_dir_path=data_dir_path,
                    output_dir_path=output_dir_path,
                    start_datetime=start_datetime,
                    subject_id=subject_id,
                    experiment_type=experiment_type,
                    experimental_group=experimental_group,
                    stub_test=stub_test,
                    verbose=verbose,
                )


if __name__ == "__main__":
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/raw_data")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/conversion_nwb")
    if output_dir_path.exists():
        shutil.rmtree(
            output_dir_path, ignore_errors=True
        )  # ignore errors due to MacOS race condition (https://github.com/python/cpython/issues/81441)
    dataset_to_nwb(data_dir_path=data_dir_path, output_dir_path=output_dir_path, stub_test=False, verbose=False)
