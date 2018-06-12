"""
@description : Fuctions to adjust channel kinectics like Time constants,
               Half actitavtion voltage.
"""
# TODO TESTING add logger statements in everybranch.
# TODO test the code.
import logging
from ajustador.helpers.loggingsystem import getlogger
from moose_nerp.prototypes.cha_proto import AlphaBetaChannelParams
from moose_nerp.prototypes.cha_proto import StandardMooseTauInfChannelParams
from moose_nerp.prototypes.cha_proto import TauInfMinChannelParams
from moose_nerp.prototypes.cha_proto import SSTauQuadraticChannelParams
from moose_nerp.prototypes.cha_proto import ZChannelParams
from moose_nerp.prototypes.cha_proto import BKChannelParams

logger = getlogger(__name__)
logger.setLevel(logging.DEBUG)

def chan_setting(s):
    "'NaF, vshift, X=123.4' → ('NaF', 'vshift', 'X', 123.4)"
    logger.debug("logger in chan_settings!!!")
    lhs, rhs = s.split('=', 1)
    rhs = float(rhs)
    chan, opt, gate= lhs.split(',', 2)
    return chan, opt, gate, rhs

def scale_xy_gate_taumul(gate_params_set, value):
    # TODO verify for each type and compute respectively for parameters.
        if isinstance(gate_params_set, AlphaBetaChannelParams):
            gate_params_set.
        elif isinstance(gate_params_set, StandardMooseTauInfChannelParams):
            gate_params_set.
        elif isinstance(gate_params_set, TauInfMinChannelParams):
            gate_params_set.
        elif isinstance(gate_params_set, SSTauQuadraticChannelParams):
            gate_params_set.

def offset_xy_gate_vshift(gate_params_set, value):
    # TODO verify for each type and compute respectively for parameters.
        if isinstance(gate_params_set, AlphaBetaChannelParams):
            gate_params_set.A_vhalf
        elif isinstance(gate_params_set, StandardMooseTauInfChannelParams):
            gate_params_set.A_vhalf
        elif isinstance(gate_params_set, TauInfMinChannelParams):
            gate_params_set.A_vhalf
        elif isinstance(gate_params_set, SSTauQuadraticChannelParams):
            gate_params_set.A_vhalf

def scale_z_gate_taumul(gate_params_set, value):
    # TODO Add functionality
    pass

def offset_z_gate_vshift(gate_params_set, value):
    # TODO Add functionality
    pass

def scale_voltage_dependents_tau_muliplier(chanset, chan_name, gate, value):
    ''' Scales the HH-channel model volatge dependents parametes with a factor
        which controls the time constants of the channel implicitly.
    '''
    if gate in ('X','Y'):
       specific_chan_set = getattr(chanset, chan_name)
       specific_chan_gate = getattr(specific_chan_set, gate)
       scale_xy_gate_taumul(specific_chan_gate, value)
       return
    elif gate is 'Z':
       # Zgate is special
       specific_chan_set = getattr(chanset, chan_name)
       specific_chan_gate = getattr(specific_chan_set, gate)
       scale_z_gate_taumul(gate_params_set, value)
       return
    elif gate is ':':
       scale_voltage_dependents_tau_muliplier(chanset, chan_name, gate='X', value)
       scale_voltage_dependents_tau_muliplier(chanset, chan_name, gate='Y', value)
       scale_voltage_dependents_tau_muliplier(chanset, chan_name, gate='Z', value)
       return

def offset_voltage_dependents_vshift(chanset, chan_name, gate, value):
    ''' Offsets the HH-channel model volatge dependents parametes with vshift.
    '''
    if gate in ('X','Y'):
       specific_chan_set = getattr(chanset, chan_name)
       specific_chan_gate = getattr(specific_chan_set, gate)
       offset_xy_gate_vshift(specific_chan_gate, value)
       return
    elif gate is 'Z':
       # Zgate is special
       specific_chan_set = getattr(chanset, chan_name)
       specific_chan_gate = getattr(specific_chan_set, gate)
       offset_z_gate_vshift(gate_params_set, value)
       return
    elif gate is ':':
       offset_voltage_dependents_vshift(chanset, chan_name, gate='X', value)
       offset_voltage_dependents_vshift(chanset, chan_name, gate='Y', value)
       offset_voltage_dependents_vshift(chanset, chan_name, gate='Z', value)
       return
