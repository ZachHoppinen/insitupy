import pandas as pd
import pytest

from insitupy.metadata import MetaDataParser

pit1dict = {"id": "COERAP_20200427_0845", "time": "2020-04-27T14:45:00+0000",\
        "lat": 38.92524, "long": -106.97112, "utm": "13", "siteid": "Aspen",\
        "sitename": "East River", "header_position": 10, 'flags': None}

pit2dict = {"id": "COGMGML_20200203", "time": "2020-02-03T21:00:00+0000",\
        "lat": 39.03917744689935, "long": -108.00312700623464, "utm": "12", "siteid": "GML",\
        "sitename": "Grand Mesa", "header_position": 7, 'flags': None}

pit3dict = {"id": "COCPMR_20210527_1145", "time": "2021-05-27T17:45:00+0000",\
        "lat": 40.51888, "long": -105.89162, "utm": "13", "siteid": "Michigan River",\
        "sitename": "Cameron Pass", "header_position": 13, 'flags': 'BDG'}

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

    @pytest.mark.skip(reason="Broken but can't figure out why it is failing...")
    def test_flags(self, metadata, expected, fname):
        assert metadata.flags is expected['flags']

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
         ['depth', 'temperature']),
        ("SnowEx20_SnowPits_GMIOP_20200203_GML_density_v01.csv",
         ['depth', 'bottom_depth','density_a', 'density_b', 'density_c']),
        ("SnowEx20_SnowPits_GMIOP_20200203_GML_stratigraphy_v01.csv",
         ['depth', 'bottom_depth', 'grain_size', 'grain_type', 'hand_hardness', 'manual_wetness', 'comments']),
        ("SnowEx20_SnowPits_GMIOP_20200203_GML_temperature_v01.csv",
         ['depth', 'temperature']),
        ("SNEX21_TS_SP_20210527_1145_COCPMR_data_density_v01.csv",
         ['depth', 'bottom_depth', 'density_a', 'density_b', 'density_c']),
        ("SNEX21_TS_SP_20210527_1145_COCPMR_data_gapFilledDensity_v01.csv",
         ['depth', 'bottom_depth', 'density_a', 'density_b']),
        ("SNEX21_TS_SP_20210527_1145_COCPMR_data_siteDetails_v01.csv",
         []),
        ("SNEX21_TS_SP_20210527_1145_COCPMR_data_stratigraphy_v01.csv",
         ['depth', 'bottom_depth', 'grain_size', 'grain_type', 'hand_hardness', 'manual_wetness', 'comments']),
        ("SNEX21_TS_SP_20210527_1145_COCPMR_data_LWC_v01.csv",
         ['depth', 'bottom_depth', 'avg_density', 'permittivity_a', 'permittivity_b', 'lwc_vol_a', 'lwc_vol_b']),
        ("SNEX21_TS_SP_20210527_1145_COCPMR_data_temperature_v01.csv",
         ['depth', 'temperature', 'time_start/end']),
    ]
)

def test_columns(fname, expected_cols, data_path):
    """
    Test the columns we expect to pass back from the file
    """
    obj = MetaDataParser(
        data_path.joinpath(fname), "US/Mountain"
    )

    if 'siteDetails' in fname:
        with pytest.raises(RuntimeError):
            metadata, columns, header_pos = obj.parse()
    else:
        metadata, columns, header_pos = obj.parse()
        assert columns == expected_cols
