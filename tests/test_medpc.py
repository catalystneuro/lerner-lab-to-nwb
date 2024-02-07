import pytest
from lerner_lab_to_nwb.seiler_2024.medpc import read_medpc_file
from datetime import date, time
import numpy as np
from pathlib import Path
import pandas as pd

data_dir_path = Path("/Volumes/T7/CatalystNeuro/NWB/Lerner/raw_data")


def test_read_medpc_file():
    file_path = data_dir_path / "FP Experiments" / "Behavior" / "RR20" / "95.259" / "95.259"
    start_date = "04/17/19"
    medpc_name_to_dict_name = {
        "Start Date": "start_date",
        "End Date": "end_date",
        "Subject": "subject",
        "Experiment": "experiment",
        "Group": "group",
        "Box": "box",
        "Start Time": "start_time",
        "End Time": "end_time",
        "MSN": "MSN",
        "G": "port_entry_times",
        "E": "duration_of_port_entry",
        "A": "left_nose_poke_times",
        "C": "right_nose_poke_times",
        "D": "right_reward_times",
        "B": "left_reward_times",
    }
    dict_name_to_type = {
        "start_date": date,
        "end_date": date,
        "subject": str,
        "experiment": str,
        "group": str,
        "box": str,
        "start_time": time,
        "end_time": time,
        "MSN": str,
        "port_entry_times": np.ndarray,
        "duration_of_port_entry": np.ndarray,
        "left_nose_poke_times": np.ndarray,
        "right_nose_poke_times": np.ndarray,
        "right_reward_times": np.ndarray,
        "left_reward_times": np.ndarray,
    }
    session_dict = read_medpc_file(
        file_path=file_path,
        start_date=start_date,
        medpc_name_to_dict_name=medpc_name_to_dict_name,
        medpc_name_to_type=dict_name_to_type,
    )
    csv_path = file_path.parent / "95.259_04-17-19.csv"
    session_df = pd.read_csv(csv_path)
    port_entry_times = np.trim_zeros(session_df["portEntryTs"].dropna().values, trim="b")
    duration_of_port_entry = np.trim_zeros(session_df["DurationOfPE"].dropna().values, trim="b")
    left_nose_poke_times = np.trim_zeros(session_df["LeftNoseTs"].dropna().values, trim="b")
    right_nose_poke_times = np.trim_zeros(session_df["RightNoseTs"].dropna().values, trim="b")
    right_reward_times = np.trim_zeros(session_df["RightRewardTs"].dropna().values, trim="b")
    left_reward_times = np.trim_zeros(session_df["LeftRewardTs"].dropna().values, trim="b")

    assert session_dict["start_date"] == date(2019, 4, 17), "start_date is not correct"
    assert session_dict["end_date"] == date(2019, 4, 17), "end_date is not correct"
    assert session_dict["subject"] == "95.259", "subject is not correct"
    assert session_dict["box"] == "1", "box is not correct"
    assert session_dict["start_time"] == time(12, 41, 30), "start_time is not correct"
    assert session_dict["end_time"] == time(13, 38, 14), "end_time is not correct"
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
