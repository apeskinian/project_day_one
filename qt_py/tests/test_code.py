"""
Unit tests for the `apply_json` function in qt_py.code.

These tests validate that JSON commands are correctly applied to a mocked
NeoPixel strip. Hardware-specific modules (`neopixel`, `board`, `supervisor`)
are patched with simple stubs so the tests can run in a standard Python
environment without CircuitPython dependencies.
"""
# Standard imports:
import logging
import unittest
import sys
from types import SimpleNamespace
# Patching fake Neopixel modules
sys.modules['neopixel'] = SimpleNamespace(
    NeoPixel=lambda *a, **k: None, GRBW=None
)
sys.modules['board'] = SimpleNamespace(A3=None)
sys.modules['supervisor'] = SimpleNamespace(
    runtime=SimpleNamespace(serial_bytes_available=False)
)
# Local imports:
import qt_py.code as code  # noqa: E402
from qt_py.code import apply_json  # noqa: E402


class MockPixels:
    """
    A mock replacement for the NeoPixel object.

    This class simulates a strip of LEDs by storing colour values in a list.
    It tracks whether `fill` and `show` have been called, allowing tests to
    assert that commands were executed correctly.
    """
    def __init__(self, n):
        self.data = [(0, 0, 0, 0)] * n
        self.fill_called = None
        self.show_called = False

    def __setitem__(self, i, colour):
        """Set the colour of a single LED at index `i`."""
        self.data[i] = tuple(colour)

    def fill(self, colour):
        """Fill all LEDs with the given colour."""
        self.fill_called = tuple(colour)
        self.data = [tuple(colour)] * len(self.data)

    def show(self):
        """Mark that the LED strip has been updated."""
        self.show_called = True


class TestApplyJson(unittest.TestCase):
    """
    Test suite for the `apply_json` function.

    Each test verifies that JSON input is correctly parsed and applied to
    the mocked NeoPixel strip. Invalid input should be handled gracefully
    without raising exceptions.
    """
    def setUp(self):
        # Arrange
        # Replace the global `pixels` object in code.py with a MockPixels.
        code.pixels = MockPixels(10)
        # Setting log level to CRITICAL to effectively silence logs in test.
        logging.getLogger('qt_py.code').setLevel(logging.CRITICAL)

    def test_fill_all_leds(self):
        # Act - set the colour of all leds to (1, 10, 19, 82)
        apply_json('[{"index": "all", "set": [1, 10, 19, 82]}]')
        # Assert
        self.assertTrue(
            all(c == (1, 10, 19, 82) for c in code.pixels.data)
        )
        self.assertTrue(code.pixels.show_called)

    def test_single_led(self):
        # Act - set the colour of led 0 to (255, 0, 0, 0)
        apply_json('[{"index": 0, "set": [255, 0, 0, 0]}]')
        # Assert
        self.assertEqual(code.pixels.data[0], (255, 0, 0, 0))
        self.assertTrue(code.pixels.show_called)

    def test_multiple_commands(self):
        # Act - set the colour of two channels to different colours
        apply_json(
            '[{"index": 0, "set": [255, 0, 0, 0]},'
            '{"index": 1, "set": [0, 0, 0, 255]}]'
        )
        # Assert
        self.assertEqual(code.pixels.data[0], (255, 0, 0, 0))
        self.assertEqual(code.pixels.data[1], (0, 0, 0, 255))

    def test_invalid_json(self):
        # Act - send an invalid input
        apply_json('not a json string')
        # Assert
        self.assertFalse(code.pixels.show_called)


if __name__ == "__main__":
    unittest.main()
