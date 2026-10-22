import argparse

import serial
import serial.tools.list_ports

DEFAULT_BAUD = 9600
READ_TIMEOUT_S = 1.0  # readline() blocks up to this long, then returns b""


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Print lines received from an Arduino over a serial port.")
    parser.add_argument("--port", help="serial port name, e.g. COM3 or /dev/ttyACM0 "
                                       "(prompts for a COM number if omitted)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD,
                        help="baud rate (default: %(default)s)")
    args = parser.parse_args(argv)

    if args.port:
        portVar = args.port
    else:
        for onePort in serial.tools.list_ports.comports():
            print(str(onePort))
        val = input("Select Port: COM")
        portVar = "COM" + str(val)

    serialInst = serial.Serial()
    serialInst.baudrate = args.baud
    serialInst.port = portVar
    serialInst.timeout = READ_TIMEOUT_S
    serialInst.open()

    try:
        while True:
            packet = serialInst.readline()
            if packet:
                print(packet.decode('utf', errors='replace')) #decoder string
    except KeyboardInterrupt:
        pass
    finally:
        serialInst.close()


if __name__ == "__main__":
    main()
