from opt_scrpt_generator import generate_opt_scripts
import multiprocessing as mp
import subprocess as sp
import sys
import os
import shutil

def peon(work_item):
    currentdir, backupdir, tmpdir, opt_script_path = work_item
    shutil.os.chdir(currentdir)
    setup(tmpdir)
    sp.call(['python', opt_script_path])
    pass

def setup(tmpdir, backupdir):
    try:
        create_backupdir(backupdir)
        shutil.copytree(tmpdir, backupdir)
    except:
         pass
    shutil.rmdtree(tmpdir)
    shutil.os.mkdir(tmpdir)

def create_backupdir(backupdir):
    try:
        shutil.os.mkdir(backupdir)
    except:
        pass

if __name__ == '__main__':
    template = sys.argv[1]
    settings_csv = sys.argv[2]
    current_dir = os.getcwd()
    tmp_backup_dir = '/tmp/backup'
    parallel_count = 2

    opt_script_paths = generate_opt_scripts(template, settings_csv)
    exec_inputs = [(currentdir, tmp_backup_dir, tmdir, opt_script_path) for tempdir, script_path in opt_script_paths]
    with mp.Pool(processes = parallel_count) as pool:
        pool.map(peon, exec_inputs)
