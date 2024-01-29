"""Primary script to run to convert example sessions using the NWBConverter."""
from pathlib import Path
from typing import Union, Literal
import datetime
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update

from lerner_lab_to_nwb.seiler_2024 import Seiler2024NWBConverter


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    session_id: str,
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

    nwbfile_path = output_dir_path / f"{experiment_type}_{experimental_group}_{session_id}.nwb"

    source_data = {}
    conversion_options = {}

    # Add Behavior
    source_data.update(dict(Behavior={}))
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
    metadata["Subject"]["subject_id"] = session_id.split("_")[0]

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


if __name__ == "__main__":
    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/raw_data")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/conversion_nwb")
    experiment_type = "FP"
    experimental_group = "RR20"
    session_id = "95.259_04-09-19"
    stub_test = False

    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        session_id=session_id,
        experiment_type=experiment_type,
        experimental_group=experimental_group,
        stub_test=stub_test,
    )
