import ajustador as aju
from ajustador.helpers import save_params, converge
import numpy as np
from ajustador import drawing
import A2Acre as a2a
import os
import argparse
from params_fitness import params_fitness
from fit_commands import create_load_fit
from fit_commands import test_coverage

#must be in current working directory for this import to work, else use exec

# a. simplest approach is to use CAPOOL (vs CASHELL, and CASLAB for spines)
# b. no spines
# c. use ghk (and ghkkluge=0.35e-6) once that is working/implemented in moose

'''
ghkkluge=1
modeltype='d1d2'
ntype='D1'
morph_file='MScelltaperspines.p'
dataname='non05Jan2015_SLH004'
rootdir='/home/Sriramsagar/neural_prj/outputs/snp_opt/'
tmpdirroot='/tmp/Sriramsagar/'
#use 1 and 3 for testing, 250 and 8 for optimization
generations=200
popsiz=8
seed=62938
#after generations, do 25 more at a time and test for convergence
test_size=25
'''
################## neuron /data specific specifications #############

parser=argparse.ArgumentParser(description='Command line interface for NeuroRD ajustador optimization.')
parser.add_argument('--model', type=str)
parser.add_argument('--neuron', type=str)
parser.add_argument('--morph-file', type=str)
parser.add_argument('--dataname', type=str)
parser.add_argument('--output-root-dir', type=str)
parser.add_argument('--temp-root-dir', type=str)
parser.add_argument('--ghk-kluge', type=float, default=1)
parser.add_argument('--generations', type=int, default=3, help='Test: 3 Normal: 200(suggested)')
parser.add_argument('--popsize', type=int, default=1, help='Test: 1 Normal: 8(suggested)')
parser.add_argument('--seed', type=int, default=0)
parser.add_argument('--test-size', type=int, default=1)
parser.add_argument('--fit-trace-indices', type=list, default=[0])

args = parser.parse_args()

ghkkluge = args.ghk_kluge
modeltype = args.model
ntype = args.neuron
dataname = args.dataname
morph_file = args.morph_file
rootdir = args.output_root_dir
tmpdirroot = args.temp_root_dir
generations = args.generations
popsiz = args.popsize
seed = args.seed
test_size = args.test_size
trace_indices = [int(i) for i in args.fit_trace_indices]

exp_to_fit = a2a.waves[dataname][trace_indices] #0,6 are hyperpol

dirname=dataname+'_'+str(seed)
if not dirname in os.listdir(rootdir):
    os.mkdir(rootdir+dirname)
os.chdir(rootdir+dirname)
################## neuron /data specific specifications #############

######## set up parameters and fitness.
params1,fitness=params_fitness(morph_file,ntype,modeltype,ghkkluge)

########### Set-up optimization.
fit = create_load_fit(dirname,tmpdirroot, exp_to_fit,modeltype,ntype,fitness,params1)

########### Run optimization.
fit.do_fit(generations, popsize=popsiz, seed=seed)

########### Compute test coverage on fitnesses.
fit, mean_dict1, std_dict1, CV1 = test_coverage(fit, test_size, popsiz)

#look at results
drawing.plot_history(fit, fit.measurement)

#Save parameters of good results from end of optimization, and all fitness values
#startgood=0  #set to 0 to print all
#threshold=5  #set to large number to print all

#save_params.save_params(fit1, startgood, threshold)

#to save the fit object
#save_params.persist(fit1,'.')