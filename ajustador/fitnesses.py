from __future__ import print_function, division

import collections
import numpy as np
import pandas as pd

from . import loader

def sub_mes_dev(reca, recb, min_dev=.005):
    xy = (reca.x - recb.x, (recb.dev**2 + min_dev**2)**0.5)
    if isinstance(reca, loader.vartype):
        return loader.vartype(*xy)
    else:
        return np.rec.fromarrays(xy, names='x,dev')

def response_fitness(sim, measurement, full=False):
    "Similarity of response to hyperpolarizing injection"
    x1 = sim.injection
    meas = measurement[measurement.injection <= 110e-12]
    x2 = meas.injection
    fitting = np.abs(x1[:,None] - x2) < 1e-12
    ind1, ind2 = np.where(fitting)
    diff = sub_mes_dev(sim[ind1].response, meas[ind2].response)
    return loader.array_rms(diff)

def baseline_fitness(sim, measurement, full=False):
    "Similarity of baselines"
    x1 = sim.injection
    x2 = measurement.injection
    fitting = np.abs(x1[:,None] - x2) < 1e-12
    ind1, ind2 = np.where(fitting)
    diff = sub_mes_dev(sim[ind1].baseline, measurement[ind2].baseline)
    return loader.array_rms(diff)

def rectification_fitness(sim, measurement, full=False):
    x1 = sim.injection
    meas = measurement[measurement.injection <= -10e-12]
    x2 = meas.injection
    fitting = np.abs(x1[:,None] - x2) < 1e-12
    ind1, ind2 = np.where(fitting)
    diff = sub_mes_dev(sim[ind1].rectification, meas[ind2].rectification)
    return loader.array_rms(diff)

def charging_curve_fitness(sim, measurement, full=False):
    x1 = sim.injection
    meas = measurement[measurement.spike_count >= 1]
    x2 = meas.injection
    fitting = np.abs(x1[:,None] - x2) < 1e-12
    ind1, ind2 = np.where(fitting)
    diff = sim[ind1].charging_curve_halfheight - meas[ind2].charging_curve_halfheight
    return (diff**2).sum()**0.5

def falling_curve_time_fitness(sim, measurement, full=False):
    x1 = sim.injection
    meas = measurement[measurement.injection <= -10e-12]
    x2 = meas.injection
    fitting = np.abs(x1[:,None] - x2) < 1e-12
    ind1, ind2 = np.where(fitting)
    lefts = loader.vartype.array([wave.falling_curve_fit.params.tau for wave in sim[ind1]])
    rights = loader.vartype.array([wave.falling_curve_fit.params.tau for wave in measurement[ind2]])
    k = np.isnan(rights.x)
    rights[k].x = 0
    rights[k].dev = 1
    diff = loader.array_sub(lefts, rights)
    return loader.array_rms(diff)

def mean_isi_fitness(sim, measurement, full=False):
    x1 = sim.injection
    meas = measurement[measurement.spike_count >= 2]
    x2 = meas.injection
    fitting = np.abs(x1[:,None] - x2) < 1e-12
    ind1, ind2 = np.where(fitting)
    diff = sub_mes_dev(sim[ind1].mean_isi, meas[ind2].mean_isi)
    return loader.array_rms(diff)

def isi_spread_fitness(sim, measurement, full=False):
    x1 = sim.injection
    meas = measurement[measurement.spike_count >= 2]
    x2 = meas.injection
    fitting = np.abs(x1[:,None] - x2) < 1e-12
    ind1, ind2 = np.where(fitting)
    diff = sim[ind1].isi_spread - meas[ind2].isi_spread
    return (diff**2).mean()**0.5

def measurement_to_spikes(meas):
    frames = [pd.DataFrame(wave.spikes) for wave in meas]
    for frame, wave in zip(frames, meas):
        frame['injection'] = wave.injection
    return pd.concat(frames)

def spike_time_fitness(sim, measurement):
    x1 = sim.injection
    meas = measurement[measurement.spike_count >= 2]
    x2 = meas.injection
    fitting = np.abs(x1[:,None] - x2) < 1e-12
    ind1, ind2 = np.where(fitting)
    spikes1 = measurement_to_spikes(sim[ind1])
    spikes2 = measurement_to_spikes(meas[ind2])
    diff = spikes1 - spikes2
    diff.pop('injection')
    diff.fillna(sim[0].depolarization_interval, inplace=True)
    return (diff.x**2).mean()**0.5

def spike_count_fitness(sim, measurement):
    x1 = sim.injection
    x2 = measurement.injection
    fitting = np.abs(x1[:,None] - x2) < 1e-12
    ind1, ind2 = np.where(fitting)
    diff = sim[ind1].spike_count - measurement[ind2].spike_count
    return (diff**2).sum()**0.5

def spike_latency_fitness(sim, measurement):
    x1 = sim.injection
    meas = measurement[measurement.spike_count >= 1]
    x2 = meas.injection
    fitting = np.abs(x1[:,None] - x2) < 1e-12
    ind1, ind2 = np.where(fitting)
    diff = sim[ind1].spike_latency - meas[ind2].spike_latency
    return (diff**2).mean()**0.5

def spike_onset_fitness(sim, measurement):
    a = spike_latency_fitness(sim, measurement)
    b = charging_curve_fitness(sim, measurement)
    return (np.array([a, b])**2).mean()**0.5

def spike_width_fitness(sim, measurement):
    a = sub_mes_dev(sim.mean_spike_width, measurement.mean_spike_width)
    return (a.x / a.dev)**2

def spike_height_fitness(sim, measurement):
    a = sub_mes_dev(sim.mean_spike_height, measurement.mean_spike_height, 0.01)
    return (a.x / a.dev)**2

def spike_ahp_fitness(sim, measurement):
    a = sub_mes_dev(sim.mean_spike_ahp, measurement.mean_spike_ahp)
    return (a.x / a.dev)**2

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
