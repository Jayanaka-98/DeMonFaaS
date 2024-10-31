import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
os.chdir(os.path.join(os.path.dirname(__file__)))

from app.api import api
from fastapi import HTTPException

def handle(event, context):
    position = int(event.path.split("/")[1])
    question = api.read_questions(position)

    if not question:
        raise HTTPException(status_code=400, detail="Error")

    return question