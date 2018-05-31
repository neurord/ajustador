from __future__ import print_function, division

import numpy as np
from ajustador import nrd_output,xml
import os

import logging 
from ajustador.helpers.loggingsystem import getlogger 
logger = getlogger(__name__) 
logger.setLevel(logging.INFO)

''' to do: 
1. Turn this into class, which has attribute norm.  Then, can use that attribute in plot_neurord_tog to plot %
2. align experiments and simulations so that simulations can be shorter than experiments
a. instantiate a wave class with stim start time
b. possibly read stim start from model.xml
c. use stim start in wave and sim to align data
d. align the simulation with experiment in fitness function based on filename param, not just sorted
'''

def specie_concentration_fitness(*, voxel=0, species_list, trial=0,start=0,norm='max'):
    def fitness(sim, measurement, full=False):
        logger.debug('sim type {}, exp type {}'.format(type(sim),type(measurement)))
        fitarray=np.zeros((len(species_list),len(sim.output)))
        fit_dict={}
        start_ms=start*1000 #convert from sec to msec
        for i,species in enumerate(species_list):
            fit_dict[species]={}
            for j,stim_set in enumerate(sim.output):
                if isinstance(measurement,xml.NeurordResult):
                    pop1=nrd_output.nrd_output_conc(stim_set,species)
                    stim_set.__exit__()
                    pop2 = nrd_output.nrd_output_conc(measurement.output[j],species)
                    diff = pop2 - pop1
                    max_mol=np.mean([np.max(pop1.values),np.max(pop2.values)])
                    logger.debug('sim:{} exp:{}'.format(os.path.basename(stim_set.file.filename),os.path.basename(measurement.output[j].file.filename)))
                else:  #measurement is experimental data, stored as CSV_conc_set
                    if norm=='percent':
                        wave1y,wave1x=nrd_output.nrd_output_percent(stim_set,species,start_ms)
                    else:
                        pop1=nrd_output.nrd_output_conc(stim_set,species)
                        wave1y=pop1.values[:,0]
                        wave1x=pop1.index
                    stim_set.__exit__()
                    pop2 = measurement.data[j].waves[species].wave
                    max_mol=np.mean([np.max(wave1y),np.max(pop2.y)])
                    # Note: np.interp(x1,x2,y2) returns values for y2 corresponding to x1 timepoints
                    #what if x1 is negative? - don't use relative time for data
                    pop1y=np.interp(pop2.x,wave1x,wave1y)
                    logger.debug('wave1y sim= {}, len= {}, max= {}'.format(measurement.data[j].injection,len(wave1y),os.path.basename(stim_set.file.filename)))
                    diff = pop2.y - pop1y
                diffnorm = diff if max_mol==0 else diff/max_mol
                fit_dict[species][stim_set.injection]=float((diffnorm**2).mean()**0.5)
                fitarray[i][j]=float((diffnorm**2).mean()**0.5)
        fitness=np.mean(fitarray)
        #print ('fitarray', fitarray)
        if full:
            return fit_dict
        else:
            return fitness
    return fitness

