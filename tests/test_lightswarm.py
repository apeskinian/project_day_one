"""
Unit tests for the Lightswarm serial interface module.

This test suite verifies:
- Platform‑specific USB port detection (Windows, macOS, Linux).
- Mapping of human‑readable command names to Lightswarm command codes.
- Validation logic for numeric values with and without brackets.
- Construction of extra payload data for supported actions
    (level, fade, set_pseudo).
- End‑to‑end payload building, including checksum calculation, framing, and
    escaping.
- Thread‑safe serial communication behavior in send_payload:
  * Successful reconnection and write.
  * Handling of SerialException during connection, write, and close.
  * Behavior with existing open connections.
  * Propagation of unexpected exceptions.

The tests use pytest and unittest.mock to isolate functionality and
simulate serial port interactions, ensuring correctness without hardware.
"""
# Standard imports:
from unittest.mock import patch, MagicMock
# Third party imports:
import pytest
# Local imports:
import lightswarm


def test_get_usb_port_windows(monkeypatch):
    """
    Ensure Windows platform resolves to COM4 USB port.
    """
    # Arrange
    monkeypatch.setattr(lightswarm.platform, 'system', lambda: 'Windows')
    # Assert
    assert lightswarm.get_usb_port() == 'COM4'


def test_get_usb_port_darwin(monkeypatch):
    """
    Ensure macOS (Darwin) platform resolves to /dev/tty.usbmodem1101.
    """
    # Arrange
    monkeypatch.setattr(lightswarm.platform, 'system', lambda: 'Darwin')
    # Assert
    assert lightswarm.get_usb_port() == '/dev/tty.usbmodem1101'


def test_get_usb_port_linux(monkeypatch):
    """
    Ensure Linux platform resolves to /dev/ttyUSB0.
    """
    # Arrange
    monkeypatch.setattr(lightswarm.platform, 'system', lambda: 'Linux')
    # Assert
    assert lightswarm.get_usb_port() == '/dev/ttyUSB0'


def test_get_command_code_valid():
    """
    Verify that valid command names map to their correct hex codes.
    """
    # Assert
    assert lightswarm.get_command_code('fade') == 0x23
    assert lightswarm.get_command_code('ping_request') == 0x02


def test_get_command_code_invalid():
    """
    Verify that an unknown command name raises ValueError with a clear message.
    """
    # Act
    with pytest.raises(ValueError) as error:
        lightswarm.get_command_code('apeskinian')
    # Assert
    assert 'Unknown action: apeskinian' in str(error)


def test_check_value_no_input():
    """
    Verify that None input raises ValueError indicating a missing
    required value.
    """
    # Act
    with pytest.raises(ValueError) as error:
        lightswarm.check_value(None, 'test')
    # Assert
    assert 'Action: "test" is missing a required value' in str(error)


def test_check_value_non_integer():
    """
    Verify that non-integer input raises TypeError with a descriptive message.
    """
    # Act
    with pytest.raises(TypeError) as error:
        lightswarm.check_value('not an integer', 'test')
    # Assert
    assert 'Value for "test" must be an integer.' in str(error)


def test_check_value_with_invalid_bracket():
    """
    Verify that a bracket list of invalid length raises ValueError.
    """
    # Act
    with pytest.raises(ValueError) as error:
        lightswarm.check_value(100, 'test', [10])
    # Assert
    assert 'Value bracket needs exactly 2 values.' in str(error)


def test_check_value_not_in_bracket():
    """
    Verify that an integer outside the allowed bracket range raises ValueError.
    """
    # Act
    with pytest.raises(ValueError) as error:
        lightswarm.check_value(50, 'test', [100, 120])
    # Assert
    assert 'Value for "test" must be between 100-120' in str(error)


def test_check_value_with_valid_inputs_with_bracket():
    """
    Verify that a valid integer within the bracket range is returned unchanged.
    """
    # Act
    returnedValue = lightswarm.check_value(50, 'test', [0, 100])
    # Assert
    assert returnedValue == 50


def test_get_extra_payload_data_with_level():
    """
    Test extra payload data for level is correctly added to the payload.
    """
    # Arrange
    command = {
        'name': 'test',
        'channels': [10],
        'action': 'level',
        'level': 100,
    }
    # Act
    extra_payload = lightswarm.get_extra_payload_data(command)
    # Assert
    assert extra_payload == [100]


def test_get_extra_payload_data_with_fade():
    """
    Verify that 'fade' action adds level, interval, and step values to the
    payload.
    """
    # Arrange
    command = {
        'name': 'test',
        'channels': [10],
        'action': 'fade',
        'level': 10,
        'interval': 20,
        'step': 30,
    }
    # Act
    extra_payload = lightswarm.get_extra_payload_data(command)
    # Assert
    assert extra_payload == [10, 20, 30]


def test_get_extra_payload_data_with_set_pseudo():
    """
    Verify that 'set_pseudo' action adds the pseudo address split into two
    bytes.
    """
    # Arrange
    command = {
        'name': 'test',
        'channels': [10],
        'action': 'set_pseudo',
        'pseudo_address': 200,
    }
    # Act
    extra_payload = lightswarm.get_extra_payload_data(command)
    first_byte = (200 >> 8) & 0xFF
    second_byte = 200 & 0xFF
    # Assert
    assert extra_payload == [first_byte, second_byte]


@patch('lightswarm.send_payload')
def test_lightswarm_command_builds_payload(mock_send):
    """
    Verify that lightswarm_command builds a correct framed payload for 'level'
    action and passes it to send_payload().
    """
    # Arrange
    command = {
        'name': 'test',
        'channels': [10],
        'action': 'level',
        'level': 100,
    }
    # Act
    lightswarm.lightswarm_command(command)
    # Assert
    mock_send.assert_called_once()
    payload = mock_send.call_args[0][0]
    assert payload == [0xC0, 0x00, 0x0A, 0x22, 0x64, 0x4C, 0xC0]


def test_build_payload_invalid_byte():
    """
    Verify that build_payload raises ValueError if a byte exceeds 0–255 range.
    """
    # Act
    with pytest.raises(ValueError) as error:
        lightswarm.build_payload([300])
    # Assert
    assert '8 bit value expected but not received.' in str(error)


@patch('lightswarm.send_payload')
def test_build_payload_with_END_matching_byte(mock_send):
    """
    Verify that build_payload escapes END (0xC0) correctly in the payload.
    """
    # Arrange
    END = 0xC0
    byte_array = [END]
    # Act
    lightswarm.build_payload(byte_array)
    # Assert
    mock_send.assert_called_once()
    payload = mock_send.call_args[0][0]
    assert payload == [END, 0xDB, 0xDC, END]


@patch('lightswarm.send_payload')
def test_build_payload_with_ESC_matching_byte(mock_send):
    """
    Verify that build_payload escapes ESC (0xDB) correctly in the payload.
    """
    # Arrange
    ESC = 0xDB
    byte_array = [ESC]
    # Act
    lightswarm.build_payload(byte_array)
    # Assert
    mock_send.assert_called_once()
    payload = mock_send.call_args[0][0]
    assert payload == [0xC0, ESC, 0xDD, 0xC0]


@patch('lightswarm.serial.Serial')
def test_send_payload_success(mock_serial, caplog):
    """
    Verify that send_payload reconnects when lightswarm is None, logs INFO,
    and writes the payload bytes to the serial port.
    """
    # Arrange
    mock_instance = MagicMock()
    mock_instance.is_open = True
    mock_serial.return_value = mock_instance
    payload = [0xC0, 0x00, 0x0A, 0x22, 0x64, 0x4C, 0xC0]
    lightswarm.lightswarm = None
    # Act
    with caplog.at_level('INFO'):
        lightswarm.send_payload(payload)
    # Assert
    assert 'INFO: reconnected to lightswarm.' in caplog.text
    mock_serial.assert_called_once_with(
        lightswarm.ser, lightswarm.baud, lightswarm.timeout
    )
    mock_instance.write.assert_called_once_with(bytes(payload))


@patch('lightswarm.serial.Serial')
def test_send_payload_serial_exception(mock_serial, caplog):
    """
    Verify that a SerialException during connection logs an error and resets
    lightswarm to None.
    """
    # Arrange
    mock_serial.side_effect = lightswarm.serial.SerialException('Port error')
    payload = [0xC0, 0x00, 0x0A, 0x22, 0x64, 0x4C, 0xC0]
    lightswarm.lightswarm = None
    # Act
    with caplog.at_level('ERROR'):
        lightswarm.send_payload(payload)
    # Assert
    assert "ERROR: Serial error: Port error" in caplog.text
    assert lightswarm.lightswarm is None


@patch('lightswarm.serial.Serial')
def test_send_payload_existing_connection(mock_serial, caplog):
    """
    Verify that with an existing open connection, send_payload writes directly
    without attempting reconnection.
    """
    # Arrange
    mock_lightswarm = MagicMock()
    mock_lightswarm.is_open = True
    lightswarm.lightswarm = mock_lightswarm
    payload = [0xC0, 0x00, 0x0A, 0x22, 0x64, 0x4C, 0xC0]
    # Act
    with caplog.at_level("INFO"):
        lightswarm.send_payload(payload)
    # Assert
    assert "INFO: reconnected to leds." not in caplog.text
    mock_lightswarm.write.assert_called_once_with(bytes(payload))
    mock_serial.assert_not_called()


@patch("lightswarm.serial.Serial")
def test_send_payload_unexpected_exception(mock_serial, caplog):
    """
    Verify that unexpected exceptions are logged and re-raised by send_payload.
    """
    # Arrange
    lightswarm.lightswarm = None
    mock_serial.side_effect = Exception("Something went wrong")
    payload = [0xC0, 0x00, 0x0A, 0x22, 0x64, 0x4C, 0xC0]
    # Act
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception, match="Something went wrong"):
            lightswarm.send_payload(payload)
    # Assert
    assert "ERROR: Unexpected error: Something went wrong" in caplog.text


@patch("lightswarm.serial.Serial")
def test_send_payload_serial_exception_with_open_lightswarm(
    mock_serial, caplog
):
    """
    Verify that a SerialException during write closes the connection,
    logs error, and resets lightswarm to None.
    """
    # Arrange
    mock_lightswarm = MagicMock()
    mock_lightswarm.is_open = True
    mock_lightswarm.write.side_effect = lightswarm.serial.SerialException(
        "Write error"
    )
    lightswarm.lightswarm = mock_lightswarm
    mock_serial.return_value = mock_lightswarm
    payload = [0xC0, 0x00, 0x0A, 0x22, 0x64, 0x4C, 0xC0]
    # Act
    with caplog.at_level("ERROR"):
        lightswarm.send_payload(payload)
    # Assert
    mock_lightswarm.close.assert_called_once()
    assert lightswarm.lightswarm is None
    assert "ERROR: Serial error: Write error" in caplog.text


@patch("lightswarm.serial.Serial")
def test_send_payload_close_raises_serial_exception(mock_serial, caplog):
    """
    Verify that if closing the connection also raises SerialException,
    lightswarm is still reset to None and error is logged.
    """
    # Arrange
    mock_lightswarm = MagicMock()
    mock_lightswarm.is_open = True
    mock_lightswarm.write.side_effect = lightswarm.serial.SerialException(
        "Write error"
    )
    mock_lightswarm.close.side_effect = lightswarm.serial.SerialException(
        "Close failed"
    )
    lightswarm.lightswarm = mock_lightswarm
    mock_serial.return_value = mock_lightswarm
    payload = [0xC0, 0x00, 0x0A, 0x22, 0x64, 0x4C, 0xC0]
    # Act
    with caplog.at_level("ERROR"):
        lightswarm.send_payload(payload)
    # Assert
    mock_lightswarm.close.assert_called_once()
    assert lightswarm.lightswarm is None
