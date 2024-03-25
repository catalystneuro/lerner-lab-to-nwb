"""Primary script to run to convert example sessions using the NWBConverter."""
from pathlib import Path
from typing import Union, Literal
import shutil
from neuroconv.utils import load_dict_from_file, dict_deep_update
from datetime import datetime

from lerner_lab_to_nwb.seiler_2024 import Seiler2024NWBConverter


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    behavior_file_path: Union[str, Path],
    fiber_photometry_folder_path: Union[str, Path],
    start_datetime: datetime,
    subject_id: str,
    session_conditions: dict,
    start_variable: str,
    experiment_type: Literal["FP", "Opto"],
    experimental_group: Literal["DPR", "PR", "PS", "RR20"],
    stub_test: bool = False,
    verbose: bool = True,
):
    """Convert a session to NWB."""

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    nwbfile_path = (
        output_dir_path / f"{experiment_type}_{experimental_group}_{subject_id}_{start_datetime.isoformat()}.nwb"
    )
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
    if experiment_type == "FP":
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

    # # session with all NaNs for port duration
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

    # Fiber Photometry session
    experiment_type = "FP"
    experimental_group = "PR"
    subject_id = "028.392"
    start_datetime = datetime(2020, 7, 9, 13, 1, 26)
    session_conditions = {
        "Start Date": start_datetime.strftime("%m/%d/%y"),
        "Start Time": start_datetime.strftime("%H:%M:%S"),
    }
    start_variable = "Start Date"
    behavior_file_path = (
        data_dir_path
        / f"{experiment_type} Experiments"
        / "Behavior"
        / f"{experimental_group}"
        / f"{subject_id}"
        / f"{subject_id}"
    )
    fiber_photometry_folder_path = (
        data_dir_path
        / f"{experiment_type} Experiments"
        / "Photometry"
        / f"Punishment Resistant"
        / f"Early RI60"
        / f"Photo_{subject_id.split('.')[0]}_{subject_id.split('.')[1]}-200709-130922"
    )
    print(fiber_photometry_folder_path)
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        behavior_file_path=behavior_file_path,
        fiber_photometry_folder_path=fiber_photometry_folder_path,
        subject_id=subject_id,
        session_conditions=session_conditions,
        start_variable=start_variable,
        start_datetime=start_datetime,
        experiment_type=experiment_type,
        experimental_group=experimental_group,
        stub_test=stub_test,
    )
