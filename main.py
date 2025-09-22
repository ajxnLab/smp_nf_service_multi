import sys
import locale

# Set UTF-8 as default encoding
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
locale.setlocale(locale.LC_ALL, '.UTF-8')

from utils.env_loader import load_environment
load_environment()

from nf_services.nf_service_manager import NFServiceManager
from smp.smp_service import SMPService
import os

def setup_environment():
    """Setup paths"""
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def main():
    setup_environment()
    smp_service = SMPService()
    smp_service.run()
    service = NFServiceManager()
    service.run()

if __name__ == "__main__":
    main()