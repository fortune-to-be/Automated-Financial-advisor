"""
Financial Planner Service

Implements deterministic algorithms for:
- Budget recommendations (50/30/20 rule with debt adjustment)
- Goal feasibility and scheduling
- Cashflow forecasting
- Portfolio allocation heuristics
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Tuple, Any, Optional
from app.database import db
from app.models import Transaction, Goal, Account, Category, AuditLog, Budget, User


class PlannerError(Exception):
    """Custom exception for planner errors"""
    pass


class BudgetRecommender:
    """Recommends monthly budgets using 50/30/20 baseline with debt adjustment"""
    
    @staticmethod
    def recommend_budgets(user_id: int, months: int = 3) -> Dict[str, Any]:
        """
        Generate per-category budget suggestions based on historical spending.
        
        Algorithm:
        1. Calculate average monthly income from last N months
        2. If debt exists, reduce discretionary budget by debt ratio
        3. Apply 50/30/20 baseline: 50% needs, 30% wants, 20% savings
        4. Adjust per-category based on historical averages
        
        Args:
            user_id: User ID
            months: Number of months to analyze (default 3)
            
        Returns:
            {
                'user_id': int,
                'recommended_budgets': [
                    {
                        'category_id': int,
                        'category_name': str,
                        'monthly_amount': Decimal,
                        'explanation': str,
                        'based_on_average': Decimal
                    }
                ],
                'monthly_income': Decimal,
                'debt_ratio': float,
                'rule_trace': [str],
                'generated_at': datetime
            }
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30 * months)
        
        # Get all transactions
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).all()
        
        if not transactions:
            raise PlannerError(f"No transaction history for user {user_id}")
        
        # Calculate income and expenses by category
        total_income = Decimal(0)
        monthly_expenses = {}  # category_id -> {amounts: [], count: int}
        
        for tx in transactions:
            if tx.type == 'income':
                total_income += Decimal(str(tx.amount))
            elif tx.type == 'expense' and tx.category_id:
                if tx.category_id not in monthly_expenses:
                    monthly_expenses[tx.category_id] = {'amounts': [], 'category': tx.category}
                monthly_expenses[tx.category_id]['amounts'].append(Decimal(str(tx.amount)))
        
        # Calculate monthly average
        num_months = max(1, (end_date - start_date).days / 30)
        monthly_income = total_income / Decimal(str(num_months))
        
        if monthly_income <= 0:
            raise PlannerError("Monthly income must be positive")
        
        # Calculate debt ratio (estimated from accounts with negative balance)
        accounts = Account.query.filter_by(user_id=user_id).all()
        total_debt = sum(max(0, -Decimal(str(acc.balance))) for acc in accounts)
        debt_ratio = min(1.0, float(total_debt / monthly_income)) if monthly_income > 0 else 0
        
        # Build recommendations
        recommendations = []
        rule_trace = []
        
        # 50/30/20 baseline with debt adjustment
        needs_budget = monthly_income * Decimal('0.50')  # 50% for needs
        wants_budget = monthly_income * Decimal('0.30') * Decimal(str(1 - debt_ratio))  # Reduce by debt
        savings_budget = monthly_income * Decimal('0.20') * Decimal(str(1 - debt_ratio))  # Reduce by debt
        
        rule_trace.append(f"Base 50/30/20 rule applied. Income: ${monthly_income:.2f}")
        
        if debt_ratio > 0:
            rule_trace.append(
                f"Debt adjustment: {debt_ratio*100:.1f}% of income owed. "
                f"Reducing wants/savings by {debt_ratio*100:.1f}%"
            )
        
        # Categorize and recommend
        for category_id, data in monthly_expenses.items():
            amounts = data['amounts']
            category = data['category']
            avg_spending = sum(amounts) / Decimal(str(len(amounts))) if amounts else Decimal(0)
            
            # Determine category type
            category_name = category.name if category else f"Category {category_id}"
            
            # Estimate if need or want
            category_type = estimate_category_type(category_name)
            
            if category_type == 'need':
                recommended = min(avg_spending * Decimal('1.1'), needs_budget / 5)  # 10% buffer or 1/5 of needs
                suggestions = "Essential spending - increased 10% for buffer"
            elif category_type == 'want':
                recommended = min(avg_spending * Decimal('1.05'), wants_budget / 5)  # 5% buffer or 1/5 of wants
                suggestions = "Discretionary spending - keep near average"
            else:
                recommended = avg_spending * Decimal('1.0')
                suggestions = "Based on historical average"
            
            recommendations.append({
                'category_id': category_id,
                'category_name': category_name,
                'monthly_amount': float(recommended),
                'explanation': suggestions,
                'based_on_average': float(avg_spending)
            })
        
        return {
            'user_id': user_id,
            'recommended_budgets': recommendations,
            'monthly_income': float(monthly_income),
            'debt_ratio': debt_ratio,
            'rule_trace': rule_trace,
            'generated_at': datetime.now(timezone.utc)
        }


class GoalScheduler:
    """Computes goal feasibility and monthly schedules"""
    
    @staticmethod
    def compute_goal_schedule(goal_id: int) -> Dict[str, Any]:
        """
        Compute monthly required amounts and feasibility for a goal.
        
        Algorithm:
        1. Get goal details (target, current, deadline)
        2. Calculate remaining amount
        3. Calculate months to deadline
        4. Compute required monthly savings
        5. Compare against historical capacity
        6. Generate alternative plans if infeasible
        
        Args:
            goal_id: Goal ID
            
        Returns:
            {
                'goal_id': int,
                'name': str,
                'target_amount': Decimal,
                'current_amount': Decimal,
                'remaining_amount': Decimal,
                'months_remaining': int,
                'monthly_required': Decimal,
                'is_feasible': bool,
                'feasibility_reason': str,
                'monthly_schedule': [
                    {
                        'month': int,
                        'date': date,
                        'cumulative_required': Decimal,
                        'status': 'on_track|behind|on_pace'
                    }
                ],
                'alternative_plans': [
                    {
                        'monthly_amount': Decimal,
                        'months_to_complete': int,
                        'target_date': date
                    }
                ],
                'rule_trace': [str]
            }
        """
        goal = db.session.get(Goal, goal_id)
        if not goal:
            raise PlannerError(f"Goal {goal_id} not found")
        
        now = datetime.now(timezone.utc)
        target_date = goal.target_date

        # Normalize target_date to timezone-aware UTC if stored as naive
        if target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=timezone.utc)

        if target_date <= now:
            raise PlannerError(f"Goal deadline {target_date} is in the past")
        
        # Calculate remaining
        target_amount = Decimal(str(goal.target_amount))
        current_amount = Decimal(str(goal.current_amount))
        remaining_amount = target_amount - current_amount
        
        if remaining_amount <= 0:
            return {
                'goal_id': goal_id,
                'name': goal.name,
                'target_amount': float(target_amount),
                'current_amount': float(current_amount),
                'remaining_amount': 0,
                'months_remaining': 0,
                'monthly_required': 0,
                'is_feasible': True,
                'feasibility_reason': 'Goal already achieved',
                'monthly_schedule': [],
                'alternative_plans': [],
                'rule_trace': ['Goal target already reached']
            }
        
        # Calculate timeline
        days_remaining = (target_date - now).days
        months_remaining = max(1, days_remaining / 30)
        monthly_required = remaining_amount / Decimal(str(months_remaining))
        
        # Get user's average savings capacity
        user = goal.user
        user_transactions = Transaction.query.filter(
            Transaction.user_id == user.id,
            Transaction.transaction_date >= now - timedelta(days=90)
        ).all()
        
        monthly_savings = Decimal(0)
        if user_transactions:
            total_income = sum(Decimal(str(tx.amount)) for tx in user_transactions if tx.type == 'income')
            total_expenses = sum(Decimal(str(tx.amount)) for tx in user_transactions if tx.type == 'expense')
            monthly_savings = (total_income - total_expenses) / Decimal('3')  # Average over 3 months
        
        # Determine feasibility
        is_feasible = monthly_required <= monthly_savings and remaining_amount > 0
        
        rule_trace = [
            f"Goal: {goal.name}",
            f"Target: ${target_amount:.2f}, Current: ${current_amount:.2f}",
            f"Remaining: ${remaining_amount:.2f} over {months_remaining:.1f} months",
            f"Required monthly: ${monthly_required:.2f}",
            f"Average monthly savings capacity: ${monthly_savings:.2f}"
        ]
        
        if is_feasible:
            feasibility_reason = f"Feasible with ${monthly_required:.2f}/month savings"
        else:
            feasibility_reason = f"Requires ${monthly_required:.2f}/month but avg capacity is ${monthly_savings:.2f}/month"
            rule_trace.append(f"⚠️ {feasibility_reason}")
        
        # Build monthly schedule
        monthly_schedule = []
        current_date = now
        cumulative = current_amount
        
        for month in range(1, int(months_remaining) + 2):
            cumulative += monthly_required
            current_date = now + timedelta(days=30 * month)
            
            # Status
            if current_date > target_date:
                status = 'behind' if cumulative < target_amount else 'on_pace'
            else:
                expected_at_this_month = current_amount + (monthly_required * Decimal(str(month)))
                if cumulative >= expected_at_this_month:
                    status = 'on_track'
                else:
                    status = 'behind'
            
            monthly_schedule.append({
                'month': month,
                'date': current_date.isoformat(),
                'cumulative_required': float(cumulative),
                'status': status
            })
        
        # Alternative plans
        alternative_plans = []
        for alt_months in [months_remaining / 2, months_remaining * 1.5, months_remaining * 2]:
            if alt_months > 0:
                alt_monthly = remaining_amount / Decimal(str(alt_months))
                alt_date = now + timedelta(days=30 * float(alt_months))
                alternative_plans.append({
                    'monthly_amount': float(alt_monthly),
                    'months_to_complete': int(alt_months),
                    'target_date': alt_date.isoformat()
                })
        
        return {
            'goal_id': goal_id,
            'name': goal.name,
            'target_amount': float(target_amount),
            'current_amount': float(current_amount),
            'remaining_amount': float(remaining_amount),
            'months_remaining': int(months_remaining),
            'monthly_required': float(monthly_required),
            'is_feasible': is_feasible,
            'feasibility_reason': feasibility_reason,
            'monthly_schedule': monthly_schedule,
            'alternative_plans': alternative_plans,
            'rule_trace': rule_trace
        }


class CashflowForecaster:
    """Forecasts monthly cashflow and balances"""
    
    @staticmethod
    def cashflow_forecast(user_id: int, months: int = 12) -> Dict[str, Any]:
        """
        Forecast future monthly balances based on historical patterns.
        
        Algorithm:
        1. Calculate average monthly income and expenses from last 3 months
        2. Project forward for N months
        3. Identify months with negative balance
        4. Generate warnings
        
        Args:
            user_id: User ID
            months: Number of months to forecast (default 12)
            
        Returns:
            {
                'user_id': int,
                'forecast_months': int,
                'starting_balance': Decimal,
                'monthly_forecasts': [
                    {
                        'month': int,
                        'date': date,
                        'avg_income': Decimal,
                        'avg_expenses': Decimal,
                        'net_cashflow': Decimal,
                        'projected_balance': Decimal,
                        'status': 'healthy|warning|critical'
                    }
                ],
                'negative_balance_months': [int],
                'warnings': [str],
                'rule_trace': [str]
            }
        """
        # Get user accounts for starting balance
        accounts = Account.query.filter_by(user_id=user_id).all()
        starting_balance = sum(Decimal(str(acc.balance)) for acc in accounts)
        
        # Get historical data (last 90 days)
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=90)
        
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date
        ).all()
        
        if not transactions:
            raise PlannerError(f"No transaction history for user {user_id}")
        
        # Calculate average monthly income and expenses
        monthly_income = Decimal(0)
        monthly_expenses = Decimal(0)
        
        for tx in transactions:
            if tx.type == 'income':
                monthly_income += Decimal(str(tx.amount))
            elif tx.type == 'expense':
                monthly_expenses += Decimal(str(tx.amount))
        
        # Average over 3 months
        monthly_income = monthly_income / Decimal('3')
        monthly_expenses = monthly_expenses / Decimal('3')
        monthly_netflow = monthly_income - monthly_expenses
        
        # Generate forecast
        monthly_forecasts = []
        negative_months = []
        warnings = []
        current_balance = starting_balance
        
        rule_trace = [
            f"Starting balance: ${starting_balance:.2f}",
            f"Average monthly income: ${monthly_income:.2f}",
            f"Average monthly expenses: ${monthly_expenses:.2f}",
            f"Average monthly netflow: ${monthly_netflow:.2f}"
        ]
        
        for month in range(1, months + 1):
            forecast_date = now + timedelta(days=30 * month)
            current_balance += monthly_netflow
            
            # Determine status
            if current_balance < 0:
                status = 'critical'
                negative_months.append(month)
                warnings.append(
                    f"Month {month} ({forecast_date.strftime('%B %Y')}): "
                    f"Balance would be ${current_balance:.2f} - CRITICAL"
                )
            elif current_balance < monthly_expenses:
                status = 'warning'
                warnings.append(
                    f"Month {month} ({forecast_date.strftime('%B %Y')}): "
                    f"Balance ${current_balance:.2f} < monthly expenses ${monthly_expenses:.2f}"
                )
            else:
                status = 'healthy'
            
            monthly_forecasts.append({
                'month': month,
                'date': forecast_date.isoformat(),
                'avg_income': float(monthly_income),
                'avg_expenses': float(monthly_expenses),
                'net_cashflow': float(monthly_netflow),
                'projected_balance': float(current_balance),
                'status': status
            })
        
        if negative_months:
            rule_trace.append(f"⚠️ {len(negative_months)} months with negative balance")
        else:
            rule_trace.append("✓ All months remain solvent")
        
        return {
            'user_id': user_id,
            'forecast_months': months,
            'starting_balance': float(starting_balance),
            'monthly_forecasts': monthly_forecasts,
            'negative_balance_months': negative_months,
            'warnings': warnings,
            'rule_trace': rule_trace
        }


class PortfolioAllocator:
    """Portfolio allocation heuristics based on risk profile and age"""
    
    @staticmethod
    def portfolio_allocation(risk_profile: str, age: int, horizon: int) -> Dict[str, Any]:
        """
        Recommend portfolio allocation using age-based and risk-based heuristics.
        
        Algorithms:
        1. Age-based baseline: 110 - age = % stocks
        2. Risk adjustment: Conservative -20%, Moderate 0%, Aggressive +20%
        3. Time horizon adjustment: Short (<5yr) reduce equity, Long (>20yr) increase
        4. Return allocation by asset class
        
        Args:
            risk_profile: 'conservative', 'moderate', 'aggressive'
            age: Age in years
            horizon: Investment horizon in years
            
        Returns:
            {
                'risk_profile': str,
                'age': int,
                'horizon': int,
                'allocation': {
                    'stocks': float (0-100),
                    'bonds': float (0-100),
                    'real_estate': float (0-100),
                    'cash': float (0-100),
                    'alternatives': float (0-100)
                },
                'explanation': str,
                'expected_return': float (annual %),
                'volatility': float (std dev %),
                'rule_trace': [str]
            }
        """
        if age < 18 or age > 120:
            raise PlannerError(f"Invalid age: {age}")
        
        if horizon < 1 or horizon > 70:
            raise PlannerError(f"Invalid horizon: {horizon}")
        
        if risk_profile not in ['conservative', 'moderate', 'aggressive']:
            raise PlannerError(f"Invalid risk profile: {risk_profile}")
        
        rule_trace = []
        
        # Age-based baseline (110 - age rule)
        age_based_equity = max(20, min(90, 110 - age))
        rule_trace.append(f"Age-based formula (110-age): {age_based_equity}% equity")
        
        # Risk adjustment
        risk_adjustments = {
            'conservative': -20,
            'moderate': 0,
            'aggressive': 20
        }
        risk_adj = risk_adjustments[risk_profile]
        equity_pct = max(10, min(95, age_based_equity + risk_adj))
        rule_trace.append(
            f"Risk adjustment ({risk_profile}): {risk_adj:+d}% → {equity_pct}% equity"
        )
        
        # Time horizon adjustment
        horizon_adj = 0
        if horizon < 5:
            horizon_adj = -10
            rule_trace.append(f"Short horizon (<5yr): -10% equity")
        elif horizon > 20:
            horizon_adj = 10
            rule_trace.append(f"Long horizon (>20yr): +10% equity")
        
        equity_pct = max(10, min(95, equity_pct + horizon_adj))
        rule_trace.append(f"Final equity allocation: {equity_pct}%")
        
        # Allocate remaining to bonds, real estate, cash, alternatives
        remaining = 100 - equity_pct
        
        # Conservative: More bonds/cash, Liberal: More alternatives
        if risk_profile == 'conservative':
            bonds = remaining * 0.60
            real_estate = remaining * 0.20
            alternatives = remaining * 0.05
            cash = remaining * 0.15
        elif risk_profile == 'moderate':
            bonds = remaining * 0.50
            real_estate = remaining * 0.25
            alternatives = remaining * 0.10
            cash = remaining * 0.15
        else:  # aggressive
            bonds = remaining * 0.30
            real_estate = remaining * 0.30
            alternatives = remaining * 0.25
            cash = remaining * 0.15
        
        allocation = {
            'stocks': round(equity_pct, 1),
            'bonds': round(bonds, 1),
            'real_estate': round(real_estate, 1),
            'cash': round(cash, 1),
            'alternatives': round(alternatives, 1)
        }
        
        # Expected return (simplified model)
        expected_return = (
            equity_pct * 0.08 +  # Stocks: 8% annually
            bonds * 0.03 +        # Bonds: 3% annually
            real_estate * 0.05 +  # Real estate: 5% annually
            alternatives * 0.04 + # Alternatives: 4% annually
            cash * 0.01           # Cash: 1% annually
        ) / 100
        
        # Volatility (simplified)
        equity_volatility = equity_pct * 0.15  # Equity volatility ~15%
        bond_volatility = bonds * 0.05         # Bond volatility ~5%
        volatility = (equity_volatility + bond_volatility) / 100
        
        explanation = (
            f"Portfolio for {age}-year-old with {risk_profile} risk tolerance "
            f"and {horizon}-year horizon. "
            f"{equity_pct}% stocks provide growth, {bonds:.1f}% bonds provide stability, "
            f"{real_estate:.1f}% real estate for diversification, "
            f"and {cash:.1f}% cash for liquidity."
        )
        
        return {
            'risk_profile': risk_profile,
            'age': age,
            'horizon': horizon,
            'allocation': allocation,
            'explanation': explanation,
            'expected_return': round(expected_return * 100, 2),
            'volatility': round(volatility * 100, 2),
            'rule_trace': rule_trace
        }


def estimate_category_type(category_name: str) -> str:
    """Estimate if category is need, want, or other"""
    needs = ['groceries', 'utilities', 'rent', 'mortgage', 'insurance', 'medical', 'healthcare', 'fuel', 'gas']
    wants = ['entertainment', 'dining', 'restaurants', 'shopping', 'hobbies', 'vacation', 'travel', 'subscriptions']
    
    name_lower = category_name.lower()
    
    for need in needs:
        if need in name_lower:
            return 'need'
    
    for want in wants:
        if want in name_lower:
            return 'want'
    
    return 'other'


def save_plan_to_audit_log(user_id: int, plan_type: str, plan_data: Dict[str, Any]) -> None:
    """Save generated plan to audit log for future reference"""
    # Normalize datetimes to ISO strings to ensure JSON serializability
    def _normalize(value):
        from datetime import datetime, date

        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, dict):
            return {k: _normalize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_normalize(v) for v in value]
        return value

    safe_plan = _normalize(plan_data)

    audit_log = AuditLog(
        user_id=user_id,
        action=f'plan_generated',
        resource_type=f'Planner{plan_type}',
        new_values=safe_plan
    )
    db.session.add(audit_log)
    db.session.commit()
