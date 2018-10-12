'''
By using this model we canrun and execute new models with ease.
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

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

def reshape_conds_to_dict(conds):
    """ Re structure conductance."""
    conds_dict = defaultdict(dict)
    for key, value in conds.items():
        if key.count('_') == 1:
           chan_name = key.split('_')[1]
           conds_dict[chan_name] = value
        elif key.count('_') == 2:
            chan_name, distance_index = key.split('_')[1], key.split('_')[2]
            if not isinstance(conds_dict[chan_name], defaultdict):
                conds_dict[chan_name] = defaultdict(dict)
            conds_dict[chan_name][distance_index] = value
    return conds_dict

def reshape_chans_to_dict(conds):
    """ Re structure conductance."""
    chans_dict = defaultdict(dict)
    for key, value in conds.items():
        if key.count('_') == 2:
            chan_name, attribute = key.split('_')[1], key_split('_')[2]
            if not isinstance(conds_dict[chan_name], defaultdict):
                conds_dict[chan_name] = defaultdict(dict)
            conds_dict[chan_name][attribute] = value
        elif key.count('_') == 3:
             chan_name, attribute, gate = key.split('_')[1], key_split('_')[2], key_split('_')[3]
             if not isinstance(conds_dict[chan_name], defaultdict):
                conds_dict[chan_name] = defaultdict(dict)
             if not isinstance(conds_dict[chan_name], defaultdict):
                 conds_dict[chan_name][attribute] = defaultdict(dict)
             conds_dict[chan_name][attribute][gate] = value
    return conds_dict

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
    """

    model_path = Path(moose_nerp.__file__.rpartition('/')[0])/model

    logger.info("START STEP 1!!!\n loading npz file: {}.".format(npz_file))
    data = np.load(npz_file)

    logger.info("START STEP 2!!! Prepare param conductances.")
    fit_number, param_data_list = get_least_fitness_params(data, fitnum)
    header_line = "# Generated from npzfile: {} of fit number: {}\n".format(
                  npz_file.rpartition('/')[2], fit_number)

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
    morph_file = clone_and_change_morph_file(new_param_cond, model_path, model, neuron_type, non_conds)
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

    logger.info("STEP 7!!! New files names \n morph: {1} \n param_cond files: {0}".format(new_cond_file_name, new_morph_file_name))

    logger.info("STEP 8!!! start channel processing.")
    chans = get_params(param_data_list, 'Chan_')
    import pdb; pdb.set_trace()

    if chan_file is None:
        chan_file = 'param_chan.py'
    new_param_chan = make_new_file_name_from_npz(data, npz_file,
                         str(new_param_path), neuron_type, chan_file)
    new_chan_file_name = check_version_build_file_path(str(new_param_chan), neuron_type, fit_number)

    logger.info("START STEP 9!!! Copy \n source : {} \n dest: {}".format(get_file_abs_path(model_path,chan_file), new_chan_file_name))
    new_param_chan = clone_file(src_path=model_path, src_file=chan_file, dest_file=new_chan_file_name)

    write_header(header_line, new_param_chan)
    logger.info("START STEP 10!!! Preparing channel and gateparams relations.")
    start_param_chan_block = get_namedict_block_start(new_param_chan, 'Channels')
    end_param_chan_block = get_block_end(new_param_chan, start_param_chan_block, r"^(\s*\))")
    chans_dict = reshape_conds_to_dict(chans)
