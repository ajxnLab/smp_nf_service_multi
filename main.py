import sys
import os
import subprocess
from config.env_config import load_environment

# Add the root path BEFORE any local import
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from smp.smp_service import SMPService

def main():
    smpBot = SMPService()
    print("\nSTARTING SMP SERVICE")
    smpBot.run()

    script_dir = os.path.dirname(os.path.abspath(__file__))   # smp_service
    bat_file = os.path.join(script_dir, "nf_main", "run_nf_service_windows.bat")
    sh_file = os.path.join(script_dir, "nf_main", "run_nf_service_mac.sh")

    if sys.platform == 'win32':
        if os.path.exists(bat_file):
            print(f"Running {bat_file} ...")
            print("\nSTARTING NF SERVICE")
            subprocess.run(bat_file, shell=True, check=True, cwd=os.path.dirname(bat_file))
        else:
            print(f"Batch file not found: {bat_file}")
    elif sys.platform == 'darwin':
        if os.path.exists(sh_file):
            print(f"Running {sh_file} ...")
            print("STARTING NF SERVICE")
            subprocess.run(sh_file, shell=True, check=True, cwd=os.path.dirname(sh_file))
        else:
            print(f"Script file not found: {sh_file}")
    else:
        print(f"This script is running on an unsupported OS: {sys.platform}")

if __name__ == "__main__":
    load_environment()
    main()
