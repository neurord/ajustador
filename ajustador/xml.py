"""Optimization details specific to xml-based models

In particular, this should be suitable for NeuroRD.
"""

import copy
import re
import shlex
import subprocess
import os
from lxml import etree
import glob    
import numpy as np
import operator

from ajustador import nrd_output  
from . import optimize, loader

import logging 
from ajustador.helpers.loggingsystem import getlogger 
logger = getlogger(__name__) 
logger.setLevel(logging.INFO)

class XMLParamMechanism(optimize.ParamMechanism):
    def __init__(self, xpath):
        self.xpath = xpath

class XMLParam(optimize.AjuParam):
    def __init__(self, name, value, *, min=None, max=None, fixed=False, constant=None, xpath):
        super().__init__(name, value, min=min, max=max,
                         constant=constant, fixed=fixed,
                         mech=XMLParamMechanism(xpath))

def open_model(fname):
    tree =  etree.parse(fname)
    tree.xinclude()
    return tree

def do_replacements(model, paramset):
    for param in paramset.params:
        mech = param.mech
        if isinstance(mech, XMLParamMechanism):
            elems = model.xpath(mech.xpath)
            if len(elems) != 1:
                raise ValueError('xpath matched {} elements - wrong Reaction id specified {}'.format(len(elems), mech.xpath))
            #concentration (and surface density) sets have different format.
            #they have values and attrib, not text. May need to enhance this for region specific sets
            if elems[0].text==None:
                elems[0].attrib['value']=str(param.value)
                #print('do_replace: conc', elems[0].values())
            else:  #perhaps elif len(elems[0].text):
                if len(elems) != 1:
                    raise ValueError('xpath matched {} elements'.format(len(elems)))
                elems[0].text = str(param.value)
        else:
            raise ValueError('Unknown mechanism {}'.format(mech))

def update_model(model, paramset):
    # do_replacements() modifies the model in place, so let's make a copy first
    model = copy.deepcopy(model)
    do_replacements(model, paramset)
    return model

def write_model(model, fname):
    with open(fname, 'wb') as out:
        out.write(etree.tostring(model))

class NeurordResult(optimize.SimulationResult):
    def __init__(self, filename, features=[],stim_time=None):
        # model.h5 is used if only a directory is specified, but a .h5 file with different name can be specified

        print('NeurordResults', filename)
        if os.path.isdir(filename):
            dirname = filename
            filenames = [dirname + '/model.h5']
        else:
            #case with only a single filename specified
            dirname = os.path.dirname(filename)
            if filename.endswith('.h5'):
                filenames=[filename]
            else:
                #case with a set of filenames specified
                exp_set=os.path.basename(filename)
                filenames=glob.glob(filename+'*.h5')
                print('NeurordResult, exp_set',exp_set, ', files', filenames)

        super().__init__(dirname, features) #define some features here?  Such as norm, baseline, peak, peaktime?

        output=[nrd_output.Output(fname,stim_time) for fname in filenames]
        output.sort(key=operator.attrgetter('injection'))
        self.output = np.array(output)
        #self.output=nrd_output.Output(filename)

def modelname_to_param(modelname,root_name):
    root_name_length=len(root_name)
    dot_loc=str.rfind(modelname,'.')
    if dot_loc>root_name_length:
        model_num=modelname[root_name_length:dot_loc]
    else:
        model_num=0
    return model_num

def stim_onset(tree):
    xpath_onset='{http://stochdiff.textensor.org}InjectionStim/{http://stochdiff.textensor.org}onset'
    start_ms=np.inf
    root=tree.getroot()
    stimset=root.find('{http://stochdiff.textensor.org}StimulationSet')
    if stimset is not None:
        for onset_elem in stimset.findall(xpath_onset):
            onset_ms=float(onset_elem.text)
            start_ms=min(onset_ms,start_ms)
    else:
        start_ms=0    
    return start_ms

class NeurordSimulation(optimize.Simulation):
    def __init__(self, dir,
                 *,
                 model,
                 features=None,
                 params,
                 single=False,
                 do_async=True,
                 map_func=None):

        super().__init__(dir,
                         params=params,
                         features=[])
        ####### Loop over each simulation in the set #######
        model_names=(glob.glob(model+"*.xml") if not model.endswith('.xml')
                     else [model])
        print(model_names)
        model_set=[]
        fout_set=[]
        param_set=[]
        start=np.inf
        for model_nm in model_names:
            model1= open_model(model_nm)
            start=min(start,stim_onset(model1))
            model2 = update_model(model1, params) #xml with new parameters
            model_num=modelname_to_param(model_nm,model)
            param_set.append(model_num)
            logger.debug('model {}, num  {}'.format(model_nm, model_num))
            modelfile = self.tmpdir.name + '/model-'+str(model_num)+'.xml'  #name for xml with new parameters
            write_model(model2, modelfile)  #actually write the xml to the modelfile
            model_set.append(modelfile) #collect all model files into one array
            fout = (modelfile[:-4] + '.h5' if modelfile.endswith('.xml')
                    else modelfile + '.h5')
            fout_set.append(fout)
        self.stim_time=start #this assumes that each model file uses same stimulation onset
        self._attributes={'stim_time':self.stim_time}
        #collect all the args into one tuple, similar to execute_for in optimize
        args=((mfile,fout,num) for mfile,fout,num in zip(model_set,fout_set,param_set))

        if do_async:
            func = optimize.exe_map(single=False, do_async=True)
            self._result = func(execute, args, callback=self._set_result)
        else:
            self._result = None
            result = optimize.exe_map(single=single, do_async=False)(execute, args)
            self._set_result(result)

    def _set_result(self, result):
        tag = os.path.join(self.tmpdir.name, '.complete')
        open(tag, 'w').close()
        
        output=[nrd_output.Output(result[i],self.stim_time) for i in range(len(result))]
        output.sort(key=operator.attrgetter('injection'))
        self.output=np.array(output,dtype=object)

    @classmethod
    def make(cls, *, dir, model, measurement, params,map_func=None):
        return cls(dir=dir, model=model, params=params,map_func=None)

def execute(p):
    modelfile, outfile, num = p
    home_path = os.path.expanduser("~")
    neurord_path = os.path.join(home_path,
                                "neurord-3.3.0-all-deps.jar")

    cmdline = ['java', '-jar', neurord_path, modelfile, outfile]
    print('+', ' '.join(shlex.quote(term) for term in cmdline), flush=True)
    subprocess.check_call(cmdline)

    return outfile
