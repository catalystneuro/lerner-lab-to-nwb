from pathlib import Path

import pytest

from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_dataset import get_fp_header_variables, get_raw_info


def medpc_run(*, subject: str, box: str, start_date: str, start_time: str, msn: str) -> str:
    return (
        f"Start Date: {start_date}\n"
        f"End Date: {start_date}\n"
        f"Subject: {subject}\n"
        "Experiment: \n"
        "Group: \n"
        f"Box: {box}\n"
        f"Start Time: {start_time}\n"
        "End Time: 16:00:00\n"
        f"MSN: {msn}\n"
        "G:\n"
        "     0:      10.000        0.000\n"
    )


@pytest.fixture
def behavior_path(tmp_path) -> Path:
    behavior_path = tmp_path / "FP Experiments" / "Behavior"
    by_date_path = behavior_path / "MEDPC_RawFilesbyDate"
    by_date_path.mkdir(parents=True)
    # 98.257's FR1 days exist only in the files organized by date, one with a mistyped Subject field
    (by_date_path / "2019-04-02").write_text(
        "\n"
        + "\n".join(
            [
                medpc_run(
                    subject="98.257",
                    box="2",
                    start_date="04/02/19",
                    start_time="12:55:46",
                    msn="FOOD_FR1 Habit Training TTL",
                ),
                medpc_run(
                    subject="97.257",
                    box="1",
                    start_date="04/02/19",
                    start_time="12:55:46",
                    msn="FOOD_FR1 Habit Training TTL",
                ),
            ]
        )
    )
    (by_date_path / "2019-04-03").write_text(
        "\n"
        + medpc_run(
            subject="98.258",
            box="2",
            start_date="04/03/19",
            start_time="13:32:27",
            msn="FOOD_FR1 Habit Training TTL",
        )
    )
    # a run that is also in 98.257's own file
    (by_date_path / "2019-04-09").write_text(
        "\n"
        + medpc_run(
            subject="98.257",
            box="2",
            start_date="04/09/19",
            start_time="11:20:00",
            msn="FOOD_RI 30 RIGHT TTL",
        )
    )
    subject_dir = behavior_path / "RR20" / "98.257"
    subject_dir.mkdir(parents=True)
    (subject_dir / "98.257").write_text(
        "\n"
        + medpc_run(
            subject="98.257",
            box="2",
            start_date="04/09/19",
            start_time="11:20:00",
            msn="FOOD_RI 30 RIGHT TTL",
        )
    )
    return behavior_path


class TestGetFpHeaderVariables:
    def test_by_date_runs_are_added_to_the_subject_file(self, behavior_path):
        by_date_path = behavior_path / "MEDPC_RawFilesbyDate"
        header_variables = get_fp_header_variables(
            behavior_path / "RR20" / "98.257", "98.257", get_raw_info(behavior_path), "Start Date"
        )
        runs = sorted(zip(*header_variables))
        assert runs == [
            (
                "04/02/19",
                "12:55:46",
                "FOOD_FR1 Habit Training TTL",
                by_date_path / "2019-04-02",
                "98.257",
                None,
            ),
            (
                "04/03/19",
                "13:32:27",
                "FOOD_FR1 Habit Training TTL",
                by_date_path / "2019-04-03",
                "98.258",
                None,
            ),
            (
                "04/09/19",
                "11:20:00",
                "FOOD_RI 30 RIGHT TTL",
                behavior_path / "RR20" / "98.257" / "98.257",
                None,
                "2",
            ),
        ]
