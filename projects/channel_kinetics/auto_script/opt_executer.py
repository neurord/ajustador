from opt_scrpt_generator import generate_opt_scripts
import sys
import os

def run_opt(tmpdir, opt_script_path):
    setup(tmpdir)
    pass

def setup(tmpdir):
    if os.path.exists(tmpdir):
        os.rmdir(tmpdir)

if __name__ == '__main__':
    template = sys.argv[1]
    settings_csv = sys.argv[2]
    opt_script_paths = generate_opt_scripts(template, settings_csv)
