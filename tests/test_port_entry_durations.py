from pathlib import Path

import pytest

from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_dataset import (
    get_no_port_entry_duration_sessions,
    get_session_key_from_kwargs,
)


def probe_test_run(*, box: str, durations: str) -> str:
    # Probe Test Habit Training TTL keeps E as a single-line variable and stores port entry durations in U
    return (
        "Start Date: 08/03/20\n"
        "End Date: 08/03/20\n"
        "Subject: 28\n"
        f"Box: {box}\n"
        "Start Time: 11:23:03\n"
        "MSN: Probe Test Habit Training TTL\n"
        "E:       0.000\n"
        "U:\n"
        f"     0:      {durations}\n"
    )


@pytest.fixture
def medpc_file_path(tmp_path) -> Path:
    file_path = tmp_path / "028.392"
    file_path.write_text(
        "\n"
        + probe_test_run(box="1", durations="1.500        2.250        0.000")
        + "\n"
        + probe_test_run(box="2", durations="0.000        0.000        0.000")
    )
    return file_path


def test_single_line_e_falls_back_to_u(medpc_file_path, tmp_path):
    session_to_nwb_args_per_session = [
        dict(
            behavior_file_path=medpc_file_path,
            session_conditions={"Start Date": "08/03/20", "Start Time": "11:23:03", "Box": box},
            start_variable="Start Date",
        )
        for box in ("1", "2")
    ]
    no_port_entry_duration_sessions = get_no_port_entry_duration_sessions(
        port_entry_file_path=tmp_path / "sessions_without_port_entry_durations.yaml",
        session_to_nwb_args_per_session=session_to_nwb_args_per_session,
    )
    assert no_port_entry_duration_sessions == {get_session_key_from_kwargs(session_to_nwb_args_per_session[1])}
