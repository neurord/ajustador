import pathlib
import matplotlib.pyplot as plt

from ajustador import loader, features

basename = pathlib.Path(loader.__file__).parent.parent / 'docs/static'
dirname = basename / 'recording/042811-6ivifcurves_Waves'
mes = loader.Measurement(str(dirname))

fig = plt.figure()
features.FallingCurve(mes[1]).plot(figure=fig)

plt.show()
