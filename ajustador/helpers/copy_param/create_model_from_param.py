# Use case 1:
#          How do I hand pick a single individual parameters out of optimization population
#          and can generate a param_cond.py, param_chan.py and morph file?

#STEP-1 : execute optimization.
#exec(open('/home/emily/mooseAssign/PlotkinCollab/Optimization/D1MatrixSample2opt_varyChans.py').read())

#STEP-2 : Save parameters from fit object of optimization to .npz file.
#from ajustador.helpers.save_params import save_params
#save_params(fit1,0,20)

# create_npz_param Input arguments in detail:
#Inputs => npz_file          -> *.npz file;
#             model             -> 'gp', 'd1d2', 'ep' or 'ca1' soon;
#             neuron_type       -> 'proto', 'D1' or 'D2' soon;
#             store_param_spath -> User intended path to store neuron parameter files;
#             fitnum            -> user desired fitnumber to extract from npz file;
#             cond_file         -> Pure file name no path prefixes, [NOTE-1] (if cond_file is None uses param_cond.py).
#             chan_file         -> Pure file name no path prefixes, [NOTE-1] (if chan_file is None uses param_chan.py).

# Assumptions and Limitations
#Note-1** Program searches for cond_file in model folder and conductance_save in-order.
#Note-2** *.p file in cond_file should be present in the same directory for proper execution.
#Note-3** Avoid scientifc notation (12E-3) in param_cond.py.

##### TAKES FOUR ARGUMENTS: model(d1d2), neurtype(D1), abs path to npz data, and name of new model (new moose_nerp file name)

import sys
import shutil, errno
import moose_nerp
import os
from ajustador.helpers.copy_param.create_npz_param import create_npz_param

def copy(src, dest):
    try:
        shutil.copytree(src, dest)
    except OSError as exc:
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dest)
        else: raise
        

def createNewModelFolder(model, neuron_type, npz_file, nameNeuron):
    ### creates new param files in moose_nerp/model/conductance_save, taking the ABSOLUTE PATH of npz file as input
    create_npz_param(npz_file, model, neuron_type, fitnum=1)

    ### copy new cond, chan, and morph files to new moose_nerp folder 
    path = moose_nerp.__path__[0]
    savedNewParams = path + "/" + model + "/conductance_save"
    newModelFolder = path + "/" + nameNeuron 
    copy(savedNewParams, newModelFolder)                                      

    ### rename the new cond, chan files to standard file names
    for filename in os.listdir(path + "/" + nameNeuron):
        if filename.find("param_chan") != -1:
            os.rename(newModelFolder + "/" + filename, newModelFolder + "/" + "param_chan.py")
        if filename.find("param_cond") != -1:
            os.rename(newModelFolder + "/" + filename, newModelFolder + "/" + "param_cond.py") 

    ### from model folder, copy everything that is .py, and does not start with param_chan or param_cond
    ### includes __main__.py, __init__.py, etc.
    for filename in os.listdir(path + "/" + model):    
        if filename.endswith(".py") and filename.find("param_chan") == -1 and filename.find("param_cond") == -1:
            shutil.copy(path + "/" + model + "/" + filename, newModelFolder)
            print(filename, "copied")
           
    ### EDIT THE MAIN so that it runs the new nameNeuron file
    mainfile = open(newModelFolder + "/__main__.py", "r")
    newmain = open(newModelFolder + "/__main__2.py", "w+") #creates new main

    lines = mainfile.readlines()
    for line in lines:
        if line.strip().endswith(" as model"):
            newmain.write("from moose_nerp import " + nameNeuron + " as model" + "\n")
        else:
            newmain.write(line)
    mainfile.close()
    newmain.close()

    os.remove(newModelFolder + "/__main__.py")           #deletes old main
    os.rename(newModelFolder + "/__main__2.py", newModelFolder + "/__main__.py")

    ### delete the conductance_save folder in moose_nerp/model
    shutil.rmtree(savedNewParams)

if __name__ == "__main__":
    model, neuron_type, npz_file, nameNeuron = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]    
    #d1d2, D1, /home/emily/fitd1d2-D1-D1_Matrix_Sample_2_real_morphtmp_8125.npz, D1MatrixSample2
    #"/home/emily/fitd1d2-D1-D1_Patch_Sample_2_post_injection_curve_tau_and_full_charging_curve_tmp_358.npz"
    createNewModelFolder(model, neuron_type, npz_file, nameNeuron)

        
    
        




















