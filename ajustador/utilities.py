import os
import functools
import contextlib

import numpy as np

from .compat import TemporaryDirectory

@contextlib.contextmanager
def chdir(dir):
    "A contextmanager to temporarily change the working directory"
    old = os.getcwd()
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(old)

def once(function):
    "A decorator which only allows a function to run once"
    def wrapper(self):
        attr = '_{}_value'.format(function.__name__)
        try:
            return getattr(self, attr)
        except AttributeError:
            pass
        val = function(self)
        setattr(self, attr, val)
        return val
    return functools.update_wrapper(wrapper, function)


def cached(function):
    "A decorator to store the return values of a function in a cache"
    def wrapper(self, arg):
        attr = '_{}_value'.format(function.__name__)
        key = tuple(arg)
        try:
            cache = getattr(self, attr)
        except AttributeError:
            cache = {}
            setattr(self, attr, cache)
        try:
            return cache[key]
        except KeyError:
            pass
        ans = cache[key] = function(self, arg)
        return ans
    return functools.update_wrapper(wrapper, function)

def arange_values(values, func, order=None):
    values = np.round(values[:, order] if order is not None else values,
                      decimals=10)
    ranges = [sorted(set(what)) for what in values.T]
    xs = np.meshgrid(*ranges, sparse=True)
    ys = np.empty(tuple(len(what) for what in ranges))
    ys[:] = np.nan

    n = values.shape[1]
    for x, y in zip(values, func):
        ind = [xs[i].flat == x[i] for i in range(n)]
        ys[ind] = y

    return xs, ys

def find_missing(values):
    xs, ys = arange_values(values, np.zeros((len(values),)))
    missing = np.where(np.isnan(ys))
    n = len(missing)
    gen = ([xs[i].flat[missing[i][k]] for i in range(n)]
           for k in range(len(missing[0])))
    return np.array(list(gen))

def permutations_to_achieve_order(src, dst):
    src = list(src)
    dst = list(dst)
    assert len(src) == len(dst)
    for i in range(len(src)):
        if src[i] == dst[i]:
            continue
        j = dst.index(src[i])
        src[i], src[j] = src[j], src[i]
        yield i, j

def reorder_list(x, order):
    x = list(x)
    for i, j in permutations_to_achieve_order(range(len(x)), order):
        x[i], x[j] = x[j], x[i]
    return x

def reorder_array(x, order):
    for i, j in permutations_to_achieve_order(range(x.ndim), order):
        x = x.swapaxes(i, j)
    return x

def mkdir_p(dirname):
    try:
        os.mkdir(dirname)
    except OSError:
        pass
