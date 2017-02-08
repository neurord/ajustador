# -*- coding:utf-8 -*-
from __future__ import print_function, division
try:
    range = xrange
    from future_builtins import zip
except NameError:
    pass

import glob
import contextlib
import functools
import os
import operator
import copy
from collections import namedtuple
import numpy as np
from scipy import optimize
from igor import binarywave

from . import utilities, features
from .vartype import vartype

def load_dir(dir, timestep=1e-4):
    "Load all .ibw files from a directory, in alphanumerical order"
    files = sorted(glob.glob(os.path.join(dir, '*.ibw')))
    inputs = (binarywave.load(file)['wave']['wData'] for file in files)
    datas = (np.rec.fromarrays((np.arange(input.size)*timestep, input), names='x,y')
             for input in inputs)
    return np.vstack(datas).view(np.recarray)

simple_exp = lambda x, amp, tau: amp * np.exp(-(x-x[0]) / tau)
negative_exp = lambda x, amp, tau: amp * (1-np.exp(-(x-x[0]) / tau))
falling_param = namedtuple('falling_param', 'amp tau')
function_fit = namedtuple('function_fit', 'function params')

def _fit_falling_curve(ccut, baseline, steady):
    if ccut.size < 5:
        func = None
        params = falling_param(vartype(np.nan, np.nan),
                               vartype(np.nan, np.nan))
    else:
        init = (ccut.y.min()-baseline.x, ccut.x.ptp())
        func = negative_exp if (steady-baseline).negative else simple_exp
        popt, pcov = optimize.curve_fit(func, ccut.x, ccut.y-baseline.x, (-1,1))
        pcov = np.zeros((2,2)) + pcov
        params = falling_param(vartype(popt[0], pcov[0,0]**0.5),
                               vartype(popt[1], pcov[1,1]**0.5))
    return function_fit(func, params)

def _find_rectification(ccut, steady, window_len=11):
    if ccut.size < window_len + 1:
        return vartype(np.nan)
    pos = ccut.y.argmin()
    end = max(pos + window_len//2, ccut.size-1)
    bottom = array_mean(ccut[end-window_len : end+window_len+1].y)
    return steady - bottom

class Params(object):
    """A set of parameters for extracting features from a wave
    """
    requires = ()
    provides = ('baseline_before', 'baseline_after',
                'steady_after', 'steady_before', 'steady_cutoff',
                'falling_curve_window', 'rectification_window',
                'spike_assymetry_multiplier')

    baseline_before = .2
    baseline_after = 0.75

    steady_after = .25
    steady_before = .6
    steady_cutoff = 80

    falling_curve_window = 20
    rectification_window = 11

    spike_assymetry_multiplier = 10

Fileinfo = namedtuple('fileinfo', 'group ident experiment protocol number extra')

def _calculate_current(fileinfo, IV, IF):
    print(fileinfo)
    assert fileinfo.experiment == 1
    start, inc = IV if fileinfo.protocol == 1 else IF
    return start + inc * (fileinfo.number - 1)

class IVCurve(object):
    """
    >>> mes = loader.Measurement('docs/static/recording/042811-6ivifcurves_Waves/')
    >>> wave = mes[2]
    >>> wave.baseline
    vartype(-0.080227, 0.000085)
    >>> print(wave.baseline)
    -0.08023±0.00009
    >>> wave.injection
    -2.5e-10
    >>> wave.time
    0.89990000000000003
    >>> type(wave.wave)
    <class 'numpy.recarray'>
    >>> wave.wave.x
    array([  0.00000000e+00,   1.00000000e-04,   2.00000000e-04, ...,
             8.99700000e-01,   8.99800000e-01,   8.99900000e-01])
    >>> wave.wave.y
    array([-0.0799375 , -0.08028125, -0.08028125, ..., -0.08025   ,
           -0.08034375, -0.08034375], dtype=float32)
    """

    def __init__(self, filename, fileinfo, injection, x, y, features):
        self.filename = filename
        self.fileinfo = fileinfo
        self.injection = injection
        self.wave = np.rec.fromarrays((x, y), names='x,y')

        self._attributes = {'wave':self}
        for feature in features:
            self.register_feature(feature)

    def register_feature(self, feature):
        # check requirements and provides
        missing = set(feature.requires) - set(self._attributes)
        print(feature.requires, self._attributes.keys())
        if missing:
            raise ValueError('Unknown attribute: ' + ', '.join(sorted(missing)))
        doubled = set(feature.provides).intersection(self._attributes)
        if doubled:
            raise ValueError('Doubled attribute: ' + ', '.join(sorted(doubled)))

        # register
        print('registering {} on {}'.format(feature, self))
        obj = feature(self) if isinstance(feature, type) else feature
        for p in feature.provides:
            self._attributes[p] = obj

    def __getattr__(self, name):
        if name in self._attributes:
            return getattr(self._attributes[name], name)
        else:
            raise AttributeError

    @classmethod
    def load(cls, dirname, filename, IV, IF, time, features):
        path = os.path.join(dirname, filename)
        data = binarywave.load(path)['wave']['wData']
        time = np.linspace(0, time, num=data.size, endpoint=False)

        a, b, c, d, e, f = os.path.basename(filename)[:-4].split('_')
        fileinfo = Fileinfo(a, b, int(c), int(d), int(e), f)

        injection = _calculate_current(fileinfo, IV, IF)

        return cls(filename, fileinfo, injection, time, data, features)

    @property
    def time(self):
        return self.wave.x[-1]

    @property
    @utilities.once
    def falling_curve_fit(self):
        return _fit_falling_curve(self.falling_curve, self.baseline, self.steady)

    @property
    @utilities.once
    def rectification(self):
        return _find_rectification(self.falling_curve,
                                   self.steady,
                                   window_len=self.params.rectification_window)

    @property
    @utilities.once
    def charging_curve_halfheight(self):
        "The height in the middle between depolarization and first spike"
        if self.spike_count < 1:
            return np.nan
        else:
            what = self.wave[(self.wave.x > self.params.steady_after)
                             & (self.wave.x < self.spikes[0].x)]
            return np.median(what.y)

    @property
    def depolarization_interval(self):
        return self.params.steady_before - self.params.steady_after

    @property
    @utilities.once
    def mean_isi(self):
        if self.spike_count > 2:
            return array_mean(np.diff(self.spikes.x))
        elif self.spike_count == 2:
            d = self.spikes.x[1]-self.spikes.x[0]
            return vartype(d, 0.001)
        else:
            return vartype(self.depolarization_interval, 0.001)

    @property
    @utilities.once
    def isi_spread(self):
        spikes = self.spikes
        if len(spikes) > 2:
            diff = np.diff(self.spikes.x)
            return diff.ptp()
        else:
            return np.nan

    @property
    @utilities.once
    def spike_latency(self):
        "Latency until the first spike or end of injection if no spikes"
        if len(self.spikes) > 0:
            return self.spikes[0].x
        else:
            return self.time

    @property
    @utilities.once
    def mean_spike_height(self):
        return array_mean(self.spikes.y)

    @property
    @utilities.once
    def spike_width(self):
        steady = self.steady.x
        spikes = self._spike_i
        ans = np.empty_like(spikes, dtype=float)
        x = self.wave.x
        y = self.wave.y
        halfheight = (self.spikes.y - steady) / 2 + steady
        for i, k in enumerate(spikes):
            beg = end = k
            while beg > 1 and y[beg - 1] > halfheight[i]:
                beg -= 1
            while end + 2 < y.size and y[end + 1] > halfheight[i]:
                end += 1
            ans[i] = (x[end] + x[end+1] - x[beg] - x[beg-1]) / 2
        return ans

    @property
    @utilities.once
    def spike_ahp(self):
        spikes = self.spikes
        widths = self.spike_width * self.params.spike_assymetry_multiplier
        x = self.wave.x
        y = self.wave.y
        ans = np.empty_like(spikes, dtype=float)
        for i in range(len(spikes)):
            beg = max(spikes[i - 1:i+1].x.mean() if i > 0 else -np.inf, spikes[i].x - widths[i])
            end = min(spikes[i : i + 2].x.mean() if i < len(spikes)-1 else np.inf, spikes[i].x + widths[i])
            left = y[(x >= beg) & (x < spikes[i].x)].min()
            right = y[(x <= end) & (x > spikes[i].x)].min()
            ans[i] = right - left
        return ans

class Attributable(object):
    _MEAN_ATTRIBUTES = {'mean_baseline', 'mean_spike_height', 'mean_spike_width', 'mean_spike_ahp'}
    _VAR_ARRAY_ATTRIBUTES = {'baseline', 'steady', 'response', 'rectification',
                             'mean_isi', 'spike_height'}
    _ARRAY_ATTRIBUTES = {'filename', 'injection',
                         'spike_latency', 'spike_count', 'spike_ahp',
                         'falling_curve_fit|params|amp', 'falling_curve_fit|params|tau',
                         'falling_curve_fit|function',
                         'charging_curve_halfheight',
                         'isi_spread'}

    def __getattribute__(self, attr):
        if attr == 'mean_spike_height':
            spikes = np.hstack([w.spikes for w in self])
            return array_mean(spikes['y'])
        elif attr == 'mean_spike_width':
            widths = np.hstack([w.spike_width for w in self])
            return array_mean(widths)
        elif attr == 'mean_spike_ahp':
            ahps = np.hstack([w.spike_ahp for w in self])
            return array_mean(ahps)
        elif attr in Attributable._MEAN_ATTRIBUTES:
            return vartype.average(getattr(self, attr[5:]))
        elif attr in Attributable._VAR_ARRAY_ATTRIBUTES:
            return vartype.array([getattr(wave, attr) for wave in self.waves])
        elif attr in Attributable._ARRAY_ATTRIBUTES:
            op = operator.attrgetter(attr.replace('|', '.'))
            ans = [op(wave) for wave in self.waves]
            return np.array(ans)
        else:
            return super(Attributable, self).__getattribute__(attr)

    def __getitem__(self, index):
        if isinstance(index, (slice, np.ndarray)):
            c = copy.copy(self)
            c.waves = self.waves[index]
            return c
        else:
            return self.waves[index]

    def __len__(self):
        return len(self.waves)

class Measurement(Attributable):
    """Load a series of recordings from a directory

    >>> mes = loader.Measurement('docs/static/recording/042811-6ivifcurves_Waves')
    >>> mes.waves
    array([<ajustador.loader.IVCurve object at ...>,
           <ajustador.loader.IVCurve object at ...>,
           <ajustador.loader.IVCurve object at ...>,
           <ajustador.loader.IVCurve object at ...>,
           <ajustador.loader.IVCurve object at ...>], dtype=object)

    >>> hyper = mes[mes.injection <= 0]
    >>> depol = mes[mes.injection > 0]
    >>> mes.injection
    array([  0.00000000e+00,  -5.00000000e-10,  -2.50000000e-10,
             2.20000000e-10,   3.20000000e-10])
    >>> hyper.injection
    array([  0.00000000e+00,  -5.00000000e-10,  -2.50000000e-10])
    >>> depol.injection
    array([  2.20000000e-10,   3.20000000e-10])
    """
    def __init__(self, dirname,
                 IV=(-500e-12, 50e-12),
                 IF=(200e-12, 20e-12),
                 time=.9,
                 bad_extra=()):
        self.name = os.path.basename(dirname)
        self.params = Params()

        fefs = [self.params,
                features.Baseline,
                features.Spikes,
                features.FallingCurve,
        ]

        ls = sorted(os.listdir(dirname))
        waves = [IVCurve.load(dirname, f, IV, IF, features=fefs, time=time)
                 for f in ls]
        self.waves = np.array([wave for wave in waves
                               if wave.fileinfo.extra not in bad_extra])
