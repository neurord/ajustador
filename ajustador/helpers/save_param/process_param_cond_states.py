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
    RE_OBJ = ReObjects.re_obj_util_nameddict

    def __init__(self, neuron_type):
        self.neuron_type = neuron_type

    def run(self, line):
        logger.debug(" Logger in ModelCompare State!!!")
        match_obj = ModelCompare.RE_OBJ.search(line)
        if match_obj:
        	if match_obj.groups()[0] == self.neuron_type:
            		return(line, 'model', 'feature')
        return(line, 'model', 'write')


class FeatureCompare(State):
    RE_OBJ = ReObjects.re_obj_parameter
    def run(self, line):
        logger.debug(" Logger in FeatureCompare State!!!")
        match_obj = FeatureCompare.RE_OBJ.match(line)
        logger.debug("{}".format(match_obj))
        if match_obj:
            return(line, 'feature', 'changeline')
        return(line, 'feature', 'blockend')

class ChangeLine(State):
    RE_OBJ_COND_NAME = ReObjects.re_obj_parameter

    def __init__(self, conds, re_strip_objs, repl_strips):
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
        logger.debug("{}".format(self.conds))
        for pos, value in self.get_cond_values().items():
            obj = self.re_strip_objs.get(pos)
            logger.debug("{} {} {}".format(pos, obj, self.cond_name))
            new_line = obj.sub(self.repl_strips.get(pos).format(value), new_line)
        logger.debug("{}".format(new_line))
        return(new_line, 'changeline', 'write')

    def get_feature_name(self, line):
        return(ChangeLine.RE_OBJ_COND_NAME.match(line).groups()[0])

    def get_cond_values(self):
        logger.debug("!!!!!!!!!!!!{} {}".format(self.conds, self.cond_name))
        return(self.conds.get(self.cond_name))

    def generate_nested_dict(self, conds):
        self.conds = defaultdict(dict)
        for key1, key2, value in conds:
            self.conds[key1][key2] = value
        logger.debug("{}".format(self.conds)) 

class BlockEnd(State):
    RE_OBJ = ReObjects.re_obj_block_end
    def run(self, line):
        logger.debug(" Logger in BlockEnd State!!!")
        match_obj = BlockEnd.RE_OBJ.match(line)
        if match_obj:
            return(line, 'blockend', 'writeall')
        return(line, 'blockend', 'write')

class WriteOuput(State):
    def run(self, line, prev_state):
        logger.debug(" Logger in WriteOutput State!!!")
        sys.stdout.write(line)
        if prev_state == 'model':
           return(line, 'write', 'model')
        return(line, 'write', 'feature')

class WriteAll(State):
    def run(self, line):
        logger.debug("Logger in WriteAll state!!!")
        sys.stdout.write(line)
        return(line, 'writeall', 'writeall')

class CondParamMachine(object):
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

def build_state_machine(neuron_type, conds, re_strip_objs, repl_strips):
    state_space = { 'blockend': BlockEnd(),
                    'changeline': ChangeLine(conds, re_strip_objs, repl_strips),
                    'feature': FeatureCompare(),
                    'model': ModelCompare(neuron_type),
                    'write': WriteOuput(),
                    'writeall': WriteAll()
                   }
    return CondParamMachine(**state_space)
