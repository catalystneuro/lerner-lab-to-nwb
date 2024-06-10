import pytest
from lerner_lab_to_nwb.seiler_2024.medpc import read_medpc_file
from datetime import date, time, datetime
import numpy as np
from pathlib import Path
import pandas as pd

data_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/raw_data")


def test_read_medpc_file():
    file_path = data_dir_path / "FP Experiments" / "Behavior" / "RR20" / "95.259" / "95.259"
    session_contions = {"Start Date": "04/17/19", "Start Time": "12:41:30"}
    start_variable = "Start Date"
    medpc_name_to_info_dict = {
        "Start Date": {"name": "start_date", "is_array": False},
        "End Date": {"name": "end_date", "is_array": False},
        "Subject": {"name": "subject", "is_array": False},
        "Experiment": {"name": "experiment", "is_array": False},
        "Group": {"name": "group", "is_array": False},
        "Box": {"name": "box", "is_array": False},
        "Start Time": {"name": "start_time", "is_array": False},
        "End Time": {"name": "end_time", "is_array": False},
        "MSN": {"name": "MSN", "is_array": False},
        "G": {"name": "port_entry_times", "is_array": True},
        "E": {"name": "duration_of_port_entry", "is_array": True},
        "A": {"name": "left_nose_poke_times", "is_array": True},
        "C": {"name": "right_nose_poke_times", "is_array": True},
        "D": {"name": "right_reward_times", "is_array": True},
        "B": {"name": "left_reward_times", "is_array": True},
    }
    session_dict = read_medpc_file(
        file_path=file_path,
        medpc_name_to_info_dict=medpc_name_to_info_dict,
        session_conditions=session_contions,
        start_variable=start_variable,
    )
    csv_path = file_path.parent / "95.259_04-17-19.csv"
    session_df = pd.read_csv(csv_path)
    port_entry_times = np.trim_zeros(session_df["portEntryTs"].dropna().values, trim="b")
    duration_of_port_entry = np.trim_zeros(session_df["DurationOfPE"].dropna().values, trim="b")
    left_nose_poke_times = np.trim_zeros(session_df["LeftNoseTs"].dropna().values, trim="b")
    right_nose_poke_times = np.trim_zeros(session_df["RightNoseTs"].dropna().values, trim="b")
    right_reward_times = np.trim_zeros(session_df["RightRewardTs"].dropna().values, trim="b")
    left_reward_times = np.trim_zeros(session_df["LeftRewardTs"].dropna().values, trim="b")

    print(session_dict["start_date"])
    assert session_dict["start_date"] == "04/17/19", "start_date is not correct"
    assert session_dict["end_date"] == "04/17/19", "end_date is not correct"
    assert session_dict["subject"] == "95.259", "subject is not correct"
    assert session_dict["box"] == "1", "box is not correct"
    assert session_dict["start_time"] == "12:41:30", "start_time is not correct"
    assert session_dict["end_time"] == "13:38:14", "end_time is not correct"
    assert session_dict["MSN"] == "RR20_Left", "MSN is not correct"
    assert np.array_equal(session_dict["port_entry_times"], port_entry_times), "port_entry_times is not correct"
    assert np.array_equal(
        session_dict["duration_of_port_entry"], duration_of_port_entry
    ), "duration_of_port_entry is not correct"
    assert np.array_equal(
        session_dict["left_nose_poke_times"], left_nose_poke_times
    ), "left_nose_poke_times is not correct"
    assert np.array_equal(
        session_dict["right_nose_poke_times"], right_nose_poke_times
    ), "right_nose_poke_times is not correct"
    assert np.array_equal(session_dict["right_reward_times"], right_reward_times), "right_reward_times is not correct"
    assert np.array_equal(session_dict["left_reward_times"], left_reward_times), "left_reward_times is not correct"
