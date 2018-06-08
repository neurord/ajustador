#!/usr/bin/python3

import os
import sys
import numpy as np
import ajustador as aju
import squid_experimental as squid # Acutual experimental data from waves.

from ajustador import drawing
from matplotlib import pyplot

########### Optimization of Squid 2 compartment neuron ##############
ntype='squid' # neuron type.
modeltype='squid' # Neuron model.
generations=1 # 1 for test run and 250 for actual run.
popsiz=3 # 3 for test run and 8 for actual run.

################## neuron /data specific specifications #############
dataname='squid_experimental' # what should be the dataname???
neuron_file_loc = '/home/Sriramsagar/neural_prj/outputs/squid_opt/'+dataname+'F'
#Change directory so that outcomes*.dat will be saved to different directories
if not os.path.exists(neuron_file_loc):
    os.mkdir(neuron_file_loc)

os.chdir(neuron_file_loc)

print("squid data keys:", squid.data.keys())
exp_to_fit = squid.data[dataname] # TODO check for data!!! get professors help.

tmpdir='/tmp/fit'+modeltype+'-'+ntype+'-'+dataname+'F'

######## setup parameters for fitness ############

P = aju.optimize.AjuParam
params1 = aju.optimize.ParamSet(
    P('junction_potential', -0.012, min=-0.020, max=-0.005),
    P('RA',                 1.000001,     min=0.1, max=10),
    P('RM',                 1.000001,      min=0.1,  max=4),
    P('CM',                 0.014,   min=0.005, max=0.05),
    P('Eleak', -0.056, min=-0.070, max=-0.030),
    P('Cond_K_0', 40, min=0, max=1000),
    P('Cond_K_1', 8.2, min=0, max=300),
    P('Cond_K_2', 80, min=0, max=1000),
    P('Cond_Na_0', 766, min=0, max=1000),
    P('Cond_Na_1', 146.6, min=0, max=2000),
    P('Cond_Na_2', 1266, min=0, max=2000),
    #P('Chan_K_vshift_X', 0.001, min=0, max=0.002),
    P('morph_file', 'squid.p', fixed=1),
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
sys.exit(0) # TODO Remove it after test!!!! Test from below this point.

#look at results
drawing.plot_history(fit1, fit1.measurement)

#Save parameters of good results toward the end, and all fitness values
startgood=1500  #set to 0 to print all
threshold=0.40  #median for jan 11 fit to proto079

#save_params(fit1, startgood, threshold)

#Temporary directory cleanup #SRIRAM01022018
#import shutil                      #SRIRAM02022018
#shutil.rmtree(tmpdir)              #SRIRAM02022018
