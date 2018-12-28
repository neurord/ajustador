# -*- coding: utf-8 -*-
'''
Create_npz_param can run and execute new models with ease.
'''

import logging
import numpy as np
import fileinput
import sys
import re
import moose_nerp
from pathlib import Path
from collections import defaultdict
from ajustador.helpers.loggingsystem import getlogger
from ajustador.helpers.copy_param.process_common import create_path
from ajustador.helpers.copy_param.process_common import check_version_build_file_path
from ajustador.helpers.copy_param.process_common import get_file_abs_path
from ajustador.helpers.copy_param.process_common import clone_file
from ajustador.helpers.copy_param.process_common import  write_header
from ajustador.helpers.copy_param.process_morph import clone_and_change_morph_file
from ajustador.helpers.copy_param.process_npz import get_least_fitness_params
from ajustador.helpers.copy_param.process_npz import make_new_file_name_from_npz
from ajustador.helpers.copy_param.process_npz import get_params
from ajustador.helpers.copy_param.process_param_cond import get_namedict_block_start
from ajustador.helpers.copy_param.process_param_cond import get_block_end
from ajustador.helpers.copy_param.process_param_cond import update_morph_file_name_in_cond
from ajustador.helpers.copy_param.process_param_cond import update_conductance_param
from ajustador.helpers.copy_param.process_param_cond import reshape_conds_to_dict
from ajustador.helpers.copy_param.process_param_chan import create_chan_param_relation
from ajustador.helpers.copy_param.process_param_chan import reshape_chans_to_dict
from ajustador.helpers.copy_param.process_param_chan import import_param_chan
from ajustador.helpers.copy_param.process_param_chan import update_chan_param
from ajustador.helpers.copy_param.process_param_chan import chan_param_locator
from ajustador.regulate_chan_kinetics import scale_voltage_dependents_tau_muliplier
from ajustador.regulate_chan_kinetics import offset_voltage_dependents_vshift

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

def create_npz_param(npz_file, model, neuron_type, store_param_path=None,
                     fitnum=None, cond_file= None, chan_file=None):
    """Main function to be executed to generate parameter file from npz_file.
       Inputs => npz_file          -> *.npz file;
                 model             -> 'gp', 'd1d2', 'ep' or 'ca1' soon;
                 neuron_type       -> 'proto', 'D1' or 'D2' soon;
                 store_param_spath -> User intended path to store neuron parameter files;
                 fitnum            -> user desired fitnumber to extract from npz file;
                 cond_file         -> Pure file name no path prefixes,
       Note** Program searches for cond_file in model folder and conductance_save in-order.
       Note** If *.p file in cond_file should be present in the same directory for proper execution.
       Note** Block comments in param_chan.py and param_cond.py must be of <'''>.
    """

    model_path = Path(moose_nerp.__file__.rpartition('/')[0])/model

    logger.info("START STEP 1!!!\n loading npz file: {}.".format(npz_file))
    data = np.load(npz_file)

    logger.info("START STEP 2!!! Prepare param conductances.")
    fit_number, param_data_list = get_least_fitness_params(data, fitnum)
    header_line = "# Generated from npzfile: {} of fit number: {}\n".format(
                  npz_file.rpartition('/')[2], fit_number)
    sample_label = npz_file.rpartition('/')[2].rstrip('.npz').split('_')[-1]

    logger.debug("Param_data: {}".format(param_data_list))
    conds = get_params(param_data_list, 'Cond_')
    non_conds = get_params(param_data_list, 'Cond_', exclude_flag=True)

    # Create new path to save param_cond.py and *.p
    new_param_path = create_path(store_param_path) if store_param_path else create_path(model_path/'conductance_save')

    if cond_file is None:
        cond_file = 'param_cond.py'
    new_param_cond = make_new_file_name_from_npz(data, npz_file,
                         str(new_param_path), neuron_type, cond_file)
    new_cond_file_name = check_version_build_file_path(str(new_param_cond), neuron_type, fit_number)
    logger.info("START STEP 3!!! Copy \n source : {} \n dest: {}".format(get_file_abs_path(model_path,cond_file), new_cond_file_name))
    new_param_cond = clone_file(src_path=model_path, src_file=cond_file, dest_file=new_cond_file_name)

    logger.info("START STEP 4!!! Extract and modify morph_file from {}".format(new_param_cond))
    morph_file = clone_and_change_morph_file(new_param_cond, model_path, model, neuron_type, non_conds, sample_label)
    #NOTE: created param_cond.py file in conductance_save directory of moose_nerp squid model.
    #NOTE: created and updated morph file.

    logger.info("START STEP 5!!! Renaming morph file after checking version.")
    new_morph_file_name = check_version_build_file_path(morph_file, neuron_type, fit_number)
    Path(str(new_param_path/morph_file)).rename(str(new_morph_file_name))

    logger.info("START STEP 6!!! Renaming morph file after checking version.")
    update_morph_file_name_in_cond(new_cond_file_name, neuron_type, new_morph_file_name.rpartition('/')[2])

    write_header(header_line, new_param_cond)
    start_param_cond_block = get_namedict_block_start(new_param_cond, neuron_type)
    end_param_cond_block = get_block_end(new_param_cond, start_param_cond_block, r"\)")
    conds_dict = reshape_conds_to_dict(conds)
    update_conductance_param(new_param_cond, conds_dict, start_param_cond_block, end_param_cond_block)

    logger.info("STEP 8!!! start channel processing.")
    chans = get_params(param_data_list, 'Chan_')
    logger.debug('{}'.format(chans))

    if chan_file is None:
        chan_file = 'param_chan.py'
    new_param_chan = make_new_file_name_from_npz(data, npz_file,
                         str(new_param_path), neuron_type, chan_file)
    new_chan_file_name = check_version_build_file_path(str(new_param_chan), neuron_type, fit_number)

    logger.info("START STEP 9!!! Copy \n source : {} \n dest: {}".format(get_file_abs_path(model_path,chan_file), new_chan_file_name))
    new_param_chan = clone_file(src_path=model_path, src_file=chan_file, dest_file=new_chan_file_name)

    logger.info("START STEP 10!!! Preparing channel and gateparams relations.")
    start_param_chan_block = get_namedict_block_start(new_param_chan, 'Channels')
    end_param_chan_block = get_block_end(new_param_chan, start_param_chan_block, r"^(\s*\))")
    chans_dict = reshape_chans_to_dict(chans)
    logger.info("START STEP 11!!! import parameters from param_chan.py. and apply scale Tau and delay SS")
    py_param_chan = import_param_chan(model) # import param_chan.py file from model.
    chanset = py_param_chan.Channels # Get Channels set from the imported param_chan.py.
    for key,value in chans_dict.items():
        chan_name, opt, gate = key
        if opt == 'taumul':
           scale_voltage_dependents_tau_muliplier(chanset, chan_name, gate, np.float(value))
        elif opt == 'vshift':
           offset_voltage_dependents_vshift(chanset, chan_name, gate, np.float(value))
    chan_param_name_relation = create_chan_param_relation(new_param_chan, start_param_chan_block, end_param_chan_block)
    param_location = chan_param_locator(new_param_chan, chan_param_name_relation)
    update_chan_param(new_param_chan, chan_param_name_relation, chanset, param_location) #Update new param_chan files with new channel params.
    write_header(header_line, new_param_chan) # Write header to the new param_chan.py
    logger.info("THE END!!! New files names \n morph: {1} \n param_cond file: {0} \n param_chan file: {2}".format(new_cond_file_name, new_morph_file_name, new_chan_file_name))
