import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from unittest.mock import patch
import requests

def test_service_to_service_api_call():
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"result": "ok"}
        response = requests.post("http://service-b/api/endpoint", json={"foo": "bar"})
        assert response.status_code == 200
        assert response.json()["result"] == "ok" 