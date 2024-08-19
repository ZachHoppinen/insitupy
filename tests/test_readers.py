import numpy as np
import pandas as pd
import pytest

from insitupy.io.readers import Reader, CSVReader, check_consecutive

pit1metadata = {"PitID": "COERAP_20200427_0845", "Date/Local Standard Time": pd.Timestamp("2020-04-27T08:45:00"),\
    "Latitude": 38.92524, "Longitude": -106.97112, "utm": "13", "Site": "Aspen",\
    "Location": "East River", "UTM Zone": '13N', 'Flags': None, "Easting": 329131, "Northing":4310328}

pit2metadata = {"Location": "Grand Mesa", "Site": "GML", "PitID": "COGMGML_20200203",\
     "Date/Local Time": pd.Timestamp("2020-02-03T14:00:00"), "UTM Zone": "12N",\
    "Easting": 759386, "Northing": 4325399, 'flags': None}

pit3metadata = {"Location": "Cameron Pass", "Site": "Michigan River", "PitID": "COCPMR_20210527_1145",\
    "Date/Local Standard Time": pd.Timestamp("2021-05-27T11:45:00"),\
    "UTM Zone": "13N", "Easting": 424470, "Northing": 4485732, "Latitude": 40.51888,\
    "Longitude": -105.89162, "Slope": -9999, "Aspect": -9999, "Air Temp": -9999,\
    "HS ": 38, "Observers": "D. McGrath", "WISe Serial No": 19, "Weather": "Sunny, 50 F", "Precip Type": None,\
    "Precip Rate": None, "Sky": "Clear", "Wind": "Moderate", "Ground Condition": "saturated", "Ground Roughnes": "Smooth",\
    "Vegetation Height": 0, "Tree Canopy": "No Trees", \
    "Pit Comments": "11-12 cm of water at base of pit. Below 12 cm pit was saturated with standing water. Water temp is 2.18 C.  Flag BDG",\
    "Flags": "BDG", "Parameter Codes": "n/a for this parameter"}

class TestReaders:
    """
    Tests of general reader functionality
    """

    # @pytest.fixture
    # def reader(self, fname, data_path):
    #     reader = Reader(data_path.joinpath(fname))
    #     return reader
    
    @pytest.mark.parametrize(
        "fname, error", [
        ("nonexistent", AssertionError),
        (123, TypeError),
        ('unsupported_extension.wrong_extension', AssertionError)
        ]
    )
    def test_continous_check_errors(self, fname, error, data_path):
        with pytest.raises(error):
            Reader(data_path.joinpath(fname))


class TestCSVReader:
    """
    Tests of CSV reader to capture data and metadata.
    """

    @pytest.fixture
    def reader(self, fname, data_path):
        reader = CSVReader(data_path.joinpath(fname))
        reader.parse()
        return reader

    @pytest.mark.parametrize("fname",
        ["SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv", 
        "SnowEx20_SnowPits_GMIOP_20200203_GML_temperature_v01.csv",
        "SNEX21_TS_SP_20210527_1145_COCPMR_data_LWC_v01.csv"])
    def test_header_marker(self, reader):
        assert reader.header_marker == '#'

    @pytest.mark.parametrize("fname",
        ["SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv", 
        "SnowEx20_SnowPits_GMIOP_20200203_GML_temperature_v01.csv",
        "SNEX21_TS_SP_20210527_1145_COCPMR_data_LWC_v01.csv"])
    def test_header_seperator(self, reader):
        assert reader.header_sep == ','
    
    @pytest.mark.parametrize("fname, expected",
        [("SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv", "COERAP_20200427_0845"), 
        ("SnowEx20_SnowPits_GMIOP_20200203_GML_temperature_v01.csv", "COGMGML_20200203"),
        ("SNEX21_TS_SP_20210527_1145_COCPMR_data_LWC_v01.csv", "COCPMR_20210527_1145")])
    def test_id(self, reader, expected):
        assert reader.metadata['PitID'] == expected

    @pytest.mark.parametrize(
        "fname, expected", [
        ("SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv", pit1metadata),
        ("SnowEx20_SnowPits_GMIOP_20200203_GML_LWC_v01.csv", pit2metadata),
        ("SNEX21_TS_SP_20210527_1145_COCPMR_data_temperature_v01.csv", pit3metadata),
        ])
    def test_metadata(self, reader, expected):
        for k, v in reader.metadata.items():
            assert v == expected[k], f'Mismatch for variable {k} between found {v} and expected: {expected[k]}'
    
    @pytest.mark.parametrize(
        "fname, expected", [
        ("SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv", 
        ["top", "bottom", "density_a", "density_b", "density_c"]),
        ("SnowEx20_SnowPits_GMIOP_20200203_GML_LWC_v01.csv", 
        ["top", "bottom", "avg_density", "permittivity_a", "permittivity_b", "lwc_vol_a", "lwc_vol_b"]),
        ("SNEX21_TS_SP_20210527_1145_COCPMR_data_gapFilledDensity_v01.csv", 
        ["top", "bottom", "density_a", "density_b"]),
        ("SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv", 
        ["depth", "temperature"]),
        ("SNEX21_TS_SP_20210527_1145_COCPMR_data_stratigraphy_v01.csv", 
        ["top", "bottom", "grain_size", "grain_type", "hand_hardness", "manual_wetness", "comments"]),
        ]
    )
    def test_columns(self, reader, expected):
        assert reader.columns == expected

    @pytest.mark.parametrize(
        "fname, expected", [
            ("SNEX21_TS_SP_20210527_1145_COCPMR_data_LWC_v01.csv", 
            {'top': ['cm'], 'bottom': ['cm'], 'avg_density': ['kg/m3'], 'permittivity_a': '[]',\
            'permittivity_b': '[]', 'lwc_vol_a': ['%'], 'lwc_vol_b': ['%']}),
            ("SNEX21_TS_SP_20210527_1145_COCPMR_data_LWC_v01.csv", 
            {'top': ['cm'], 'bottom': ['cm'], 'density_a': ['kg/m3'],'density_b': ['kg/m3'],\
            'density_c': ['kg/m3'],'avg_density': ['kg/m3'], 'lwc_vol_a': ['%'], 'lwc_vol_b': ['%'],\
            'permittivity_a': '[]', 'permittivity_b': '[]'}),
            ("SnowEx20_SnowPits_GMIOP_20200203_GML_stratigraphy_v01.csv", 
            {'top': ['cm'], 'bottom': ['cm'], 'grain_size': ['mm'], 'grain_type': '[]', 'hand_hardness': '[]',\
            'manual_wetness': '[]', 'comments': '[]'}),
        ]
    )
    def test_units(self, reader, expected):
        for k, v in  reader.units.items():
            assert v == expected[k]

    strat_data = pd.DataFrame(
    [[116.0,96.5,"< 1 mm","DF","F","D","Some rounds"],
    [96.5, 71.0, "< 1 mm", "RG", "4F", "D", np.nan],
    [71.0, 57.0, "< 1 mm", "FC", "1F", "D", "Rounding facets"],
    [57.0, 45.0, "1-2 mm", "FC", "4F", "D", np.nan],
    [45.0, 9.0, "1-2 mm", "FC", "1F", "D", np.nan],
    [9.0, 0.0, "2-4 mm", "FC", "1F", "D", np.nan],
    ], 
    columns = ['top','bottom','grain_size','grain_type','hand_hardness','manual_wetness','comments'])

    # SNEX21_TS_SP_20210527_1145_COCPMR_data_LWC_v01
    lwc_data = pd.DataFrame(
        [[38.0,28.0,408.75,2.584,2.62,4.8,4.99],
        [28.0,18.0,405.0,2.302,2.674,3.38,5.3]]
    ,
    columns = ['top','bottom','avg_density','permittivity_a',\
        'permittivity_b', 'lwc_vol_a','lwc_vol_b'])

    @pytest.mark.parametrize(
        "fname, expected", [
            ("SnowEx20_SnowPits_GMIOP_20200203_GML_stratigraphy_v01.csv", strat_data),
            ("SNEX21_TS_SP_20210527_1145_COCPMR_data_LWC_v01.csv", lwc_data)
        ]
    )
    def test_data(self, reader, expected):
        pd.testing.assert_frame_equal(reader.data, expected)

    @pytest.mark.skip('No errors known yet to test for')
    def test_errors(self, reader, expected):
        assert 1 == 0

class TestUtils:

    @pytest.mark.parametrize(
        "l, expected", [
            ([0,1,2,3], True),
            ([0,1,2,5], False),
            ([-3,1,2,3], False),
            ([4,3,2,1], False),
        ]
    )
    def test_continous_check(self, l, expected):
        assert check_consecutive(l) == expected
    
    @pytest.mark.parametrize(
        "l, error", [
        ([], ValueError),
        ('a', TypeError),
        (None, TypeError)
        ]
    )
    def test_continous_check_errors(self, l, error):
        with pytest.raises(error):
            check_consecutive(l)
 
