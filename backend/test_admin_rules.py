"""Admin rule management endpoint tests"""
import pytest
from app import create_app
from app.config import TestingConfig
from app.database import db
from app.models import User, Rule
from app.services import AuthService
from datetime import datetime


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
def admin_token(client, app):
    """Create admin user and get access token"""
    with app.app_context():
        # Use simple hash for testing to avoid bcrypt issues
        admin = User(
            email='admin@test.com',
            username='admin_user',
            password_hash='$2b$12$test_hash_here_admin_token_safely',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        
        # Create token manually using JWT
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=admin.id)
        return token


@pytest.fixture
def user_token(client, app):
    """Create regular user and get access token"""
    with app.app_context():
        # Use simple hash for testing to avoid bcrypt issues
        user = User(
            email='user@test.com',
            username='normal_user',
            password_hash='$2b$12$test_hash_here_user_token_safely_123',
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=user.id)
        return token


class TestAdminRulesList:
    """Test rule listing endpoint"""
    
    def test_list_rules_admin(self, client, admin_token):
        """Test listing rules as admin"""
        response = client.get(
            '/api/admin/rules',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        assert 'data' in response.json
        assert 'total' in response.json
    
    def test_list_rules_non_admin(self, client, user_token):
        """Test listing rules as non-admin returns 403"""
        response = client.get(
            '/api/admin/rules',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 403
    
    def test_list_rules_unauthenticated(self, client):
        """Test listing rules without authentication"""
        response = client.get('/api/admin/rules')
        assert response.status_code == 401


class TestAdminRulesCreate:
    """Test rule creation endpoint"""
    
    def test_create_rule_admin(self, client, admin_token):
        """Test creating a rule as admin"""
        rule_data = {
            'name': 'Grocery Rule',
            'description': 'Categorize grocery transactions',
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
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 201
        assert response.json['name'] == 'Grocery Rule'
        assert response.json['priority'] == 5
        assert response.json['is_active'] is True
    
    def test_create_rule_minimal(self, client, admin_token):
        """Test creating a rule with minimal data"""
        rule_data = {
            'name': 'Minimal Rule',
            'condition': {
                'operator': 'amount_gt',
                'value': 100
            },
            'action': {
                'type': 'set_tags',
                'tags': ['large']
            }
        }
        
        response = client.post(
            '/api/admin/rules',
            json=rule_data,
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 201
        assert response.json['name'] == 'Minimal Rule'
        assert response.json['priority'] == 0  # default
        assert response.json['is_active'] is True  # default
    
    def test_create_rule_invalid_condition_operator(self, client, admin_token):
        """Test creating rule with invalid condition operator"""
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
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_create_rule_invalid_regex(self, client, admin_token):
        """Test creating rule with invalid regex pattern"""
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
            '/api/admin/rules',
            json=rule_data,
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 400
        assert 'regex' in response.json.get('error', '').lower()
    
    def test_create_rule_non_admin(self, client, user_token):
        """Test creating rule as non-admin returns 403"""
        rule_data = {
            'name': 'Test Rule',
            'condition': {'operator': 'amount_gt', 'value': 100},
            'action': {'type': 'set_category', 'category_id': 1}
        }
        
        response = client.post(
            '/api/admin/rules',
            json=rule_data,
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 403


class TestAdminRulesGet:
    """Test get single rule endpoint"""
    
    def test_get_rule(self, client, admin_token, app):
        """Test getting a single rule"""
        # Create a rule first
        with app.app_context():
            # Get admin user
            admin = User.query.filter_by(email='admin@test.com').first()
            rule = Rule(
                user_id=admin.id,
                name='Test Rule',
                condition={'operator': 'amount_gt', 'value': 50},
                action={'type': 'set_tags', 'tags': ['test']},
                priority=1
            )
            db.session.add(rule)
            db.session.commit()
            rule_id = rule.id
        
        response = client.get(
            f'/api/admin/rules/{rule_id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        assert response.json['name'] == 'Test Rule'
        assert response.json['priority'] == 1
    
    def test_get_nonexistent_rule(self, client, admin_token):
        """Test getting a non-existent rule"""
        response = client.get(
            '/api/admin/rules/99999',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 404


class TestAdminRulesUpdate:
    """Test rule update endpoint"""
    
    def test_update_rule(self, client, admin_token, app):
        """Test updating a rule"""
        # Create rule first
        with app.app_context():
            admin = User.query.filter_by(email='admin@test.com').first()
            rule = Rule(
                user_id=admin.id,
                name='Original Name',
                condition={'operator': 'merchant_contains', 'value': 'store'},
                action={'type': 'set_category', 'category_id': 1},
                priority=0
            )
            db.session.add(rule)
            db.session.commit()
            rule_id = rule.id
        
        # Update rule
        update_data = {
            'name': 'Updated Name',
            'priority': 10
        }
        
        response = client.put(
            f'/api/admin/rules/{rule_id}',
            json=update_data,
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        assert response.json['name'] == 'Updated Name'
        assert response.json['priority'] == 10
    
    def test_update_rule_full(self, client, admin_token, app):
        """Test updating all rule fields"""
        with app.app_context():
            admin = User.query.filter_by(email='admin@test.com').first()
            rule = Rule(
                user_id=admin.id,
                name='Original',
                condition={'operator': 'amount_gt', 'value': 100},
                action={'type': 'set_tags', 'tags': ['old']},
                priority=0,
                is_active=True
            )
            db.session.add(rule)
            db.session.commit()
            rule_id = rule.id
        
        update_data = {
            'name': 'Fully Updated',
            'description': 'New description',
            'condition': {'operator': 'amount_gte', 'value': 200},
            'action': {'type': 'set_tags', 'tags': ['new']},
            'priority': 5,
            'is_active': False
        }
        
        response = client.put(
            f'/api/admin/rules/{rule_id}',
            json=update_data,
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        assert response.json['name'] == 'Fully Updated'
        assert response.json['is_active'] is False
        assert response.json['priority'] == 5


class TestAdminRulesDelete:
    """Test rule deletion endpoint"""
    
    def test_delete_rule(self, client, admin_token, app):
        """Test deleting a rule"""
        # Create rule first
        with app.app_context():
            admin = User.query.filter_by(email='admin@test.com').first()
            rule = Rule(
                user_id=admin.id,
                name='Rule to Delete',
                condition={'operator': 'amount_gt', 'value': 50},
                action={'type': 'set_tags', 'tags': ['delete']},
                priority=0
            )
            db.session.add(rule)
            db.session.commit()
            rule_id = rule.id
        
        # Delete rule
        response = client.delete(
            f'/api/admin/rules/{rule_id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get(
            f'/api/admin/rules/{rule_id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_rule(self, client, admin_token):
        """Test deleting a non-existent rule"""
        response = client.delete(
            '/api/admin/rules/99999',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 404


class TestAdminRulesToggle:
    """Test rule toggle endpoint"""
    
    def test_toggle_rule_active(self, client, admin_token, app):
        """Test toggling rule active status"""
        # Create rule
        with app.app_context():
            admin = User.query.filter_by(email='admin@test.com').first()
            rule = Rule(
                user_id=admin.id,
                name='Toggle Rule',
                condition={'operator': 'amount_gt', 'value': 50},
                action={'type': 'set_tags', 'tags': ['test']},
                is_active=True
            )
            db.session.add(rule)
            db.session.commit()
            rule_id = rule.id
        
        # Toggle to inactive
        response = client.post(
            f'/api/admin/rules/{rule_id}/toggle',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        assert response.json['is_active'] is False
        
        # Toggle back to active
        response = client.post(
            f'/api/admin/rules/{rule_id}/toggle',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        assert response.json['is_active'] is True


class TestAdminRulesValidate:
    """Test rule validation endpoint"""
    
    def test_validate_valid_rule(self, client, admin_token):
        """Test validating a valid rule"""
        rule_data = {
            'name': 'Valid Rule',
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
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        assert response.json['valid'] is True
    
    def test_validate_invalid_regex(self, client, admin_token):
        """Test validation with invalid regex"""
        rule_data = {
            'name': 'Bad Regex',
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
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 400
        assert response.json['valid'] is False
    
    def test_validate_with_sample_transaction(self, client, admin_token):
        """Test validation with sample transaction"""
        rule_data = {
            'name': 'Amount Rule',
            'condition': {
                'operator': 'amount_gt',
                'value': 50
            },
            'action': {
                'type': 'set_tags',
                'tags': ['large']
            }
        }
        
        response = client.post(
            '/api/admin/rules/validate',
            json=rule_data,
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        assert response.json['valid'] is True
        assert 'sample_transaction' in response.json or 'message' in response.json
