import pathlib
import matplotlib.pyplot as plt

from ajustador import features
import strange1

try:
    wavename
except NameError:
    wavename, n = 'high_baseline_post', -1

rec = strange1.waves[wavename][n]

fig = plt.figure()
features.Spikes(rec).plot(figure=fig)

plt.show(block=True)
