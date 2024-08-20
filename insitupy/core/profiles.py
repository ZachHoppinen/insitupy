"""
SnowDataset Class an extension of xarray's dataset with addition snow features.
"""

import logging

from collections.abc import Iterable

import numpy as np
import pandas as pd
import xarray as xr

LOG = logging.getLogger(__name__)

class SnowProfile(xr.Dataset):

    def __init__(self, ds = False, data_vars = False, coords = False, attrs = {}, clean = True):
        
        if not isinstance(ds, xr.Dataset):
            assert isinstance(data_vars, Iterable), f'data_vars ({data_vars}) not an iterable instead of type {type(data_vars)}'
            assert isinstance(coords, Iterable), f'Coords ({coords}) not an iterable instead of type {type(coords)}'
        if ds:
            data_vars = ds.data_vars
            coords = ds.coords
            attrs = ds.attrs
        super().__init__(data_vars = data_vars, coords = coords, attrs = attrs)

        if clean:
            self = self.clean_profile()
    
    def clean_profile(self):

        self = self.profile_to_z_meters(self)
        self = self.clean_profile(self)
        self = self.clean_vars(self)

        return self

    def profile_to_z_meters(self):

        current_units = self.z.attrs['units']
        
        if not current_units: raise RuntimeError(f"Unable to convert units to meters based on .z.attrs['units'] of\
            {self}")
        
        if current_units == 'mm': self['z'] = self.z / 1000
        elif current_units == 'cm': self['z'] = self.z / 100
        elif current_units == 'm': LOG.info(f"Z dimension already in meters")
        else: raise ValueError(f"Unable to convert {current_units} to meters.")

        self.z.attrs['units'] = 'm'

        return self

    def clean_profile(self):

        NANVALUES = [-9999, '', 'nan']

        for nanval in NANVALUES:
            self = self.where(self != nanval)
        
        # remove massive negative or positive values
        for var in self.data_vars:
            if self[var].dtype == object: continue

            self[var] = self[var].where(self[var] > -1e29)
            self[var] = self[var].where(self[var] < 1e29)
        return self


    def clean_vars(self):
        for var in self.data_vars:
            if self[var].count() == 0:
                self = self.drop_vars(var)
        
        return self

    