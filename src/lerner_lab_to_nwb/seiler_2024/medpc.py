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


def get_session_lines(lines: list, session_conditions: dict, start_variable: str) -> list:
    """
    Get the lines for a session from a MedPC file.

    Parameters
    ----------
    lines : list
        The lines of the MedPC file.
    session_conditions : dict
        The conditions that define the session. The keys are the names of the single-line variables (ex. 'Start Date')
        and the values are the values of those variables for the desired session (ex. '11/09/18').
    start_variable : str
        The name of the variable that starts the session (ex. 'Start Date').

    Returns
    -------
    list
        The lines for the session.

    Raises
    ------
    ValueError
        If the session with the given conditions could not be found.
    ValueError
        If the start variable of the session with the given conditions could not be found.
    """
    session_condition_has_been_met = {name: False for name in session_conditions}
    start_line, end_line = None, len(lines)
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith(f"{start_variable}:"):
            start_line = i
        for condition_name, condition_value in session_conditions.items():
            if line == f"{condition_name}: {condition_value}":
                session_condition_has_been_met[condition_name] = True
        if line == "" and all(session_condition_has_been_met.values()):
            end_line = i
            break
        elif line == "":
            session_condition_has_been_met = {name: False for name in session_conditions}
            start_line = None
    if not all(session_condition_has_been_met.values()):
        raise ValueError(f"Could not find the session with conditions {session_conditions}")
    if start_line is None:
        raise ValueError(
            f"Could not find the start variable ({start_variable}) of the session with conditions {session_conditions}"
        )
    session_lines = lines[start_line:end_line]
    return session_lines


def read_medpc_file(
    file_path: str,
    medpc_name_to_dict_name: dict,
    dict_name_to_type: dict,
    session_conditions: dict,
    start_variable: str,
) -> dict:
    """Read a raw MedPC text file into a dictionary."""
    with open(file_path, "r") as f:
        lines = f.readlines()
    session_lines = get_session_lines(lines, session_conditions=session_conditions, start_variable=start_variable)

    # Parse the session lines into a dictionary
    session_dict = {}
    for i, line in enumerate(session_lines):
        line = line.rstrip()
        if line.startswith("\\"):  # \\ indicates a commented line in the MedPC file
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
