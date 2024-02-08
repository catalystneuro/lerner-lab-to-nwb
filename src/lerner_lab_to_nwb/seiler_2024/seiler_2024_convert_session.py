"""Primary script to run to convert example sessions using the NWBConverter."""
from pathlib import Path
from typing import Union, Literal
import datetime
from zoneinfo import ZoneInfo
import shutil
from neuroconv.utils import load_dict_from_file, dict_deep_update

from lerner_lab_to_nwb.seiler_2024 import Seiler2024NWBConverter


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    start_date: str,
    subject_id: str,
    experiment_type: Literal["FP", "Opto"],
    experimental_group: Literal["DPR", "PR", "PS", "RR20"],
    stub_test: bool = False,
):
    """Convert a session to NWB."""

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    nwbfile_path = output_dir_path / f"{experiment_type}_{experimental_group}_{start_date}.nwb"
    source_data = {}
    conversion_options = {}

    # Add Behavior
    behavior_file_path = (
        data_dir_path
        / f"{experiment_type} Experiments"
        / "Behavior"
        / f"{experimental_group}"
        / f"{subject_id}"
        / f"{subject_id}"
    )
    source_data.update(
        dict(
            Behavior={
                "file_path": str(behavior_file_path),
                "start_date": start_date,
            }
        )
    )
    conversion_options.update(dict(Behavior={}))

    converter = Seiler2024NWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    datetime.datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("US/Eastern"))
    date = datetime.datetime.today()  # TODO: Get this from author
    metadata["NWBFile"]["session_start_time"] = date

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "seiler_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)
    metadata["Subject"]["subject_id"] = subject_id

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


if __name__ == "__main__":
    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/raw_data")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/conversion_nwb")
    experiment_type = "FP"
    experimental_group = "RR20"
    subject_id = "95.259"
    stub_test = False

    if output_dir_path.exists():
        shutil.rmtree(
            output_dir_path, ignore_errors=True
        )  # ignore errors due to MacOS race condition (https://github.com/python/cpython/issues/81441)

    # No-shock example session
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        subject_id=subject_id,
        start_date="04_09_19",
        experiment_type=experiment_type,
        experimental_group=experimental_group,
        stub_test=stub_test,
    )

    # Shock session
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        subject_id=subject_id,
        start_date="04_18_19",
        experiment_type=experiment_type,
        experimental_group=experimental_group,
        stub_test=stub_test,
    )
