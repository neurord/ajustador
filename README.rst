Docs
~~~~

https://neurord.github.io/ajustador/

Code
~~~~

https://github.com/neurord/ajustador/


Setting up Optimizations on the Neuroscience Gate (NSG)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- create directory with main optimization scripts, such as my_NSGopt_dir
   - example is gpNpas_opt.py, in https://github.com/neurord/optimization_scripts/blob/master/gp_opt/, which 
   
     + specifies model type (moose_nerp package)
     + specifies neuron type
     + specifies data name (i.e., which experimental trace)
     + specifies optimization parameters, such as generations and population size
     + creates and moves to output directory according to some naming convention, e.g.
       ::
         rootdir=os.getcwd()+'/output'
         dirname='cmaes_'+dataname+'_'+str(seed)+'_'+str(popsiz)
         if not in dirname in os.listdir(rootdir):
            os.mkdir(rootdir+dirname)
         os.chdir(rootdir+dirname)
   -  fit_commands.py
   -  param_fitness_chan.py, which specifies
      - which parameters to change, and their ranges
      - the fitness function, and weights on fitness features
- create empty /output subdirectory
- copy (or link)
  - moose_nerp/moose_nerp
  - dill module
  - adjustador/ajustador
    - make sure __init__ in ajustador does not import xml.py, loadconc.py, nrd_fitness.py, drawing.py, nrd_output.py
    - make sure ajustador/helpers/save_params.py does not import xml
- copy (or link) the data directory, and python file that specifies the data as class Params, e.g. from waves:
  - https://github.com/neurord/waves/blob/master/gpedata_experimental.py
  - https://github.com/neurord/waves/tree/master/gpedata-experimental

- create a zip file from the directory _above_ the directory you just created 
  ::
    zip -r NSGopt.zip my_NSGopt_dir/
