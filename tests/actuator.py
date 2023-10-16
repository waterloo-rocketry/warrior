import random
import sys
import time

import warrior
from warrior import test, expect

# Slot 10 - Analog Output
#   Output A -> hall sensor feedback pin (LIMIT_CLOSED)
# Slot 9 - Analog Input
#   Input A -> 12V supply
#   GND A -> 12V gnd
#   Ouptut A -> 12V line on actuator's CAN connector
#
#   Input B -> actuator output (RELAY_MINUS)
#   Output B -> 10k resistor to 5V

# map of actuators to safe state timeouts
ACTUATORS = {
    "injector": ("ACTUATOR_INJ", "ACTUATOR_INJECTOR_VALVE", 0),
    "vent": ("ACTUATOR_VENT", "ACTUATOR_VENT_VALVE", 10)
}

if len(sys.argv) != 2 or sys.argv[1] not in ACTUATORS:
    print(f"Usage: {sys.argv[0]} <actuator_id>\n\nactuator_id must be one of: {', '.join(ACTUATORS.keys())}")
    sys.exit(1)

BOARD_ID, ACTUATOR_ID, SAFE_STATE_TIME = ACTUATORS[sys.argv[1]]

hilt = warrior.find_hilt()
v_12, actuator_out = warrior.AnalogInput(hilt[9])
hall, _ = warrior.Output(hilt[10])

@test.nominal
def nominal():
    v_12.set_connected(True)
    actuator_out.set_connected(True)
    hall.mode(warrior.Output.ANALOG)
    hall.set(2.5)

    expect.equal(v_12.get_voltage(), 12, tolerance=0.3)

    status = hilt.get_can_message(1, board_id=BOARD_ID, msg_type="GENERAL_BOARD_STATUS")
    expect.non_none(status)
    expect.equal(status["data"]["status"], "E_NOMINAL")

@test
def battery_voltage_sense():
    voltage = hilt.get_can_message(1, board_id=BOARD_ID, msg_type="SENSOR_ANALOG", sensor_id="SENSOR_BATT_VOLT")
    expect.non_none(voltage)
    expect.equal(voltage["data"]["value"] / 1000, v_12.get_voltage(), tolerance=0.5)
    # Zero voltage is checked in batt_voltage_error

@test
def actuator_position():
    expected = [(0, "ACTUATOR_OFF"), (1.5, "ACTUATOR_OFF"), (2.5, "ACTUATOR_ON"), (4.0, "ACTUATOR_ON"), (4.2, "ACTUATOR_ILLEGAL")]

    for v, state in expected:
        hall.set(v)

        voltage = hilt.get_can_message(1, board_id=BOARD_ID, msg_type="SENSOR_ANALOG", sensor_id="SENSOR_MAG_1")
        expect.non_none(voltage)
        expect.equal(voltage["data"]["value"] / 1000, v, tolerance=0.5)

        status = hilt.get_can_message(1, board_id=BOARD_ID, msg_type="ACTUATOR_STATUS")
        expect.non_none(status)
        expect.equal(status["data"]["cur_state"], state)

@test
def batt_voltage_error():
    v_12.set_connected(False)
    actuator_out.set_connected(False) # disable pull-up since otherwise voltage leaks through the flyback diode
    status = hilt.get_can_message(1, board_id=BOARD_ID, msg_type="GENERAL_BOARD_STATUS", status="E_BATT_UNDER_VOLTAGE")
    expect.non_none(status)
    expect.equal(status["data"]["voltage"] / 1000, 0, tolerance=0.5)

@test
def actuator_state_error():
    hall.set(5.0)
    status = hilt.get_can_message(1, board_id=BOARD_ID, msg_type="GENERAL_BOARD_STATUS", status="E_ACTUATOR_STATE")
    expect.non_none(status)
    expect.equal(status["data"]["cur_state"], "ACTUATOR_ILLEGAL")

@test
def actuation():
    hilt.send_can_message("ACTUATOR_CMD", actuator=ACTUATOR_ID, req_state="ACTUATOR_ON")
    time.sleep(0.5)
    expect.equal(actuator_out.get_voltage(), 0, tolerance=0.5)

    hilt.send_can_message("ACTUATOR_CMD", actuator=ACTUATOR_ID, req_state="ACTUATOR_OFF")
    time.sleep(0.5)
    # There is a 10k pullup to 5V, and actuator board's resistance is only 20k so the volatage doesn't get that high
    expect.equal(actuator_out.get_voltage(), 5, tolerance=2)

@test.conditional(SAFE_STATE_TIME > 0)
def safe_state_no_command():
    hilt.send_can_message("ACTUATOR_CMD", actuator=ACTUATOR_ID, req_state="ACTUATOR_ON")
    time.sleep(0.5)
    expect.equal(actuator_out.get_voltage(), 0, tolerance=0.5)
    time.sleep(SAFE_STATE_TIME - 1)
    expect.equal(actuator_out.get_voltage(), 0, tolerance=0.5)
    time.sleep(1)
    expect.equal(actuator_out.get_voltage(), 5, tolerance=2)

@test.conditional(SAFE_STATE_TIME > 0)
def safe_state_battery():
    hilt.send_can_message("ACTUATOR_CMD", actuator=ACTUATOR_ID, req_state="ACTUATOR_ON")
    time.sleep(0.5)
    expect.equal(actuator_out.get_voltage(), 0, tolerance=0.5)
    v_12.set_connected(False)
    time.sleep(0.5)
    expect.equal(actuator_out.get_voltage(), 5, tolerance=2)

@test
def safe_state_bus_down():
    hilt.send_can_message("ACTUATOR_CMD", actuator=ACTUATOR_ID, req_state="ACTUATOR_ON")
    time.sleep(0.5)
    expect.equal(actuator_out.get_voltage(), 0, tolerance=0.5)
    hilt.send_can_message("GENERAL_CMD", command="BUS_DOWN_WARNING")
    time.sleep(0.5)
    expect.equal(actuator_out.get_voltage(), 5, tolerance=2)

@test.conditional(lambda: random.random() < 0.3)
def reset():
    hilt.send_can_message("RESET_CMD", reset_board_id=BOARD_ID)

    status = hilt.get_can_message(1, board_id=BOARD_ID, msg_type="GENERAL_BOARD_STATUS")
    expect.non_none(status)
    expect.equal(status["data"]["time"], 0, tolerance=1) # 1 second

warrior.run()
