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

class CondRegexPatterns(object):
     NEURON_UTIL_NAMEDDICT = r"\s*_([a-z]+)\s*=\s*_util.NamedDict\("
     PARAMETER = r"\s*([a-zA-Z0-9]+)\s*=\s*\{\s*prox\s*:\s*[0-9\.]+,\s*dist\s*:\s*[0-9\.]+\s*,\s*axon\s*:\s*[0-9\.]+}"
     BLOCK_END = r"\)"
     RE_STRIPS = {'0' : r"prox\s*:\s*[0-9\.]+", '1' : r"dist\s*:\s*[0-9\.]+", '2' : r"axon\s*:\s*[0-9\.]+"}

class CondPlaceHolders(object):
      replace_holders = {'0' : "prox : {}", '1' : "dist : {}", '2' : "axon : {}"}

class ReObjects(object):
    re_obj_util_nameddict = re.compile(CondRegexPatterns.NEURON_UTIL_NAMEDDICT, re.I)
    re_obj_parameter = re.compile(CondRegexPatterns.PARAMETER, re.I)
    re_obj_block_end = re.compile(CondRegexPatterns.BLOCK_END, re.I)
    re_obj_re_strips = {key: re.compile(pattern) for key, pattern in CondRegexPatterns.RE_STRIPS.items()}

def get_state_machine(neuron_type, conds):
    from ajustador.helpers.save_param.process_param_cond_states import build_state_machine
    logger.debug(" neuron_type: {} conds: {}".format(neuron_type, conds))
    machine = build_state_machine(neuron_type, conds, ReObjects.re_obj_re_strips, CondPlaceHolders.replace_holders)
    return machine

def process_cond_line(line, machine):
    machine.run(line)
    return
