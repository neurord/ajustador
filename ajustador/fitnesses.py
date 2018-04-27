from __future__ import print_function, division

import collections
import enum
import numpy as np
import pandas as pd

from . import vartype

class ErrorCalc(enum.IntEnum):
    normal = 1
    relative = 2

"If 'b' (measurement) is 0, limit to this value"
RELATIVE_MAX_RATIO = 10

NAN_REPLACEMENT = 1.5

def sub_mes_dev(reca, recb):
    if isinstance(reca, vartype.vartype):
        assert reca == vartype.vartype.nan
        return vartype.vartype.nan
    if isinstance(recb, vartype.vartype):
        assert recb == vartype.vartype.nan
        return vartype.vartype.nan
    if len(reca) == 0 or len(recb) == 0:
        return vartype.vartype.nan

    if hasattr(reca, 'x'):
        xy = (reca.x - recb.x, (reca.dev**2 + recb.dev**2)**0.5)
        if isinstance(reca, vartype.vartype):
            return vartype.vartype(*xy)
        else:
            return np.rec.fromarrays(xy, names='x,dev')
    else:
        return reca - recb

def _select(a, b, which=None):
    if which is not None:
        bsel = b[which]
    else:
        bsel = b
    fitting = np.abs(a.injection[:,None] - bsel.injection) < 1e-12
    ind1, ind2 = np.where(fitting)
    return a[ind1], bsel[ind2]

def relative_diff_single(a, b, extra=0):
    x = getattr(a, 'x', a)
    y = getattr(b, 'x', b)

    base = abs(x) + abs(y) / RELATIVE_MAX_RATIO
    nonzero = np.atleast_1d(base > 0).any()
    return ((abs(x - y) / base if nonzero else base)
             + RELATIVE_MAX_RATIO * extra)

def relative_diff(a, b):
    """A difference between a and b using b as the yardstick

    .. math::
       W = |a - b| / (|b| + |a| * RELATIVE_MAX_RATIO)
       w = rms(W)
    """
    n1, n2 = len(a), len(b)
    if n1 == n2 == 0:
        return np.array([])
    if n1 < n2:
        a = a[:n2]
    elif n1 < n2:
        b = b[:n1]
    return relative_diff_single(a, b, extra=abs(n1 - n2))

def _evaluate(a, b, error=ErrorCalc.relative):
    if error == ErrorCalc.normal:
        diff = sub_mes_dev(a, b)
        ans = vartype.array_rms(diff)
    elif error == ErrorCalc.relative:
        diff = relative_diff(a, b)
        diff[np.isnan(diff)] = NAN_REPLACEMENT
        ans = vartype.array_rms(diff)
    else:
        assert False, error
    if np.isnan(ans):
        return NAN_REPLACEMENT
    else:
        return ans

def _evaluate_single(a, b, error=ErrorCalc.relative):
    if error == ErrorCalc.normal:
        ans = float(abs(a - b))
    elif error == ErrorCalc.relative:
        ans = relative_diff_single(a, b)
    else:
        raise AssertionError
    if np.isnan(ans):
        return NAN_REPLACEMENT
    else:
        return ans

def response_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    "Similarity of response to hyperpolarizing injection"
    m1, m2 = _select(sim, measurement, measurement.injection <= 110e-12)
    return _evaluate(m1.response, m2.response, error=error)

def baseline_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    "Similarity of baselines"
    m1, m2 = _select(sim, measurement)
    return _evaluate(m1.baseline, m2.baseline, error=error)

def baseline_pre_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    "Similarity of baselines"
    m1, m2 = _select(sim, measurement)
    return _evaluate(m1.baseline_pre, m2.baseline_pre, error=error)

def baseline_post_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    "Similarity of baselines"
    m1, m2 = _select(sim, measurement)
    return _evaluate(m1.baseline_post, m2.baseline_post, error=error)

def rectification_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    m1, m2 = _select(sim, measurement, measurement.injection <= -10e-12)
    return _evaluate(m1.rectification, m2.rectification, error=error)

#This should be calculated for positive current injection, even if no spike.  Maybe only if no spike
def charging_curve_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    m1, m2 = _select(sim, measurement, measurement.spike_count >= 1)
    if len(m2) == 0:
        return vartype.vartype.nan
    return _evaluate(m1.charging_curve_halfheight, m2.charging_curve_halfheight,
                     error=error)

#alternatively, could do falling curve for positive current injection if no spike
def falling_curve_time_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    m1, m2 = _select(sim, measurement, measurement.injection <= -10e-12)
    if len(m2) == 0:
        return vartype.vartype.nan
    return _evaluate(m1.falling_curve_tau, m2.falling_curve_tau, error=error)

def mean_isi_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    m1, m2 = _select(sim, measurement, measurement.spike_count >= 2)
    if len(m2) == 0:
        return vartype.vartype.nan
    return _evaluate(m1.mean_isi, m2.mean_isi, error=error)

def isi_spread_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    m1, m2 = _select(sim, measurement, measurement.spike_count >= 2)
    if len(m2) == 0:
        return vartype.vartype.nan
    return _evaluate(m1.isi_spread, m2.isi_spread, error=error)

def _measurement_to_spikes(meas):
    frames = [pd.DataFrame(wave.spikes) for wave in meas]
    for frame, wave in zip(frames, meas):
        frame['injection'] = wave.injection
        frame.reset_index(inplace=True)
        frame.set_index(['index', 'injection'], inplace=True)
    return pd.concat(frames)

def spike_time_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    m1, m2 = _select(sim, measurement, measurement.spike_count >= 2)
    if len(m1) == 0:
        m1, m2 = _select(measurement, sim, sim.spike_count >= 2)
        if len(m1) == 0:
            # neither is spiking, cannot determine spike timing
            return np.nan

    spikes1 = _measurement_to_spikes(m1)
    spikes2 = _measurement_to_spikes(m2)
    diff = spikes2 - spikes1
    spikes1 = spikes1 + diff # this is original spikes1 with nans inserted for missing spikes
    spikes2 = spikes2 - diff # and the same for spikes2
    spikes1.fillna(sim[0].injection_interval, inplace=True)
    spikes2.fillna(sim[0].injection_interval, inplace=True)
    return _evaluate(spikes1['x'], spikes2['x'], error=error)

def spike_count_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    m1, m2 = _select(sim, measurement)
    return _evaluate(m1.spike_count, m2.spike_count, error=error)

def spike_latency_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    m1, m2 = _select(sim, measurement, measurement.spike_count >= 1)
    return _evaluate(m1.spike_latency, m2.spike_latency, error=error)

def spike_width_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    return _evaluate_single(sim.mean_spike_width, measurement.mean_spike_width,
                            error=error)

def spike_height_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    return _evaluate_single(sim.mean_spike_height, measurement.mean_spike_height,
                            error=error)

def spike_ahp_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    m1, m2 = _select(sim, measurement, measurement.spike_count >= 1)

    # Just ignore any extra spikes. Let's assume that most spikes
    # and AHPs are similar, and that we're using a different fitness
    # function to compare spike counts.
    left = m1.spike_ahp
    right = m2.spike_ahp
    if len(left) < len(right):
        right = right[:len(left)]
    elif len(left) > len(right):
        left = left[:len(right)]

    return _evaluate(left, right, error=ErrorCalc.relative)

def interpolate(wave1, wave2):
    "Interpolate wave1 to wave2.x"
    y = np.interp(wave2.x, wave1.x, wave1.y)
    return np.rec.fromarrays((wave2.x, y), names='x,y')

def ahp_curve_centered(wave, i):
    windows = wave.spike_ahp_window
    if i >= len(windows):
        return None
    cut = windows[i]
    ahp_y = wave.spike_ahp[i]
    ahp_x = wave.spike_ahp_position[i]
    return cut.relative_to(ahp_x.x, ahp_y.x)

def ahp_curve_compare(cut1, cut2):
    """Returns a number from [0, 1] which compares how close they are.

    0 means the same, 1 means very different.
    """
    assert not cut1 is cut2 is None

    if cut1 is None or cut2 is None:
        return 1

    cut1i = interpolate(cut1, cut2)
    diff = np.tanh((cut1i.y - cut2.y) / cut2.y)
    diff[np.isnan(diff)] = np.nanmax(diff)
    return ((diff**2).sum()/diff.size)**0.5

def _pick_spikes(wave1, wave2):
    n = max(wave1.spike_count, wave2.spike_count)
    # let's compare max 10 spikes
    if n <= 10:
        return range(n)
    else:
        return np.linspace(0, n-1, 10, dtype=int)

def ahp_curve_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    m1, m2 = _select(sim, measurement,
                     sim.spike_count + measurement.spike_count > 0)

    diffs = [ahp_curve_compare(ahp_curve_centered(wave1, i),
                               ahp_curve_centered(wave2, i))
             for wave1, wave2 in zip(m1, m2)
             for i in _pick_spikes(wave1, wave2)]
    if not diffs:
        return 0

    assert 0 <= min(diffs) <= 1, diffs
    assert 0 <= max(diffs) <= 1, diffs

    diffs = np.array(diffs)
    if full:
        return diffs
    else:
        return ((diffs**2).sum()/diffs.size)**0.5

class WaveHistogram:
    """Compute the difference between cumulative histograms of two waves

    Since the x step might be different, we need to scale to the same
    range. This is done by doing a frequency histogram, which
    abstracts away the number of points in either plot.
    """
    def __init__(self, wave1, wave2, left=-np.inf, right=+np.inf):
        self.wave1 = wave1
        self.wave2 = wave2
        self.left = left
        self.right = right

    def x1(self):
        return self.wave1.x[(self.wave1.x >= self.left) & (self.wave1.x <= self.right)]
    def x2(self):
        return self.wave2.x[(self.wave2.x >= self.left) & (self.wave2.x <= self.right)]
    def y1(self):
        return self.wave1.y[(self.wave1.x >= self.left) & (self.wave1.x <= self.right)]
    def y2(self):
        return self.wave2.y[(self.wave2.x >= self.left) & (self.wave2.x <= self.right)]

    def hist(self, bins, y, cumulative=True):
        hist = np.histogram(y, bins=bins, density=True)[0]
        hist /= hist.sum()
        if cumulative:
            return np.cumsum(hist)
        else:
            return hist

    def bins(self, n=50):
        y1, y2 = self.y1(), self.y2()
        low = min(y1.min(), y2.min())
        high = max(y1.max(), y2.max())
        return np.linspace(low, high, n)

    def diff(self, full=False):
        bins = self.bins()
        hist1 = self.hist(bins, self.y1())
        hist2 = self.hist(bins, self.y2())
        diff = (hist2 - hist1) * bins.ptp()
        if full:
            return diff
        else:
            # we return something that is approximately the area betwen the CDFs
            return np.abs(diff).sum()

    def plot(self, figure):
        from matplotlib import pyplot

        ax1 = figure.add_subplot(121)
        ax2 = figure.add_subplot(122)
        ax1.plot(self.x1(), self.y1(), label='recording 1', color='blue')
        ax1.plot(self.x2(), self.y2(), label='recording 2', color='red')

        bins = self.bins()
        hist1 = self.hist(bins, self.y1())
        hist2 = self.hist(bins, self.y2())
        diff = self.diff(full=True)

        height = bins.ptp() / bins.size
        ax2.barh(bins[:-1], hist1, height=height, alpha=0.2, color='blue')
        ax2.barh(bins[:-1], hist2, height=height, alpha=0.2, color='red')

        bars = ax2.barh(bins[:-1], left=hist1, width=hist2-hist1,
                        height=height, color='none', edgecolor='black')
        for bar in bars:
            bar.set_hatch('x')

        ax2.set_title('cumulative histograms\ndiff={}'.format(np.abs(diff).sum()))
        ax2.yaxis.set_major_formatter(pyplot.NullFormatter())
        figure.tight_layout()
        return ax1, ax2

def spike_range_y_histogram_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    """Match histograms of y-values in spiking regions

    This returns an rms of `WaveHistogram.diff` over the injection
    region. Waves are filtered to have at at least one spike between
    the pair. This is done to make this fitness function sensitive to
    depolarization block. Otherwise, the result would be dominated by
    baseline mismatches and response mismatches.

    `baseline_post_fitness` and `response_fitness` are better fitted
    to detect mismatches in other regions.
    """
    m1, m2 = _select(sim, measurement)

    diffs = np.array([WaveHistogram(wave1.wave, wave2.wave,
                                    wave1.injection_start, wave1.injection_end).diff()
                      for wave1, wave2 in zip(m1, m2)
                      if max(wave1.spike_count, wave2.spike_count) > 0])

    if full:
        return diffs
    else:
        return (diffs**2).mean()**0.5

def parametrized_fitness(response=1, baseline=0.3, rectification=1,
                         falling_curve_param=1,
                         mean_isi=1, spike_latency=1,
                         spike_height=1, spike_width=1, spike_ahp=1,
                         error=ErrorCalc.relative):
    def fitness(sim, measurement):
        f1 = response_fitness(sim, measurement, error=error) if response else 0
        f2 = baseline_fitness(sim, measurement, error=error) if baseline else 0
        f3 = rectification_fitness(sim, measurement, error=error) if rectification else 0
        f4 = falling_curve_time_fitness(sim, measurement, error=error) if falling_curve_param else 0
        f5 = mean_isi_fitness(sim, measurement, error=error) if mean_isi else 0
        f6 = spike_latency_fitness(sim, measurement, error=error) if spike_latency else 0
        f7 = spike_height_fitness(sim, measurement, error=error) if spike_height else 0
        f8 = spike_width_fitness(sim, measurement, error=error) if spike_width else 0
        f9 = spike_ahp_fitness(sim, measurement, error=error) if spike_ahp else 0
        return (response * f1 / 16 +
                baseline * f2 / 35 +
                rectification * f3 / 3 +
                falling_curve_param * f4 / 0.70 +
                mean_isi * f5 / 5 +
                spike_latency * f6 / 0.10 +
                spike_height * f7 / 20 +
                spike_width * f8 / 10 +
                spike_ahp * f9 / 8)
    return fitness

def hyperpol_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    a = response_fitness(sim, measurement, error=error)
    b1 = baseline_pre_fitness(sim, measurement, error=error)
    b2 = baseline_post_fitness(sim, measurement, error=error)
    c = rectification_fitness(sim, measurement, error=error)
    d = falling_curve_time_fitness(sim, measurement, error=error)
    e = spike_count_fitness(sim, measurement, error=error)
    if error == ErrorCalc.normal:
        arr = np.array([a, b1/5, b2/5, c*4, d/20, e])
    else:
        arr = np.array([a, b1, b2, c, d, e])
    if full:
        return arr
    else:
        return (arr**2).mean()**0.5

def spike_fitness_0(sim, measurement, full=False, error=ErrorCalc.relative):
    a = mean_isi_fitness(sim, measurement, error=error)
    b = spike_latency_fitness(sim, measurement, error=error)
    c = spike_width_fitness(sim, measurement, error=error)
    d = spike_height_fitness(sim, measurement, error=error)
    e = spike_ahp_fitness(sim, measurement, error=error)
    f = spike_time_fitness(sim, measurement, error=error)
    arr = np.array([a, b, c, d, e, f])
    if full:
        return arr
    else:
        return (arr**2).mean()**0.5

def spike_fitness(sim, measurement, full=False, error=ErrorCalc.relative):
    a = spike_time_fitness(sim, measurement, error=error)
    b = spike_width_fitness(sim, measurement, error=error)
    c = spike_height_fitness(sim, measurement, error=error)
    d = spike_ahp_fitness(sim, measurement, error=error)
    arr = np.array([a, b, c, d])
    if full:
        return arr
    else:
        return (arr**2).mean()**0.5

class combined_fitness:
    """Basic weighted combinations of fitness functions
    """
    presets = {
        'empty' : collections.OrderedDict(),

        'new_combined_fitness' : collections.OrderedDict(
            response=1,
            baseline_pre=1,
            baseline_post=1,
            rectification=1,
            falling_curve_time=1,
            spike_time=1,
            spike_width=1,
            spike_height=1,
            spike_latency=1,
            spike_ahp=1,
            ahp_curve=1,
            spike_range_y_histogram=1),

        'simple_combined_fitness' : collections.OrderedDict(
            response=1,
            baseline=1,
            rectification=1,
            falling_curve_time=1,
            mean_isi=1,
            spike_latency=1,
            spike_height=1,
            spike_width=1,
            spike_ahp=1,
            spike_count=1,
            isi_spread=1),
    }

    @staticmethod
    def fitness_by_name(name):
        return globals()[name + '_fitness']

    def __init__(self,
                 preset='new_combined_fitness',
                 *,
                 error=ErrorCalc.relative,
                 extra=None,
                 **kwargs):
        """Creates a weighted combination of features.

        preset can be used to pick one of the starting sets of fitness
        functions and their weights. To modify the weight for one of
        the "known" functions from this module, the new weight can be
        passed as a keyword argument:

        >>> new_combined_fitness('new_combined_fitness', spike_latency=2.5)

        Arbitrary fitness functions can be given as (weight, function) pairs
        in extra:

        >>> def fitness1(sim, measurement, full=False, error=ErrorCalc.relative):
        ...   return 5
        >>> f = combined_fitness('empty',
        ...                      extra={fitness1 : 0.5})
        >>> print(f.report('a', 'b'))
        fitness1=0.5*5=2.5
        total: 2.5
        """

        self.error = error

        weights = self.presets[preset].copy()
        weights.update(kwargs)

        pairs1 = [(w, self.fitness_by_name(k))
                  for k, w in weights.items()]
        pairs2 = [(w, k) for k, w in extra.items()] if extra else []
        if set(f for w,f in pairs1).intersection(set(f for w,f in pairs2)):
            raise ValueError('"known" function specified in extra')
        self.pairs = pairs1 + pairs2

    def _parts(self, sim, measurement, *, full=False):
        for w, func in self.pairs:
            if w or full:
                yield (w, func(sim, measurement, error=self.error), func.__name__)

    def __call__(self, sim, measurement, full=False):
        parts = [w*r for w, r, name in self._parts(sim, measurement)]
        arr = np.array(parts)
        if full:
            return arr
        else:
            return (arr**2).mean()**0.5

    @property
    def __name__(self):
        return self.__class__.__name__

    def report(self, sim, measurement, *, full=False):
        parts = list(self._parts(sim, measurement, full=full))
        desc = '\n'.join('{}={}*{:.2g}={:.2g}'.format(name, w, r, w*r)
                         for w, r, name in parts)
        total = desc + '\n' + 'total: {:.02g}'.format(self.__call__(sim, measurement))
        return total

def fit_sort(group, measurement, fitness):
    w = np.array([fitness(sim, measurement) for sim in group])
    w[np.isnan(w)] = np.inf
    return np.array(group)[w.argsort()]

def fit_finished(fitness, cutoff=0.01, window=10):
    isdf = isinstance(fitness, pd.DataFrame)
    if not isdf:
        fitness = pd.DataFrame(fitness)
    dev = pd.rolling_var(fitness, window) ** 0.5
    quit = dev / dev.max() < cutoff
    if isdf:
        return quit
    else:
        return quit.values.flatten()

def find_best(group, measurement, fitness):
    w = np.array([fitness(sim, measurement) for sim in group])
    w[np.isnan(w)] = np.inf
    return group[w.argmin()]

def find_multi_best(group, measurement, fitness,
                    similarity=.10,
                    debug=False, full=False):
    best = np.empty(0, dtype=object)
    scores = np.empty(0)

    for sim in group:
        score = fitness(sim, measurement, full=1)

        # ignore misfits
        if np.isnan(score).any():
            if debug:
                print('dropping for nans:', sim)
            continue

        for i, key in enumerate(best):
            if (scores[i] < score).all():
                if debug:
                    print('dropping worse:', sim)
                break

        if scores.size:
            dominates = (score < scores).all(axis=1)
            if debug:
                print('dropping', dominates.sum(), 'dominated')
            best = np.hstack((best[-dominates], [sim]))
            scores = np.vstack((scores[-dominates], score))

        else:
            best = np.hstack([sim])
            scores = score[None, :]

    if similarity:
        # sort by rms
        total = (scores ** 2).sum(axis=1)
        order = total.argsort()
        best = best[order]
        scores = scores[order]
        worse = np.empty_like(best, dtype=bool)

        for i in reversed(range(best.size)):
            similar = scores[i] - scores[:i]
            worse[i] = ((similar ** 2).sum(axis=1) < total[i] * similarity).any()

        scores = scores[-worse]
        best = best[-worse]

    if full:
        return best, scores
    else:
        return best

def normalize_dimensions(vect):
    mean = np.mean(vect, axis=0)
    radius = np.ptp(vect, axis=0) / 2
    trivial = radius == 0 # ignore non-variable parameters
    return ((vect - mean) / radius).T[-trivial].T

find_nonsimilar_result = collections.namedtuple('find_nonsimilar_result', 'group scores params')

def find_nonsimilar(group, measurement, fitness,
                    similarity=.10):
    from . import analysis

    what = group[0].params.keys()
    params, scores = analysis.convert_to_values(group, measurement, fitness, *what, full=1)
    group = np.array(group, dtype=object)
    scores = np.array(scores)
    scores[np.isnan(scores)] = np.inf

    total = (scores ** 2).sum(axis=1)
    order = total.argsort()
    group = group[order]
    scores = scores[order]
    params = params[order]

    normalized = normalize_dimensions(params)

    # sort by rms
    duplicate = np.zeros_like(group, dtype=bool)

    for i in range(group.size - 1):
        if not duplicate[i]: # ignore the ones already ignored
            diff = ((normalized[i + 1:] - normalized[i])**2).sum(axis=1)**0.5
            duplicate[i + 1:] |= diff < similarity

    return find_nonsimilar_result(group[-duplicate], scores[-duplicate], params[-duplicate])
