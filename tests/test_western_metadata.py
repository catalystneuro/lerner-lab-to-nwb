import numpy as np
import pytest
from pynwb import NWBHDF5IO
from tifffile import imwrite

from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_session import western_blot_to_nwb


@pytest.fixture
def western_blot_image() -> np.ndarray:
    return np.arange(12, dtype=np.uint16).reshape(3, 4)


@pytest.fixture
def nwbfile_path(request, western_blot_image, tmp_path):
    file_path = tmp_path / request.param
    imwrite(file_path, western_blot_image)
    output_dir_path = tmp_path / "nwb"
    western_blot_to_nwb(file_path=file_path, output_dir_path=output_dir_path, verbose=False)
    return output_dir_path / f"{file_path.stem}.nwb"


class TestWesternBlotToNwb:
    @pytest.mark.parametrize("nwbfile_path", ["Female_DMS_DAT_WT.tif"], indirect=True)
    def test_wild_type_metadata(self, nwbfile_path, western_blot_image):
        with NWBHDF5IO(nwbfile_path, "r") as io:
            nwbfile = io.read()
            assert nwbfile.session_description == "Western blot of DAT in DMS from female wild-type mice."
            assert nwbfile.subject.genotype == "WT: C57BL/6J"
            assert nwbfile.subject.description == (
                "Adult female wild-type (C57BL/6J) mice whose DMS tissue was used for quantitative immunoblotting."
            )
            np.testing.assert_array_equal(
                nwbfile.acquisition["images"]["western_blot_image"].data[:], western_blot_image
            )

    @pytest.mark.parametrize("nwbfile_path", ["Male_DLS_Actin_DAT-IRES-Cre-het.tif"], indirect=True)
    def test_dat_ires_cre_het_metadata(self, nwbfile_path):
        with NWBHDF5IO(nwbfile_path, "r") as io:
            nwbfile = io.read()
            assert (
                nwbfile.session_description
                == "Western blot of β-actin in DLS from male DAT-IRES-Cre heterozygous mice."
            )
            assert nwbfile.subject.genotype == "DAT-IRES-Cre heterozygous: B6.SJL-Slc6a3tm1.1(cre)Bkmn/J"
            assert nwbfile.subject.description == (
                "Adult male DAT-IRES-Cre heterozygous (backcrossed to C57BL/6J) mice whose DLS tissue was used for "
                "quantitative immunoblotting."
            )
