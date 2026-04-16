from flask import Flask
from app.routes.auth_routes import auth_bp
from app.routes.dashboard_routes import dashboard_bp
from app.models.user_model import UserModel
from app.routes.fleet_routes import fleet_bp
from app.routes.driver_routes import driver_bp
from app.routes.allocation_routes import allocation_bp
from app.routes.request_routes import request_bp
from app.routes.report_routes import report_bp
from app.routes.customer_routes import customer_bp
from app.routes.admin_support_routes import admin_support_bp


def create_app() -> Flask:
    """Initialize the core application, register blueprints, and setup DB."""
    app = Flask(__name__)
    
    # Secret key is required for sessions and flash messages
    app.secret_key = "transport_company_super_secret_key"
    
    # Register the authentication blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(fleet_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(allocation_bp)
    app.register_blueprint(request_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_support_bp)

    
    # Initialize the database table for users
    user_db = UserModel()
    user_db.create_table()
    
    return app