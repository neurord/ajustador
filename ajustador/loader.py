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
from igor import binarywave

from . import utilities, features
from .vartype import vartype

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
        if missing:
            raise ValueError('Unknown attribute: ' + ', '.join(sorted(missing)))
        doubled = set(feature.provides).intersection(self._attributes)
        if doubled:
            raise ValueError('Doubled attribute: ' + ', '.join(sorted(doubled)))

        # register
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
    def depolarization_interval(self):
        return self.params.steady_before - self.params.steady_after

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

        fefs = (self.params,) + features.standard_features
        ls = os.listdir(dirname)
        waves = [IVCurve.load(dirname, f, IV, IF, features=fefs, time=time)
                 for f in ls]
        waves = np.array([wave for wave in waves
                          if wave.fileinfo.extra not in bad_extra])
        order = np.argsort([wave.injection for wave in waves])
        self.waves = waves[order]
