from pathlib import Path

import numpy as np
import pytest

from lerner_lab_to_nwb.seiler_2024.medpc_helpers import read_medpc_file
from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_dataset import (
    UNLISTED_RUN_TO_SUBJECT_ID,
    add_unlisted_runs,
    opto_to_nwb,
    reassign_misfiled_runs,
    subject_field_refers_to_subject,
)

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
        # A run alone at its start time whose Subject field names another mouse
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
    def test_subject_file_reads_one_run_per_start_time(self, data_dir_path, tmp_path):
        session_to_nwb_args_per_session = opto_to_nwb(
            data_dir_path=data_dir_path,
            output_dir_path=tmp_path / "nwb",
            start_variable="Start Date",
            verbose=False,
        )
        start_date_to_port_entry_times = {}
        for session_to_nwb_args in session_to_nwb_args_per_session:
            session_dict = read_medpc_file(
                file_path=session_to_nwb_args["behavior_file_path"],
                medpc_name_to_info_dict={"G": {"name": "port_entry_times", "is_array": True}},
                session_conditions=session_to_nwb_args["session_conditions"],
                start_variable="Start Date",
            )
            start_date_to_port_entry_times[session_to_nwb_args["session_conditions"]["Start Date"]] = session_dict[
                "port_entry_times"
            ]
        assert sorted(start_date_to_port_entry_times) == ["07/30/20", "07/31/20"]
        # the file's mouse's own run, not the other mouse's run listed first at the same start time
        np.testing.assert_array_equal(start_date_to_port_entry_times["07/30/20"], np.array([20.0]))
        # a run alone at its start time is kept whatever its Subject field says
        np.testing.assert_array_equal(start_date_to_port_entry_times["07/31/20"], np.array([30.0]))


class TestReassignMisfiledRuns:
    def test_run_is_assigned_to_the_mouse_it_belongs_to(self):
        # 123.280's run on 07/18/19 is saved in 113.283's file
        misfiled_run = dict(
            behavior_file_path=Path("FP Experiments/Behavior/PS/113.283/113.283"),
            subject_id="113.283",
            session_conditions={"Start Date": "07/18/19", "Start Time": "12:36:46", "Box": "1"},
            experiment_type="FP",
            experimental_group="PS",
        )
        own_run = dict(
            behavior_file_path=Path("FP Experiments/Behavior/PS/113.283/113.283"),
            subject_id="113.283",
            session_conditions={"Start Date": "07/18/19", "Start Time": "12:01:24", "Box": "4"},
            experiment_type="FP",
            experimental_group="PS",
        )
        other_mouse_run = dict(
            behavior_file_path=Path("Opto Experiments/DMS Excitatory/EYFP/123.280"),
            subject_id="123.280",
            session_conditions={"Start Date": "07/17/19", "Start Time": "11:33:25", "Box": "1"},
            experiment_type="Opto",
            experimental_group="DMS-Excitatory",
            optogenetic_treatment="EYFP",
        )
        session_to_nwb_args_per_session = reassign_misfiled_runs([misfiled_run, own_run, other_mouse_run])
        assert session_to_nwb_args_per_session == [
            dict(
                behavior_file_path=Path("FP Experiments/Behavior/PS/113.283/113.283"),
                subject_id="123.280",
                session_conditions={"Start Date": "07/18/19", "Start Time": "12:36:46", "Box": "1"},
                experiment_type="Opto",
                experimental_group="DMS-Excitatory",
                optogenetic_treatment="EYFP",
            ),
            own_run,
            other_mouse_run,
        ]

    def test_run_in_a_file_named_for_an_unlisted_subject(self):
        # 244.465's run on 10/27/21 is saved in a file named for 244.464, which is not in the demographics sheet
        misfiled_run = dict(
            behavior_file_path=Path("Opto Experiments/DMS Inhibitory/Group 2/EYFP/2021-10-27_244.464"),
            subject_id="244.464",
            session_conditions={"Start Date": "10/27/21", "Start Time": "11:15:55", "Box": "3"},
            experiment_type="Opto",
            experimental_group="DMS-Inhibitory",
            optogenetic_treatment="EYFP",
        )
        own_session = dict(
            behavior_file_path=Path("Opto Experiments/DMS Inhibitory/Group 2/EYFP/2021-10-26_244.465"),
            subject_id="244.465",
            session_conditions={"Start Date": "10/26/21", "Start Time": "11:29:13", "Box": "3"},
            experiment_type="Opto",
            experimental_group="DMS-Inhibitory",
            optogenetic_treatment="EYFP",
        )
        session_to_nwb_args_per_session = reassign_misfiled_runs([misfiled_run, own_session])
        assert session_to_nwb_args_per_session == [
            dict(
                behavior_file_path=Path("Opto Experiments/DMS Inhibitory/Group 2/EYFP/2021-10-27_244.464"),
                subject_id="244.465",
                session_conditions={"Start Date": "10/27/21", "Start Time": "11:15:55", "Box": "3"},
                experiment_type="Opto",
                experimental_group="DMS-Inhibitory",
                optogenetic_treatment="EYFP",
            ),
            own_session,
        ]

    def test_run_is_assigned_to_a_mouse_in_another_treatment(self):
        # 480's (EYFP) run at 09:43:23 on 06/13/19 is saved in 479's (ChR2) file, next to 479's own run that day
        misfiled_run = dict(
            behavior_file_path=Path("Opto Experiments/DMS Excitatory/ChR2/479"),
            subject_id="479",
            session_conditions={"Start Date": "06/13/19", "Start Time": "09:43:23", "Box": "2"},
            experiment_type="Opto",
            experimental_group="DMS-Excitatory",
            optogenetic_treatment="ChR2",
        )
        own_run = dict(
            behavior_file_path=Path("Opto Experiments/DMS Excitatory/ChR2/479"),
            subject_id="479",
            session_conditions={"Start Date": "06/13/19", "Start Time": "12:54:17", "Box": "4"},
            experiment_type="Opto",
            experimental_group="DMS-Excitatory",
            optogenetic_treatment="ChR2",
        )
        other_mouse_run = dict(
            behavior_file_path=Path("Opto Experiments/DMS Excitatory/EYFP/480"),
            subject_id="480",
            session_conditions={"Start Date": "06/13/19", "Start Time": "12:18:47", "Box": "2"},
            experiment_type="Opto",
            experimental_group="DMS-Excitatory",
            optogenetic_treatment="EYFP",
        )
        session_to_nwb_args_per_session = reassign_misfiled_runs([misfiled_run, own_run, other_mouse_run])
        assert session_to_nwb_args_per_session == [
            dict(
                behavior_file_path=Path("Opto Experiments/DMS Excitatory/ChR2/479"),
                subject_id="480",
                session_conditions={"Start Date": "06/13/19", "Start Time": "09:43:23", "Box": "2"},
                experiment_type="Opto",
                experimental_group="DMS-Excitatory",
                optogenetic_treatment="EYFP",
            ),
            own_run,
            other_mouse_run,
        ]


class TestAddUnlistedRuns:
    def test_run_is_added_for_the_mouse_it_belongs_to(self, tmp_path):
        # 334.394's run on 07/28/20 shares its start time with 272.396's run in 272.396's file
        photometry_session = dict(
            behavior_file_path=tmp_path / "FP Experiments/Behavior/DPR/334.394/334.394",
            fiber_photometry_folder_path=tmp_path / "FP Experiments/Photometry/Photo_334_394-200727-131426",
            subject_id="334.394",
            session_conditions={"Start Date": "07/27/20", "Start Time": "13:14:26", "Box": "4"},
            experiment_type="FP",
            experimental_group="DPR",
        )
        behavior_session = dict(
            behavior_file_path=tmp_path / "FP Experiments/Behavior/DPR/334.394/334.394",
            subject_id="334.394",
            session_conditions={"Start Date": "07/29/20", "Start Time": "11:35:37", "Box": "4"},
            experiment_type="FP",
            experimental_group="DPR",
        )
        session_to_nwb_args_per_session = add_unlisted_runs(
            session_to_nwb_args_per_session=[photometry_session, behavior_session],
            data_dir_path=tmp_path,
            unlisted_run_to_subject_id={
                ("FP Experiments/Behavior/DPR/272.396/272.396", "07/28/20", "13:21:15", "4"): "334.394"
            },
        )
        assert session_to_nwb_args_per_session == [
            photometry_session,
            behavior_session,
            dict(
                behavior_file_path=tmp_path / "FP Experiments/Behavior/DPR/272.396/272.396",
                subject_id="334.394",
                session_conditions={"Start Date": "07/28/20", "Start Time": "13:21:15", "Box": "4"},
                experiment_type="FP",
                experimental_group="DPR",
            ),
        ]

    def test_run_saved_only_in_another_mouse_file_is_added(self, tmp_path):
        # 333.393's run on 07/31/20 is saved only in 346.394's file, at the same start time as 346.394's own run
        behavior_session = dict(
            behavior_file_path=tmp_path / "FP Experiments/Behavior/DPR/333.393/333.393",
            subject_id="333.393",
            session_conditions={"Start Date": "07/29/20", "Start Time": "11:53:42", "Box": "6"},
            experiment_type="FP",
            experimental_group="DPR",
        )
        session_to_nwb_args_per_session = add_unlisted_runs(
            session_to_nwb_args_per_session=[behavior_session],
            data_dir_path=tmp_path,
            unlisted_run_to_subject_id={
                run: subject_id for run, subject_id in UNLISTED_RUN_TO_SUBJECT_ID.items() if subject_id == "333.393"
            },
        )
        assert session_to_nwb_args_per_session == [
            behavior_session,
            dict(
                behavior_file_path=tmp_path / "FP Experiments/Behavior/DPR/346.394/346.394",
                subject_id="333.393",
                session_conditions={"Start Date": "07/31/20", "Start Time": "12:03:31", "Box": "6"},
                experiment_type="FP",
                experimental_group="DPR",
            ),
        ]
