import ajustador as aju
import numpy as np
from ajustador import drawing
from matplotlib import pyplot
import EPdata as epdata

dataname='120617'
ntype='ep'
modeltype='ep'

exp_to_fit=epdata.EPwaves120617[[0,2,5,7]]

P = aju.optimize.AjuParam
params1 = aju.optimize.ParamSet(
    P('junction_potential', -0.012, min=-0.020, max=-0.005),
    P('RA',                 4 ,     min=1, max=10),
    P('RM',                 4,      min=1,  max=10),
    P('CM',                 0.007,   min=.002, max=0.012),
    P('Eleak', -0.056, min=-0.070, max=-0.030),
    P('Cond_KDr_0', 4, min=0, max=100),
    P('Cond_KDr_1', 6, min=0, max=30),
    P('Cond_KDr_2', 20, min=0, max=100),
    P('Cond_Kv3_0', 600, min=0, max=1000),
    P('Cond_Kv3_1', 70, min=0, max=1000),
    P('Cond_Kv3_2', 1400, min=0, max=2000),
    P('Cond_KvF_0',  100, min=0, max=200),
    P('Cond_KvF_1',  100, min=0, max=200),
    P('Cond_KvF_2',  100, min=0, max=200),
    P('Cond_NaF_0', 20e3, min=100, max=100e3),
    P('Cond_NaF_1', 200, min=0, max=2000),
    P('Cond_NaF_2', 20e3, min=100, max=100e3),
    # HCN1={prox: 0.4, dist: 0.4, axon: 0},
    P('Cond_HCN1_0', 0.3, min=0.1, max=2),
    P('Cond_HCN1_1', 0.3, min=0.1, max=2),
    P('Cond_NaS_0', 0.3, min=0, max=10),
    # Ca={prox: 0.1, dist: 0.06, axon: 0},
    P('Cond_Ca_0', 0.1, min=0, max=10),
    P('Cond_SKCa_0', 2, min=0, max=100),
    P('Cond_BKCa_0', 0.1, min=0, max=10),
    P('morph_file', 'EP_41comp.p', fixed=1),
    P('neuron_type',     ntype, fixed=1),
    P('model',           modeltype,     fixed=1))

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

tmpdir='/tmp/fit-'+modeltype+'-'+ntype+'-'+dataname
fit1 = aju.optimize.Fit(tmpdir,
                          exp_to_fit,
                          modeltype, ntype,
                          fitness, params1,
                          _make_simulation=aju.optimize.MooseSimulation.make,
                          _result_constructor=aju.optimize.MooseSimulationResult)

fit1.load()

fit1.do_fit(400, popsize=8)

drawing.plot_history(fit1, fit1.measurement)

#full=1 will print fitness of each feature, full=0 prints only overall fitness
for i in range(len(fit1)):
    print(i, fit1.fitness_func(fit1[i], fit1.measurement, full=1),
          '→', fit1.fitness_func(fit1[i], fit1.measurement, full=0))

#to print param values for all simulations the last N simulations which fit well:
startgood=2800  #set to 0 to print all
threshold=0.63  #set to large number to print all
paramvals=[]

fname=ntype+'_'+dataname+'.params'
header=[nm+'='+str(np.round(val,6))+'+/-'+str(np.round(stdev,6))
        for nm,val,stdev in zip(fit1.param_names(),
                                fit1.params.unscale(fit1.optimizer.result()[0]),
                                fit1.params.unscale(fit1.optimizer.result()[6]))]
header.append('fitness')
header.insert(0,'iteration')
for i in range(startgood,len(fit1)):
    if fit1.fitness_func(fit1[i], fit1.measurement, full=0)<threshold:
        line=[fit1[i].params[j].value for j in fit1[i].params.keys()
              if j != 'simtime' and not fit1[i].params[j].fixed]
        line.append(fit1.fitness_func(fit1[i], fit1.measurement, full=0))
        paramvals.append(line.insert(0,i))

np.savetxt(fname,paramvals,fmt='%.6f', header=" ".join(header))
