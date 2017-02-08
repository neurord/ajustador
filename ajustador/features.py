from . import utilities, detect

def _find_spikes(wave, min_height=0.0):
    peaks = detect.detect_peaks(wave.y, P_low=0.75, P_high=0.20)
    return peaks[wave.y[peaks] > min_height]

class Spikes:
    """Find the position and height of spikes
    """
    requires = 'wave'
    provides = 'spike_i', 'spikes', 'spike_count'

    def __init__(self, obj):
        self._wave = obj.wave

    @property
    @utilities.once
    def spike_i(self):
        "Indices of spike maximums in the wave.x, wave.y arrays"
        return _find_spikes(self._wave)

    @property
    @utilities.once
    def spikes(self):
        "An array with .x and .y components marking the spike maximums"
        return self._wave[self.spike_i]

    @property
    def spike_count(self):
        "The number of spikes"
        return len(self.spike_i)

    def plot(self, figure):
        ax = figure.add_subplot(111)
        ax.plot(self._wave.x, self._wave.y, label='recording')
        ax.set_xlabel('time / s')
        ax.set_ylabel('membrane potential / V')

        ax.vlines(self.spikes.x, -0.06, self.spikes.y, 'r')
        ax.text(0.05, 0.5, '{} spikes'.format(self.spike_count),
                horizontalalignment='left',
                transform=ax.transAxes)

        ax.set_title('Depolarizing injection response')
        figure.tight_layout()

        if self.spike_count > 0:
            ax2 = figure.add_axes([.7, .45, .25, .4])
            ax2.set_xlim(self.spikes.x[0] - 0.001, self.spikes.x[0] + 0.0015)
            ax2.plot(self._wave.x, self._wave.y, label='recording')
            ax2.vlines(self.spikes.x[:1], -0.06, self.spikes.y, 'r')
            ax2.tick_params(labelbottom='off', labelleft='off')
            ax2.set_title('first spike', fontsize='smaller')
