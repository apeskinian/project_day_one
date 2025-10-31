import serial
import json
import platform

# Set up ledstrip serial interface
baud = 115200
ledstrip = None


def get_usb_port():
    if platform.system() == 'Windows':
        return 'COM4'
    elif platform.system() == 'Darwin':
        return '/dev/tty.usbmodem101'
    else:
        return '/dev/ttyUSB0'


def get_command_code(colour):
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
    for cmd in payload:
        print(f'Setting {cmd['index']} to {cmd['set']}')
    global ledstrip
    try:
        # Reconnect if lost
        if not ledstrip or not ledstrip.is_open:
            ledstrip = serial.Serial(get_usb_port(), baud)
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
