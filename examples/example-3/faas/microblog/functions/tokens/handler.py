import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
os.chdir(os.path.join(os.path.dirname(__file__)))

# from app.api.tokens import 
from app.api.auth import basic_auth, token_auth
from app import db

def handle(event, context):
    if event.method == "POST":
        return get_token()
    elif event.mthod == "DELETE":
        return revoke_token() 
    return 400
    
    


# @bp.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = basic_auth.current_user().get_token()
    db.session.commit()
    return {'token': token}


# @bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    token_auth.current_user().revoke_token()
    db.session.commit()
    return '', 204