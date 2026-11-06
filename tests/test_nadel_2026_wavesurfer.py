from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import h5py
import numpy as np
import pandas as pd
import pytest
from neuroconv.datainterfaces import WaveSurferIntracellularInterface

from lerner_lab_to_nwb.nadel_2026 import Nadel2026NWBConverter
from lerner_lab_to_nwb.nadel_2026.nadel_2026_extract_log_sheets import (
    get_held_run_rows,
    parse_sweep_entry,
    read_cell_blocks,
)
from lerner_lab_to_nwb.nadel_2026.nadel_2026_log_sheets import (
    get_log_cell_columns,
    get_log_cell_metadata,
    get_log_session_notes,
    get_test_pulse_access_resistances,
)

# 10 Hz keeps sweeps short enough to write expected values by hand: a 2 s sweep is 20 samples.
SAMPLING_RATE = 10.0
SWEEP_DURATION = 2.0


def write_wavesurfer_file(
    file_path: Path,
    *,
    mode: str,
    clock_at_run_start: list,
    response_units: str,
    command_channel_name: str,
    command_unit: str,
    sweep_timestamps: list,
    first_sweep_number: int,
    protocol_name: str,
):
    """Write a minimal WaveSurfer 0.945 file holding the header fields the WaveSurfer interface reads."""

    def strings(values):
        return np.array([value.encode() for value in values])

    def number(value):
        return np.array([[float(value)]])

    num_samples = int(SAMPLING_RATE * SWEEP_DURATION)
    monitor_name = {"mV": "Electrode 1 Voltage", "pA": "Electrode 1 Current"}[response_units]
    loopback_name = {"pA": "Current Injection", "mV": "Voltage Cmd"}[command_unit]
    with h5py.File(file_path, "w") as file:
        header = file.create_group("header")
        header["VersionString"] = strings(["0.945"])
        header["ClockAtRunStart"] = np.array(clock_at_run_start, dtype=float).reshape(-1, 1)
        header["AbsoluteProtocolFileName"] = strings([f"R:\\protocols\\{protocol_name}.cfg"])
        header["AreSweepsFiniteDuration"] = number(1)
        header["StimulationUsesAcquisitionTrigger"] = number(1)
        header["SweepDuration"] = number(SWEEP_DURATION)
        electrode = header.create_group("Ephys/ElectrodeManager/Electrodes/element1")
        for field, value in dict(
            Name="Electrode 1",
            Type="Axon Multiclamp",
            Mode=mode,
            MonitorChannelName=monitor_name,
            CommandChannelName=command_channel_name,
        ).items():
            electrode[field] = strings([value])
        acquisition = header.create_group("Acquisition")
        acquisition["SampleRate"] = number(SAMPLING_RATE)
        acquisition["AnalogChannelNames"] = strings([monitor_name, loopback_name])
        acquisition["AnalogChannelUnits"] = strings([response_units, command_unit])
        acquisition["AnalogChannelScales"] = np.array([[0.01], [0.0025]])
        acquisition["IsAnalogChannelActive"] = np.array([[1.0], [1.0]])
        acquisition["AnalogScalingCoefficients"] = np.array([[0.1, 0.0003, 0.0, 0.0], [0.1, 0.0003, 0.0, 0.0]])
        stimulation = header.create_group("Stimulation")
        stimulation["IsEnabled"] = number(1)
        stimulation["SampleRate"] = number(SAMPLING_RATE)
        stimulation["AnalogChannelNames"] = strings([command_channel_name])
        stimulation["AnalogChannelUnits"] = strings([command_unit])
        stimulation["DoRepeatSequence"] = number(1)
        library = stimulation.create_group("StimulusLibrary")
        library["SelectedOutputableClassName"] = strings(["ws.StimulusMap"])
        library["SelectedOutputableIndex"] = number(1)
        library["Maps/element1/Name"] = strings(["Steps"])
        library["Maps/element1/ChannelName"] = strings([command_channel_name])
        library["Maps/element1/Multiplier"] = np.array([[1.0]])
        library["Maps/element1/IndexOfEachStimulusInLibrary/element1"] = number(1)
        stimulus = library.create_group("Stimuli/element1")
        for field, value in dict(
            Name="Steps", TypeString="SquarePulse", Amplitude="20*(i-1)", Delay="0.5", Duration="0.5", DCOffset="0"
        ).items():
            stimulus[field] = strings([value])
        stimulus["Delegate/TypeString"] = strings(["SquarePulse"])
        for sweep_number, timestamp in enumerate(sweep_timestamps, start=first_sweep_number):
            counts = np.full((2, num_samples), sweep_number - first_sweep_number, dtype="int16")
            file[f"sweep_{sweep_number:04d}/analogScans"] = counts
            file[f"sweep_{sweep_number:04d}/timestamp"] = number(timestamp)


@pytest.fixture
def current_clamp_file_path(tmp_path) -> Path:
    file_path = tmp_path / "m203_0571-0573.h5"
    write_wavesurfer_file(
        file_path,
        mode="cc",
        clock_at_run_start=[2025, 2, 13, 16, 58, 12.5],
        response_units="mV",
        command_channel_name="Command Current 1",
        command_unit="pA",
        sweep_timestamps=[0.7, 2.9, 5.1],
        first_sweep_number=571,
        protocol_name="PA_Ch1_CC excitability 20 pA steps to 200 pA",
    )
    return file_path


@pytest.fixture
def voltage_clamp_file_path(tmp_path) -> Path:
    file_path = tmp_path / "m203_0610.h5"
    write_wavesurfer_file(
        file_path,
        mode="vc",
        clock_at_run_start=[2025, 2, 13, 17, 0, 2.5],
        response_units="pA",
        command_channel_name="Command Voltage 1",
        command_unit="mV",
        sweep_timestamps=[1.0],
        first_sweep_number=610,
        protocol_name="PA_Ch1_WC_VC_Ih test",
    )
    return file_path


@pytest.fixture
def converter(current_clamp_file_path, voltage_clamp_file_path) -> Nadel2026NWBConverter:
    return Nadel2026NWBConverter(
        data_interfaces={
            "cell/m203_0571-0573": WaveSurferIntracellularInterface(
                file_path=current_clamp_file_path, reconstruct_stimulus=True, metadata_key="m203_0571-0573"
            ),
            "cell/m203_0610": WaveSurferIntracellularInterface(
                file_path=voltage_clamp_file_path, reconstruct_stimulus=True, metadata_key="m203_0610"
            ),
        }
    )


@pytest.fixture
def metadata(converter) -> dict:
    """The converter's metadata with both runs on one cell and the lab's log sheet entries."""
    metadata = converter.get_metadata()
    metadata["Devices"]["digitizer"] = dict(name="PCIe6323", description="National Instruments PCIe-6323 digitizer.")
    metadata["Icephys"]["IntracellularElectrodes"] = dict(
        electrode_m203_s3c2=dict(
            name="electrode_m203_s3c2",
            device_metadata_key="axon_multiclamp",
            description="Patch pipette.",
            cell_id="m203 s3c2",
            resistance="4.1 MOhm",
            initial_access_resistance="15.5 MOhm",
        )
    )
    for series_metadata in metadata["Icephys"]["PatchClampSeries"].values():
        series_metadata["electrode_metadata_key"] = "electrode_m203_s3c2"
    metadata["Icephys"].update(
        Cells=dict(
            electrode_m203_s3c2=dict(
                experimenter="JN",
                stress_group="naive",
                projection_target="TS",
                pipette_offset=np.nan,
                time_of_recording="",
            )
        ),
        CellColumns=dict(
            experimenter="Initials of the person who recorded the cell.",
            stress_group="Group of the mouse.",
            projection_target="Region where retrobeads were injected.",
            pipette_offset="Pipette offset.",
            time_of_recording="Time the cell was recorded.",
        ),
        TestPulseAccessResistances={"m203_0610.h5": 12.5},
        HeldRuns=["m203_0571-0573.h5"],
    )
    return metadata


class TestNadel2026NWBConverter:
    def test_session_start_time(self, metadata):
        assert metadata["NWBFile"]["session_start_time"] == datetime(2025, 2, 13, 16, 58, 12, 500000)

    def test_runs_share_the_cell_electrode(self, converter, metadata):
        nwbfile = converter.create_nwbfile(metadata=metadata)

        assert list(nwbfile.icephys_electrodes) == ["electrode_m203_s3c2"]
        electrode = nwbfile.icephys_electrodes["electrode_m203_s3c2"]
        assert electrode.cell_id == "m203 s3c2"
        assert electrode.initial_access_resistance == "15.5 MOhm"
        assert electrode.device.name == "AxonMulticlamp"
        assert "PCIe6323" in nwbfile.devices
        assert list(nwbfile.intracellular_recordings.category_tables["electrodes"]["experimenter"].data) == ["JN"] * 4

    def test_log_sheet_columns(self, converter, metadata):
        nwbfile = converter.create_nwbfile(metadata=metadata)

        sequential_recordings = nwbfile.get_icephys_sequential_recordings()
        assert list(sequential_recordings["source_file"].data) == ["m203_0571-0573.h5", "m203_0610.h5"]
        np.testing.assert_array_equal(sequential_recordings["access_resistance"].data, [np.nan, 12.5])
        assert list(sequential_recordings["held_near_minus_60_mV"].data) == [True, False]
        electrodes = nwbfile.intracellular_recordings.category_tables["electrodes"]
        np.testing.assert_array_equal(electrodes["pipette_offset"].data, [np.nan] * 4)
        assert list(electrodes["time_of_recording"].data) == [""] * 4
        assert list(electrodes["stress_group"].data) == ["naive"] * 4
        assert list(electrodes["projection_target"].data) == ["TS"] * 4


class TestLogSheets:
    def test_parse_sweep_entry(self):
        assert parse_sweep_entry("1-3 (35)") == (1, 3, "35")
        assert parse_sweep_entry("113 (20)") == (113, None, "20")
        assert parse_sweep_entry("1115 (VC)") == (1115, None, "VC")
        assert parse_sweep_entry("1122 bad") == (1122, None, None)
        assert parse_sweep_entry("-8 pA") is None
        assert parse_sweep_entry("died") is None

    def test_read_cell_blocks(self):
        header = {
            "B": "L or R",
            "C": "Retrob+",
            "F": "Er",
            "G": "P off",
            "I": "Rt",
            "J": "h",
            "M": "i to hold -70 mV",
            "N": "Resting",
        }
        rows = {
            14: {"B": "@ (hh:mm)", "C": "2:15"},
            15: {"B": "DRUGS:", "C": "NBQX", "D": "DAP5", "E": "GBZ"},
            16: header,
            17: {"A": "sXcX", "F": "4.5", "J": "22.78", "M": "-175", "N": "-60, -55"},
            20: {"A": "Whole Cell KGluc for CC"},
            21: {"A": "1 - VC test pulse", "B": "1-3 (35)", "C": "4-6 (11)"},
            22: {"A": "2 - CC spont firing", "B": "7", "C": "dead :("},
            24: {"B": "@ (hh:mm)"},
            25: {"A": "s1c2", "B": "DRUGS:", "C": "NBQX"},
            26: header,
            27: {"G": "20.46"},
            31: {"A": "1 - VC test pulse at end", "B": "116-118 (10.5)"},
        }
        first_block, second_block = read_cell_blocks(rows)

        assert (first_block["first_row"], first_block["last_row"]) == (14, 23)
        assert first_block["label"] == "sXcX"
        assert first_block["time"] == "2:15"
        assert first_block["drugs"] == "NBQX DAP5 GBZ"
        assert first_block["values"] == {"Er": "4.5", "h": "22.78", "i to hold -70 mV": "-175", "Resting": "-60, -55"}
        assert [run["entry"] for run in first_block["runs"]] == [(1, 3, "35"), (4, 6, "11"), (7, None, None)]
        assert second_block["label"] == "s1c2"
        assert second_block["time"] == ""
        assert second_block["drugs"] == "NBQX"
        assert second_block["values"] == {"P off": "20.46"}
        assert [run["entry"] for run in second_block["runs"]] == [(116, 118, "10.5")]

    def test_held_run_rows(self):
        header = {"B": "L or R", "F": "Er", "N": "Resting"}
        rows = {
            37: {"B": "@ (hh:mm)", "C": "3:01"},
            38: {"B": "DRUGS:", "C": "NBQX"},
            39: header,
            40: {"A": "sXcX", "N": "-74"},
            46: {"A": "3 - CC excitability 20 pA to 200 pA", "B": "232-242"},
            49: {"A": "2 - CC spont firing holding at -60 mV", "B": "339", "C": "42 pA"},
            50: {
                "A": "3 - CC excitability 20 pA to 200 pA holding at -60 mV",
                "B": "340-350",
                "C": "351",
                "D": "51 pA",
                "E": "47 pA",
            },
            52: {
                "A": "5 - CC rheobase 5 pA to 100 pA holding at -60 mV",
                "B": "385-405",
                "C": "406-426",
                "D": "35 pA",
            },
        }
        (block,) = read_cell_blocks(rows)
        block["source_sheet"] = "20230920 m011"
        cell_files = pd.DataFrame(
            dict(
                filename=["m011_0232-0242.h5", "m011_0339.h5", "m011_0340-0350.h5", "m011_0351-0361.h5"]
                + ["m011_0385-0405.h5", "m011_0406-0426.h5"],
                sweep_first=[232, 339, 340, 351, 385, 406],
                sweep_last=[242, 339, 350, 361, 405, 426],
            )
        )
        cell = SimpleNamespace(mouse_folder="20230920 608-011", cell_folder="m011 s2c1 +")
        held_run_rows = pd.DataFrame(get_held_run_rows(block=block, cell_files=cell_files, cell=cell))

        assert list(held_run_rows.filename) == [
            "m011_0339.h5",
            "m011_0340-0350.h5",
            "m011_0351-0361.h5",
            "m011_0385-0405.h5",
            "m011_0406-0426.h5",
        ]
        # One current per run is assigned in order; a row with fewer currents than runs leaves them blank
        assert list(held_run_rows.holding_current_pA) == ["42", "51", "47", "", ""]
        assert held_run_rows.extraction_note[2] == "logged as sweep 351, the first sweep of the file"
        assert held_run_rows.extraction_note[3] == "holding currents ['35 pA'] do not match the 2 runs of the row"

    def test_log_cell_metadata(self):
        cells = get_log_cell_metadata(mouse_folder="20230914 607-022")

        assert cells["m022 s2c1 +"]["electrode"] == {"resistance": "4.0 MOhm"}
        columns = cells["m022 s2c1 +"]["columns"]
        assert columns["pipette_offset"] == 24.97
        assert columns["time_of_recording"] == ""
        assert columns["holding_current_to_minus_70_mV"] == "+10"
        assert cells["m022 s1c4 +"]["columns"]["pipette_offset"] == 23.18
        assert cells["m022 s1c4 +"]["electrode"] == {}

    def test_log_cell_columns_skip_empty_columns(self):
        log_cells = {
            "m203 s1c1": dict(
                columns=dict(
                    pipette_offset=np.nan,
                    fast_capacitance_compensation=6.016,
                    time_of_recording="",
                    holding_current_to_minus_70_mV="",
                    resting_potential="-51",
                    bath_drugs="NBQX DAP5 GBZ",
                )
            ),
            "m203 s2c1": dict(
                columns=dict(
                    pipette_offset=np.nan,
                    fast_capacitance_compensation=np.nan,
                    time_of_recording="2:15",
                    holding_current_to_minus_70_mV="",
                    resting_potential="",
                    bath_drugs="NBQX DAP5 GBZ",
                )
            ),
        }
        assert list(get_log_cell_columns(log_cells)) == [
            "fast_capacitance_compensation",
            "time_of_recording",
            "resting_potential",
            "bath_drugs",
        ]

    def test_test_pulse_access_resistances(self):
        access_resistances = get_test_pulse_access_resistances(mouse_folder="20230914 607-022")

        assert access_resistances["m022_1924-1926.h5"] == 21.0
        assert access_resistances["m022_1927-1929.h5"] == 11.6

    def test_log_session_notes(self):
        assert get_log_session_notes(mouse_folder="20230912 611-006") == (
            "Log sheet: internal Kgluc for CC; surgery Beads SNL bilat, looks good; slicing outcome Good-ish, "
            "ventral side of slices kinda goofy; days since surgery 7 ish."
        )
        assert get_log_session_notes(mouse_folder="20230913 607-009") == "Log sheet: days since surgery 7 ish."
