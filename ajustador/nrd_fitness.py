from __future__ import print_function, division

import numpy as np
from pandas import core
from ajustador import nrd_output,xml
import os

import logging 
from ajustador.helpers.loggingsystem import getlogger 
logger = getlogger(__name__) 
logger.setLevel(logging.INFO)

AVOGADRO = 6.02214179
"""Avogadro constant from CODATA 2006"""
PUVC = AVOGADRO / 10
"""Converts concentrations to particle numbers"""
ms_to_sec=1000

''' to do: 
1. Turn this into class, which has attribute norm? and various features?  Then, can use that attribute in plot_neurord_tog to plot %
2. align experiments and simulations so that simulations can be shorter than experiments
c. use stim start in wave and sim to align data
d. align the simulation with experiment in fitness function based on filename param, not just sorted
'''
def summed_species(stim_set, species_set): #called for each species, send in the  (values of dictionary)
    for i,sp in enumerate(species_set):  #loop over the list
        pop1=nrd_output.nrd_output_conc(stim_set, sp)
        wave1x=pop1.index
        if i == 0:
            wave1y=pop1.values[:,0]
        else:
            wave1y+=pop1.values[:,0]
    return wave1y, wave1x

def nrd_output_percent(sim_output,specie_list,stim_time,scale=1,expbasal=1):
    #pop1=nrd_output.nrd_output_conc(sim_output,specie)
    wave1y, wave1x=summed_species(sim_output, specie_list) #summed_species takes a list of molecules
    start_index,wave1y_basal=basal(wave1x,wave1y,stim_time)
    if scale==1 and wave1y_basal != 0:
        wave1y=wave1y/wave1y_basal
    elif wave1y_basal > 0:
        wave1y=expbasal+(wave1y/wave1y_basal-1)/scale #specify expbasal=0 for FRET-FLIM
        #kluge just for FRET percent change optimization, because model peak to basal Epac1cAMP ratio ~4.0 (not 0.4 as in fret)
        #perhaps should add ability to parse and execute arbitrary equation.  Invert this for data in drawing.plot_neurord_tog
        #wave1y=1+(wave1y/wave1y_basal-1)/scale
    else:
        wave1y=wave1y #do not normalized if wave1y_basal is 0
    return wave1y,wave1x

def yvalues(y):
    if isinstance(y, np.ndarray):
        yval=y
    elif isinstance(y,core.frame.DataFrame):
        y=y.values 
    else:
        print('******* nrd_fitness.yvalues: unknown data type **********')
    return yval

def basal(x,y,stim_start):
    start_index=np.fabs(x-stim_start).argmin()
    if start_index==0:
        start_index=1  #use 1st point as basal if stimulation starts at t=0
    yval=yvalues(y)
    wave1y_basal=np.mean(yval[0:start_index])
    return start_index,wave1y_basal

def peak(x,y,start_index):
    yval=yvalues(y)
    peakpoint=yval[start_index:].argmax()+start_index
    peaktime=x[peakpoint]
    peak=np.mean(yval[peakpoint-1:peakpoint+2]) #3 point average
    return peaktime,peak
    
def specie_concentration_fitness(*, voxel=0, species_list, trial=0,start=None,norm='max'): #changed species_list to species_list, because species_list sent into summed_species
    def fitness(sim, measurement, full=False):
        logger.debug('sim type {}, exp type {}'.format(type(sim),type(measurement)))
        fitarray=np.zeros((len(species_list),len(sim.output)))
        fit_dict={}
        stim_start=sim.stim_time if start is None else start*ms_to_sec
        for i,(species,species_set) in enumerate(species_list.items()): #species_list = dict values, sent into summed_species
            fit_dict[species]={}
            for j,stim_set in enumerate(sim.output):
                if isinstance(measurement,xml.NeurordResult):
                    #pop1=nrd_output.nrd_output_conc(stim_set,species)
                    wave1y, wave1x= summed_species(stim_set, species_set)
                    stim_set.__exit__()
                    #pop2 = nrd_output.nrd_output_conc(measurement.output[j],species)
                    wave2y, wave2x= summed_species(measurement.output[j], species_set)
                    diff = wave2y - wave1y
                    max_mol=np.mean([np.max(wave1y),np.max(wave2y)])
                    logger.debug('sim:{} exp:{}'.format(os.path.basename(stim_set.file.filename),os.path.basename(measurement.output[j].file.filename)))
                else:  #measurement is experimental data, stored as CSV_conc_set
                    if measurement.data[j].waves[species].norm: #nrd_output_percent needs species_list, not species
                        wave1y,wave1x=nrd_output_percent(stim_set,species_set,stim_start,scale=measurement.data[j].waves[species].scale,
                                                         expbasal=measurement.data[j].waves[species].exp_basal)
                        stim_set.norm=norm
                    else:
                        #pop1=nrd_output.nrd_output_conc(stim_set,species)
                        wave1y, wave1x = summed_species(stim_set, species_set)
                    stim_set.__exit__()
                    pop2 = measurement.data[j].waves[species].wave
                    max_mol=np.mean([np.max(wave1y),np.max(pop2.y)]) 
                    # Note: np.interp(x1,x2,y2) returns values for y2 corresponding to x1 timepoints
                    #what if x1 is negative? - don't use relative time for data
                    pop1y=np.interp(pop2.x,wave1x,wave1y)
                    #print('wave1y sim= {}, len= {}, file= {}'.format(measurement.data[j].injection,len(wave1y),stim_set.file,'interpolated',pop1y,'nrd',pop2y)
                    logger.debug('wave1y sim= {}, len= {}, file= {}'.format(measurement.data[j].injection,len(wave1y),stim_set.file))
                    #os.path.basename(stim_set.file.filename doesn't work for some strange reason, maybe because file is <Closed HDF5 file>?
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

