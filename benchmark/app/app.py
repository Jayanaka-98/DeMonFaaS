from flask import Flask, Blueprint
from app.apis.quick import quick_api
from app.apis.compute import compute_api

# Create the Flask app
app = Flask(__name__)

# Define a route within app
@app.route('/')
def index():
    return 'Hello from app!'

# Register the blueprints with the app
app.register_blueprint(quick_api)
app.register_blueprint(compute_api)

if __name__ == '__main__':
    app.run()