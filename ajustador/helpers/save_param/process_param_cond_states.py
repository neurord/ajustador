"""
@Description: Sates and state machine to updated param_cond.py file based on the model
              and neuron_type.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 5th Mar, 2018.
"""

import logging
import sys
from collections import defaultdict
from ajustador.helpers.loggingsystem import getlogger
from ajustador.helpers.save_param.process_param_cond import ReObjects

logger = getlogger(__name__)
logger.setLevel(logging.INFO)

class State(object):
    "Interface class for the param_cond line states"
    def run(self, line):
        pass

class ModelCompare(State):
    """Model state to check the start of conductance parameter using regex compile
     object"""

    def __init__(self, neuron_type, re_obj):
        self.neuron_type = neuron_type
        self.re_obj = re_obj

    def run(self, line):
        logger.debug(" Logger in ModelCompare State!!!")
        match_obj = self.re_obj.search(line)
        if match_obj:
        	if match_obj.groups()[0] == self.neuron_type:
            		return(line, 'model', 'feature')
        return(line, 'model', 'write')

class FeatureCompare(State):
    """Feature state to check identify actual conductance parameter values using regex compile
     object"""

    def __init__(self, parameter_obj):  #DO changes to identify kluge
        self.parameter_obj = parameter_obj

    def run(self, line):
        logger.debug(" Logger in FeatureCompare State!!!")
        logger.debug("{}".format(line))
        match_obj = self.parameter_obj.match(line)
        logger.debug("{}".format(match_obj))
        if match_obj:
            return(line, 'feature', 'changeline')
        return(line, 'feature', 'blockend')

class ChangeLine(State):
    """Change line state to modify the parameter values inplace
       using regex compile object"""
    def __init__(self, conds, re_strip_objs, repl_strips, parameter_obj):
        self.parameter_obj = parameter_obj
        self.generate_nested_dict(conds)
        self.re_strip_objs = re_strip_objs
        logger.debug(" self.re_strip_objs: {}".format(self.re_strip_objs))
        self.repl_strips = repl_strips

    def run(self, line):
        logger.debug("{}".format(self.conds))
        logger.debug(" Logger in ChangeLine State!!!")
        new_line = line
        self.cond_name = self.get_feature_name(line)
        logger.debug("{}".format(self.cond_name))
        for pos, value in self.get_cond_values().items():
            obj = self.re_strip_objs.get(pos)
            logger.debug("{} {} {}".format(pos, obj, self.cond_name))
            new_line = obj.sub(self.repl_strips.get(pos).format(value), new_line)
        logger.debug("{}".format(new_line))
        return(new_line, 'changeline', 'write')

    def get_feature_name(self, line):
        """ Return conductance name fetched from line"""
        return(self.parameter_obj.match(line).groups()[0])

    def get_cond_values(self):
        "Function to structue condctance value based on the conductance."
        item = self.conds.get(self.cond_name)
        if isinstance(item, dict):
            return item
        return({str(i):item for i in range(len(self.re_strip_objs))})

    def generate_nested_dict(self, conds):
        """ Re structure conductance to consume the values with ease
          by change line state."""
        self.conds = defaultdict(dict)
        for key, value in conds.items():
            if key.count('_') == 1:
               self.conds[key.split('_')[1]] = value
            elif key.count('_') == 2:
                 if not isinstance(self.conds[key.split('_')[1]], defaultdict):
                    self.conds[key.split('_')[1]] = defaultdict(dict)
                 self.conds[key.split('_')[1]][key.split('_')[2]] = value

class BlockEnd(State):
    "Parameter set block end identification state."
    RE_OBJ = ReObjects.re_obj_block_end
    def run(self, line):
        logger.debug(" Logger in BlockEnd State!!!")
        match_obj = BlockEnd.RE_OBJ.match(line)
        if match_obj:
            return(line, 'blockend', 'writeall')
        return(line, 'blockend', 'write')

class WriteOuput(State):
    """ Write output state write a line to stdout inorder to write to a file.
        the state machine should be run internal to a fileoutput instance loop."""
    def run(self, line, prev_state):
        logger.debug(" Logger in WriteOutput State!!!")
        sys.stdout.write(line)
        if prev_state == 'model':
           return(line, 'write', 'model')
        return(line, 'write', 'feature')

class WriteAll(State):
    """ WriteAll State flushes a single line to the output stream
        and stay on the same state.
    """
    def run(self, line):
        logger.debug("Logger in WriteAll state!!!")
        sys.stdout.write(line)
        return(line, 'writeall', 'writeall')

class CondParamMachine(object):
    """State machine class with execution mechanics.
    """
    machine = None
    def __init__(self, **all_states):
        if CondParamMachine.machine == None:
            self.all_states = all_states
            self.prev = 'write'
            self.next = 'model'
            self.current_state = self.all_states.get(self.next)
            CondParamMachine.machine = self
        else:
           logger.info("State Machine is live please use CondParamMachine.machine!!!")

    def run(self, line):
        if self.next == 'model':
           self.current_state = self.all_states.get(self.next)
           self.line, self.prev, self.next = self.current_state.run(line)

        if self.next == 'write':  # Gets write state object.
           self.current_state = self.all_states.get(self.next)
           self.line, self.prev, self.next = self.current_state.run(line, self.prev)
           return

        if self.next == 'feature': # Gets feature state object.
           self.current_state = self.all_states.get(self.next)
           self.line, self.prev, self.next = self.current_state.run(line)

        if self.next == 'changeline': # Gets change state object.
           self.current_state = self.all_states.get(self.next)
           self.line, self.prev, self.next = self.current_state.run(line)

        if self.next == 'write':  # Gets write state object.
           self.current_state = self.all_states.get(self.next) # gets write state
           self.line, self.prev, self.next = self.current_state.run(self.line, self.prev)
           return

        if self.next == 'blockend': # gets blockend state object.
           self.current_state = self.all_states.get(self.next)
           self.line, self.prev, self.next = self.current_state.run(line)

        if self.next == 'write':  # Gets write state object.
           self.current_state = self.all_states.get(self.next)
           self.line, self.prev, self.next = self.current_state.run(self.line, self.prev)
           return

        if self.next == 'writeall':
           self.current_state = self.all_states.get(self.next)
           self.line, self.prev, self.next = self.current_state.run(line)
           self.current_state = self.all_states.get(self.next) # State writeall
           return

def build_state_machine(neuron_type, conds, re_strip_objs, repl_strips, parameter_obj, re_model_obj):
    """ State Machine factory method to construct state machine and link it with
        state objects"""
    state_space = { 'blockend': BlockEnd(),
                    'changeline': ChangeLine(conds, re_strip_objs, repl_strips, parameter_obj),
                    'feature': FeatureCompare(parameter_obj),
                    'model': ModelCompare(neuron_type, re_model_obj),
                    'write': WriteOuput(),
                    'writeall': WriteAll()
                   }
    return CondParamMachine(**state_space)
