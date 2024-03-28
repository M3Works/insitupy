from dataclasses import dataclass
from datetime import timedelta

import logging
import pandas as pd
import pytz
import utm

from loomsitu.campaigns.strings import StringManager

LOG = logging.getLogger(__name__)


@dataclass()
class ProfileMetaData:
    id: str
    date_time: pd.Timestamp
    latitude: float
    longitude: float
    utm_zone: str = None
    site_id: str = None
    site_name: str = None


class MetaDataParser:
    """
    Base class for parsing metadata
    """
    def __init__(self, fname, timezone):
        self._fname = fname
        self.input_timezone = timezone

    def parse_id(self, meta_str) -> str:
        pass

    def parse_date_time(self, meta_str) -> pd.Timestamp:
        pass

    def parse_latitude(self, meta_str) -> float:
        pass

    def parse_longitude(self, meta_str) -> float:
        pass

    def parse_utm_zone(self, meta_str) -> str:
        pass

    def parse_site_id(self, meta_str) -> str:
        pass

    def parse_site_name(self, meta_str) -> str:
        pass

    def parse(self) -> ProfileMetaData:
        """
        Parse the file and return a metadata object.
        We can override these methods as needed to parse the different
        metadata
        """
        meta_str = None  # get the metadata string from reading the file
        metadata = ProfileMetaData(
            id=self.parse_id(meta_str),
            date_time=self.parse_date_time(meta_str),
            latitude=self.parse_latitude(meta_str),
            longitude=self.parse_longitude(meta_str),
            utm_zone=self.parse_utm_zone(meta_str),
            site_id=self.parse_site_id(meta_str),
            site_name=self.parse_site_name(meta_str),
        )
        columns = None
        header_position = None

        return metadata, columns, header_position



class MetaMixIn:
    @staticmethod
    def find_kw_in_lines(kw, lines, addon_str=' = '):
        """
        Returns the index of a list of strings that had a kw in it

        Args:
            kw: Keyword to find in a line
            lines: List of strings to search for the keyword
            addon_str: String to append to your key word to help filter
        Return:
            i: Integer of the index of a line containing a kw. -1 otherwise
        """
        str_temp = '{}' + addon_str

        for i, line in enumerate(lines):
            s = str_temp.format(kw)

            uncommented = line.strip('#')

            if s in uncommented:
                if s[0] == uncommented[0]:
                    break
        # No match
        # TODO: here
        if i == len(lines) - 1:
            i = -1

        return i

    @staticmethod
    def assign_default_kwargs(object, kwargs, defaults, leave=None):
        """
        Assign keyword arguments to class attributes. If a key in the default
        is not in the kwargs then its value becomes the value in the default.
        Any value found in the defaults is removed from the kwargs

        Args:
            object: Object to assign as keys in defaults as attributes
            kwargs: Dictionary of keyword arguments provided
            defaults: Dictionary of all class related arguments that are assigned as attributes
            leave: List of attributes to leave in mod_kwargs
        Returns:
            mod_kwargs: kwargs with all keys in the defaults removed from it.
        """
        leave = leave or []
        mod_kwargs = kwargs.copy()

        # Loop over all the defaults
        for k, v in defaults.items():
            # if the k was provided then use it and remove it from the kwargs
            if k in kwargs.keys():
                value = kwargs[k]
                # Delete it so kwargs could be passed on for other use unless its
                # requested to be left
                if k not in leave:
                    del mod_kwargs[k]

            else:
                # Make sure we have a value assigned from the defaults
                value = v

            # Assign it as a class attribute
            setattr(object, k, value)

        return mod_kwargs

    @staticmethod
    def is_point_data(columns):
        """
        Searches the csv column names to see if the data set is point data,
        which will have latitude or easting in the columns. If it is, return True

        Args:
            columns: List of dataframe columns
        Return:
            result: Boolean indicating if the data is point data
        """

        result = False

        # Check for point data which will contain this in the data not the header
        if columns is not None and (
            'latitude' in columns or 'easting' in columns):
            result = True

        return result

    @staticmethod
    def manage_degrees(info):
        """
        Manages and interprets string values relating to degrees. Removes
        degrees symbols and interprets key word flat for slope.

        Args:
            info: Dictionary containing potential degrees entries to be converted
                  to numbers
        Returns:
            info: Modificed dictionary containing string numeric representations of keys
                  aspect and slope_angle
        """

        # Manage degrees symbols
        for k in ['aspect', 'slope_angle', 'air_temp']:
            if k in info.keys():
                v = info[k]
                if isinstance(v, str) and v is not None:
                    # Remove any degrees symbols
                    v = v.replace('\u00b0', '')
                    v = v.replace('Â', '')

                    # Sometimes a range is used for the slope. Always pick the
                    # larger value
                    if '-' in v:
                        v = v.split('-')[-1]

                    if v.lower() == 'flat':
                        v = '0'

                    if v.isnumeric():
                        v = float(v)
                    info[k] = v
        return info

    @classmethod
    def manage_aspect(cls, info):
        """
        Manages when aspect is recorded in cardinal directions and converts it to
        a degrees from North float.

        Args:
            info: Dictionary potentially containing key aspect. Converts cardinal
        Returns:
            info: Dictionary with any key named aspect converted to  a float of degrees from north
        """

        # Convert Cardinal dirs to degrees
        if 'aspect' in info.keys():
            aspect = info['aspect']
            if aspect is not None and isinstance(aspect, str):
                # Check for number of numeric values.
                numeric = len([True for c in aspect if c.isnumeric()])

                if numeric != len(aspect) and aspect is not None:
                    LOG.warning('Aspect recorded for site {} is in cardinal '
                                'directions, converting to degrees...'
                                ''.format(info['site_id']))
                    deg = cls.convert_cardinal_to_degree(aspect)
                    info['aspect'] = deg
        return info

    @staticmethod
    def convert_cardinal_to_degree(cardinal):
        """
        Converts cardinal directions to degrees. Also removes any / or - that
        might get used to say between two cardinal directions

        e.g. S/SW turns into SSW which is interpreted as halfway between those
        two directions allowing for 22.5 degree increments.

        Args:
            Cardinal: Letters representing cardinal direction

        Returns:
            degrees: Float representing cardinal direction in degrees from north
        """

        dirs = [
            'N',
            'NNE',
            'NE',
            'ENE',
            'E',
            'ESE',
            'SE',
            'SSE',
            'S',
            'SSW',
            'SW',
            'WSW',
            'W',
            'WNW',
            'NW',
            'NNW']

        # Manage extra characters separating composite dirs, make it all upper case
        d = ''.join([c.upper() for c in cardinal if c not in '/-'])

        # Assume West, East, South, Or North
        if len(d) > 3:
            d = d[0]
            LOG.warning("Assuming {} is {}".format(cardinal, d))

        if d in dirs:
            i = dirs.index(d)
            degrees = i * (360. / len(dirs))
        else:
            raise ValueError('Invalid cardinal direction {}!'.format(cardinal))

        return degrees

    @staticmethod
    def manage_utm_zone(info):
        """
        Maanage the nuance of having a utm zone string sometimes and
        then not being in the keys at all. If the utm_zone is in the
        dictionary then convert it to an integer. Otherwise add with
        assign None

        Args:
            info: Dictionary potentially carrying utm_zone
        Returns:
            info: Dictionary containing utm_zone
        """
        if 'utm_zone' in info.keys():
            info['utm_zone'] = int(
                ''.join([c for c in info['utm_zone'] if c.isnumeric()]))
            info['epsg'] = int(f"269{info['utm_zone']}")
        elif 'epsg' in info.keys():
            if info['epsg'] is not None:
                info['utm_zone'] = int(str(info['epsg'])[-2:])
        else:
            info['utm_zone'] = None
            info['epsg'] = None

        return info


class DataHeader(MetaMixIn):
    """
    Class for managing information stored in files headers about a snow pit
    site.

    Format of such file headers should be
    1. Each line of importance is preceded by a #
    2. Key values should be comma separated.

    e.g.
        `# PitID,COGM1C8_20200131`
        `# Date/Time,2020-01-31-15:10`

    If the file is not determined to be a site details file as indicated by the
    word site in the filename, then the all header lines except the last line
    is interpreted as header. In csv files the last line of the
    header should be the column header which is also interpreted and stored
    as a class attribute

    Attributes:
        info: Dictionary containing all header information, stripped of
              unnecessary chars, all lower case, and all spaces replaced with
              underscores
        columns: Column names of data stored in csv. None for site description
                 files which is basically all one header
        data_names: List of data names to be uploaded
        multi_sample_profiles: List containing profile types that
                              have multiple samples (e.g. density). This
                              triggers calculating the mean of the profiles
                              for the main value
        extra_header: Dictionary containing supplemental information to write
                      into the .info dictionary after its generated. Any
                      duplicate keys will be overwritten with this info.
    """

    # Typical names we run into that need renaming
    # TODO: these could be enums
    rename = {'location': 'site_name',
              'top': 'depth',
              'height': 'depth',
              'bottom': 'bottom_depth',
              'site': 'site_id',
              'pitid': 'pit_id',
              'slope': 'slope_angle',
              'weather': 'weather_description',
              'sky': 'sky_cover',
              'notes': 'site_notes',
              'sample_top_height': 'depth',
              'deq': 'equivalent_diameter',
              'operator': 'observers',
              'surveyors': 'observers',
              'observer': 'observers',
              'total_snow_depth': 'total_depth',
              'smp_serial_number': 'instrument',
              'lat': 'latitude',
              'long': 'longitude',
              'lon': 'longitude',
              'twt': 'two_way_travel',
              'twt_ns': 'two_way_travel',
              'utmzone': 'utm_zone',
              'measurement_tool': 'instrument',
              'avgdensity': 'density',
              'avg_density': 'density',
              'dielectric_constant': 'permittivity',
              'flag': 'flags',
              'hs': 'depth',
              'swe_mm': 'swe',
              'depth_m': 'depth',
              'date_dd_mmm_yy': 'date',
              'time_gmt': 'time',
              'elev_m': 'elevation'
              }

    # Known possible profile types anything not in here will throw an error
    # TODO: these could be variables
    available_data_names = ['density', 'permittivity', 'lwc_vol', 'temperature',
                            'force', 'reflectance', 'sample_signal',
                            'specific_surface_area', 'equivalent_diameter',
                            'grain_size', 'hand_hardness', 'grain_type',
                            'manual_wetness', 'two_way_travel', 'depth', 'swe']

    # Defaults to keywords arguments
    defaults = {
        'in_timezone': None,
        'out_timezone': 'UTC',
        'epsg': None,
        'header_sep': ',',
        'northern_hemisphere': True,
        'depth_is_metadata': True}

    def __init__(self, filename, **kwargs):
        """
        Class for managing site details information

        Args:
            filename: File for a site details file containing
            header_sep: key value pairs in header information separator (: , etc)
            northern_hemisphere: Bool describing if the pit location is in the
                                 northern_hemisphere for converting utm coordinatess
            depth_is_metadata: Whether or not to include depth as a main
                              variable (useful for point data that contains
                              snow depth and other variables), profiles should
                              use depth as metadata
            kwargs: keyword values to pass to the database as metadata
        """

        self.extra_header = self.assign_default_kwargs(
            self, kwargs, self.defaults, leave=['epsg'])

        # Validate that an intentionally good in timezone was given
        in_timezone = kwargs.get('in_timezone')
        if in_timezone is None or "local" in in_timezone.lower():
            raise ValueError("A valid in_timezone was not provided")
        else:
            self.in_timezone = in_timezone

        LOG.info('Interpreting metadata in {}'.format(filename))

        # Site location files will have no data_name
        self.data_names = None

        # Does our profile type have multiple samples
        self.multi_sample_profiles = []

        # Read in the header into dictionary and list of columns names
        info, self.columns, self.header_pos = self._read(filename)

        # Interpret any data needing interpretation e.g. aspect
        self.info = self.interpret_data(info)

    @staticmethod
    def rename_sample_profiles(columns, data_names):
        """
        Rename columns like density_a to density_sample_a
        """
        result = []
        for c in columns:
            for data_name in data_names:
                v = c
                if data_name in c and c[-2] == '_':
                    v = c.replace(data_name, '{}_sample'.format(data_name))
                    result.append(v)

                elif c not in result and c[-2] != '_':
                    result.append(c)
        return result

    def parse_column_names(self, lines):
        """
        A flexible mnethod that attempts to find and standardize column names
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
            columns: list of column names
        """

        # Minimum column size should match the last line of data (Assumption
        # #2)
        n_columns = len(lines[-1].split(','))

        # Use these to monitor if a larger column count is found
        header_pos = 0
        if lines[0][0] == '#':
            header_indicator = '#'
        else:
            header_indicator = None

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

        LOG.debug('Found end of header at line {}...'.format(header_pos))

        # Parse the columns header based on the size of the last line
        str_line = lines[header_pos]
        # Remove units
        for c in ['()', '[]']:
            str_line = StringManager.strip_encapsulated(str_line, c)

        raw_cols = str_line.strip('#').split(',')
        standard_cols = [StringManager.standardize_key(c) for c in raw_cols]

        # Rename any column names to more standard ones
        columns = StringManager.remap_data_names(standard_cols, self.rename)

        # Determine the profile type
        (self.data_names, self.multi_sample_profiles) = \
            self.determine_data_names(columns)

        self.data_names = StringManager.remap_data_names(
            self.data_names, self.rename
        )

        if self.multi_sample_profiles:
            columns = self.rename_sample_profiles(columns, self.data_names)

        return columns, header_pos

    def determine_data_names(self, raw_columns):
        """
        Determine the names of the data to be uploaded from the raw column
        header. Also determine if this is the type of profile file that will
        submit more than one main value (e.g. hand_hardness, grain size all in
        the same file)

        Args:
            raw_columns: list of raw text split on commas of the column names

        Returns:
            type: **data_names** - list of column names that will be uploaded
                   as a main value
                  **multi_sample_profiles** - boolean representing if we will
                    average the samples for a main value (e.g. density)
        """
        # Names of columns we are going to submit as main values
        data_names = []
        multi_sample_profiles = []

        # String of the columns for counting
        str_cols = ' '.join(raw_columns).replace(' ', "_").lower()

        for dname in self.available_data_names:

            kw_count = str_cols.count(dname)

            # if we have keyword match in our columns then add the type
            if kw_count > 0:
                data_names.append(dname)

                # Avoid triggering on depth and bottom depth in profiles
                if kw_count > 1 and dname != 'depth':
                    LOG.debug('{} is multisampled...'.format(dname))
                    multi_sample_profiles.append(dname)

        # If depth is metadata (e.g. profiles) then remove it as a main
        # variable
        if 'depth' in data_names and self.depth_is_metadata:
            data_names.pop(data_names.index('depth'))

        if data_names:
            LOG.info('Names to be uploaded as main data are: {}'
                          ''.format(', '.join(data_names)))
        else:
            raise ValueError('Unable to determine data names from'
                             ' header/columns columns: {}'.format(", ".join(raw_columns)))

        if multi_sample_profiles:
            LOG.info('{} contains multiple samples for each '
                          'layer. The main value will be the average of '
                          'these samples.'.format(', '.join(multi_sample_profiles)))

        return data_names, multi_sample_profiles

    @classmethod
    def add_date_time_keys(cls, data, in_timezone=None, out_timezone='UTC'):
        """
        Convert string info from a date/time keys in a dictionary to date and time
        objects and assign it back to the dictionary as date and time

        Args:
            data: dictionary containing either the keys date/time or two keys date
                  and time
            in_timezone: String representing Pytz valid timezone of the data coming in
            out_timezone: String representing Pytz valid timezone of the data being returned

        Returns:
            d: Python Datetime object
        """
        keys = [k.lower() for k in data.keys()]
        d = None
        out_tz = pytz.timezone(out_timezone)
        in_tz = None

        # Convert timezones if it is provided
        if in_timezone is not None:
            in_tz = pytz.timezone(in_timezone)

        # Otherwise assume incoming data is the same timezone
        else:
            raise ValueError("We did not recieve a valid in_timezone")

        # Look for a single header entry containing date and time.
        for k in data.keys():
            kl = k.lower()
            if 'date' in kl and 'time' in kl:
                str_date = str(data[k].replace('T', '-'))
                d = pd.to_datetime(str_date)
                break

        # If we didn't find date/time combined.
        if d is None:
            # Handle data dates and times
            if 'date' in keys and 'time' in keys:
                # Assume MMDDYY format
                if len(data['date']) == 6:
                    dt = data['date']
                    # Put into YY-MM-DD
                    data['date'] = f'20{dt[-2:]}-{dt[0:2]}-{dt[2:4]}'
                    # Allow for nan time
                    data['time'] = StringManager.parse_none(data['time'])

                dstr = ' '.join([str(data[k]) for k in ['date', 'time']
                                 if data[k] is not None])
                d = pd.to_datetime(dstr)

            elif 'date' in keys:
                d = pd.to_datetime(data['date'])

            # Handle gpr data dates
            elif 'utcyear' in keys and 'utcdoy' in keys and 'utctod' in keys:
                base = pd.to_datetime(
                    '{:d}-01-01 00:00:00 '.format(int(data['utcyear'])),
                    utc=True)

                # Number of days since january 1
                d = int(data['utcdoy']) - 1

                # Zulu time (time without colons)
                time = str(data['utctod'])
                hr = int(time[0:2])  # hours
                mm = int(time[2:4])  # minutes
                ss = int(time[4:6])  # seconds
                ms = int(
                    float('0.' + time.split('.')[-1]) * 1000)  # milliseconds

                delta = timedelta(
                    days=d,
                    hours=hr,
                    minutes=mm,
                    seconds=ss,
                    milliseconds=ms)
                # This is the only key set that ignores in_timezone
                d = base.astimezone(pytz.timezone('UTC')) + delta

                # Avoid using in_timezone and UTC defined keys
                in_timezone = None

                d = d.astimezone(out_tz)

            else:
                raise ValueError(
                    'Data is missing date/time info!\n{}'.format(data))

        if in_timezone is not None:
            d = d.tz_localize(in_tz)
            d = d.astimezone(out_tz)

        else:
            d.replace(tzinfo=out_tz)

        data['date'] = d.date()

        # Dont add time to a time that was nan or none
        if 'time' not in data.keys():
            data['time'] = d.timetz()
        else:
            if data['time'] is not None:
                data['time'] = d.timetz()

        dt_str = data["date"].isoformat()
        if data.get("time"):
            dt_str += f"T{data['time'].isoformat()}"
        dt = pd.to_datetime(dt_str)
        data["date_time"] = dt

        return data

    def _read(self, filename):
        """
        Read in all site details file for a pit If the filename has the word site in it then we
        read everything in the file. Otherwise we use this to read all the site
        data up to the header of the profile.

        E.g. Read all commented data until we see a column descriptor.

        Args:
            filename: Path to a csv containing # leading lines with site details

        Returns:
            tuple: **data** - Dictionary containing site details
                   **columns** - List of clean column names
                   **header_pos** - Index of the columns header for skiprows in
                                    read_csv
       """

        with open(filename, encoding='latin') as fp:
            lines = fp.readlines()
            fp.close()

        # Site description files have no need for column lists
        if 'site' in filename.lower():
            LOG.info('Parsing site description header...')
            columns = None
            header_pos = None

            # Site location parses all of the file

        # Find the column names and where it is in the file
        else:
            columns, header_pos = self.parse_column_names(lines)
            LOG.debug('Column Data found to be {} columns based on Line '
                           '{}'.format(len(columns), header_pos))

            # Only parse what we know if the header
            lines = lines[0:header_pos]

        # Clean up the lines from line returns to grab header info
        lines = [ln.strip() for ln in lines]
        str_data = " ".join(lines).split('#')

        # Keep track of the number of lines with # in it for data opening
        self.length = len(str_data)

        # Key value pairs are separate by some separator provided.
        data = {}

        # Collect key value pairs from the information above the column header
        for ln in str_data:
            d = ln.split(self.header_sep)

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

        # If there is not header data then don't bother (useful for point data)
        if data:
            data = self.add_date_time_keys(
                data,
                in_timezone=self.in_timezone,
                out_timezone=self.out_timezone)

        # Rename the info dictionary keys to more standard ones
        data = StringManager.remap_data_names(data, self.rename)
        LOG.debug('Discovered {} lines of valid header info.'
                       ''.format(len(data.keys())))

        return data, columns, header_pos

    @staticmethod
    def reproject_point_in_dict(info, is_northern=True, zone_number=None):
        """
        Add/ensure that northing, easting, utm_zone, latitude, longitude and epsg code
        are in the metadata. Default to always project the lat long (if provided) to
        the northing and easting.

        Args:
            info: Dictionary containing key northing/easting or latitude longitude
            is_northern: Boolean for which hemisphere this data is in
            zone_number: Integer for the utm zone to enforce, otherwise let utm
                        figure it out

        Returns:
            result: Dictionary containing all previous information plus a coordinates
                    reprojected counter part
        """
        result = info.copy()

        # Convert any coords to numbers
        for c in ['northing', 'easting', 'latitude', 'longitude']:
            if c in result.keys():
                try:
                    result[c] = float(result[c])
                except Exception:
                    del result[c]

        keys = result.keys()
        # Use lat/long first
        if all([k in keys for k in ['latitude', 'longitude']]):
            LOG.debug("Already have lat, lon coordinates in metadata")

        # Secondarily use the utm to add lat long
        elif all([k in keys for k in ['northing', 'easting', 'utm_zone']]):

            if isinstance(result['utm_zone'], str):
                result['utm_zone'] = \
                    int(''.join(
                        [s for s in result['utm_zone'] if s.isnumeric()]))

            lat, long = utm.to_latlon(result['easting'], result['northing'],
                                      result['utm_zone'],
                                      northern=is_northern)

            result['latitude'] = lat
            result['longitude'] = long
        return result

    def interpret_data(self, raw_info):
        """
        Some data inside the headers is inconsistently noted. This function
        adjusts such data to the correct format.

        Adjustments include:

        A. Add in any extra info from the extra_header dictionary, defer to info
        provided by user

        B: Rename any keys that need to be renamed

        C. Aspect is recorded either cardinal directions or degrees from north,
        should be in degrees

        D. Cast UTM attributes to correct types. Convert UTM to lat long, store both


        Args:
            raw_info: Dictionary containing information to be parsed
        Returns:
            info: Dictionary of the raw_info containing interpetted info

        """
        info = {}

        # A. Parse out any nans, nones or other not-data type entries
        for k, v in raw_info.items():
            info[k] = StringManager.parse_none(raw_info[k])

        keys = info.keys()

        # Merge information, warn user about overwriting
        overwrite_keys = [k for k in keys if k in self.extra_header.keys()]

        if overwrite_keys:
            LOG.warning('Extra header information passed will overwrite '
                             'the following information found in the file '
                             'header:\n{}'.format(', '.join(overwrite_keys)))

        info.update(self.extra_header)

        # Convert slope, aspect, and zone to numbers
        info = self.manage_degrees(info)
        info = self.manage_aspect(info)
        info = self.manage_utm_zone(info)

        # Convert lat/long to utm and vice versa if either exist
        original_zone = info['utm_zone']
        info = self.reproject_point_in_dict(
            info, is_northern=self.northern_hemisphere)

        if info['utm_zone'] != original_zone and original_zone is not None:
            LOG.warning(f'Overwriting UTM zone in the header from {original_zone} to {info["utm_zone"]}')

        self.epsg = info['epsg']

        # Check for point data which will contain this in the data not the
        # header
        if not self.is_point_data(self.columns):
            if self.epsg is None:
                raise RuntimeError("EPSG was not determined from the header nor was it "
                                   "passed as a kwarg to uploader. If there is no "
                                   "projection information in the file please "
                                   "prescribe an epsg value")

            # info = self.add_geom(info, self.epsg)

        # If columns or info does not have coordinates raise an error
        important = ['northing', 'latitude']

        cols_have_coords = []
        if self.columns is not None:
            cols_have_coords = [c for c in self.columns if c in important]

        hdr_has_coords = [c for c in info if c in important]

        if not cols_have_coords and not hdr_has_coords:
            raise (ValueError('No geographic information was provided in the'
                              ' file header or via keyword arguments.'))
        return info
