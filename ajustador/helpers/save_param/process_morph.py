import logging
import fileinput
import shutil
import numpy as np
import re
import sys
from pathlib import Path
from datetime import datetime
from ajustador.helpers.loggingsystem import getlogger

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

class MorphRegexPatterns(object):
    	SET_COMPT_PARAM = r"^\*set_compt_param\s*(?P<feature>[A-Z]+)\s+(?P<value>[\-.0-9]+)"
    	MORPH_FILE = r"morph_file\s+=\s+\{" #checks in param_cond
    	NEURON_P_FILE = r"\s*'([a-z]+)'\s*:\s*'([A-Z0-9.a-z_]+)'\s*" #use find all

class ReObjects(object):
     re_obj_morph_file = re.compile(MorphRegexPatterns.MORPH_FILE, re.I)
     re_obj_neuron_p_file = re.compile(MorphRegexPatterns.NEURON_P_FILE, re.I)
     re_obj_set_compt_param = re.compile(MorphRegexPatterns.SET_COMPT_PARAM,re.I)


def find_morph_file(line):
    "Finds the 'morph_file =' is in the given input line"
    return True if ReObjects.re_obj_morph_file.match(line) else False

def get_morph_file_name(line, neuron_type):
    "Get morph file name from the the line if it mathes with pattern in re_obj."
    re_obj = ReObjects.re_obj_neuron_p_file
    logger.debug("Found {} {}".format(re_obj.search(line), line))
    if re_obj.search(line):
        logger.debug("Found {}".format(re_obj.findall(line)))
        return dict(re_obj.findall(line)).get(neuron_type, None)
    return None

def process_morph_line(line, non_conds):
    "Modifies morph file values on line using the pattern in re_obj and input non_conds dictionary."
    re_obj = ReObjects.re_obj_set_compt_param
    if re_obj.match(line):
        logger.debug("Found {} {}".format(re_obj.match(line).groups(), re_obj.match(line).group('feature')))
        if non_conds.get(re_obj.match(line).group('feature'), None):
            new_line=line.replace(re_obj.match(line).group('value'), non_conds.get(re_obj.match(line).group('feature')))
            logger.debug("{}".format(new_line))
            line = new_line
    return line
