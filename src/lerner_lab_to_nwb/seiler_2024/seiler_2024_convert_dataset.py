"""Convert the entire dataset to NWB."""
from pathlib import Path
from typing import Union
from tqdm import tqdm

from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_session import session_to_nwb
from lerner_lab_to_nwb.seiler_2024.medpc import get_start_dates, get_MSNs


def dataset_to_nwb(data_dir_path: Union[str, Path], output_dir_path: Union[str, Path], stub_test: bool = False):
    """Convert the entire dataset to NWB."""
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    experiment_type = "FP"
    experimental_groups = ["DPR", "PR", "PS", "RR20"]
    behavior_path = data_dir_path / f"{experiment_type} Experiments" / "Behavior"
    for experimental_group in experimental_groups:
        print(f"Converting Experimental Group: {experimental_group}")
        experimental_group_path = behavior_path / experimental_group
        subject_dirs = [subject_dir for subject_dir in experimental_group_path.iterdir() if subject_dir.is_dir()]
        for subject_dir in tqdm(subject_dirs):
            subject_id = subject_dir.name
            print(f"Converting Subject: {subject_id}")
            medpc_file_path = subject_dir / f"{subject_id}"
            try:
                start_dates = get_start_dates(medpc_file_path)
                msns = get_MSNs(medpc_file_path)
            except FileNotFoundError:  # TODO: Find the missing medpc files
                print(f"Could not find MedPC file for subject {subject_id}")
                continue
            for start_date, msn in zip(start_dates, msns):
                if msn == "FOOD_Magazine Training 1 hr":
                    continue  # magazine training does not yield useful data
                start_date = start_date.replace("/", "_")
                print(f"Converting Session: {start_date}")
                session_to_nwb(
                    data_dir_path=data_dir_path,
                    output_dir_path=output_dir_path,
                    start_date=start_date,
                    subject_id=subject_id,
                    experiment_type=experiment_type,
                    experimental_group=experimental_group,
                    stub_test=stub_test,
                )


if __name__ == "__main__":
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/raw_data")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/conversion_nwb")
    dataset_to_nwb(data_dir_path=data_dir_path, output_dir_path=output_dir_path, stub_test=False)
