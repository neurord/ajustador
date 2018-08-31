"""
@description : Utility module to deliver appropritate value based on scale character code.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 11th JUL, 2018.
"""

from ajustador.helpers.loggingsystem import getlogger
logger = getlogger(__name__)

def get_units_scale_factor(eng_units):
    ''' Fuction to get suitable multiplier using the scale characater code from units
            information.

            @Usage:
                   get_units_scale_factor(eng_units='mA') -> 10e-3
    '''
    units_prefix = {"y":1e-24, "z":1e-21, "a":1e-18, "f":1e-15, "p": 1e-12,
                    "n":1e-9, "u":1e-6, "µ":1e-6, "m":1e-3, "c":1e-2, "d":0.1,
                    "h":100, "k":1000, "M":1e6, "G":1e9, "T":1e12, "P":1e15,
                    "E":1e18, "Z":1e21, "Y":1e14}
    try:
        prefix = eng_units.strip('(')[0]
        return units_prefix[prefix]
    except (KeyError, IndexError):
        logger.warn("Provided units {}! Using scaling factor 1.0! Check your input units in csv.".format(eng_units))
        return 1.0
