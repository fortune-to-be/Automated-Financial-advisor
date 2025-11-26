"""Additional backend tests and fixtures for DB-seeded tests"""

import pytest
from app import create_app
from app.database import db
from app.models import User, Account, Category, Transaction, Rule
from decimal import Decimal
from datetime import datetime, timezone, timedelta


@pytest.fixture(scope='function')
def test_app():
    """Create a Flask app configured for testing with an in-memory DB."""
    app = create_app()
    ctx = app.app_context()
    ctx.push()
    # Ensure fresh database
    db.drop_all()
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture(scope='function')
def client(test_app):
    return test_app.test_client()


@pytest.fixture(scope='function')
def seeded_db(test_app):
    """Seed the database with a user, account, category and some transactions."""
    user = User(email='seed@local', username='seed', password_hash='x')
    db.session.add(user)
    db.session.commit()

    acct = Account(user_id=user.id, name='Checking', account_type='checking', balance=1000)
    db.session.add(acct)
    cat = Category(name='Groceries', description='Grocery expenses')
    db.session.add(cat)
    db.session.commit()

    # Add a couple of transactions
    t1 = Transaction(user_id=user.id, account_id=acct.id, amount=Decimal('23.45'), type='expense', description="Trader Joe's", transaction_date=datetime.now(timezone.utc) - timedelta(days=10))
    t2 = Transaction(user_id=user.id, account_id=acct.id, amount=Decimal('150.00'), type='expense', description='Rent', transaction_date=datetime.now(timezone.utc) - timedelta(days=5))
    db.session.add_all([t1, t2])
    db.session.commit()

    # Add a rule that categorizes Trader Joe's
    rule = Rule(user_id=user.id, name='Grocery rule', condition={'operator': 'merchant_contains', 'value': 'trader'}, action={'type': 'set_category', 'category_id': cat.id}, priority=0, is_active=True)
    db.session.add(rule)
    db.session.commit()

    return {
        'user': user,
        'account': acct,
        'category': cat,
        'transactions': [t1, t2],
        'rule': rule,
    }


def test_seeded_transactions_present(seeded_db):
    # Ensure transactions were created
    txs = Transaction.query.all()
    assert len(txs) >= 2


def test_rule_application_using_service(seeded_db):
    # Import rule engine and apply rule to a transaction dict
    from app.services.rule_engine import RuleEngine

    engine = RuleEngine()
    tx = {
        'description': "Trader Joe's",
        'amount': Decimal('23.45'),
        'category_id': None
    }

    # Load rule from DB
    rule = seeded_db['rule']
    modified_tx, trace = engine.evaluate_transaction(tx, [
        {
            'id': rule.id,
            'name': rule.name,
            'condition': rule.condition,
            'action': rule.action,
            'is_active': rule.is_active,
            'priority': rule.priority,
        }
    ])

    assert modified_tx['category_id'] == seeded_db['category'].id
    assert len(trace) == 1
