"""Optimization details specific to xml-based models

In particular, this should be suitable for NeuroRD.
"""

import copy
import re
import shlex
import subprocess
import os
from lxml import etree

from ajustador import nrd_output  
from . import optimize, loader


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
            if len(elems) != 1:
                raise ValueError('xpath matched {} elements'.format(len(elemes)))
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
        # model.h5 is used by default, but a .h5 file with different name can be specified
        if os.path.isdir(filename):
            dirname = filename
            filename = dirname + '/model.h5'
        else:
            dirname = os.path.dirname(filename)

        super().__init__(dirname, features)

        self.output = nrd_output.Output(filename)

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
                         features=features)

        model2 = update_model(model, params)
        modelfile = self.tmpdir.name + '/model.xml'
        write_model(model2, modelfile)

        fout = (modelfile[:-4] + '.h5' if modelfile.endswith('.xml')
                else modelfile + '.h5')

        args = ((modelfile, fout),)

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

        assert len(result) == 1
        self.output = nrd_output.Output(result[0])

    @classmethod
    def make(cls, *, dir, model, measurement, params):
        return cls(dir=dir, model=model, params=params)

def execute(p):
    modelfile, outfile = p

    cmdline = ['neurord', modelfile, outfile]
    print('+', ' '.join(shlex.quote(term) for term in cmdline), flush=True)
    subprocess.check_call(cmdline)

    return outfile
