from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import Budget, Transaction, Category
from app.schemas import BudgetSchema
from decimal import Decimal
from datetime import datetime

budgets_bp = Blueprint('budgets', __name__, url_prefix='/api/budgets')


@budgets_bp.route('/', methods=['GET'])
@jwt_required()
def list_budgets():
    user_id = get_jwt_identity()
    budgets = Budget.query.filter_by(user_id=user_id).all()
    out = []
    for b in budgets:
        # compute spent amount within budget window
        q = Transaction.query.filter(Transaction.user_id == user_id)
        if b.category_id:
            q = q.filter(Transaction.category_id == b.category_id)
        if b.start_date:
            q = q.filter(Transaction.transaction_date >= b.start_date)
        if b.end_date:
            q = q.filter(Transaction.transaction_date <= b.end_date)
        spent = sum([float(tx.amount) for tx in q.all() if tx.type == 'expense'])

        cat_name = None
        if b.category_id:
            c = db.session.get(Category, b.category_id)
            if c:
                cat_name = c.name

        out.append({
            'id': b.id,
            'category_id': b.category_id,
            'category_name': cat_name,
            'limit_amount': float(b.limit_amount),
            'period': b.period,
            'start_date': b.start_date.isoformat() if b.start_date else None,
            'end_date': b.end_date.isoformat() if b.end_date else None,
            'is_active': b.is_active,
            'spent': spent,
        })

    return jsonify({'data': out}), 200


@budgets_bp.route('/', methods=['POST'])
@jwt_required()
def create_budget():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    try:
        # Parse optional dates if provided as ISO strings
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if isinstance(start_date, str):
            try:
                start_date = datetime.fromisoformat(start_date)
            except Exception:
                start_date = None
        if isinstance(end_date, str):
            try:
                end_date = datetime.fromisoformat(end_date)
            except Exception:
                end_date = None

        b = Budget(
            user_id=user_id,
            category_id=data.get('category_id'),
            limit_amount=data.get('limit_amount', 0),
            period=data.get('period', 'monthly'),
            start_date=start_date,
            end_date=end_date,
            is_active=data.get('is_active', True),
        )
        db.session.add(b)
        db.session.commit()
        return jsonify({'id': b.id}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create budget error: {e}")
        return jsonify({'error': 'Failed to create budget'}), 500


@budgets_bp.route('/<int:budget_id>', methods=['PUT'])
@jwt_required()
def update_budget(budget_id):
    user_id = get_jwt_identity()
    b = db.session.get(Budget, budget_id)
    if not b or b.user_id != user_id:
        return jsonify({'error': 'Budget not found'}), 404

    data = request.get_json() or {}
    allowed = ['limit_amount', 'is_active', 'start_date', 'end_date', 'period', 'category_id']
    for k in allowed:
        if k in data:
            setattr(b, k, data[k])

    try:
        db.session.commit()
        return jsonify({'id': b.id}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update budget error: {e}")
        return jsonify({'error': 'Failed to update budget'}), 500
