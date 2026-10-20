from pathlib import Path

import pytest

from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_dataset import opto_to_nwb

TREATMENT_FOLDERS = [
    "DLS Excitatory/ChR2",
    "DLS Excitatory/EYFP",
    "DLS Excitatory/Scrambled",
    "DMS Excitatory/ChR2",
    "DMS Excitatory/EYFP",
    "DMS Excitatory/Scrambled",
    "DMS Inhibitory/Group 1/Halo",
    "DMS Inhibitory/Group 1/EYFP",
    "DMS Inhibitory/Group 1/Scrambled",
    "DMS Inhibitory/Group 2/NpHr",
    "DMS Inhibitory/Group 2/EYFP",
    "DMS Inhibitory/Group 2/Scrambled",
]


def medpc_run(*, subject: str, box: str) -> str:
    return (
        "Start Date: 09/23/20\n"
        f"Subject: {subject}\n"
        f"Box: {box}\n"
        "Start Time: 12:41:13\n"
        "MSN: FR1_BOTH_WStim\n"
    )


@pytest.fixture
def data_dir_path(tmp_path) -> Path:
    opto_path = tmp_path / "Opto Experiments"
    for treatment_folder in TREATMENT_FOLDERS:
        (opto_path / treatment_folder).mkdir(parents=True)
    csv_folder_path = opto_path / "DLS Excitatory" / "ChR2" / "290.407"
    csv_folder_path.mkdir()
    (csv_folder_path / "290.407_09-23-20.csv").write_text(
        ",Start Date,End Date,Subject,Experiment,Group,Box,Start Time,End Time,MSN\n"
        "0,09/23/20,09/23/20,290.407,,,2,12:41:13,13:41:13,FR1_BOTH_WStim\n"
    )
    (opto_path / "DLS Excitatory" / "2020-09-23").write_text(
        "\n" + medpc_run(subject="290.407", box="2") + "\n" + medpc_run(subject="291.407", box="1")
    )
    return tmp_path


class TestOptoToNwb:
    def test_290_and_291_first_days_are_dms_excitatory(self, data_dir_path, tmp_path):
        session_to_nwb_args_per_session = opto_to_nwb(
            data_dir_path=data_dir_path,
            output_dir_path=tmp_path / "nwb",
            start_variable="Start Date",
            verbose=False,
        )
        labels = sorted(
            (
                session_to_nwb_args["subject_id"],
                session_to_nwb_args["experimental_group"],
                session_to_nwb_args["optogenetic_treatment"],
            )
            for session_to_nwb_args in session_to_nwb_args_per_session
        )
        assert labels == [("290.407", "DMS-Excitatory", "ChR2Scrambled"), ("291.407", "DMS-Excitatory", "EYFP")]
