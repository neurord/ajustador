import numpy as np

def save_params(fitX, start,threshold):

    #initialized arrays and lists for feature fitnesses and param values
    cols=len(fitX.fitness_func.report(fitX[0],fitX.measurement).split('\n'))
    rows=len(fitX)
    fitnessX=np.zeros((rows,cols))
    paramcols=len(fitX.param_names())
    paramvals=np.zeros((rows,paramcols))
    param_subset=[]  #this only saves a subset of simulation parameters
    
    #full=1 will print fitness of each feature, full=0 prints only overall fitness
    for i in range(len(fitX)):
        fitnessX[i,0:-1]=fitX.fitness_func(fitX[i], fitX.measurement, full=1)
        fitnessX[i,-1]=fitX.fitness_func(fitX[i], fitX.measurement, full=0)
        paramvals[i]=[np.round(fitX[i].params[j].value,6) for j in fitX.param_names()]
        line=list(paramvals[i])
        line.insert(0,i)
        if fitnessX[i,-1]<threshold and i>=start:
            line.append(fitnessX[i,-1])
            param_subset.append(line)

    fname=fitX.name
    header=[nm+'='+str(np.round(val,6))+'+/-'+str(np.round(stdev,6))
            for nm,val,stdev in zip(fitX.param_names(),
                                    fitX.params.unscale(fitX.optimizer.result()[0]),
                                    fitX.params.unscale(fitX.optimizer.result()[6]))]
    header.append('fitness')
    header.insert(0,'cell iteration')
    feature_list=fitX.fitness_func.report(fitX[-1],fitX.measurement).split('\n')
    feature_list.append('model='+fitX.model)
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
