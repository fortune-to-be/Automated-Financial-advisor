"""
Planner API Routes

Endpoints for budget recommendations, goal scheduling, cashflow forecasting,
and portfolio allocation.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.planner import (
    BudgetRecommender, GoalScheduler, CashflowForecaster, PortfolioAllocator, PlannerError, save_plan_to_audit_log
)

planner_bp = Blueprint('planner', __name__, url_prefix='/api/planner')


@planner_bp.route('/recommend-budgets', methods=['POST'])
@jwt_required()
def recommend_budgets():
    """
    POST /api/planner/recommend-budgets
    
    Generate budget recommendations for the current user.
    
    JSON Body:
    {
        "months": 3  (optional, default 3)
    }
    
    Returns: Budget recommendations with 50/30/20 rule and debt adjustment
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        months = data.get('months', 3)
        
        # Validate
        if not isinstance(months, int) or months < 1 or months > 12:
            return jsonify({'error': 'months must be 1-12'}), 400
        
        # Generate recommendations
        recommendations = BudgetRecommender.recommend_budgets(user_id, months)
        
        # Save to audit log
        save_plan_to_audit_log(user_id, 'BudgetRecommendation', recommendations)
        
        return jsonify(recommendations), 200
    
    except PlannerError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@planner_bp.route('/goal-schedule/<int:goal_id>', methods=['GET'])
@jwt_required()
def compute_goal_schedule(goal_id):
    """
    GET /api/planner/goal-schedule/<goal_id>
    
    Compute monthly payment schedule and feasibility for a goal.
    
    Returns: Goal schedule with feasibility analysis and alternatives
    """
    try:
        user_id = get_jwt_identity()
        
        # Verify goal ownership
        from app.models import Goal
        goal = Goal.query.get(goal_id)
        if not goal or goal.user_id != user_id:
            return jsonify({'error': 'Goal not found or not owned by user'}), 404
        
        # Compute schedule
        schedule = GoalScheduler.compute_goal_schedule(goal_id)
        
        # Save to audit log
        save_plan_to_audit_log(user_id, 'GoalSchedule', schedule)
        
        return jsonify(schedule), 200
    
    except PlannerError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@planner_bp.route('/cashflow-forecast', methods=['GET'])
@jwt_required()
def cashflow_forecast():
    """
    GET /api/planner/cashflow-forecast?months=12
    
    Forecast future monthly balances and identify negative balance months.
    
    Query Parameters:
    - months: Number of months to forecast (1-36, default 12)
    
    Returns: Monthly projections with warnings for negative balances
    """
    try:
        user_id = get_jwt_identity()
        months = request.args.get('months', 12, type=int)
        
        # Validate
        if months < 1 or months > 36:
            return jsonify({'error': 'months must be 1-36'}), 400
        
        # Generate forecast
        forecast = CashflowForecaster.cashflow_forecast(user_id, months)
        
        # Save to audit log
        save_plan_to_audit_log(user_id, 'CashflowForecast', forecast)
        
        return jsonify(forecast), 200
    
    except PlannerError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@planner_bp.route('/portfolio-allocation', methods=['POST'])
@jwt_required()
def portfolio_allocation():
    """
    POST /api/planner/portfolio-allocation
    
    Recommend portfolio allocation based on risk profile, age, and horizon.
    
    JSON Body:
    {
        "risk_profile": "conservative|moderate|aggressive",
        "age": 35,
        "horizon": 20
    }
    
    Returns: Asset allocation percentages with expected return and volatility
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Validate
        risk_profile = data.get('risk_profile', '').lower()
        age = data.get('age')
        horizon = data.get('horizon')
        
        if not risk_profile or risk_profile not in ['conservative', 'moderate', 'aggressive']:
            return jsonify({'error': 'risk_profile must be conservative, moderate, or aggressive'}), 400
        
        if not isinstance(age, int) or age < 18 or age > 120:
            return jsonify({'error': 'age must be 18-120'}), 400
        
        if not isinstance(horizon, int) or horizon < 1 or horizon > 70:
            return jsonify({'error': 'horizon must be 1-70'}), 400
        
        # Generate allocation
        allocation = PortfolioAllocator.portfolio_allocation(risk_profile, age, horizon)
        
        # Save to audit log
        save_plan_to_audit_log(user_id, 'PortfolioAllocation', allocation)
        
        return jsonify(allocation), 200
    
    except PlannerError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500
