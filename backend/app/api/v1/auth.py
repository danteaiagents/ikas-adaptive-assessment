from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, set_refresh_cookies, unset_jwt_cookies
from werkzeug.security import generate_password_hash, check_password_hash
from pydantic import ValidationError
from app.api.v1 import bp, api_response
from app.models.dtos import UserRegister, UserLogin
from app.repositories.user_repo import create_user, get_by_email, get_by_id

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = UserRegister(**request.json)
        if get_by_email(data.email):
            return api_response(False, error="Email already registered", status=400)
        
        user = create_user(
            email=data.email,
            username=data.username,
            password_hash=generate_password_hash(data.password),
            display_name=data.display_name or data.username
        )
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        resp, status = api_response(True, data={"access_token": access_token, "user_id": user.id}, status=201)
        set_refresh_cookies(resp, refresh_token)
        return resp, status
    except ValidationError as e:
        return api_response(False, error=e.errors(), status=400)

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = UserLogin(**request.json)
        user = get_by_email(data.email)
        if not user or not check_password_hash(user.password_hash, data.password):
            return api_response(False, error="Invalid credentials", status=401)
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        resp, status = api_response(True, data={"access_token": access_token, "user_id": user.id})
        set_refresh_cookies(resp, refresh_token)
        return resp, status
    except ValidationError as e:
        return api_response(False, error=e.errors(), status=400)

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return api_response(True, data={"access_token": access_token})

@bp.route('/logout', methods=['POST'])
def logout():
    resp, status = api_response(True, data="Logged out")
    unset_jwt_cookies(resp)
    return resp, status

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    current_user_id = get_jwt_identity()
    user = get_by_id(current_user_id)
    if not user:
        return api_response(False, error="User not found", status=404)
    return api_response(True, data={"id": user.id, "email": user.email, "username": user.username, "display_name": user.display_name})
