"""
Profile data structures
"""
import logging
from pathlib import Path
import geopandas as gpd
from typing import List

import numpy as np
import pandas as pd

from insitupy.io.readers import CSV_reader # excel_reader, camml_reader
from insitupy.core.metadata import ProfileMetaData
from insitupy.core.variables import ProfileVariables, MeasurementDescription, \
    SnowExProfileVariables


LOG = logging.getLogger(__name__)


class ProfileData:
    """
    This would be one pit, SMP profile, etc
    Unique date, location, variable
    """
    VARIABLES = ProfileVariables
    # META_PARSER = MetaDataParser
    # add more here as we get them.
    READERS = {'.csv': CSV_reader}

    def __init__(
        self, input_df, metadata: ProfileMetaData, variable: MeasurementDescription,
    ):
        """
        Take df of layered data (SMP, pit, etc)
        Args:
            input_df: dataframe of data
                Should include depth and optional bottom depth
                Should include sample or sample_a, sample_b, etc

        """
        self._depth_layer = self.VARIABLES.DEPTH
        self._lower_depth_layer = self.VARIABLES.BOTTOM_DEPTH
        self._metadata = metadata
        # TODO: auto parse variable if not given
        self.variable: MeasurementDescription = variable
        # mapping of column name to measurement type
        self._column_mappings = {}
        # List of measurements to keep
        self._measurements_to_keep = [
            self._depth_layer, self._lower_depth_layer, self.variable
        ]

        self._id = metadata.id
        self._dt = metadata.date_time

        # This will populate the column mapping
        self._df = self._format_df(input_df)

        columns = self._df.columns.values
        if self._depth_layer.code not in columns:
            raise ValueError(f"Expected {self._depth_layer} in columns")

        # List of columns that are not the desired variable
        _non_measure_columns = [
            self._depth_layer.code, self._lower_depth_layer.code,
            "datetime",
            "geometry"
        ]
        self._non_measure_columns = [
            c for c in _non_measure_columns if c in columns
        ]

        # Columns related to the variable
        self._sample_columns = [
            c for c in columns if self._column_mappings.get(c) == self.variable
        ]
        if len(self._sample_columns) == 0:
            raise ValueError(f"Requested sample column {self.variable} not found in {columns}")

        # describe the data a bit
        self._has_layers = self._lower_depth_layer.code in columns
        # More than 1 sample of the variable (sample_1, sample_2)...
        self._multi_sample = len(self._sample_columns) > 1
        # Extend the df info
        self._extend_df()
    
    @classmethod
    def from_file(cls, fname, variable: MeasurementDescription, timezone = None):
        # # TODO: timezone here (mapped from site?)
        
        # identify correct reader to use
        reader = cls.READERS[Path(fname).suffix] or None
        if not reader: raise RuntimeError(f"No reader could be identified for file: {fname}")

        # parse out metadata and inut dataframe
        reader_obj = reader(fname, timezone)


        profile = cls(reader_obj.df, reader_obj.metadata, variable)

        return profile

        # meta_parser = cls.META_PARSER(fname, "US/Mountain")
        # # Parse the metadata and column info
        # metadata, columns, header_pos = meta_parser.parse()
        # # read in the actual data
        # data = cls._read(fname, columns, header_pos)

        # return cls(data, metadata, variable)

    def _format_df(self, input_df):
        """
        Format the incoming df with the column headers and other info we want
        """

        # Get rid of columns we don't want and populate column mapping
        columns = input_df.columns.values
        for c in columns:
            cn, cm = self.VARIABLES.from_mapping(c)
            # join with existing mappings
            self._column_mappings = {**cm, **self._column_mappings}

        columns_to_keep = [
            c for c in columns
            if self._column_mappings[c] in self._measurements_to_keep
        ]
        df = input_df.loc[:, columns_to_keep]

        n_entries = len(df)
        df["datetime"] = [self._dt] * n_entries

        # parse the location
        lat, lon = self.latlon
        location = gpd.points_from_xy(
            [lon] * n_entries, [lat] * n_entries
        )

        df = gpd.GeoDataFrame(
            df, geometry=location
        ).set_crs("EPSG:4326")
        df = df.replace(-9999, np.nan)

        return df

    def _extend_df(self):
        # set the thickness of the layer
        if self._has_layers:
            self._df[self.VARIABLES.LAYER_THICKNESS.code] = (
                self._df[self._depth_layer.code] - self._df[
                    self._lower_depth_layer.code
                ]
            )

    @property
    def latlon(self):
        # return location metadata
        return self._metadata.latitude, self._metadata.longitude

    @property
    def df(self):
        return self._df

    @property
    def sum(self):
        # get bulk value
        if not self._has_layers:
            # could we assume equidistant spacing and do a mean?
            raise RuntimeError("Cannot compute for no layers")

        # this should work for multi or not multi sample
        profile_average = self._df.loc[:, self._sample_columns].mean(axis=1)
        self._df["mean"] = profile_average
        # TODO: sum up with depth change
        # TODO: could we use the weighted mean * the total depth?
        # TODO: units
        pass

    @property
    def mean(self):
        profile_average = self._df.loc[:, self._sample_columns].mean(
            axis=1)
        if pd.isna(profile_average).all():
            return np.nan
        if self._has_layers:
            # height weighted mean for these layers
            thickness = self._df[self.VARIABLES.LAYER_THICKNESS.code]
            # this works for a weighted mean, but is not assumed to be
            # the total thickness of the snowpack
            thickness_total = thickness.sum()
            weighted_mean = (
                profile_average * thickness / thickness_total
            ).sum()
            value = weighted_mean
        else:
            value = np.mean(profile_average)

        return value

    @property
    def total_depth(self):
        profile = self._df.loc[:, self._depth_layer.code].values
        return np.nanmax(profile)

    def get_profile(self, snow_datum="ground"):
        # TODO: snow datum is ground or snow
        # get profile of values
        profile_average = self._df.loc[:, self._sample_columns].mean(
            axis=1)
        df = self._df.copy()
        df[self.variable.code] = profile_average
        columns_of_interest = [*self._non_measure_columns, self.variable.code]
        return df.loc[:, columns_of_interest]