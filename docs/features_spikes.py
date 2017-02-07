import pathlib
import matplotlib.pyplot as plt

from ajustador import loader, features

basename = pathlib.Path(loader.__file__).parent.parent / 'docs/static'
dirname = basename / 'recording/042811-6ivifcurves_Waves'
mes = loader.Measurement(str(dirname))
depol = mes[mes.injection > 0]
rec = depol[-1]

fig = plt.figure()
features.Spikes(rec).plot(figure=fig)

plt.show()
