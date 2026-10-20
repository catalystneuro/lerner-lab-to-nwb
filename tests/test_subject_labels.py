from pathlib import Path

from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_dataset import SUBJECTS_TO_SKIP, get_opto_subject_id


class TestSubject262478:
    def test_nphr_run_is_converted(self):
        subject_id = get_opto_subject_id(Path("Group 2/NpHr/2021-10-29_262_259.478"))
        assert subject_id == "262.478"
        assert subject_id not in SUBJECTS_TO_SKIP

    def test_scrambled_copy_is_skipped(self):
        subject_id = get_opto_subject_id(Path("Group 2/Scrambled/2021-10-29_262_259 - Copy.478"))
        assert subject_id in SUBJECTS_TO_SKIP
