"""
Reader classes to parse CSV, excel, CAAML files and return:
    data as numpy array
    x, y, time coordinates for array location (optional id coordinate)
    other metadata as a dictionary to save in .attrs
"""

from pathlib import Path
import string
import logging

import numpy as np
import pandas as pd
import xarray as xr

from snowcore.util.strings import StringManager
from snowcore.core.profiles import SnowProfile

LOG = logging.getLogger(__name__)

class Reader:

    # list of acceptable extensions to check for
    EXTENSIONS = [".csv", ".xls"]
    ID_NAMES = ["pitid", "pit_id"]
    Y_NAMES = ["lat", "latitude", 'y', 'northing']
    X_NAMES = ["lon", "lon", "longitude", "long", "x", 'easting']
    TOP_NAMES = ["depth", "top", "sample_top_height", "hs", \
        "depth_m", 'snowdepthfilter(m)', 'snowdepthfilter', "height"]
    BOTTOM_NAMES = ["bottom", "bottom_depth"]

    def __init__(self, filepath):

        # type and existence checking for all passed file paths
        if isinstance(filepath, Path): pass
        elif isinstance(filepath, str): filepath = Path(filepath)
        else: raise ValueError(f'Provided filepath {filepath} is not a recognized type.')

        filepath = filepath.absolute().expanduser().resolve()

        assert filepath.exists(), f"Provided filepath {filepath} does not exist."

        assert filepath.suffix in self.EXTENSIONS, f'Filepath {filepath} does not contain recognized extension of options {EXTENSIONS}.'

        LOG.info(f"Parsing filepath {filepath}")
        self._filepath = filepath
    
    @property
    def filepath(self):
        return self._filepath
    
    @property
    def columns(self):
        return self._columns
    
    @property
    def metadata(self):
        return self._metadata
    
    @property
    def units(self):
        return self._units
    
    @property
    def lines(self):
        return self._lines
    
    @property
    def data(self):
        return self._data

    def read_lines(self, filepath  = None):
        """
        Read in from file

        Args:
            filename: Path to a csv file

        Returns:
            lines: list of all lines
        """

        filepath = filepath or self._filepath

        encodings = ['latin', 'utf-8','utf-8-sig']
        for encoding in encodings:
            # check if we got the correct encoding
            with open(filepath, encoding=encoding) as fp:
                lines = fp.readlines()
            
            if all([c in string.printable for c in ''.join(lines)]): 
                LOG.info(f"Read lines with encoding {encoding}")
                break
        
        LOG.debug(f"Found lines in {filepath} {lines}")
        
        return lines
    
    def _clean_metadata(self):

        assert isinstance(self.metadata, dict), f"Found metadata: {self.metadata} of wrong type {type(self.metadata)}. Need dictionary."

        metadata = {}

        for k, v in self.metadata.items():
            try:
                metadata[k] = float(v)
                continue
            except ValueError: pass
            
            try:
                metadata[k] = int(v)
                continue
            except ValueError: pass

            metadata[k] = v
        
        return metadata

    def create_snowpit(self):
        """
        Generates a snowpit xarray object from data and metadata
        """

        assert(len(self.data) > 0), f'No data found to create snowpit from for file {self.filepath}.'

        coords = self._parse_coords(self.metadata)
        coords = {k:[v] for k, v in coords.items()}

        # identify layers
        top_cols = [c for c in self.data.columns if c.lower() in self.TOP_NAMES]
        bottom_cols = [c for c in self.data.columns if c.lower() in self.BOTTOM_NAMES]

        assert len(top_cols) == 1, f'Unable to parse top column for {self.filepath} out of columns: {self.data.columns}'

        assert len(bottom_cols) < 2, f'Too many colummns parsed for bottom column for {self.filepath} out of columns: {self.data.columns}'

        top = top_cols[0]

        print(self.data)
        if len(bottom_cols) == 1:
            bottom = self.data[bottom_cols[0]]
            self._data = self.data.drop(bottom_cols[0], axis = 1) 
        else:
            bottom = self.data[top]
            
        # rename whatever our top column is called to z and make it an index
        snowprofile = SnowProfile(self.data.rename({top: 'z'}, axis = 1).set_index('z'),
                    # set coords for x, y, time, z
                    coords = coords).assign_coords(bottom = ('z', bottom))        

        return snowprofile


    def _parse_coords(self, metadata):
        """
        Parses a metadata dictionary and returns values neccesary for creating xarray
        coordinates [x, y, time, and an optional id].

        If only UTM is found will use that but preference for lat, long.
        """

        # parse location (x, y, id) first        
        coords = self._parse_location(metadata)
        
        # next parse time
        coords['time'] = self._parse_time(metadata)
        
        return coords
    
    def _parse_location(self, metadata):
        """
        Parse the x and y from the metadata dictionary

        returns diction of {x: x_value, y: y_value, id: id_value}
        """
        coords = {'x': [], 'y': [], 'id': []}

        for coord_name, NAMES in zip(coords, [self.X_NAMES, self.Y_NAMES, self.ID_NAMES]):

            possible_coords = [k for k in metadata if k.lower() in NAMES]

            assert possible_coords, f"No {coord_name} value found in metadata \
                {metadata} searching with list {NAMES}"
            
            if len(possible_coords) > 1:
                if coord_name == 'x':
                    possible_coords = [c for c in possible_coords if 'lon' in c.lower()]
                if coord_name == 'y':
                    possible_coords = [c for c in possible_coords if 'lat' in c.lower()]                
            
            assert len(possible_coords) == 1, f"More than 1 {coord_name} value found in metadata \
                {metadata} searching with list {NAMES}"
            
            coords[coord_name] = metadata[possible_coords[0]]

        return coords
    
    def _parse_time(self, metadata):
        
        str_dt, str_date, str_time = [None, None, None]

        for k, v in metadata.items():
            kl = k.lower()
            # check if both in k
            if 'date' in kl and 'time' in kl:
                str_dt = metadata[k]
                
            elif 'date' in kl:
                str_date = metadata[k]
            
            elif 'time' in kl:
                str_time = metadata[k]
            
            else: pass

        assert str_date or str_dt, f'Unable to parse date from metadata {metadata}'

        try:
            if str_dt: return pd.to_datetime(str_dt)
        except ValueError as ve:
            raise ValueError(f"Error {ve} trying to convert timestamp for metadata: {metadata}")

        # add trailing :00 to make HH:MM:SS format
        time_list = str_time.split(':')
        if len(time_list) == 2: str_time = ':'.join(time_list + ['00'])
        else: str_time = ':'.join(time_list)

        return pd.to_datetime(str_date) + pd.Timedelta(str_time)

    # def clean_data(self):
        

class CSVReader(Reader):

    SYMBOLS = string.printable[62:94]
    # if adding units they should start with least complex to most complex
    UNITS = [ "m", "cm", "mm","km", "kg", "kg/m3", "%", "deg C", "deg F", "g/cm"]

    def __init__(self, filepath, header_symbol: str = None, header_sep: str = None):

        Reader.__init__(self, filepath)
        lines = self.read_lines()
        self._lines = lines

        self._header_marker = header_symbol
        self._header_sep = header_sep

        self.parse()
    
    def parse(self):

        self._header = self._parse_header()

        self._columns, self._units = self._parse_columns()
        LOG.debug(f"Found columns {self._columns}")

        # check to be sure no duplicate columns
        assert len(self.columns) == len(set(self.columns)), f"Found duplicate columns in {self.columns}"

        self._data = pd.read_csv(self._filepath, comment = self._header_marker, names = self.columns)
        # self._clean_data()

        LOG.debug(f"Found {len(self.data)} rows of data and {len(self.data.columns)} columns.")

        self._metadata = self._parse_metadata()
        self._metadata = self._clean_metadata()

    @property
    def header_marker(self):
        if not self._header_marker:
            self._header_marker = self._parse_header_symbol()
        return self._header_marker
    
    @property
    def header_sep(self):
        if not self._header_sep:
            self._header_sep = self._parse_header_sep()
        return self._header_sep
    
    @property
    def header(self):
        if not self._header:
            self._header = self._parse_header()
        return self._header

    def _parse_header_symbol(self):

        assert len(self.lines) > 0, f'Did not find any lines in files {filepath}'

        if self.lines[0][0] in self.SYMBOLS:
            LOG.debug(f"Found header symbol {self.lines[0][0]}")
            return self._lines[0][0]
        
        else:
            raise ValueError(f"Did not find any header information in {self._filepath}")
    
    def _parse_header_sep(self):

        assert len(self.lines) > 0, f'Did not find any lines in files {filepath}'

        # search through possible symbols and find most comment character to identify seperator
        symbol_count = {}
        for symbol in self.SYMBOLS:
            if symbol == self.header_marker: continue
            
            symbol_count[symbol] = ''.join(self.header).count(symbol)
        header_sep = max(symbol_count, key=symbol_count.get)

        LOG.debug(f"Found header seperator: {header_sep}")

        return header_sep

    def _parse_columns(self):
        """
        Parse last line of header for column names and unit information.
        """

        # first strip header comment symbol and split on seperator
        dirty_columns = self.header[-1].split(self.header_sep)
        
        # next clean strings of undesirable characters
        clean_columns = [StringManager.clean_str(c) for c in dirty_columns]

        # next seperate units and save for later
        _units = {}
        _clean_cols = []
        for col in clean_columns:
            str_line = col.strip(self._header_marker)
            # Remove units
            col_nounits = str_line
            for c in ['()', '[]']:
                col_nounits = StringManager.strip_encapsulated(col_nounits, c)
            col_nounits = StringManager.standardize_key(col_nounits)
            _clean_cols.append(col_nounits)
            
            # Get units
            for c in ['()', '[]']:
                col_units = StringManager.get_encapsulated(str_line, c)
                if len(col_units) > 0: 
                    _units[col_nounits] = col_units
                    break

                # if last symbol and we haven't hit the above condition add
                # in an empty unit value
                if c == '[]': _units[col_nounits] = '[]'

        LOG.debug(f"Found columns {_clean_cols}")
        LOG.debug(f"Found units {_units}")
    
        return _clean_cols, _units

    def _parse_header(self):
        
        # parse header into dictionary of clean values
        header = [StringManager.clean_str(l.strip(self.header_marker)) for l in self.lines if l[0] == self.header_marker]

        return header

    def _parse_metadata(self):

        metadata = self.header[:-1]

        metadata = {l[0]:l[1] for l in [l.split(',') for l in metadata] if len(l) == 2}

        return metadata


def from_file(filepath):
    READERS = {'.csv': CSVReader}

    # does same basic filepath checking and conversion for us
    reader = Reader(filepath)

    # select correct reader
    reader = READERS[reader.filepath.suffix]

    # parse out data and metadata
    reader = reader(filepath)
    reader.parse()

    snowpit = reader.create_snowpit()

    return snowpit