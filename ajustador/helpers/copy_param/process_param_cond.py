"""
@Description: Sates and state machine to updated param_cond.py file based on the model
              and neuron_type.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 5th Mar, 2018.
"""

import logging
import re
import sys
import shutil
import fileinput
from pathlib import Path
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

def clone_param_cond_file(src_path, src_file, dest_file):
    ''' Inputs param_cond_file == string => Absolute path of cond_file.
    model_path == Path objects => model Path objects.
    model == string => model name.
    neuron_type == string => Neuron model.
    '''
    from ajustador.helpers.copy_param.process_common import get_file_abs_path
    from ajustador.helpers.copy_param.process_common import get_file_name_with_version

    src_abs_path = get_file_abs_path(src_path, src_file)
    if Path(dest_file).is_file(): # Creates a version file of destination file.
        dest_file = get_file_name_with_version(dest_file)
        shutil.copy(src_abs_path, dest_file)
        return dest_file
    shutil.copy(src_abs_path, dest_file)
    return dest_file
