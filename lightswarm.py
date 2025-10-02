# import serial
from functools import reduce

# baud = 115200
# usb_port = '/dev/ttyUSB0'
# timeout = 1
# lightswarm = None
# lightswarm = serial.Serial(usb_port, baud, timeout)


def get_command_code(action):
    codes = {
        'nothing': 0x00,
        'reset': 0x01,
        'ping_request': 0x02,
        'ping_response': 0x03,
        'on': 0x20,
        'off': 0x21,
        'level': 0x22,
        'fade': 0x23,
        'set_pseudo': 0x25,
        'erase_pseudo': 0x26,
        'media_function': 0x27,
        'event_start': 0x28,
        'event_stop': 0x29,
        'data_forward': 0x2A,
        'mech_command': 0x2B,
        'set_rgb': 0x2C,
        'toggle': 0x2D,
        'flash': 0x2E,
        'flash_rgb': 0x2F,
        'fade_multi': 0x30,
        'fade_rgb': 0x31,
        'config': 0x7E
    }
    try:
        return codes[action]
    except KeyError:
        raise ValueError(f'Unknown action: {action}')


def check_value(input, action, bracket=None):
    if input is None:
        raise ValueError(f'Action: "{action}" is missing a required value')
    if not isinstance(input, int):
        raise TypeError(f'Value for "{action}" must be an integer.')
    if bracket:
        if len(bracket) > 2:
            raise ValueError('Value bracket has too many limits.')
        if len(bracket) == 2:
            if not (bracket[0] <= input <= bracket[1]):
                raise ValueError(
                    f'Error in setting value for "{action}"'
                    f'Value must be between {bracket[0]}-{bracket[1]}.'
                )
        else:
            if not (bracket[0] < input):
                raise ValueError(
                    f'Error in setting value for "{action}"'
                    'Value must be more than 0'
                )
    return input


def get_extra_payload_data(command):
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
        extra_payload_data.append(check_value(fade_interval, action, [0]))
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


def compile_command(command):
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
    print(f'Sending payload of "{bytes(payload)}" to USB port...')
    # global lightswarm
    # try:
    #     # Reconnect if lost
    #     if not lightswarm or not lightswarm.is_open:
    #         lightswarm = serial.Serial(usb_port, baud, timeout)
    #         print('INFO: reconnected to lightswarm.')
    #     # Send payload
    #     lightswarm.write(bytes(payload))
    #     print('Sending command to lightswarm.')
    # except serial.SerialException as error:
    #     print(f'ERROR: Serial error: {error}')
    #     try:
    #         if lightswarm and lightswarm.is_open:
    #             lightswarm.close()
    #     except serial.SerialException:
    #         pass
    #     lightswarm = None
    # except Exception as error:
    #     print(f'ERROR: Unexpected error: {error}')
    #     raise
