"""Isolated unit tests for "Serial Arduino - Python.py".

The serial dependency is replaced with mocks, so these tests never touch
real hardware and are not hardware validation.

Run from this folder:  python -m unittest -v test_serial_reader
"""
import contextlib
import importlib.util
import io
import os
import sys
import types
import unittest
from unittest import mock

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "Serial Arduino - Python.py")


def load_script_with_fake_serial():
    """Import the script with a mocked `serial` package; return (module, fake)."""
    fake = types.ModuleType("serial")
    fake.Serial = mock.MagicMock(name="Serial")
    fake.tools = types.ModuleType("serial.tools")
    fake.tools.list_ports = types.ModuleType("serial.tools.list_ports")
    fake.tools.list_ports.comports = mock.MagicMock(name="comports")
    modules = {
        "serial": fake,
        "serial.tools": fake.tools,
        "serial.tools.list_ports": fake.tools.list_ports,
    }
    with mock.patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location("serial_reader_under_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module, fake


class SerialReaderTests(unittest.TestCase):
    def test_import_does_not_open_or_enumerate_ports(self):
        _, fake = load_script_with_fake_serial()
        fake.Serial.assert_not_called()
        fake.tools.list_ports.comports.assert_not_called()

    def test_help_does_not_touch_serial(self):
        module, fake = load_script_with_fake_serial()
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as ctx:
            module.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
        fake.Serial.assert_not_called()
        fake.tools.list_ports.comports.assert_not_called()

    def test_main_prints_one_line_then_closes_on_keyboard_interrupt(self):
        module, fake = load_script_with_fake_serial()
        inst = fake.Serial.return_value
        inst.readline.side_effect = [b"hello\n", KeyboardInterrupt()]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            module.main(["--port", "FAKE1", "--baud", "115200"])
        self.assertIn("hello", out.getvalue())
        self.assertEqual(inst.port, "FAKE1")
        self.assertEqual(inst.baudrate, 115200)
        self.assertGreater(inst.timeout, 0)
        inst.open.assert_called_once_with()
        inst.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
