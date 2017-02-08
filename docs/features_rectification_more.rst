Additional plots for Rectification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. plot::

   import pathlib
   import matplotlib.pyplot as plt

   from ajustador import loader, features

   basename = pathlib.Path(loader.__file__).parent.parent / 'docs/static'
   dirname = basename / 'recording/042811-6ivifcurves_Waves'
   mes = loader.Measurement(str(dirname))

   fig = plt.figure()
   features.Rectification(mes[0]).plot(figure=fig)

.. plot::

   import pathlib
   import matplotlib.pyplot as plt

   from ajustador import loader, features

   basename = pathlib.Path(loader.__file__).parent.parent / 'docs/static'
   dirname = basename / 'recording/042811-6ivifcurves_Waves'
   mes = loader.Measurement(str(dirname))

   fig = plt.figure()
   features.Rectification(mes[1]).plot(figure=fig)

.. plot::

   import pathlib
   import matplotlib.pyplot as plt

   from ajustador import loader, features

   basename = pathlib.Path(loader.__file__).parent.parent / 'docs/static'
   dirname = basename / 'recording/042811-6ivifcurves_Waves'
   mes = loader.Measurement(str(dirname))

   fig = plt.figure()
   features.Rectification(mes[2]).plot(figure=fig)

.. plot::

   import pathlib
   import matplotlib.pyplot as plt

   from ajustador import loader, features

   basename = pathlib.Path(loader.__file__).parent.parent / 'docs/static'
   dirname = basename / 'recording/042811-6ivifcurves_Waves'
   mes = loader.Measurement(str(dirname))

   fig = plt.figure()
   features.Rectification(mes[3]).plot(figure=fig)

.. plot::

   import pathlib
   import matplotlib.pyplot as plt

   from ajustador import loader, features

   basename = pathlib.Path(loader.__file__).parent.parent / 'docs/static'
   dirname = basename / 'recording/042811-6ivifcurves_Waves'
   mes = loader.Measurement(str(dirname))

   fig = plt.figure()
   features.Rectification(mes[4]).plot(figure=fig)
   # make sure we got all of them
   assert len(mes) == 5
