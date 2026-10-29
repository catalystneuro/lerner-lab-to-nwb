"""Read the lab log sheet tables (written by nadel_2026_extract_log_sheets.py) into conversion metadata."""
from pathlib import Path

import numpy as np
import pandas as pd

LOG_CELLS_FILE_PATH = Path(__file__).parent / "nadel_2026_log_cells.csv"
LOG_TEST_PULSES_FILE_PATH = Path(__file__).parent / "nadel_2026_log_test_pulses.csv"
LOG_SESSIONS_FILE_PATH = Path(__file__).parent / "nadel_2026_log_sessions.csv"

# Per-cell log fields written as columns on the electrodes category of the intracellular recordings table.
# Numeric columns are NaN where the log has no entry; text columns are an empty string.
LOG_CELL_NUMERIC_COLUMNS = {
    "pipette_offset": "Pipette offset ('P off') as noted in the lab log sheet; the log does not state the unit.",
    "fast_capacitance_compensation": "Fast pipette capacitance compensation ('Cp fast') as noted in the lab log "
    "sheet; the log does not state the unit.",
}
LOG_CELL_TEXT_COLUMNS = {
    "time_of_recording": "Time the cell was recorded, as written in the lab log sheet (h:mm, 12-hour clock).",
    "holding_current_to_minus_70_mV": "Holding current in pA needed to hold the cell at -70 mV ('i to hold -70 mV'), "
    "as written in the lab log sheet; some entries hold two readings or a remark.",
    "resting_potential": "Resting membrane potential in mV ('Resting'), as written in the lab log sheet; some "
    "entries hold two readings.",
    "bath_drugs": "Drugs in the bath, as written in the lab log sheet.",
}
LOG_CELL_COLUMN_SOURCES = {
    "pipette_offset": "pipette_offset",
    "fast_capacitance_compensation": "fast_capacitance_compensation",
    "time_of_recording": "time_of_recording",
    "holding_current_to_minus_70_mV": "holding_current_to_minus_70_mV_pA",
    "resting_potential": "resting_potential_mV",
    "bath_drugs": "bath_drugs",
}
LOG_CELL_COLUMNS = {**LOG_CELL_NUMERIC_COLUMNS, **LOG_CELL_TEXT_COLUMNS}


def get_log_cell_metadata(mouse_folder: str) -> dict[str, dict]:
    """Return the log sheet fields of each paper cell of a recording day, keyed by cell folder.

    Each value has 'electrode' (IntracellularElectrode fields: resistance and initial_access_resistance, as text with
    the unit, where the log has them) and 'columns' (values of the LOG_CELL_COLUMNS).
    """
    log_cells = pd.read_csv(LOG_CELLS_FILE_PATH, dtype=str, keep_default_na=False)
    log_cells = log_cells[log_cells.mouse_folder == mouse_folder]
    cells = {}
    for log_cell in log_cells.itertuples():
        electrode = {}
        if log_cell.pipette_resistance_megaohm != "":
            electrode["resistance"] = f"{log_cell.pipette_resistance_megaohm} MOhm"
        if log_cell.access_resistance_at_break_in_megaohm != "":
            electrode["initial_access_resistance"] = f"{log_cell.access_resistance_at_break_in_megaohm} MOhm"
        columns = {}
        for column, source_column in LOG_CELL_COLUMN_SOURCES.items():
            value = getattr(log_cell, source_column)
            if column in LOG_CELL_NUMERIC_COLUMNS:
                value = np.nan if value == "" else float(value)
            columns[column] = value
        cells[log_cell.cell_folder] = dict(electrode=electrode, columns=columns)
    return cells


def get_log_cell_columns(log_cells: dict[str, dict]) -> dict[str, str]:
    """Return the descriptions of the LOG_CELL_COLUMNS that have a value for at least one of the given cells."""
    return {
        column: description
        for column, description in LOG_CELL_COLUMNS.items()
        if any(
            not (isinstance(value, float) and np.isnan(value)) and value != ""
            for value in (log_cell["columns"][column] for log_cell in log_cells.values())
        )
    }


def get_test_pulse_access_resistances(mouse_folder: str) -> dict[str, float]:
    """Return the access resistance in MOhm noted after each VC test pulse run of a day, keyed by WaveSurfer file."""
    test_pulses = pd.read_csv(LOG_TEST_PULSES_FILE_PATH)
    test_pulses = test_pulses[
        (test_pulses.mouse_folder == mouse_folder)
        & test_pulses.filename.notna()
        & test_pulses.access_resistance_megaohm.notna()
    ]
    return dict(zip(test_pulses.filename, test_pulses.access_resistance_megaohm.astype(float)))


def get_log_session_notes(mouse_folder: str) -> str:
    """Return the day-level log sheet fields of a recording day as one labeled line, or '' if the log has none."""
    log_sessions = pd.read_csv(LOG_SESSIONS_FILE_PATH, dtype=str, keep_default_na=False)
    log_session = log_sessions[log_sessions.mouse_folder == mouse_folder].iloc[0]
    labels = {
        "internal": "internal",
        "surgery": "surgery",
        "slicing_outcome": "slicing outcome",
        "ephys_outcome": "ephys outcome",
        "days_since_surgery": "days since surgery",
    }
    items = [f"{label} {log_session[column]}" for column, label in labels.items() if log_session[column] != ""]
    if not items:
        return ""
    return "Log sheet: " + "; ".join(items) + "."
