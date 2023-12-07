import time
import sys
import random
import warrior
from warrior import test, expect

SAFE_STATE_TIME = 10
ALT_BATT_VOLTAGE = 9

if len(sys.argv) != 2 and sys.argv[1] is not "MAG_ON" or "MAG_OFF":
    print(f"Invalid Args for {sys.argv[0]}, either MAG_ON or MAG_OFF")
    sys.exit(1)

MAG_SWITCH = True if sys.argv[1] == "MAG_ON" else False

hilt = warrior.find_hilt()
# Connect between the 9V batteries and RA's battery inputs
bat_1, bat_2 = warrior.AnalogInput(hilt[1])
# Connect in place of the mag switches
mag_1, mag_2 = warrior.AnalogInput(hilt[2])
# Connect to altimiter power provided by RA
alt_1, alt_2 = warrior.AnalogInput(hilt[3])
# Connect to drogue pyro negative channels (1 and 4)
drogue_1, drogue_2 = warrior.Output(hilt[4])
# Connect to main pyro negative channels (1 and 4)
main_1, main_2 = warrior.Output(hilt[5])
# Connect between 5V and RA's 5V input from its CAN connector
can_5v, _ = warrior.AnalogInput(hilt[6])
# Connect to the stratologger UART data line
# uart, _ = warrior.Output(hilt[7])

@test.nominal
def nominal():
    expect.equal(bat_1.get_voltage(), 3, tolerance=2)
    expect.equal(bat_2.get_voltage(), 9, tolerance=1)
    bat_1.set_connected(True)
    bat_2.set_connected(True)
    mag_1.set_connected(False)
    mag_2.set_connected(False)
    drogue_1.set(False)
    drogue_2.set(False)
    main_1.set(False)
    main_2.set(False)
    can_5v.set_connected(True)
    status = hilt.get_can_message(1, board_id="ARMING", msg_type="E_NOMINAL")
    expect.non_none(status)
    expect.equal(status["data"]["status"], "E_NOMINAL")

@test
def battery_voltage_sense():
    bat1_voltage = hilt.get_can_message(1, board_id="ARMING", msg_type="SENSOR_ANALOG", sensor_id="SENSOR_ARM_BATT_1")
    bat2_voltage = hilt.get_can_message(1, board_id="ARMING", msg_type="SENSOR_ANALOG", sensor_id="SENSOR_ARM_BATT_2")
    expect.non_none(bat1_voltage)
    expect.non_none(bat2_voltage)
    expect.equal(bat1_voltage["data"]["value"] / 1000, bat_1.get_voltage(), tolerance=0.5)
    expect.equal(bat2_voltage["data"]["value"] / 1000, bat_2.get_voltage(), tolerance=0.5)


@test
def battery_current_draw():
    # Check bus current draw is normal
    bus_current = hilt.get_can_message(1, board_id="ARMING", msg_type="SENSOR_ANALOG", sensor_id="SENSOR_BUS_CURR")
    # Check battery current draw is normal
    batt_current = hilt.get_can_message(1, board_id="ARMING", msg_type="SENSOR_ANALOG", sensor_id="SENSOR_BATT_CURR")
    expect.non_none(bus_current)
    expect.non_none(batt_current)
    # What current draw should I be expecting for each?
    expect.equal()
    expect.equal()


@test
def batt_voltage_error():
    bat_1.set_connected(False)
    bat_2.set_connected(False)
    status = hilt.get_can_message(1, board_id="ARMING", msg_type="GENERAL_BOARD_STATUS", status="E_BATT_UNDER_VOLTAGE")
    expect.non_none(status)
    expect.equal(status["data"]["voltage"] / 1000, 0, tolerance=0.5)


@test
def drogue_voltage_sense():
    drogue_1.set(ALT_BATT_VOLTAGE)
    v_drogue1 = hilt.get_can_message(1, board_id="ARMING", msg_type="ALT_ARM_STATUS")
    expect.non_none(v_drogue1)
    expect.equal(v_drogue1["data"]["V_DROGUE_H"] / 1000, 2.4, tolerance=1)

    drogue_2.set(ALT_BATT_VOLTAGE)
    v_drogue2 = hilt.get_can_message(1, board_id="ARMING", msg_type="ALT_ARM_STATUS")
    expect.non_none(v_drogue2)
    expect.equal(v_drogue2["data"]["V_DROGUE_L"] / 1000, 2.4, tolerance=1)


@test
def main_voltage_sense():
    main_1.set(ALT_BATT_VOLTAGE)
    v_main1 = hilt.get_can_message(1, board_id="ARMING", msg_type="ALT_ARM_STATUS")
    expect.non_none(v_main1)
    expect.equal(v_main1["data"]["V_MAIN_H"] / 1000, 2.4, tolerance=1)
    main_2.set(ALT_BATT_VOLTAGE)
    v_main2 = hilt.get_can_message(1, board_id="ARMING", msg_type="ALT_ARM_STATUS")
    expect.non_none(v_main2)
    expect.equal(v_main2["data"]["V_MAIN_L"] / 1000, 2.4, tolerance=1)


@test.conditional(MAG_SWITCH)
def mag_switch_testing():
    mag_1.set_connected(False)
    mag_2.set_connected(False)
    v_mag1 = hilt.get_can_message(1, board_id="ARMING", msg_type="SENSOR_ANALOG", sensor_id="SENSOR_MAG_1")
    v_mag2 = hilt.get_can_message(1, board_id="ARMING", msg_type="SENSOR_ANALOG", sensor_id="SENSOR_MAG_2")
    expect.non_none(v_mag1)
    expect.non_none(v_mag2)
    expect.equal(v_mag1["data"]["voltage"] / 1000, 0, tolerance=0.5)
    expect.equal(v_mag2["data"]["voltage"] / 1000, 0, tolerance=0.5)
    mag_1.set_connected(True)
    mag_2.set_connected(True)
    v_mag1_on = hilt.get_can_message(1, board_id="ARMING", msg_type="SENSOR_ANALOG", sensor_id="SENSOR_MAG_1")
    v_mag2_on = hilt.get_can_message(1, board_id="ARMING", msg_type="SENSOR_ANALOG", sensor_id="SENSOR_MAG_2")
    expect.non_none(v_mag1_on)
    expect.non_none(v_mag2_on)
    expect.equal(v_mag1_on["data"]["voltage"] / 1000, 2.4, tolerance=1)
    expect.equal(v_mag2_on["data"]["voltage"] / 1000, 2.4, tolerance=1)


@test
def can_voltage_off():
    hilt.send_can_message("ALT_ARM_CMD", actuator="ARMING", req_state="ARMED")
    time.sleep(0.5)
    can_5v.set_connected(False)
    v_mag_stat = hilt.get_can_message(1, board_id="ARMING", msg_type="SENSOR_ANALOG", sensor_id="SENSOR_MAG_1")
    expect.non_none(v_mag_stat)
    expect.equal(v_mag_stat["data"]["voltage"] / 1000, 2.4, tolerance=1)
    expect.equal(alt_1.get_voltage, 9, 1)
    expect.equal(alt_2.get_voltage, 9, 1)


@test
def arm_altimeters():
    expect.equal(alt_1.get_voltage(), 0, tolerance=0.5)
    expect.equal(alt_2.get_voltage(), 0, tolerance=0.5)
    # Is there a way to specify which?
    hilt.send_can_message("ALT_ARM_CMD", actuator="ARMING", req_state="ARMED")
    time.sleep(0.5)
    expect.equal(alt_1.get_voltage(), 9, tolerance=0.5)
    expect.equal(alt_2.get_voltage(), 9, tolerance=0.5)


@test
def pyro_current_draw():
    # Hook up 1k resistor to pyro connector for drogue 1
    drogue_1.set(ALT_BATT_VOLTAGE)
    time.sleep(0.5)
    expect.equal(drogue_1.get_current, 9, 10)


@test.conditional(lambda: random.random() < 0.3)
def reset():
    hilt.send_can_message("RESET_CMD", reset_board_id="ARMING")

    status = hilt.get_can_message(1, board_id="ARMING", msg_type="GENERAL_BOARD_STATUS")
    expect.non_none(status)
    expect.equal(status["data"]["time"], 0, tolerance=1)


warrior.run()
