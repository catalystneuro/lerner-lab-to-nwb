from pathlib import Path

import pytest
from neuroconv.utils import load_dict_from_file

import lerner_lab_to_nwb.seiler_2024 as seiler_2024


@pytest.fixture
def metadata():
    return load_dict_from_file(Path(seiler_2024.__file__).parent / "seiler_2024_metadata.yaml")


def test_fr1_both_scrambled_session_description(metadata):
    # FR1_BOTH_SCRAMBLED.MPC state set 4 stimulates when RANDI V = F is 5, checked every 12 s
    assert metadata["MedPC"]["msn_to_session_description"]["FR1_BOTH_SCRAMBLED"] == (
        "FR1 Training with optogenetic stimulation, rewards delivered on both left and right nose pokes, "
        "optogenetic stimulation delivered on a random timer, on average every 120 seconds"
    )


@pytest.mark.parametrize(
    "experimental_group, injection_site",
    [
        ("DMS-Excitatory", "in medial SNc (AP -3.1, ML 0.8, DV -4.7)"),
        ("DLS-Excitatory", "in lateral SNc (AP -3.1, ML 1.3, DV -4.2)"),
        ("DMS-Inhibitory", "in bilateral medial SNc (AP -3.1, ML 0.8, DV -4.7)"),
    ],
)
def test_ogen_site_description_injection_site(metadata, experimental_group, injection_site):
    description = metadata["Optogenetics"]["experimental_group_to_metadata"][experimental_group][
        "ogen_site_description"
    ]
    assert injection_site in description
