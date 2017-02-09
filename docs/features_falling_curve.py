import pathlib
import matplotlib.pyplot as plt

from ajustador import features
import measurements1

try:
    n
except NameError:
    n = 0

rec = measurements1.waves042811[n]

fig = plt.figure()
features.FallingCurve(rec).plot(figure=fig)

plt.show()
