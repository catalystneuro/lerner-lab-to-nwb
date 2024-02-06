from datetime import datetime, date, time, timezone
import numpy as np


# TODO: Add tests to compare to .csvs
# TODO: Refactor to separate file and clean up code (ex. inversion)
def read_medpc_file(file_path: str, start_date: str, medpc_name_to_dict_name: dict, medpc_name_to_type: dict) -> dict:
    """Read a raw MedPC text file into a dictionary."""
    # Read the file
    with open(file_path, "r") as f:
        lines = f.readlines()

    # Find the start and end lines for the given session
    start_line, end_line = None, None
    for i, line in enumerate(lines):
        if line == f"Start Date: {start_date}\n":
            start_line = i
        elif start_line is not None and line == "\n":
            end_line = i
            break
    if start_line is None:
        raise ValueError(f"Could not find start date {start_date} in file {file_path}")
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
            if medpc_name == "     0":
                multiline_variable_name = session_lines[i - 1].split(":")[0]
                if multiline_variable_name not in medpc_name_to_dict_name:
                    continue
                session_dict[medpc_name_to_dict_name[multiline_variable_name]] = []
            if multiline_variable_name not in medpc_name_to_dict_name:
                continue
            data = data.split(" ")
            for datum in data:
                datum = datum.strip()
                if datum == "":
                    continue
                session_dict[medpc_name_to_dict_name[multiline_variable_name]].append(datum)
        elif medpc_name in medpc_name_to_dict_name:
            dict_name = medpc_name_to_dict_name[medpc_name]
            session_dict[dict_name] = data

    # Convert the data types
    for medpc_name, data_type in medpc_name_to_type.items():
        if medpc_name in session_dict:
            if data_type == date:
                session_dict[medpc_name] = datetime.strptime(session_dict[medpc_name], "%m/%d/%y").date()
            elif data_type == time:
                session_dict[medpc_name] = datetime.strptime(session_dict[medpc_name], "%H:%M:%S").time()
            elif data_type == np.ndarray:
                if session_dict[medpc_name] == "":
                    session_dict[medpc_name] = np.array([], dtype=float)
                else:
                    session_dict[medpc_name] = np.array(session_dict[medpc_name], dtype=float)
    return session_dict
