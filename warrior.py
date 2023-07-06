import argparse
from enum import Enum
import serial

class Pin(Enum):
    D1 = 'd'
    D2 = 'e'
    AN1 = 'a'
    AN2 = 'b'
    PPS1 = 'p'
    PPS2 = 'q'

class Hilt:
    def __init__(self, port):
        self.serial = serial.Serial(port, 9600, timeout=0.1)

    def digital_read(self, slot, pin: Pin):
        selector = f"{slot - 1}{pin.value}"
        self.serial.write(f";d{selector};".encode('ascii'))
        res = self.nom_until("D")
        if len(res) != 3 or res[:2] != selector or res[2] not in "01":
            print(f"Error unexpected D response {res} for ask {slot}:{pin}.")
            return None
        return res[2] == "1"

    def analog_read(self, slot, pin: Pin):
        selector = f"{slot - 1}{pin.value}"
        self.serial.write(f";a{selector};".encode('ascii'))
        res = self.nom_until("A")
        if len(res) != 7 or res[:2] != selector or not res[2:].isdigit():
            print(f"Error unexpected D response {res} for ask {slot}:{pin}.")
            return None
        return int(res[2:])

    def digital_write(self, slot, pin: Pin, value):
        selector = f"{slot - 1}{pin.value}"
        self.serial.write(f";e{selector}{1 if value else 0};".encode('ascii'))

    def analog_write(self, slot, pin: Pin, channel, value):
        selector = f"{slot - 1}{pin.value}"
        if value < 0 or value > 99:
            print(f"Invalid analog value {value}.")
        self.serial.write(f";b{selector}{channel}{value:02d};".encode('ascii'))

    def nom_until(self, cmd, validator = lambda _: True):
        buf = ''
        while True:
            line = self.serial.read(1024).decode('ascii')
            if not line:
                continue
            buf += line

            while True:
                start = buf.find(cmd)
                if start < 0:
                    buf = ''
                    break
                buf = buf[start:]

                end = buf.find(";")
                if end < 0:
                    break
                res = buf[1:end]
                buf = buf[end + 1:]
                if validator(res):
                    return res

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='the serial port of the HILT')
    args = parser.parse_args()

    hilt = Hilt(args.port)
