import sys
import os

# Path project yang BENAR
project_home = '/home/lath1977/public_html/sispakapp'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Aktifkan virtualenv yang BENAR
activate_this = '/home/lath1977/public_html/sispakapp/venv/bin/activate_this.py'
with open(activate_this) as f:
    exec(f.read(), {'__file__': activate_this})

# Import Flask app
from app import app as application
