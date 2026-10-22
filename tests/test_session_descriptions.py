from pathlib import Path

import pandas as pd
import pytest
from pynwb import NWBHDF5IO

from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_session import session_to_nwb


@pytest.fixture
def data_dir_path(tmp_path) -> Path:
    data_dir_path = tmp_path / "data"
    data_dir_path.mkdir()
    pd.DataFrame(
        {
            "Mouse ID": ["75.214"],
            "Sex": ["Female"],
            "Surgical Manipulation": ["Fiber Photometry"],
            "Treatment": [None],
            "Experiment": ["Fiber Photometry"],
            "Hemisphere with DMS": ["Left"],
            "Behavior": ["DPR"],
            "Punishment Group": ["Sensitive"],
        }
    ).to_excel(data_dir_path / "MouseDemographicsCorrected.xlsx", sheet_name="Mouse Demographics", index=False)
    return data_dir_path


@pytest.fixture
def behavior_file_path(data_dir_path) -> Path:
    # A behavior-only day on a program that sends TTLs to the photometry rig
    file_path = data_dir_path / "75.214"
    file_path.write_text(
        "\n"
        "Start Date: 10/29/18\n"
        "End Date: 10/29/18\n"
        "Subject: 75.214\n"
        "Box: 1\n"
        "Start Time: 10:30:13\n"
        "End Time: 11:30:16\n"
        "MSN: FOOD_FR1 TTL Left\n"
        "O:       0.000\n"
        "P:       2.000\n"
        "R:       0.000\n"
        "S:       1.000\n"
        "W:       2.000\n"
        "A:\n"
        "     0:       10.000       20.000\n"
        "B:\n"
        "     0:       10.000\n"
        "C:\n"
        "D:\n"
        "E:\n"
        "     0:        0.500        1.000\n"
        "G:\n"
        "     0:       12.000       30.000\n"
    )
    return file_path


class TestSessionToNwb:
    def test_behavior_only_session_description(self, data_dir_path, behavior_file_path, tmp_path):
        output_dir_path = tmp_path / "nwbfiles"
        session_to_nwb(
            data_dir_path=data_dir_path,
            output_dir_path=output_dir_path,
            behavior_file_path=behavior_file_path,
            subject_id="75.214",
            session_conditions={"Start Date": "10/29/18", "Start Time": "10:30:13"},
            start_variable="Start Date",
            experiment_type="FP",
            experimental_group="DPR",
            verbose=False,
        )
        nwbfile_path = output_dir_path / "sub-75.214_ses-FP_DPR_2018-10-29T10-30-13.nwb"
        with NWBHDF5IO(nwbfile_path, mode="r") as io:
            nwbfile = io.read()
            assert nwbfile.session_description == "FR1 Training, rewards delivered on left nose pokes"
