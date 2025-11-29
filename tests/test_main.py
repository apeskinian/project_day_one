"""
Unit tests for the FastAPI lighting control service.

This test suite verifies:
- Static file serving and root index endpoint behaviour.
- Correct handling of Lightswarm commands, including success and error cases.
- Correct handling of SK6812 LED strip commands, including success and error
cases.

Hardware‑dependent functions (`lightswarm_command` and `sk6812_command`) are
mocked to ensure tests run safely and deterministically without requiring
physical devices. The FastAPI TestClient is used to simulate HTTP requests
and validate responses.
"""
# Standard imports:
import os
# Third party imports:
from fastapi.testclient import TestClient
from unittest.mock import patch
# Local imports:
from main import app

# Set up test client
client = TestClient(app)


def test_serve_index(tmp_path, monkeypatch):
    """
    Test serving the index.html file at the root endpoint.

    - Creates a temporary `static/index.html` file.
    - Monkeypatches `os.path.join` to point to the temp file.
    - Verifies that GET `/` returns a 200 response and contains the test HTML.
    """
    # Arrange
    static_dir = tmp_path / 'static'
    static_dir.mkdir()
    index_file = static_dir / 'index.html'
    index_file.write_text('<html>Test</html>')
    monkeypatch.setattr(os.path, 'join', lambda *args: str(index_file))
    # Act
    response = client.get('/')
    # Assert
    assert response.status_code == 200
    assert 'Test' in response.text


@patch('main.lightswarm_command')
def test_lightswarm_success(mock_command):
    """
    Test the /lightswarm endpoint with a valid payload.

    - Mocks `lightswarm_command` to succeed (no exception).
    - Sends a POST request with a sample LightswarmCommand payload.
    - Verifies that the response is 200 and returns {'status': 'Success'}.
    - Ensures the mocked command was called once.
    """
    # Arrange
    mock_command.return_value = None
    payload = {
        'name': 'test',
        'channels': [1, 2],
        'action': 'on',
        'level': 50,
    }
    # Act
    response = client.post('/lightswarm', json=payload)
    # Assert
    assert response.status_code == 200
    assert response.json() == {'status': 'Success'}
    mock_command.assert_called_once()


@patch('main.lightswarm_command')
def test_lightswarm_error(mock_command):
    """
    Test the /lightswarm endpoint when the command raises an exception.

    - Mocks `lightswarm_command` to raise a hardware failure exception.
    - Sends a POST request with a sample payload.
    - Verifies that the response is 200 and contains an
    'Error:' status message.
    """
    # Arrange
    mock_command.side_effect = Exception('Hardware failure')
    payload = {
        'name': 'test',
        'channels': [4],
        'action': 'on',
        'level': 80,
    }
    # Act
    response = client.post('/lightswarm', json=payload)
    # Assert
    assert response.status_code == 200
    assert 'Error:' in response.json()['status']


@patch('main.sk6812_command')
def test_sk6812_success(mock_command):
    """
    Test the /sk6812 endpoint with a valid payload.

    - Mocks `sk6812_command` to succeed (no exception).
    - Sends a POST request with a sample SK6812Command payload.
    - Verifies that the response is 200 and returns {'status': 'Success'}.
    - Ensures the mocked command was called once.
    """
    # Arrange
    mock_command.return_value = None
    payload = {
        'name': 'test',
        'channels': [1, 2],
        'colour': '(12, 34, 56, 78)',
        'brightness':  0.5,
        'effect': 'on',
    }
    # Act
    response = client.post('/sk6812', json=payload)
    # Assert
    assert response.status_code == 200
    assert response.json() == {'status': 'Success'}
    mock_command.assert_called_once()


@patch('main.sk6812_command')
def test_sk6812_error(mock_command):
    """
    Test the /sk6812 endpoint when the command raises an exception.

    - Mocks `sk6812_command` to raise a hardware failure exception.
    - Sends a POST request with a sample payload.
    - Verifies that the response is 200 and contains an
    'Error:' status message.
    """
    # Arrange
    mock_command.side_effect = Exception('Hardware failure')
    payload = {
        'name': 'test',
        'channels': [1, 2],
        'colour': '(12, 34, 56, 78)',
        'brightness':  0.5,
        'effect': 'on',
    }
    # Act
    response = client.post('/sk6812', json=payload)
    # Assert
    assert response.status_code == 200
    assert 'Error:' in response.json()['status']
