from datetime import datetime

import numpy as np
import pytest
from tdt import StructType

from lerner_lab_to_nwb.seiler_2024 import Seiler2024NWBConverter
from lerner_lab_to_nwb.seiler_2024.seiler_2024fiberphotometryinterface import get_block_start_times


def tdt_block(*, start_date: datetime, ttl_name_to_onsets: dict[str, list[float]]) -> StructType:
    block = StructType()
    block.info = StructType()
    block.info.start_date = start_date
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
    return tdt_block(
        start_date=datetime(2019, 9, 12, 9, 50, 34),
        ttl_name_to_onsets={"RNnR": [10.0, 20.0], "RNRW": [20.0], "LNnR": [], "LNRW": [], "PrtN": [21.0]},
    )


def second_block(ttl_name_to_onsets: dict[str, list[float]]) -> StructType:
    # Starts 2707 s after the first block
    return tdt_block(start_date=datetime(2019, 9, 12, 10, 35, 41), ttl_name_to_onsets=ttl_name_to_onsets)


def test_get_block_start_times(first_block):
    assert get_block_start_times([first_block, second_block({})]) == [0.0, 2707.0]


class TestSeiler2024NWBConverter:
    def test_split_session_ttls_are_placed_at_block_start(self, converter):
        # 332.393's first block has no rewards
        blocks = [
            tdt_block(start_date=datetime(2020, 7, 28, 12, 24, 3), ttl_name_to_onsets={"RNnR": [5.0], "PrtN": [6.0]}),
            tdt_block(
                start_date=datetime(2020, 7, 28, 12, 33, 14),
                ttl_name_to_onsets={"RNnR": [1.0, 2.0], "RNRW": [2.0], "PrtN": [3.0]},
            ),
        ]
        right_reward_times = converter.get_session_ttl_timestamps("RNRW", blocks, len_behavior=1)
        right_nose_poke_times = converter.get_session_ttl_timestamps("RNnR", blocks, len_behavior=3)
        port_entry_times = converter.get_session_ttl_timestamps("PrtN", blocks, len_behavior=2)
        np.testing.assert_array_equal(right_reward_times, np.array([553.0]))
        np.testing.assert_array_equal(right_nose_poke_times, np.array([5.0, 552.0, 553.0]))
        np.testing.assert_array_equal(port_entry_times, np.array([6.0, 554.0]))

    def test_rewarded_nose_pokes_already_in_nose_pokes_are_not_added_again(self, converter, first_block):
        # As in 139.298: RNnR already contains the rewarded nose poke
        blocks = [first_block, second_block({"RNnR": [5.0, 7.0], "RNRW": [5.0]})]
        right_reward_times = converter.get_session_ttl_timestamps("RNRW", blocks, len_behavior=10)
        right_nose_poke_times = converter.get_session_ttl_timestamps("RNnR", blocks, len_behavior=10)
        np.testing.assert_array_equal(right_reward_times, np.array([20.0, 2712.0]))
        np.testing.assert_array_equal(right_nose_poke_times, np.array([10.0, 20.0, 2712.0, 2714.0]))

    def test_rewarded_nose_pokes_merged_into_nose_pokes_are_shifted_once(self, converter, first_block):
        # As in 92.246: LNnR has only the unrewarded nose pokes
        blocks = [first_block, second_block({"LNnR": [7.0], "LNRW": [5.0]})]
        left_reward_times = converter.get_session_ttl_timestamps("LNRW", blocks, len_behavior=10)
        left_nose_poke_times = converter.get_session_ttl_timestamps("LNnR", blocks, len_behavior=10)
        np.testing.assert_array_equal(left_reward_times, np.array([2712.0]))
        np.testing.assert_array_equal(left_nose_poke_times, np.array([2712.0, 2714.0]))
