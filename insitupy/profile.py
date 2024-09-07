"""
Classes for vertical snow profiles. Contains a single variables as a function of 
either distance from ground or snow surface.
"""

from abc import ABC
from typing import Union

from pathlib import Path

class SnowProfile(ABC):
    """
    General profile class. Can contain x, y, time data. As per the 
    International Classification of Seasonal Snow on the Ground (ICSSG)
    heights and SWE measurements are in centimeters, snow strength are in Pa,
    penetration depths are in cm.

    ICSSG documentation: https://unesdoc.unesco.org/ark:/48223/pf0000186462

    Args:
        x [default = None]: x spatial location [i.e. longitude]
        y [default = None]: y spatial location [i.e. latitude]
        epsg [default = None]: epsg code for x, y values
        datetime [default = None]: date and time of profile. String (format: YYYY-MM-DDTHH:MM) or datetime object
        timezone [default = None]: timezone of datetime if not present in datetime object
        id [default = None]: unique profile id.
        datum [default = ground]: Is there vertical heights relative to ground ['ground'] or
            snow surface ['surface']?
        
    """

    def __init__(self, x = None, y = None, epsg = None, datetime = None, timezone = None, id = None, datum = 'ground'):

        self._x = x
        self._y = y
        self._epsg = epsg
        self._datetime = datetime
        self._timezone = timezone
        self._id = id

    # checks on x, y, datetime, and id
    
    # checks for x, y values if we get utm zone

    # checks for timezones on datetime

    # checks for ground_datum vs surface_datum

    # generate random id if not provided? Could be either np.random.randint()
    # or based on YYYYMMDD_Xlocation_Ylocation_randomextranumbers

    # general sanity checks for datatypes (need to all be the same or castable)

    # general load from file functionality?
    # could seperate metadata and data loading for folks who only care about metadata
    # find appropriate reader from filepath and load metadata/data

    # other profile general functionality?


class LayeredProfile(SnowProfile):
    """
    Profile with measurements between a top and bottom location that defines
    layers within the snowpack

    args: 
        layer_bottoms: vertical location of the measurement bottoms
        layer_tops: vertical location of the measurement tops
        layer_values: values to associate with each layer

    """

    # checks to ensure we have matching layer bottoms, tops, and values
    # and that our bottoms are all less than our tops

    # do we want to figure out units on z axis now?

    # resampling functions to go to gridded from layered data

    # resampling functions to go to geopandas from layer data

    pass

class PointProfile(SnowProfile):
    """
    Profile with measurements at distinct locations within the snowpack
    that do not have appreciable thickness.

    args: 
        measurement_location: vertical location of the measurement
        measurement_values: values to associate with each measurement
    """

    # checks to ensure we have matching number of locations and measurement values

    # do we want to figure out units on z axis now?

    # resampling functions to go to gridded from point data with nans filling gaps

    # resampling functions to go to geopandas from point data
    pass

class DensityProfile(LayeredProfile):
    """
    Density profile class. Contains densitys in kg/m3 for a single location and
    time as a function of distances from ground or snow surface.

    args:
        layer_bottoms: vertical location of the density layer bottoms
        layer_tops: vertical location of the density layer tops
        layer_values: density values to associate with each layer. must be in kg/m3
    """

    # checks for kg/m3 and not g/cm3 or %
    # could add keyword to convert from g/cm3 or % to kg/m3

    pass

class HandHardnessProfile(LayeredProfile):
    """
    Hand hardness profile class. Contains qualitative hand hardness for a single 
    location and time as a function of distances from ground or snow surface.

    Must be one of the five International Classification of Seasonal Snow on the Ground (ICSSG)
    hardness classifications table 1.3 (Fist [F], 4-finger [4F], 1-finger [1F], pencil [P], knife [k]). 
    Associated sub typing with "+" for harder and "-" for less harder are acceptable.
    i.e. 4F+ is harder than 4F but not quite as hard as 1F-.

    Can also be I for ice.

    Acceptable values: [F-, F, F+, 4F-, 4F, 4F+, 1F-, 1F, 1F+, P-, P, P+, K-, K, K+, I]

    args:
        layer_bottoms: vertical location of the hand hardness layer bottoms
        layer_tops: vertical location of the hand hardness layer tops
        layer_values: Hand Hardness values to associate with each layer. must be in acceptabke ICSSG values.
    """

    # check for ICSSG snow hardness classification
    pass

class LWCProfile(LayeredProfile):
    """
    Liquid water content profile class. Contains liquid water contents for a single 
    location and time as a function of distances from ground or snow surface. Can be either numeric
    representing volumetric liquid water contents with ranges up to 20% and can be in the form of a 
    percentage (3) or decimal (0.03) both representing 3%. Or can be qualtative representing manual
    wetness measurements of International Classification of Seasonal Snow on the Ground (ICSSG) table 1.5.
    Acceptable options are dry, D, moist, M, wet, W, very wet, V, VW, soaked, S.

    args:
        layer_bottoms: vertical location of the LWC layering bottoms
        layer_tops: vertical location of the LWC layering tops
        layer_values: Liquid water content values to associate with each layer. must be in %
    """

    # check for appropriate data ranges
    pass

class GrainTypeProfile(LayeredProfile):
    """
    Stratigraphy profile class. Contains grain type for a single 
    location and time as a function of layers with distances from 
    ground or snow surface.

    Grain types must be one of International Classification of Seasonal Snow on the Ground (ICSSG)
    grain types table 1.2. Options include Preciptiation Particles [P or PP], Machine Made snow [MM],
    Decomposing and Fragmented precipitation particles [DF], Rounded Grains [R, RG], Faceted Crystals [F, FC],
    Depth Hoar [DH], Surface Hoar [SH], Melt Forms [M, MF], Ice Formations [I, IF].

    args:
        layer_bottoms: vertical location of the grain type layer bottoms
        layer_tops: vertical location of the grain type layer tops
        layer_values: Liquid water content values to associate with each layer. must be in %

    """
    # check for grain types
    pass

class GrainSizeProfile(LayeredProfile):
    """
    Stratigraphy profile class. Contains grain size for a single 
    location and time as a function of layers with distances from 
    ground or snow surface.

    Grain sizes are in mm and are the dimension of greatest extent of the average snow
    grain.

    args:
        layer_bottoms: vertical location of the grain type layer bottoms
        layer_tops: vertical location of the grain type layer tops
        layer_values: Liquid water content values to associate with each layer. must be in %

    """
    # check for grain types
    pass

class TemperatureProfile(PointProfile):
    """
    Temperature profile class. Contains snow temperatures for a single 
    location and time as a function of distances from ground or snow surface.

    args:
        measurement locations: vertical location of the temperature measurements
        layer_values: temperatures values to associate with each layer. Must be in °C
    """
    pass