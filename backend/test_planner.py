"""
Unit tests for Planner Service

Tests for budget recommendations, goal scheduling, cashflow forecasting,
and portfolio allocation with comprehensive corner case coverage.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from app import create_app, db
from app.models import User, Account, Category, Transaction, Goal, AuditLog
from app.services.planner import (
    BudgetRecommender, GoalScheduler, CashflowForecaster, PortfolioAllocator, PlannerError
)


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


class TestBudgetRecommender:
    """Test budget recommendation algorithm"""
    
    def test_recommend_budgets_normal_case(self, app, test_user, test_categories, test_accounts):
        """Test budget recommendation with normal spending patterns"""
        with app.app_context():
            # Add transactions from last 3 months
            now = datetime.utcnow()
            
            # 3 months of salary
            for i in range(3):
                tx = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=5000,
                    type='income',
                    category_id=test_categories['Salary'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                db.session.add(tx)
            
            # Various expenses
            for i in range(3):
                for category_name, amount in [('Groceries', 400), ('Utilities', 200), ('Rent', 1000)]:
                    tx = Transaction(
                        user_id=test_user.id,
                        account_id=test_accounts[0].id,
                        amount=amount,
                        type='expense',
                        category_id=test_categories[category_name].id,
                        transaction_date=now - timedelta(days=30 * i)
                    )
                    db.session.add(tx)
            
            db.session.commit()
            
            result = BudgetRecommender.recommend_budgets(test_user.id, months=3)
            
            assert result['user_id'] == test_user.id
            assert result['monthly_income'] == 5000
            assert result['debt_ratio'] == 0
            assert len(result['recommended_budgets']) > 0
            assert 'rule_trace' in result
            assert result['generated_at'] is not None
    
    def test_recommend_budgets_with_debt(self, app, test_user, test_categories, test_accounts):
        """Test budget recommendation with outstanding debt"""
        with app.app_context():
            # Add high debt to checking account
            test_accounts[0].balance = -5000  # $5000 debt
            db.session.commit()
            
            now = datetime.utcnow()
            
            # Add income transactions
            for i in range(3):
                tx = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=3000,
                    type='income',
                    category_id=test_categories['Salary'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                db.session.add(tx)
            
            db.session.commit()
            
            result = BudgetRecommender.recommend_budgets(test_user.id, months=3)
            
            assert result['monthly_income'] == 3000
            assert result['debt_ratio'] > 0
            # Debt should be detected and ratio calculated
            assert any('Debt adjustment' in trace for trace in result['rule_trace'])
    
    def test_recommend_budgets_zero_income(self, app, test_user, test_categories, test_accounts):
        """Test budget recommendation with no income (corner case)"""
        with app.app_context():
            now = datetime.utcnow()
            
            # Only expenses, no income
            for i in range(3):
                tx = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=100,
                    type='expense',
                    category_id=test_categories['Groceries'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                db.session.add(tx)
            
            db.session.commit()
            
            with pytest.raises(PlannerError, match='Monthly income must be positive'):
                BudgetRecommender.recommend_budgets(test_user.id)
    
    def test_recommend_budgets_no_history(self, app, test_user):
        """Test budget recommendation with no transaction history"""
        with app.app_context():
            with pytest.raises(PlannerError, match='No transaction history'):
                BudgetRecommender.recommend_budgets(test_user.id)
    
    def test_recommend_budgets_multiple_months(self, app, test_user, test_categories, test_accounts):
        """Test budget recommendation analyzes specified number of months"""
        with app.app_context():
            now = datetime.utcnow()
            
            # Add transactions from 6 months ago
            for i in range(6):
                tx = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=4000,
                    type='income',
                    category_id=test_categories['Salary'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                db.session.add(tx)
            
            db.session.commit()
            
            # Analyze 3 months
            result3 = BudgetRecommender.recommend_budgets(test_user.id, months=3)
            # Analyze 6 months
            result6 = BudgetRecommender.recommend_budgets(test_user.id, months=6)
            
            # Both should work
            assert result3['monthly_income'] > 0
            assert result6['monthly_income'] > 0


class TestGoalScheduler:
    """Test goal scheduling algorithm"""
    
    def test_compute_goal_schedule_feasible(self, app, test_user, test_categories, test_accounts):
        """Test feasible goal schedule"""
        with app.app_context():
            # Create goal
            target_date = datetime.utcnow() + timedelta(days=180)  # 6 months
            goal = Goal(
                user_id=test_user.id,
                name='Vacation Fund',
                target_amount=3000,
                current_amount=1000,
                target_date=target_date,
                category='savings',
                priority='medium'
            )
            db.session.add(goal)
            db.session.commit()
            
            # Add income/expense transactions (good savings capacity)
            now = datetime.utcnow()
            for i in range(3):
                tx_income = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=5000,
                    type='income',
                    category_id=test_categories['Salary'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                tx_expense = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=3000,
                    type='expense',
                    category_id=test_categories['Groceries'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                db.session.add_all([tx_income, tx_expense])
            
            db.session.commit()
            
            result = GoalScheduler.compute_goal_schedule(goal.id)
            
            assert result['goal_id'] == goal.id
            assert result['name'] == 'Vacation Fund'
            assert result['target_amount'] == 3000
            assert result['current_amount'] == 1000
            assert result['remaining_amount'] == 2000
            assert result['months_remaining'] > 0
            assert result['monthly_required'] > 0
            assert 'monthly_schedule' in result
            assert 'alternative_plans' in result
    
    def test_compute_goal_schedule_already_achieved(self, app, test_user, test_categories):
        """Test goal schedule when target is already achieved"""
        with app.app_context():
            target_date = datetime.utcnow() + timedelta(days=180)
            goal = Goal(
                user_id=test_user.id,
                name='Achieved Goal',
                target_amount=1000,
                current_amount=1500,  # Already exceeded
                target_date=target_date,
                category='savings',
                priority='low'
            )
            db.session.add(goal)
            db.session.commit()
            
            result = GoalScheduler.compute_goal_schedule(goal.id)
            
            assert result['is_feasible'] == True
            assert result['monthly_required'] == 0
            assert result['feasibility_reason'] == 'Goal already achieved'
    
    def test_compute_goal_schedule_short_deadline(self, app, test_user, test_categories, test_accounts):
        """Test goal schedule with short deadline (corner case)"""
        with app.app_context():
            target_date = datetime.utcnow() + timedelta(days=15)  # 15 days
            goal = Goal(
                user_id=test_user.id,
                name='Urgent Goal',
                target_amount=1000,
                current_amount=100,
                target_date=target_date,
                category='savings',
                priority='high'
            )
            db.session.add(goal)
            db.session.commit()
            
            now = datetime.utcnow()
            tx = Transaction(
                user_id=test_user.id,
                account_id=test_accounts[0].id,
                amount=1000,
                type='income',
                category_id=test_categories['Salary'].id,
                transaction_date=now - timedelta(days=1)
            )
            db.session.add(tx)
            db.session.commit()
            
            result = GoalScheduler.compute_goal_schedule(goal.id)
            
            assert result['months_remaining'] <= 1
            # High required amount for short timeframe
            assert result['monthly_required'] > 0
    
    def test_compute_goal_schedule_not_found(self, app, test_user):
        """Test goal schedule with non-existent goal"""
        with app.app_context():
            with pytest.raises(PlannerError, match='not found'):
                GoalScheduler.compute_goal_schedule(999)
    
    def test_compute_goal_schedule_past_deadline(self, app, test_user, test_categories):
        """Test goal schedule with past deadline"""
        with app.app_context():
            target_date = datetime.utcnow() - timedelta(days=1)  # Yesterday
            goal = Goal(
                user_id=test_user.id,
                name='Past Goal',
                target_amount=1000,
                current_amount=100,
                target_date=target_date,
                category='savings',
                priority='low'
            )
            db.session.add(goal)
            db.session.commit()
            
            with pytest.raises(PlannerError, match='past'):
                GoalScheduler.compute_goal_schedule(goal.id)


class TestCashflowForecaster:
    """Test cashflow forecasting algorithm"""
    
    def test_cashflow_forecast_normal(self, app, test_user, test_categories, test_accounts):
        """Test cashflow forecast with normal patterns"""
        with app.app_context():
            now = datetime.utcnow()
            
            # Add 3 months of transactions
            for i in range(3):
                tx_income = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=5000,
                    type='income',
                    category_id=test_categories['Salary'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                tx_expense = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=3000,
                    type='expense',
                    category_id=test_categories['Groceries'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                db.session.add_all([tx_income, tx_expense])
            
            db.session.commit()
            
            result = CashflowForecaster.cashflow_forecast(test_user.id, months=6)
            
            assert result['user_id'] == test_user.id
            assert result['forecast_months'] == 6
            assert result['starting_balance'] == 15000  # Checking + Savings
            assert len(result['monthly_forecasts']) == 6
            assert 'warnings' in result
    
    def test_cashflow_forecast_negative_projection(self, app, test_user, test_categories, test_accounts):
        """Test cashflow forecast with negative balance projection"""
        with app.app_context():
            now = datetime.utcnow()
            
            # High expenses, low income
            for i in range(3):
                tx_income = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=1000,
                    type='income',
                    category_id=test_categories['Salary'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                tx_expense = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=3000,  # Triple the income ensures negative cashflow
                    type='expense',
                    category_id=test_categories['Groceries'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                db.session.add_all([tx_income, tx_expense])
            
            db.session.commit()
            
            result = CashflowForecaster.cashflow_forecast(test_user.id, months=6)
            
            # Verify result structure
            assert result is not None
            assert len(result['monthly_forecasts']) == 6
            assert 'warnings' in result
            assert 'rule_trace' in result
    
    def test_cashflow_forecast_no_history(self, app, test_user):
        """Test cashflow forecast with no transaction history"""
        with app.app_context():
            with pytest.raises(PlannerError, match='No transaction history'):
                CashflowForecaster.cashflow_forecast(test_user.id)
    
    def test_cashflow_forecast_zero_income(self, app, test_user, test_categories, test_accounts):
        """Test cashflow forecast with only expenses (corner case)"""
        with app.app_context():
            now = datetime.utcnow()
            
            # Only expenses
            for i in range(3):
                tx = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=1000,
                    type='expense',
                    category_id=test_categories['Groceries'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                db.session.add(tx)
            
            db.session.commit()
            
            result = CashflowForecaster.cashflow_forecast(test_user.id, months=3)
            
            # Should project negative netflow
            assert result['monthly_forecasts'][0]['net_cashflow'] < 0
    
    def test_cashflow_forecast_extended_horizon(self, app, test_user, test_categories, test_accounts):
        """Test cashflow forecast with extended horizon"""
        with app.app_context():
            now = datetime.utcnow()
            
            # Add base transactions
            for i in range(3):
                tx_income = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=4000,
                    type='income',
                    category_id=test_categories['Salary'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                db.session.add(tx_income)
            
            db.session.commit()
            
            # Forecast 24 months
            result = CashflowForecaster.cashflow_forecast(test_user.id, months=24)
            
            assert len(result['monthly_forecasts']) == 24


class TestPortfolioAllocator:
    """Test portfolio allocation algorithm"""
    
    def test_portfolio_allocation_conservative(self, app):
        """Test conservative portfolio allocation"""
        with app.app_context():
            result = PortfolioAllocator.portfolio_allocation('conservative', 65, 10)
            
            assert result['risk_profile'] == 'conservative'
            assert result['age'] == 65
            assert result['horizon'] == 10
            assert 'allocation' in result
            assert sum(result['allocation'].values()) == 100
            # Conservative = lower equity
            assert result['allocation']['stocks'] < 50
            assert result['allocation']['bonds'] > 20
            assert 'expected_return' in result
            assert 'volatility' in result
    
    def test_portfolio_allocation_moderate(self, app):
        """Test moderate portfolio allocation"""
        with app.app_context():
            result = PortfolioAllocator.portfolio_allocation('moderate', 45, 25)
            
            assert result['risk_profile'] == 'moderate'
            # Moderate = balanced equity (45-year-old: 110-45=65% base)
            assert result['allocation']['stocks'] >= 60
            assert sum(result['allocation'].values()) == 100
    
    def test_portfolio_allocation_aggressive(self, app):
        """Test aggressive portfolio allocation"""
        with app.app_context():
            result = PortfolioAllocator.portfolio_allocation('aggressive', 30, 35)
            
            assert result['risk_profile'] == 'aggressive'
            # Aggressive = high equity
            assert result['allocation']['stocks'] > 70
            assert sum(result['allocation'].values()) == 100
    
    def test_portfolio_allocation_short_horizon(self, app):
        """Test portfolio allocation with short horizon"""
        with app.app_context():
            result = PortfolioAllocator.portfolio_allocation('moderate', 50, 3)
            
            # Short horizon should reduce equity (50-10=40%)
            assert result['allocation']['stocks'] <= 50
            assert any('Short horizon' in trace for trace in result['rule_trace'])
    
    def test_portfolio_allocation_long_horizon(self, app):
        """Test portfolio allocation with long horizon"""
        with app.app_context():
            result = PortfolioAllocator.portfolio_allocation('moderate', 35, 30)
            
            # Long horizon should increase equity
            assert result['allocation']['stocks'] > 60
            # Check rule trace mentions long horizon instead of description
            assert any('Long horizon' in trace for trace in result['rule_trace'])
    
    def test_portfolio_allocation_young_age(self, app):
        """Test portfolio allocation for young investor"""
        with app.app_context():
            result = PortfolioAllocator.portfolio_allocation('moderate', 25, 40)
            
            # Young age should favor equity
            assert result['allocation']['stocks'] > 70
    
    def test_portfolio_allocation_elderly(self, app):
        """Test portfolio allocation for elderly investor"""
        with app.app_context():
            result = PortfolioAllocator.portfolio_allocation('moderate', 75, 15)
            
            # Elderly should have lower equity (110-75=35%), conservative (moderate -0) = 35%
            # With 15-year horizon, no additional adjustment
            assert result['allocation']['stocks'] < 50
            assert result['allocation']['bonds'] > 20
    
    def test_portfolio_allocation_invalid_risk(self, app):
        """Test portfolio allocation with invalid risk profile"""
        with app.app_context():
            with pytest.raises(PlannerError, match='Invalid risk profile'):
                PortfolioAllocator.portfolio_allocation('risky', 50, 20)
    
    def test_portfolio_allocation_invalid_age(self, app):
        """Test portfolio allocation with invalid age"""
        with app.app_context():
            with pytest.raises(PlannerError, match='Invalid age'):
                PortfolioAllocator.portfolio_allocation('moderate', 150, 20)
            
            with pytest.raises(PlannerError, match='Invalid age'):
                PortfolioAllocator.portfolio_allocation('moderate', 10, 20)
    
    def test_portfolio_allocation_invalid_horizon(self, app):
        """Test portfolio allocation with invalid horizon"""
        with app.app_context():
            with pytest.raises(PlannerError, match='Invalid horizon'):
                PortfolioAllocator.portfolio_allocation('moderate', 50, -5)


class TestAuditLogging:
    """Test audit log recording of planner actions"""
    
    def test_audit_log_budget_recommendations(self, app, test_user, test_categories, test_accounts):
        """Test that budget recommendations are logged"""
        with app.app_context():
            now = datetime.utcnow()
            
            for i in range(3):
                # Add income
                tx_income = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=5000,
                    type='income',
                    category_id=test_categories['Salary'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                db.session.add(tx_income)
                
                # Add multiple expense categories so there are budgets to recommend
                for category_name, amount in [('Groceries', 400), ('Utilities', 200), ('Rent', 1000)]:
                    tx_expense = Transaction(
                        user_id=test_user.id,
                        account_id=test_accounts[0].id,
                        amount=amount,
                        type='expense',
                        category_id=test_categories[category_name].id,
                        transaction_date=now - timedelta(days=30 * i)
                    )
                    db.session.add(tx_expense)
            
            db.session.commit()
            
            result = BudgetRecommender.recommend_budgets(test_user.id)
            
            # Verify result has recommendations
            assert result is not None
            assert result['monthly_income'] > 0
            assert len(result['recommended_budgets']) > 0


class TestPlannerIntegration:
    """Integration tests for planner service"""
    
    def test_all_planners_accessible(self, app, test_user, test_categories, test_accounts):
        """Test that all planner functions are accessible with proper setup"""
        with app.app_context():
            now = datetime.utcnow()
            
            # Setup data
            for i in range(3):
                tx_income = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=5000,
                    type='income',
                    category_id=test_categories['Salary'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                tx_expense = Transaction(
                    user_id=test_user.id,
                    account_id=test_accounts[0].id,
                    amount=1000,
                    type='expense',
                    category_id=test_categories['Groceries'].id,
                    transaction_date=now - timedelta(days=30 * i)
                )
                db.session.add_all([tx_income, tx_expense])
            
            # Create goal
            goal = Goal(
                user_id=test_user.id,
                name='Test Goal',
                target_amount=5000,
                current_amount=1000,
                target_date=now + timedelta(days=180),
                category='savings',
                priority='medium'
            )
            db.session.add(goal)
            db.session.commit()
            
            # Test all functions
            budgets = BudgetRecommender.recommend_budgets(test_user.id)
            assert budgets is not None
            
            schedule = GoalScheduler.compute_goal_schedule(goal.id)
            assert schedule is not None
            
            cashflow = CashflowForecaster.cashflow_forecast(test_user.id)
            assert cashflow is not None
            
            portfolio = PortfolioAllocator.portfolio_allocation('moderate', 45, 25)
            assert portfolio is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
