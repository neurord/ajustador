"""
@Description: Sates and state machine to updated param_cond.py file based on the model
              and neuron_type.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 5th Mar, 2018.
"""

import logging
import re
from ajustador.helpers.loggingsystem import getlogger

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

class CondRegexPatterns(object):
     """ Conductance identification and processing regex patterns used
        by state machine.
     """
     NEURON_UTIL_NAMEDDICT = r"\s*_([a-zA-Z0-9]+)\s*=\s*_util.NamedDict\("
     PARAMETERS = {'gp': r"\s*([a-zA-Z0-9]+)\s*=\s*\{\s*prox\s*:\s*[0-9\.\*a-zA-Z]+,\s*dist\s*:\s*[0-9\.\*a-zA-Z]+\s*,\s*axon\s*:\s*[0-9\.\*a-zA-Z]+}",
                   'd1d2': r"\s*([a-zA-Z0-9]+)\s*=\s*\{\s*prox\s*:\s*[0-9\.\*a-zA-Z]+,\s*med\s*:\s*[0-9\.\*a-zA-Z]+\s*,\s*dist\s*:\s*[0-9\.\*a-zA-Z]+}",
                   'ca1' : r"\s*([a-zA-Z0-9]+)\s*=\s*\{\s*inclu\s*:\s*[0-9\.\*a-zA-Z]+",
                   'ep'  : r"\s*([a-zA-Z0-9]+)\s*=\s*\{\s*prox\s*:\s*[0-9\.\*a-zA-Z]+,\s*dist\s*:\s*[0-9\.\*a-zA-Z]+\s*,\s*axon\s*:\s*[0-9\.\*a-zA-Z]+}"}

     BLOCK_END = r"\)"
     RE_STRIPS = {'gp' : {'0' : r"prox\s*:\s*[0-9\.]+", '1' : r"dist\s*:\s*[0-9\.]+", '2' : r"axon\s*:\s*[0-9\.]+"},
                  'd1d2' : {'0' : r"prox\s*:\s*[0-9\.]+", '1' : r"med\s*:\s*[0-9\.]+", '2' : r"dist\s*:\s*[0-9\.]+"},
                  'ca1' : {'0' : r"inclu\s*:\s*[0-9\.]+"},
                  'ep' : {'0' : r"prox\s*:\s*[0-9\.]+", '1' : r"dist\s*:\s*[0-9\.]+", '2' : r"axon\s*:\s*[0-9\.]+"}}

     @classmethod
     def get_parameter(cls, model):
         return cls.PARAMETERS.get(model.lower())

class CondPlaceHolders(object):
      """ Regex place holders to substitue the parameter values used by state
          machine.
      """
      replace_holders = {'gp': {'0' : "prox : {}", '1' : "dist : {}", '2' : "axon : {}"},
                         'd1d2': {'0' : "prox : {}", '1' : "med : {}", '2' : "dist : {}"},
                         'ca1' : {'0' : "inclu: {}"},
                         'ep' : {'0' : "prox : {}", '1' : "dist : {}", '2' : "axon : {}"}}
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
    from ajustador.helpers.save_param.process_param_cond_states import build_state_machine
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
