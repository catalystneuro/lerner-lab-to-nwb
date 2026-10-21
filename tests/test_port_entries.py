from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pytest
from neuroconv.utils import dict_deep_update, load_dict_from_file
from pynwb import NWBFile
from pynwb.testing.mock.file import mock_NWBFile

import lerner_lab_to_nwb.seiler_2024 as seiler_2024
from lerner_lab_to_nwb.seiler_2024 import Seiler2024CSVBehaviorInterface
from lerner_lab_to_nwb.seiler_2024.medpcdatainterface import MedPCInterface

EDITABLE_METADATA_PATH = Path(seiler_2024.__file__).parent / "seiler_2024_metadata.yaml"


def medpc_run(*, start_time: str, durations: str) -> str:
    # FOOD_RI 60 RIGHT TTL writes port entries to G and port entry durations to E from separate inputs
    return (
        "Start Date: 11/02/18\n"
        "End Date: 11/02/18\n"
        "Subject: 64.205\n"
        "Box: 1\n"
        f"Start Time: {start_time}\n"
        "MSN: FOOD_RI 60 RIGHT TTL\n"
        "E:\n"
        f"     0:      {durations}\n"
        "G:\n"
        "     0:       10.000       20.000       30.000\n"
    )


@pytest.fixture
def medpc_file_path(tmp_path) -> Path:
    file_path = tmp_path / "64.205"
    file_path.write_text(
        "\n"
        + medpc_run(start_time="10:00:00", durations="0.500        1.000        0.250")
        + "\n"
        + medpc_run(start_time="11:00:00", durations="0.500        1.000")
    )
    return file_path


@pytest.fixture
def metadata() -> dict:
    metadata = load_dict_from_file(EDITABLE_METADATA_PATH)
    medpc_name_to_output_name = metadata["MedPC"]["msn_to_medpc_name_to_output_name"]["FOOD_RI 60 RIGHT TTL"]
    metadata["MedPC"]["medpc_name_to_info_dict"] = {
        medpc_name: {"name": output_name, "is_array": True}
        for medpc_name, output_name in medpc_name_to_output_name.items()
        if medpc_name in ("E", "G")
    }
    metadata["MedPC"]["Events"] = []
    return metadata


@pytest.fixture
def matched_interface(medpc_file_path) -> MedPCInterface:
    return MedPCInterface(
        file_path=medpc_file_path,
        session_conditions={"Start Date": "11/02/18", "Start Time": "10:00:00"},
        start_variable="Start Date",
        metadata_medpc_name_to_info_dict={"MSN": {"name": "MSN", "is_array": False}},
        verbose=False,
    )


@pytest.fixture
def mismatched_interface(medpc_file_path) -> MedPCInterface:
    return MedPCInterface(
        file_path=medpc_file_path,
        session_conditions={"Start Date": "11/02/18", "Start Time": "11:00:00"},
        start_variable="Start Date",
        metadata_medpc_name_to_info_dict={"MSN": {"name": "MSN", "is_array": False}},
        verbose=False,
    )


class TestMedPCInterface:
    def test_matched_durations_are_intervals(self, matched_interface, metadata):
        nwbfile = mock_NWBFile()
        matched_interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

        behavior_module = nwbfile.processing["behavior"]
        assert set(behavior_module.data_interfaces) == {"behavioral_epochs"}
        reward_port_intervals = behavior_module["behavioral_epochs"].interval_series["reward_port_intervals"]
        np.testing.assert_array_equal(reward_port_intervals.timestamps, np.array([10.0, 10.5, 20.0, 21.0, 30.0, 30.25]))
        np.testing.assert_array_equal(reward_port_intervals.data, np.array([1, -1, 1, -1, 1, -1]))

    def test_mismatched_durations_keep_every_port_entry(self, mismatched_interface, metadata):
        nwbfile = mock_NWBFile()
        mismatched_interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

        behavior_module = nwbfile.processing["behavior"]
        assert set(behavior_module.data_interfaces) == {"reward_port_entry_times"}
        reward_port_entry_times = behavior_module["reward_port_entry_times"]
        assert reward_port_entry_times.description == "Reward port entry times"
        np.testing.assert_array_equal(reward_port_entry_times.timestamps, np.array([10.0, 20.0, 30.0]))

    def test_mismatched_ttl_onsets_keep_every_ttl_onset(self, matched_interface, metadata):
        # E and G agree, but the photometry TTLs hold one more port entry than G
        matched_interface.set_aligned_timestamps(
            dict(
                reward_port_entry_times=np.array([5.0, 10.1, 20.1, 30.1]),
                duration_of_port_entry=np.array([0.5, 1.0, 0.25]),
            )
        )
        matched_interface.source_data["aligned_timestamp_names"] = ["reward_port_entry_times", "duration_of_port_entry"]
        nwbfile = mock_NWBFile()
        matched_interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

        behavior_module = nwbfile.processing["behavior"]
        assert set(behavior_module.data_interfaces) == {"reward_port_entry_times"}
        np.testing.assert_array_equal(
            behavior_module["reward_port_entry_times"].timestamps, np.array([5.0, 10.1, 20.1, 30.1])
        )


@pytest.fixture
def csv_file_path(tmp_path) -> Path:
    file_path = tmp_path / "64.205_11-02-18.csv"
    file_path.write_text(
        ",Start Date,End Date,Subject,Experiment,Group,Box,Start Time,End Time,MSN,"
        "LeftNoseTs,LeftRewardTs,RightNoseTs,RightRewardTs,DurationOfPE,portEntryTs\n"
        "0,11/02/18,11/02/18,64.205,,,1,10:00:00,11:00:00,FOOD_RI 60 RIGHT TTL,,,5.0,,0.5,10.0\n"
        "1,,,,,,,,,,,,,,1.0,20.0\n"
        "2,,,,,,,,,,,,,,,30.0\n"
    )
    return file_path


@pytest.fixture
def csv_nwbfile(csv_file_path) -> NWBFile:
    interface = Seiler2024CSVBehaviorInterface(file_path=str(csv_file_path), verbose=False)
    metadata = dict_deep_update(interface.get_metadata(), load_dict_from_file(EDITABLE_METADATA_PATH))
    metadata["NWBFile"]["session_id"] = "test"
    nwbfile = NWBFile(
        session_description="test",
        identifier="test",
        session_start_time=datetime(2018, 11, 2, 10, 0, 0, tzinfo=ZoneInfo("America/Chicago")),
    )
    interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)
    return nwbfile


class TestSeiler2024CSVBehaviorInterface:
    def test_mismatched_durations_keep_every_port_entry(self, csv_nwbfile):
        behavior_module = csv_nwbfile.processing["behavior"]
        assert "behavioral_epochs" not in behavior_module.data_interfaces
        np.testing.assert_array_equal(
            behavior_module["reward_port_entry_times"].timestamps, np.array([10.0, 20.0, 30.0])
        )
