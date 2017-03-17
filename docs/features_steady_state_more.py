import os
import measurements1
import strange1
import pprint

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

filters = {'features_spikes':{'042811-6ivifcurves_Waves': (21, 22, 23), # no spikes, some spikes
                              '042911-10ivifcurves_Waves': (),
                              '050311-4ivifcurves_Waves': (),
                              '050411-7ivifcurves_Waves': (5, ),           # three nice spikes
                              '050511-3ivifcurves_Waves': (),
                              '050611-5ivifcurves_Waves': (),
                              '051311-9ivifcurves_Waves': (10, 18),        # spontaneous event, late spike
                              '051411-5ivifcurves_Waves': (),
                              '051811-13ivifcurves_Waves': (10, ),         # undulating no injection
                              '090612-1ivcurves_Waves': (12, 14),          # high spikes, changing size
                              '091312-4ivcurves_Waves': (),
                              'high_baseline_post': (3, 4),
                             },
           'features_steady_state': {'042811-6ivifcurves_Waves': (0, 2, 8, 9, 10, 11, 13, 14),
                                     '042911-10ivifcurves_Waves': (2, ),
                                     '050311-4ivifcurves_Waves': (0, 7, 8, 9, 10, 11, 12),
                                     '050411-7ivifcurves_Waves': (),
                                     '050511-3ivifcurves_Waves': (),
                                     '050611-5ivifcurves_Waves': (),
                                     '051311-9ivifcurves_Waves': (0, 2, 10),
                                     '051411-5ivifcurves_Waves': (),
                                     '051811-13ivifcurves_Waves': (),
                                     '090612-1ivcurves_Waves': (0, 9),
                                     '091312-4ivcurves_Waves': (),
                                     'high_baseline_post': (3, 4),
                                    },
           'features_rectification': {'042811-6ivifcurves_Waves': (0, 5, 8),
                                      '042911-10ivifcurves_Waves': (0, ),
                                      '050311-4ivifcurves_Waves': (),
                                      '050411-7ivifcurves_Waves': (0, 1, 2, 3, 4),
                                      '050511-3ivifcurves_Waves': (),
                                      '050611-5ivifcurves_Waves': (),
                                      '051311-9ivifcurves_Waves': (),
                                      '051411-5ivifcurves_Waves': (),
                                      '051811-13ivifcurves_Waves': (),
                                      '090612-1ivcurves_Waves': (7, 8),
                                      '091312-4ivcurves_Waves': (),
                                      'high_baseline_post': (3, 4),
                                     },
           'features_charging_curve': {'042811-6ivifcurves_Waves': (0, 10, 21, 22, 23),
                                       '042911-10ivifcurves_Waves': (),
                                       '050311-4ivifcurves_Waves': (),
                                       '050411-7ivifcurves_Waves': (),
                                       '050511-3ivifcurves_Waves': (20, 21, 22),
                                       '050611-5ivifcurves_Waves': (),
                                       '051311-9ivifcurves_Waves': (),
                                       '051411-5ivifcurves_Waves': (18, ),
                                       '051811-13ivifcurves_Waves': (),
                                       '090612-1ivcurves_Waves': (),
                                       '091312-4ivcurves_Waves': (),
                                       'high_baseline_post': (3, 4),
                                      },
           'features_falling_curve': {'042811-6ivifcurves_Waves': (0, 1, 3, 6, 8, 9, 10, 11, 12),
                                      '042911-10ivifcurves_Waves': (),
                                      '050311-4ivifcurves_Waves': (),
                                      '050411-7ivifcurves_Waves': (),
                                      '050511-3ivifcurves_Waves': (),
                                      '050611-5ivifcurves_Waves': (0, 4),
                                      '051311-9ivifcurves_Waves': (),
                                      '051411-5ivifcurves_Waves': (),
                                      '051811-13ivifcurves_Waves': (),
                                      '090612-1ivcurves_Waves': (0, 2, 4),
                                      '091312-4ivcurves_Waves': (0, 2, 4),
                                      'high_baseline_post': (3, 4),
                                     },
}

filter = filters.get(basename, None)
print('Looking at {}'.format(basename),
      ', filter with {} entries'.format(len(filter))
      if filter is not None else '')

if filter is None:
    empty = dict((mes.name, ())
                 for mod in (measurements1, strange1)
                 for mes in sorted(mod.waves.values()))
    pprint.pprint({basename: empty})

with open(stem + '_more.rst', 'w') as f:
    print(title, file=f)
    for mod in (measurements1, strange1):
        for ident, mes in sorted(mod.waves.items()):
            fallback = range(len(mes))
            indices = filter.get(mes.name, fallback) if filter else fallback
            print('    {} → {}'.format(mes.name, indices if indices != fallback else ' (all)'))

            if indices:
                print(header(mes.name, '`'), file=f)
            for n in indices:
                print('''\
.. plot::

   import {} as mod
   wavename, n = {!r}, {}
   exec(open('{}').read())
'''.format(mod.__name__, ident, n, basename + '.py'), file=f)
            print('{} is written ({})'.format(f.name, section))
