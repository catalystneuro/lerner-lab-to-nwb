"""Primary script to run to convert example sessions using the NWBConverter."""
from pathlib import Path
from typing import Union, Literal, Optional
import shutil
from neuroconv.utils import load_dict_from_file, dict_deep_update
from datetime import datetime

from lerner_lab_to_nwb.seiler_2024 import Seiler2024NWBConverter


def session_to_nwb(
    *,
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    behavior_file_path: Union[str, Path],
    start_datetime: datetime,
    subject_id: str,
    session_conditions: dict,
    start_variable: str,
    experiment_type: Literal["FP", "Opto"],
    experimental_group: Literal["DPR", "PR", "PS", "RR20", "DMS-Inhibitory", "DMS-Excitatory", "DLS-Excitatory"],
    optogenetic_treatment: Optional[Literal["ChR2", "EYFP", "ChR2Scrambled", "NpHR", "NpHRScrambled"]] = None,
    fiber_photometry_folder_path: Optional[Union[str, Path]] = None,
    stub_test: bool = False,
    verbose: bool = True,
):
    """Convert a session to NWB.

    Parameters
    ----------
    data_dir_path : Union[str, Path]
        Path to the directory containing the raw data.
    output_dir_path : Union[str, Path]
        Path to the directory to save the NWB file.
    behavior_file_path : Union[str, Path]
        Path to the MedPC file. Or path to the csv file if the behavior data is in a csv file.
    start_datetime : datetime
        The start datetime of the session.
    subject_id : str
        The subject ID.
    session_conditions : dict
        The conditions that define the session. The keys are the names of the single-line variables (ex. 'Start Date')
        and the values are the values of those variables for the desired session (ex. '11/09/18').
    start_variable : str
        The name of the variable that starts the session (ex. 'Start Date').
    experiment_type : Literal["FP", "Opto"]
        The type of experiment.
    experimental_group : Literal["DPR", "PR", "PS", "RR20", "DMS-Inhibitory", "DMS-Excitatory", "DLS-Excitatory"]
        The experimental group.
    optogenetic_treatment : Optional[Literal["ChR2", "EYFP", "ChR2Scrambled", "NpHR", "NpHRScrambled"]], optional
        The optogenetic treatment, by default None for FP sessions.
    stub_test : bool, optional
        Whether to run a stub test, by default False
    verbose : bool, optional
        Whether to print verbose output, by default True
    """

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    if experiment_type == "FP":
        nwbfile_path = (
            output_dir_path / f"{experiment_type}_{experimental_group}_{subject_id}_{start_datetime.isoformat()}.nwb"
        )
    elif experiment_type == "Opto":
        nwbfile_path = (
            output_dir_path
            / f"{experiment_type}_{experimental_group}_{optogenetic_treatment}_{subject_id}_{start_datetime.isoformat()}.nwb"
        )
    else:
        raise ValueError(f"Invalid experiment type: {experiment_type}")
    source_data = {}
    conversion_options = {}

    # Add Behavior
    source_data.update(
        dict(
            Behavior={
                "file_path": str(behavior_file_path),
                "session_conditions": session_conditions,
                "start_variable": start_variable,
                "verbose": verbose,
            }
        )
    )
    conversion_options.update(dict(Behavior={}))

    # Add Fiber Photometry
    if fiber_photometry_folder_path is not None:
        source_data.update(
            dict(
                FiberPhotometry={
                    "folder_path": str(fiber_photometry_folder_path),
                    "verbose": verbose,
                    "behavior_kwargs": source_data["Behavior"],
                }
            )
        )
        conversion_options.update(dict(FiberPhotometry={}))

    # Add Optogenetics
    if experiment_type == "Opto":
        source_data.update(
            dict(
                Optogenetic={
                    "file_path": str(behavior_file_path),
                    "session_conditions": session_conditions,
                    "start_variable": start_variable,
                    "experimental_group": experimental_group,
                    "optogenetic_treatment": optogenetic_treatment,
                    "verbose": verbose,
                }
            )
        )
        conversion_options.update(dict(Optogenetic={}))

    converter = Seiler2024NWBConverter(source_data=source_data, verbose=verbose)
    metadata = converter.get_metadata()

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "seiler_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


if __name__ == "__main__":
    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/raw_data")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/conversion_nwb")
    stub_test = False

    if output_dir_path.exists():
        shutil.rmtree(
            output_dir_path, ignore_errors=True
        )  # ignore errors due to MacOS race condition (https://github.com/python/cpython/issues/81441)

    # # No-shock example session
    # experiment_type = "FP"
    # experimental_group = "RR20"
    # subject_id = "95.259"
    # start_datetime = datetime(2019, 4, 9, 10, 34, 30)
    # behavior_file_path = (
    #     data_dir_path
    #     / f"{experiment_type} Experiments"
    #     / "Behavior"
    #     / f"{experimental_group}"
    #     / f"{subject_id}"
    #     / f"{subject_id}"
    # )
    # session_conditions = {
    #     "Start Date": start_datetime.strftime("%m/%d/%y"),
    #     "Start Time": start_datetime.strftime("%H:%M:%S"),
    # }
    # start_variable = "Start Date"
    # session_to_nwb(
    #     data_dir_path=data_dir_path,
    #     output_dir_path=output_dir_path,
    #     behavior_file_path=behavior_file_path,
    #     subject_id=subject_id,
    #     session_conditions=session_conditions,
    #     start_variable=start_variable,
    #     start_datetime=start_datetime,
    #     experiment_type=experiment_type,
    #     experimental_group=experimental_group,
    #     stub_test=stub_test,
    # )

    # # Shock session
    # experiment_type = "FP"
    # experimental_group = "RR20"
    # subject_id = "95.259"
    # start_datetime = datetime(2019, 4, 18, 10, 41, 42)
    # session_conditions = {
    #     "Start Date": start_datetime.strftime("%m/%d/%y"),
    #     "Start Time": start_datetime.strftime("%H:%M:%S"),
    # }
    # start_variable = "Start Date"
    # behavior_file_path = (
    #     data_dir_path
    #     / f"{experiment_type} Experiments"
    #     / "Behavior"
    #     / f"{experimental_group}"
    #     / f"{subject_id}"
    #     / f"{subject_id}"
    # )
    # session_to_nwb(
    #     data_dir_path=data_dir_path,
    #     output_dir_path=output_dir_path,
    #     behavior_file_path=behavior_file_path,
    #     subject_id=subject_id,
    #     session_conditions=session_conditions,
    #     start_variable=start_variable,
    #     start_datetime=start_datetime,
    #     experiment_type=experiment_type,
    #     experimental_group=experimental_group,
    #     stub_test=stub_test,
    # )

    # # session with lots of trailing whitespace
    # experiment_type = "FP"
    # experimental_group = "PR"
    # subject_id = "141.308"
    # start_datetime = datetime(2019, 8, 1, 14, 1, 17)
    # session_conditions = {
    #     "Start Date": start_datetime.strftime("%m/%d/%y"),
    #     "Start Time": start_datetime.strftime("%H:%M:%S"),
    # }
    # start_variable = "Start Date"
    # behavior_file_path = (
    #     data_dir_path
    #     / f"{experiment_type} Experiments"
    #     / "Behavior"
    #     / f"{experimental_group}"
    #     / f"{subject_id}"
    #     / f"{subject_id}"
    # )
    # session_to_nwb(
    #     data_dir_path=data_dir_path,
    #     output_dir_path=output_dir_path,
    #     behavior_file_path=behavior_file_path,
    #     subject_id=subject_id,
    #     session_conditions=session_conditions,
    #     start_variable=start_variable,
    #     start_datetime=start_datetime,
    #     experiment_type=experiment_type,
    #     experimental_group=experimental_group,
    #     stub_test=stub_test,
    # )

    # # session with missing medpc file
    # experiment_type = "FP"
    # experimental_group = "PS"
    # subject_id = "75.214"
    # start_datetime = datetime(2018, 10, 29, 12, 41, 44)
    # session_conditions = {
    #     "Start Date": start_datetime.strftime("%m/%d/%y"),
    #     "Start Time": start_datetime.strftime("%H:%M:%S"),
    #     "Subject": subject_id,
    # }
    # start_variable = "Start Date"
    # behavior_file_path = (
    #     data_dir_path
    #     / f"{experiment_type} Experiments"
    #     / "Behavior"
    #     / "MEDPC_RawFilesbyDate"
    #     / f"{start_datetime.date().isoformat()}"
    # )
    # session_to_nwb(
    #     data_dir_path=data_dir_path,
    #     output_dir_path=output_dir_path,
    #     behavior_file_path=behavior_file_path,
    #     subject_id=subject_id,
    #     session_conditions=session_conditions,
    #     start_variable=start_variable,
    #     start_datetime=start_datetime,
    #     experiment_type=experiment_type,
    #     experimental_group=experimental_group,
    #     stub_test=stub_test,
    # )

    # # session with missing medpc file and missing subject info, but has csv file
    # experiment_type = "FP"
    # experimental_group = "PS"
    # subject_id = "75.214"
    # start_datetime = datetime(2018, 11, 9, 11, 46, 33)
    # box = "1"
    # session_conditions = {
    #     "Start Date": start_datetime.strftime("%m/%d/%y"),
    #     "Start Time": start_datetime.strftime("%H:%M:%S"),
    #     "Box": box,
    # }
    # start_variable = "Start Date"
    # behavior_file_path = (
    #     data_dir_path
    #     / f"{experiment_type} Experiments"
    #     / "Behavior"
    #     / "MEDPC_RawFilesbyDate"
    #     / f"{start_datetime.date().isoformat()}"
    # )
    # session_to_nwb(
    #     data_dir_path=data_dir_path,
    #     output_dir_path=output_dir_path,
    #     behavior_file_path=behavior_file_path,
    #     subject_id=subject_id,
    #     session_conditions=session_conditions,
    #     start_variable=start_variable,
    #     start_datetime=start_datetime,
    #     experiment_type=experiment_type,
    #     experimental_group=experimental_group,
    #     stub_test=stub_test,
    # )

    # # Fiber Photometry session
    # experiment_type = "FP"
    # experimental_group = "PR"
    # subject_id = "028.392"
    # start_datetime = datetime(2020, 7, 9, 13, 1, 26)
    # session_conditions = {
    #     "Start Date": start_datetime.strftime("%m/%d/%y"),
    #     "Start Time": start_datetime.strftime("%H:%M:%S"),
    # }
    # start_variable = "Start Date"
    # behavior_file_path = (
    #     data_dir_path
    #     / f"{experiment_type} Experiments"
    #     / "Behavior"
    #     / f"{experimental_group}"
    #     / f"{subject_id}"
    #     / f"{subject_id}"
    # )
    # fiber_photometry_folder_path = (
    #     data_dir_path
    #     / f"{experiment_type} Experiments"
    #     / "Photometry"
    #     / f"Punishment Resistant"
    #     / f"Early RI60"
    #     / f"Photo_{subject_id.split('.')[0]}_{subject_id.split('.')[1]}-200709-130922"
    # )
    # session_to_nwb(
    #     data_dir_path=data_dir_path,
    #     output_dir_path=output_dir_path,
    #     behavior_file_path=behavior_file_path,
    #     fiber_photometry_folder_path=fiber_photometry_folder_path,
    #     subject_id=subject_id,
    #     session_conditions=session_conditions,
    #     start_variable=start_variable,
    #     start_datetime=start_datetime,
    #     experiment_type=experiment_type,
    #     experimental_group=experimental_group,
    #     stub_test=stub_test,
    # )

    # # Fiber Photometry session without unrewarded port entries
    # experiment_type = "FP"
    # experimental_group = "PS"
    # subject_id = "249.391"
    # start_datetime = datetime(2020, 7, 21, 11, 42, 49)
    # session_conditions = {
    #     "Start Date": start_datetime.strftime("%m/%d/%y"),
    #     "Start Time": start_datetime.strftime("%H:%M:%S"),
    # }
    # start_variable = "Start Date"
    # behavior_file_path = (
    #     data_dir_path
    #     / f"{experiment_type} Experiments"
    #     / "Behavior"
    #     / f"{experimental_group}"
    #     / f"{subject_id}"
    #     / f"{subject_id}"
    # )
    # fiber_photometry_folder_path = (
    #     data_dir_path
    #     / f"{experiment_type} Experiments"
    #     / "Photometry"
    #     / f"Punishment Sensitive"
    #     / f"Late RI60"
    #     / f"Photo_{subject_id.split('.')[0]}_{subject_id.split('.')[1]}-200721-120136"
    # )
    # session_to_nwb(
    #     data_dir_path=data_dir_path,
    #     output_dir_path=output_dir_path,
    #     behavior_file_path=behavior_file_path,
    #     fiber_photometry_folder_path=fiber_photometry_folder_path,
    #     subject_id=subject_id,
    #     session_conditions=session_conditions,
    #     start_variable=start_variable,
    #     start_datetime=start_datetime,
    #     experiment_type=experiment_type,
    #     experimental_group=experimental_group,
    #     stub_test=stub_test,
    # )

    # # Behavior session from csv file
    # experiment_type = "FP"
    # experimental_group = "DPR"
    # subject_id = "87.239"
    # start_datetime = datetime(2019, 3, 19, 0, 0, 0)
    # session_conditions = {}
    # start_variable = ""
    # behavior_file_path = (
    #     data_dir_path
    #     / f"{experiment_type} Experiments"
    #     / "Behavior"
    #     / f"{experimental_group}"
    #     / f"{subject_id}"
    #     / f"{subject_id}_{start_datetime.strftime('%m-%d-%y')}.csv"
    # )
    # session_to_nwb(
    #     data_dir_path=data_dir_path,
    #     output_dir_path=output_dir_path,
    #     behavior_file_path=behavior_file_path,
    #     subject_id=subject_id,
    #     session_conditions=session_conditions,
    #     start_variable=start_variable,
    #     start_datetime=start_datetime,
    #     experiment_type=experiment_type,
    #     experimental_group=experimental_group,
    #     stub_test=stub_test,
    # )

    # Example Opto session
    experiment_type = "Opto"
    experimental_group = "DMS-Inhibitory"
    optogenetic_treatment = "NpHR"
    subject_id = "112.415"
    start_datetime = datetime(2020, 10, 21, 13, 8, 39)
    session_conditions = {
        "Start Date": start_datetime.strftime("%m/%d/%y"),
        "Start Time": start_datetime.strftime("%H:%M:%S"),
    }
    start_variable = "Start Date"
    behavior_file_path = (
        data_dir_path
        / f"{experiment_type} Experiments"
        / f"{experimental_group.replace('-', ' ')}"
        / f"Group 1"
        / f"Halo"
        / f"{subject_id}"
    )
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        behavior_file_path=behavior_file_path,
        subject_id=subject_id,
        session_conditions=session_conditions,
        start_variable=start_variable,
        start_datetime=start_datetime,
        experiment_type=experiment_type,
        experimental_group=experimental_group,
        optogenetic_treatment=optogenetic_treatment,
        stub_test=stub_test,
    )
