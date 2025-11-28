"""
Serial interface for controlling SK6812 LED strips.

This module provides:
- Automatic detection of the correct USB port based on platform.
- Mapping of human-readable colour names to SK6812 command codes.
- Functions to build and send JSON payloads to the LED strip over serial.
- Thread-safe serial communication with automatic reconnection.
"""
# Standard imports:
import json
import serial
import platform
import threading

# Serial configuration
baud = 115200
ledstrip = None
serial_lock = threading.Lock()


def get_usb_port():
    """
    Determine the appropriate USB port for the LED strip based on the host
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


def get_command_code(colour):
    """
    Map a colour name to its corresponding SK6812 command code.

    Args:
        colour (str): Human-readable colour name (e.g., 'red', 'blue', 'warm').

    Returns:
        tuple[int, int, int, int]: A 4-tuple representing (R, G, B, W) values.

    Raises:
        ValueError: If the provided colour name is not recognized.
    """
    codes = {
        'natural': (0, 0, 0, 255),
        'cool': (255, 255, 255, 255),
        'warm': (253, 244, 220, 0),
        'red': (255, 0, 0, 0),
        'green': (0, 255, 0, 0),
        'blue': (0, 0, 255, 0),
        'off': (0, 0, 0, 0)
    }
    try:
        return codes[colour]
    except KeyError:
        raise ValueError(f'Unknown settings for: {colour}')


def sk6812_command(command):
    """
    Build and send a command payload for the SK6812 LED strip.

    Args:
        command (dict): A dictionary containing:
            - 'channels' (list[int]): Target channel indices.
            - 'colour' (str): Colour name to apply.
            - 'brightness' (float): Brightness level.
            - 'effect' (str): Lighting effect to apply.

    Side Effects:
        Calls `send_payload()` to transmit the payload over serial.
    """
    payload = []
    for channel in command['channels']:
        payload.append(
            {
                'index': channel,
                'set': get_command_code(command['colour']),
                'brightness': command['brightness'],
                'effect': command['effect']
            }
        )
    send_payload(payload)


def send_payload(payload):
    """
    Send a JSON-encoded payload to the LED strip over serial.

    Args:
        payload (list[dict]): A list of command dictionaries, each containing:
            - 'index' (int): Channel index.
            - 'set' (tuple): Colour values (R, G, B, W).
            - 'brightness' (float): Brightness level.
            - 'effect' (str): Lighting effect.

    Behavior:
        - Ensures thread-safe access to the serial connection.
        - Automatically reconnects if the serial connection is lost.
        - Handles and logs serial errors gracefully.

    Raises:
        Exception: Re-raises unexpected errors after logging.
    """
    global ledstrip
    try:
        with serial_lock:
            # Reconnect if lost
            if not ledstrip or not ledstrip.is_open:
                ledstrip = serial.Serial(ser, baud)
                print('INFO: reconnected to leds.')
            # Send payload
            ledstrip.write((json.dumps(payload) + '\n').encode())
    except serial.SerialException as error:
        print(f'ERROR: Serial error: {error}')
        try:
            if ledstrip and ledstrip.is_open:
                ledstrip.close()
        except serial.SerialException:
            pass
        ledstrip = None
    except Exception as error:
        print(f'ERROR: Unexpected error: {error}')
        raise
