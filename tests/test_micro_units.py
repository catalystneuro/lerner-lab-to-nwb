from pathlib import Path

import pytest
from neuroconv.utils import load_dict_from_file

import lerner_lab_to_nwb.seiler_2024 as seiler_2024
from lerner_lab_to_nwb.seiler_2024.seiler_2024fiberphotometryinterface import INDICATOR_DESCRIPTION


def test_photometry_injection_volume():
    assert "1 μl of AAV5-CAG-FLEX-jGCaMP7b-WPRE" in INDICATOR_DESCRIPTION


@pytest.mark.parametrize(
    "experimental_group, injection_volume, fiber_core",
    [
        ("DMS-Excitatory", "1 μl of", "250 μm core"),
        ("DLS-Excitatory", "1 μl of", "250 μm core"),
        ("DMS-Inhibitory", "1 μl per side of", "500 μm core"),
    ],
)
def test_optogenetics_injection_volume_and_fiber_core(experimental_group, injection_volume, fiber_core):
    metadata = load_dict_from_file(Path(seiler_2024.__file__).parent / "seiler_2024_metadata.yaml")
    description = metadata["Optogenetics"]["experimental_group_to_metadata"][experimental_group][
        "ogen_site_description"
    ]
    assert injection_volume in description
    assert fiber_core in description
