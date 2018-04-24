import math
import types
import collections
import itertools
import operator
import os
import sys
import shlex
import shutil
import subprocess
import glob
import re
import pickle
import multiprocessing

import numpy as np
import cma

from . import loader, features as _features, fitnesses, utilities

import logging #SRIRAM 02152018
from ajustador.helpers.loggingsystem import getlogger #SRIRAM 02152018
logger = getlogger(__name__) #SRIRAM 02152018
logger.setLevel(logging.INFO) #SRIRAM 02152018

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
    logger.debug("Unseralized params:\n {} inject {}".format(params,injection)) #SRIRAM 02192018
    params['injection_delay'] = params['injection_delay'][0] #SRIRAM 02192018
    params['injection_width'] = params['injection_width'][0] #SRIRAM 02192018
    params = basic_simulation.serialize_options(params)
    result = iv_filename(injection) #result is filename
    cmdline = [sys.executable,
               basic_simulation.__file__,
               '-i={}'.format(injection),
               '--save-vm={}'.format(result),
    ] + params
    #print('+', ' '.join(shlex.quote(term) for term in cmdline), flush=True)
    logger.debug("Logger in execute function!!!")
    logger.debug("Seralized params:\n {}".format(params)) #SRIRAM 02192018
    logger.debug("Basic_simulation command:\n {}".format(cmdline)) #SRIRAM 02192018
    with utilities.chdir(dirname):
        subprocess.check_call(cmdline)
        iv = load_simulation(result,
                             simtime=simtime,
                             junction_potential=junction_potential,
                             features=features)
    return iv

def load_simulation(ivfile, simtime, junction_potential, features):
    logger.info("Logger in load simulation function!!!")
    injection_current = iv_filename_to_current(ivfile)
    voltage = np.load(ivfile)
    x = np.linspace(0, float(simtime), voltage.size)
    iv = loader.IVCurve(None, None,
                        injection=injection_current,
                        x=x, y=voltage - float(junction_potential),
                        features=features)
    return iv


class Simulation(loader.Attributable):
    def __init__(self, dir, *, params, features):
        super().__init__(features=features)

        self.params = params
        self.features = features

        self.name = (', '.join('{}={}'.format(k,v) for k,v in self.params.items())
                     if self.params else 'unmodified')
        logger.debug("Logger in Simulation!!!") #SRIRAM 02192018
        logger.debug("Params of simulation\n {}".format(self.name)) #SRIRAM 02192018

        self.tmpdir = utilities.TemporaryDirectory(dir=dir)
        # print("Directory {} created".format(self.tmpdir.name))

        jar = os.path.join(self.tmpdir.name, 'params.pickle')
        with open(jar, 'wb') as f:
            pickle.dump(self.params, f)

    def _param_str(self, sep=' '):
        return sep.join('{}={}'.format(k, v) for k, v in self.params.items())

    def __repr__(self):
        return '{}({}, {})'.format(
            self.__class__.__name__,
            self.tmpdir, self._param_str())

    def wait(self):
        if self._result is not None:
            self._result.wait()

class MooseSimulation(Simulation):
    def __init__(self, dir,
                 currents=None,
                 *,
                 simtime,
                 injection_delay,    #SRIRAM add injection width and delay here.
                 injection_width,  #SRIRMA add injection_interval
                 morph_file=None,
                 single=False,
                 async=False,
                 features=None,
                 params):

        junction_potential = params['junction_potential'].value # FIXME: nicer syntax?
        params = filtereddict(simtime=simtime,
                              injection_delay=injection_delay,   #SRIRAM 02192018
                              injection_width=injection_width,   #SRIRAM 02192018
                              **dict(params.items()))
        super().__init__(dir, params=params, features=features)

        if currents is None:
            self.waves = np.array([], dtype=object)
        else:
            print("Simulating{} at {} points".format(" asynchronously" if async else "", len(currents)))
            self.execute_for(currents, junction_potential, single, async=async)

    def execute_for(self, injection_currents, junction_potential, single, async):
        params = ((self.tmpdir.name, inj, junction_potential, self.params, self.features)
                  for inj in injection_currents)
        if async:
            logger.debug("MooseSimulation, Params in execute_for \n {}".format(params)) #SRIRAM
            self._result = exe_map(single=False, async=True)(execute, params, callback=self._set_result)
        else:
            self._result = None
            logger.debug("MooseSimulation, Params in execute_for \n {} featues {}".format(self.params, self.features)) #SRIRAM
            result = exe_map(single=single, async=False)(execute, params)
            self._set_result(result)

    def _set_result(self, result):
        self.waves = np.array(result, dtype=object)

        tag = os.path.join(self.tmpdir.name, '.complete')
        open(tag, 'w').close()

    @classmethod
    def make(cls, *, dir, model, measurement, params):
        # A hack wrapper to push moose-specific stuff out from Fit
        simtime = measurement.waves[0].time
        injection_delay=measurement.features[0].injection_start,    #SRIRAM 02192018
        injection_width=measurement.features[0].injection_interval,  #SRIRAM 02192018
        baseline = measurement.mean_baseline.x
        logger.debug("Logger in MooseSimulation.make!!!") #SRIRAM
        logger.debug("Params \n {}".format(params))

        return cls(dir=dir,
                   # FIXME!
                   # model=model,
                   # neuron_type=,
                   injection_delay=injection_delay,    #SRIRAM 02192018
                   injection_width=injection_width,  #SRIRAM 02192018
                   currents=measurement.injection,
                   simtime=simtime,
                   features=measurement.features,
                   params=params)

class SimulationResult(loader.Attributable):
    def __init__(self, dirname, features):
        self.name = os.path.basename(dirname)

        if not isinstance(features, (list, tuple)):
            features = [features, *_features.standard_features]

        jar = os.path.join(dirname, 'params.pickle')
        if os.path.exists(jar):
            with open(jar, 'rb') as f:
                params = pickle.load(f)
        else:
            params = {}
        params = ParamSet(*params)

        super().__init__(features)
        self.features = features
        self.params = params


    def _param_str(self, sep=' '):
        return sep.join(('{}={:.3g}' if isinstance(v, float) else '{}={}').format(k, v)
                        for k, v in self.params.items())

    def __repr__(self):
        return '{}({!r}, {})'.format(self.__class__.__name__, self.name,
                                     self._param_str())

    def report(self):
        return '{}({!r})\n{}'.format(self.__class__.__name__, self.name,
                                     self._param_str('\n'))


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

class MooseSimulationResult(SimulationResult):
    def __init__(self, dirname, features):
        super().__init__(dirname, features)

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

class SimulationResults(object):
    def __init__(self, dirname, features, *, constructor=MooseSimulationResult):
        self.dirname = dirname
        self.features = features
        self._constructor = constructor

    def _dirs(self, last=None):
        paths = glob.glob(os.path.join(self.dirname, '*/.complete'))
        dirs = (os.path.dirname(path) for path in paths)
        # sort by the simulation initialization order
        compare = lambda dir: os.stat(os.path.join(dir, 'params.pickle')).st_mtime
        ans = sorted(dirs, key=compare)
        if last is None:
            return ans
        else:
            return ans[-last:]

    def load(self, last=None):
        dirs = self._dirs(last=last)
        n = len(dirs)
        for i, dir in enumerate(dirs):
            yield i, n, self._constructor(dir, self.features)

    def ordered(self, measurement, *, fitness=fitnesses.combined_fitness):
        values, fitnesses = convert_to_values(self.results, measurement, fitness)
        keys = np.argsort(fitnesses)
        return np.array(self.results)[keys]


class ParamMechanism:
    "A class to specify how a parameter is adjusted in the model"
    pass

ParamMechanism.unspecified = ParamMechanism()

class Param:
    """ Base class for AjuParam class encapsulated set of values (name, value, fixed, mech).
    used for simulation.
    """
    min = max = None

    def __init__(self, name, value, fixed=True, mech=ParamMechanism.unspecified):
        self.name = name
        assert isinstance(value, (float, int, str)), value
        self.value = value
        self.fixed = fixed
        self.mech = mech

    def __repr__(self):
        return 'Param {}={}'.format(self.name, self.value)

    def __float__(self):
        return self.value

    @staticmethod
    def make(args):
        """ Returns Param object based on type and number of args.
            type of args is string then the string should of form:
            	"name value [fixed=<Bool>]"
        """
        if isinstance(args, Param):
            # pass-through
            return args
        elif isinstance(args[1], str):
            # a filename or such, cannot optimize
            return Param(*args)
        elif len(args) == 3 and args[2] == 'fixed':
            return Param(*args[:2])
        else:
            return AjuParam(*args)

    def valid(self, val):
        return True

class AjuParam(Param):
    """ Class AjuParam is a custom data structure to hold parameters (name, value, min=<Interger>, max=<integer>, fixed=<Bool>, [mech]).
    used for simulation.
    """
    def __init__(self, name, value, *, min=None, max=None,
                 fixed=False,
                 mech=ParamMechanism.unspecified):

        super().__init__(name, value, fixed=fixed, mech=mech)
        self.min = min
        self.max = max

        if fixed:
            self._scaling = None
        else:
            # if starting value is less than 0.1 or more than 10, scale to that region
            # self._scaling property is set by logically assesing value input parameter along with inputs min, max.
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
        return val / self._scaling if self._scaling is not None else self.value

    def unscale(self, val):
        return val * self._scaling if self._scaling is not None else self.value

    def valid(self, val):
        return ((self.min is None or self.min <= val) and
                (self.max is None or val <= self.max))

    def updated(self, value):
        return AjuParam(self.name, value,
                        min=self.min,
                        max=self.max,
                        fixed=self.fixed,
                        mech=self.mech)

class ParamSet:
    def __init__(self, *params, **other):
        other = tuple(Param(k, v) for k,v in other.items())
        self.params = params + other
        self.fixedparams = tuple(p for p in self.params if p.fixed)
        self.ajuparams = tuple(p for p in self.params if not p.fixed)

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

    def updated(self, **kwargs):
        args = (p.updated(kwargs[p.name]) if p.name in kwargs else p
                for p in self.params)
        return ParamSet(*args)

    # FIXME: remove
    update = updated

    def items(self):
        for param in self.params:
            yield param.name, param

    def __getitem__(self, key):
        for param in self.params:
            if param.name == key:
                return param
        raise KeyError(key)

    def get(self, key, fallback=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            if fallback is not None:
                return fallback
            raise

    @property
    @utilities.once
    def scaled_bounds(self):
        return ([p.scale(p.min) if p.min is not None else None
                 for p in self.ajuparams],
                [p.scale(p.max) if p.max is not None else None
                 for p in self.ajuparams])

    def __repr__(self):
        vv = ' '.join('{}={}{}'.format(p.name, p.value,
                                       '' if p.valid(p.value) else '*')
                      for p in self.params)
        return 'ParamSet ' + vv

class Fit:
    fitness_max = 200

    def __init__(self, dirname, measurement, model, neuron_type, fitness_func, params,
                 feature_list=None,
                 _make_simulation=None,
                 _result_constructor=MooseSimulationResult):
        self.dirname = dirname
        self.measurement = measurement
        self.model = model
        self.neuron_type = neuron_type
        self.fitness_func = fitness_func
        self.params = params
        self._history = []
        self._async = False
        self.optimizer = None
        self._make_simulation = _make_simulation
        self._result_constructor = _result_constructor

        # we assume that the first param value does not need penalties
        self._fitness_worst = None

        utilities.mkdir_p(dirname)

    def load(self, last=None):
        try:
            self._sim_value
        except AttributeError:
            self._sim_value = collections.OrderedDict()

        new = SimulationResults(self.dirname,
                                features=self.measurement.features,
                                constructor=self._result_constructor)
        need_erase = False
        for i, n, sim in new.load(last=last):
            print('{}/{} {}'.format(i, n, sim.name), end='\r')
            need_erase = True
            key = tuple(sim.params.scaled)
            if key not in self._sim_value:
                self._sim_value[key] = sim
                print(sim)
                need_erase = False

        if need_erase:
            print(' ' * shutil.get_terminal_size().columns, end='\r')

    def param_names(self):
        return [p.name for p in self.params.ajuparams]

    @utilities.cached
    def sim(self, scaled_params):
        unscaled = self.params.unscaled_dict(scaled_params)
        sim = self._make_simulation(dir=self.dirname,
                                    model=self.model,
                                    measurement=self.measurement,
                                    params=self.params.updated(**unscaled)) #define params here SRIRAM
        return sim

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
        #many values is the population_size set of parameter values
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
                values[i, j] = item.params[param].value
        return values

    def do_fit(self, count, params=None, sigma=1, popsize=8, seed=123):
        if self.optimizer is None:
            if params is None:
                params = self.params.scaled
            bounds = self.params.scaled_bounds
            opts = dict(bounds=bounds, popsize=popsize, seed=seed)
            self.optimizer = cma.CMAEvolutionStrategy(params, sigma, opts)

        for i in range(count):
            if self.optimizer.stop():
                break
            points = self.optimizer.ask()
            values = self.fitness_multi(points)
            self.optimizer.tell(points, values)
            self.optimizer.logger.add()  # write data to disc to be plotted
            self.optimizer.disp()
