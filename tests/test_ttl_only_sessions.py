from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pytest
from neuroconv.utils import load_dict_from_file
from pynwb.testing.mock.file import mock_NWBFile
from tdt import StructType

import lerner_lab_to_nwb.seiler_2024.seiler_2024nwbconverter as seiler_2024nwbconverter
import lerner_lab_to_nwb.seiler_2024.seiler_2024ttlbehaviorinterface as seiler_2024ttlbehaviorinterface
from lerner_lab_to_nwb.seiler_2024 import Seiler2024NWBConverter, Seiler2024TTLBehaviorInterface
from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_dataset import (
    fp_to_nwb,
    get_no_port_entry_duration_sessions,
)

METADATA_PATH = Path(__file__).parent.parent / "src" / "lerner_lab_to_nwb" / "seiler_2024" / "seiler_2024_metadata.yaml"
FOLDER_NAME = "Photo_89_247-190308-095258"
# 09:53:22 in Chicago on 03/08/19, the start of 89.247's footshock probe recording
BLOCK_START_TIMESTAMP = datetime(2019, 3, 8, 9, 53, 22, tzinfo=ZoneInfo("America/Chicago")).timestamp()
# A small version of the TTLs of 89.247's footshock probe
TTL_NAME_TO_ONSETS = {
    "Sock": [30.0, 90.0],
    "LNRW": [20.0, 80.0],
    "LNnR": [10.0, 30.0, 90.0],
    "RNPS": [50.0],
    "PrtR": [21.0, 81.0],
    "PrtN": [40.0],
}


def tdt_block() -> StructType:
    block = StructType()
    block.info = StructType()
    # tdt gives the block start in the local time of the computer running the conversion
    block.info.start_date = datetime.fromtimestamp(BLOCK_START_TIMESTAMP)
    block.epocs = StructType()
    for ttl_name, onsets in TTL_NAME_TO_ONSETS.items():
        block.epocs[ttl_name] = StructType()
        block.epocs[ttl_name].onset = np.array(onsets)
    return block


@pytest.fixture
def fake_read_block(monkeypatch):
    def read_block(*args, **kwargs):
        return tdt_block()

    monkeypatch.setattr(seiler_2024nwbconverter, "read_block", read_block)
    monkeypatch.setattr(seiler_2024ttlbehaviorinterface, "read_block", read_block)


def medpc_run(*, subject: str, box: str, start_date: str, start_time: str, msn: str, left_nose_poke_time: float) -> str:
    return (
        f"Start Date: {start_date}\n"
        f"End Date: {start_date}\n"
        f"Subject: {subject}\n"
        "Experiment: \n"
        "Group: \n"
        f"Box: {box}\n"
        f"Start Time: {start_time}\n"
        "End Time: 11:07:20\n"
        f"MSN: {msn}\n"
        "A:\n"
        f"     0:      {left_nose_poke_time:.3f}\n"
        "G:\n"
        "     0:      16.500\n"
        "E:\n"
        "     0:       0.400\n"
    )


@pytest.fixture
def data_dir_path(tmp_path) -> Path:
    fp_path = tmp_path / "FP Experiments"
    for long_name in ["Delayed Punishment Resistant", "Punishment Resistant", "Punishment Sensitive", "RR20"]:
        (fp_path / "Photometry" / long_name).mkdir(parents=True)
    for experimental_group in ["DPR", "PR", "PS", "RR20"]:
        (fp_path / "Behavior" / experimental_group).mkdir(parents=True)
    (fp_path / "Photometry" / "Punishment Resistant" / "Early RI60" / FOLDER_NAME).mkdir(parents=True)
    (fp_path / "Behavior" / "PR" / "89.247").mkdir()
    raw_files_by_date_path = fp_path / "Behavior" / "MEDPC_RawFilesbyDate"
    raw_files_by_date_path.mkdir()
    # The only MedPC run of 89.247 that day, a probe test that started after the recording ended
    probe_test = medpc_run(
        subject="89.247",
        box="1",
        start_date="03/08/19",
        start_time="10:59:10",
        msn="Probe Test Habit Training TTL",
        left_nose_poke_time=15.95,
    )
    (raw_files_by_date_path / "2019-03-08 89.247probe").write_text("\n" + probe_test)
    return tmp_path


class TestFpToNwb:
    def test_shock_probe_photometry_is_converted_from_its_ttls(self, data_dir_path, tmp_path):
        session_to_nwb_args_per_session = fp_to_nwb(
            data_dir_path=data_dir_path, output_dir_path=tmp_path / "nwb", start_variable="Start Date", verbose=False
        )
        photometry_sessions = [
            args for args in session_to_nwb_args_per_session if "fiber_photometry_folder_path" in args
        ]
        assert len(photometry_sessions) == 1
        photometry_session = photometry_sessions[0]
        assert photometry_session["fiber_photometry_folder_path"].name == FOLDER_NAME
        assert photometry_session["behavior_file_path"] is None
        assert photometry_session["ttl_msn"] == "Footshock Degradation Left"
        assert photometry_session["session_conditions"] == {"Start Date": "03/08/19", "Start Time": "09:53:22"}
        assert photometry_session["has_demodulated_commanded_voltages"] is False

    def test_probe_test_is_converted_as_behavior_only(self, data_dir_path, tmp_path):
        session_to_nwb_args_per_session = fp_to_nwb(
            data_dir_path=data_dir_path, output_dir_path=tmp_path / "nwb", start_variable="Start Date", verbose=False
        )
        behavior_sessions = [
            args for args in session_to_nwb_args_per_session if "fiber_photometry_folder_path" not in args
        ]
        assert len(behavior_sessions) == 1
        probe_test = behavior_sessions[0]
        assert probe_test["subject_id"] == "89.247"
        assert probe_test["behavior_file_path"].name == "2019-03-08 89.247probe"
        assert probe_test["session_conditions"] == {
            "Start Date": "03/08/19",
            "Start Time": "10:59:10",
            "Subject": "89.247",
        }

    def test_ttl_only_session_has_no_port_entry_durations_to_read(self, data_dir_path, tmp_path):
        session_to_nwb_args_per_session = fp_to_nwb(
            data_dir_path=data_dir_path, output_dir_path=tmp_path / "nwb", start_variable="Start Date", verbose=False
        )
        no_port_entry_duration_sessions = get_no_port_entry_duration_sessions(
            port_entry_file_path=tmp_path / "sessions_without_port_entry_durations.yaml",
            session_to_nwb_args_per_session=session_to_nwb_args_per_session,
        )
        # the session without a behavior file is skipped, and the probe test has its port entry duration
        assert no_port_entry_duration_sessions == set()


class TestTTLBehavior:
    @pytest.fixture
    def metadata(self) -> dict:
        metadata = load_dict_from_file(METADATA_PATH)
        metadata["TTLBehavior"] = {"MSN": "Footshock Degradation Left"}
        metadata["NWBFile"]["session_id"] = "FP_PR_ShockProbe_2019-03-08T09-53-22"
        return metadata

    @pytest.fixture
    def converter(self) -> Seiler2024NWBConverter:
        return Seiler2024NWBConverter(
            source_data=dict(
                FiberPhotometry={"folder_path": FOLDER_NAME, "verbose": False},
                TTLBehavior={"folder_path": FOLDER_NAME, "msn": "Footshock Degradation Left", "verbose": False},
            ),
            verbose=False,
        )

    def test_session_starts_at_the_block_start(self, fake_read_block):
        interface = Seiler2024TTLBehaviorInterface(folder_path=FOLDER_NAME, msn="Footshock Degradation Left")
        assert interface.get_metadata()["TTLBehavior"] == {
            "MSN": "Footshock Degradation Left",
            "start_date": "03/08/19",
            "start_time": "09:53:22",
        }

    def test_all_ttls_are_kept(self, fake_read_block, converter, metadata):
        converter.temporally_align_data_interfaces(
            metadata=metadata, conversion_options={"FiberPhotometry": {"flip_ttls_lr": False}}
        )
        timestamps = converter.data_interface_objects["TTLBehavior"].get_timestamps()
        assert sorted(timestamps) == [
            "footshock_times",
            "left_nose_poke_times",
            "left_reward_times",
            "reward_port_entry_times",
            "right_nose_poke_times",
        ]
        np.testing.assert_array_equal(timestamps["footshock_times"], [30.0, 90.0])
        np.testing.assert_array_equal(timestamps["left_reward_times"], [20.0, 80.0])
        # unrewarded and rewarded left nose pokes
        np.testing.assert_array_equal(timestamps["left_nose_poke_times"], [10.0, 20.0, 30.0, 80.0, 90.0])
        np.testing.assert_array_equal(timestamps["right_nose_poke_times"], [50.0])
        # port entries after a reward and after no reward
        np.testing.assert_array_equal(timestamps["reward_port_entry_times"], [21.0, 40.0, 81.0])

    def test_footshocks_need_a_shock_probe_session_id(self, fake_read_block, converter, metadata):
        metadata["NWBFile"]["session_id"] = "FP_PR_2019-03-08T09-53-22"
        converter.temporally_align_data_interfaces(
            metadata=metadata, conversion_options={"FiberPhotometry": {"flip_ttls_lr": False}}
        )
        assert "footshock_times" not in converter.data_interface_objects["TTLBehavior"].get_timestamps()

    def test_ttls_are_written_as_events(self, fake_read_block, converter, metadata):
        converter.temporally_align_data_interfaces(
            metadata=metadata, conversion_options={"FiberPhotometry": {"flip_ttls_lr": False}}
        )
        nwbfile = mock_NWBFile()
        converter.data_interface_objects["TTLBehavior"].add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)
        behavior_module = nwbfile.processing["behavior"]
        assert "MSN = Footshock Degradation Left" in behavior_module.description
        assert len(behavior_module["footshock_times"].timestamps) == 2
        assert behavior_module["footshock_times"].description == "Footshock times"
        assert behavior_module["reward_port_entry_times"].description == "Reward port entry times"
        assert len(behavior_module["left_nose_poke_times"].timestamps) == 5
