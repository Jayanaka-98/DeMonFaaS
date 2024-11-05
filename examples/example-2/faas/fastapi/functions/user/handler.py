import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
os.chdir(os.path.join(os.path.dirname(__file__)))

from app.api import api

def handle(event, context):
    user = api.read_user()
    if 'body' not in user:
        return {"body":user}
    else:
        return user