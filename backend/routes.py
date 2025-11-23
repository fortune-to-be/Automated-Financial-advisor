from flask import Blueprint, jsonify, request

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/advisor', methods=['GET'])
def get_advisor():
    """Get advisor information"""
    return jsonify({
        'name': 'Automated Financial Advisor',
        'version': '1.0.0',
        'status': 'active'
    }), 200

@api_bp.route('/recommendations', methods=['POST'])
def get_recommendations():
    """Generate financial recommendations based on user profile"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Placeholder for recommendation logic
    recommendations = {
        'recommendations': [
            'Consider diversifying your portfolio',
            'Review your emergency fund',
            'Evaluate your insurance coverage'
        ],
        'risk_level': 'medium'
    }
    
    return jsonify(recommendations), 200
