import pandas as pd
import pytest
import pytz

from insitupy.io.dates import DateTimeManager
from insitupy.io.yaml_codes import YamlCodes

in_timezone = 'US/Mountain'
out_timezone = 'UTC'


@pytest.fixture
def test_date():
    return pd.to_datetime('2025-04-01')


class TestDateTimeManager:
    # TODO: Cover GPR dates logic

    def test_parse_with_datetime(self):
        date = "2025-06-05T12:30:00"
        header = {
            YamlCodes.DATE_TIME: date,
        }

        result = DateTimeManager.parse(header)

        assert isinstance(result, pd.Timestamp)
        assert result == pd.Timestamp(date)

    def test_parse_with_separate_date_and_time(self, mocker):
        header = {
            YamlCodes.DATE: "2025-06-05",
            YamlCodes.TIME: "12:30:00",
        }
        mocked_handle_separate_datetime = mocker.patch(
            "insitupy.io.dates.DateTimeManager.handle_separate_datetime",
            return_value=pd.Timestamp("2025-06-05 12:30:00")
        )

        result = DateTimeManager.parse(header)

        mocked_handle_separate_datetime.assert_called_once_with(header)
        assert isinstance(result, pd.Timestamp)
        assert result == pd.Timestamp("2025-06-05 12:30:00")

    def test_parse_with_missing_data(self, mocker):
        header = {}
        mocked_handle_separate_datetime = mocker.patch(
            "insitupy.io.dates.DateTimeManager.handle_separate_datetime",
            return_value=None
        )

        result = DateTimeManager.parse(header)

        mocked_handle_separate_datetime.assert_called_once_with(header)
        assert result is None

    def test_parse_with_invalid_datetime(self):
        header = {
            YamlCodes.DATE_TIME: "invalid-datetime",
        }
        with pytest.raises(ValueError):
            DateTimeManager.parse(header)

    @pytest.mark.parametrize(
        "date, time",
        [
            ("2025-04-01", "12:00"),
            ("2025-04-01", "NaN"),
            ("2025-04-01", ""),
            ("20250401", "12:00"),
            ("20250401", "12:00:00"),
            ("20250401", "12:00:59"),
            ("040125", "120059.15"),
            ("040125", "NaN"),
        ],
    )
    def test_separate_date_and_time(self, date, time):
        date = DateTimeManager.handle_separate_datetime(
            {
                'date': date,
                'time': time,
                'header1': 'value1',
            }
        )
        assert type(date), pd.DatetimeIndex
        assert date.year == 2025
        assert date.month == 4
        assert date.day == 1
        if ':' in time or '.' in time:
            assert date.hour == 12
            assert date.minute == 0
            if time[-1] == '0':
                assert date.second == 0
            elif time[-3] == '.':
                assert str(date.second) == time[-5:-3]
            else:
                assert str(date.second) == time[-2:]
        else:
            assert date.hour == 0
            assert date.minute == 0
            assert date.second == 0

    def test_separate_date_no_time(self):
        date = DateTimeManager.handle_separate_datetime({'date': '2025-04-01'})
        assert type(date), pd.DatetimeIndex
        assert date.year == 2025
        assert date.month == 4
        assert date.day == 1
        assert date.hour == 00
        assert date.minute == 0

    def test_separate_date_time_nan(self):
        date = DateTimeManager.handle_separate_datetime(
            {'date': '2025-04-01', 'time': 'nan'}
        )
        assert type(date), pd.DatetimeIndex
        assert date.year == 2025
        assert date.month == 4
        assert date.day == 1
        assert date.hour == 00
        assert date.minute == 0

    def test_separate_date_mmddyy(self):
        date = DateTimeManager.handle_separate_datetime({'date': '040125'})
        assert type(date), pd.DatetimeIndex
        assert date.year == 2025
        assert date.month == 4
        assert date.day == 1
        assert date.hour == 00
        assert date.minute == 0

    def test_separate_date_mmddyy_time(self):
        date = DateTimeManager.handle_separate_datetime(
            {'date': '040125', 'time': '12:00'}
        )
        assert type(date), pd.DatetimeIndex
        assert date.year == 2025
        assert date.month == 4
        assert date.day == 1
        assert date.hour == 12
        assert date.minute == 0

    def test_separate_date_mmddyy_no_time(self):
        date = DateTimeManager.handle_separate_datetime(
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
            DateTimeManager.handle_separate_datetime({})

    # ========================= #
    # Method: adjust_timezone   #
    # ========================= #

    def test_adjust_timezone_date_with_no_zone(self, test_date):
        assert test_date.tz is None
        date = DateTimeManager.adjust_timezone(
            test_date, in_timezone, out_timezone
        )
        assert date.tz.zone == out_timezone
        # Should have shifted the hours. Not testing for exactness to make
        # the test safe against running on machines in different locations
        assert date.hour != test_date.hour

    def test_adjust_timezone_date_with_zone(self, test_date):
        test_date = test_date.tz_localize(pytz.timezone('US/Mountain'))
        date = DateTimeManager.adjust_timezone(
            test_date, in_timezone, out_timezone
        )
        assert date.tz.zone == out_timezone

    def test_adjust_timezone_no_in_zone(self, test_date):
        with pytest.raises(ValueError):
            DateTimeManager.adjust_timezone(
                date=test_date,
                out_timezone=out_timezone
            )
