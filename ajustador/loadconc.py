#loadconc.py - possibly these classes will be added to ajustador/loader.py when ready
# -*- coding:utf-8 -*-

from __future__ import print_function, division
import numpy as np
from ajustador import xml,nrd_fitness
import glob    
import os
import operator

msec_per_sec=1000
nM_per_uM=1000
nM_per_mM=1e6

class trace(object):
    def __init__(self, molname, x, y,stim_time):
        molname_parts=molname.split()
        self.molname=molname_parts[0]
        if len(molname_parts)>1:
            self.units=molname_parts[1]
            if len(molname_parts)>2:
                #strip out any trailing non-numeric characteris
                self.scale=int(''.join([c for c in molname_parts[2] if c.isdigit()]))
            else:
                self.scale=1
        else:
            self.units='nM'
            self.scale=1
        if self.units.startswith('m') or self.units.startswith('(m'):
            yvalue=y*nM_per_mM
        elif self.units.startswith('u') or self.units.startswith('(u'):
            yvalue=y*nM_per_uM
        else:
            #assume nM (or percent if fret)
            yvalue=y
        self.wave=np.rec.fromarrays((x, yvalue), names='x,y')
        #calculate features: baseline, peaktime, peak value
        start_index,basal=nrd_fitness.basal(x,yvalue,stim_time)
        pt,peak=nrd_fitness.peak(x,yvalue,start_index)
        self.features={'basal':basal, 'stim_pt': start_index,'peaktime':pt,'peakval': peak}

class CSV_conc(object):
    """Load a series of concentration measurements from a CSV file
    Each CSV file contains data for one or more molecules:
      Time time_units, mol_name1 (nM), [mol_name2]
      read time_units (sec,msec,min allowed) and convert to msec
    """
    def __init__(self, fname,rootname,stim_time,features=[]):
        import pandas as pd
        model_num=xml.modelname_to_param(fname,rootname)
        self.name=os.path.basename(fname)[0:os.path.basename(fname).rfind('.')]
        self.injection=model_num
        self.features=features
        
        csv = pd.read_csv(fname, index_col=0)
        x_head=csv.index.name.split()
        if len(x_head)>1:
            time_units=x_head[-1]
            if time_units.startswith('sec') or time_units.startswith('(sec'):
                time_factor=msec_per_sec
            elif time_units.startswith('min') or time_units.startswith('(min'):
                time_factor=msec_per_sec*60 #sec_per_min
            else:
                time_factor=1
            print('x column header: {}, time_units: {}, conversion factor: {}'.format(x_head,time_units,time_factor))
        else:
            time_factor=1
        x = csv.index.values*time_factor #time values
        #may want to read units of y value, e.g. allow uM or mM and convert to nM
        self.waves = {col.split()[0]:trace(col, x, csv[col].values,stim_time) for col in csv.columns}

class CSV_conc_set(object):
    #set of files, each one a CSV_conc object, differing in stim protocol
    def __init__(self,rootname,stim_time=0,features=[]):
        self.stim_time=stim_time*msec_per_sec
        self.features=features
        if os.path.isdir(rootname): #if directory, look for all csv files
            dirname = rootname
            filenames=glob.glob(rootname+'/*.csv')
            self.name=rootname
        else:
            if rootname.endswith('.csv'):
                #case with single filename specified
                filenames=[rootname]
            else:
                #case with a set of filenames specified, with common "prefix" + variable "suffix"
                filenames=glob.glob(rootname+'*.csv')
            dirname = os.path.dirname(rootname)
            self.name=os.path.basename(rootname)
        print('CSV_conc_set:',self.name, 'dir',dirname,'files',filenames,'stim_start (ms)', self.stim_time)
        if len(filenames)==0:
            print('**************** CSV_conc_set: NO FILES FOUND **************************')
        
        csv_list=[CSV_conc(fn,rootname,self.stim_time,features) for fn in filenames]
        csv_list.sort(key=operator.attrgetter('injection'))
        self.data=csv_list


