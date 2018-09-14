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

class CondRegexPatterns(object):
     """ Conductance identification and processing regex patterns used
        by state machine.
        **Note: Facilitates gp, d1d2, ca1, ep and squid. New models should be of same structure
          as any of the provided model, and new models place_holders should be updated.
     """
     NEURON_UTIL_NAMEDDICT = r"\s*_([a-zA-Z0-9]+)\s*=\s*_util.NamedDict\("
     PARAMETERS = {'gp': r"\s*([a-zA-Z0-9]+)\s*=\s*\{\s*prox\s*:\s*[0-9\.\*a-zA-Z]+,\s*dist\s*:\s*[0-9\.\*a-zA-Z]+\s*,\s*axon\s*:\s*[0-9\.\*a-zA-Z]+}",
                   'd1d2': r"\s*([a-zA-Z0-9]+)\s*=\s*\{\s*prox\s*:\s*[0-9\.\*a-zA-Z]+,\s*med\s*:\s*[0-9\.\*a-zA-Z]+\s*,\s*dist\s*:\s*[0-9\.\*a-zA-Z]+}",
                   'ca1' : r"\s*([a-zA-Z0-9]+)\s*=\s*\{\s*inclu\s*:\s*[0-9\.\*a-zA-Z]+",
                   'ep'  : r"\s*([a-zA-Z0-9]+)\s*=\s*\{\s*prox\s*:\s*[0-9\.\*a-zA-Z]+,\s*dist\s*:\s*[0-9\.\*a-zA-Z]+\s*,\s*axon\s*:\s*[0-9\.\*a-zA-Z]+}",
                   'squid' : r"\s*([a-zA-Z0-9]+)\s*=\s*\{\s*prox\s*:\s*[0-9\.\*a-zA-Z]+,\s*dist\s*:\s*[0-9\.\*a-zA-Z]+\s*"}

     BLOCK_END = r"\)"
     RE_STRIPS = {'gp' : {'0' : r"prox\s*:\s*[0-9\.]+", '1' : r"dist\s*:\s*[0-9\.]+", '2' : r"axon\s*:\s*[0-9\.]+"},
                  'd1d2' : {'0' : r"prox\s*:\s*[0-9\.]+", '1' : r"med\s*:\s*[0-9\.]+", '2' : r"dist\s*:\s*[0-9\.]+"},
                  'ca1' : {'0' : r"inclu\s*:\s*[0-9\.]+"},
                  'ep' : {'0' : r"prox\s*:\s*[0-9\.]+", '1' : r"dist\s*:\s*[0-9\.]+", '2' : r"axon\s*:\s*[0-9\.]+"},
                  'squid': {'0' : r"prox\s*:\s*[0-9\.]+", '1' : r"dist\s*:\s*[0-9\.]+", '2' : r"axon\s*:\s*[0-9\.]+"}}

     @classmethod
     def get_parameter(cls, model):
         return cls.PARAMETERS.get(model.lower())

class CondPlaceHolders(object):
      """ Regex place holders to substitue the parameter values used by state
          machine.
          **Note: Facilitates gp, d1d2, ca1, ep and squid. New models should be of same structure
          as any of the provided model, and new models place_holders should be updated.
      """
      replace_holders = {'gp': {'0' : "prox : {}", '1' : "dist : {}", '2' : "axon : {}"},
                         'd1d2': {'0' : "prox : {}", '1' : "med : {}", '2' : "dist : {}"},
                         'ca1' : {'0' : "inclu: {}"},
                         'ep' : {'0' : "prox : {}", '1' : "dist : {}", '2' : "axon : {}"},
                         'squid': {'0' : "prox : {}", '1' : "dist : {}", '2' : "axon : {}"}}
      @classmethod
      def get_replace_holders(cls, model):
          return cls.replace_holders.get(model.lower())

class ReObjects(object):
    """ Regex objects store used by state machine.
    """
    re_obj_util_nameddict = re.compile(CondRegexPatterns.NEURON_UTIL_NAMEDDICT, re.I)
    re_obj_block_end = re.compile(CondRegexPatterns.BLOCK_END, re.I)

    @classmethod
    def get_re_obj_re_strips(cls, model):
        return {key: re.compile(pattern) for key, pattern in CondRegexPatterns.RE_STRIPS.get(model.lower()).items()}

    @classmethod
    def get_re_obj_parameter(self, model):
        return re.compile(CondRegexPatterns.get_parameter(model.lower()), re.I)

def get_state_machine(model, neuron_type, conds):
    " Builder method to generate state machine."
    from ajustador.helpers.copy_param.process_param_cond_states import build_state_machine
    logger.debug("model {} neuron_type: {} conds: {}".format(model, neuron_type, conds))
    machine = build_state_machine(neuron_type, conds,
                                  ReObjects.get_re_obj_re_strips(model),
                                  CondPlaceHolders.get_replace_holders(model),
                                  ReObjects.get_re_obj_parameter(model),
                                  ReObjects.re_obj_util_nameddict)
    return machine

def process_cond_line(line, machine):
    " Process a single line on state machine passed as input along with the line."
    machine.run(line)
    return

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

def exercise_machine_on_cond(machine, cond_file_path, header_line):
    with fileinput.input(files=(cond_file_path), inplace=True) as f_obj:
       machine = machine
       header_not_written = True
       for line in f_obj:
           if header_not_written:
               sys.stdout.write(header_line)
               header_not_written = False
           process_cond_line(line, machine)
