"""
@description : Fuctions to adjust channel kinectics like Time constants,
               Half actitavtion voltage.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 20th JUN, 2018.
"""

# TODO test the code.
import logging
from ajustador.helpers.loggingsystem import getlogger
from moose_nerp.prototypes.chan_proto import AlphaBetaChannelParams
from moose_nerp.prototypes.chan_proto import StandardMooseTauInfChannelParams
from moose_nerp.prototypes.chan_proto import TauInfMinChannelParams
from moose_nerp.prototypes.chan_proto import ZChannelParams
from moose_nerp.prototypes.chan_proto import BKChannelParams # Not used

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
    # TODO TEST
        if isinstance(gate_params_set, AlphaBetaChannelParams):
            # TODO Test
            logger.debug("logger processing taumul for AlphaBetaChannelParams!!!")
            gate_params_set.A_rate *= value
            gate_params_set.A_B *= value
            gate_params_set.B_rate *= value
            gate_params_set.B_B *= value
            return
        elif isinstance(gate_params_set, StandardMooseTauInfChannelParams): # Can be merged with above branch after testing.
            # TODO Test
            logger.debug("logger processing taumul for StandardMooseTauInfChannelParams!!!")
            gate_params_set.T_rate *= value
            gate_params_set.T_B *= value
            gate_params_set.SS_rate *= value
            gate_params_set.SS_B *= value
            return
        elif isinstance(gate_params_set, TauInfMinChannelParams):
            # TODO TEST
            logger.debug("logger processing taumul for TauInfMinChannelParams!!!")
            gate_params_set.T_min *= value
            gate_params_set.T_vdep *= value
            pass

def offset_xy_gate_vshift(gate_params_set, value):
    # TODO TEST
        if isinstance(gate_params_set, AlphaBetaChannelParams):
            # TODO TEST
            logger.debug("logger processing vshift for AlphaBetaChannelParams!!!")
            gate_params_set.A_rate += value
            gate_params_set.A_vhalf += value
            gate_params_set.B_rate += value
            gate_params_set.B_vhalf += value
            return
        elif isinstance(gate_params_set, StandardMooseTauInfChannelParams):
            # TODO TEST
            logger.debug("logger processing vshift for StandardMooseTauInfChannelParams!!!")
            gate_params_set.T_rate += value
            gate_params_set.T_vhalf += value
            gate_params_set.T_rate += value
            gate_params_set.T_vhalf += value
            return
        elif isinstance(gate_params_set, TauInfMinChannelParams):
            # TODO TEST
            logger.debug("logger processing vshift for TauInfMinChannelParams!!!")
            gate_params_set.SS_vhalf += value
            gate_params_set.T_vhalf += value
            return

def scale_z_gate_taumul(gate_params_set, value):
    # TODO TEST
    logger.debug("logger processing taumul for z_gate!!!")
    if isinstance(gate_params_set, ZChannelParams): # Special case
       logger.debug("logger processing special case Z gate")
       gate_params_set.tau *= value
       gate_params_set.taumax *= value
    else:
       logger.debug("logger processing normal case Z gate")
       scale_xy_gate_taumul(gate_params_set, value) # Normal case
    return

def offset_z_gate_Ca_shift(gate_params_set, value):
    # TODO TEST
    logger.debug("logger processing offset for z_gate!!!")
    if isinstance(gate_params_set, ZChannelParams): # Special case
       logger.debug("logger processing special case Z gate")
       gate_params_set.Kd += value
    else:
       logger.debug("logger processing normal case Z gate")
       offset_xy_gate_vshift(gate_params_set, value) # Normal case
    return

def scale_voltage_dependents_tau_muliplier(chanset, chan_name, gate, value):
    ''' Scales the HH-channel model volatge dependents parametes with a factor
        which controls the time constants of the channel implicitly.
    '''
    # TODO TEST
    if gate is ':':
       for gate in ('X', 'Y', 'Z'):
           scale_voltage_dependents_tau_muliplier(chanset, chan_name, gate, value)
       return
    specific_chan_set = getattr(chanset, chan_name)
    specific_chan_gate = getattr(specific_chan_set, gate)
    if gate in ('X','Y'):
       scale_xy_gate_taumul(specific_chan_gate, value)
       return
    elif gate is 'Z':
       scale_z_gate_taumul(specific_chan_gate, value)
       return
    else:
       logger.info("Channel gate other than X, Y and Z!!!")
       return

def offset_voltage_dependents_vshift(chanset, chan_name, gate, value):
    ''' Offsets the HH-channel model volatge dependents parametes with vshift.
    '''
    # TODO TEST
    if gate is ':':
       for gate in ('X', 'Y', 'Z'):
           offset_voltage_dependents_vshift(chanset, chan_name, gate, value)
       return
    specific_chan_set = getattr(chanset, chan_name)
    specific_chan_gate = getattr(specific_chan_set, gate)
    if gate in ('X','Y'):
       offset_xy_gate_vshift(specific_chan_gate, value)
       return
    elif gate is 'Z':
       offset_z_gate_Ca_shift(specific_chan_gate, value)
       return
    else:
       logger.info("Channel gate other than X, Y and Z!!!")
       return
