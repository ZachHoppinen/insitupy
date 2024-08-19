import numpy as np
import pandas as pd
import pytest

from snowcore.io.readers import CSVReader

pit1dict = {"id": "COERAP_20200427_0845", "time": "2020-04-27T14:45:00+0000",\
    "lat": 38.92524, "long": -106.97112, "utm": "13", "siteid": "Aspen",\
    "sitename": "East River", "header_position": 10, 'flags': None,
    "data": np.array([])}

pit2dict = {"id": "COGMGML_20200203", "time": "2020-02-03T21:00:00+0000",\
    "lat": 39.03917744689935, "long": -108.00312700623464, "utm": "12", "siteid": "GML",\
    "sitename": "Grand Mesa", "header_position": 7, 'flags': None,
    "data": np.array([])}

pit3dict = {"id": "COCPMR_20210527_1145", "time": "2021-05-27T17:45:00+0000",\
    "lat": 40.51888, "long": -105.89162, "utm": "13", "siteid": "Michigan River",\
    "sitename": "Cameron Pass", "header_position": 13, 'flags': 'BDG',
    "data": np.array([])}

@pytest.mark.parametrize(
    "fname, expected", [
    ("SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv", pit1dict),
    ("SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv", pit1dict),
    ("SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv", pit1dict),
    # density 2020 this one doesn't have Lat, long
    ("SnowEx20_SnowPits_GMIOP_20200203_GML_density_v01.csv", pit2dict),
    # stratigrapy 2020 this one has a column "comments" with no data
    ("SnowEx20_SnowPits_GMIOP_20200203_GML_stratigraphy_v01.csv", pit2dict),
    # temperature 20202 this one uses "Height (cm)" instead of "Top (cm)"
    ("SnowEx20_SnowPits_GMIOP_20200203_GML_temperature_v01.csv", pit2dict),
    # LWC 2020
    ("SnowEx20_SnowPits_GMIOP_20200203_GML_LWC_v01.csv", pit2dict),
    # 2021 pits
    ("SNEX21_TS_SP_20210527_1145_COCPMR_data_density_v01.csv", pit3dict),
    ("SNEX21_TS_SP_20210527_1145_COCPMR_data_gapFilledDensity_v01.csv", pit3dict),
    # ("SNEX21_TS_SP_20210527_1145_COCPMR_data_siteDetails_v01.csv", pit3dict),
    ("SNEX21_TS_SP_20210527_1145_COCPMR_data_stratigraphy_v01.csv", pit3dict),
    ("SNEX21_TS_SP_20210527_1145_COCPMR_data_LWC_v01.csv", pit3dict),
    ("SNEX21_TS_SP_20210527_1145_COCPMR_data_temperature_v01.csv", pit3dict),
    ]
)

class TestCSVReader:
    """
    Tests of CSV reader to capture data and metadata.
    """

    @pytest.fixture
    def reader(self, fname, data_path):
        reader = CSVReader(data_path.joinpath(fname))
        # reader = reader.parse()
        return reader

    def test_id(self, reader, expected):
        assert reader.metadata['PitID'] == expected['id']

    def test_long(self, reader, expected):
        assert reader.metadata['Longitude'] == expected['long']
    
    # def test_x(self, snowreadpit, expected):
    #     assert snowpit.x == expected['long']
    
    # def test_y(self, snowpit, expected):
    #     assert snowpit.y == expected['lat']
    
    # def test_time(self, snowpit, expected):
    #     assert snowpit.time == expected['time']
    
    # def test_siteid(self, snowpit, expected):
    #     assert snowpit.attrs['siteid'] == expected['siteid']
    
    # def test_siteid(self, snowpit, expected):
    #     assert snowpit.attrs['sitename'] == expected['sitename']

    # def test_data(self, snowpit, expected):
    #     assert snowpit.data == expected['data']

    # @pytest.mark.skip('No errors known yet to test for')
    # def test_errors(self, fname, expected):
    #     assert 1 == 0

