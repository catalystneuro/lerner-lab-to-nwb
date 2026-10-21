from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pytest
from neuroconv.utils import dict_deep_update, load_dict_from_file
from pynwb import NWBFile

import lerner_lab_to_nwb.seiler_2024 as seiler_2024
from lerner_lab_to_nwb.seiler_2024 import Seiler2024OptogeneticInterface

RUNS = {
    # program, box, left rewards, stimulation times
    "FOOD_FR1 TTL Left": ("1", "15.200        31.650", None),
    "FR1_LEFT_STIM": ("2", "15.200        31.650", None),
    "RI60_LEFT_SCRAM": ("3", "15.200        31.650", "0.000"),
    "RI60_RIGHT_SCRAM": ("4", "15.200        31.650", "0.000       32.000       63.000"),
}


def medpc_run(*, msn: str, box: str, left_rewards: str, stimulation_times: str | None) -> str:
    run = (
        "Start Date: 10/23/20\n"
        "Subject: 322.415\n"
        f"Box: {box}\n"
        "Start Time: 13:00:52\n"
        f"MSN: {msn}\n"
        "B:\n"
        f"     0:      {left_rewards}        0.000\n"
        "D:\n"
        "     0:        0.000\n"
    )
    if stimulation_times is not None:
        run += f"Z:\n     0:        {stimulation_times}\n"
    return run


@pytest.fixture
def medpc_file_path(tmp_path) -> Path:
    file_path = tmp_path / "322.415"
    file_path.write_text(
        "\n"
        + "\n".join(
            medpc_run(msn=msn, box=box, left_rewards=left_rewards, stimulation_times=stimulation_times)
            for msn, (box, left_rewards, stimulation_times) in RUNS.items()
        )
    )
    return file_path


def add_optogenetics(medpc_file_path: Path, msn: str) -> NWBFile:
    interface = Seiler2024OptogeneticInterface(
        file_path=str(medpc_file_path),
        session_conditions={"Start Date": "10/23/20", "Start Time": "13:00:52", "Box": RUNS[msn][0]},
        start_variable="Start Date",
        experimental_group="DMS-Excitatory",
        optogenetic_treatment="ChR2",
        verbose=False,
    )
    editable_metadata_path = Path(seiler_2024.__file__).parent / "seiler_2024_metadata.yaml"
    metadata = dict_deep_update(interface.get_metadata(), load_dict_from_file(editable_metadata_path))
    metadata["MedPC"]["MSN"] = msn
    metadata["NWBFile"]["session_id"] = "test"
    nwbfile = NWBFile(
        session_description="test",
        identifier="test",
        session_start_time=datetime(2020, 10, 23, 13, 0, 52, tzinfo=ZoneInfo("America/Chicago")),
    )
    interface.add_to_nwbfile(nwbfile=nwbfile, metadata=metadata)
    return nwbfile


class TestSeiler2024OptogeneticInterface:
    def test_non_stimulation_program_has_no_series(self, medpc_file_path):
        nwbfile = add_optogenetics(medpc_file_path, msn="FOOD_FR1 TTL Left")
        assert "OptogeneticSeries" not in nwbfile.stimulus
        assert "OptogeneticStimulusSite" in nwbfile.ogen_sites

    def test_stimulation_program_has_series_at_rewards(self, medpc_file_path):
        nwbfile = add_optogenetics(medpc_file_path, msn="FR1_LEFT_STIM")
        timestamps = nwbfile.stimulus["OptogeneticSeries"].timestamps
        np.testing.assert_array_equal(timestamps[:2], np.array([0.0, 15.2]))  # baseline, then first rewarded pulse

    def test_scrambled_program_without_stimulation_has_no_series(self, medpc_file_path):
        nwbfile = add_optogenetics(medpc_file_path, msn="RI60_LEFT_SCRAM")
        assert "OptogeneticSeries" not in nwbfile.stimulus

    def test_scrambled_program_skips_unwritten_first_stimulation_slot(self, medpc_file_path):
        nwbfile = add_optogenetics(medpc_file_path, msn="RI60_RIGHT_SCRAM")
        timestamps = nwbfile.stimulus["OptogeneticSeries"].timestamps
        np.testing.assert_array_equal(timestamps[:2], np.array([0.0, 32.0]))  # baseline, then first stimulation pulse
