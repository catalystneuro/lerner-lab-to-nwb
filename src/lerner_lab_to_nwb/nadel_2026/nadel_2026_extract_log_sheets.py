"""Extract the lab log sheet fields of the nadel_2026 paper cells into the tables the conversion reads.

Run once against the hand-off folder; the tables it writes are committed next to this script:

- nadel_2026_log_cells.csv: per-cell amplifier settings and measurements (one row per paper cell)
- nadel_2026_log_test_pulses.csv: access resistance noted after each VC test pulse run
- nadel_2026_log_sessions.csv: day-level fields of each converted recording day

Each tab of a log sheet is one recording day: a day header block, then one block per cell. A cell block starts with a
time row ('@ (hh:mm)'), a drugs row ('DRUGS:'), a header row ('L or R', 'Retrob+', ..., 'Resting') whose labels name
the columns of the value row directly below it, and then one row per protocol with the logged sweep ranges. Paper cells
are matched to cell blocks by the sweep numbers of their WaveSurfer files, since several blocks carry a placeholder
('sXcX') or no cell label. Free-text notes are not extracted.
"""
import re
import warnings
from pathlib import Path

import openpyxl
import pandas as pd

LOG_SHEETS = {
    "CeA": "Ephys Log Sheet - aCUS CeA Beads (started 09-10-23).xlsx",
    "TS": "Ephys Log Sheet - aCUS SNL Beads (started 02-07-25).xlsx",
    "MZ": "MZ Ephys Log - JN CeA beads (started 2023 09 12).xlsx",
}
# MZ logged his Sept 2023 cells under his own mouse numbering; 611-323 (m323) is his m024 (README item 7).
MZ_MOUSE_CODES = {"m006": "m006", "m323": "m024"}

# Log column label -> output column of nadel_2026_log_cells.csv
CELL_FIELDS = {
    "Er": "pipette_resistance_megaohm",
    "P off": "pipette_offset",
    "Cp fast": "fast_capacitance_compensation",
    "Rt": "access_resistance_at_break_in_megaohm",
    "BB": "bridge_balance",
    "P Neutr": "pipette_capacitance_neutralization",
    "i to hold -70 mV": "holding_current_to_minus_70_mV_pA",
    "Resting": "resting_potential_mV",
}

# Hand corrections of single log entries, keyed by (mouse_folder, cell_folder, output column):
# (value as written, value used, reason). The reason is written to extraction_note.
CELL_VALUE_CORRECTIONS = {
    ("20230914 607-022", "m022 s3c2 +", "fast_capacitance_compensation"): (
        "14/106",
        "14.106",
        "slash for decimal point; the other cells of the day have 14.106",
    ),
    ("20240529 675-L", "m103 s3c4", "holding_current_to_minus_70_mV_pA"): ("-100\\", "-100", "stray backslash"),
    ("20260610 2006-151", "m410 s2c1", "time_of_recording"): ("2L46", "2:46", "L for colon"),
}
# Log entries left blank, keyed like CELL_VALUE_CORRECTIONS: (value as written, reason).
CELL_VALUE_BLANKS = {
    ("20230918 611-323", "m323 s3c2 + (mz_s1c2)", "access_resistance_at_break_in_megaohm"): (
        "4.5",
        "in the pipette resistance range and below the 20 MOhm access of the first test pulse; may belong under Er",
    ),
    ("20251017 854-L", "m403 s2c3", "pipette_resistance_megaohm"): (
        "34.05",
        "in the range of P off (19-43), not of pipette resistance (3.8-5.8); may belong under P off",
    ),
    ("20250210 755-0", "m202 s1c4", "pipette_capacitance_neutralization"): (
        "-150",
        "the only P Neutr entry in the log, and in the range of the holding current; column uncertain",
    ),
    ("20250306 757-L", "m113 s4c2", "resting_potential_mV"): ("60", "positive resting potential; sign uncertain"),
}
# Test pulse access corrections, keyed by (mouse_folder, cell_folder, log cell): (as written, value used, reason).
TEST_PULSE_ACCESS_CORRECTIONS = {
    ("20260610 2006-151", "m410 s2c1", "B59"): ("19,5", "19.5", "comma for decimal point"),
}
# Day-level corrections, keyed by (mouse_folder, output column): (value as written, value used or "", reason).
SESSION_VALUE_CORRECTIONS = {
    ("20230921 608-021", "internal"): ("021", "", "the mouse number written in the Internal field"),
    ("20240603 675-R", "surgery"): ("s", "", "incomplete entry"),
}
# Log entries that end in a remark with no experimental content: only the leading part is kept. Cell entries are keyed
# like CELL_VALUE_CORRECTIONS and day entries like SESSION_VALUE_CORRECTIONS; the value is the part kept.
CELL_REMARK_REMOVALS = {
    ("20240523 674-R", "m001 s5c1", "resting_potential_mV"): "-45?",
}
SESSION_REMARK_REMOVALS = {
    ("20240606 670-RL", "slicing_outcome"): "sliced @ 250, not so good",
}
REMARK_REMOVAL_NOTE = "kept '{kept}' (removed a trailing remark with no experimental content)"

# The parenthetical may be closed with '_' or not at all ('238-240 (11.9_', '234-236 (10').
SWEEP_ENTRY_PATTERN = re.compile(r"^(\d+)(?:\s*-\s*(\d+))?\s*(?:\(([^)_]*)(?:\)|_|$))?\s*(.*)$")
NUMBER_PATTERN = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


def format_value(value) -> str:
    """Return a log entry as text, as written in the cell."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def read_rows(worksheet) -> dict[int, dict[str, str]]:
    """Return the non-empty cells of a worksheet as {row number: {column letter: text}}."""
    rows = {}
    for row in worksheet.iter_rows():
        values = {cell.column_letter: format_value(cell.value) for cell in row if format_value(cell.value) != ""}
        if values:
            rows[row[0].row] = values
    return rows


def parse_sweep_entry(text: str) -> tuple[int, int | None, str | None] | None:
    """Parse a logged run like '1-3 (35)', '1122 bad', or '113 (20)' into (first sweep, last sweep, parenthetical).

    Returns None for entries that are not a sweep range (e.g. 'died', '-8 pA', 'N/A').
    """
    if "pA" in text or "mV" in text:
        return None
    match = SWEEP_ENTRY_PATTERN.match(text)
    if match is None:
        return None
    first, last, parenthetical, _ = match.groups()
    return int(first), None if last is None else int(last), parenthetical


def read_cell_blocks(rows: dict[int, dict[str, str]]) -> list[dict]:
    """Split a day tab into cell blocks."""
    header_row_numbers = sorted(
        row_number for row_number, values in rows.items() if "L or R" in values.values() and "Er" in values.values()
    )
    blocks = []
    for index, header_row_number in enumerate(header_row_numbers):
        first_row = header_row_number - 2
        last_row = header_row_numbers[index + 1] - 3 if index + 1 < len(header_row_numbers) else max(rows)
        header = rows[header_row_number]
        value_row = rows.get(header_row_number + 1, {})
        label_candidates = [
            rows.get(row_number, {}).get("A", "")
            for row_number in (
                header_row_number + 1,
                header_row_number + 2,
                header_row_number,
                header_row_number - 1,
            )
        ]
        label = next((candidate for candidate in label_candidates if re.match(r"^s.c.", candidate, re.I)), "")
        time_row = rows.get(first_row, {})
        drugs_row = rows.get(header_row_number - 1, {})
        runs = []
        for row_number in range(header_row_number + 2, last_row + 1):
            row = rows.get(row_number, {})
            protocol = row.get("A", "")
            if not re.match(r"^\d+ - ", protocol):
                continue
            for column, text in row.items():
                if column == "A":
                    continue
                entry = parse_sweep_entry(text)
                if entry is not None:
                    runs.append(dict(protocol=protocol, row=row_number, column=column, text=text, entry=entry))
        blocks.append(
            dict(
                first_row=first_row,
                last_row=last_row,
                label=label,
                time=time_row.get("C", ""),
                time_label=time_row.get("B", ""),
                drugs=" ".join(value for column, value in sorted(drugs_row.items()) if column not in ("A", "B")),
                values={header[column]: value_row[column] for column in header if column in value_row},
                unlabeled_values={
                    column: value for column, value in value_row.items() if column not in header and column != "A"
                },
                runs=runs,
            )
        )
    return blocks


def get_cell_files(manifest: pd.DataFrame, misfiled_runs: pd.DataFrame, mouse_folder: str, cell_folder: str):
    """Return the WaveSurfer files of a cell as in the conversion: its folder plus runs misfiled elsewhere."""
    files = manifest[
        (manifest.mouse_folder == mouse_folder) & (manifest.cell_folder == cell_folder) & manifest.subfolder.isna()
    ]
    misfiled = misfiled_runs[(misfiled_runs.mouse_folder == mouse_folder) & (misfiled_runs.cell_folder == cell_folder)]
    moved = manifest[
        (manifest.mouse_folder == mouse_folder)
        & manifest.cell_folder.isin(misfiled.found_in_cell_folder)
        & manifest.filename.isin(misfiled.filename)
        & manifest.subfolder.isna()
    ]
    return pd.concat([files, moved])[
        ["filename", "file_prefix", "sweep_first", "sweep_last", "protocol_short", "run_start"]
    ]


def match_block(blocks: list[dict], cell_files: pd.DataFrame, cell_label: str) -> dict:
    """Return the log block of a cell.

    The block is the one whose logged runs share the most first sweeps with the cell's files. Where every cell of
    the day has its own file prefix (853-L, 'm404_s1c1_'), sweep numbers restart for each cell, so the block is the
    one with the cell's label.
    """
    if cell_files.file_prefix.str.endswith(f"_{cell_label}").all():
        best_blocks = [block for block in blocks if block["label"].lower() == cell_label.lower()]
    else:
        file_starts = set(cell_files.sweep_first.astype(int))
        scores = [len(file_starts & {run["entry"][0] for run in block["runs"]}) for block in blocks]
        best_blocks = [block for block, score in zip(blocks, scores) if score == max(scores) and score > 0]
    if len(best_blocks) != 1:
        raise ValueError(f"No single log block matches the files of {cell_label}")
    return best_blocks[0]


def extract_log_sheets(data_dir_path: Path, output_dir_path: Path) -> None:
    """Write the log cell, test pulse, and session tables for the paper cells."""
    warnings.filterwarnings("ignore", message="Conditional Formatting extension is not supported")
    log_sheets_dir_path = data_dir_path / "metadata" / "log_sheets"
    workbooks = {
        name: openpyxl.load_workbook(log_sheets_dir_path / file_name, data_only=True)
        for name, file_name in LOG_SHEETS.items()
    }
    tabs = {}
    for name, workbook in workbooks.items():
        for worksheet in workbook.worksheets:
            code_match = re.search(r" (m\d{3})$", worksheet.title)
            if code_match is not None:
                tabs[(name, code_match.group(1))] = (LOG_SHEETS[name], worksheet.title, read_rows(worksheet))

    module_dir_path = Path(__file__).parent
    paper_cells = pd.read_csv(module_dir_path / "nadel_2026_paper_cells.csv")
    misfiled_runs = pd.read_csv(module_dir_path / "nadel_2026_misfiled_runs.csv")
    manifest = pd.read_csv(data_dir_path / "tables" / "raw_h5_manifest.csv")
    cells_master = pd.read_csv(data_dir_path / "tables" / "cells_master.csv")
    paper_cells = paper_cells.merge(
        cells_master[["mouse_folder", "cell_folder", "cell_id", "projection_target"]],
        on=["mouse_folder", "cell_folder"],
    )

    cell_rows, test_pulse_rows = [], []
    for cell in paper_cells.itertuples():
        mouse_code, cell_label = cell.cell_id.split(" ")
        notes = []
        if "(mz_" in cell.cell_folder:
            workbook_name = "MZ"
            tab_code = MZ_MOUSE_CODES[mouse_code]
            cell_label = re.search(r"\(mz_(s\d+c\d+)\)", cell.cell_folder).group(1)
            notes.append(f"MZ's log, his cell {tab_code} {cell_label}")
        else:
            workbook_name = "TS" if cell.projection_target == "TS" else "CeA"
            tab_code = mouse_code
        source_file, source_sheet, rows = tabs[(workbook_name, tab_code)]
        blocks = read_cell_blocks(rows)
        for block in blocks:
            block["source_sheet"] = source_sheet
        cell_files = get_cell_files(
            manifest=manifest, misfiled_runs=misfiled_runs, mouse_folder=cell.mouse_folder, cell_folder=cell.cell_folder
        )
        day_files = manifest[
            (manifest.mouse_folder == cell.mouse_folder) & manifest.file_prefix.isin(cell_files.file_prefix)
        ]
        day_files = day_files.assign(
            folder_path=day_files.cell_folder.fillna("")
            + day_files.subfolder.fillna("").map(lambda subfolder: f"/{subfolder}" if subfolder else "")
        )
        block = match_block(blocks=blocks, cell_files=cell_files, cell_label=cell_label)
        if block["label"].lower() != cell_label.lower():
            label_text = f"'{block['label']}'" if block["label"] else "no cell label"
            notes.append(f"log block has {label_text}; matched to the cell by its sweep ranges")
        if block["time"] and not block["time_label"]:
            notes.append("time written without the '@ (hh:mm)' label")
        if block["unlabeled_values"]:
            notes.append(f"values in unlabeled columns not extracted: {block['unlabeled_values']}")

        row = dict(
            mouse_folder=cell.mouse_folder,
            cell_folder=cell.cell_folder,
            source_file=source_file,
            source_sheet=source_sheet,
            source_rows=f"{block['first_row']}-{block['last_row']}",
            time_of_recording=block["time"],
            bath_drugs=block["drugs"],
        )
        for log_label, column in CELL_FIELDS.items():
            row[column] = block["values"].get(log_label, "")
        for column in ["time_of_recording", *CELL_FIELDS.values()]:
            key = (cell.mouse_folder, cell.cell_folder, column)
            if key in CELL_VALUE_CORRECTIONS:
                written, corrected, reason = CELL_VALUE_CORRECTIONS[key]
                assert row[column] == written, f"{key}: expected '{written}' in the log, found '{row[column]}'"
                row[column] = corrected
                notes.append(f"{column}: '{written}' read as '{corrected}' ({reason})")
            elif key in CELL_VALUE_BLANKS:
                written, reason = CELL_VALUE_BLANKS[key]
                assert row[column] == written, f"{key}: expected '{written}' in the log, found '{row[column]}'"
                row[column] = ""
                notes.append(f"{column}: '{written}' left blank ({reason})")
            elif key in CELL_REMARK_REMOVALS:
                kept = CELL_REMARK_REMOVALS[key]
                assert row[column].startswith(kept), f"{key}: expected an entry starting with '{kept}' in the log"
                row[column] = kept
                notes.append(f"{column}: {REMARK_REMOVAL_NOTE.format(kept=kept)}")
        row["extraction_note"] = "; ".join(notes)
        cell_rows.append(row)

        test_pulse_rows.extend(get_test_pulse_rows(block=block, cell_files=cell_files, day_files=day_files, cell=cell))

    cell_columns = [
        "mouse_folder",
        "cell_folder",
        "source_file",
        "source_sheet",
        "source_rows",
        "time_of_recording",
        *CELL_FIELDS.values(),
        "bath_drugs",
        "extraction_note",
    ]
    pd.DataFrame(cell_rows)[cell_columns].to_csv(output_dir_path / "nadel_2026_log_cells.csv", index=False)
    pd.DataFrame(test_pulse_rows).to_csv(output_dir_path / "nadel_2026_log_test_pulses.csv", index=False)

    session_rows = []
    for mouse_folder, day_cells in paper_cells.groupby("mouse_folder", sort=False):
        jn_cells = day_cells[~day_cells.cell_folder.str.contains(r"\(mz_")]
        mouse_code = jn_cells.cell_id.iloc[0].split(" ")[0]
        workbook_name = "TS" if jn_cells.projection_target.iloc[0] == "TS" else "CeA"
        source_file, source_sheet, rows = tabs[(workbook_name, mouse_code)]
        session_rows.append(
            get_session_row(mouse_folder=mouse_folder, source_file=source_file, source_sheet=source_sheet, rows=rows)
        )
    pd.DataFrame(session_rows).to_csv(output_dir_path / "nadel_2026_log_sessions.csv", index=False)


def get_test_pulse_rows(block: dict, cell_files: pd.DataFrame, day_files: pd.DataFrame, cell) -> list[dict]:
    """Return one row per logged VC test pulse run with an access value in parentheses.

    A logged run is matched to the cell's file with the same first and last sweep. A logged range that matches no file
    exactly is matched to the one VC test pulse file of the cell that overlaps it and that no other logged run claims;
    otherwise the row is kept without a file name.
    """
    all_test_pulse_runs = [run for run in block["runs"] if run["protocol"].startswith("1 - VC test pulse")]
    test_pulse_files = cell_files[cell_files.protocol_short.str.startswith("VC test pulse")].sort_values("run_start")
    test_pulse_runs = [run for run in all_test_pulse_runs if run["entry"][2] is not None]
    exact_matches = {}
    for index, run in enumerate(test_pulse_runs):
        first, last, _ = run["entry"]
        last = first if last is None else last
        exact = cell_files[(cell_files.sweep_first == first) & (cell_files.sweep_last == last)]
        if len(exact) == 1:
            exact_matches[index] = exact.filename.iloc[0]
    claimed_files = set(exact_matches.values())

    test_pulse_rows = []
    for index, run in enumerate(test_pulse_runs):
        first, last, parenthetical = run["entry"]
        last = first if last is None else last
        logged_range = f"{first}-{last}" if last != first else f"{first}"
        notes = []
        filename = exact_matches.get(index, "")
        if filename == "":
            overlapping = cell_files[
                cell_files.protocol_short.str.startswith("VC test pulse")
                & ~cell_files.filename.isin(claimed_files)
                & (cell_files.sweep_first <= last)
                & (cell_files.sweep_last >= first)
            ]
            if len(overlapping) == 1:
                filename = overlapping.filename.iloc[0]
                file_range = f"{int(overlapping.sweep_first.iloc[0])}-{int(overlapping.sweep_last.iloc[0])}"
                notes.append(f"logged as sweeps {logged_range}; the cell's test pulse file holds sweeps {file_range}")
            elif len(all_test_pulse_runs) == len(test_pulse_files):
                position = all_test_pulse_runs.index(run)
                matched = test_pulse_files.iloc[position]
                filename = matched.filename
                notes.append(
                    f"logged as sweeps {logged_range}, which no test pulse file of the cell holds; matched by order "
                    f"(test pulse {position + 1} of {len(test_pulse_files)} in the log and in the files, "
                    f"sweeps {int(matched.sweep_first)}-{int(matched.sweep_last)})"
                )
            else:
                holding = day_files[(day_files.sweep_first <= last) & (day_files.sweep_last >= first)]
                found = ", ".join(f"{folder}/{name}" for folder, name in zip(holding.folder_path, holding.filename))
                notes.append(
                    f"logged as sweeps {logged_range}; no converted file of the cell holds them"
                    + (f" (overlapping files: {found})" if found else " (no file in the hand-off holds them)")
                )
        if not re.search(r"\([^)]*\)", run["text"]):
            notes.append(f"written as '{run['text']}' (parenthesis not closed)")
        access = parenthetical.strip()
        correction_key = (cell.mouse_folder, cell.cell_folder, f"{run['column']}{run['row']}")
        if correction_key in TEST_PULSE_ACCESS_CORRECTIONS:
            written, corrected, reason = TEST_PULSE_ACCESS_CORRECTIONS[correction_key]
            assert access == written, f"{correction_key}: expected '{written}', found '{access}'"
            notes.append(f"access written as '({written})', read as {corrected} ({reason})")
            access = corrected
        elif not NUMBER_PATTERN.match(access):
            stripped = access.rstrip("!").strip()
            if NUMBER_PATTERN.match(stripped):
                notes.append(f"access written as '({parenthetical})'")
                access = stripped
            else:
                notes.append(f"access written as '({parenthetical})', left blank as not a single reading")
                access = ""
        test_pulse_rows.append(
            dict(
                mouse_folder=cell.mouse_folder,
                cell_folder=cell.cell_folder,
                filename=filename,
                access_resistance_megaohm=access,
                source_sheet=block["source_sheet"],
                source_cell=f"{run['column']}{run['row']}",
                extraction_note="; ".join(notes),
            )
        )
    return test_pulse_rows


def get_session_row(mouse_folder: str, source_file: str, source_sheet: str, rows: dict[int, dict[str, str]]) -> dict:
    """Return the day-level log fields of a recording day."""
    labels = {}
    for row_number in range(1, 14):
        row = rows.get(row_number, {})
        if "A" in row:
            labels[row["A"]] = row.get("B", "")
        if "G" in row:
            labels[row["G"]] = next((value for column, value in sorted(row.items()) if "G" < column < "K"), "")
    session_row = dict(
        mouse_folder=mouse_folder,
        source_file=source_file,
        source_sheet=source_sheet,
        internal=labels.get("Internal", ""),
        surgery=labels.get("Surgery", ""),
        slicing_outcome=labels.get("Slicing outcome", ""),
        ephys_outcome=labels.get("Ephys outcome", ""),
        days_since_surgery=labels.get("days since surgery", ""),
    )
    notes = []
    for column in list(session_row)[3:]:
        key = (mouse_folder, column)
        if key in SESSION_VALUE_CORRECTIONS:
            written, corrected, reason = SESSION_VALUE_CORRECTIONS[key]
            assert session_row[column] == written, f"{key}: expected '{written}', found '{session_row[column]}'"
            session_row[column] = corrected
            outcome = f"read as '{corrected}'" if corrected else "left blank"
            notes.append(f"{column}: '{written}' {outcome} ({reason})")
        elif key in SESSION_REMARK_REMOVALS:
            kept = SESSION_REMARK_REMOVALS[key]
            assert session_row[column].startswith(kept), f"{key}: expected an entry starting with '{kept}' in the log"
            session_row[column] = kept
            notes.append(f"{column}: {REMARK_REMOVAL_NOTE.format(kept=kept)}")

    date, animal_id = mouse_folder.split(" ")
    if not source_sheet.startswith(date):
        notes.append(f"tab name '{source_sheet}' does not start with the recording date {date}")
    log_mouse = labels.get("Mouse", "")
    if log_mouse and not animal_id.endswith(log_mouse):
        notes.append(f"Mouse field reads '{log_mouse}' (subject is {animal_id})")
    log_date = labels.get("Date", "")
    month_day = [int(number) for number in re.findall(r"\d+", log_date)[:2]]
    if log_date and month_day != [int(date[4:6]), int(date[6:8])]:
        notes.append(f"Date field reads '{log_date}'")
    session_row["extraction_note"] = "; ".join(notes)
    return session_row


if __name__ == "__main__":
    extract_log_sheets(
        data_dir_path=Path("/Volumes/T7/CatalystNeuro/Lerner/aCUS_ephys_raw_for_NWB"),
        output_dir_path=Path(__file__).parent,
    )
