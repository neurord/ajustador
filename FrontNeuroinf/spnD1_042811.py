import ajustador as aju
from ajustador.helpers import save_params,converge
import numpy as np
from ajustador import drawing
import measurements1 as ms1
import os

# a. simplest approach is to use CAPOOL (vs CASHELL, and CASLAB for spines)
# b. no spines
# c. use ghk (and ghkkluge=0.35e-6) once that is working/implemented in moose
ghkkluge=1

modeltype='d1d2'
rootdir='/home/avrama/moose/SPN_opt/'
#use 1 and 3 for testing, 250 and 8 for optimization
generations=200
popsiz=8
seed=62938
#after generations, do 25 more at a time and test for convergence
test_size=25

################## neuron /data specific specifications #############
ntype='D1'
dataname='D1_042811'
exp_to_fit = ms1.D1waves042811[[8, 20, 22, 23]] #0,6 are hyperpol

dirname=dataname+'_pas2_'+str(seed)
if not dirname in os.listdir(rootdir):
    os.mkdir(rootdir+dirname)
os.chdir(rootdir+dirname)

tmpdir='/tmp/fit'+modeltype+'-'+ntype+'-'+dirname

######## set up parameters and fitness 

P = aju.optimize.AjuParam
params1 = aju.optimize.ParamSet(
    P('junction_potential', -.013,       fixed=1),
    P('RA',                 5.3,  min=1,      max=200),
    P('RM',                2.78,   min=0.1,      max=10),
    P('CM',                 0.010, min=0.001,      max=0.03),
    P('Cond_Kir',      9.5,      min=0, max=20),
    P('Eleak', -0.08, min=-0.080, max=-0.030),
    P('Cond_NaF_0',      219e3,      min=0, max=600e3),
    P('Cond_NaF_1',      1878,      min=0, max=10000),
    P('Cond_NaF_2',      878,      min=0, max=10000),
    P('Cond_KaS_0',      599,        min=0, max=2000),
    P('Cond_KaS_1',      372,        min=0, max=2000),
    P('Cond_KaS_2',      37.2,        min=0, max=200),
    P('Cond_KaF_0',      887,        min=0, max=2000),
    P('Cond_KaF_1',      641,        min=0, max=2000),
    P('Cond_KaF_2',      641,        min=0, max=2000),
    P('Cond_Krp_0',      0.05,        min=0, max=600),
    P('Cond_Krp_1',      0.05,        min=0, max=600),
    P('Cond_Krp_2',      0.05,        min=0, max=600),
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
    P('morph_file', 'MScelltaperspines.p', fixed=1),
    P('neuron_type', ntype,                     fixed=1),
    P('model',           'd1d2',     fixed=1))

#fitness=aju.fitnesses.combined_fitness('new_combined_fitness')
fitness = aju.fitnesses.combined_fitness('empty',
                                         response=1,
                                         baseline_pre=1,
                                         baseline_post=1,
                                         rectification=0,
                                         falling_curve_time=1,
                                         spike_time=0,
                                         spike_width=1,
                                         spike_height=1,
                                         spike_latency=1,
                                         spike_count=1,
                                         spike_ahp=1,
                                         ahp_curve=4,
                                         charging_curve=1,
                                         spike_range_y_histogram=1)

########### Neuron and fit specific commands ############
fit1 = aju.optimize.Fit(tmpdir,
                        exp_to_fit,
                        modeltype, ntype,
                        fitness, params1,
                        _make_simulation=aju.optimize.MooseSimulation.make,
                        _result_constructor=aju.optimize.MooseSimulationResult)

fit1.load()

fit1.do_fit(generations, popsize=popsiz,seed=seed)
mean_dict,std_dict,CV=converge.iterate_fit(fit1,test_size,popsiz)

#look at results
drawing.plot_history(fit1, fit1.measurement)

#Save parameters of good results from end of optimization, and all fitness values
startgood=1000  #set to 0 to print all
threshold=0.8  #set to large number to print all

save_params.save_params(fit1, startgood, threshold)

#to save the fit object
#save_params.persist(fit1,'.')
