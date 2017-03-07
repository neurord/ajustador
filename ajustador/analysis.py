from __future__ import print_function, division

import os
import sys
import glob
import itertools
import subprocess
import socket
import multiprocessing
import operator
import re
import copy
import shlex
from collections import namedtuple, OrderedDict
try:
    import cPickle as pickle
except ImportError:
    import pickle
import numpy as np

from . import (loader,
               fitnesses,
               utilities,
               basic_simulation,
              )

_exe = None
def exe_map(single=False, async=False):
    if single and not async:
        return map
    else:
        global _exe
        if _exe is None:
            _exe = multiprocessing.Pool(multiprocessing.cpu_count() * 1)
        if async:
            return _exe.map_async
        else:
            return _exe.map

def load_simulation(ivfile, simtime, junction_potential=0):
    name = os.path.basename(ivfile)
    injection_current = float(name[7:-4])
    voltage = np.load(ivfile)
    x = np.linspace(0, simtime, voltage.size)
    iv = loader.IVCurve(None, None,
                        injection=injection_current,
                        x=x, y=voltage - junction_potential,
                        params=loader.Params())
    return iv

def filtereddict(**kwargs):
    return dict((k,v) for (k,v) in kwargs.items() if v is not None)

PARAMS = ('junction_potential',
          'RA', 'RM', 'CM', 'Cond_D1_Kir',
          'Kir_X_A_rate', 'Kir_X_A_vslope',
          'Kir_X_B_rate', 'Kir_X_B_vslope',
          'Kir_offset',
          'Cond_D1_NaF_0',
          'Cond_D1_KaS_0',
          'Cond_D1_KaF_0',
          'Cond_D1_Krp_0',
          'Cond_D1_BKCa_0',
          'qfactNaF')

class Namespace(object):
    "A stupid workaround for DEAP misdesign"
    pass

def iv_filename(injection_current):
    return 'ivdata-{}.npy'.format(injection_current)

def execute(p):
    dirname, injection, junction_potential, options = p
    params = basic_simulation.serialize_options(options)
    result = iv_filename(injection)
    cmdline = [sys.executable,
               basic_simulation.__file__,
               '-i={}'.format(injection),
               '--save={}'.format(result),
              ] + params
    print('+', ' '.join(shlex.quote(term) for term in cmdline), flush=True)
    with utilities.chdir(dirname):
        subprocess.call(cmdline)
        iv = load_simulation(result, simtime=options['simtime'],
                             junction_potential=junction_potential)
    return iv

def convert_to_values(group, measurement, fitness_func, *what, **opts):
    values = np.empty((len(group), len(what)))
    for i, item in enumerate(group):
        for j, param in enumerate(what):
            values[i, j] = item.params[param]

    if measurement is None:
        if fitness_func is None:
            fitness = None
        else:
            fitness = [fitness_func(item, **opts) for item in group]
    else:
        if fitness_func is None:
            fitness_func = fitnesses.combined_fitness
        fitness = [fitness_func(item, measurement, **opts) for item in group]
    return values, fitness

def _scan_params_job(settings):
    return Simulation(single=True, **settings)

def scan_params(dir, IVs, **params):
    values = [np.atleast_1d(p) for p in params.values()]
    res = np.empty(tuple(p.size for p in values), dtype=object)
    jobs = [dict(zip(params, comb)) for comb in itertools.product(*values)]
    for job in jobs:
        job['dir'] = dir
        job['currents'] = IVs

    ans = exe_map()(_scan_params_job, jobs)
    res.flat = ans
    return res

def scan_missing(dir, group):
    IVs = group[0].injection
    params = group[0].params.keys()
    values, _ = convert_to_values(group, None, None, *params)
    missing = utilities.find_missing(values)
    res = np.empty((values.shape[0],), dtype=object)
    jobs = [dict(zip(params, comb)) for comb in missing]
    for job in jobs:
        job['dir'] = dir
        job['currents'] = IVs

    ans = exe_map()(_scan_params_job, jobs)
    res.flat = ans
    return res

class PositiveStepper(object):
   def __init__(self, stepsize, params, **constraints):
       self.stepsize = stepsize
       self.params = params
       self._lower = np.zeros(len(params))
       self._upper = np.ones(len(params)) * np.inf
       for name, limit in constraints.items():
           i = params.index(name)
           if limit[0] is not None:
               self._lower[i] = limit[0]
           if len(limit) > 1 and limit[1] is not None:
               self._upper[i] = limit[1]
   def __call__(self, x):
       s = self.stepsize
       for i in range(len(x)):
           l = np.clip(x[i] - s, self._lower[i], self._upper[i])
           u = np.clip(x[i] + s, self._lower[i], self._upper[i])
           x[i] = np.random.uniform(l, u)
       return x

def penalty(params, bounds, max_fitness=20, power=1, worst=None):
    "Implement a penalty for each out-of-bounds param"
    bad = 0
    for i in range(len(params)):
        if np.isnan(params[i]):
            bad += max_fitness
            continue
        if len(bounds) > i and bounds[i] is not None:
            lower, upper = bounds[i]
            scaling = (upper if upper is not None else 0) - (lower if lower is not None else 0)
            if lower is not None and params[i] < lower:
                bad += min(abs((params[i] - lower) / scaling) ** power, max_fitness)
                continue
            elif upper is not None and params[i] > upper:
                bad += min(abs((params[i] - upper) / scaling) ** power, max_fitness)
                continue
    if bad > 0:
        return worst + np.array([bad] * len(worst))
    else:
        return None
