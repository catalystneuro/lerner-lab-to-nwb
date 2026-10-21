from pathlib import Path

import pytest
from pynwb.testing.mock.file import mock_NWBFile
from neuroconv.utils import load_dict_from_file

import lerner_lab_to_nwb.seiler_2024 as seiler_2024
from lerner_lab_to_nwb.seiler_2024.medpcdatainterface import MedPCInterface


@pytest.fixture
def medpc_file_path(tmp_path) -> Path:
    # An RR20Right run that kept its counters but lost its nose poke and reward timestamps
    file_path = tmp_path / "96.259"
    file_path.write_text(
        "\n"
        "Start Date: 04/30/19\n"
        "End Date: 04/30/19\n"
        "Subject: 96.259\n"
        "Box: 1\n"
        "Start Time: 11:47:14\n"
        "End Time: 12:47:17\n"
        "MSN: RR20Right\n"
        "O:      48.000\n"
        "P:       3.000\n"
        "R:     993.000\n"
        "S:       0.000\n"
        "W:       5.000 (left nosepokes)\n"
        "A:\n"
        "B:\n"
        "C:\n"
        "D:\n"
        "     0:        0.000        0.000\n"
        "E:\n"
        "     0:        0.500        1.000        0.250\n"
        "G:\n"
        "     0:       10.000       20.000       30.000\n"
        "H:\n"
    )
    return file_path


@pytest.fixture
def interface(medpc_file_path) -> MedPCInterface:
    return MedPCInterface(
        file_path=medpc_file_path,
        session_conditions={"Start Date": "04/30/19", "Start Time": "11:47:14"},
        start_variable="Start Date",
        metadata_medpc_name_to_info_dict={"MSN": {"name": "MSN", "is_array": False}},
        verbose=False,
    )


def test_counters_are_stored_without_timestamps(interface):
    metadata = load_dict_from_file(Path(seiler_2024.__file__).parent / "seiler_2024_metadata.yaml")
    medpc_name_to_output_name = metadata["MedPC"]["msn_to_medpc_name_to_output_name"]["RR20Right"]
    metadata["MedPC"]["medpc_name_to_info_dict"] = {
        medpc_name: {"name": output_name, "is_array": True} for medpc_name, output_name in medpc_name_to_output_name.items()
    }
    metadata["MedPC"]["medpc_name_to_counter_name"] = metadata["MedPC"]["msn_to_medpc_name_to_counter_name"]["RR20Right"]
    nwbfile = mock_NWBFile()
    interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

    behavior_module = nwbfile.processing["behavior"]
    assert set(behavior_module.data_interfaces) == {"behavioral_epochs", "session_counts"}
    assert behavior_module["session_counts"].to_dataframe().to_dict(orient="records") == [
        dict(
            right_rewards=48,
            reward_port_entries=3,
            right_nose_pokes=993,
            left_rewards=0,
            left_nose_pokes=5,
        )
    ]
