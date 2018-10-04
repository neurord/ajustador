"""
@Description: Generic function used for processing npz files and fit objects to
              generate conductance parameter save file.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 6th Apr, 2018.
"""

import re
import logging

from pathlib import Path

from ajustador.helpers.loggingsystem import getlogger
from ajustador.helpers.copy_param.process_param_cond import clone_param_cond_file
from ajustador.helpers.copy_param.process_morph import clone_and_change_morph_file
from ajustador.helpers.copy_param.process_param_cond import update_morph_file_name_in_cond

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

def create_path(path,*args):
    "Creates sub-directories recursively if they are not available"
    path = Path(path)
    path = path.joinpath(*args)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_file_abs_path(model_path, file_):
    "Function to resolve correct path to cond_file and *.p path for the system."
    if (model_path/file_).is_file():
        return str(model_path/file_)
    elif (model_path/'conductance_save'/file_).is_file():
        return str(model_path/'conductance_save'/file_)
    else:
        raise ValueError("file {} NOT FOUND in MODEL PATH and CONDUCTANCE_SAVE directories!!!".format(file_))

def get_file_name_with_version(file_):
    file_ = str(file_)
    if file_.endswith('.py'):
        py_ = r'_V(\d+).py$'
        if re.search(py_, file_):
           v_num = int(re.search(py_, file_).group(1)) + 1
           return re.sub(py_, '_V{}.py'.format(v_num), file_)
        return re.sub(r'.py$', '_V1.py', file_)
    p_ = r'_V\d+.p$'
    if re.search(p_, file_):
       v_num = int(re.search(p_, file_).group(1)) + 1
       return re.sub(p_, '_V{}.p'.format(v_num), file_)
    return re.sub(r'.p$', '_V1.p', file_)

def check_version_build_file_path(file_, neuron_type, fit_number):
    abs_file_name, _, extn = file_.rpartition('.')
    if re.search('_V\d*$', abs_file_name):
        post_fix = re.search('_(V\d*)$', abs_file_name).group(1)
        abs_file_name = abs_file_name.strip('_'+ post_fix)
        return '_'.join([abs_file_name, neuron_type, str(fit_number), post_fix]) + _ + extn
    return '_'.join([abs_file_name, neuron_type, str(fit_number)]) + _ + extn

def make_model_path_obj(model_path, model):
    Object = lambda **kwargs: type("Object", (), kwargs)
    return Object(__file__ = str(model_path), value = model)
