from datetime import datetime
from pathlib import Path

import h5py
import numpy as np
import pytest
from pynwb.icephys import CurrentClampSeries, IZeroClampSeries, VoltageClampSeries
from pynwb.testing.mock.file import mock_NWBFile

from lerner_lab_to_nwb.nadel_2026 import Nadel2026NWBConverter, WaveSurferIntracellularInterface

# 10 Hz keeps sweeps short enough to write expected values by hand: a 2 s sweep is 20 samples.
SAMPLING_RATE = 10.0
SWEEP_DURATION = 2.0


def write_wavesurfer_file(
    file_path: Path,
    *,
    mode: str,
    clock_at_run_start: list,
    response_units: str,
    output_channel_name: str,
    output_channel_unit: str,
    stimuli: list,
    sweep_timestamps: list,
    first_sweep_number: int,
    protocol_name: str,
):
    """Write a minimal WaveSurfer 0.945 file holding the header fields the interface reads."""

    def strings(values):
        return np.array([value.encode() for value in values])

    num_samples = int(SAMPLING_RATE * SWEEP_DURATION)
    with h5py.File(file_path, "w") as file:
        header = file.create_group("header")
        header["Ephys/ElectrodeManager/Electrodes/element1/Mode"] = strings([mode])
        header["AbsoluteProtocolFileName"] = strings([f"R:\\protocols\\{protocol_name}.cfg"])
        header["ClockAtRunStart"] = np.array(clock_at_run_start, dtype=float).reshape(-1, 1)
        header["Acquisition/SampleRate"] = np.array([[SAMPLING_RATE]])
        header["Acquisition/AnalogChannelUnits"] = strings([response_units, output_channel_unit])
        header["Acquisition/AnalogChannelScales"] = np.array([[0.01], [0.0025]])
        header["Acquisition/AnalogScalingCoefficients"] = np.array([[0.1, 0.0003, 0.0, 0.0], [0.1, 0.0003, 0.0, 0.0]])
        header["Stimulation/AnalogChannelNames"] = strings([output_channel_name])
        header["Stimulation/AnalogChannelUnits"] = strings([output_channel_unit])
        library = header.create_group("Stimulation/StimulusLibrary")
        library["SelectedOutputableIndex"] = np.array([[1.0]])
        library["Maps/element1/ChannelName"] = strings([output_channel_name] * len(stimuli))
        library["Maps/element1/Multiplier"] = np.ones((1, len(stimuli)))
        for stimulus_index, stimulus in enumerate(stimuli, start=1):
            library[f"Maps/element1/IndexOfEachStimulusInLibrary/element{stimulus_index}"] = np.array(
                [[stimulus_index]]
            )
            group = library.create_group(f"Stimuli/element{stimulus_index}")
            for field in ("Name", "TypeString", "Amplitude", "Delay", "Duration"):
                group[field] = strings([stimulus[field]])
            for field, value in stimulus.get("Delegate", {}).items():
                group[f"Delegate/{field}"] = strings([value])
        for sweep_number, timestamp in enumerate(sweep_timestamps, start=first_sweep_number):
            counts = np.full((2, num_samples), sweep_number - first_sweep_number, dtype="int16")
            file[f"sweep_{sweep_number:04d}/analogScans"] = counts
            file[f"sweep_{sweep_number:04d}/timestamp"] = np.array([[timestamp]])


CURRENT_STEPS = dict(
    Name="Current Steps delta 20 pA", TypeString="SquarePulse", Amplitude="20*(i-1)", Delay="0.5", Duration="0.5"
)
DEPOLARIZING_AND_HYPERPOLARIZING_STEP = dict(
    Name="Depol and Hyperpol Step",
    TypeString="TwoSquarePulses",
    Amplitude="1",
    Delay="0.5",
    Duration="1",
    Delegate=dict(
        FirstPulseAmplitude="30",
        FirstPulseDuration="0.5",
        DelayBetweenPulses="0",
        SecondPulseAmplitude="-50",
        SecondPulseDuration="0.5",
    ),
)
TEST_PULSE = dict(Name="Test pulse (50 ms)", TypeString="SquarePulse", Amplitude="-5", Delay="0.1", Duration="0.1")


@pytest.fixture
def current_clamp_file_path(tmp_path) -> Path:
    file_path = tmp_path / "m203_0571-0573.h5"
    write_wavesurfer_file(
        file_path,
        mode="cc",
        clock_at_run_start=[2025, 2, 13, 16, 58, 12.5],
        response_units="mV",
        output_channel_name="Command Current 1",
        output_channel_unit="pA",
        stimuli=[CURRENT_STEPS],
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
        output_channel_name="Command Voltage 1",
        output_channel_unit="mV",
        stimuli=[DEPOLARIZING_AND_HYPERPOLARIZING_STEP],
        sweep_timestamps=[1.0],
        first_sweep_number=610,
        protocol_name="PA_Ch1_WC_VC_Ih test",
    )
    return file_path


@pytest.fixture
def reset_counter_file_path(tmp_path) -> Path:
    # A later run whose sweep counter was set back, so its first sweep repeats the last sweep number of m203_0571-0573
    file_path = tmp_path / "m203_0573-0575.h5"
    write_wavesurfer_file(
        file_path,
        mode="vc",
        clock_at_run_start=[2025, 2, 13, 17, 1, 0.0],
        response_units="pA",
        output_channel_name="Command Voltage 1",
        output_channel_unit="mV",
        stimuli=[TEST_PULSE],
        sweep_timestamps=[0.5, 1.0, 1.5],
        first_sweep_number=573,
        protocol_name="PA_Ch1_WC_VC_test pulse",
    )
    return file_path


@pytest.fixture
def test_pulse_in_current_clamp_file_path(tmp_path) -> Path:
    file_path = tmp_path / "m114_0433.h5"
    write_wavesurfer_file(
        file_path,
        mode="cc",
        clock_at_run_start=[2025, 3, 10, 13, 18, 8.0],
        response_units="mV",
        output_channel_name="Command Voltage 1",
        output_channel_unit="mV",
        stimuli=[TEST_PULSE],
        sweep_timestamps=[0.5],
        first_sweep_number=433,
        protocol_name="PA_Ch1_WC_VC_test pulse",
    )
    return file_path


@pytest.fixture
def izero_file_path(tmp_path) -> Path:
    file_path = tmp_path / "m401_0360.h5"
    write_wavesurfer_file(
        file_path,
        mode="i_equals_zero",
        clock_at_run_start=[2025, 10, 15, 14, 39, 19.0],
        response_units="mV",
        output_channel_name="Command Current 1",
        output_channel_unit="pA",
        stimuli=[dict(Name="nothing", TypeString="SquarePulse", Amplitude="0", Delay="0", Duration="0")],
        sweep_timestamps=[0.5],
        first_sweep_number=360,
        protocol_name="PA_Ch1_CC spont firing for 30s",
    )
    return file_path


@pytest.fixture
def metadata() -> dict:
    return dict(
        Icephys=dict(
            Devices=[dict(name="MultiClamp700B", description="MultiClamp 700B patch clamp amplifier.")],
            IntracellularElectrodes=dict(
                electrode_m203_s3c2=dict(
                    device_name="MultiClamp700B", description="Patch pipette.", cell_id="m203 s3c2"
                )
            ),
            Cells=dict(electrode_m203_s3c2=dict(in_paper=True)),
            CellColumns=dict(in_paper="Whether the cell is in the paper."),
        )
    )


class TestWaveSurferIntracellularInterface:
    def test_run_start_time(self, current_clamp_file_path):
        interface = WaveSurferIntracellularInterface(
            file_path=current_clamp_file_path, electrode_name="electrode_m203_s3c2"
        )
        assert interface.get_metadata()["NWBFile"]["session_start_time"] == datetime(2025, 2, 13, 16, 58, 12, 500000)

    def test_current_clamp_response(self, current_clamp_file_path, metadata):
        interface = WaveSurferIntracellularInterface(
            file_path=current_clamp_file_path, electrode_name="electrode_m203_s3c2"
        )
        interface.set_aligned_starting_time(10.0)
        nwbfile = mock_NWBFile()
        interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

        response = nwbfile.acquisition["m203_0571-0573_sweep_0572_response"]
        assert isinstance(response, CurrentClampSeries)
        assert response.sweep_number == 572
        # volts = (0.1 + 0.0003 * counts) / (0.01 V/mV) * 1e-3 V/mV
        assert response.conversion == pytest.approx(3e-5)
        assert response.offset == pytest.approx(0.01)
        assert response.starting_time == pytest.approx(12.9)
        assert response.rate == SAMPLING_RATE
        np.testing.assert_array_equal(response.data, np.ones(20, dtype="int16"))

    def test_current_clamp_stimulus(self, current_clamp_file_path, metadata):
        interface = WaveSurferIntracellularInterface(
            file_path=current_clamp_file_path, electrode_name="electrode_m203_s3c2"
        )
        nwbfile = mock_NWBFile()
        interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

        # Third sweep of the run: 20 * (3 - 1) = 40 pA from 0.5 s to 1.0 s, samples 5 to 9 at 10 Hz
        stimulus = nwbfile.stimulus["m203_0571-0573_sweep_0573_stimulus"]
        expected = np.zeros(20, dtype="float32")
        expected[5:10] = 40.0
        np.testing.assert_array_equal(stimulus.data, expected)
        assert stimulus.conversion == 1e-12
        assert stimulus.offset == 0.0

    def test_voltage_clamp_stimulus(self, voltage_clamp_file_path, metadata):
        interface = WaveSurferIntracellularInterface(
            file_path=voltage_clamp_file_path,
            electrode_name="electrode_m203_s3c2",
            voltage_clamp_holding_potential=-70.0,
        )
        nwbfile = mock_NWBFile()
        interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

        assert isinstance(nwbfile.acquisition["m203_0610_sweep_0610_response"], VoltageClampSeries)
        # +30 mV from 0.5 to 1.0 s, then -50 mV from 1.0 to 1.5 s, relative to the -70 mV holding potential
        stimulus = nwbfile.stimulus["m203_0610_sweep_0610_stimulus"]
        expected = np.zeros(20, dtype="float32")
        expected[5:10] = 30.0
        expected[10:15] = -50.0
        np.testing.assert_array_equal(stimulus.data, expected)
        assert stimulus.conversion == 1e-3
        assert stimulus.offset == pytest.approx(-0.07)

    def test_command_that_does_not_match_the_clamp_mode(self, test_pulse_in_current_clamp_file_path, metadata):
        interface = WaveSurferIntracellularInterface(
            file_path=test_pulse_in_current_clamp_file_path, electrode_name="electrode_m203_s3c2"
        )
        nwbfile = mock_NWBFile()
        interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

        stimulus = nwbfile.stimulus["m114_0433_sweep_0433_stimulus"]
        np.testing.assert_array_equal(stimulus.data, np.zeros(20, dtype="float32"))
        assert stimulus.description.startswith("No command was delivered")

    def test_izero_has_no_stimulus(self, izero_file_path, metadata):
        interface = WaveSurferIntracellularInterface(file_path=izero_file_path, electrode_name="electrode_m203_s3c2")
        nwbfile = mock_NWBFile()
        interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

        assert isinstance(nwbfile.acquisition["m401_0360_sweep_0360_response"], IZeroClampSeries)
        assert len(nwbfile.stimulus) == 0

    def test_icephys_tables(self, current_clamp_file_path, metadata):
        interface = WaveSurferIntracellularInterface(
            file_path=current_clamp_file_path, electrode_name="electrode_m203_s3c2"
        )
        nwbfile = mock_NWBFile()
        interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

        assert len(nwbfile.intracellular_recordings) == 3
        assert len(nwbfile.icephys_simultaneous_recordings) == 3
        sequential_recordings = nwbfile.get_icephys_sequential_recordings()
        assert sequential_recordings["stimulus_type"].data == ["PA_Ch1_CC excitability 20 pA steps to 200 pA"]
        assert interface.sequential_recording_index == 0


class TestNadel2026NWBConverter:
    def test_session_start_time(self, current_clamp_file_path, voltage_clamp_file_path):
        converter = Nadel2026NWBConverter(
            data_interfaces=dict(
                voltage_clamp=WaveSurferIntracellularInterface(
                    file_path=voltage_clamp_file_path, electrode_name="electrode_m203_s3c2"
                ),
                current_clamp=WaveSurferIntracellularInterface(
                    file_path=current_clamp_file_path, electrode_name="electrode_m203_s3c2"
                ),
            )
        )
        assert converter.get_metadata()["NWBFile"]["session_start_time"] == datetime(2025, 2, 13, 16, 58, 12, 500000)

    def test_runs_on_one_timeline(self, current_clamp_file_path, voltage_clamp_file_path, metadata):
        converter = Nadel2026NWBConverter(
            data_interfaces=dict(
                voltage_clamp=WaveSurferIntracellularInterface(
                    file_path=voltage_clamp_file_path, electrode_name="electrode_m203_s3c2"
                ),
                current_clamp=WaveSurferIntracellularInterface(
                    file_path=current_clamp_file_path, electrode_name="electrode_m203_s3c2"
                ),
            )
        )
        metadata["NWBFile"] = dict(session_start_time=datetime(2025, 2, 13, 16, 58, 12, 500000))
        converter.temporally_align_data_interfaces(metadata=metadata)
        nwbfile = mock_NWBFile()
        converter.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

        # The voltage clamp run started at 17:00:02.5, 110 s after the current clamp run, and its sweep 1 s later
        assert nwbfile.acquisition["m203_0571-0573_sweep_0571_response"].starting_time == pytest.approx(0.7)
        assert nwbfile.acquisition["m203_0610_sweep_0610_response"].starting_time == pytest.approx(111.0)
        sequential_recordings = nwbfile.get_icephys_sequential_recordings()
        assert list(sequential_recordings["source_file"].data) == ["m203_0571-0573.h5", "m203_0610.h5"]
        assert len(nwbfile.get_icephys_repetitions()) == 2
        assert list(nwbfile.intracellular_recordings.category_tables["electrodes"]["in_paper"].data) == [True] * 4

    def test_repeated_sweep_numbers(self, current_clamp_file_path, reset_counter_file_path, metadata):
        converter = Nadel2026NWBConverter(
            data_interfaces=dict(
                current_clamp=WaveSurferIntracellularInterface(
                    file_path=current_clamp_file_path, electrode_name="electrode_m203_s3c2"
                ),
                test_pulse=WaveSurferIntracellularInterface(
                    file_path=reset_counter_file_path, electrode_name="electrode_m203_s3c2"
                ),
            )
        )
        metadata["NWBFile"] = dict(session_start_time=datetime(2025, 2, 13, 16, 58, 12, 500000))
        converter.temporally_align_data_interfaces(metadata=metadata)
        nwbfile = mock_NWBFile()
        converter.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)

        assert isinstance(nwbfile.acquisition["m203_0571-0573_sweep_0573_response"], CurrentClampSeries)
        assert isinstance(nwbfile.acquisition["m203_0573-0575_sweep_0573_response"], VoltageClampSeries)
