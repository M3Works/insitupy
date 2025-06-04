import logging
from typing import List

import pandas as pd

from .dates import DateManager
from .locations import LocationManager
from .strings import StringManager
from .yaml_codes import YamlCodes
from ..profiles.metadata import ProfileMetaData
from ..variables import ExtendableVariables

LOG = logging.getLogger(__name__)


class MetaDataParser:
    """
    Base class for parsing metadata
    """
    OUT_TIMEZONE = "UTC"

    def __init__(
        self,
        fname,
        timezone,
        primary_variables: ExtendableVariables,
        metadata_variables: ExtendableVariables,
        header_sep=",",
        allow_split_lines=False,
        allow_map_failures=False,
        _id=None,
        campaign_name=None,
        units_map=None
    ):
        """
        Args:
            fname: path of csv file to parse
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
            _id: optional pass in to override id in parse_id
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
            self._lat_lon_easting_northing = \
                LocationManager.parse(self.rough_obj)
        return self._lat_lon_easting_northing

    # TODO: See remark on .parse_campaign_name
    def parse_id(self) -> str:
        if self._id is not None:
            return self._id
        else:
            try:
                return self.rough_obj[YamlCodes.ID_NAME]
            except KeyError:
                raise RuntimeError(f"Failed to parse ID from {self.rough_obj}")

    def parse_date_time(self) -> pd.Timestamp:
        datetime = None
        # TODO: Move this logic into the DateManager and extend the base
        #       metadata parser to also support separate time and date fields
        # In case we found a date entry that has date and time
        if self.rough_obj[YamlCodes.DATE_TIME] is not None:
            str_date = str(
                self.rough_obj[YamlCodes.DATE_TIME].replace('T', '-')
            )
            datetime = pd.to_datetime(str_date)

        # If we didn't find date/time combined.
        if datetime is None:
            datetime = DateManager.handle_separate_datetime(self.rough_obj)

        return DateManager.adjust_timezone(
            datetime,
            in_timezone=self._input_timezone,
            out_timezone=self.OUT_TIMEZONE
        )

    def parse_latitude(self) -> float:
        return self.lat_lon_easting_northing[0]

    def parse_longitude(self) -> float:
        return self.lat_lon_easting_northing[1]

    def parse_utm_epsg(self) -> int:
        return LocationManager.parse_utm_epsg(self.rough_obj)

    # TODO: This needs to be revisited. Right now we have a mix and match
    #       of wording for a site vs a campaign
    def parse_campaign_name(self) -> str:
        if self._campaign_name is not None:
            return self._campaign_name
        else:
            try:
                return self.rough_obj[YamlCodes.SITE_NAME]
            except KeyError:
                raise RuntimeError(
                    f"Failed to parse Site Name from {self.rough_obj}"
                )

    # TODO: Expand base metadata YAML to detect this
    def parse_flags(self):
        result = None
        for k, v in self.rough_obj.items():
            if k in ["flags"]:
                result = v
                break

        return result

    # TODO: Expand base metadata YAML to detect this
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
        meta_lines, columns, columns_map, header_position = \
            self.find_header_info(self._fname)
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
            # TODO: could we return unmapped columns here?
            mapped_col, col_map = self.primary_variables.from_mapping(
                c, allow_failure=self._allow_map_failures
            )
            # Store the list of columns to use when reading in the
            # dataframe
            final_cols.append(mapped_col)
            # Store the map of column name to the known variable
            final_col_map = {**final_col_map, **col_map}
            # Store the map of column name to inferred unit
            result_obj = col_map[mapped_col]
            if result_obj is None:
                if self._allow_map_failures:
                    LOG.warning(f"No unit for {c}")
                else:
                    raise RuntimeError(
                        f"No unit for {c} - column mapping has failed"
                    )
            else:
                # override the code if it is given
                inferred_units_map[
                    result_obj.code
                ] = self._units_map.get(result_obj.code) or unit

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
