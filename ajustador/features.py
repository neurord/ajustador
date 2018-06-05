import math
from collections import namedtuple
import pprint
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

    def plot(self, figure=None):
        if figure is None:
            from matplotlib import pyplot
            figure = pyplot.figure()

        wave = self._obj.wave

        ax = figure.add_subplot(111)
        ax.plot(wave.x, wave.y, label='recording')
        ax.set_xlabel('time / s')
        ax.set_ylabel('membrane potential / V')
        return ax

    def spike_plot(self, figure=None, max_spikes=20,
                   bottom=None, spike_bounds=None,
                   lmargin=0.0010, rmargin=0.0015, rowsize=None):

        if figure is None:
            from matplotlib import pyplot
            figure = pyplot.figure()

        wave = self._obj.wave
        spikes = self._obj.spikes

        spike_count = min(len(spikes), max_spikes)
        if rowsize is None:
            rowsize = 3 if spike_count < 19 else 5
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

    def report_attr(self, name):
        val = getattr(self, name)
        prefix = '{} = '.format(name)
        if hasattr(val, 'report'):
            ans = val.report(prefix=prefix)
        elif isinstance(val, np.ndarray) and hasattr(val, 'dev'):
            ans = vartype.vartype.format_array(val, prefix=prefix)
        elif hasattr(val, '__len__'):
            joiner = '\n' + len(prefix)*' '
            ans = prefix + joiner.join(str(x) for x in val)
        else:
            ans = prefix + str(val)
        if name in self.mean_attributes and hasattr(val, '__len__'):
            mean = vartype.vartype.average(val)
            ans += '\n{:{}} = {}'.format('', len(name), mean)
        return ans

    def report(self):
        return '\n'.join(self.report_attr(name) for name in self.provides)

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
    provides = ('baseline', 'steady', 'response',
                'baseline_pre', 'baseline_post')

    mean_attributes = ('baseline', 'steady', 'response',
                       'baseline_pre', 'baseline_post')
    array_attributes = ('baseline', 'steady', 'response',
                        'baseline_pre', 'baseline_post')

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
        if before is None and after is None:
            raise ValueError('cannot determine baseline')
        region = ((wave.x < before if before is not None else False) |
                  (wave.x > after if after is not None else False))
        what = wave.y[region]
        cutoffa, cutoffb = np.percentile(what, (40, 60))
        cut = what[(what >= cutoffa) & (what <= cutoffb)]
        return vartype.array_mean(cut)

    @property
    @utilities.once
    def baseline_pre(self):
        """The mean voltage of the area before the injection interval

        Returns mean value of wave after excluding "outliers", values
        > 95th or < 5th percentile.
        """
        wave = self._obj.wave
        before = self._obj.baseline_before
        if before is None:
            return vartype.vartype.nan

        what = wave.y[(wave.x < before)]
        cutoffa, cutoffb = np.percentile(what, (40, 60))
        cut = what[(what >= cutoffa) & (what <= cutoffb)]
        return vartype.array_mean(cut)

    @property
    @utilities.once
    def baseline_post(self):
        """The mean voltage of the area after the injection interval

        Returns mean value of wave after excluding "outliers", values
        > 95th or < 5th percentile.
        """
        wave = self._obj.wave
        after = self._obj.baseline_after
        if after is None:
            return vartype.vartype.nan

        what = wave.y[(wave.x > after)]
        cutoffa, cutoffb = np.percentile(what, (40, 60))
        cut = what[(what >= cutoffa) & (what <= cutoffb)]
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
        cut = data[data <= cutoff]
        return vartype.array_mean(cut)

    @property
    @utilities.once
    def response(self):
        return self.steady - self.baseline

    def plot(self, figure=None, pre_post=False):
        wave = self._obj.wave
        before = self._obj.baseline_before
        after = self._obj.baseline_after
        steady_after = self._obj.steady_after
        steady_before = self._obj.steady_before
        time = wave.x[-1]

        ax = super().plot(figure)
        if not pre_post:
            _plot_line(ax,
                       [(0, before), (after, time)],
                       self.baseline,
                       'baseline', 'k')
        else:
            if before is not None:
                _plot_line(ax,
                           [(0, before)],
                           self.baseline_pre,
                           'baseline_pre', 'k')
            if after is not None:
                _plot_line(ax,
                           [(after, time)],
                           self.baseline_post,
                           'baseline_post', 'k')

        _plot_line(ax,
                   [(steady_after, steady_before)],
                   self.steady,
                   'steady', 'r')
        ax.annotate('response',
                    xy=(time/2, self.steady.x),
                    xytext=(time/2, self.baseline.x),
                    arrowprops=dict(facecolor='black',
                                    shrink=0),
                    horizontalalignment='center', verticalalignment='bottom')

        ax.legend(loc='upper right')
        ax.figure.tight_layout()


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
        try:
            ythresh = charge_threshold * yderiv.max()
            thresh = y[1:][yderiv > ythresh].min()
            thresholds[i] = thresh
        except Exception:
            thresholds[i] = np.nan
    return peak_and_threshold(peaks, thresholds)

class WaveRegion:
    def __init__(self, wave, left_i, right_i):
        self._wave = wave
        self.left_i = left_i
        self.right_i = right_i

    @property
    def left(self):
        "x coordinate of the left edge of FWHM"
        if self.left_i == 0:    # arr[-1:1] is an empty slice
            return self._wave.x[0]
        else:
            return self._wave.x[self.left_i-1:self.left_i+1].mean()

    @property
    def right(self):
        "x coordinate of the right edge of FWHM"
        return self._wave.x[self.right_i:self.right_i+2].mean()

    @property
    def width(self):
        return self.right - self.left

    @property
    def wave(self):
        return self._wave[self.left_i:self.right_i+1]

    @property
    def x(self):
        return self._wave.x[self.left_i:self.right_i+1]

    @property
    def y(self):
        return self._wave.y[self.left_i:self.right_i+1]

    def min(self):
        return self.wave.min()

    def relative_to(self, x, y):
        new = np.rec.fromarrays((self.x - x, self.y - y), names='x,y')
        return WaveRegion(new, 0, new.size-1)

    def __str__(self):
        y = self.y
        return 'WaveRegion[{} points, x={:.04f}-{:.04f}, y={:.03f}-{:.03f}]'.format(
            self.right_i - self.left_i + 1,
            self.left, self.right,
            self.y.min(), self.y.max())

    def report(self, prefix='WaveRegion = '):
        return '{}{}'.format(prefix, self)

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
    mean_attributes = ('spike_height', 'spike_width', 'spike_threshold')

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
            return self._obj.injection_end - self._obj.injection_start

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

    def plot(self, figure=None):
        from . import drawing_util

        wave = self._obj.wave
        ax = super().plot(figure)
        bottom = -0.06 # self._obj.steady.x
                       # Doing the "proper" thing makes the plot hard to read

        vline1 = ax.vlines(self.spikes.x, bottom, self.spikes.y, 'r',
                            label='timing of spike maximum')
        ax.text(0.05, 0.5, plural(self.spike_count, 'spike'),
                horizontalalignment='left',
                transform=ax.transAxes)

        _plot_line(ax,
                   [(self._obj.steady_after, self._obj.steady_before)],
                   self.mean_spike_height,
                   'spike_height', 'y', zorder=0)
        ax.legend(loc='upper left',
                  handler_map={vline1: drawing_util.HandlerVLineCollection()})
        ax.figure.tight_layout()

        if self.spike_count > 0:
            ax2 = ax.figure.add_axes([.7, .45, .25, .4])
            ax2.tick_params(labelbottom='off', labelleft='off')
            ax2.set_title('first spike', fontsize='smaller')

            _plot_spike(ax2, wave, self.spikes, i=0,
                        bottom=-0.06, spike_bounds=self.spike_bounds)

    def spike_plot(self, figure=None, **kwargs):
        x = self._obj.spikes.x.mean()
        spike_bounds = self.spike_bounds
        thresholds = self.spike_threshold
        height = self.spike_height

        lmargin = self.spike_width.max()
        rmargin = self.spike_width.max() * 2

        axes = super().spike_plot(figure=None,
                                  spike_bounds=spike_bounds,
                                  lmargin=lmargin, rmargin=rmargin,
                                  **kwargs)

        for i in range(len(axes)):
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
    provides = ('spike_ahp_window', 'spike_ahp', 'spike_ahp_position')
    array_attributes = ('spike_ahp_window', 'spike_ahp', 'spike_ahp_position')
    mean_attributes = ('spike_ahp',)

    @property
    @utilities.once
    def spike_ahp_window(self):
        spikes = self._obj.spikes
        spike_bounds = self._obj.spike_bounds
        thresholds = self._obj.spike_threshold
        injection_start = self._obj.injection_start
        injection_end = self._obj.injection_end

        x = self._obj.wave.x
        y = self._obj.wave.y
        ans = []
        for i in range(len(spikes)):
            beg = spike_bounds[i].right_i

            # Don't allow the ahp to straddle an injection start/stop edge.
            # The ahp will be invalid anyway.
            rlimit = min(spike_bounds[i+1].left if i < len(spikes)-1 else x[-1],
                         injection_start if injection_start > x[beg] else np.infty,
                         injection_end if injection_end > x[beg] else np.infty)

            w = spike_bounds[i].width
            if not np.isnan(w):
                n_rolling_window = int(w // (x[1] - x[0])) + 1
            else:
                # FIXME: consider rejecting those outright
                n_rolling_window = 5

            # if we are before the AHP, or mostly going down, advance
            while (beg < y.size - n_rolling_window and
                   y[beg] >= thresholds[i] and x[beg + 1] < rlimit and
                   y[beg] > y[beg + n_rolling_window]):
                beg += 1

            end = beg + n_rolling_window
            while (end < x.size and
                   (y[end] < thresholds[i] or end - beg < 5) and
                   x[end] < rlimit):
                end += 1

            ans.append(WaveRegion(self._obj.wave, beg, end))

        return ans

    @property
    @utilities.once
    def spike_ahp(self):
        """Returns the (averaged) minimum in y of each AHP window

        `spike_ahp_window` is used to determine the extent of the AHP.
        An average of the bottom area of the window of the width of the
        spike is used.
        Probably this should be changed to return the difference between threshold and minimum y
        thresh=spikes.spike_threshold
        mean=vartype.array_mean(cut.y)-thresh[i], or ans[i]=mean.x-spikes.spike_threshold[i],mean.dev
        """
        windows = self.spike_ahp_window
        spikes = self._obj.spikes
        spike_bounds = self._obj.spike_bounds

        ans = np.empty((len(windows), 2))
        for i in range(len(windows)):
            w = spike_bounds[i].width
            left = windows[i].x[windows[i].y.argmin()] - w/2
            right = windows[i].x[windows[i].y.argmin()] + w/2
            cut = windows[i].wave[(windows[i].x >= left) & (windows[i].x <= right)]
            mean = vartype.array_mean(cut.y)
            ans[i] = mean.x, mean.dev

        return np.rec.fromarrays(ans.T, names='x,dev')

    @property
    @utilities.once
    def spike_ahp_position(self):
        """Returns the (averaged) x of the minimum in y of each AHP window

        `spike_ahp_window` is used to determine the extent of the AHP.
        An average of the bottom area of the window of the width of the
        spike is used.

        TODO: add to plot
        """
        windows = self.spike_ahp_window
        spikes = self._obj.spikes
        spike_bounds = self._obj.spike_bounds

        ans = np.empty((len(windows), 2))
        for i in range(len(windows)):
            step = windows[i].x[1] - windows[i].x[0]
            # Make sure that we have at least a few points in the window,
            # even if the spike is very narrow.
            w = max(spike_bounds[i].width, 8 * step)
            left = windows[i].x[windows[i].y.argmin()] - w/2
            right = windows[i].x[windows[i].y.argmin()] + w/2
            cut = windows[i].wave[(windows[i].x >= left) & (windows[i].x <= right)]
            bottom = vartype.array_mean(cut.y)
            relative = cut.y - bottom.x
            weights = (relative / relative.ptp())**-2
            weights = np.fmin(weights, 100)
            avg = (cut.x * weights).sum() / weights.sum()
            assert not np.isnan(avg)
            dev = ((cut.x-avg)**2 * weights).sum()**0.5 / weights.sum()**0.5
            assert not np.isnan(dev)
            # TODO: check the formula for dev
            ans[i] = (avg, dev)

        return np.rec.fromarrays(ans.T, names='x,dev')

    def _do_plots(self, axes):
        spikes = self._obj.spikes
        spike_bounds = self._obj.spike_bounds
        thresholds = self._obj.spike_threshold
        windows = self.spike_ahp_window
        ahps = self.spike_ahp
        low, high = np.inf, -np.inf

        spike_count = len(axes)

        for i in range(spike_count):
            window = windows[i]
            x = spikes.x[i]
            width = window.right - x

            axes[i].plot(window.x, window.y, 'r', label='AHP')
            _plot_line(axes[i],
                       [(spikes[i].x - 3*spike_bounds[i].width,
                         spikes[i].x + 3*spike_bounds[i].width)],
                       thresholds[i],
                       'spike threshold', 'green')
            _plot_line(axes[i],
                       [(x, window.right)],
                       vartype.vartype(*ahps[i]),
                       'AHP bottom', 'magenta')

            axes[i].annotate('AHP',
                             xytext=(x + width/2, ahps[i].x),
                             xy=(x + width/2, thresholds[i]),
                             arrowprops=dict(facecolor='black',
                                             shrink=0),
                             horizontalalignment='center', verticalalignment='top')
            diff = abs(thresholds[i] - ahps[i].x)
            low = min(ahps[i].x - diff*0.5, thresholds[i] - diff*0.5, low)
            high = max(thresholds[i] + diff*0.5, high)

            axes[i].set_ylim(low, high)

    def plot(self, figure=None):
        ax = super().plot(figure)
        if self._obj.spike_count == 0:
            ax.text(0.5, 0.5, 'no spikes',
                    horizontalalignment='center',
                    transform=ax.transAxes)
        else:
            ax.set_xlim(self._obj.spikes[0].x - self._obj.injection_interval*0.05,
                        self._obj.spikes[-1].x + self._obj.injection_interval*0.05)
            self._do_plots([ax] * self._obj.spike_count)
        ax.figure.tight_layout()

    def spike_plot(self, figure=None, **kwargs):
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
    dd = smooth(d.y, window='hanning', window_len=window)[(d.x > after) & (d.x < before)]
    start = end = dd.argmin() + (d.x <= after).sum()
    while start > 0 and wave[start - 1].y > wave[start].y and wave[start].x > after:
        start -= 1
    sm = smooth(wave.y, window='hanning', window_len=window)
    smallest = sm[end]
    # find minimum
    while (end+window < wave.size and wave[end+window].x < before
           and sm[end:end + window].min() < smallest):
        smallest = sm[end]
        end += window // 2
    start_override = (d.x > after).argmax()
    ccut = wave[start_override + 1 : end]
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
                'injection_start', 'steady_before',
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
                                   after=self._obj.injection_start,
                                   before=self._obj.steady_before)

    @property
    @utilities.once
    def falling_curve_fit(self):
        return _fit_falling_curve(self.falling_curve, self._obj.baseline, self._obj.steady)

    @property
    def falling_curve_amp(self):
        fit = self.falling_curve_fit
        return fit.params.amp if fit.good else vartype.vartype.nan

    @property
    def falling_curve_tau(self):
        fit = self.falling_curve_fit
        return fit.params.tau if fit.good else vartype.vartype.nan

    @property
    def falling_curve_function(self):
        fit = self.falling_curve_fit
        return fit.function if fit.good else None

    def plot(self, figure=None):
        ax = super().plot(figure)

        ccut = self.falling_curve
        baseline = self._obj.baseline
        steady = self._obj.steady
        ax.plot(ccut.x, ccut.y, 'r', label='falling curve')
        ax.set_xlim(self._obj.injection_start - 0.005, ccut.x.max() + .01)

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
        ax.figure.tight_layout()


class Rectification(Feature):
    requires = ('injection_start',
                'steady_after', 'steady_before',
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

    def plot(self, figure=None):
        ax = super().plot(figure)

        ccut = self._obj.falling_curve
        after = self._obj.steady_after
        before = self._obj.steady_before
        steady = self._obj.steady

        ax.set_xlim(self._obj.injection_start - 0.005, before)

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
        ax.figure.tight_layout()


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
        threshold = self._obj.spike_threshold[0]
        baseline = self._obj.baseline

        return (threshold - baseline) / 2

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

    def plot(self, figure=None):
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
        ax.figure.tight_layout()


standard_features = (
    SteadyState,
    Spikes,
    AHP,
    FallingCurve,
    Rectification,
    ChargingCurve,
    )
