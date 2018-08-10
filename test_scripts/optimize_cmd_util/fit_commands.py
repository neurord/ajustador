import ajustador as aju
from ajustador.helpers import converge

def create_load_fit(dirname, tmpdirroot, exp_to_fit, modeltype, ntype, fitness, params):
    "Function to create and load optimization object"
    tmpdir= tmpdirroot+ modeltype+ '-'+ ntype+ '-'+ dirname
    fit = aju.optimize.Fit(tmpdir,
                        exp_to_fit,
                        modeltype, ntype,
                        fitness, params,
                        _make_simulation=aju.optimize.MooseSimulation.make,
                        _result_constructor=aju.optimize.MooseSimulationResult)
    fit.load()
    return fit

def test_coverage(fit, test_size, popsize):
    if test_size:
        mean_dict, std_dict, CV=converge.iterate_fit(fit,test_size, popsize)
        return fit, mean_dict, std_dict, CV
    return fit, None, None, None
