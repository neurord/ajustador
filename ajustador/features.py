from collections import namedtuple
import numpy as np
from scipy import optimize

from . import utilities, detect, vartype
from .signal_smooth import smooth

def _plot_line(ax, ranges, value, color, zorder=3):
    for (a,b) in ranges:
        ax.hlines(float(value), a, b, color, linestyles='-', zorder=zorder)
        if isinstance(value, vartype.vartype):
            ax.hlines([value.x - 3*value.dev, value.x + 3*value.dev], a, b,
                      color, linestyles='--', zorder=zorder)

def plural(n, word):
    return '{} {}{}'.format(n, word, '' if n == 1 else 's')

class Feature:
    def __init__(self, obj):
        self._obj = obj

    def plot(self, figure):
        wave = self._obj.wave

        ax = figure.add_subplot(111)
        ax.plot(wave.x, wave.y, label='recording')
        ax.set_xlabel('time / s')
        ax.set_ylabel('membrane potential / V')
        return ax

class SteadyState(Feature):
    """Find the baseline and injection steady states

    The range *before* `baseline_before` and *after* `baseline_after`
    is used for `baseline`.

    The range *between* `steady_after` and `steady_before` is used
    for `steady`.
    """
    requires = ('wave',
                'baseline_before', 'baseline_after',
                'steady_after', 'steady_before', 'steady_cutoff')
    provides = 'baseline', 'steady', 'response'

    @property
    @utilities.once
    def baseline(self):
        wave = self._obj.wave
        before = self._obj.baseline_before
        after = self._obj.baseline_after

        what = wave.y[(wave.x < before) | (wave.x > after)]
        cutoffa, cutoffb = np.percentile(what, (5, 95))
        cut = what[(what > cutoffa) & (what < cutoffb)]
        return vartype.array_mean(cut)

    @property
    @utilities.once
    def steady(self):
        wave = self._obj.wave
        after = self._obj.steady_after
        before = self._obj.steady_before
        cutoff = self._obj.steady_cutoff

        data = wave.y[(wave.x > after) & (wave.x < before)]
        cutoff = np.percentile(data, cutoff)
        cut = data[data < cutoff]
        return vartype.array_mean(cut)

    @property
    @utilities.once
    def response(self):
        return self.steady - self.baseline

    def plot(self, figure):
        wave = self._obj.wave
        before = self._obj.baseline_before
        after = self._obj.baseline_after
        time = wave.x[-1]

        ax = super().plot(figure)
        _plot_line(ax,
                   [(0, before), (after, time)],
                   self.baseline,
                   'k')
        _plot_line(ax,
                   [(after, before)],
                   self.steady,
                   'r')
        ax.annotate('response',
                    xy=(time/2, self.steady.x),
                    xytext=(time/2, self.baseline.x),
                    arrowprops=dict(facecolor='black',
                                    shrink=0),
                    horizontalalignment='center', verticalalignment='bottom')

        ax.legend(loc='center right')
        figure.tight_layout()


def _find_spikes(wave, min_height=0.0):
    peaks = detect.detect_peaks(wave.y, P_low=0.75, P_high=0.20)
    return peaks[wave.y[peaks] > min_height]

class Spikes(Feature):
    """Find the position and height of spikes
    """
    requires = 'wave',
    provides = ('spike_i', 'spikes', 'spike_count',
                'mean_isi', 'isi_spread',
                'spike_latency',
                'spike_bounds', 'spike_width',
                'mean_spike_height')

    @property
    @utilities.once
    def spike_i(self):
        "Indices of spike maximums in the wave.x, wave.y arrays"
        return _find_spikes(self._obj.wave)

    @property
    @utilities.once
    def spikes(self):
        "An array with .x and .y components marking the spike maximums"
        return self._obj.wave[self.spike_i]

    @property
    def spike_count(self):
        "The number of spikes"
        return len(self.spike_i)

    mean_isi_fallback_variance = 0.001

    @property
    @utilities.once
    def mean_isi(self):
        """The mean interval between spikes

        Defined as:

        * :math:`<x_{i+1} - x_i>`, if there are at least two spikes,
        * the length of the depolarization interval otherwise (`depolarization_interval`)

        If there less than three spikes, the variance is fixed as
        `mean_isi_fallback_variance`.
        """
        if self.spike_count > 2:
            return vartype.array_mean(np.diff(self.spikes.x))
        elif self.spike_count == 2:
            d = self.spikes.x[1]-self.spikes.x[0]
            return vartype.vartype(d, 0.001)
        else:
            return vartype.vartype(self._obj.depolarization_interval, 0.001)

    @property
    @utilities.once
    def isi_spread(self):
        """The difference between the largest and smallest inter-spike intervals

        Only defined when `spike_count` is at least 3.
        """
        if len(self.spikes) > 2:
            diff = np.diff(self.spikes.x)
            return diff.ptp()
        else:
            return np.nan

    @property
    @utilities.once
    def spike_latency(self):
        "Latency until the first spike or end of injection if no spikes"
        # TODO: add spike_latency to plot
        if len(self.spikes) > 0:
            return self.spikes[0].x
        else:
            return self.wave.x[-1]

    @property
    @utilities.once
    def spike_bounds(self):
        "The halfheight left and right positions of spikes"
        steady = self._obj.steady.x

        ans = np.empty((self.spike_count, 2), dtype=float)
        x = self._obj.wave.x
        y = self._obj.wave.y
        halfheight = (self.spikes.y - steady) / 2 + steady

        for i, k in enumerate(self.spike_i):
            beg = end = k
            while beg > 1 and y[beg - 1] > halfheight[i]:
                beg -= 1
            while end + 2 < y.size and y[end + 1] > halfheight[i]:
                end += 1
            ans[i] = (x[beg-1] + x[beg])/2, (x[end] + x[end+1])/2
        return ans

    @property
    @utilities.once
    def spike_width(self):
        return self.spike_bounds[:, 1] - self.spike_bounds[:, 0]

    @property
    @utilities.once
    def mean_spike_height(self):
        "The mean absolute position of spike vertices"
        # TODO: is the variance too big?
        return vartype.array_mean(self.spikes.y)

    def plot(self, figure):
        wave = self._obj.wave
        ax = super().plot(figure)
        bottom = -0.06 # self._obj.steady.x
                       # Doing the "proper" thing makes the plot hard to read

        ax.vlines(self.spikes.x, bottom, self.spikes.y, 'r')
        ax.text(0.05, 0.5, plural(self.spike_count, 'spike'),
                horizontalalignment='left',
                transform=ax.transAxes)

        _plot_line(ax,
                   [(self._obj.steady_after, self._obj.steady_before)],
                   self.mean_spike_height,
                   'y', zorder=0)

        figure.tight_layout()

        if self.spike_count > 0:
            x = self.spikes.x
            ax2 = figure.add_axes([.7, .45, .25, .4])
            ax2.set_xlim(x[0] - 0.001, x[0] + 0.0015)
            ax2.plot(wave.x, wave.y, label='recording')
            ax2.vlines(x[:1], bottom, self.spikes.y, 'r', zorder=3)
            ax2.tick_params(labelbottom='off', labelleft='off')
            ax2.set_title('first spike', fontsize='smaller')

            w = self.spike_bounds
            ax2.axvspan(*w[0], alpha=0.3, color='cyan')

def _find_falling_curve(wave, window=20, after=0.2, before=0.6):
    d = vartype.array_diff(wave)
    dd = smooth(d.y, window='hanning')[(d.x > after) & (d.x < before)]
    start = end = dd.argmin() + (d.x <= after).sum()
    while start > 0 and wave[start - 1].y > wave[start].y and wave[start].x > after:
        start -= 1
    sm = smooth(wave.y, window='hanning')
    smallest = sm[end]
    # find minimum
    while (end+window < wave.size and wave[end+window].x < before
           and sm[end:end + window].min() < smallest):
        smallest = sm[end]
        end += window // 2
    ccut = wave[start + 1 : end]
    return ccut

def simple_exp(x, amp, tau):
    return float(amp) * np.exp(-(x-x[0]) / float(tau))
def negative_exp(x, amp, tau):
    return float(amp) * (1-np.exp(-(x-x[0]) / float(tau)))

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
        params = falling_param(vartype.vartype(popt[0], pcov[0,0]**0.5),
                               vartype.vartype(popt[1], pcov[1,1]**0.5))
    return function_fit(func, params)


class FallingCurve(Feature):
    requires = ('wave',
                'steady_before', 'baseline_before',
                'falling_curve_window',
                 'baseline', 'steady')
    provides = 'falling_curve',

    @property
    @utilities.once
    def falling_curve(self):
        return _find_falling_curve(self._obj.wave,
                                   window=self._obj.falling_curve_window,
                                   before=self._obj.steady_before)

    @property
    @utilities.once
    def falling_curve_fit(self):
        return _fit_falling_curve(self.falling_curve, self._obj.baseline, self._obj.steady)

    def plot(self, figure):
        ax = super().plot(figure)

        ccut = self.falling_curve
        baseline = self._obj.baseline
        steady = self._obj.steady
        ax.plot(ccut.x, ccut.y, 'r', label='falling curve')
        ax.set_xlim(self._obj.baseline_before - 0.005, ccut.x.max() + .01)

        func, popt = self.falling_curve_fit
        label = 'fitted {}'.format(func.__name__)
        ax.plot(ccut.x, baseline.x + func(ccut.x, *popt), 'g--', label=label)

        ax.legend(loc='upper right')
        figure.tight_layout()


class Rectification(Feature):
    requires = ('baseline_before', 'steady_after', 'steady_before',
                'falling_curve', 'steady')
    provides = 'rectification',

    window_len = 11

    @property
    @utilities.once
    def rectification(self):
        ccut = self._obj.falling_curve
        steady = self._obj.steady

        if ccut.size < self.window_len + 1:
            return vartype.vartype(np.nan)
        pos = ccut.y.argmin()
        end = max(pos + self.window_len//2, ccut.size-1)
        bottom = vartype.array_mean(ccut[end-self.window_len : end+self.window_len+1].y)
        return steady - bottom

    def plot(self, figure):
        ax = super().plot(figure)

        ccut = self._obj.falling_curve
        after = self._obj.steady_after
        before = self._obj.steady_before
        steady = self._obj.steady

        ax.set_xlim(self._obj.baseline_before - 0.005, before)

        _plot_line(ax,
                   [(after, before)],
                   steady,
                   'r')
        right = (after + before) / 2
        bottom = steady.x - self.rectification.x
        _plot_line(ax,
                   [(after, right)],
                   bottom,
                   'g')
        ax.annotate('rectification',
                    xytext=(right, bottom),
                    xy=(right, self._obj.steady.x),
                    arrowprops=dict(facecolor='black'),
                    horizontalalignment='center', verticalalignment='top')

        ax.legend(loc='upper right')
        figure.tight_layout()


class ChargingCurve(Feature):
    requires = ('wave', 'steady_after', 'steady', 'spikes', 'spike_count')
    provides = 'charging_curve_halfheight',

    @property
    @utilities.once
    def charging_curve_halfheight(self):
        "The height in the middle between depolarization start and first spike"
        if self._obj.spike_count < 1:
            return np.nan
        else:
            wave = self._obj.wave
            steady_after = self._obj.steady_after
            spike0 = self._obj.spikes[0]

            what = wave[(wave.x > steady_after) & (wave.x < spike0.x)]
            return np.median(what.y)

    def plot(self, figure):
        ax = super().plot(figure)

        after = self._obj.steady_after
        steady = self._obj.steady

        if np.isnan(self.charging_curve_halfheight):
            ax.text(0.05, 0.5, 'cannot determine charging curve',
                    horizontalalignment='left',
                    transform=ax.transAxes)
            before = self._obj.wave.x[-1]
        else:
            before = self._obj.spikes[0].x
            ax.set_xlim(after - 0.005, before + 0.005)
            _plot_line(ax,
                       [(after, before)],
                       self.charging_curve_halfheight,
                       'g')

        _plot_line(ax,
                   [(after, before)],
                   steady,
                   'r')

        ax.legend(loc='upper right')
        figure.tight_layout()


standard_features = (
                SteadyState,
                Spikes,
                FallingCurve,
                Rectification,
                ChargingCurve,
    )
