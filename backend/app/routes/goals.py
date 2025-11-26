from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import Goal

goals_bp = Blueprint('goals', __name__, url_prefix='/api/goals')


@goals_bp.route('/', methods=['GET'])
@jwt_required()
def list_goals():
    user_id = get_jwt_identity()
    goals = Goal.query.filter_by(user_id=user_id).all()
    out = []
    for g in goals:
        out.append({
            'id': g.id,
            'name': g.name,
            'description': g.description,
            'target_amount': float(g.target_amount),
            'current_amount': float(g.current_amount),
            'target_date': g.target_date.isoformat() if g.target_date else None,
            'category': g.category,
            'priority': g.priority,
            'is_active': g.is_active,
        })
    return jsonify({'data': out}), 200


@goals_bp.route('/', methods=['POST'])
@jwt_required()
def create_goal():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    try:
        g = Goal(
            user_id=user_id,
            name=data.get('name'),
            description=data.get('description'),
            target_amount=data.get('target_amount', 0),
            current_amount=data.get('current_amount', 0),
            target_date=data.get('target_date'),
            category=data.get('category'),
            priority=data.get('priority', 'medium'),
            is_active=data.get('is_active', True),
        )
        db.session.add(g)
        db.session.commit()
        return jsonify({'id': g.id}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create goal error: {e}")
        return jsonify({'error': 'Failed to create goal'}), 500


@goals_bp.route('/<int:goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    user_id = get_jwt_identity()
    g = db.session.get(Goal, goal_id)
    if not g or g.user_id != user_id:
        return jsonify({'error': 'Goal not found'}), 404

    data = request.get_json() or {}
    allowed = ['name', 'description', 'target_amount', 'current_amount', 'target_date', 'category', 'priority', 'is_active']
    for k in allowed:
        if k in data:
            setattr(g, k, data[k])

    try:
        db.session.commit()
        return jsonify({'id': g.id}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update goal error: {e}")
        return jsonify({'error': 'Failed to update goal'}), 500
