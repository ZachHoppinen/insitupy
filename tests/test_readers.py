import numpy as np
import pandas as pd
import pytest

from insitupy.io.readers import CSVReader

pit1dict = {"id": "COERAP_20200427_0845","PitID": "COERAP_20200427_0845", "Date/Local Standard Time": "2020-04-27T0845",\
    "Latitude": 38.92524, "Longitude": -106.97112, "utm": "13", "Site": "Aspen",\
    "Location": "East River", "UTM Zone": '13N', 'Flags': "", "Easting": 329131, "Northing":4310328, \
    "data": np.array([])}

pit2dict = {"id": "COGMGML_20200203", "Location": "Grand Mesa",\
    "Site": "GML", "PitID": "COGMGML_20200203", "Date/Local Time": "2020-02-03T1400", "UTM Zone": "12N",\
    "Easting": 759386, "Northing": 4325399, 'flags': '',
    "data": np.array([])}

pit3dict = {"id": "COCPMR_20210527_1145", "Location": "Cameron Pass",\
    "Site": "Michigan River", "PitID": "COCPMR_20210527_1145", "Date/Local Standard Time": "2021-05-27T1145",\
    "UTM Zone": "13N", "Easting": 424470, "Northing": 4485732, "Latitude": 40.51888,\
    "Longitude": -105.89162, "Slope": -9999, "Aspect": -9999, "Air Temp": -9999,\
    "HS ": 38, "Observers": "D. McGrath", "WISe Serial No": 19, "Weather": "Sunny, 50 F", "Precip Type": None,\
    "Precip Rate": None, "Sky": "Clear", "Wind": "Moderate", "Ground Condition": "Saturated", "Ground Roughnes": "Smooth",\
    "Vegetation Height": 0, "Tree Canopy": "No Trees", \
    "Pit Comments": "11-12 cm of water at base of pit. Below 12 cm pit was saturated with standing water. Water temp is 2.18 C. ",\
    "Flags": "BDG",\
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

    def test_variables(self, reader, expected):
        for k, v in reader.metadata.items():
            assert v == expected[k], f'Mismatch for variable {k} between found {v} and expected: {expected[k]}'

    @pytest.mark.skip('Need to put in data')
    def test_data(self, reader, expected):
        assert snowpit.data == expected['data']

    @pytest.mark.skip('No errors known yet to test for')
    def test_errors(self, reader, expected):
        assert 1 == 0

