"""
@Description: Facilitator functions to read and modify param_cond.py file.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 5th Mar, 2018.
"""

import logging
import re
import sys
import fileinput
from pathlib import Path
from collections import defaultdict
from ajustador.helpers.loggingsystem import getlogger
from ajustador.helpers.copy_param.process_morph import find_morph_file
from ajustador.helpers.copy_param.process_morph import get_morph_file_name
from ajustador.helpers.copy_param.process_morph import update_morph_file_name

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

def extract_morph_file_from_cond(cond_file_path, neuron_type):
    with fileinput.input(files=(cond_file_path)) as f_obj:
       for line in f_obj:
           if find_morph_file(line):
               return get_morph_file_name(line, neuron_type)

def update_morph_file_name_in_cond(cond_file, neuron_type, morph_file_name):
    logger.debug("\n {}".format(cond_file))
    with fileinput.input(files=(cond_file), inplace=True) as f_obj:
         for line in f_obj:
           if find_morph_file(line):
              line = update_morph_file_name(line, neuron_type, morph_file_name)
           sys.stdout.write(line)

def get_namedict_block_start(file_in, dict_name):
    c_line_pattern = '.*=\s*(_util.)?NamedDict\(.*$'
    n_line_pattern = '^\s*\'{}\'\s*,\s*$'.format(dict_name)
    from ajustador.helpers.copy_param.process_common import test_block_comment
    from ajustador.helpers.copy_param.process_common import test_line_comment

    #print(c_line_pattern, n_line_pattern)
    with fileinput.input(files=(file_in)) as f_obj:
        c_line = next(f_obj)
        flag_in_block_comment=test_block_comment(c_line, flag_in_block_comment=False)
        for n_line in f_obj:
            flag_in_block_comment=test_block_comment(n_line, flag_in_block_comment)
            if flag_in_block_comment:
                c_line = n_line
                continue
            if test_line_comment(n_line):
                c_line = n_line
                continue
            if re.search(c_line_pattern, c_line) and re.match(n_line_pattern, n_line):
                return f_obj.lineno()
            c_line = n_line

def get_block_end(file_in, start_block_line_no, block_end_pattern):
    from ajustador.helpers.copy_param.process_common import test_line_comment
    with fileinput.input(files=(file_in)) as f_obj:
        for line in f_obj:
            if f_obj.lineno() <= start_block_line_no:
                continue
            if test_line_comment(line):
                continue
            if re.search(block_end_pattern, line):
                return f_obj.lineno()

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
