"""Primary class for converting experiment-specific fiber photometry."""
from pynwb.file import NWBFile
from pynwb.core import DynamicTableRegion
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from neuroconv.tools import nwb_helpers
from pathlib import Path
from ndx_photometry import (
    FibersTable,
    PhotodetectorsTable,
    ExcitationSourcesTable,
    MultiCommandedVoltage,
    FiberPhotometry,
    FluorophoresTable,
    FiberPhotometryResponseSeries,
)
from hdmf.backends.hdf5.h5_utils import H5DataIO
from tdt import read_block


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

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # Load Data
        folder_path = Path(self.source_data["folder_path"])
        assert folder_path.is_dir(), f"Folder path {folder_path} does not exist."
        tdt_photometry = read_block(str(folder_path))

        # Commanded Voltages
        multi_commanded_voltage = MultiCommandedVoltage()
        dms_commanded_signal_series = multi_commanded_voltage.create_commanded_voltage_series(
            name="dms_commanded_signal",
            data=H5DataIO(tdt_photometry.streams["Fi1d"].data[0, :], compression=True),
            frequency=211.0,
            power=1.0,
            rate=tdt_photometry.streams["Fi1d"].fs,
            unit="volts",
        )
        dms_commanded_reference_series = multi_commanded_voltage.create_commanded_voltage_series(
            name="dms_commanded_reference",
            data=H5DataIO(tdt_photometry.streams["Fi1d"].data[1, :], compression=True),
            frequency=330.0,
            power=1.0,
            rate=tdt_photometry.streams["Fi1d"].fs,
            unit="volts",
        )
        dls_commanded_signal_series = multi_commanded_voltage.create_commanded_voltage_series(
            name="dls_commanded_signal",
            data=H5DataIO(tdt_photometry.streams["Fi1d"].data[3, :], compression=True),
            frequency=450.0,
            power=1.0,
            rate=tdt_photometry.streams["Fi1d"].fs,
            unit="volts",
        )
        dls_commanded_reference_series = multi_commanded_voltage.create_commanded_voltage_series(
            name="dls_commanded_reference",
            data=H5DataIO(tdt_photometry.streams["Fi1d"].data[2, :], compression=True),
            frequency=270.0,
            power=1.0,
            rate=tdt_photometry.streams["Fi1d"].fs,
            unit="volts",
        )

        # Excitation Sources
        excitation_sources_table = ExcitationSourcesTable(
            description="465nm and 405nm LEDs were modulated at 211 Hz and 330 Hz, respectively, for DMS probes. 465nm and 405nm LEDs were modulated at 450 Hz and 270 Hz, respectively for DLS probes. LED currents were adjusted in order to return a voltage between 150-200mV for each signal, were offset by 5 mA, were demodulated using a 4 Hz lowpass frequency filter.",
        )
        excitation_sources_table.add_row(
            peak_wavelength=465.0,
            source_type="LED",
            commanded_voltage=dms_commanded_signal_series,
        )
        excitation_sources_table.add_row(
            peak_wavelength=405.0,
            source_type="LED",
            commanded_voltage=dms_commanded_reference_series,
        )
        excitation_sources_table.add_row(
            peak_wavelength=465.0,
            source_type="LED",
            commanded_voltage=dls_commanded_signal_series,
        )
        excitation_sources_table.add_row(
            peak_wavelength=405.0,
            source_type="LED",
            commanded_voltage=dls_commanded_reference_series,
        )

        photodetectors_table = PhotodetectorsTable(
            description="Some description",  # TODO: Get description from Lerner lab
        )
        photodetectors_table.add_row(
            peak_wavelength=527.0,  # TODO: Get peak wavelength from Lerner lab
            type="PMT",  # TODO: Get type from Lerner lab
            gain=1.0,  # TODO: Get gain from Lerner lab
        )

        # Fluorophores
        fluorophores_table = FluorophoresTable(
            description="GCaMP7b was used as the fluorophore in both DMS and DLS.",
        )
        fluorophores_table.add_row(
            label="GCaMP7b",
            location="DMS",
            coordinates=(0.8, 1.5, -2.8),  # (AP, ML, DV)
        )
        fluorophores_table.add_row(
            label="GCaMP7b",
            location="DLS",
            coordinates=(-0.1, 2.8, -3.5),  # (AP, ML, DV)
        )

        fibers_table = FibersTable(
            description="Mice for fiber photometry experiments received infusions of 1ml of AAV5-CAG-FLEX-jGCaMP7b-WPRE (1.02e13 vg/mL, Addgene, lot 18-429) into lateral SNc (AP 3.1, ML 1.3, DV 4.2) in one hemisphere and medial SNc (AP 3.1, ML 0.8, DV 4.7) in the other. Hemispheres were counterbalanced between mice. Fiber optic implants (Doric Lenses; 400 mm, 0.48 NA) were placed above DMS (AP 0.8, ML 1.5, DV 2.8) and DLS (AP 0.1, ML 2.8, DV 3.5). The DMS implant was placed in the hemisphere receiving a medial SNc viral injection, while the DLS implant was placed in the hemisphere receiving a lateral SNc viral injection. Calcium signals from dopamine terminals in DMS and DLS were recorded during RI30, on the first and last days of RI60/RR20 training as well as on both footshock probes for each mouse. All recordings were done using a fiber photometry rig with optical components from Doric lenses controlled by a real-time processor from Tucker Davis Technologies (TDT; RZ5P). TDT Synapse software was used for data acquisition.",
        )
        fibers_table.add_row(location="DMS")
        fibers_table.add_row(location="DLS")

        nwbfile.add_lab_meta_data(
            FiberPhotometry(
                fibers=fibers_table,
                excitation_sources=excitation_sources_table,
                photodetectors=photodetectors_table,
                fluorophores=fluorophores_table,
            )
        )
        dms_fiber_ref = DynamicTableRegion(
            # name="dms_fiber",
            name="fiber",
            data=[0],
            description="Fiber used in the DMS.",
            table=fibers_table,
        )
        dls_fiber_ref = DynamicTableRegion(
            # name="dls_fiber",
            name="fiber",
            data=[1],
            description="Fiber used in the DLS.",
            table=fibers_table,
        )
        dms_excitation_ref = DynamicTableRegion(
            # name="dms_excitation",
            name="excitation_source",
            data=[0, 1],
            description="Excitation sources used in the DMS.",
            table=excitation_sources_table,
        )
        dls_excitation_ref = DynamicTableRegion(
            # name="dls_excitation",
            name="excitation_source",
            data=[2, 3],
            description="Excitation sources used in the DLS.",
            table=excitation_sources_table,
        )
        photodetector_ref = DynamicTableRegion(
            name="photodetector",
            data=[0],
            description="Photodetector used in the DMS and DLS.",
            table=photodetectors_table,
        )
        dms_fluorophore_ref = DynamicTableRegion(
            # name="dms_fluorophore",
            name="fluorophore",
            data=[0],
            description="Fluorophore used in the DMS.",
            table=fluorophores_table,
        )
        dls_fluorophore_ref = DynamicTableRegion(
            # name="dls_fluorophore",
            name="fluorophore",
            data=[1],
            description="Fluorophore used in the DLS.",
            table=fluorophores_table,
        )

        dms_signal_series = FiberPhotometryResponseSeries(
            name="dms_signal",
            description="The fluorescence from the blue light excitation (465nm) corresponding to the calcium signal in the DMS.",
            data=H5DataIO(tdt_photometry.streams["Dv1A"].data, compression=True),
            unit="a.u.",
            fiber=dms_fiber_ref,
            excitation_source=dms_excitation_ref,
            photodetector=photodetector_ref,
            fluorophore=dms_fluorophore_ref,
            rate=tdt_photometry.streams["Dv1A"].fs,
        )
        dms_reference_series = FiberPhotometryResponseSeries(
            name="dms_reference",
            description="The fluorescence from the UV light excitation (405nm) corresponding to the isosbestic reference in the DMS.",
            data=H5DataIO(tdt_photometry.streams["Dv2A"].data, compression=True),
            unit="a.u.",
            fiber=dms_fiber_ref,
            excitation_source=dms_excitation_ref,
            photodetector=photodetector_ref,
            fluorophore=dms_fluorophore_ref,
            rate=tdt_photometry.streams["Dv2A"].fs,
        )
        dls_signal_series = FiberPhotometryResponseSeries(
            name="dls_signal",
            description="The fluorescence from the blue light excitation (465nm) corresponding to the calcium signal in the DLS.",
            data=H5DataIO(tdt_photometry.streams["Dv3B"].data, compression=True),
            unit="a.u.",
            fiber=dls_fiber_ref,
            excitation_source=dls_excitation_ref,
            photodetector=photodetector_ref,
            fluorophore=dls_fluorophore_ref,
            rate=tdt_photometry.streams["Dv3B"].fs,
        )
        dls_reference_series = FiberPhotometryResponseSeries(
            name="dls_reference",
            description="The fluorescence from the UV light excitation (405nm) corresponding to the isosbestic reference in the DLS.",
            data=H5DataIO(tdt_photometry.streams["Dv4B"].data, compression=True),
            unit="a.u.",
            fiber=dls_fiber_ref,
            excitation_source=dls_excitation_ref,
            photodetector=photodetector_ref,
            fluorophore=dls_fluorophore_ref,
            rate=tdt_photometry.streams["Dv4B"].fs,
        )

        # Add the data to the NWBFile
        # ophys_module = nwb_helpers.get_module(
        #     nwbfile=nwbfile,
        #     name="ophys",
        #     description="Fiber photometry data from DMS and DLS.",
        # )
        # ophys_module.add(multi_commanded_voltage)
        # ophys_module.add(dms_signal_series)
        # ophys_module.add(dms_reference_series)
        # ophys_module.add(dls_signal_series)
        # ophys_module.add(dls_reference_series)
        # TODO: Acquisition or Ophys?
        nwbfile.add_acquisition(multi_commanded_voltage)
        nwbfile.add_acquisition(dms_signal_series)
        nwbfile.add_acquisition(dms_reference_series)
        nwbfile.add_acquisition(dls_signal_series)
        nwbfile.add_acquisition(dls_reference_series)
