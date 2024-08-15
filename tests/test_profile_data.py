import numpy as np
import pytest

from insitupy.campaign import SnowExProfileData
from insitupy.variables import ProfileVariables


class TestSnowexPitProfile:
    """
    Test the attributes of the profile
    """

        # ("SNEX21_TS_SP_20210527_1145_COCPMR_data_temperature_v01.csv", pit3dict),

    @pytest.mark.parametrize(
        "fname, variable, expected", [
            ("SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv",
                ProfileVariables.SNOW_TEMPERATURE, 0.0),
            ("SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                ProfileVariables.LWC, np.nan),
            ("SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                ProfileVariables.PERMITTIVITY, np.nan),
            ("SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
                ProfileVariables.DENSITY, 395.037037),
            ("SnowEx20_SnowPits_GMIOP_20200203_GML_density_v01.csv",
                ProfileVariables.DENSITY, 284.2121),
            ("SnowEx20_SnowPits_GMIOP_20200203_GML_temperature_v01.csv",
                ProfileVariables.SNOW_TEMPERATURE, -4.423076),
            ("SnowEx20_SnowPits_GMIOP_20200203_GML_LWC_v01.csv",
                ProfileVariables.LWC, 0.0),
            ("SnowEx20_SnowPits_GMIOP_20200203_GML_LWC_v01.csv",
                ProfileVariables.DENSITY, 284.21212),
            ("SnowEx20_SnowPits_GMIOP_20200203_GML_LWC_v01.csv",
                ProfileVariables.PERMITTIVITY, 1.308909),
            ("SNEX21_TS_SP_20210527_1145_COCPMR_data_density_v01.csv",
                ProfileVariables.DENSITY, 408.0),
            ("SNEX21_TS_SP_20210527_1145_COCPMR_data_gapFilledDensity_v01.csv",
                ProfileVariables.DENSITY, 405.0),
            ("SNEX21_TS_SP_20210527_1145_COCPMR_data_stratigraphy_v01.csv",
                ProfileVariables.GRAIN_SIZE, np.nan),
            # this will fail because we have a two line comment in this file
            # so it cuts off the first line of data.
            ("SNEX21_TS_SP_20210527_1145_COCPMR_data_LWC_v01.csv",
                ProfileVariables.DENSITY, 406.875),
            ("SNEX21_TS_SP_20210527_1145_COCPMR_data_temperature_v01.csv",
                ProfileVariables.SNOW_TEMPERATURE, np.nan),
        ]
    )

    def test_mean(self, fname, variable, expected, data_path):
        file_path = data_path.joinpath(fname)
        obj = SnowExProfileData.from_file(file_path, variable)        

        result = obj.mean

        if np.isnan(expected):
            assert np.isnan(result)
        else:
            assert result == pytest.approx(expected)


    @pytest.mark.parametrize(
        "fname, variable", [
            (
                "SnowEx20_SnowPits_GMIOP_20200203_GML_stratigraphy_v01.csv",
                ProfileVariables.GRAIN_SIZE
            )
        ]
    )

    def test_mean_fail_nonnumeric(self, fname, variable, data_path):
        """
        Test filepaths expected to fail due to non-numeric values
        """
        file_path = data_path.joinpath(fname)
        obj = SnowExProfileData.from_file(file_path, variable)
        with pytest.raises(TypeError):
            result = obj.mean


    @pytest.mark.parametrize(
        "fname, variable", [
            (
                "SNEX21_TS_SP_20210527_1145_COCPMR_data_siteDetails_v01.csv",
                ProfileVariables.GRAIN_SIZE),
            ("SNEX21_TS_SP_20210527_1145_COCPMR_data_siteDetails_v01.csv",
                ProfileVariables.GRAIN_SIZE)
        ]
    )

    def test_mean_fail_sitedetails(self, fname, variable, data_path):
        """
        Test filepaths expected to fail due to non-numeric values
        """
        file_path = data_path.joinpath(fname)
        with pytest.raises(RuntimeError):
            obj = SnowExProfileData.from_file(file_path, variable)
            result = obj.mean


    @pytest.mark.parametrize(
        "fname, variable, expected", [
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv",
                ProfileVariables.SNOW_TEMPERATURE, 95.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                ProfileVariables.LWC, 95.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                ProfileVariables.PERMITTIVITY, 95.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
                ProfileVariables.DENSITY, 95.0
            ),
        ]
    )
    def test_total_depth(self, fname, variable, expected, data_path):
        file_path = data_path.joinpath(fname)
        obj = SnowExProfileData.from_file(file_path, variable)
        result = obj.total_depth
        assert result == pytest.approx(expected)
