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
from ajustador.helpers.save_param.support import get_morph_file_abs_path
from ajustador.helpers.save_param.support import make_cond_file_name
from ajustador.helpers.save_param.support import get_file_name_with_version

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

def extract_morp_file_from_cond(cond_file_path, neuron_type):
    with fileinput.input(files=(cond_file_path)) as f_obj:
       for line in f_obj:
           if find_morph_file(line):
               return get_morph_file_name(line, neuron_type)

def make_model_path_obj(model_path, model):
    Object = lambda **kwargs: type("Object", (), kwargs)
    return Object(__file__ = str(model_path), value = model)

def exercise_machine_on_cond(machine, cond_file_path, header_line):
    with fileinput.input(files=(cond_file_path), inplace=True) as f_obj:
       machine = machine
       header_not_written = True
       for line in f_obj:
           if header_not_written:
               sys.stdout.write(header_line)
               header_not_written = False
           process_cond_line(line, machine)

def update_morph_file_name_in_cond(cond_file, neuron_type, morph_file_name):
    with fileinput.input(files=(cond_file), inplace=True) as f_obj:
         for line in f_obj:
           if find_morph_file(line):
              logger.debug("{}".format(morph_file_name))
              line = update_morph_file_name(line, neuron_type, morph_file_name)
              logger.debug("{}".format(line))
           sys.stdout.write(line)

def clone_param_cond_file(src_path, src_file, dest_file):
    ## Modify this function mechanics reliable.
    logger.info("{}\n {} \n {}".format(src_path, src_file, dest_file))
    src_abs_path = get_cond_file_abs_path(src_path, src_file)
    if Path(dest_file).is_file(): # Creates a version file of destination file.
        dest_file = get_file_name_with_version(dest_file)
        shutil.copy(src_abs_path, dest_file)
        return dest_file
    shutil.copy(src_abs_path, dest_file)
    logger.info("{}".format(dest_file))
    return dest_file

def clone_and_change_morph_file(param_cond_file, model_path, model, neuron_type):
    morph_file = extract_morp_file_from_cond(param_cond_file, neuron_type)
    morph_file_path = get_morph_file_abs_path(morph_file)
    model_obj = make_model_path_obj(model_path, model)
    from ajustador.basic_simulation import morph_morph_file
    morph_morph_file(model_obj, neuron_type, str(model_path/morph_file), new_file = open(str(new_param_path/morph_file),'w'),
                 **{k:v for k,v in non_conds.items() if k in morph_features})

def create_npz_param(npz_file, model, neuron_type, store_param_path=None,
                     fitnum=None, cond_file='param_cond.py'):
    """Main function to be executed to generate parameter file from npz_file.
       Inputs => *.npz file; model can be 'gp', 'd1d2', 'ep' or 'ca1' soon;
                 neuron_type can be 'proto', 'D1' or 'D2' soon;
                 store_param_spath is user intended path to store neuron parameter files;
                 fitnum is user desired fitnumber to extract from npz file;
                 cond_file= Pure file name no path prefixes,
       Note** Program searches for cond_file in model folder and conductance_save in-order.
    """
    import moose_nerp
    morph_features = ('RM', 'Eleak', 'RA', 'CM')
    model_path = Path(moose_nerp.__file__.rpartition('/')[0])/model

    logger.info("START STEP 1!!!\n loading npz file: {}.".format(npz_file))
    data = np.load(npz_file)

    logger.info("START STEP 2!!! Prepare params.")
    fit_number, param_data_list = get_least_fitness_params(data, fitnum)
    header_line = "# Generated from npzfile: {} of fit number: {}\n".format(
                  npz_file.rpartition('/')[2], fit_number)
    logger.debug("Param_data: {}".format(param_data_list))
    conds, non_conds = get_conds_non_conds(param_data_list)

    new_param_path = create_path(store_param_path) if store_param_path else create_path(model_path/'conductance_save')
    new_param_cond = make_cond_file_name(data, npz_file, str(new_param_path), neuron_type)

    # Move param_cond.py to conductance_save.
    #if not str(new_param_path) in get_cond_file_abs_path(model_path, cond_file): #check this logic!!!
    logger.info("START STEP 3!!! Copy \n source : {} \n dest: {}".format(get_cond_file_abs_path(model_path,cond_file), new_param_cond))
    new_param_cond = clone_param_cond_file(src_path=model_path, src_file=cond_file, dest_file=new_param_cond)

    logger.info("START STEP 4!!! Extract morph_file from param_cond.py file in the holding folder")
    morph_file = clone_and_change_morph_file(new_param_cond, model_path, model, neuron_type)
    logger.info("\n {}".format(morph_file))
    sys.exit()
    #morph_file = extract_morp_file_from_cond(new_param_cond, neuron_type)

    logger.info("START STEP 5!!! Modify the respective *.p file in {}".format(str(new_param_path)))
    #model_obj = make_model_path_obj(model_path, model)
    #from ajustador.basic_simulation import morph_morph_file
    #morph_morph_file(model_obj, neuron_type, str(model_path/morph_file), new_file = open(str(new_param_path/morph_file),'w'),
    #             **{k:v for k,v in non_conds.items() if k in morph_features})

    logger.info("START STEP 6!!! Modify the param file {}".format(new_param_cond))
    machine = get_state_machine(model, neuron_type, conds)
    exercise_machine_on_cond(machine, new_param_cond,
                             header_line)

    logger.info("START STEP 7!!! Renaming morph and param_cond files.")
    new_cond_file_name, _, extn = new_param_cond.rpartition('.') #new_param_cond change it !!!!
    new_cond_file_name = '_'.join([new_cond_file_name, neuron_type, str(fit_number)]) + _+ extn
    new_morp_file_name, _, extn =  morph_file.rpartition('.')
    new_morp_file_name = '_'.join([new_morp_file_name, neuron_type, str(fit_number)]) + _ + extn
    new_cond_file = new_param_path/new_cond_file_name
    new_morp_file = new_param_path/new_morp_file_name
    Path(str(new_param_path/new_param_cond)).rename(str(new_cond_file))
    Path(str(new_param_path/morph_file)).rename(str(new_morp_file))
    logger.info("END STEP 7!!! New files names \n morph: {1} \n param_cond files: {0}".format(new_cond_file, new_morp_file))
    logger.info("START STEP 8!!! Update the file name in cond_param file {}".format(new_cond_file))
    update_morph_file_name_in_cond(str(new_cond_file), neuron_type, new_morp_file_name)

    logger.info("!!!Environment cleanup!!!")
    del machine
    logger.info("!!!! CONDUCTANCE PARAMTER SAVE COMPLETED !!!!")
