"""
Readers for various (CSV, excel, CAAMXL) data formats.
"""
from dataclasses import dataclass, field

from datetime import timedelta
import logging

import pandas as pd
import pytz
import utm

from insitupy.util.strings import StringManager
from insitupy.core.variables import ProfileVariables
from insitupy.core.metadata import ProfileMetaData

LOG = logging.getLogger(__name__)

class MetaDataParser:
    """
    Base class for parsing metadata
    """
    OUT_TIMEZONE = "UTC"
    ID_NAMES = ["pitid", "pit_id"]
    SITE_ID_NAMES = ["site"]
    SITE_NAME_NAMES = ["location"]
    LAT_NAMES = ["lat", "latitude"]
    LON_NAMES = ["lon", "lon", "longitude", "long"]
    UTM_EPSG_PREFIX = "269"
    # if adding units they should start with least complex to most complex
    UNITS = [ "m", "cm", "mm","km", "kg", "kg/m3", "%", "deg C", "deg F", "g/cm"]
    NORTHERN_HEMISPHERE = True
    VARIABLES_CLASS = ProfileVariables

    def __init__(
        self, fname, timezone = None, header_sep=",", allow_split_lines=False
    ):
        """
        Args:
            fname: path to file
            timezone: string timezone
            header_sep: expected header separator
            allow_split_lines: Allow for split header lines that
                don't start with the expected header character. In this case
                the number of header lines will be the max line starting with
                the expected character, and lines that don't start with
                that character will be combined with the previous line
        """
        self._fname = fname

        #TODO set up automated time zone based on location
        self._input_timezone = timezone
        self._header_sep = header_sep
        self._rough_obj = {}
        self._lat_lon_easting_northing = None
        self._units = None

        self._allow_split_header_lines = allow_split_lines

    @property
    def rough_obj(self):
        return self._rough_obj

    @property
    def units(self):
        if self._units is None:
            self._units = self._parse_units()
        return self._units

    @property
    def lat_lon_easting_northing(self):
        if self._lat_lon_easting_northing is None:
            self._lat_lon_easting_northing = self._parse_location()
        return self._lat_lon_easting_northing

    def parse_id(self) -> str:
        for k, v in self.rough_obj.items():
            if k in self.ID_NAMES:
                return v

        raise RuntimeError(f"Failed to parse ID from {self.rough_obj}")
    
    def parse(self):
        """
        Parse the file and return a metadata object.
        We can override these methods as needed to parse the different
        metadata

        This populates self.rough_obj

        Returns:
            (metadata object, column list, position of header in file)
        """
        meta_lines, columns = self.find_header_info()
        self._rough_obj = self._preparse_meta(meta_lines)
        
        LOG.debug(
            f'Discovered the following metadata entries: {self.rough_obj}'
        )
        
        # Create a standard metadata object
        metadata = ProfileMetaData(
            id=self.parse_id(),
            date_time=self.parse_date_time(),
            latitude=self.parse_latitude(),
            longitude=self.parse_longitude(),
            utm_epsg=self.parse_utm_epsg(),
            site_id=self.parse_site_id(),
            site_name=self.parse_site_name(),
            units = self.parse_units(),
            flags=self.parse_flags(),
        )

        return metadata, columns
    
    def _handle_separate_datetime(self, keys, out_tz):
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
            if len(self.rough_obj['date']) == 6:
                dt = self.rough_obj['date']
                # Put into YY-MM-DD
                self.rough_obj['date'] = f'20{dt[-2:]}-{dt[0:2]}-{dt[2:4]}'
                # Allow for nan time
                self.rough_obj['time'] = StringManager.parse_none(
                    self.rough_obj['time']
                )

            date_str = self.rough_obj["date"]
            if self.rough_obj["time"] is not None:
                date_str += f" {self.rough_obj['time']}"
            d = pd.to_datetime(date_str)

        elif 'date' in keys:
            d = pd.to_datetime(self.rough_obj['date'])

        # Handle gpr data dates
        elif 'utcyear' in keys and 'utcdoy' in keys and 'utctod' in keys:
            base = pd.to_datetime(
                '{:d}-01-01 00:00:00 '.format(int(self.rough_obj['utcyear'])),
                utc=True)

            # Number of days since january 1
            d = int(self.rough_obj['utcdoy']) - 1

            # Zulu time (time without colons)
            time = str(self.rough_obj['utctod'])
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
                f'Data is missing date/time info!\n{self.rough_obj}'
            )
        return d

    def parse_date_time(self) -> pd.Timestamp:
        keys = [k.lower() for k in self.rough_obj.keys()]
        d = None
        out_tz = pytz.timezone(self.OUT_TIMEZONE)
        # Convert timezones if it is provided
        # this variable gets rewritten later
        in_timezone = self._input_timezone
        if in_timezone is not None:
            in_tz = pytz.timezone(in_timezone)
        # Otherwise assume incoming data is the same timezone
        else:
            raise ValueError("We did not recieve a valid in_timezone")

        # Look for a single header entry containing date and time.
        for k in keys:
            kl = k.lower()
            if 'date' in kl and 'time' in kl:
                str_date = str(self.rough_obj[k].replace('T', '-'))
                d = pd.to_datetime(str_date)
                break

        # If we didn't find date/time combined.
        if d is None:
            d = self._handle_separate_datetime(keys, out_tz)

        if in_timezone is not None:
            d = d.tz_localize(in_tz)
            d = d.astimezone(out_tz)

        else:
            d.replace(tzinfo=out_tz)

        self.rough_obj['date'] = d.date()

        # Don't add time to a time that was nan or none
        if 'time' not in self.rough_obj.keys():
            self.rough_obj['time'] = d.timetz()
        else:
            if self.rough_obj['time'] is not None:
                self.rough_obj['time'] = d.timetz()

        dt_str = self.rough_obj["date"].isoformat()
        if self.rough_obj.get("time"):
            dt_str += f"T{self.rough_obj['time'].isoformat()}"
        dt = pd.to_datetime(dt_str)

        return dt

    def _parse_location(self):
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
        lat = None
        lon = None
        easting = None
        northing = None
        for k, v in self.rough_obj.items():
            if k in self.LAT_NAMES:
                lat = float(v)
            elif k in self.LON_NAMES:
                lon = float(v)
            elif k == "easting":
                easting = float(v)
            elif k == "northing":
                northing = float(v)

        # Do nothing first
        if lat and lon and easting and northing:
            LOG.info("All location info is in the file")
        elif lat and lon:
            # do we want to do this?
            # zone_number = self.parse_utm_epsg()[-2:]
            # LOG.debug("Calculating the easting and northing")
            # easting, northing, *_ = utm.from_latlon(
            #     lat, lon, force_zone_number=int(zone_number)
            # )
            pass
        elif easting and northing:
            zone_number = self.parse_utm_epsg()[-2:]
            LOG.debug(f"Found utm zone number: {zone_number}")
            lat, lon = utm.to_latlon(
                easting, northing, int(zone_number),
                northern=self.NORTHERN_HEMISPHERE)
        else:
            raise ValueError(
                f"Could not parse location from {self.rough_obj}"
            )
        return lat, lon, easting, northing

    def parse_latitude(self) -> float:
        return self.lat_lon_easting_northing[0]

    def parse_longitude(self) -> float:
        return self.lat_lon_easting_northing[1]

    def parse_utm_epsg(self) -> str:
        info = self.rough_obj
        epsg = None
        if 'utm_zone' in info.keys():
            utm_zone = int(
                ''.join([c for c in info['utm_zone'] if c.isnumeric()]))
            epsg = int(f"{self.UTM_EPSG_PREFIX}{utm_zone}")
        elif 'epsg' in info.keys():
            epsg = info["epsg"]
        return epsg

    def parse_site_id(self) -> str:
        for k, v in self.rough_obj.items():
            if k in self.SITE_ID_NAMES:
                return v

        raise RuntimeError(f"Failed to parse Site ID from {self.rough_obj}")

    def parse_site_name(self) -> str:
        for k, v in self.rough_obj.items():
            if k in self.SITE_NAME_NAMES:
                return v

        raise RuntimeError(f"Failed to parse Site Name from {self.rough_obj}")

    def parse_flags(self):
        result = None
        for k, v in self.rough_obj.items():
            if k in ["flags"]:
                result = v
                break

        return result
    
    def read_lines(self, filename = None):
        """
        Read in from file

        Args:
            filename: Path to a csv file

        Returns:
            lines: list of all lines
        """

        filename = filename or self._fname
        filename = str(filename)

        with open(filename, encoding='latin') as fp:
            lines = fp.readlines()
        
        return lines

    def parse_utm_epsg(self):
        """
        Finds UTM zone from metadata. Either parses it directly or infers it from
        lat/long.

        Assumptions:
        1. If only 2 digits are given we are use self.UTM_EPSG_PREFIX

        Args:

        Returns:
            five digit utm zone
        """
        utm_zone = None

        if "utm_zone" in self.rough_obj:

            utm_zone = self.rough_obj["utm_zone"]
            # cut out N and S letters
            if isinstance(utm_zone, str): utm_zone = utm_zone.strip('N').strip('S')
            
            # add our set prefix if we are only given 2 numbers
            if len(utm_zone) > 2: utm_zone = utm_zone[-2:]
            
            assert len(utm_zone) == 2, f"Invalid utm zone: {utm_zone} found."

            return utm_zone
        
        elif self.rough_obj["latitude"] and self.rough_obj["longitude"]:
            
            # this is a 2 digit code
            utm_zone = utm.latlon_to_zone_number(self.rough_obj["latitude"], self.rough_obj["longitude"])
            
            return utm_zone
        
        else:

            raise RuntimeError(f"Unable to parse UTM EPGS from {self.rough_obj}")

class CSVMetaDataParser(MetaDataParser):
    """
    Metadata parser from CSV files
    """

    def __init__(self, fname, timezone = None):
        self._header_indicator = None
        self._header_pos = None

        MetaDataParser.__init__(self, fname = fname, timezone = timezone)
        self.lines = self.read_lines()

    @property
    def header_indicator(self):
        if self._header_indicator is None:
            self._header_indicator = self._find_header_position()[1]
        return self._header_indicator
    
    @property
    def header_pos(self):
        if self._header_pos is None:
            self._header_pos = self._find_header_position()[0]
        return self._header_pos

    def _find_header_position(self):
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

        lines = self.lines
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

            # if i > header_pos:
            #     break
        return header_pos

    def find_header_info(self):
        """
        Read in all site details file for a pit If the filename has the word
        site in it then we read everything in the file. Otherwise, we use this
        to read all the site data up to the header of the profile.

        E.g. Read all commented data until we see a column descriptor.

        Args:
            None

        Returns:
            tuple: **data** - Dictionary containing site details
                    **columns** - List of clean column names
                    **header_pos** - Index of the columns header for skiprows in
                                    read_csv
        """

        # Site description files have no need for column lists
        if 'sitedetails' in str(self._fname).lower():
            LOG.info('Parsing site description header...')
            columns = None
            header_pos = None
            header_indicator = '#'
            header = self.lines

        # Find the column names and where it is in the file
        else:
            header_pos, header_indicator = self._find_header_position()

            columns = self._parse_columns(self.lines[header_pos])
            LOG.debug(
                f'Column Data found to be {len(columns)} columns based on'
                f' Line {header_pos}'
            )
            # Only parse what we know if the header
            header = self.lines[0:header_pos]

        # Clean up the lines from line returns to grab header info
        header = [ln.strip() for ln in header]
        # Join all data and split on header separator
        # This handles combining split lines
        header = " ".join(header).split(header_indicator)
        header = [ln.strip() for ln in header if ln]

        return header, columns
    
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
        for c in ['()', '[]']:
            str_line = StringManager.strip_encapsulated(str_line, c)

        raw_cols = str_line.strip('#').split(',')
        standard_cols = [StringManager.standardize_key(c) for c in raw_cols]
        final_cols = []
        for c in standard_cols:
            mapped_col, col_map = self.VARIABLES_CLASS.from_mapping(c)
            final_cols.append(mapped_col)

        return final_cols

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

            # Assign non empty strings to dictionary
            if k and value:
                data[k] = value.strip(
                    ' '
                ).replace('"', '').replace('  ', ' ')

            elif k and not value:
                data[k] = None
        return data
    
    def parse_units(self):
        """
        Parse out unit information from columns

        Args:

        Returns:
        dict: units: a dictionary of column name and units
        """

        _units = {}

        if not self._fname:
            raise RuntimeError("No file found to parse units from.")
        
        # site detail CSV doesn't have units
        if 'siteDetails_' in self._fname.name:
            return _units

        header_pos, header_indicator = self._find_header_position()

        raw_cols = self.lines[header_pos].strip('#').split(',')
        clean_cols = self._parse_columns(self.lines[header_pos])
        for clean, raw in zip(clean_cols, raw_cols):
            # gets tripped up on the mm in comments
            if 'comment' in clean: continue

            for unit_name in self.UNITS:
                if unit_name in raw:
                    _units[clean] = unit_name
        

        return _units

class DataParser:

    def __init__(self, filename):
        self._fname = filename
        self._df = None
    
    @property
    def df(self):
        if self._df is None:
            self._df = self.get_df()
        return self._df

    def get_df(self):
        raise NotImplementedError

    @staticmethod
    def _clean_df(df):
        """
        # TODO: better name mapping here
        Read in a profile file. Managing the number of lines to skip and
        adjusting column names

        Args:
            profile_filename: Filename containing the a manually measured
                             profile
        Returns:
            df: pd.dataframe contain csv data with standardized column names
        """
        # header=0 because docs say to if using skip rows and columns

        # TODO if there is a multiline comment in header this will cut off
        # the first line of data... See failing test for 
        # SNEX21_TS_SP_20210527_1145_COCPMR_data_LWC_v01 in test_profile_data.test_mean
        LOG.debug(f"Initial dataframe: {df}")
        # Special SMP specific tasks
        depth_fmt = 'snow_height'
        is_smp = False
        if 'force' in df.columns:
            # Convert depth from mm to cm
            df['depth'] = df['depth'].div(10)
            is_smp = True
            # Make the data negative from snow surface
            depth_fmt = 'surface_datum'

            # SMP serial number and original filename for provenance to the comment
            f = Path(profile_filename).name
            serial_no = f.split('SMP_')[-1][1:3]

            df['comments'] = f"fname = {f}, " \
                             f"serial no. = {serial_no}"

        if not df.empty:
            # Standardize all depth data
            new_depth = standardize_depth(
                df['depth'], desired_format=depth_fmt, is_smp=is_smp
            )

            if 'bottom_depth' in df.columns:
                delta = df['depth'] - new_depth
                df['bottom_depth'] = df['bottom_depth'] - delta

            df['depth'] = new_depth

            delta = abs(df['depth'].max() - df['depth'].min())
            LOG.debug(
                f'File contains a profile with'
                f' with {len(df)} layers across {delta:0.2f} cm'
            )
        return df

class CSVDataParser(DataParser):

    def __init__(self, profile_filename, metadata, columns):
        DataParser.__init__(self, profile_filename)

        raw_df = self.get_df(metadata.header_indicator, metadata.header_pos, columns)

        self._df = self._clean_df(raw_df)
    
    def get_df(self, header_indicator, header_pos, columns):
        df = pd.read_csv(
            self._fname, header=0,
            skiprows=header_pos,
            names=columns,
            encoding='latin'
        )

        return df
        
def standardize_depth(depths, desired_format='snow_height', is_smp=False):
    """
    Data that is a function of depth comes in 2 formats. Sometimes 0 is
    the snow surface, sometimes 0 is the ground. This function standardizes it
    for each profile. desired_format can be:

        snow_height: Zero at the bottom of the data.
        surface_datum: Zero at the top of the data and uses negative depths
                       (easier for plotting)

    Args:
        depths: Pandas series of depths in either format
        desired_format: string indicating which format the data is in
        is_smp: Boolean indicating which data this is, if smp then the data is
                surface_datum but with positive depths
   Returns:
        new:
    """
    max_depth = depths.max()
    min_depth = depths.min()

    new = depths.copy()

    # How is the depth ordered
    # max_depth_at_top = depths.iloc[0] > depths.iloc[-1]

    # Is the data in surface_datum already
    bottom_is_negative = depths.iloc[-1] < 0

    if desired_format == 'snow_height':

        if is_smp:
            LOG.info('Converting SMP depths to snow height format.')
            new = (depths - max_depth).abs()

        elif bottom_is_negative:
            LOG.info('Converting depths in surface datum to snow height format.')

            new = (depths + abs(min_depth))

    elif desired_format == 'surface_datum':
        if is_smp:
            LOG.info('Converting SMP depths to surface datum format.')
            new = depths.mul(-1)

        elif not bottom_is_negative:
            LOG.info('Converting depths in snow height to surface datum format.')
            new = depths - max_depth

    else:
        raise ValueError(
            f'{desired_format} is an invalid depth format! Options are:'
            f' {["snow_height", "surface_datum"]}'
        )

    return new

class reader:
    @property
    def df(self):
        return self._df
    
    @property
    def metadata(self):
        return self._metadata

class CSV_reader(reader):
    """
    Reader for CSV files that combines a  metadata and data
    """

    def __init__(self, filepath, timezone = None):
        # first read in metadata and column names
        obj = CSVMetaDataParser(filepath, timezone)
        metadata, columns = obj.parse()

        # next read in csv data
        data = CSVDataParser(filepath, obj, columns)
    
        self._metadata = metadata
        self._df = data.df


