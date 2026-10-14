import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.providers import DatabricksProvider, OllamaProvider


client = TestClient(app)

def test_health():
    assert client.get('/healthz').status_code == 200

def test_mock_chat():
    r = client.post('/v1/chat', json={'messages':[{'role':'user','content':'hello'}]})
    assert r.status_code == 200
    assert 'Mock response' in r.json()['output']


def test_agent_uses_configured_provider():
    r = client.post('/v1/agent', json={'task': 'Summarize Kafka offsets.'})
    assert r.status_code == 200
    assert 'Summarize Kafka offsets.' in r.json()['output']


def test_ollama_provider():
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return json.dumps({"message": {"content": "Ollama response"}}).encode()

    with patch("app.providers.urlopen", return_value=FakeResponse()) as open_url:
        assert OllamaProvider().converse([{"role": "user", "content": "hello"}]) == "Ollama response"

    request = open_url.call_args.args[0]
    assert request.full_url.endswith("/api/chat")
    assert json.loads(request.data)["stream"] is False


def test_databricks_provider():
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "Databricks response"}}]}).encode()

    with patch("app.providers.urlopen", return_value=FakeResponse()) as open_url:
        with patch.object(settings, "databricks_host", "https://workspace.cloud.databricks.com"), patch.object(settings, "databricks_token", "token"), patch.object(settings, "databricks_endpoint", "foundation-model"):
            assert DatabricksProvider().converse([{"role": "user", "content": "hello"}]) == "Databricks response"

    request = open_url.call_args.args[0]
    assert request.full_url.endswith("/serving-endpoints/foundation-model/invocations")
    assert request.get_header("Authorization") == "Bearer token"
