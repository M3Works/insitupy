from datetime import timedelta

import logging
from typing import List

import pandas as pd
import pytz
import utm

from .strings import StringManager
from ..variables import ExtendableVariables
from ..profiles.metadata import ProfileMetaData

LOG = logging.getLogger(__name__)


class MetaDataParser:
    """
    Base class for parsing metadata
    """
    OUT_TIMEZONE = "UTC"
    ID_NAMES = ["pitid", "pit_id"]
    SITE_NAME_NAMES = ["location", "site_name"]
    LAT_NAMES = ["lat", "latitude"]
    LON_NAMES = ["lon", "lon", "longitude"]
    UTM_EPSG_PREFIX = "269"
    NORTHERN_HEMISPHERE = True

    def __init__(
        self, fname, timezone, primary_variables: ExtendableVariables,
        metadata_variables: ExtendableVariables,
        header_sep=",", allow_split_lines=False,
        allow_map_failures=False,
        _id=None, campaign_name=None, units_map=None
    ):
        """
        Args:
            fname: path to file
            timezone: string timezone
            primary_variables: ExtendableVariables for primary variables
            metadata_variables: ExtendableVariables for metadata variables
            header_sep: expected header separator
            allow_split_lines: Allow for split header lines that
                don't start with the expected header character. In this case
                the number of header lines will be the max line starting with
                the expected character, and lines that don't start with
                that character will be combined with the previous line
            allow_map_failures: if a mapping fails, warn us and use the
                original string (default False)
            id: optional pass in to override id in parse_id
            campaign_name: optional override for campaign name
            units_map = optional map of variable type to MeasurementDescription
        """
        self._fname = fname
        self._input_timezone = timezone
        self._header_sep = header_sep
        self._rough_obj = {}
        self._lat_lon_easting_northing = None
        self._id = _id
        self._campaign_name = campaign_name
        self._units_map = units_map or {}

        self.primary_variables = primary_variables
        self.metadata_variables = metadata_variables

        self._allow_split_header_lines = allow_split_lines
        self._allow_map_failures = allow_map_failures

    @property
    def rough_obj(self):
        return self._rough_obj

    @property
    def units_map(self):
        return self._units_map

    @property
    def lat_lon_easting_northing(self):
        if self._lat_lon_easting_northing is None:
            self._lat_lon_easting_northing = self.parse_location_from_row(
                self.rough_obj
            )
        return self._lat_lon_easting_northing

    def parse_id(self) -> str:
        if self._id is not None:
            return self._id
        else:
            for k, v in self.rough_obj.items():
                if k in self.ID_NAMES:
                    return v

        raise RuntimeError(f"Failed to parse ID from {self.rough_obj}")

    @staticmethod
    def _handle_separate_datetime(row, keys, out_tz):
        """
        Handle a separate date and time entry

        Args:
            keys: list of keys
            out_tz: desired timezone
        Returns:
            parsed datetime
        """
        # Handle data dates and times
        if 'date' in keys and 'time' in keys:
            # Assume MMDDYY format
            if len(str(row['date'])) == 6:
                dt = str(row['date'])
                # Put into YY-MM-DD
                row['date'] = f'20{dt[-2:]}-{dt[0:2]}-{dt[2:4]}'
                # Allow for nan time
                row['time'] = StringManager.parse_none(
                    row['time']
                )

            date_str = str(row["date"])
            if row["time"] is not None:
                date_str += f" {row['time']}"
            d = pd.to_datetime(date_str)

        elif 'date' in keys:
            d = pd.to_datetime(row['date'])

        # Handle gpr data dates
        elif 'utcyear' in keys and 'utcdoy' in keys and 'utctod' in keys:
            base = pd.to_datetime(
                '{:d}-01-01 00:00:00 '.format(int(row['utcyear'])),
                utc=True)

            # Number of days since january 1
            d = int(row['utcdoy']) - 1

            # Zulu time (time without colons)
            time = str(row['utctod'])
            hr = int(time[0:2])  # hours
            mm = int(time[2:4])  # minutes
            ss = int(time[4:6])  # seconds
            ms = int(
                float('0.' + time.split('.')[-1]) * 1000)  # milliseconds

            delta = timedelta(
                days=d, hours=hr, minutes=mm, seconds=ss, milliseconds=ms
            )
            # This is the only key set that ignores in_timezone
            d = base.astimezone(pytz.timezone('UTC')) + delta
            d = d.astimezone(out_tz)

        else:
            raise ValueError(
                f'Data is missing date/time info!\n{row}'
            )
        return d

    def parse_date_time(self) -> pd.Timestamp:
        return self.datetime_from_row(
            self.rough_obj, in_timezone=self._input_timezone
        )

    @classmethod
    def datetime_from_row(cls, row, in_timezone=None):
        keys = [k.lower() for k in row.keys()]
        d = None
        out_tz = pytz.timezone(cls.OUT_TIMEZONE)
        # Convert timezones if it is provided
        # this variable gets rewritten later
        if in_timezone is not None:
            in_tz = pytz.timezone(in_timezone)
        # Otherwise assume incoming data is the same timezone
        # TODO: how do we handle row based timezone
        else:
            raise ValueError("We did not recieve a valid in_timezone")

        # Look for a single header entry containing date and time.
        for k in keys:
            kl = k.lower()
            if 'date' in kl and 'time' in kl:
                str_date = str(row[k].replace('T', '-'))
                d = pd.to_datetime(str_date)
                break

        # If we didn't find date/time combined.
        if d is None:
            d = cls._handle_separate_datetime(row, keys, out_tz)

        if in_timezone is not None:
            if d.tz is not None and d.tz.zone == in_tz.zone:
                pass
            else:
                d = d.tz_localize(in_tz)
                d = d.astimezone(out_tz)

        else:
            d.replace(tzinfo=out_tz)

        row['date'] = d.date()

        # Don't add time to a time that was nan or none
        if 'time' not in row.keys():
            row['time'] = d.timetz()
        else:
            if row['time'] is not None:
                row['time'] = d.timetz()

        dt_str = row["date"].isoformat()
        if row.get("time"):
            dt_str += f"T{row['time'].isoformat()}"
        dt = pd.to_datetime(dt_str)

        return dt

    @classmethod
    def _parse_location_from_raw(cls, row):
        """
        Initial parse of lat, lon, easting, northing from
        the rough object
        """
        lat = None
        lon = None
        easting = None
        northing = None
        for k, v in row.items():
            if k in cls.LAT_NAMES:
                lat = float(v)
            elif k in cls.LON_NAMES:
                lon = float(v)
            elif k == "easting":
                easting = v
            elif k == "northing":
                northing = v

        return lat, lon, easting, northing

    @classmethod
    def lat_lon_from_easting_northing(cls, row, easting, northing):
        zone_number = cls.utm_epsg_from_row(row)
        if isinstance(zone_number, str):
            raise RuntimeError(
                f"{zone_number} should be an integer"
            )
        # Get the last two digits
        zone_number = int(str(zone_number)[-2:])
        try:
            lat, lon = utm.to_latlon(
                float(easting), float(northing), int(zone_number),
                northern=cls.NORTHERN_HEMISPHERE)
        except Exception as e:
            LOG.error(e)
            raise RuntimeError(f"Failed with {easting}, {northing}")

        return lat, lon

    @classmethod
    def parse_location_from_row(cls, row):
        """
        Parse the lat and lon from the rough input object
        Also parse the easting and northing
        # UTM Zone,13N
        # Easting,329131
        # Northing,4310328
        # Latitude,38.92524
        # Longitude,-106.97112
        # Flags,

        returns lat, lon, easting, northing
        """
        lat, lon, easting, northing = cls._parse_location_from_raw(row)

        # Do nothing first
        if lat and lon:
            LOG.info("Latitude and Longitude parsed from the file")
        elif easting and northing:
            lat, lon = cls.lat_lon_from_easting_northing(row, easting, northing)
        else:
            raise ValueError(
                f"Could not parse location from {row}"
            )
        return lat, lon, easting, northing

    def parse_latitude(self) -> float:
        return self.lat_lon_easting_northing[0]

    def parse_longitude(self) -> float:
        return self.lat_lon_easting_northing[1]

    def parse_utm_epsg(self) -> int:
        return self.utm_epsg_from_row(self.rough_obj)

    @classmethod
    def utm_epsg_from_row(cls, row):
        epsg = None
        if 'utm_zone' in row.keys():
            utm_zone = int(
                ''.join([c for c in row['utm_zone'] if c.isnumeric()]))
            epsg = int(f"{cls.UTM_EPSG_PREFIX}{utm_zone}")
        elif 'epsg' in row.keys():
            epsg = row["epsg"]
        # TODO: row based utm?
        return epsg

    @classmethod
    def parse_campaign_from_row(cls, row):
        for k, v in row.items():
            if k in cls.SITE_NAME_NAMES:
                return v
        return None

    def parse_campaign_name(self) -> str:
        if self._campaign_name is not None:
            return self._campaign_name
        else:
            campaign_name = self.parse_campaign_from_row(self.rough_obj)
            if campaign_name is None:
                raise RuntimeError(
                    f"Failed to parse Site Name from {self.rough_obj}"
                )
            return campaign_name

    def parse_flags(self):
        result = None
        for k, v in self.rough_obj.items():
            if k in ["flags"]:
                result = v
                break

        return result

    def observers_from_row(self, row):
        result = None
        for k, v in row.items():
            if k in ["observers"]:
                entry = v
                result = entry.split(", ")
                result = [r.strip() for r in result]
                break
        return result

    def parse_observers(self) -> List[str]:
        return self.observers_from_row(self.rough_obj)

    def _preparse_meta(self, meta_lines):
        """
        Organize the header lines into a dictionary with lower case keys
        """
        # Key value pairs are separate by some separator provided.
        data = {}

        # Collect key value pairs from the information above the column header
        for ln in meta_lines:
            d = ln.split(self._header_sep)

            # Key is always the first entry in comma sep list
            k = StringManager.standardize_key(d[0])

            # Avoid splitting on times
            if 'time' in k or 'date' in k:
                value = ':'.join(d[1:]).strip()
            else:
                value = ', '.join(d[1:])
                value = StringManager.clean_str(value)

            # cast the rough object key to a known key
            known_name, k_mapping = self.metadata_variables.from_mapping(
                k, allow_failure=self._allow_map_failures
            )

            # Assign non-empty strings to dictionary
            if k and value:
                data[known_name] = value.strip(
                    ' '
                ).replace('"', '').replace('  ', ' ')

            elif k and not value:
                data[known_name] = None
        return data

    def parse(self):
        """
        Parse the file and return a metadata object.
        We can override these methods as needed to parse the different
        metadata

        This populates self.rough_obj

        Returns:
            (metadata object, column list, position of header in file)
        """
        (meta_lines, columns,
         columns_map, header_position) = self.find_header_info(self._fname)
        self._rough_obj = self._preparse_meta(meta_lines)
        # Create a standard metadata object
        metadata = ProfileMetaData(
            site_name=self.parse_id(),
            date_time=self.parse_date_time(),
            latitude=self.parse_latitude(),
            longitude=self.parse_longitude(),
            utm_epsg=str(self.parse_utm_epsg()),
            campaign_name=self.parse_campaign_name(),
            flags=self.parse_flags(),
            observers=self.parse_observers()
        )

        return metadata, columns, columns_map, header_position

    def _parse_header(self, lines):
        # Key value pairs are separate by some separator provided.
        data = {}

        # Collect key value pairs from the information above the column header
        for ln in lines:
            d = ln.split(self._header_sep)

            # Key is always the first entry in comma sep list
            k = StringManager.standardize_key(d[0])

            # Avoid splitting on times
            if 'time' in k or 'date' in k:
                value = ':'.join(d[1:]).strip()
            else:
                value = ', '.join(d[1:])
                value = StringManager.clean_str(value)

            # Assign non empty strings to dictionary
            if k and value:
                data[k] = value.strip(' ').replace('"', '').replace('  ', ' ')

            elif k and not value:
                data[k] = None

        LOG.debug(
            'Discovered {} lines of valid header info.'
            ''.format(len(data.keys()))
        )
        return data

    def _parse_columns(self, str_line):
        """
        Parse the column names from the input line. This can include mapping
        """
        # Parse the columns header based on the size of the last line
        # Remove units
        # for c in ['()', '[]']:
        #     str_line = StringManager.strip_encapsulated(str_line, c)

        raw_cols = str_line.strip('#').split(',')
        # Clean the raw columns
        standard_cols = [StringManager.standardize_key(c) for c in raw_cols]
        # Infer units from the raw columns
        infered_units = [StringManager.infer_unit_from_key(c) for c in raw_cols]
        final_cols = []
        final_col_map = {}
        inferred_units_map = {}
        # Iterate through the columns and map to desired result
        for c, unit in zip(standard_cols, infered_units):
            mapped_col, col_map = self.primary_variables.from_mapping(
                c, allow_failure=self._allow_map_failures
            )
            # Store the list of columns to use when reading in the
            # dataframe
            final_cols.append(mapped_col)
            # Store the map of column name to the known variable
            final_col_map = {**final_col_map, **col_map}
            # Store the map of column name to inferred unit
            inferred_units_map[col_map[mapped_col].code] = unit

        return final_cols, final_col_map, inferred_units_map

    def find_header_info(self, filename=None):
        """
        Read in all site details file for a pit If the filename has the word
        site in it then we read everything in the file. Otherwise, we use this
        to read all the site data up to the header of the profile.

        E.g. Read all commented data until we see a column descriptor.

        Args:
            filename: Path to a csv containing # leading lines with site details

        Returns:
            tuple: **data** - Dictionary containing site details
                   **columns** - List of clean column names
                   **header_pos** - Index of the columns header for skiprows in
                                    read_csv
       """
        filename = filename or self._fname
        filename = str(filename)
        try:
            with open(filename, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(filename, "r", encoding="latin1") as f:
                lines = f.readlines()

        # Site description files have no need for column lists
        if 'site' in filename.lower():
            LOG.info('Parsing site description header...')
            columns = None
            header_pos = None
            header_indicator = None
            columns_map = {}
            self._units_map = self._units_map

        # Find the column names and where it is in the file
        else:
            header_pos, header_indicator = self._find_header_position(lines)
            # identify columns, map columns, and units map
            columns, columns_map, units_map = self._parse_columns(
                lines[header_pos]
            )
            # Combine with user defined units map
            self._units_map = {**self._units_map, **units_map}
            LOG.debug(
                f'Column Data found to be {len(columns)} columns based on'
                f' Line {header_pos}'
            )
            # Only parse what we know if the header
            lines = lines[0:header_pos]

        final_lines = lines

        # Clean up the lines from line returns to grab header info
        final_lines = [ln.strip() for ln in final_lines]
        # Join all data and split on header separator
        # This handles combining split lines
        str_data = " ".join(final_lines).split('#')
        str_data = [ln.strip() for ln in str_data if ln]

        return str_data, columns, columns_map, header_pos

    def _iterative_header_pos_search(self, lines, n_columns, header_indicator):
        # Use these to monitor if a larger column count is found
        header_pos = 0
        for i, l in enumerate(lines):
            if i == 0:
                previous = StringManager.get_alpha_ratio(lines[i])
            else:
                previous = StringManager.get_alpha_ratio(lines[i - 1])

            if StringManager.line_is_header(
                l, expected_columns=n_columns,
                header_indicator=header_indicator,
                previous_alpha_ratio=previous
            ):
                header_pos = i

            if i > header_pos:
                break
        return header_pos

    def _find_header_position(self, lines):
        """
        A flexible method that attempts to find and standardize column names
        for csv data. Looks for a comma separated line with N entries == to the
        last line in the file. If an entry is found with more commas than the
        last line then we use that. This allows us to have data that doesn't
        have all the commas in the data (SSA typically missing the comma for
        veg unless it was notable)

        Assumptions:

        1. The last line in file is of representative csv data
        2. The header is the last column that has more chars than numbers

        Args:
            lines: Complete list of strings from the file

        Returns:
            header position
        """

        # Minimum column size should match the last line of data (Assumption
        # #2)
        n_columns = len(lines[-1].split(','))

        if lines[0][0] == '#':
            header_indicator = '#'
        else:
            header_indicator = None

        if self._allow_split_header_lines:
            if header_indicator is None:
                raise RuntimeError(
                    "Cannot allow split lines with no clear header indicator"
                )
            else:
                # header pos is max lines with
                # first character == header indicator
                header_indices = [
                    index for index, value in enumerate(lines)
                    if value[0] == header_indicator
                ]
                header_pos = max(header_indices)

        else:
            header_pos = self._iterative_header_pos_search(
                lines, n_columns, header_indicator
            )

        LOG.debug('Found end of header at line {}...'.format(header_pos))
        return header_pos, header_indicator
