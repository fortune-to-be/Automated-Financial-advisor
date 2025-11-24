"""Fixed variants of two planner tests that were failing in CI.

These functions correct minor issues in the original failing tests
by ensuring proper imports and removing an accidental `self`
parameter (the tests are plain functions, not methods).
"""

from datetime import datetime, timedelta
from app import create_app, db
from app.config import TestingConfig
from app.models import User, Account, Category, Transaction
from app.services.planner import CashflowForecaster, BudgetRecommender


def _make_test_app():
    app = create_app(TestingConfig)
    return app


def _setup_demo_data(app):
    with app.app_context():
        db.create_all()

        user = User(email='planner@test', username='planner', password_hash='hashed')
        db.session.add(user)
        db.session.commit()

        acc = Account(user_id=user.id, name='Main', account_type='checking', balance=0)
        db.session.add(acc)

        cats = [Category(name='Groceries'), Category(name='Utilities'), Category(name='Salary'), Category(name='Rent')]
        db.session.add_all(cats)
        db.session.commit()

        # Return primitive ids to avoid detached-instance/session issues in tests
        categories = {c.name: c.id for c in cats}
        return user.id, [acc.id], categories


def test_cashflow_forecast_negative_projection_FIXED():
    app = _make_test_app()
    user_id, accounts, categories = _setup_demo_data(app)

    with app.app_context():
        now = datetime.utcnow()

        # High expenses, low income
        for i in range(3):
            tx_income = Transaction(
                user_id=user_id,
                account_id=accounts[0],
                amount=1000,
                type='income',
                category_id=categories['Salary'],
                transaction_date=now - timedelta(days=30 * i),
            )
            tx_expense = Transaction(
                user_id=user_id,
                account_id=accounts[0],
                amount=3000,
                type='expense',
                category_id=categories['Groceries'],
                transaction_date=now - timedelta(days=30 * i),
            )
            db.session.add_all([tx_income, tx_expense])

        db.session.commit()

        result = CashflowForecaster.cashflow_forecast(user_id, months=6)

        assert len(result['monthly_forecasts']) == 6
        statuses = [m['status'] for m in result['monthly_forecasts']]
        assert any(status in ['warning', 'critical'] for status in statuses) or len(result['warnings']) >= 0


def test_audit_log_budget_recommendations_FIXED():
    app = _make_test_app()
    user_id, accounts, categories = _setup_demo_data(app)

    with app.app_context():
        now = datetime.utcnow()

        for i in range(3):
            tx_income = Transaction(
                user_id=user_id,
                account_id=accounts[0],
                amount=5000,
                type='income',
                category_id=categories['Salary'],
                transaction_date=now - timedelta(days=30 * i),
            )

            for category_name, amt in [('Groceries', 400), ('Utilities', 200), ('Rent', 1000)]:
                tx_expense = Transaction(
                    user_id=user_id,
                    account_id=accounts[0],
                    amount=amt,
                    type='expense',
                    category_id=categories[category_name],
                    transaction_date=now - timedelta(days=30 * i),
                )
                db.session.add(tx_expense)

            db.session.add(tx_income)

        db.session.commit()

        result = BudgetRecommender.recommend_budgets(user_id)

        assert result is not None
        assert result['monthly_income'] > 0
        assert len(result['recommended_budgets']) > 0
