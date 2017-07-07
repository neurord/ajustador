import pathlib
import matplotlib.pyplot as plt

from ajustador import features

try:
    wavename
except NameError:
    import strange1 as mod
    wavename, n = 'high_baseline_post', -1

rec = mod.waves[wavename][n]

fig = plt.figure()
features.Spikes(rec).plot(figure=fig)

plt.show(block=True)
