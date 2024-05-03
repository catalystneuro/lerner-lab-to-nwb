"""Primary class for converting experiment-specific fiber photometry."""
import numpy as np
from pynwb.file import NWBFile
from pynwb.core import DynamicTableRegion
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from neuroconv.tools import nwb_helpers
from pathlib import Path
from ndx_fiber_photometry import (
    FiberPhotometryTable,
    FiberPhotometryResponseSeries,
    CommandedVoltageSeries,
    OpticalFiber,
    ExcitationSource,
    Photodetector,
    OpticalFilter,
    DichroicMirror,
    Indicator,
)
from hdmf.backends.hdf5.h5_utils import H5DataIO
from tdt import read_block
import os
from contextlib import redirect_stdout
from typing import Optional


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
            if second_folder_path is not None:
                tdt_photometry2 = read_block(str(second_folder_path))
                tdt_photometry.streams["Dv1A"].data = np.concatenate(
                    [tdt_photometry.streams["Dv1A"].data, tdt_photometry2.streams["Dv1A"].data], axis=0
                )
                tdt_photometry.streams["Dv2A"].data = np.concatenate(
                    [tdt_photometry.streams["Dv2A"].data, tdt_photometry2.streams["Dv2A"].data], axis=0
                )
                tdt_photometry.streams["Dv3B"].data = np.concatenate(
                    [tdt_photometry.streams["Dv3B"].data, tdt_photometry2.streams["Dv3B"].data], axis=0
                )
                tdt_photometry.streams["Dv4B"].data = np.concatenate(
                    [tdt_photometry.streams["Dv4B"].data, tdt_photometry2.streams["Dv4B"].data], axis=0
                )
                if has_demodulated_commanded_voltages:
                    tdt_photometry.streams["Fi1d"].data = np.concatenate(
                        [tdt_photometry.streams["Fi1d"].data, tdt_photometry2.streams["Fi1d"].data], axis=1
                    )
                else:
                    tdt_photometry.streams["Fi1r"].data = np.concatenate(
                        [tdt_photometry.streams["Fi1r"].data, tdt_photometry2.streams["Fi1r"].data], axis=1
                    )

        # Optical Fibers
        dms_fiber = OpticalFiber(
            name="dms_fiber",
            description="Fiber optic implants (Doric Lenses; 400 um, 0.48 NA) were placed above DMS (AP 0.8, ML 1.5, DV 2.8) and DLS (AP 0.1, ML 2.8, DV 3.5). The DMS implant was placed in the hemisphere receiving a medial SNc viral injection, while the DLS implant was placed in the hemisphere receiving a lateral SNc viral injection. Calcium signals from dopamine terminals in DMS and DLS were recorded during RI30, on the first and last days of RI60/RR20 training as well as on both footshock probes for each mouse. All recordings were done using a fiber photometry rig with optical components from Doric lenses controlled by a real-time processor from Tucker Davis Technologies (TDT; RZ5P). TDT Synapse software was used for data acquisition.",
            manufacturer="Doric Lenses",
            model="Fiber Optic Implant",
            numerical_aperture=0.48,
            core_diameter_in_um=400.0,
        )
        dls_fiber = OpticalFiber(
            name="dls_fiber",
            description="Fiber optic implants (Doric Lenses; 400 um, 0.48 NA) were placed above DMS (AP 0.8, ML 1.5, DV 2.8) and DLS (AP 0.1, ML 2.8, DV 3.5). The DMS implant was placed in the hemisphere receiving a medial SNc viral injection, while the DLS implant was placed in the hemisphere receiving a lateral SNc viral injection. Calcium signals from dopamine terminals in DMS and DLS were recorded during RI30, on the first and last days of RI60/RR20 training as well as on both footshock probes for each mouse. All recordings were done using a fiber photometry rig with optical components from Doric lenses controlled by a real-time processor from Tucker Davis Technologies (TDT; RZ5P). TDT Synapse software was used for data acquisition.",
            manufacturer="Doric Lenses",
            model="Fiber Optic Implant",
            numerical_aperture=0.48,
            core_diameter_in_um=400.0,
        )

        # Excitation Sources
        dms_signal_excitation_source = ExcitationSource(
            name="dms_signal_excitation_source",
            description="465nm and 405nm LEDs were modulated at 211 Hz and 330 Hz, respectively, for DMS probes. 465nm and 405nm LEDs were modulated at 450 Hz and 270 Hz, respectively for DLS probes. LED currents were adjusted in order to return a voltage between 150-200mV for each signal, were offset by 5 mA, were demodulated using a 4 Hz lowpass frequency filter.",
            manufacturer="Doric Lenses",
            model="Connectorized LED",
            illumination_type="LED",
            excitation_wavelength_in_nm=465.0,
        )
        dms_reference_excitation_source = ExcitationSource(
            name="dms_reference_excitation_source",
            description="465nm and 405nm LEDs were modulated at 211 Hz and 330 Hz, respectively, for DMS probes. 465nm and 405nm LEDs were modulated at 450 Hz and 270 Hz, respectively for DLS probes. LED currents were adjusted in order to return a voltage between 150-200mV for each signal, were offset by 5 mA, were demodulated using a 4 Hz lowpass frequency filter.",
            manufacturer="Doric Lenses",
            model="Connectorized LED",
            illumination_type="LED",
            excitation_wavelength_in_nm=405.0,
        )
        dls_signal_excitation_source = ExcitationSource(
            name="dls_signal_excitation_source",
            description="465nm and 405nm LEDs were modulated at 211 Hz and 330 Hz, respectively, for DMS probes. 465nm and 405nm LEDs were modulated at 450 Hz and 270 Hz, respectively for DLS probes. LED currents were adjusted in order to return a voltage between 150-200mV for each signal, were offset by 5 mA, were demodulated using a 4 Hz lowpass frequency filter.",
            manufacturer="Doric Lenses",
            model="Connectorized LED",
            illumination_type="LED",
            excitation_wavelength_in_nm=465.0,
        )
        dls_reference_excitation_source = ExcitationSource(
            name="dls_reference_excitation_source",
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
        emission_filter = OpticalFilter(
            name="emission_filter",
            description="Dual excitation band fiber photometry measurements use a Fluorescence Mini Cube with 4 ports: one port for the functional fluorescence excitation light, one for the isosbestic excitation, one for the fluorescence detection, and one for the sample. The cube has dichroic mirrors to combine isosbestic and fluorescence excitations and separate the fluorescence emission and narrow bandpass filters limiting the excitation fluorescence spectrum.",
            manufacturer="Doric Lenses",
            model="4 ports Fluorescence Mini Cube - GCaMP",
            peak_wavelength_in_nm=525.0,
            bandwidth_in_nm=(500.0, 550.0),
            filter_type="bandpass",
        )
        excitation_filter = OpticalFilter(
            name="excitation_filter",
            description="Dual excitation band fiber photometry measurements use a Fluorescence Mini Cube with 4 ports: one port for the functional fluorescence excitation light, one for the isosbestic excitation, one for the fluorescence detection, and one for the sample. The cube has dichroic mirrors to combine isosbestic and fluorescence excitations and separate the fluorescence emission and narrow bandpass filters limiting the excitation fluorescence spectrum.",
            manufacturer="Doric Lenses",
            model="4 ports Fluorescence Mini Cube - GCaMP",
            peak_wavelength_in_nm=475.0,
            bandwidth_in_nm=(460.0, 490.0),
            filter_type="bandpass",
        )
        isosbestic_excitation_filter = OpticalFilter(
            name="isosbestic_excitation_filter",
            description="Dual excitation band fiber photometry measurements use a Fluorescence Mini Cube with 4 ports: one port for the functional fluorescence excitation light, one for the isosbestic excitation, one for the fluorescence detection, and one for the sample. The cube has dichroic mirrors to combine isosbestic and fluorescence excitations and separate the fluorescence emission and narrow bandpass filters limiting the excitation fluorescence spectrum.",
            manufacturer="Doric Lenses",
            model="4 ports Fluorescence Mini Cube - GCaMP",
            peak_wavelength_in_nm=405.0,
            bandwidth_in_nm=(400.0, 410.0),
            filter_type="bandpass",
        )

        # Dichroic Mirror
        dichroic_mirror = DichroicMirror(  # TODO: Get characteristic wavelengths from Doric Lenses
            name="dichroic_mirror",
            description="Dual excitation band fiber photometry measurements use a Fluorescence Mini Cube with 4 ports: one port for the functional fluorescence excitation light, one for the isosbestic excitation, one for the fluorescence detection, and one for the sample. The cube has dichroic mirrors to combine isosbestic and fluorescence excitations and separate the fluorescence emission and narrow bandpass filters limiting the excitation fluorescence spectrum.",
            manufacturer="Doric Lenses",
            model="4 ports Fluorescence Mini Cube - GCaMP",
            cut_on_wavelength_in_nm=495.0,
        )

        # Indicators (aka Fluorophores)
        dms_fluorophore = Indicator(
            name="dms_fluorophore",
            description="Mice for fiber photometry experiments received infusions of 1ml of AAV5-CAG-FLEX-jGCaMP7b-WPRE (1.02e13 vg/mL, Addgene, lot 18-429) into lateral SNc (AP 3.1, ML 1.3, DV 4.2) in one hemisphere and medial SNc (AP 3.1, ML 0.8, DV 4.7) in the other. Hemispheres were counterbalanced between mice.",
            manufacturer="Addgene",
            label="GCaMP7b",
            injection_location="medial SNc",
            injection_coordinates_in_mm=(3.1, 0.8, 4.7),
        )
        dls_fluorophore = Indicator(
            name="dls_fluorophore",
            description="Mice for fiber photometry experiments received infusions of 1ml of AAV5-CAG-FLEX-jGCaMP7b-WPRE (1.02e13 vg/mL, Addgene, lot 18-429) into lateral SNc (AP 3.1, ML 1.3, DV 4.2) in one hemisphere and medial SNc (AP 3.1, ML 0.8, DV 4.7) in the other. Hemispheres were counterbalanced between mice.",
            manufacturer="Addgene",
            label="GCaMP7b",
            injection_location="lateral SNc",
            injection_coordinates_in_mm=(3.1, 1.3, 4.2),
        )

        # Commanded Voltage Series
        if has_demodulated_commanded_voltages:
            dms_commanded_signal_series = CommandedVoltageSeries(
                name="dms_commanded_signal",
                data=H5DataIO(tdt_photometry.streams["Fi1d"].data[0, :], compression=True),
                unit="volts",
                frequency=211.0,
                rate=tdt_photometry.streams["Fi1d"].fs,
            )
            dms_commanded_reference_series = CommandedVoltageSeries(
                name="dms_commanded_reference",
                data=H5DataIO(tdt_photometry.streams["Fi1d"].data[1, :], compression=True),
                unit="volts",
                frequency=330.0,
                rate=tdt_photometry.streams["Fi1d"].fs,
            )
            dls_commanded_signal_series = CommandedVoltageSeries(
                name="dls_commanded_signal",
                data=H5DataIO(tdt_photometry.streams["Fi1d"].data[3, :], compression=True),
                unit="volts",
                frequency=450.0,
                rate=tdt_photometry.streams["Fi1d"].fs,
            )
            dls_commanded_reference_series = CommandedVoltageSeries(
                name="dls_commanded_reference",
                data=H5DataIO(tdt_photometry.streams["Fi1d"].data[2, :], compression=True),
                unit="volts",
                frequency=270.0,
                rate=tdt_photometry.streams["Fi1d"].fs,
            )
        else:
            dms_commanded_voltage_series = CommandedVoltageSeries(
                name="dms_commanded_voltage",
                data=H5DataIO(tdt_photometry.streams["Fi1r"].data[0, :], compression=True),
                unit="volts",
                rate=tdt_photometry.streams["Fi1r"].fs,
            )
            dls_commanded_voltage_series = CommandedVoltageSeries(
                name="dls_commanded_voltage",
                data=H5DataIO(tdt_photometry.streams["Fi1r"].data[1, :], compression=True),
                unit="volts",
                rate=tdt_photometry.streams["Fi1r"].fs,
            )

        # Fiber Photometry Table
        fiber_photometry_table = FiberPhotometryTable(
            name="fiber_photometry_table",
            description="Fiber optic implants (Doric Lenses; 400 um, 0.48 NA) were placed above DMS (AP 0.8, ML 1.5, DV 2.8) and DLS (AP 0.1, ML 2.8, DV 3.5). The DMS implant was placed in the hemisphere receiving a medial SNc viral injection, while the DLS implant was placed in the hemisphere receiving a lateral SNc viral injection. Calcium signals from dopamine terminals in DMS and DLS were recorded during RI30, on the first and last days of RI60/RR20 training as well as on both footshock probes for each mouse. All recordings were done using a fiber photometry rig with optical components from Doric lenses controlled by a real-time processor from Tucker Davis Technologies (TDT; RZ5P). TDT Synapse software was used for data acquisition.",
        )
        if has_demodulated_commanded_voltages:
            fiber_photometry_table.add_row(
                location="DMS",
                coordinates=(0.8, 1.5, 2.8),
                commanded_voltage_series=dms_commanded_signal_series,
                indicator=dms_fluorophore,
                optical_fiber=dms_fiber,
                excitation_source=dms_signal_excitation_source,
                photodetector=photodetector,
                excitation_filter=excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
            fiber_photometry_table.add_row(
                location="DMS",
                coordinates=(0.8, 1.5, 2.8),
                commanded_voltage_series=dms_commanded_reference_series,
                indicator=dms_fluorophore,
                optical_fiber=dms_fiber,
                excitation_source=dms_reference_excitation_source,
                photodetector=photodetector,
                excitation_filter=isosbestic_excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
            fiber_photometry_table.add_row(
                location="DLS",
                coordinates=(0.1, 2.8, 3.5),
                commanded_voltage_series=dls_commanded_signal_series,
                indicator=dls_fluorophore,
                optical_fiber=dls_fiber,
                excitation_source=dls_signal_excitation_source,
                photodetector=photodetector,
                excitation_filter=excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
            fiber_photometry_table.add_row(
                location="DLS",
                coordinates=(0.1, 2.8, 3.5),
                commanded_voltage_series=dls_commanded_reference_series,
                indicator=dls_fluorophore,
                optical_fiber=dls_fiber,
                excitation_source=dls_reference_excitation_source,
                photodetector=photodetector,
                excitation_filter=isosbestic_excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
        else:
            fiber_photometry_table.add_row(
                location="DMS",
                coordinates=(0.8, 1.5, 2.8),
                commanded_voltage_series=dms_commanded_voltage_series,
                indicator=dms_fluorophore,
                optical_fiber=dms_fiber,
                excitation_source=dms_signal_excitation_source,
                photodetector=photodetector,
                excitation_filter=excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
            fiber_photometry_table.add_row(
                location="DMS",
                coordinates=(0.8, 1.5, 2.8),
                commanded_voltage_series=dms_commanded_voltage_series,
                indicator=dms_fluorophore,
                optical_fiber=dms_fiber,
                excitation_source=dms_reference_excitation_source,
                photodetector=photodetector,
                excitation_filter=isosbestic_excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
            fiber_photometry_table.add_row(
                location="DLS",
                coordinates=(0.1, 2.8, 3.5),
                commanded_voltage_series=dls_commanded_voltage_series,
                indicator=dls_fluorophore,
                optical_fiber=dls_fiber,
                excitation_source=dls_signal_excitation_source,
                photodetector=photodetector,
                excitation_filter=excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
            fiber_photometry_table.add_row(
                location="DLS",
                coordinates=(0.1, 2.8, 3.5),
                commanded_voltage_series=dls_commanded_voltage_series,
                indicator=dls_fluorophore,
                optical_fiber=dls_fiber,
                excitation_source=dls_reference_excitation_source,
                photodetector=photodetector,
                excitation_filter=isosbestic_excitation_filter,
                emission_filter=emission_filter,
                dichroic_mirror=dichroic_mirror,
            )
        dms_signal_region = fiber_photometry_table.create_region(
            name="fiber_photometry_table_region",
            description="The region of the FiberPhotometryTable corresponding to the DMS signal.",
            region=[0],
        )
        dms_reference_region = fiber_photometry_table.create_region(
            name="fiber_photometry_table_region",
            description="The region of the FiberPhotometryTable corresponding to the DMS reference.",
            region=[1],
        )
        dls_signal_region = fiber_photometry_table.create_region(
            name="fiber_photometry_table_region",
            description="The region of the FiberPhotometryTable corresponding to the DLS signal.",
            region=[2],
        )
        dls_reference_region = fiber_photometry_table.create_region(
            name="fiber_photometry_table_region",
            description="The region of the FiberPhotometryTable corresponding to the DLS reference.",
            region=[3],
        )

        # Fiber Photometry Response Series
        dms_signal_series = FiberPhotometryResponseSeries(
            name="dms_signal",
            description="The fluorescence from the blue light excitation (465nm) corresponding to the calcium signal in the DMS.",
            data=H5DataIO(tdt_photometry.streams["Dv1A"].data, compression=True),
            unit="a.u.",
            rate=tdt_photometry.streams["Dv1A"].fs,
            fiber_photometry_table_region=dms_signal_region,
        )
        dms_reference_series = FiberPhotometryResponseSeries(
            name="dms_reference",
            description="The fluorescence from the UV light excitation (405nm) corresponding to the isosbestic reference in the DMS.",
            data=H5DataIO(tdt_photometry.streams["Dv2A"].data, compression=True),
            unit="a.u.",
            rate=tdt_photometry.streams["Dv2A"].fs,
            fiber_photometry_table_region=dms_reference_region,
        )
        dls_signal_series = FiberPhotometryResponseSeries(
            name="dls_signal",
            description="The fluorescence from the blue light excitation (465nm) corresponding to the calcium signal in the DLS.",
            data=H5DataIO(tdt_photometry.streams["Dv3B"].data, compression=True),
            unit="a.u.",
            rate=tdt_photometry.streams["Dv3B"].fs,
            fiber_photometry_table_region=dls_signal_region,
        )
        dls_reference_series = FiberPhotometryResponseSeries(
            name="dls_reference",
            description="The fluorescence from the UV light excitation (405nm) corresponding to the isosbestic reference in the DLS.",
            data=H5DataIO(tdt_photometry.streams["Dv4B"].data, compression=True),
            unit="a.u.",
            rate=tdt_photometry.streams["Dv4B"].fs,
            fiber_photometry_table_region=dls_reference_region,
        )

        nwbfile.add_device(dms_fiber)
        nwbfile.add_device(dls_fiber)
        nwbfile.add_device(dms_signal_excitation_source)
        nwbfile.add_device(dms_reference_excitation_source)
        nwbfile.add_device(dls_signal_excitation_source)
        nwbfile.add_device(dls_reference_excitation_source)
        nwbfile.add_device(photodetector)
        nwbfile.add_device(excitation_filter)
        nwbfile.add_device(isosbestic_excitation_filter)
        nwbfile.add_device(emission_filter)
        nwbfile.add_device(dichroic_mirror)
        nwbfile.add_device(dms_fluorophore)
        nwbfile.add_device(dls_fluorophore)
        if has_demodulated_commanded_voltages:
            nwbfile.add_acquisition(dms_commanded_signal_series)
            nwbfile.add_acquisition(dms_commanded_reference_series)
            nwbfile.add_acquisition(dls_commanded_signal_series)
            nwbfile.add_acquisition(dls_commanded_reference_series)
        else:
            nwbfile.add_acquisition(dms_commanded_voltage_series)
            nwbfile.add_acquisition(dls_commanded_voltage_series)
        nwbfile.add_acquisition(fiber_photometry_table)
        nwbfile.add_acquisition(dms_signal_series)
        nwbfile.add_acquisition(dms_reference_series)
        nwbfile.add_acquisition(dls_signal_series)
        nwbfile.add_acquisition(dls_reference_series)
