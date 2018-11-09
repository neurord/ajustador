from opt_script_generator import generate_opt_scripts
import multiprocessing as mp
import subprocess as sp
import sys
import os
import shutil

def peon(work_item):
    currentdir, backupdir, tmpdir, opt_script_path, _python = work_item
    shutil.os.chdir(currentdir)
    setup(tmpdir, backupdir)
    sp.call([_python, opt_script_path])
    return 0

def setup(tmpdir, backupdir):
    try:
        create_backupdir(backupdir)
        versioned_backup_path = create_backupdir_name(tmpdir, backupdir)
        shutil.copytree(tmpdir, versioned_backup_path)
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

def create_backupdir_name(tmpdir, backupdir):
    dirname = tmpdir.split('/')[-1]
    max_version = [0]
    version_dirs = [dir_ for dir_ in os.listdir(backupdir) if dirname in dir_]
    version = max(max_version + [int(dir_.split('#')[-1]) for dir_ in version_dirs if "#" in dir_])
    version = int(version) + 1
    new_bkp_path = os.path.join(backupdir,dirname+'#{}'.format(version))
    return new_bkp_path

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
