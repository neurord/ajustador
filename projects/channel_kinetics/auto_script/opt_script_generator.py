import pandas as pd
import os

def get_settings_iterator(settings_csv_file):
    if settings_csv_file.endswith('csv'):
        try:
            return pd.read_csv(settings_csv_file).iterrows()
        except:
            ValueError("Not able to open: {}!!!".format(settings_csv_file))
    raise ValueError(" Not a valid csv optimizaion script settings file.: {}!!!".format(settings_csv_file))

def get_script_template(template_file):
    try:
      with open(template_file) as f1:
           return f1.read()
    except:
       raise ValueError("Not able to open: {}".format(template_file))


def generate_opt_scripts(opt_settings_csv, template_file):
    settings = get_settings_iterator(settings_csv_file)
    script_template = get_script_template(template_file)
    generated_scripts = []
    cwd = os.getcwd()

    for idx, item in settings.iterrows():
        ntype = item.ntype
        modeltype = item.modeltype
        generations = item.generations
        popsiz = item.popsiz
        morph_file = item.morph_file
        dataname = item.dataname
        rootdir = item.rootdir
        seed = item.seed
        trace_array = item.trace_array
        tmp_dir_prefix = item.tmp_dir_prefix
        optimization_parmas_finess_weights = item.optimization_parmas_finess_weights
        data_wave_module = item.data_wave_module
        datasection = item.datasection

        with open(optimization_parmas_finess_weights) as f1:
             aju_param_fitness = f1.read()

        script = script_template.format(ntype=ntype,
                           modeltype=modeltype,
                          generations = generations,
                          popsiz = popsiz,
                          morph_file = morph_file,
                          dataname = dataname,
                          rootdir = rootdir,
                          seed = seed,
                          trace_array = trace_array,
                          tmpdir = tmp_dir_prefix,
                          optimization_parmas_finess_weights = optimization_parmas_finess_weights,
                          exp_data = data_wave_module,
                          aju_params_fitness = aju_param_fitness,
                          datasection = datasection
                          )

        output_script_name = '_'.join(('opt',modeltype,ntype,dataname,'{}.py'.format(idx)))
        with open(output_script_name, 'w') as f1:
             f1.write(script)
        print('Genearted optimization script:', cwd + '/' + output_script_name)
        generated_scripts.append(cwd + '/' + output_script_name)
        
    return generated_scripts
