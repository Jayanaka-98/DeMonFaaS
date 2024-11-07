from flask import Blueprint

quick_api = Blueprint('quick_api', __name__)

@quick_api.route('/test1')
def test1():
    return "Hello from the quick api!"