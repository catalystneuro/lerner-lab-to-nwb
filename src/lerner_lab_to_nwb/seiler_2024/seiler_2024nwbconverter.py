"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter

from lerner_lab_to_nwb.seiler_2024 import Seiler2024BehaviorInterface


class Seiler2024NWBConverter(NWBConverter):
    """Primary conversion class."""

    data_interface_classes = dict(
        Behavior=Seiler2024BehaviorInterface,
    )
