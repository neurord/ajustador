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
from numpy.lib import recfunctions
from igor import binarywave

from . import utilities
from .vartype import vartype

Fileinfo = namedtuple('fileinfo', 'group ident experiment protocol number extra')

def _calculate_current(fileinfo, IV, IF):
    assert fileinfo.experiment == 1
    tulength = len(IV)
    if tulength ==3:
        assert len(IF)==3
    #tulength will be the length of the tuple in IV, whether 2 or 3
    if tulength == 2:
        start, inc = IV if fileinfo.protocol == 1 else IF
        return start + inc * (fileinfo.number - 1)
    #tulength == 2 refers to OLD data files with 2 variables in tuple IV
    elif tulength == 3:
        startIV, inIV, IVnum = IV
        start, inc,x = IV if fileinfo.protocol == IVnum else IF
        return start + inc * (fileinfo.number - 1)
    else:
        print('ERROR: specify start, increment, and optionally protocol number')
        assert tulength==2 or tulength==3
        #tulength == 3 refers to NEW data files with 3 variables including trace number (usually 3 or 4) in tuple IV

class Trace(object):
    def __init__(self, injection, x, y, features):
        self.injection = injection

        self.wave = np.rec.fromarrays((x, y), names='x,y')

        self._attributes = {'wave':self,
                            'injection':self}

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
        if name != '_attributes' and name in self._attributes:
            return getattr(self._attributes[name], name)
        raise AttributeError(name)

    @property
    def time(self):
        return self.wave.x[-1]


class IVCurve(Trace):
    """
    >>> mes = loader.IVCurveSeries('docs/static/recording/042811-6ivifcurves_Waves/')
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
        super().__init__(injection, x, y, features)

        self.filename = filename
        self.fileinfo = fileinfo

    @classmethod
    def load(cls, dirname, filename, IV, IF, endtime, features):
        path = os.path.join(dirname, filename)
        dat=binarywave.load(path)
        data = dat['wave']['wData']
        if dat['version']==2:
            dt=dat['wave']['wave_header']['hsA']
        elif dat['version']==5:
            dt=dat['wave']['wave_header']['sfA'][0]
        numpts=binarywave.load(path)['wave']['wave_header']['npnts']
        tot_time=dt*numpts
        #time = np.linspace(0, endtime, num=data.size, endpoint=False)
        time = np.linspace(0, tot_time, num=numpts, endpoint=False)
        #optionally shorten the data
        #if endtime<tot_time:
        #    end_index=np.abs(time-endtime).argmin()
        #    data=data[0:end_index]
        #    time=time[0:end_index]

        a, b, c, d, e, f = os.path.basename(filename)[:-4].split('_')
        fileinfo = Fileinfo(a, b, int(c), int(d), int(e), f)

        injection = _calculate_current(fileinfo, IV, IF)

        return cls(filename, fileinfo, injection, time, data, features)


class Attributable(object):
    def __init__(self, features=None):
        # TODO: check duplicates, check dependencies between mean_attrs and array_attrs
        """ Acquires 'array_attributes' and 'mean_attributes' of all features into instance object """
        self._array_attributes = {p
                                  for feature in features
                                  for p in getattr(feature, 'array_attributes', ())} | \
                                 {'injection', 'filename'} # FIXME
        self._mean_attributes = {p
                                 for feature in features
                                 for p in getattr(feature, 'mean_attributes', ())}

    def __getattr__(self, attr):
        #print('getting', self.__class__.__name__, attr)
        if attr.startswith('__'):
            # we get asked for __setstate__ by copy.copy before we're
            # fully initialized. Just say no to all special names.
            raise AttributeError(attr)

        if not attr.startswith('_') and attr in getattr(self, '_array_attributes', {}):
            arr = [getattr(wave, attr) for wave in self.waves]
            if not arr:
                return np.empty(0)
            if isinstance(arr[0], vartype):
                return vartype.array(arr)
            if isinstance(arr[0], np.recarray):
                return recfunctions.stack_arrays(arr, asrecarray=True, usemask=False)
            if isinstance(arr[0], np.ndarray):
                return np.hstack(arr)
            return np.array(arr)

        if attr.startswith('mean_') and attr[5:] in getattr(self, '_mean_attributes', {}):
            values = self.__getattr__(attr[5:])
            return vartype.average(values)

        raise AttributeError('{} object does not have {} attribute'.format(
            self.__class__.__name__, attr))

    def __getitem__(self, index):
        if isinstance(index, (slice, np.ndarray, list)):
            c = copy.copy(self)
            c.waves = self.waves[index]
            return c
        else:
            return self.waves[index]

    def __len__(self):
        return len(self.waves)


class Measurement(Attributable):
    def __init__(self, dirname, params, *, features=None):
        if features is None:
            from . import features as _features
            features = _features.standard_features

        super().__init__(features)

        self.dirname = dirname
        self.name = os.path.basename(dirname).split('.', 1)[0]
        self.features = (params, *features)

    @property
    @utilities.once
    def waves(self):
        waves = np.array(self._waves())
        order = np.argsort([wave.injection for wave in waves])
        return waves[order]

    @waves.setter
    def waves(self, value):
        self._waves_value = value

    def __lt__(self, other):
        try:
            return self.name < other.name
        except AttributeError:
            raise TypeError

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.name)


class IVCurveSeries(Measurement):
    """Load a series of recordings from a directory

    >>> mes = loader.IVCurveSeries('docs/static/recording/042811-6ivifcurves_Waves')
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
    def __init__(self, dirname, params, *, IV, IF, time, bad_extra=(), features=None):
        super().__init__(dirname, params, features=features)

        self._load_args = dict(IV=IV, IF=IF, endtime=time)
        self._bad_extra = bad_extra

    def _waves(self):
        ls = os.listdir(self.dirname)
        waves = [IVCurve.load(self.dirname, f, features=self.features, **self._load_args)
                 for f in ls]
        return [wave for wave in waves
                if wave.fileinfo.extra not in self._bad_extra]

def parse_data_header(text):
    ''' input -> "100 pA"
        returns -> 100, 10e-15.
    '''
    from ajustador.helpers.scaling_factors import get_units_scale_factor
    parts = text.split(' ')
    if len(parts) != 2:
        raise ValueError
    if parts[0].lower().startswith('t'):
       return parts[0], get_units_scale_factor(parts[1])
    return float(parts[0]) * get_units_scale_factor(parts[1])

class CSVSeries(Measurement):
    """Load a series of measurements from a CSV file

    Each CSV file contains data for multiple injection currents::

      Time (ms),-200 pA,-150 pA,-100 pA,-50 pA,0 pA
      0,-46.6918945313,-44.2504882813,-48.5229492188,-47.3022460938,-46.38671875
      0.1000000015,-46.38671875,-45.7763671875,-46.38671875,-46.9970703125,-49.1333007813

    The time and injection values are extracted automatically.
    """
    def __init__(self, dirname, params, *, features=None, voltage_units=None):
        super().__init__(dirname, params, features=features)
        from ajustador.helpers.scaling_factors import get_units_scale_factor
        self.voltage_scale = get_units_scale_factor('mV') if voltage_units is None else get_units_scale_factor(voltage_units)

    def _waves(self):
        import pandas as pd
        #Need to add "time" as in IVCurve, and limit csv to data between 0 and time

        csv = pd.read_csv(self.dirname, index_col=0)
        value, factor = parse_data_header(csv.index.name)
        if value.lower().startswith('t'):
           x = csv.index.values * factor
        waves = [Trace(parse_data_header(column), x, csv[column].values * self.voltage_scale, self.features)
                 for column in csv.columns]
        return waves
