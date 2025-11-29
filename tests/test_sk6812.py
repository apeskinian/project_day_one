"""
Test suite for the `sk6812` LED strip control module.

This collection of unit tests validates platform detection, command encoding,
and payload transmission logic for SK6812 LED strips. The tests use pytest,
monkeypatching, and unittest.mock to isolate hardware dependencies and ensure
robust error handling.

Coverage includes:
- USB port resolution across operating systems (Windows, macOS/Darwin, Linux).
- Command code mapping for valid and invalid colour names.
- Payload construction via `sk6812_command`, ensuring correct colour,
    brightness, and effect fields.
- Serial communication through `send_payload`, including:
  * Successful connection and payload write.
  * Handling of `SerialException` during connection and write operations.
  * Reconnection logic when an existing serial connection is open.
  * Logging of INFO and ERROR messages for diagnostic clarity.
  * Graceful recovery when closing the serial port raises exceptions.
  * Propagation of unexpected exceptions.

Mocks:
- `serial.Serial` is patched to simulate hardware connections.
- `send_payload` is patched to validate payload construction without I/O.

These tests ensure that the `sk6812` module behaves predictably across
platforms, produces correct LED control payloads, and handles serial
communication errors gracefully.
"""
# Standard imports:
import json
from unittest.mock import patch, MagicMock
# Third party imports:
import pytest
# Local imports:
import sk6812


def test_get_usb_port_windows(monkeypatch):
    """
    Ensure Windows platform resolves to COM4 USB port.
    """
    # Arrange
    monkeypatch.setattr(sk6812.platform, 'system', lambda: 'Windows')
    # Assert
    assert sk6812.get_usb_port() == 'COM4'


def test_get_usb_port_darwin(monkeypatch):
    """
    Ensure macOS (Darwin) platform resolves to /dev/tty.usbmodem1101.
    """
    # Arrange
    monkeypatch.setattr(sk6812.platform, 'system', lambda: 'Darwin')
    # Assert
    assert sk6812.get_usb_port() == '/dev/tty.usbmodem1101'


def test_get_usb_port_linux(monkeypatch):
    """
    Ensure Linux platform resolves to /dev/ttyUSB0.
    """
    # Arrange
    monkeypatch.setattr(sk6812.platform, 'system', lambda: 'Linux')
    # Assert
    assert sk6812.get_usb_port() == '/dev/ttyUSB0'


def test_get_command_code_valid():
    """
    Verify valid colour names map to correct RGBW tuples.
    """
    # Assert
    assert sk6812.get_command_code('red') == (255, 0, 0, 0)
    assert sk6812.get_command_code('warm') == (253, 244, 220, 0)


def test_get_command_code_invalid():
    """
    Verify invalid colour names raise ValueError.
    """
    # Assert
    with pytest.raises(ValueError):
        sk6812.get_command_code('rainbow')


@patch('sk6812.send_payload')
def test_sk6812_command_builds_payload(mock_send):
    """
    Ensure sk6812_command builds payload with correct colour, brightness,
    and effect.
    """
    # Arrange
    command = {
        'name': 'test',
        'channels': [0, 1, 2],
        'colour': 'warm',
        'brightness': 0.5,
        'effect': 'on'
    }
    # Act
    sk6812.sk6812_command(command)
    # Assert
    mock_send.assert_called_once()
    payload = mock_send.call_args[0][0]
    assert payload[0]['set'] == (253, 244, 220, 0)
    assert payload[0]['brightness'] == 0.5
    assert payload[0]['effect'] == 'on'


@patch('sk6812.serial.Serial')
def test_send_payload_success(mock_serial, caplog):
    """
    Verify successful payload send logs reconnection and writes JSON to serial.
    """
    # Arrange
    mock_instance = MagicMock()
    mock_instance.is_open = True
    mock_serial.return_value = mock_instance
    payload = [
        {
            "index": 0,
            "set": (255, 0, 0, 0),
            "brightness": 1.0,
            "effect": "on"
        }]
    sk6812.ledstrip = None
    # Act
    with caplog.at_level('INFO'):
        sk6812.send_payload(payload)
    # Assert
    assert 'INFO: reconnected to leds.' in caplog.text
    mock_serial.assert_called_once_with(sk6812.ser, sk6812.baud)
    mock_instance.write.assert_called_once()
    written = mock_instance.write.call_args[0][0].decode().strip()
    decoded = json.loads(written)
    assert decoded == [
        {"index": 0, "set": [255, 0, 0, 0], "brightness": 1.0, "effect": "on"}
    ]


@patch('sk6812.serial.Serial')
def test_send_payload_serial_exception(mock_serial, caplog):
    """
    Verify SerialException during connection logs error and resets ledstrip.
    """
    # Arrange
    mock_serial.side_effect = sk6812.serial.SerialException('Port error')
    payload = [
        {
            "index": 0,
            "set": (255, 0, 0, 0),
            "brightness": 1.0,
            "effect": "on"
        }]
    sk6812.ledstrip = None
    # Act
    with caplog.at_level('ERROR'):
        sk6812.send_payload(payload)
    # Assert
    assert "ERROR: Serial error: Port error" in caplog.text
    assert sk6812.ledstrip is None


@patch('sk6812.serial.Serial')
def test_send_payload_existing_connection(mock_serial, caplog):
    """
    Verify existing open connection writes payload without reconnection.
    """
    # Arrange
    mock_ledstrip = MagicMock()
    mock_ledstrip.is_open = True
    sk6812.ledstrip = mock_ledstrip
    payload = [{
        "index": 0,
        "set": (255, 0, 0, 0),
        "brightness": 1.0,
        "effect": "on"
    }]
    # Act
    with caplog.at_level("INFO"):
        sk6812.send_payload(payload)
    # Assert
    assert "INFO: reconnected to leds." not in caplog.text
    mock_ledstrip.write.assert_called_once()
    mock_serial.assert_not_called()


@patch("sk6812.serial.Serial")
def test_send_payload_unexpected_exception(mock_serial, caplog):
    """
    Verify unexpected exceptions propagate and log error message.
    """
    # Arrange
    sk6812.ledstrip = None
    mock_serial.side_effect = Exception("Something went wrong")
    payload = [{
        "index": 0,
        "set": (255, 0, 0, 0),
        "brightness": 1.0,
        "effect": "on"
    }]
    # Act
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception, match="Something went wrong"):
            sk6812.send_payload(payload)
    # Assert
    assert "ERROR: Unexpected error: Something went wrong" in caplog.text


@patch("sk6812.serial.Serial")
def test_send_payload_serial_exception_with_open_ledstrip(mock_serial, caplog):
    """
    Verify SerialException during write closes connection, logs error, and
    resets ledstrip.
    """
    # Arrange
    mock_ledstrip = MagicMock()
    mock_ledstrip.is_open = True
    mock_ledstrip.write.side_effect = sk6812.serial.SerialException(
        "Write error"
    )
    sk6812.ledstrip = mock_ledstrip
    mock_serial.return_value = mock_ledstrip
    payload = [{
        "index": 0,
        "set": (255, 0, 0, 0),
        "brightness": 1.0,
        "effect": "on"
    }]
    # Act
    with caplog.at_level("ERROR"):
        sk6812.send_payload(payload)
    # Assert
    mock_ledstrip.close.assert_called_once()
    assert sk6812.ledstrip is None
    assert "ERROR: Serial error: Write error" in caplog.text


@patch("sk6812.serial.Serial")
def test_send_payload_close_raises_serial_exception(mock_serial, caplog):
    """
    Verify SerialException during close still resets ledstrip and logs error.
    """
    # Arrange
    mock_ledstrip = MagicMock()
    mock_ledstrip.is_open = True
    mock_ledstrip.write.side_effect = sk6812.serial.SerialException(
        "Write error"
    )
    mock_ledstrip.close.side_effect = sk6812.serial.SerialException(
        "Close failed"
    )
    sk6812.ledstrip = mock_ledstrip
    mock_serial.return_value = mock_ledstrip
    payload = [{
        "index": 0,
        "set": (255, 0, 0, 0),
        "brightness": 1.0,
        "effect": "on"
    }]
    # Act
    with caplog.at_level("ERROR"):
        sk6812.send_payload(payload)
    # Assert
    mock_ledstrip.close.assert_called_once()
    assert sk6812.ledstrip is None
