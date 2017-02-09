import pathlib
import matplotlib.pyplot as plt

from ajustador import features
import measurements1

try:
    n
except NameError:
    n = 8

rec = measurements1.waves042811[n]

fig = plt.figure()
features.SteadyState(rec).plot(figure=fig)

plt.show()
