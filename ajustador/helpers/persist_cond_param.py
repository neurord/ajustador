# TODO add descriptor and explain.

from ajustador.helpers.save_param.create_fit_param import create_fit_param
from ajustador.helpers.save_param.create_npz_param import create_npz_param

def persist_cond_param(object_type, model, neuron_type, **kwargs):
    if object_type == "fit":
        # TODO Add a fit object processing.
        pass
    elif object_type == "npz":
        npz_file = kwargs.get('npz_file') if kwargs.get('npz_file') else raise ValueError('npz_file needed!!!')
        create_npz_param(npz_file, model, neuron_type, store_param_path=kwargs.get('store_param_path'),
                             fitnum=kwargs.get('fitnum'), cond_file= kwargs.get('cond_file'))
    else:
        raise ValueError("Object_type must be 'fit' or 'npz' with valid parameters!")
