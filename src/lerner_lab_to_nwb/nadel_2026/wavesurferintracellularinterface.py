"""Primary class for converting intracellular electrophysiology recorded with WaveSurfer."""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import h5py
import numpy as np
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from pydantic import FilePath
from pynwb import NWBFile
from pynwb.icephys import (
    CurrentClampSeries,
    CurrentClampStimulusSeries,
    IZeroClampSeries,
    VoltageClampSeries,
    VoltageClampStimulusSeries,
)

# WaveSurfer electrode mode -> (response class, stimulus class, unit of the command the amplifier expects)
MODE_TO_SERIES_CLASSES = {
    "cc": (CurrentClampSeries, CurrentClampStimulusSeries, "pA"),
    "vc": (VoltageClampSeries, VoltageClampStimulusSeries, "mV"),
    "i_equals_zero": (IZeroClampSeries, None, None),
}
UNIT_TO_SI_CONVERSION = {"mV": 1e-3, "pA": 1e-12, "V": 1.0, "A": 1.0}


class WaveSurferIntracellularInterface(BaseDataInterface):
    """Data interface for one WaveSurfer HDF5 file, which holds one run of one protocol from one electrode.

    Every sweep is written as its own response series (raw int16 ADC counts with the file's scaling) and, when the
    run drove a command, a stimulus series built from the stimulus library stored in the file header. Each sweep is
    one row of the intracellular recordings table and one simultaneous recording, and the run is one sequential
    recording whose stimulus type is the protocol file name.
    """

    display_name = "WaveSurfer Intracellular"
    keywords = ("intracellular electrophysiology", "patch clamp", "icephys", "wavesurfer")
    associated_suffixes = (".h5",)
    info = "Interface for intracellular electrophysiology recorded with WaveSurfer (Janelia)."

    def __init__(
        self,
        file_path: FilePath,
        electrode_name: str,
        voltage_clamp_holding_potential: Optional[float] = None,
        verbose: bool = False,
    ):
        """Initialize the interface.

        Parameters
        ----------
        file_path : FilePath
            Path to the WaveSurfer .h5 file.
        electrode_name : str
            Name of the IntracellularElectrode in metadata["Icephys"]["IntracellularElectrodes"] that recorded this run.
        voltage_clamp_holding_potential : float, optional
            Holding potential in mV set on the amplifier for voltage clamp runs. WaveSurfer stores the command relative
            to this holding potential, so it is written as the offset of the voltage clamp stimulus series.
            If None, the stimulus is written relative to the holding potential.
        verbose : bool, optional
            Whether to print verbose output, by default False
        """
        super().__init__(
            file_path=file_path,
            electrode_name=electrode_name,
            voltage_clamp_holding_potential=voltage_clamp_holding_potential,
            verbose=verbose,
        )
        self.sequential_recording_index = None
        self._starting_time = 0.0

        with h5py.File(file_path, "r") as file:
            header = file["header"]
            self.mode = read_strings(header["Ephys/ElectrodeManager/Electrodes/element1/Mode"])[0]
            self.protocol_name = Path(read_strings(header["AbsoluteProtocolFileName"])[0].replace("\\", "/")).stem
            clock_at_run_start = np.asarray(header["ClockAtRunStart"]).ravel()
            year, month, day, hour, minute = (int(value) for value in clock_at_run_start[:5])
            self.run_start_time = datetime(year, month, day, hour, minute) + timedelta(
                seconds=float(clock_at_run_start[5])
            )
            self.sampling_rate = float(np.asarray(header["Acquisition/SampleRate"]).ravel()[0])
            self.response_unit = read_strings(header["Acquisition/AnalogChannelUnits"])[0]
            response_scale = float(np.asarray(header["Acquisition/AnalogChannelScales"]).ravel()[0])
            scaling_coefficients = np.asarray(header["Acquisition/AnalogScalingCoefficients"])[0]
            self.stimulus_bindings = read_stimulus_bindings(header)
            self.sweep_names = sorted(name for name in file if name.startswith("sweep_"))

        # WaveSurfer converts ADC counts to volts with a cubic polynomial whose quadratic and cubic terms shift the
        # result by less than one ADC count over the int16 range, so the linear terms are an exact enough scaling.
        unit_conversion = UNIT_TO_SI_CONVERSION[self.response_unit]
        self.response_conversion = float(scaling_coefficients[1]) / response_scale * unit_conversion
        self.response_offset = float(scaling_coefficients[0]) / response_scale * unit_conversion

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        metadata["NWBFile"]["session_start_time"] = self.run_start_time
        return metadata

    def set_aligned_starting_time(self, aligned_starting_time: float) -> None:
        """Set the time of the run start in seconds relative to the session start."""
        self._starting_time = aligned_starting_time

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict) -> None:
        electrode = get_or_create_electrode(
            nwbfile=nwbfile, metadata=metadata, electrode_name=self.source_data["electrode_name"]
        )
        response_class, stimulus_class, command_unit = MODE_TO_SERIES_CLASSES[self.mode]
        simultaneous_recording_indices = []
        with h5py.File(self.source_data["file_path"], "r") as file:
            for sweep_position, sweep_name in enumerate(self.sweep_names, start=1):
                sweep_number = int(sweep_name.split("_")[1])
                # Sweep numbers can repeat within a recording day (the counter is per file prefix and can be reset),
                # while file names are unique within a day.
                series_name = f"{Path(self.source_data['file_path']).stem}_sweep_{sweep_number:04d}"
                data = file[sweep_name]["analogScans"][0]
                starting_time = self._starting_time + float(np.asarray(file[sweep_name]["timestamp"]).ravel()[0])
                response = response_class(
                    name=f"{series_name}_response",
                    description=f"Response recorded during sweep {sweep_number} of protocol '{self.protocol_name}'.",
                    data=data,
                    electrode=electrode,
                    gain=np.nan,
                    conversion=self.response_conversion,
                    offset=self.response_offset,
                    starting_time=starting_time,
                    rate=self.sampling_rate,
                    sweep_number=np.uint32(sweep_number),
                )
                nwbfile.add_acquisition(response)

                stimulus = None
                if stimulus_class is not None and len(self.stimulus_bindings) > 0:
                    stimulus = stimulus_class(
                        name=f"{series_name}_stimulus",
                        description=self.get_stimulus_description(command_unit=command_unit),
                        data=self.get_stimulus_waveform(
                            sweep_position=sweep_position, num_samples=data.size, command_unit=command_unit
                        ),
                        electrode=electrode,
                        gain=np.nan,
                        conversion=UNIT_TO_SI_CONVERSION[command_unit],
                        offset=self.get_stimulus_offset(),
                        starting_time=starting_time,
                        rate=self.sampling_rate,
                        sweep_number=np.uint32(sweep_number),
                    )
                    nwbfile.add_stimulus(stimulus)

                recording_index = nwbfile.add_intracellular_recording(
                    electrode=electrode, response=response, stimulus=stimulus
                )
                simultaneous_recording_indices.append(
                    nwbfile.add_icephys_simultaneous_recording(recordings=[recording_index])
                )
        self.sequential_recording_index = nwbfile.add_icephys_sequential_recording(
            stimulus_type=self.protocol_name, simultaneous_recordings=simultaneous_recording_indices
        )

    def get_stimulus_waveform(self, sweep_position: int, num_samples: int, command_unit: str) -> np.ndarray:
        """Build the command waveform of one sweep from the stimulus library, in the units of the command channel.

        Parameters
        ----------
        sweep_position : int
            1-based position of the sweep within the run, the `i` in WaveSurfer amplitude expressions.
        num_samples : int
            Number of samples in the sweep.
        command_unit : str
            Unit of the command the amplifier expects in this clamp mode. A stimulus bound to a channel with other
            units (a voltage clamp protocol run in current clamp, for example) did not reach the cell as specified,
            so the command is all zeros.
        """
        times = np.arange(num_samples) / self.sampling_rate
        waveform = np.zeros(num_samples, dtype="float32")
        for binding in self.stimulus_bindings:
            if binding["channel_unit"] != command_unit:
                continue
            if binding["type"] == "SquarePulse":
                pulses = [
                    (evaluate_amplitude(binding["amplitude"], sweep_position), binding["delay"], binding["duration"])
                ]
            elif binding["type"] == "TwoSquarePulses":
                second_pulse_delay = (
                    binding["delay"] + binding["first_pulse_duration"] + binding["delay_between_pulses"]
                )
                pulses = [
                    (binding["first_pulse_amplitude"], binding["delay"], binding["first_pulse_duration"]),
                    (binding["second_pulse_amplitude"], second_pulse_delay, binding["second_pulse_duration"]),
                ]
            else:
                raise NotImplementedError(f"WaveSurfer stimulus type '{binding['type']}' is not supported.")
            for amplitude, delay, duration in pulses:
                waveform[(times >= delay) & (times < delay + duration)] += amplitude * binding["multiplier"]
        return waveform

    def get_stimulus_offset(self) -> float:
        holding_potential = self.source_data["voltage_clamp_holding_potential"]
        if self.mode != "vc" or holding_potential is None:
            return 0.0
        return holding_potential * UNIT_TO_SI_CONVERSION["mV"]

    def get_stimulus_description(self, command_unit: str) -> str:
        bound_names = [binding["name"] for binding in self.stimulus_bindings if binding["channel_unit"] == command_unit]
        if len(bound_names) == 0:
            description = (
                f"No command was delivered: protocol '{self.protocol_name}' drives a channel in "
                f"{self.stimulus_bindings[0]['channel_unit']}, which does not match the clamp mode."
            )
        else:
            description = (
                f"Command built from the WaveSurfer stimulus library of protocol '{self.protocol_name}' "
                f"(stimuli: {', '.join(bound_names)})."
            )
        if self.get_stimulus_offset() != 0.0:
            description += (
                f" The data are relative to the holding potential of "
                f"{self.source_data['voltage_clamp_holding_potential']} mV set on the amplifier, which is the offset."
            )
        return description


def read_strings(dataset: h5py.Dataset) -> list:
    """Decode a MATLAB character array stored by WaveSurfer as a list of strings."""
    return [value.decode() if isinstance(value, bytes) else value for value in np.asarray(dataset).ravel().tolist()]


def read_stimulus_bindings(header: h5py.Group) -> list:
    """Return the stimuli of the selected stimulus map that drive one of the run's analog output channels."""
    output_channel_names = read_strings(header["Stimulation/AnalogChannelNames"])
    output_channel_units = read_strings(header["Stimulation/AnalogChannelUnits"])
    library = header["Stimulation/StimulusLibrary"]
    map_index = int(np.asarray(library["SelectedOutputableIndex"]).ravel()[0])
    stimulus_map = library[f"Maps/element{map_index}"]
    multipliers = np.asarray(stimulus_map["Multiplier"]).ravel()
    bindings = []
    for binding_index, channel_name in enumerate(read_strings(stimulus_map["ChannelName"]), start=1):
        if channel_name not in output_channel_names:
            continue
        stimulus_index = int(
            np.asarray(stimulus_map[f"IndexOfEachStimulusInLibrary/element{binding_index}"]).ravel()[0]
        )
        stimulus = library[f"Stimuli/element{stimulus_index}"]
        binding = dict(
            name=read_strings(stimulus["Name"])[0],
            type=read_strings(stimulus["TypeString"])[0],
            channel_unit=output_channel_units[output_channel_names.index(channel_name)],
            multiplier=float(multipliers[binding_index - 1]),
            amplitude=read_strings(stimulus["Amplitude"])[0],
            delay=float(read_strings(stimulus["Delay"])[0]),
            duration=float(read_strings(stimulus["Duration"])[0]),
        )
        if binding["type"] == "TwoSquarePulses":
            delegate = stimulus["Delegate"]
            binding.update(
                first_pulse_amplitude=float(read_strings(delegate["FirstPulseAmplitude"])[0]),
                first_pulse_duration=float(read_strings(delegate["FirstPulseDuration"])[0]),
                delay_between_pulses=float(read_strings(delegate["DelayBetweenPulses"])[0]),
                second_pulse_amplitude=float(read_strings(delegate["SecondPulseAmplitude"])[0]),
                second_pulse_duration=float(read_strings(delegate["SecondPulseDuration"])[0]),
            )
        bindings.append(binding)
    return bindings


def evaluate_amplitude(expression: str, sweep_position: int) -> float:
    """Evaluate a WaveSurfer amplitude expression such as '20*(i-1)', where i is the 1-based sweep position."""
    return float(eval(expression, {"__builtins__": {}}, {"i": sweep_position}))


def get_or_create_electrode(nwbfile: NWBFile, metadata: dict, electrode_name: str):
    """Return the named intracellular electrode, creating it and the icephys devices on first use."""
    if electrode_name in nwbfile.icephys_electrodes:
        return nwbfile.icephys_electrodes[electrode_name]
    for device_metadata in metadata["Icephys"]["Devices"]:
        if device_metadata["name"] not in nwbfile.devices:
            nwbfile.create_device(**device_metadata)
    electrode_metadata = metadata["Icephys"]["IntracellularElectrodes"][electrode_name]
    return nwbfile.create_icephys_electrode(
        name=electrode_name,
        device=nwbfile.devices[electrode_metadata["device_name"]],
        **{key: value for key, value in electrode_metadata.items() if key != "device_name"},
    )
