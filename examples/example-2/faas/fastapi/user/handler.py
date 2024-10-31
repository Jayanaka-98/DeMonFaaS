import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
os.chdir(sys.path)

from app.api import api

def handle(event, context):
    return api.read_user()