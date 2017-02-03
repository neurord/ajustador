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

class Simulation(loader.Attributable):
    def __init__(self, dir,
                 junction_potential=0,
                 currents=None, simtime=.9, baseline=-0.0815,
                 morph_file=None,
                 single=False,
                 async=False,
                 **params):
        self.params = filtereddict(junction_potential=junction_potential,
                                   morph_file=morph_file,
                                   simtime=simtime,
                                   baseline=baseline,
                                   **params)

        self.name = (', '.join('{}={}'.format(k,v) for k,v in self.params.items())
                     if self.params else 'unmodified')

        self.tmpdir = utilities.TemporaryDirectory(dir=dir)
        print("Directory {} created".format(self.tmpdir.name))

        jar = os.path.join(self.tmpdir.name, 'params.pickle')
        with open(jar, 'wb') as f:
            pickle.dump(self.params, f)

        if currents is None:
            self.waves = np.array([], dtype=object)
        else:
            print("Simulating{} at {} points".format(" asynchronously" if async else "", len(currents)))
            self.execute_for(currents, junction_potential, single, async=async)

    @property
    def _param_str(self):
        return ' '.join('{}={:.5g}'.format(k, self.params[k])
                        for k in PARAMS if k in self.params)

    def __repr__(self):
        return '{}({}, time={}) {}'.format(
            self.__class__.__name__,
            self.tmpdir, self.params['simtime'], self._param_str)

    def _set_result(self, result):
        self.waves = np.array(result, dtype=object)

    def execute_for(self, injection_currents, junction_potential, single, async):
        params = ((self.tmpdir.name, inj, junction_potential, self.params)
                  for inj in injection_currents)
        if async:
            self._result = exe_map(single=False, async=True)(execute, params, callback=self._set_result)
        else:
            self._result = None
            result = exe_map(single=single, async=False)(execute, params)
            self._set_result(result)

    def wait(self):
        if self._result is not None:
            self._result.wait()

class SimulationResult(loader.Attributable):
    def __init__(self, dirname, time=.9):
        self.name = dirname

        jar = os.path.join(dirname, 'params.pickle')
        with open(jar, 'rb') as f:
            self.params = pickle.load(f)

        print("Result from {}, {}".format(dirname, self._param_str))
        ivfiles = glob.glob(os.path.join(dirname, 'ivdata-*.npy'))

        junction_potential = self.params.get('junction_potential', 0)
        waves = [load_simulation(ivfile, simtime=time,
                                 junction_potential=junction_potential)
                 for ivfile in ivfiles]
        waves.sort(key=operator.attrgetter('injection'))
        self.waves = np.array(waves, dtype=object)

    @property
    def param_values(self):
        return np.array([self.params[k] for k in PARAMS if k in self.params])

    @property
    def _param_str(self):
        return ' '.join('{}={:.5g}'.format(k, self.params[k])
                        for k in PARAMS if k in self.params)

    def __repr__(self):
        return '{}({}, time={}) {}'.format(
            self.__class__.__name__,
            self.name, self.waves[0].time, self._param_str)

    @staticmethod
    def find_global(param, p_file):
        pat = r'\*set_global {} (.*)'.format(param)
        t = open(p_file).read()
        m = re.search(pat, t)
        if m is None:
            return np.nan
        else:
            return float(m.group(1))

    def wait(self):
        pass

class SimulationResults(object):
    def __init__(self, dirname, time=.9):
        self.dirname = dirname
        self.time = time
        sims = [SimulationResult(dir, time=time) for dir in self._dirs()]
        if sims:
            size = max(sim.waves.size for sim in sims)
        self.results = [sim for sim in sims if sim.waves.size == size and size > 0]

    def _dirs(self):
        return sorted(glob.glob(os.path.join(self.dirname, '*/')),
                      key=lambda dir: os.stat(dir).st_mtime)

    def update(self):
        dirs = self._dirs()
        old = [sim for sim in self.results if sim.name in dirs]
        for sim in self.results:           # hack for reloading
            sim.__class__ = SimulationResult

        olddirs = {sim.name for sim in old}
        sims = [SimulationResult(dir, time=self.time) for dir in dirs
                if dir not in olddirs]
        sims = [sim for sim in sims if sim.waves.size >= self.results[0].waves.size]
        self.results.extend(sims)
        return self

    def ordered(self, measurement, *, fitness=fitnesses.combined_fitness):
        values, fitnesses = convert_to_values(self.results, measurement, fitness)
        keys = np.argsort(fitnesses)
        return np.array(self.results)[keys]

    def __getitem__(self, i):
        return self.results.__getitem__(i)
    def __len__(self):
        return len(self.results)

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

class Fit(object):
    fitness_max = 200

    def __init__(self, dir, measurement, fitness_func, *params, bounds=[], **scaling):
        self.dir = dir
        self.measurement = measurement
        self._currents = sorted(set(self.measurement.injection))
        self.fitness_func = fitness_func
        self.params = params
        self.scaling = scaling
        self._history = []
        self._async = False
        self.bounds = bounds

        # we assume that the first param value does not need penalties
        self._fitness_worst = None

    def from_result(self, result):
        return [result.params[name] / self.scaling.get(name, 1)
                for name in self.params]

    def load(self):
        old = SimulationResults(self.dir).results
        try:
            self._sim_value
        except AttributeError:
            self._sim_value = OrderedDict()
        for sim in old:
            key = tuple(self.from_result(sim))
            if key not in self._sim_value:
                self._sim_value[key] = sim

    @utilities.cached
    def sim(self, values):
        pairs = zip(self.params, values)
        settings = dict((k, v*self.scaling.get(k, 1)) for (k,v) in pairs)
        for k, v in self.scaling.items():
            if k not in self.params:
                settings[k] = v
        baseline = self.measurement.mean_baseline.x
        return Simulation(dir=self.dir, currents=self._currents, baseline=baseline, async=self._async, **settings)

    def sim_fitness(self, sim, full=False, max_fitness=None):
        fitness = self.fitness_func(sim, self.measurement, full=full)
        if full and max_fitness is not None:
            for i in range(len(fitness)):
                if fitness[i] > max_fitness:
                    fitness[i] = max_fitness
        self._history.append(fitness)
        return fitness

    @utilities.cached
    def fitness(self, values):
        sim = self.sim(values)
        return self.sim_fitness(sim)

    @utilities.cached
    def fitness_full(self, values):
        if self._fitness_worst is not None:
            pen = penalty(values, self.bounds, max_fitness=20, worst=self._fitness_worst)
            if pen is not None:
                print('fitness_full: penalty {} → {}'.format(values, pen))
                return -pen

        sim = self.sim(values)
        ans = self.sim_fitness(sim, full=True, max_fitness=18)
        ans[np.isnan(ans)] = self.fitness_max
        if self._fitness_worst is None:
            self._fitness_worst = ans
        else:
            k = self._fitness_worst < ans
            self._fitness_worst[k] = ans[k]
        print('fitness_full: {} → {}'.format(values, ans))
        return -ans

    def fitness_multi(self, many_values):
        self._async = True
        sims = [self.sim(values) for values in many_values]
        for sim in sims:
            sim.wait()
        results = [self.fitness(values) for values in many_values]
        return results

    def finished(self):
        quit = fitnesses.fit_finished(self._history)
        return quit.any()

    def __getitem__(self, i):
        return list(self._sim_value.values()).__getitem__(i)
    def __len__(self):
        return len(self._sim_value)
