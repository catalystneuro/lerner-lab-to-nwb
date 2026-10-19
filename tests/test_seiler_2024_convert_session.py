from datetime import datetime, timedelta

from lerner_lab_to_nwb.seiler_2024.seiler_2024_convert_session import SESSION_TIMEZONE


class TestSessionTimezone:
    def test_daylight_saving_offset(self):
        session_start_time = datetime(2020, 7, 31, 12, 3, 31).replace(tzinfo=SESSION_TIMEZONE)
        assert session_start_time.utcoffset() == timedelta(hours=-5)

    def test_standard_offset(self):
        session_start_time = datetime(2019, 2, 27, 14, 32, 10).replace(tzinfo=SESSION_TIMEZONE)
        assert session_start_time.utcoffset() == timedelta(hours=-6)
