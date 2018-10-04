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

from ajustador.helpers.copy_param.process_param_cond import clone_param_cond_file
from ajustador.helpers.copy_param.process_param_cond import update_morph_file_name_in_cond

from ajustador.helpers.copy_param.process_npz import get_least_fitness_params
from ajustador.helpers.copy_param.process_npz import make_cond_file_name
from ajustador.helpers.copy_param.process_npz import get_conds_non_conds

from ajustador.helpers.copy_param.process_morph import clone_and_change_morph_file

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

def write_header(header_line, new_param_cond):
    header_not_written = True
    with fileinput.input(files=(new_param_cond), inplace=True) as f_obj:
        for line in f_obj:
            if header_not_written:
                sys.stdout.write(header_line)
                header_not_written = False
            sys.stdout.write(line)

def get_condutace_block_start(new_param_cond, neuron_type):
    c_line_pattern = '.*=\s*_util.NamedDict\(.*$'
    n_line_pattern = '^\s*\'{}\'\s*,\s*$'.format(neuron_type)
    #print(c_line_pattern, n_line_pattern)
    with fileinput.input(files=(new_param_cond)) as f_obj:
        c_line = next(f_obj)
        test_block_comment(c_line)
        for n_line in f_obj:
            if test_block_comment(n_line):
                c_line = n_line
                continue
            if test_line_comment(n_line):
                c_line = n_line
                continue
            if re.search(c_line_pattern, c_line) and re.match(n_line_pattern, n_line):
                return f_obj.lineno()
            c_line = n_line

def get_conductance_block_end(new_param_cond, start_block_line_no):
    block_end_pattern = r"\)"
    with fileinput.input(files=(new_param_cond)) as f_obj:
        for line in f_obj:
            if f_obj.lineno() <= start_block_line_no:
                continue
            if test_line_comment(line):
                continue
            if re.search(block_end_pattern, line):
                return f_obj.lineno()

def update_conductance_param(new_param_cond, conds, start_block_lineno, end_block_lineno):
    with fileinput.input(files=(new_param_cond), inplace=True) as f_obj:
        for line in f_obj:
            if start_block_lineno < f_obj.lineno() < end_block_lineno:
                if re.search("(?P<chan>\w+)\s*=\s*{([\sa-zA-Z0-9\.:,\*]+)", line):
                    chan = re.search("(?P<chan>\w+)\s*=\s*{([\sa-zA-Z0-9\.:,\*]+)", line).group('chan')
                    chunks = re.split("([\sa-zA-Z0-9\.:,\*]+)", line)
                    logger.debug('{} {}'.format(chunks, len(chunks)))
                    for index, chunk in iter(enumerate(chunks)):
                        mod = get_modified_sub_string(chunk, chan, conds)
                        chunks[index] = mod
                    line = ''.join(chunks)
            sys.stdout.write(line)

def get_modified_sub_string(sub_str, chan, conds):
    if re.match("[\sa-z-Z0-9\.:,]+", sub_str) and ':' in sub_str:
        fragments = re.split('(\d+\.?\d*)', sub_str)
        item = conds.get(chan)
        if isinstance(item, dict):
            for key, val in item.items():
                logger.debug('{} {}'.format(fragments, len(fragments)))
                logger.debug('key: {}, value:{}'.format(key, val))
                try:
                    fragments[int(1+2*int(key))] = str(val)
                except IndexError:
                    pass
            return ''.join(fragments)
        elif item is None:
            return sub_str
        else:
            logger.debug("Non_dict {} {}".format(fragments, len(fragments)))
            vals = [item] * (len(fragments) // 2)
            for key, val in enumerate(vals):
                try:
                    fragments[int(1+2*int(key))] = str(val)
                except IndexError:
                    pass
            return ''.join(fragments)
    return sub_str

def reshape_conds_to_dict(conds):
    """ Re structure conductance."""
    conds_dict = defaultdict(dict)
    for key, value in conds.items():
        if key.count('_') == 1:
           conds_dict[key.split('_')[1]] = value
        elif key.count('_') == 2:
             if not isinstance(conds_dict[key.split('_')[1]], defaultdict):
                conds_dict[key.split('_')[1]] = defaultdict(dict)
             conds_dict[key.split('_')[1]][key.split('_')[2]] = value
    return conds_dict

flag_in_block_comment = False
def test_block_comment(line):
    global flag_in_block_comment
    if re.match("^\s*'''.*$", line):
            flag_in_block_comment = not(flag_in_block_comment)
    return flag_in_block_comment

def test_line_comment(line):
    return True if re.match('^\s*#.*$', line) else False

def create_npz_param(npz_file, model, neuron_type, store_param_path=None,
                     fitnum=None, cond_file= None):
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
    conds, non_conds = get_conds_non_conds(param_data_list)

    # Create new path to save param_cond.py and *.p
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
    #NOTE: created param_cond.py file in conductance_save directory of moose_nerp squid model.
    #NOTE: created and updated morph file.

    logger.info("START STEP 5!!! Renaming morph file after checking version.")
    new_morph_file_name = check_version_build_file_path(morph_file, neuron_type, fit_number)
    Path(str(new_param_path/morph_file)).rename(str(new_morph_file_name))

    logger.info("START Processing param cond file.")
    logger.info("START STEP 6!!! Renaming morph file after checking version.")
    update_morph_file_name_in_cond(new_cond_file_name, neuron_type, new_morph_file_name.rpartition('/')[2])

    write_header(header_line, new_param_cond)
    start_param_cond_block = get_condutace_block_start(new_param_cond, neuron_type)
    end_param_cond_block = get_conductance_block_end(new_param_cond, start_param_cond_block)
    conds_dict = reshape_conds_to_dict(conds)
    update_conductance_param(new_param_cond, conds_dict, start_param_cond_block, end_param_cond_block)

    logger.info("STEP 7!!! New files names \n morph: {1} \n param_cond files: {0}".format(new_cond_file_name, new_morph_file_name))
