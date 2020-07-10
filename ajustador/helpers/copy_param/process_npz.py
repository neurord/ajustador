import logging
import fileinput
import re
import os
import numpy as np
from pathlib import Path

from ajustador.helpers.loggingsystem import getlogger

logger = getlogger(__name__)
logger.setLevel(logging.DEBUG)

def get_least_fitness_params(data, fitnum= None):
    """ fitnum == None -> return last item least fitness parameters list.
        fitnum == integer -> return fitnum item from data(npz object).
    """
    row = fitnum if fitnum else np.argmin(data['fitvals'][:,-1])
    return (row, np.dstack((data['params'][row],data['paramnames']))[0])

def check_key_in_npz_data(npz_data, key):
    feat=[feat.split('=')[0] for feat in npz_data['features']]
    if key in npz_data.files:
         return True
    elif key in feat:
        return True
    logger.error("No KEY {} in optimization npz data load!!!".format(key))
    return False

def make_new_file_name_from_npz(npz_data, npz_file_name, dest_path, neuron_type, file_in):
    "Makes new cond file name from npz data"
    logger.info("file_in={} npz_file={} dest_path={} {}".format(file_in, npz_file_name, dest_path, neuron_type))
    if check_key_in_npz_data(npz_data,'neuron_type') \
    and check_key_in_npz_data(npz_data,'measurment_name'): # may be removed in future.
       if npz_data['neuron_type'] in npz_data['measurment_name']:
           file_name = file_in.rstrip('.py') + '_' + npz_data['measurment_name'] + '.py'
       else:
           file_name = file_in.rstrip('.py') + '_' + npz_data['measurment_name'] + npz_data['neuron_type'] + '.py'
    else:
        file_name = file_in.rstrip('.py') + '_' + os.path.basename(npz_file_name).rpartition('-' + neuron_type + '-')[2].rstrip('.npz') + '.py'
    logger.debug("{} {}".format(file_in.rstrip('.py'), file_name))
    return os.path.join(dest_path, file_name)

def get_params(param_data_list, prefix, exclude_flag=False):
    if exclude_flag:
        return {item[1]:item[0] for item in param_data_list if not item[1].startswith(prefix)}
    else:
        return {item[1]:item[0] for item in param_data_list if item[1].startswith(prefix)}
