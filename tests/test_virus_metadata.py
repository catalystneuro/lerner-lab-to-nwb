from pathlib import Path

import pandas as pd
import pytest

from lerner_lab_to_nwb.seiler_2024.seiler_2024excelmetadatainterface import Seiler2024ExcelMetadataInterface

SUBJECTS = [
    ("1.1", "Fiber Photometry", None),
    ("2.2", "DLS Excitatory", "Excitatory stimulation on rewarded nosepokes"),
    ("3.3", "DLS Excitatory", "Excitatory stimulation on random nosepokes"),
    ("4.4", "DLS Excitatory", "Control"),
    ("5.5", "DMS Excitatory", "Excitatory stimulation on rewarded nosepokes"),
    ("6.6", "DMS Excitatory", "Excitatory stimulation on random nosepokes"),
    ("7.7", "DMS Excitatory", "Control"),
    ("8.8", "DMS Inhibitory", "Inhibitory stimulation on rewarded nosepokes"),
    ("9.9", "DMS Inhibitory", "Inhibitory stimulation on random nosepokes"),
    ("10.10", "DMS Inhibitory", "Control"),
    ("11.11", "DMS Inhibitory Group 2", "Inhibitory stimulation on rewarded nosepokes (after FR training)"),
    ("12.12", "DMS Inhibitory Group 2", "Inhibitory stimulation on random nosepokes (after FR training)"),
    ("13.13", "DMS Inhibitory Group 2", "Control"),
]


@pytest.fixture
def file_path(tmp_path) -> Path:
    file_path = tmp_path / "MouseDemographics.xlsx"
    df = pd.DataFrame(
        {
            "Mouse ID": [subject_id for subject_id, _, _ in SUBJECTS],
            "Experiment": [experiment for _, experiment, _ in SUBJECTS],
            "Behavior": "FR1",
            "Sex": "Male",
            "Surgical Manipulation": "Surgery",
            "Hemisphere with DMS": "Left",
            "Punishment Group": "Resistant",
            "Treatment": [treatment for _, _, treatment in SUBJECTS],
        }
    )
    df.to_excel(file_path, sheet_name="Mouse Demographics", index=False)
    return file_path


class TestSeiler2024ExcelMetadataInterface:
    @pytest.mark.parametrize(
        "subject_id, expected_virus",
        [
            ("1.1", "AAV5-CAG-FLEX-jGCaMP7b-WPRE"),
            ("2.2", "AAV5-EF1a-DIO-hChR2(H134R)-EYFP"),
            ("3.3", "AAV5-EF1a-DIO-hChR2(H134R)-EYFP"),
            ("4.4", "AAV5-EF1a-DIO-EYFP"),
            ("5.5", "AAV5-EF1a-DIO-hChR2(H134R)-EYFP"),
            ("6.6", "AAV5-EF1a-DIO-hChR2(H134R)-EYFP"),
            ("7.7", "AAV5-EF1a-DIO-EYFP"),
            ("8.8", "AAV5-EF1a-DIO-eNpHR3.0-EYFP"),
            ("9.9", "AAV5-EF1a-DIO-eNpHR3.0-EYFP"),
            ("10.10", "AAV5-EF1a-DIO-EYFP"),
            ("11.11", "AAV5-EF1a-DIO-eNpHR3.0-EYFP"),
            ("12.12", "AAV5-EF1a-DIO-eNpHR3.0-EYFP"),
            ("13.13", "AAV5-EF1a-DIO-EYFP"),
        ],
    )
    def test_virus(self, file_path, subject_id, expected_virus):
        interface = Seiler2024ExcelMetadataInterface(file_path=str(file_path), subject_id=subject_id, verbose=False)
        assert interface.get_metadata()["NWBFile"]["virus"] == expected_virus
