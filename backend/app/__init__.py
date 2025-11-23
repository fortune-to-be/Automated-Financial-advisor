from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from app.config import get_config
from app.database import db
from app.routes import auth_bp
from app.routes.admin import admin_bp

migrate = Migrate()
jwt = JWTManager()

def create_app(config=None):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    if config is None:
        config = get_config()
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    @app.route('/health', methods=['GET'])
    def health():
        return {'status': 'healthy'}, 200
    
    @app.route('/api/advisor', methods=['GET'])
    def get_advisor():
        return {
            'name': 'Automated Financial Advisor',
            'version': '1.0.0',
            'status': 'active'
        }, 200
    
    # Create tables and context
    with app.app_context():
        db.create_all()
    
    return app
