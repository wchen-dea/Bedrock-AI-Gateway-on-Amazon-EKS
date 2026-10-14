from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_health():
    assert client.get('/healthz').status_code == 200

def test_mock_chat():
    r = client.post('/v1/chat', json={'messages':[{'role':'user','content':'hello'}]})
    assert r.status_code == 200
    assert 'Mock response' in r.json()['output']
