import os
import sys
import numpy as np
import ajustador as aju
#import measurements1 as ms1
import A2Acre as a2a

from ajustador import drawing
from matplotlib import pyplot
from ajustador.helpers import save_params,converge

# a. simplest approach is to use CAPOOL (vs CASHELL, and CASLAB for spines)
# b. no spines
# c. use ghk (and ghkkluge=0.35e-6) once that is working/implemented in moose
ghkkluge=1

ntype='D2'
modeltype='d1d2'

generations = 250  # 1 for test run and 250 for actual run.
popsiz = 8  # 3 for test run and 8 for actual run.

morph_file= 'MScelltaperspines.p'
dataname= 'LR06Jan2015_SLH004'
rootdir = '/home/Sriramsagar/neural_prj/outputs/spn_opt/'  # Checkthis
seed=20112018
#after generations, do 25 more at a time and test for convergence
test_size=25

dirname=dataname+'_labmanual_'+str(seed)
if not dirname in os.listdir(rootdir):
    os.mkdir(rootdir+dirname)
os.chdir(rootdir+dirname)

################## neuron /data specific specifications #############
exp_to_fit = a2a.alldata[dataname][[1, 15, 18, 20]]

tmpdir = '/tmp/Sriramsagar'+modeltype+'-'+ntype+'-'+dirname

P = aju.optimize.AjuParam
params = aju.optimize.ParamSet(
    P('junction_potential', -.013,       fixed=1),
    P('RA',                 5.3,  min=1,      max=200),
    P('RM',                2.78,   min=0.1,      max=10),
    P('CM',                 0.010, min=0.001,      max=0.03),
    P('Cond_Kir',      9.5,      min=0, max=20),
    P('Chan_Kir_taumul',      1,      min=0.5, max=2),
    P('Chan_Kir_vshift',      0,      min=-10E-3, max=10E-3),
    P('Eleak', -0.08, min=-0.080, max=-0.030),
    P('Chan_NaF_vshift',  0,      min=-10E-3, max=10E-3),
    P('Chan_NaF_taumul',  1,        min=0.5, max=2),
    P('Cond_NaF_0',      219e3,      min=0, max=600e3),
    P('Cond_NaF_1',      1878,      min=0, max=10000),
    P('Cond_NaF_2',      878,      min=0, max=10000),
    P('Chan_KaS_vshift',  0,      min=-10E-3, max=10E-3),
    P('Chan_KaS_taumul',  1,        min=0.5, max=2),
    P('Cond_KaS_0',      599,        min=0, max=2000),
    P('Cond_KaS_1',      372,        min=0, max=2000),
    P('Cond_KaS_2',      37.2,        min=0, max=200),
    P('Chan_KaF_vshift',  0,      min=-10E-3, max=10E-3),
    P('Chan_KaF_taumul',  1,        min=0.5, max=2),
    P('Cond_KaF_0',      887,        min=0, max=2000),
    P('Cond_KaF_1',      641,        min=0, max=2000),
    P('Cond_KaF_2',      641,        min=0, max=2000),
    P('Chan_Krp_vshift',  0,      min=-10E-3, max=10E-3),
    P('Chan_Krp_taumul',  1,        min=0.5, max=2),
    P('Cond_Krp_0',      0.05,        min=0, max=60),
    P('Cond_Krp_1',      0.05,        min=0, max=60),
    P('Cond_Krp_2',      0.05,        min=0, max=60),
    P('Cond_SKCa', 1.7, min=0, max=5),
    P('Cond_BKCa', 5.6, min=0, max=50),
    P('Cond_CaN_0',      3*ghkkluge,      min=0, max=100*ghkkluge),
    P('Cond_CaT_1',      2*ghkkluge,      min=0, max=100*ghkkluge),
    P('Cond_CaT_2',      2*ghkkluge,      min=0, max=100*ghkkluge),
    P('Cond_CaL12_0',    8*ghkkluge,      min=0, max=100*ghkkluge),
    P('Cond_CaL12_1',    4*ghkkluge,      min=0, max=100*ghkkluge),
    P('Cond_CaL12_2',    4*ghkkluge,      min=0, max=100*ghkkluge),
    P('Cond_CaL13_0',   12*ghkkluge,      min=0, max=100*ghkkluge),
    P('Cond_CaL13_1',    6*ghkkluge,      min=0, max=100*ghkkluge),
    P('Cond_CaL13_2',    6*ghkkluge,      min=0, max=100*ghkkluge),
    P('Cond_CaR_0',     20*ghkkluge,      min=0, max=1000*ghkkluge),
    P('Cond_CaR_1',     45*ghkkluge,      min=0, max=1000*ghkkluge),
    P('Cond_CaR_2',     45*ghkkluge,      min=0, max=1000*ghkkluge),
    P('morph_file', morph_file, fixed=1),
    P('neuron_type', ntype,                     fixed=1),
    P('model',           modeltype,     fixed=1))


fitness = aju.fitnesses.combined_fitness('empty',
                                         response=1,
                                         baseline_pre=1,
                                         baseline_post=1,
                                         rectification=1,
                                         falling_curve_time=1,
                                         spike_time=0,
                                         spike_width=1,
                                         spike_height=1,
                                         spike_latency=1,
                                         spike_count=1,
                                         spike_ahp=1,
                                         ahp_curve=2,
                                         charging_curve=1,
                                         spike_range_y_histogram=1)
########### Neuron and fit specific commands ############

fit = aju.optimize.Fit(tmpdir,
                        exp_to_fit,
                        modeltype, ntype,
                        fitness, params,
                        _make_simulation=aju.optimize.MooseSimulation.make,
                        _result_constructor=aju.optimize.MooseSimulationResult)

fit.load()

fit.do_fit(generations, popsize=popsiz, seed=seed)

startgood=1000  #set to 0 to print all
threshold=0.8  #set to large number to print all
s_crt = 2E-3
max_eval = 5000
fitness=[fit.fitness_func(fit[i], fit.measurement, full=0) for i in range(len(fit))]

while(True):
    mean_dict,std_dict,CV=converge.iterate_fit(fit,test_size,popsiz, slope_crit=s_crt, max_evals=max_eval, fitness=fitness)
    save_params.save_params(fit, startgood, threshold)
    char = input("plot_history opt (Y/N):")
    if char.upper() == 'Y':
        drawing.plot_history(fit, fit.measurement)
    char = input("Continue opt (Y/N):")
    if char.upper() == 'N':
        break
    else:
        s_crt = np.float32(input("slope_criteria old_cirterial is {}?".format(s_crt)))
        max_eval = np.long(input("Maximum evaluations must be > {}?".format(len(fit))))
        continue
#Save parameters of good results from end of optimization, and all fitness values
#startgood=1000  #set to 0 to print all
#threshold=0.8  #set to large number to print all
#save_params.save_params(fit, startgood, threshold)

#to save the fit object
#save_params.persist(fit3,'.')
