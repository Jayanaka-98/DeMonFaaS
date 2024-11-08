from flask import Blueprint

data_api = Blueprint('data_api', __name__)

@data_api.route('/dataapi')
def test1():
    return "ehllo"