from datetime import datetime, date, time, timezone
import numpy as np


def get_start_dates(file_path: str) -> list:  # TODO: Refactor get methods into a class
    """Get the start dates of all sessions in a MedPC file."""
    with open(file_path, "r") as f:
        lines = f.readlines()
    start_dates = []
    for line in lines:
        if line.startswith("Start Date: "):
            start_date = line.split("Start Date: ")[1].strip()
            start_dates.append(start_date)
    return start_dates


def get_start_times(file_path: str) -> list:
    """Get the start times of all sessions in a MedPC file."""
    with open(file_path, "r") as f:
        lines = f.readlines()
    start_times = []
    for line in lines:
        if line.startswith("Start Time: "):
            start_time = line.split("Start Time: ")[1].strip()
            start_times.append(start_time)
    return start_times


def get_MSNs(file_path: str) -> list:
    """Get the MSNs of all sessions in a MedPC file."""
    with open(file_path, "r") as f:
        lines = f.readlines()
    msns = []
    for line in lines:
        if line.startswith("MSN: "):
            msn = line.split("MSN: ")[1].strip()
            msns.append(msn)
    return msns


def read_medpc_file(
    file_path: str, start_datetime: datetime, medpc_name_to_dict_name: dict, dict_name_to_type: dict
) -> dict:
    """Read a raw MedPC text file into a dictionary."""
    # Read the file
    with open(file_path, "r") as f:
        lines = f.readlines()

    # Find the start and end lines for the given session
    start_date = start_datetime.strftime("%m/%d/%y")
    start_time = start_datetime.strftime("%H:%M:%S")
    start_date_is_match, start_time_is_match = False, False
    start_line, end_line = None, None
    for i, line in enumerate(lines):
        if line == f"Start Date: {start_date}\n":
            start_date_is_match = True
            start_line = i
        elif line == f"Start Time: {start_time}\n" and start_date_is_match:
            start_time_is_match = True
        elif line == "\n" and start_time_is_match:
            end_line = i
            break
        elif line == "\n":
            start_date_is_match, start_time_is_match = False, False
    if not (start_date_is_match and start_time_is_match):
        raise ValueError(f"Could not find start date {start_date} and time {start_time} in file {file_path}")
    if end_line is None:
        raise ValueError(f"Could not find end of session ('\\n') in file {file_path}")
    session_lines = lines[start_line:end_line]

    # Parse the session lines into a dictionary
    session_dict = {}
    for i, line in enumerate(session_lines):
        line = line.strip("\\n")
        split_line = line.split(":", maxsplit=1)
        medpc_name, data = split_line
        data = data.strip()
        if line.find(":") == 6:  # multiline variable
            if medpc_name == "     0":  # first line of multiline variable
                multiline_variable_name = session_lines[i - 1].split(":")[0]
                if multiline_variable_name in medpc_name_to_dict_name:
                    session_dict[medpc_name_to_dict_name[multiline_variable_name]] = []
            if multiline_variable_name not in medpc_name_to_dict_name:
                continue
            data = data.split(" ")
            data = [datum.strip() for datum in data if datum.strip() != ""]
            for datum in data:
                session_dict[medpc_name_to_dict_name[multiline_variable_name]].append(datum)

        # single line variable
        elif medpc_name in medpc_name_to_dict_name:
            dict_name = medpc_name_to_dict_name[medpc_name]
            session_dict[dict_name] = data

    # Convert the data types
    for dict_name, data_type in dict_name_to_type.items():
        if dict_name in session_dict:
            if data_type == date:
                session_dict[dict_name] = datetime.strptime(session_dict[dict_name], "%m/%d/%y").date()
            elif data_type == time:
                session_dict[dict_name] = datetime.strptime(session_dict[dict_name], "%H:%M:%S").time()
            elif data_type == np.ndarray:
                if session_dict[dict_name] == "":
                    session_dict[dict_name] = np.array([], dtype=float)
                elif type(session_dict[dict_name]) == str:  # not a multiline variable
                    raise ValueError(
                        f"Expected {dict_name} to be a multiline variable, but found a single line variable."
                    )
                else:
                    session_dict[dict_name] = np.array(session_dict[dict_name], dtype=float)
                    session_dict[dict_name] = np.trim_zeros(
                        session_dict[dict_name], trim="b"
                    )  # MEDPC adds extra zeros to the end of the array
    return session_dict
