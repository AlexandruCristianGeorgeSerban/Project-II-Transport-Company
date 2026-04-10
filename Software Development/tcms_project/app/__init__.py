from flask import Flask
from app.routes.auth_routes import auth_bp
from app.routes.dashboard_routes import dashboard_bp
from app.routes.fleet_routes import fleet_bp  # <-- AICI importam flota
from app.models.user_model import UserModel

def create_app() -> Flask:
    """Initialize the core application, register blueprints, and setup DB."""
    app = Flask(__name__)
    app.secret_key = "transport_company_super_secret_key"
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(fleet_bp)
    
    # Initialize the database table for users
    user_db = UserModel()
    user_db.create_table()
    
    return app