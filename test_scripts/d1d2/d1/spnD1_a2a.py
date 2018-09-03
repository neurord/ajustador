import ajustador as aju
from ajustador.helpers import save_params,converge
import numpy as np
from ajustador import drawing
import A2Acre as a2a
import os
#must be in current working directory for this import to work, else use exec
from params_fitness import params_fitness
from fit_commands import create_load_fit
from fit_commands import test_coverage

# a. simplest approach is to use CAPOOL (vs CASHELL, and CASLAB for spines)
# b. no spines
# c. use ghk (and ghkkluge=0.35e-6) once that is working/implemented in moose
ghkkluge=1

modeltype='d1d2'
rootdir='/home/Sriramsagar/neural_prj/outputs/snp_opt/'
tmpdirroot='/tmp/Sriramsagar/'
#use 1 and 3 for testing, 250 and 8 for optimization
generations=2
popsiz=8
seed=62938
#after generations, do 25 more at a time and test for convergence
test_size=25

################## neuron /data specific specifications #############
ntype='D1'
morph_file='MScelltaperspines.p'
dataname='non05Jan2015_SLH004'
exp_to_fit = a2a.waves[dataname][[0, 6, 10, 15, 16, 20]] #0,6 are hyperpol

dirname=dataname+'_'+str(seed)
if not dirname in os.listdir(rootdir):
    os.mkdir(rootdir+dirname)
os.chdir(rootdir+dirname)

######## set up parameters and fitness.
params1,fitness=params_fitness(morph_file,ntype,modeltype,ghkkluge)

########### Set-up optimization.
fit = create_load_fit(dirname,tmpdirroot, exp_to_fit,modeltype,ntype,fitness,params1)

########### Run optimization.
fit.do_fit(generations, popsize=popsiz, seed=seed)

########### Compute test coverage on fitnesses.
fit, mean_dict1, std_dict1, CV1 = test_coverage(fit, test_size, popsiz)

#look at results
drawing.plot_history(fit1, fit1.measurement)

#Save parameters of good results from end of optimization, and all fitness values
#startgood=0  #set to 0 to print all
#threshold=5  #set to large number to print all

#save_params.save_params(fit1, startgood, threshold)

#to save the fit object
#save_params.persist(fit1,'.')
