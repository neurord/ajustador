import ajustador as aju
import measurements1 as ms1
import numpy as np
from ajustador import drawing
from matplotlib import pyplot
import gpedata_experimental as gpe

#####################################################################################
# example using hyperpol_fitness() - which uses only hyperpolarizing currents
#####################################################################################
exp_to_fit = ms1.D1waves042811[[0, 6, 9]]
P = aju.optimize.AjuParam
params5 = aju.optimize.ParamSet(
    P('junction_potential', 0,       min=-0.030, max=+0.030),
    P('RA',                 12.004,  min=0,      max=100),
    P('RM',                 9.427,   min=0,      max=10),
    P('CM',                 0.03604, min=0,      max=0.10),
    P('Cond_Kir',           14.502,  min=0,      max=100),
    P('Kir_offset',         -.004,   min=-0.005, max=+0.005),
    P('morph_file', 'MScell-tertDendlongRE.p', fixed=1),
    P('neuron_type', 'D1',                     fixed=1),
    P('model',           'd1d2',     fixed=1))

fit5 = aju.optimize.Fit('/tmp/out3',
                        exp_to_fit,
                        'd1d2', 'D1',
                        aju.fitnesses.hyperpol_fitness, params5,
                        _make_simulation=aju.optimize.MooseSimulation.make,
                        _result_constructor=aju.optimize.MooseSimulationResult)
#NOTE, if fit directory has stuff in it, then you get an error:
#  File "/home/avrama/moose/ajustador/ajustador/optimize.py", line 341, in <genexpr>
#    self.fixedparams = tuple(p for p in self.params if p.fixed)
#AttributeError: 'str' object has no attribute 'fixed'

fit5.load()
#Default population size is 8
fit5.do_fit(100)

for i in range(len(fit5)):
    print(i, fit5.fitness_func(fit5[i], fit5.measurement, full=1),
          '→', fit5.fitness_func(fit5[i], fit5.measurement, full=0))
    #to print param values for all simulations
    print(fit5[i].params)
#print best estimate of parameters
for i in len(fit5.param_names()):
    print(fit5.param_names()[i], ':', fit5.params.unscale(fit5.optimizer.result()[0])[i])
      
drawing.plot_history(fit5, fit5.measurement)

#####################################################################################
# example using combined_fitness() - which uses both hyperpolarizing and depolarizing currents
#####################################################################################
exp_to_fit = ms1.D1waves042811[[0, 6, 9]]
P = aju.optimize.AjuParam
params6 = aju.optimize.ParamSet(
    P('junction_potential', 0,       min=-0.015, max=+0.015),
    P('RA',                 12.004,  min=0,      max=100),
    P('RM',                 9.427,   min=0,      max=10),
    P('CM',                 0.03604, min=0,      max=0.10),
    P('Cond_Kir',           14.502,  min=0,      max=100),
    P('Kir_offset',         -.004,   min=-0.005, max=+0.005),
    P('morph_file', 'MScell-tertDendlongRE.p', fixed=1),
    P('neuron_type', 'D1',                     fixed=1),
    P('Cond_NaF_0',      150e3,      min=0, max=600e3),
    P('Cond_KaS_0',      372,        min=0, max=600),
    P('Cond_KaF_0',      641,        min=0, max=1000),
    P('Cond_Krp_0',      177,        min=0, max=600),
    P('model',           'd1d2',     fixed=1))

fit6 = aju.optimize.Fit('/tmp/out2',
                        ms1.waves5[[0, 3, 7, 13, 17, 19, 21, 22, 23]],
                        'd1d2', 'D1',
                        aju.fitnesses.combined_fitness(), params6,
                        _make_simulation=aju.optimize.MooseSimulation.make,
                        _result_constructor=aju.optimize.MooseSimulationResult)
fit6.load()
iterations=1
fit6.do_fit(iterations, popsize=2)

#full=1 will print fitness of each feature, full=0 prints only overall fitness
for i in range(len(fit6)):
    print(i, fit6.fitness_func(fit6[i], fit6.measurement, full=1),
          '→', fit6.fitness_func(fit6[i], fit6.measurement, full=0))
    #to print param values, either of these two will work
    print(fit6[0].params)
    print(fit6.params.unscale(fit6.optimizer.result()[i]))
drawing.plot_history(fit6, fit6.measurement)

#####################################################################################
#example showing how to update parameters with results of previous optimization, and then start again
#This still needs testing
#####################################################################################
# fit6.params.update(**fit6[5650].params)
P = aju.optimize.AjuParam
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
fit7 = aju.optimize.Fit('./tmp/out2',
                        ms1.waves5[[0, 7, 17, 21, 23]],
                        'd1d2', 'D1',
                        aju.fitnesses.combined_fitness(), params7,
                        _make_simulation=aju.optimize.MooseSimulation.make,
                        _result_constructor=aju.optimize.MooseSimulationResult)
fit7.load()
fit7.do_fit(150, popsize=8)

#####################################################################################
#How to plot the fitness history of various features
#####################################################################################

drawing.plot_history(fit7, fit7.measurement, fitness=aju.fitnesses.combined_fitness())
drawing.plot_history(fit7, fit7.measurement, fitness=aju.fitnesses.spike_time_fitness, clear=False)
drawing.plot_history(fit7, fit7.measurement, fitness=aju.fitnesses.spike_width_fitness, clear=False)
drawing.plot_history(fit7, fit7.measurement, fitness=aju.fitnesses.spike_ahp_fitness, clear=False)
drawing.plot_history(fit7, fit7.measurement, fitness=aju.fitnesses.ahp_curve_fitness, clear=False)

#####################################################################################
#another example showing how to update parameters with results of previous optimization, and then start again
#
# updated fitness functions, use wave with late spikes to fit latency
# fit9.params.update(**fit9["194"].params)
#####################################################################################
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
fitness = aju.fitnesses.combined_fitness('new_combined_fitness')

fit10 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-10',
                         ms1.waves5[[0, 7, 17, 18, 21]],
                        'd1d2', 'D1',
                         fitness, params10, 
                        _make_simulation=aju.optimize.MooseSimulation.make,
                        _result_constructor=aju.optimize.MooseSimulationResult)
fit10.load()

#####################################################################################
#How to plot the overall fitness history
#####################################################################################
drawing.plot_history(fit10, fit10.measurement)
fit10.do_fit(400, popsize=20)

# the same as before, but with spike_latency_fitness thrown into the mix
fitness = aju.fitnesses.combined_fitness('new_combined_fitness')
fit11 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-11',
                         ms1.waves5[[0, 7, 17, 18, 21]],
                        'd1d2', 'D1',
                         fitness, params10, 
                        _make_simulation=aju.optimize.MooseSimulation.make,
                        _result_constructor=aju.optimize.MooseSimulationResult)
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
fitness = aju.fitnesses.combined_fitness('new_combined_fitness')
fit11a = aju.optimize.Fit('../fit-2017-aju-cma-wave5-11a',
                          ms1.waves5[[0, 7, 17, 18, 21]],
                          fitness, params11a)
fit11a.load(last=200)
fit11a.do_fit(400, popsize=20)

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
fitness = aju.fitnesses.combined_fitness('new_combined_fitness')
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
fitness = aju.fitnesses.combined_fitness('new_combined_fitness')
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
fitness = aju.fitnesses.combined_fitness('new_combined_fitness')
fit14 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-14',
                         ms1.waves5[[0, 7, 17, 18, 21]],
                         'd1d2', 'D1',
                         fitness, params14)
fit14.load(last=200)
fit14.do_fit(100, popsize=30)



fit14_waves1 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-14-waves1',
                                ms1.waves1[[0, 7, 22, 23]],
                                'd1d2', 'D1',
                                fitness, params14)
fit14_waves1.load()
fit14_waves1.do_fit(300, popsize=12)


fit14_waves3 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-14-waves3_2',
                                ms1.waves3[[0, 8, -4, -1]],
                                'd1d2', 'D1',
                                fitness, params14)
fit14_waves3.load()
fit14_waves3.do_fit(400, popsize=12)

# There are no hyperpolarizing injections, hence no falling curves
fitness10 = aju.fitnesses.combined_fitness('new_combined_fitness',
                                           falling_curve_time=0)
fit14_waves10 = aju.optimize.Fit('../fit-2017-aju-cma-wave5-14-waves10',
                                 ms1.waves10[[0, 7, -3, -1]],
                                 'd1d2', 'D1',
                                 fitness10, params14)
fit14_waves10.load()
fit14_waves10.do_fit(300, popsize=12)


#####################################################################################
# example using GP data.  Note elimination of basline and spike_latency in fitness
#####################################################################################

fitness = aju.fitnesses.combined_fitness('empty',
                                         response=1,
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
fitgp1 = aju.optimize.Fit('../fit-2017-gp-nr140-5.5', gpe.data['nr140'], 'gp', 'arky', fitness, paramsgp1, 
                        _make_simulation=aju.optimize.MooseSimulation.make,
                        _result_constructor=aju.optimize.MooseSimulationResult)
fitgp1.load()
fitgp1.do_fit(150, popsize=12)

############### Update example.  Need to test if this works

paramsgp2 = paramsgp1.update(
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
fitness = aju.fitnesses.combined_fitness('empty',
                                         response=1,
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

fitgp2 = aju.optimize.Fit('../fit-2017-gp-nr144-3', gpe.data['nr144'], 'gp', 'proto', fitness, paramsgp2, 
                        _make_simulation=aju.optimize.MooseSimulation.make,
                        _result_constructor=aju.optimize.MooseSimulationResult)
fitgp2.load()
fitgp2.do_fit(150, popsize=10)
