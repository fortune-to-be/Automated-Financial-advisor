from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from marshmallow import ValidationError
from app.schemas import RegisterSchema, LoginSchema, RefreshTokenSchema, UserSchema, TokenResponseSchema
from app.services import AuthService, UserService
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    schema = RegisterSchema()
    
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    try:
        user = AuthService.register_user(
            email=data['email'],
            username=data['username'],
            password=data['password'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        
        tokens = AuthService.create_tokens(user.id)
        user_schema = UserSchema()
        
        return jsonify({
            'user': user_schema.dump(user),
            'tokens': tokens
        }), 201
    
    except ValueError as err:
        return jsonify({'error': str(err)}), 400
    except Exception as err:
        current_app.logger.error(f"Registration error: {str(err)}")
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user"""
    schema = LoginSchema()
    
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    try:
        user = AuthService.authenticate_user(
            email=data['email'],
            password=data['password']
        )
        
        tokens = AuthService.create_tokens(user.id)
        user_schema = UserSchema()
        
        return jsonify({
            'user': user_schema.dump(user),
            'tokens': tokens
        }), 200
    
    except ValueError as err:
        return jsonify({'error': str(err)}), 401
    except Exception as err:
        current_app.logger.error(f"Login error: {str(err)}")
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token"""
    schema = RefreshTokenSchema()
    
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    try:
        # Decode refresh token
        from flask_jwt_extended import decode_token
        refresh_token = data['refresh_token']
        decoded = decode_token(refresh_token, allow_expired=False)
        user_id = decoded.get('sub')
        
        # Create new tokens
        tokens = AuthService.create_tokens(user_id)
        
        return jsonify(tokens), 200
    
    except Exception as err:
        return jsonify({'error': 'Invalid refresh token'}), 401


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    user_id = get_jwt_identity()
    user = UserService.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    schema = UserSchema()
    return jsonify(schema.dump(user)), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        user = UserService.update_user(user_id, **data)
        schema = UserSchema()
        return jsonify(schema.dump(user)), 200
    except ValueError as err:
        return jsonify({'error': str(err)}), 400
    except Exception as err:
        current_app.logger.error(f"Profile update error: {str(err)}")
        return jsonify({'error': 'Failed to update profile'}), 500
