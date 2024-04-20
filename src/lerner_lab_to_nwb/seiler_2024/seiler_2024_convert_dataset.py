"""Convert the entire dataset to NWB."""
from pathlib import Path
from typing import Union
from tqdm import tqdm
from datetime import datetime
import shutil
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from pprint import pformat
import traceback

from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_session import session_to_nwb
from lerner_lab_to_nwb.seiler_2024.medpc import get_medpc_variables
from lerner_lab_to_nwb.seiler_2024.medpc import read_medpc_file


def dataset_to_nwb(
    *,
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    max_workers: int = 1,
    stub_test: bool = False,
    verbose: bool = True,
):
    """Convert the entire dataset to NWB.

    Parameters
    ----------
    data_dir_path : Union[str, Path]
        The path to the directory containing the raw data.
    output_dir_path : Union[str, Path]
        The path to the directory where the NWB files will be saved.
    stub_test : bool, optional
        Whether to run a stub test, by default False
    verbose : bool, optional
        Whether to print verbose output, by default True
    """
    start_variable = "Start Date"
    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    fp_session_to_nwb_args_per_session = fp_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        start_variable=start_variable,
        stub_test=stub_test,
        verbose=verbose,
    )
    # opto_session_to_nwb_args_per_session = opto_to_nwb(
    #     data_dir_path=data_dir_path,
    #     output_dir_path=output_dir_path,
    #     start_variable=start_variable,
    #     stub_test=stub_test,
    #     verbose=verbose,
    # )
    # session_to_nwb_args_per_session = fp_session_to_nwb_args_per_session + opto_session_to_nwb_args_per_session
    session_to_nwb_args_per_session = fp_session_to_nwb_args_per_session
    # print(len(session_to_nwb_args_per_session))
    # return

    futures = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for session_to_nwb_kwargs in session_to_nwb_args_per_session:
            experiment_type = session_to_nwb_kwargs["experiment_type"]
            experimental_group = session_to_nwb_kwargs["experimental_group"]
            subject_id = session_to_nwb_kwargs["subject_id"]
            start_datetime = session_to_nwb_kwargs["start_datetime"]
            optogenetic_treatment = session_to_nwb_kwargs.get("optogenetic_treatment", None)
            if experiment_type == "FP":
                exception_file_path = (
                    output_dir_path
                    / f"ERROR_{experiment_type}_{experimental_group}_{subject_id}_{start_datetime.isoformat().replace(':', '-')}.txt"
                )
            elif experiment_type == "Opto":
                exception_file_path = (
                    output_dir_path
                    / f"ERROR_{experiment_type}_{experimental_group}_{optogenetic_treatment}_{subject_id}_{start_datetime.isoformat().replace(':', '-')}.txt"
                )
            futures.append(
                executor.submit(
                    safe_session_to_nwb,
                    session_to_nwb_kwargs=session_to_nwb_kwargs,
                    exception_file_path=exception_file_path,
                )
            )
        for _ in tqdm(as_completed(futures), total=len(futures)):
            pass


def safe_session_to_nwb(*, session_to_nwb_kwargs: dict, exception_file_path: Union[Path, str]):
    """Convert a session to NWB while handling any errors by recording error messages to the exception_file_path.

    Parameters
    ----------
    session_to_nwb_kwargs : dict
        The arguments for session_to_nwb.
    exception_file_path : Path
        The path to the file where the exception messages will be saved.
    """
    exception_file_path = Path(exception_file_path)
    try:
        session_to_nwb(**session_to_nwb_kwargs)
    except Exception as e:
        with open(exception_file_path, mode="w") as f:
            f.write(f"session_to_nwb_kwargs: \n {pformat(session_to_nwb_kwargs)}\n\n")
            f.write(traceback.format_exc())


def fp_to_nwb(
    *, data_dir_path: Path, output_dir_path: Path, start_variable: str, stub_test: bool = False, verbose: bool = True
):
    """Convert the Fiber Photometry portion of the dataset to NWB.

    Parameters
    ----------
    data_dir_path : Path
        The path to the directory containing the raw data.
    output_dir_path : Path
        The path to the directory where the NWB files will be saved.
    start_variable : str
        The variable to use as the start variable for the session.
    stub_test : bool, optional
        Whether to run a stub test, by default False
    verbose : bool, optional
        Whether to print verbose output, by default True

    Returns
    -------
    list[dict]
        A list of dictionaries containing the arguments for session_to_nwb for each session.
    """
    # Setup
    experiment_type = "FP"
    experimental_groups = ["DPR", "PR", "PS", "RR20"]
    experimental_group_to_long_name = {
        "DPR": "Delayed Punishment Resistant",
        "PR": "Punishment Resistant",
        "PS": "Punishment Sensitive",
        # "RR20": "RR20",
    }
    behavior_path = data_dir_path / f"{experiment_type} Experiments" / "Behavior"
    photometry_path = data_dir_path / f"{experiment_type} Experiments" / "Photometry"
    fi1r_only_sessions = {
        "Photo_333_393-200713-121027",
        "Photo_346_394-200707-141513",
        "Photo_64_205-181017-094913",
        "Photo_81_236-190117-102128",
        "Photo_87_239-190228-111317",
        "Photo_81_236-190207-101451",
        "Photo_87_239-190321-110120",
        "Photo_88_239-190311-112034",
        "Photo_333_393-200729-115506",
        "Photo_346_394-200722-132345",
        "Photo_349_393-200717-123319",
        "Photo_111_285-190605-142759",
        "Photo_141_308-190809-143410",
        "Photo_80_236-190121-093425",
        "Photo_61_207-181017-105639",
        "Photo_63_207-181015-093910",
        "Photo_63_207-181030-103332",
        "Photo_80_236-190121-093425",
        "Photo_89_247-190328-125515",
        "Photo_028_392-200724-130323",
        "Photo_048_392-200728-121222",
        "Photo_112_283-190620-093542",
        "Photo_113_283-190605-115438",
        "Photo_114_273-190607-140822",
        "Photo_115_273-190611-115654",
        "Photo_139_298-190809-132427",
        "Photo_75_214-181029-124815",
        "Photo_92_246-190227-143210",
        "Photo_92_246-190227-150307",
        "Photo_93_246-190222-130128",
        "Photo_75_214-181029-124815",
        "Photo_78_214-181031-131820",
        "Photo_90_247-190328-103249",
        "Photo_92_246-190228-132737",
        "Photo_92_246-190319-114357",
        "Photo_93_246-190222-130128",
        "Photo_94_246-190328-113641",
        "Photo_140_306-190903-102551",
        "Photo_271_396-200722-121638",
        "Photo_347_393-200723-113530",
        "Photo_348_393-200730-113125",
        "Photo_139_298-190912-095034",
        "Photo_88_239-190219-140027",
        "Photo_89_247-190308-095258",
        "Photo_140_306-190809-121107",
        "Photo_271_396-200707-125117",
    }
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
                header_variables = get_fp_header_variables(
                    subject_dir, photometry_subject_id, raw_file_to_info, start_variable
                )
                start_dates, start_times, msns, file_paths, subjects, box_numbers = header_variables
                matching_start_dates = []
                matching_start_times = []
                matching_msns = []
                matching_file_paths = []
                matching_subjects = []
                matching_box_numbers = []
                for start_date, start_time, msn, file, subject, box_number in zip(
                    start_dates, start_times, msns, file_paths, subjects, box_numbers
                ):
                    if (
                        photometry_subject_id == "271.396"
                        and photometry_start_date == "07/07/20"
                        and msn == "FOOD_RI 60 RIGHT TTL"
                        or photometry_subject_id == "88.239"
                        and photometry_start_date == "02/19/19"
                        and msn == "FOOD_RI 60 LEFT TTL"
                    ):
                        continue
                    if start_date == photometry_start_date:
                        matching_start_dates.append(start_date)
                        matching_start_times.append(start_time)
                        matching_msns.append(msn)
                        matching_file_paths.append(file)
                        matching_subjects.append(subject)
                        matching_box_numbers.append(box_number)
                if (
                    (
                        photometry_subject_id == "334.394" and photometry_start_date == "07/21/20"
                    )  # TODO: Ask Lerner Lab about this session
                    or (
                        photometry_subject_id == "64.205"
                        and photometry_start_date == "10/17/18"
                        and experimental_subgroup.name == "Late"
                    )
                    or (
                        photometry_subject_id == "81.236"
                        and photometry_start_date == "01/17/19"
                        and experimental_subgroup.name == "Late"
                    )
                    or (
                        photometry_subject_id == "87.239"
                        and photometry_start_date == "02/28/19"
                        and experimental_subgroup.name == "Late"
                    )
                    or (
                        photometry_subject_id == "88.239"
                        and photometry_start_date == "02/19/19"
                        and experimental_subgroup.name == "Late"
                    )
                    or (
                        photometry_subject_id == "80.236"
                        and photometry_start_date == "01/21/19"
                        and experimental_subgroup.name == "Late RI60"
                    )
                    or (
                        photometry_subject_id == "75.214"
                        and photometry_start_date == "10/29/18"
                        and experimental_subgroup.name == "Late RI60"
                    )
                    or (
                        photometry_subject_id == "93.246"
                        and photometry_start_date == "02/22/19"
                        and experimental_subgroup.name == "Late RI60"
                    )
                    or (
                        photometry_subject_id == "78.214"
                        and photometry_start_date == "10/31/18"
                        and experimental_subgroup.name == "Late RI60"
                    )
                ):
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
                if fiber_photometry_folder_path.name in fi1r_only_sessions:
                    session_to_nwb_args["has_demodulated_commanded_voltages"] = False
                if fiber_photometry_folder_path.name == "Photo_139_298-190912-095034":
                    session_to_nwb_args["fiber_photometry_t2"] = 2267.0
                    session_to_nwb_args["second_fiber_photometry_folder_path"] = (
                        fiber_photometry_folder_path.parent / "Photo_139_298-190912-103544"
                    )
                if fiber_photometry_folder_path.name == "Photo_139_298-190912-103544":
                    continue
                if fiber_photometry_folder_path.name == "Photo_332_393-200728-122403":
                    session_to_nwb_args["second_fiber_photometry_folder_path"] = (
                        fiber_photometry_folder_path.parent / "Photo_332_393-200728-123314"
                    )
                if fiber_photometry_folder_path.name == "Photo_332_393-200728-123314":
                    continue
                if fiber_photometry_folder_path.name == "Photo_92_246-190227-143210":
                    session_to_nwb_args["second_fiber_photometry_folder_path"] = (
                        fiber_photometry_folder_path.parent / "Photo_92_246-190227-150307"
                    )
                if fiber_photometry_folder_path.name == "Photo_92_246-190227-150307":
                    continue
                if photometry_subject_id == "140.306" and photometry_start_date == "08/09/19":
                    session_to_nwb_args["flip_ttls_lr"] = True

                session_to_nwb_args_per_session.append(session_to_nwb_args)
                nwbfile_path = (
                    output_dir_path
                    / f"{experiment_type}_{experimental_group}_{photometry_subject_id}_{start_datetime.isoformat()}.nwb"
                )
                nwbfile_paths.add(nwbfile_path)

    # # Iterate through all behavior files
    # for experimental_group in experimental_groups:
    #     experimental_group_path = behavior_path / experimental_group
    #     subject_dirs = [subject_dir for subject_dir in experimental_group_path.iterdir() if subject_dir.is_dir()]
    #     for subject_dir in subject_dirs:
    #         subject_id = subject_dir.name
    #         header_variables = get_fp_header_variables(subject_dir, subject_id, raw_file_to_info, start_variable)
    #         start_dates, start_times, msns, file_paths, subjects, box_numbers = header_variables
    #         for start_date, start_time, msn, file, subject, box_number in zip(
    #             start_dates, start_times, msns, file_paths, subjects, box_numbers
    #         ):
    #             if session_should_be_skipped(
    #                 start_date=start_date,
    #                 start_time=start_time,
    #                 subject_id=subject_id,
    #                 msn=msn,
    #             ):
    #                 continue
    #             session_conditions = {
    #                 "Start Date": start_date,
    #                 "Start Time": start_time,
    #             }
    #             if subject is not None:
    #                 session_conditions["Subject"] = subject
    #             if box_number is not None:
    #                 session_conditions["Box"] = box_number
    #             start_datetime = datetime.strptime(f"{start_date} {start_time}", "%m/%d/%y %H:%M:%S")
    #             session_to_nwb_args = dict(
    #                 data_dir_path=data_dir_path,
    #                 output_dir_path=output_dir_path,
    #                 behavior_file_path=file,
    #                 subject_id=subject_id,
    #                 session_conditions=session_conditions,
    #                 start_variable=start_variable,
    #                 start_datetime=start_datetime,
    #                 experiment_type=experiment_type,
    #                 experimental_group=experimental_group,
    #                 stub_test=stub_test,
    #                 verbose=verbose,
    #             )
    #             nwbfile_path = (
    #                 output_dir_path
    #                 / f"{experiment_type}_{experimental_group}_{subject_id}_{start_datetime.isoformat()}.nwb"
    #             )
    #             if nwbfile_path in nwbfile_paths:
    #                 continue
    #             nwbfile_paths.add(nwbfile_path)
    #             session_to_nwb_args_per_session.append(session_to_nwb_args)
    return session_to_nwb_args_per_session


def opto_to_nwb(
    *, data_dir_path: Path, output_dir_path: Path, start_variable: str, stub_test: bool = False, verbose: bool = True
):
    """Convert the Optogenetic portion of the dataset to NWB.

    Parameters
    ----------
    data_dir_path : Path
        The path to the directory containing the raw data.
    output_dir_path : Path
        The path to the directory where the NWB files will be saved.
    start_variable : str
        The variable to use as the start variable for the session.
    stub_test : bool, optional
        Whether to run a stub test, by default False
    verbose : bool, optional
        Whether to print verbose output, by default True

    Returns
    -------
    list[dict]
        A list of dictionaries containing the arguments for session_to_nwb for each session.
    """
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
                        or path.name.endswith(".CSV")  # TODO: add support for session-aggregated CSV files
                    )
                ]
                for subject_path in subject_paths:
                    subject_id = (
                        subject_path.name.split(" ")[1] if "Subject" in subject_path.name else subject_path.name
                    )
                    header_variables = get_opto_header_variables(subject_path)
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


def get_opto_header_variables(subject_path):
    """Get the header variables for the Optogenetic portion of the dataset.

    Parameters
    ----------
    subject_path : Path
        The path to the subject directory.

    Returns
    -------
    tuple
        A tuple containing the start dates, start times, MSNs, file paths, subjects, and box numbers.
    """
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
        for file in csv_files:
            start_date = file.stem.split("_")[1].replace("-", "/")
            start_time = "00:00:00"
            msn = "Unknown"
            start_dates.append(start_date)
            start_times.append(start_time)
            msns.append(msn)
            file_paths.append(file)
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


def get_fp_header_variables(subject_dir, subject_id, raw_file_to_info, start_variable):
    """Get the header variables for the Fiber Photometry portion of the dataset.

    Parameters
    ----------
    subject_dir : Path
        The path to the subject directory.
    subject_id : str
        The subject ID.
    raw_file_to_info : dict
        A dictionary mapping raw files to their information.
    start_variable : str
        The variable to use as the start variable for the session.

    Returns
    -------
    tuple
        A tuple containing the start dates, start times, MSNs, file paths, subjects, and box numbers.
    """
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
    max_workers = 4
    dataset_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        max_workers=max_workers,
        stub_test=False,
        verbose=False,
    )
