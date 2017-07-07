import pathlib
import matplotlib.pyplot as plt

from ajustador import features

try:
    wavename
except NameError:
    import measurements1 as mod
    wavename, n = 'waves042811', -1

rec = mod.waves[wavename][n]

fig = plt.figure()
features.AHP(rec).plot(figure=fig)

plt.show()
