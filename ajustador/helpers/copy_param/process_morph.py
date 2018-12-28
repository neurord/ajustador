"""
@Description: Functions and regex patterns to identifies and return morph_file
              name from param_cond.py.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 5th Mar, 2018.
"""
import re
import logging
import numpy as np

from ajustador.helpers.loggingsystem import getlogger

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

def find_morph_file(line):
    "Finds the 'morph_file =' is in the given input line"
    re_obj = re.compile(r"morph_file\s+=\s+\{", re.I)
    return True if re_obj.match(line) else False

def get_morph_file_name(line, neuron_type):
    "Get morph file name from the the line if it matches with pattern in re_obj."
    re_obj = re.compile(r"\s*'([a-zA-Z0-9]+)'\s*:\s*'([A-Z0-9.a-z_\-]+)'\s*", re.I)
    if re_obj.search(line):
        return dict(re_obj.findall(line)).get(neuron_type, None)
    return None

def update_morph_file_name(line, neuron_type, file_name):
    " Update morph file name into in param_cond.py file based on neuron type"
    pattern = r"\'{}\'\s*:\s*\'[0-9a-zA-Z\.\-_]+\'".format(neuron_type)
    repl = "'{}':'{}'".format(neuron_type, file_name)
    return re.sub(pattern, repl, line)

def clone_and_change_morph_file(param_cond_file, model_path, model, neuron_type, non_conds, sample_name=''):
    ''' Inputs param_cond_file == string => Absolute path of cond_file.
               model_path == Path objects => model Path objects.
               model == string => model name.
               neuron_type == string => Neuron model.
    '''
    from ajustador.basic_simulation import morph_morph_file
    from ajustador.helpers.copy_param.process_common import get_file_abs_path
    from ajustador.helpers.copy_param.process_common import get_file_name_with_version
    from ajustador.helpers.copy_param.process_common import make_model_path_obj
    from ajustador.helpers.copy_param.process_param_cond import extract_morph_file_from_cond
    morph_features = ('RM', 'Eleak', 'RA', 'CM')
    model_obj = make_model_path_obj(model_path, model)
    logger.debug("\n{} \n{}".format(param_cond_file, neuron_type))
    morph_file = extract_morph_file_from_cond(param_cond_file, neuron_type) #PROBLEM HERE.  NOT RETURNING CORRECT FILE FOR D2?
    logger.debug('\n{} \n{}'.format(model_path, morph_file))
    src_morph_file_path = get_file_abs_path(model_path, morph_file)
    if 'conductance_save' in src_morph_file_path:
        new_morph_file_path = get_file_name_with_version(src_morph_file_path)
        morph_morph_file(model_obj, neuron_type, src_morph_file_path, new_file = open(new_morph_file_path,'w'),
        **{k:v for k,v in non_conds.items() if k in morph_features})
        return new_morph_file_path
    new_morph_file_path = str(model_path/'conductance_save'/morph_file)[:-2]+'_'+sample_name+'.p'
    morph_morph_file(model_obj, neuron_type, src_morph_file_path, new_file = open(new_morph_file_path, 'w'),
    **{k:v for k,v in non_conds.items() if k in morph_features})
    return new_morph_file_path
