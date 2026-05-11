import pytest
from app.routes.driver_routes import remove_diacritics
from app.controllers.request_controller import RequestController
from app.models.user_model import UserModel
from werkzeug.security import check_password_hash

def test_remove_diacritics():
    """1. ALGORITM: Verifică funcția de curățare a diacriticelor pentru export PDF/CSV."""
    assert remove_diacritics("șțîăâ") == "stiaa"
    assert remove_diacritics("ȘȚÎĂÂ") == "STIAA"
    assert remove_diacritics("București") == "Bucuresti"
    assert remove_diacritics(None) == ""

def test_request_auto_price_calculation(app):
    """2. ALGORITM: Verifică logica matematică de calcul automat al prețului."""
    with app.app_context():
        controller = RequestController()
        
       
        res = controller.add_new_request(
            r_id="REQ-TEST-ALGO", client="Test", c_type="Gen", desc="D", 
            weight=10.0, volume=20.0, pickup="A", delivery="B", 
            date="2026-05-11", status="Draft"
        )
        assert res["success"] == True
        assert "205.0" in res["message"]

def test_send_price_offer_negative_value(app):
    """3. ALGORITM: Verifică logica de validare a unei oferte de preț negative sau zero."""
    with app.app_context():
        controller = RequestController()
        res = controller.send_price_offer("REQ-123", "-50")
        assert res["success"] == False
        assert "mai mare decât 0" in res["message"]

def test_send_price_offer_invalid_format(app):
    """4. ALGORITM: Verifică protecția algoritmului la input-uri text în loc de numere."""
    with app.app_context():
        controller = RequestController()
        res = controller.send_price_offer("REQ-123", "o_suta_de_dolari")
        assert res["success"] == False
        assert "invalid" in res["message"]

def test_user_password_hashing(app):
    """5. ALGORITM: Verifică algoritmul de criptare (hashing) la crearea parolelor."""
    with app.app_context():
        model = UserModel()
        model.register_user("test_hacker", "parola_secreta", "Test", "H", "hack@test.com", "123", "2000-01-01")
        user = model.get_user_for_login("test_hacker")
        
        assert user is not None
        
        assert user["password_hash"] != "parola_secreta"
        assert check_password_hash(user["password_hash"], "parola_secreta") == True

def test_negotiation_logic_higher_price(app):
    """6. ALGORITM: Verifică logica matematică a negocierii (noua ofertă trebuie să fie STRICT mai mică)."""
    with app.app_context():
        controller = RequestController()
        controller.add_new_request("REQ-NEG", "C", "G", "D", 10.0, 10.0, "A", "B", "2026-01-01", "Pending")
        
        res = controller.handle_negotiation_offer("REQ-NEG", "staff1", "Oferta", 500.0)
        assert res["success"] == False
        assert "STRICT MAI MICĂ" in res["message"]