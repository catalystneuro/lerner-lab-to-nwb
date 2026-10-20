from pathlib import Path

import numpy as np
import pytest
from neuroconv.utils import load_dict_from_file

import lerner_lab_to_nwb.seiler_2024 as seiler_2024
from lerner_lab_to_nwb.seiler_2024.medpc_helpers import read_medpc_file


@pytest.fixture
def medpc_file_path(tmp_path) -> Path:
    # The left program writes left rewards to array D and never writes array B
    file_path = tmp_path / "300.405"
    file_path.write_text(
        "\n"
        "Start Date: 09/29/20\n"
        "End Date: 09/29/20\n"
        "Subject: 300.405\n"
        "Experiment: \n"
        "Group: \n"
        "Box: 5\n"
        "Start Time: 11:36:53\n"
        "End Time: 12:36:45\n"
        "MSN: Footshock Degradation Left\n"
        "A:\n"
        "     0:       15.200       31.650       43.000\n"
        "B:\n"
        "D:\n"
        "     0:       15.200       31.650       43.000\n"
    )
    return file_path


def test_left_footshock_rewards_are_left_rewards(medpc_file_path):
    metadata = load_dict_from_file(Path(seiler_2024.__file__).parent / "seiler_2024_metadata.yaml")
    medpc_name_to_output_name = metadata["MedPC"]["msn_to_medpc_name_to_output_name"]["Footshock Degradation Left"]
    session_dict = read_medpc_file(
        file_path=medpc_file_path,
        medpc_name_to_info_dict={
            medpc_name: {"name": medpc_name_to_output_name[medpc_name], "is_array": True} for medpc_name in "ABD"
        },
        session_conditions={"Start Date": "09/29/20", "Start Time": "11:36:53"},
        start_variable="Start Date",
    )
    np.testing.assert_array_equal(session_dict["left_reward_times"], np.array([15.2, 31.65, 43.0]))
    np.testing.assert_array_equal(session_dict["right_reward_times"], np.array([]))
