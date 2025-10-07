# import board
# import neopixel
# import json
# import supervisor
# import sys


# LED_pin = board.A3
# LED_num = 10
# pixels = neopixel.NeoPixel(
#     LED_pin, LED_num,
#     pixel_order=neopixel.GRBW,
#     auto_write=False
#     brightness = 1
# )

# def apply_json(data):
#     try:
#         commands = json.loads(data)
#         pixels.brightness = commands.get('brightness', 1)
#         for cmd in commands:
#             i = cmd.get("index")
#             colour = cmd.get("set", 0)
#             if i is not None and 0 <= i < len(pixels):
#                 pixels[i] = (colour)
#         pixels.show()
#     except Exception as e:
#         print("Error:", e)


# while True:
#     if supervisor.runtime.serial_bytes_available:
#         line = sys.stdin.readline().strip()
#         apply_json(line)
