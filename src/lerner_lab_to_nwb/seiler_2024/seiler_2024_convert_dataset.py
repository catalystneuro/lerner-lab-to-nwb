"""Convert the entire dataset to NWB."""
from pathlib import Path
from typing import Union
from tqdm import tqdm
from datetime import datetime
import shutil
import pandas as pd
import numpy as np

from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_session import session_to_nwb
from lerner_lab_to_nwb.seiler_2024.medpc import get_medpc_variables
from lerner_lab_to_nwb.seiler_2024.medpc import read_medpc_file


def dataset_to_nwb(
    data_dir_path: Union[str, Path], output_dir_path: Union[str, Path], stub_test: bool = False, verbose: bool = True
):
    """Convert the entire dataset to NWB."""
    # Setup
    start_variable = "Start Date"
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    experiment_type = "FP"
    experimental_groups = ["DPR", "PR", "PS", "RR20"]
    behavior_path = data_dir_path / f"{experiment_type} Experiments" / "Behavior"
    raw_file_to_info = get_raw_info(behavior_path)

    # Iterate through file system to get necessary information for converting each session
    session_to_nwb_args_per_session: list[dict] = []  # Each dict contains the args for session_to_nwb for a session
    for experimental_group in experimental_groups:
        experimental_group_path = behavior_path / experimental_group
        subject_dirs = [subject_dir for subject_dir in experimental_group_path.iterdir() if subject_dir.is_dir()]
        for subject_dir in subject_dirs:
            subject_id = subject_dir.name
            header_variables = get_header_variables(subject_dir, subject_id, raw_file_to_info, start_variable)
            start_dates, start_times, msns, file_paths, subjects, box_numbers = header_variables
            for start_date, start_time, msn, file, subject, box_number in zip(
                start_dates, start_times, msns, file_paths, subjects, box_numbers
            ):
                if (
                    (
                        start_date == "09/20/19"
                        and start_time == "09:42:54"
                        and subject_id == "139.298"
                        and msn == "RI 60 RIGHT STIM"
                    )
                    or (
                        start_date == "07/28/20"
                        and start_time == "13:21:15"
                        and subject_id == "272.396"
                        and msn == "Probe Test Habit Training TTL"
                    )
                    or (
                        start_date == "07/31/20"
                        and start_time == "12:03:31"
                        and subject_id == "346.394"
                        and msn == "FOOD_RI 60 RIGHT TTL"
                    )
                ):
                    continue  # these sessions are the wrong subject TODO: Ask Lerner Lab about this
                session_conditions = {
                    "Start Date": start_date,
                    "Start Time": start_time,
                }
                if subject is not None:
                    session_conditions["Subject"] = subject
                if box_number is not None:
                    session_conditions["Box"] = box_number
                start_datetime = datetime.strptime(f"{start_date} {start_time}", "%m/%d/%y %H:%M:%S")
                session_to_nwb_args = dict(
                    data_dir_path=data_dir_path,
                    output_dir_path=output_dir_path,
                    behavior_file_path=file,
                    subject_id=subject_id,
                    session_conditions=session_conditions,
                    start_variable=start_variable,
                    start_datetime=start_datetime,
                    experiment_type=experiment_type,
                    experimental_group=experimental_group,
                    stub_test=stub_test,
                    verbose=verbose,
                )
                session_to_nwb_args_per_session.append(session_to_nwb_args)

    # Convert all sessions and handle missing MSNs
    missing_msn_errors = set()
    for session_to_nwb_args in tqdm(session_to_nwb_args_per_session):
        try:
            session_to_nwb(**session_to_nwb_args)
        except KeyError as e:
            missing_msn_errors.add(str(e))
            continue
        except Exception as e:
            print(
                f"Could not convert {session_to_nwb_args['experimental_group']}/{session_to_nwb_args['subject_id']}/{session_to_nwb_args['session_conditions']['Start Date']} {session_to_nwb_args['session_conditions']['Start Time']}"
            )
            raise Exception(e)
    if missing_msn_errors:
        print("Missing MSN errors:")
        for error in missing_msn_errors:
            print(error)


def get_csv_session_dates(subject_dir):
    csv_session_dates = []
    for file in subject_dir.iterdir():
        if file.suffix == ".csv" and not file.name.startswith(".") and not "dataForEachAnimal" in file.name:
            date = file.stem.split("_")[1].replace("-", "/")
            csv_session_dates.append(date)
    return csv_session_dates


def get_header_variables(subject_dir, subject_id, raw_file_to_info, start_variable):
    medpc_file_path = subject_dir / f"{subject_id}"
    if medpc_file_path.exists():  # Medpc file with all the sessions for the subject is located in the subject directory
        medpc_variables = get_medpc_variables(
            file_path=medpc_file_path, variable_names=["Start Date", "Start Time", "MSN"]
        )
        start_dates = medpc_variables["Start Date"]
        start_times = medpc_variables["Start Time"]
        msns = medpc_variables["MSN"]
        file_paths = [medpc_file_path] * len(start_dates)
        subjects = [None] * len(start_dates)
        box_numbers = [None] * len(start_dates)
    else:  # We need to grab all the subject's sessions from the Medpc files organized by date (rather than by subject)
        start_dates, start_times, msns, file_paths, subjects = [], [], [], [], []
        for file, info in raw_file_to_info.items():
            for subject, start_date, start_time, msn in zip(
                info["Subject"], info["Start Date"], info["Start Time"], info["MSN"]
            ):
                if subject == subject_id:
                    start_dates.append(start_date)
                    start_times.append(start_time)
                    msns.append(msn)
                    file_paths.append(file)
                    subjects.append(subject_id)
        box_numbers = [None] * len(start_dates)

    # Some subjects have sessions in the Medpc files organized by date without identifying subject info
    # We can identify these sessions by matching them to the CSV files in the subject directory
    csv_session_dates = get_csv_session_dates(subject_dir)
    for csv_date in csv_session_dates:
        if csv_date not in start_dates:
            session_df = pd.read_csv(subject_dir / f"{subject_id}_{csv_date.replace('/', '-')}.csv")
            port_entry_times = np.trim_zeros(session_df["portEntryTs"].dropna().values, trim="b")
            for file, info in raw_file_to_info.items():
                for start_date, start_time, msn, box_number in zip(
                    info["Start Date"], info["Start Time"], info["MSN"], info["Box"]
                ):
                    if start_date == csv_date:
                        medpc_name_to_dict_name = {"G": "port_entry_times"}
                        dict_name_to_type = {
                            "port_entry_times": np.ndarray,
                        }
                        session_conditions = {
                            "Start Date": start_date,
                            "Start Time": start_time,
                            "Box": box_number,
                        }
                        session_dict = read_medpc_file(
                            file_path=file,
                            medpc_name_to_dict_name=medpc_name_to_dict_name,
                            dict_name_to_type=dict_name_to_type,
                            session_conditions=session_conditions,
                            start_variable=start_variable,
                        )
                        if np.array_equal(port_entry_times, session_dict["port_entry_times"]):
                            start_dates.append(start_date)
                            start_times.append(start_time)
                            msns.append(msn)
                            file_paths.append(file)
                            subjects.append(None)
                            box_numbers.append(box_number)
    return start_dates, start_times, msns, file_paths, subjects, box_numbers


def get_raw_info(behavior_path):
    raw_files_by_date_path = behavior_path / "MEDPC_RawFilesbyDate"
    raw_files_by_date = [file for file in raw_files_by_date_path.iterdir() if not file.name.startswith(".")]
    raw_file_to_info = {}
    for file in raw_files_by_date:
        info = get_medpc_variables(file_path=file, variable_names=["Subject", "Start Date", "Start Time", "MSN", "Box"])
        raw_file_to_info[file] = info
    return raw_file_to_info


if __name__ == "__main__":
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/raw_data")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/conversion_nwb")
    if output_dir_path.exists():
        shutil.rmtree(
            output_dir_path, ignore_errors=True
        )  # ignore errors due to MacOS race condition (https://github.com/python/cpython/issues/81441)
    dataset_to_nwb(data_dir_path=data_dir_path, output_dir_path=output_dir_path, stub_test=False, verbose=False)
