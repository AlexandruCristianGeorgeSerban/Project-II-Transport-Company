import pytest

def test_guest_home_page(client):
    """7. INTERFAȚĂ: Verifică pagina principală (Guest)."""
    response = client.get('/')
    assert response.status_code == 200

def test_login_page_renders(client):
    """8. INTERFAȚĂ: Verifică randarea paginii de Login."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"password" in response.data.lower()

def test_register_page_renders(client):
    """9. INTERFAȚĂ: Verifică randarea paginii de Register."""
    response = client.get('/register')
    assert response.status_code == 200

def test_login_invalid_credentials(client):
    """10. INTERFAȚĂ: Verifică răspunsul la un login eșuat."""
    response = client.post('/login', data={"username": "fake_user", "password": "wrong_password"}, follow_redirects=True)
    assert response.status_code == 200

def test_logout_redirects_to_login(client):
    """11. INTERFAȚĂ: Verifică dacă logout curăță sesiunea și te duce la login."""
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"login" in response.data.lower()

def test_admin_dashboard_redirects_unauthenticated(client):
    """12. INTERFAȚĂ: Protecție rută admin pentru utilizatori nelogați."""
    response = client.get('/dashboard')
    assert response.status_code == 302

def test_driver_portal_redirects_unauthenticated(client):
    """13. INTERFAȚĂ: Protecție rută șoferi pentru utilizatori nelogați."""
    response = client.get('/driver_portal')
    assert response.status_code == 302

def test_requests_page_redirects_unauthenticated(client):
    """14. INTERFAȚĂ: Protecție rută logistică pentru intruși."""
    response = client.get('/requests')
    assert response.status_code == 302

def test_drivers_page_redirects_unauthenticated(client):
    """15. INTERFAȚĂ: Protecție rută resurse umane."""
    response = client.get('/drivers')
    assert response.status_code == 302

def test_fleet_page_redirects_unauthenticated(client):
    """16. INTERFAȚĂ: Protecție rută flotă."""
    response = client.get('/fleet')
    assert response.status_code == 302