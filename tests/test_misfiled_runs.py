from pathlib import Path

import numpy as np
import pytest

from lerner_lab_to_nwb.seiler_2024.medpc_helpers import read_medpc_file
from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_dataset import opto_to_nwb, subject_field_refers_to_subject

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


def medpc_run(*, subject: str, box: str, start_date: str, start_time: str, msn: str, port_entry_time: float) -> str:
    return (
        f"Start Date: {start_date}\n"
        f"End Date: {start_date}\n"
        f"Subject: {subject}\n"
        "Experiment: \n"
        "Group: \n"
        f"Box: {box}\n"
        f"Start Time: {start_time}\n"
        "End Time: 13:23:54\n"
        f"MSN: {msn}\n"
        "G:\n"
        f"     0:      {port_entry_time:.3f}        0.000\n"
    )


@pytest.fixture
def data_dir_path(tmp_path) -> Path:
    opto_path = tmp_path / "Opto Experiments"
    for treatment_folder in TREATMENT_FOLDERS:
        (opto_path / treatment_folder).mkdir(parents=True)
    runs = [
        # Another mouse's run listed before 344.400's own run at the same start time
        medpc_run(
            subject="271",
            box="2",
            start_date="07/30/20",
            start_time="12:23:54",
            msn="Probe Test Habit Training TTL",
            port_entry_time=10.0,
        ),
        medpc_run(
            subject="344",
            box="1",
            start_date="07/30/20",
            start_time="12:23:54",
            msn="RI 60 LEFT_STIM",
            port_entry_time=20.0,
        ),
        # A third mouse's run alone on another day
        medpc_run(
            subject="333.393",
            box="6",
            start_date="07/31/20",
            start_time="12:03:31",
            msn="RI 60 LEFT_STIM",
            port_entry_time=30.0,
        ),
    ]
    (opto_path / "DLS Excitatory" / "EYFP" / "344.400").write_text("\n" + "\n".join(runs))
    return tmp_path


class TestSubjectFieldRefersToSubject:
    @pytest.mark.parametrize(
        "subject_field, subject_id",
        [
            ("344.400", "344.400"),
            ("", "344.400"),
            ("344", "344.400"),
            ("28", "028.392"),
            ("121.28", "121.280"),
            ("DAT-127", "127.280"),
            ("391", "249.391"),
        ],
    )
    def test_refers_to_subject(self, subject_field, subject_id):
        assert subject_field_refers_to_subject(subject_field=subject_field, subject_id=subject_id)

    @pytest.mark.parametrize(
        "subject_field, subject_id",
        [("271", "344.400"), ("333", "346.394"), ("321.415", "322.415"), ("480", "479")],
    )
    def test_refers_to_other_subject(self, subject_field, subject_id):
        assert not subject_field_refers_to_subject(subject_field=subject_field, subject_id=subject_id)


class TestOptoToNwb:
    def test_subject_file_keeps_only_the_subjects_runs(self, data_dir_path, tmp_path):
        session_to_nwb_args_per_session = opto_to_nwb(
            data_dir_path=data_dir_path,
            output_dir_path=tmp_path / "nwb",
            start_variable="Start Date",
            verbose=False,
        )
        assert len(session_to_nwb_args_per_session) == 1
        (session_to_nwb_args,) = session_to_nwb_args_per_session
        session_dict = read_medpc_file(
            file_path=session_to_nwb_args["behavior_file_path"],
            medpc_name_to_info_dict={"G": {"name": "port_entry_times", "is_array": True}},
            session_conditions=session_to_nwb_args["session_conditions"],
            start_variable="Start Date",
        )
        np.testing.assert_array_equal(session_dict["port_entry_times"], np.array([20.0]))
