import pathlib
import matplotlib.pyplot as plt

from ajustador import features
import measurements1

try:
    wavename
except NameError:
    wavename, n = 'waves042811', -1

rec = measurements1.waves[wavename][n]

fig = plt.figure()
features.Spikes(rec).plot(figure=fig)

plt.show()
