import pytest
import json
from app import create_app
from app.config import TestingConfig
from app.database import db

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """CLI runner"""
    return app.test_cli_runner()

class TestHealth:
    """Health check tests"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json['status'] == 'healthy'
    
    def test_advisor_info(self, client):
        """Test advisor info endpoint"""
        response = client.get('/api/advisor')
        assert response.status_code == 200
        assert 'name' in response.json
        assert response.json['name'] == 'Automated Financial Advisor'


class TestAuthentication:
    """Authentication tests"""
    
    def test_register_user(self, client):
        """Test user registration"""
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123',
            'first_name': 'Test',
            'last_name': 'User'
        })
        assert response.status_code == 201
        assert 'user' in response.json
        assert 'tokens' in response.json
        assert response.json['user']['email'] == 'test@example.com'
    
    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        # First registration
        client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'username': 'testuser1',
            'password': 'password123'
        })
        
        # Second registration with same email
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'username': 'testuser2',
            'password': 'password123'
        })
        assert response.status_code == 400
        assert 'Email already registered' in response.json.get('error', '')
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post('/api/auth/register', json={
            'email': 'invalid-email',
            'username': 'testuser',
            'password': 'password123'
        })
        assert response.status_code == 400
    
    def test_register_short_password(self, client):
        """Test registration with short password"""
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'pass'
        })
        assert response.status_code == 400
    
    def test_login_success(self, client):
        """Test successful login"""
        # Register user
        client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Login
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert 'tokens' in response.json
        assert 'access_token' in response.json['tokens']
    
    def test_login_invalid_password(self, client):
        """Test login with invalid password"""
        # Register user
        client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Try login with wrong password
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent email"""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })
        assert response.status_code == 401
    
    def test_get_profile_authenticated(self, client):
        """Test getting profile as authenticated user"""
        # Register and login
        client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123',
            'first_name': 'Test'
        })
        
        login_response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        access_token = login_response.json['tokens']['access_token']
        
        # Get profile
        response = client.get(
            '/api/auth/profile',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert response.status_code == 200
        assert response.json['email'] == 'test@example.com'
    
    def test_get_profile_unauthenticated(self, client):
        """Test getting profile without authentication"""
        response = client.get('/api/auth/profile')
        assert response.status_code == 401

