# Use case 1:
          How do I hand pick a single individual parameters out of optimization population
          and can generate a param_cond.py, param_chan.py and morph file?

STEP-1 : execute optimization.
exec(open('squid_opt.py').read())

STEP-2 : Save parameters from fit object of optimization to .npz file.
from ajustador.helpers.save_params import save_params
save_params(fit1,0,20)

STEP-3 : Generate conductance parameters(param_cond.py ), channel kinetics(param_chan.py) and morph_file.
npz_file = "/home/Sriramsagar/neural_prj/outputs/squid_opt/squid_experimentaltau_z/Sriramsagarsquid-squid-squid_experimentaltau_z.npz"
from ajustador.helpers.copy_param.create_npz_param import create_npz_param
npz_file = "/home/Sriramsagar/neural_prj/outputs/squid_opt/squid_experimentaltau_z_ns/Sriramsagarsquid-squid-squid_experimentaltau_z_ns.npz"
model='squid'
neuron_type='squid'
create_npz_param(npz_file, model, neuron_type, fitnum=1) # Give a fitnumber of your choice.

# Varation
create_npz_param(npz_file, model, neuron_type) # process best fit out of .npz file.
