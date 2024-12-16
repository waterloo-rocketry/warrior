import argparse
import sys
import time

import warrior
from warrior import test, expect
from warrior.ui import ui

# Slot 1 - Output
#   Output A -> Slot 2, Input A
#   Output B -> Slot 2, Input B
#
# Slot 2 - Analog Input
#   Input A -> Slot 1, Output A
#   Output A -> 1k resistor to Slot 2, Output B
#
#   Input B -> Slot 1, Output B
#   Output B -> 1k resistor to Slot 2, Output A

parser = argparse.ArgumentParser(description="HILT self-test via analog input/output loopback on two slots")
parser.add_argument("analog_input", type=int);
parser.add_argument("output", type=int);
args = parser.parse_args()
if args.analog_input < 1 or args.analog_input > 10:
    print("Error: analog input slot id is invalid, should be between 1 and 10.")
    sys.exit(1);
if args.output < 1 or args.output > 10:
    print("Error: output slot id is invalid, should be between 1 and 10.")
    sys.exit(1);

hilt = warrior.find_hilt()
inputs = warrior.AnalogInput(hilt[args.analog_input])
outputs = warrior.Output(hilt[args.output])

# Slot 1 pin D2 and slot 5 pin D1 are input only
BAD_DIGITAL = set([(1, 1), (5, 0)])

@test.nominal
def digital_voltage():
    inputs[0].set_connected(False)
    inputs[1].set_connected(False)
    outputs[0].mode(warrior.Output.DIGITAL)
    outputs[1].mode(warrior.Output.DIGITAL)

    for val in [False, True]:
        for i in range(2):
            outputs[i].set(val)
            expect.equal(inputs[i].get_voltage(), 5 if val else 0, tolerance=1)

@test
def analog_voltage():
    inputs[0].set_connected(False)
    inputs[1].set_connected(False)
    outputs[0].mode(warrior.Output.ANALOG)
    outputs[1].mode(warrior.Output.ANALOG)

    for val in [0, 1, 2.5, 4, 5]:
        for i in range(2):
            if (args.output, i) in BAD_DIGITAL:
                continue
            outputs[i].set(val)
            expect.equal(inputs[i].get_voltage(), val, tolerance=0.4)

@test
def current_sense():
    outputs[0].mode(warrior.Output.ANALOG)
    outputs[1].mode(warrior.Output.ANALOG)
    outputs[0].set(0)
    outputs[1].set(5)
    inputs[0].set_connected(True)
    inputs[1].set_connected(True)
    time.sleep(0.1)
    voltage = inputs[1].get_voltage() - inputs[0].get_voltage()
    current = voltage / 154
    expect.equal(inputs[0].get_current(), -current, tolerance=0.01)
    expect.equal(inputs[1].get_current(), current, tolerance=0.01)
    expect.equal(outputs[0].get_current(), -current, tolerance=0.001)
    expect.equal(outputs[1].get_current(), current, tolerance=0.001)

warrior.run()

