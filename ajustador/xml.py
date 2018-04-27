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
    def __init__(self, name, value, *, min=None, max=None, fixed=False, xpath):
        super().__init__(name, value, min=min, max=max,
                         fixed=fixed,
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
            #print(param,elems,elems[0].text)
            print(param)
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
    def __init__(self, filename, features=[]):
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

        super().__init__(dirname, features)

        output=[nrd_output.Output(fname) for fname in filenames]
        output.sort(key=operator.attrgetter('injection'))
        self.output = np.array(output)
        #self.output=nrd_output.Output(filename)

def modelname_to_param(modelname,root_name):
    root_name_length=len(root_name)
    model_num=modelname[root_name_length:-4]
    return model_num
   
class NeurordSimulation(optimize.Simulation):
    def __init__(self, dir,
                 *,
                 model,
                 features=None,
                 params,
                 single=False,
                 async=True):

        super().__init__(dir,
                         params=params,
                         features=[])#features)  without '=[]' doesn't work.

        ####### Loop over each simulation in the set #######
        model_names=(glob.glob(model+"*.xml") if not model.endswith('.xml')
                     else [model])
        model_set=[]
        fout_set=[]
        param_set=[]
        for model_nm in model_names:
            model1= open_model(model_nm)
            model2 = update_model(model1, params) #xml with new parameters
            model_num=modelname_to_param(model_nm,model)
            param_set.append(model_num)
            logger.info('model _name, _num: {} {}'.format(model_nm, model_num))
            modelfile = self.tmpdir.name + '/model-'+str(model_num)+'.xml'  #name for xml with new parameters
            write_model(model2, modelfile)  #actually write the xml to the modelfile
            model_set.append(modelfile) #collect all model files into one array
            fout = (modelfile[:-4] + '.h5' if modelfile.endswith('.xml')
                    else modelfile + '.h5')
            fout_set.append(fout)
        #collect all the args into one tuple, similar to execute_for in optimize
        args=((mfile,fout,num) for mfile,fout,num in zip(model_set,fout_set,param_set))

        if async:
            func = optimize.exe_map(single=False, async=True)
            self._result = func(execute, args, callback=self._set_result)
        else:
            self._result = None
            result = optimize.exe_map(single=single, async=False)(execute, args)
            self._set_result(result)

    def _set_result(self, result):
        tag = os.path.join(self.tmpdir.name, '.complete')
        open(tag, 'w').close()
        
        output=[nrd_output.Output(result[i]) for i in range(len(result))]
        output.sort(key=operator.attrgetter('injection'))
        self.output=np.array(output,dtype=object)

    @classmethod
    def make(cls, *, dir, model, measurement, params):
        return cls(dir=dir, model=model, params=params)

def execute(p):
    modelfile, outfile, num = p

    cmdline = ['neurord', modelfile, outfile]
    print('+', ' '.join(shlex.quote(term) for term in cmdline), flush=True)
    subprocess.check_call(cmdline)

    return outfile
