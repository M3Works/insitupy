from datetime import timedelta

import pandas as pd
import pytz

from .strings import StringManager
from .yaml_codes import YamlCodes


class RowKeys:
    UTC_DOY = 'utcdoy'
    UTC_YEAR = 'utcyear'
    UTC_TOD = 'utctod'


class DateTimeManager:
    @staticmethod
    def parse(rows: dict) -> pd.Timestamp:
        """
        Parses the header dictionary to extract a datetime value.

        Args:
            rows (dict): Dictionary containing date and time information.

        Returns:
            pd.Timestamp: A pandas Timestamp object representing the parsed
            datetime value.
        """
        datetime = None
        # Look for a 'datetime' header entry
        if rows.get(YamlCodes.DATE_TIME) is not None:
            str_date = str(
                rows[YamlCodes.DATE_TIME].replace('T', '-')
            )
            datetime = pd.to_datetime(str_date)

        # If we didn't find date/time combined.
        if datetime is None:
            datetime = DateTimeManager.handle_separate_datetime(rows)

        return datetime

    @staticmethod
    def handle_separate_datetime(rows):
        """
        Handle a separate date and time entry. This assumes the keys
        'date' and 'time' in two separate lines in the header.

        Args:
            rows: parsed header rows
        Returns:
            parsed datetime
        """
        keys = [k.lower() for k in rows.keys()]

        # Handle data dates and times
        if YamlCodes.DATE in keys and YamlCodes.TIME in keys:
            date_str = str(rows[YamlCodes.DATE])

            # Let pandas try the date separate first
            if len(date_str) == 6:
                date_str = pd.to_datetime(date_str).strftime('%Y-%m-%d')

            # Allow for nan time
            time_str = StringManager.parse_none(rows[YamlCodes.TIME])

            if time_str is not None:
                date_str += f" {time_str}"

            datetime = pd.to_datetime(date_str)

        elif YamlCodes.DATE in keys:
            datetime = pd.to_datetime(rows[YamlCodes.DATE])

        # Handle gpr data dates
        elif RowKeys.UTC_YEAR in keys and \
                RowKeys.UTC_DOY in keys and RowKeys.UTC_TOD in keys:
            base = pd.to_datetime(
                '{:d}-01-01 00:00:00 '.format(int(rows[RowKeys.UTC_YEAR])),
                utc=True
            )

            # Number of days since january 1
            days = int(rows[RowKeys.UTC_DOY]) - 1

            # Zulu time (time without colons)
            time = str(rows[RowKeys.UTC_TOD])
            hours = int(time[0:2])  # hours
            minutes = int(time[2:4])  # minutes
            seconds = int(time[4:6])  # seconds
            milliseconds = int(
                float('0.' + time.split('.')[-1]) * 1000
            )  # milliseconds

            delta = timedelta(
                days=days, hours=hours, minutes=minutes,
                seconds=seconds, milliseconds=milliseconds
            )
            # This is the only key set that ignores in_timezone
            datetime = base.astimezone(pytz.timezone('UTC')) + delta

        else:
            raise ValueError(f'Data is missing date/time info!\n{rows}')

        return datetime

    @staticmethod
    def adjust_timezone(date, in_timezone=None, out_timezone=None):
        """
        Adjust the datatime object for given timezone

        Args:
            date: parsed datetime object from pandas
            in_timezone: str - Incoming time zone
            out_timezone: str - Target time zone

        Returns:
            Date changed to target timezone
        """
        out_timezone = pytz.timezone(out_timezone)

        # Convert timezones if it is provided this variable gets rewritten
        # later
        if in_timezone is not None:
            in_tz = pytz.timezone(in_timezone)
        # Otherwise assume incoming data is the same timezone
        # TODO: how do we handle row based timezone
        else:
            raise ValueError("We did not receive a valid in_timezone")

        if date.tz is not None and date.tz.zone == in_tz.zone:
            date = date.astimezone(out_timezone)
        else:
            date = date.tz_localize(in_tz)
            date = date.astimezone(out_timezone)

        return date
