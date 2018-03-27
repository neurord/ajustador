"""
@Description: Primary execution module to generate modified param_cond.py and
              morph_file.p based on the conductance parameters present in npz file.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 5th Mar, 2018.
"""

import logging
import fileinput
import shutil
import sys
import re
import numpy as np
from pathlib import Path
from ajustador.helpers.loggingsystem import getlogger
from ajustador.helpers.save_param.process_morph import find_morph_file
from ajustador.helpers.save_param.process_morph import get_morph_file_name
from ajustador.helpers.save_param.process_morph import update_morph_file_name
from ajustador.helpers.save_param.process_param_cond import get_state_machine
from ajustador.helpers.save_param.process_param_cond import process_cond_line
from ajustador.helpers.save_param.support import create_path
from ajustador.helpers.save_param.support import get_least_fitness_params
from ajustador.helpers.save_param.support import get_conds_non_conds
from ajustador.helpers.save_param.support import get_cond_file_abs_path

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

def create_npz_param(npz_file, model, neuron_type, store_param_path=None,
                     fitnum=None, cond_file='param_cond.py'):
    """Main function to be executed to generate parameter file from npz_file.
       Inputs => *.npz file; model can be 'gp', 'd1d2', 'ep' or 'ca1' soon;
                 neuron_type can be 'proto', 'D1' or 'D2' soon;
                 store_param_path is user intended path to store neuron parameter files;
                 fitnum is user desired fitnumber to extract from npz file;
                 cond_file= Pure file name no path prefixes,
       Note** Program searches for cond_file in model folder and conductance_save in-order.
    """
    import moose_nerp
    morph_features = ('RM', 'Eleak', 'RA', 'CM')
 
    model_path = Path(moose_nerp.__file__.rpartition('/')[0])/model
    logger.info("START STEP 1!!!loading npz file: {}.".format(npz_file))
    data = np.load(npz_file)

    logger.info("START STEP 2!!! Prepare params.")
    fit_number, param_data_list = get_least_fitness_params(data, fitnum)
    header_line = "# Generated from npzfile: {} of fit number: {}\n".format(
                  npz_file.rpartition('/')[2], fit_number)

    logger.debug("Param_data: {}".format(param_data_list))
    conds, non_conds = get_conds_non_conds(param_data_list)

    new_param_path = create_path(store_param_path) if store_param_path else create_path(model_path/'conductance_save')
    logger.info("START STEP 3!!! Copy {} file from {} to {} folder.".format(cond_file ,str(model_path), str(new_param_path)))
# Create a new cond_file name and assign it it cond_file

    if not str(new_param_path) in get_cond_file_abs_path(model_path,cond_file):
       shutil.copy(get_cond_file_abs_path(model_path,cond_file), str(new_param_path))  # Assign new_cond_name

    logger.info("START STEP 4!!! Extract morph_file from param_cond.py file in the holding folder")
    with fileinput.input(files=(str(new_param_path/cond_file))) as f_obj: #new_param_cond
       for line in f_obj:
           if find_morph_file(line):
               morph_file = get_morph_file_name(line, neuron_type)
               if morph_file is not None:
                  break

    logger.info("START STEP 5!!! Modify the respective *.p file in {}".format(str(new_param_path)))
    Object = lambda **kwargs: type("Object", (), kwargs)
    model_obj = Object(__file__ = str(model_path), value = model)

    from ajustador.basic_simulation import morph_morph_file

    morph_morph_file(model_obj, neuron_type, str(model_path/morph_file), new_file = open(str(new_param_path/morph_file),'w'),
                 **{k:v for k,v in non_conds.items() if k in morph_features})

    logger.info("START STEP 6!!! Modify the param_cond.py file in {}".format(str(new_param_path)))
    with fileinput.input(files=(str(new_param_path/cond_file)), inplace=True) as f_obj: #new_param_cond
       machine = get_state_machine(model_obj.value, neuron_type, conds)
       header_not_written = True
       for line in f_obj:
           if header_not_written:
               sys.stdout.write(header_line)
               header_not_written = False
           process_cond_line(line, machine)

    logger.info("START STEP 7!!! Renaming morph and param_cond files.")
    new_cond_file_name, _, extn = cond_file.rpartition('.') #new_param_cond
    new_cond_file_name = '_'.join([new_cond_file_name, neuron_type, str(fit_number)]) + _+ extn
    new_morp_file_name, _, extn =  morph_file.rpartition('.')
    new_morp_file_name = '_'.join([new_morp_file_name, neuron_type, str(fit_number)]) + _ + extn
    new_cond_file = new_param_path/new_cond_file_name
    new_morp_file = new_param_path/new_morp_file_name
    Path(str(new_param_path/cond_file)).rename(str(new_cond_file))
    Path(str(new_param_path/morph_file)).rename(str(new_morp_file))
    logger.info("END STEP 7!!! New file names morph and param_cond files are {} {}".format(new_cond_file, new_morp_file))
    logger.info("START STEP 8!!! Update the file name in cond_param file {}".format(new_cond_file))
    with fileinput.input(files=(str(new_cond_file)), inplace=True) as f_obj:
         for line in f_obj:
           if find_morph_file(line):
              logger.debug("{}".format(new_morp_file_name))
              line = update_morph_file_name(line, neuron_type, new_morp_file_name)
              logger.debug("{}".format(line))
           sys.stdout.write(line)

    logger.info("!!!Environment cleanup!!!")
    del machine
    logger.info("!!!! CONDUCTANCE PARAMTER SAVE COMPLETED !!!!")
