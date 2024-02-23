"""Convert the entire dataset to NWB."""
from pathlib import Path
from typing import Union
from tqdm import tqdm
from datetime import datetime
import shutil

from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_session import session_to_nwb
from lerner_lab_to_nwb.seiler_2024.medpc import get_medpc_variables


def dataset_to_nwb(
    data_dir_path: Union[str, Path], output_dir_path: Union[str, Path], stub_test: bool = False, verbose: bool = True
):
    """Convert the entire dataset to NWB."""
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    experiment_type = "FP"
    experimental_groups = ["DPR", "PR", "PS", "RR20"]
    behavior_path = data_dir_path / f"{experiment_type} Experiments" / "Behavior"
    missing_msn_errors = []
    for experimental_group in experimental_groups:
        experimental_group_path = behavior_path / experimental_group
        subject_dirs = [subject_dir for subject_dir in experimental_group_path.iterdir() if subject_dir.is_dir()]
        for subject_dir in tqdm(subject_dirs):
            subject_id = subject_dir.name
            medpc_file_path = subject_dir / f"{subject_id}"
            try:
                medpc_variables = get_medpc_variables(
                    file_path=medpc_file_path, variable_names=["Start Date", "Start Time", "MSN"]
                )
                start_dates = medpc_variables["Start Date"]
                start_times = medpc_variables["Start Time"]
                msns = medpc_variables["MSN"]
            except FileNotFoundError:  # TODO: Find the missing medpc files
                print(f"Could not find MedPC file for subject {subject_id}")
                continue
            for start_date, start_time, msn in zip(start_dates, start_times, msns):
                if msn in {
                    "FOOD_Magazine Training 1 hr",
                    "Magazine Training 1 hr",
                    "Probe Test Habit Training TTL",
                }:  # TODO: Find the missing msn files
                    continue  # magazine training does not yield useful data
                start_datetime = datetime.strptime(f"{start_date} {start_time}", "%m/%d/%y %H:%M:%S")
                if (
                    start_datetime == datetime(2019, 9, 20, 9, 42, 54)
                    and subject_id == "139.298"
                    and msn == "RI 60 RIGHT STIM"
                ):
                    continue  # this session is the wrong subject TODO: Ask Lerner Lab about this
                try:
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
                except KeyError as e:
                    missing_msn_errors.append(e)
                    continue
                except Exception as e:
                    print(f"Could not convert {experimental_group}/{subject_id}/{start_datetime.isoformat()}")
                    raise Exception(e)
    if missing_msn_errors:
        print("Missing MSN errors:")
        for error in missing_msn_errors:
            print(error)


if __name__ == "__main__":
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/raw_data")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/conversion_nwb")
    if output_dir_path.exists():
        shutil.rmtree(
            output_dir_path, ignore_errors=True
        )  # ignore errors due to MacOS race condition (https://github.com/python/cpython/issues/81441)
    dataset_to_nwb(data_dir_path=data_dir_path, output_dir_path=output_dir_path, stub_test=False, verbose=False)
