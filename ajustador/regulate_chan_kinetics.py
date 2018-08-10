"""
@description : Fuctions to adjust channel kinectics like Time constants,
               Half actitavtion voltage.
@Author: Sri Ram Sagar Kappagantula
@e-mail: skappag@masonlive.gmu.edu
@Date: 20th JUN, 2018.
"""

from ajustador.helpers.loggingsystem import getlogger
from moose_nerp.prototypes.chan_proto import AlphaBetaChannelParams
from moose_nerp.prototypes.chan_proto import StandardMooseTauInfChannelParams
from moose_nerp.prototypes.chan_proto import TauInfMinChannelParams
from moose_nerp.prototypes.chan_proto import ZChannelParams
from moose_nerp.prototypes.chan_proto import BKChannelParams # Not used

logger = getlogger(__name__)

def chan_setting(s):
    "'NaF, vshift, X=123.4' → ('NaF', 'vshift', 'X', 123.4)"
    lhs, rhs = s.split('=', 1)
    logger.debug("lhs =  {}".format(lhs))
    rhs = float(rhs)
    chan, opt, gate= lhs.split(',', 2)
    return chan, opt, gate, rhs

def scale_xy_gate_taumul(gate_params_set, value):
    # TODO Add doc string and comments.
        if isinstance(gate_params_set, AlphaBetaChannelParams):
            logger.debug("taumul for AlphaBetaChannelParams!!! before {}".format(gate_params_set))
            gate_params_set.A_rate *= value
            gate_params_set.A_B *= value
            gate_params_set.B_rate *= value
            gate_params_set.B_B *= value
            logger.debug("taumul for AlphaBetaChannelParams after {}".format(gate_params_set))
            return
        elif isinstance(gate_params_set, StandardMooseTauInfChannelParams): # Can be merged with above branch after testing.
            logger.debug("taumul for StandardMooseTauInfChannelParams before {}".format(gate_params_set))
            gate_params_set.T_rate *= value
            gate_params_set.T_B *= value
            gate_params_set.SS_rate *= value
            gate_params_set.SS_B *= value
            logger.debug("taumul for StandardMooseTauInfChannelParams after {}".format(gate_params_set))
            return
        elif isinstance(gate_params_set, TauInfMinChannelParams):
            logger.debug("logger processing taumul for TauInfMinChannelParams before {}".format(gate_params_set))
            gate_params_set.T_min *= value
            gate_params_set.T_vdep *= value
            logger.debug("logger processing taumul for TauInfMinChannelParams after {}".format(gate_params_set))
            return

def offset_xy_gate_vshift(gate_params_set, value):
    # TODO Add doc string and comments.
        if isinstance(gate_params_set, AlphaBetaChannelParams):
            logger.debug("vshift for AlphaBetaChannelParams before {}".format(gate_params_set))
            gate_params_set.A_rate += value
            gate_params_set.A_vhalf += value
            gate_params_set.B_rate += value
            gate_params_set.B_vhalf += value
            logger.debug("vshift for AlphaBetaChannelParams after {}".format(gate_params_set))
            return
        elif isinstance(gate_params_set, StandardMooseTauInfChannelParams):
            logger.debug("vshift for StandardMooseTauInfChannelParams before {}".format(gate_params_set))
            gate_params_set.T_rate += value
            gate_params_set.T_vhalf += value
            gate_params_set.T_rate += value
            gate_params_set.T_vhalf += value
            logger.debug("vshift for StandardMooseTauInfChannelParams after {}".format(gate_params_set))
            return
        elif isinstance(gate_params_set, TauInfMinChannelParams):
            logger.debug("vshift for TauInfMinChannelParams before {}".format(gate_params_set))
            gate_params_set.SS_vhalf += value
            gate_params_set.T_vhalf += value
            logger.debug("vshift for TauInfMinChannelParams after {}".format(gate_params_set))
            return

def scale_z_gate_taumul(gate_params_set, value):
    # TODO Add doc string and comments
    if isinstance(gate_params_set, ZChannelParams): # Special case
       logger.debug(" taumul special case Z gate before {}".format(gate_params_set))
       gate_params_set.tau *= value
       gate_params_set.taumax *= value
       logger.debug(" taumul special case Z gate after {}".format(gate_params_set))
    else:
       logger.debug("taumul normal case Z gate before {}".format(gate_params_set))
       scale_xy_gate_taumul(gate_params_set, value) # Normal case
       logger.debug("taumul normal case Z gate after {}".format(gate_params_set))
    return

def offset_z_gate_Ca_shift(gate_params_set, value):
    # TODO Add doc string and comments.
    if isinstance(gate_params_set, ZChannelParams): # Special case
       logger.debug("ca_shift special case Z gate before {}".format(gate_params_set))
       gate_params_set.Kd += value
       logger.debug("ca_shift special case Z gate after {}".format(gate_params_set))
    else:
       logger.debug("ca_shift normal case Z gate before {}".format(gate_params_set))
       offset_xy_gate_vshift(gate_params_set, value) # Normal case
       logger.debug("ca_shift normal case Z gate after {}".format(gate_params_set))
    return

def scale_voltage_dependents_tau_muliplier(chanset, chan_name, gate, value):
    ''' Scales the HH-channel model volatge dependents parametes with a factor
        which controls the time constants of the channel implicitly.
    '''
    logger.debug("Processing taumul on chan_name {} gate {}".format(chan_name, gate))
    if gate is ':':
       for gate in ('X', 'Y', 'Z'):
           scale_voltage_dependents_tau_muliplier(chanset, chan_name, gate, value)
       return
    specific_chan_set = getattr(chanset, chan_name)
    specific_chan_gate = getattr(specific_chan_set, gate)
    if gate in ('X','Y'):
       logger.debug("gate {}".format(gate))
       scale_xy_gate_taumul(specific_chan_gate, value)
       return
    elif gate is 'Z':
       logger.debug("gate {}".format(gate))
       scale_z_gate_taumul(specific_chan_gate, value)
       return
    else:
       logger.info("Channel gate other than X, Y and Z!!!")
       return

def offset_voltage_dependents_vshift(chanset, chan_name, gate, value):
    ''' Offsets the HH-channel model volatge dependents parametes with vshift.
    '''
    logger.debug("Processing vshift on chan_name {} gate {}".format(chan_name, gate))
    if gate is ':':
       for gate in ('X', 'Y', 'Z'):
           offset_voltage_dependents_vshift(chanset, chan_name, gate, value)
       return
    specific_chan_set = getattr(chanset, chan_name)
    logger.debug("specific_chan_set {}".format(specific_chan_set))
    specific_chan_gate = getattr(specific_chan_set, gate)
    if gate in ('X','Y'):
       logger.debug("gate {}".format(gate))
       logger.debug("specific_chan_gate {}".format(specific_chan_gate))
       offset_xy_gate_vshift(specific_chan_gate, value)
       return
    elif gate is 'Z':
       logger.debug("gate {}".format(gate))
       logger.debug("specific_chan_gate {}".format(specific_chan_gate))
       offset_z_gate_Ca_shift(specific_chan_gate, value)
       return
    else:
       logger.info("Channel gate other than X, Y and Z!!!")
       return
