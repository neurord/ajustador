import pathlib
import matplotlib.pyplot as plt

from ajustador import loader

basename = pathlib.Path(loader.__file__).parent.parent / 'docs/static'
dirname = basename / 'recording/042811-6ivifcurves_Waves'
mes = loader.Measurement(str(dirname))
depol = mes[mes.injection > 0]
rec = depol[-1]

fig, ax = plt.subplots()
ax.plot(rec.wave.x, rec.wave.y, label='recording')
ax.set_xlabel('time / s')
ax.set_ylabel('membrane potential / V')

ax.vlines(rec.spikes.x, -0.06, rec.spikes.y, 'r')
ax.text(0.05, 0.5, '{} spikes'.format(len(rec.spikes)),
        horizontalalignment='left',
        transform=ax.transAxes)

ax.set_title('Depolarizing injection response')
fig.tight_layout()

ax2 = fig.add_axes([.7, .45, .25, .4])
ax2.set_xlim(rec.spikes.x[0] - 0.001, rec.spikes.x[0] + 0.0015)
ax2.plot(rec.wave.x, rec.wave.y, label='recording')
ax2.vlines(rec.spikes.x[:1], -0.06, rec.spikes.y, 'r')
ax2.tick_params(labelbottom='off', labelleft='off')
ax2.set_title('first spike', fontsize='smaller')

plt.show()
