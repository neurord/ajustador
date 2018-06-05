import logging
import fileinput
import shutil
import numpy as np
import re
import sys
from pathlib import Path
from datetime import datetime
from ajustador.helpers.loggingsystem import getlogger
from ajustador.helpers.save_param.process_common import process_modification
from ajustador.helpers.save_param.process_npz import get_conds_non_conds

def extract_model_details(data):
    model = data.pop()[0]
    neuron_type = data.pop()[0]
    morph_file = data.pop()[0]
    return (data, model, neuron_type, morph_file)

create_fit_param(fit_obj, model, neuron_type, store_param_path=None,
                     fitnum=None, cond_file=None):

    #Extract model parameters.
    data = [[str(item[1]).split('=')[1] , item[0]] for item in fit_obj.params.items()]
    param_data_list, model, neuron_type, morph_file  = extract_model_details(data)

    conds, non_conds = get_conds_non_conds(param_data_list)
    header_line = "# Generated from fit_obj\n"

    new_param_path = create_path(store_param_path) if store_param_path else create_path(model_path/'conductance_save')

    if cond_file is None:
        cond_file = 'param_cond.py'

    # npz_file??????????? fit_number?????????????
    # new_cond_file name while saving from fit_obj???.
    # We have a parameter called fit_number which determines the name of outputs
    # how to handle the output file_names???
    #(TODO) (Sri ram) Write new functiton to make cond_file for fit_object.
    new_param_cond = make_cond_file_name(data, npz_file,
                         str(new_param_path), neuron_type, cond_file)

    #(TODO) What should be the fit_number??
    process_modification(new_param_cond, model_path, new_param_path,
                         neuron_type, fit_number, cond_file, model,
                             conds, non_conds, header_line)

#How are the parameter values in fit_object?
