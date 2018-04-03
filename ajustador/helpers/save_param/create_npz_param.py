"""
@Description: Primary execution module to generate modified param_cond.py and
              morph_file.p based on the conductance parameters present in npz file.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 5th Mar, 2018.
"""

import logging
import numpy as np
from pathlib import Path
from ajustador.helpers.loggingsystem import getlogger
from ajustador.helpers.save_param.process_param_cond import get_state_machine
from ajustador.helpers.save_param.support import create_path
from ajustador.helpers.save_param.support import get_least_fitness_params
from ajustador.helpers.save_param.support import get_conds_non_conds
from ajustador.helpers.save_param.support import get_file_abs_path
from ajustador.helpers.save_param.support import make_cond_file_name
from ajustador.helpers.save_param.support import get_file_name_with_version
from ajustador.helpers.save_param.support import check_version_build_file_path
from ajustador.helpers.save_param.support import extract_morph_file_from_cond
from ajustador.helpers.save_param.support import make_model_path_obj
from ajustador.helpers.save_param.support import exercise_machine_on_cond
from ajustador.helpers.save_param.support import update_morph_file_name_in_cond
from ajustador.helpers.save_param.support import clone_param_cond_file
from ajustador.helpers.save_param.support import clone_and_change_morph_file

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

def create_npz_param(npz_file, model, neuron_type, store_param_path=None,
                     fitnum=None, cond_file= None):
    """Main function to be executed to generate parameter file from npz_file.
       Inputs => *.npz file; model can be 'gp', 'd1d2', 'ep' or 'ca1' soon;
                 neuron_type can be 'proto', 'D1' or 'D2' soon;
                 store_param_spath is user intended path to store neuron parameter files;
                 fitnum is user desired fitnumber to extract from npz file;
                 cond_file= Pure file name no path prefixes,
       Note** Program searches for cond_file in model folder and conductance_save in-order.
    """
    import moose_nerp
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
    if cond_file is None:
        cond_file = 'param_cond.py'
    new_param_cond = make_cond_file_name(data, npz_file,
                         str(new_param_path), neuron_type, cond_file)

    new_cond_file_name = check_version_build_file_path(str(new_param_cond), neuron_type, fit_number)
    logger.info("START STEP 3!!! Copy \n source : {} \n dest: {}".format(get_file_abs_path(model_path,cond_file), new_cond_file_name))
    new_param_cond = clone_param_cond_file(src_path=model_path, src_file=cond_file, dest_file=new_cond_file_name)

    logger.info("START STEP 4!!! Extract and modify morph_file from {}".format(new_param_cond))
    morph_file = clone_and_change_morph_file(new_param_cond, model_path, model, neuron_type, non_conds)
    logger.info("END STEP 4!!! Modified {} file in {}".format(morph_file, str(new_param_path)))

    logger.info("START STEP 6!!! Modify the param file {}".format(new_param_cond))
    machine = get_state_machine(model, neuron_type, conds)
    exercise_machine_on_cond(machine, new_param_cond, header_line)

    logger.info("START STEP 7!!! Renaming morph and param_cond files.")
    new_morph_file_name = check_version_build_file_path(morph_file, neuron_type, fit_number)
    Path(str(new_param_path/morph_file)).rename(str(new_morph_file_name))
    logger.info("END STEP 7!!! New files names \n morph: {1} \n param_cond files: {0}".format(new_cond_file_name, new_morph_file_name))

    logger.info("START STEP 8!!! Update the morph file name in cond_param file {}".format(new_cond_file_name))
    update_morph_file_name_in_cond(new_cond_file_name, neuron_type, new_morph_file_name.rpartition('/')[2])

    logger.info("!!!Environment cleanup!!!")
    del machine
    logger.info("!!!! CONDUCTANCE PARAMTER SAVE COMPLETED !!!!")
