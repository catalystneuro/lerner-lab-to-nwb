from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pytest
from neuroconv.utils import dict_deep_update, load_dict_from_file
from pynwb import NWBFile

import lerner_lab_to_nwb.seiler_2024 as seiler_2024
from lerner_lab_to_nwb.seiler_2024 import Seiler2024CSVBehaviorInterface


@pytest.fixture
def csv_file_path(tmp_path) -> Path:
    file_path = tmp_path / "300.405_09-29-20.csv"
    file_path.write_text(
        ",Start Date,End Date,Subject,Experiment,Group,Box,Start Time,End Time,MSN,"
        "LeftNoseTs,LeftRewardTs,RightNoseTs,RightRewardTs,DurationOfPE,portEntryTs,H\n"
        # The left program writes left rewards to MedPC array D, which is exported as RightRewardTs
        "0,09/29/20,09/29/20,300.405,,,5,11:36:53,12:36:45,Footshock Degradation Left,15.2,,0.85,15.2,1.0,52.2,116.3\n"
        "1,,,,,,,,,,31.65,,14.2,31.65,2.0,90.5,160.6\n"
        "2,,,,,,,,,,43.0,,,43.0,2.0,120.0,0.0\n"
    )
    return file_path


@pytest.fixture
def metadata(csv_file_path) -> dict:
    interface = Seiler2024CSVBehaviorInterface(file_path=str(csv_file_path), verbose=False)
    editable_metadata_path = Path(seiler_2024.__file__).parent / "seiler_2024_metadata.yaml"
    metadata = dict_deep_update(interface.get_metadata(), load_dict_from_file(editable_metadata_path))
    metadata["NWBFile"]["session_id"] = "test"
    return metadata


@pytest.fixture
def nwbfile(csv_file_path, metadata) -> NWBFile:
    interface = Seiler2024CSVBehaviorInterface(file_path=str(csv_file_path), verbose=False)
    nwbfile = NWBFile(
        session_description="test",
        identifier="test",
        session_start_time=datetime(2020, 9, 29, 11, 36, 53, tzinfo=ZoneInfo("America/Chicago")),
    )
    interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)
    return nwbfile


class TestSeiler2024CSVBehaviorInterface:
    def test_footshock_times(self, nwbfile):
        footshock_times = nwbfile.processing["behavior"]["footshock_times"].timestamps
        np.testing.assert_array_equal(footshock_times, np.array([116.3, 160.6]))

    def test_left_footshock_rewards_are_left_rewards(self, nwbfile):
        left_reward_times = nwbfile.processing["behavior"]["left_reward_times"].timestamps
        np.testing.assert_array_equal(left_reward_times, np.array([15.2, 31.65, 43.0]))
        assert "right_reward_times" not in nwbfile.processing["behavior"].data_interfaces
