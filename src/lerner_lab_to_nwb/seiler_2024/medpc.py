from datetime import datetime, date, time, timezone
import numpy as np


def get_medpc_variables(file_path: str, variable_names: list) -> dict:
    """
    Get the values of the given single-line variables from a MedPC file for all sessions in that file.

    Parameters
    ----------
    file_path : str
        The path to the MedPC file.
    variable_names : list
        The names of the variables to get the values of.

    Returns
    -------
    dict
        A dictionary with the variable names as keys and a list of variable values as values.
    """
    with open(file_path, "r") as f:
        lines = f.readlines()
    medpc_variables = {name: [] for name in variable_names}
    for line in lines:
        for variable_name in variable_names:
            if line.startswith(variable_name):
                medpc_variables[variable_name].append(line.split(":", maxsplit=1)[1].strip())
    return medpc_variables


def read_medpc_file(
    file_path: str,
    start_datetime: datetime,
    medpc_name_to_dict_name: dict,
    dict_name_to_type: dict,
    subject_id: str | None = None,
) -> dict:
    """Read a raw MedPC text file into a dictionary."""
    # Read the file
    with open(file_path, "r") as f:
        lines = f.readlines()

    # Find the start and end lines for the given session
    start_date = start_datetime.strftime("%m/%d/%y")
    start_time = start_datetime.strftime("%H:%M:%S")
    start_date_is_match, start_time_is_match = False, False
    if subject_id is None:
        subject_id_is_match = True
    else:
        subject_id_is_match = False
    start_line, end_line = 0, len(lines)
    for i, line in enumerate(lines):
        line = line.strip()
        if line == f"Start Date: {start_date}":
            start_date_is_match = True
            start_line = i
        elif line == f"Start Time: {start_time}" and start_date_is_match:
            start_time_is_match = True
        elif line == f"Subject: {subject_id}":
            subject_id_is_match = True
        elif line == "" and start_time_is_match and subject_id_is_match:
            end_line = i
            break
        elif line == "":
            start_date_is_match, start_time_is_match = False, False
            if subject_id is not None:
                subject_id_is_match = False
    if not (start_date_is_match and start_time_is_match):
        raise ValueError(f"Could not find start date {start_date} and time {start_time} in file {file_path}")
    session_lines = lines[start_line:end_line]

    # Parse the session lines into a dictionary
    session_dict = {}
    for i, line in enumerate(session_lines):
        line = line.rstrip()
        if line == "\\rec" or line == "\\Recording":  # some files have a "rec" line at the end of the session
            continue
        assert ":" in line, f"Could not find ':' in line {repr(line)}"
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
            for datum in data:
                datum = datum.strip()
                if datum == "":
                    continue
                if (
                    "\t" in datum
                ):  # some sessions have a bunch of garbage after the last datum in the line separated by tabs
                    datum = datum.split("\t")[0]  # TODO: Make sure this is generalizable for neuroconv
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
