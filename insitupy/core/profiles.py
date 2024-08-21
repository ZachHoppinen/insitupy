"""
This module is an extension for xarray to provide snow specific capabilities
to xarray datasets.
"""

import logging

from collections.abc import Iterable
from typing import Union

from itertools import combinations

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

from insitupy.util.plotting import plot_profile

LOG = logging.getLogger(__name__)

# https://docs.xarray.dev/en/stable/internals/extending-xarray.html
@xr.register_dataset_accessor("snow")
class SnowProfile:

    def __init__(self, xarray_obj: Union[xr.DataArray, xr.Dataset], clean = True):
        self._obj: Union[xr.DataArray, xr.Dataset] = xarray_obj

        self._bottom = {}

        self._wet = False
        self._total_swe = False
    
    def _get_obj(self, inplace: bool = True) -> Union[xr.Dataset]:
        """
        Get the object to modify.

        Parameters
        ----------
        inplace: bool
            If True, returns self.

        Returns
        -------
        :obj:`xarray.Dataset` | :obj:`xarray.DataArray`
        """
        if inplace:
            return self._obj
        obj_copy = self._obj.copy(deep=True)
        # preserve attribute information
        return obj_copy

    @property
    def vars(self) -> list:
        """list: Returns non-coordinate varibles"""
        return list(self._obj.data_vars)
    
    @property 
    def bottom(self) -> list:
        if not self._bottom:
            self._bottom = {}
        return self._bottom
    
    @property 
    def total_swe(self):
        if not self._total_swe:
            self._total_swe = self._get_total_swe()
        return self._total_swe
    
    @property 
    def wet_dry(self):
        if not self._wet_dry:
            self._wet_dry = self._get_wet_dry()
        return self._wet_dry
    
    def _get_total_swe(self):

        raise NotImplementedError

        # either use average density, or average all available densities.

        density_vars = [v for v in self.vars if 'dens' in v]
        assert density_var, f'No density variables found in {self.vars}'

        if len(density_var) > 1:
            ave_den_vars = [d for d in density_var if 'avg' in d or 'ave' in d]

            if len(ave_den_vars) == 1:
                density_var = ave_den_vars

            
            a_den_vars = [d for d in density_var if '_a' in d or 'a_' in d]

            if len(a_den_vars) == 1:
                density_var = a_den_vars
            
        density_var = density_var[0]
        
        # next find heights of each layer

        # next multiply all together for total SWE.
        # self._obj[density_vars] = 

    def _get_wet_dry(self):

        # see if we have manual wetness, temperature, and/or LWC.

        raise NotImplementedError
    
    def clean_profile(self) -> xr.Dataset:
        """
        Cleans a profile by:
        1. masking known nan values
        2. droppping empty variables
        3. removing identical variables
        """

        
        ds = self.mask_nans()
        ds = ds.snow.drop_empty_vars()
        ds = ds.snow.drop_identical_vars()

        return ds

    def mask_nans(self) -> xr.Dataset:
        """
        Clean known nan values and outliers

        Using this: https://github.com/corteva/rioxarray/blob/25fbbce8612ba9a38786a67dc56d24c7d8f79db7/rioxarray/raster_dataset.py#L250
        as reference.
        """
        cleaned_dataset = xr.Dataset(coords = self._obj.coords, attrs=self._obj.attrs)

        NANVALUES = [-9999, '', 'nan', -9999.0, '-9999']

        i = False
        for nanval in NANVALUES:
            if not i:
                cleaned_dataset = self._obj.copy().where(self._obj != nanval)
                i = True
                continue
            cleaned_dataset = cleaned_dataset.where(cleaned_dataset != nanval)

        
        return cleaned_dataset

    def drop_empty_vars(self) -> xr.Dataset:
        """
        drop dataset variables with no data in any depth
        """

        cleaned_dataset = xr.Dataset(coords = self._obj.coords, attrs=self._obj.attrs)

        for var in self.vars:
            if self._obj[var].count() != 0:
                cleaned_dataset[var] = self._obj[var]
        
        return cleaned_dataset
    
    def drop_identical_vars(self) -> xr.Dataset:
        """
        drop variables with duplicate values. Usually a b and c profile that are
        identical.
        """

        cleaned_dataset = xr.Dataset(coords = self._obj.coords, attrs=self._obj.attrs)
        
        for var in sorted(self.vars):
            if var in cleaned_dataset.data_vars: continue
            drop = False

            for var2 in cleaned_dataset.data_vars:
                if (self._obj[var].dropna('z') == cleaned_dataset[var2].dropna('z')).all():
                    LOG.info(f"Dropping variable {var}.")
                    drop = True
                    break

            if not drop:
                cleaned_dataset[var] = self._obj[var]
        
        return cleaned_dataset
    
    def plot_profile(self) -> plt.Figure:
        """
        Custom plotting functionality for snowpits.
        Shows: density, temperature, stratigraphy, LWC, permittivity

        returns: Matplotlib Figure
        """
        # for var in self.var:
        #     self._obj[var].attrs['bottom'] = self.bottom[var]
        fig = plot_profile(self._obj)
        return fig

    

    # def profile_to_z_meters(self):

    #     ds = self.ds.copy()

    #     current_units = ds.z.attrs['units']
        
    #     if not current_units: raise RuntimeError(f"Unable to convert units to meters based on .z.attrs['units'] of\
    #         {ds}")
        
    #     if current_units == 'mm': ds['z'] = ds.z / 1000
    #     elif current_units == 'cm': ds['z'] = ds.z / 100
    #     elif current_units == 'm': LOG.info(f"Z dimension already in meters")
    #     else: raise ValueError(f"Unable to convert {current_units} to meters.")

    #     ds.z.attrs['units'] = 'm'
            