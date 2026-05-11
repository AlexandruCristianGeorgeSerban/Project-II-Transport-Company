import os
import tempfile
import pytest
from app import create_app

from app.models import user_model, driver_model, request_model

@pytest.fixture
def app():
    """Creeaza o aplicatie Flask pentru teste cu o baza de date fantoma."""
    
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)  
    
    original_user_db = user_model.DB_PATH
    original_driver_db = getattr(driver_model, 'DB_PATH', "instance/database.sqlite")
    original_req_db = getattr(request_model, 'DB_PATH', "instance/database.sqlite")
    
    user_model.DB_PATH = db_path
    driver_model.DB_PATH = db_path
    request_model.DB_PATH = db_path
    
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    # Creăm tabelele în baza de date fantomă
    with app.app_context():
        user_model.UserModel().create_table()
        driver_model.DriverModel().create_table()
        request_model.RequestModel().create_table()

    yield app

    user_model.DB_PATH = original_user_db
    driver_model.DB_PATH = original_driver_db
    request_model.DB_PATH = original_req_db

    try:
        os.unlink(db_path)
    except PermissionError:
        pass

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()