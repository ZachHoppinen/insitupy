import pandas as pd
import pytest

from insitupy.campaigns.metadata import MetaDataParser

pit1dict = {"id": "COERAP_20200427_0845", "time": "2020-04-27T14:45:00+0000",\
        "lat": 38.92524, "long": -106.97112, "utm": "13", "siteid": "Aspen",\
        "sitename": "East River", "header_position": 10}

pit2dict = {"id": "COGMGML_20200203", "time": "2020-02-03T21:00:00+0000",\
        "lat": 39.03917744689935, "long": -108.00312700623464, "utm": "12", "siteid": "GML",\
        "sitename": "Grand Mesa", "header_position": 7}

@pytest.mark.parametrize(
    "fname, expected", [
        ("SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
        pit1dict),
        ("SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
        pit1dict),
        ("SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv",
        pit1dict),
        ("SnowEx20_SnowPits_GMIOP_20200203_GML_density_v01.csv",
        pit2dict)
        # "SnowEx20_SnowPits_GMIOP_20200203_GML_stratigraphy_v01.csv",
        # "SnowEx20_SnowPits_GMIOP_20200203_GML_temperature_v01.csv"
    ]
)
class TestSnowexPitMetadata:
    """
    Test that we can consistently read metadata across
    multiple pit measurements
    """

    @pytest.fixture
    def metadata_info(self, fname, data_path):
        # This is the parser object
        obj = MetaDataParser(
            data_path.joinpath(fname), "US/Mountain"
        )
        metadata, columns, header_pos = obj.parse()
        return metadata, columns, header_pos

    @pytest.fixture
    def metadata(self, metadata_info):
        return metadata_info[0]

    @pytest.fixture
    def columns(self, metadata_info):
        return metadata_info[1]

    @pytest.fixture
    def header_pos(self, metadata_info):
        return metadata_info[2]

    # fname needs to be in test since it is a class
    # level parameterization
    def test_id(self, metadata, expected, fname):
        assert metadata.id == expected['id']

    def test_date_time(self, metadata, expected, fname):
        # converted from mountain time
        assert metadata.date_time == pd.to_datetime(
            expected['time']
        )

    def test_latitude(self, metadata, expected, fname):
        assert metadata.latitude == expected['lat']

    def test_longitude(self, metadata, expected, fname):
        assert metadata.longitude == expected['long']

    def test_utm_epsg(self, metadata, expected, fname):
        assert metadata.utm_epsg == expected['utm']

    def test_site_id(self, metadata, expected, fname):
        assert metadata.site_id == expected['siteid']

    def test_site_name(self, metadata, expected, fname):
        assert metadata.site_name == expected['sitename']

    def test_flags(self, metadata, expected, fname):
        assert metadata.flags is None

    def test_header_position(self, header_pos, expected, fname):
        assert header_pos == expected['header_position']


@pytest.mark.parametrize(
    "fname, expected_cols", [
        ("SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
         ['depth', 'bottom_depth', 'density_a', 'density_b', 'density_c']),
        ("SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
         ['depth', 'bottom_depth', 'avg_density', 'permittivity_a',
          'permittivity_b', 'lwc_vol_a', 'lwc_vol_b']),
        ("SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv",
         ['depth', 'temperature'])
    ]
)
def test_columns(fname, expected_cols, data_path):
    """
    Test the columns we expect to pass back from the file
    """
    obj = MetaDataParser(
        data_path.joinpath(fname), "US/Mountain"
    )
    metadata, columns, header_pos = obj.parse()
    assert columns == expected_cols
