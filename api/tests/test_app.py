from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint():
    response = TestClient(app).get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert data['synthetic_data_only'] is True
    assert 'not diagnosis' in data['clinical_disclaimer']
