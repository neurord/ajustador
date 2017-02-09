import os
import measurements1

def header(name, underline):
    return '{}\n{}\n'.format(name, underline * len(name))

assert(__file__.endswith('_more.py'))
stem = __file__[:-8]
basename = os.path.basename(stem)
classnames = {'features_steady_state':'SteadyState',
              'features_spikes':'Spikes',
              'features_falling_curve':'FallingCurve',
              'features_rectification':'Rectification',
              'features_charging_curve':'ChargingCurve',
             }
section = 'Additional plots for ' + classnames[basename]
title = header(section, '~')

with open(stem + '_more.rst', 'w') as f:
    print(title, file=f)
    for ident, mes in measurements1.waves.items():
        print(header(mes.name, '`'), file=f)
        for n in range(len(mes)):
            print('''\
.. plot::

   import os
   wavename, n = {!r}, {}
   exec(open('{}').read())
'''.format(ident, n, basename + '.py'), file=f)
    print('{} is written ({})'.format(f.name, section))
