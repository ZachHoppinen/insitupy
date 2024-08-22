import numpy as np
import pandas as pd
import pytest

from pandas import Timestamp, NaT

from pandas.testing import assert_frame_equal

from insitupy.io.readers import Reader, CSVReader, NETCDFReader, check_consecutive

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

class TestNETCDFReader:
    """
    Tests of NetCDF reader to read in datafiles and parse attributes
    """

    @pytest.fixture
    def reader(self, fname, data_path):
        reader = NETCDFReader(data_path.joinpath(fname))
        return reader
    
    @pytest.fixture
    def ds(self, reader):
        ds = reader.create_snowprofile()
        return ds
    
    @pytest.mark.parametrize("fname",
        ["SNEX20_TS_SP_20200422_1512_COGMSO_data_v02.nc"])
    
    def test_exists(self, reader):
        assert type(reader) == NETCDFReader

    @pytest.mark.parametrize("fname, expected",
        [("SNEX20_TS_SP_20200422_1512_COGMSO_data_v02.nc",
        ['avg_density', 'comments', 'density_a', 'density_b', 'grain_size',\
        'grain_type', 'hand_hardness','lwc_vol_a','lwc_vol_b',\
        'manual_wetness', 'permittivity_a', 'permittivity_b', 'temperature'])])
    
    def test_variables(self, ds, expected):
        assert list(ds.data_vars) == expected
    
    @pytest.mark.parametrize("fname, expected",
        [("SNEX20_TS_SP_20200422_1512_COGMSO_data_v02.nc",
        {'Location': 'Grand Mesa',
        'Site': 'Skyway Open',
        'PitID': 'COGMSO_20200422_1512',
        'DateLocal Standard Time': Timestamp('2020-04-22 15:12:00'),
        'UTM Zone': '12N',
        'Easting': np.float64(754251.0),
        'Northing': np.float64(4325772.0),
        'Latitude': np.float64(39.04404),
        'Longitude': np.float64(-108.06224),
        'Flags': "",
        'Pit Comments': '111-101 and 101-91 cm density lots of water percolating. Temp. start 16:12  Temp end 1619',
        'Parameter Codes': 'na for this parameter',
        'x_coord_name': 'Longitude',
        'y_coord_name': 'Latitude',
        'id_coord_name': 'PitID',
        'units': {'depth': ['cm'], 'temperature': ['deg C']}})])
    
    def test_attrs(self, ds, expected):
        assert ds.attrs == expected
    
    @pytest.mark.parametrize("fname, expected",
        [("SNEX20_TS_SP_20200422_1512_COGMSO_data_v02.nc",
        np.array([111., 101., 91., 81., 71., 61., 51., 41., 31., 21., 11., 1.]))])
    
    def test_bottom_density(self, ds, expected):
        assert np.array_equal(ds['avg_density'].attrs['bottom'], expected)
    
    @pytest.mark.parametrize("fname, expected",
        [("SNEX20_TS_SP_20200422_1512_COGMSO_data_v02.nc",
        np.array([115., 99., 97., 94., 91., 80., 75., 56., 42., 10., 0.]))])
    def test_bottom_layer(self, ds, expected):
        assert np.array_equal(ds['hand_hardness'].attrs['bottom'], expected)
    
    @pytest.mark.parametrize("fname, expected",
        [("SNEX20_TS_SP_20200422_1512_COGMSO_data_v02.nc",
        ['z', 'x', 'y', 'id', 'time'])])
    def test_indexes(self, ds, expected):
        assert list(ds.indexes) == expected
    
    @pytest.mark.parametrize("fname, expected",
        [("SNEX20_TS_SP_20200422_1512_COGMSO_data_v02.nc",
        [0., 10., 11., 20., 21.])])
    def test_zs(self, ds, expected):
        assert list(ds.z.data) == expected

    @pytest.mark.parametrize("fname, attrs, expected",
    [("SNEX20_TS_SP_20200422_1512_COGMSO_data_v02.nc", 
    {"a": "a", "b": "1", "c": "[1,2,3]","d":'{"a":1}'},\
    {"a": "a", "b": 1, "c": [1,2,3], "d":{"a":1}})])
    def test_decoder_numbers(self, reader, attrs, expected):
        assert expected == reader._decode_attrs(attrs)
    
    @pytest.mark.parametrize("fname, attrs, expected",
    [("SNEX20_TS_SP_20200422_1512_COGMSO_data_v02.nc", 
    {"a": '2020-01-02'},\
    {"a": pd.to_datetime('2020-01-02')})])
    def test_decoder_datetime(self, reader, attrs, expected):
        assert expected == reader._decode_attrs(attrs)

class TestCSVReader:
    """
    Tests of CSV reader to capture data and metadata.
    """

    @pytest.fixture
    def reader(self, fname, data_path):
        reader = CSVReader(data_path.joinpath(fname))
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
 
