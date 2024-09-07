"""
Classes for holding multiple SnowProfile measurement objects (grain type, lwc, etc). Can occur in distinct
spatial or temporal values or be co-located.
"""

class SnowCampaign:
    """
    Generic collection class for multiple SnowProfile objects. 
    Holds one type of measurement with multiple profiles with distinct locations or dates.

    Args:
        Profiles: iterable of SnowProfile objects.
    """

    # error checking

    # matches in space and in time for overlapping pits

    # get locations

    # get times

    # summary functions

    # load from one directory .from_directory()

    # gridded functionality

    # geopandas functionality