import logging
import numpy as np
from pathlib import Path

from ajustador.helpers.loggingsystem import getlogger

logger = getlogger(__name__)
logger.setLevel(logging.DEBUG)

def create_path(path,*args):
    "Creates sub-directories recursively if they are not available"
    path = Path(path)
    path = path.joinpath(*args)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_least_fitness_params(data, fitnum= None):
    """ fitnum == None -> return last item least fitness parameters list.
        fitnum == integer -> return fitnum item from data(npz object).
    """
    row = fitnum if fitnum else np.argmin(data['fitvals'][:,-1])
    return (row, np.dstack((data['params'][row],data['paramnames']))[0])

def get_conds_non_conds(param_data_list):
    "Function to structure a dictonary and filter conds and non_conds parameters for npz file."
    non_conds = {item[1]:item[0] for item in param_data_list if not item[1].startswith('Cond_')}
    conds = {item[1]:item[0] for item in param_data_list if item[1].startswith('Cond_')}
    return(conds, non_conds)

def get_cond_file_abs_path(model_path, cond_file):
    "Function to resolve correct path to cond_file path for the system."
    if (model_path/cond_file).is_file():
        return str(model_path/cond_file)
    elif (model_path/'conductance_save'/cond_file).is_file():
        return str(model_path/'conductance_save'/cond_file)
    else:
        raise ValueError("Cond_file NOT FOUND in MODEL PATH and CONDUCTANCE_SAVE directories!!!")

def check_key_in_npz_data(npz_data, key):
    if key in npz_data.files:
         return True
    # I want to show key is not present in npz file
    logger.error("No KEY {} in optimization npz data load!!!".format(key))
    return False

def make_cond_file_name(npz_data, npz_file_name, neuron_type):
    "Makes new cond file name from npz data"
    logger.debug("{} {} {}".format(npz_data, npz_file_name, neuron_type))
    if check_key_in_npz_data(npz_data,'neuron_type') \
    and check_key_in_npz_data(npz_data,'measurment_name'):
       if npz_data['neuron_type'] in npz_data['measurment_name']:
           return 'param_cond_'+ npz_data['measurment_name'] + '.py'
       return 'param_cond_' + npz_data['measurment_name'] + npz_data['neuron_type'] + '.py'
    return npz_file_name.rpartition('-' + neuron_type + '-')[2].rstrip('.npz') + '.py'
