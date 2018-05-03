import ajustador as aju
from ajustador.helpers import save_params,converge
import numpy as np
from ajustador import drawing
import gpedata_experimental as gpe
import os

########### Optimization of GP neurons ##############3
#proto 079, 154

ntype='proto'
modeltype='gp'
rootdir='/home/avrama/moose/gp_opt/'
#use 1 and 3 for testing, 200 and 8 for optimization
generations=200
popsiz=8
seed=62938
#after generations, do 25 more at a time and test for convergence
test_size=25

################## neuron /data specific specifications #############
dataname='proto079'
exp_to_fit = gpe.data[dataname+'-2s'][[0,2,4]]

dirname=dataname+'F_'+str(seed)
if not dirname in os.listdir(rootdir):
    os.mkdir(rootdir+dirname)
os.chdir(rootdir+dirname)

tmpdir='/tmp/fit'+modeltype+'-'+ntype+'-'+dirname

######## set up parameters and fitness to be used for all opts  ############

P = aju.optimize.AjuParam
params1 = aju.optimize.ParamSet(
    P('junction_potential', -0.012, min=-0.020, max=-0.005),
    P('RA',                 1.74,     min=0.1, max=12),
    P('RM',                 1.3,      min=0.1,  max=8),
    P('CM',                 0.014,   min=0.005, max=0.05),
    P('Eleak', -0.056, min=-0.070, max=-0.030),
    P('Cond_KDr_0', 40, min=0, max=1000),
    P('Cond_KDr_1', 8.2, min=0, max=300),
    P('Cond_KDr_2', 80, min=0, max=1000),
    P('Cond_Kv3_0', 766, min=0, max=1000),
    P('Cond_Kv3_1', 146.6, min=0, max=2000),
    P('Cond_Kv3_2', 1266, min=0, max=2000),
    P('Cond_KvF_0',  10, min=0, max=50),
    P('Cond_KvF_1',  10, min=0, max=50),
    P('Cond_KvF_2',  25, min=0, max=100),
    P('Cond_KvS_0', 1, min=0, max=50),
    P('Cond_KvS_1', 3, min=0, max=50),
    P('Cond_KvS_2', 3, min=0, max=50),
    P('Cond_NaF_0', 400, min=100, max=100e3),
    P('Cond_NaF_1', 40, min=10, max=2000),
    P('Cond_NaF_2', 4000, min=100, max=100000),
    P('Cond_HCN1_0', 0.2, min=0.0, max=1.2),
    P('Cond_HCN1_1', 0.2, min=0.0, max=1.2),
    P('Cond_HCN2_0', 0.2, min=0.0, max=1.2),
    P('Cond_HCN2_1', 0.2, min=0.0, max=1.2),
    P('Cond_KCNQ_0', 0.04, min=0, max=1),
    P('Cond_NaS_0', 0.5, min=0, max=10),
    P('Cond_NaS_1', 0.5, min=0, max=10),
    P('Cond_Ca_0', 0.1, min=0, max=10),
    P('Cond_Ca_1', 0.1, min=0, max=10),
    P('Cond_SKCa_0', 2, min=0, max=100),
    P('Cond_SKCa_1', 2, min=0, max=100),
    P('Cond_BKCa_0', 2, min=0, max=800),
    P('Cond_BKCa_1', 2, min=0, max=800),
    P('morph_file', 'GP1_41comp.p', fixed=1),
    P('neuron_type',     ntype, fixed=1),
    P('model',           modeltype,     fixed=1))

fitness = aju.fitnesses.combined_fitness('empty',
                                         response=1,
                                         baseline_pre=0,
                                         baseline_post=1,
                                         rectification=2,
                                         falling_curve_time=1,
                                         spike_time=0.5,
                                         spike_width=1,
                                         spike_height=1,
                                         spike_latency=0,
                                         spike_count=1,
                                         spike_ahp=1,
                                         ahp_curve=1,
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
mean_dict1,std_dict1,CV1=converge.iterate_fit(fit1,test_size,popsiz)

#look at results
drawing.plot_history(fit1, fit1.measurement)

#Save parameters of good results toward the end, and all fitness values
startgood=1500  #set to 0 to print all
threshold=0.40  #median 
save_params.save_params(fit1, startgood, threshold)
#save_params.persist(fit1,'.')

################## Next neuron #############
dataname='proto154'
exp_to_fit = gpe.data[dataname+'-2s'][[0,2,4]]

dirname=dataname+'F_'+str(seed)
if not dirname in os.listdir(rootdir):
    os.mkdir(rootdir+dirname)
os.chdir(rootdir+dirname)

tmpdir='/tmp/fit'+modeltype+'-'+ntype+'-'+dirname

fit2 = aju.optimize.Fit(tmpdir,
                        exp_to_fit,
                        modeltype, ntype,
                        fitness, params1,
                        _make_simulation=aju.optimize.MooseSimulation.make,
                        _result_constructor=aju.optimize.MooseSimulationResult)

fit2.load()

fit2.do_fit(generations, popsize=popsiz,seed=seed)
mean_dict2,std_dict2,CV2=converge.iterate_fit(fit2,test_size,popsiz)

#look at results
drawing.plot_history(fit2, fit2.measurement)

startgood=1500
threshold=0.34 #median = 0.34 
save_params.save_params(fit2, startgood, threshold) 
#save_params.persist(fit2,'.')

