"""
SnowDataset Class an extension of xarray's dataset with addition snow features.
"""

import logging

import numpy as np
import pandas as pd
import xarray as xr

LOG = logging.getLogger(__name__)

# class SnowProfile(xr.Dataset):
    
def clean_profile(ds):

    ds = profile_to_z_meters(ds)
    ds = clean_profile(ds)
    print(ds)
    ds = clean_vars(ds)
    print(ds)

    return ds

def profile_to_z_meters(ds):

    current_units = ds.z.attrs['units']
    
    if not current_units: raise RuntimeError(f"Unable to convert units to meters based on .z.attrs['units'] of\
        {ds}")
    
    if current_units == 'mm': ds['z'] = ds.z / 1000
    elif current_units == 'cm': ds['z'] = ds.z / 100
    elif current_units == 'm': LOG.info(f"Z dimension already in meters")
    else: raise ValueError(f"Unable to convert {current_units} to meters.")

    ds.z.attrs['units'] = 'm'

    return ds

def clean_profile(ds):

    NANVALUES = [-9999, '', 'nan']

    for nanval in NANVALUES:
        ds = ds.where(ds != nanval)
    
    # remove massive negative or positive values
    for var in ds.data_vars:
        if ds[var].dtype == object: continue

        ds[var] = ds[var].where(ds[var] > -1e29)
        ds[var] = ds[var].where(ds[var] < 1e29)
    return ds


def clean_vars(ds):
    for var in ds.data_vars:
        if ds[var].count() == 0:
            ds = ds.drop_vars(var)
    
    return ds

    