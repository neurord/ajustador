import numpy as np
from ajustador import xml
import importlib

def save_params(fitX, start,threshold):

    #initialized arrays and lists for feature fitnesses and param values
    if isinstance(fitX[0],xml.NeurordSimulation):
        mols=list(fitX.fitness_func(fitX[0],fitX.measurement,full=1).keys())
        conditions=list(fitX.fitness_func(fitX[0],fitX.measurement,full=1)[mols[0]].keys())
        cols=len(mols)*len(conditions)
    else:
        model_params = importlib.import_module('moose_nerp.' + fitX.model)
        cols=len(fitX.fitness_func.report(fitX[0],fitX.measurement).split('\n'))
    rows=len(fitX)
    fitnessX=np.zeros((rows,cols))
    paramcols=len(fitX.param_names())
    paramvals=np.zeros((rows,paramcols))
    param_subset=[]  #this only saves a subset of simulation parameters

    #full=1 will print fitness of each feature, full=0 prints only overall fitness
    for i in range(len(fitX)):
        if isinstance(fitX[0],xml.NeurordSimulation):
            fitness_tmp=[fitX.fitness_func(fitX[i],fitX.measurement,full=1)[mol][cond] for mol in mols for cond in conditions]
            for j in range(len(fitness_tmp)):
                fitnessX[i,j]=fitness_tmp[j]
        else:
            fitnessX[i,0:-1]=fitX.fitness_func(fitX[i], fitX.measurement, full=1)
        fitnessX[i,-1]=fitX.fitness_func(fitX[i], fitX.measurement, full=0)
        #paramvals[i]=['%.5g'%(fitX[i].params[j].value) for j in fitX.param_names()] # Here we are rounding to 5 decimal places.wa
        paramvals[i]=[fitX[i].params[j].value for j in fitX.param_names()]
        line=list(paramvals[i])
        line.insert(0,i)
        if fitnessX[i,-1]<threshold and i>=start:
            line.append(fitnessX[i,-1])
            param_subset.append(line)

    fname=fitX.name
    if len(fitX.name)==0:
        fname=fitX.model
    header=[nm+'='+'%.5g'%(val)+'+/-'+'%.5g'%(stdev)
            for nm,val,stdev in zip(fitX.param_names(),
                                    fitX.params.unscale(fitX.optimizer.result()[0]),
                                    fitX.params.unscale(fitX.optimizer.result()[6]))]
    header.append('fitness')
    if isinstance(fitX[0],xml.NeurordSimulation):
        header.insert(0,'iteration')
        feature_list=["".join(mol+' '+cond) for mol in mols for cond in conditions]
    else:
        header.insert(0,'cell iteration')
        header.append('Init: cal='+str(model_params.calYN)+' spines='+str(model_params.spineYN))
        feature_list=fitX.fitness_func.report(fitX[-1],fitX.measurement).split('\n')
    feature_list.append('model='+fitX.model)
    if fitX.neuron_type is not None:
        feature_list.append('neuron='+fitX.neuron_type)
    #
    #save as text file to read into sas
    np.savetxt(fname+'.sasparams',param_subset,fmt='%-10s', header=" ".join(header))
    print ('parameters saved to', fname)
    #save entire parameters and individual fitness values as dictionary
    np.savez(fname, params=paramvals, paramnames=fitX.param_names(),fitvals=fitnessX,features=feature_list)

#To access the data:
#dat=np.load(fname)
#if np.save:
#data=dat.item()
#if np.savez:
#dat.keys(), then data['key'].item

def persist (fitX,path):
    import dill
    import os
    persist_path = path+'/'+fitX.name+"_persist_dill.obj"
    if os.path.exists(persist_path):
        os.remove(persist_path)
    with open(persist_path, 'wb') as persist:
        dill.dump(fitX, persist)

def load_persist(fname):
    import dill
    with open(fname,'rb') as persist:
        fit1 = dill.load(persist)
    return fit1
