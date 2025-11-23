from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token
from passlib.context import CryptContext
from app.database import db
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Authentication service"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(password, password_hash)
    
    @staticmethod
    def create_tokens(user_id: int, additional_claims=None):
        """Create access and refresh tokens"""
        claims = {'user_id': user_id}
        if additional_claims:
            claims.update(additional_claims)
        
        access_token = create_access_token(identity=user_id, additional_claims=claims)
        refresh_token = create_refresh_token(identity=user_id, additional_claims=claims)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600  # 1 hour
        }
    
    @staticmethod
    def register_user(email: str, username: str, password: str, first_name: str = None, last_name: str = None):
        """Register a new user"""
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            raise ValueError('Email already registered')
        
        if User.query.filter_by(username=username).first():
            raise ValueError('Username already taken')
        
        # Create new user
        user = User(
            email=email,
            username=username,
            password_hash=AuthService.hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role='user'
        )
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def authenticate_user(email: str, password: str):
        """Authenticate a user by email and password"""
        user = User.query.filter_by(email=email).first()
        
        if not user or not AuthService.verify_password(password, user.password_hash):
            raise ValueError('Invalid email or password')
        
        if not user.is_active:
            raise ValueError('User account is inactive')
        
        return user


class UserService:
    """User service"""
    
    @staticmethod
    def get_user_by_id(user_id: int):
        """Get user by ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_email(email: str):
        """Get user by email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_user_by_username(username: str):
        """Get user by username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def update_user(user_id: int, **kwargs):
        """Update user information"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('User not found')
        
        allowed_fields = ['first_name', 'last_name']
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(user, key, value)
        
        db.session.commit()
        return user
