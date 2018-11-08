import pandas as pd
import os
from collections import namedtuple

file_info_record = namedtule('file_info_record', "tempdir opt_script")

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
    generated_scripts = []
    for idx, item in settings.iterrows():
        tmpdir = '{tmpdir}'.format(item.tmp_dir_prefix)+modeltype+'-'+ntype+'-'+dirname
        generated_scripts.append(file_info_record(tmpdir, generate_opt_script(template_file, replacement_set)))
    return generated_scripts

def generate_opt_script(template_file, replacement_set):
    script_template = get_script_template(template_file)
    cwd = os.getcwd()

    with open(repacement_set.optimization_parmas_finess_weights) as f1:
         aju_param_fitness = f1.read()

    script = script_template.format(ntype=replacement_set.ntype,
                       modeltype=repacement_set.modeltype,
                      generations = repacement_set.generations,
                      popsiz = repacement_set.popsiz,
                      morph_file = repacement_set.morph_file,
                      dataname = repacement_set.dataname,
                      rootdir = repacement_set.rootdir,
                      seed = repacement_set.seed,
                      trace_array = repacement_set.trace_array,
                      tmpdir = repacement_set.tmp_dir_prefix,
                      optimization_parmas_finess_weights = repacement_set.optimization_parmas_finess_weights,
                      exp_data = repacement_set.data_wave_module,
                      aju_params_fitness = repacement_set.aju_param_fitness,
                      datasection = repacement_set.datasection
                      )

    output_script_name = '_'.join(('opt',modeltype,ntype,dataname,'{}.py'.format(idx)))

    with open(output_script_name, 'w') as f1:
         f1.write(script)

    print('Genearted optimization script:', cwd + '/' + output_script_name)

    return cwd + '/' + output_script_name
