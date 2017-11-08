"""Run a single simulation from the command-line

This module takes a set of parameters which override the defaults
provides by the moose_nerp module and runs the simulation and saves the
results. In particular, this is useful when running multiple simulation
in parallel, where each one should be run out-of-process::

  $ python3 -m ajustador.basic_simulation \\
      --baseline=-0.07639880161359705 \\
      --RA=9.273975490852102 \\
      --RM=0.11241922550664576 \\
      --CM=0.0298401595465488 \\
      --Cond-Kir=6.441375022294002 \\
      --Kir-offset=6.529897906031442e-07 \\
      --morph-file=MScell-tertDendlongRE.p \\
      --simtime=0.9 \\
      -i=-5.0000000000000034e-11 \\
      --save-vm=ivdata--5.0000000000000034e-11.npy

This module is not automatically imported as a child of ajustador.
An explicit import is needed:
>>> import ajustador.basic_simulation
"""

import sys
import tempfile
import re
import importlib
import numpy as np
import moose
from moose_nerp.prototypes import (cell_proto,
                                   calcium,
                                   clocks,
                                   inject_func,
                                   tables,
                                   util,
                                   standard_options)
from moose_nerp.graph import neuron_graph


def real(s):
    f = float(s)
    if np.isnan(f):
        raise ValueError
    return f

def cond_setting(s):
    "Splits 'NaF,0=123.4' → ('NaF', 0, 123.4)"
    lhs, rhs = s.split('=', 1)
    rhs = float(rhs)
    chan, comp = lhs.split(',', 1)
    if comp != ':':
        comp = int(comp)
    return chan, comp, rhs

def option_parser():
    p = standard_options.standard_options(
        default_injection_delay=0.2,
        default_injection_width=0.4,
        default_injection_current=[-0.15e-9, 0.15e-9, 0.35e-9],
        default_simulation_time=.9,
        default_plot_vm=None,
    )
    p.add_argument('--morph-file')
    p.add_argument('--baseline', type=real)
    p.add_argument('--model', required=True)
    p.add_argument('--neuron-type', required=True)

    p.add_argument('--RA', type=real)
    p.add_argument('--RM', type=real)
    p.add_argument('--CM', type=real)
    p.add_argument('--Erest', type=real)
    p.add_argument('--Eleak', type=real)

    p.add_argument('--Kir-offset', type=real)

    p.add_argument('--cond', default=[], nargs='+', type=cond_setting, action=standard_options.AppendFlat)

    p.add_argument('--save-vm')
    return p

@util.listize
def serialize_options(opts):
    conds = []
    for key,val in opts.items():
        if key == 'junction_potential':
            # ignore, handled by the caller
            continue
        if val is not None:
            parts = key.split('_')
            num = getattr(val, 'value', val)
            if parts[0] == 'Cond' and len(parts) == 3: # e.g. Cond_NaF_0
                conds.append('{},{}={}'.format(parts[1], parts[2], num))
            elif parts[0] == 'Cond' and len(parts) == 2: # e.g. Cond_Kir
                conds.append('{},:={}'.format(parts[1], num))
            else:
                key = key.replace('_', '-')
                yield '--{}={}'.format(key, num)
    if conds:
        yield '--cond'
        yield from conds

def morph_morph_file(model, ntype, morph_file, new_file=None,
                     RA=None, RM=None, CM=None, Erest=None, Eleak=None):
    if morph_file:
        morph_file = util.find_model_file(model, morph_file)
    else:
        morph_file = cell_proto.find_morph_file(model, ntype)

    t = open(morph_file).read()

    if new_file is None:
        new_file = tempfile.NamedTemporaryFile('wt', prefix='morphology-', suffix='.p')

    for param, value in (('RA', RA),
                         ('RM', RM),
                         ('CM', CM),
                         ('EREST_ACT', Erest),
                         ('ELEAK', Eleak)):
        if value is not None:
            pat = r'(\*(set_global|set_compt_param) {})\s.*'.format(param)
            repl = r'\1 {}'.format(value)
            t_new = re.sub(pat, repl, t, count=1)
            if t_new == t:
                raise ValueError('substitution failed on {}: {!r}'.format(morph_file, pat))
            t = t_new

    new_file.write(t)
    new_file.flush()

    return new_file

def setup_conductance(condset, name, index, value):
    attr = getattr(condset, name)
    keys = sorted(attr.keys())
    if index == ':':
        for k in keys:
            attr[k] = value
    else:
        attr[keys[index]] = value

def setup(param_sim, model):
    if param_sim.calcium is not None:
        model.calYN = param_sim.calcium
    if param_sim.spines is not None:
        model.spineYN = param_sim.spines

    condset = getattr(model.Condset, param_sim.neuron_type)

    if param_sim.Kir_offset is not None:
        model.Channels.Kir.X.A_vhalf += param_sim.Kir_offset
        model.Channels.Kir.X.B_vhalf += param_sim.Kir_offset

    for cond in sorted(param_sim.cond):
        name, comp, value = cond
        print('cond:', name, comp, value)
        setup_conductance(condset, name, comp, value)

    new_file = morph_morph_file(model,
                                param_sim.neuron_type,
                                param_sim.morph_file,
                                RA=param_sim.RA, RM=param_sim.RM, CM=param_sim.CM,
                                Erest=param_sim.Erest, Eleak=param_sim.Eleak)
    model.morph_file[param_sim.neuron_type] = new_file.name

    MSNsyn, neurons = cell_proto.neuronclasses(model)
    neuron_paths = {ntype:[neuron.path]
                    for ntype, neuron in neurons.items()}
    pg = inject_func.setupinj(model, param_sim.injection_delay, param_sim.injection_width, neuron_paths)
    tables.graphtables(model, neurons,
                       param_sim.plot_current,
                       param_sim.plot_current_message)
    writer = tables.setup_hdf5_output(model, neurons, compartments=['soma'], filename='d1d2_bs.h5')

    simpaths=['/'+param_sim.neuron_type]
    clocks.assign_clocks(simpaths, param_sim.simdt, param_sim.plotdt, param_sim.hsolve,
                         model.param_cond.NAME_SOMA)

    if param_sim.hsolve and model.calYN:
        calcium.fix_calcium(model.neurontypes(), model)

    return pg, writer

def reset_baseline(neuron, baseline, Cond_Kir):
    for n, w in enumerate(moose.wildcardFind('/{}/#[TYPE=Compartment]'.format(neuron))):
        w.initVm = w.Vm = baseline

        if Cond_Kir != 0:
            kir = moose.element(w.path + '/Kir')
            Em = baseline + kir.Gk * w.Rm * (baseline - kir.Ek)
            if n == 0:
                print("%s Em %f -> %f" % (w.path, w.Em, Em))
            w.Em = Em

def run_simulation(injection_current, simtime, param_sim, model):
    global pulse_gen
    print(u'◢◤◢◤◢◤◢◤ injection_current = {} ◢◤◢◤◢◤◢◤'.format(injection_current))
    pulse_gen.firstLevel = injection_current
    moose.reinit()
    if param_sim.baseline is not None:
        condset = getattr(model.Condset, param_sim.neuron_type)
        try:
            attr = condset.Kir
        except KeyError:
            pass
        else:
            keys = sorted(attr.keys())
            Cond_Kir = attr[keys[0]]
            reset_baseline(param_sim.neuron_type, param_sim.baseline, Cond_Kir)
    moose.start(simtime)

def main(args):
    global param_sim, pulse_gen
    param_sim = option_parser().parse_args(args)
    model = importlib.import_module('moose_nerp.' + param_sim.model)
    model.neurontypes([param_sim.neuron_type])
    pulse_gen, hdf5writer = setup(param_sim, model)
    run_simulation(param_sim.injection_current[0], param_sim.simtime, param_sim, model)
    hdf5writer.close()

    if param_sim.plot_vm:
        neuron_graph.graphs(model, param_sim.plot_current, param_sim.simtime, compartments=[0])
        util.block_if_noninteractive()
    if param_sim.save_vm:
        elemname = '/data/Vm{}_0'.format(param_sim.neuron_type)
        np.save(param_sim.save_vm, moose.element(elemname).vector)

if __name__ == '__main__':
    main(sys.argv[1:])
