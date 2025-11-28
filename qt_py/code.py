# Standard imports:
import json
import sys
# Third party imports:
import neopixel  # type: ignore
# Local imports:
import board  # type: ignore
import supervisor  # type: ignore

# Setting up the neopixel board.
LED_pin = board.A3  # Check pin is correct
LED_num = 10
pixels = neopixel.NeoPixel(
    LED_pin, LED_num,
    pixel_order=neopixel.GRBW,
    brightness=0.2,
    auto_write=False
)


def apply_json(data):
    """
    Parse a JSON string of LED commands and apply them to the NeoPixel strip.

    The JSON string should represent a list of command objects. Each command
    must contain:
    - "index": either an integer (LED position) or the string "all"
    - "set": a tuple/list of color values (e.g., (R, G, B) or (R, G, B, W))

    Example JSON inputs:
        '{"index": 0, "set": [255, 0, 0]}`
        `{"index": "all", "set": [0, 0, 255]}'

    Args:
        data (str): A JSON-encoded string containing LED commands.

    Raises:
        Exception: If parsing or applying the commands fails, prints an error
        message.
    """
    try:
        commands = json.loads(data)
        for cmd in commands:
            i = cmd.get("index")
            colour = cmd.get("set", 0)
            if i == 'all':
                pixels.fill(colour)
            else:
                pixels[i] = (colour)
        pixels.show()
    except Exception as e:
        print("Error:", e)


def main() -> None:
    """
    Continuously listen for JSON commands over the serial connection
    and apply them to the NeoPixel strip.

    The loop checks if there are bytes available on the serial interface.
    When a line of input is received, it is stripped of whitespace and
    passed to `apply_json()` for processing.

    This function runs indefinitely until the program is stopped.
    """
    while True:
        if supervisor.runtime.serial_bytes_available:
            line = sys.stdin.readline().strip()
            apply_json(line)


if __name__ == "__main__":
    main()
