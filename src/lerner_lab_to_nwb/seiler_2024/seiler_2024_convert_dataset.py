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
    start_variable = "Start Date"
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    # session_to_nwb_args_per_session = fp_to_nwb(
    #     data_dir_path=data_dir_path,
    #     output_dir_path=output_dir_path,
    #     start_variable=start_variable,
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )

    session_to_nwb_args_per_session = opto_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        start_variable=start_variable,
        stub_test=stub_test,
        verbose=verbose,
    )

    # Convert all sessions and handle missing Fi1d's
    missing_fi1d_sessions = []
    missing_msn_errors = set()
    for session_to_nwb_args in tqdm(session_to_nwb_args_per_session):
        try:
            session_to_nwb(**session_to_nwb_args)
        except AttributeError as e:
            if str(e) == "'StructType' object has no attribute 'Fi1d'":
                missing_fi1d_sessions.append(
                    str(session_to_nwb_args["fiber_photometry_folder_path"]).split("Photometry/")[1]
                )
                continue
            else:
                print(
                    f"Could not convert {session_to_nwb_args['experimental_group']}/{session_to_nwb_args['subject_id']}/{session_to_nwb_args['session_conditions']['Start Date']} {session_to_nwb_args['session_conditions']['Start Time']}"
                )
                raise AttributeError(e)
        except KeyError as e:
            missing_msn_errors.add(str(e))
        except Exception as e:
            print(
                f"Could not convert {session_to_nwb_args['experimental_group']}/{session_to_nwb_args['subject_id']}/{session_to_nwb_args['session_conditions']['Start Date']} {session_to_nwb_args['session_conditions']['Start Time']}"
            )
            raise Exception(e)
    if missing_fi1d_sessions:
        print("Missing Fi1d Sessions:")
        for session in missing_fi1d_sessions:
            print(session)
    if missing_msn_errors:
        print("Missing MSN errors:")
        for error in missing_msn_errors:
            print(error)


def fp_to_nwb(
    *, data_dir_path: Path, output_dir_path: Path, start_variable: str, stub_test: bool = False, verbose: bool = True
):
    # Setup
    experiment_type = "FP"
    experimental_groups = ["DPR", "PR", "PS", "RR20"]
    experimental_group_to_long_name = {
        "DPR": "Delayed Punishment Resistant",
        "PR": "Punishment Resistant",
        "PS": "Punishment Sensitive",
        "RR20": "RR20",
    }
    behavior_path = data_dir_path / f"{experiment_type} Experiments" / "Behavior"
    photometry_path = data_dir_path / f"{experiment_type} Experiments" / "Photometry"
    raw_file_to_info = get_raw_info(behavior_path)

    # Iterate through file system to get necessary information for converting each session
    session_to_nwb_args_per_session: list[dict] = []  # Each dict contains the args for session_to_nwb for a session
    nwbfile_paths = set()  # Each path is the path to the nwb file created for a session

    # Iterate through all photometry files
    for experimental_group, long_name in experimental_group_to_long_name.items():
        experimental_group_path = photometry_path / long_name
        experimental_subgroups = [subgroup for subgroup in experimental_group_path.iterdir() if subgroup.is_dir()]
        for experimental_subgroup in experimental_subgroups:  # Early or Late but with typos ex. 'late' vs 'Late'
            fiber_photometry_folder_paths = []
            for fiber_photometry_folder_path in experimental_subgroup.iterdir():
                if fiber_photometry_folder_path.name.startswith("Photo"):
                    fiber_photometry_folder_paths.append(fiber_photometry_folder_path)
                elif fiber_photometry_folder_path.is_dir():
                    for fiber_photometry_folder_path_sub in fiber_photometry_folder_path.iterdir():
                        if fiber_photometry_folder_path_sub.name.startswith("Photo"):
                            fiber_photometry_folder_paths.append(fiber_photometry_folder_path_sub)
            for fiber_photometry_folder_path in fiber_photometry_folder_paths:
                photometry_subject_id = (
                    fiber_photometry_folder_path.name.split("-")[0].split("Photo_")[1].replace("_", ".")
                )
                photometry_start_date = fiber_photometry_folder_path.name.split("-")[1]
                photometry_start_date = datetime.strptime(photometry_start_date, "%y%m%d").strftime("%m/%d/%y")

                subject_dir = behavior_path / experimental_group / photometry_subject_id
                header_variables = get_header_variables(
                    subject_dir, photometry_subject_id, raw_file_to_info, start_variable
                )
                start_dates, start_times, msns, file_paths, subjects, box_numbers = header_variables
                (
                    matching_start_dates,
                    matching_start_times,
                    matching_msns,
                    matching_file_paths,
                    matching_subjects,
                    matching_box_numbers,
                ) = ([], [], [], [], [], [])
                for start_date, start_time, msn, file, subject, box_number in zip(
                    start_dates, start_times, msns, file_paths, subjects, box_numbers
                ):
                    if start_date == photometry_start_date:
                        matching_start_dates.append(start_date)
                        matching_start_times.append(start_time)
                        matching_msns.append(msn)
                        matching_file_paths.append(file)
                        matching_subjects.append(subject)
                        matching_box_numbers.append(box_number)
                if (
                    (photometry_subject_id == "88.239" and photometry_start_date == "02/19/19")
                    or (photometry_subject_id == "271.396" and photometry_start_date == "07/07/20")
                    or (photometry_subject_id == "332.393" and photometry_start_date == "07/28/20")
                    or (photometry_subject_id == "334.394" and photometry_start_date == "07/21/20")
                    or (photometry_subject_id == "140.306" and photometry_start_date == "08/09/19")
                    or (photometry_subject_id == "139.298" and photometry_start_date == "09/12/19")
                ):  # TODO: Ask Lerner Lab about these sessions
                    continue
                assert (
                    len(matching_start_dates) == 1
                ), f"Expected 1 matching session for {experimental_group}/{photometry_subject_id} on {photometry_start_date}, but found {len(matching_start_dates)}"
                start_date, start_time, msn, file, subject, box_number = (
                    matching_start_dates[0],
                    matching_start_times[0],
                    matching_msns[0],
                    matching_file_paths[0],
                    matching_subjects[0],
                    matching_box_numbers[0],
                )
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
                    fiber_photometry_folder_path=fiber_photometry_folder_path,
                    subject_id=photometry_subject_id,
                    session_conditions=session_conditions,
                    start_variable=start_variable,
                    start_datetime=start_datetime,
                    experiment_type=experiment_type,
                    experimental_group=experimental_group,
                    stub_test=stub_test,
                    verbose=verbose,
                )
                session_to_nwb_args_per_session.append(session_to_nwb_args)
                nwbfile_path = (
                    output_dir_path
                    / f"{experiment_type}_{experimental_group}_{photometry_subject_id}_{start_datetime.isoformat()}.nwb"
                )
                nwbfile_paths.add(nwbfile_path)

    # Iterate through all behavior files
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
                if session_should_be_skipped(
                    start_date=start_date,
                    start_time=start_time,
                    subject_id=subject_id,
                    msn=msn,
                ):
                    continue
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
                nwbfile_path = (
                    output_dir_path
                    / f"{experiment_type}_{experimental_group}_{subject_id}_{start_datetime.isoformat()}.nwb"
                )
                if nwbfile_path in nwbfile_paths:
                    continue
                nwbfile_paths.add(nwbfile_path)
                session_to_nwb_args_per_session.append(session_to_nwb_args)
    return session_to_nwb_args_per_session


def opto_to_nwb(
    *, data_dir_path: Path, output_dir_path: Path, start_variable: str, stub_test: bool = False, verbose: bool = True
):
    experiment_type = "Opto"
    experimental_groups = ["DLS-Excitatory", "DMS-Excitatory", "DMS-Inhibitory"]
    experimental_group_to_optogenetic_treatments = {
        "DLS-Excitatory": ["ChR2", "EYFP", "ChR2Scrambled"],
        "DMS-Excitatory": ["ChR2", "EYFP", "ChR2Scrambled"],
        "DMS-Inhibitory": ["NpHR", "EYFP", "NpHRScrambled"],
    }
    optogenetic_treatment_to_folder_name = {
        "ChR2": "ChR2",
        "EYFP": "EYFP",
        "ChR2Scrambled": "Scrambled",
        "NpHR": "Halo",
        "NpHRScrambled": "Scrambled",
    }
    experimental_group_to_subgroups = {
        "DLS-Excitatory": [""],
        "DMS-Excitatory": [""],
        "DMS-Inhibitory": ["Group 1"],  # TODO: Get group 2 data from Lerner Lab
    }
    opto_path = data_dir_path / f"{experiment_type} Experiments"
    session_to_nwb_args_per_session: list[dict] = []  # Each dict contains the args for session_to_nwb for a session
    nwbfile_paths = set()  # Each path is the path to the nwb file created for a session

    for experimental_group in experimental_groups:
        experimental_group_path = opto_path / experimental_group.replace("-", " ")
        for subgroup in experimental_group_to_subgroups[experimental_group]:
            subgroup_path = experimental_group_path / subgroup if subgroup else experimental_group_path
            optogenetic_treatments = experimental_group_to_optogenetic_treatments[experimental_group]
            for optogenetic_treatment in optogenetic_treatments:
                optogenetic_treatment_path = subgroup_path / optogenetic_treatment_to_folder_name[optogenetic_treatment]
                subject_paths = [
                    path
                    for path in optogenetic_treatment_path.iterdir()
                    if not (
                        path.name.startswith(".")
                        or path.name.endswith(".csv")
                        or path.name.endswith(".CSV")  # TODO: add support for CSV files
                    )
                ]
                for subject_path in subject_paths:
                    subject_id = (
                        subject_path.name.split(" ")[1] if "Subject" in subject_path.name else subject_path.name
                    )
                    header_variables = get_opto_header_variables(subject_path, start_variable)
                    start_dates, start_times, msns, file_paths, subjects, box_numbers = header_variables
                    for start_date, start_time, msn, file, subject, box_number in zip(
                        start_dates, start_times, msns, file_paths, subjects, box_numbers
                    ):
                        if session_should_be_skipped(
                            start_date=start_date,
                            start_time=start_time,
                            subject_id=subject_id,
                            msn=msn,
                        ):
                            continue
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
                            optogenetic_treatment=optogenetic_treatment,
                            stub_test=stub_test,
                            verbose=verbose,
                        )
                        nwbfile_path = (
                            output_dir_path
                            / f"{experiment_type}_{experimental_group}__{optogenetic_treatment}_{subject_id}_{start_datetime.isoformat()}.nwb"
                        )
                        if nwbfile_path in nwbfile_paths:
                            continue
                        nwbfile_paths.add(nwbfile_path)
                        session_to_nwb_args_per_session.append(session_to_nwb_args)
    return session_to_nwb_args_per_session


def get_opto_header_variables(subject_path, start_variable):
    if subject_path.is_file():
        medpc_file_path = subject_path
        medpc_variables = get_medpc_variables(
            file_path=medpc_file_path, variable_names=["Start Date", "Start Time", "MSN"]
        )
        start_dates = medpc_variables["Start Date"]
        start_times = medpc_variables["Start Time"]
        msns = medpc_variables["MSN"]
        file_paths = [medpc_file_path] * len(start_dates)
        subjects = [None] * len(start_dates)
        box_numbers = [None] * len(start_dates)
    elif subject_path.is_dir():
        start_dates, start_times, msns, file_paths = [], [], [], []
        medpc_files, csv_files = [], []
        for file in subject_path.iterdir():
            if file.name.startswith("."):
                continue
            if file.suffix == ".csv" or file.suffix == ".CSV":
                csv_files.append(file)
            elif not file.name.startswith("."):
                medpc_files.append(file)
        for file in medpc_files:
            medpc_variables = get_medpc_variables(file_path=file, variable_names=["Start Date", "Start Time", "MSN"])
            for start_date, start_time, msn in zip(
                medpc_variables["Start Date"], medpc_variables["Start Time"], medpc_variables["MSN"]
            ):
                start_dates.append(start_date)
                start_times.append(start_time)
                msns.append(msn)
                file_paths.append(file)
        # for file in csv_files:
        #     start_date = file.stem.split("_")[1].replace("-", "/")
        #     start_time = "00:00:00"
        #     msn = "Unknown"
        #     start_dates.append(start_date)
        #     start_times.append(start_time)
        #     msns.append(msn)
        #     file_paths.append(file)
        subjects = [None] * len(start_dates)
        box_numbers = [None] * len(start_dates)

    return start_dates, start_times, msns, file_paths, subjects, box_numbers


def session_should_be_skipped(*, start_date, start_time, subject_id, msn):
    """Return True if the session should be skipped, False otherwise.

    Sessions should be skipped if their msn is irrelevant to the dataset or
    if they have subject_ids that don't match the file structure.

    Parameters
    ----------
    start_date : str
        The start date of the session.
    start_time : str
        The start time of the session.
    subject_id : str
        The subject ID of the session.
    msn : str
        The MSN of the session.

    Returns
    -------
    bool
        True if the session should be skipped, False otherwise.
    """
    msns_to_skip = {
        "RR10_Right_AHJS",
        "Magazine Training 1 hr",
        "FOOD_Magazine Training 1 hr",
        "RI_60_Left_Probability_AH_050619",
        "RI_60_Right_Probability_AH_050619",
        "RR20_Right_AHJS",
        "RR20_Left",
        "Extinction - 1 HR",
        "RR10_Left_AHJS",
        "Probe Test Habit Training CC",
        "FOOD_FR1 Hapit Training TTL",
    }
    if msn in msns_to_skip:
        return True
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
        return True
    return False


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
        if csv_date in start_dates:
            continue
        csv_file_path = subject_dir / f"{subject_id}_{csv_date.replace('/', '-')}.csv"
        session_df = pd.read_csv(csv_file_path)
        port_entry_times = np.trim_zeros(session_df["portEntryTs"].dropna().values, trim="b")
        start_date, start_time, msn, file, subject, box_number = match_csv_session_to_medpc_session(
            raw_file_to_info=raw_file_to_info,
            csv_date=csv_date,
            port_entry_times=port_entry_times,
            start_variable=start_variable,
        )
        if start_date is None:  # If we can't find a matching session in the Medpc files, we'll use the CSV file
            start_date = csv_date
            start_time = "00:00:00"
            msn = "Unknown"
            file = csv_file_path
            subject = subject_id
            box_number = None

        start_dates.append(start_date)
        start_times.append(start_time)
        msns.append(msn)
        file_paths.append(file)
        subjects.append(subject)
        box_numbers.append(box_number)

    return start_dates, start_times, msns, file_paths, subjects, box_numbers


def match_csv_session_to_medpc_session(*, raw_file_to_info, csv_date, port_entry_times, start_variable):
    subject = None
    for file, info in raw_file_to_info.items():
        for start_date, start_time, msn, box_number in zip(
            info["Start Date"], info["Start Time"], info["MSN"], info["Box"]
        ):
            if start_date != csv_date:
                continue
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
                return start_date, start_time, msn, file, subject, box_number
    return None, None, None, None, None, None


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
