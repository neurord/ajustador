import numpy as np

from . import utilities, detect, loader
from .signal_smooth import smooth

def _plot_line(ax, ranges, value, color):
    for (a,b) in ranges:
        print(a, b, value, color)
        ax.hlines(value.x, a, b, color, linestyles='-', zorder=3)
        ax.hlines([value.x - 3*value.dev, value.x + 3*value.dev], a, b,
                  color, linestyles='--', zorder=3)

def array_mean(data):
    return loader.vartype(data.mean(), data.var(ddof=1)**0.5)

def array_diff(wave, n=1):
    xy = (wave.x[:n] + wave.x[n:])/n, np.diff(wave.y)
    return np.rec.fromarrays(xy, names='x,y')

class Baseline:
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

    def __init__(self, obj):
        self._obj = obj

    @property
    @utilities.once
    def baseline(self):
        wave = self._obj.wave
        before = self._obj.baseline_before
        after = self._obj.baseline_after

        what = wave.y[(wave.x < before) | (wave.x > after)]
        cutoffa, cutoffb = np.percentile(what, (5, 95))
        cut = what[(what > cutoffa) & (what < cutoffb)]
        return array_mean(cut)

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
        return array_mean(cut)

    @property
    @utilities.once
    def response(self):
        return self.steady - self.baseline

    def plot(self, figure):
        wave = self._obj.wave
        before = self._obj.baseline_before
        after = self._obj.baseline_after
        time = wave.x[-1]

        ax = figure.add_subplot(111)
        ax.plot(wave.x, wave.y, label='recording')
        ax.set_xlabel('time / s')
        ax.set_ylabel('membrane potential / V')

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
                    arrowprops=dict(facecolor='black'),
                    horizontalalignment='center', verticalalignment='bottom')

        ax.legend(loc='center right')
        figure.tight_layout()


def _find_spikes(wave, min_height=0.0):
    peaks = detect.detect_peaks(wave.y, P_low=0.75, P_high=0.20)
    return peaks[wave.y[peaks] > min_height]

class Spikes:
    """Find the position and height of spikes
    """
    requires = 'wave'
    provides = 'spike_i', 'spikes', 'spike_count'

    def __init__(self, obj):
        self._obj = obj

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

    def plot(self, figure):
        wave = self._obj.wave
        ax = figure.add_subplot(111)
        ax.plot(wave.x, wave.y, label='recording')
        ax.set_xlabel('time / s')
        ax.set_ylabel('membrane potential / V')

        ax.vlines(self.spikes.x, -0.06, self.spikes.y, 'r')
        ax.text(0.05, 0.5, '{} spikes'.format(self.spike_count),
                horizontalalignment='left',
                transform=ax.transAxes)
        figure.tight_layout()

        if self.spike_count > 0:
            ax2 = figure.add_axes([.7, .45, .25, .4])
            ax2.set_xlim(self.spikes.x[0] - 0.001, self.spikes.x[0] + 0.0015)
            ax2.plot(wave.x, wave.y, label='recording')
            ax2.vlines(self.spikes.x[:1], -0.06, self.spikes.y, 'r')
            ax2.tick_params(labelbottom='off', labelleft='off')
            ax2.set_title('first spike', fontsize='smaller')
