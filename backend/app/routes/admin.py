from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app.database import db
from app.models import Rule, User, Category
from app.schemas import RuleSchema, RuleDetailSchema
from app.services.rule_engine import (
    RuleEngine, RuleValidationError, create_sample_transaction
)
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

rule_engine = RuleEngine()


def admin_required(fn):
    """Decorator to require admin role"""
    @wraps(fn)
    def decorator(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return fn(*args, **kwargs)
    
    return decorator


@admin_bp.route('/rules', methods=['GET'])
@jwt_required()
@admin_required
def list_rules():
    """List all rules with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Rule.query.order_by(Rule.priority.desc(), Rule.created_at.desc())
    
    # Filter by active status if provided
    active = request.args.get('active', type=lambda v: v.lower() == 'true', default=None)
    if active is not None:
        query = query.filter_by(is_active=active)
    
    paginated = query.paginate(page=page, per_page=per_page)
    
    schema = RuleSchema(many=True)
    return jsonify({
        'data': schema.dump(paginated.items),
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }), 200


@admin_bp.route('/rules/<int:rule_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_rule(rule_id):
    """Get a specific rule"""
    rule = Rule.query.get(rule_id)
    
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    schema = RuleDetailSchema()
    return jsonify(schema.dump(rule)), 200


@admin_bp.route('/rules', methods=['POST'])
@jwt_required()
@admin_required
def create_rule():
    """Create a new rule"""
    schema = RuleDetailSchema()
    
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    try:
        # Validate the rule
        rule_engine.validate_rule({
            'name': data['name'],
            'condition': data['condition'],
            'action': data['action']
        })
        
        rule = Rule(
            user_id=get_jwt_identity(),
            name=data['name'],
            description=data.get('description'),
            condition=data['condition'],
            action=data['action'],
            priority=data.get('priority', 0),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(rule)
        db.session.commit()
        
        # Invalidate cache
        rule_engine.invalidate_cache()
        
        result = RuleDetailSchema().dump(rule)
        return jsonify(result), 201
    
    except RuleValidationError as err:
        return jsonify({'error': str(err)}), 400
    except Exception as err:
        db.session.rollback()
        current_app.logger.error(f"Error creating rule: {str(err)}")
        return jsonify({'error': 'Failed to create rule'}), 500


@admin_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_rule(rule_id):
    """Update a rule"""
    rule = Rule.query.get(rule_id)
    
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    schema = RuleDetailSchema(partial=True)
    
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    try:
        # If condition or action is being updated, validate the whole rule
        if 'condition' in data or 'action' in data:
            rule_engine.validate_rule({
                'name': data.get('name', rule.name),
                'condition': data.get('condition', rule.condition),
                'action': data.get('action', rule.action)
            })
        
        # Update fields
        for key, value in data.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        db.session.commit()
        
        # Invalidate cache
        rule_engine.invalidate_cache()
        
        result = RuleDetailSchema().dump(rule)
        return jsonify(result), 200
    
    except RuleValidationError as err:
        db.session.rollback()
        return jsonify({'error': str(err)}), 400
    except Exception as err:
        db.session.rollback()
        current_app.logger.error(f"Error updating rule: {str(err)}")
        return jsonify({'error': 'Failed to update rule'}), 500


@admin_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_rule(rule_id):
    """Delete a rule"""
    rule = Rule.query.get(rule_id)
    
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    try:
        db.session.delete(rule)
        db.session.commit()
        
        # Invalidate cache
        rule_engine.invalidate_cache()
        
        return jsonify({'message': 'Rule deleted'}), 200
    except Exception as err:
        db.session.rollback()
        current_app.logger.error(f"Error deleting rule: {str(err)}")
        return jsonify({'error': 'Failed to delete rule'}), 500


@admin_bp.route('/rules/validate', methods=['POST'])
@jwt_required()
@admin_required
def validate_rule():
    """Validate rule JSON and test on sample transaction"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Validate the rule structure
        rule_engine.validate_rule(data)
        
        # Test on sample transaction
        sample_tx = create_sample_transaction()
        
        try:
            modified_tx, trace = rule_engine.evaluate_transaction(sample_tx, [data])
            
            # Remove internal fields
            if '_stop_processing' in modified_tx:
                del modified_tx['_stop_processing']
            
            # Convert Decimal to float for JSON
            if 'amount' in modified_tx:
                modified_tx['amount'] = float(modified_tx['amount'])
            
            return jsonify({
                'valid': True,
                'message': 'Rule is valid',
                'sample_evaluation': {
                    'sample_transaction': {
                        'description': sample_tx.get('description'),
                        'amount': float(sample_tx.get('amount', 0)),
                        'date': sample_tx.get('transaction_date').isoformat() if sample_tx.get('transaction_date') else None
                    },
                    'matched': len(trace) > 0,
                    'trace': trace
                }
            }), 200
        
        except Exception as e:
            return jsonify({
                'valid': True,
                'message': 'Rule structure is valid but evaluation failed',
                'evaluation_error': str(e)
            }), 200
    
    except RuleValidationError as err:
        return jsonify({
            'valid': False,
            'message': 'Rule validation failed',
            'error': str(err)
        }), 400
    except Exception as err:
        current_app.logger.error(f"Error validating rule: {str(err)}")
        return jsonify({'error': 'Failed to validate rule'}), 500


@admin_bp.route('/rules/<int:rule_id>/toggle', methods=['POST'])
@jwt_required()
@admin_required
def toggle_rule_active(rule_id):
    """Toggle rule active status"""
    rule = Rule.query.get(rule_id)
    
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    try:
        rule.is_active = not rule.is_active
        db.session.commit()
        
        # Invalidate cache
        rule_engine.invalidate_cache()
        
        result = RuleDetailSchema().dump(rule)
        return jsonify(result), 200
    except Exception as err:
        db.session.rollback()
        current_app.logger.error(f"Error toggling rule: {str(err)}")
        return jsonify({'error': 'Failed to toggle rule'}), 500
