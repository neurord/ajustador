import ajustador as aju, measurements1 as ms1, numpy as np
from ajustador import drawing
from matplotlib import pyplot
import gpedata_experimental as gpe

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
fit5 = aju.optimize.Fit('../fit-2017-aju-cma-wave5h-2',
                        ms1.waves5[0:10:2], aju.fitnesses.hyperpol_fitness, params5)
fit5.load()
fit5.do_fit(100)

for i in range(len(fit5)):
    print(i, fit5.fitness_func(fit5[i], fit5.measurement, full=1),
          '→', fit5.fitness_func(fit5[i], fit5.measurement, full=0))


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


# updated fitness functions, use wave with late spikes to fit latency
# fit9.params.update(**fit9["194"].params)
params10 = params8.update(junction_potential=-0.011962426960236439,
                          RA=7.461321794316308,
                          RM=7.430291533499045,
                          CM=0.06459645379574586,
                          Cond_Kir=16.785027556088167,
                          Kir_offset=-0.004966350334998441,
                          Cond_NaF_0=193235.13881770396,
                          Cond_KaS_0=596.4041260775343,
                          Cond_KaF_0=748.532913089759,
                          Cond_Krp_0=3.9188988122933415,
                          Cond_SKCa_0=0.8627234570253062,
                          Cond_BKCa_0=8.435723459115415)
fitness = aju.fitnesses.new_combined_fitness()

fit10 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-10',
                         ms1.waves5[[0, 7, 17, 18, 21]],
                         fitness, params10)
fit10.load()
drawing.plot_history(fit10, fit10.measurement)
fit10.do_fit(400, popsize=20)

# the same as before, but with spike_latency_fitness thrown into the mix
fitness = aju.fitnesses.new_combined_fitness()
fit11 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-11',
                         ms1.waves5[[0, 7, 17, 18, 21]],
                         fitness, params10)
fit11.load(last=200)
fit11.do_fit(800, popsize=20)

# redo the plots with different starting points
params11a = params8.update(junction_potential=-0.011962426960236439/2,
                           RA=7.461321794316308/2,
                           RM=7.430291533499045/2,
                           CM=0.06459645379574586/2,
                           Cond_Kir=16.785027556088167/2,
                           Kir_offset=-0.004966350334998441/2,
                           Cond_NaF_0=193235.13881770396/2,
                           Cond_KaS_0=596.4041260775343/2,
                           Cond_KaF_0=748.532913089759/2,
                           Cond_Krp_0=3.9188988122933415/2,
                           Cond_SKCa_0=0.8627234570253062/2,
                           Cond_BKCa_0=8.435723459115415/2)
fitness = aju.fitnesses.new_combined_fitness()
fit11a = aju.optimize.Fit('../fit-2017-aju-cma-wave5-11a',
                          ms1.waves5[[0, 7, 17, 18, 21]],
                          fitness, params11a)
fit11a.load(last=200)
fit11a.do_fit(400, popsize=20)

params11b = params8.update(junction_potential=-0.011962426960236439*2,
                           RA=7.461321794316308*2,
                           RM=7.430291533499045*1.3,
                           CM=0.06459645379574586*1.5,
                           Cond_Kir=16.785027556088167*2,
                           Kir_offset=-0.004966350334998441,
                           Cond_NaF_0=193235.13881770396*2,
                           Cond_KaS_0=596.4041260775343*0.8,
                           Cond_KaF_0=748.532913089759*1.2,
                           Cond_Krp_0=3.9188988122933415*2,
                           Cond_SKCa_0=0.8627234570253062*2,
                           Cond_BKCa_0=8.435723459115415*2)
fitness = aju.fitnesses.new_combined_fitness()
fit11b = aju.optimize.Fit('../fit-2017-aju-cma-wave5-11b',
                          ms1.waves5[[0, 7, 17, 18, 21]],
                          fitness, params11b)
fit11b.load(last=200)
fit11b.do_fit(400, popsize=20)


params11c = params8.update(junction_potential=-0.011962426960236439/2,
                           RA=7.461321794316308/2,
                           RM=7.430291533499045/1.3,
                           CM=0.06459645379574586/1.5,
                           Cond_Kir=16.785027556088167*2,
                           Kir_offset=-0.004966350334998441,
                           Cond_NaF_0=193235.13881770396*1.5,
                           Cond_KaS_0=596.4041260775343*0.8,
                           Cond_KaF_0=748.532913089759/1.2,
                           Cond_Krp_0=3.9188988122933415*1.5,
                           Cond_SKCa_0=0.8627234570253062*3,
                           Cond_BKCa_0=8.435723459115415*3)
fitness = aju.fitnesses.new_combined_fitness()
fit11c = aju.optimize.Fit('../fit-2017-aju-cma-wave5-11c',
                          ms1.waves5[[0, 7, 17, 18, 21]],
                          fitness, params11c)
fit11c.load(last=200)
fit11c.do_fit(120, popsize=20)

# also allow the medial conductances to vary
params12 = aju.optimize.ParamSet(
    ('junction_potential', -0.012, 'fixed'),
    ('RA',                 12.004,    0, 100),
    ('RM',                 9.427,     0,  10),
    ('CM',                 0.03604,   0, 0.10),
    ('Cond_Kir',           14.502,    0, 100),
    ('Kir_offset',         -.004,    -0.010, +0.005),
    ('morph_file', 'MScell-tertDendlongRE.p'),
    ('Cond_NaF_0',      150e3,      0, 600e3),
    ('Cond_NaF_1',      1894,       0, 10000),
    ('Cond_KaS_0',      372,        0, 2000),
    ('Cond_KaF_0',      641,        0, 1000),
    ('Cond_Krp_0',      177,        0, 600),
    ('Cond_SKCa_0',     0.5,        0, 6),
    ('Cond_BKCa_0',     10,         0, 100),
    ('Cond_BKCa_1',     10,         0, 100))
# redo with higher upper bound for KaS density
# and ahp_curve_fitness updated to take rms of all AHPs
params12 = params12.update(RA=5.294949868179399,
                    RM=7.7809771401424435,
                    CM=0.060402895206330624,
                    Cond_Kir=17.040420667688142,
                    Kir_offset=-0.005857481956356754,
                    Cond_NaF_0=219356.6071179029,
                    Cond_NaF_1=878.6938806162441,
                    Cond_KaS_0=599.9317714317569,
                    Cond_KaF_0=887.4082517102048,
                    Cond_Krp_0=0.045796847567147546,
                    Cond_SKCa_0=1.736719977809778,
                    Cond_BKCa_0=5.634221337003896,
                    Cond_BKCa_1=9.824714710660963)
fitness = aju.fitnesses.new_combined_fitness()
fit12 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-12',
                         ms1.waves5[[0, 7, 17, 18, 21]],
                         'd1d2', 'D1',
                         fitness, params12)
fit12.load(last=200)
fit12.do_fit(150, popsize=10)

# also allow Eleak to vary
params13 = aju.optimize.ParamSet(
    ('junction_potential', -0.012, 'fixed'),
    ('RA',                 12.004,    0, 100),
    ('RM',                 9.427,     0,  10),
    ('CM',                 0.03604,   0, 0.10),
    ('Eleak',              -0.056, -0.080, -0.030),
    ('Cond_Kir',           14.502,    0, 100),
    ('Kir_offset',         -.004,    -0.010, +0.005),
    ('morph_file', 'MScell-tertDendlongRE.p'),
    ('Cond_NaF_0',      150e3,      0, 600e3),
    ('Cond_NaF_1',      1894,       0, 10000),
    ('Cond_KaS_0',      372,        0, 2000),
    ('Cond_KaF_0',      641,        0, 1000),
    ('Cond_Krp_0',      177,        0, 600),
    ('Cond_SKCa_0',     0.5,        0, 6),
    ('Cond_BKCa_0',     10,         0, 100),
    ('Cond_BKCa_1',     10,         0, 100))
# redo with higher upper bound for KaS density
# and ahp_curve_fitness updated to take rms of all AHPs
params13 = params13.update(RA=5.294949868179399,
                    RM=7.7809771401424435,
                    CM=0.060402895206330624,
                    Cond_Kir=17.040420667688142,
                    Kir_offset=-0.005857481956356754,
                    Cond_NaF_0=219356.6071179029,
                    Cond_NaF_1=878.6938806162441,
                    Cond_KaS_0=599.9317714317569,
                    Cond_KaF_0=887.4082517102048,
                    Cond_Krp_0=0.045796847567147546,
                    Cond_SKCa_0=1.736719977809778,
                    Cond_BKCa_0=5.634221337003896,
                    Cond_BKCa_1=9.824714710660963)
fitness = aju.fitnesses.new_combined_fitness()
fit13 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-13',
                         ms1.waves5[[0, 7, 17, 18, 21]],
                         'd1d2', 'D1',
                         fitness, params13)
fit13.load(last=200)
fit13.do_fit(150, popsize=10)



# also mostly everything to vary
params14 = aju.optimize.ParamSet(
    ('junction_potential', -0.012, 'fixed'),
    ('RA',                 12.004,    0, 100),
    ('RM',                 9.427,     0,  10),
    ('CM',                 0.03604,   0, 0.10),
    ('Eleak',              -0.056, -0.080, -0.030),
    ('Cond_Kir',           14.502,    0, 100),
    ('Kir_offset',         -.004,    -0.010, +0.005),
    ('morph_file', 'MScell-tertDendlongRE.p'),
    ('Cond_NaF_0',      150e3,      0, 600e3),
    ('Cond_NaF_1',      1894,       0, 10000),
    ('Cond_NaF_2',      927,       0, 10000),
    ('Cond_KaS_0',      372,        0, 2000),
    ('Cond_KaS_1',      32.9,       0, 200),
    ('Cond_KaF_0',      641,        0, 1000),
    ('Cond_KaF_1',      641,        0, 1000),
    ('Cond_KaF_2',      641,        0, 1000),
    ('Cond_Krp_0',      177,        0, 600),
    ('Cond_Krp_1',      70,        0, 600),
    ('Cond_Krp_2',      77,        0, 600),
    ('Cond_SKCa_0',     0.5,        0, 10),
    ('Cond_SKCa_1',     0.5,        0, 10),
    ('Cond_SKCa_2',     0.5,        0, 10),
    ('Cond_BKCa_0',     10,         0, 100),
    ('Cond_BKCa_1',     10,         0, 100),
    ('Cond_BKCa_2',     10,         0, 100))
params14 = params14.update(RA=5.294949868179399,
                    RM=7.7809771401424435,
                    CM=0.060402895206330624,
                    Cond_Kir=17.040420667688142,
                    Kir_offset=-0.005857481956356754,
                    Cond_NaF_0=219356.6071179029,
                    Cond_NaF_1=878.6938806162441,
                    Cond_KaS_0=599.9317714317569,
                    Cond_KaF_0=887.4082517102048,
                    Cond_Krp_0=0.045796847567147546,
                    Cond_SKCa_0=1.736719977809778,
                    Cond_BKCa_0=5.634221337003896,
                    Cond_BKCa_1=9.824714710660963)
fitness = aju.fitnesses.new_combined_fitness()
fit14 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-14',
                         ms1.waves5[[0, 7, 17, 18, 21]],
                         'd1d2', 'D1',
                         fitness, params14)
fit14.load(last=200)
fit14.do_fit(100, popsize=30)



paramsgp1 = aju.optimize.ParamSet(
    ('junction_potential', -0.012, -0.020, -0.005),
    ('RA',                 5 ,     0, 100),
    ('RM',                 5,      0,  10),
    ('CM',                 0.07,   0, 0.10),
    # ('morph_file', 'GP_arky_41comp.p'),
    # ('neuron_type',     'arky'),
    ('Eleak', -0.056, -0.080, -0.030),

    ('Cond_KDr_0', 300, 0, 1000),
    ('Cond_KDr_1', 58.2, 0, 300),
    ('Cond_KDr_2', 58.2, 0, 1000),

    # Kv3={prox: 266, dist: 46.6, axon: 466},
    ('Cond_Kv3_0', 266, 0, 1000),
    ('Cond_Kv3_1', 46.6, 0, 1000),
    ('Cond_Kv3_2', 266, 0, 1000),

    # KvF={prox: 2.5, dist: 2.5, axon: 25},
    ('Cond_KvF_0',  2.5, 0, 10),
    ('Cond_KvF_1',  2.5, 0, 10),
    ('Cond_KvF_2',  25, 0, 100),

    # KvS={prox: 0.75, dist: 0.75, axon: 7.5},
    ('Cond_KvS_0', 0.75, 0, 10),

    # NaF={prox: 40000, dist: 400, axon: 40000},
    ('Cond_NaF_0', 40e3, 0, 100e3),
    ('Cond_NaF_1', 400, 0, 2000),
    ('Cond_NaF_2', 40000, 0, 100000),

    # HCN1={prox: 0.2, dist: 0.2, axon: 0},
    # HCN2={prox: 0.25, dist: 0.25, axon: 0},
    # KCNQ={prox: 0.04, dist: 0.04, axon: 0.04},
    ('Cond_KCNQ_0', 0.04, 0, 10),

    # NaS={prox: 0.15, dist: 0.15, axon: 0.5},
    ('Cond_NaS_0', 0.15, 0, 10),

    # Ca={prox: 0.1, dist: 0.06, axon: 0},

    # SKCa={prox: 35, dist: 3.5, axon: 0},
    ('Cond_SKCa_0', 35, 0, 100),

    # BKCa={prox: 200, dist: 200, axon: 0},
    ('Cond_BKCa_0', 200, 0, 800),
)
paramsgp1 = paramsgp1.update(
    junction_potential=-0.019,
    RA=7.37,
    RM=3.95,
    CM=0.0234,
    Eleak=-0.043,
    Cond_KDr_0=52.2,
    Cond_KDr_1=70.6,
    Cond_KDr_2=0.264,
    Cond_Kv3_0=167,
    Cond_Kv3_1=84.6,
    Cond_Kv3_2=801,
    Cond_KvF_0=0.742,
    Cond_KvF_1=6.37,
    Cond_KvF_2=0.633,
    Cond_KvS_0=5.67,
    Cond_NaF_0=257,
    Cond_NaF_1=187,
    Cond_NaF_2=1.81e+03,
    Cond_KCNQ_0=0.0408,
    Cond_NaS_0=0.197,
    Cond_SKCa_0=13.4,
    Cond_BKCa_0=782)

fitness = aju.fitnesses.new_combined_fitness(response=1,
                                             baseline_pre=0,
                                             baseline_post=1,
                                             rectification=1,
                                             falling_curve_time=1,
                                             spike_time=1,
                                             spike_width=1,
                                             spike_height=1,
                                             spike_latency=0,
                                             spike_count=1,
                                             spike_ahp=1,
                                             ahp_curve=1,
                                             spike_range_y_histogram=1)
fitgp1 = aju.optimize.Fit('../fit-2017-gp-nr140-5.5', gpe.data['nr140'], 'gp', 'arky', fitness, paramsgp1)
fitgp1.load()
fitgp1.do_fit(150, popsize=12)



paramsgp2 = aju.optimize.ParamSet(
    ('junction_potential', -0.012, -0.020, -0.005),
    ('RA',                 5 ,     0, 100),
    ('RM',                 5,      0,  10),
    ('CM',                 0.07,   0, 0.10),
    # ('morph_file', 'GP_arky_41comp.p'),
    # ('neuron_type',     'arky'),
    ('Eleak', -0.056, -0.080, -0.030),

    ('Cond_KDr_0', 300, 0, 1000),
    ('Cond_KDr_1', 58.2, 0, 300),
    ('Cond_KDr_2', 58.2, 0, 1000),

    # Kv3={prox: 266, dist: 46.6, axon: 466},
    ('Cond_Kv3_0', 266, 0, 1000),
    ('Cond_Kv3_1', 46.6, 0, 1000),
    ('Cond_Kv3_2', 266, 0, 1000),

    # KvF={prox: 2.5, dist: 2.5, axon: 25},
    ('Cond_KvF_0',  2.5, 0, 10),
    ('Cond_KvF_1',  2.5, 0, 10),
    ('Cond_KvF_2',  25, 0, 100),

    # KvS={prox: 0.75, dist: 0.75, axon: 7.5},
    ('Cond_KvS_0', 0.75, 0, 10),

    # NaF={prox: 40000, dist: 400, axon: 40000},
    ('Cond_NaF_0', 40e3, 0, 100e3),
    ('Cond_NaF_1', 400, 0, 2000),
    ('Cond_NaF_2', 40000, 0, 100000),

    # HCN1={prox: 0.2, dist: 0.2, axon: 0},
    # HCN2={prox: 0.25, dist: 0.25, axon: 0},
    # KCNQ={prox: 0.04, dist: 0.04, axon: 0.04},
    ('Cond_KCNQ_0', 0.04, 0, 10),

    # NaS={prox: 0.15, dist: 0.15, axon: 0.5},
    ('Cond_NaS_0', 0.15, 0, 10),

    # Ca={prox: 0.1, dist: 0.06, axon: 0},

    # SKCa={prox: 35, dist: 3.5, axon: 0},
    ('Cond_SKCa_0', 35, 0, 100),

    # BKCa={prox: 200, dist: 200, axon: 0},
    ('Cond_BKCa_0', 200, 0, 800),
)
fitness = aju.fitnesses.new_combined_fitness(response=1,
                                             baseline_pre=0,
                                             baseline_post=1,
                                             rectification=1,
                                             falling_curve_time=1,
                                             spike_time=1,
                                             spike_width=1,
                                             spike_height=1,
                                             spike_latency=0,
                                             spike_count=1,
                                             spike_ahp=1,
                                             ahp_curve=1,
                                             spike_range_y_histogram=1)
fitgp2 = aju.optimize.Fit('../fit-2017-gp-nr144-2', gpe.data['nr144'], 'gp', 'proto', fitness, paramsgp2)
fitgp2.load()
fitgp2.do_fit(150, popsize=10)


paramsgp3 = paramsgp2.update(
    junction_potential=-0.0183,
    RA=1.84,
    RM=2.34,
    CM=0.0111,
    Eleak=-0.0585,
    Cond_KDr_0=914,
    Cond_KDr_1=22.4,
    Cond_KDr_2=0.0567,
    Cond_Kv3_0=673,
    Cond_Kv3_1=40,
    Cond_Kv3_2=0.201,
    Cond_KvF_0=0.795,
    Cond_KvF_1=2.62,
    Cond_KvF_2=24.7,
    Cond_KvS_0=1.46,
    Cond_NaF_0=8.13e+03,
    Cond_NaF_1=1.03e+03,
    Cond_NaF_2=5.02e+03,
    Cond_KCNQ_0=0.0857,
    Cond_NaS_0=1.74,
    Cond_SKCa_0=64.9,
    Cond_BKCa_0=189)
fitness = aju.fitnesses.new_combined_fitness(response=1,
                                             baseline_pre=0,
                                             baseline_post=1,
                                             rectification=1,
                                             falling_curve_time=0,
                                             spike_time=1,
                                             spike_width=1,
                                             spike_height=1,
                                             spike_latency=0,
                                             spike_count=1,
                                             spike_ahp=0,
                                             ahp_curve=0,
                                             spike_range_y_histogram=1)

fitgp3 = aju.optimize.Fit('../fit-2017-gp-nr144-3', gpe.data['nr144'], 'gp', 'proto', fitness, paramsgp3)
fitgp3.load()
fitgp3.do_fit(150, popsize=10)
