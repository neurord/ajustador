import pathlib
import matplotlib.pyplot as plt

from ajustador import loader

def plot_line(ax, ranges, value, color):
    for (a,b) in ranges:
        print(a, b, value, color)
        ax.hlines(value.x, a, b, color, linestyles='-', zorder=3)
        ax.hlines([value.x - 3*value.dev, value.x + 3*value.dev], a, b,
                  color, linestyles='--', zorder=3)

basename = pathlib.Path(loader.__file__).parent.parent / 'docs/static'
dirname = basename / 'recording/042811-6ivifcurves_Waves'
mes = loader.Measurement(str(dirname))
hyper = mes[mes.injection < 0]
rec = hyper[0]

fig, ax = plt.subplots()
ax.plot(rec.wave.x, rec.wave.y, label='recording')
ax.set_xlabel('time / s')
ax.set_ylabel('membrane potential / V')

plot_line(ax,
          [(0, rec.params.baseline_before), (rec.params.baseline_after, rec.time)],
          rec.baseline,
          'k')
plot_line(ax,
          [(rec.params.steady_after, rec.params.steady_before)],
          rec.baseline + rec.response,
          'r')

ax.set_title('Hyperpolarizing injection response with baseline and response marked')
fig.tight_layout()
plt.show()
