from pathlib import Path

from neuroconv.utils import load_dict_from_file

import lerner_lab_to_nwb.seiler_2024 as seiler_2024


def test_institution():
    metadata = load_dict_from_file(Path(seiler_2024.__file__).parent / "seiler_2024_metadata.yaml")
    assert metadata["NWBFile"]["institution"] == "Northwestern University"
