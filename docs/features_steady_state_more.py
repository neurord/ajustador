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
             }
section = 'Additional plots for ' + classnames[basename]
title = header(section, '~')

with open(stem + '_more.rst', 'w') as f:
    print(title, file=f)
    for mes in measurements1.waves:
        print(header(mes.name, '`'), file=f)
        for n in range(len(mes)):
            print('''\
.. plot::

   import os
   n = {}
   exec(open('{}').read())
'''.format(n, basename + '.py'), file=f)
    print('{} is written ({})'.format(f.name, section))
