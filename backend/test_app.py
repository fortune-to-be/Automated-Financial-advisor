import pytest
import json
from app import create_app
from app.config import TestingConfig
from app.database import db
from app.models import User, Category

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

@pytest.fixture
def admin_user(client):
    """Create admin user for testing"""
    response = client.post('/api/auth/register', json={
        'email': 'admin@test.com',
        'username': 'admin_user',
        'password': 'password123'
    })
    
    user_id = response.json['user']['id']
    
    # Promote to admin
    with client.application.app_context():
        user = User.query.get(user_id)
        user.role = 'admin'
        db.session.commit()
    
    return response.json['tokens']['access_token']

@pytest.fixture
def normal_user(client):
    """Create normal user for testing"""
    response = client.post('/api/auth/register', json={
        'email': 'user@test.com',
        'username': 'normal_user',
        'password': 'password123'
    })
    
    return response.json['tokens']['access_token']

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


class TestAdminRules:
    """Admin rule management tests"""
    
    def test_list_rules_admin(self, client, admin_user):
        """Test listing rules as admin"""
        response = client.get(
            '/api/admin/rules',
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        assert response.status_code == 200
        assert 'data' in response.json
    
    def test_list_rules_non_admin(self, client, normal_user):
        """Test listing rules as non-admin"""
        response = client.get(
            '/api/admin/rules',
            headers={'Authorization': f'Bearer {normal_user}'}
        )
        assert response.status_code == 403
    
    def test_create_rule_admin(self, client, admin_user):
        """Test creating a rule as admin"""
        rule_data = {
            'name': 'Test Rule',
            'description': 'Test description',
            'condition': {
                'operator': 'merchant_contains',
                'value': 'grocery'
            },
            'action': {
                'type': 'set_category',
                'category_id': 1
            },
            'priority': 5,
            'is_active': True
        }
        
        response = client.post(
            '/api/admin/rules',
            json=rule_data,
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        assert response.status_code == 201
        assert response.json['name'] == 'Test Rule'
        assert response.json['priority'] == 5
    
    def test_create_rule_invalid_condition(self, client, admin_user):
        """Test creating rule with invalid condition"""
        rule_data = {
            'name': 'Invalid Rule',
            'condition': {
                'operator': 'unknown_operator',
                'value': 'test'
            },
            'action': {
                'type': 'set_category',
                'category_id': 1
            }
        }
        
        response = client.post(
            '/api/admin/rules',
            json=rule_data,
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        assert response.status_code == 400
        assert 'Unknown operator' in response.json.get('error', '')
    
    def test_create_rule_non_admin(self, client, normal_user):
        """Test creating rule as non-admin"""
        rule_data = {
            'name': 'Test Rule',
            'condition': {'operator': 'amount_gt', 'value': 100},
            'action': {'type': 'set_category', 'category_id': 1}
        }
        
        response = client.post(
            '/api/admin/rules',
            json=rule_data,
            headers={'Authorization': f'Bearer {normal_user}'}
        )
        assert response.status_code == 403
    
    def test_validate_rule(self, client, admin_user):
        """Test rule validation endpoint"""
        rule_data = {
            'name': 'Grocery Rule',
            'condition': {
                'operator': 'merchant_contains',
                'value': 'grocery'
            },
            'action': {
                'type': 'set_category',
                'category_id': 1
            }
        }
        
        response = client.post(
            '/api/admin/rules/validate',
            json=rule_data,
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        assert response.status_code == 200
        assert response.json['valid'] is True
    
    def test_validate_rule_invalid_regex(self, client, admin_user):
        """Test validation with invalid regex"""
        rule_data = {
            'name': 'Bad Regex Rule',
            'condition': {
                'operator': 'merchant_regex',
                'value': '[invalid('
            },
            'action': {
                'type': 'set_category',
                'category_id': 1
            }
        }
        
        response = client.post(
            '/api/admin/rules/validate',
            json=rule_data,
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        assert response.status_code == 400
        assert response.json['valid'] is False
    
    def test_update_rule(self, client, admin_user):
        """Test updating a rule"""
        # Create rule first
        rule_data = {
            'name': 'Original Rule',
            'condition': {
                'operator': 'merchant_contains',
                'value': 'grocery'
            },
            'action': {
                'type': 'set_category',
                'category_id': 1
            },
            'priority': 0
        }
        
        create_response = client.post(
            '/api/admin/rules',
            json=rule_data,
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        rule_id = create_response.json['id']
        
        # Update rule
        update_data = {
            'name': 'Updated Rule',
            'priority': 10
        }
        
        response = client.put(
            f'/api/admin/rules/{rule_id}',
            json=update_data,
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        assert response.status_code == 200
        assert response.json['name'] == 'Updated Rule'
        assert response.json['priority'] == 10
    
    def test_delete_rule(self, client, admin_user):
        """Test deleting a rule"""
        # Create rule first
        rule_data = {
            'name': 'Rule to Delete',
            'condition': {
                'operator': 'amount_gt',
                'value': 100
            },
            'action': {
                'type': 'set_tags',
                'tags': ['large_expense']
            }
        }
        
        create_response = client.post(
            '/api/admin/rules',
            json=rule_data,
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        rule_id = create_response.json['id']
        
        # Delete rule
        response = client.delete(
            f'/api/admin/rules/{rule_id}',
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get(
            f'/api/admin/rules/{rule_id}',
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        assert get_response.status_code == 404
    
    def test_toggle_rule_active(self, client, admin_user):
        """Test toggling rule active status"""
        # Create rule
        rule_data = {
            'name': 'Toggle Rule',
            'condition': {'operator': 'amount_gt', 'value': 50},
            'action': {'type': 'set_tags', 'tags': ['test']},
            'is_active': True
        }
        
        create_response = client.post(
            '/api/admin/rules',
            json=rule_data,
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        rule_id = create_response.json['id']
        
        # Toggle
        response = client.post(
            f'/api/admin/rules/{rule_id}/toggle',
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        assert response.status_code == 200
        assert response.json['is_active'] is False
        
        # Toggle again
        response = client.post(
            f'/api/admin/rules/{rule_id}/toggle',
            headers={'Authorization': f'Bearer {admin_user}'}
        )
        assert response.json['is_active'] is True

