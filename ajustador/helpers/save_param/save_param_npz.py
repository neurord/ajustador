import logging
import fileinput
import shutil
import numpy as np
import re
import sys
from pathlib import Path
from datetime import datetime
from ajustador.helpers.loggingsystem import getlogger
from ajustador.helpers.save.save_param.process_morph import find_morph_file
from ajustador.helpers.save.save_param.process_morph import get_morph_file_name
from ajustador.helpers.save.save_param.process_morph import process_morph_line
from ajustador.helpers.save.save_param.process_param_cond import get_state_machine
from ajustador.helpers.save.save_param.process_param_cond import process_cond_line

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

def load_npz(file_path):
    "Loads the single npz file into environment."
    logger.debug("Path: {}".format(file_path))
    return np.load(file_path)

def create_path(path,*args):
    "Creates sub-directories recursively if they are not available"
    path = Path(path)
    path = path.joinpath(*args)
    logger.debug("Path: {}".format(path))
    path.mkdir(parents=True)
    return path

def get_least_fitness_params(data): #need to discuss with professor.
    "Returns least fitness parameters list."
    logger.debug("{}".format(data['fitvals'].shape))
    logger.debug("{}".format(np.argmin(data['fitvals'], axis=0)))
    rows = np.argmin(data['fitvals'], axis=0)
    logger.debug("{}".format(data['fitvals'][np.argmin(data['fitvals'], axis=0)[-1],]))
    return [np.dstack((data['params'][row],data['paramnames'])) for row in rows]

def get_conds_non_conds(param_data_list):
    logger.debug("{}".format(param_data_list))
    conds = [(ele[1].split('_')[-2], ele[1].split('_')[-1], ele[0]) for item in param_data_list[-1] for ele in item if '_' in ele[1]]
    logger.debug("{}".format(conds))
    non_conds = [(ele[1].split('_')[-1].upper(), ele[0]) for item in param_data_list[-1] for ele in item if '_' not in ele[1]]
    non_conds = dict(non_conds)
    logger.debug("{}".format(non_conds))
    return(conds, non_conds)


def save_param_npz(npz_file, model, neuron_type, store_param_path, cond_file='param_cond.py'):
    import moose_nerp
    model_path = Path(moose_nerp.__file__.rpartition('/')[0])/model
    logger.info("START STEP 1!!!loading npz file.")
    data = load_npz(npz_file)
    logger.info("END STEP 1!!! loading npz file.")

    logger.info("START STEP 2!!! Prepare params for loaded npz.")
    param_data_list = get_least_fitness_params(data)
    conds, non_conds = get_conds_non_conds(param_data_list)
    logger.info("END STEP 2!!! Prepared params for loaded npz.")

    logger.info("START STEP 3!!! Copy file from respective prototye folder to new_param holding folder.")

    new_param_path = create_path(store_param_path, model, neuron_type)

    logger.debug("model_path {} new_path {}".format(model_path/cond_file, new_param_path))
    logger.debug("model_path type {} new_path type {}".format(type(model_path/cond_file), type(new_param_path)))
    shutil.copy(str(model_path/cond_file), str(new_param_path))
    logger.info("END STEP 3!!! Copy file from respective prototye folder to new_param holding folder.")

    logger.info("START STEP 4!!! Extract morph_file from param_cond.py file in the holding folder")
    with fileinput.input(files=(str(new_param_path/cond_file))) as f_obj:
       for line in f_obj:
           if find_morph_file(line):
               logger.debug("{}".format(find_morph_file(line)))
               logger.debug("{} {}".format(line, neuron_type))
               morph_file = get_morph_file_name(line, neuron_type)
               logger.debug("{}".format(morph_file))
               if morph_file is not None:
                  break
    logger.debug("morph_file: {}".format(morph_file))
    logger.info("END STEP 4!!! Extract the respective param_cond.py file in the holding folder")

    logger.info("START STEP 5!!! Modify the respective *.p file in the holding folder")
    shutil.copy(str(model_path/morph_file), str(new_param_path))
    with fileinput.input(files=(str(new_param_path/morph_file)), inplace=True) as f_obj:
       for line in f_obj:
           new_line = process_morph_line(line, non_conds)
           sys.stdout.write(new_line)
    logger.info("END STEP 5!!! Modify the respective *.p file in the holding folder")

    logger.info("START STEP 6!!! Modify the param_cond.py file in the holding folder")
    with fileinput.input(files=(str(new_param_path/cond_file)), inplace=True) as f_obj:
       machine = get_state_machine(neuron_type, conds)
       for line in f_obj:
           process_cond_line(line, machine)
    logger.info("END STEP 6!!! Modified the param_cond.py file in the holding folder")

