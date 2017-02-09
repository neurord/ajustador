import pathlib
import matplotlib.pyplot as plt

import measurements1
from ajustador import features

rec = measurements1.waves042811[8]

fig = plt.figure()
features.Baseline(rec).plot(figure=fig)

plt.show()
