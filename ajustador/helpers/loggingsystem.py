"""
@Description: Logging system to get reported of Moose executions and sotware state while execution.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 15th Feb, 2018.
"""

import logging

def getlogger(name):
    """ Getter function to generate logging object.
    """
    FORMAT = '%(asctime)s - %(process)d - %(filename)s - %(lineno)d - %(funcName)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT)
    return(logging.getLogger(name))
