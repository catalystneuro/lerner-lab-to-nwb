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


def medpc_run(subject: str, box: str) -> str:
    return (
        "Start Date: 09/29/20\n"
        "End Date: 09/29/20\n"
        f"Subject: {subject}\n"
        "Experiment: \n"
        "Group: \n"
        f"Box: {box}\n"
        "Start Time: 11:36:53\n"
        "End Time: 12:36:45\n"
        "MSN: Footshock Degradation Left\n"
    )


@pytest.fixture
def data_dir_path(tmp_path) -> Path:
    opto_path = tmp_path / "Opto Experiments"
    for treatment_folder in TREATMENT_FOLDERS:
        (opto_path / treatment_folder).mkdir(parents=True)

    # 300.405's run exported to its own folder as a CSV
    subject_folder_path = opto_path / "DLS Excitatory" / "Scrambled" / "300_405"
    subject_folder_path.mkdir()
    (subject_folder_path / "300.405_09-29-20.csv").write_text(
        ",Start Date,End Date,Subject,Experiment,Group,Box,Start Time,End Time,MSN\n"
        "0,09/29/20,09/29/20,300.405,,,5,11:36:53,12:36:45,Footshock Degradation Left\n"
    )

    # The same run and another mouse's run in the date-organized MED-PC file
    (opto_path / "DLS Excitatory" / "2020-09-29").write_text(
        "\n" + medpc_run(subject="418.404", box="1") + "\n" + medpc_run(subject="300.405", box="5")
    )
    return tmp_path


class TestOptoToNwb:
    def test_by_date_run_already_in_subject_folder_is_skipped(self, data_dir_path, tmp_path):
        session_to_nwb_args_per_session = opto_to_nwb(
            data_dir_path=data_dir_path,
            output_dir_path=tmp_path / "nwb",
            start_variable="Start Date",
            verbose=False,
        )
        subject_and_treatment = sorted(
            (session_to_nwb_args["subject_id"], session_to_nwb_args["optogenetic_treatment"])
            for session_to_nwb_args in session_to_nwb_args_per_session
        )
        assert subject_and_treatment == [("300.405", "ChR2Scrambled"), ("418.404", "Unknown")]
