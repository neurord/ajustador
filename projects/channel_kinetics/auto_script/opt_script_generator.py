import pandas as pd
import os
from collections import namedtuple

file_info_record = namedtuple('file_info_record', "tempdir opt_script")

def get_settings_iterator(settings_csv_file):
    if settings_csv_file.endswith('.csv'):
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
    settings = get_settings_iterator(opt_settings_csv)
    generated_scripts = []
    for idx, item in settings:
        tmpdir = '{}'.format(item.tmp_dir_prefix)+item.modeltype+'-'+item.ntype+'-'+item.dataname+str(item.seed)
        generated_scripts.append(file_info_record(tmpdir, generate_opt_script(template_file, item)))
    return generated_scripts

def generate_opt_script(template_file, replacement_set):
    script_template = get_script_template(template_file)
    cwd = os.getcwd()

    with open(replacement_set.optimization_parmas_finess_weights) as f1:
         aju_param_fitness = f1.read()

    script = script_template.format(ntype=replacement_set.ntype,
                       modeltype=replacement_set.modeltype,
                      generations = replacement_set.generations,
                      popsiz = replacement_set.popsiz,
                      morph_file = replacement_set.morph_file,
                      dataname = replacement_set.dataname,
                      rootdir = replacement_set.rootdir,
                      seed = replacement_set.seed,
                      trace_array = replacement_set.trace_array,
                      tmpdir = replacement_set.tmp_dir_prefix,
                      aju_params_fitness = aju_param_fitness,
                      exp_data = replacement_set.data_wave_module,
                      datasection = replacement_set.datasection
                      )

    output_script_name = '_'.join(('opt',replacement_set.modeltype,replacement_set.ntype,replacement_set.dataname,'.py'))

    with open(output_script_name, 'w') as f1:
         f1.write(script)

    print('Genearted optimization script:', cwd + '/' + output_script_name)

    return cwd + '/' + output_script_name
