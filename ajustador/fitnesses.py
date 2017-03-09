from __future__ import print_function, division

import collections
import enum
import numpy as np
import pandas as pd

from . import vartype

class ErrorCalc(enum.Enum):
    normal = 1,
    relative = 2,

ERROR = ErrorCalc.normal

"If 'b' (measurement) is 0, limit to this value"
RELATIVE_MAX_RATIO = 10

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

    return (abs(x - y) / (abs(x) + abs(y) / RELATIVE_MAX_RATIO)
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

def _evaluate(a, b):
    if ERROR == ErrorCalc.normal:
        diff = sub_mes_dev(a, b)
        return vartype.array_rms(diff)
    elif ERROR == ErrorCalc.relative:
        diff = relative_diff(a, b)
        return vartype.array_rms(diff)
    else:
        raise AssertionError

def _evaluate_single(a, b):
    if ERROR == ErrorCalc.normal:
        return float(abs(a - b))
    elif ERROR == ErrorCalc.relative:
        return relative_diff_single(a, b)
    else:
        raise AssertionError

def response_fitness(sim, measurement, full=False):
    "Similarity of response to hyperpolarizing injection"
    m1, m2 = _select(sim, measurement, measurement.injection <= 110e-12)
    return _evaluate(m1.response, m2.response)

def baseline_fitness(sim, measurement, full=False):
    "Similarity of baselines"
    m1, m2 = _select(sim, measurement)
    return _evaluate(m1.baseline, m2.baseline)

def rectification_fitness(sim, measurement, full=False):
    m1, m2 = _select(sim, measurement, measurement.injection <= -10e-12)
    return _evaluate(m1.rectification, m2.rectification)

def charging_curve_fitness(sim, measurement, full=False):
    m1, m2 = _select(sim, measurement, measurement.spike_count >= 1)
    if len(m2) == 0:
        return vartype.vartype.nan
    return _evaluate(m1.charging_curve_halfheight, m2.charging_curve_halfheight)

def falling_curve_time_fitness(sim, measurement, full=False):
    m1, m2 = _select(sim, measurement, measurement.injection <= -10e-12)
    if len(m2) == 0:
        return vartype.vartype.nan
    return _evaluate(m1.falling_curve_tau, m2.falling_curve_tau)

def mean_isi_fitness(sim, measurement, full=False):
    m1, m2 = _select(sim, measurement, measurement.spike_count >= 2)
    if len(m2) == 0:
        return vartype.vartype.nan
    return _evaluate(m1.mean_isi, m2.mean_isi)

def isi_spread_fitness(sim, measurement, full=False):
    m1, m2 = _select(sim, measurement, measurement.spike_count >= 2)
    if len(m2) == 0:
        return vartype.vartype.nan
    return _evaluate(m1.isi_spread, m2.isi_spread)

def _measurement_to_spikes(meas):
    frames = [pd.DataFrame(wave.spikes) for wave in meas]
    for frame, wave in zip(frames, meas):
        frame['injection'] = wave.injection
    return pd.concat(frames)

def spike_time_fitness(sim, measurement):
    m1, m2 = _select(sim, measurement, measurement.spike_count >= 2)
    if len(m1) == 0:
        m1, m2 = _select(measurement, sim, sim.spike_count >= 2)
        if len(m1) == 0:
            # neither is spiking, cannot determine spike timing
            return np.nan

    spikes1 = _measurement_to_spikes(m1)
    spikes2 = _measurement_to_spikes(m2)
    diff = spikes1 - spikes2
    diff.pop('injection')
    diff.fillna(sim[0].injection_interval, inplace=True)
    # FIXME
    return (diff.x**2).mean()**0.5

def spike_count_fitness(sim, measurement):
    m1, m2 = _select(sim, measurement)
    return _evaluate(m1.spike_count, m2.spike_count)

def spike_latency_fitness(sim, measurement):
    m1, m2 = _select(sim, measurement, measurement.spike_count >= 1)
    return _evaluate(m1.spike_latency, m2.spike_latency)

def spike_width_fitness(sim, measurement):
    return _evaluate_single(sim.mean_spike_width, measurement.mean_spike_width)

def spike_height_fitness(sim, measurement):
    return _evaluate_single(sim.mean_spike_height, measurement.mean_spike_height)

def spike_ahp_fitness(sim, measurement):
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

    return _evaluate(left, right)

def parametrized_fitness(response=1, baseline=0.3, rectification=1,
                         falling_curve_param=1,
                         mean_isi=1, spike_latency=1,
                         spike_height=1, spike_width=1, spike_ahp=1):
    def fitness(sim, measurement):
        f1 = response_fitness(sim, measurement) if response else 0
        f2 = baseline_fitness(sim, measurement) if baseline else 0
        f3 = rectification_fitness(sim, measurement) if rectification else 0
        f4 = falling_curve_time_fitness(sim, measurement) if falling_curve_param else 0
        f5 = mean_isi_fitness(sim, measurement) if mean_isi else 0
        f6 = spike_latency_fitness(sim, measurement) if spike_latency else 0
        f7 = spike_height_fitness(sim, measurement) if spike_height else 0
        f8 = spike_width_fitness(sim, measurement) if spike_width else 0
        f9 = spike_ahp_fitness(sim, measurement) if spike_ahp else 0
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

def hyperpol_fitness(sim, measurement, full=False):
    a = response_fitness(sim, measurement)
    b = baseline_fitness(sim, measurement) / 5
    c = rectification_fitness(sim, measurement) * 4
    d = falling_curve_time_fitness(sim, measurement) / 20
    e = spike_count_fitness(sim, measurement)
    arr = np.array([a, b, c, d, e])
    if full:
        return arr
    else:
        return (arr**2).mean()**0.5

def spike_fitness_0(sim, measurement, full=False):
    a = mean_isi_fitness(sim, measurement)
    b = spike_latency_fitness(sim, measurement)
    c = spike_width_fitness(sim, measurement)
    d = spike_height_fitness(sim, measurement)
    e = spike_ahp_fitness(sim, measurement)
    f = spike_time_fitness(sim, measurement)
    arr = np.array([a, b, c, d, e, f])
    if full:
        return arr
    else:
        return (arr**2).mean()**0.5

def spike_fitness(sim, measurement, full=False):
    a = spike_time_fitness(sim, measurement)
    b = spike_width_fitness(sim, measurement)
    c = spike_height_fitness(sim, measurement)
    d = spike_ahp_fitness(sim, measurement)
    arr = np.array([a, b, c, d])
    if full:
        return arr
    else:
        return (arr**2).mean()**0.5

def new_combined_fitness(sim, measurement, full=False):
    a = response_fitness(sim, measurement)
    b = baseline_fitness(sim, measurement)
    c = 2 * rectification_fitness(sim, measurement)
    d = falling_curve_time_fitness(sim, measurement)
    e = spike_time_fitness(sim, measurement)
    f = spike_width_fitness(sim, measurement)
    g = spike_height_fitness(sim, measurement)
    h = spike_ahp_fitness(sim, measurement)
    arr = np.array([a, b, c, d, e, f, g, h])
    if full:
        return arr
    else:
        return (arr**2).mean()**0.5


def simple_combined_fitness(sim, measurement, full=False):
    arr = np.fromiter((f(sim, measurement)**2 for f in
                        [response_fitness,
                         baseline_fitness,
                         rectification_fitness,
                         falling_curve_time_fitness,
                         mean_isi_fitness,
                         spike_latency_fitness,
                         spike_height_fitness,
                         spike_width_fitness,
                         spike_ahp_fitness,
                         spike_count_fitness,
                         isi_spread_fitness]), dtype=float)
    if full:
        return arr
    else:
        return (np.nansum(arr**2) / arr.size)**0.5

combined_fitness = simple_combined_fitness

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
