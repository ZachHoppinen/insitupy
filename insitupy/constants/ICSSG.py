"""
Holds International Classification of Seasonal Snow on the Ground (ICSSG)
classifications and mappings.

Usage:
from constants import ICSSG

assert 'D' in ICSSG.GrainTypes


"""

class StandardizeValues:
    
    def from_string(self, values):
        pass

class LiquidWaterContent:
    """
    Class holding all the ICSSG liquid water content approximations.

    manual wetness measurements of International Classification of Seasonal Snow on the Ground (ICSSG) 
    table 1.5.
    Acceptable options are dry, D, moist, M, wet, W, very wet, V, VW, soaked, S.
    """
    
    FACET = 'F'

    pass

class HandHardnesses:
    """
    Class holding all the ICSSG hand hardness values.

    Acceptable values: [F-, F, F+, 4F-, 4F, 4F+, 1F-, 1F, 1F+, P-, P, P+, K-, K, K+, I]
    """
    
    FACET = 'F'

    pass

class GrainTypes:
    """
    Class holding all the ICSSG grain types.

    Grain types must be one of International Classification of Seasonal Snow on the Ground (ICSSG)
    grain types table 1.2. Options include Preciptiation Particles [P or PP], Machine Made snow [MM],
    Decomposing and Fragmented precipitation particles [DF], Rounded Grains [R, RG], Faceted Crystals [F, FC],
    Depth Hoar [DH], Surface Hoar [SH], Melt Forms [M, MF], Ice Formations [I, IF].

    """
    
    FACET = 'F'

    pass