from insitupy.profile import SnowProfile, LayeredProfile, PointProfile, \
    DensityProfile, HandHardnessProfile, LWCProfile, \
    GrainTypeProfile, TemperatureProfile


import numpy as np
import pandas as pd
import pytest

# no values entered
profile_expected = {SnowProfile(): {"x": None, "y": None, "epsg": None, "datetime": None, "timezone": None, "id": None}, 
# only x, y
SnowProfile(x = 10, y = 20): {"x": 10, "y": 20, "epsg": None, "datetime": None, "timezone": None, "id": None}, 
# only x, y, epsg
SnowProfile(x = 10, y = 20, epsg = 32612): {"x": 10, "y": 20, "epsg": 32612, "datetime": None, "timezone": None, "id": None}, 
# only datetime
SnowProfile(datetime = '20201001'): {"x": None, "y": None, "epsg": None, "datetime": pd.to_datetime('2020-10-01'), "timezone": None, "id": None}, 
# all values
SnowProfile(x = -114.56, y = 45.01, epsg = 4326, datetime = '2021-01-05T10:34', timezone = 'Mountain', id = 'ATL03W'): 
    {"x": -114.56, "y": 45.01, "epsg": 4326, "datetime": '2021-01-05T10:34', "timezone": 'Mountain', "id": 'ATL03W'}}

@pytest.mark.parametrize(
    "profile, expected", profile_expected.items())

class TestGeneralProfile:

    def test_x(self, profile, expected):
        assert profile._x == expected['x']
    
    def test_y(self, profile, expected):
        assert profile._y == expected['y']
    
    def test_epsg(self, profile, expected):
        assert profile._epsg == expected['epsg']

    def test_datetime(self, profile, expected):
        assert profile._datetime == expected['datetime']
    
    def test_timezone(self, profile, expected):
        assert profile._timezone == expected['timezone']
    
    def test_id(self, profile, expected):
        assert profile._id == expected['id']

class TestLayerProfile:
    pass

class TestPointProfile:
    pass

class TestDensityProfile:
    pass

class TestHandHarndessProfile:
    pass

class TestLWCProfile:
    pass

class TestGrainTypeProfile:
    pass
    
class TestTemperatureProfile:
    pass
    


