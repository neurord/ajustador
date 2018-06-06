#!/usr/bin/python3
# sys.path.insert(0, "/home/ram/neural_prj/ajustador") #SRIRAM01302018
# sys.path.insert(0, "/home/ram/neural_prj/waves")     #SRIRAM01302018
# sys.path.insert(0, "/home/ram/neural_prj/moose_nerp") #SRIRAM01312018

# add ajustador to system PYTHONPATH
import sys
import ajustador as aju
import numpy as np
from ajustador import drawing
from matplotlib import pyplot
import gpedata_experimental as gpe #creata file to data in .npy.
import os

########### Optimization of GP neurons ##############3
#proto 079, 154

ntype='squid'
modeltype='squid'
#use 1 and 3 for testing, 250 and 8 for optimization
generations=1
popsiz=3

################## neuron /data specific specifications #############
dataname='proto079'
sys.exit(0) # TODO Remove it after test!!!! Test from below this point.
#dataname='nr120' #SRIRAM01312018
neuron_file_loc = '/home/ram/neural_prj/outputs/squid_opt/'+dataname+'F'
#Change directory so that outcmaes*.dat will be saved to different directories
if not os.path.exists(neuron_file_loc):
     os.mkdir(neuron_file_loc)

os.chdir(neuron_file_loc)

print("gpe data keys:", gpe.data.keys())
exp_to_fit = gpe.data[dataname + '-2s'][[0,2,4]] #SRIRAM01312018 removed '-2s'

tmpdir='/tmp/fit'+modeltype+'-'+ntype+'-'+dataname+'F'


######## set up parameters and fitness to be used for all opts  ############

#replaces the python2 execfile; import doesn't work unless package
# Use the save command and make note that should be fixed in future.
#exec(open("/home/ram/neural_prj/run_scripts/prof_resources/save_params.py").read())

P = aju.optimize.AjuParam
params1 = aju.optimize.ParamSet(
    P('junction_potential', -0.012, min=-0.020, max=-0.005),
    P('RA',                 1.000001,     min=0.1, max=10),
    P('RM',                 1.000001,      min=0.1,  max=4),
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

fit1.do_fit(generations, popsize=popsiz)

#look at results
drawing.plot_history(fit1, fit1.measurement)

#Save parameters of good results toward the end, and all fitness values
startgood=1500  #set to 0 to print all
threshold=0.40  #median for jan 11 fit to proto079

#save_params(fit1, startgood, threshold)

#Temporary directory cleanup #SRIRAM01022018
#import shutil                      #SRIRAM02022018
#shutil.rmtree(tmpdir)              #SRIRAM02022018
