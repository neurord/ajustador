from opt_script_generator import generate_opt_scripts
import multiprocessing as mp
import subprocess as sp
import sys
import os
import shutil

def peon(work_item):
    currentdir, backupdir, tmpdir, opt_script_path _python= work_item
    shutil.os.chdir(currentdir)
    setup(tmpdir, backupdir)
    sp.call([_python, opt_script_path])
    return 0

def setup(tmpdir, backupdir):
    try:
        create_backupdir(backupdir)
        shutil.copytree(tmpdir, backupdir)
    except:
         pass
    try:
        shutil.rmtree(tmpdir)
    except:
        pass

def create_backupdir(backupdir):
    try:
        shutil.os.mkdir(backupdir)
    except:
        pass

if __name__ == '__main__':
    template = sys.argv[1]      # template.py
    settings_csv = sys.argv[2]  # opt_settings.csv
    which_python = sys.argv[3]  # /usr/bin/python3
    current_dir = os.getcwd()
    tmp_backup_dir = '/tmp/backup'
    parallel_count = 2

    opt_script_paths = generate_opt_scripts(settings_csv, template)
    exec_inputs = [(current_dir, tmp_backup_dir, tempdir, script_path, which_python) for tempdir, script_path in opt_script_paths]
    with mp.Pool(processes = parallel_count) as pool:
        pool.map(peon, exec_inputs)

# python3 opt_executer.py template.py opt_script_settings.csv /usr/bin/python3
