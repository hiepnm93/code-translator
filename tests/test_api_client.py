"""Tests for NLLB API client."""
from unittest.mock import patch, MagicMock
from translator.api_client import NLLBClient


def _mock_response(data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = data
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


@patch("translator.api_client.requests.post")
def test_translate_single(mock_post):
    mock_post.return_value = _mock_response({"translatedText": "Xin chào"})
    client = NLLBClient("http://localhost:5000")
    result = client.translate("你好", "zh", "vi")
    assert result == "Xin chào"


@patch("translator.api_client.requests.post")
def test_translate_batch(mock_post):
    mock_post.return_value = _mock_response({"translatedTexts": ["Xin chào", "Thế giới"]})
    client = NLLBClient("http://localhost:5000")
    results = client.translate_batch(["你好", "世界"], "zh", "vi")
    assert results == ["Xin chào", "Thế giới"]


@patch("translator.api_client.requests.post")
def test_translate_batch_chunking(mock_post):
    mock_post.return_value = _mock_response({"translatedTexts": ["text"] * 2})
    client = NLLBClient("http://localhost:5000", batch_size=2)
    texts = ["a", "b", "c", "d"]
    results = client.translate_batch(texts, "zh", "vi")
    assert len(results) == 4
    assert mock_post.call_count == 2


@patch("translator.api_client.requests.post")
def test_retry_on_failure(mock_post):
    mock_post.side_effect = [
        Exception("Connection refused"),
        _mock_response({"translatedText": "OK"}),
    ]
    client = NLLBClient("http://localhost:5000", retries=3)
    result = client.translate("test", "en", "vi")
    assert result == "OK"
    assert mock_post.call_count == 2


@patch("translator.api_client.requests.post")
def test_detect(mock_post):
    mock_post.return_value = _mock_response({"language": "zho_Hans", "confidence": 0.95})
    client = NLLBClient("http://localhost:5000")
    lang, conf = client.detect("你好")
    assert lang == "zho_Hans"
    assert conf == 0.95
