import os
import sys
import numpy as np
import ajustador as aju
#import measurements1 as ms1
import {exp_data} as a2a

from ajustador import drawing
from matplotlib import pyplot
from ajustador.helpers import save_params,converge

# a. simplest approach is to use CAPOOL (vs CASHELL, and CASLAB for spines)
# b. no spines
# c. use ghk (and ghkkluge=0.35e-6) once that is working/implemented in moose
ghkkluge=1

ntype= '{ntype}'
modeltype= '{modeltype}'

generations = {generations}  # 1 for test run and 250 for actual run.
popsiz = {popsiz}  # 3 for test run and 8 for actual run.

morph_file= '{morph_file}'
dataname= '{dataname}'
rootdir = '{rootdir}'  # Checkthis
seed= {seed}
#after generations, do 25 more at a time and test for convergence
test_size= 25

dirname=dataname+str(seed)
if not dirname in os.listdir(rootdir):
    os.mkdir(rootdir+dirname)
os.chdir(rootdir+dirname)

################## neuron /data specific specifications #############
exp_to_fit = a2a.{datasection}[dataname][{trace_array}]

tmpdir = '{tmpdir}'+modeltype+'-'+ntype+'-'+dirname

######## set up parameters and fitness
P = aju.optimize.AjuParam
{aju_params_fitness}
########### Neuron and fit specific commands ############

fit = aju.optimize.Fit(tmpdir,
                        exp_to_fit,
                        modeltype, ntype,
                        fitness, params,
                        _make_simulation=aju.optimize.MooseSimulation.make,
                        _result_constructor=aju.optimize.MooseSimulationResult)

fit.load()

fit.do_fit(generations, popsize=popsiz, seed=seed)
mean_dict,std_dict,CV=converge.iterate_fit(fit,test_size,popsiz, max_evals=7000)

#look at results
#drawing.plot_history(fit, fit.measurement)

#Save parameters of good results from end of optimization, and all fitness values
startgood=0  #set to 0 to print all
threshold=1000  #set to large number to print all
save_params.save_params(fit, startgood, threshold)

#to save the fit object
save_params.persist(fit,'.')
