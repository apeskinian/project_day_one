"""
Serial interface for controlling Lightswarm lighting devices.

This module provides:
- Automatic detection of the correct USB port based on platform.
- Mapping of human-readable actions to Lightswarm command codes.
- Validation helpers for command values.
- Functions to build and send byte-encoded payloads with checksum and framing.
- Thread-safe serial communication with automatic reconnection.

- NOTE: CURRENTLY UNTESTED!!
"""

# Standard imports:
import serial
import platform
import threading
from functools import reduce

# Serial configuration
baud = 115200
lightswarm = None
serial_lock = threading.Lock()
timeout = 1


def get_usb_port():
    """
    Determine the appropriate USB port for the Lightswarm based on the host
    platform. Check designated port on hardware and change as necessary.

    Return examples:
        str: The serial port path:
        - 'COM4' for Windows
        - '/dev/tty.usbmodem1101' for macOS
        - '/dev/ttyUSB0' for Linux
    """
    if platform.system() == 'Windows':
        return 'COM4'
    elif platform.system() == 'Darwin':
        return '/dev/tty.usbmodem1101'
    else:
        return '/dev/ttyUSB0'


ser = get_usb_port()


def get_command_code(action):
    """
    Map an action string to its corresponding Lightswarm command code.
    Args:
        action (str): Human-readable action name (e.g., 'on', 'off', 'fade').
    Returns:
        int: The command code as a single byte value.
    Raises:
        ValueError: If the provided action is not recognized.
    """
    codes = {
        'nothing': 0x00,
        'reset': 0x01,
        'ping_request': 0x02,
        'ping_response': 0x03,
        'on': 0x20,  # implemented
        'off': 0x21,  # implemented
        'level': 0x22,  # implemented
        'fade': 0x23,  # implemented
        'set_pseudo': 0x25,  # implemented
        # 'erase_pseudo': 0x26,
        # 'media_function': 0x27,
        # 'event_start': 0x28,
        # 'event_stop': 0x29,
        # 'data_forward': 0x2A,
        # 'mech_command': 0x2B,
        # 'set_rgb': 0x2C,
        'toggle': 0x2D,
        # 'flash': 0x2E,
        # 'flash_rgb': 0x2F,
        # 'fade_multi': 0x30,
        # 'fade_rgb': 0x31,
        # 'config': 0x7E
    }
    try:
        return codes[action]
    except KeyError:
        raise ValueError(f'Unknown action: {action}')


def check_value(input, action, bracket=None):
    """
    Validate a numeric value for a given action.
    Args:
        input (int): The value to validate.
        action (str): The action name for context in error messages.
        bracket (list[int] | None): Optional [min, max] range for validation.
    Returns:
        int: The validated input value.
    Raises:
        ValueError: If the input is missing or outside the allowed range.
        TypeError: If the input is not an integer.
    """
    if input is None:
        raise ValueError(f'Action: "{action}" is missing a required value')
    if not isinstance(input, int):
        raise TypeError(f'Value for "{action}" must be an integer.')
    if bracket:
        if len(bracket) != 2:
            raise ValueError('Value bracket needs exactly 2 values.')
        if len(bracket) == 2:
            if not (bracket[0] <= input <= bracket[1]):
                raise ValueError(
                    f'Value for "{action}" must be between '
                    f'{bracket[0]}-{bracket[1]}. Value entered: {input}.'
                )
    return input


def get_extra_payload_data(command):
    """
    Build extra payload data depending on the action type.
    Args:
        command (dict): Command dictionary containing 'action' and optional
        fields like 'level', 'interval', 'step', 'pseudo_address'.
    Returns:
        list[int]: Extra payload bytes to append to the command.
    """
    action = command['action']
    extra_payload_data = []
    # Applying new level
    if action == 'level':
        new_level = command.get('level')
        extra_payload_data.append(check_value(new_level, action, [0, 255]))
    # Applying fade
    if action == 'fade':
        fade_level = command.get('level')
        fade_interval = command.get('interval')
        fade_step = command.get('step')
        extra_payload_data.append(check_value(fade_level, action, [0, 255]))
        extra_payload_data.append(check_value(fade_interval, action, [1, 255]))
        extra_payload_data.append(check_value(fade_step, action, [0, 255]))
    # Applying pseudo address
    if action == 'set_pseudo':
        pseudo_address = check_value(command.get('pseudo_address'), action)
        first_pseudo_address_byte = (pseudo_address >> 8) & 0xFF
        second_pseudo_address_byte = pseudo_address & 0xFF
        extra_payload_data.extend(
            [first_pseudo_address_byte, second_pseudo_address_byte]
        )

    return extra_payload_data


def lightswarm_command(command):
    """
    Construct and send a Lightswarm command for one or more channels.
    Args:
        command (dict): Command dictionary containing:
            - 'channels' (list[int]): Target channel addresses.
            - 'name' (str): Human-readable name for logging.
            - 'action' (str): Action to perform.
            - Optional fields depending on action (e.g., 'level', 'interval').
    Side Effects:
        Calls `build_payload()` to transmit.
    """
    for channel in command['channels']:
        byte_array = []
        # Split light address into 1 byte blocks
        first_address_byte = (channel >> 8) & 0xFF
        second_address_byte = channel & 0xFF
        # Create command as 1 byte block
        command_byte = get_command_code(command['action'])
        # Check for custom command data to add
        extra_payload_data = get_extra_payload_data(command)
        # Build byte_array
        byte_array.extend(
            [first_address_byte, second_address_byte, command_byte]
        )
        byte_array.extend(extra_payload_data)
        # Calculate checksum
        checksum_byte = reduce(lambda x, y: x ^ y, byte_array)
        byte_array.append(checksum_byte)
        # Build payload
        build_payload(byte_array)


def build_payload(byte_array):
    """
    Apply framing and escaping to a byte array to build a valid Lightswarm
    payload.
    Args:
        byte_array (list[int]): Raw command bytes including checksum.
    Raises:
        ValueError: If any byte is outside the 0–255 range.
    Side Effects:
        Calls `send_payload()` with the framed payload.
    """
    END = 0xC0
    ESC = 0xDB
    END_ESC = 0xDC
    ESC_ESC = 0xDD

    payload = [END]
    for byte in byte_array:
        if not (0 <= byte <= 255):
            raise ValueError('8 bit value expected but not received.')
        if byte == END:
            payload.extend([ESC, END_ESC])
        elif byte == ESC:
            payload.extend([ESC, ESC_ESC])
        else:
            payload.append(byte)
    payload.append(END)
    send_payload(payload)


def send_payload(payload):
    """
    Send a payload to the Lightswarm device over serial.
    Args:
        payload (list[int]): Fully framed payload bytes.
    Behavior:
        - Ensures thread-safe access to the serial connection.
        - Automatically reconnects if the serial connection is lost.
        - Logs errors and resets the connection if needed.
    Raises:
        Exception: Re-raises unexpected errors after logging.
    """
    global lightswarm
    try:
        with serial_lock:
            # Reconnect if lost
            if not lightswarm or not lightswarm.is_open:
                lightswarm = serial.Serial(ser, baud, timeout)
                print('INFO: reconnected to lightswarm.')
            # Send payload
            lightswarm.write(bytes(payload))
    except serial.SerialException as error:
        print(f'ERROR: Serial error: {error}')
        try:
            if lightswarm and lightswarm.is_open:
                lightswarm.close()
        except serial.SerialException:
            pass
        lightswarm = None
    except Exception as error:
        print(f'ERROR: Unexpected error: {error}')
        raise
