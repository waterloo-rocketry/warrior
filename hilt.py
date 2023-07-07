from enum import Enum
import time

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

        self.pwm_channels = {slot + 1: [None, None] for slot in range(10)}

    def _set_pwm(self, slot, pin: Pin, value):
        if pin == Pin.PPS1:
            self.pwm_channels[slot][0] = value
        if pin == Pin.PPS2:
            self.pwm_channels[slot][1] = value

    def digital_read(self, slot, pin: Pin):
        self._set_pwm(slot, pin, None)
        selector = f"{slot - 1}{pin.value}"
        while True:
            self.serial.write(f";d{selector};".encode('ascii'))
            res = self._nom_until("D")
            if res is None or len(res) != 3 or res[:2] != selector or res[2] not in "01":
                print(f"Error unexpected D response {res} for ask {slot}:{pin}.")
                continue
            return res[2] == "1"

    def analog_read(self, slot, pin: Pin):
        self._set_pwm(slot, pin, None)
        selector = f"{slot - 1}{pin.value}"
        while True:
            self.serial.write(f";a{selector};".encode('ascii'))
            res = self._nom_until("A")
            if res is None or len(res) != 7 or res[:2] != selector or not res[2:].isdigit():
                print(f"Error unexpected D response {res} for ask {slot}:{pin}.")
                continue
            return int(res[2:]) / 2**12 * 3.3

    def digital_write(self, slot, pin: Pin, value):
        self._set_pwm(slot, pin, None)
        selector = f"{slot - 1}{pin.value}"
        self.serial.write(f";e{selector}{1 if value else 0};".encode('ascii'))

    def analog_write(self, slot, pin: Pin, voltage):
        self._set_pwm(slot, pin, None)
        unused_channels = set(range(9))
        for (pps1, pps2) in self.pwm_channels.values():
            if pps1 is not None:
                unused_channels.remove(pps1)
            if pps2 is not None:
                unused_channels.remove(pps2)
        if not unused_channels:
            raise KeyError("Out of PWM channels!")
        channel = unused_channels.pop()
        self._set_pwm(slot, pin, channel)

        selector = f"{slot - 1}{pin.value}"
        if voltage < 0 or voltage > 5:
            print(f"Invalid analog output voltage {voltage}.")
        value = int(voltage * 99 // 5)
        self.serial.write(f";b{selector}{channel}{value:02d};".encode('ascii'))

    def _nom_until(self, prefix, validator=lambda _: True, timeout=None):
        deadline = None
        if timeout:
            deadline = time.monotonic() + timeout

        buf = '' # cache incomplete messages between read() calls
        while True:
            if deadline and time.time() > deadline:
                return None
            line = self.serial.read(1024).decode('ascii')
            if not line:
                continue
            buf += line

            while True:
                start = buf.find(prefix)
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
