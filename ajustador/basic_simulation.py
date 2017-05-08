"""Run a single simulation from the command-line

This module takes a set of parameters which override the defaults
provides by the spspine module and runs the simulation and saves the
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
      --save=ivdata--5.0000000000000034e-11.npy

This module is not automatically imported as a child of ajustador.
An explicit import is needed:
>>> import ajustador.basic_simulation
"""

import sys
import tempfile
import re
import numpy as np
import moose
from spspine import d1d2
from spspine import (cell_proto,
                     clocks,
                     inject_func,
                     tables,
                     util,
                     standard_options)
from spspine.graph import neuron_graph


def real(s):
    f = float(s)
    if np.isnan(f):
        raise ValueError
    return f

def option_parser():
    p = standard_options.standard_options(
        default_injection_delay=0.2,
        default_injection_width=0.4,
        default_injection_current=[-0.15e-9, 0.15e-9, 0.35e-9],
        default_simulation_time=.9,
    )
    p.add_argument('--morph-file')
    p.add_argument('--baseline', type=real)
    p.add_argument('--neuron-type')

    p.add_argument('--RA', type=real)
    p.add_argument('--RM', type=real)
    p.add_argument('--CM', type=real)

    p.add_argument('--Cond-Kir', type=real)
    p.add_argument('--Kir-offset', type=real)

    p.add_argument('--Cond-NaF-0', type=real)
    p.add_argument('--Cond-KaS-0', type=real)
    p.add_argument('--Cond-KaF-0', type=real)
    p.add_argument('--Cond-Krp-0', type=real)
    p.add_argument('--Cond-BKCa-0', type=real)
    p.add_argument('--Cond-SKCa-0', type=real)

    p.add_argument('--Cond-CaL12-0', type=real)
    p.add_argument('--Cond-CaL13-0', type=real)
    p.add_argument('--Cond-CaN-0', type=real)
    p.add_argument('--Cond-CaR-0', type=real)
    p.add_argument('--Cond-CaT-0', type=real)

    p.add_argument('--Cond-NaF-1', type=real)
    p.add_argument('--Cond-KaS-1', type=real)
    p.add_argument('--Cond-KaF-1', type=real)
    p.add_argument('--Cond-Krp-1', type=real)
    p.add_argument('--Cond-BKCa-1', type=real)
    p.add_argument('--Cond-SKCa-1', type=real)

    p.add_argument('--Cond-CaL12-1', type=real)
    p.add_argument('--Cond-CaL13-1', type=real)
    p.add_argument('--Cond-CaN-1', type=real)
    p.add_argument('--Cond-CaR-1', type=real)
    p.add_argument('--Cond-CaT-1', type=real)

    p.add_argument('--save')
    return p

@util.listize
def serialize_options(opts):
    for key,val in opts.items():
        if key == 'junction_potential':
            # ignore, handled by the caller
            continue
        if val is not None:
            key = key.replace('_', '-')
            yield '--{}={}'.format(key, val)

def morph_morph_file(model, ntype, morph_file, new_file=None, RA=None, RM=None, CM=None):
    if morph_file:
        morph_file = util.find_model_file(model, morph_file)
    else:
        morph_file = cell_proto.find_morph_file(model, ntype)

    t = open(morph_file).read()

    if new_file is None:
        new_file = tempfile.NamedTemporaryFile('wt', prefix='morphology-', suffix='.p')

    for param in ('RA', 'RM', 'CM'):
        value = locals()[param]
        if value is not None:
            pat = r'(\*set_global {}) .*'.format(param)
            repl = r'\1 {}'.format(value)
            t = re.sub(pat, repl, t, count=1)
    new_file.write(t)
    new_file.flush()

    return new_file

def setup_conductance(condset, name, index, value):
    if value is not None:
        attr = getattr(condset, name)
        keys = sorted(attr.keys())
        attr[keys[index]] = value

def setup(param_sim, model):
    condset = getattr(model.Condset, param_sim.neuron_type)
    if param_sim.Cond_Kir is not None:
        for key in condset.Kir:
            condset.Kir[key] = param_sim.Cond_Kir

    if param_sim.Kir_offset is not None:
        model.Channels.Kir.X.Avhalf += param_sim.Kir_offset
        model.Channels.Kir.X.Bvhalf += param_sim.Kir_offset

    for value, name in [(param_sim.Cond_NaF_0, 'NaF'),
                        (param_sim.Cond_KaS_0, 'KaS'),
                        (param_sim.Cond_KaF_0, 'KaF'),
                        (param_sim.Cond_Krp_0, 'Krp'),
                        (param_sim.Cond_BKCa_0, 'BKCa'),
                        (param_sim.Cond_SKCa_0, 'SKCa'),
                        (param_sim.Cond_CaL12_0, 'CaL12'),
                        (param_sim.Cond_CaL13_0, 'CaL13'),
                        (param_sim.Cond_CaN_0, 'CaN'),
                        (param_sim.Cond_CaR_0, 'CaR'),
                        (param_sim.Cond_CaT_0, 'CaT')]:
        setup_conductance(condset, name, 0, value)

    for value, name in [(param_sim.Cond_NaF_1, 'NaF'),
                        (param_sim.Cond_KaS_1, 'KaS'),
                        (param_sim.Cond_KaF_1, 'KaF'),
                        (param_sim.Cond_Krp_1, 'Krp'),
                        (param_sim.Cond_BKCa_1, 'BKCa'),
                        (param_sim.Cond_SKCa_1, 'SKCa'),
                        (param_sim.Cond_CaL12_1, 'CaL12'),
                        (param_sim.Cond_CaL13_1, 'CaL13'),
                        (param_sim.Cond_CaN_1, 'CaN'),
                        (param_sim.Cond_CaR_1, 'CaR'),
                        (param_sim.Cond_CaT_1, 'CaT')]:
        setup_conductance(condset, name, 1, value)

    new_file = morph_morph_file(model,
                                param_sim.neuron_type,
                                param_sim.morph_file,
                                RA=param_sim.RA, RM=param_sim.RM, CM=param_sim.CM)
    model.morph_file[param_sim.neuron_type] = new_file.name

    MSNsyn, neurons = cell_proto.neuronclasses(model)
    neuron_paths = {ntype:[neuron.path]
                    for ntype, neuron in neurons.items()}
    pg = inject_func.setupinj(model, param_sim.injection_delay, param_sim.injection_width, neuron_paths)
    vmtab,catab,plastab,currtab = tables.graphtables(model, neurons,
                                                     param_sim.plot_current,
                                                     param_sim.plot_current_message)
    simpaths=['/'+param_sim.neuron_type]
    clocks.assign_clocks(simpaths, param_sim.simdt, param_sim.plotdt, param_sim.hsolve,
                         model.param_cond.NAME_SOMA)
    return pg

def reset_baseline(neuron, baseline, Cond_Kir):
    for n, w in enumerate(moose.wildcardFind('/{}/#[TYPE=Compartment]'.format(neuron))):
        w.initVm = w.Vm = baseline

        if Cond_Kir != 0:
            kir = moose.element(w.path + '/Kir')
            Em = baseline + kir.Gk * w.Rm * (baseline - kir.Ek)
            if n == 0:
                print("%s Em %f -> %f" % (w.path, w.Em, Em))
            w.Em = Em

def run_simulation(injection_current, simtime, param_sim):
    global pulse_gen
    print(u'◢◤◢◤◢◤◢◤ injection_current = {} ◢◤◢◤◢◤◢◤'.format(injection_current))
    pulse_gen.firstLevel = injection_current
    moose.reinit()
    if param_sim.baseline is not None:
        reset_baseline(param_sim.neuron_type, param_sim.baseline, param_sim.Cond_Kir)
    moose.start(simtime)

def main(args):
    global param_sim, pulse_gen
    param_sim = option_parser().parse_args(args)
    d1d2.neurontypes([param_sim.neuron_type])
    pulse_gen = setup(param_sim, d1d2)
    run_simulation(param_sim.injection_current[0], param_sim.simtime, param_sim)

    if param_sim.plot_current:
        neuron_graph.graphs(d1d2, False, param_sim.simtime, compartments=[0])
        util.block_if_noninteractive()
    if param_sim.save:
        np.save(param_sim.save, moose.element(elemname).vector)

if __name__ == '__main__':
    main(sys.argv[1:])
