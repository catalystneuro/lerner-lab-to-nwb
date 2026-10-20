import numpy as np
import pytest
from tdt import StructType

from lerner_lab_to_nwb.seiler_2024 import Seiler2024NWBConverter


def tdt_block(*, ttl_name_to_onsets: dict[str, list[float]], number_of_samples: int = 101) -> StructType:
    block = StructType()
    block.streams = StructType()
    block.streams["Dv1A"] = StructType()
    block.streams["Dv1A"].fs = 1.0
    block.streams["Dv1A"].data = np.zeros(number_of_samples)
    block.epocs = StructType()
    for ttl_name, onsets in ttl_name_to_onsets.items():
        block.epocs[ttl_name] = StructType()
        block.epocs[ttl_name].onset = np.array(onsets)
    return block


@pytest.fixture
def converter() -> Seiler2024NWBConverter:
    return Seiler2024NWBConverter(source_data={})


@pytest.fixture
def first_block() -> StructType:
    # 101 samples at 1 Hz, so the second block is placed 100 s after the first
    return tdt_block(ttl_name_to_onsets={})


class TestSeiler2024NWBConverter:
    def test_rewarded_nose_pokes_already_in_nose_pokes_are_not_added_again(self, converter, first_block):
        # As in 139.298: RNnR already contains the rewarded nose poke
        second_block = tdt_block(ttl_name_to_onsets={"RNnR": [5.0, 7.0], "RNRW": [5.0]})
        right_reward_times = converter.get_second_block_ttl_timestamps("RNRW", first_block, second_block, 10)
        right_nose_poke_times = converter.get_second_block_ttl_timestamps("RNnR", first_block, second_block, 10)
        np.testing.assert_array_equal(right_reward_times, np.array([105.0]))
        np.testing.assert_array_equal(right_nose_poke_times, np.array([105.0, 107.0]))

    def test_rewarded_nose_pokes_merged_into_nose_pokes_are_shifted_once(self, converter, first_block):
        # As in 92.246: LNnR has only the unrewarded nose pokes
        second_block = tdt_block(ttl_name_to_onsets={"LNnR": [7.0], "LNRW": [5.0]})
        left_reward_times = converter.get_second_block_ttl_timestamps("LNRW", first_block, second_block, 10)
        left_nose_poke_times = converter.get_second_block_ttl_timestamps("LNnR", first_block, second_block, 10)
        np.testing.assert_array_equal(left_reward_times, np.array([105.0]))
        np.testing.assert_array_equal(left_nose_poke_times, np.array([105.0, 107.0]))
