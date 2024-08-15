"""
Profile metadata structures
"""

from dataclasses import dataclass, field

import logging

import pandas as pd

LOG = logging.getLogger(__name__)


@dataclass()
class ProfileMetaData:
    id: str
    date_time: pd.Timestamp
    latitude: float
    longitude: float
    utm_epsg: str = None  # the EPSG for the utm zone
    site_id: str = None
    site_name: str = None
    units: dict = field(default_factory= lambda: {})
    flags: str = None