"""
Unit tests for Transaction Service and Routes

Tests for CRUD operations, CSV import/export, rule engine integration,
and comprehensive corner case coverage.
"""

import pytest
import csv
import io
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app import create_app, db
from app.models import User, Account, Category, Transaction, Rule, AuditLog
from app.services.transaction import TransactionService, TransactionImporter, TransactionError


@pytest.fixture
def app():
    """Create test application"""
    from app.config import TestingConfig
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create test user"""
    user = User(
        email='test@example.com',
        username='testuser',
        password_hash='hashed'
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_categories(app):
    """Create test categories"""
    categories = [
        Category(name='Groceries'),
        Category(name='Utilities'),
        Category(name='Salary'),
        Category(name='Entertainment'),
        Category(name='Rent'),
    ]
    db.session.add_all(categories)
    db.session.commit()
    return {cat.name: cat for cat in categories}


@pytest.fixture
def test_accounts(app, test_user):
    """Create test accounts"""
    accounts = [
        Account(user_id=test_user.id, name='Checking', account_type='checking', balance=5000),
        Account(user_id=test_user.id, name='Savings', account_type='savings', balance=10000),
    ]
    db.session.add_all(accounts)
    db.session.commit()
    return accounts


@pytest.fixture
def test_rules(app, test_user, test_categories):
    """Create test rules for auto-categorization"""
    grocery_rule = Rule(
        user_id=test_user.id,
        name='Auto-categorize groceries',
        description='Match grocery store transactions',
        condition={
            'operator': 'merchant_contains',
            'value': 'grocery'
        },
        action={
            'type': 'set_category',
            'category_id': test_categories['Groceries'].id
        },
        priority=10,
        is_active=True
    )
    
    utility_rule = Rule(
        user_id=test_user.id,
        name='Auto-categorize utilities',
        description='Match utility bill transactions',
        condition={
            'operator': 'merchant_contains',
            'value': 'power'
        },
        action={
            'type': 'set_category',
            'category_id': test_categories['Utilities'].id
        },
        priority=10,
        is_active=True
    )
    
    db.session.add_all([grocery_rule, utility_rule])
    db.session.commit()
    return [grocery_rule, utility_rule]


@pytest.fixture
def transaction_service(app):
    """Create transaction service instance"""
    return TransactionService()


@pytest.fixture
def transaction_importer(app):
    """Create transaction importer instance"""
    return TransactionImporter()


class TestTransactionService:
    """Test TransactionService CRUD operations"""
    
    def test_create_transaction_basic(self, app, test_user, test_accounts, transaction_service):
        """Test creating a basic transaction"""
        with app.app_context():
            tx_dict, applied_rules = transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('50.00'),
                type='expense',
                description='Groceries'
            )
            
            assert tx_dict['id'] is not None
            assert tx_dict['amount'] == 50.0
            assert tx_dict['type'] == 'expense'
            assert tx_dict['description'] == 'Groceries'
            assert 'rule_trace' in tx_dict
    
    def test_create_transaction_with_rule_match(self, app, test_user, test_accounts, test_rules, test_categories, transaction_service):
        """Test creating transaction that matches a rule"""
        with app.app_context():
            tx_dict, applied_rules = transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('75.50'),
                type='expense',
                description='At grocery store now'
            )
            
            assert tx_dict['category_id'] == test_categories['Groceries'].id
            assert len(applied_rules) > 0
            assert len(tx_dict['rule_trace']) > 0
            assert 'matched' in tx_dict['rule_trace'][0].lower()
    
    def test_create_transaction_with_tags(self, app, test_user, test_accounts, transaction_service):
        """Test creating transaction with tags"""
        with app.app_context():
            tx_dict, applied_rules = transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('100.00'),
                type='expense',
                description='Lunch',
                tags=['meal', 'casual']
            )
            
            assert 'meal' in tx_dict['tags']
            assert 'casual' in tx_dict['tags']
    
    def test_create_transaction_invalid_account(self, app, test_user, transaction_service):
        """Test creating transaction with invalid account"""
        with app.app_context():
            with pytest.raises(TransactionError):
                transaction_service.create_transaction(
                    user_id=test_user.id,
                    account_id=9999,
                    amount=Decimal('50.00'),
                    type='expense',
                    description='Test'
                )
    
    def test_update_transaction(self, app, test_user, test_accounts, test_categories, transaction_service):
        """Test updating a transaction"""
        with app.app_context():
            # Create transaction
            tx_dict, _ = transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('50.00'),
                type='expense',
                description='Original'
            )
            
            tx_id = tx_dict['id']
            
            # Update transaction
            updated_tx, _ = transaction_service.update_transaction(
                user_id=test_user.id,
                transaction_id=tx_id,
                description='Updated description',
                category_id=test_categories['Entertainment'].id
            )
            
            assert updated_tx['description'] == 'Updated description'
            assert updated_tx['category_id'] == test_categories['Entertainment'].id
    
    def test_update_transaction_triggers_reeval(self, app, test_user, test_accounts, test_rules, test_categories, transaction_service):
        """Test that updating transaction re-evaluates rules"""
        with app.app_context():
            # Create transaction that doesn't match
            tx_dict, _ = transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('50.00'),
                type='expense',
                description='Test'
            )
            
            tx_id = tx_dict['id']
            assert tx_dict['category_id'] is None
            
            # Update to match rule
            updated_tx, applied_rules = transaction_service.update_transaction(
                user_id=test_user.id,
                transaction_id=tx_id,
                description='At grocery store'
            )
            
            # Should now have category assigned by rule
            assert updated_tx['category_id'] == test_categories['Groceries'].id
            assert len(applied_rules) > 0
    
    def test_get_transactions_pagination(self, app, test_user, test_accounts, transaction_service):
        """Test pagination in get_transactions"""
        with app.app_context():
            # Create multiple transactions
            for i in range(25):
                transaction_service.create_transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=Decimal('10.00'),
                    type='expense',
                    description=f'Transaction {i}'
                )
            
            # Get first page
            result = transaction_service.get_transactions(
                user_id=test_user.id,
                page=1,
                per_page=10
            )
            
            assert len(result['data']) == 10
            assert result['total'] == 25
            assert result['pages'] == 3
            assert result['current_page'] == 1
    
    def test_get_transactions_date_filter(self, app, test_user, test_accounts, transaction_service):
        """Test date filtering in get_transactions"""
        with app.app_context():
            today = datetime.now(timezone.utc)
            
            # Create transaction today
            transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('10.00'),
                type='expense',
                description='Today',
                transaction_date=today
            )
            
            # Create transaction yesterday
            yesterday = today - timedelta(days=1)
            transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('20.00'),
                type='expense',
                description='Yesterday',
                transaction_date=yesterday
            )
            
            # Filter for today only
            result = transaction_service.get_transactions(
                user_id=test_user.id,
                start_date=today,
                end_date=today
            )
            
            assert len(result['data']) == 1
            assert result['data'][0]['description'] == 'Today'
    
    def test_get_transactions_category_filter(self, app, test_user, test_accounts, test_categories, transaction_service):
        """Test category filtering"""
        with app.app_context():
            # Create transactions in different categories
            transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('10.00'),
                type='expense',
                description='Food',
                category_id=test_categories['Groceries'].id
            )
            
            transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('50.00'),
                type='expense',
                description='Movie',
                category_id=test_categories['Entertainment'].id
            )
            
            # Filter by category
            result = transaction_service.get_transactions(
                user_id=test_user.id,
                category_id=test_categories['Groceries'].id
            )
            
            assert len(result['data']) == 1
            assert result['data'][0]['description'] == 'Food'
    
    def test_get_transaction_single(self, app, test_user, test_accounts, transaction_service):
        """Test retrieving single transaction"""
        with app.app_context():
            tx_dict, _ = transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('50.00'),
                type='expense',
                description='Test'
            )
            
            retrieved = transaction_service.get_transaction(
                user_id=test_user.id,
                transaction_id=tx_dict['id']
            )
            
            assert retrieved['id'] == tx_dict['id']
            assert retrieved['description'] == 'Test'
    
    def test_delete_transaction(self, app, test_user, test_accounts, transaction_service):
        """Test deleting a transaction"""
        with app.app_context():
            tx_dict, _ = transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('50.00'),
                type='expense',
                description='To delete'
            )
            
            tx_id = tx_dict['id']
            
            # Delete
            transaction_service.delete_transaction(test_user.id, tx_id)
            
            # Verify deletion
            with pytest.raises(TransactionError):
                transaction_service.get_transaction(test_user.id, tx_id)


class TestTransactionImporter:
    """Test TransactionImporter CSV functionality"""
    
    def _create_csv(self, rows):
        """Helper to create CSV content"""
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=['account_id', 'amount', 'type', 'description', 'transaction_date']
        )
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()
    
    def test_preview_csv_basic(self, app, test_user, test_accounts, transaction_importer):
        """Test basic CSV preview"""
        with app.app_context():
            rows = [
                {
                    'account_id': str(test_accounts[0].id),
                    'amount': '50.00',
                    'type': 'expense',
                    'description': 'Groceries',
                    'transaction_date': datetime.now(timezone.utc).isoformat()
                },
                {
                    'account_id': str(test_accounts[0].id),
                    'amount': '100.00',
                    'type': 'income',
                    'description': 'Salary',
                    'transaction_date': datetime.now(timezone.utc).isoformat()
                }
            ]
            
            csv_content = self._create_csv(rows)
            
            result = transaction_importer.preview_csv(
                user_id=test_user.id,
                csv_content=csv_content,
                max_rows=10
            )
            
            assert len(result['preview_rows']) == 2
            assert result['preview_rows'][0]['description'] == 'Groceries'
            assert result['preview_rows'][1]['description'] == 'Salary'
    
    def test_preview_csv_with_rules(self, app, test_user, test_accounts, test_rules, test_categories, transaction_importer):
        """Test CSV preview with rule matching"""
        with app.app_context():
            rows = [
                {
                    'account_id': str(test_accounts[0].id),
                    'amount': '50.00',
                    'type': 'expense',
                    'description': 'At grocery store today',
                    'transaction_date': datetime.now(timezone.utc).isoformat()
                }
            ]
            
            csv_content = self._create_csv(rows)
            
            result = transaction_importer.preview_csv(
                user_id=test_user.id,
                csv_content=csv_content
            )
            
            assert len(result['preview_rows']) == 1
            assert result['preview_rows'][0]['category_id'] == test_categories['Groceries'].id
            assert len(result['preview_rows'][0]['rule_trace']) > 0
    
    def test_preview_csv_invalid_account(self, app, test_user, transaction_importer):
        """Test CSV preview with invalid account"""
        with app.app_context():
            rows = [
                {
                    'account_id': '9999',
                    'amount': '50.00',
                    'type': 'expense',
                    'description': 'Test',
                    'transaction_date': datetime.now(timezone.utc).isoformat()
                }
            ]
            
            csv_content = self._create_csv(rows)
            
            result = transaction_importer.preview_csv(
                user_id=test_user.id,
                csv_content=csv_content
            )
            
            assert len(result['preview_rows']) == 0
            assert len(result['warnings']) > 0
    
    def test_preview_csv_invalid_type(self, app, test_user, test_accounts, transaction_importer):
        """Test CSV preview with invalid transaction type"""
        with app.app_context():
            rows = [
                {
                    'account_id': str(test_accounts[0].id),
                    'amount': '50.00',
                    'type': 'invalid',
                    'description': 'Test',
                    'transaction_date': datetime.now(timezone.utc).isoformat()
                }
            ]
            
            csv_content = self._create_csv(rows)
            
            result = transaction_importer.preview_csv(
                user_id=test_user.id,
                csv_content=csv_content
            )
            
            assert len(result['preview_rows']) == 0
            assert len(result['warnings']) > 0
    
    def test_commit_import_successful(self, app, test_user, test_accounts, transaction_importer):
        """Test successful CSV import commit"""
        with app.app_context():
            rows = [
                {
                    'account_id': str(test_accounts[0].id),
                    'amount': '50.00',
                    'type': 'expense',
                    'description': 'Groceries',
                    'transaction_date': datetime.now(timezone.utc).isoformat()
                },
                {
                    'account_id': str(test_accounts[0].id),
                    'amount': '100.00',
                    'type': 'income',
                    'description': 'Salary',
                    'transaction_date': datetime.now(timezone.utc).isoformat()
                }
            ]
            
            csv_content = self._create_csv(rows)
            
            result = transaction_importer.commit_import(
                user_id=test_user.id,
                csv_content=csv_content
            )
            
            assert result['created_count'] == 2
            assert result['total_errors'] == 0
    
    def test_commit_import_with_errors(self, app, test_user, test_accounts, transaction_importer):
        """Test CSV import with mixed valid/invalid rows"""
        with app.app_context():
            rows = [
                {
                    'account_id': str(test_accounts[0].id),
                    'amount': '50.00',
                    'type': 'expense',
                    'description': 'Valid',
                    'transaction_date': datetime.now(timezone.utc).isoformat()
                },
                {
                    'account_id': '9999',
                    'amount': '50.00',
                    'type': 'expense',
                    'description': 'Invalid account',
                    'transaction_date': datetime.now(timezone.utc).isoformat()
                }
            ]
            
            csv_content = self._create_csv(rows)
            
            result = transaction_importer.commit_import(
                user_id=test_user.id,
                csv_content=csv_content
            )
            
            assert result['created_count'] == 1
            assert result['total_errors'] == 1
    
    def test_commit_import_empty_csv(self, app, test_user, transaction_importer):
        """Test CSV import with empty file"""
        with app.app_context():
            with pytest.raises(TransactionError):
                transaction_importer.commit_import(
                    user_id=test_user.id,
                    csv_content=''
                )
    
    def test_commit_import_missing_fields(self, app, test_user, test_accounts, transaction_importer):
        """Test CSV import with missing required fields"""
        with app.app_context():
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['account_id', 'amount'])
            writer.writeheader()
            writer.writerow({'account_id': str(test_accounts[0].id), 'amount': '50.00'})
            csv_content = output.getvalue()
            
            with pytest.raises(TransactionError):
                transaction_importer.commit_import(
                    user_id=test_user.id,
                    csv_content=csv_content
                )


class TestTransactionAuditLog:
    """Test transaction audit logging"""
    
    def test_create_transaction_audit_log(self, app, test_user, test_accounts, transaction_service):
        """Test that creating transaction creates audit log"""
        with app.app_context():
            tx_dict, _ = transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('50.00'),
                type='expense',
                description='Test'
            )
            
            # Check audit log
            audit = AuditLog.query.filter_by(
                user_id=test_user.id,
                resource_type='transaction'
            ).first()
            
            assert audit is not None
            assert audit.action == 'create'
            assert audit.resource_id == tx_dict['id']
    
    def test_update_transaction_audit_log(self, app, test_user, test_accounts, transaction_service):
        """Test that updating transaction creates audit log"""
        with app.app_context():
            tx_dict, _ = transaction_service.create_transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=Decimal('50.00'),
                type='expense',
                description='Original'
            )
            
            tx_id = tx_dict['id']
            
            # Clear previous audit logs
            AuditLog.query.delete()
            
            # Update
            transaction_service.update_transaction(
                user_id=test_user.id,
                transaction_id=tx_id,
                description='Updated'
            )
            
            # Check audit log
            audit = AuditLog.query.filter_by(
                user_id=test_user.id,
                action='update'
            ).first()
            
            assert audit is not None
            assert audit.action == 'update'
            assert audit.old_values['description'] == 'Original'


class TestTransactionEndpoints:
    """Test transaction API endpoints"""
    
    def test_create_transaction_endpoint(self, app, test_user, test_accounts, client):
        """Test POST /api/transactions endpoint"""
        with app.app_context():
            # Get JWT token
            from app.services.auth import AuthService
            auth_service = AuthService()
            token = auth_service.generate_tokens(test_user.id)['access_token']
            
            response = client.post(
                '/api/transactions/',
                json={
                    'account_id': test_accounts[0].id,
                    'amount': '50.00',
                    'type': 'expense',
                    'description': 'Test transaction'
                },
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 201
            assert response.json['data']['amount'] == 50.0
    
    def test_list_transactions_endpoint(self, app, test_user, test_accounts, transaction_service, client):
        """Test GET /api/transactions endpoint"""
        with app.app_context():
            # Create some transactions
            for i in range(5):
                transaction_service.create_transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=Decimal('10.00'),
                    type='expense',
                    description=f'Transaction {i}'
                )
            
            from app.services.auth import AuthService
            auth_service = AuthService()
            token = auth_service.generate_tokens(test_user.id)['access_token']
            
            response = client.get(
                '/api/transactions/',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            assert response.status_code == 200
            assert len(response.json['data']) == 5

