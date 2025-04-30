import pandas as pd
import pytest
import pytz

from insitupy.io.dates import DateManager

in_timezone = 'US/Mountain'
out_timezone = 'UTC'


@pytest.fixture
def test_date():
    return pd.to_datetime('2025-04-01')


class TestDates:
    # TODO: Cover GPR dates logic

    def test_separate_date_and_time(self):
        date = DateManager.handle_separate_datetime(
            {
                'date': '2025-04-01',
                'time': '12:00',
                'header1': 'value1',
            }
        )
        assert type(date), pd.DatetimeIndex
        assert date.year == 2025
        assert date.month == 4
        assert date.day == 1
        assert date.hour == 12
        assert date.minute == 0

    def test_separate_date_no_time(self):
        date = DateManager.handle_separate_datetime({'date': '2025-04-01'})
        assert type(date), pd.DatetimeIndex
        assert date.year == 2025
        assert date.month == 4
        assert date.day == 1
        assert date.hour == 00
        assert date.minute == 0

    def test_separate_date_time_nan(self):
        date = DateManager.handle_separate_datetime(
            {'date': '2025-04-01', 'time': 'nan'}
        )
        assert type(date), pd.DatetimeIndex
        assert date.year == 2025
        assert date.month == 4
        assert date.day == 1
        assert date.hour == 00
        assert date.minute == 0

    def test_separate_date_mmddyy(self):
        date = DateManager.handle_separate_datetime({'date': '040125'})
        assert type(date), pd.DatetimeIndex
        assert date.year == 2025
        assert date.month == 4
        assert date.day == 1
        assert date.hour == 00
        assert date.minute == 0

    def test_separate_date_mmddyy_time(self):
        date = DateManager.handle_separate_datetime(
            {'date': '040125', 'time': '12:00'}
        )
        assert type(date), pd.DatetimeIndex
        assert date.year == 2025
        assert date.month == 4
        assert date.day == 1
        assert date.hour == 12
        assert date.minute == 0

    def test_separate_date_mmddyy_no_time(self):
        date = DateManager.handle_separate_datetime(
            {'date': '040125', 'time': 'nan'}
        )
        assert type(date), pd.DatetimeIndex
        assert date.year == 2025
        assert date.month == 4
        assert date.day == 1
        assert date.hour == 00
        assert date.minute == 0

    def test_separate_date_no_date(self):
        with pytest.raises(ValueError):
            DateManager.handle_separate_datetime({})
    # ========================= #
    # Method: adjust_timezone   #
    # ========================= #

    def test_adjust_timezone_date_with_no_zone(self, test_date):
        assert test_date.tz is None
        date = DateManager.adjust_timezone(
            test_date, in_timezone, out_timezone
        )
        assert date.tz.zone == out_timezone
        # Should have shifted the hours. Not testing for exactness to make
        # the test safe against running on machines in different locations
        assert date.hour != test_date.hour

    def test_adjust_timezone_date_with_zone(self, test_date):
        test_date = test_date.tz_localize(pytz.timezone('US/Mountain'))
        date = DateManager.adjust_timezone(
            test_date, in_timezone, out_timezone
        )
        assert date.tz.zone == out_timezone

    def test_adjust_timezone_no_in_zone(self, test_date):
        with pytest.raises(ValueError):
            DateManager.adjust_timezone(
                date=test_date,
                out_timezone=out_timezone
            )
