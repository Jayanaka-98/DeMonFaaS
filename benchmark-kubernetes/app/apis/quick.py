from flask import Blueprint

quick_api = Blueprint('quick_api', __name__)

@quick_api.route('/quickapi/test1')
def test1():
    return "Hello from the quick api!"

@quick_api.route(f'/quickapi/<id>/test2')
def test2(id):
    return f"Request took in id {id}"