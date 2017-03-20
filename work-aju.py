import ajustador as aju, measurements1 as ms1, numpy as np
from ajustador import drawing
from matplotlib import pyplot

# waves1h = ms1.waves1[ms1.waves1.injection <= 0][::3]
# waves2h = ms1.waves2[ms1.waves2.injection <= 0][::3]
# waves3h = ms1.waves3[ms1.waves3.injection <= 0][::3]
# waves4h = ms1.waves4[ms1.waves4.injection <= 0][::3]
# waves5h = ms1.waves5[ms1.waves5.injection <= 0][::3]
# waves6h = ms1.waves6[ms1.waves6.injection <= 0][::3]
# waves7h = ms1.waves7[ms1.waves7.injection <= 0][::3]
# waves8h = ms1.waves8[ms1.waves8.injection <= 0][::3]
waves9h = ms1.waves9[ms1.waves9.injection <= 0][::3]

params = aju.optimize.ParamSet(
    ('RA',                 4.309,    0, 100),
    ('RM',                 0.722,    0,  10),
    ('CM',                 0.015,    0, 0.10),
    ('Cond_Kir',           9.4644,   0, 100),
    ('Kir_offset',         0,        -0.005, +0.005),
    ('morph_file', 'MScell-tertDendlongRE.p'),
    ('neuron_type', 'D1'))

fit = aju.optimize.Fit('../fit-2017-aju-cma-wave9h-1',
                       waves9h, aju.fitnesses.hyperpol_fitness, params)
fit.load()
fit.do_fit(100)


params2 = params.update(RA=3.309,
                        RM=1.722,
                        CM=0.025,
                        Cond_Kir=1.4644,
                        Kir_offset=0)
fit2 = aju.optimize.Fit('../fit-2017-aju-cma-wave9h-2',
                       waves9h, aju.fitnesses.hyperpol_fitness, params2)
fit2.load()
fit2.do_fit(100)


params3 = aju.optimize.ParamSet(
    ('junction_potential', 0,       -0.030, +0.030),
    ('RA',                 12.004,    0, 100),
    ('RM',                 9.427,     0,  10),
    ('CM',                 0.03604,   0, 0.10),
    ('Cond_Kir',           14.502,    0, 100),
    ('Kir_offset',         -.004,    -0.005, +0.005),
    ('morph_file', 'MScell-tertDendlongRE.p'),
    ('neuron_type', 'D1'))
fit3 = aju.optimize.Fit('../fit-2017-aju-cma-wave9h-3',
                        waves9h, aju.fitnesses.hyperpol_fitness, params3)
fit3.load()
fit3.do_fit(100)


params4 = params3
fit4 = aju.optimize.Fit('../fit-2017-aju-cma-wave5h-1',
                        ms1.waves5[0:10:2], aju.fitnesses.hyperpol_fitness, params4)
fit4.load()
fit4.do_fit(100)


params5 = params3
aju.fitnesses.ERROR = aju.fitnesses.ErrorCalc.relative
fit5 = aju.optimize.Fit('../fit-2017-aju-cma-wave5h-2',
                        ms1.waves5[0:10:2], aju.fitnesses.hyperpol_fitness, params5)
fit5.load()
fit5.do_fit(100)

for i in range(len(fit5)):
    print(i, fit5.fitness_func(fit5[i], fit5.measurement, full=1),
          '→', fit5.fitness_func(fit5[i], fit5.measurement, full=0))


aju.fitnesses.ERROR = aju.fitnesses.ErrorCalc.relative
params6 = aju.optimize.ParamSet(
    ('junction_potential', 0,       -0.030, +0.030),
    ('RA',                 12.004,    0, 100),
    ('RM',                 9.427,     0,  10),
    ('CM',                 0.03604,   0, 0.10),
    ('Cond_Kir',           14.502,    0, 100),
    ('Kir_offset',         -.004,    -0.005, +0.005),
    ('morph_file', 'MScell-tertDendlongRE.p'),
    ('neuron_type', 'D1'),
    ('Cond_NaF_0',      150e3,      0, 600e3),
    ('Cond_KaS_0',      372,        0, 600),
    ('Cond_KaF_0',      641,        0, 1000),
    ('Cond_Krp_0',      177,        0, 600))
fit6 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-2',
                        ms1.waves5[[0, 3, 7, 13, 17, 19, 21, 22, 23]],
                        aju.fitnesses.new_combined_fitness, params6)
fit6.load()
fit6.do_fit(150, popsize=20)

aju.fitnesses.ERROR = aju.fitnesses.ErrorCalc.relative
# fit6.params.update(**fit6[5650].params)
params7 = params6.update(junction_potential=-0.01473080415412029,
                         RA=10.65928280866225,
                         RM=9.084575725069685,
                         CM=0.06497639701396317,
                         Cond_Kir=16.683626881626683,
                         Kir_offset=-0.00499822637790663,
                         Cond_NaF_0=158950.93821085666,
                         Cond_KaS_0=178.8056033265561,
                         Cond_KaF_0=611.1236043484937,
                         Cond_Krp_0=204.35266201409314)
fit7 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-4',
                        ms1.waves5[[0, 7, 17, 21, 23]],
                        aju.fitnesses.new_combined_fitness, params7)
fit7.load()
fit7.do_fit(150, popsize=8)

drawing.plot_history(fit7, fit7.measurement, fitness=aju.fitnesses.new_combined_fitness)
drawing.plot_history(fit7, fit7.measurement, fitness=aju.fitnesses.spike_time_fitness, clear=False)
drawing.plot_history(fit7, fit7.measurement, fitness=aju.fitnesses.spike_width_fitness, clear=False)
drawing.plot_history(fit7, fit7.measurement, fitness=aju.fitnesses.spike_ahp_fitness, clear=False)
drawing.plot_history(fit7, fit7.measurement, fitness=aju.fitnesses.ahp_curve_fitness, clear=False)


params8 = aju.optimize.ParamSet(
    ('junction_potential', 0,       -0.030, +0.030),
    ('RA',                 12.004,    0, 100),
    ('RM',                 9.427,     0,  10),
    ('CM',                 0.03604,   0, 0.10),
    ('Cond_Kir',           14.502,    0, 100),
    ('Kir_offset',         -.004,    -0.005, +0.005),
    ('morph_file', 'MScell-tertDendlongRE.p'),
    ('neuron_type', 'D1'),
    ('Cond_NaF_0',      150e3,      0, 600e3),
    ('Cond_KaS_0',      372,        0, 600),
    ('Cond_KaF_0',      641,        0, 1000),
    ('Cond_Krp_0',      177,        0, 600),
    ('Cond_SKCa_0',     0.5,        0, 6),
    ('Cond_BKCa_0',     10,         0, 100))
aju.fitnesses.ERROR = aju.fitnesses.ErrorCalc.relative
fit8 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-8',
                        ms1.waves5[[0, 7, 17, 21, 23]],
                        aju.fitnesses.new_combined_fitness, params8)
fit8.load()
fit8.do_fit(150, popsize=20)

# baseline → baseline_pre, baseline_post
# fit8.params.update(**fit8[2536].params)
params9 = params8.update(junction_potential=-0.01358622557992854,
                         RA=7.5097716484728485,
                         RM=9.865608455066301,
                         CM=0.05695624758868263,
                         Cond_Kir=15.175645393785455,
                         Kir_offset=-0.004965981023001747,
                         Cond_NaF_0=165710.14383336686,
                         Cond_KaS_0=529.1622011113959,
                         Cond_KaF_0=670.775894939824,
                         Cond_Krp_0=4.446655927879732,
                         Cond_SKCa_0=0.12046639942362143,
                         Cond_BKCa_0=11.51439493711431)
fitness = aju.fitnesses.new_combined_fitness()
fit9 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-9',
                        ms1.waves5[[0, 7, 17, 21, 23]],
                        fitness, params9)
fit9.load()
fit9.do_fit(400, popsize=20)
