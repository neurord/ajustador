import math
import types
import collections
import itertools
import operator
import os
import sys
import shlex
import subprocess
import glob
import re
import pickle
import multiprocessing

import numpy as np
import cma

from . import loader, features, fitnesses, utilities

def filtereddict(**kwargs):
    return dict((k,v) for (k,v) in kwargs.items() if v is not None)


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

def iv_filename(injection_current):
    return 'ivdata-{}.npy'.format(injection_current)

def iv_filename_to_current(ivfile):
    name = os.path.basename(ivfile)
    injection_current = float(name[7:-4])
    return injection_current

def execute(p):
    from . import basic_simulation

    dirname, injection, junction_potential, params, features = p
    simtime = params['simtime']
    params = basic_simulation.serialize_options(params)
    result = iv_filename(injection)
    cmdline = [sys.executable,
               basic_simulation.__file__,
               '-i={}'.format(injection),
               '--save={}'.format(result),
              ] + params
    print('+', ' '.join(shlex.quote(term) for term in cmdline), flush=True)
    with utilities.chdir(dirname):
        subprocess.call(cmdline)
        iv = load_simulation(result,
                             simtime=simtime,
                             junction_potential=junction_potential,
                             features=features)
    return iv

def load_simulation(ivfile, simtime, junction_potential, features):
    injection_current = iv_filename_to_current(ivfile)
    voltage = np.load(ivfile)
    x = np.linspace(0, simtime, voltage.size)
    iv = loader.IVCurve(None, None,
                        injection=injection_current,
                        x=x, y=voltage - junction_potential,
                        features=features)
    return iv


class Simulation(loader.Attributable):
    def __init__(self, dir,
                 junction_potential=0,
                 currents=None, simtime=None, baseline=None,
                 morph_file=None,
                 single=False,
                 async=False,
                 features=None,
                 **params):
        if simtime is None:
            raise ValueError
        if baseline is None:
            raise ValueError

        super().__init__(features)
        self.params = filtereddict(junction_potential=junction_potential,
                                   morph_file=morph_file,
                                   simtime=simtime,
                                   baseline=baseline,
                                   **params)
        self.features = features

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
        return ' '.join('{}={}'.format(k, v) for k, v in self.params.items())

    def __repr__(self):
        return '{}({}, {})'.format(
            self.__class__.__name__,
            self.tmpdir, self._param_str)

    def _set_result(self, result):
        self.waves = np.array(result, dtype=object)

    def execute_for(self, injection_currents, junction_potential, single, async):
        params = ((self.tmpdir.name, inj, junction_potential, self.params, self.features)
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
    def __init__(self, dirname, features):
        self.name = dirname

        jar = os.path.join(dirname, 'params.pickle')
        with open(jar, 'rb') as f:
            params = pickle.load(f)

        super().__init__(features)
        self.params = params
        self.features = (params, *features)

        ivfiles = glob.glob(os.path.join(dirname, 'ivdata-*.npy'))

        junction_potential = self.params.get('junction_potential', 0)
        simtime = self.params.get('simtime')
        waves = [load_simulation(ivfile,
                                 simtime=simtime,
                                 junction_potential=junction_potential,
                                 features=features)
                 for ivfile in ivfiles]

        waves.sort(key=operator.attrgetter('injection'))
        self.waves = np.array(waves, dtype=object)

    @property
    def _param_str(self):
        return ' '.join('{}={}'.format(k, v) for k, v in self.params.items())

    def __repr__(self):
        return '{}({!r}, {})'.format(
            self.__class__.__name__, self.name, self._param_str)

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
    def __init__(self, dirname, features):
        self.dirname = dirname
        sims = [SimulationResult(dir, features) for dir in self._dirs()]
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



class Param:
    min = max = None

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return 'Param {}={}'.format(self.name, self.value)

    @staticmethod
    def make(args):
        if isinstance(args, Param):
            # pass-through
            return args
        elif isinstance(args[1], str):
            # a filename or such, cannot optimize
            return Param(*args)
        else:
            return AjuParam(*args)

class AjuParam(Param):
    def __init__(self, name, value, min=None, max=None):
        super().__init__(name, value)
        self.min = min
        self.max = max

        # if starting value is less than 0.1 or more than 10, scale to that region
        val = value if value != 0 else (
            max if max is not None and max != 0 else
            (min if min is not None else 0))
        rr = math.log10(abs(val)) if val != 0 else -1
        if abs(rr) <= 1:
            self._scaling = 1
        else:
            self._scaling = 10**math.floor(rr)

    @property
    def scaled(self):
        return self.scale(self.value)

    def scale(self, val):
        return val / self._scaling

    def unscale(self, val):
        return val * self._scaling

class ParamSet:
    def __init__(self, *params):
        self.params = tuple(Param.make(p) for p in params)
        self.ajuparams = tuple(p for p in self.params
                               if isinstance(p, AjuParam))
        self.fixedparams = tuple(p for p in self.params
                                 if not isinstance(p, AjuParam))

    @property
    def scaled(self):
        return self.scale(p.value for p in self.ajuparams)

    def scale(self, values):
        assert (isinstance(values, types.GeneratorType) or
                len(values) == len(self.ajuparams)), values
        return [p.scale(v) for p, v in zip(self.ajuparams, values)]

    def scale_dict(self, values):
        return self.scale(values[p.name] for p in self.ajuparams)

    def unscale(self, scaled_values):
        assert len(scaled_values) == len(self.ajuparams)
        return [p.unscale(v) for p, v in zip(self.ajuparams, scaled_values)]

    def unscaled_dict(self, scaled_values):
        assert len(scaled_values) == len(self.ajuparams)
        gen = itertools.chain(((p.name, p.unscale(v))
                               for (p, v) in zip(self.ajuparams, scaled_values)),
                              ((p.name, p.value)
                               for p in self.fixedparams))
        return collections.OrderedDict(gen)

    def update(self, **kwargs):
        args = ((AjuParam(p.name, kwargs[p.name], p.min, p.max)
                 if isinstance(p, AjuParam)
                 else Param(p.name, kwargs[p.name]))
                if p.name in kwargs
                else p
                for p in self.params)
        return ParamSet(*args)

    @property
    @utilities.once
    def scaled_bounds(self):
        return ([p.scale(p.min) if p.min is not None else None
                 for p in self.params
                 if isinstance(p, AjuParam)],
                [p.scale(p.max) if p.max is not None else None
                 for p in self.params
                 if isinstance(p, AjuParam)])

    def __repr__(self):
        vv = ' '.join('{}={}'.format(p.name, p.value) for p in self.params)
        return 'ParamSet ' + vv

class Fit:
    fitness_max = 200

    def __init__(self, dirname, measurement, fitness_func, params, feature_list=None):
        self.dirname = dirname
        self.measurement = measurement
        self.fitness_func = fitness_func
        self.params = params
        self._history = []
        self._async = False
        self.optimizer = None

        # we assume that the first param value does not need penalties
        self._fitness_worst = None

        utilities.mkdir_p(dir)

    def load(self):
        try:
            self._sim_value
        except AttributeError:
            self._sim_value = collections.OrderedDict()

        old = SimulationResults(self.dirname, features=self.measurement.features)
        for sim in old.results:
            key = tuple(self.params.scale_dict(sim.params))
            if key not in self._sim_value:
                self._sim_value[key] = sim
                print(sim)

    def param_names(self):
        return [p.name for p in self.params.ajuparams]

    @utilities.cached
    def sim(self, scaled_params):
        unscaled = self.params.unscaled_dict(scaled_params)
        baseline = self.measurement.mean_baseline.x
        simtime = self.measurement.waves[0].time
        return Simulation(dir=self.dirname,
                          currents=self.measurement.injection,
                          baseline=baseline,
                          simtime=simtime,
                          async=self._async,
                          features=self.measurement.features,
                          **unscaled)

    def sim_fitness(self, sim, full=False, max_fitness=None):
        fitness = self.fitness_func(sim, self.measurement, full=full)
        if full and max_fitness is not None:
            for i in range(len(fitness)):
                if fitness[i] > max_fitness:
                    fitness[i] = max_fitness
        self._history.append(fitness)
        return fitness

    @property
    def name(self):
        return os.path.basename(self.dirname)

    @utilities.cached
    def fitness(self, scaled_params):
        sim = self.sim(scaled_params)
        return self.sim_fitness(sim)

    @utilities.cached
    def fitness_full(self, scaled_params):
        if self._fitness_worst is not None:
            pen = penalty(scaled_params, self.bounds, max_fitness=20, worst=self._fitness_worst)
            if pen is not None:
                print('fitness_full: penalty {} → {}'.format(scaled_params, pen))
                return -pen

        sim = self.sim(scaled_params)
        ans = self.sim_fitness(sim, full=True, max_fitness=18)
        ans[np.isnan(ans)] = self.fitness_max
        if self._fitness_worst is None:
            self._fitness_worst = ans
        else:
            k = self._fitness_worst < ans
            self._fitness_worst[k] = ans[k]
        print('fitness_full: {} → {}'.format(scaled_params, ans))
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

    def param_values(self, *what):
        values = np.empty((self.__len__(), len(what)))
        for i, item in enumerate(self):
            for j, param in enumerate(what):
                values[i, j] = item.params[param]
        return values

    def do_fit(self, count, params=None, sigma=1, popsize=8, seed=123):
        if self.optimizer is None:
            if params is None:
                params = self.params.scaled
            bounds = self.params.scaled_bounds
            opts = dict(bounds=bounds, popsize=popsize, seed=123)
            self.optimizer = cma.CMAEvolutionStrategy(params, sigma, opts)

        for i in range(count):
            if self.optimizer.stop():
                break
            points = self.optimizer.ask()
            values = self.fitness_multi(points)
            self.optimizer.tell(points, values)
            self.optimizer.logger.add()  # write data to disc to be plotted
            self.optimizer.disp()
