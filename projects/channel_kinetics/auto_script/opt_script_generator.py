import pandas as pd
settings = pd.read_csv('opt_script_settings.csv')

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

with open("template.py") as f1:
    script = f1.read()

with open(optimization_parmas_finess_weights) as f1:
    aju_param_fitness = f1.read()

script = script.format(ntype=ntype,
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

with open('exec_script.py', 'w') as f1:
    f1.write(script)
