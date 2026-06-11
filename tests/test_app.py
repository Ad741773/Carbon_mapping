import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    r = client.get('/api/health')
    assert r.status_code == 200

def test_register(client):
    r = client.post('/api/auth/register', json={
        'name': 'Test User',
        'email': 'test@test.com',
        'password': 'Test@1234'
    })
    assert r.status_code in [200, 201, 409]

def test_login_fail(client):
    r = client.post('/api/auth/login', json={
        'email': 'wrong@test.com',
        'password': 'wrongpass'
    })
    assert r.status_code == 401
