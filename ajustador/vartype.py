import numbers
import math
import numpy as np

class vartype(object):
    """A number with an uncertainty (σ)

    >>> x = vartype(123, 5)
    >>> y = vartype(8, 1)
    >>> x + y
    vartype(131.0, 5.1)
    >>> x - y
    vartype(115.0, 5.1)
    >>> y / 3
    vartype(2.67, 0.33)
    >>> y < y
    False
    >>> print(y)
    8±1
    >>> print(x)
    123±5
    """
    def __init__(self, x, dev=0):
        self.x = x
        self.dev = dev

    @property
    def positive(self):
        """Check if the number is greater than 3σ

        >>> x = vartype(4, 1)
        >>> x.positive
        True
        >>> y = x - vartype(3)
        >>> y
        vartype(1.0, 1.0)
        >>> y.positive
        False
        """
        return self.x > self.dev*3

    @property
    def negative(self):
        """Check if the number is smaller than -3σ

        >>> x = vartype(-4, 1)
        >>> x.negative
        True
        """
        return self.x < -self.dev*3

    def __nonzero__(self):
        return abs(self.x) > self.dev*3

    def __sub__(self, other):
        return self + -other

    def __neg__(self):
        return vartype(-self.x, self.dev)

    def __add__(self, other):
        if isinstance(other, vartype):
            return vartype(self.x + other.x, (self.dev**2 + other.dev**2)**0.5)
        else:
            return vartype(self.x + other, self.dev + other)

    def __radd__(self, other):
        return vartype(other + self.x, self.dev)

    def __rsub__(self, other):
        return vartype(other - self.x, self.dev)

    def __mul__(self, other):
        if isinstance(other, vartype):
            return vartype(self.x * other.x,
                           (self.x**2*other.dev**2 + other.x**2*self.dev**2)**0.5)
        else:
            return vartype(self.x * other, self.dev * other)

    def __lt__(self, other):
        return self.x < other.x

    def __truediv__(self, other):
        if isinstance(other, numbers.Real):
            return vartype(self.x/other, self.dev/other)
        else:
            return NotImplemented

    def __pow__(self, other):
        return vartype(self.x**other, self.dev**other)

    def _prec(self):
        preca = int(math.floor(math.log10(abs(self.x)))) if self.x < 0 or self.x > 0 else 0
        precb = int(math.floor(math.log10(self.dev))) if self.dev > 0 else 0
        prec = -min(preca, precb, 0)
        return prec

    def __str__(self):
        return '{0.x:.{1}f}±{0.dev:.{1}f}'.format(self, self._prec())

    def __repr__(self):
        prec = self._prec() + 1
        return '{0.__class__.__name__}({0.x:.{1}f}, {0.dev:.{1}f})'.format(self, prec)

    def __float__(self):
        return float(self.x)

    def __abs__(self):
        if self.x >= 0:
            return self
        else:
            return -self

    @classmethod
    def average(cls, vect):
        """Calculate a weighted average of an array

        >>> items = [vartype(x, 1 + x/10) for x in range(5)]
        >>> X = vartype.array(items)
        >>> print(X)
        rec.array([(0, 1.0), (1, 1.1), (2, 1.2), (3, 1.3), (4, 1.4)],
                  dtype=[('x', '<i8'), ('dev', '<f8')])
        >>> vartype.average(X)
        vartype(1.66, 0.53)
        """
        if len(vect) == 0:
            return cls(np.nan, np.nan)
        elif isinstance(vect[0], numbers.Number):
            return array_mean(vect)
        else:
            sq = vect.dev**-2
            var = 1 / sq.sum()
            x = (vect.x * sq * var).sum()
            return cls(x, var**0.5)

    @classmethod
    def array(cls, items):
        """Create an array of vartypes

        The array is a numpy structured array with .x and .dev attributes.

        >>> items = [vartype(x, 1 + x/10) for x in range(5)]
        >>> X = vartype.array(items)
        >>> X
        rec.array([(0, 1.0), (1, 1.1), (2, 1.2), (3, 1.3), (4, 1.4)],
                  dtype=[('x', '<i8'), ('dev', '<f8')])
        >>> X.x
        array([0, 1, 2, 3, 4])
        >>> X.dev
        array([ 1. ,  1.1,  1.2,  1.3,  1.4])
        """
        x = np.array([getattr(p, 'x', p) for p in items])
        dev = np.array([getattr(p, 'dev', np.nan) for p in items])
        return np.rec.fromarrays((x, dev), names='x,dev')

    @classmethod
    def format_array(cls, array, prefix=''):
        prec = max(cls(*x)._prec() for x in array)
        gen = ('{0:.{2}f}±{1:.{2}f}'.format(*x, prec) for x in array)
        joiner = '\n' + ' ' * len(prefix)
        return prefix + joiner.join(gen)

vartype.nan = vartype(np.nan, np.nan)

def array_mean(data):
    return vartype(data.mean(), data.var(ddof=1)**0.5)

def array_diff(wave, n=1):
    xy = (wave.x[:n] + wave.x[n:])/n, np.diff(wave.y)
    return np.rec.fromarrays(xy, names='x,y')

def array_sub(reca, recb):
    """Return the difference of two arrays

    The uncertainty is calculated in the usual way.
    """
    if len(reca) == len(recb) == 0:
        return np.rec.fromarrays(([],[]), names='x,dev')
    xy = (reca.x - recb.x, (reca.dev**2 + recb.dev**2)**0.5)
    return np.rec.fromarrays(xy, names='x,dev')

def array_rms(rec):
    """Return the rms of an array

    .. math::
        \mathrm{rms} = \sqrt{\sum_i (x_i / \sigma_i)^2}
    """
    if isinstance(rec, vartype):
        return float(rec)

    if hasattr(rec, 'x'):
        return ((rec.x / rec.dev)**2).mean()**0.5
    else:
        return (rec ** 2).mean()**0.5
