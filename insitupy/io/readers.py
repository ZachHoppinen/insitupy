"""
Reader classes to parse CSV, excel, CAAML files and return:
    data as numpy array
    x, y, time coordinates for array location (optional id coordinate)
    other metadata as a dictionary to save in .attrs
"""

from pathlib import Path
import string
import logging
import shutil
import ast
from datetime import datetime

import random
from types import NoneType

import numpy as np
import pandas as pd
import xarray as xr

from pandas import NaT
from pandas._libs.tslibs.nattype import NaTType
from pandas.errors import EmptyDataError
from pandas._libs.tslibs.parsing import DateParseError

from insitupy.util.strings import StringManager
from insitupy.core.profiles import SnowProfile

LOG = logging.getLogger(__name__)

class Reader:

    # list of acceptable extensions to check for
    EXTENSIONS = [".csv", ".xls", ".nc"]
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

        assert filepath.suffix in self.EXTENSIONS, f'Filepath {filepath} does not contain recognized extension of options {self.EXTENSIONS}.'

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
                LOG.debug(f"Read lines with encoding {encoding}")
                break
        
        LOG.debug(f"Found lines in {filepath} {lines}")
        
        return lines
    
    def _clean_metadata(self):

        assert isinstance(self.metadata, dict), f"Found metadata: {self.metadata} of wrong type {type(self.metadata)}. Need dictionary."

        metadata = {}

        for k, v in self.metadata.items():
            kl = StringManager.clean_str(k)
            try:
                metadata[kl] = float(v)
                continue
            except ValueError: pass
            
            try:
                metadata[kl] = int(v)
                continue
            except ValueError: pass

            try:
                dt = pd.to_datetime(v)
                if pd.isnull(dt): raise ValueError
                metadata[kl] = dt
                continue
            except ValueError: pass

            if v == "":
                metadata[kl] = None
                continue

            metadata[kl] = v
        
        return metadata

    def create_snowprofile(self):
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

        # check if there is a bottom column or just assign top column to be depth
        if len(bottom_cols) == 1:
            bottom_col = bottom_cols[0]
            bottom = self.data[bottom_cols[0]]
            self._data = self.data.drop(bottom_cols[0], axis = 1) 
        else:
            bottom_col = top
            bottom = self.data[top]

        # rename whatever our top column is called to z and make it an index
        snowprofile = xr.Dataset(data_vars = self.data.rename({top: 'z'}, axis = 1).set_index('z'),
                    # set coords for x, y, time, z
                    coords = coords, attrs = self.metadata)#.assign_coords(bottom = ('z', bottom))
                    # last line adds a coordinate bottom that holds bottom values

        # get bottom information and add to attributions
        for var in snowprofile.data_vars:
            snowprofile.snow.samples[var] = bottom
            snowprofile[var].attrs['samples'] = bottom.set_axis(self.data[top])

        snowprofile.attrs['units'] = self.units

        # add in units to dimensions
        if top in self.units.keys():
            if top in self.units.keys():
                snowprofile.z.attrs['units'] = self.units[top][0]
            else:
                snowprofile.z.attrs['units'] = None
        
        # add in coord names used
        for coord_name in ['x','y','id']:
            if self.metadata[f'{coord_name}_coord_name'] in self.units:
                snowprofile[coord_name].attrs['units'] = self.units[self.metadata[f'{coord_name}_coord_name']]
                continue
            
            snowprofile[coord_name].attrs['units'] = ''
        
        # this might be giving us problems with .netcdf()
        # snowprofile['time'].attrs['units'] = ''

        # find long names and save for plitting
        for coord_name in ['x', 'y','id']:
            snowprofile[coord_name].attrs['long_name'] = self.metadata[f'{coord_name}_coord_name']
        snowprofile['z'].attrs['long_name'] = 'Snow Height'
        snowprofile['time'].attrs['long_name'] = 'Pit Time'

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

            possible_coords = [k for k in metadata if any([n in k.lower() for n in NAMES])]

            if coord_name == 'id' and not possible_coords:
                id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                LOG.info(f"No pit id found assigning a random id {id}")
                metadata['pitid'] = [id]
                possible_coords = 'pitid'


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

            self.metadata[f'{coord_name}_coord_name'] = possible_coords[0]

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

    def parse(self):

        raise NotImplementedError

class NETCDFReader(Reader):

    def __init__(self, filepath):
        Reader.__init__(self, filepath)

    def create_snowprofile(self):

        snowprofile = xr.open_dataset(self._filepath)

        snowprofile.attrs = self._decode_attrs(snowprofile.attrs)
        for v in snowprofile.data_vars: snowprofile[v].attrs = self._decode_attrs(snowprofile[v].attrs)

        return snowprofile

    def _decode_attrs(self, attrs):
        decoded_strs = {}
        for k, v in attrs.items():
            
            decoded = v
            if isinstance(v, str):  
                try:
                    decoded = eval(v)
                except (SyntaxError, NameError, EmptyDataError):    
                    pass
                try:
                    decoded = pd.to_datetime(v)
                    if np.isnat(decoded):
                        decoded = ""
                except (DateParseError, ValueError, TypeError):
                    pass
            if isinstance(decoded, NaTType):
                 decoded = ""
            
            decoded_strs[k] = decoded

        return decoded_strs

    def encode_attrs(attrs):
        """
        encode attributes as strings, arrays, or numbers for saving to netcdf
        """
        encoded_strs = {}
        for k, v in attrs.items():
            coded = v
            if isinstance(v, dict) or isinstance(v, list) or isinstance(v, complex):
                coded = str(v)
            if isinstance(v, pd.Series):
                coded = v.values
            if isinstance(v, pd.DataFrame):
                coded = v.values
            
            if isinstance(v, datetime):
                coded = str(v)
            
            if isinstance(coded, NoneType):
                coded = ''
            
            if not any(isinstance(coded, netcdftype) for netcdftype in [str, np.ndarray, int, float, complex, list, tuple]):
                print(coded)

            if isinstance(coded, str):
                coded = coded.strip('" "').replace('\\','_').replace('/','')

            encoded_strs[k.strip('" "').replace('\\','_').replace('/','')] = coded
        
        return encoded_strs





class CSVReader(Reader):

    SYMBOLS = string.printable[62:94]
    # if adding units they should start with least complex to most complex
    UNITS = [ "m", "cm", "mm","km", "kg", "kg/m3", "%", "deg C", "deg F", "g/cm"]

    def __init__(self, filepath, header_symbol: str = None, header_sep: str = None):

        LOG.info(f"Parsing filepath {filepath}")

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

        # read in data
        # if split lines read temporary file with comments fixed
        if self.split_lines:
            self._data = pd.read_csv(self._temp_filepath, comment = self._header_marker, names = self.columns)

            # clean up temporary file
            self._temp_filepath.unlink()
            LOG.debug(f'Deleting split line temorary file {self._temp_filepath}')

        else:
            self._data = pd.read_csv(self._filepath, comment = self._header_marker, names = self.columns)
        # self._clean_data()

        LOG.debug(f"Found {len(self.data)} rows of data and {len(self.data.columns)} columns.")

        self._metadata = self._parse_metadata()
        self._metadata = self._clean_metadata()
        # add metadata units
        self._units = self._parse_metadata_units()


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
    
    @property
    def split_lines(self):
        if not self._split_lines:
            self._parse_header()
        return self._split_lines

    def _parse_header_symbol(self):

        assert len(self.lines) > 0, f'Did not find any lines in files {self._filepath}'

        if self.lines[0][0] in self.SYMBOLS:
            LOG.debug(f"Found header symbol {self.lines[0][0]}")
            return self._lines[0][0]
        
        else:
            raise ValueError(f"Did not find any header information in {self._filepath}")
    
    def _parse_header_sep(self):

        assert len(self.lines) > 0, f'Did not find any lines in files {self._filepath}'

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
        """
        parsed header from read in lines
        """
        # first check for/fix split lines
        header_positions = [i for i, line in enumerate(self.lines) if line.startswith(self.header_marker)]
        max_header = max(header_positions)

        split_lines = []

        if not check_consecutive(header_positions):
            LOG.debug(f"Found split lines in {self.filepath}. Trying to parse.")
            fixed_header = []
            for i, line in enumerate(self.lines):
                if i in header_positions: fixed_header.append(line); continue

                if i > max_header:
                    break
                
                fixed_header[-1] = fixed_header[-1].strip('\n') + ' ' + line
                split_lines.append([line, fixed_header[-1].strip('\n') + ' ' + line])
            
            header = fixed_header

            LOG.debug(f"Found {len(split_lines)} split lines.")
            LOG.debug(f'Fixed lines: {[f"{l1} to {l2}" for l1, l2 in split_lines]}')
            self._split_lines = True

            # save out temporary file
            data_lines = self.lines[max_header + 1:]
            tmp_fp = Path('split_line_fix.csv')
            with open(tmp_fp, 'w') as fp:
                fp.writelines(header + data_lines)
            
            self._temp_filepath = tmp_fp

        else:
            header = [l for l in self.lines if l[0].startswith(self.header_marker)]
            self._split_lines = False

        # parse header into dictionary of clean values
        header = [StringManager.clean_str(l.strip(self.header_marker)) for l in header]

        return header

    def _parse_metadata(self):
        """
        parses metadata from header into dictionary
        """
        metadata = self.header[:-1]

        metadata = {l[0]:l[1] for l in [l.split(',') for l in metadata] if len(l) == 2}

        return metadata
    
    def _parse_metadata_units(self):
        _units = self.units

        for k, v in self.metadata.items():
            for encapsulator in ['[]','()']:
                encapsulated = StringManager.get_encapsulated(k, encapsulator)
                if len(encapsulated) == 1:
                    _units[k] = encapsulated
        return _units

def check_consecutive(l):
    """
    https://www.geeksforgeeks.org/python-check-if-list-contains-consecutive-numbers/#
    """
    return l == list(range(min(l), max(l)+1))

def from_file(filepath) -> xr.Dataset:
    f"""
    Reads in an appropriate file into a Insitupy SnowProfile object.

    Currently accepted readers are: {Reader.EXTENSIONS}.

    Args:
        Filepath: str or Path
    
    Return
        xarray dataset containing metadata in .attrs and data as variables.
    """
    READERS = {'.csv': CSVReader, '.nc': NETCDFReader}

    # does same basic filepath checking and conversion for us
    reader = Reader(filepath)

    # select correct reader
    reader = READERS[reader.filepath.suffix]

    # parse out data and metadata
    reader = reader(filepath)
    # reader.parse()

    snowprofile = reader.create_snowprofile()

    return snowprofile
