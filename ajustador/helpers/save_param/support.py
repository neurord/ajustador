import logging
import fileinput
import re
import os
import shutil
import sys
import numpy as np
from pathlib import Path

from ajustador.helpers.loggingsystem import getlogger
from ajustador.helpers.save_param.process_morph import find_morph_file
from ajustador.helpers.save_param.process_morph import get_morph_file_name
from ajustador.helpers.save_param.process_param_cond import process_cond_line
from ajustador.helpers.save_param.process_morph import update_morph_file_name

logger = getlogger(__name__)
logger.setLevel(logging.DEBUG)

def create_path(path,*args):
    "Creates sub-directories recursively if they are not available"
    path = Path(path)
    path = path.joinpath(*args)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_least_fitness_params(data, fitnum= None):
    """ fitnum == None -> return last item least fitness parameters list.
        fitnum == integer -> return fitnum item from data(npz object).
    """
    row = fitnum if fitnum else np.argmin(data['fitvals'][:,-1])
    return (row, np.dstack((data['params'][row],data['paramnames']))[0])

def get_conds_non_conds(param_data_list):
    "Function to structure a dictonary and filter conds and non_conds parameters for npz file."
    non_conds = {item[1]:item[0] for item in param_data_list if not item[1].startswith('Cond_')}
    conds = {item[1]:item[0] for item in param_data_list if item[1].startswith('Cond_')}
    return(conds, non_conds)

def get_file_abs_path(model_path, file_):
    "Function to resolve correct path to cond_file and *.p path for the system."
    if (model_path/file_).is_file():
        return str(model_path/file_)
    elif (model_path/'conductance_save'/file_).is_file():
        return str(model_path/'conductance_save'/file_)
    else:
        raise ValueError("file {} NOT FOUND in MODEL PATH and CONDUCTANCE_SAVE directories!!!".format(file_))

def check_key_in_npz_data(npz_data, key):
    if key in npz_data.files:
         return True
    logger.error("No KEY {} in optimization npz data load!!!".format(key))
    return False

def make_cond_file_name(npz_data, npz_file_name, dest_path, neuron_type, cond_file):
    "Makes new cond file name from npz data"
    logger.debug("{} {} {} {}".format(npz_data, npz_file_name, dest_path, neuron_type))
    if check_key_in_npz_data(npz_data,'neuron_type') \
    and check_key_in_npz_data(npz_data,'measurment_name'): # may be removed in future.
       if npz_data['neuron_type'] in npz_data['measurment_name']:
           file_name = cond_file.rstrip('.py') + '_' + npz_data['measurment_name'] + '.py'
           logger.debug("1 {} {}".format(cond_file.strip('.py'), file_name))
           return os.path.join(dest_path, file_name)
       file_name = cond_file.rstrip('.py') + '_' + npz_data['measurment_name'] + npz_data['neuron_type'] + '.py'
       logger.debug("2 {} {}".format(cond_file.strip('.py'), file_name))
       return os.path.join(dest_path, file_name)
    file_name = cond_file.rstrip('.py') + '_' + npz_file_name.rpartition('-' + neuron_type + '-')[2].rstrip('.npz') + '.py'
    logger.debug("3 {} {}".format(cond_file.rstrip('.py'), file_name))
    return os.path.join(dest_path, file_name)

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

def extract_morph_file_from_cond(cond_file_path, neuron_type):
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
    src_abs_path = get_file_abs_path(src_path, src_file)
    if Path(dest_file).is_file(): # Creates a version file of destination file.
        dest_file = get_file_name_with_version(dest_file)
        shutil.copy(src_abs_path, dest_file)
        return dest_file
    shutil.copy(src_abs_path, dest_file)
    return dest_file

def clone_and_change_morph_file(param_cond_file, model_path, model, neuron_type, non_conds):
    ''' Inputs param_cond_file == string => Absolute path of cond_file.
               model_path == Path objects => model Path objects.
               model == string => model name.
               neuron_type == string => Neuron model.
    '''
    from ajustador.basic_simulation import morph_morph_file
    morph_features = ('RM', 'Eleak', 'RA', 'CM')
    model_obj = make_model_path_obj(model_path, model)
    morph_file = extract_morph_file_from_cond(param_cond_file, neuron_type)
    src_morph_file_path = get_file_abs_path(model_path, morph_file)
    if 'conductance_save' in src_morph_file_path:
        new_morph_file_path = get_file_name_with_version(src_morph_file_path)
        morph_morph_file(model_obj, neuron_type, src_morph_file_path, new_file = open(new_morph_file_path,'w'),
        **{k:v for k,v in non_conds.items() if k in morph_features})
        return new_morph_file_path
    morph_morph_file(model_obj, neuron_type, src_morph_file_path, new_file = open(str(model_path/'conductance_save'/morph_file),'w'),
    **{k:v for k,v in non_conds.items() if k in morph_features})
    return str(model_path/'conductance_save'/morph_file)
