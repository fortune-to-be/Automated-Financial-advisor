"""Transaction routes for CRUD operations and CSV import"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime
from decimal import Decimal

from app.database import db
from app.models import Transaction
from app.schemas import (
    TransactionCreateSchema,
    TransactionUpdateSchema,
    TransactionResponseSchema,
    TransactionListSchema,
    CSVImportPreviewResponseSchema,
    CSVImportCommitResponseSchema
)
from app.services.transaction import TransactionService, TransactionImporter, TransactionError

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

transaction_service = TransactionService()
transaction_importer = TransactionImporter()


@transactions_bp.route('/', methods=['POST'])
@jwt_required()
def create_transaction():
    """Create a new transaction"""
    user_id = get_jwt_identity()
    schema = TransactionCreateSchema()
    
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    try:
        tx_dict, applied_rules = transaction_service.create_transaction(
            user_id=user_id,
            account_id=data['account_id'],
            amount=Decimal(str(data['amount'])),
            type=data['type'],
            description=data['description'],
            transaction_date=data.get('transaction_date'),
            category_id=data.get('category_id'),
            tags=data.get('tags')
        )
        
        return jsonify({
            'data': tx_dict,
            'applied_rules': applied_rules
        }), 201
    
    except TransactionError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to create transaction: {str(e)}'}), 500


@transactions_bp.route('/', methods=['GET'])
@jwt_required()
def list_transactions():
    """List transactions with pagination and filters"""
    user_id = get_jwt_identity()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category_id = request.args.get('category_id', type=int)
    account_id = request.args.get('account_id', type=int)
    include_rule_trace = request.args.get('rule_trace', 'false').lower() == 'true'
    
    # Parse dates
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format. Use ISO format.'}), 400
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format. Use ISO format.'}), 400
    
    try:
        result = transaction_service.get_transactions(
            user_id=user_id,
            page=page,
            per_page=per_page,
            start_date=start_dt,
            end_date=end_dt,
            category_id=category_id,
            account_id=account_id,
            include_rule_trace=include_rule_trace
        )
        
        schema = TransactionListSchema()
        return jsonify(schema.dump(result)), 200
    
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve transactions: {str(e)}'}), 500


@transactions_bp.route('/<int:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    """Get a single transaction"""
    user_id = get_jwt_identity()
    include_rule_trace = request.args.get('rule_trace', 'false').lower() == 'true'
    
    try:
        tx_dict = transaction_service.get_transaction(
            user_id=user_id,
            transaction_id=transaction_id,
            include_rule_trace=include_rule_trace
        )
        
        return jsonify({'data': tx_dict}), 200
    
    except TransactionError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve transaction: {str(e)}'}), 500


@transactions_bp.route('/<int:transaction_id>', methods=['PUT'])
@jwt_required()
def update_transaction(transaction_id):
    """Update a transaction (triggers re-evaluation)"""
    user_id = get_jwt_identity()
    schema = TransactionUpdateSchema()
    
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    try:
        tx_dict, applied_rules = transaction_service.update_transaction(
            user_id=user_id,
            transaction_id=transaction_id,
            **data
        )
        
        return jsonify({
            'data': tx_dict,
            'applied_rules': applied_rules
        }), 200
    
    except TransactionError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to update transaction: {str(e)}'}), 500


@transactions_bp.route('/<int:transaction_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(transaction_id):
    """Delete a transaction"""
    user_id = get_jwt_identity()
    
    try:
        transaction_service.delete_transaction(user_id, transaction_id)
        return jsonify({'message': 'Transaction deleted'}), 200
    
    except TransactionError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to delete transaction: {str(e)}'}), 500


@transactions_bp.route('/import/preview', methods=['POST'])
@jwt_required()
def import_preview():
    """Preview CSV import without committing"""
    user_id = get_jwt_identity()
    
    # Check if CSV file is provided
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV format'}), 400
    
    try:
        csv_content = file.read().decode('utf-8')
        max_rows = request.args.get('max_rows', 10, type=int)
        
        result = transaction_importer.preview_csv(
            user_id=user_id,
            csv_content=csv_content,
            max_rows=max_rows
        )
        
        schema = CSVImportPreviewResponseSchema()
        return jsonify(schema.dump(result)), 200
    
    except TransactionError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to preview CSV: {str(e)}'}), 500


@transactions_bp.route('/import/commit', methods=['POST'])
@jwt_required()
def import_commit():
    """Commit CSV import and create transactions"""
    user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV format'}), 400
    
    try:
        csv_content = file.read().decode('utf-8')
        
        result = transaction_importer.commit_import(
            user_id=user_id,
            csv_content=csv_content
        )
        
        schema = CSVImportCommitResponseSchema()
        return jsonify(schema.dump(result)), 200
    
    except TransactionError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to commit import: {str(e)}'}), 500

