"""
@Description: Functions and regex patterns to identifies and return morph_file
              name from param_cond.py.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 5th Mar, 2018.
"""

import numpy as np
import re
from ajustador.helpers.loggingsystem import getlogger

class MorphRegexPatterns(object):
     " Regex patterns to idenfiy the morph_file name in param_cond file."
     MORPH_FILE = r"morph_file\s+=\s+\{"
     NEURON_P_FILE = r"\s*'([a-zA-Z0-9]+)'\s*:\s*'([A-Z0-9.a-z_\-]+)'\s*"

class ReObjects(object):
     " Regex compile objects to discern morph and neuron file in param_cond.py"
     re_obj_morph_file = re.compile(MorphRegexPatterns.MORPH_FILE, re.I)
     re_obj_neuron_p_file = re.compile(MorphRegexPatterns.NEURON_P_FILE, re.I)

def find_morph_file(line):
    "Finds the 'morph_file =' is in the given input line"
    return True if ReObjects.re_obj_morph_file.match(line) else False

def get_morph_file_name(line, neuron_type):
    "Get morph file name from the the line if it mathes with pattern in re_obj."
    re_obj = ReObjects.re_obj_neuron_p_file
    if re_obj.search(line):
        return dict(re_obj.findall(line)).get(neuron_type, None)
    return None
