import numpy as np
# from ajustador import xml 
import importlib

def save_params(fitX, start = 0,threshold = np.inf,fn=None, sas=False, npz=True):
    index = [i for i in range(len(fitX)) if i > start and fitX._history[i] < threshold]
    print(index)
    #initialized arrays and lists for feature fitnesses and param values
    if 'NeurordSimulation' in str(type(fitX[0])):
        mols=list(fitX.fitness_func(fitX[0],fitX.measurement,full=1).keys())
        conditions=list(fitX.fitness_func(fitX[0],fitX.measurement,full=1)[mols[0]].keys())
        cols=len(mols)*len(conditions)
    else:
        model_params = importlib.import_module('moose_nerp.' + fitX.model)
        cols=len(fitX.fitness_func.report(fitX[0],fitX.measurement).split('\n'))
    rows=len(index)
    fitnessX=np.zeros((rows,cols))
    paramcols=len(fitX.param_names())
    paramvals=np.zeros((rows,paramcols))
    param_subset=[]  #this only saves a subset of simulation parameters
    tmpdirs=[fitX[i].tmpdir.name for i in index]
    
    #full=1 will print fitness of each feature, full=0 prints only overall fitness
    for n,i in enumerate(index):
        if 'NeurordSimulation' in str(type(fitX[0])):
            fitness_tmp=[fitX.fitness_func(fitX[i],fitX.measurement,full=1)[mol][cond] for mol in mols for cond in conditions]
            for j in range(len(fitness_tmp)):
                fitnessX[n,j]=fitness_tmp[j]
        else:
            fitnessX[n,0:-1]=fitX.fitness_func(fitX[i], fitX.measurement, full=1)
        fitnessX[n,-1]=fitX._history[i]
        #paramvals[i]=['%.5g'%(fitX[i].params[j].value) for j in fitX.param_names()] # Here we are rounding to 5 decimal places.wa
        paramvals[n]=[fitX[i].params[j].value for j in fitX.param_names()]
        if sas:
            param_subset=paramvals

    fname=fitX.name
    if len(fitX.name)==0:
        fname=fitX.model
        if fn==None:
            fname=fname+fitX.measurement.name
        else:
            fname=fname+fn
    if callable(fitX.optimizer.result):
        result = fitX.optimizer.result()
    else:
        result = fitX.optimizer.result
    header=[nm+'='+'%.5g'%(val)+'+/-'+'%.5g'%(stdev)
            for nm,val,stdev in zip(fitX.param_names(),
                                    fitX.params.unscale(result[0]),
                                    fitX.params.unscale(result[6]))]
    opt_result={nm:{'mean':val,'std':stdev} for nm,val,stdev in zip(fitX.param_names(),
                                    fitX.params.unscale(result[0]),
                                    fitX.params.unscale(result[6]))}
    opt_result['datawave']=fitX.measurement.name
    header.append('fitness')
    if 'NeurordSimulation' in str(type(fitX[0])):
        header.insert(0,'iteration')
        feature_list=["".join(mol+' '+cond) for mol in mols for cond in conditions]
    else:
        header.insert(0,'cell iteration')
        model_bits='Init: cal='+str(model_params.calYN)+' spines='+str(model_params.spineYN)+' syn='+str(model_params.synYN)+' ghk='+str(model_params.ghkYN)+'plas='+str(model_params.plasYN)
        opt_result['model_bits']=model_bits
        header.append(model_bits)
        feature_list=fitX.fitness_func.report(fitX[-1],fitX.measurement).split('\n')
    feature_list.append('model='+fitX.model)
    if fitX.neuron_type is not None:
        feature_list.append('neuron='+fitX.neuron_type)
    feature_list.append('dataname='+fitX.measurement.name)
    #
    #save as text file to read into sas
    if sas:
        np.savetxt(fname+'.sasparams',param_subset,fmt='%-10s', header=" ".join(header))
        print('parameters saved to', fname)
    #save entire parameters and individual fitness values as dictionary
    if npz:
        np.savez(fname, params=paramvals, paramnames=fitX.param_names(),fitvals=fitnessX,features=feature_list,tmpdirs=tmpdirs,finalfit=opt_result)

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
