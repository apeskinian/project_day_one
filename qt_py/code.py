import board  # type: ignore
import neopixel  # type: ignore
import json
import supervisor  # type: ignore
import sys

LED_pin = board.A3
LED_num = 10
pixels = neopixel.NeoPixel(
    LED_pin, LED_num,
    pixel_order=neopixel.GRBW,
    brightness=0.2,
    auto_write=False
)


def apply_json(data):
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


while True:
    if supervisor.runtime.serial_bytes_available:
        line = sys.stdin.readline().strip()
        apply_json(line)
