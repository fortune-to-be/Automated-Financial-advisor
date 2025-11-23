import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_get_advisor(client):
    """Test get advisor endpoint"""
    response = client.get('/api/advisor')
    assert response.status_code == 200
    assert 'name' in response.json
    assert response.json['name'] == 'Automated Financial Advisor'

def test_recommendations_post(client):
    """Test recommendations endpoint"""
    response = client.post('/api/recommendations', json={'user_profile': 'test'})
    assert response.status_code == 200
    assert 'recommendations' in response.json

def test_recommendations_no_data(client):
    """Test recommendations endpoint with no data"""
    response = client.post('/api/recommendations', json={})
    # Should handle empty data gracefully
    assert response.status_code in [200, 400]
