from dataclasses import dataclass
import queue
import sys
import time
import threading
from typing import List

import serial
from serial.tools import list_ports

import parsley

from .ui import ui

def find_hilt():
    ports = list(list_ports.grep("hilt"))
    if not ports:
        print("Could not find HILT. Make sure it is plugged in.")
        sys.exit(1)
    if len(ports) > 1:
        print("Multiple HILTs are not supported yet.")
        sys.exit(1)
    return Hilt(ports[0].device)

class Pin:
    def __init__(self, hilt, slot, number):
        self.hilt = hilt
        self.slot = slot
        self.pin = "de"[number]

    def __hash__(self):
        return hash((self.slot, self.pin))

    def digital_read(self):
        self.hilt.pwm_channels[self] = None
        selector = f"{self.slot - 1}{self.pin}"
        with self.hilt.digital_data.mutex:
            self.hilt.digital_data.queue.clear()
        while True:
            self.hilt.write(f";d{selector};".encode('ascii'))
            try:
                res = self.hilt.digital_data.get(timeout=0.5)
            except queue.Empty:
                ui.print_log("Error: Timed out waiting for G response")
                continue
            if res[0] != selector:
                ui.print_log(f"Error: Got G response selector {res[0]} when we expected {selector}.")
                continue
            return res[1]

    def digital_write(self, value):
        self.hilt.pwm_channels[self] = None
        selector = f"{self.slot - 1}{self.pin}"
        self.hilt.write(f";e{selector}{1 if value else 0};".encode('ascii'))

class AnalogPin(Pin):
    def __init__(self, hilt, slot, number):
        super().__init__(hilt, slot, number)
        self.pin = "ab"[number]

    def analog_read(self):
        self.hilt.pwm_channels[self] = None
        selector = f"{self.slot - 1}{self.pin}"
        with self.hilt.analog_data.mutex:
            self.hilt.analog_data.queue.clear()
        while True:
            self.hilt.write(f";a{selector};".encode('ascii'))
            try:
                res = self.hilt.analog_data.get(timeout=0.5)
            except queue.Empty:
                ui.print_log("Error: Timed out waiting for N response")
                continue
            if res[0] != selector:
                ui.print_log(f"Error: Got N response selector {res[0]} when we expected {selector}.")
                continue
            return res[1] / 2**12 * 3.3

class PPSPin(AnalogPin):
    def __init__(self, hilt, slot, number):
        super().__init__(hilt, slot, number)
        self.pin = "pq"[number]

    def analog_write(self, voltage):
        self.hilt.pwm_channels[self] = None
        unused_channels = set(range(9))
        for channel in self.hilt.pwm_channels.values():
            if channel is not None:
                unused_channels.remove(channel)
        if not unused_channels:
            raise KeyError("Out of PWM channels!")
        channel = unused_channels.pop()
        self.hilt.pwm_channels[self] = channel

        selector = f"{self.slot - 1}{self.pin}"
        if voltage < 0 or voltage > 5:
            ui.print_log(f"Invalid analog output voltage {voltage}.")
        value = int(voltage * 99 // 5)
        self.hilt.write(f";b{selector}{channel}{value:02d};".encode('ascii'))

@dataclass
class Slot:
    pps: List[PPSPin]
    an: List[AnalogPin]
    d: List[Pin]

class Hilt:
    def __init__(self, port):
        self.serial = serial.Serial(port, 9600, timeout=0.1)
        self.pwm_channels = {}
        self.slots = []
        for i in range(10):
            pps = [PPSPin(self, i + 1, j) for j in range(2)]
            an = [AnalogPin(self, i + 1, j) for j in range(2)]
            d = [Pin(self, i + 1, j) for j in range(2)]
            self.slots.append(Slot(pps, an, d))

        self.can_messages = queue.Queue()
        self.analog_data = queue.Queue()
        self.digital_data = queue.Queue()

        self.input_thread = threading.Thread(target=self.input_handler, daemon=True)
        self.input_thread.start()

    def __getitem__(self, slot):
        return self.slots[slot - 1]

    def send_can_message(self, msg_type, **kwargs):
        msg = {"msg_type": msg_type, "board_id": "ANY", "time": 0, **kwargs}
        self.send_can_message_raw(msg)

    def send_can_message_raw(self, msg):
        sid, data = parsley.encode_data(msg)
        data = ','.join([f"{b:02X}" for b in data])
        cmd = f"m{sid:03X},{data};"
        self.write(cmd.encode('ascii'))

    def get_can_message(self, timeout, **kwargs):
        with self.can_messages.mutex:
            self.can_messages.queue.clear()
        deadline = time.monotonic() + timeout

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                msg = self.can_messages.get(timeout=remaining)
            except queue.Empty:
                return None

            for k, v in kwargs.items():
                if k not in msg:
                    if k not in msg["data"]:
                        break
                    if msg["data"][k] != v:
                        break
                elif msg[k] != v:
                    break
            else: # else clause runs if for loop wasn't broken out of, ie success
                return msg

    def write(self, data: bytes):
        return self.serial.write(data)

    def input_handler(self):
        self.serial.read(4096) # get rid of old data in the buffer
        buf = "" # buf always starts with an incomplete command
        while True:
            buf += self.serial.read(1024).decode('ascii')
            while True:
                end = buf.find(";")
                if end < 0: # no commands remaining
                    break
                command, buf = buf[:end], buf[end + 1:]
                if command[0] == "G":
                    if len(command) != 4 or command[3] not in "01":
                        ui.print_log(f"Error: Unexpected G response '{command}'.")
                    self.digital_data.put((command[1:3], command[3] == "1"))
                elif command[0] == "N":
                    if len(command) != 8 or not command[3:].isdigit():
                        ui.print_log(f"Error: Unexpected N response '{command}'.")
                    self.analog_data.put((command[1:3], int(command[3:])))
                elif command[0] == "M":
                    sid, data = command[1:].split(",", 1)
                    msg = parsley.parse(*parsley.parse_usb_debug(f"${sid}:{data}"))
                    self.can_messages.put(msg)
                    ui.print_can(parsley.format_line(msg) + "\n")

                while buf and buf[0] not in "GNM":
                    buf = buf[1:]
