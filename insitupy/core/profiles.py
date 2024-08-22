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

        self._samples = {}

        self._wet = False
        self._total_swe = False
        self._snow_vars = {}

        # self._obj = self.clean_profile()
    
    def parse_snow_vars(self):
        """
        Find/identify variables and # iterations for standard measurements
        that are used in other snowprofile functionality:
        - density
        - temp
        - hand hardness
        - grain type/size
        - lwc

        returns:
            dictionary of known variables with inner dictionary of exists, iterations, and names
        """

        known_var_names = ['density','temp','hardness', 'grain_type','grain_size','lwc']

        for known_var in known_var_names:
            for var in [v.lower() for v in self.vars]:
                self._snow_vars[known_var] =  {'exists': self._is_variable(known_var), \
                'n_iterations': self._number_iterations(known_var), \
                'var_names': self._get_var_names(known_var)}

    def _is_variable(self, var_name):
        if len(self._get_var_names(var_name)) == 0:
            return False
        else:
            return True
        
    def _number_iterations(self, var_stem):
        
        observation_vars = self._get_var_names(var_stem)

        return len(observation_vars)
    
    def _get_var_names(self, var_stem):
        
        observation_vars = [v for v in self.vars if var_stem.lower() in v.lower()]

        return observation_vars

    
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
        obj_copy.snow._snow_vars = self.snow_vars
        obj_copy.snow._total_swe = self._total_swe
        obj_copy.snow._wet_dry = self._wet_dry

        return obj_copy

    @property
    def vars(self) -> list:
        """list: Returns non-coordinate varibles"""
        return list(self._obj.data_vars)
    
    @property
    def snow_vars(self) -> dict:
        """list: Returns non-coordinate varibles"""
        if not self._snow_vars:
            self.parse_snow_vars()
        return self._snow_vars
    
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
    
    @property
    def samples(self) -> dict:
        if not self._samples:
            self._get_sampling()
        return self._samples
    
    def _get_sampling(self) -> dict:
        self._samples = {}
        for var in self.vars:
            # if we didn't save sampling heights
            if 'samples' not in self._obj[var].attrs:
                self._samples[var] = pd.Series()
            else:
                self._samples[var] = self._obj[var].attrs['samples']


    def _get_total_swe(self):
        
        data_obj = self._get_obj()

        # get all density variables
        d_vars = self._get_var_names('density')

        # remove variables with all nans
        for v in d_vars:
            if data_obj[v].count() == 0:
                d_vars.remove(v) 
        
        # if we have no density left return nan
        if len(d_vars) == 0:
            LOG.info(f"No density found for {self._obj}")
            return np.nan
        
        # if we have 1 left use that variable
        if len(d_vars) == 1:
            d_var = d_vars[0]

        # if we have mulitple variables with density
        if len(d_vars) > 1:
            # use average variable if available
            if any([('avg' in v) or ('ave' in v) for v in d_vars]):
                d_var = [v for v in d_vars if ('avg' in v) or ('ave' in v)][0]

            # else average remaining variables to new array and bring attributes
            else:
                data_obj['new_mean_density'] = data_obj[d_vars].to_array(dim='new').mean('new')
                data_obj['new_mean_density'].attrs = data_obj[d_vars[0]].attrs
                # re run get sampling to ensure we have the new attribute
                self._get_sampling()
                d_var = 'new_mean_density'
        
        da = data_obj[d_var]
        da = da.dropna('z')
        
        # get sample heights from sampling strategy attribute
        sample_hs = []
        for top, bottom in self.samples[d_var].items():
            if top not in da.z: continue
            sample_hs.append(top - bottom)
        
        assert len(sample_hs) == len(da), f"Found different numbers of samples ({len(sample_hs)})\
             and data variable observations {len(da)}."
        
        water_density = 997 # kg/m3
        assert da.mean() > 1, f"Density units below 1. Convert to kg/m3."
        
        # get total swe as the sum of each layer height by density / h20 density
        _total_swe = np.sum(da.data * sample_hs / water_density)
        # not final units are in whatever sampling units are
        return _total_swe

    def _get_wet_dry(self):

        # see if we have manual wetness, temperature, and/or LWC.

        raise NotImplementedError
    
    def clean_profile(self) -> xr.Dataset:
        """
        Cleans a profile by:
        1. masking known nan values
        2. droppping empty variables
        3. removing identical variables

        Returns
        xarray.dataset
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
        # cleaned_dataset = xr.Dataset(coords = self._obj.coords, attrs=self._obj.attrs)

        NANVALUES = [-9999, '', 'nan', -9999.0, '-9999']

        i = False
        for nanval in NANVALUES:
            if not i:
                cleaned_dataset = self._obj.copy().where(self._obj.copy() != nanval)
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
            