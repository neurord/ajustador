import math
from collections import namedtuple
import numpy as np
from scipy import optimize

from . import utilities, detect, vartype
from .signal_smooth import smooth

def _plot_line(ax, ranges, value, label, color, zorder=3):
    for (a,b) in ranges:
        ax.plot([a, b], [float(value)]*2,
                label=label, color=color, linestyle='-', zorder=zorder)
        label = None # we only need one line labeled
        if isinstance(value, vartype.vartype):
            ax.plot([a, b], [value.x - 3*value.dev]*2,
                      color, linestyle='--', zorder=zorder)
            ax.plot([a, b], [value.x + 3*value.dev]*2,
                      color, linestyle='--', zorder=zorder)

def _plot_spike(ax, wave, spikes, i, bottom=None, spike_bounds=None, lmargin=0.0010, rmargin=0.0015):
    ax.set_xlim(spikes.x[i] - lmargin, spikes.x[i] + rmargin)
    ax.plot(wave.x, wave.y, label='recording')
    if bottom is not None:
        ax.vlines(spikes.x[i:i+1], bottom, spikes.y, 'r', zorder=3)
    if spike_bounds is not None:
        ax.axvspan(spike_bounds[i].left, spike_bounds[i].right,
                   alpha=0.3, color='cyan')

def plural(n, word):
    return '{} {}{}'.format(n, word, '' if n == 1 else 's')

class Feature:
    requires = ()
    provides = ()
    array_attributes = ()
    mean_attributes = ()

    def __init__(self, obj):
        self._obj = obj

    def plot(self, figure):
        wave = self._obj.wave

        ax = figure.add_subplot(111)
        ax.plot(wave.x, wave.y, label='recording')
        ax.set_xlabel('time / s')
        ax.set_ylabel('membrane potential / V')
        return ax

    def spike_plot(self, figure, bottom=None, spike_bounds=None,
                   lmargin=0.0010, rmargin=0.0015, rowsize=3):
        wave = self._obj.wave
        spikes = self._obj.spikes

        spike_count = len(spikes)
        rows = math.ceil(spike_count / rowsize)
        columns = min(spike_count, rowsize)

        axes = []
        sharey = None
        for i in range(spike_count):
            ax = figure.add_subplot(rows, columns, i+1, sharey=sharey)
            if i == 0:
                sharey = ax
            else:
                ax.tick_params(labelleft='off')
            axes.append(ax)

            _plot_spike(ax, wave, spikes, i, bottom=bottom, spike_bounds=spike_bounds,
                        lmargin=lmargin, rmargin=rmargin)

        figure.autofmt_xdate()
        return axes

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
    provides = ('baseline', 'steady', 'response')

    mean_attributes = ('baseline', 'steady', 'response')
    array_attributes = ('baseline', 'steady', 'response')

    @property
    @utilities.once
    def baseline(self):
        """The mean voltage of the area outside of injection interval

        Returns mean value of wave after excluding "outliers", values
        > 95th or < 5th percentile.
        """
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
        """Returns mean value of wave between `steady_after` and `steady_before`.

        "Outliers", values > 80th percentile (which is a parameter), are excluded.
        80th percentile excludes the spikes.
        """
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
                   'baseline', 'k')
        _plot_line(ax,
                   [(after, before)],
                   self.steady,
                   'steady', 'r')
        ax.annotate('response',
                    xy=(time/2, self.steady.x),
                    xytext=(time/2, self.baseline.x),
                    arrowprops=dict(facecolor='black',
                                    shrink=0),
                    horizontalalignment='center', verticalalignment='bottom')

        ax.legend(loc='center right')
        figure.tight_layout()


peak_and_threshold = namedtuple('peak_and_threshold', 'peaks thresholds')

def _find_spikes(wave, min_height=0.0, max_charge_time=0.004, charge_threshold=0.02):
    peaks = detect.detect_peaks(wave.y, P_low=0.75, P_high=0.50)
    peaks = peaks[wave.y[peaks] > min_height]

    thresholds = np.empty(peaks.size)
    for i in range(len(peaks)):
        start = (wave.x >= wave.x[peaks[i]] - max_charge_time).argmax()
        x = wave.x[start:peaks[i] + 1]
        y = wave.y[start:peaks[i] + 1]
        yderiv = np.diff(y)
        #spike threshold is point where derivative is 2% of steepest
        ythresh = charge_threshold * yderiv.max()
        thresh = y[1:][yderiv > ythresh].min()
        thresholds[i] = thresh
    return peak_and_threshold(peaks, thresholds)

class WaveRegion:
    def __init__(self, wave, left_i, right_i):
        self._wave = wave
        self.left_i = left_i
        self.right_i = right_i

    @property
    def left(self):
        "x coordinate of the left edge of FWHM"
        return self._wave.x[self.left_i-1:self.left_i+1].mean()

    @property
    def right(self):
        "x coordinate of the right edge of FWHM"
        return self._wave.x[self.right_i:self.right_i+2].mean()

    @property
    def width(self):
        return self.right - self.left

    def min(self):
        return self._wave.y[self.left_i : self.right_i+1].min()

class Spikes(Feature):
    """Find the position and height of spikes
    """
    requires = ('wave', 'injection_interval', 'injection_start')
    provides = ('spike_i', 'spikes', 'spike_count',
                'spike_threshold',
                'mean_isi', 'isi_spread',
                'spike_latency',
                'spike_bounds',
                'spike_height', 'spike_width',
                'mean_spike_height', # TODO: is it OK to have mean_spike_height as
                                     #       here and as an aggregated attribute?
                )
    array_attributes = ('spike_count',
                        'spike_height', 'spike_width',
                        'mean_isi', 'isi_spread',
                        'spike_latency')
    mean_attributes = ('spike_height', 'spike_width')

    @property
    @utilities.once
    def spike_i_and_threshold(self):
        "Indices of spike maximums in the wave.x, wave.y arrays"
        return _find_spikes(self._obj.wave)

    @property
    def spike_i(self):
        "Indices of spike maximums in the wave.x, wave.y arrays"
        return self.spike_i_and_threshold.peaks

    @property
    def spike_threshold(self):
        "Indices of spike maximums in the wave.x, wave.y arrays"
        return self.spike_i_and_threshold.thresholds

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
        * the length of the depolarization interval otherwise (`injection_interval`)

        If there less than three spikes, the variance is fixed as
        `mean_isi_fallback_variance`.
        """
        if self.spike_count > 2:
            return vartype.array_mean(np.diff(self.spikes.x))
        elif self.spike_count == 2:
            d = self.spikes.x[1]-self.spikes.x[0]
            return vartype.vartype(d, 0.001)
        else:
            return vartype.vartype(self._obj.injection_interval, 0.001)

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
        "Latency until the first spike or nan if no spikes"
        # TODO: add spike_latency to plot
        if len(self.spikes) > 0:
            return self.spikes[0].x - self._obj.injection_start
        else:
            return np.nan

    @property
    @utilities.once
    def spike_bounds(self):
        "The FWHM box and other measurements for each spike"
        spikes, thresholds = self.spike_i_and_threshold

        ans = []
        y = self._obj.wave.y
        halfheight = (self.spikes.y - thresholds) / 2 + thresholds

        for i, k in enumerate(self.spike_i):
            beg = end = k
            while beg > 1 and y[beg - 1] > halfheight[i]:
                beg -= 1
            while end + 2 < y.size and y[end + 1] > halfheight[i]:
                end += 1
            ans.append(WaveRegion(self._obj.wave, beg, end))
        return ans

    @property
    @utilities.once
    def spike_height(self):
        "The difference between spike peaks and spike threshold"
        spikes, thresholds = self.spike_i_and_threshold
        height = self.spikes.y - thresholds
        return height

    @property
    @utilities.once
    def spike_width(self):
        return np.array([bounds.width for bounds in self.spike_bounds])

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
                   'spike_height', 'y', zorder=0)
        ax.legend(loc='upper left')
        figure.tight_layout()

        if self.spike_count > 0:
            ax2 = figure.add_axes([.7, .45, .25, .4])
            ax2.tick_params(labelbottom='off', labelleft='off')
            ax2.set_title('first spike', fontsize='smaller')

            _plot_spike(ax2, wave, self.spikes, i=0,
                        bottom=-0.06, spike_bounds=self.spike_bounds)

    def spike_plot(self, figure, **kwargs):
        x = self._obj.spikes.x.mean()
        spike_bounds = self.spike_bounds
        thresholds = self.spike_threshold
        height = self.spike_height

        lmargin = self.spike_width.max()
        rmargin = self.spike_width.max() * 2

        axes = super().spike_plot(figure,
                                  spike_bounds=spike_bounds,
                                  lmargin=lmargin, rmargin=rmargin,
                                  **kwargs)

        for i in range(self.spike_count):
            y = thresholds[i] + height[i] / 2
            axes[i].annotate('FWHM',
                             xy=(spike_bounds[i].left, y),
                             xytext=(spike_bounds[i].right, y),
                             arrowprops=dict(facecolor='black',
                                             shrink=0),
                             verticalalignment='bottom')

            axes[i].axhline(thresholds[i], color='green', linestyle='--', linewidth=0.3)

class AHP(Feature):
    """Find the depth of "after hyperpolarization"
    """
    requires = ('wave',
                'injection_start', 'injection_end', 'injection_interval',
                'spikes', 'spike_count', 'spike_bounds', 'spike_threshold')
    provides = ('spike_ahp_window', 'spike_ahp')
    array_attributes = ('spike_ahp_window', 'spike_ahp')
    mean_attributes = ('spike_ahp',)

    @property
    @utilities.once
    def spike_ahp_window(self):
        spikes = self._obj.spikes
        bounds = self._obj.spike_bounds
        thresholds = self._obj.spike_threshold
        injection_end = self._obj.injection_end

        x = self._obj.wave.x
        y = self._obj.wave.y
        ans = []
        for i in range(len(spikes)):
            rlimit = bounds[i+1].left if i < len(spikes)-1 else injection_end

            beg = bounds[i].right_i
            while y[beg] >= thresholds[i] and x[beg + 1] < rlimit:
                beg += 1

            end = beg
            while (y[end] < thresholds[i] or end - beg < 5) and x[end] < rlimit:
                end += 1

            ans.append(WaveRegion(self._obj.wave, beg, end))

        return ans

    @property
    @utilities.once
    def spike_ahp(self):
        return np.array([window.min() for window in self.spike_ahp_window])

    def _do_plots(self, axes):
        spikes = self._obj.spikes
        thresholds = self._obj.spike_threshold
        windows = self.spike_ahp_window
        low, high = np.inf, -np.inf

        for i in range(self._obj.spike_count):
            window = windows[i]
            x = spikes.x[i]
            width = window.right - x

            _plot_line(axes[i],
                       [(window.left - width/2, window.left + width/2)],
                       thresholds[i],
                       'spike threshold', 'green')
            _plot_line(axes[i],
                       [(x, window.right)],
                       window.min(),
                       'AHP lower edge', 'magenta')

            axes[i].annotate('AHP',
                             xytext=(x + width/2, window.min()),
                             xy=(x + width/2, thresholds[i]),
                             arrowprops=dict(facecolor='black',
                                             shrink=0),
                             horizontalalignment='center', verticalalignment='top')
            diff = thresholds[i] - window.min()
            low = min(window.min() - diff*0.05, low)
            high = max(thresholds[i] + diff*0.05, high)

            axes[i].set_ylim(low, high)

    def plot(self, figure):
        ax = super().plot(figure)
        ax.set_xlim(self._obj.injection_start - self._obj.injection_interval*0.05,
                    self._obj.injection_end + self._obj.injection_interval*0.05)
        if self._obj.spike_count == 0:
            ax.text(0.5, 0.5, 'no spikes',
                    horizontalalignment='center',
                    transform=ax.transAxes)
        else:
            self._do_plots([ax] * self._obj.spike_count)
        figure.tight_layout()

    def spike_plot(self, figure, **kwargs):
        spike_bounds = self._obj.spike_bounds

        axes = super().spike_plot(figure, **kwargs)
        self._do_plots(axes)

        for i in range(self._obj.spike_count):
            l = spike_bounds[i].left
            r = self.spike_ahp_window[i].right
            diff = r - l
            axes[i].set_xlim(l - diff*0.15, r + diff*0.15)

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
function_fit = namedtuple('function_fit', 'function params good')

def _fit_falling_curve(ccut, baseline, steady):
    if ccut.size < 5 or not (steady-baseline).negative:
        func = None
        params = falling_param(vartype.vartype.nan,
                               vartype.vartype.nan)
        good = False
    else:
        init = (ccut.y.min()-baseline.x, ccut.x.ptp())
        func = negative_exp
        popt, pcov = optimize.curve_fit(func, ccut.x, ccut.y-baseline.x, (-1,1))
        pcov = np.zeros((2,2)) + pcov
        params = falling_param(vartype.vartype(popt[0], pcov[0,0]**0.5),
                               vartype.vartype(popt[1], pcov[1,1]**0.5))
        good = params.amp.negative and params.tau.positive
    return function_fit(func, params, good)


class FallingCurve(Feature):
    requires = ('wave',
                'steady_before', 'baseline_before',
                'falling_curve_window',
                 'baseline', 'steady')
    provides = ('falling_curve', 'falling_curve_fit',
                'falling_curve_amp', 'falling_curve_tau',
                'falling_curve_function')
    array_attributes = ('falling_curve_amp', 'falling_curve_tau',
                        'falling_curve_function')

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

    @property
    def falling_curve_amp(self):
        fit = self.falling_curve_fit
        return fit.params.amp if fit.good else np.nan

    @property
    def falling_curve_tau(self):
        fit = self.falling_curve_fit
        return fit.params.tau if fit.good else np.nan

    @property
    def falling_curve_function(self):
        fit = self.falling_curve_fit
        return fit.function if fit.good else None

    def plot(self, figure):
        ax = super().plot(figure)

        ccut = self.falling_curve
        baseline = self._obj.baseline
        steady = self._obj.steady
        ax.plot(ccut.x, ccut.y, 'r', label='falling curve')
        ax.set_xlim(self._obj.baseline_before - 0.005, ccut.x.max() + .01)

        func, popt, good = self.falling_curve_fit
        if good:
            label = 'fitted {}'.format(func.__name__)
            ax.plot(ccut.x, baseline.x + func(ccut.x, *popt), 'g--', label=label)
        else:
            ax.text(0.2, 0.5, 'bad fit',
                    horizontalalignment='center',
                    transform=ax.transAxes,
                    color='red')

        ax.legend(loc='upper right')
        figure.tight_layout()


class Rectification(Feature):
    requires = ('baseline_before', 'steady_after', 'steady_before',
                'falling_curve', 'steady')
    provides = 'rectification',
    array_attributes = 'rectification',
    mean_attributes = 'rectification',

    window_len = 11

    @property
    @utilities.once
    def rectification(self):
        ccut = self._obj.falling_curve
        steady = self._obj.steady

        if ccut.size < self.window_len + 1:
            return vartype.vartype.nan
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
                   'steady', 'r')
        right = (after + before) / 2
        bottom = steady.x - self.rectification.x
        if np.isnan(bottom):
            ax.text(0.5, 0.5, 'rectification not detected',
                    horizontalalignment='center',
                    transform=ax.transAxes,
                    color='red')
        else:
            _plot_line(ax,
                       [(after, right)],
                       bottom,
                       'rectification bottom', 'g')
            ax.annotate('rectification',
                        xytext=(right, bottom),
                        xy=(right, self._obj.steady.x),
                        arrowprops=dict(facecolor='black',
                                        shrink=0),
                        horizontalalignment='center', verticalalignment='top')

        ax.legend(loc='upper right')
        figure.tight_layout()


class ChargingCurve(Feature):
    requires = ('wave', 'injection_start',
                'baseline', 'baseline_before',
                'spikes', 'spike_count', 'spike_threshold')
    provides = 'charging_curve_halfheight',
    array_attributes = 'charging_curve_halfheight',

    @property
    @utilities.once
    def charging_curve_halfheight(self):
        "The height in the middle between depolarization start and first spike"
        ccut = self.charging_curve
        if ccut is None:
            return vartype.vartype.nan

        baseline = self._obj.baseline
        return np.median(ccut.y) - baseline

    @property
    @utilities.once
    def charging_curve(self):
        if self._obj.spike_count < 1:
            return None
        wave = self._obj.wave
        injection_start = self._obj.injection_start
        spike0 = self._obj.spikes[0]
        baseline = self._obj.baseline
        threshold = self._obj.spike_threshold[0]

        what = wave[(wave.x > injection_start) & (wave.x < spike0.x)]
        what = what[what.y < threshold]
        return what

    def plot(self, figure):
        ax = super().plot(figure)
        baseline = self._obj.baseline

        ccut = self.charging_curve
        if ccut is None:
            ax.text(0.05, 0.5, 'cannot determine charging curve',
                    horizontalalignment='left',
                    transform=ax.transAxes,
                    color='red')
        else:
            ax.plot(ccut.x, ccut.y, 'r', label='charging curve')
            ax.set_xlim(ccut.x[0] - 0.005, self._obj.spikes[0].x)

            _plot_line(ax,
                       [(ccut.x[0], ccut.x[-1])],
                       baseline + self.charging_curve_halfheight,
                       'charging curve halfheight', 'g')

        _plot_line(ax,
                   [(0, self._obj.baseline_before)],
                   baseline,
                   'baseline', 'k')

        ax.legend(loc='upper left')
        figure.tight_layout()


standard_features = (
    SteadyState,
    Spikes,
    AHP,
    FallingCurve,
    Rectification,
    ChargingCurve,
    )
