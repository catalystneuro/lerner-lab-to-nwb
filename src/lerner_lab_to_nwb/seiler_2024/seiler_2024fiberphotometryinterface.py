"""Primary class for converting experiment-specific fiber photometry."""
import numpy as np
from pynwb.file import NWBFile
from pynwb.core import DynamicTableRegion
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from neuroconv.tools import nwb_helpers
from pathlib import Path
from ndx_fiber_photometry import (
    FiberPhotometry,
    FiberPhotometryTable,
    FiberPhotometryResponseSeries,
    CommandedVoltageSeries,
    OpticalFiber,
    ExcitationSource,
    Photodetector,
    BandOpticalFilter,
    DichroicMirror,
    Indicator,
)
from tdt import read_block
import os
from contextlib import redirect_stdout
from typing import Optional

# Stereotaxic coordinates (AP, ML, DV) in mm from the Methods of Seiler et al. 2022
DMS_FIBER_COORDINATES_IN_MM = (0.8, 1.5, -2.8)
DLS_FIBER_COORDINATES_IN_MM = (-0.1, 2.8, -3.5)
MEDIAL_SNC_INJECTION_COORDINATES_IN_MM = (-3.1, 0.8, -4.7)
LATERAL_SNC_INJECTION_COORDINATES_IN_MM = (-3.1, 1.3, -4.2)


class Seiler2024FiberPhotometryInterface(BaseDataInterface):
    """Fiber Photometry interface for seiler_2024 conversion."""

    keywords = ["fiber photometry"]

    def __init__(self, folder_path: str, verbose: bool = True):
        super().__init__(
            folder_path=folder_path,
            verbose=verbose,
        )

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()
        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        return metadata_schema

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: dict,
        t2: Optional[float] = None,
        flip_ttls_lr: bool = False,
        has_demodulated_commanded_voltages: bool = True,
        second_folder_path: Optional[str] = None,
    ):
        # Load Data
        folder_path = Path(self.source_data["folder_path"])
        assert folder_path.is_dir(), f"Folder path {folder_path} does not exist."
        with open(os.devnull, "w") as f, redirect_stdout(f):
            if t2 is None:
                tdt_photometry = read_block(str(folder_path))
            else:
                tdt_photometry = read_block(str(folder_path), t2=t2)
            tdt_blocks = [tdt_photometry]
            if second_folder_path is not None:
                tdt_blocks.append(read_block(str(second_folder_path)))

        # Sessions split across blocks are joined with each block placed at its own start time
        block_start_times = get_block_start_times(tdt_blocks)
        commanded_voltage_stream_name = "Fi1d" if has_demodulated_commanded_voltages else "Fi1r"
        stream_name_to_timing_kwargs = {}
        for stream_name in ("Dv1A", "Dv2A", "Dv3B", "Dv4B", commanded_voltage_stream_name):
            rate = tdt_photometry.streams[stream_name].fs
            if len(tdt_blocks) == 1:
                stream_name_to_timing_kwargs[stream_name] = dict(starting_time=0.0, rate=rate)
                continue
            timestamps = [
                block_start_time + np.arange(tdt_block.streams[stream_name].data.shape[-1]) / rate
                for tdt_block, block_start_time in zip(tdt_blocks, block_start_times)
            ]
            stream_name_to_timing_kwargs[stream_name] = dict(timestamps=np.concatenate(timestamps))
            tdt_photometry.streams[stream_name].data = np.concatenate(
                [tdt_block.streams[stream_name].data for tdt_block in tdt_blocks], axis=-1
            )

        # Optical Fibers
        optical_fiber = OpticalFiber(
            name="optical_fiber",
            description="Fiber optic implants (Doric Lenses; 400 um, 0.48 NA) were placed above DMS (AP 0.8, ML 1.5, DV -2.8) and DLS (AP -0.1, ML 2.8, DV -3.5). The DMS implant was placed in the hemisphere receiving a medial SNc viral injection, while the DLS implant was placed in the hemisphere receiving a lateral SNc viral injection. Calcium signals from dopamine terminals in DMS and DLS were recorded during RI30, on the first and last days of RI60/RR20 training as well as on both footshock probes for each mouse. All recordings were done using a fiber photometry rig with optical components from Doric lenses controlled by a real-time processor from Tucker Davis Technologies (TDT; RZ5P). TDT Synapse software was used for data acquisition.",
            manufacturer="Doric Lenses",
            model="Fiber Optic Implant",
            numerical_aperture=0.48,
            core_diameter_in_um=400.0,
        )

        # Excitation Sources
        excitation_source_calcium_signal = ExcitationSource(
            name="excitation_source_calcium_signal",
            description="465nm and 405nm LEDs were modulated at 211 Hz and 330 Hz, respectively, for DMS probes. 465nm and 405nm LEDs were modulated at 450 Hz and 270 Hz, respectively for DLS probes. LED currents were adjusted in order to return a voltage between 150-200mV for each signal, were offset by 5 mA, were demodulated using a 4 Hz lowpass frequency filter.",
            manufacturer="Doric Lenses",
            model="Connectorized LED",
            illumination_type="LED",
            excitation_wavelength_in_nm=465.0,
        )
        excitation_source_isosbestic_control = ExcitationSource(
            name="excitation_source_isosbestic_control",
            description="465nm and 405nm LEDs were modulated at 211 Hz and 330 Hz, respectively, for DMS probes. 465nm and 405nm LEDs were modulated at 450 Hz and 270 Hz, respectively for DLS probes. LED currents were adjusted in order to return a voltage between 150-200mV for each signal, were offset by 5 mA, were demodulated using a 4 Hz lowpass frequency filter.",
            manufacturer="Doric Lenses",
            model="Connectorized LED",
            illumination_type="LED",
            excitation_wavelength_in_nm=405.0,
        )

        # Photodetector
        photodetector = Photodetector(
            name="photodetector",
            description="This battery-operated photoreceiver has high gain and detects CW light signals in the sub-picowatt to nanowatt range. When used in conjunction with a modulated light source and a lock-in amplifier to reduce the measurement bandwidth, it achieves sensitivity levels in the femtowatt range. Doric offer this Newport product with add-on fiber optic adapter that improves coupling efficiency between the large core, high NA optical fibers used in Fiber Photometry and relatively small detector area. Its output analog voltage (0-5 V) can be monitored with an oscilloscope or with a DAQ board to record the data with a computer.",
            manufacturer="Doric Lenses",
            model="Newport Visible Femtowatt Photoreceiver Module",
            detector_type="photodiode",
            detected_wavelength_in_nm=525.0,
            gain=1e10,
        )

        # Optical Filters
        emission_filter = BandOpticalFilter(
            name="emission_filter",
            description="Dual excitation band fiber photometry measurements use a Fluorescence Mini Cube with 4 ports: one port for the functional fluorescence excitation light, one for the isosbestic excitation, one for the fluorescence detection, and one for the sample. The cube has dichroic mirrors to combine isosbestic and fluorescence excitations and separate the fluorescence emission and narrow bandpass filters limiting the excitation fluorescence spectrum.",
            manufacturer="Doric Lenses",
            model="4 ports Fluorescence Mini Cube - GCaMP",
            center_wavelength_in_nm=525.0,
            bandwidth_in_nm=50.0,
            filter_type="Bandpass",
        )
        excitation_filter = BandOpticalFilter(
            name="excitation_filter",
            description="Dual excitation band fiber photometry measurements use a Fluorescence Mini Cube with 4 ports: one port for the functional fluorescence excitation light, one for the isosbestic excitation, one for the fluorescence detection, and one for the sample. The cube has dichroic mirrors to combine isosbestic and fluorescence excitations and separate the fluorescence emission and narrow bandpass filters limiting the excitation fluorescence spectrum.",
            manufacturer="Doric Lenses",
            model="4 ports Fluorescence Mini Cube - GCaMP",
            center_wavelength_in_nm=475.0,
            bandwidth_in_nm=30.0,
            filter_type="Bandpass",
        )
        isosbestic_excitation_filter = BandOpticalFilter(
            name="isosbestic_excitation_filter",
            description="Dual excitation band fiber photometry measurements use a Fluorescence Mini Cube with 4 ports: one port for the functional fluorescence excitation light, one for the isosbestic excitation, one for the fluorescence detection, and one for the sample. The cube has dichroic mirrors to combine isosbestic and fluorescence excitations and separate the fluorescence emission and narrow bandpass filters limiting the excitation fluorescence spectrum.",
            manufacturer="Doric Lenses",
            model="4 ports Fluorescence Mini Cube - GCaMP",
            center_wavelength_in_nm=405.0,
            bandwidth_in_nm=10.0,
            filter_type="Bandpass",
        )

        # Dichroic Mirror
        dichroic_mirror = DichroicMirror(
            name="dichroic_mirror",
            description="Dual excitation band fiber photometry measurements use a Fluorescence Mini Cube with 4 ports: one port for the functional fluorescence excitation light, one for the isosbestic excitation, one for the fluorescence detection, and one for the sample. The cube has dichroic mirrors to combine isosbestic and fluorescence excitations and separate the fluorescence emission and narrow bandpass filters limiting the excitation fluorescence spectrum.",
            manufacturer="Doric Lenses",
            model="4 ports Fluorescence Mini Cube - GCaMP",
        )

        # Indicators (aka Fluorophores)
        dms_green_fluorophore = Indicator(
            name="dms_green_fluorophore",
            description="Mice for fiber photometry experiments received infusions of 1ml of AAV5-CAG-FLEX-jGCaMP7b-WPRE (1.02e13 vg/mL, Addgene, lot 18-429) into lateral SNc (AP -3.1, ML 1.3, DV -4.2) in one hemisphere and medial SNc (AP -3.1, ML 0.8, DV -4.7) in the other. Hemispheres were counterbalanced between mice.",
            manufacturer="Addgene",
            label="GCaMP7b",
            injection_location="medial SNc",
            injection_coordinates_in_mm=MEDIAL_SNC_INJECTION_COORDINATES_IN_MM,
        )
        dls_green_fluorophore = Indicator(
            name="dls_green_fluorophore",
            description="Mice for fiber photometry experiments received infusions of 1ml of AAV5-CAG-FLEX-jGCaMP7b-WPRE (1.02e13 vg/mL, Addgene, lot 18-429) into lateral SNc (AP -3.1, ML 1.3, DV -4.2) in one hemisphere and medial SNc (AP -3.1, ML 0.8, DV -4.7) in the other. Hemispheres were counterbalanced between mice.",
            manufacturer="Addgene",
            label="GCaMP7b",
            injection_location="lateral SNc",
            injection_coordinates_in_mm=LATERAL_SNC_INJECTION_COORDINATES_IN_MM,
        )

        # Commanded Voltage Series
        if has_demodulated_commanded_voltages:
            commanded_voltage_series_dms_calcium_signal = CommandedVoltageSeries(
                name="commanded_voltage_series_dms_calcium_signal",
                description="The commanded voltage for the DMS calcium signal.",
                data=tdt_photometry.streams["Fi1d"].data[0, :],
                unit="volts",
                frequency=211.0,
                **stream_name_to_timing_kwargs["Fi1d"],
            )
            commanded_voltage_series_dms_isosbestic_control = CommandedVoltageSeries(
                name="commanded_voltage_series_dms_isosbestic_control",
                description="The commanded voltage for the DMS isosbestic control.",
                data=tdt_photometry.streams["Fi1d"].data[1, :],
                unit="volts",
                frequency=330.0,
                **stream_name_to_timing_kwargs["Fi1d"],
            )
            commanded_voltage_series_dls_calcium_signal = CommandedVoltageSeries(
                name="commanded_voltage_series_dls_calcium_signal",
                description="The commanded voltage for the DLS calcium signal.",
                data=tdt_photometry.streams["Fi1d"].data[2, :],
                unit="volts",
                frequency=450.0,
                **stream_name_to_timing_kwargs["Fi1d"],
            )
            commanded_voltage_series_dls_isosbestic_control = CommandedVoltageSeries(
                name="commanded_voltage_series_dls_isosbestic_control",
                description="The commanded voltage for the DLS isosbestic control.",
                data=tdt_photometry.streams["Fi1d"].data[3, :],
                unit="volts",
                frequency=270.0,
                **stream_name_to_timing_kwargs["Fi1d"],
            )
        elif tdt_photometry.streams["Fi1r"].data.shape[0] == 6:
            has_demodulated_commanded_voltages = (
                True  # Some sessions have demodulated commanded voltages hiding in Fi1r
            )
            commanded_voltage_series_dms_calcium_signal = CommandedVoltageSeries(
                name="commanded_voltage_series_dms_calcium_signal",
                description="The commanded voltage for the DMS calcium signal.",
                data=tdt_photometry.streams["Fi1r"].data[0, :],
                unit="volts",
                frequency=211.0,
                **stream_name_to_timing_kwargs["Fi1r"],
            )
            commanded_voltage_series_dms_isosbestic_control = CommandedVoltageSeries(
                name="commanded_voltage_series_dms_isosbestic_control",
                description="The commanded voltage for the DMS isosbestic control.",
                data=tdt_photometry.streams["Fi1r"].data[1, :],
                unit="volts",
                frequency=330.0,
                **stream_name_to_timing_kwargs["Fi1r"],
            )
            commanded_voltage_series_dls_calcium_signal = CommandedVoltageSeries(
                name="commanded_voltage_series_dls_calcium_signal",
                description="The commanded voltage for the DLS calcium signal.",
                data=tdt_photometry.streams["Fi1r"].data[2, :],
                unit="volts",
                **stream_name_to_timing_kwargs["Fi1r"],
                frequency=450.0,
            )
            commanded_voltage_series_dls_isosbestic_control = CommandedVoltageSeries(
                name="commanded_voltage_series_dls_isosbestic_control",
                description="The commanded voltage for the DLS isosbestic control.",
                data=tdt_photometry.streams["Fi1r"].data[3, :],
                unit="volts",
                frequency=270.0,
                **stream_name_to_timing_kwargs["Fi1r"],
            )
        else:
            assert (
                tdt_photometry.streams["Fi1r"].data.shape[0] == 2
            ), f"Fi1r should have 6 arrays or 2 arrays, but it has {tdt_photometry.streams['Fi1r'].data.shape[0]}"
            commanded_voltage_series_dms = CommandedVoltageSeries(
                name="commanded_voltage_series_dms",
                description="The commanded voltage for the frequency-modulated DMS calcium signal and DMS isosbestic control.",
                data=tdt_photometry.streams["Fi1r"].data[0, :],
                unit="volts",
                **stream_name_to_timing_kwargs["Fi1r"],
            )
            commanded_voltage_series_dls = CommandedVoltageSeries(
                name="commanded_voltage_series_dls",
                description="The commanded voltage for the frequency-modulated DLS calcium signal and DLS isosbestic control.",
                data=tdt_photometry.streams["Fi1r"].data[1, :],
                unit="volts",
                **stream_name_to_timing_kwargs["Fi1r"],
            )

        # Fiber Photometry Table
        fiber_photometry_table = FiberPhotometryTable(
            name="fiber_photometry_table",
            description="Fiber optic implants (Doric Lenses; 400 um, 0.48 NA) were placed above DMS (AP 0.8, ML 1.5, DV -2.8) and DLS (AP -0.1, ML 2.8, DV -3.5). The DMS implant was placed in the hemisphere receiving a medial SNc viral injection, while the DLS implant was placed in the hemisphere receiving a lateral SNc viral injection. Calcium signals from dopamine terminals in DMS and DLS were recorded during RI30, on the first and last days of RI60/RR20 training as well as on both footshock probes for each mouse. All recordings were done using a fiber photometry rig with optical components from Doric lenses controlled by a real-time processor from Tucker Davis Technologies (TDT; RZ5P). TDT Synapse software was used for data acquisition.",
        )
        if has_demodulated_commanded_voltages:
            fiber_photometry_table.add_row(
                location="DMS",
                coordinates=DMS_FIBER_COORDINATES_IN_MM,
                commanded_voltage_series=commanded_voltage_series_dms_calcium_signal,
                indicator=dms_green_fluorophore,
                optical_fiber=optical_fiber,
                excitation_source=excitation_source_calcium_signal,
                photodetector=photodetector,
                excitation_filter=excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
            fiber_photometry_table.add_row(
                location="DMS",
                coordinates=DMS_FIBER_COORDINATES_IN_MM,
                commanded_voltage_series=commanded_voltage_series_dms_isosbestic_control,
                indicator=dms_green_fluorophore,
                optical_fiber=optical_fiber,
                excitation_source=excitation_source_isosbestic_control,
                photodetector=photodetector,
                excitation_filter=isosbestic_excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
            fiber_photometry_table.add_row(
                location="DLS",
                coordinates=DLS_FIBER_COORDINATES_IN_MM,
                commanded_voltage_series=commanded_voltage_series_dls_calcium_signal,
                indicator=dls_green_fluorophore,
                optical_fiber=optical_fiber,
                excitation_source=excitation_source_calcium_signal,
                photodetector=photodetector,
                excitation_filter=excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
            fiber_photometry_table.add_row(
                location="DLS",
                coordinates=DLS_FIBER_COORDINATES_IN_MM,
                commanded_voltage_series=commanded_voltage_series_dls_isosbestic_control,
                indicator=dls_green_fluorophore,
                optical_fiber=optical_fiber,
                excitation_source=excitation_source_isosbestic_control,
                photodetector=photodetector,
                excitation_filter=isosbestic_excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
        else:
            fiber_photometry_table.add_row(
                location="DMS",
                coordinates=DMS_FIBER_COORDINATES_IN_MM,
                commanded_voltage_series=commanded_voltage_series_dms,
                indicator=dms_green_fluorophore,
                optical_fiber=optical_fiber,
                excitation_source=excitation_source_calcium_signal,
                photodetector=photodetector,
                excitation_filter=excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
            fiber_photometry_table.add_row(
                location="DMS",
                coordinates=DMS_FIBER_COORDINATES_IN_MM,
                commanded_voltage_series=commanded_voltage_series_dms,
                indicator=dms_green_fluorophore,
                optical_fiber=optical_fiber,
                excitation_source=excitation_source_isosbestic_control,
                photodetector=photodetector,
                excitation_filter=isosbestic_excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
            fiber_photometry_table.add_row(
                location="DLS",
                coordinates=DLS_FIBER_COORDINATES_IN_MM,
                commanded_voltage_series=commanded_voltage_series_dls,
                indicator=dls_green_fluorophore,
                optical_fiber=optical_fiber,
                excitation_source=excitation_source_calcium_signal,
                photodetector=photodetector,
                excitation_filter=excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
            fiber_photometry_table.add_row(
                location="DLS",
                coordinates=DLS_FIBER_COORDINATES_IN_MM,
                commanded_voltage_series=commanded_voltage_series_dls,
                indicator=dls_green_fluorophore,
                optical_fiber=optical_fiber,
                excitation_source=excitation_source_isosbestic_control,
                photodetector=photodetector,
                excitation_filter=isosbestic_excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
        fiber_photometry_table_region = fiber_photometry_table.create_fiber_photometry_table_region(
            description="The region of the FiberPhotometryTable corresponding to the DMS calcium signal, DMS isosbestic control, DLS calcium signal, and DLS isosbestic control.",
            region=[0, 1, 2, 3],
        )
        fiber_photometry_table_metadata = FiberPhotometry(
            name="fiber_photometry",
            fiber_photometry_table=fiber_photometry_table,
        )

        # Fiber Photometry Response Series
        fiber_photometry_data = np.column_stack(
            (
                tdt_photometry.streams["Dv2A"].data,
                tdt_photometry.streams["Dv1A"].data,
                tdt_photometry.streams["Dv4B"].data,
                tdt_photometry.streams["Dv3B"].data,
            ),
        )
        fiber_photometry_response_series = FiberPhotometryResponseSeries(
            name="fiber_photometry_response_series",
            description="The fluorescence from the DMS calcium signal, DMS isosbestic control, DLS calcium signal, and DLS isosbestic control.",
            data=fiber_photometry_data,
            unit="a.u.",
            **stream_name_to_timing_kwargs["Dv1A"],
            fiber_photometry_table_region=fiber_photometry_table_region,
        )

        nwbfile.add_device(optical_fiber)
        nwbfile.add_device(excitation_source_calcium_signal)
        nwbfile.add_device(excitation_source_isosbestic_control)
        nwbfile.add_device(photodetector)
        nwbfile.add_device(excitation_filter)
        nwbfile.add_device(isosbestic_excitation_filter)
        nwbfile.add_device(emission_filter)
        nwbfile.add_device(dichroic_mirror)
        nwbfile.add_device(dms_green_fluorophore)
        nwbfile.add_device(dls_green_fluorophore)
        if has_demodulated_commanded_voltages:
            nwbfile.add_acquisition(commanded_voltage_series_dms_calcium_signal)
            nwbfile.add_acquisition(commanded_voltage_series_dms_isosbestic_control)
            nwbfile.add_acquisition(commanded_voltage_series_dls_calcium_signal)
            nwbfile.add_acquisition(commanded_voltage_series_dls_isosbestic_control)
        else:
            nwbfile.add_acquisition(commanded_voltage_series_dms)
            nwbfile.add_acquisition(commanded_voltage_series_dls)
        nwbfile.add_lab_meta_data(fiber_photometry_table_metadata)
        nwbfile.add_acquisition(fiber_photometry_response_series)


def get_block_start_times(tdt_blocks: list) -> list[float]:
    """Get the start time of each TDT block in seconds relative to the start of the first block.

    Parameters
    ----------
    tdt_blocks : list
        The TDT blocks of a session, in recording order, as returned by tdt.read_block.

    Returns
    -------
    list[float]
        The start time of each block relative to the first block.
    """
    first_start_date = tdt_blocks[0].info.start_date
    return [(tdt_block.info.start_date - first_start_date).total_seconds() for tdt_block in tdt_blocks]
