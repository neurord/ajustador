# Use case 1:
          How do I hand pick a single individual parameters out of optimization population
          and can generate a param_cond.py, param_chan.py and morph file?

STEP-1 : execute optimization.
exec(open('squid_opt.py').read())

STEP-2 : Save parameters from fit object of optimization to .npz file.
from ajustador.helpers.save_params import save_params
save_params(fit1,0,20)

STEP-3 : Generate conductance parameters(param_cond.py ), channel kinetics(param_chan.py) and morph_file.

from ajustador.helpers.copy_param.create_npz_param import create_npz_param
npz_file = "/abs_path_to_file/squid-squid_experimentaltau_z_ns.npz"
model='squid'
neuron_type='squid'
create_npz_param(npz_file, model, neuron_type, fitnum=1) # Give a fitnumber of your choice.

# Varation
create_npz_param(npz_file, model, neuron_type) # process best fit out of .npz file.

# Input arguments in detail:
Inputs => npz_file          -> *.npz file;
             model             -> 'gp', 'd1d2', 'ep' or 'ca1' soon;
             neuron_type       -> 'proto', 'D1' or 'D2' soon;
             store_param_spath -> User intended path to store neuron parameter files;
             fitnum            -> user desired fitnumber to extract from npz file;
             cond_file         -> Pure file name no path prefixes, [NOTE-1] (if cond_file is None uses param_cond.py).
             chan_file         -> Pure file name no path prefixes, [NOTE-1] (if chan_file is None uses param_chan.py).

# Assumptions and Limitations
Note-1** Program searches for cond_file in model folder and conductance_save in-order.
Note-2** *.p file in cond_file should be present in the same directory for proper execution.
Note-3** Avoid scientifc notation (12E-3) in param_cond.py.

create_model_from_param.py creates new moose_nerp model folder from optimization results.

